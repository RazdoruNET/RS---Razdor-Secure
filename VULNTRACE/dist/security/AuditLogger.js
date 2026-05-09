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
exports.AuditLogger = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class AuditLogger {
    constructor(workspaceRoot, enabled = true, logPath) {
        this.workspaceRoot = workspaceRoot;
        this.enabled = enabled;
        this.logPath = logPath || path.join(workspaceRoot, '.sql-scanner-audit.log');
    }
    async logEntry(entry) {
        if (!this.enabled) {
            return;
        }
        const fullEntry = {
            ...entry,
            metadata: {
                workspaceRoot: this.workspaceRoot,
                userAgent: 'SQL Vulnerability Scanner v1.0.0',
                version: '1.0.0'
            }
        };
        try {
            const logLine = JSON.stringify(fullEntry) + '\n';
            await fs.promises.appendFile(this.logPath, logLine, 'utf8');
        }
        catch (error) {
            console.warn('Failed to write audit log:', error);
        }
    }
    async logScanStart(filePath) {
        await this.logEntry({
            timestamp: new Date().toISOString(),
            action: 'scan_started',
            filePath,
            analysisType: 'static'
        });
    }
    async logScanComplete(filePath, queryCount, vulnerabilityCount, duration) {
        await this.logEntry({
            timestamp: new Date().toISOString(),
            action: 'scan_completed',
            filePath,
            queryCount,
            vulnerabilityCount,
            analysisType: 'static',
            duration
        });
    }
    async logFileAnalyzed(filePath, fileSize) {
        await this.logEntry({
            timestamp: new Date().toISOString(),
            action: 'file_analyzed',
            filePath,
            fileSize,
            analysisType: 'static'
        });
    }
    async logVulnerabilityFound(filePath) {
        await this.logEntry({
            timestamp: new Date().toISOString(),
            action: 'vulnerability_found',
            filePath,
            analysisType: 'static'
        });
    }
    getLogPath() {
        return this.logPath;
    }
    isEnabled() {
        return this.enabled;
    }
    setEnabled(enabled) {
        this.enabled = enabled;
    }
    async clearLogs() {
        try {
            await fs.promises.unlink(this.logPath);
        }
        catch (error) {
            // File doesn't exist or cannot be deleted
            console.warn('Failed to clear audit logs:', error);
        }
    }
    async getLogEntries(limit = 100) {
        try {
            const content = await fs.promises.readFile(this.logPath, 'utf8');
            const lines = content.trim().split('\n').filter(line => line.length > 0);
            const entries = lines.slice(-limit).map(line => JSON.parse(line));
            return entries;
        }
        catch (error) {
            return [];
        }
    }
}
exports.AuditLogger = AuditLogger;
//# sourceMappingURL=AuditLogger.js.map