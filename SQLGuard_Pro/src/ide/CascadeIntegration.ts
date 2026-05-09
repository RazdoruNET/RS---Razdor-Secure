import {
  Vulnerability,
  AnalysisResult,
  IDEIntegration,
  SQLQuery,
  Severity
} from '../types';
import { SQLVulnerabilityScanner } from '../core/SQLVulnerabilityScanner';
import * as fs from 'fs';
import * as path from 'path';
const glob = require('glob');

export class CascadeIntegration implements IDEIntegration {
  private scanner: SQLVulnerabilityScanner;
  private decorations: Map<string, any[]> = new Map();
  private tooltipProvider: any;
  private commandProvider: any;
  private statusBarItem: any;

  constructor(scanner: SQLVulnerabilityScanner) {
    this.scanner = scanner;
    this.setupIntegration();
  }

  // IDEIntegration interface implementation
  highlightVulnerabilities = (vulnerabilities: Vulnerability[]): void => {
    console.log(`Highlighting ${vulnerabilities.length} vulnerabilities`);
  };

  showTooltip = (vulnerability: Vulnerability): void => {
    console.log(`Showing tooltip for vulnerability: ${vulnerability.title}`);
  };

  openFile = (filePath: string, line: number, column: number): void => {
    console.log(`Opening file: ${filePath} at line ${line}, column ${column}`);
  };

  showReport = (result: AnalysisResult): void => {
    console.log(`Showing report with ${result.vulnerabilities.length} vulnerabilities`);
  };

  ignoreVulnerability = (vulnerabilityId: string): void => {
    console.log(`Ignoring vulnerability: ${vulnerabilityId}`);
  };

  private setupIntegration(): void {
    this.registerCommands();
    this.registerEventListeners();
    this.createStatusBarItem();
    this.setupTooltipProvider();
  }

  private registerCommands(): void {
    const commands = [
      {
        id: 'sqlScanner.analyzeCurrentFile',
        title: 'Analyze Current File',
        description: 'Analyze currently active SQL file for vulnerabilities'
      },
      {
        id: 'sqlScanner.analyzeWorkspace',
        title: 'Analyze Workspace',
        description: 'Analyze all SQL files in workspace'
      },
      {
        id: 'sqlScanner.generateReport',
        title: 'Generate Report',
        description: 'Generate a vulnerability report'
      },
      {
        id: 'sqlScanner.showSettings',
        title: 'Show Settings',
        description: 'Open SQL scanner settings'
      }
    ];

    commands.forEach(cmd => {
      console.log(`Registered command: ${cmd.id}`);
    });
  }

  private registerEventListeners(): void {
    this.onFileChanged = this.onFileChanged.bind(this);
    this.onFileOpened = this.onFileOpened.bind(this);
    this.onFileSaved = this.onFileSaved.bind(this);

    console.log('Registered event listeners for file changes');
  }

  private createStatusBarItem(): void {
    this.statusBarItem = {
      text: 'SQL Scanner: Ready',
      tooltip: 'SQL Vulnerability Scanner',
      command: 'sqlScanner.showSettings'
    };

    console.log('Created status bar item');
  }

  private setupTooltipProvider(): void {
    this.tooltipProvider = {
      provideHover: this.provideHover.bind(this)
    };

    console.log('Setup tooltip provider');
  }

  async analyzeCurrentFile(): Promise<void> {
    const activeFile = this.getActiveFile();
    
    if (!activeFile) {
      console.log('No active file found');
      return;
    }

    try {
      const content = await this.getFileContent(activeFile);
      const result = await this.scanner.analyzeFile(activeFile, content);
      
      this.highlightVulnerabilities(result.vulnerabilities);
      
      if (result.vulnerabilities.length > 0) {
        this.showNotification(`Found ${result.vulnerabilities.length} vulnerabilities`, 'warning');
      } else {
        this.showNotification('No vulnerabilities found', 'success');
      }
    } catch (error) {
      this.showNotification(`Analysis failed: ${error}`, 'error');
    }
  }

  async analyzeWorkspace(): Promise<void> {
    const sqlFiles = await this.getWorkspaceSQLFiles();
    
    if (sqlFiles.length === 0) {
      this.showNotification('No SQL files found in workspace', 'info');
      return;
    }

    try {
      const filePaths = sqlFiles.map(f => f.path);
      const results = await this.scanner.analyzeMultipleFiles(filePaths);
      const allVulnerabilities = results.flatMap(r => r.vulnerabilities);
      
      this.highlightVulnerabilities(allVulnerabilities);
      
      this.showNotification(`Analyzed ${sqlFiles.length} files, found ${allVulnerabilities.length} vulnerabilities`, 'info');
    } catch (error) {
      this.showNotification(`Workspace analysis failed: ${error}`, 'error');
    }
  }

  private async generateReport(): Promise<void> {
    const sqlFiles = await this.getWorkspaceSQLFiles();
    const filePaths = sqlFiles.map(f => f.path);
    const results = await this.scanner.analyzeMultipleFiles(filePaths);
    
    const combinedResult: AnalysisResult = {
      content: results.map(r => r.content).join('\n'),
      vulnerabilities: results.flatMap(r => r.vulnerabilities),
      queries: results.flatMap(r => r.queries),
      analysisType: 'combined',
      duration: results.reduce((sum, r) => sum + r.duration, 0),
      metadata: {
        workspaceRoot: process.cwd(),
        userAgent: 'SQL Vulnerability Scanner v1.0',
        version: '1.0.0'
      },
      statistics: {
        totalQueries: results.reduce((sum, r) => sum + (r.statistics?.totalQueries || 0), 0),
        vulnerabilitiesByType: {} as any,
        vulnerabilitiesBySeverity: {} as any,
        filesAnalyzed: results.length,
        linesAnalyzed: results.reduce((sum, r) => sum + (r.statistics?.linesAnalyzed || 0), 0),
        coverage: results.reduce((sum, r) => sum + (r.statistics?.coverage || 0), 0) / results.length
      }
    };

    this.showReport(combinedResult);
  }

  private clearHighlights(): void {
    this.decorations.clear();
    console.log('Cleared all vulnerability highlights');
  }

  private showHTMLReport(result: AnalysisResult): void {
    console.log('Generating vulnerability report...');
    
    const htmlContent = this.generateHTMLReport(result);
    console.log('Report generated:', htmlContent.substring(0, 100) + '...');
  }

  private generateHTMLReport(result: AnalysisResult): string {
    const criticalCount = result.vulnerabilities.filter(v => v.severity === 'critical').length;
    const highCount = result.vulnerabilities.filter(v => v.severity === 'high').length;

    return `
<!DOCTYPE html>
<html>
<head>
    <title>SQL Vulnerability Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; color: white; padding: 20px; border-radius: 5px; }
        .summary { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .summary-item { text-align: center; padding: 10px; border-radius: 3px; min-width: 100px; }
        .critical { background: #dc3545; color: white; }
        .high { background: #f57c00; color: white; }
        .medium { background: #ffc107; color: black; }
        .low { background: #28a745; color: white; }
        .vulnerability { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 10px; }
        .vulnerability-header { font-weight: bold; color: #333; }
        .vulnerability-content { margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SQL Vulnerability Report</h1>
        <p>Generated on ${new Date().toLocaleDateString()}</p>
    </div>

    <div class="summary">
        <div class="summary-item critical">
            <h2>${criticalCount}</h2>
            <p>Critical</p>
        </div>
        <div class="summary-item high">
            <h2>${highCount}</h2>
            <p>High</p>
        </div>
    </div>

    <h2>Vulnerabilities (${result.vulnerabilities.length})</h2>
    ${result.vulnerabilities.map(vuln => `
        <div class="vulnerability">
            <div class="vulnerability-header">
                ${vuln.title} - ${vuln.severity.toUpperCase()}
            </div>
            <div class="vulnerability-content">
                <p><strong>File:</strong> ${vuln.filePath}:${vuln.line}</p>
                <p><strong>Type:</strong> ${vuln.type}</p>
                <p><strong>Description:</strong> ${vuln.description}</p>
                <p><strong>Recommendation:</strong> ${vuln.recommendation}</p>
            </div>
        </div>
    `).join('')}
</body>
</html>
    `;
  }

  private updateStatusBar(vulnerabilities: Vulnerability[]): void {
    const criticalCount = vulnerabilities.filter(v => v.severity === 'critical').length;
    const highCount = vulnerabilities.filter(v => v.severity === 'high').length;
    
    if (this.statusBarItem) {
      this.statusBarItem.text = `SQL Scanner: ${criticalCount} Critical, ${highCount} High`;
    }
  }

  private onFileChanged(event: { fileName: string }): void {
    if (this.isSQLFile(event.fileName)) {
      this.analyzeCurrentFile();
    }
  }

  private onFileOpened(event: { fileName: string }): void {
    if (this.isSQLFile(event.fileName)) {
      this.analyzeCurrentFile();
    }
  }

  private onFileSaved(event: { fileName: string }): void {
    if (this.isSQLFile(event.fileName)) {
      this.analyzeCurrentFile();
    }
  }

  private getActiveFile(): string | null {
    const activeFile = process.env.ACTIVE_FILE || 'example.sql';
    return activeFile;
  }

  private async getFileContent(filePath: string): Promise<string> {
    try {
      return await fs.promises.readFile(filePath, 'utf-8');
    } catch (error) {
      console.error(`Failed to read file ${filePath}:`, error);
      return '';
    }
  }

  private async getWorkspaceSQLFiles(): Promise<Array<{ path: string; content: string }>> {
    const workspaceRoot = process.cwd();
    const sqlFiles = await this.findSQLFiles(workspaceRoot);
    
    const files: Array<{ path: string; content: string }> = [];
    
    for (const filePath of sqlFiles) {
      try {
        const content = await this.getFileContent(filePath);
        files.push({ path: filePath, content });
      } catch (error) {
        console.error(`Failed to read SQL file ${filePath}:`, error);
      }
    }
    
    return files;
  }

  private async findSQLFiles(directory: string): Promise<string[]> {
    const sqlPattern = '**/*.{sql,ddl,dml,proc,func}';
    const files = await glob(sqlPattern, { cwd: directory, ignore: ['**/node_modules/**', '**/dist/**'] });
    return files.map((file: string) => path.join(directory, file));
  }

  private isSQLFile(fileName: string): boolean {
    const sqlExtensions = ['.sql', '.ddl', '.dml', '.proc', '.func'];
    return sqlExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
  }

  private getVulnerabilityAtCursor(): Vulnerability | null {
    const allVulnerabilities: Vulnerability[] = [];
    this.decorations.forEach((vulns: any[]) => {
      allVulnerabilities.push(...vulns);
    });
    
    return allVulnerabilities.length > 0 ? allVulnerabilities[0] : null;
  }

  private provideHover(document: any, position: any): any {
    const vulnerability = this.getVulnerabilityAtCursor();
    
    if (vulnerability) {
      return {
        contents: {
          kind: 'markdown',
          value: this.createHoverMessage(vulnerability)
        }
      };
    }
    
    return null;
  }

  private createHoverMessage(vulnerability: Vulnerability): string {
    return `
# ${vulnerability.title}

## File Information
- **Path:** ${vulnerability.filePath}
- **Line:** ${vulnerability.line}
- **Column:** ${vulnerability.column}

## Vulnerability Details
- **Type:** ${vulnerability.type}
- **Severity:** ${vulnerability.severity.toUpperCase()}
- **Category:** ${vulnerability.category}
- **Confidence:** ${(vulnerability.confidence * 100).toFixed(0)}%

## Description
${vulnerability.description}

## Recommendation
${vulnerability.recommendation}

## SQL Query
\`\`\`sql
${vulnerability.sqlQuery}
\`\`\`

## References
${vulnerability.cwe ? `- **CWE:** ${vulnerability.cwe}` : ''}
${vulnerability.owasp ? `- **OWASP:** ${vulnerability.owasp}` : ''}
    `;
  }

  private showNotification(message: string, type: 'info' | 'warning' | 'error' | 'success'): void {
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
}
