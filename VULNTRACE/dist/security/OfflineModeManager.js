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
exports.OfflineModeManager = void 0;
const fs = __importStar(require("fs"));
const NetworkMonitor_1 = require("./NetworkMonitor");
class OfflineModeManager {
    constructor() {
        this.offlineMode = true;
        this.networkMonitor = new NetworkMonitor_1.NetworkMonitor();
        this.networkMonitor.enableOfflineMode();
    }
    static getInstance() {
        if (!OfflineModeManager.instance) {
            OfflineModeManager.instance = new OfflineModeManager();
        }
        return OfflineModeManager.instance;
    }
    enableOfflineMode() {
        if (!this.offlineMode) {
            this.offlineMode = true;
            this.networkMonitor.enableOfflineMode();
            console.log('[SECURITY] Offline mode enabled - all external network requests blocked');
        }
    }
    disableOfflineMode() {
        if (this.offlineMode) {
            this.offlineMode = false;
            this.networkMonitor.disableOfflineMode();
            console.warn('[SECURITY] Offline mode disabled - external network requests allowed');
        }
    }
    isOfflineMode() {
        return this.offlineMode;
    }
    getBlockedRequests() {
        return this.networkMonitor.getBlockedRequests();
    }
    clearBlockedRequestsLog() {
        this.networkMonitor.clearBlockedRequests();
    }
    validateLocalFile(filePath) {
        try {
            const stats = fs.statSync(filePath);
            return stats.isFile();
        }
        catch (error) {
            return false;
        }
    }
    validateLocalDirectory(dirPath) {
        try {
            const stats = fs.statSync(dirPath);
            return stats.isDirectory();
        }
        catch (error) {
            return false;
        }
    }
    ensureLocalExecution() {
        if (!this.offlineMode) {
            throw new Error('[SECURITY] Local execution required - enable offline mode');
        }
    }
    async checkForExternalDependencies(code) {
        return NetworkMonitor_1.NetworkMonitor.scanForExternalCalls(code);
    }
    generateSecurityReport() {
        const report = this.networkMonitor.getSecurityReport();
        return {
            offlineMode: this.offlineMode,
            blockedRequestsCount: report.blockedRequestsCount,
            blockedRequests: report.blockedRequests,
            timestamp: report.timestamp
        };
    }
    // Get network monitoring wrappers for use in application
    getHttpWrapper() {
        return this.networkMonitor.getHttpWrapper();
    }
    getHttpsWrapper() {
        return this.networkMonitor.getHttpsWrapper();
    }
    getFetchWrapper() {
        return this.networkMonitor.getFetchWrapper();
    }
}
exports.OfflineModeManager = OfflineModeManager;
//# sourceMappingURL=OfflineModeManager.js.map