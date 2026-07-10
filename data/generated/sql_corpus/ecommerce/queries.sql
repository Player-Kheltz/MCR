SELECT * FROM users WHERE email = 'test@example.com';

SELECT p.name, p.price, c.name AS category
FROM products p
JOIN categories c ON p.category_id = c.id
WHERE p.stock > 0
ORDER BY p.price DESC;

SELECT o.id, o.total, o.status, u.name AS user_name
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at >= '2024-01-01';

INSERT INTO orders (user_id, total, status) VALUES (1, 99.90, 'pending');

UPDATE products SET stock = stock - 1 WHERE id = 42 AND stock > 0;

DELETE FROM order_items WHERE order_id = 1;
DELETE FROM orders WHERE id = 1;

SELECT c.name, COUNT(p.id) AS product_count
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
GROUP BY c.id
HAVING product_count > 0;
