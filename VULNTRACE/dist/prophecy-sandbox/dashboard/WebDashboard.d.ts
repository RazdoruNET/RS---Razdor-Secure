import { SandboxExecution, MaliciousSample, LearningMetrics } from '../security/types';
import { AccessControlSystem } from '../access-control/AccessControlSystem';
import { EventEmitter } from 'events';
export interface DashboardConfig {
    port: number;
    host: string;
    enableRealTimeUpdates: boolean;
    enableCharts: boolean;
    maxHistoryItems: number;
    refreshInterval: number;
}
export interface DashboardData {
    activeExecutions: SandboxExecution[];
    recentSamples: MaliciousSample[];
    threatTrends: ThreatTrend[];
    learningMetrics: LearningMetrics;
    systemStatus: SystemStatus;
    alerts: SecurityAlert[];
}
export interface ThreatTrend {
    timestamp: string;
    riskScore: number;
    techniqueCount: number;
    anomalyCount: number;
}
export interface SystemStatus {
    sandboxRunning: boolean;
    activeExecutions: number;
    totalSamples: number;
    learningActive: boolean;
    lastUpdate: string;
}
export interface SecurityAlert {
    id: string;
    timestamp: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    title: string;
    message: string;
    acknowledged: boolean;
}
export declare class WebDashboard extends EventEmitter {
    private config;
    private accessControl;
    private app;
    private server;
    private io;
    private dashboardData;
    private updateTimer?;
    constructor(config: DashboardConfig, accessControl: AccessControlSystem);
    private setupExpress;
    private authenticateMiddleware;
    private setupRoutes;
    private serveDashboard;
    private getStatus;
    private getExecutions;
    private getExecution;
    private getSamples;
    private getAnalytics;
    private getAlerts;
    private acknowledgeAlert;
    private getMetrics;
    private getThreatTrends;
    private initializeData;
    start(): Promise<void>;
    private setupSocketIO;
    private startPeriodicUpdates;
    private updateDashboardData;
    private cleanupOldData;
    updateExecution(execution: SandboxExecution): void;
    updateSample(sample: MaliciousSample): void;
    updateMetrics(metrics: LearningMetrics): void;
    addAlert(alert: Omit<SecurityAlert, 'id'>): void;
    private checkForAlerts;
    stop(): Promise<void>;
    getDashboardData(): DashboardData;
}
//# sourceMappingURL=WebDashboard.d.ts.map