import * as Docker from 'dockerode';
import { EventEmitter } from 'events';
export interface ContainerConfig {
    image: string;
    command: string[];
    workingDir: string;
    memory: string;
    cpu: string;
    networkMode: string;
    readonlyRootfs: boolean;
    tmpfs: Record<string, string>;
    binds: string[];
    autoRemove: boolean;
    environment?: Record<string, string>;
}
export interface ContainerInfo {
    id: string;
    name: string;
    status: string;
    image: string;
    created: Date;
    ports: Record<string, string>;
    networks: string[];
    stats: ContainerStats;
}
export interface ContainerStats {
    cpu: number;
    memory: number;
    networkIO: number;
    blockIO: number;
    processes: number;
}
export declare class RealDockerManager extends EventEmitter {
    private docker;
    private activeContainers;
    private containerStats;
    private monitoringInterval;
    private defaultImage;
    constructor(dockerOptions?: Docker.DockerOptions);
    testConnection(): Promise<boolean>;
    pullImage(imageName: string): Promise<void>;
    createContainer(config: Partial<ContainerConfig>): Promise<string>;
    startContainer(containerName: string): Promise<void>;
    executeCommand(containerName: string, command: string[]): Promise<{
        output: string;
        exitCode: number;
    }>;
    stopContainer(containerName: string, timeout?: number): Promise<void>;
    removeContainer(containerName: string, force?: boolean): Promise<void>;
    getContainerInfo(containerName: string): Promise<ContainerInfo>;
    listContainers(all?: boolean): Promise<ContainerInfo[]>;
    cleanupOrphanedContainers(): Promise<number>;
    private waitForContainer;
    private startMonitoring;
    private updateContainerStats;
    private parseStats;
    private parseMemory;
    private extractPorts;
    createNetwork(networkName: string, options?: any): Promise<void>;
    removeNetwork(networkName: string): Promise<void>;
    buildImage(dockerfilePath: string, contextPath: string, imageName: string): Promise<void>;
    getImageInfo(imageName: string): Promise<any>;
    removeImage(imageName: string, force?: boolean): Promise<void>;
    destroy(): void;
}
//# sourceMappingURL=RealDockerManager.d.ts.map