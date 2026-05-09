import { SecurityConfig, SecurityContext, SecurityViolation, SecurityViolationType } from './types';
import { EthicalUsageManager } from './EthicalUsageManager';
import { AuditLogger } from './AuditLogger';
import * as fs from 'fs';
import * as path from 'path';

export class SecurityManager {
  private config: SecurityConfig;
  private ethicalUsageManager: EthicalUsageManager;
  private auditLogger: AuditLogger;
  private workspaceRoot: string;

  constructor(workspaceRoot: string, config: SecurityConfig) {
    this.workspaceRoot = workspaceRoot;
    this.config = config;
    this.ethicalUsageManager = new EthicalUsageManager(config);
    this.auditLogger = new AuditLogger(workspaceRoot, config.enableAuditLogging, config.auditLogPath);
  }

  async initialize(): Promise<boolean> {
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

  validateAccess(filePath: string): SecurityContext {
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

    const context: SecurityContext = {
      workspaceRoot: this.workspaceRoot,
      filePath: normalizedPath,
      isTrusted,
      hasUserConsent,
      auditLogEnabled: this.config.enableAuditLogging
    };

    if (!isTrusted) {
      this.logSecurityViolation(SecurityViolationType.UNTRUSTED_WORKSPACE, 
        `Attempt to analyze file outside trusted workspace: ${filePath}`, context);
    }

    return context;
  }

  async confirmAnalysis(context: SecurityContext): Promise<boolean> {
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
      
      this.logSecurityViolation(SecurityViolationType.MISSING_CONSENT, 
        'User did not consent to analysis', context);
      return false;
    }

    return true;
  }

  private async promptUser(question: string): Promise<string> {
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
        
        const onData = (key: Buffer | string) => {
          const keyStr = typeof key === 'string' ? key : key.toString();
          
          if (keyStr === '\r' || keyStr === '\n' || keyStr === '\u0003') {
            cleanup();
            resolve(input.trim());
          } else if (keyStr === '\u007F') {
            input = input.slice(0, -1);
          } else if (keyStr >= ' ' && keyStr <= '~') {
            input += keyStr;
          }
        };
        
        const onError = (error: Error) => {
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
        
      } catch (error) {
        reject(error);
      }
    });
  }

  private isPathTrusted(filePath: string, workspaceRoot: string): boolean {
    const relative = path.relative(workspaceRoot, filePath);
    return !relative.startsWith('..') && !path.isAbsolute(relative);
  }

  private logSecurityViolation(type: SecurityViolationType, message: string, context: SecurityContext): void {
    const violation: SecurityViolation = {
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

  blockExternalRequest(url: string): boolean {
    if (this.config.blockExternalRequests) {
      console.error(`[BLOCKED] External request to ${url} - offline mode enabled`);
      return true;
    }
    return false;
  }

  ensureReadOnly(): boolean {
    if (!this.config.readonly) {
      console.warn('[WARNING] Write mode detected - SQL code modification is not recommended');
    }
    return this.config.readonly;
  }

  async logAnalysisStart(filePath: string): Promise<void> {
    await this.auditLogger.logScanStart(filePath);
  }

  async logAnalysisComplete(filePath: string, queryCount: number, vulnerabilityCount: number, duration: number): Promise<void> {
    await this.auditLogger.logScanComplete(filePath, queryCount, vulnerabilityCount, duration);
  }

  async logFileAnalyzed(filePath: string, fileSize: number): Promise<void> {
    await this.auditLogger.logFileAnalyzed(filePath, fileSize);
  }

  async logVulnerabilityFound(filePath: string): Promise<void> {
    await this.auditLogger.logVulnerabilityFound(filePath);
  }

  getAuditLogger(): AuditLogger {
    return this.auditLogger;
  }

  updateConfig(config: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...config };
    this.auditLogger.setEnabled(this.config.enableAuditLogging);
  }

  getConfig(): SecurityConfig {
    return { ...this.config };
  }

  getEthicalGuidelines(): string[] {
    return this.ethicalUsageManager.getEthicalGuidelines();
  }

  async shutdown(): Promise<void> {
    await this.auditLogger.logEntry({
      timestamp: new Date().toISOString(),
      action: 'scan_completed',
      analysisType: 'static'
    });
  }
}
