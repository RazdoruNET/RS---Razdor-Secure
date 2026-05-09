import { SQLQuery, Vulnerability, AnalysisContext, AppConfig } from '../types';
export declare class GPTAnalyzer {
    private config;
    private openai;
    constructor(config: AppConfig);
    analyze(queries: SQLQuery[], context: AnalysisContext, staticVulnerabilities: Vulnerability[]): Promise<Vulnerability[]>;
    private analyzeQuery;
    private performGPTAnalysis;
    private getSystemPrompt;
    private buildAnalysisPrompt;
    private parseGPTResponse;
    private extractRisks;
    private extractRecommendations;
    private convertGPTResponseToVulnerabilities;
    private createGPTVulnerability;
    private classifyVulnerabilityType;
    private classifySeverity;
    private classifyCategory;
    private mapToCWE;
    private mapToOWASP;
    private analyzeQueryComplexity;
    private checkDataPrivacy;
    private analyzeBusinessLogic;
}
//# sourceMappingURL=GPTAnalyzer.d.ts.map