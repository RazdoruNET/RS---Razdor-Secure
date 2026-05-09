import * as fs from 'fs';
import { NetworkMonitor, NetworkRequest } from './NetworkMonitor';

export class OfflineModeManager {
  private static instance: OfflineModeManager;
  private networkMonitor: NetworkMonitor;
  private offlineMode: boolean = true;

  private constructor() {
    this.networkMonitor = new NetworkMonitor();
    this.networkMonitor.enableOfflineMode();
  }

  static getInstance(): OfflineModeManager {
    if (!OfflineModeManager.instance) {
      OfflineModeManager.instance = new OfflineModeManager();
    }
    return OfflineModeManager.instance;
  }

  enableOfflineMode(): void {
    if (!this.offlineMode) {
      this.offlineMode = true;
      this.networkMonitor.enableOfflineMode();
      console.log('[SECURITY] Offline mode enabled - all external network requests blocked');
    }
  }

  disableOfflineMode(): void {
    if (this.offlineMode) {
      this.offlineMode = false;
      this.networkMonitor.disableOfflineMode();
      console.warn('[SECURITY] Offline mode disabled - external network requests allowed');
    }
  }

  isOfflineMode(): boolean {
    return this.offlineMode;
  }

  getBlockedRequests(): NetworkRequest[] {
    return this.networkMonitor.getBlockedRequests();
  }

  clearBlockedRequestsLog(): void {
    this.networkMonitor.clearBlockedRequests();
  }

  validateLocalFile(filePath: string): boolean {
    try {
      const stats = fs.statSync(filePath);
      return stats.isFile();
    } catch (error) {
      return false;
    }
  }

  validateLocalDirectory(dirPath: string): boolean {
    try {
      const stats = fs.statSync(dirPath);
      return stats.isDirectory();
    } catch (error) {
      return false;
    }
  }

  ensureLocalExecution(): void {
    if (!this.offlineMode) {
      throw new Error('[SECURITY] Local execution required - enable offline mode');
    }
  }

  async checkForExternalDependencies(code: string): Promise<string[]> {
    return NetworkMonitor.scanForExternalCalls(code);
  }

  generateSecurityReport(): {
    offlineMode: boolean;
    blockedRequestsCount: number;
    blockedRequests: NetworkRequest[];
    timestamp: string;
  } {
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
