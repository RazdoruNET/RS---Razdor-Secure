import { AppConfig, DatabaseType, CustomRule } from '../types';
export declare class ConfigManager {
    private config;
    private configPath;
    constructor(config?: Partial<AppConfig>, configPath?: string);
    getConfig(): AppConfig;
    updateConfig(updates: Partial<AppConfig>): void;
    private loadConfig;
    private saveConfig;
    private getDefaultConfigPath;
    addCustomRule(rule: CustomRule): void;
    removeCustomRule(ruleId: string): void;
    ignoreRule(ruleId: string): void;
    unignoreRule(ruleId: string): void;
    setSecurityLevel(level: 'strict' | 'moderate' | 'lenient'): void;
    private adjustSeverityThresholds;
    validateConfig(): {
        isValid: boolean;
        errors: string[];
    };
    exportConfig(): string;
    importConfig(configJson: string): void;
    resetToDefaults(): void;
    getDatabaseConfig(databaseType: DatabaseType): Partial<AppConfig>;
    getEnvironmentConfig(): Partial<AppConfig>;
    mergeConfigurations(base: Partial<AppConfig>, override: Partial<AppConfig>): AppConfig;
    getConfigSummary(): string;
}
//# sourceMappingURL=ConfigManager.d.ts.map