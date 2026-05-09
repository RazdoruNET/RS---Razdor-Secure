import { ConfigManager } from '../config/ConfigManager';
import { SQLParser } from '../parser/SQLParser';
import { StaticAnalyzer } from '../analyzer/StaticAnalyzer';
import { GPTAnalyzer } from '../gpt/GPTAnalyzer';
import { ReportGenerator } from '../reporter/ReportGenerator';
import { SecurityManager } from '../security/SecurityManager';
import { OfflineModeManager } from '../security/OfflineModeManager';
import { AppConfig } from '../types';

export interface ServiceToken {
  CONFIG_MANAGER: 'CONFIG_MANAGER';
  SQL_PARSER: 'SQL_PARSER';
  STATIC_ANALYZER: 'STATIC_ANALYZER';
  GPT_ANALYZER: 'GPT_ANALYZER';
  REPORT_GENERATOR: 'REPORT_GENERATOR';
  SECURITY_MANAGER: 'SECURITY_MANAGER';
  OFFLINE_MODE_MANAGER: 'OFFLINE_MODE_MANAGER';
}

export class Container {
  private services = new Map<string, any>();
  private factories = new Map<string, () => any>();
  private singletons = new Set<string>();

  register<T>(token: string, factory: () => T, singleton = true): void {
    this.factories.set(token, factory);
    if (singleton) {
      this.singletons.add(token);
    }
  }

  get<T>(token: string): T {
    // Check if already instantiated
    if (this.services.has(token)) {
      return this.services.get(token);
    }

    // Get factory
    const factory = this.factories.get(token);
    if (!factory) {
      throw new Error(`Service ${token} not registered`);
    }

    // Create instance
    const instance = factory();

    // Store if singleton
    if (this.singletons.has(token)) {
      this.services.set(token, instance);
    }

    return instance;
  }

  has(token: string): boolean {
    return this.factories.has(token);
  }

  clear(): void {
    this.services.clear();
    this.factories.clear();
    this.singletons.clear();
  }
}

export function createContainer(config?: Partial<AppConfig>, workspaceRoot: string = process.cwd()): Container {
  const container = new Container();

  // Configuration
  container.register('CONFIG_MANAGER', () => new ConfigManager(config));

  // Security services
  container.register('SECURITY_MANAGER', () => {
    const configManager = container.get('CONFIG_MANAGER');
    const securityConfig = {
      readonly: false,
      requireConfirmation: true,
      enableAuditLogging: true,
      trustedWorkspaces: [workspaceRoot],
      blockExternalRequests: true,
      offlineMode: true,
      ethicalWarningAccepted: false
    };
    return new SecurityManager(workspaceRoot, securityConfig);
  });

  container.register('OFFLINE_MODE_MANAGER', () => OfflineModeManager.getInstance());

  // Core services
  container.register('SQL_PARSER', () => {
    const configManager = container.get('CONFIG_MANAGER') as ConfigManager;
    return new SQLParser(configManager.getConfig());
  });

  container.register('STATIC_ANALYZER', () => {
    const configManager = container.get('CONFIG_MANAGER') as ConfigManager;
    return new StaticAnalyzer(configManager.getConfig());
  });

  container.register('GPT_ANALYZER', () => {
    const configManager = container.get('CONFIG_MANAGER') as ConfigManager;
    return new GPTAnalyzer(configManager.getConfig());
  });

  container.register('REPORT_GENERATOR', () => {
    const configManager = container.get('CONFIG_MANAGER') as ConfigManager;
    return new ReportGenerator(configManager.getConfig());
  });

  return container;
}
