import { Server as SocketIOServer } from 'socket.io';
import { SQLVulnerabilityScanner } from '../core/SQLVulnerabilityScanner';
export declare class APIServer {
    private app;
    private httpServer;
    private io;
    private scanner;
    private sqlParser;
    private configManager;
    private securityManager;
    private port;
    private workspaceRoot;
    constructor(port?: number, workspaceRoot?: string);
    private setupMiddleware;
    private setupRoutes;
    private setupWebSocket;
    private setupErrorHandling;
    start(): Promise<void>;
    stop(): Promise<void>;
    getScanner(): SQLVulnerabilityScanner;
    getIO(): SocketIOServer;
}
//# sourceMappingURL=Server.d.ts.map