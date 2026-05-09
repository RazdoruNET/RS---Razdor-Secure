import {
  SQLQuery,
  Vulnerability,
  VulnerabilityType,
  Severity,
  VulnerabilityCategory,
  AnalysisContext,
  AppConfig,
  DatabaseType,
  QueryType,
  AnalysisRule
} from '../types';

export class StaticAnalyzer {
  private config: AppConfig;
  private rules: AnalysisRule[];

  constructor(config: AppConfig) {
    this.config = config;
    this.rules = this.initializeRules();
  }

  async analyze(queries: SQLQuery[], context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];

    for (const query of queries) {
      const queryVulnerabilities = await this.analyzeQuery(query, context);
      vulnerabilities.push(...queryVulnerabilities);
    }

    return this.filterIgnoredRules(vulnerabilities);
  }

  private async analyzeQuery(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];

    for (const rule of this.rules) {
      if (this.shouldApplyRule(rule, query)) {
        const ruleVulnerabilities = await rule.analyze(query, context);
        vulnerabilities.push(...ruleVulnerabilities);
      }
    }

    return vulnerabilities;
  }

  private shouldApplyRule(rule: AnalysisRule, query: SQLQuery): boolean {
    return rule.databaseTypes.includes(query.database) &&
           rule.queryTypes.includes(query.type);
  }

  private filterIgnoredRules(vulnerabilities: Vulnerability[]): Vulnerability[] {
    return vulnerabilities.filter(vuln => 
      !this.config.ignoredRules.includes(vuln.id)
    );
  }

  private initializeRules(): AnalysisRule[] {
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

// SQL Injection Detection Rule
class SQLInjectionRule implements AnalysisRule {
  id = 'SQL_INJECTION';
  name = 'SQL Injection Vulnerability';
  description = 'Potential SQL injection vulnerability detected';
  severity = Severity.CRITICAL;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
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
        vulnerabilities.push(this.createVulnerability(query, 
          `String concatenation detected: ${matches[0]}`,
          'Use parameterized queries instead of string concatenation'
        ));
      }
    }

    // Check for unsafe functions
    const unsafeFunctions = [
      'exec', 'execute', 'sp_executesql', 'eval', 'system'
    ];

    for (const func of unsafeFunctions) {
      if (sql.includes(func)) {
        vulnerabilities.push(this.createVulnerability(query,
          `Unsafe function detected: ${func}`,
          'Avoid using dynamic SQL execution functions'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.SQL_INJECTION,
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
class DynamicSQLRule implements AnalysisRule {
  id = 'DYNAMIC_SQL';
  name = 'Dynamic SQL Construction';
  description = 'Dynamic SQL detected without proper validation';
  severity = Severity.HIGH;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE, QueryType.EXEC];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    const dynamicPatterns = [
      /exec\s*\(/gi,
      /execute\s*immediate/gi,
      /sp_executesql/gi,
      /prepare\s+.*\s+from/gi
    ];

    for (const pattern of dynamicPatterns) {
      if (pattern.test(sql)) {
        vulnerabilities.push(this.createVulnerability(query,
          'Dynamic SQL construction detected',
          'Ensure proper input validation and parameterization for dynamic SQL'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.SQL_INJECTION,
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
class ConcatenationRule implements AnalysisRule {
  id = 'STRING_CONCATENATION';
  name = 'String Concatenation in SQL';
  description = 'String concatenation used in SQL query';
  severity = Severity.MEDIUM;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text;

    // Check for concatenation operators
    const concatOperators = [/\+/, /\|\|/, /concat\s*\(/gi];

    for (const operator of concatOperators) {
      if (operator.test(sql)) {
        vulnerabilities.push(this.createVulnerability(query,
          'String concatenation operator detected',
          'Use parameterized queries instead of string concatenation'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.SQL_INJECTION,
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
class UnparameterizedQueryRule implements AnalysisRule {
  id = 'UNPARAMETERIZED_QUERY';
  name = 'Unparameterized Query';
  description = 'Query uses literal values instead of parameters';
  severity = Severity.MEDIUM;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];

    if (!query.parameters || query.parameters.length === 0) {
      // Check if query contains literal values that could be parameters
      const literalPattern = /'(.*?)'/g;
      const matches = query.text.match(literalPattern);
      
      if (matches && matches.length > 2) { // More than 2 literals might indicate missing parameters
        vulnerabilities.push(this.createVulnerability(query,
          'Multiple literal values found - consider using parameters',
          'Use parameterized queries for better security and performance'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.SQL_INJECTION,
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
class PerformanceRule implements AnalysisRule {
  id = 'PERFORMANCE_ISSUE';
  name = 'Performance Issue';
  description = 'Query performance issue detected';
  severity = Severity.MEDIUM;
  category = VulnerabilityCategory.PERFORMANCE;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    // Check for SELECT * without LIMIT
    if (sql.includes('select *') && !sql.includes('limit') && !sql.includes('top')) {
      vulnerabilities.push(this.createVulnerability(query,
        'SELECT * without LIMIT or TOP clause',
        'Specify only needed columns and add LIMIT clause'
      ));
    }

    // Check for missing WHERE clause
    if (sql.includes('select') && !sql.includes('where') && !sql.includes('limit')) {
      vulnerabilities.push(this.createVulnerability(query,
        'Missing WHERE clause in SELECT statement',
        'Add WHERE clause to limit result set'
      ));
    }

    // Check for suboptimal JOIN patterns
    if (sql.includes('join') && sql.includes('select *')) {
      vulnerabilities.push(this.createVulnerability(query,
        'SELECT * with JOIN may be inefficient',
        'Specify specific columns instead of SELECT *'
      ));
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.PERFORMANCE_ISSUE,
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
class MissingIndexRule implements AnalysisRule {
  id = 'MISSING_INDEX';
  name = 'Potential Missing Index';
  description = 'Query may benefit from an index';
  severity = Severity.LOW;
  category = VulnerabilityCategory.PERFORMANCE;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE];
  queryTypes = [QueryType.SELECT];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    // Check for ORDER BY without index hint
    if (sql.includes('order by') && !sql.includes('index')) {
      vulnerabilities.push(this.createVulnerability(query,
        'ORDER BY clause may benefit from index',
        'Consider adding an index on ORDER BY columns'
      ));
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.PERFORMANCE_ISSUE,
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
class SelectAllRule implements AnalysisRule {
  id = 'SELECT_ALL';
  name = 'SELECT * Usage';
  description = 'SELECT * can cause performance and maintenance issues';
  severity = Severity.LOW;
  category = VulnerabilityCategory.BEST_PRACTICE_VIOLATION;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    if (sql.includes('select *')) {
      vulnerabilities.push(this.createVulnerability(query,
        'SELECT * used instead of specific columns',
        'Specify only the columns you need'
      ));
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.BEST_PRACTICE_VIOLATION,
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
class HardcodedCredentialsRule implements AnalysisRule {
  id = 'HARDCODED_CREDENTIALS';
  name = 'Hardcoded Credentials';
  description = 'Potential hardcoded credentials detected';
  severity = Severity.HIGH;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text;

    // Check for password-like patterns
    const passwordPatterns = [
      /password\s*=\s*['"]\w+['"]/gi,
      /pwd\s*=\s*['"]\w+['"]/gi,
      /secret\s*=\s*['"]\w+['"]/gi
    ];

    for (const pattern of passwordPatterns) {
      if (pattern.test(sql)) {
        vulnerabilities.push(this.createVulnerability(query,
          'Potential hardcoded password detected',
          'Use parameterized queries or environment variables for credentials'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.DATA_EXPOSURE,
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
class DataExposureRule implements AnalysisRule {
  id = 'DATA_EXPOSURE';
  name = 'Sensitive Data Exposure';
  description = 'Query may expose sensitive data';
  severity = Severity.HIGH;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    // Check for sensitive column names
    const sensitiveColumns = [
      'password', 'passwd', 'pwd', 'secret', 'token', 'key',
      'ssn', 'social_security', 'credit_card', 'cc_number',
      'email', 'phone', 'address', 'salary'
    ];

    for (const column of sensitiveColumns) {
      if (sql.includes(column)) {
        vulnerabilities.push(this.createVulnerability(query,
          `Sensitive column detected: ${column}`,
          'Ensure proper access controls and data masking for sensitive information'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.DATA_EXPOSURE,
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
class PermissionRule implements AnalysisRule {
  id = 'PERMISSION_ISSUE';
  name = 'Permission Issue';
  description = 'Query may violate principle of least privilege';
  severity = Severity.MEDIUM;
  category = VulnerabilityCategory.SECURITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    // Check for administrative operations
    const adminOperations = [
      'drop table', 'truncate table', 'delete from', 'grant all',
      'revoke all', 'create user', 'drop user'
    ];

    for (const operation of adminOperations) {
      if (sql.includes(operation)) {
        vulnerabilities.push(this.createVulnerability(query,
          `Administrative operation detected: ${operation}`,
          'Ensure proper authorization checks for administrative operations'
        ));
      }
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.PERMISSION_ISSUE,
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
class BestPracticeRule implements AnalysisRule {
  id = 'BEST_PRACTICE';
  name = 'Best Practice Violation';
  description = 'SQL best practice violation';
  severity = Severity.LOW;
  category = VulnerabilityCategory.MAINTAINABILITY;
  databaseTypes = [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.MSSQL, DatabaseType.ORACLE, DatabaseType.SQLITE];
  queryTypes = [QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE];

  async analyze(query: SQLQuery, context: AnalysisContext): Promise<Vulnerability[]> {
    const vulnerabilities: Vulnerability[] = [];
    const sql = query.text.toLowerCase();

    // Check for inconsistent naming
    if (sql.match(/[a-z][a-z_]*[a-z]/) && sql.match(/[A-Z][A-Z_]*[A-Z]/)) {
      vulnerabilities.push(this.createVulnerability(query,
        'Inconsistent naming convention detected',
        'Use consistent naming convention (camelCase or snake_case)'
      ));
    }

    // Check for missing error handling
    if (sql.includes('begin') && !sql.includes('exception') && !sql.includes('catch')) {
      vulnerabilities.push(this.createVulnerability(query,
        'Missing error handling in transaction',
        'Add proper error handling for database operations'
      ));
    }

    return vulnerabilities;
  }

  private createVulnerability(query: SQLQuery, issue: string, recommendation: string): Vulnerability {
    return {
      id: `${this.id}_${query.id}`,
      type: VulnerabilityType.BEST_PRACTICE_VIOLATION,
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
