# Product Analytics Results

Generated from deterministic synthetic application events. These results demonstrate pipeline and metric behavior; they do not describe real users, production traffic, or a business improvement.

## Dataset

| Measure | Observed value |
|---|---:|
| Accepted events | 3,248 |
| Synthetic users | 120 |
| Sessions | 1,325 |
| Unique quarantined records | 2 |
| Observed active-user dates | 31 |

## Activation and ordered conversion

| Measure | Observed value |
|---|---:|
| Users with complete activation windows | 120 |
| Activated within 24 hours | 86 |
| Weighted activation rate | 71.7% |
| Sessions viewing an item | 881 |
| Sessions adding to cart after viewing | 473 |
| Sessions purchasing after adding to cart | 209 |
| Session view-to-purchase rate | 23.7% |

## Exact-day retention

Rates are weighted by eligible users, not averages of cohort percentages. Only observable cohort/day combinations enter denominators.

| Offset | Retained users | Eligible users | Weighted retention |
|---|---:|---:|---:|
| D1 | 94 | 120 | 78.3% |
| D7 | 71 | 120 | 59.2% |
| D14 | 47 | 120 | 39.2% |

## Experiment data readiness

- Assignment rows: 120.
- Missing exposures: 0.
- Complete seven-day outcome windows: 120.
- These are exposure and outcome datasets, not evidence of a treatment effect.

## Reliability and SQL review

- Latest pipeline quality status: PASS.
- Latest inserted events: 0.
- Latest exact replays: 3249.
- Automated AI-query review: PASS.
- Human review: PENDING.
- Production deployment: none.

## Interpretation limits

The generator is deliberately synthetic and seeded. Activity decreases with time in its programmed sampling process, so observed trends cannot support real product recommendations. UTC is the reporting timezone, retention is exact-day rather than rolling, and the latest observed timestamp is a demonstration completeness watermark. Cloud orchestration, distributed storage, and Tableau are outside the implemented local scope.
