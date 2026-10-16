# Pipeline Runbook

## Demo service-level objectives

These are proposed learning targets, not commitments agreed with actual consumers.

- Freshness: latest accepted event falls within the previous 24 hours of the supplied clock.
- Uniqueness: event_id is unique; one assignment per user and experiment.
- Completeness: event contract fields are present.
- Relationships: every event maps to a user and session.
- Recovery: reruns do not duplicate accepted events; a historical file can be replayed.

The default clock is fixed to the synthetic generator. Supply `--as-of` to test a different clock. Scheduled production ingestion would use a real UTC clock and a source completeness signal.

## Investigate a failed run

1. Read the printed quality-check results.
2. Inspect the relevant input and quarantine reason without exposing sensitive data.
3. Determine whether the issue is the source contract, duplicate experiment assignment, stale delivery, or transformation logic.
4. Correct the source or code and run tests.
5. Replay the corrected batch with the same event identifiers.
6. Regenerate CSVs and inspect downstream metrics.
7. Record root cause, impacted dates, validation evidence, and preventive action.

```bash
python -m pipeline.run --input data/events.jsonl
python -m analytics.export
```

To backfill, use `--input` with a historical JSONL file. Late events with new identifiers are inserted. Identical events are skipped; changed payloads with existing identifiers are quarantined.

## Known operational limitations

- Single-machine SQLite storage, not a distributed warehouse.
- No deployed scheduler, alerts, access-role integration, or retention-deletion job.
- Model rebuilds and quality checks are not an atomic warehouse publication. Accepted facts persist even if a later quality check fails.
- File failures and process crashes before quality evaluation do not receive pipeline_runs rows.
- Whole-file reading and Python row-by-row inserts are suitable for this demo, not high-volume ingestion.
- Quarantine may contain source payloads. Keep it local, access-restricted, and outside Git.
- The demo implements data minimization through synthetic inputs, not a complete privacy compliance program.

