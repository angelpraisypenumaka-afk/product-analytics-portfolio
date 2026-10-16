WITH offsets AS (
    SELECT 1 AS day_offset UNION ALL SELECT 7 UNION ALL SELECT 14
),
observation AS (
    SELECT date(MAX(event_timestamp)) AS last_observed_date FROM events
),
eligible AS (
    SELECT u.user_id, date(u.signup_at) AS cohort_date, o.day_offset
    FROM dim_users u CROSS JOIN offsets o CROSS JOIN observation obs
    WHERE u.signup_at IS NOT NULL
      AND date(u.signup_at, '+' || o.day_offset || ' days') <= obs.last_observed_date
)
SELECT el.cohort_date, el.day_offset,
       COUNT(DISTINCT el.user_id) AS eligible_users,
       COUNT(DISTINCT e.user_id) AS retained_users,
       ROUND(1.0 * COUNT(DISTINCT e.user_id)
           / COUNT(DISTINCT el.user_id),4) AS retention_rate
FROM eligible el
LEFT JOIN events e ON e.user_id=el.user_id
 AND e.event_name IN ('app_open','view_item','add_to_cart','purchase')
 AND date(e.event_timestamp)=date(el.cohort_date, '+' || el.day_offset || ' days')
GROUP BY 1,2 ORDER BY 1,2;

