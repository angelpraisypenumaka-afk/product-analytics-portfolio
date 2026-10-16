WITH users AS (
    SELECT user_id, signup_at FROM dim_users WHERE signup_at IS NOT NULL
),
activated AS (
    SELECT DISTINCT u.user_id
    FROM users u JOIN events e ON u.user_id=e.user_id
    WHERE e.event_name='view_item'
      AND julianday(e.event_timestamp) >= julianday(u.signup_at)
      AND julianday(e.event_timestamp) < julianday(u.signup_at) + 1
)
SELECT date(u.signup_at) AS signup_date,
       COUNT(*) AS signed_up_users,
       COUNT(a.user_id) AS activated_users,
       ROUND(1.0 * COUNT(a.user_id) / COUNT(*), 4) AS activation_rate
FROM users u LEFT JOIN activated a USING(user_id)
GROUP BY 1 ORDER BY 1;

