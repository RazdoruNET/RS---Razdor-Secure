import { AuditLogEntry } from './types';
export declare class AuditLogger {
    private enabled;
    private logPath;
    private workspaceRoot;
    constructor(workspaceRoot: string, enabled?: boolean, logPath?: string);
    logEntry(entry: Omit<AuditLogEntry, 'metadata'>): Promise<void>;
    logScanStart(filePath: string): Promise<void>;
    logScanComplete(filePath: string, queryCount: number, vulnerabilityCount: number, duration: number): Promise<void>;
    logFileAnalyzed(filePath: string, fileSize: number): Promise<void>;
    logVulnerabilityFound(filePath: string): Promise<void>;
    getLogPath(): string;
    isEnabled(): boolean;
    setEnabled(enabled: boolean): void;
    clearLogs(): Promise<void>;
    getLogEntries(limit?: number): Promise<AuditLogEntry[]>;
}
//# sourceMappingURL=AuditLogger.d.ts.map