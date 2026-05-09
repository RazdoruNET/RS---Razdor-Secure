import { AppConfig, DatabaseType, Severity, CustomRule } from '../types';
import * as fs from 'fs';
import * as path from 'path';

export class ConfigManager {
  private config: AppConfig;
  private configPath: string;

  constructor(config?: Partial<AppConfig>, configPath?: string) {
    this.configPath = configPath || this.getDefaultConfigPath();
    this.config = this.loadConfig(config);
  }

  getConfig(): AppConfig {
    return { ...this.config };
  }

  updateConfig(updates: Partial<AppConfig>): void {
    this.config = { ...this.config, ...updates };
    this.saveConfig();
  }

  private loadConfig(providedConfig?: Partial<AppConfig>): AppConfig {
    const defaultConfig: AppConfig = {
      databaseType: DatabaseType.GENERIC,
      securityLevel: 'moderate',
      enableGPTAnalysis: false,
      enablePerformanceAnalysis: true,
      ignoredRules: [],
      customRules: []
    };

    let config = { ...defaultConfig };

    // Load from file if exists
    if (fs.existsSync(this.configPath)) {
      try {
        const fileConfig = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
        config = { ...config, ...fileConfig };
      } catch (error) {
        console.warn(`Failed to load config from ${this.configPath}:`, error);
      }
    }

    // Override with provided config
    if (providedConfig) {
      config = { ...config, ...providedConfig };
    }

    return config;
  }

  private saveConfig(): void {
    try {
      const configDir = path.dirname(this.configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.warn(`Failed to save config to ${this.configPath}:`, error);
    }
  }

  private getDefaultConfigPath(): string {
    const homeDir = require('os').homedir();
    return path.join(homeDir, '.sql-vulnerability-scanner', 'config.json');
  }

  // Method to add custom rules
  addCustomRule(rule: CustomRule): void {
    this.config.customRules.push(rule);
    this.saveConfig();
  }

  // Method to remove custom rule
  removeCustomRule(ruleId: string): void {
    this.config.customRules = this.config.customRules.filter(rule => rule.id !== ruleId);
    this.saveConfig();
  }

  // Method to ignore a rule
  ignoreRule(ruleId: string): void {
    if (!this.config.ignoredRules.includes(ruleId)) {
      this.config.ignoredRules.push(ruleId);
      this.saveConfig();
    }
  }

  // Method to unignore a rule
  unignoreRule(ruleId: string): void {
    this.config.ignoredRules = this.config.ignoredRules.filter(id => id !== ruleId);
    this.saveConfig();
  }

  // Method to set security level
  setSecurityLevel(level: 'strict' | 'moderate' | 'lenient'): void {
    this.config.securityLevel = level;
    this.adjustSeverityThresholds();
    this.saveConfig();
  }

  private adjustSeverityThresholds(): void {
    // Adjust configuration based on security level
    switch (this.config.securityLevel) {
      case 'strict':
        // Enable all checks, lower confidence thresholds
        this.config.enableGPTAnalysis = true;
        this.config.enablePerformanceAnalysis = true;
        break;
      case 'moderate':
        // Balanced approach
        this.config.enableGPTAnalysis = false;
        this.config.enablePerformanceAnalysis = true;
        break;
      case 'lenient':
        // Minimal checks, only critical issues
        this.config.enableGPTAnalysis = false;
        this.config.enablePerformanceAnalysis = false;
        break;
    }
  }

  // Method to validate configuration
  validateConfig(): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Validate database type
    if (!Object.values(DatabaseType).includes(this.config.databaseType)) {
      errors.push(`Invalid database type: ${this.config.databaseType}`);
    }

    // Validate security level
    if (!['strict', 'moderate', 'lenient'].includes(this.config.securityLevel)) {
      errors.push(`Invalid security level: ${this.config.securityLevel}`);
    }

    // Validate custom rules
    this.config.customRules.forEach(rule => {
      if (!rule.id || !rule.name || !rule.pattern) {
        errors.push(`Invalid custom rule: missing required fields`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Method to export configuration
  exportConfig(): string {
    return JSON.stringify(this.config, null, 2);
  }

  // Method to import configuration
  importConfig(configJson: string): void {
    try {
      const importedConfig = JSON.parse(configJson);
      const validation = this.validateConfig();
      
      if (!validation.isValid) {
        throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
      }

      this.config = { ...this.config, ...importedConfig };
      this.saveConfig();
    } catch (error) {
      throw new Error(`Failed to import configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Method to reset to defaults
  resetToDefaults(): void {
    this.config = {
      databaseType: DatabaseType.GENERIC,
      securityLevel: 'moderate',
      enableGPTAnalysis: false,
      enablePerformanceAnalysis: true,
      ignoredRules: [],
      customRules: []
    };
    this.saveConfig();
  }

  // Method to get configuration for specific database
  getDatabaseConfig(databaseType: DatabaseType): Partial<AppConfig> {
    const databaseSpecificConfigs: Record<DatabaseType, Partial<AppConfig>> = {
      [DatabaseType.MYSQL]: {
        databaseType: DatabaseType.MYSQL,
        customRules: [
          {
            id: 'mysql_specific',
            name: 'MySQL Specific Issues',
            pattern: 'GROUP_CONCAT.*LIMIT',
            severity: Severity.MEDIUM,
            description: 'GROUP_CONCAT with LIMIT may cause data truncation',
            recommendation: 'Use proper pagination or increase group_concat_max_len'
          }
        ]
      },
      [DatabaseType.POSTGRESQL]: {
        databaseType: DatabaseType.POSTGRESQL,
        customRules: [
          {
            id: 'postgresql_specific',
            name: 'PostgreSQL Specific Issues',
            pattern: 'ILIKE.*%',
            severity: Severity.LOW,
            description: 'Leading wildcard in ILIKE prevents index usage',
            recommendation: 'Consider full-text search or trigram indexes'
          }
        ]
      },
      [DatabaseType.MSSQL]: {
        databaseType: DatabaseType.MSSQL,
        customRules: [
          {
            id: 'mssql_specific',
            name: 'MSSQL Specific Issues',
            pattern: 'SELECT TOP.*ORDER BY',
            severity: Severity.LOW,
            description: 'TOP with ORDER BY may be inefficient',
            recommendation: 'Consider using OFFSET-FETCH or proper indexing'
          }
        ]
      },
      [DatabaseType.ORACLE]: {
        databaseType: DatabaseType.ORACLE,
        customRules: [
          {
            id: 'oracle_specific',
            name: 'Oracle Specific Issues',
            pattern: 'ROWNUM.*ORDER BY',
            severity: Severity.MEDIUM,
            description: 'ROWNUM applied before ORDER BY',
            recommendation: 'Use subquery with ORDER BY or modern pagination syntax'
          }
        ]
      },
      [DatabaseType.SQLITE]: {
        databaseType: DatabaseType.SQLITE,
        customRules: [
          {
            id: 'sqlite_specific',
            name: 'SQLite Specific Issues',
            pattern: 'INSERT.*VALUES.*VALUES',
            severity: Severity.MEDIUM,
            description: 'Multiple VALUES clauses not supported in older SQLite versions',
            recommendation: 'Use separate INSERT statements or check SQLite version'
          }
        ]
      },
      [DatabaseType.GENERIC]: {
        databaseType: DatabaseType.GENERIC,
        customRules: []
      }
    };

    return databaseSpecificConfigs[databaseType] || {};
  }

  // Method to get environment-specific configuration
  getEnvironmentConfig(): Partial<AppConfig> {
    const env = process.env.NODE_ENV || 'development';
    
    const environmentConfigs: Record<string, Partial<AppConfig>> = {
      development: {
        securityLevel: 'lenient',
        enableGPTAnalysis: false
      },
      testing: {
        securityLevel: 'moderate',
        enableGPTAnalysis: false
      },
      staging: {
        securityLevel: 'strict',
        enableGPTAnalysis: true
      },
      production: {
        securityLevel: 'strict',
        enableGPTAnalysis: true
      }
    };

    return environmentConfigs[env] || environmentConfigs.development;
  }

  // Method to merge configurations with precedence
  mergeConfigurations(base: Partial<AppConfig>, override: Partial<AppConfig>): AppConfig {
    return {
      databaseType: override.databaseType || base.databaseType || DatabaseType.GENERIC,
      securityLevel: override.securityLevel || base.securityLevel || 'moderate',
      enableGPTAnalysis: override.enableGPTAnalysis ?? base.enableGPTAnalysis ?? false,
      enablePerformanceAnalysis: override.enablePerformanceAnalysis ?? base.enablePerformanceAnalysis ?? true,
      ignoredRules: [...(base.ignoredRules || []), ...(override.ignoredRules || [])],
      customRules: [...(base.customRules || []), ...(override.customRules || [])]
    };
  }

  // Method to get configuration summary
  getConfigSummary(): string {
    return `
SQL Vulnerability Scanner Configuration:
- Database Type: ${this.config.databaseType}
- Security Level: ${this.config.securityLevel}
- GPT Analysis: ${this.config.enableGPTAnalysis ? 'Enabled' : 'Disabled'}
- Performance Analysis: ${this.config.enablePerformanceAnalysis ? 'Enabled' : 'Disabled'}
- Ignored Rules: ${this.config.ignoredRules.length}
- Custom Rules: ${this.config.customRules.length}
- Config File: ${this.configPath}
    `.trim();
  }
}
