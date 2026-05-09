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
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.SQLVulnerabilityPlugin = exports.ConfigManager = exports.ReportGenerator = exports.GPTAnalyzer = exports.StaticAnalyzer = exports.SQLParser = exports.CascadeIntegration = exports.SQLVulnerabilityScanner = void 0;
var SQLVulnerabilityScanner_1 = require("./core/SQLVulnerabilityScanner");
Object.defineProperty(exports, "SQLVulnerabilityScanner", { enumerable: true, get: function () { return SQLVulnerabilityScanner_1.SQLVulnerabilityScanner; } });
var CascadeIntegration_1 = require("./ide/CascadeIntegration");
Object.defineProperty(exports, "CascadeIntegration", { enumerable: true, get: function () { return CascadeIntegration_1.CascadeIntegration; } });
__exportStar(require("./types"), exports);
var SQLParser_1 = require("./parser/SQLParser");
Object.defineProperty(exports, "SQLParser", { enumerable: true, get: function () { return SQLParser_1.SQLParser; } });
var StaticAnalyzer_1 = require("./analyzer/StaticAnalyzer");
Object.defineProperty(exports, "StaticAnalyzer", { enumerable: true, get: function () { return StaticAnalyzer_1.StaticAnalyzer; } });
var GPTAnalyzer_1 = require("./gpt/GPTAnalyzer");
Object.defineProperty(exports, "GPTAnalyzer", { enumerable: true, get: function () { return GPTAnalyzer_1.GPTAnalyzer; } });
var ReportGenerator_1 = require("./reporter/ReportGenerator");
Object.defineProperty(exports, "ReportGenerator", { enumerable: true, get: function () { return ReportGenerator_1.ReportGenerator; } });
var ConfigManager_1 = require("./config/ConfigManager");
Object.defineProperty(exports, "ConfigManager", { enumerable: true, get: function () { return ConfigManager_1.ConfigManager; } });
// Main entry point for the plugin
class SQLVulnerabilityPlugin {
    constructor(config) {
        this.scanner = new SQLVulnerabilityScanner(config);
        this.integration = new CascadeIntegration(this.scanner);
    }
    async activate() {
        console.log('SQL Vulnerability Scanner plugin activated');
    }
    async deactivate() {
        console.log('SQL Vulnerability Scanner plugin deactivated');
    }
    getScanner() {
        return this.scanner;
    }
    getIntegration() {
        return this.integration;
    }
}
exports.SQLVulnerabilityPlugin = SQLVulnerabilityPlugin;
// Default export for easy importing
exports.default = SQLVulnerabilityPlugin;
//# sourceMappingURL=main.js.map