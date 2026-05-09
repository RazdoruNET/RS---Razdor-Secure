import * as http from 'http';
import * as https from 'https';
import { EventEmitter } from 'events';
export interface NetworkRequest {
    url: string;
    method: string;
    timestamp: string;
    blocked: boolean;
    reason?: string;
}
export declare class NetworkMonitor extends EventEmitter {
    private blockedRequests;
    private offlineMode;
    private originalHttp;
    private originalHttps;
    private originalFetch;
    constructor();
    enableOfflineMode(): void;
    disableOfflineMode(): void;
    private installWrappers;
    private restoreWrappers;
    isOfflineMode(): boolean;
    wrapHttpRequest(originalRequest: typeof http.request): typeof http.request;
    wrapHttpsRequest(originalRequest: typeof https.request): typeof https.request;
    wrapFetch(originalFetch: typeof global.fetch): typeof global.fetch;
    getHttpWrapper(): typeof http.request;
    getHttpsWrapper(): typeof https.request;
    getFetchWrapper(): typeof global.fetch;
    private extractUrl;
    getBlockedRequests(): NetworkRequest[];
    clearBlockedRequests(): void;
    getSecurityReport(): {
        offlineMode: boolean;
        blockedRequestsCount: number;
        blockedRequests: NetworkRequest[];
        timestamp: string;
    };
    static scanForExternalCalls(code: string): Promise<string[]>;
}
//# sourceMappingURL=NetworkMonitor.d.ts.map