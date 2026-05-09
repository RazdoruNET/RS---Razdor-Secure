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
export declare class Container {
    private services;
    private factories;
    private singletons;
    register<T>(token: string, factory: () => T, singleton?: boolean): void;
    get<T>(token: string): T;
    has(token: string): boolean;
    clear(): void;
}
export declare function createContainer(config?: Partial<AppConfig>, workspaceRoot?: string): Container;
//# sourceMappingURL=Container.d.ts.map