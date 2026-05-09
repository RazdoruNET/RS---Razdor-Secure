"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Severity = exports.VulnerabilityType = void 0;
var VulnerabilityType;
(function (VulnerabilityType) {
    VulnerabilityType["SQL_INJECTION"] = "sql_injection";
    VulnerabilityType["PERFORMANCE_ISSUE"] = "performance_issue";
    VulnerabilityType["BEST_PRACTICE_VIOLATION"] = "best_practice_violation";
    VulnerabilityType["LOGIC_ERROR"] = "logic_error";
    VulnerabilityType["DATA_EXPOSURE"] = "data_exposure";
    VulnerabilityType["PERMISSION_ISSUE"] = "permission_issue";
    VulnerabilityType["INSECURE_OPERATION"] = "insecure_operation";
})(VulnerabilityType || (exports.VulnerabilityType = VulnerabilityType = {}));
var Severity;
(function (Severity) {
    Severity["CRITICAL"] = "critical";
    Severity["HIGH"] = "high";
    Severity["MEDIUM"] = "medium";
    Severity["LOW"] = "low";
    Severity["INFO"] = "info";
})(Severity || (exports.Severity = Severity = {}));
//# sourceMappingURL=types.js.map