SELECT a.name AS account, COUNT(p.id) AS project_count
FROM accounts a
LEFT JOIN projects p ON a.id = p.account_id
GROUP BY a.id
ORDER BY project_count DESC;

SELECT p.name AS project, t.title, t.status, tm.role
FROM projects p
JOIN tasks t ON p.id = t.project_id
JOIN team_members tm ON t.assigned_to = tm.id
WHERE t.status != 'done'
ORDER BY t.priority DESC, t.due_date ASC;

SELECT t.name AS team, COUNT(tm.id) AS member_count
FROM teams t
LEFT JOIN team_members tm ON t.id = tm.team_id
GROUP BY t.id;

UPDATE tasks SET status = 'in_progress' WHERE id = 1;
UPDATE projects SET status = 'archived' WHERE id = 1;

INSERT INTO team_members (team_id, user_id, role) VALUES (1, 42, 'admin');
INSERT INTO tasks (project_id, title, assigned_to) VALUES (1, 'Fix login bug', 1);

DELETE FROM tasks WHERE status = 'done' AND created_at < date('now', '-30 days');
