import { AnalysisResult, ReportConfig, AppConfig } from '../types';
export declare class ReportGenerator {
    private config;
    constructor(config: AppConfig);
    generate(result: AnalysisResult, format?: 'json' | 'html' | 'pdf' | 'sarif', reportConfig?: Partial<ReportConfig>): Promise<string>;
    private mergeReportConfig;
    private generateJSONReport;
    private generateHTMLReport;
    private generatePDFReport;
    private generateSARIFReport;
    private generateSARIFRules;
    private generateSARIFResult;
    private mapSeverityToSARIFLevel;
    private filterResult;
    private generateSummary;
    private groupVulnerabilities;
    private groupByType;
    private groupBySeverity;
    private groupByFile;
    private generateHTMLSummary;
    private generateHTMLVulnerabilities;
    private generateHTMLVulnerability;
    private escapeHtml;
    generateJIRATickets(result: AnalysisResult, config?: Partial<ReportConfig>): Promise<any[]>;
    private getHighestSeverity;
    private shouldCreateTicket;
    private mapToJIRAPriority;
    private generateJIRADescription;
    generateCSVReport(result: AnalysisResult): string;
    generateExecutiveSummary(result: AnalysisResult): string;
}
//# sourceMappingURL=ReportGenerator.d.ts.map