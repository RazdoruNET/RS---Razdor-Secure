import { SQLVulnerabilityScanner } from './core/SQLVulnerabilityScanner';
import { CascadeIntegration } from './ide/CascadeIntegration';
import * as types from './types';
import { SQLParser } from './parser/SQLParser';
import { StaticAnalyzer } from './analyzer/StaticAnalyzer';
import { GPTAnalyzer } from './gpt/GPTAnalyzer';
import { ReportGenerator } from './reporter/ReportGenerator';
import { ConfigManager } from './config/ConfigManager';

// Export all types and classes
export { SQLVulnerabilityScanner, CascadeIntegration, SQLParser, StaticAnalyzer, GPTAnalyzer, ReportGenerator, ConfigManager };
export * from './types';

// Main entry point for the plugin
export class SQLVulnerabilityPlugin {
  private scanner: SQLVulnerabilityScanner;
  private integration: CascadeIntegration;

  constructor(config?: any) {
    this.scanner = new SQLVulnerabilityScanner(config);
    this.integration = new CascadeIntegration(this.scanner);
  }

  async activate(): Promise<void> {
    console.log('SQL Vulnerability Scanner plugin activated');
  }

  async deactivate(): Promise<void> {
    console.log('SQL Vulnerability Scanner plugin deactivated');
  }

  getScanner(): SQLVulnerabilityScanner {
    return this.scanner;
  }

  getIntegration(): CascadeIntegration {
    return this.integration;
  }
}

// Default export for easy importing
export default SQLVulnerabilityPlugin;
