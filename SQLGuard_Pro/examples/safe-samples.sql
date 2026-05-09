-- Safe SQL Examples (No vulnerabilities should be detected)

-- 1. Parameterized Queries
SELECT id, username, email FROM users WHERE id = ? AND status = ?;

-- 2. Prepared Statements
PREPARE stmt FROM 'SELECT * FROM products WHERE category = ? AND price < ?';
EXECUTE stmt USING @category, @max_price;
DEALLOCATE PREPARE stmt;

-- 3. Stored Procedures with Parameters
CREATE PROCEDURE GetUserById(IN userId INT)
BEGIN
    SELECT id, username, email, created_at 
    FROM users 
    WHERE id = userId;
END;

-- 4. Safe Dynamic SQL with Parameters
CREATE PROCEDURE SearchUsers(IN searchTerm VARCHAR(100))
BEGIN
    SET @sql = 'SELECT id, username, email FROM users WHERE username LIKE CONCAT(''%'', ?, ''%'')';
    PREPARE stmt FROM @sql;
    EXECUTE stmt USING searchTerm;
    DEALLOCATE PREPARE stmt;
END;

-- 5. Proper JOIN with Specific Columns
SELECT 
    u.id,
    u.username,
    u.email,
    COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.id, u.username, u.email
LIMIT 100;

-- 6. Safe INSERT with Parameters
INSERT INTO users (username, email, password_hash, created_at)
VALUES (?, ?, ?, NOW());

-- 7. Safe UPDATE with WHERE clause
UPDATE users 
SET last_login = NOW(), login_count = login_count + 1 
WHERE id = ? AND status = 'active';

-- 8. Safe DELETE with WHERE clause
DELETE FROM sessions 
WHERE user_id = ? AND expires_at < NOW();

-- 9. View with Limited Columns
CREATE VIEW user_public_info AS
SELECT 
    id,
    username,
    created_at,
    last_login
FROM users
WHERE status = 'active';

-- 10. Function with Parameters
CREATE FUNCTION GetUserOrderCount(userId INT)
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE orderCount INT;
    
    SELECT COUNT(*) INTO orderCount
    FROM orders
    WHERE user_id = userId;
    
    RETURN orderCount;
END;

-- 11. Trigger with Safe Operations
CREATE TRIGGER update_user_stats
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO user_stats (user_id, order_count, total_spent, last_order_date)
    VALUES (NEW.user_id, 1, NEW.total, NEW.created_at)
    ON DUPLICATE KEY UPDATE 
        order_count = order_count + 1,
        total_spent = total_spent + NEW.total,
        last_order_date = NEW.created_at;
END;

-- 12. Transaction with Error Handling
START TRANSACTION;

BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    INSERT INTO orders (user_id, total, status, created_at)
    VALUES (?, ?, 'pending', NOW());
    
    UPDATE products 
    SET stock = stock - 1 
    WHERE id = ? AND stock > 0;
    
    COMMIT;
END;

-- 13. CTE (Common Table Expression) with Proper Structure
WITH user_orders AS (
    SELECT 
        u.id,
        u.username,
        COUNT(o.id) as order_count,
        SUM(o.total) as total_spent
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.status = 'active'
    GROUP BY u.id, u.username
),
user_stats AS (
    SELECT 
        id,
        username,
        CASE 
            WHEN order_count = 0 THEN 'No orders'
            WHEN order_count < 5 THEN 'Occasional buyer'
            WHEN order_count < 20 THEN 'Regular buyer'
            ELSE 'Frequent buyer'
        END as buyer_type
    FROM user_orders
)
SELECT 
    us.*,
    uo.order_count,
    uo.total_spent
FROM user_stats us
JOIN user_orders uo ON us.id = uo.id
ORDER BY uo.total_spent DESC
LIMIT 50;

-- 14. Window Functions with Proper Usage
SELECT 
    id,
    username,
    email,
    ROW_NUMBER() OVER (ORDER BY created_at DESC) as newest_first,
    RANK() OVER (PARTITION BY status ORDER BY last_login DESC) as rank_in_status,
    LAG(last_login) OVER (ORDER BY created_at) as previous_login
FROM users
WHERE status = 'active';

-- 15. JSON Operations (PostgreSQL)
SELECT 
    id,
    username,
    profile_data->>'first_name' as first_name,
    profile_data->>'last_name' as last_name,
    profile_data->'preferences'->>'theme' as theme
FROM users
WHERE profile_data->>'newsletter' = 'true';

-- 16. Full-Text Search (PostgreSQL)
SELECT 
    id,
    title,
    content,
    ts_rank(search_vector, plainto_tsquery(?, 1)) as relevance
FROM articles
WHERE search_vector @@ plainto_tsquery(?)
ORDER BY relevance DESC
LIMIT 20;

-- 17. Partitioned Table Operations
INSERT INTO orders_2024 (user_id, total, status, created_at)
VALUES (?, ?, 'completed', NOW());

SELECT 
    id,
    user_id,
    total,
    status,
    created_at
FROM orders_2024
WHERE created_at >= DATE_TRUNC('month', NOW())
ORDER BY created_at DESC
LIMIT 100;

-- 18. Materialized View Refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY user_order_summary;

SELECT 
    user_id,
    username,
    total_orders,
    total_spent,
    avg_order_value
FROM user_order_summary
WHERE total_orders > 10
ORDER BY total_spent DESC;

-- 19. Recursive CTE for Hierarchy
WITH RECURSIVE user_hierarchy AS (
    SELECT 
        id,
        username,
        manager_id,
        1 as level
    FROM users
    WHERE manager_id IS NULL
    
    UNION ALL
    
    SELECT 
        u.id,
        u.username,
        u.manager_id,
        uh.level + 1
    FROM users u
    JOIN user_hierarchy uh ON u.manager_id = uh.id
)
SELECT 
    id,
    username,
    level,
    LPAD(' ', (level - 1) * 4, ' ') || username as formatted_name
FROM user_hierarchy
ORDER BY level, username;

-- 20. Batch Processing with Proper Limits
INSERT INTO email_queue (user_id, email, subject, body, created_at)
SELECT 
    id,
    email,
    'Welcome to our platform',
    'Thank you for joining our community!',
    NOW()
FROM users
WHERE status = 'active' 
  AND email_verified = true
  AND last_email_sent IS NULL
LIMIT 1000;
