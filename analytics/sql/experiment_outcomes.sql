WITH assignments AS (
    SELECT user_id,
           json_extract(properties,'$.experiment_id') AS experiment_id,
           json_extract(properties,'$.variant') AS variant,
           event_timestamp AS assigned_at
    FROM events WHERE event_name='experiment_assigned'
),
exposures AS (
    SELECT a.user_id,a.experiment_id,MIN(e.event_timestamp) AS exposed_at
    FROM assignments a JOIN events e ON a.user_id=e.user_id
      AND e.event_name='experiment_exposed'
      AND json_extract(e.properties,'$.experiment_id')=a.experiment_id
      AND e.event_timestamp >= a.assigned_at
    GROUP BY 1,2
)
SELECT a.user_id,a.experiment_id,a.variant,a.assigned_at,x.exposed_at,
       CASE WHEN x.exposed_at IS NULL THEN 1 ELSE 0 END AS missing_exposure,
       MAX(CASE WHEN e.event_name='purchase' THEN 1 ELSE 0 END) AS purchased_within_7_days,
       CASE WHEN julianday((SELECT MAX(event_timestamp) FROM events))
                  >= julianday(x.exposed_at) + 7 THEN 1 ELSE 0 END AS outcome_window_complete
FROM assignments a LEFT JOIN exposures x USING(user_id,experiment_id)
LEFT JOIN events e ON e.user_id=a.user_id
  AND julianday(e.event_timestamp) >= julianday(x.exposed_at)
  AND julianday(e.event_timestamp) < julianday(x.exposed_at) + 7
GROUP BY a.user_id,a.experiment_id,a.variant,a.assigned_at,x.exposed_at
ORDER BY a.user_id,a.experiment_id;

