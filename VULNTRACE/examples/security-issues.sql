-- Security Vulnerability Examples
-- These examples demonstrate various SQL security issues

-- Example 1: Hardcoded credentials (HIGH)
-- Issue: Password hardcoded in query
SELECT * FROM users 
WHERE username = 'admin' 
AND password = 'secret123';

-- Example 2: Sensitive data exposure (HIGH)
-- Issue: Selecting sensitive columns without protection
SELECT id, username, email, password, ssn, credit_card 
FROM users;

-- Example 3: GRANT ALL privileges (CRITICAL)
-- Issue: Granting excessive permissions
GRANT ALL PRIVILEGES ON database.* TO 'app_user'@'%';

-- Example 4: Public access (HIGH)
-- Issue: Granting access to PUBLIC
GRANT SELECT ON sensitive_table TO PUBLIC;

-- Example 5: DROP TABLE without checks (CRITICAL)
-- Issue: Destructive operation without safeguards
DROP TABLE IF EXISTS users;

-- Example 6: TRUNCATE without WHERE (HIGH)
-- Issue: Truncating entire table
TRUNCATE TABLE logs;

-- Example 7: xp_cmdshell (CRITICAL)
-- Issue: Executing system commands from SQL
EXEC xp_cmdshell 'dir c:\';

-- Example 8: Unsafe system procedure (HIGH)
-- Issue: Using unsafe system procedures
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;

-- Example 9: Data exposure in error messages (MEDIUM)
-- Issue: Error messages may expose sensitive data
SELECT * FROM users WHERE id = 1/0;

-- Example 10: Missing encryption (HIGH)
-- Issue: Storing sensitive data without encryption
INSERT INTO users (username, password, ssn) 
VALUES ('user1', 'plaintext', '123-45-6789');

-- Example 11: Weak password policy (MEDIUM)
-- Issue: No password complexity check
SELECT * FROM users 
WHERE password = '123456' OR password = 'password';

-- Example 12: Privilege escalation (CRITICAL)
-- Issue: Attempting to escalate privileges
GRANT CREATE USER TO 'regular_user';
GRANT DROP ANY TABLE TO 'regular_user';

-- Example 13: Access to system tables (HIGH)
-- Issue: Querying system tables may expose metadata
SELECT * FROM information_schema.columns 
WHERE table_name = 'users';

-- Example 14: Comment-based attacks (MEDIUM)
-- Issue: Comments may hide malicious code
SELECT * FROM users -- DROP TABLE users; --
WHERE id = 1;

-- Example 15: Time-based injection detection (MEDIUM)
-- Issue: Using time delays for injection testing
SELECT * FROM users 
WHERE id = 1; WAITFOR DELAY '00:00:05';
