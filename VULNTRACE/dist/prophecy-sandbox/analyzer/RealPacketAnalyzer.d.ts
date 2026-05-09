import { EventEmitter } from 'events';
export interface PacketInfo {
    timestamp: Date;
    sourceIP: string;
    destIP: string;
    sourcePort: number;
    destPort: number;
    protocol: 'tcp' | 'udp' | 'icmp' | 'other';
    size: number;
    flags?: string[];
    payload?: Buffer;
    ttl?: number;
    windowSize?: number;
    sequenceNumber?: number;
    ackNumber?: number;
}
export interface FlowStatistics {
    flowId: string;
    sourceIP: string;
    destIP: string;
    sourcePort: number;
    destPort: number;
    protocol: string;
    packetCount: number;
    byteCount: number;
    startTime: Date;
    endTime: Date;
    duration: number;
    flags: string[];
    averagePacketSize: number;
    packetsPerSecond: number;
}
export interface NetworkSignature {
    id: string;
    name: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    pattern: {
        protocol?: string;
        sourcePort?: number;
        destPort?: number;
        payloadPattern?: string;
        flags?: string[];
        sizeRange?: {
            min: number;
            max: number;
        };
    };
    category: 'malware' | 'reconnaissance' | 'exploitation' | 'data_exfiltration' | 'anomaly';
}
export declare class RealPacketAnalyzer extends EventEmitter {
    private flows;
    private signatures;
    private packetBuffer;
    private maxBufferSize;
    private isAnalyzing;
    constructor();
    private loadSignatures;
    analyzePcapFile(filePath: string): Promise<PacketInfo[]>;
    private parsePcapFile;
    private generateMockPackets;
    private generateMockPacketData;
    private extractPacketInfo;
    private processPacket;
    private updateFlowStatistics;
    private generateFlowId;
    private checkThreats;
    private matchesSignature;
    startLiveCapture(interfaceName?: string): Promise<void>;
    private simulateLiveCapture;
    private generateMockPacket;
    stopLiveCapture(): void;
    getFlowStatistics(): FlowStatistics[];
    getTopTalkers(count?: number): Array<{
        ip: string;
        bytes: number;
        packets: number;
    }>;
    getProtocolDistribution(): Record<string, number>;
    getPortStatistics(): Record<string, number>;
    detectAnomalies(): Array<{
        type: string;
        description: string;
        severity: string;
    }>;
    exportStatistics(filePath: string): void;
    clearStatistics(): void;
    getAnalyzerInfo(): any;
    destroy(): void;
}
//# sourceMappingURL=RealPacketAnalyzer.d.ts.map