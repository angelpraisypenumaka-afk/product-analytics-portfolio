"""Produce a factual Markdown results report from the current local database."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def query(db, name):
    return db.execute(Path(__file__).parent.joinpath("sql", f"{name}.sql").read_text()).fetchall()


def report(db_path=Path("data/analytics.db"), output=Path("exports"), review=None):
    if not Path(db_path).exists():
        raise FileNotFoundError("Run the pipeline before building the report.")
    with closing(sqlite3.connect(f"{Path(db_path).resolve().as_uri()}?mode=ro", uri=True)) as db:
        event_count = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        user_count = db.execute("SELECT COUNT(*) FROM dim_users").fetchone()[0]
        session_count = db.execute("SELECT COUNT(*) FROM fact_sessions").fetchone()[0]
        quarantine_count = db.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
        dau = query(db, "daily_active_users")
        activation = query(db, "activation")
        retention = query(db, "cohort_retention")
        funnel = query(db, "funnel")[0]
        experiments = query(db, "experiment_outcomes")
        latest_run = db.execute("""
          SELECT input_records,inserted_events,replayed_events,rejected_records,quality_status
          FROM pipeline_runs ORDER BY run_id DESC LIMIT 1""").fetchone()
    eligible = sum(row[1] for row in activation)
    activated = sum(row[2] for row in activation)
    activation_text = f"{activated / eligible:.1%}" if eligible else "Not yet observable"
    by_day = {}
    for _, offset, denominator, numerator, _ in retention:
        counts = by_day.setdefault(offset, [0, 0])
        counts[0] += numerator
        counts[1] += denominator
    retention_rows = "\n".join(
        f"| D{offset} | {numerator} | {denominator} | {numerator / denominator:.1%} |"
        for offset, (numerator, denominator) in sorted(by_day.items())
    )
    if review is None:
        review_path = output / "ai_review_report.json"
        review = json.loads(review_path.read_text()) if review_path.exists() else {}
    text = f"""# Product Analytics Results

Generated from deterministic synthetic application events. These results demonstrate pipeline and metric behavior; they do not describe real users, production traffic, or a business improvement.

## Dataset

| Measure | Observed value |
|---|---:|
| Accepted events | {event_count:,} |
| Synthetic users | {user_count:,} |
| Sessions | {session_count:,} |
| Unique quarantined records | {quarantine_count:,} |
| Observed active-user dates | {len(dau)} |

## Activation and ordered conversion

| Measure | Observed value |
|---|---:|
| Users with complete activation windows | {eligible} |
| Activated within 24 hours | {activated} |
| Weighted activation rate | {activation_text} |
| Sessions viewing an item | {funnel[0]} |
| Sessions adding to cart after viewing | {funnel[1]} |
| Sessions purchasing after adding to cart | {funnel[2]} |
| Session view-to-purchase rate | {funnel[3]:.1%} |

## Exact-day retention

Rates are weighted by eligible users, not averages of cohort percentages. Only observable cohort/day combinations enter denominators.

| Offset | Retained users | Eligible users | Weighted retention |
|---|---:|---:|---:|
{retention_rows}

## Experiment data readiness

- Assignment rows: {len(experiments)}.
- Missing exposures: {sum(row[5] for row in experiments)}.
- Complete seven-day outcome windows: {sum(row[7] for row in experiments)}.
- These are exposure and outcome datasets, not evidence of a treatment effect.

## Reliability and SQL review

- Latest pipeline quality status: {latest_run[4] if latest_run else 'No run recorded'}.
- Latest inserted events: {latest_run[1] if latest_run else 0}.
- Latest exact replays: {latest_run[2] if latest_run else 0}.
- Automated AI-query review: {review.get('automated_status', 'Not run')}.
- Human review: {review.get('human_review_status', 'Not recorded')}.
- Production deployment: none.

## Interpretation limits

The generator is deliberately synthetic and seeded. Activity decreases with time in its programmed sampling process, so observed trends cannot support real product recommendations. UTC is the reporting timezone, retention is exact-day rather than rolling, and the latest observed timestamp is a demonstration completeness watermark. Cloud orchestration, distributed storage, and Tableau are outside the implemented local scope.
"""
    output.mkdir(parents=True, exist_ok=True)
    path = output / "results.md"
    path.write_text(text, encoding="utf-8")
    print(f"Results report: {path}")
    return path


if __name__ == "__main__":
    report()
