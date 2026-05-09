import { SecurityConfig, SandboxConfig, MaliciousSample, SandboxExecution } from '../security/types';
import { AccessControlSystem, AccessControlConfig } from './access-control/AccessControlSystem';
import { AnalysisConfig } from './analyzer/ThreatAnalyzer';
import { LearningConfig } from './learning/SelfLearningSystem';
import { WebDashboard, DashboardConfig } from './dashboard/WebDashboard';
import { CLIConfig } from './cli/CLIInterface';
import { EventEmitter } from 'events';
export interface ProphecySandboxConfig {
    enabled: boolean;
    sandbox: SandboxConfig;
    accessControl: AccessControlConfig;
    analysis: AnalysisConfig;
    learning: LearningConfig;
    dashboard: DashboardConfig;
    cli: CLIConfig;
    integration: {
        cascadeHooks: boolean;
        nativeImageUnderstanding: boolean;
        fastContext: boolean;
        rbac: boolean;
        codemaps: boolean;
    };
}
export declare class ProphecySandbox extends EventEmitter {
    private config;
    private securityManager;
    private auditLogger;
    private accessControl;
    private codeConstructor;
    private sandbox;
    private analyzer;
    private learningSystem;
    private dashboard;
    private cli;
    private isInitialized;
    private isRunning;
    constructor(workspaceRoot: string, baseSecurityConfig: SecurityConfig, config: ProphecySandboxConfig);
    private initializeComponents;
    private setupEventHandlers;
    initialize(): Promise<boolean>;
    generateSample(templateId: string, generationConfig: any, userId: string): Promise<MaliciousSample>;
    executeSample(sample: MaliciousSample, userId: string): Promise<SandboxExecution>;
    getExecution(executionId: string, userId: string): Promise<SandboxExecution | null>;
    getMetrics(userId: string): Promise<any>;
    runCLI(argv: string[]): Promise<void>;
    private ensureInitialized;
    private logProphecyAction;
    private handleExecutionStarted;
    private handleExecutionCompleted;
    private handleExecutionTerminated;
    private handleRazdorAuthenticated;
    private handleAccessDenied;
    private handleSecurityViolation;
    private handleModelUpdated;
    private handleDashboardAlert;
    integrateWithCascade(): Promise<void>;
    private setupCascadeHooks;
    private setupNativeImageUnderstanding;
    private setupFastContext;
    private setupRBAC;
    private setupCodemaps;
    shutdown(): Promise<void>;
    getAccessControl(): AccessControlSystem;
    getDashboard(): WebDashboard;
    getConfig(): ProphecySandboxConfig;
    isReady(): boolean;
}
//# sourceMappingURL=ProphecySandbox.d.ts.map