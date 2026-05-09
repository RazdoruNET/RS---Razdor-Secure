import { SandboxLogEntry, SystemCallRecord, NetworkActivityRecord, FileChangeRecord } from '../../security/types';
import { EventEmitter } from 'events';
export interface MonitorConfig {
    enableStrace: boolean;
    enableNetworkMonitor: boolean;
    enableFileMonitor: boolean;
    straceOptions: string[];
    networkInterface: string;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
}
export declare class RealTimeMonitor extends EventEmitter {
    private config;
    private straceProcess?;
    private tcpdumpProcess?;
    private inotifyProcess?;
    private isMonitoring;
    private logBuffer;
    private syscallBuffer;
    private networkBuffer;
    private fileBuffer;
    private pcapFilePath;
    private pcapParserInterval?;
    constructor(config: MonitorConfig);
    startMonitoring(containerId: string, executionId: string): Promise<void>;
    stopMonitoring(): Promise<void>;
    private startStraceMonitoring;
    private startNetworkMonitoring;
    private startFileMonitoring;
    private parseStraceOutput;
    private parseSyscallLine;
    private parseSyscallArgs;
    private parseNetworkOutput;
    private extractNetworkActivity;
    private parseFileOutput;
    private parseFileChangeLine;
    private mapEventToAction;
    private calculateFileHash;
    private getFileSize;
    private addLog;
    private flushBuffers;
    getLogs(): SandboxLogEntry[];
    getSyscalls(): SystemCallRecord[];
    getNetworkActivity(): NetworkActivityRecord[];
    getFileChanges(): FileChangeRecord[];
    getMonitoringStats(): {
        logCount: number;
        syscallCount: number;
        networkCount: number;
        fileCount: number;
        isMonitoring: boolean;
    };
    clearBuffers(): void;
}
//# sourceMappingURL=RealTimeMonitor.d.ts.map