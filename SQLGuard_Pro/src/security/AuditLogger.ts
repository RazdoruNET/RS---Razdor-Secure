import { AuditLogEntry, SecurityContext } from './types';
import * as fs from 'fs';
import * as path from 'path';

export class AuditLogger {
  private enabled: boolean;
  private logPath: string;
  private workspaceRoot: string;

  constructor(workspaceRoot: string, enabled: boolean = true, logPath?: string) {
    this.workspaceRoot = workspaceRoot;
    this.enabled = enabled;
    this.logPath = logPath || path.join(workspaceRoot, '.sql-scanner-audit.log');
  }

  async logEntry(entry: Omit<AuditLogEntry, 'metadata'>): Promise<void> {
    if (!this.enabled) {
      return;
    }

    const fullEntry: AuditLogEntry = {
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
    } catch (error) {
      console.warn('Failed to write audit log:', error);
    }
  }

  async logScanStart(filePath: string): Promise<void> {
    await this.logEntry({
      timestamp: new Date().toISOString(),
      action: 'scan_started',
      filePath,
      analysisType: 'static'
    });
  }

  async logScanComplete(filePath: string, queryCount: number, vulnerabilityCount: number, duration: number): Promise<void> {
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

  async logFileAnalyzed(filePath: string, fileSize: number): Promise<void> {
    await this.logEntry({
      timestamp: new Date().toISOString(),
      action: 'file_analyzed',
      filePath,
      fileSize,
      analysisType: 'static'
    });
  }

  async logVulnerabilityFound(filePath: string): Promise<void> {
    await this.logEntry({
      timestamp: new Date().toISOString(),
      action: 'vulnerability_found',
      filePath,
      analysisType: 'static'
    });
  }

  getLogPath(): string {
    return this.logPath;
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  async clearLogs(): Promise<void> {
    try {
      await fs.promises.unlink(this.logPath);
    } catch (error) {
      // File doesn't exist or cannot be deleted
      console.warn('Failed to clear audit logs:', error);
    }
  }

  async getLogEntries(limit: number = 100): Promise<AuditLogEntry[]> {
    try {
      const content = await fs.promises.readFile(this.logPath, 'utf8');
      const lines = content.trim().split('\n').filter(line => line.length > 0);
      const entries = lines.slice(-limit).map(line => JSON.parse(line) as AuditLogEntry);
      return entries;
    } catch (error) {
      return [];
    }
  }
}
