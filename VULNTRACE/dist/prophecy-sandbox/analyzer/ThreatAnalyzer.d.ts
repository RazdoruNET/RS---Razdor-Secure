import { SandboxExecution, ThreatAnalysisResult, ThreatSignature } from '../security/types';
export interface AnalysisConfig {
    enableBehavioralAnalysis: boolean;
    enableSignatureMatching: boolean;
    enableAnomalyDetection: boolean;
    riskThreshold: number;
    knownTechniquesDatabase: string;
}
export interface TechniquePattern {
    id: string;
    name: string;
    category: string;
    syscallPatterns: string[];
    networkPatterns: string[];
    filePatterns: string[];
    description: string;
}
export declare class ThreatAnalyzer {
    private config;
    private techniqueDatabase;
    private signatureDatabase;
    private graphBuilder;
    private graphConfig;
    constructor(config: AnalysisConfig);
    analyzeExecution(execution: SandboxExecution): Promise<ThreatAnalysisResult>;
    private buildBehaviorGraph;
    private calculateNodeRisk;
    private calculateNodeAnomalyScore;
    private buildNodeRelationships;
    private identifyAttackTechniques;
    private calculateTechniqueConfidence;
    private matchesPattern;
    private gatherEvidence;
    private detectAnomalies;
    private detectSyscallAnomalies;
    private detectNetworkAnomalies;
    private detectFileAnomalies;
    private calculateFileChangeRate;
    private matchSignatures;
    private calculateSignatureConfidence;
    private calculateRiskScore;
    private generateSummary;
    private getRiskLevel;
    private loadTechniqueDatabase;
    private loadSignatureDatabase;
    addSignature(signature: ThreatSignature): void;
    addTechnique(technique: TechniquePattern): void;
    getTechniqueDatabase(): TechniquePattern[];
    getSignatureDatabase(): ThreatSignature[];
}
//# sourceMappingURL=ThreatAnalyzer.d.ts.map