"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DatabaseType = exports.QueryType = exports.VulnerabilityCategory = exports.Severity = exports.VulnerabilityType = void 0;
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
var VulnerabilityCategory;
(function (VulnerabilityCategory) {
    VulnerabilityCategory["SECURITY"] = "security";
    VulnerabilityCategory["PERFORMANCE"] = "performance";
    VulnerabilityCategory["MAINTAINABILITY"] = "maintainability";
    VulnerabilityCategory["RELIABILITY"] = "reliability";
    VulnerabilityCategory["BEST_PRACTICE_VIOLATION"] = "best_practice_violation";
})(VulnerabilityCategory || (exports.VulnerabilityCategory = VulnerabilityCategory = {}));
var QueryType;
(function (QueryType) {
    QueryType["SELECT"] = "SELECT";
    QueryType["INSERT"] = "INSERT";
    QueryType["UPDATE"] = "UPDATE";
    QueryType["DELETE"] = "DELETE";
    QueryType["CREATE"] = "CREATE";
    QueryType["ALTER"] = "ALTER";
    QueryType["DROP"] = "DROP";
    QueryType["TRUNCATE"] = "TRUNCATE";
    QueryType["MERGE"] = "MERGE";
    QueryType["EXEC"] = "EXEC";
    QueryType["UNKNOWN"] = "UNKNOWN";
})(QueryType || (exports.QueryType = QueryType = {}));
var DatabaseType;
(function (DatabaseType) {
    DatabaseType["MYSQL"] = "mysql";
    DatabaseType["POSTGRESQL"] = "postgresql";
    DatabaseType["MSSQL"] = "mssql";
    DatabaseType["ORACLE"] = "oracle";
    DatabaseType["SQLITE"] = "sqlite";
    DatabaseType["GENERIC"] = "generic";
})(DatabaseType || (exports.DatabaseType = DatabaseType = {}));
//# sourceMappingURL=index.js.map