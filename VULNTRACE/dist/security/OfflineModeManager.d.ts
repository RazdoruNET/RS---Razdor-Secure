import { NetworkRequest } from './NetworkMonitor';
export declare class OfflineModeManager {
    private static instance;
    private networkMonitor;
    private offlineMode;
    private constructor();
    static getInstance(): OfflineModeManager;
    enableOfflineMode(): void;
    disableOfflineMode(): void;
    isOfflineMode(): boolean;
    getBlockedRequests(): NetworkRequest[];
    clearBlockedRequestsLog(): void;
    validateLocalFile(filePath: string): boolean;
    validateLocalDirectory(dirPath: string): boolean;
    ensureLocalExecution(): void;
    checkForExternalDependencies(code: string): Promise<string[]>;
    generateSecurityReport(): {
        offlineMode: boolean;
        blockedRequestsCount: number;
        blockedRequests: NetworkRequest[];
        timestamp: string;
    };
    getHttpWrapper(): typeof import("http").request;
    getHttpsWrapper(): typeof import("https").request;
    getFetchWrapper(): typeof fetch;
}
//# sourceMappingURL=OfflineModeManager.d.ts.map