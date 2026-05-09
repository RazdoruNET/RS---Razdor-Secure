import { EventEmitter } from 'events';
export interface FuzzingConfig {
    targetPath: string;
    targetArgs: string[];
    inputGenerator: 'random' | 'mutation' | 'grammar' | 'hybrid';
    maxIterations: number;
    timeout: number;
    maxInputSize: number;
    crashDetection: boolean;
    memoryLimit: number;
    cpuLimit: number;
    corpusDirectory: string;
    outputDirectory: string;
}
export interface CrashInfo {
    id: string;
    input: string | Buffer;
    signal: string;
    exitCode: number;
    stackTrace: string;
    registers: Record<string, string>;
    memoryMap: string[];
    timestamp: Date;
    reproducible: boolean;
    severity: 'low' | 'medium' | 'high' | 'critical';
}
export interface FuzzingStats {
    totalExecutions: number;
    crashesFound: number;
    uniqueCrashes: number;
    hangsFound: number;
    coverage: number;
    executionRate: number;
    averageExecutionTime: number;
    corpusSize: number;
    startTime: Date;
    endTime?: Date;
}
export interface MutationStrategy {
    name: string;
    probability: number;
    mutate: (input: Buffer) => Buffer;
}
export declare class RealFuzzer extends EventEmitter {
    private config;
    private isFuzzing;
    private stats;
    private crashes;
    private corpus;
    private mutationStrategies;
    private coverageData;
    constructor(config: FuzzingConfig);
    private initializeMutationStrategies;
    private loadCorpus;
    private createInitialCorpus;
    startFuzzing(): Promise<void>;
    private randomFuzzing;
    private mutationFuzzing;
    private grammarFuzzing;
    private hybridFuzzing;
    private generateRandomInput;
    private mutateInput;
    private bitFlipMutation;
    private byteInsertionMutation;
    private byteDeletionMutation;
    private arithmeticMutation;
    private interestingValuesMutation;
    private spliceMutation;
    private randomBytesMutation;
    private dictionaryMutation;
    private generateGrammarBasedInput;
    private generateSQLGrammar;
    private generateHTTPGrammar;
    private generateFormatStringGrammar;
    private generatePathGrammar;
    private executeTarget;
    private runTargetWithInput;
    private simulateCoverageCollection;
    private handleCrash;
    private generateCrashId;
    private generateStackTrace;
    private getRegisters;
    private getMemoryMap;
    private testReproducibility;
    private determineCrashSeverity;
    private saveCrash;
    private saveCorpusInput;
    stopFuzzing(): void;
    getStats(): FuzzingStats;
    getCrashes(): CrashInfo[];
    getCorpus(): Buffer[];
    generateReport(format?: 'json' | 'html'): string;
    destroy(): void;
}
//# sourceMappingURL=RealFuzzer.d.ts.map