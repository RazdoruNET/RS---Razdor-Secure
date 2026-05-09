export interface Vulnerability {
    id: string;
    type: VulnerabilityType;
    severity: Severity;
    title: string;
    description: string;
    recommendation: string;
    codeExample?: string;
    cwe?: string;
    owasp?: string;
    line: number;
    column: number;
    filePath: string;
    sqlQuery: string;
    confidence: number;
    category: VulnerabilityCategory;
}
export declare enum VulnerabilityType {
    SQL_INJECTION = "sql_injection",
    PERFORMANCE_ISSUE = "performance_issue",
    BEST_PRACTICE_VIOLATION = "best_practice_violation",
    LOGIC_ERROR = "logic_error",
    DATA_EXPOSURE = "data_exposure",
    PERMISSION_ISSUE = "permission_issue",
    INSECURE_OPERATION = "insecure_operation"
}
export declare enum Severity {
    CRITICAL = "critical",
    HIGH = "high",
    MEDIUM = "medium",
    LOW = "low",
    INFO = "info"
}
export declare enum VulnerabilityCategory {
    SECURITY = "security",
    PERFORMANCE = "performance",
    MAINTAINABILITY = "maintainability",
    RELIABILITY = "reliability",
    BEST_PRACTICE_VIOLATION = "best_practice_violation"
}
export interface SQLQuery {
    id: string;
    text: string;
    type: QueryType;
    line: number;
    column: number;
    filePath: string;
    ast?: any;
    database: DatabaseType;
    parameters?: Parameter[];
}
export declare enum QueryType {
    SELECT = "SELECT",
    INSERT = "INSERT",
    UPDATE = "UPDATE",
    DELETE = "DELETE",
    CREATE = "CREATE",
    ALTER = "ALTER",
    DROP = "DROP",
    TRUNCATE = "TRUNCATE",
    MERGE = "MERGE",
    EXEC = "EXEC",
    UNKNOWN = "UNKNOWN"
}
export declare enum DatabaseType {
    MYSQL = "mysql",
    POSTGRESQL = "postgresql",
    MSSQL = "mssql",
    ORACLE = "oracle",
    SQLITE = "sqlite",
    GENERIC = "generic"
}
export interface Parameter {
    name: string;
    type: string;
    isUserInput: boolean;
    isSanitized: boolean;
    line: number;
    column: number;
}
export interface AnalysisContext {
    filePath: string;
    content: string;
    database: DatabaseType;
    metadata?: DatabaseMetadata;
    applicationContext?: ApplicationContext;
}
export interface DatabaseMetadata {
    tables: TableMetadata[];
    views: ViewMetadata[];
    procedures: ProcedureMetadata[];
    functions: FunctionMetadata[];
}
export interface TableMetadata {
    name: string;
    columns: ColumnMetadata[];
    indexes: IndexMetadata[];
    constraints: ConstraintMetadata[];
}
export interface ColumnMetadata {
    name: string;
    type: string;
    nullable: boolean;
    defaultValue?: string;
    isPrimaryKey: boolean;
    isForeignKey: boolean;
    references?: string;
}
export interface IndexMetadata {
    name: string;
    columns: string[];
    isUnique: boolean;
    isPrimary: boolean;
}
export interface ConstraintMetadata {
    name: string;
    type: 'PRIMARY_KEY' | 'FOREIGN_KEY' | 'UNIQUE' | 'CHECK' | 'NOT_NULL';
    columns: string[];
    references?: string;
}
export interface ViewMetadata {
    name: string;
    definition: string;
    columns: string[];
}
export interface ProcedureMetadata {
    name: string;
    parameters: Parameter[];
    definition: string;
}
export interface FunctionMetadata {
    name: string;
    parameters: Parameter[];
    returnType: string;
    definition: string;
}
export interface ApplicationContext {
    userInputs: UserInput[];
    sessionData: SessionData[];
    config: AppConfig;
}
export interface UserInput {
    name: string;
    source: string;
    type: string;
    validation: ValidationRule[];
    sanitization: SanitizationRule[];
}
export interface ValidationRule {
    type: string;
    pattern?: string;
    minLength?: number;
    maxLength?: number;
    allowedValues?: string[];
}
export interface SanitizationRule {
    type: string;
    method: string;
}
export interface SessionData {
    key: string;
    value: any;
    type: string;
}
export interface AppConfig {
    databaseType: DatabaseType;
    securityLevel: 'strict' | 'moderate' | 'lenient';
    enableGPTAnalysis: boolean;
    enablePerformanceAnalysis: boolean;
    ignoredRules: string[];
    customRules: CustomRule[];
}
export interface CustomRule {
    id: string;
    name: string;
    pattern: string;
    severity: Severity;
    description: string;
    recommendation: string;
}
export interface AnalysisResult {
    vulnerabilities: Vulnerability[];
    statistics: AnalysisStatistics;
    queries: SQLQuery[];
    duration: number;
    context: AnalysisContext;
}
export interface AnalysisStatistics {
    totalQueries: number;
    vulnerabilitiesByType: Record<VulnerabilityType, number>;
    vulnerabilitiesBySeverity: Record<Severity, number>;
    filesAnalyzed: number;
    linesAnalyzed: number;
    coverage: number;
}
export interface GPTAnalysisRequest {
    query: SQLQuery;
    context: AnalysisContext;
    vulnerabilities: Vulnerability[];
}
export interface GPTAnalysisResponse {
    semanticAnalysis: string;
    businessLogic: string;
    risks: string[];
    recommendations: string[];
    confidence: number;
}
export interface ReportConfig {
    format: 'json' | 'html' | 'pdf' | 'jira';
    includeStatistics: boolean;
    includeCodeExamples: boolean;
    groupBy: 'type' | 'severity' | 'file';
    filter: {
        severities?: Severity[];
        types?: VulnerabilityType[];
        files?: string[];
    };
}
export interface IDEIntegration {
    highlightVulnerabilities: (vulnerabilities: Vulnerability[]) => void;
    showTooltip: (vulnerability: Vulnerability) => void;
    openFile: (filePath: string, line: number, column: number) => void;
    showReport: (result: AnalysisResult) => void;
    ignoreVulnerability: (vulnerabilityId: string) => void;
}
//# sourceMappingURL=index.d.ts.map