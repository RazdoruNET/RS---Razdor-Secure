"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SQLParser = void 0;
const node_sql_parser_1 = require("node-sql-parser");
const types_1 = require("../types");
class SQLParser {
    constructor(config) {
        this.config = config;
        this.parser = new node_sql_parser_1.Parser();
    }
    async parseQueries(context) {
        const queries = [];
        const lines = context.content.split('\n');
        // Extract SQL queries from the content
        const sqlBlocks = this.extractSQLBlocks(context.content);
        for (const block of sqlBlocks) {
            try {
                const query = await this.parseSQLBlock(block, context.filePath, context.database);
                if (query) {
                    queries.push(query);
                }
            }
            catch (error) {
                // Log parsing error but continue with other queries
                console.warn(`Failed to parse SQL block: ${error}`);
            }
        }
        return queries;
    }
    extractSQLBlocks(content) {
        const blocks = [];
        const lines = content.split('\n');
        let currentSQL = '';
        let startLine = 0;
        let startColumn = 0;
        let inSQL = false;
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            // Detect SQL start patterns
            if (this.isSQLStart(trimmed) && !inSQL) {
                inSQL = true;
                currentSQL = line;
                startLine = i + 1;
                startColumn = line.indexOf(trimmed) + 1;
            }
            else if (inSQL) {
                currentSQL += '\n' + line;
                // Detect SQL end patterns
                if (this.isSQLEnd(trimmed)) {
                    inSQL = false;
                    blocks.push({
                        text: currentSQL.trim(),
                        line: startLine,
                        column: startColumn
                    });
                    currentSQL = '';
                }
            }
        }
        // Add remaining SQL if any
        if (inSQL && currentSQL.trim()) {
            blocks.push({
                text: currentSQL.trim(),
                line: startLine,
                column: startColumn
            });
        }
        return blocks;
    }
    isSQLStart(line) {
        const sqlKeywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
            'TRUNCATE', 'MERGE', 'EXEC', 'EXECUTE', 'WITH', 'DECLARE'
        ];
        return sqlKeywords.some(keyword => line.toUpperCase().startsWith(keyword) &&
            (line.length === keyword.length || line[keyword.length] === ' ' || line[keyword.length] === '('));
    }
    isSQLEnd(line) {
        const trimmed = line.trim();
        return trimmed.endsWith(';') || trimmed.endsWith('END') || trimmed.endsWith('GO');
    }
    async parseSQLBlock(block, filePath, databaseType) {
        try {
            const ast = this.parser.astify(block.text, { database: databaseType });
            const queryType = this.detectQueryType(block.text);
            const query = {
                id: this.generateQueryId(block.text, filePath, block.line),
                text: block.text,
                type: queryType,
                line: block.line,
                column: block.column,
                filePath,
                ast,
                database: databaseType,
                parameters: this.extractParameters(block.text, block.line)
            };
            return query;
        }
        catch (error) {
            // Try to parse as simple text if AST parsing fails
            const queryType = this.detectQueryType(block.text);
            return {
                id: this.generateQueryId(block.text, filePath, block.line),
                text: block.text,
                type: queryType,
                line: block.line,
                column: block.column,
                filePath,
                database: databaseType,
                parameters: this.extractParameters(block.text, block.line)
            };
        }
    }
    detectQueryType(sql) {
        const trimmed = sql.trim().toUpperCase();
        if (trimmed.startsWith('SELECT'))
            return types_1.QueryType.SELECT;
        if (trimmed.startsWith('INSERT'))
            return types_1.QueryType.INSERT;
        if (trimmed.startsWith('UPDATE'))
            return types_1.QueryType.UPDATE;
        if (trimmed.startsWith('DELETE'))
            return types_1.QueryType.DELETE;
        if (trimmed.startsWith('CREATE'))
            return types_1.QueryType.CREATE;
        if (trimmed.startsWith('ALTER'))
            return types_1.QueryType.ALTER;
        if (trimmed.startsWith('DROP'))
            return types_1.QueryType.DROP;
        if (trimmed.startsWith('TRUNCATE'))
            return types_1.QueryType.TRUNCATE;
        if (trimmed.startsWith('MERGE'))
            return types_1.QueryType.MERGE;
        if (trimmed.startsWith('EXEC') || trimmed.startsWith('EXECUTE'))
            return types_1.QueryType.EXEC;
        return types_1.QueryType.UNKNOWN;
    }
    extractParameters(sql, baseLine) {
        const parameters = [];
        // Extract parameter placeholders like @param, :param, ?, etc.
        const paramPatterns = [
            /@(\w+)/g, // SQL Server style
            /:(\w+)/g, // PostgreSQL/Oracle style  
            /\$(\d+)/g, // PostgreSQL positional
            /\?/g, // JDBC style
            /%(\w+)%/g // Some frameworks
        ];
        paramPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(sql)) !== null) {
                const name = match[1] || match[0];
                const position = this.findLinePosition(sql, match.index, baseLine);
                parameters.push({
                    name,
                    type: 'unknown',
                    isUserInput: this.isLikelyUserInput(name, sql),
                    isSanitized: false,
                    line: position.line,
                    column: position.column
                });
            }
        });
        return parameters;
    }
    isLikelyUserInput(paramName, sql) {
        const userInputPatterns = [
            /user/i, /input/i, /data/i, /form/i, /request/i,
            /param/i, /arg/i, /value/i, /search/i, /filter/i
        ];
        return userInputPatterns.some(pattern => pattern.test(paramName)) ||
            sql.toLowerCase().includes('concat') ||
            sql.toLowerCase().includes('||');
    }
    findLinePosition(text, index, baseLine) {
        const beforeIndex = text.substring(0, index);
        const lines = beforeIndex.split('\n');
        return {
            line: baseLine + lines.length - 1,
            column: lines[lines.length - 1].length + 1
        };
    }
    generateQueryId(sql, filePath, line) {
        const hash = this.simpleHash(sql + filePath + line);
        return `query_${hash}`;
    }
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(16);
    }
    // Method to validate SQL syntax
    validateSQL(sql, databaseType) {
        try {
            this.parser.astify(sql, { database: databaseType });
            return true;
        }
        catch {
            return false;
        }
    }
    // Method to get table names from query
    extractTableNames(query) {
        const tables = [];
        if (!query.ast)
            return tables;
        const extractFromAST = (node) => {
            if (!node)
                return;
            if (node.table) {
                tables.push(node.table);
            }
            if (node.from && node.from.table) {
                tables.push(node.from.table);
            }
            if (node.join) {
                if (Array.isArray(node.join)) {
                    node.join.forEach((join) => {
                        if (join.table)
                            tables.push(join.table);
                    });
                }
                else if (node.join.table) {
                    tables.push(node.join.table);
                }
            }
            // Recursively check all properties
            Object.values(node).forEach(value => {
                if (typeof value === 'object') {
                    extractFromAST(value);
                }
            });
        };
        extractFromAST(query.ast);
        return [...new Set(tables)]; // Remove duplicates
    }
    // Method to get column names from query
    extractColumnNames(query) {
        const columns = [];
        if (!query.ast)
            return columns;
        const extractFromAST = (node) => {
            if (!node)
                return;
            if (node.column) {
                columns.push(node.column);
            }
            if (node.columns && Array.isArray(node.columns)) {
                node.columns.forEach((col) => {
                    if (col.column)
                        columns.push(col.column);
                    if (col.expr && col.expr.column)
                        columns.push(col.expr.column);
                });
            }
            Object.values(node).forEach(value => {
                if (typeof value === 'object') {
                    extractFromAST(value);
                }
            });
        };
        extractFromAST(query.ast);
        return [...new Set(columns)];
    }
}
exports.SQLParser = SQLParser;
//# sourceMappingURL=SQLParser.js.map