-- Performance Issue Examples
-- These examples demonstrate various SQL performance anti-patterns

-- Example 1: SELECT * without LIMIT (MEDIUM)
-- Issue: Retrieves all columns and rows without limit
SELECT * FROM large_table;

-- Example 2: Missing WHERE clause (HIGH)
-- Issue: DELETE without WHERE affects all rows
DELETE FROM logs;

-- Example 3: SELECT * with JOIN (MEDIUM)
-- Issue: SELECT * with JOIN retrieves unnecessary columns
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id
JOIN payments p ON o.id = p.order_id;

-- Example 4: Cartesian product (CRITICAL)
-- Issue: Missing JOIN condition creates Cartesian product
SELECT * FROM users, orders;

-- Example 5: N+1 query pattern (HIGH)
-- Issue: Subquery in SELECT clause executed for each row
SELECT u.*, 
  (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
FROM users u;

-- Example 6: ORDER BY without index (MEDIUM)
-- Issue: ORDER BY on non-indexed column
SELECT * FROM products 
ORDER BY created_at DESC;

-- Example 7: Leading wildcard in LIKE (MEDIUM)
-- Issue: Leading wildcard prevents index usage
SELECT * FROM users 
WHERE username LIKE '%john%';

-- Example 8: OR conditions on different columns (MEDIUM)
-- Issue: Multiple OR conditions may not use indexes efficiently
SELECT * FROM orders 
WHERE status = 'pending' OR status = 'processing' OR status = 'shipped';

-- Example 9: Suboptimal JOIN order (MEDIUM)
-- Issue: JOIN order may affect performance
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
WHERE u.status = 'active';

-- Example 10: Missing index on foreign key (LOW)
-- Issue: Foreign key without index can slow down JOINs
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > '2024-01-01';

-- Example 11: Large IN clause (MEDIUM)
-- Issue: Large IN clause can be inefficient
SELECT * FROM products 
WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20);

-- Example 12: Function on indexed column (MEDIUM)
-- Issue: Using function on indexed column prevents index usage
SELECT * FROM users 
WHERE UPPER(email) = 'USER@EXAMPLE.COM';

-- Example 13: DISTINCT without GROUP BY (MEDIUM)
-- Issue: DISTINCT can be expensive
SELECT DISTINCT user_id FROM orders;

-- Example 14: Multiple subqueries (HIGH)
-- Issue: Nested subqueries can be inefficient
SELECT * FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE total > 1000)
AND id NOT IN (SELECT user_id FROM blocked_users);

-- Example 15: Unnecessary columns (LOW)
-- Issue: Retrieving more columns than needed
SELECT id, name, email, phone, address, city, state, zip, country, 
       created_at, updated_at, last_login, status, role
FROM users
WHERE status = 'active';
