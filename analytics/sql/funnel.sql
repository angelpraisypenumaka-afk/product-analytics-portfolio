WITH views AS (
    SELECT user_id, session_id, MIN(event_timestamp) AS viewed_at
    FROM events WHERE event_name='view_item' GROUP BY 1,2
),
carts AS (
    SELECT v.user_id, v.session_id, MIN(e.event_timestamp) AS carted_at
    FROM views v JOIN events e USING(user_id,session_id)
    WHERE e.event_name='add_to_cart' AND e.event_timestamp >= v.viewed_at
    GROUP BY 1,2
),
purchases AS (
    SELECT c.user_id, c.session_id, MIN(e.event_timestamp) AS purchased_at
    FROM carts c JOIN events e USING(user_id,session_id)
    WHERE e.event_name='purchase' AND e.event_timestamp >= c.carted_at
    GROUP BY 1,2
)
SELECT COUNT(*) AS sessions_viewed,
       COUNT(c.carted_at) AS sessions_carted,
       COUNT(p.purchased_at) AS sessions_purchased,
       ROUND(1.0 * COUNT(p.purchased_at) / NULLIF(COUNT(*),0),4) AS view_to_purchase_rate
FROM views v LEFT JOIN carts c USING(user_id,session_id)
LEFT JOIN purchases p USING(user_id,session_id);

