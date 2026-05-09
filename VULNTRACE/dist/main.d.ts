export { SQLVulnerabilityScanner } from './core/SQLVulnerabilityScanner';
export { CascadeIntegration } from './ide/CascadeIntegration';
export * from './types';
export { SQLParser } from './parser/SQLParser';
export { StaticAnalyzer } from './analyzer/StaticAnalyzer';
export { GPTAnalyzer } from './gpt/GPTAnalyzer';
export { ReportGenerator } from './reporter/ReportGenerator';
export { ConfigManager } from './config/ConfigManager';
export declare class SQLVulnerabilityPlugin {
    private scanner;
    private integration;
    constructor(config?: any);
    activate(): Promise<void>;
    deactivate(): Promise<void>;
    getScanner(): SQLVulnerabilityScanner;
    getIntegration(): CascadeIntegration;
}
export default SQLVulnerabilityPlugin;
//# sourceMappingURL=main.d.ts.map