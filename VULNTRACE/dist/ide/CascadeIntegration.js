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
exports.CascadeIntegration = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const glob_1 = require("glob");
class CascadeIntegration {
    constructor(scanner) {
        this.decorations = new Map();
        this.scanner = scanner;
        this.setupIntegration();
    }
    setupIntegration() {
        // This would integrate with Cascade SWE-1.5's extension API
        // For now, we'll simulate the integration points
        this.registerCommands();
        this.registerEventListeners();
        this.createStatusBarItem();
        this.setupTooltipProvider();
    }
    registerCommands() {
        // Register commands for Cascade SWE-1.5
        const commands = [
            {
                id: 'sqlScanner.analyzeCurrentFile',
                title: 'Analyze Current SQL File',
                handler: () => this.analyzeCurrentFile()
            },
            {
                id: 'sqlScanner.analyzeWorkspace',
                title: 'Analyze Entire Workspace',
                handler: () => this.analyzeWorkspace()
            },
            {
                id: 'sqlScanner.generateReport',
                title: 'Generate Vulnerability Report',
                handler: () => this.generateReport()
            },
            {
                id: 'sqlScanner.clearHighlights',
                title: 'Clear Vulnerability Highlights',
                handler: () => this.clearHighlights()
            },
            {
                id: 'sqlScanner.ignoreVulnerability',
                title: 'Ignore Vulnerability',
                handler: () => this.ignoreCurrentVulnerability()
            },
            {
                id: 'sqlScanner.showSettings',
                title: 'Scanner Settings',
                handler: () => this.showSettings()
            }
        ];
        // In real implementation, these would be registered with Cascade's command API
        commands.forEach(cmd => {
            console.log(`Registered command: ${cmd.id}`);
        });
    }
    registerEventListeners() {
        // Listen for file changes
        this.onFileChanged = this.onFileChanged.bind(this);
        this.onFileOpened = this.onFileOpened.bind(this);
        this.onFileSaved = this.onFileSaved.bind(this);
        // In real implementation, these would be registered with Cascade's event API
        console.log('Registered event listeners for file changes');
    }
    createStatusBarItem() {
        // Create status bar item showing scan status
        this.statusBarItem = {
            text: 'SQL Scanner: Ready',
            tooltip: 'SQL Vulnerability Scanner',
            command: 'sqlScanner.showSettings'
        };
        console.log('Created status bar item');
    }
    setupTooltipProvider() {
        // Setup hover provider for vulnerability tooltips
        this.tooltipProvider = {
            provideHover: (document, position) => {
                return this.provideHover(document, position);
            }
        };
        console.log('Setup tooltip provider');
    }
    async highlightVulnerabilities(vulnerabilities) {
        // Clear existing highlights
        this.clearHighlights();
        // Group vulnerabilities by file
        const vulnerabilitiesByFile = this.groupVulnerabilitiesByFile(vulnerabilities);
        for (const [filePath, fileVulnerabilities] of vulnerabilitiesByFile) {
            await this.highlightFileVulnerabilities(filePath, fileVulnerabilities);
        }
        this.updateStatusBar(vulnerabilities);
    }
    groupVulnerabilitiesByFile(vulnerabilities) {
        const grouped = new Map();
        vulnerabilities.forEach(vuln => {
            if (!grouped.has(vuln.filePath)) {
                grouped.set(vuln.filePath, []);
            }
            grouped.get(vuln.filePath).push(vuln);
        });
        return grouped;
    }
    async highlightFileVulnerabilities(filePath, vulnerabilities) {
        const decorations = [];
        vulnerabilities.forEach(vuln => {
            const decoration = this.createDecoration(vuln);
            decorations.push(decoration);
        });
        this.decorations.set(filePath, decorations);
        // In real implementation, this would apply decorations to the editor
        console.log(`Highlighted ${vulnerabilities.length} vulnerabilities in ${filePath}`);
    }
    createDecoration(vulnerability) {
        const severityColors = {
            critical: '#ff0000',
            high: '#ff8c00',
            medium: '#ffd700',
            low: '#90ee90',
            info: '#87ceeb'
        };
        return {
            range: {
                start: { line: vulnerability.line - 1, character: vulnerability.column - 1 },
                end: { line: vulnerability.line - 1, character: vulnerability.column - 1 + vulnerability.sqlQuery.length }
            },
            options: {
                className: `sql-vulnerability-${vulnerability.severity}`,
                color: severityColors[vulnerability.severity],
                textDecoration: 'underline wavy',
                hoverMessage: {
                    value: this.createHoverMessage(vulnerability)
                }
            }
        };
    }
    createHoverMessage(vulnerability) {
        return `
## ${vulnerability.title}

**Severity:** ${vulnerability.severity.toUpperCase()}  
**Type:** ${vulnerability.type}  
**Confidence:** ${(vulnerability.confidence * 100).toFixed(0)}%

**Description:** ${vulnerability.description}

**Recommendation:** ${vulnerability.recommendation}

${vulnerability.cwe ? `**CWE:** ${vulnerability.cwe}` : ''}
${vulnerability.owasp ? `**OWASP:** ${vulnerability.owasp}` : ''}

---
[Ignore Vulnerability](command:sqlScanner.ignoreVulnerability) | [View Details](command:sqlScanner.showDetails)
    `.trim();
    }
    showTooltip(vulnerability) {
        // Show detailed tooltip for the vulnerability
        const tooltipContent = this.createDetailedTooltip(vulnerability);
        // In real implementation, this would show a modal or popup
        console.log('Showing tooltip:', tooltipContent);
    }
    createDetailedTooltip(vulnerability) {
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

## Actions
- [Ignore this vulnerability](command:sqlScanner.ignoreVulnerability)
- [View in context](command:sqlScanner.viewInContext)
- [Generate fix suggestion](command:sqlScanner.suggestFix)
    `.trim();
    }
    openFile(filePath, line, column) {
        // Open file and navigate to specific location
        console.log(`Opening ${filePath} at line ${line}, column ${column}`);
        // In real implementation, this would use Cascade's API to open and navigate
    }
    showReport(result) {
        // Show comprehensive report in a webview or panel
        const reportContent = this.generateReportContent(result);
        console.log('Showing report:', reportContent);
        // In real implementation, this would create a webview panel
    }
    generateReportContent(result) {
        const criticalCount = result.vulnerabilities.filter(v => v.severity === 'critical').length;
        const highCount = result.vulnerabilities.filter(v => v.severity === 'high').length;
        const mediumCount = result.vulnerabilities.filter(v => v.severity === 'medium').length;
        const lowCount = result.vulnerabilities.filter(v => v.severity === 'low').length;
        return `
<!DOCTYPE html>
<html>
<head>
    <title>SQL Vulnerability Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .summary-item { padding: 20px; border-radius: 8px; text-align: center; color: white; }
        .critical { background: #dc3545; }
        .high { background: #fd7e14; }
        .medium { background: #ffc107; color: black; }
        .low { background: #28a745; }
        .vulnerability { border: 1px solid #ddd; margin-bottom: 20px; border-radius: 8px; }
        .vulnerability-header { padding: 15px; font-weight: bold; border-bottom: 1px solid #ddd; }
        .vulnerability-content { padding: 15px; }
    </style>
</head>
<body>
    <h1>SQL Vulnerability Analysis Report</h1>
    
    <div class="summary">
        <div class="summary-item critical">
            <h2>${criticalCount}</h2>
            <p>Critical</p>
        </div>
        <div class="summary-item high">
            <h2>${highCount}</h2>
            <p>High</p>
        </div>
        <div class="summary-item medium">
            <h2>${mediumCount}</h2>
            <p>Medium</p>
        </div>
        <div class="summary-item low">
            <h2>${lowCount}</h2>
            <p>Low</p>
        </div>
    </div>

    <h2>Vulnerabilities (${result.vulnerabilities.length})</h2>
    ${result.vulnerabilities.map(vuln => `
        <div class="vulnerability severity-${vuln.severity}">
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
    ignoreVulnerability(vulnerabilityId) {
        // Add vulnerability ID to ignored list
        const config = this.scanner.getConfig();
        config.ignoredRules.push(vulnerabilityId);
        this.scanner.updateConfig(config);
        // Clear highlights for ignored vulnerability
        this.clearHighlights();
        console.log(`Ignored vulnerability: ${vulnerabilityId}`);
    }
    async analyzeCurrentFile() {
        // Get current active file in Cascade
        const activeFile = this.getActiveFile();
        if (!activeFile) {
            console.log('No active file found');
            return;
        }
        try {
            const content = await this.getFileContent(activeFile);
            const result = await this.scanner.analyzeFile(activeFile, content);
            await this.highlightVulnerabilities(result.vulnerabilities);
            if (result.vulnerabilities.length > 0) {
                this.showNotification(`Found ${result.vulnerabilities.length} vulnerabilities`, 'warning');
            }
            else {
                this.showNotification('No vulnerabilities found', 'success');
            }
        }
        catch (error) {
            this.showNotification(`Analysis failed: ${error}`, 'error');
        }
    }
    async analyzeWorkspace() {
        // Get all SQL files in workspace
        const sqlFiles = await this.getWorkspaceSQLFiles();
        if (sqlFiles.length === 0) {
            this.showNotification('No SQL files found in workspace', 'info');
            return;
        }
        try {
            const results = await this.scanner.analyzeMultipleFiles(sqlFiles);
            const allVulnerabilities = results.flatMap(r => r.vulnerabilities);
            await this.highlightVulnerabilities(allVulnerabilities);
            this.showNotification(`Analyzed ${sqlFiles.length} files, found ${allVulnerabilities.length} vulnerabilities`, 'info');
        }
        catch (error) {
            this.showNotification(`Workspace analysis failed: ${error}`, 'error');
        }
    }
    async generateReport() {
        // Get current analysis results or run new analysis
        const sqlFiles = await this.getWorkspaceSQLFiles();
        const results = await this.scanner.analyzeMultipleFiles(sqlFiles);
        // Combine results
        const combinedResult = {
            vulnerabilities: results.flatMap(r => r.vulnerabilities),
            statistics: {
                totalQueries: results.reduce((sum, r) => sum + r.statistics.totalQueries, 0),
                vulnerabilitiesByType: {},
                vulnerabilitiesBySeverity: {},
                filesAnalyzed: results.length,
                linesAnalyzed: results.reduce((sum, r) => sum + r.statistics.linesAnalyzed, 0),
                coverage: results.reduce((sum, r) => sum + r.statistics.coverage, 0) / results.length
            },
            queries: results.flatMap(r => r.queries),
            duration: results.reduce((sum, r) => sum + r.duration, 0),
            context: results[0]?.context || {}
        };
        this.showReport(combinedResult);
    }
    clearHighlights() {
        // Clear all vulnerability decorations
        this.decorations.clear();
        console.log('Cleared all vulnerability highlights');
    }
    ignoreCurrentVulnerability() {
        // Get vulnerability at current cursor position
        const currentVulnerability = this.getVulnerabilityAtCursor();
        if (currentVulnerability) {
            this.ignoreVulnerability(currentVulnerability.id);
            this.showNotification(`Ignored vulnerability: ${currentVulnerability.title}`, 'info');
        }
        else {
            this.showNotification('No vulnerability found at cursor position', 'warning');
        }
    }
    showSettings() {
        // Open settings panel
        console.log('Opening settings panel');
    }
    updateStatusBar(vulnerabilities) {
        const criticalCount = vulnerabilities.filter(v => v.severity === 'critical').length;
        const highCount = vulnerabilities.filter(v => v.severity === 'high').length;
        if (this.statusBarItem) {
            this.statusBarItem.text = `SQL Scanner: ${criticalCount} Critical, ${highCount} High`;
        }
    }
    // Event handlers
    onFileChanged(event) {
        // Re-analyze file when it changes
        if (this.isSQLFile(event.fileName)) {
            this.analyzeCurrentFile();
        }
    }
    onFileOpened(event) {
        // Analyze file when opened if it's a SQL file
        if (this.isSQLFile(event.fileName)) {
            this.analyzeCurrentFile();
        }
    }
    onFileSaved(event) {
        // Re-analyze file when saved
        if (this.isSQLFile(event.fileName)) {
            this.analyzeCurrentFile();
        }
    }
    // Helper methods (these integrate with file system for standalone operation)
    getActiveFile() {
        // In real IDE integration, this would get the active editor file from Cascade's API
        // For standalone operation, we use environment variable or default
        const activeFile = process.env.ACTIVE_FILE;
        return activeFile || null;
    }
    async getFileContent(filePath) {
        try {
            if (fs.existsSync(filePath)) {
                return fs.readFileSync(filePath, 'utf8');
            }
            throw new Error(`File not found: ${filePath}`);
        }
        catch (error) {
            console.error(`Failed to read file ${filePath}:`, error);
            throw error;
        }
    }
    async getWorkspaceSQLFiles() {
        const workspaceRoot = process.cwd();
        const sqlFiles = await this.findSQLFiles(workspaceRoot);
        const files = [];
        for (const filePath of sqlFiles) {
            try {
                const content = await this.getFileContent(filePath);
                files.push({ path: filePath, content });
            }
            catch (error) {
                console.error(`Failed to read SQL file ${filePath}:`, error);
            }
        }
        return files;
    }
    async findSQLFiles(directory) {
        const sqlPattern = '**/*.{sql,ddl,dml,proc,func}';
        const files = await (0, glob_1.glob)(sqlPattern, { cwd: directory, ignore: ['**/node_modules/**', '**/dist/**'] });
        return files.map((file) => path.join(directory, file));
    }
    isSQLFile(fileName) {
        const sqlExtensions = ['.sql', '.ddl', '.dml', '.proc', '.func'];
        return sqlExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
    }
    getVulnerabilityAtCursor() {
        // Get vulnerability at current cursor position
        // In real IDE integration, this would use Cascade's cursor position API
        // For standalone operation, return the first vulnerability if any exist
        const allVulnerabilities = [];
        this.decorations.forEach((vulns) => {
            allVulnerabilities.push(...vulns);
        });
        return allVulnerabilities.length > 0 ? allVulnerabilities[0] : null;
    }
    provideHover(document, position) {
        // Provide hover information for vulnerabilities
        // In real IDE integration, this would use Cascade's hover provider API
        // For standalone operation, return basic hover info
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
    showNotification(message, type) {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}
exports.CascadeIntegration = CascadeIntegration;
//# sourceMappingURL=CascadeIntegration.js.map