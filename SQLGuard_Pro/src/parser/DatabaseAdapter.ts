import { DatabaseType, SQLQuery, AnalysisContext } from '../types';

export interface DatabaseAdapter {
  databaseType: DatabaseType;
  parseSQL(sql: string): any;
  validateSQL(sql: string): boolean;
  getDialectSpecificRules(): string[];
  adaptQuery(query: SQLQuery): SQLQuery;
  getSupportedFeatures(): string[];
}

export class MySQLAdapter implements DatabaseAdapter {
  databaseType = DatabaseType.MYSQL;

  parseSQL(sql: string): any {
    // MySQL-specific parsing logic would go here
    return { dialect: 'mysql', sql };
  }

  validateSQL(sql: string): boolean {
    // MySQL-specific validation
    const mysqlPatterns = [
      /LIMIT\s+\d+/i,
      /AUTO_INCREMENT/i,
      /ENGINE\s*=/i
    ];
    return mysqlPatterns.some(pattern => pattern.test(sql)) || true;
  }

  getDialectSpecificRules(): string[] {
    return [
      'MYSQL_GROUP_CONCAT_LIMIT',
      'MYSQL_INDEX_HINTS',
      'MYSQL_ENGINE_SPECIFICATION',
      'MYSQL_AUTO_INCREMENT'
    ];
  }

  adaptQuery(query: SQLQuery): SQLQuery {
    // Adapt MySQL-specific syntax
    let adaptedSQL = query.text;
    
    // Convert LIMIT syntax if needed
    adaptedSQL = adaptedSQL.replace(/LIMIT\s+(\d+),\s*(\d+)/gi, 'LIMIT $2 OFFSET $1');
    
    return {
      ...query,
      text: adaptedSQL,
      database: DatabaseType.MYSQL
    };
  }

  getSupportedFeatures(): string[] {
    return [
      'CTE',
      'Window Functions',
      'JSON Functions',
      'Stored Procedures',
      'Triggers',
      'Views',
      'Indexes'
    ];
  }
}

export class PostgreSQLAdapter implements DatabaseAdapter {
  databaseType = DatabaseType.POSTGRESQL;

  parseSQL(sql: string): any {
    return { dialect: 'postgresql', sql };
  }

  validateSQL(sql: string): boolean {
    const postgresPatterns = [
      /ILIKE/i,
      /::text/i,
      /ARRAY\[.*\]/i,
      /JSONB/i
    ];
    return postgresPatterns.some(pattern => pattern.test(sql)) || true;
  }

  getDialectSpecificRules(): string[] {
    return [
      'POSTGRES_ILIKE_WILDCARD',
      'POSTGRES_ARRAY_OPERATORS',
      'POSTGRES_JSONB_USAGE',
      'POSTGRES_TRUNCATE_CASCADE'
    ];
  }

  adaptQuery(query: SQLQuery): SQLQuery {
    let adaptedSQL = query.text;
    
    // Adapt PostgreSQL-specific syntax
    adaptedSQL = adaptedSQL.replace(/ILIKE/gi, 'LIKE');
    
    return {
      ...query,
      text: adaptedSQL,
      database: DatabaseType.POSTGRESQL
    };
  }

  getSupportedFeatures(): string[] {
    return [
      'CTE',
      'Window Functions',
      'JSON/JSONB',
      'Arrays',
      'Stored Procedures',
      'Triggers',
      'Views',
      'Indexes',
      'Full Text Search'
    ];
  }
}

export class MSSQLAdapter implements DatabaseAdapter {
  databaseType = DatabaseType.MSSQL;

  parseSQL(sql: string): any {
    return { dialect: 'mssql', sql };
  }

  validateSQL(sql: string): boolean {
    const mssqlPatterns = [
      /TOP\s+\d+/i,
      /sp_executesql/i,
      /N'/i,
      /IDENTITY/i
    ];
    return mssqlPatterns.some(pattern => pattern.test(sql)) || true;
  }

  getDialectSpecificRules(): string[] {
    return [
      'MSSQL_TOP_ORDERBY',
      'MSSQL_DYNAMIC_SQL',
      'MSSQL_SP_EXECUTE',
      'MSSQL_IDENTITY_INSERT'
    ];
  }

  adaptQuery(query: SQLQuery): SQLQuery {
    let adaptedSQL = query.text;
    
    // Convert TOP to LIMIT equivalent for analysis
    adaptedSQL = adaptedSQL.replace(/TOP\s+(\d+)/gi, 'LIMIT $1');
    
    return {
      ...query,
      text: adaptedSQL,
      database: DatabaseType.MSSQL
    };
  }

  getSupportedFeatures(): string[] {
    return [
      'CTE',
      'Window Functions',
      'JSON',
      'Stored Procedures',
      'Triggers',
      'Views',
      'Indexes',
      'Full Text Search'
    ];
  }
}

export class OracleAdapter implements DatabaseAdapter {
  databaseType = DatabaseType.ORACLE;

  parseSQL(sql: string): any {
    return { dialect: 'oracle', sql };
  }

  validateSQL(sql: string): boolean {
    const oraclePatterns = [
      /ROWNUM/i,
      /DUAL/i,
      /CONNECT BY/i,
      /NVL/i
    ];
    return oraclePatterns.some(pattern => pattern.test(sql)) || true;
  }

  getDialectSpecificRules(): string[] {
    return [
      'ORACLE_ROWNUM_ORDERBY',
      'ORACLE_DUAL_TABLE',
      'ORACLE_CONNECT_BY',
      'ORACLE_NVL_COALESCE'
    ];
  }

  adaptQuery(query: SQLQuery): SQLQuery {
    let adaptedSQL = query.text;
    
    // Convert ROWNUM to LIMIT equivalent for analysis
    adaptedSQL = adaptedSQL.replace(/WHERE ROWNUM <= (\d+)/gi, 'LIMIT $1');
    
    return {
      ...query,
      text: adaptedSQL,
      database: DatabaseType.ORACLE
    };
  }

  getSupportedFeatures(): string[] {
    return [
      'CTE',
      'Window Functions',
      'JSON',
      'Stored Procedures',
      'Triggers',
      'Views',
      'Indexes',
      'Materialized Views'
    ];
  }
}

export class SQLiteAdapter implements DatabaseAdapter {
  databaseType = DatabaseType.SQLITE;

  parseSQL(sql: string): any {
    return { dialect: 'sqlite', sql };
  }

  validateSQL(sql: string): boolean {
    const sqlitePatterns = [
      /AUTOINCREMENT/i,
      /INTEGER PRIMARY KEY/i,
      /WITHOUT ROWID/i
    ];
    return sqlitePatterns.some(pattern => pattern.test(sql)) || true;
  }

  getDialectSpecificRules(): string[] {
    return [
      'SQLITE_AUTOINCREMENT',
      'SQLITE_WITHOUT_ROWID',
      'SQLITE_LIMITATIONS'
    ];
  }

  adaptQuery(query: SQLQuery): SQLQuery {
    // SQLite uses standard SQL, minimal adaptation needed
    return {
      ...query,
      database: DatabaseType.SQLITE
    };
  }

  getSupportedFeatures(): string[] {
    return [
      'CTE',
      'Window Functions',
      'JSON',
      'Views',
      'Indexes'
    ];
  }
}

export class DatabaseAdapterFactory {
  static createAdapter(databaseType: DatabaseType): DatabaseAdapter {
    switch (databaseType) {
      case DatabaseType.MYSQL:
        return new MySQLAdapter();
      case DatabaseType.POSTGRESQL:
        return new PostgreSQLAdapter();
      case DatabaseType.MSSQL:
        return new MSSQLAdapter();
      case DatabaseType.ORACLE:
        return new OracleAdapter();
      case DatabaseType.SQLITE:
        return new SQLiteAdapter();
      case DatabaseType.GENERIC:
      default:
        return new SQLiteAdapter(); // Use SQLite as generic fallback
    }
  }

  static getSupportedDatabases(): DatabaseType[] {
    return [
      DatabaseType.MYSQL,
      DatabaseType.POSTGRESQL,
      DatabaseType.MSSQL,
      DatabaseType.ORACLE,
      DatabaseType.SQLITE,
      DatabaseType.GENERIC
    ];
  }

  static detectDatabaseType(sql: string): DatabaseType {
    const lowerSQL = sql.toLowerCase();

    if (lowerSQL.includes('limit ') && lowerSQL.includes('auto_increment')) {
      return DatabaseType.MYSQL;
    }
    if (lowerSQL.includes('ilike') || lowerSQL.includes('jsonb') || lowerSQL.includes('::')) {
      return DatabaseType.POSTGRESQL;
    }
    if (lowerSQL.includes('top ') && lowerSQL.includes('sp_executesql')) {
      return DatabaseType.MSSQL;
    }
    if (lowerSQL.includes('rownum') || lowerSQL.includes('from dual')) {
      return DatabaseType.ORACLE;
    }
    if (lowerSQL.includes('autoincrement')) {
      return DatabaseType.SQLITE;
    }

    return DatabaseType.GENERIC;
  }
}
