# Responsible AI-Assisted Development

## Provenance

Development of the initial implementation and candidate SQL used AI assistance. Human approval has not yet been recorded. The review report deliberately starts with human_review_status=PENDING and production_approved=false.

No AI API is called by the application. The project demonstrates reviewing an AI-authored artifact, not building an autonomous coding agent.

## Reproduce a prompt iteration

Use only the schema, metric definition, and tiny synthetic fixtures:

> Write a read-only SQLite query for exact-day D1, D7, and D14 product retention. dim_users contains user_id and signup_at. events contains user_id, event_timestamp, and event_name. Only app_open, view_item, add_to_cart, and purchase count as activity. Deduplicate user activity by date. Exclude cohort/day combinations without a complete observation window, using the maximum observed event date as the demo cutoff. Return cohort_date, day_offset, eligible_users, retained_users, and retention_rate. Explain denominator and censoring assumptions. Do not request real user data.

Save your actual prompt, actual response, date, and the tool/model you used in a new Markdown file. Do not invent these records.

## Review checks

Run `python -m ai_review.check`.

- Candidate output must equal the reference output on synthetic generated data.
- Independent expected-value fixtures cover duplicate daily activity, nonqualifying activity, zero-return users, and incomplete observation windows.
- Retained users cannot exceed eligible users.
- Rates must remain between zero and one.
- Execution uses a read-only database connection.

Reference agreement alone is weak evidence because the same assistant supplied both queries. Independent expected values and your own additional tests are important.

## Required human review

1. Explain the grain and denominator without reading the query.
2. Check UTC date boundaries and exact-day versus rolling retention.
3. Add an independently designed boundary fixture.
4. Verify that prompts and logs contain no credentials, personal data, or confidential code.
5. Review runtime and query plans on a larger synthetic dataset.
6. Record approval or rejection, reasons, reviewer, and date using your real details.

Do not change production_approved to true simply because automated checks passed. No production deployment or formal approval is provided by this demo.

## Measuring a workflow improvement

Time one comparable SQL task manually and one AI-assisted task, including review and rework. Keep the same correctness criteria and record failures. Report only your observed results; the repository does not claim an efficiency percentage.
