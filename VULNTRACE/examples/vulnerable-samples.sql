-- SQL Injection Vulnerabilities
-- 1. String Concatenation
SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "';

-- 2. Dynamic SQL with EXEC
DECLARE @sql NVARCHAR(MAX);
SET @sql = 'SELECT * FROM users WHERE id = ' + @id;
EXEC(@sql);

-- 3. Unsafe Function Usage
EXEC('SELECT * FROM users WHERE name = ''' + @name + '''');

-- 4. Concatenation with CONCAT function
SELECT * FROM products WHERE name = CONCAT('%', @search, '%');

-- Performance Issues
-- 5. SELECT * without LIMIT
SELECT * FROM large_table;

-- 6. Missing WHERE clause
DELETE FROM logs;

-- 7. SELECT * with JOIN
SELECT * FROM users u JOIN orders o ON u.id = o.user_id;

-- 8. Inefficient LIKE query
SELECT * FROM products WHERE name LIKE '%test%';

-- Best Practice Violations
-- 9. Hardcoded credentials
SELECT * FROM admin_users WHERE password = 'admin123';

-- 10. SELECT * usage
SELECT * FROM users WHERE active = 1;

-- 11. Inconsistent naming
SELECT UserName, Email_Address, phone_number FROM Users;

-- Data Exposure
-- 12. Sensitive data exposure
SELECT id, email, phone, address, ssn, credit_card FROM users;

-- 13. Password field in SELECT
SELECT id, username, password FROM users;

-- Permission Issues
-- 14. Administrative operations
DROP TABLE IF EXISTS temp_data;
TRUNCATE TABLE audit_log;
GRANT ALL PRIVILEGES ON *.* TO 'user'@'%';

-- Complex Vulnerabilities
-- 15. Stored procedure with dynamic SQL
CREATE PROCEDURE GetUserOrders(@UserId INT)
AS
BEGIN
    DECLARE @sql NVARCHAR(MAX);
    SET @sql = 'SELECT * FROM orders WHERE user_id = ' + CAST(@UserId AS NVARCHAR(10));
    EXEC(@sql);
END;

-- 16. Trigger with security issues
CREATE TRIGGER audit_trigger
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action, user_id, timestamp)
    VALUES ('INSERT', NEW.id, NOW());
    
    -- Vulnerable: Dynamic SQL in trigger
    SET @sql = CONCAT('UPDATE user_stats SET count = count + 1 WHERE user_id = ', NEW.id);
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END;

-- 17. View with sensitive data
CREATE VIEW user_details AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.phone,
    u.address,
    p.password_hash,
    p.ssn,
    p.credit_card_number
FROM users u
JOIN profiles p ON u.id = p.user_id;

-- 18. Function with SQL injection risk
CREATE FUNCTION GetUserStatus(@Username VARCHAR(50))
RETURNS VARCHAR(20)
BEGIN
    DECLARE @status VARCHAR(20);
    DECLARE @sql NVARCHAR(MAX);
    
    SET @sql = 'SELECT status FROM users WHERE username = ''' + @Username + '''';
    
    -- This is vulnerable to SQL injection
    EXEC sp_executesql @sql, N'@status VARCHAR(20) OUTPUT', @status OUTPUT;
    
    RETURN @status;
END;

-- 19. Batch operations with vulnerabilities
BEGIN TRANSACTION;

-- Vulnerable insert
INSERT INTO users (username, password, email)
VALUES ('" + username + "', '" + password + "', '" + email + "');

-- Performance issue: Large update without WHERE
UPDATE users SET last_login = NOW();

-- Data exposure: Selecting sensitive data
SELECT * FROM users WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 DAY);

COMMIT;

-- 20. Complex query with multiple issues
SELECT 
    u.*,
    o.order_total,
    p.product_name,
    c.credit_card_number,
    a.address
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
LEFT JOIN credit_cards c ON u.id = c.user_id
LEFT JOIN addresses a ON u.id = a.user_id
WHERE u.username LIKE CONCAT('%', '" + search_term + "', '%')
ORDER BY u.created_at DESC;
