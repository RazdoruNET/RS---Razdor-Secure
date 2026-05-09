-- SQL Injection Vulnerability Examples
-- These examples demonstrate various SQL injection patterns

-- Example 1: String concatenation (CRITICAL)
-- Vulnerability: Direct string concatenation with user input
SELECT * FROM users 
WHERE username = '" + username + "' 
AND password = '" + password + "'";

-- Example 2: Dynamic SQL with EXEC (CRITICAL)
-- Vulnerability: Dynamic SQL construction without parameterization
DECLARE @sql NVARCHAR(MAX);
SET @sql = 'SELECT * FROM users WHERE id = ' + @id;
EXEC(@sql);

-- Example 3: Unsafe CONCAT function (HIGH)
-- Vulnerability: Using CONCAT with user input
SELECT * FROM products 
WHERE name = CONCAT('%', @searchTerm, '%')
AND description = CONCAT(@prefix, @suffix);

-- Example 4: Format string injection (HIGH)
-- Vulnerability: Using string formatting with user input
SELECT * FROM orders 
WHERE customer_id = FORMAT(@userId)
AND status = FORMAT(@status);

-- Example 5: Parameter interpolation (MEDIUM)
-- Vulnerability: Direct parameter interpolation
SELECT * FROM accounts 
WHERE account_number = ${accountId}
AND balance > ${threshold};

-- Example 6: Stored procedure with dynamic SQL (CRITICAL)
-- Vulnerability: sp_executesql without proper parameterization
DECLARE @query NVARCHAR(MAX);
SET @query = N'SELECT * FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;

-- Example 7: Oracle EXECUTE IMMEDIATE (CRITICAL)
-- Vulnerability: Dynamic SQL in Oracle
DECLARE
  sql_stmt VARCHAR2(200);
BEGIN
  sql_stmt := 'SELECT * FROM users WHERE id = ' || :user_id;
  EXECUTE IMMEDIATE sql_stmt;
END;

-- Example 8: PostgreSQL EXECUTE (CRITICAL)
-- Vulnerability: Dynamic SQL in PostgreSQL
DO $$
BEGIN
  EXECUTE 'SELECT * FROM users WHERE id = ' || quote_literal(user_id);
END $$;

-- Example 9: MySQL prepared statement misuse (HIGH)
-- Vulnerability: Incorrect use of prepared statements
SET @sql = CONCAT('SELECT * FROM users WHERE id = ', @id);
PREPARE stmt FROM @sql;
EXECUTE stmt;

-- Example 10: Multiple concatenation points (CRITICAL)
-- Vulnerability: Multiple points of injection
SELECT * FROM transactions 
WHERE user_id = '" + userId + "' 
AND amount > " + minAmount + "
AND date BETWEEN '" + startDate + "' AND '" + endDate + "'";
