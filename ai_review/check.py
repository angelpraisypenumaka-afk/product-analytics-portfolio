"""Compare an AI candidate with a reference and independent edge-case fixtures."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fixture_check(candidate):
    db = sqlite3.connect(":memory:")
    db.executescript("""
    CREATE TABLE dim_users(user_id TEXT, signup_at TEXT);
    CREATE TABLE events(user_id TEXT,event_timestamp TEXT,event_name TEXT);
    INSERT INTO dim_users VALUES
      ('a','2026-01-01T00:00:00+00:00'),
      ('b','2026-01-01T00:00:00+00:00'),
      ('c','2026-01-09T00:00:00+00:00');
    INSERT INTO events VALUES
      ('a','2026-01-02T01:00:00+00:00','app_open'),
      ('a','2026-01-02T02:00:00+00:00','app_open'),
      ('a','2026-01-08T01:00:00+00:00','purchase'),
      ('b','2026-01-02T01:00:00+00:00','experiment_assigned'),
      ('c','2026-01-09T01:00:00+00:00','app_open');
    PRAGMA query_only=ON;
    """)
    try:
        actual = db.execute(candidate).fetchall()
    finally:
        db.close()
    expected = [
        ("2026-01-01", 1, 2, 1, 0.5),
        ("2026-01-01", 7, 2, 1, 0.5),
    ]
    return actual == expected


def check(db_path=Path("data/analytics.db"), output=Path("exports")):
    if not db_path.exists():
        raise FileNotFoundError("Run the event pipeline first.")
    candidate = (ROOT / "ai_review/candidate_retention.sql").read_text()
    reference = (ROOT / "analytics/sql/cohort_retention.sql").read_text()
    with closing(sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        generated = db.execute(candidate).fetchall()
        baseline = db.execute(reference).fetchall()
    checks = {
        "matches_reference_on_generated_data": generated == baseline,
        "independent_edge_case_fixture": fixture_check(candidate),
        "rates_within_zero_and_one": all(0 <= row[4] <= 1 for row in generated),
        "retained_not_above_eligible": all(row[3] <= row[2] for row in generated),
    }
    report = {
        "automated_checks": checks,
        "automated_status": "PASS" if all(checks.values()) else "FAIL",
        "human_review_status": "PENDING",
        "production_approved": False,
        "limitations": [
            "Synthetic fixtures are not a production correctness guarantee.",
            "The reference and candidate were supplied in the same AI-assisted build.",
            "Read-only SQLite is a guardrail, not an untrusted-code sandbox.",
            "No AI service is called by this command.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "ai_review_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise RuntimeError("AI candidate failed review.")
    return report


if __name__ == "__main__":
    check()
