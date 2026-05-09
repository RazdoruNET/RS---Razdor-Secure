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
exports.SandboxEnvironment = void 0;
const uuid_1 = require("uuid");
const Docker = __importStar(require("dockerode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const events_1 = require("events");
const RealTimeMonitor_1 = require("./RealTimeMonitor");
class SandboxEnvironment extends events_1.EventEmitter {
    constructor(config) {
        super();
        this.activeExecutions = new Map();
        this.resources = new Map();
        this.monitors = new Map();
        this.config = config;
        this.docker = new Docker();
    }
    async initialize() {
        try {
            // Create Docker network for isolation if network isolation is enabled
            if (this.config.networkIsolated) {
                await this.createIsolatedNetwork();
            }
            // Create base sandbox image
            await this.createBaseImage();
            console.log('Prophecy Sandbox initialized successfully');
        }
        catch (error) {
            console.error('Failed to initialize sandbox:', error);
            throw error;
        }
    }
    async executeSample(sample) {
        const executionId = (0, uuid_1.v4)();
        const startTime = new Date().toISOString();
        const execution = {
            id: executionId,
            sampleId: sample.id,
            startTime,
            status: 'pending',
            logs: [],
            systemCalls: [],
            networkActivity: [],
            fileChanges: [],
            analysisResults: {
                behaviorGraph: [],
                techniques: [],
                anomalies: [],
                signatures: [],
                riskScore: 0,
                summary: ''
            }
        };
        this.activeExecutions.set(executionId, execution);
        try {
            // Setup sandbox resources
            const resources = await this.setupSandboxResources(executionId, sample);
            this.resources.set(executionId, resources);
            // Update status to running
            execution.status = 'running';
            this.emit('executionStarted', execution);
            // Execute the sample
            await this.runInSandbox(execution, sample, resources);
            // Update status to completed
            execution.endTime = new Date().toISOString();
            execution.status = 'completed';
        }
        catch (error) {
            execution.endTime = new Date().toISOString();
            execution.status = 'failed';
            execution.logs.push({
                timestamp: new Date().toISOString(),
                level: 'error',
                source: 'sandbox',
                message: `Execution failed: ${error.message}`
            });
        }
        finally {
            // Cleanup resources
            await this.cleanupResources(executionId);
        }
        this.emit('executionCompleted', execution);
        return execution;
    }
    async setupSandboxResources(executionId, sample) {
        const tempDir = await this.createTempDirectory(executionId);
        const containerId = await this.createContainer(executionId, sample, tempDir);
        return {
            containerId,
            tempDir,
            networkId: this.config.networkIsolated ? 'prophecy-sandbox-network' : undefined
        };
    }
    async createTempDirectory(executionId) {
        const tempDir = path.join('/tmp', 'prophecy-sandbox', executionId);
        await fs.promises.mkdir(tempDir, { recursive: true });
        return tempDir;
    }
    async createContainer(executionId, sample, tempDir) {
        // Write sample code to file
        const sampleFile = path.join(tempDir, this.getSampleFileName(sample));
        await fs.promises.writeFile(sampleFile, sample.code);
        // Create container configuration
        const containerConfig = {
            Image: 'prophecy-sandbox-base:latest',
            Cmd: this.getExecutionCommand(sample),
            WorkingDir: '/workspace',
            HostConfig: {
                Memory: this.parseMemoryLimit(this.config.resourceLimits.memory),
                CpuQuota: this.parseCpuLimit(this.config.resourceLimits.cpu),
                NetworkMode: this.config.networkIsolated ? 'prophecy-sandbox-network' : 'none',
                ReadonlyRootfs: true,
                Tmpfs: {
                    '/tmp': 'noexec,nosuid,size=100m',
                    '/workspace': 'noexec,nosuid,size=200m'
                },
                Binds: [`${tempDir}:/workspace:rw`],
                AutoRemove: this.config.autoDestroy,
                LogConfig: {
                    Type: 'json-file',
                    Config: {
                        'max-size': '10m',
                        'max-file': '3'
                    }
                }
            },
            Env: [
                'SANDBOX_MODE=enabled',
                'MONITORING_LEVEL=full',
                `EXECUTION_ID=${executionId}`
            ]
        };
        // Create and start container
        const container = await this.docker.createContainer(containerConfig);
        await container.start();
        return container.id;
    }
    getSampleFileName(sample) {
        const extensions = {
            python: 'py',
            javascript: 'js',
            cpp: 'cpp',
            powershell: 'ps1',
            bash: 'sh'
        };
        return `sample.${extensions[sample.language] || 'txt'}`;
    }
    getExecutionCommand(sample) {
        const commands = {
            python: ['python3', '/workspace/sample.py'],
            javascript: ['node', '/workspace/sample.js'],
            cpp: ['g++', '/workspace/sample.cpp', '-o', '/workspace/sample', '&&', '/workspace/sample'],
            powershell: ['pwsh', '-File', '/workspace/sample.ps1'],
            bash: ['bash', '/workspace/sample.sh']
        };
        return commands[sample.language] || ['cat', '/workspace/sample'];
    }
    async runInSandbox(execution, sample, resources) {
        const container = this.docker.getContainer(resources.containerId);
        // Setup real-time monitoring
        const monitorConfig = {
            enableStrace: true,
            enableNetworkMonitor: this.config.networkIsolated,
            enableFileMonitor: true,
            straceOptions: ['-f', '-e', 'trace=all'],
            networkInterface: this.config.networkIsolated ? 'none' : 'eth0',
            logLevel: 'info'
        };
        const monitor = new RealTimeMonitor_1.RealTimeMonitor(monitorConfig);
        this.monitors.set(execution.id, monitor);
        // Setup event listeners for real monitoring data
        monitor.on('syscall', (syscall) => {
            execution.systemCalls.push(syscall);
        });
        monitor.on('networkActivity', (network) => {
            execution.networkActivity.push(network);
        });
        monitor.on('fileChange', (file) => {
            execution.fileChanges.push(file);
        });
        monitor.on('log', (log) => {
            execution.logs.push(log);
        });
        try {
            // Start real monitoring
            await monitor.startMonitoring(resources.containerId, execution.id);
            // Wait for execution or timeout
            const executionPromise = this.waitForExecution(container, execution);
            await Promise.race([
                executionPromise,
                this.createTimeoutPromise(this.config.maxExecutionTime * 1000)
            ]);
        }
        finally {
            // Stop monitoring
            await monitor.stopMonitoring();
            this.monitors.delete(execution.id);
        }
    }
    async monitorContainer(container, execution) {
        // Monitor container logs
        const logStream = await container.logs({
            stdout: true,
            stderr: true,
            timestamps: true,
            follow: true
        });
        logStream.on('data', (chunk) => {
            const lines = chunk.toString().split('\n');
            for (const line of lines) {
                if (line.trim()) {
                    execution.logs.push({
                        timestamp: new Date().toISOString(),
                        level: 'info',
                        source: 'container',
                        message: line.trim()
                    });
                }
            }
        });
        // Monitor container stats (CPU, memory, network)
        this.monitorContainerStats(container, execution);
    }
    async monitorContainerStats(container, execution) {
        const interval = setInterval(async () => {
            try {
                const stats = await container.stats({ stream: false });
                // Log system calls (simplified - in real implementation would use strace)
                execution.systemCalls.push({
                    timestamp: new Date().toISOString(),
                    syscall: 'process_activity',
                    args: ['cpu', 'memory'],
                    result: 0,
                    process: 'sample'
                });
                // Monitor network activity
                if (stats.networks) {
                    for (const [interfaceName, data] of Object.entries(stats.networks)) {
                        if (data.rx_bytes > 0 || data.tx_bytes > 0) {
                            execution.networkActivity.push({
                                timestamp: new Date().toISOString(),
                                protocol: 'tcp',
                                source: interfaceName,
                                destination: 'unknown',
                                port: 0,
                                size: data.rx_bytes + data.tx_bytes,
                                blocked: this.config.networkIsolated
                            });
                        }
                    }
                }
            }
            catch (error) {
                // Container might have stopped
                clearInterval(interval);
            }
        }, 1000);
        // Clean up interval after execution
        setTimeout(() => clearInterval(interval), this.config.maxExecutionTime * 1000);
    }
    async waitForExecution(container, execution) {
        const data = await container.wait();
        if (data.StatusCode !== 0) {
            execution.logs.push({
                timestamp: new Date().toISOString(),
                level: 'error',
                source: 'container',
                message: `Process exited with code ${data.StatusCode}`
            });
        }
    }
    createTimeoutPromise(timeoutMs) {
        return new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Execution timeout')), timeoutMs);
        });
    }
    async cleanupResources(executionId) {
        const resources = this.resources.get(executionId);
        if (!resources)
            return;
        try {
            // Stop and remove container
            const container = this.docker.getContainer(resources.containerId);
            try {
                await container.kill();
                await container.remove();
            }
            catch (error) {
                // Container might already be removed
            }
            // Clean up temp directory
            await fs.promises.rm(resources.tempDir, { recursive: true, force: true });
            this.resources.delete(executionId);
        }
        catch (error) {
            console.error(`Failed to cleanup resources for ${executionId}:`, error);
        }
    }
    async createIsolatedNetwork() {
        try {
            const network = await this.docker.createNetwork({
                Name: 'prophecy-sandbox-network',
                Driver: 'bridge',
                Internal: true, // No external access
                IPAM: {
                    Config: [{
                            Subnet: '172.20.0.0/16',
                            IPRange: '172.20.1.0/24'
                        }]
                }
            });
            console.log('Created isolated network:', network.id);
        }
        catch (error) {
            if (!error.message.includes('already exists')) {
                throw error;
            }
        }
    }
    async createBaseImage() {
        const dockerfile = `
FROM ubuntu:22.04

# Install minimal runtime environments
RUN apt-get update && apt-get install -y \\
    python3 \\
    nodejs \\
    g++ \\
    powershell \\
    bash \\
    strace \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m sandbox
USER sandbox

# Set up workspace
WORKDIR /workspace

# Add monitoring hooks
COPY monitoring.sh /usr/local/bin/monitoring.sh
RUN chmod +x /usr/local/bin/monitoring.sh

# Set up security constraints
ENV SANDBOX_MODE=enabled
ENV MONITORING_ENABLED=true

CMD ["/usr/local/bin/monitoring.sh"]
    `.trim();
        const tempDir = await this.createTempDirectory('base-image');
        const dockerfilePath = path.join(tempDir, 'Dockerfile');
        await fs.promises.writeFile(dockerfilePath, dockerfile);
        try {
            // Build the image
            const stream = await this.docker.buildImage({
                context: tempDir,
                src: ['Dockerfile']
            }, { t: 'prophecy-sandbox-base:latest' });
            await new Promise((resolve, reject) => {
                stream.on('data', () => { });
                stream.on('end', resolve);
                stream.on('error', reject);
            });
            console.log('Base sandbox image created successfully');
        }
        finally {
            await fs.promises.rm(tempDir, { recursive: true, force: true });
        }
    }
    parseMemoryLimit(limit) {
        // Convert memory limit to bytes
        const units = { k: 1024, m: 1024 * 1024, g: 1024 * 1024 * 1024 };
        const match = limit.toLowerCase().match(/^(\\d+)([kmg]?)$/);
        if (!match)
            return 512 * 1024 * 1024; // Default 512MB
        const [, size, unit] = match;
        return parseInt(size) * (units[unit] || 1);
    }
    parseCpuLimit(limit) {
        // Convert CPU limit to Docker quota (100000 = 1 CPU)
        const cpu = parseFloat(limit);
        return Math.floor(cpu * 100000);
    }
    async terminateExecution(executionId) {
        const execution = this.activeExecutions.get(executionId);
        if (!execution)
            return;
        execution.status = 'terminated';
        execution.endTime = new Date().toISOString();
        await this.cleanupResources(executionId);
        this.emit('executionTerminated', execution);
    }
    getExecution(executionId) {
        return this.activeExecutions.get(executionId);
    }
    getActiveExecutions() {
        return Array.from(this.activeExecutions.values());
    }
    async shutdown() {
        // Terminate all active executions
        const terminationPromises = Array.from(this.activeExecutions.keys())
            .map(id => this.terminateExecution(id));
        await Promise.all(terminationPromises);
        // Remove isolated network
        if (this.config.networkIsolated) {
            try {
                const network = this.docker.getNetwork('prophecy-sandbox-network');
                await network.remove();
            }
            catch (error) {
                // Network might not exist
            }
        }
        console.log('Prophecy Sandbox shutdown completed');
    }
}
exports.SandboxEnvironment = SandboxEnvironment;
//# sourceMappingURL=SandboxEnvironment.js.map