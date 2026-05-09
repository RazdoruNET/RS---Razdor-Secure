import { EventEmitter } from 'events';
export interface FileSystemEvent {
    type: 'create' | 'modify' | 'delete' | 'move' | 'access';
    path: string;
    oldPath?: string;
    timestamp: Date;
    size?: number;
    permissions?: string;
    uid?: number;
    gid?: number;
    inode?: number;
    hash?: string;
    process?: string;
    pid?: number;
}
export interface MonitorConfig {
    watchPath: string;
    recursive: boolean;
    events: ('create' | 'modify' | 'delete' | 'move' | 'access')[];
    ignorePatterns: string[];
    maxEvents: number;
    bufferSize: number;
    includeHidden: boolean;
    trackProcesses: boolean;
    calculateHashes: boolean;
}
export interface ProcessInfo {
    pid: number;
    name: string;
    command: string;
    user: string;
    startTime: Date;
    parentPid: number;
}
export interface AnomalyDetection {
    type: 'rapid_file_creation' | 'mass_deletion' | 'sensitive_access' | 'unusual_permissions' | 'crypto_activity';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    events: FileSystemEvent[];
    timestamp: Date;
}
export declare class RealFileSystemMonitor extends EventEmitter {
    private config;
    private isMonitoring;
    private eventBuffer;
    private activeProcesses;
    private inotifyProcess;
    private watchTimer;
    private sensitivePaths;
    constructor(config: MonitorConfig);
    private validateConfig;
    startMonitoring(): Promise<void>;
    private startInotifyProcess;
    private processInotifyOutput;
    private createFileSystemEvent;
    private shouldIgnorePath;
    private calculateFileHash;
    private getProcessForFile;
    private handleFileSystemEvent;
    private startPollingFallback;
    private scanDirectory;
    private startProcessTracking;
    private getProcessList;
    private startAnomalyDetection;
    private detectAnomalies;
    private isSensitivePath;
    stopMonitoring(): void;
    getEventHistory(count?: number): FileSystemEvent[];
    getActiveProcesses(): ProcessInfo[];
    getStatistics(): any;
    exportEvents(filePath: string, format?: 'json' | 'csv'): void;
    clearEventBuffer(): void;
    updateConfig(newConfig: Partial<MonitorConfig>): void;
    getMonitorInfo(): any;
    destroy(): void;
}
//# sourceMappingURL=RealFileSystemMonitor.d.ts.map