import { CodeTemplate } from './MaliciousCodeConstructor';
export interface GeneticConfig {
    populationSize: number;
    mutationRate: number;
    crossoverRate: number;
    elitismRate: number;
    maxGenerations: number;
    fitnessThreshold: number;
}
export interface Individual {
    id: string;
    template: CodeTemplate;
    fitness: number;
    generation: number;
    parentIds: string[];
    mutations: Mutation[];
}
export interface Mutation {
    type: 'insert' | 'delete' | 'replace' | 'reorder' | 'obfuscate' | 'encrypt';
    position: number;
    original: string;
    mutated: string;
    description: string;
}
export interface FitnessResult {
    score: number;
    stealth: number;
    complexity: number;
    evasion: number;
    novelty: number;
}
export declare class RealGeneticAlgorithm {
    private config;
    private population;
    private generation;
    private fitnessHistory;
    constructor(config: GeneticConfig);
    evolvePopulation(initialTemplate: CodeTemplate, targetCharacteristics: string[]): Promise<CodeTemplate>;
    mutateTemplate(template: CodeTemplate, mutationRate: number): Promise<CodeTemplate>;
    private initializePopulation;
    private createVariant;
    private evaluatePopulation;
    private calculateFitness;
    private calculateStealth;
    private calculateComplexity;
    private calculateEvasionScore;
    private calculateNovelty;
    private selection;
    private tournamentSelection;
    private createNextGeneration;
    private selectParent;
    private crossover;
    private applyMutations;
    private selectMutationType;
    private applyMutation;
    private applyObfuscation;
    private applyEncryption;
    private applyStructureMutation;
    private generateInsertion;
    private generateReplacement;
    private reorderCodeBlocks;
    private generateJunkCode;
    private generateRandomName;
    private isReservedWord;
    private addRandomEvasion;
    private shouldTerminate;
    private getBestIndividual;
    getPopulation(): Individual[];
    getFitnessHistory(): number[];
    getGeneration(): number;
    getStats(): {
        populationSize: number;
        averageFitness: number;
        bestFitness: number;
        generation: number;
        convergenceRate: number;
    };
}
//# sourceMappingURL=RealGeneticAlgorithm.d.ts.map