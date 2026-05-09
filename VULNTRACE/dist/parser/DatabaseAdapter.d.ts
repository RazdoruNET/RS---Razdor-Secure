import { DatabaseType, SQLQuery } from '../types';
export interface DatabaseAdapter {
    databaseType: DatabaseType;
    parseSQL(sql: string): any;
    validateSQL(sql: string): boolean;
    getDialectSpecificRules(): string[];
    adaptQuery(query: SQLQuery): SQLQuery;
    getSupportedFeatures(): string[];
}
export declare class MySQLAdapter implements DatabaseAdapter {
    databaseType: any;
    parseSQL(sql: string): any;
    validateSQL(sql: string): boolean;
    getDialectSpecificRules(): string[];
    adaptQuery(query: SQLQuery): SQLQuery;
    getSupportedFeatures(): string[];
}
export declare class PostgreSQLAdapter implements DatabaseAdapter {
    databaseType: any;
    parseSQL(sql: string): any;
    validateSQL(sql: string): boolean;
    getDialectSpecificRules(): string[];
    adaptQuery(query: SQLQuery): SQLQuery;
    getSupportedFeatures(): string[];
}
export declare class MSSQLAdapter implements DatabaseAdapter {
    databaseType: any;
    parseSQL(sql: string): any;
    validateSQL(sql: string): boolean;
    getDialectSpecificRules(): string[];
    adaptQuery(query: SQLQuery): SQLQuery;
    getSupportedFeatures(): string[];
}
export declare class OracleAdapter implements DatabaseAdapter {
    databaseType: any;
    parseSQL(sql: string): any;
    validateSQL(sql: string): boolean;
    getDialectSpecificRules(): string[];
    adaptQuery(query: SQLQuery): SQLQuery;
    getSupportedFeatures(): string[];
}
export declare class SQLiteAdapter implements DatabaseAdapter {
    databaseType: any;
    parseSQL(sql: string): any;
    validateSQL(sql: string): boolean;
    getDialectSpecificRules(): string[];
    adaptQuery(query: SQLQuery): SQLQuery;
    getSupportedFeatures(): string[];
}
export declare class DatabaseAdapterFactory {
    static createAdapter(databaseType: DatabaseType): DatabaseAdapter;
    static getSupportedDatabases(): DatabaseType[];
    static detectDatabaseType(sql: string): DatabaseType;
}
//# sourceMappingURL=DatabaseAdapter.d.ts.map