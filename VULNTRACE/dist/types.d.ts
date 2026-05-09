export interface SQLQuery {
    query: string;
    startLine: number;
    endLine: number;
    type: string;
    parameters?: string[];
}
export interface Vulnerability {
    id: string;
    type: VulnerabilityType;
    severity: Severity;
    title: string;
    description: string;
    line: number;
    column: number;
    recommendation: string;
    cwe?: string;
    owasp?: string;
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
export interface AnalysisContext {
    filePath: string;
    content: string;
    database: string;
}
export interface AnalysisResult {
    content: string;
    queries: SQLQuery[];
    vulnerabilities: Vulnerability[];
    analysisType: 'static' | 'gpt' | 'combined';
    duration: number;
    metadata: {
        workspaceRoot: string;
        userAgent: string;
        version: string;
    };
}
export interface AppConfig {
    databaseType: string;
    enableGPTAnalysis: boolean;
    maxFileSize: number;
    timeout: number;
    outputFormat: 'json' | 'html' | 'pdf';
}
//# sourceMappingURL=types.d.ts.map