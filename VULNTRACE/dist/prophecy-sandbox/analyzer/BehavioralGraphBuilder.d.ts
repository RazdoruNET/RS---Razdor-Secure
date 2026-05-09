import { BehaviorNode, SystemCallRecord, NetworkActivityRecord, FileChangeRecord, SandboxLogEntry } from '../security/types';
export interface GraphConfig {
    maxNodes: number;
    timeWindow: number;
    minSimilarity: number;
    enableClustering: boolean;
    clusterThreshold: number;
}
export interface GraphMetrics {
    nodeCount: number;
    edgeCount: number;
    averageDegree: number;
    clusteringCoefficient: number;
    pathLength: number;
    modularity: number;
}
export interface BehaviorCluster {
    id: string;
    nodes: string[];
    type: 'sequential' | 'parallel' | 'conditional' | 'loop';
    description: string;
    confidence: number;
}
export declare class BehavioralGraphBuilder {
    private config;
    private nodes;
    private adjacencyList;
    private clusters;
    constructor(config: GraphConfig);
    buildGraph(syscalls: SystemCallRecord[], networkActivity: NetworkActivityRecord[], fileChanges: FileChangeRecord[], logs: SandboxLogEntry[]): BehaviorNode[];
    private createNodesFromSyscalls;
    private createNodesFromNetwork;
    private createNodesFromFileChanges;
    private createNodesFromLogs;
    private buildTemporalRelationships;
    private buildSemanticRelationships;
    private calculateSemanticSimilarity;
    private calculateTextSimilarity;
    private addEdge;
    private applyClustering;
    private findCluster;
    private determineClusterType;
    private analyzeSyscallPattern;
    private analyzeFilePattern;
    private generateClusterDescription;
    private calculateClusterConfidence;
    private limitGraphSize;
    private formatSyscallDescription;
    private formatNetworkDescription;
    private formatFileDescription;
    private categorizeSyscall;
    private categorizeNetworkActivity;
    private categorizeFileChange;
    private categorizeLogEntry;
    private assessSyscallRisk;
    private assessNetworkRisk;
    private assessFileRisk;
    private assessLogRisk;
    getGraphMetrics(): GraphMetrics;
    private calculateClusteringCoefficient;
    private calculateAveragePathLength;
    private calculateModularity;
    getClusters(): BehaviorCluster[];
    getNodes(): BehaviorNode[];
    getAdjacencyList(): Map<string, Set<string>>;
}
//# sourceMappingURL=BehavioralGraphBuilder.d.ts.map