import { SandboxExecution, ThreatAnalysisResult, ThreatSignature } from '../security/types';
import { TechniquePattern } from '../analyzer/ThreatAnalyzer';
import { CodeTemplate } from '../constructor/MaliciousCodeConstructor';
export interface LearningConfig {
    enableAdaptiveGeneration: boolean;
    enableSignatureEvolution: boolean;
    enableTechniqueLearning: boolean;
    learningRate: number;
    minSamplesForLearning: number;
    modelPersistencePath: string;
}
export interface LearningMetrics {
    totalSamplesAnalyzed: number;
    successfulDetections: number;
    falsePositives: number;
    falseNegatives: number;
    averageRiskScore: number;
    techniqueEvolutionCount: number;
    signatureEvolutionCount: number;
    lastUpdateTime: string;
}
export interface EvolutionResult {
    evolved: boolean;
    changes: string[];
    confidence: number;
    newVersion: string;
}
export declare class SelfLearningSystem {
    private config;
    private metrics;
    private learningData;
    private techniquePerformance;
    private signaturePerformance;
    constructor(config: LearningConfig);
    processExecution(execution: SandboxExecution, analysisResult: ThreatAnalysisResult): Promise<void>;
    evolveTechniques(techniques: TechniquePattern[]): Promise<EvolutionResult>;
    evolveSignatures(signatures: ThreatSignature[]): Promise<EvolutionResult>;
    optimizeGeneration(templates: CodeTemplate[]): Promise<CodeTemplate[]>;
    private evolveTechnique;
    private evolveSignature;
    private optimizeTemplate;
    private generateNewPatterns;
    private makePatternMoreSpecific;
    private getSuccessfulEvasionTechniques;
    private triggerLearningCycle;
    private analyzeTrends;
    private updateModels;
    private generateInsights;
    private generateLearningInsights;
    private updateMetrics;
    private updateTechniquePerformance;
    private updateSignaturePerformance;
    private calculateAverageRiskScore;
    private calculateEvolutionConfidence;
    private generateVersionNumber;
    private initializeMetrics;
    private loadLearningData;
    private saveLearningData;
    getMetrics(): LearningMetrics;
    getLearningInsights(): string[];
    getTechniquePerformance(): Map<string, TechniquePerformance>;
    getSignaturePerformance(): Map<string, SignaturePerformance>;
    reset(): Promise<void>;
}
interface TechniquePerformance {
    techniqueId: string;
    detectionCount: number;
    successCount: number;
    falsePositiveCount: number;
    successRate: number;
    lastUpdated: string;
}
interface SignaturePerformance {
    signatureId: string;
    matchCount: number;
    falsePositiveCount: number;
    truePositiveCount: number;
    falsePositiveRate: number;
    precision: number;
    lastUpdated: string;
}
export {};
//# sourceMappingURL=SelfLearningSystem.d.ts.map