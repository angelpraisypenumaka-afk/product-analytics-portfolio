import contextlib
import io
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from ai_review.check import check, fixture_check, ROOT
from analytics.export import export
from pipeline.generate import AS_OF, generate
from pipeline.run import run, validate, check_quality
from demo import demo


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "data/analytics.db"
        with contextlib.redirect_stdout(io.StringIO()):
            self.source = generate(self.root)
            self.first = run(self.source, self.db)

    def tearDown(self):
        self.temp.cleanup()

    def quiet_run(self, path):
        with contextlib.redirect_stdout(io.StringIO()):
            return run(path, self.db)

    def write_record(self, name, row):
        path = self.root / name
        path.write_text(json.dumps(row) + "\n")
        return path

    def valid_record(self):
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            values = db.execute("SELECT * FROM events LIMIT 1").fetchone()
        keys = ("event_id","user_id","session_id","event_name",
                "event_timestamp","schema_version","properties")
        row = dict(zip(keys, values))
        row["properties"] = json.loads(row["properties"])
        return row

    def test_quarantine_and_replay(self):
        self.assertEqual(self.first["counts"]["rejected_records"], 2)
        self.assertEqual(self.first["counts"]["replayed_events"], 1)
        second = self.quiet_run(self.source)
        self.assertEqual(second["counts"]["inserted_events"], 0)
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0], 2)

    def test_late_arrival_and_repeatable_backfill(self):
        row = self.valid_record()
        row.update(event_id="late_unique", event_name="app_open",
                   event_timestamp="2026-01-01T00:00:00+00:00", properties={})
        path = self.write_record("late.jsonl", row)
        self.assertEqual(self.quiet_run(path)["counts"]["inserted_events"], 1)
        self.assertEqual(self.quiet_run(path)["counts"]["inserted_events"], 0)
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            observed = db.execute("SELECT first_seen_at FROM dim_users WHERE user_id=?",
                                  (row["user_id"],)).fetchone()[0]
        self.assertEqual(observed, "2026-01-01T00:00:00.000000+00:00")

    def test_conflicting_id_is_rejected(self):
        row = self.valid_record()
        row["properties"]["changed"] = True
        result = self.quiet_run(self.write_record("conflict.jsonl", row))
        self.assertEqual(result["counts"]["rejected_records"], 1)
        self.assertEqual(result["counts"]["inserted_events"], 0)

    def test_invalid_json_is_quarantined(self):
        path = self.root / "broken.jsonl"
        path.write_text("{not json}\n")
        self.assertEqual(self.quiet_run(path)["counts"]["rejected_records"], 1)

    def test_event_contract_rejects_bad_fields(self):
        base = self.valid_record()
        for key, value in (
            ("user_id", ""), ("event_timestamp", "2026-01-01"),
            ("schema_version", True), ("properties", []),
            ("event_name", "unrecognized"),
        ):
            row = dict(base)
            row[key] = value
            self.assertIsNotNone(validate(row))

    def test_stale_and_future_data_fail_freshness(self):
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            self.assertFalse(check_quality(db, AS_OF + timedelta(days=4))["freshness_within_24h"])
            self.assertFalse(check_quality(db, AS_OF - timedelta(days=40))["freshness_within_24h"])

    def test_duplicate_experiment_assignment_fails_quality(self):
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.execute("""
            INSERT INTO events
            SELECT event_id || '_duplicate_assignment',user_id,session_id,
                   event_name,event_timestamp,schema_version,properties
            FROM events WHERE event_name='experiment_assigned' LIMIT 1
            """)
            self.assertFalse(check_quality(db, AS_OF)["experiment_assignment_unique"])

    def test_metric_exports_and_ai_checks(self):
        output = self.root / "exports"
        with contextlib.redirect_stdout(io.StringIO()):
            export(self.db, output)
            report = check(self.db, output)
        self.assertEqual(len(list(output.glob("*.csv"))), 5)
        self.assertEqual(report["automated_status"], "PASS")
        self.assertFalse(report["production_approved"])
        self.assertTrue(fixture_check((ROOT / "ai_review/candidate_retention.sql").read_text()))
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            for name in ("activation", "cohort_retention"):
                rows = db.execute((ROOT / f"analytics/sql/{name}.sql").read_text()).fetchall()
                self.assertTrue(rows)
                self.assertTrue(all(0 <= row[-1] <= 1 for row in rows))

    def test_funnel_excludes_out_of_order_purchases(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.executescript("""
        CREATE TABLE events(user_id TEXT,session_id TEXT,event_name TEXT,event_timestamp TEXT);
        INSERT INTO events VALUES
         ('u','s','purchase','2026-01-01T01:00:00+00:00'),
         ('u','s','view_item','2026-01-01T02:00:00+00:00'),
         ('u','s','add_to_cart','2026-01-01T03:00:00+00:00');
        """)
        row = db.execute((ROOT / "analytics/sql/funnel.sql").read_text()).fetchone()
        self.assertEqual(row, (1, 1, 0, 0.0))

    def test_experiment_missing_exposure_is_visible(self):
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.execute("DELETE FROM events WHERE event_name='experiment_exposed'")
            rows = db.execute((ROOT / "analytics/sql/experiment_outcomes.sql").read_text()).fetchall()
            self.assertEqual(len(rows), 120)
            self.assertTrue(all(row[5] == 1 and row[6] == 0 and row[7] == 0 for row in rows))

    def test_nonfinite_properties_are_rejected(self):
        row = self.valid_record()
        row["properties"] = {"amount": float("nan")}
        self.assertIsNotNone(validate(row))
        row.update(event_name="experiment_assigned",
                   properties={"experiment_id": "synthetic_experiment", "variant": []})
        self.assertIsNotNone(validate(row))

    def test_equivalent_timezone_and_subsecond_ordering(self):
        row = self.valid_record()
        row.update(event_id="timezone_record", event_timestamp="2026-01-01T01:00:00+01:00")
        self.assertEqual(self.quiet_run(self.write_record("timezone.jsonl", row))["counts"]["inserted_events"], 1)
        row["event_timestamp"] = "2026-01-01T00:00:00.000000+00:00"
        self.assertEqual(self.quiet_run(self.write_record("timezone_replay.jsonl", row))["counts"]["replayed_events"], 1)
        row["event_id"] = "subsecond_record"
        row["event_timestamp"] = "2026-01-01T00:00:00.500000+00:00"
        self.quiet_run(self.write_record("subsecond.jsonl", row))
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            ids = db.execute("""
              SELECT event_id FROM events WHERE event_id IN ('timezone_record','subsecond_record')
              ORDER BY event_timestamp""").fetchall()
        self.assertEqual(ids, [("timezone_record",), ("subsecond_record",)])

    def test_activation_excludes_immature_users_and_24h_boundary(self):
        with contextlib.closing(sqlite3.connect(":memory:")) as db:
            db.executescript("""
            CREATE TABLE dim_users(user_id TEXT,signup_at TEXT);
            CREATE TABLE events(user_id TEXT,event_name TEXT,event_timestamp TEXT);
            INSERT INTO dim_users VALUES
             ('a','2026-01-01T00:00:00+00:00'),
             ('b','2026-01-02T00:00:00+00:00');
            INSERT INTO events VALUES
             ('a','view_item','2026-01-02T00:00:00+00:00'),
             ('b','view_item','2026-01-02T00:10:00+00:00');
            """)
            rows = db.execute((ROOT / "analytics/sql/activation.sql").read_text()).fetchall()
        self.assertEqual(rows, [("2026-01-01", 1, 0, 0.0)])

    def test_incorrect_ai_query_fails_fixture(self):
        candidate = (ROOT / "ai_review/candidate_retention.sql").read_text()
        mutated = candidate.replace("COUNT(a.user_id) AS retained_users", "0 AS retained_users")
        self.assertFalse(fixture_check(mutated))

    def test_complete_demo_and_results(self):
        with contextlib.redirect_stdout(io.StringIO()):
            result = demo(self.root / "complete")
        self.assertEqual(result["first_load"]["counts"]["inserted_events"], 3248)
        self.assertEqual(result["replay"]["counts"]["inserted_events"], 0)
        text = result["report"].read_text()
        self.assertIn("3,248", text)
        self.assertIn("Automated AI-query review: PASS", text)
        self.assertIn("Human review: PENDING", text)

    @unittest.skipUnless(importlib.util.find_spec("matplotlib"), "Optional plotting dependency not installed")
    def test_static_chart_export(self):
        from analytics.plot import plot
        output = self.root / "figures"
        with contextlib.redirect_stdout(io.StringIO()):
            export(self.db, output)
            path = plot(output)
        self.assertGreater(path.stat().st_size, 20000)
        self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
