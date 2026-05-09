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
exports.ConfigManager = void 0;
const types_1 = require("../types");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class ConfigManager {
    constructor(config, configPath) {
        this.configPath = configPath || this.getDefaultConfigPath();
        this.config = this.loadConfig(config);
    }
    getConfig() {
        return { ...this.config };
    }
    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
        this.saveConfig();
    }
    loadConfig(providedConfig) {
        const defaultConfig = {
            databaseType: types_1.DatabaseType.GENERIC,
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
            }
            catch (error) {
                console.warn(`Failed to load config from ${this.configPath}:`, error);
            }
        }
        // Override with provided config
        if (providedConfig) {
            config = { ...config, ...providedConfig };
        }
        return config;
    }
    saveConfig() {
        try {
            const configDir = path.dirname(this.configPath);
            if (!fs.existsSync(configDir)) {
                fs.mkdirSync(configDir, { recursive: true });
            }
            fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
        }
        catch (error) {
            console.warn(`Failed to save config to ${this.configPath}:`, error);
        }
    }
    getDefaultConfigPath() {
        const homeDir = require('os').homedir();
        return path.join(homeDir, '.sql-vulnerability-scanner', 'config.json');
    }
    // Method to add custom rules
    addCustomRule(rule) {
        this.config.customRules.push(rule);
        this.saveConfig();
    }
    // Method to remove custom rule
    removeCustomRule(ruleId) {
        this.config.customRules = this.config.customRules.filter(rule => rule.id !== ruleId);
        this.saveConfig();
    }
    // Method to ignore a rule
    ignoreRule(ruleId) {
        if (!this.config.ignoredRules.includes(ruleId)) {
            this.config.ignoredRules.push(ruleId);
            this.saveConfig();
        }
    }
    // Method to unignore a rule
    unignoreRule(ruleId) {
        this.config.ignoredRules = this.config.ignoredRules.filter(id => id !== ruleId);
        this.saveConfig();
    }
    // Method to set security level
    setSecurityLevel(level) {
        this.config.securityLevel = level;
        this.adjustSeverityThresholds();
        this.saveConfig();
    }
    adjustSeverityThresholds() {
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
    validateConfig() {
        const errors = [];
        // Validate database type
        if (!Object.values(types_1.DatabaseType).includes(this.config.databaseType)) {
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
    exportConfig() {
        return JSON.stringify(this.config, null, 2);
    }
    // Method to import configuration
    importConfig(configJson) {
        try {
            const importedConfig = JSON.parse(configJson);
            const validation = this.validateConfig();
            if (!validation.isValid) {
                throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
            }
            this.config = { ...this.config, ...importedConfig };
            this.saveConfig();
        }
        catch (error) {
            throw new Error(`Failed to import configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    // Method to reset to defaults
    resetToDefaults() {
        this.config = {
            databaseType: types_1.DatabaseType.GENERIC,
            securityLevel: 'moderate',
            enableGPTAnalysis: false,
            enablePerformanceAnalysis: true,
            ignoredRules: [],
            customRules: []
        };
        this.saveConfig();
    }
    // Method to get configuration for specific database
    getDatabaseConfig(databaseType) {
        const databaseSpecificConfigs = {
            [types_1.DatabaseType.MYSQL]: {
                databaseType: types_1.DatabaseType.MYSQL,
                customRules: [
                    {
                        id: 'mysql_specific',
                        name: 'MySQL Specific Issues',
                        pattern: 'GROUP_CONCAT.*LIMIT',
                        severity: types_1.Severity.MEDIUM,
                        description: 'GROUP_CONCAT with LIMIT may cause data truncation',
                        recommendation: 'Use proper pagination or increase group_concat_max_len'
                    }
                ]
            },
            [types_1.DatabaseType.POSTGRESQL]: {
                databaseType: types_1.DatabaseType.POSTGRESQL,
                customRules: [
                    {
                        id: 'postgresql_specific',
                        name: 'PostgreSQL Specific Issues',
                        pattern: 'ILIKE.*%',
                        severity: types_1.Severity.LOW,
                        description: 'Leading wildcard in ILIKE prevents index usage',
                        recommendation: 'Consider full-text search or trigram indexes'
                    }
                ]
            },
            [types_1.DatabaseType.MSSQL]: {
                databaseType: types_1.DatabaseType.MSSQL,
                customRules: [
                    {
                        id: 'mssql_specific',
                        name: 'MSSQL Specific Issues',
                        pattern: 'SELECT TOP.*ORDER BY',
                        severity: types_1.Severity.LOW,
                        description: 'TOP with ORDER BY may be inefficient',
                        recommendation: 'Consider using OFFSET-FETCH or proper indexing'
                    }
                ]
            },
            [types_1.DatabaseType.ORACLE]: {
                databaseType: types_1.DatabaseType.ORACLE,
                customRules: [
                    {
                        id: 'oracle_specific',
                        name: 'Oracle Specific Issues',
                        pattern: 'ROWNUM.*ORDER BY',
                        severity: types_1.Severity.MEDIUM,
                        description: 'ROWNUM applied before ORDER BY',
                        recommendation: 'Use subquery with ORDER BY or modern pagination syntax'
                    }
                ]
            },
            [types_1.DatabaseType.SQLITE]: {
                databaseType: types_1.DatabaseType.SQLITE,
                customRules: [
                    {
                        id: 'sqlite_specific',
                        name: 'SQLite Specific Issues',
                        pattern: 'INSERT.*VALUES.*VALUES',
                        severity: types_1.Severity.MEDIUM,
                        description: 'Multiple VALUES clauses not supported in older SQLite versions',
                        recommendation: 'Use separate INSERT statements or check SQLite version'
                    }
                ]
            },
            [types_1.DatabaseType.GENERIC]: {
                databaseType: types_1.DatabaseType.GENERIC,
                customRules: []
            }
        };
        return databaseSpecificConfigs[databaseType] || {};
    }
    // Method to get environment-specific configuration
    getEnvironmentConfig() {
        const env = process.env.NODE_ENV || 'development';
        const environmentConfigs = {
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
    mergeConfigurations(base, override) {
        return {
            databaseType: override.databaseType || base.databaseType || types_1.DatabaseType.GENERIC,
            securityLevel: override.securityLevel || base.securityLevel || 'moderate',
            enableGPTAnalysis: override.enableGPTAnalysis ?? base.enableGPTAnalysis ?? false,
            enablePerformanceAnalysis: override.enablePerformanceAnalysis ?? base.enablePerformanceAnalysis ?? true,
            ignoredRules: [...(base.ignoredRules || []), ...(override.ignoredRules || [])],
            customRules: [...(base.customRules || []), ...(override.customRules || [])]
        };
    }
    // Method to get configuration summary
    getConfigSummary() {
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
exports.ConfigManager = ConfigManager;
//# sourceMappingURL=ConfigManager.js.map