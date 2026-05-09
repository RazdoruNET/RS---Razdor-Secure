"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.RealDockerManager = void 0;
const Docker = __importStar(require("dockerode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const events_1 = require("events");
const uuid_1 = require("uuid");
class RealDockerManager extends events_1.EventEmitter {
    constructor(dockerOptions) {
        super();
        this.activeContainers = new Map();
        this.containerStats = new Map();
        this.monitoringInterval = null;
        this.defaultImage = 'prophecy-sandbox-base:latest';
        try {
            this.docker = new Docker(dockerOptions);
            console.log('[Docker] Docker manager initialized');
        }
        catch (error) {
            console.error('[Docker] Failed to initialize Docker:', error);
            throw new Error('Docker is not available. Please ensure Docker is installed and running.');
        }
        this.startMonitoring();
    }
    async testConnection() {
        try {
            await this.docker.ping();
            console.log('[Docker] Docker connection successful');
            return true;
        }
        catch (error) {
            console.error('[Docker] Docker connection failed:', error);
            return false;
        }
    }
    async pullImage(imageName) {
        try {
            console.log(`[Docker] Pulling image: ${imageName}`);
            return new Promise((resolve, reject) => {
                this.docker.pull(imageName, (err, stream) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    this.docker.modem.followProgress(stream, (event) => {
                        if (event.status && event.status !== 'Pull complete') {
                            console.log(`[Docker] ${event.status}: ${event.progress || ''}`);
                        }
                    }, (err) => {
                        if (err) {
                            reject(err);
                        }
                        else {
                            console.log(`[Docker] Image pulled successfully: ${imageName}`);
                            resolve();
                        }
                    });
                });
            });
        }
        catch (error) {
            console.error(`[Docker] Failed to pull image ${imageName}:`, error);
            throw error;
        }
    }
    async createContainer(config) {
        try {
            const containerName = `prophecy-sandbox-${(0, uuid_1.v4)()}`;
            const fullConfig = {
                image: config.image || this.defaultImage,
                command: config.command || ['/bin/bash'],
                workingDir: config.workingDir || '/sandbox',
                memory: config.memory || '512m',
                cpu: config.cpu || '0.5',
                networkMode: config.networkMode || 'none',
                readonlyRootfs: config.readonlyRootfs || true,
                tmpfs: config.tmpfs || { '/tmp': 'rw,noexec,nosuid,size=100m' },
                binds: config.binds || [],
                autoRemove: config.autoRemove || true,
                environment: config.environment || {}
            };
            // Create container with security constraints
            const containerConfig = {
                Image: fullConfig.image,
                Cmd: fullConfig.command,
                WorkingDir: fullConfig.workingDir,
                HostConfig: {
                    Memory: this.parseMemory(fullConfig.memory),
                    CpuQuota: parseInt(fullConfig.cpu) * 100000,
                    NetworkMode: fullConfig.networkMode,
                    ReadonlyRootfs: fullConfig.readonlyRootfs,
                    Tmpfs: fullConfig.tmpfs,
                    Binds: fullConfig.binds,
                    AutoRemove: fullConfig.autoRemove,
                    SecurityOpt: ['no-new-privileges:true'],
                    CapDrop: ['ALL'],
                    CapAdd: ['CHOWN', 'DAC_OVERRIDE', 'FOWNER', 'SETGID', 'SETUID'],
                    PidsLimit: 50,
                    Ulimits: [
                        { Name: 'nofile', Hard: 1024, Soft: 1024 },
                        { Name: 'nproc', Hard: 50, Soft: 50 }
                    ]
                },
                Env: Object.entries(fullConfig.environment || {}).map(([key, value]) => `${key}=${value}`),
                User: 'nobody',
                AttachStdin: false,
                AttachStdout: true,
                AttachStderr: true,
                Tty: true,
                OpenStdin: false,
                StdinOnce: false
            };
            console.log(`[Docker] Creating container: ${containerName}`);
            const container = await this.docker.createContainer({
                ...containerConfig,
                name: containerName
            });
            this.activeContainers.set(containerName, container);
            console.log(`[Docker] Container created: ${containerName}`);
            this.emit('containerCreated', containerName, fullConfig);
            return containerName;
        }
        catch (error) {
            console.error('[Docker] Failed to create container:', error);
            throw error;
        }
    }
    async startContainer(containerName) {
        try {
            const container = this.activeContainers.get(containerName);
            if (!container) {
                throw new Error(`Container ${containerName} not found`);
            }
            console.log(`[Docker] Starting container: ${containerName}`);
            await container.start();
            // Wait for container to be ready
            await this.waitForContainer(containerName, 30000);
            console.log(`[Docker] Container started: ${containerName}`);
            this.emit('containerStarted', containerName);
        }
        catch (error) {
            console.error(`[Docker] Failed to start container ${containerName}:`, error);
            throw error;
        }
    }
    async executeCommand(containerName, command) {
        try {
            const container = this.activeContainers.get(containerName);
            if (!container) {
                throw new Error(`Container ${containerName} not found`);
            }
            console.log(`[Docker] Executing command in ${containerName}: ${command.join(' ')}`);
            const exec = await container.exec({
                Cmd: command,
                AttachStdout: true,
                AttachStderr: true,
                User: 'nobody'
            });
            const stream = await exec.start({
                hijack: true,
                stdin: false
            });
            let output = '';
            let exitCode = 0;
            return new Promise((resolve, reject) => {
                stream.on('data', (chunk) => {
                    output += chunk.toString();
                });
                stream.on('end', async () => {
                    try {
                        const inspect = await exec.inspect();
                        exitCode = inspect.ExitCode || 0;
                        console.log(`[Docker] Command completed with exit code: ${exitCode}`);
                        resolve({ output, exitCode });
                    }
                    catch (error) {
                        reject(error);
                    }
                });
                stream.on('error', reject);
            });
        }
        catch (error) {
            console.error(`[Docker] Failed to execute command in ${containerName}:`, error);
            throw error;
        }
    }
    async stopContainer(containerName, timeout = 10000) {
        try {
            const container = this.activeContainers.get(containerName);
            if (!container) {
                throw new Error(`Container ${containerName} not found`);
            }
            console.log(`[Docker] Stopping container: ${containerName}`);
            await container.stop({ t: timeout / 1000 });
            console.log(`[Docker] Container stopped: ${containerName}`);
            this.emit('containerStopped', containerName);
        }
        catch (error) {
            console.error(`[Docker] Failed to stop container ${containerName}:`, error);
            throw error;
        }
    }
    async removeContainer(containerName, force = false) {
        try {
            const container = this.activeContainers.get(containerName);
            if (!container) {
                throw new Error(`Container ${containerName} not found`);
            }
            console.log(`[Docker] Removing container: ${containerName}`);
            await container.remove({ force });
            this.activeContainers.delete(containerName);
            this.containerStats.delete(containerName);
            console.log(`[Docker] Container removed: ${containerName}`);
            this.emit('containerRemoved', containerName);
        }
        catch (error) {
            console.error(`[Docker] Failed to remove container ${containerName}:`, error);
            throw error;
        }
    }
    async getContainerInfo(containerName) {
        try {
            const container = this.activeContainers.get(containerName);
            if (!container) {
                throw new Error(`Container ${containerName} not found`);
            }
            const inspect = await container.inspect();
            const stats = this.containerStats.get(containerName) || {
                cpu: 0,
                memory: 0,
                networkIO: 0,
                blockIO: 0,
                processes: 0
            };
            return {
                id: inspect.Id,
                name: inspect.Name,
                status: inspect.State.Status,
                image: inspect.Config.Image,
                created: new Date(inspect.Created),
                ports: this.extractPorts(inspect.NetworkSettings.Ports),
                networks: Object.keys(inspect.NetworkSettings.Networks),
                stats
            };
        }
        catch (error) {
            console.error(`[Docker] Failed to get container info for ${containerName}:`, error);
            throw error;
        }
    }
    async listContainers(all = false) {
        try {
            const containers = await this.docker.listContainers({ all });
            const containerInfos = [];
            for (const container of containers) {
                const info = {
                    id: container.Id,
                    name: container.Names[0],
                    status: container.Status,
                    image: container.Image,
                    created: new Date(container.Created * 1000),
                    ports: this.extractPorts(container.Ports),
                    networks: container.Names,
                    stats: this.containerStats.get(container.Id) || {
                        cpu: 0,
                        memory: 0,
                        networkIO: 0,
                        blockIO: 0,
                        processes: 0
                    }
                };
                containerInfos.push(info);
            }
            return containerInfos;
        }
        catch (error) {
            console.error('[Docker] Failed to list containers:', error);
            throw error;
        }
    }
    async cleanupOrphanedContainers() {
        try {
            console.log('[Docker] Cleaning up orphaned containers...');
            const containers = await this.docker.listContainers({ all: true });
            const prophecyContainers = containers.filter((container) => container.Names.some((name) => name.includes('prophecy-sandbox')));
            let cleanedCount = 0;
            for (const container of prophecyContainers) {
                if (container.State === 'exited' || container.State === 'dead') {
                    try {
                        const dockerContainer = this.docker.getContainer(container.Id);
                        await dockerContainer.remove({ force: true });
                        cleanedCount++;
                        console.log(`[Docker] Cleaned up container: ${container.Id}`);
                    }
                    catch (error) {
                        console.error(`[Docker] Failed to cleanup container ${container.Id}:`, error);
                    }
                }
            }
            console.log(`[Docker] Cleaned up ${cleanedCount} orphaned containers`);
            return cleanedCount;
        }
        catch (error) {
            console.error('[Docker] Failed to cleanup orphaned containers:', error);
            return 0;
        }
    }
    async waitForContainer(containerName, timeout) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const checkStatus = async () => {
                try {
                    const container = this.activeContainers.get(containerName);
                    if (!container) {
                        reject(new Error(`Container ${containerName} not found`));
                        return;
                    }
                    const inspect = await container.inspect();
                    if (inspect.State.Status === 'running') {
                        resolve();
                        return;
                    }
                    if (Date.now() - startTime > timeout) {
                        reject(new Error(`Container ${containerName} failed to start within ${timeout}ms`));
                        return;
                    }
                    setTimeout(checkStatus, 1000);
                }
                catch (error) {
                    reject(error);
                }
            };
            checkStatus();
        });
    }
    startMonitoring() {
        this.monitoringInterval = setInterval(async () => {
            await this.updateContainerStats();
        }, 5000);
    }
    async updateContainerStats() {
        try {
            for (const [containerName, container] of this.activeContainers) {
                try {
                    const stats = await container.stats({ stream: false });
                    const containerStats = this.parseStats(stats);
                    this.containerStats.set(containerName, containerStats);
                }
                catch (error) {
                    // Container might not be running
                    this.containerStats.delete(containerName);
                }
            }
        }
        catch (error) {
            console.error('[Docker] Failed to update container stats:', error);
        }
    }
    parseStats(stats) {
        const cpuStats = stats.cpu_stats;
        const preCpuStats = stats.precpu_stats;
        const memoryStats = stats.memory_stats;
        const networkStats = stats.networks;
        const blockIOStats = stats.blkio_stats;
        // Calculate CPU usage percentage
        const cpuDelta = cpuStats.cpu_usage.total_usage - preCpuStats.cpu_usage.total_usage;
        const systemDelta = cpuStats.system_cpu_usage - preCpuStats.system_cpu_usage;
        const cpuUsage = systemDelta > 0 ? (cpuDelta / systemDelta) * 100 : 0;
        // Calculate memory usage in MB
        const memoryUsage = memoryStats.usage / (1024 * 1024);
        // Calculate network I/O
        let networkIO = 0;
        if (networkStats) {
            Object.values(networkStats).forEach((net) => {
                networkIO += (net.rx_bytes + net.tx_bytes) / (1024 * 1024);
            });
        }
        // Calculate block I/O
        let blockIO = 0;
        if (blockIOStats && blockIOStats.io_service_bytes_recursive) {
            blockIOStats.io_service_bytes_recursive.forEach((io) => {
                blockIO += io.value / (1024 * 1024);
            });
        }
        return {
            cpu: cpuUsage,
            memory: memoryUsage,
            networkIO,
            blockIO,
            processes: stats.pids_stats.current || 0
        };
    }
    parseMemory(memoryStr) {
        const units = {
            'b': 1,
            'k': 1024,
            'm': 1024 * 1024,
            'g': 1024 * 1024 * 1024
        };
        const match = memoryStr.toLowerCase().match(/^(\d+)([bkmg]?)$/);
        if (!match) {
            return 512 * 1024 * 1024; // Default 512MB
        }
        const [, size, unit] = match;
        return parseInt(size) * (units[unit] || 1);
    }
    extractPorts(ports) {
        const portMap = {};
        if (Array.isArray(ports)) {
            ports.forEach(port => {
                if (port.PrivatePort) {
                    portMap[port.PrivatePort.toString()] = port.PublicPort?.toString() || 'internal';
                }
            });
        }
        else if (typeof ports === 'object') {
            Object.entries(ports).forEach(([port, bindings]) => {
                if (Array.isArray(bindings) && bindings.length > 0) {
                    portMap[port] = bindings[0].HostPort || 'internal';
                }
            });
        }
        return portMap;
    }
    async createNetwork(networkName, options = {}) {
        try {
            console.log(`[Docker] Creating network: ${networkName}`);
            await this.docker.createNetwork({
                Name: networkName,
                Driver: 'bridge',
                Internal: false,
                CheckDuplicate: true,
                ...options
            });
            console.log(`[Docker] Network created: ${networkName}`);
        }
        catch (error) {
            console.error(`[Docker] Failed to create network ${networkName}:`, error);
            throw error;
        }
    }
    async removeNetwork(networkName) {
        try {
            console.log(`[Docker] Removing network: ${networkName}`);
            const network = this.docker.getNetwork(networkName);
            await network.remove();
            console.log(`[Docker] Network removed: ${networkName}`);
        }
        catch (error) {
            console.error(`[Docker] Failed to remove network ${networkName}:`, error);
            throw error;
        }
    }
    async buildImage(dockerfilePath, contextPath, imageName) {
        try {
            console.log(`[Docker] Building image: ${imageName}`);
            return new Promise((resolve, reject) => {
                this.docker.buildImage({
                    context: fs.createReadStream(contextPath),
                    buildinfo: {
                        dockerfile: path.basename(dockerfilePath)
                    }
                }, { t: imageName }, (err, stream) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    this.docker.modem.followProgress(stream, (event) => {
                        if (event.status && event.status !== 'Download complete') {
                            console.log(`[Docker] Build: ${event.status} ${event.progress || ''}`);
                        }
                    }, (err) => {
                        if (err) {
                            reject(err);
                        }
                        else {
                            console.log(`[Docker] Image built successfully: ${imageName}`);
                            resolve();
                        }
                    });
                });
            });
        }
        catch (error) {
            console.error(`[Docker] Failed to build image ${imageName}:`, error);
            throw error;
        }
    }
    async getImageInfo(imageName) {
        try {
            const image = this.docker.getImage(imageName);
            const inspect = await image.inspect();
            return {
                id: inspect.Id,
                repoTags: inspect.RepoTags,
                size: inspect.Size,
                created: new Date(inspect.Created * 1000),
                architecture: inspect.Architecture,
                os: inspect.Os
            };
        }
        catch (error) {
            console.error(`[Docker] Failed to get image info for ${imageName}:`, error);
            throw error;
        }
    }
    async removeImage(imageName, force = false) {
        try {
            console.log(`[Docker] Removing image: ${imageName}`);
            const image = this.docker.getImage(imageName);
            await image.remove({ force });
            console.log(`[Docker] Image removed: ${imageName}`);
        }
        catch (error) {
            console.error(`[Docker] Failed to remove image ${imageName}:`, error);
            throw error;
        }
    }
    destroy() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        console.log('[Docker] Docker manager destroyed');
    }
}
exports.RealDockerManager = RealDockerManager;
//# sourceMappingURL=RealDockerManager.js.map