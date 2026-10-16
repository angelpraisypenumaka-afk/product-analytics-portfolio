# Local Verification Record

Verified in an isolated development environment on October 16, 2026 using Python 3.14.3 and SQLite through Python's standard library. These observations describe the synthetic dataset and local implementation, not production performance.

## Automated tests

`python -m unittest discover -s tests -v` completed with 16 passing tests with the optional plotting dependency installed.

Coverage includes idempotent replay, quarantine deduplication, late-arriving records, repeatable backfills, conflicting event identifiers, invalid JSON, required fields, nonfinite property values, timezone and subsecond normalization, stale/future freshness failures, duplicate experiment assignment detection, CSV export, SQL candidate review, out-of-order funnel events, activation eligibility and boundaries, missing experiment exposure, a full demo run, and static chart export.

## Fresh database run

`python -m pipeline.run --db data/verified.db` reported:

| Observation | Value |
|---|---|
| Input records | 3,251 |
| Inserted valid events | 3,248 |
| Exact replay records | 1 |
| Rejected records | 2 |
| Quality checks | All five passed |

## Generated analytics

| Export | Data rows |
|---|---|
| Daily active users | 31 |
| Activation | 10 |
| Cohort retention | 30 |
| Experiment outcomes | 120 |
| Session funnel | 1 |

The AI-query review passed its five automated checks. A deliberately incorrect retention query failed the expected-value fixture. Human review remains pending, and production approval remains false.

The one-command demo and optional chart rendering completed successfully. Sample metric CSVs, a results report, a review report, and the rendered chart are committed under docs/evidence.

## Not verified here

No Airflow deployment, dbt project, Snowflake account, or Tableau workbook was configured or tested. GitHub Actions is a separate hosted execution and should be checked in the repository after pushing.
