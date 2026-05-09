import * as http from 'http';
import * as https from 'https';
import { EventEmitter } from 'events';

export interface NetworkRequest {
  url: string;
  method: string;
  timestamp: string;
  blocked: boolean;
  reason?: string;
}

export class NetworkMonitor extends EventEmitter {
  private blockedRequests: NetworkRequest[] = [];
  private offlineMode: boolean = true;
  private originalHttp: typeof http.request;
  private originalHttps: typeof https.request;
  private originalFetch: typeof global.fetch;

  constructor() {
    super();
    this.originalHttp = http.request;
    this.originalHttps = https.request;
    this.originalFetch = global.fetch;
  }

  enableOfflineMode(): void {
    if (!this.offlineMode) {
      this.offlineMode = true;
      // Install wrappers globally
      this.installWrappers();
      console.log('[SECURITY] Network monitoring enabled - external requests will be blocked');
    }
  }

  disableOfflineMode(): void {
    if (this.offlineMode) {
      this.offlineMode = false;
      // Restore original functions
      this.restoreWrappers();
      console.warn('[SECURITY] Network monitoring disabled - external requests allowed');
    }
  }

  private installWrappers(): void {
    // Install HTTP wrapper globally
    (http as any).request = this.wrapHttpRequest(this.originalHttp);
    // Install HTTPS wrapper globally
    (https as any).request = this.wrapHttpsRequest(this.originalHttps);
    // Install fetch wrapper globally if available
    if (typeof global.fetch !== 'undefined') {
      (global as any).fetch = this.wrapFetch(this.originalFetch);
    }
  }

  private restoreWrappers(): void {
    // Restore original HTTP
    (http as any).request = this.originalHttp;
    // Restore original HTTPS
    (https as any).request = this.originalHttps;
    // Restore original fetch
    if (typeof global.fetch !== 'undefined') {
      (global as any).fetch = this.originalFetch;
    }
  }

  isOfflineMode(): boolean {
    return this.offlineMode;
  }

  // Method to wrap HTTP requests with monitoring
  wrapHttpRequest(originalRequest: typeof http.request): typeof http.request {
    const self = this;
    return function(options: any, callback?: any): any {
      const args = [options, callback];
      const extractedUrl = self.extractUrl(args);
      const method = typeof options === 'string' ? 'GET' : (options as http.RequestOptions)?.method || 'GET';
      
      const request: NetworkRequest = {
        url: extractedUrl,
        method,
        timestamp: new Date().toISOString(),
        blocked: self.offlineMode,
        reason: self.offlineMode ? 'Offline mode enabled' : undefined
      };

      self.blockedRequests.push(request);
      self.emit('requestAttempt', request);

      if (self.offlineMode) {
        console.warn(`[BLOCKED] External HTTP request: ${method} ${extractedUrl}`);
        const error = new Error(`[OFFLINE MODE] External HTTP request blocked: ${method} ${extractedUrl}`);
        (error as any).code = 'OFFLINE_MODE_BLOCKED';
        // Return a mock request object that will emit error
        const mockReq = new (require('events').EventEmitter)();
        process.nextTick(() => mockReq.emit('error', error));
        return mockReq as any;
      }

      // Allow the request if not in offline mode
      return originalRequest(options, callback);
    };
  }

  // Method to wrap HTTPS requests with monitoring
  wrapHttpsRequest(originalRequest: typeof https.request): typeof https.request {
    const self = this;
    return function(options: any, callback?: any): any {
      const args = [options, callback];
      const extractedUrl = self.extractUrl(args);
      const method = typeof options === 'string' ? 'GET' : (options as https.RequestOptions)?.method || 'GET';
      
      const request: NetworkRequest = {
        url: extractedUrl,
        method,
        timestamp: new Date().toISOString(),
        blocked: self.offlineMode,
        reason: self.offlineMode ? 'Offline mode enabled' : undefined
      };

      self.blockedRequests.push(request);
      self.emit('requestAttempt', request);

      if (self.offlineMode) {
        console.warn(`[BLOCKED] External HTTPS request: ${method} ${extractedUrl}`);
        const error = new Error(`[OFFLINE MODE] External HTTPS request blocked: ${method} ${extractedUrl}`);
        (error as any).code = 'OFFLINE_MODE_BLOCKED';
        // Return a mock request object that will emit error
        const mockReq = new (require('events').EventEmitter)();
        process.nextTick(() => mockReq.emit('error', error));
        return mockReq as any;
      }

      return originalRequest(options, callback);
    };
  }

  // Method to wrap fetch requests with monitoring
  wrapFetch(originalFetch: typeof global.fetch): typeof global.fetch {
    const self = this;
    return (input: RequestInfo | string | URL, init?: RequestInit): Promise<Response> => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url || 'unknown';
      const method = init?.method || 'GET';
      
      const request: NetworkRequest = {
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
        (error as any).code = 'OFFLINE_MODE_BLOCKED';
        return Promise.reject(error);
      }

      return originalFetch(input, init);
    };
  }

  // Get monitoring wrappers that can be used instead of original functions
  getHttpWrapper(): typeof http.request {
    return this.wrapHttpRequest(this.originalHttp);
  }

  getHttpsWrapper(): typeof https.request {
    return this.wrapHttpsRequest(this.originalHttps);
  }

  getFetchWrapper(): typeof global.fetch {
    return this.wrapFetch(this.originalFetch);
  }

  private extractUrl(args: any[]): string {
    if (typeof args[0] === 'string') {
      return args[0];
    }
    if (args[0] instanceof URL) {
      return args[0].toString();
    }
    if (args[0] && typeof args[0] === 'object' && 'hostname' in args[0]) {
      const options = args[0] as http.RequestOptions;
      return options.hostname ? `${options.protocol || 'http:'}//${options.hostname}${options.path || ''}` : 'unknown';
    }
    return 'unknown';
  }

  getBlockedRequests(): NetworkRequest[] {
    return [...this.blockedRequests];
  }

  clearBlockedRequests(): void {
    this.blockedRequests = [];
  }

  getSecurityReport(): {
    offlineMode: boolean;
    blockedRequestsCount: number;
    blockedRequests: NetworkRequest[];
    timestamp: string;
  } {
    return {
      offlineMode: this.offlineMode,
      blockedRequestsCount: this.blockedRequests.length,
      blockedRequests: [...this.blockedRequests],
      timestamp: new Date().toISOString()
    };
  }

  // Check if code contains potential external calls
  static async scanForExternalCalls(code: string): Promise<string[]> {
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

    const matches: string[] = [];
    
    patterns.forEach(pattern => {
      const found = code.match(pattern);
      if (found) {
        matches.push(...found);
      }
    });

    return Array.from(new Set(matches)); // Remove duplicates
  }
}
