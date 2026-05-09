-- SQL Best Practices Examples
-- These examples demonstrate proper SQL coding practices

-- Example 1: Parameterized queries (SAFE)
-- Good: Using parameterized queries
SELECT * FROM users 
WHERE username = ? 
AND password = ?;

-- Example 2: Specific column selection (GOOD)
-- Good: Selecting only needed columns
SELECT id, username, email 
FROM users 
WHERE status = 'active';

-- Example 3: LIMIT clause (GOOD)
-- Good: Using LIMIT to restrict results
SELECT id, name, price 
FROM products 
WHERE category = 'electronics'
LIMIT 100;

-- Example 4: Proper JOIN syntax (GOOD)
-- Good: Using explicit JOIN with specific columns
SELECT u.id, u.username, o.order_id, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';

-- Example 5: Indexed columns in WHERE (GOOD)
-- Good: Using indexed columns in WHERE clause
SELECT * FROM orders 
WHERE user_id = ? 
AND created_at > ?;

-- Example 6: Prepared statements (SAFE)
-- Good: Using prepared statements
PREPARE stmt FROM 'SELECT * FROM users WHERE id = ?';
EXECUTE stmt USING @userId;
DEALLOCATE PREPARE stmt;

-- Example 7: Transaction with error handling (GOOD)
-- Good: Proper transaction handling
BEGIN TRANSACTION;
BEGIN TRY
  UPDATE accounts SET balance = balance - ? WHERE id = ?;
  UPDATE accounts SET balance = balance + ? WHERE id = ?;
  COMMIT TRANSACTION;
END TRY
BEGIN CATCH
  ROLLBACK TRANSACTION;
  THROW;
END CATCH;

-- Example 8: CTE for readability (GOOD)
-- Good: Using CTE for complex queries
WITH user_orders AS (
  SELECT user_id, COUNT(*) as order_count, SUM(total) as total_spent
  FROM orders
  WHERE created_at > '2024-01-01'
  GROUP BY user_id
)
SELECT u.username, uo.order_count, uo.total_spent
FROM users u
JOIN user_orders uo ON u.id = uo.user_id;

-- Example 9: Window functions (GOOD)
-- Good: Using window functions instead of subqueries
SELECT 
  id,
  username,
  total_spent,
  RANK() OVER (ORDER BY total_spent DESC) as spending_rank
FROM user_spending_summary;

-- Example 10: Proper indexing (GOOD)
-- Good: Creating appropriate indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Example 11: Least privilege principle (SAFE)
-- Good: Granting minimal required permissions
GRANT SELECT, INSERT ON app.users TO 'app_user'@'localhost';
GRANT SELECT, UPDATE ON app.orders TO 'app_user'@'localhost';

-- Example 12: Data masking (GOOD)
-- Good: Masking sensitive data
SELECT 
  id,
  username,
  CONCAT(LEFT(email, 3), '***@', SUBSTRING_INDEX(email, '@', -1)) as masked_email,
  CONCAT('***-**-', RIGHT(ssn, 4)) as masked_ssn
FROM users;

-- Example 13: Stored procedure with parameters (SAFE)
-- Good: Using stored procedures with parameters
CREATE PROCEDURE GetUserById(IN userId INT)
BEGIN
  SELECT id, username, email 
  FROM users 
  WHERE id = userId;
END;

-- Example 14: Proper error handling (GOOD)
-- Good: Comprehensive error handling
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  
  START TRANSACTION;
  -- Your SQL statements here
  COMMIT;
END;

-- Example 15: Consistent naming (GOOD)
-- Good: Using consistent naming conventions
CREATE TABLE user_profiles (
  user_id INT PRIMARY KEY,
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  email_address VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
