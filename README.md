# Product Analytics Engineering Portfolio

Three connected learning projects using synthetic product events: a reliable event pipeline, product engagement and retention analytics, and a reviewed AI-assisted SQL workflow.

**Status:** The default implementation runs locally using Python and SQLite. The repository includes automated tests, SQL analytics, CSV dashboard exports, a GitHub Actions workflow, and an AI review example. Airflow, dbt, Snowflake, and Tableau are extension exercises described in the guide, not completed integrations.

No paid account, real customer records, API key, or third-party Python package is required for the local version.

## Start here

Read [the step-by-step guide](docs/STEP_BY_STEP.md), then run:

```bash
python --version
python -m unittest discover -s tests -v
python -m pipeline.generate
python -m pipeline.run
python -m analytics.export
python -m ai_review.check
```

Use Python 3.11 or newer. Run commands from this repository's root. Some Windows installations use `py` instead of `python`.

The generator prints its fixed synthetic-data clock. The pipeline uses this same clock for reproducible freshness checks; it is not claiming that generated events are current production data.

## Architecture

```text
Deterministic synthetic JSONL events
                 |
     Schema validation / quarantine
                 |
    Idempotent SQLite event upserts
       /                        \
Users / sessions / events    Quality checks + run audit
       |
SQL marts: DAU / activation / funnel / cohort retention
       |
CSV exports --> optional Tableau dashboard

AI-authored SQL candidate --> correctness tests --> review report
                                                    |
                                   Human approval still required
```

## Repository layout

```text
pipeline/           Synthetic generator, validation, ingestion, quality checks
analytics/          Metric SQL and CSV exporter
ai_review/          AI-authored candidate and executable review checks
tests/              Automated pipeline and analytics tests
docs/               Setup guide, event contract, metrics, operations, AI review
.github/workflows/  Local tests and integration smoke run
```

## Project scope

| Project | Implemented locally | Extension work |
|---|---|---|
| Product Event Analytics Pipeline | Event contract; quarantine; deduplication; late-event handling; repeatable backfills; user/session/event tables; quality checks; freshness checks; run log | Airflow orchestration; dbt models; Snowflake warehouse; deployed alerting |
| Product Engagement and Retention Analytics | DAU; activation; ordered funnel; cohort retention; experiment assignment/exposure/outcome datasets; CSV exports | Tableau workbook; metric stakeholder review; statistical experiment analysis |
| Responsible AI-Assisted Data Development | AI-authored retention query; reference comparison; edge-case fixtures; read-only execution; privacy checklist; machine-readable report | Your own prompt iterations; human review record; measured comparison against a manual workflow |

## Truthful resume use

Before publishing, run the code, read it, change it, and be able to explain the design. Until the extensions are implemented, describe this as **Python, SQL, SQLite, and GitHub Actions**, not as a deployed Airflow/dbt/Snowflake system. The AI review produces evidence of automated checks; it does not substitute for human approval or demonstrate production safety.

Use [the verification checklist](docs/STEP_BY_STEP.md#completion-checklist) to decide which project claims you can support.

