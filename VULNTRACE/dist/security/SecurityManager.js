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
exports.SecurityManager = void 0;
const types_1 = require("./types");
const EthicalUsageManager_1 = require("./EthicalUsageManager");
const AuditLogger_1 = require("./AuditLogger");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class SecurityManager {
    constructor(workspaceRoot, config) {
        this.workspaceRoot = workspaceRoot;
        this.config = config;
        this.ethicalUsageManager = new EthicalUsageManager_1.EthicalUsageManager(config);
        this.auditLogger = new AuditLogger_1.AuditLogger(workspaceRoot, config.enableAuditLogging, config.auditLogPath);
    }
    async initialize() {
        const ethicalAccepted = await this.ethicalUsageManager.showEthicalWarning();
        if (!ethicalAccepted) {
            return false;
        }
        await this.auditLogger.logEntry({
            timestamp: new Date().toISOString(),
            action: 'scan_started',
            analysisType: 'static'
        });
        return true;
    }
    validateAccess(filePath) {
        // Input validation
        if (!filePath || typeof filePath !== 'string') {
            throw new Error('Invalid file path provided');
        }
        if (!fs.existsSync(filePath)) {
            throw new Error(`File does not exist: ${filePath}`);
        }
        const stats = fs.statSync(filePath);
        if (!stats.isFile()) {
            throw new Error(`Path is not a file: ${filePath}`);
        }
        const normalizedPath = path.resolve(filePath);
        const normalizedWorkspace = path.resolve(this.workspaceRoot);
        const isTrusted = this.isPathTrusted(normalizedPath, normalizedWorkspace);
        const hasUserConsent = this.config.requireConfirmation ? false : true;
        const context = {
            workspaceRoot: this.workspaceRoot,
            filePath: normalizedPath,
            isTrusted,
            hasUserConsent,
            auditLogEnabled: this.config.enableAuditLogging
        };
        if (!isTrusted) {
            this.logSecurityViolation(types_1.SecurityViolationType.UNTRUSTED_WORKSPACE, `Attempt to analyze file outside trusted workspace: ${filePath}`, context);
        }
        return context;
    }
    async confirmAnalysis(context) {
        if (!context.isTrusted) {
            return false;
        }
        if (this.config.requireConfirmation && !context.hasUserConsent) {
            console.log(`\nЗапрошен анализ файла: ${context.filePath}`);
            console.log('Это ваш собственный проект? (y/N)');
            const answer = await this.promptUser('');
            if (answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes') {
                context.hasUserConsent = true;
                return true;
            }
            this.logSecurityViolation(types_1.SecurityViolationType.MISSING_CONSENT, 'User did not consent to analysis', context);
            return false;
        }
        return true;
    }
    async promptUser(question) {
        // In IDE environment, this should be replaced with proper dialog
        // For now, we'll use console input with proper error handling
        return new Promise((resolve, reject) => {
            try {
                process.stdout.write(question);
                process.stdin.setRawMode(true);
                process.stdin.resume();
                process.stdin.setEncoding('utf8');
                let input = '';
                let isResolved = false;
                const cleanup = () => {
                    if (!isResolved) {
                        isResolved = true;
                        process.stdin.setRawMode(false);
                        process.stdin.pause();
                        process.stdin.removeListener('data', onData);
                        process.stdin.removeListener('error', onError);
                    }
                };
                const onData = (key) => {
                    const keyStr = typeof key === 'string' ? key : key.toString();
                    if (keyStr === '\r' || keyStr === '\n' || keyStr === '\u0003') {
                        cleanup();
                        resolve(input.trim());
                    }
                    else if (keyStr === '\u007F') {
                        input = input.slice(0, -1);
                    }
                    else if (keyStr >= ' ' && keyStr <= '~') {
                        input += keyStr;
                    }
                };
                const onError = (error) => {
                    cleanup();
                    reject(error);
                };
                process.stdin.on('data', onData);
                process.stdin.on('error', onError);
                // Timeout after 30 seconds
                const timeout = setTimeout(() => {
                    cleanup();
                    reject(new Error('User input timeout'));
                }, 30000);
            }
            catch (error) {
                reject(error);
            }
        });
    }
    isPathTrusted(filePath, workspaceRoot) {
        const relative = path.relative(workspaceRoot, filePath);
        return !relative.startsWith('..') && !path.isAbsolute(relative);
    }
    logSecurityViolation(type, message, context) {
        const violation = {
            type,
            message,
            context,
            timestamp: new Date().toISOString(),
            blocked: true
        };
        console.error(`[SECURITY VIOLATION] ${type}: ${message}`);
        if (this.config.enableAuditLogging) {
            this.auditLogger.logEntry({
                timestamp: violation.timestamp,
                action: 'scan_completed',
                analysisType: 'static'
            });
        }
    }
    blockExternalRequest(url) {
        if (this.config.blockExternalRequests) {
            console.error(`[BLOCKED] External request to ${url} - offline mode enabled`);
            return true;
        }
        return false;
    }
    ensureReadOnly() {
        if (!this.config.readonly) {
            console.warn('[WARNING] Write mode detected - SQL code modification is not recommended');
        }
        return this.config.readonly;
    }
    async logAnalysisStart(filePath) {
        await this.auditLogger.logScanStart(filePath);
    }
    async logAnalysisComplete(filePath, queryCount, vulnerabilityCount, duration) {
        await this.auditLogger.logScanComplete(filePath, queryCount, vulnerabilityCount, duration);
    }
    async logFileAnalyzed(filePath, fileSize) {
        await this.auditLogger.logFileAnalyzed(filePath, fileSize);
    }
    async logVulnerabilityFound(filePath) {
        await this.auditLogger.logVulnerabilityFound(filePath);
    }
    getAuditLogger() {
        return this.auditLogger;
    }
    updateConfig(config) {
        this.config = { ...this.config, ...config };
        this.auditLogger.setEnabled(this.config.enableAuditLogging);
    }
    getConfig() {
        return { ...this.config };
    }
    getEthicalGuidelines() {
        return this.ethicalUsageManager.getEthicalGuidelines();
    }
    async shutdown() {
        await this.auditLogger.logEntry({
            timestamp: new Date().toISOString(),
            action: 'scan_completed',
            analysisType: 'static'
        });
    }
}
exports.SecurityManager = SecurityManager;
//# sourceMappingURL=SecurityManager.js.map