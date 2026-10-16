"""Validate and load events, rebuild small demo dimensions, and check quality."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from pipeline.generate import AS_OF

NAMES = {"signup", "app_open", "view_item", "add_to_cart", "purchase",
         "experiment_assigned", "experiment_exposed"}

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    properties TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quarantine (
    record_hash TEXT PRIMARY KEY,
    raw_record TEXT NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY,
    executed_at TEXT NOT NULL,
    input_records INTEGER NOT NULL,
    inserted_events INTEGER NOT NULL,
    replayed_events INTEGER NOT NULL,
    rejected_records INTEGER NOT NULL,
    quality_status TEXT NOT NULL
);
"""


def validate(row):
    if not isinstance(row, dict):
        return "record must be an object"
    for key in ("event_id", "user_id", "session_id", "event_name", "event_timestamp"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            return f"missing or invalid {key}"
    if type(row.get("schema_version")) is not int or row["schema_version"] != 1:
        return "unsupported schema_version"
    if row["event_name"] not in NAMES:
        return "unaccepted event_name"
    try:
        stamp = datetime.fromisoformat(row["event_timestamp"])
        if stamp.tzinfo is None:
            return "event_timestamp must include timezone"
    except ValueError:
        return "invalid event_timestamp"
    if not isinstance(row.get("properties"), dict):
        return "properties must be an object"
    try:
        json.dumps(row["properties"], allow_nan=False)
    except (ValueError, TypeError):
        return "properties must contain valid finite JSON values"
    if row["event_name"] in {"experiment_assigned", "experiment_exposed"}:
        if not isinstance(row["properties"].get("experiment_id"), str) or not row["properties"]["experiment_id"]:
            return "experiment_id is required"
    if row["event_name"] == "experiment_assigned":
        variant = row["properties"].get("variant")
        if not isinstance(variant, str) or variant not in {"control", "treatment"}:
            return "unsupported experiment variant"
    return None


def normalized(row):
    return (
        row["event_id"], row["user_id"], row["session_id"], row["event_name"],
        datetime.fromisoformat(row["event_timestamp"]).astimezone(timezone.utc).isoformat(timespec="microseconds"),
        row["schema_version"], json.dumps(row["properties"], sort_keys=True),
    )


def rebuild_models(db):
    # Rebuilt for correctness and simplicity at demo scale, not a large-scale design.
    db.executescript("""
    DROP TABLE IF EXISTS dim_users;
    CREATE TABLE dim_users AS
    SELECT user_id,
           MIN(event_timestamp) AS first_seen_at,
           MIN(CASE WHEN event_name = 'signup' THEN event_timestamp END) AS signup_at
    FROM events GROUP BY user_id;
    CREATE UNIQUE INDEX dim_users_key ON dim_users(user_id);
    DROP TABLE IF EXISTS fact_sessions;
    CREATE TABLE fact_sessions AS
    SELECT user_id, session_id, MIN(event_timestamp) AS started_at,
           MAX(event_timestamp) AS ended_at, COUNT(*) AS event_count
    FROM events GROUP BY user_id, session_id;
    CREATE UNIQUE INDEX fact_sessions_key ON fact_sessions(user_id, session_id);
    CREATE INDEX IF NOT EXISTS events_user_time ON events(user_id, event_timestamp);
    CREATE INDEX IF NOT EXISTS events_name_time ON events(event_name, event_timestamp);
    """)


def check_quality(db, as_of):
    checks = {
        "nonempty": db.execute("SELECT COUNT(*) > 0 FROM events").fetchone()[0] == 1,
        "user_relationship": db.execute("""
            SELECT COUNT(*) FROM events e LEFT JOIN dim_users u USING(user_id)
            WHERE u.user_id IS NULL""").fetchone()[0] == 0,
        "session_relationship": db.execute("""
            SELECT COUNT(*) FROM events e LEFT JOIN fact_sessions s
            ON e.user_id=s.user_id AND e.session_id=s.session_id
            WHERE s.session_id IS NULL""").fetchone()[0] == 0,
        "experiment_assignment_unique": db.execute("""
            SELECT COUNT(*) FROM (
              SELECT user_id, json_extract(properties, '$.experiment_id'), COUNT(*)
              FROM events WHERE event_name='experiment_assigned'
              GROUP BY 1,2 HAVING COUNT(*) > 1
            )""").fetchone()[0] == 0,
    }
    latest = db.execute("SELECT MAX(event_timestamp) FROM events").fetchone()[0]
    if latest:
        age = (as_of - datetime.fromisoformat(latest)).total_seconds()
        checks["freshness_within_24h"] = 0 <= age <= 86400
    else:
        checks["freshness_within_24h"] = False
    return checks


def run(input_path, db_path, as_of=AS_OF):
    input_path, db_path = Path(input_path), Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as db:
        db.executescript(SCHEMA)
        counts = {"input_records": 0, "inserted_events": 0,
                  "replayed_events": 0, "rejected_records": 0}
        for line in input_path.read_text().splitlines():
            if not line.strip():
                continue
            counts["input_records"] += 1
            try:
                row = json.loads(line)
                reason = validate(row)
            except json.JSONDecodeError:
                row, reason = None, "invalid JSON"
            if reason is None:
                values = normalized(row)
                existing = db.execute(
                    "SELECT * FROM events WHERE event_id=?", (values[0],)
                ).fetchone()
                if existing is None:
                    db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?)", values)
                    counts["inserted_events"] += 1
                    continue
                if existing == values:
                    counts["replayed_events"] += 1
                    continue
                reason = "event_id collision with different payload"
            record_hash = hashlib.sha256(line.encode()).hexdigest()
            db.execute("INSERT OR IGNORE INTO quarantine VALUES (?,?,?)",
                       (record_hash, line, reason))
            counts["rejected_records"] += 1
        db.commit()
        rebuild_models(db)
        checks = check_quality(db, as_of)
        db.execute("INSERT INTO pipeline_runs VALUES (NULL,?,?,?,?,?,?)", (
            datetime.now(timezone.utc).isoformat(),
            counts["input_records"], counts["inserted_events"],
            counts["replayed_events"], counts["rejected_records"],
            "PASS" if all(checks.values()) else "FAIL",
        ))
        db.commit()
    result = {"counts": counts, "quality_checks": checks}
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise RuntimeError("Data quality checks failed; inspect output and runbook.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/events.jsonl")
    parser.add_argument("--db", default="data/analytics.db")
    parser.add_argument("--as-of", default=AS_OF.isoformat())
    args = parser.parse_args()
    clock = datetime.fromisoformat(args.as_of)
    if clock.tzinfo is None:
        parser.error("--as-of must include timezone")
    run(args.input, args.db, clock)
