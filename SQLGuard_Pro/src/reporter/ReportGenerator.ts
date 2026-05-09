import {
  AnalysisResult,
  Vulnerability,
  ReportConfig,
  AppConfig,
  Severity,
  VulnerabilityType
} from '../types';
import puppeteer from 'puppeteer';
import * as fs from 'fs';
import * as path from 'path';

export class ReportGenerator {
  private config: AppConfig;

  constructor(config: AppConfig) {
    this.config = config;
  }

  async generate(result: AnalysisResult, format: 'json' | 'html' | 'pdf' | 'sarif' = 'json', reportConfig?: Partial<ReportConfig>): Promise<string> {
    const config = this.mergeReportConfig(reportConfig);

    switch (format) {
      case 'json':
        return this.generateJSONReport(result, config);
      case 'html':
        return this.generateHTMLReport(result, config);
      case 'pdf':
        return await this.generatePDFReport(result, config);
      case 'sarif':
        return this.generateSARIFReport(result, config);
      default:
        throw new Error(`Unsupported report format: ${format}`);
    }
  }

  private mergeReportConfig(partial?: Partial<ReportConfig>): ReportConfig {
    return {
      format: 'json',
      includeStatistics: true,
      includeCodeExamples: true,
      groupBy: 'type',
      filter: {
        severities: [],
        types: [],
        files: []
      },
      ...partial
    };
  }

  private generateJSONReport(result: AnalysisResult, config: ReportConfig): string {
    const filteredResult = this.filterResult(result, config);
    const report = {
      metadata: {
        generatedAt: new Date().toISOString(),
        scanner: 'SQL Vulnerability Scanner v1.0.0',
        duration: result.duration,
        filesAnalyzed: result.statistics?.filesAnalyzed || 1
      },
      summary: config.includeStatistics ? this.generateSummary(filteredResult) : undefined,
      vulnerabilities: this.groupVulnerabilities(filteredResult.vulnerabilities, config.groupBy),
      statistics: config.includeStatistics ? filteredResult.statistics : undefined
    };

    return JSON.stringify(report, null, 2);
  }

  private generateHTMLReport(result: AnalysisResult, config: ReportConfig): string {
    const filteredResult = this.filterResult(result, config);
    const vulnerabilities = this.groupVulnerabilities(filteredResult.vulnerabilities, config.groupBy);
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Vulnerability Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }
        .severity-critical { border-left-color: #dc3545; }
        .severity-high { border-left-color: #fd7e14; }
        .severity-medium { border-left-color: #ffc107; }
        .severity-low { border-left-color: #28a745; }
        .vulnerability { border: 1px solid #dee2e6; border-radius: 6px; margin-bottom: 20px; overflow: hidden; }
        .vulnerability-header { padding: 15px; font-weight: bold; cursor: pointer; }
        .vulnerability-content { padding: 15px; background: #f8f9fa; display: none; }
        .vulnerability-content.show { display: block; }
        .code-block { background: #f1f1f1; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; }
        .badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .badge-critical { background: #dc3545; color: white; }
        .badge-high { background: #fd7e14; color: white; }
        .badge-medium { background: #ffc107; color: black; }
        .badge-low { background: #28a745; color: white; }
        .collapsible { background: #007bff; color: white; cursor: pointer; padding: 10px; border: none; text-align: left; width: 100%; font-size: 16px; }
        .collapsible:hover { background: #0056b3; }
        .content { padding: 0 18px; display: none; overflow: hidden; background-color: #f1f1f1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SQL Vulnerability Analysis Report</h1>
            <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
            <p>Analysis completed in ${result.duration}ms</p>
        </div>

        ${config.includeStatistics ? this.generateHTMLSummary(filteredResult) : ''}

        <div class="vulnerabilities">
            <h2>Vulnerabilities</h2>
            ${this.generateHTMLVulnerabilities(vulnerabilities, config)}
        </div>
    </div>

    <script>
        function toggleContent(element) {
            element.classList.toggle("show");
        }
        
        document.querySelectorAll('.vulnerability-header').forEach(header => {
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                content.classList.toggle('show');
            });
        });
    </script>
</body>
</html>`;
  }

  private async generatePDFReport(result: AnalysisResult, config: ReportConfig): Promise<string> {
    const filteredResult = this.filterResult(result, config);
    const htmlContent = this.generateHTMLReport(filteredResult, config);

    let browser;
    try {
      browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });

      const page = await browser.newPage();
      await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

      const pdfBuffer = await page.pdf({
        format: 'A4',
        margin: {
          top: '20px',
          right: '20px',
          bottom: '20px',
          left: '20px'
        },
        printBackground: true
      });

      await browser.close();

      return pdfBuffer.toString('base64');
    } catch (error) {
      if (browser) {
        await browser.close();
      }
      throw new Error(`PDF generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private generateSARIFReport(result: AnalysisResult, config: ReportConfig): string {
    const filteredResult = this.filterResult(result, config);
    
    const sarifLog = {
      version: '2.1.0',
      $schema: 'https://json.schemastore.org/sarif-2.1.0.json',
      runs: [
        {
          tool: {
            driver: {
              name: 'SQL Vulnerability Scanner',
              version: '1.0.0',
              informationUri: 'https://github.com/cascade/sql-vulnerability-scanner',
              rules: this.generateSARIFRules(filteredResult.vulnerabilities)
            }
          },
          invocations: [
            {
              startTimeUtc: new Date().toISOString(),
              endTimeUtc: new Date(Date.now() + result.duration).toISOString(),
              executionSuccessful: true
            }
          ],
          results: filteredResult.vulnerabilities.map(vuln => this.generateSARIFResult(vuln)),
          statistics: {
            total: filteredResult.vulnerabilities.length,
            bySeverity: {
              critical: filteredResult.vulnerabilities.filter(v => v.severity === Severity.CRITICAL).length,
              high: filteredResult.vulnerabilities.filter(v => v.severity === Severity.HIGH).length,
              medium: filteredResult.vulnerabilities.filter(v => v.severity === Severity.MEDIUM).length,
              low: filteredResult.vulnerabilities.filter(v => v.severity === Severity.LOW).length
            }
          }
        }
      ]
    };

    return JSON.stringify(sarifLog, null, 2);
  }

  private generateSARIFRules(vulnerabilities: Vulnerability[]): any[] {
    const uniqueRules = new Map<string, any>();

    vulnerabilities.forEach(vuln => {
      const ruleId = vuln.type;
      if (!uniqueRules.has(ruleId)) {
        uniqueRules.set(ruleId, {
          id: ruleId,
          name: vuln.title,
          shortDescription: {
            text: vuln.description
          },
          fullDescription: {
            text: `${vuln.description}. ${vuln.recommendation}`
          },
          help: {
            text: vuln.recommendation,
            markdown: `**Recommendation:** ${vuln.recommendation}\n\n**Severity:** ${vuln.severity.toUpperCase()}`
          },
          properties: {
            category: vuln.category,
            cwe: vuln.cwe,
            owasp: vuln.owasp
          }
        });
      }
    });

    return Array.from(uniqueRules.values());
  }

  private generateSARIFResult(vulnerability: Vulnerability): any {
    return {
      ruleId: vulnerability.type,
      level: this.mapSeverityToSARIFLevel(vulnerability.severity),
      message: {
        text: vulnerability.description
      },
      locations: [
        {
          physicalLocation: {
            artifactLocation: {
              uri: vulnerability.filePath
            },
            region: {
              startLine: vulnerability.line,
              startColumn: vulnerability.column,
              endLine: vulnerability.line,
              endColumn: vulnerability.column + vulnerability.sqlQuery.length
            }
          }
        }
      ],
      codeFlows: [
        {
          threadFlows: [
            {
              locations: [
                {
                  location: {
                    physicalLocation: {
                      artifactLocation: {
                        uri: vulnerability.filePath
                      },
                      region: {
                        startLine: vulnerability.line,
                        startColumn: vulnerability.column
                      }
                    },
                    message: {
                      text: `SQL Query: ${vulnerability.sqlQuery}`
                    }
                  }
                }
              ]
            }
          ]
        }
      ],
      attachments: vulnerability.codeExample ? [
        {
          description: {
            text: 'Code Example'
          },
          artifactLocation: {
            uri: vulnerability.filePath
          },
          regions: [
            {
              startLine: vulnerability.line,
              startColumn: vulnerability.column,
              snippet: {
                text: vulnerability.sqlQuery
              }
            }
          ]
        }
      ] : [],
      properties: {
        confidence: vulnerability.confidence,
        category: vulnerability.category,
        cwe: vulnerability.cwe,
        owasp: vulnerability.owasp,
        recommendation: vulnerability.recommendation
      }
    };
  }

  private mapSeverityToSARIFLevel(severity: Severity): string {
    const mapping: Record<Severity, string> = {
      [Severity.CRITICAL]: 'error',
      [Severity.HIGH]: 'error',
      [Severity.MEDIUM]: 'warning',
      [Severity.LOW]: 'note',
      [Severity.INFO]: 'note'
    };

    return mapping[severity];
  }

  private filterResult(result: AnalysisResult, config: ReportConfig): AnalysisResult {
    let vulnerabilities = result.vulnerabilities;

    // Filter by severity
    if (config.filter.severities && config.filter.severities.length > 0) {
      vulnerabilities = vulnerabilities.filter(v => config.filter.severities!.includes(v.severity));
    }

    // Filter by type
    if (config.filter.types && config.filter.types.length > 0) {
      vulnerabilities = vulnerabilities.filter(v => config.filter.types!.includes(v.type));
    }

    // Filter by file
    if (config.filter.files && config.filter.files.length > 0) {
      vulnerabilities = vulnerabilities.filter(v => config.filter.files!.includes(v.filePath));
    }

    return {
      ...result,
      vulnerabilities
    };
  }

  private generateSummary(result: AnalysisResult) {
    const vulnerabilities = result.vulnerabilities;
    
    return {
      total: vulnerabilities.length,
      bySeverity: {
        critical: vulnerabilities.filter(v => v.severity === Severity.CRITICAL).length,
        high: vulnerabilities.filter(v => v.severity === Severity.HIGH).length,
        medium: vulnerabilities.filter(v => v.severity === Severity.MEDIUM).length,
        low: vulnerabilities.filter(v => v.severity === Severity.LOW).length
      },
      byType: this.groupByType(vulnerabilities),
      filesAnalyzed: result.statistics?.filesAnalyzed || 1,
      queriesAnalyzed: result.statistics?.totalQueries || result.queries.length,
      coverage: result.statistics?.coverage || 0
    };
  }

  private groupVulnerabilities(vulnerabilities: Vulnerability[], groupBy: string): Record<string, Vulnerability[]> {
    switch (groupBy) {
      case 'type':
        return this.groupByType(vulnerabilities);
      case 'severity':
        return this.groupBySeverity(vulnerabilities);
      case 'file':
        return this.groupByFile(vulnerabilities);
      default:
        return { all: vulnerabilities };
    }
  }

  private groupByType(vulnerabilities: Vulnerability[]): Record<string, Vulnerability[]> {
    const grouped: Record<string, Vulnerability[]> = {};
    
    vulnerabilities.forEach(vuln => {
      if (!grouped[vuln.type]) {
        grouped[vuln.type] = [];
      }
      grouped[vuln.type].push(vuln);
    });

    return grouped;
  }

  private groupBySeverity(vulnerabilities: Vulnerability[]): Record<string, Vulnerability[]> {
    const grouped: Record<string, Vulnerability[]> = {};
    
    vulnerabilities.forEach(vuln => {
      if (!grouped[vuln.severity]) {
        grouped[vuln.severity] = [];
      }
      grouped[vuln.severity].push(vuln);
    });

    return grouped;
  }

  private groupByFile(vulnerabilities: Vulnerability[]): Record<string, Vulnerability[]> {
    const grouped: Record<string, Vulnerability[]> = {};
    
    vulnerabilities.forEach(vuln => {
      if (!grouped[vuln.filePath]) {
        grouped[vuln.filePath] = [];
      }
      grouped[vuln.filePath].push(vuln);
    });

    return grouped;
  }

  private generateHTMLSummary(result: AnalysisResult): string {
    const summary = this.generateSummary(result);
    
    return `
    <div class="summary">
        <div class="summary-card">
            <h3>Total Vulnerabilities</h3>
            <h2>${summary.total}</h2>
        </div>
        <div class="summary-card severity-critical">
            <h3>Critical</h3>
            <h2>${summary.bySeverity.critical}</h2>
        </div>
        <div class="summary-card severity-high">
            <h3>High</h3>
            <h2>${summary.bySeverity.high}</h2>
        </div>
        <div class="summary-card severity-medium">
            <h3>Medium</h3>
            <h2>${summary.bySeverity.medium}</h2>
        </div>
        <div class="summary-card severity-low">
            <h3>Low</h3>
            <h2>${summary.bySeverity.low}</h2>
        </div>
        <div class="summary-card">
            <h3>Files Analyzed</h3>
            <h2>${summary.filesAnalyzed}</h2>
        </div>
        <div class="summary-card">
            <h3>Queries Analyzed</h3>
            <h2>${summary.queriesAnalyzed}</h2>
        </div>
        <div class="summary-card">
            <h3>Coverage</h3>
            <h2>${summary.coverage.toFixed(1)}%</h2>
        </div>
    </div>`;
  }

  private generateHTMLVulnerabilities(groupedVulnerabilities: Record<string, Vulnerability[]>, config: ReportConfig): string {
    let html = '';

    Object.entries(groupedVulnerabilities).forEach(([group, vulnerabilities]) => {
      html += `
        <div class="vulnerability-group">
            <h3>${group} (${vulnerabilities.length})</h3>
            ${vulnerabilities.map(vuln => this.generateHTMLVulnerability(vuln, config)).join('')}
        </div>
      `;
    });

    return html;
  }

  private generateHTMLVulnerability(vulnerability: Vulnerability, config: ReportConfig): string {
    const severityClass = `severity-${vulnerability.severity}`;
    const badgeClass = `badge-${vulnerability.severity}`;

    return `
      <div class="vulnerability">
        <div class="vulnerability-header ${severityClass}">
          <span class="badge ${badgeClass}">${vulnerability.severity}</span>
          <strong>${vulnerability.title}</strong>
          <span style="float: right;">${vulnerability.filePath}:${vulnerability.line}</span>
        </div>
        <div class="vulnerability-content">
          <p><strong>Description:</strong> ${vulnerability.description}</p>
          <p><strong>Recommendation:</strong> ${vulnerability.recommendation}</p>
          <p><strong>Type:</strong> ${vulnerability.type}</p>
          <p><strong>Confidence:</strong> ${(vulnerability.confidence * 100).toFixed(0)}%</p>
          ${vulnerability.cwe ? `<p><strong>CWE:</strong> ${vulnerability.cwe}</p>` : ''}
          ${vulnerability.owasp ? `<p><strong>OWASP:</strong> ${vulnerability.owasp}</p>` : ''}
          ${config.includeCodeExamples ? `
            <p><strong>SQL Query:</strong></p>
            <div class="code-block">${this.escapeHtml(vulnerability.sqlQuery)}</div>
          ` : ''}
        </div>
      </div>
    `;
  }

  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  // Method to generate JIRA tickets
  async generateJIRATickets(result: AnalysisResult, config: Partial<ReportConfig> = {}): Promise<any[]> {
    const filteredResult = this.filterResult(result, this.mergeReportConfig(config));
    const tickets: any[] = [];

    // Group vulnerabilities by type and severity for ticket creation
    const grouped = this.groupVulnerabilities(filteredResult.vulnerabilities, 'type');

    Object.entries(grouped).forEach(([type, vulnerabilities]) => {
      const severity = this.getHighestSeverity(vulnerabilities);
      
      if (this.shouldCreateTicket(severity)) {
        const ticket = {
          fields: {
            project: { key: 'SEC' },
            summary: `SQL Vulnerability: ${type}`,
            description: this.generateJIRADescription(vulnerabilities),
            issuetype: { name: 'Security Vulnerability' },
            priority: this.mapToJIRAPriority(severity),
            labels: ['sql-vulnerability', 'automated-scan'],
            customfield_10010: vulnerabilities.length // Number of vulnerabilities
          }
        };

        tickets.push(ticket);
      }
    });

    return tickets;
  }

  private getHighestSeverity(vulnerabilities: Vulnerability[]): Severity {
    const severityOrder = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW];
    
    for (const severity of severityOrder) {
      if (vulnerabilities.some(v => v.severity === severity)) {
        return severity;
      }
    }

    return Severity.LOW;
  }

  private shouldCreateTicket(severity: Severity): boolean {
    return severity === Severity.CRITICAL || severity === Severity.HIGH;
  }

  private mapToJIRAPriority(severity: Severity): string {
    const mapping: Record<Severity, string> = {
      [Severity.CRITICAL]: 'Highest',
      [Severity.HIGH]: 'High',
      [Severity.MEDIUM]: 'Medium',
      [Severity.LOW]: 'Low',
      [Severity.INFO]: 'Lowest'
    };

    return mapping[severity];
  }

  private generateJIRADescription(vulnerabilities: Vulnerability[]): string {
    const description = `
h2. SQL Vulnerability Analysis Results

Found ${vulnerabilities.length} vulnerabilities of this type:

${vulnerabilities.map(vuln => `
* *File:* ${vuln.filePath}:${vuln.line}
* *Severity:* ${vuln.severity}
* *Description:* ${vuln.description}
* *Recommendation:* ${vuln.recommendation}
* *SQL:* {code:sql}${vuln.sqlQuery}{code}
`).join('\n')}

h3. Recommended Actions

# Review and fix all identified vulnerabilities
# Implement proper input validation and parameterization
# Add security tests to prevent regression
# Consider implementing security code reviews

This ticket was automatically generated by the SQL Vulnerability Scanner.
    `.trim();

    return description;
  }

  // Method to export to CSV
  generateCSVReport(result: AnalysisResult): string {
    const headers = [
      'ID', 'Type', 'Severity', 'Title', 'Description', 'Recommendation',
      'File Path', 'Line', 'Column', 'SQL Query', 'Confidence', 'Category'
    ];

    const rows = result.vulnerabilities.map(vuln => [
      vuln.id,
      vuln.type,
      vuln.severity,
      vuln.title,
      vuln.description.replace(/"/g, '""'), // Escape quotes for CSV
      vuln.recommendation.replace(/"/g, '""'),
      vuln.filePath,
      vuln.line.toString(),
      vuln.column.toString(),
      vuln.sqlQuery.replace(/"/g, '""'),
      (vuln.confidence * 100).toFixed(0) + '%',
      vuln.category
    ]);

    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
  }

  // Method to generate executive summary
  generateExecutiveSummary(result: AnalysisResult): string {
    const criticalCount = result.vulnerabilities.filter(v => v.severity === Severity.CRITICAL).length;
    const highCount = result.vulnerabilities.filter(v => v.severity === Severity.HIGH).length;
    const totalIssues = result.vulnerabilities.length;

    return `
# Executive Summary

## Overview
SQL vulnerability analysis completed on ${new Date().toLocaleDateString()}.
- **Total Issues Found:** ${totalIssues}
- **Critical Issues:** ${criticalCount}
- **High Priority Issues:** ${highCount}
- **Files Analyzed:** ${result.statistics?.filesAnalyzed || 1}
- **Security Coverage:** ${(result.statistics?.coverage || 0).toFixed(1)}%

## Risk Assessment
${criticalCount > 0 ? '⚠️ **IMMEDIATE ACTION REQUIRED** - Critical security vulnerabilities detected' : 
  highCount > 0 ? '⚠️ **HIGH PRIORITY** - High-severity issues require prompt attention' :
  '✅ **LOW RISK** - No critical or high-severity issues found'}

## Recommendations
${criticalCount > 0 ? 
  '1. Address all critical vulnerabilities immediately\n2. Implement emergency security patches\n3. Conduct security incident assessment' :
  highCount > 0 ?
  '1. Prioritize high-severity fixes\n2. Schedule security updates within next sprint\n3. Enhance security testing procedures' :
  '1. Continue regular security scanning\n2. Maintain security best practices\n3. Monitor for new vulnerability patterns'
}

## Next Steps
- Review detailed vulnerability report
- Assign remediation tasks to development team
- Schedule follow-up security assessment
- Update security policies and procedures

---
*Report generated by SQL Vulnerability Scanner v1.0.0*
    `.trim();
  }
}
