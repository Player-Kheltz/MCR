SELECT p.title, p.body, a.name AS author
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE p.published = 1
ORDER BY p.created_at DESC;

SELECT p.title, COUNT(c.id) AS comment_count
FROM posts p
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY p.id
ORDER BY comment_count DESC;

SELECT t.name, COUNT(pt.post_id) AS post_count
FROM tags t
JOIN post_tags pt ON t.id = pt.tag_id
GROUP BY t.id
ORDER BY post_count DESC;

INSERT INTO posts (title, body, author_id, published) VALUES ('Hello World', 'First post!', 1, 1);

UPDATE posts SET published = 1 WHERE id = 1;

SELECT * FROM comments WHERE post_id = 1 ORDER BY created_at ASC;
