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
exports.NetworkMonitor = void 0;
const http = __importStar(require("http"));
const https = __importStar(require("https"));
const events_1 = require("events");
class NetworkMonitor extends events_1.EventEmitter {
    constructor() {
        super();
        this.blockedRequests = [];
        this.offlineMode = true;
        this.originalHttp = http.request;
        this.originalHttps = https.request;
        this.originalFetch = global.fetch;
    }
    enableOfflineMode() {
        if (!this.offlineMode) {
            this.offlineMode = true;
            // Install wrappers globally
            this.installWrappers();
            console.log('[SECURITY] Network monitoring enabled - external requests will be blocked');
        }
    }
    disableOfflineMode() {
        if (this.offlineMode) {
            this.offlineMode = false;
            // Restore original functions
            this.restoreWrappers();
            console.warn('[SECURITY] Network monitoring disabled - external requests allowed');
        }
    }
    installWrappers() {
        // Install HTTP wrapper globally
        http.request = this.wrapHttpRequest(this.originalHttp);
        // Install HTTPS wrapper globally
        https.request = this.wrapHttpsRequest(this.originalHttps);
        // Install fetch wrapper globally if available
        if (typeof global.fetch !== 'undefined') {
            global.fetch = this.wrapFetch(this.originalFetch);
        }
    }
    restoreWrappers() {
        // Restore original HTTP
        http.request = this.originalHttp;
        // Restore original HTTPS
        https.request = this.originalHttps;
        // Restore original fetch
        if (typeof global.fetch !== 'undefined') {
            global.fetch = this.originalFetch;
        }
    }
    isOfflineMode() {
        return this.offlineMode;
    }
    // Method to wrap HTTP requests with monitoring
    wrapHttpRequest(originalRequest) {
        const self = this;
        return function (options, callback) {
            const args = [options, callback];
            const url = self.extractUrl(args);
            const method = typeof options === 'string' ? 'GET' : options?.method || 'GET';
            const request = {
                url,
                method,
                timestamp: new Date().toISOString(),
                blocked: self.offlineMode,
                reason: self.offlineMode ? 'Offline mode enabled' : undefined
            };
            self.blockedRequests.push(request);
            self.emit('requestAttempt', request);
            if (self.offlineMode) {
                console.warn(`[BLOCKED] External HTTP request: ${method} ${url}`);
                const error = new Error(`[OFFLINE MODE] External HTTP request blocked: ${method} ${url}`);
                error.code = 'OFFLINE_MODE_BLOCKED';
                // Return a mock request object that will emit error
                const mockReq = new (require('events').EventEmitter)();
                process.nextTick(() => mockReq.emit('error', error));
                return mockReq;
            }
            // Allow the request if not in offline mode
            return originalRequest(options, callback);
        };
    }
    // Method to wrap HTTPS requests with monitoring
    wrapHttpsRequest(originalRequest) {
        const self = this;
        return function (options, callback) {
            const args = [options, callback];
            const url = self.extractUrl(args);
            const method = args[0]?.method || 'GET';
            const request = {
                url,
                method,
                timestamp: new Date().toISOString(),
                blocked: self.offlineMode,
                reason: self.offlineMode ? 'Offline mode enabled' : undefined
            };
            self.blockedRequests.push(request);
            self.emit('requestAttempt', request);
            if (self.offlineMode) {
                console.warn(`[BLOCKED] External HTTPS request: ${method} ${url}`);
                const error = new Error(`[OFFLINE MODE] External HTTPS request blocked: ${method} ${url}`);
                error.code = 'OFFLINE_MODE_BLOCKED';
                // Return a mock request object that will emit error
                const mockReq = new (require('events').EventEmitter)();
                process.nextTick(() => mockReq.emit('error', error));
                return mockReq;
            }
            return originalRequest(options, callback);
        };
    }
    // Method to wrap fetch requests with monitoring
    wrapFetch(originalFetch) {
        const self = this;
        return (input, init) => {
            const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url || 'unknown';
            const method = init?.method || 'GET';
            const request = {
                url,
                method,
                timestamp: new Date().toISOString(),
                blocked: this.offlineMode,
                reason: this.offlineMode ? 'Offline mode enabled' : undefined
            };
            this.blockedRequests.push(request);
            this.emit('requestAttempt', request);
            if (this.offlineMode) {
                console.warn(`[BLOCKED] External fetch request: ${method} ${url}`);
                const error = new Error(`[OFFLINE MODE] External fetch request blocked: ${method} ${url}`);
                error.code = 'OFFLINE_MODE_BLOCKED';
                return Promise.reject(error);
            }
            return originalFetch(input, init);
        };
    }
    // Get monitoring wrappers that can be used instead of original functions
    getHttpWrapper() {
        return this.wrapHttpRequest(this.originalHttp);
    }
    getHttpsWrapper() {
        return this.wrapHttpsRequest(this.originalHttps);
    }
    getFetchWrapper() {
        return this.wrapFetch(this.originalFetch);
    }
    extractUrl(args) {
        if (typeof args[0] === 'string') {
            return args[0];
        }
        if (args[0] instanceof URL) {
            return args[0].toString();
        }
        if (args[0] && typeof args[0] === 'object' && 'hostname' in args[0]) {
            const options = args[0];
            return options.hostname ? `${options.protocol || 'http:'}//${options.hostname}${options.path || ''}` : 'unknown';
        }
        return 'unknown';
    }
    getBlockedRequests() {
        return [...this.blockedRequests];
    }
    clearBlockedRequests() {
        this.blockedRequests = [];
    }
    getSecurityReport() {
        return {
            offlineMode: this.offlineMode,
            blockedRequestsCount: this.blockedRequests.length,
            blockedRequests: [...this.blockedRequests],
            timestamp: new Date().toISOString()
        };
    }
    // Check if code contains potential external calls
    static async scanForExternalCalls(code) {
        const patterns = [
            /https?:\/\/[^\s\)]+/g,
            /fetch\s*\(/g,
            /axios\./g,
            /request\s*\(/g,
            /http\.request/g,
            /https\.request/g,
            /\.get\s*\(/g,
            /\.post\s*\(/g
        ];
        const matches = [];
        patterns.forEach(pattern => {
            const found = code.match(pattern);
            if (found) {
                matches.push(...found);
            }
        });
        return Array.from(new Set(matches)); // Remove duplicates
    }
}
exports.NetworkMonitor = NetworkMonitor;
//# sourceMappingURL=NetworkMonitor.js.map