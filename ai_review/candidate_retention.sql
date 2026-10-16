-- AI-authored exact-day retention candidate.
-- Cohorts without a complete observation window must not enter denominators.
WITH days(day_offset) AS (VALUES(1),(7),(14)),
limits AS (SELECT date(MAX(event_timestamp)) AS cutoff FROM events),
population AS (
 SELECT u.user_id,date(u.signup_at) AS cohort_date,d.day_offset
 FROM dim_users u CROSS JOIN days d CROSS JOIN limits l
 WHERE u.signup_at IS NOT NULL
 AND date(u.signup_at,'+' || d.day_offset || ' days') <= l.cutoff
),
daily_users AS (
 SELECT DISTINCT user_id,date(event_timestamp) AS activity_date
 FROM events WHERE event_name IN ('app_open','view_item','add_to_cart','purchase')
)
SELECT p.cohort_date,p.day_offset,COUNT(*) AS eligible_users,
       COUNT(a.user_id) AS retained_users,
       ROUND(1.0 * COUNT(a.user_id)/COUNT(*),4) AS retention_rate
FROM population p LEFT JOIN daily_users a
 ON a.user_id=p.user_id
 AND a.activity_date=date(p.cohort_date,'+' || p.day_offset || ' days')
GROUP BY 1,2 ORDER BY 1,2;

