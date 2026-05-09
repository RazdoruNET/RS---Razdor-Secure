"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DatabaseAdapterFactory = exports.SQLiteAdapter = exports.OracleAdapter = exports.MSSQLAdapter = exports.PostgreSQLAdapter = exports.MySQLAdapter = void 0;
const types_1 = require("../types");
class MySQLAdapter {
    constructor() {
        this.databaseType = types_1.DatabaseType.MYSQL;
    }
    parseSQL(sql) {
        // MySQL-specific parsing logic would go here
        return { dialect: 'mysql', sql };
    }
    validateSQL(sql) {
        // MySQL-specific validation
        const mysqlPatterns = [
            /LIMIT\s+\d+/i,
            /AUTO_INCREMENT/i,
            /ENGINE\s*=/i
        ];
        return mysqlPatterns.some(pattern => pattern.test(sql)) || true;
    }
    getDialectSpecificRules() {
        return [
            'MYSQL_GROUP_CONCAT_LIMIT',
            'MYSQL_INDEX_HINTS',
            'MYSQL_ENGINE_SPECIFICATION',
            'MYSQL_AUTO_INCREMENT'
        ];
    }
    adaptQuery(query) {
        // Adapt MySQL-specific syntax
        let adaptedSQL = query.text;
        // Convert LIMIT syntax if needed
        adaptedSQL = adaptedSQL.replace(/LIMIT\s+(\d+),\s*(\d+)/gi, 'LIMIT $2 OFFSET $1');
        return {
            ...query,
            text: adaptedSQL,
            database: types_1.DatabaseType.MYSQL
        };
    }
    getSupportedFeatures() {
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
exports.MySQLAdapter = MySQLAdapter;
class PostgreSQLAdapter {
    constructor() {
        this.databaseType = types_1.DatabaseType.POSTGRESQL;
    }
    parseSQL(sql) {
        return { dialect: 'postgresql', sql };
    }
    validateSQL(sql) {
        const postgresPatterns = [
            /ILIKE/i,
            /::text/i,
            /ARRAY\[.*\]/i,
            /JSONB/i
        ];
        return postgresPatterns.some(pattern => pattern.test(sql)) || true;
    }
    getDialectSpecificRules() {
        return [
            'POSTGRES_ILIKE_WILDCARD',
            'POSTGRES_ARRAY_OPERATORS',
            'POSTGRES_JSONB_USAGE',
            'POSTGRES_TRUNCATE_CASCADE'
        ];
    }
    adaptQuery(query) {
        let adaptedSQL = query.text;
        // Adapt PostgreSQL-specific syntax
        adaptedSQL = adaptedSQL.replace(/ILIKE/gi, 'LIKE');
        return {
            ...query,
            text: adaptedSQL,
            database: types_1.DatabaseType.POSTGRESQL
        };
    }
    getSupportedFeatures() {
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
exports.PostgreSQLAdapter = PostgreSQLAdapter;
class MSSQLAdapter {
    constructor() {
        this.databaseType = types_1.DatabaseType.MSSQL;
    }
    parseSQL(sql) {
        return { dialect: 'mssql', sql };
    }
    validateSQL(sql) {
        const mssqlPatterns = [
            /TOP\s+\d+/i,
            /sp_executesql/i,
            /N'/i,
            /IDENTITY/i
        ];
        return mssqlPatterns.some(pattern => pattern.test(sql)) || true;
    }
    getDialectSpecificRules() {
        return [
            'MSSQL_TOP_ORDERBY',
            'MSSQL_DYNAMIC_SQL',
            'MSSQL_SP_EXECUTE',
            'MSSQL_IDENTITY_INSERT'
        ];
    }
    adaptQuery(query) {
        let adaptedSQL = query.text;
        // Convert TOP to LIMIT equivalent for analysis
        adaptedSQL = adaptedSQL.replace(/TOP\s+(\d+)/gi, 'LIMIT $1');
        return {
            ...query,
            text: adaptedSQL,
            database: types_1.DatabaseType.MSSQL
        };
    }
    getSupportedFeatures() {
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
exports.MSSQLAdapter = MSSQLAdapter;
class OracleAdapter {
    constructor() {
        this.databaseType = types_1.DatabaseType.ORACLE;
    }
    parseSQL(sql) {
        return { dialect: 'oracle', sql };
    }
    validateSQL(sql) {
        const oraclePatterns = [
            /ROWNUM/i,
            /DUAL/i,
            /CONNECT BY/i,
            /NVL/i
        ];
        return oraclePatterns.some(pattern => pattern.test(sql)) || true;
    }
    getDialectSpecificRules() {
        return [
            'ORACLE_ROWNUM_ORDERBY',
            'ORACLE_DUAL_TABLE',
            'ORACLE_CONNECT_BY',
            'ORACLE_NVL_COALESCE'
        ];
    }
    adaptQuery(query) {
        let adaptedSQL = query.text;
        // Convert ROWNUM to LIMIT equivalent for analysis
        adaptedSQL = adaptedSQL.replace(/WHERE ROWNUM <= (\d+)/gi, 'LIMIT $1');
        return {
            ...query,
            text: adaptedSQL,
            database: types_1.DatabaseType.ORACLE
        };
    }
    getSupportedFeatures() {
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
exports.OracleAdapter = OracleAdapter;
class SQLiteAdapter {
    constructor() {
        this.databaseType = types_1.DatabaseType.SQLITE;
    }
    parseSQL(sql) {
        return { dialect: 'sqlite', sql };
    }
    validateSQL(sql) {
        const sqlitePatterns = [
            /AUTOINCREMENT/i,
            /INTEGER PRIMARY KEY/i,
            /WITHOUT ROWID/i
        ];
        return sqlitePatterns.some(pattern => pattern.test(sql)) || true;
    }
    getDialectSpecificRules() {
        return [
            'SQLITE_AUTOINCREMENT',
            'SQLITE_WITHOUT_ROWID',
            'SQLITE_LIMITATIONS'
        ];
    }
    adaptQuery(query) {
        // SQLite uses standard SQL, minimal adaptation needed
        return {
            ...query,
            database: types_1.DatabaseType.SQLITE
        };
    }
    getSupportedFeatures() {
        return [
            'CTE',
            'Window Functions',
            'JSON',
            'Views',
            'Indexes'
        ];
    }
}
exports.SQLiteAdapter = SQLiteAdapter;
class DatabaseAdapterFactory {
    static createAdapter(databaseType) {
        switch (databaseType) {
            case types_1.DatabaseType.MYSQL:
                return new MySQLAdapter();
            case types_1.DatabaseType.POSTGRESQL:
                return new PostgreSQLAdapter();
            case types_1.DatabaseType.MSSQL:
                return new MSSQLAdapter();
            case types_1.DatabaseType.ORACLE:
                return new OracleAdapter();
            case types_1.DatabaseType.SQLITE:
                return new SQLiteAdapter();
            case types_1.DatabaseType.GENERIC:
            default:
                return new SQLiteAdapter(); // Use SQLite as generic fallback
        }
    }
    static getSupportedDatabases() {
        return [
            types_1.DatabaseType.MYSQL,
            types_1.DatabaseType.POSTGRESQL,
            types_1.DatabaseType.MSSQL,
            types_1.DatabaseType.ORACLE,
            types_1.DatabaseType.SQLITE,
            types_1.DatabaseType.GENERIC
        ];
    }
    static detectDatabaseType(sql) {
        const lowerSQL = sql.toLowerCase();
        if (lowerSQL.includes('limit ') && lowerSQL.includes('auto_increment')) {
            return types_1.DatabaseType.MYSQL;
        }
        if (lowerSQL.includes('ilike') || lowerSQL.includes('jsonb') || lowerSQL.includes('::')) {
            return types_1.DatabaseType.POSTGRESQL;
        }
        if (lowerSQL.includes('top ') && lowerSQL.includes('sp_executesql')) {
            return types_1.DatabaseType.MSSQL;
        }
        if (lowerSQL.includes('rownum') || lowerSQL.includes('from dual')) {
            return types_1.DatabaseType.ORACLE;
        }
        if (lowerSQL.includes('autoincrement')) {
            return types_1.DatabaseType.SQLITE;
        }
        return types_1.DatabaseType.GENERIC;
    }
}
exports.DatabaseAdapterFactory = DatabaseAdapterFactory;
//# sourceMappingURL=DatabaseAdapter.js.map