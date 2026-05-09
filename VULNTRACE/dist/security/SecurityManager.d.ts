import { SecurityConfig, SecurityContext } from './types';
import { AuditLogger } from './AuditLogger';
export declare class SecurityManager {
    private config;
    private ethicalUsageManager;
    private auditLogger;
    private workspaceRoot;
    constructor(workspaceRoot: string, config: SecurityConfig);
    initialize(): Promise<boolean>;
    validateAccess(filePath: string): SecurityContext;
    confirmAnalysis(context: SecurityContext): Promise<boolean>;
    private promptUser;
    private isPathTrusted;
    private logSecurityViolation;
    blockExternalRequest(url: string): boolean;
    ensureReadOnly(): boolean;
    logAnalysisStart(filePath: string): Promise<void>;
    logAnalysisComplete(filePath: string, queryCount: number, vulnerabilityCount: number, duration: number): Promise<void>;
    logFileAnalyzed(filePath: string, fileSize: number): Promise<void>;
    logVulnerabilityFound(filePath: string): Promise<void>;
    getAuditLogger(): AuditLogger;
    updateConfig(config: Partial<SecurityConfig>): void;
    getConfig(): SecurityConfig;
    getEthicalGuidelines(): string[];
    shutdown(): Promise<void>;
}
//# sourceMappingURL=SecurityManager.d.ts.map