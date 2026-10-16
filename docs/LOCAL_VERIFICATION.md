# Local Verification Record

Verified in the build sandbox on October 16, 2026 using Python 3.14.3 and SQLite through Python's standard library. These observations describe the supplied synthetic dataset, not production performance or the learner's employment history.

## Automated tests

`python -m unittest discover -s tests -v` completed with 10 passing tests.

Coverage includes idempotent replay, quarantine deduplication, late-arriving records, repeatable backfills, conflicting event identifiers, invalid JSON, required fields, stale/future freshness failures, duplicate experiment assignment detection, CSV export, SQL candidate review, out-of-order funnel events, and missing experiment exposure.

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

The AI-query review passed its four automated checks. Human review remains pending, and production approval remains false.

## Not verified here

No Airflow deployment, dbt project, Snowflake account, or Tableau workbook was configured or tested. GitHub Actions is a separate hosted execution and should be checked in the repository after pushing.
