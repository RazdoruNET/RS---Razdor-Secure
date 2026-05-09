-- Vulnerable SQL examples for testing SQLGuard Pro

-- 1. SQL Injection vulnerability
SELECT * FROM users WHERE username = '${username}' AND password = '${password}';

-- 2. Another SQL injection pattern  
SELECT * FROM products WHERE id = 1 OR '1'='1';

-- 3. Performance issue - SELECT * without LIMIT
SELECT * FROM large_table ORDER BY created_date;

-- 4. Hardcoded credentials
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'password123';

-- 5. Missing WHERE clause in DELETE
DELETE FROM logs;

-- 6. Unsafe dynamic SQL
EXEC('SELECT * FROM users WHERE id = ' + @userId);

-- 7. Information disclosure
SELECT * FROM users WHERE email LIKE '%@%' AND status = 'active';
