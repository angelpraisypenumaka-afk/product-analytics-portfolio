SELECT date(event_timestamp) AS activity_date,
       COUNT(DISTINCT user_id) AS daily_active_users
FROM events
WHERE event_name IN ('app_open', 'view_item', 'add_to_cart', 'purchase')
GROUP BY 1
ORDER BY 1;

