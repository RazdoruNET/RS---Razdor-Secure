import { AnalysisContext, SQLQuery, DatabaseType } from '../types';
import { AppConfig } from '../types';
export declare class SQLParser {
    private parser;
    private config;
    constructor(config: AppConfig);
    parseQueries(context: AnalysisContext): Promise<SQLQuery[]>;
    private extractSQLBlocks;
    private isSQLStart;
    private isSQLEnd;
    private parseSQLBlock;
    private detectQueryType;
    private extractParameters;
    private isLikelyUserInput;
    private findLinePosition;
    private generateQueryId;
    private simpleHash;
    validateSQL(sql: string, databaseType: DatabaseType): boolean;
    extractTableNames(query: SQLQuery): string[];
    extractColumnNames(query: SQLQuery): string[];
}
//# sourceMappingURL=SQLParser.d.ts.map