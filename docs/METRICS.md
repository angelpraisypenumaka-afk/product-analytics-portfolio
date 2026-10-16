# Metric Definitions

All timestamps are normalized to UTC. Synthetic data reflects one illustrative application, not a real business.

## Daily active users

Distinct users with app_open, view_item, add_to_cart, or purchase on a UTC calendar day. Signup and experiment logging alone do not constitute engagement.

## Activation

First view_item within the half-open 24-hour interval beginning at signup. Denominator: users who signed up on the cohort date and whose 24-hour window ends on or before the latest observed event timestamp. Recent signups with incomplete windows are excluded. The latest observed timestamp is a demonstration watermark; a production source should supply an explicit completeness signal.

## Conversion funnel

Session-level view_item → add_to_cart → purchase, with nondecreasing event timestamps. Denominator: sessions with a view. Each step counts qualifying sessions, not total events. A purchase before the qualifying cart does not count.

## Retention

Exact-day D1, D7, and D14 retention, not rolling retention. Denominator: users in a signup cohort whose target UTC date falls on or before the latest observed event date. Numerator: those users with a qualifying activity event on that exact target date.

Using the latest observed event date as an observation boundary assumes data is complete through that date. A production system should use an explicit completeness watermark or agreed business cutoff.

## Experiment dataset

Grain: user_id and experiment_id. Columns preserve assignment, first matching exposure after assignment, missing-exposure flag, purchase within seven days after exposure, and outcome-window completeness.

Assignment uniqueness is checked in pipeline quality tests. An unexposed user is flagged rather than silently omitted. A zero purchase flag means no qualifying observed outcome, not necessarily a mature negative outcome; filter outcome_window_complete when interpreting exposed-window conversion.

This is a data-preparation exercise. It is not a causal estimate, sample-ratio-mismatch analysis, power calculation, or production experiment decision.
