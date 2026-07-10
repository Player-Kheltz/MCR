SELECT event_type, COUNT(*) AS count
FROM events
WHERE created_at >= datetime('now', '-7 days')
GROUP BY event_type
ORDER BY count DESC;

SELECT date, page_views, unique_visitors, conversions, revenue
FROM daily_metrics
WHERE date >= date('now', '-30 days')
ORDER BY date DESC;

SELECT e.event_type, COUNT(DISTINCT e.user_id) AS unique_users
FROM events e
JOIN conversions c ON e.id = c.event_id
GROUP BY e.event_type;

SELECT strftime('%Y-%m', created_at) AS month,
       COUNT(*) AS total_events,
       COUNT(DISTINCT user_id) AS unique_users
FROM events
GROUP BY month
ORDER BY month DESC;

INSERT INTO daily_metrics (date, page_views, unique_visitors) VALUES (date('now'), 0, 0);
UPDATE daily_metrics SET page_views = page_views + 1 WHERE date = date('now');
