# Event Contract

All records are synthetic JSON objects stored one per line. No emails, names, device identifiers, credentials, or real customer records belong in this demonstration.

## Required fields

| Field | Type | Rule |
|---|---|---|
| event_id | String | Nonempty; globally unique immutable event identifier |
| user_id | String | Nonempty; synthetic identifier |
| session_id | String | Nonempty; session grain is user_id plus session_id |
| event_name | String | signup, app_open, view_item, add_to_cart, purchase, experiment_assigned, experiment_exposed |
| event_timestamp | String | ISO timestamp with timezone; normalized to UTC with fixed microsecond precision on load |
| schema_version | Integer | Exactly 1; booleans are rejected |
| properties | Object | Finite JSON values; experiment events require experiment_id; assignments require control or treatment variant |

## Replay and rejection behavior

- Identical normalized events with an existing event_id are counted as replays.
- A reused event_id with a different payload is quarantined; existing facts are not silently overwritten.
- Missing fields, bad JSON, unsupported names, invalid timestamps, and unsupported schema versions are quarantined with a reason.
- A content hash prevents repeated ingestion from duplicating quarantine rows.
- Late events are accepted. Derived tables rebuild over complete history, so late events affect historical sessions and cohorts.
- This is event-level incremental ingestion, not an incrementally maintained warehouse. Full dimension/session rebuilds are an intentional demo-scale tradeoff.
- Correcting an invalid record may require removing its old quarantine entry after review; the demo does not automate that remediation.

## Table grains

- events: one accepted event per event_id.
- dim_users: one user_id, with first observed event and first signup timestamp.
- fact_sessions: one user_id/session_id combination.
- quarantine: one unique rejected raw record.
- pipeline_runs: one successful load attempt that reaches quality evaluation, including attempts with failed quality checks.
