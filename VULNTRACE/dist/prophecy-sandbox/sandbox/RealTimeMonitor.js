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
exports.RealTimeMonitor = void 0;
const events_1 = require("events");
const child_process = __importStar(require("child_process"));
const fs = __importStar(require("fs"));
class RealTimeMonitor extends events_1.EventEmitter {
    constructor(config) {
        super();
        this.isMonitoring = false;
        this.logBuffer = [];
        this.syscallBuffer = [];
        this.networkBuffer = [];
        this.fileBuffer = [];
        this.config = config;
        this.pcapFilePath = `/tmp/network-capture-${Date.now()}.pcap`;
    }
    async startMonitoring(containerId, executionId) {
        if (this.isMonitoring) {
            throw new Error('Monitoring already active');
        }
        this.isMonitoring = true;
        this.logBuffer = [];
        this.syscallBuffer = [];
        this.networkBuffer = [];
        this.fileBuffer = [];
        try {
            // Start strace monitoring
            if (this.config.enableStrace) {
                await this.startStraceMonitoring(containerId, executionId);
            }
            // Start network monitoring
            if (this.config.enableNetworkMonitor) {
                await this.startNetworkMonitoring(containerId, executionId);
            }
            // Start file monitoring
            if (this.config.enableFileMonitor) {
                await this.startFileMonitoring(containerId, executionId);
            }
            this.addLog('info', 'monitor', 'Real-time monitoring started');
            this.emit('monitoringStarted', { executionId, containerId });
        }
        catch (error) {
            this.isMonitoring = false;
            throw error;
        }
    }
    async stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }
        this.isMonitoring = false;
        // Stop all monitoring processes
        if (this.straceProcess) {
            this.straceProcess.kill('SIGTERM');
            this.straceProcess = undefined;
        }
        if (this.tcpdumpProcess) {
            this.tcpdumpProcess.kill('SIGTERM');
            this.tcpdumpProcess = undefined;
        }
        if (this.inotifyProcess) {
            this.inotifyProcess.kill('SIGTERM');
            this.inotifyProcess = undefined;
        }
        // Stop pcap parser interval
        if (this.pcapParserInterval) {
            clearInterval(this.pcapParserInterval);
            this.pcapParserInterval = undefined;
        }
        // Clean up pcap file
        if (fs.existsSync(this.pcapFilePath)) {
            try {
                fs.unlinkSync(this.pcapFilePath);
            }
            catch (error) {
                this.addLog('warn', 'network', `Failed to delete pcap file: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
        }
        this.addLog('info', 'monitor', 'Real-time monitoring stopped');
        this.emit('monitoringStopped');
        // Flush remaining buffers
        this.flushBuffers();
    }
    async startStraceMonitoring(containerId, executionId) {
        return new Promise((resolve, reject) => {
            const straceCmd = [
                'docker', 'exec', containerId,
                'strace',
                '-f', // Follow forks
                '-e', 'trace=all', // Trace all syscalls
                '-e', 'signal=!SIGCHLD', // Ignore SIGCHLD
                '-o', '/tmp/strace-output.log', // Output to file
                '-p', '1' // Trace PID 1 (main process)
            ];
            this.straceProcess = child_process.spawn(straceCmd[0], straceCmd.slice(1), {
                stdio: ['ignore', 'pipe', 'pipe']
            });
            this.straceProcess.on('error', (error) => {
                this.addLog('error', 'strace', `Strace process error: ${error.message}`);
                reject(error);
            });
            this.straceProcess.on('exit', (code, signal) => {
                if (code !== 0 && signal !== 'SIGTERM') {
                    this.addLog('warn', 'strace', `Strace exited with code ${code}`);
                }
            });
            // Start parsing strace output
            this.parseStraceOutput(containerId, executionId);
            resolve();
        });
    }
    async startNetworkMonitoring(containerId, executionId) {
        return new Promise((resolve, reject) => {
            // Get container network interface
            const networkCmd = [
                'docker', 'exec', containerId,
                'tcpdump',
                '-i', 'any',
                '-n', // Don't resolve hostnames
                '-w', this.pcapFilePath
            ];
            this.tcpdumpProcess = child_process.spawn(networkCmd[0], networkCmd.slice(1), {
                stdio: ['ignore', 'pipe', 'pipe']
            });
            this.tcpdumpProcess.on('error', (error) => {
                this.addLog('error', 'network', `Tcpdump process error: ${error.message}`);
                reject(error);
            });
            this.tcpdumpProcess.on('exit', (code, signal) => {
                if (code !== 0 && signal !== 'SIGTERM') {
                    this.addLog('warn', 'network', `Tcpdump exited with code ${code}`);
                }
            });
            // Start parsing network output
            this.parseNetworkOutput(containerId, executionId);
            resolve();
        });
    }
    async startFileMonitoring(containerId, executionId) {
        return new Promise((resolve, reject) => {
            // Use inotifywait for file monitoring
            const fileCmd = [
                'docker', 'exec', containerId,
                'inotifywait',
                '-m', // Monitor recursively
                '-r', // Recursive
                '--format', '%w%f %e %T',
                '-e', 'create,modify,delete,move,attrib',
                '/workspace'
            ];
            this.inotifyProcess = child_process.spawn(fileCmd[0], fileCmd.slice(1), {
                stdio: ['ignore', 'pipe', 'pipe']
            });
            this.inotifyProcess.on('error', (error) => {
                this.addLog('error', 'file', `Inotify process error: ${error}`);
                reject(error);
            });
            this.inotifyProcess.on('exit', (code, signal) => {
                if (code !== 0 && signal !== 'SIGTERM') {
                    this.addLog('warn', 'file', `Inotify exited with code ${code}`);
                }
            });
            // Start parsing file output
            this.parseFileOutput(containerId, executionId);
            resolve();
        });
    }
    parseStraceOutput(containerId, executionId) {
        if (!this.straceProcess)
            return;
        const readline = require('readline');
        const rl = readline.createInterface({
            input: this.straceProcess.stdout,
            crlfDelay: Infinity
        });
        rl.on('line', (line) => {
            try {
                const syscall = this.parseSyscallLine(line, executionId);
                if (syscall) {
                    this.syscallBuffer.push(syscall);
                    this.emit('syscall', syscall);
                }
            }
            catch (error) {
                this.addLog('warn', 'strace', `Failed to parse syscall line: ${line}`);
            }
        });
        rl.on('error', (error) => {
            this.addLog('error', 'strace', `Readline error: ${error.message}`);
        });
    }
    parseSyscallLine(line, executionId) {
        // Parse strace output format: PID syscall(args) = return
        const match = line.match(/^(\d+)\s+(\w+)\((.*)\)\s*=\s*(.*)$/);
        if (!match)
            return null;
        const [, pid, syscall, argsStr, result] = match;
        // Parse arguments
        let args = [];
        if (argsStr && argsStr !== 'void') {
            // Simple argument parsing - split by comma, handle quotes
            args = this.parseSyscallArgs(argsStr);
        }
        return {
            timestamp: new Date().toISOString(),
            syscall,
            args,
            result: parseInt(result) || 0,
            process: `pid_${pid}`
        };
    }
    parseSyscallArgs(argsStr) {
        const args = [];
        let current = '';
        let inQuotes = false;
        let depth = 0;
        for (let i = 0; i < argsStr.length; i++) {
            const char = argsStr[i];
            if (char === '"' && (i === 0 || argsStr[i - 1] !== '\\')) {
                inQuotes = !inQuotes;
                current += char;
            }
            else if (char === '[' && !inQuotes) {
                depth++;
                current += char;
            }
            else if (char === ']' && !inQuotes) {
                depth--;
                current += char;
            }
            else if (char === ',' && !inQuotes && depth === 0) {
                args.push(current.trim());
                current = '';
            }
            else {
                current += char;
            }
        }
        if (current.trim()) {
            args.push(current.trim());
        }
        return args;
    }
    parseNetworkOutput(containerId, executionId) {
        // Parse pcap file periodically to detect network activity
        this.pcapParserInterval = setInterval(() => {
            if (!this.isMonitoring)
                return;
            // Check if pcap file exists and has content
            if (!fs.existsSync(this.pcapFilePath)) {
                return;
            }
            try {
                const stats = fs.statSync(this.pcapFilePath);
                if (stats.size === 0) {
                    return;
                }
                // Parse the pcap file
                const PcapParser = require('pcap-parser');
                const parser = new PcapParser(this.pcapFilePath);
                let packetCount = 0;
                let totalSize = 0;
                parser.on('packet', (packet) => {
                    if (!this.isMonitoring)
                        return;
                    if (packetCount > 100)
                        return; // Limit packets per interval
                    const networkActivity = this.extractNetworkActivity(packet, executionId);
                    if (networkActivity) {
                        this.networkBuffer.push(networkActivity);
                        this.emit('networkActivity', networkActivity);
                        totalSize += networkActivity.size;
                        packetCount++;
                    }
                });
                parser.on('error', (error) => {
                    this.addLog('warn', 'network', `Pcap parse error: ${error.message}`);
                });
                parser.on('complete', () => {
                    if (packetCount > 0) {
                        this.addLog('debug', 'network', `Parsed ${packetCount} packets, total size: ${totalSize} bytes`);
                    }
                });
                parser.parse();
                // Clear the pcap file after parsing to avoid re-reading
                fs.truncateSync(this.pcapFilePath, 0);
            }
            catch (error) {
                this.addLog('warn', 'network', `Failed to parse pcap: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
        }, 3000); // Parse every 3 seconds
    }
    extractNetworkActivity(packet, executionId) {
        try {
            const data = packet.data;
            if (!data || data.length === 0)
                return null;
            // Basic Ethernet frame parsing
            const ethType = data.readUInt16BE(12);
            // IPv4 (0x0800)
            if (ethType === 0x0800) {
                const ipHeaderLength = (data[14] & 0x0F) * 4;
                const protocol = data[23];
                const sourceIP = `${data[26]}.${data[27]}.${data[28]}.${data[29]}`;
                const destIP = `${data[30]}.${data[31]}.${data[32]}.${data[33]}`;
                let protocolName = 'unknown';
                let port = 0;
                // TCP (6)
                if (protocol === 6 && data.length >= 14 + ipHeaderLength + 20) {
                    protocolName = 'tcp';
                    port = data.readUInt16BE(14 + ipHeaderLength);
                }
                // UDP (17)
                else if (protocol === 17 && data.length >= 14 + ipHeaderLength + 8) {
                    protocolName = 'udp';
                    port = data.readUInt16BE(14 + ipHeaderLength);
                }
                // ICMP (1)
                else if (protocol === 1) {
                    protocolName = 'icmp';
                }
                return {
                    timestamp: new Date().toISOString(),
                    protocol: protocolName,
                    source: sourceIP,
                    destination: destIP,
                    port,
                    size: data.length,
                    blocked: this.config.networkInterface === 'none'
                };
            }
            return null;
        }
        catch (error) {
            return null;
        }
    }
    parseFileOutput(containerId, executionId) {
        if (!this.inotifyProcess)
            return;
        const readline = require('readline');
        const rl = readline.createInterface({
            input: this.inotifyProcess.stdout,
            crlfDelay: Infinity
        });
        rl.on('line', (line) => {
            try {
                const fileChange = this.parseFileChangeLine(line, executionId);
                if (fileChange) {
                    this.fileBuffer.push(fileChange);
                    this.emit('fileChange', fileChange);
                }
            }
            catch (error) {
                this.addLog('warn', 'file', `Failed to parse file line: ${line}`);
            }
        });
    }
    parseFileChangeLine(line, executionId) {
        // Parse inotifywait output: PATH EVENT(S) TIMESTAMP
        const parts = line.trim().split(/\s+/);
        if (parts.length < 2)
            return null;
        const [filePath, ...eventParts] = parts;
        const events = eventParts.join(' ').replace(/["']/g, '');
        const action = this.mapEventToAction(events);
        if (!action)
            return null;
        return {
            timestamp: new Date().toISOString(),
            action,
            path: filePath,
            hash: action === 'create' || action === 'modify' ? this.calculateFileHash(filePath) || '' : undefined,
            size: action === 'create' || action === 'modify' ? this.getFileSize(filePath) : undefined
        };
    }
    mapEventToAction(events) {
        if (events.includes('CREATE'))
            return 'create';
        if (events.includes('MODIFY') || events.includes('ATTRIB'))
            return 'modify';
        if (events.includes('DELETE'))
            return 'delete';
        if (events.includes('MOVED_FROM') || events.includes('MOVED_TO'))
            return 'rename';
        return null;
    }
    calculateFileHash(filePath) {
        try {
            const crypto = require('crypto');
            const data = fs.readFileSync(filePath);
            return crypto.createHash('sha256').update(data).digest('hex');
        }
        catch (error) {
            return undefined;
        }
    }
    getFileSize(filePath) {
        try {
            const stats = fs.statSync(filePath);
            return stats.size;
        }
        catch (error) {
            return 0;
        }
    }
    addLog(level, source, message) {
        const log = {
            timestamp: new Date().toISOString(),
            level,
            source,
            message
        };
        this.logBuffer.push(log);
        this.emit('log', log);
    }
    flushBuffers() {
        // Emit final buffer contents
        this.syscallBuffer.forEach(syscall => this.emit('syscall', syscall));
        this.networkBuffer.forEach(network => this.emit('networkActivity', network));
        this.fileBuffer.forEach(file => this.emit('fileChange', file));
        this.logBuffer.forEach(log => this.emit('log', log));
    }
    // Public API methods
    getLogs() {
        return [...this.logBuffer];
    }
    getSyscalls() {
        return [...this.syscallBuffer];
    }
    getNetworkActivity() {
        return [...this.networkBuffer];
    }
    getFileChanges() {
        return [...this.fileBuffer];
    }
    getMonitoringStats() {
        return {
            logCount: this.logBuffer.length,
            syscallCount: this.syscallBuffer.length,
            networkCount: this.networkBuffer.length,
            fileCount: this.fileBuffer.length,
            isMonitoring: this.isMonitoring
        };
    }
    clearBuffers() {
        this.logBuffer = [];
        this.syscallBuffer = [];
        this.networkBuffer = [];
        this.fileBuffer = [];
    }
}
exports.RealTimeMonitor = RealTimeMonitor;
//# sourceMappingURL=RealTimeMonitor.js.map