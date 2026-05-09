"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StaticAnalyzer = void 0;
const types_1 = require("../types");
class StaticAnalyzer {
    constructor(config) {
        this.config = config;
        this.rules = this.initializeRules();
    }
    async analyze(queries, context) {
        const vulnerabilities = [];
        for (const query of queries) {
            const queryVulnerabilities = await this.analyzeQuery(query, context);
            vulnerabilities.push(...queryVulnerabilities);
        }
        return this.filterIgnoredRules(vulnerabilities);
    }
    async analyzeQuery(query, context) {
        const vulnerabilities = [];
        for (const rule of this.rules) {
            if (this.shouldApplyRule(rule, query)) {
                const ruleVulnerabilities = await rule.analyze(query, context);
                vulnerabilities.push(...ruleVulnerabilities);
            }
        }
        return vulnerabilities;
    }
    shouldApplyRule(rule, query) {
        return rule.databaseTypes.includes(query.database) &&
            rule.queryTypes.includes(query.type);
    }
    filterIgnoredRules(vulnerabilities) {
        return vulnerabilities.filter(vuln => !this.config.ignoredRules.includes(vuln.id));
    }
    initializeRules() {
        return [
            new SQLInjectionRule(),
            new DynamicSQLRule(),
            new ConcatenationRule(),
            new UnparameterizedQueryRule(),
            new PerformanceRule(),
            new MissingIndexRule(),
            new SelectAllRule(),
            new HardcodedCredentialsRule(),
            new DataExposureRule(),
            new PermissionRule(),
            new BestPracticeRule()
        ];
    }
}
exports.StaticAnalyzer = StaticAnalyzer;
// SQL Injection Detection Rule
class SQLInjectionRule {
    constructor() {
        this.id = 'SQL_INJECTION';
        this.name = 'SQL Injection Vulnerability';
        this.description = 'Potential SQL injection vulnerability detected';
        this.severity = types_1.Severity.CRITICAL;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        // Check for string concatenation patterns
        const concatenationPatterns = [
            /concat\s*\(/gi,
            /\|\|/g,
            /\+/g,
            /string\.format/gi,
            /\$\{.*?\}/g,
            /f['"]{.*?}/g
        ];
        for (const pattern of concatenationPatterns) {
            const matches = sql.match(pattern);
            if (matches) {
                vulnerabilities.push(this.createVulnerability(query, `String concatenation detected: ${matches[0]}`, 'Use parameterized queries instead of string concatenation'));
            }
        }
        // Check for unsafe functions
        const unsafeFunctions = [
            'exec', 'execute', 'sp_executesql', 'eval', 'system'
        ];
        for (const func of unsafeFunctions) {
            if (sql.includes(func)) {
                vulnerabilities.push(this.createVulnerability(query, `Unsafe function detected: ${func}`, 'Avoid using dynamic SQL execution functions'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.SQL_INJECTION,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.8,
            category: this.category,
            cwe: 'CWE-89',
            owasp: 'A03:2021 – Injection'
        };
    }
}
// Dynamic SQL Detection Rule
class DynamicSQLRule {
    constructor() {
        this.id = 'DYNAMIC_SQL';
        this.name = 'Dynamic SQL Construction';
        this.description = 'Dynamic SQL detected without proper validation';
        this.severity = types_1.Severity.HIGH;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'EXEC'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        const dynamicPatterns = [
            /exec\s*\(/gi,
            /execute\s*immediate/gi,
            /sp_executesql/gi,
            /prepare\s+.*\s+from/gi
        ];
        for (const pattern of dynamicPatterns) {
            if (pattern.test(sql)) {
                vulnerabilities.push(this.createVulnerability(query, 'Dynamic SQL construction detected', 'Ensure proper input validation and parameterization for dynamic SQL'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.SQL_INJECTION,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.7,
            category: this.category
        };
    }
}
// String Concatenation Rule
class ConcatenationRule {
    constructor() {
        this.id = 'STRING_CONCATENATION';
        this.name = 'String Concatenation in SQL';
        this.description = 'String concatenation used in SQL query';
        this.severity = types_1.Severity.MEDIUM;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text;
        // Check for concatenation operators
        const concatOperators = [/\+/, /\|\|/, /concat\s*\(/gi];
        for (const operator of concatOperators) {
            if (operator.test(sql)) {
                vulnerabilities.push(this.createVulnerability(query, 'String concatenation operator detected', 'Use parameterized queries instead of string concatenation'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.SQL_INJECTION,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.6,
            category: this.category
        };
    }
}
// Unparameterized Query Rule
class UnparameterizedQueryRule {
    constructor() {
        this.id = 'UNPARAMETERIZED_QUERY';
        this.name = 'Unparameterized Query';
        this.description = 'Query uses literal values instead of parameters';
        this.severity = types_1.Severity.MEDIUM;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        if (!query.parameters || query.parameters.length === 0) {
            // Check if query contains literal values that could be parameters
            const literalPattern = /'(.*?)'/g;
            const matches = query.text.match(literalPattern);
            if (matches && matches.length > 2) { // More than 2 literals might indicate missing parameters
                vulnerabilities.push(this.createVulnerability(query, 'Multiple literal values found - consider using parameters', 'Use parameterized queries for better security and performance'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.SQL_INJECTION,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.5,
            category: this.category
        };
    }
}
// Performance Issues Rule
class PerformanceRule {
    constructor() {
        this.id = 'PERFORMANCE_ISSUE';
        this.name = 'Performance Issue';
        this.description = 'Query performance issue detected';
        this.severity = types_1.Severity.MEDIUM;
        this.category = types_1.VulnerabilityCategory.PERFORMANCE;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        // Check for SELECT * without LIMIT
        if (sql.includes('select *') && !sql.includes('limit') && !sql.includes('top')) {
            vulnerabilities.push(this.createVulnerability(query, 'SELECT * without LIMIT or TOP clause', 'Specify only needed columns and add LIMIT clause'));
        }
        // Check for missing WHERE clause
        if (sql.includes('select') && !sql.includes('where') && !sql.includes('limit')) {
            vulnerabilities.push(this.createVulnerability(query, 'Missing WHERE clause in SELECT statement', 'Add WHERE clause to limit result set'));
        }
        // Check for suboptimal JOIN patterns
        if (sql.includes('join') && sql.includes('select *')) {
            vulnerabilities.push(this.createVulnerability(query, 'SELECT * with JOIN may be inefficient', 'Specify specific columns instead of SELECT *'));
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.PERFORMANCE_ISSUE,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.7,
            category: this.category
        };
    }
}
// Missing Index Rule
class MissingIndexRule {
    constructor() {
        this.id = 'MISSING_INDEX';
        this.name = 'Potential Missing Index';
        this.description = 'Query may benefit from an index';
        this.severity = types_1.Severity.LOW;
        this.category = types_1.VulnerabilityCategory.PERFORMANCE;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle'];
        this.queryTypes = ['SELECT'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        // Check for ORDER BY without index hint
        if (sql.includes('order by') && !sql.includes('index')) {
            vulnerabilities.push(this.createVulnerability(query, 'ORDER BY clause may benefit from index', 'Consider adding an index on ORDER BY columns'));
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.PERFORMANCE_ISSUE,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.4,
            category: this.category
        };
    }
}
// SELECT * Rule
class SelectAllRule {
    constructor() {
        this.id = 'SELECT_ALL';
        this.name = 'SELECT * Usage';
        this.description = 'SELECT * can cause performance and maintenance issues';
        this.severity = types_1.Severity.LOW;
        this.category = types_1.VulnerabilityCategory.BEST_PRACTICE_VIOLATION;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        if (sql.includes('select *')) {
            vulnerabilities.push(this.createVulnerability(query, 'SELECT * used instead of specific columns', 'Specify only the columns you need'));
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.BEST_PRACTICE_VIOLATION,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.8,
            category: this.category
        };
    }
}
// Hardcoded Credentials Rule
class HardcodedCredentialsRule {
    constructor() {
        this.id = 'HARDCODED_CREDENTIALS';
        this.name = 'Hardcoded Credentials';
        this.description = 'Potential hardcoded credentials detected';
        this.severity = types_1.Severity.HIGH;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text;
        // Check for password-like patterns
        const passwordPatterns = [
            /password\s*=\s*['"]\w+['"]/gi,
            /pwd\s*=\s*['"]\w+['"]/gi,
            /secret\s*=\s*['"]\w+['"]/gi
        ];
        for (const pattern of passwordPatterns) {
            if (pattern.test(sql)) {
                vulnerabilities.push(this.createVulnerability(query, 'Potential hardcoded password detected', 'Use parameterized queries or environment variables for credentials'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.DATA_EXPOSURE,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.9,
            category: this.category
        };
    }
}
// Data Exposure Rule
class DataExposureRule {
    constructor() {
        this.id = 'DATA_EXPOSURE';
        this.name = 'Sensitive Data Exposure';
        this.description = 'Query may expose sensitive data';
        this.severity = types_1.Severity.HIGH;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        // Check for sensitive column names
        const sensitiveColumns = [
            'password', 'passwd', 'pwd', 'secret', 'token', 'key',
            'ssn', 'social_security', 'credit_card', 'cc_number',
            'email', 'phone', 'address', 'salary'
        ];
        for (const column of sensitiveColumns) {
            if (sql.includes(column)) {
                vulnerabilities.push(this.createVulnerability(query, `Sensitive column detected: ${column}`, 'Ensure proper access controls and data masking for sensitive information'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.DATA_EXPOSURE,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.7,
            category: this.category
        };
    }
}
// Permission Rule
class PermissionRule {
    constructor() {
        this.id = 'PERMISSION_ISSUE';
        this.name = 'Permission Issue';
        this.description = 'Query may violate principle of least privilege';
        this.severity = types_1.Severity.MEDIUM;
        this.category = types_1.VulnerabilityCategory.SECURITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        // Check for administrative operations
        const adminOperations = [
            'drop table', 'truncate table', 'delete from', 'grant all',
            'revoke all', 'create user', 'drop user'
        ];
        for (const operation of adminOperations) {
            if (sql.includes(operation)) {
                vulnerabilities.push(this.createVulnerability(query, `Administrative operation detected: ${operation}`, 'Ensure proper authorization checks for administrative operations'));
            }
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.PERMISSION_ISSUE,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.6,
            category: this.category
        };
    }
}
// Best Practice Rule
class BestPracticeRule {
    constructor() {
        this.id = 'BEST_PRACTICE';
        this.name = 'Best Practice Violation';
        this.description = 'SQL best practice violation';
        this.severity = types_1.Severity.LOW;
        this.category = types_1.VulnerabilityCategory.MAINTAINABILITY;
        this.databaseTypes = ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'];
        this.queryTypes = ['SELECT', 'INSERT', 'UPDATE', 'DELETE'];
    }
    async analyze(query, context) {
        const vulnerabilities = [];
        const sql = query.text.toLowerCase();
        // Check for inconsistent naming
        if (sql.match(/[a-z][a-z_]*[a-z]/) && sql.match(/[A-Z][A-Z_]*[A-Z]/)) {
            vulnerabilities.push(this.createVulnerability(query, 'Inconsistent naming convention detected', 'Use consistent naming convention (camelCase or snake_case)'));
        }
        // Check for missing error handling
        if (sql.includes('begin') && !sql.includes('exception') && !sql.includes('catch')) {
            vulnerabilities.push(this.createVulnerability(query, 'Missing error handling in transaction', 'Add proper error handling for database operations'));
        }
        return vulnerabilities;
    }
    createVulnerability(query, issue, recommendation) {
        return {
            id: `${this.id}_${query.id}`,
            type: types_1.VulnerabilityType.BEST_PRACTICE_VIOLATION,
            severity: this.severity,
            title: this.name,
            description: `${this.description}: ${issue}`,
            recommendation,
            line: query.line,
            column: query.column,
            filePath: query.filePath,
            sqlQuery: query.text,
            confidence: 0.5,
            category: this.category
        };
    }
}
//# sourceMappingURL=StaticAnalyzer.js.map