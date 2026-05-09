import { AccessControlSystem } from '../access-control/AccessControlSystem';
import { MaliciousCodeConstructor } from '../constructor/MaliciousCodeConstructor';
import { SandboxEnvironment } from '../sandbox/SandboxEnvironment';
import { ThreatAnalyzer } from '../analyzer/ThreatAnalyzer';
import { SelfLearningSystem } from '../learning/SelfLearningSystem';
export interface CLIConfig {
    outputFormat: 'json' | 'table' | 'csv';
    verbose: boolean;
    configPath: string;
    autoSave: boolean;
}
export declare class CLIInterface {
    private program;
    private accessControl;
    private codeConstructor;
    private sandbox;
    private analyzer;
    private learningSystem;
    private config;
    constructor(accessControl: AccessControlSystem, codeConstructor: MaliciousCodeConstructor, sandbox: SandboxEnvironment, analyzer: ThreatAnalyzer, learningSystem: SelfLearningSystem, config: CLIConfig);
    private setupCommands;
    private createAuthChallengeCommand;
    private createAuthLoginCommand;
    private createGenerateSampleCommand;
    private createListTemplatesCommand;
    private createExecuteSampleCommand;
    private createListExecutionsCommand;
    private createGetExecutionCommand;
    private createAnalyzeExecutionCommand;
    private createListTechniquesCommand;
    private createListSignaturesCommand;
    private createGetMetricsCommand;
    private createGetInsightsCommand;
    private createResetLearningCommand;
    private createStatusCommand;
    private createInitCommand;
    private createShutdownCommand;
    private ensureAuthenticated;
    private loadToken;
    private saveToken;
    private outputSample;
    private outputExecution;
    private outputAnalysis;
    run(argv: string[]): Promise<void>;
}
//# sourceMappingURL=CLIInterface.d.ts.map