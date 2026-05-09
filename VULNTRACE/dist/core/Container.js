"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Container = void 0;
exports.createContainer = createContainer;
const ConfigManager_1 = require("../config/ConfigManager");
const SQLParser_1 = require("../parser/SQLParser");
const StaticAnalyzer_1 = require("../analyzer/StaticAnalyzer");
const GPTAnalyzer_1 = require("../gpt/GPTAnalyzer");
const ReportGenerator_1 = require("../reporter/ReportGenerator");
const SecurityManager_1 = require("../security/SecurityManager");
const OfflineModeManager_1 = require("../security/OfflineModeManager");
class Container {
    constructor() {
        this.services = new Map();
        this.factories = new Map();
        this.singletons = new Set();
    }
    register(token, factory, singleton = true) {
        this.factories.set(token, factory);
        if (singleton) {
            this.singletons.add(token);
        }
    }
    get(token) {
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
    has(token) {
        return this.factories.has(token);
    }
    clear() {
        this.services.clear();
        this.factories.clear();
        this.singletons.clear();
    }
}
exports.Container = Container;
function createContainer(config, workspaceRoot = process.cwd()) {
    const container = new Container();
    // Configuration
    container.register('CONFIG_MANAGER', () => new ConfigManager_1.ConfigManager(config));
    // Security services
    container.register('SECURITY_MANAGER', () => {
        const configManager = container.get('CONFIG_MANAGER');
        const securityConfig = {
            enableAuditLogging: true,
            blockExternalRequests: true,
            offlineMode: true,
            ethicalWarningAccepted: false
        };
        return new SecurityManager_1.SecurityManager(workspaceRoot, securityConfig);
    });
    container.register('OFFLINE_MODE_MANAGER', () => OfflineModeManager_1.OfflineModeManager.getInstance());
    // Core services
    container.register('SQL_PARSER', () => {
        const configManager = container.get('CONFIG_MANAGER');
        return new SQLParser_1.SQLParser(configManager.getConfig());
    });
    container.register('STATIC_ANALYZER', () => {
        const configManager = container.get('CONFIG_MANAGER');
        return new StaticAnalyzer_1.StaticAnalyzer(configManager.getConfig());
    });
    container.register('GPT_ANALYZER', () => {
        const configManager = container.get('CONFIG_MANAGER');
        return new GPTAnalyzer_1.GPTAnalyzer(configManager.getConfig());
    });
    container.register('REPORT_GENERATOR', () => {
        const configManager = container.get('CONFIG_MANAGER');
        return new ReportGenerator_1.ReportGenerator(configManager.getConfig());
    });
    return container;
}
//# sourceMappingURL=Container.js.map