import { SandboxConfig, SandboxExecution, MaliciousSample, SandboxLogEntry, SystemCallRecord, NetworkActivityRecord, FileChangeRecord } from '../security/types';
import { EventEmitter } from 'events';
export interface SandboxResources {
    containerId: string;
    tempDir: string;
    networkId?: string;
    volumeId?: string;
}
export interface MonitoringData {
    logs: SandboxLogEntry[];
    systemCalls: SystemCallRecord[];
    networkActivity: NetworkActivityRecord[];
    fileChanges: FileChangeRecord[];
}
export declare class SandboxEnvironment extends EventEmitter {
    private docker;
    private config;
    private activeExecutions;
    private resources;
    private monitors;
    constructor(config: SandboxConfig);
    initialize(): Promise<void>;
    executeSample(sample: MaliciousSample): Promise<SandboxExecution>;
    private setupSandboxResources;
    private createTempDirectory;
    private createContainer;
    private getSampleFileName;
    private getExecutionCommand;
    private runInSandbox;
    private monitorContainer;
    private monitorContainerStats;
    private waitForExecution;
    private createTimeoutPromise;
    private cleanupResources;
    private createIsolatedNetwork;
    private createBaseImage;
    private parseMemoryLimit;
    private parseCpuLimit;
    terminateExecution(executionId: string): Promise<void>;
    getExecution(executionId: string): SandboxExecution | undefined;
    getActiveExecutions(): SandboxExecution[];
    shutdown(): Promise<void>;
}
//# sourceMappingURL=SandboxEnvironment.d.ts.map