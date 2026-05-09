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
exports.RealFileSystemMonitor = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const child_process = __importStar(require("child_process"));
const events_1 = require("events");
class RealFileSystemMonitor extends events_1.EventEmitter {
    constructor(config) {
        super();
        this.isMonitoring = false;
        this.eventBuffer = [];
        this.activeProcesses = new Map();
        this.inotifyProcess = null;
        this.watchTimer = null;
        this.sensitivePaths = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/hosts',
            '/root/',
            '/home/',
            '/var/log/',
            '/proc/',
            '/sys/',
            '/dev/'
        ];
        this.config = config;
        this.validateConfig();
    }
    validateConfig() {
        if (!fs.existsSync(this.config.watchPath)) {
            throw new Error(`Watch path does not exist: ${this.config.watchPath}`);
        }
        if (!fs.statSync(this.config.watchPath).isDirectory()) {
            throw new Error(`Watch path is not a directory: ${this.config.watchPath}`);
        }
    }
    async startMonitoring() {
        if (this.isMonitoring) {
            throw new Error('File system monitoring already started');
        }
        console.log(`[FSMonitor] Starting monitoring: ${this.config.watchPath}`);
        try {
            // Start inotify process
            await this.startInotifyProcess();
            // Start process tracking
            if (this.config.trackProcesses) {
                this.startProcessTracking();
            }
            // Start anomaly detection
            this.startAnomalyDetection();
            this.isMonitoring = true;
            this.emit('monitoringStarted');
            console.log('[FSMonitor] File system monitoring started successfully');
        }
        catch (error) {
            console.error('[FSMonitor] Failed to start monitoring:', error);
            throw error;
        }
    }
    async startInotifyProcess() {
        const inotifyPath = '/usr/bin/inotifywait';
        // Check if inotifywait is available
        if (!fs.existsSync(inotifyPath)) {
            console.warn('[FSMonitor] inotifywait not found, using fallback polling method');
            this.startPollingFallback();
            return;
        }
        const args = [
            '-m', // Monitor mode
            '-r', // Recursive
            '--format', '%e %w%f',
            '--timefmt', '%Y-%m-%d %H:%M:%S'
        ];
        // Add event types
        const eventMap = {
            'create': 'create',
            'modify': 'modify',
            'delete': 'delete',
            'move': 'moved_to,moved_from',
            'access': 'access'
        };
        const eventsToWatch = this.config.events
            .map(event => eventMap[event])
            .filter(Boolean)
            .join(',');
        if (eventsToWatch) {
            args.push('-e', eventsToWatch);
        }
        args.push(this.config.watchPath);
        console.log(`[FSMonitor] Starting inotifywait with args: ${args.join(' ')}`);
        this.inotifyProcess = child_process.spawn(inotifyPath, args);
        this.inotifyProcess.stdout?.on('data', (data) => {
            this.processInotifyOutput(data.toString());
        });
        this.inotifyProcess.stderr?.on('data', (data) => {
            console.error('[FSMonitor] inotifywait error:', data.toString());
        });
        this.inotifyProcess.on('close', (code) => {
            console.log(`[FSMonitor] inotifywait process exited with code: ${code}`);
            if (this.isMonitoring && code !== 0) {
                console.warn('[FSMonitor] inotifywait crashed, restarting...');
                setTimeout(() => this.startInotifyProcess(), 1000);
            }
        });
        this.inotifyProcess.on('error', (error) => {
            console.error('[FSMonitor] inotifywait process error:', error);
            this.startPollingFallback();
        });
    }
    processInotifyOutput(output) {
        const lines = output.trim().split('\n');
        for (const line of lines) {
            if (!line.trim())
                continue;
            try {
                // Parse inotifywait output format: "EVENTS TIMESTAMP PATH"
                const match = line.match(/^(.+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)$/);
                if (!match)
                    continue;
                const [, eventsStr, timestampStr, filePath] = match;
                const timestamp = new Date(timestampStr);
                const events = eventsStr.split(',');
                for (const event of events) {
                    const fsEvent = this.createFileSystemEvent(event.trim(), filePath, timestamp);
                    if (fsEvent) {
                        this.handleFileSystemEvent(fsEvent);
                    }
                }
            }
            catch (error) {
                console.error('[FSMonitor] Failed to parse inotify output:', error);
            }
        }
    }
    createFileSystemEvent(eventType, filePath, timestamp) {
        try {
            // Map inotify events to our event types
            const eventMap = {
                'CREATE': 'create',
                'MODIFY': 'modify',
                'DELETE': 'delete',
                'MOVED_TO': 'create',
                'MOVED_FROM': 'delete',
                'ACCESS': 'access',
                'OPEN': 'access',
                'CLOSE': 'access'
            };
            const type = eventMap[eventType];
            if (!type)
                return null;
            // Check ignore patterns
            if (this.shouldIgnorePath(filePath)) {
                return null;
            }
            const event = {
                type,
                path: filePath,
                timestamp
            };
            // Get file metadata
            try {
                if (fs.existsSync(filePath)) {
                    const stats = fs.statSync(filePath);
                    event.size = stats.size;
                    event.permissions = (stats.mode & 0o777).toString(8);
                    event.uid = stats.uid;
                    event.gid = stats.gid;
                    event.inode = stats.ino;
                    // Calculate hash if enabled
                    if (this.config.calculateHashes && stats.isFile()) {
                        event.hash = this.calculateFileHash(filePath);
                    }
                }
            }
            catch (error) {
                // File might have been deleted
            }
            // Get process information if tracking is enabled
            if (this.config.trackProcesses) {
                const processInfo = this.getProcessForFile(filePath);
                if (processInfo) {
                    event.process = processInfo.name;
                    event.pid = processInfo.pid;
                }
            }
            return event;
        }
        catch (error) {
            console.error('[FSMonitor] Failed to create file system event:', error);
            return null;
        }
    }
    shouldIgnorePath(filePath) {
        // Check hidden files
        if (!this.config.includeHidden) {
            const basename = path.basename(filePath);
            if (basename.startsWith('.')) {
                return true;
            }
        }
        // Check ignore patterns
        for (const pattern of this.config.ignorePatterns) {
            if (filePath.includes(pattern)) {
                return true;
            }
        }
        return false;
    }
    calculateFileHash(filePath) {
        try {
            const crypto = require('crypto');
            const hash = crypto.createHash('sha256');
            const fileBuffer = fs.readFileSync(filePath);
            hash.update(fileBuffer);
            return hash.digest('hex');
        }
        catch (error) {
            console.error('[FSMonitor] Failed to calculate file hash:', error);
            return '';
        }
    }
    getProcessForFile(filePath) {
        // In a real implementation, this would use system calls to determine
        // which process is accessing the file
        // For demonstration, we'll return a mock process
        const mockProcesses = [
            { pid: 1234, name: 'node', command: 'node index.js', user: 'user', startTime: new Date(), parentPid: 1 },
            { pid: 5678, name: 'vim', command: 'vim file.txt', user: 'user', startTime: new Date(), parentPid: 1234 },
            { pid: 9012, name: 'bash', command: 'bash -c', user: 'user', startTime: new Date(), parentPid: 5678 }
        ];
        return mockProcesses[Math.floor(Math.random() * mockProcesses.length)];
    }
    handleFileSystemEvent(event) {
        // Add to buffer
        this.eventBuffer.push(event);
        // Maintain buffer size
        if (this.eventBuffer.length > this.config.bufferSize) {
            this.eventBuffer.shift();
        }
        // Emit event
        this.emit('fileSystemEvent', event);
        // Check for anomalies
        this.checkForAnomalies(event);
        console.log(`[FSMonitor] ${event.type}: ${event.path}`);
    }
    startPollingFallback() {
        console.log('[FSMonitor] Starting polling fallback method');
        const pollInterval = 5000; // 5 seconds
        const fileStates = new Map();
        const poll = () => {
            if (!this.isMonitoring)
                return;
            try {
                this.scanDirectory(this.config.watchPath, fileStates);
            }
            catch (error) {
                console.error('[FSMonitor] Polling error:', error);
            }
            setTimeout(poll, pollInterval);
        };
        poll();
    }
    scanDirectory(dirPath, fileStates) {
        const files = fs.readdirSync(dirPath);
        for (const file of files) {
            const filePath = path.join(dirPath, file);
            if (this.shouldIgnorePath(filePath)) {
                continue;
            }
            try {
                const stats = fs.statSync(filePath);
                const currentState = { size: stats.size, mtime: stats.mtime };
                const previousState = fileStates.get(filePath);
                if (!previousState) {
                    // New file
                    const event = this.createFileSystemEvent('create', filePath, new Date());
                    if (event)
                        this.handleFileSystemEvent(event);
                }
                else if (previousState.size !== currentState.size || previousState.mtime.getTime() !== currentState.mtime.getTime()) {
                    // Modified file
                    const event = this.createFileSystemEvent('modify', filePath, new Date());
                    if (event)
                        this.handleFileSystemEvent(event);
                }
                fileStates.set(filePath, currentState);
                // Recursively scan subdirectories
                if (stats.isDirectory() && this.config.recursive) {
                    this.scanDirectory(filePath, fileStates);
                }
            }
            catch (error) {
                // File might have been deleted
                if (fileStates.has(filePath)) {
                    const event = this.createFileSystemEvent('delete', filePath, new Date());
                    if (event)
                        this.handleFileSystemEvent(event);
                    fileStates.delete(filePath);
                }
            }
        }
    }
    startProcessTracking() {
        console.log('[FSMonitor] Starting process tracking');
        const updateProcesses = () => {
            if (!this.isMonitoring)
                return;
            try {
                // Get process list (simplified implementation)
                const processes = this.getProcessList();
                for (const process of processes) {
                    this.activeProcesses.set(process.pid, process);
                }
                // Clean up old processes
                const now = Date.now();
                for (const [pid, process] of this.activeProcesses) {
                    if (now - process.startTime.getTime() > 300000) { // 5 minutes
                        this.activeProcesses.delete(pid);
                    }
                }
            }
            catch (error) {
                console.error('[FSMonitor] Process tracking error:', error);
            }
            setTimeout(updateProcesses, 10000); // Update every 10 seconds
        };
        updateProcesses();
    }
    getProcessList() {
        // In a real implementation, this would read from /proc or use system APIs
        // For demonstration, we'll return mock processes
        return [
            { pid: 1, name: 'init', command: '/sbin/init', user: 'root', startTime: new Date(), parentPid: 0 },
            { pid: 1234, name: 'node', command: 'node index.js', user: 'user', startTime: new Date(), parentPid: 1 },
            { pid: 5678, name: 'vim', command: 'vim file.txt', user: 'user', startTime: new Date(), parentPid: 1234 }
        ];
    }
    startAnomalyDetection() {
        console.log('[FSMonitor] Starting anomaly detection');
        const detectAnomalies = () => {
            if (!this.isMonitoring)
                return;
            try {
                const anomalies = this.detectAnomalies();
                for (const anomaly of anomalies) {
                    this.emit('anomalyDetected', anomaly);
                    console.log(`[FSMonitor] Anomaly detected: ${anomaly.type} (${anomaly.severity})`);
                }
            }
            catch (error) {
                console.error('[FSMonitor] Anomaly detection error:', error);
            }
            setTimeout(detectAnomalies, 30000); // Check every 30 seconds
        };
        detectAnomalies();
    }
    detectAnomalies() {
        const anomalies = [];
        const now = new Date();
        const recentEvents = this.eventBuffer.filter(event => now.getTime() - event.timestamp.getTime() < 60000 // Last minute
        );
        // Check for rapid file creation
        const createEvents = recentEvents.filter(event => event.type === 'create');
        if (createEvents.length > 100) {
            anomalies.push({
                type: 'rapid_file_creation',
                severity: 'high',
                description: `Rapid file creation detected: ${createEvents.length} files in last minute`,
                events: createEvents,
                timestamp: now
            });
        }
        // Check for mass deletion
        const deleteEvents = recentEvents.filter(event => event.type === 'delete');
        if (deleteEvents.length > 50) {
            anomalies.push({
                type: 'mass_deletion',
                severity: 'critical',
                description: `Mass deletion detected: ${deleteEvents.length} files in last minute`,
                events: deleteEvents,
                timestamp: now
            });
        }
        // Check for sensitive file access
        const sensitiveEvents = recentEvents.filter(event => this.isSensitivePath(event.path));
        if (sensitiveEvents.length > 0) {
            anomalies.push({
                type: 'sensitive_access',
                severity: 'high',
                description: `Sensitive file access detected: ${sensitiveEvents.length} events`,
                events: sensitiveEvents,
                timestamp: now
            });
        }
        // Check for unusual permissions
        const unusualPermissionEvents = recentEvents.filter(event => {
            if (!event.permissions)
                return false;
            const perms = parseInt(event.permissions, 8);
            return (perms & 0o777) === 0o777; // World-writable
        });
        if (unusualPermissionEvents.length > 0) {
            anomalies.push({
                type: 'unusual_permissions',
                severity: 'medium',
                description: `Unusual file permissions detected: ${unusualPermissionEvents.length} files`,
                events: unusualPermissionEvents,
                timestamp: now
            });
        }
        // Check for potential crypto activity (many file modifications)
        const modifyEvents = recentEvents.filter(event => event.type === 'modify');
        if (modifyEvents.length > 200) {
            anomalies.push({
                type: 'crypto_activity',
                severity: 'critical',
                description: `Potential crypto activity detected: ${modifyEvents.length} file modifications`,
                events: modifyEvents,
                timestamp: now
            });
        }
        return anomalies;
    }
    isSensitivePath(filePath) {
        return this.sensitivePaths.some(sensitivePath => filePath.startsWith(sensitivePath));
    }
    stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }
        console.log('[FSMonitor] Stopping file system monitoring');
        this.isMonitoring = false;
        // Kill inotify process
        if (this.inotifyProcess) {
            this.inotifyProcess.kill();
            this.inotifyProcess = null;
        }
        // Clear timers
        if (this.watchTimer) {
            clearTimeout(this.watchTimer);
            this.watchTimer = null;
        }
        this.emit('monitoringStopped');
        console.log('[FSMonitor] File system monitoring stopped');
    }
    getEventHistory(count) {
        if (count) {
            return this.eventBuffer.slice(-count);
        }
        return [...this.eventBuffer];
    }
    getActiveProcesses() {
        return Array.from(this.activeProcesses.values());
    }
    getStatistics() {
        const now = new Date();
        const recentEvents = this.eventBuffer.filter(event => now.getTime() - event.timestamp.getTime() < 3600000 // Last hour
        );
        const eventCounts = recentEvents.reduce((counts, event) => {
            counts[event.type] = (counts[event.type] || 0) + 1;
            return counts;
        }, {});
        return {
            isMonitoring: this.isMonitoring,
            totalEvents: this.eventBuffer.length,
            recentEvents: recentEvents.length,
            eventCounts,
            activeProcesses: this.activeProcesses.size,
            watchPath: this.config.watchPath,
            bufferSize: this.config.bufferSize
        };
    }
    exportEvents(filePath, format = 'json') {
        try {
            const data = this.eventBuffer.map(event => ({
                ...event,
                timestamp: event.timestamp.toISOString()
            }));
            let output;
            if (format === 'csv') {
                const headers = ['timestamp', 'type', 'path', 'size', 'permissions', 'uid', 'gid', 'process', 'pid'];
                const csvRows = [headers.join(',')];
                for (const event of data) {
                    const row = headers.map(header => {
                        const value = event[header];
                        return value ? `"${value}"` : '';
                    });
                    csvRows.push(row.join(','));
                }
                output = csvRows.join('\n');
            }
            else {
                output = JSON.stringify(data, null, 2);
            }
            fs.writeFileSync(filePath, output);
            console.log(`[FSMonitor] Events exported to: ${filePath}`);
        }
        catch (error) {
            console.error('[FSMonitor] Failed to export events:', error);
            throw error;
        }
    }
    clearEventBuffer() {
        this.eventBuffer = [];
        console.log('[FSMonitor] Event buffer cleared');
    }
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        console.log('[FSMonitor] Configuration updated');
        // Restart monitoring if it's active
        if (this.isMonitoring) {
            this.stopMonitoring();
            setTimeout(() => this.startMonitoring(), 1000);
        }
    }
    getMonitorInfo() {
        return {
            isMonitoring: this.isMonitoring,
            config: this.config,
            bufferSize: this.eventBuffer.length,
            activeProcesses: this.activeProcesses.size,
            sensitivePaths: this.sensitivePaths.length
        };
    }
    destroy() {
        this.stopMonitoring();
        this.eventBuffer = [];
        this.activeProcesses.clear();
        console.log('[FSMonitor] File system monitor destroyed');
    }
}
exports.RealFileSystemMonitor = RealFileSystemMonitor;
//# sourceMappingURL=RealFileSystemMonitor.js.map