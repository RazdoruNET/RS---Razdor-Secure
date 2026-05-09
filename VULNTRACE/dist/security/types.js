"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProphecySandboxAction = exports.SecurityViolationType = void 0;
var SecurityViolationType;
(function (SecurityViolationType) {
    SecurityViolationType["EXTERNAL_REQUEST_BLOCKED"] = "external_request_blocked";
    SecurityViolationType["UNTRUSTED_WORKSPACE"] = "untrusted_workspace";
    SecurityViolationType["MISSING_CONSENT"] = "missing_consent";
    SecurityViolationType["AUTO_MODIFICATION_ATTEMPT"] = "auto_modification_attempt";
    SecurityViolationType["DATA_EXPORT_ATTEMPT"] = "data_export_attempt";
})(SecurityViolationType || (exports.SecurityViolationType = SecurityViolationType = {}));
var ProphecySandboxAction;
(function (ProphecySandboxAction) {
    ProphecySandboxAction["SAMPLE_GENERATED"] = "sample_generated";
    ProphecySandboxAction["SANDBOX_STARTED"] = "sandbox_started";
    ProphecySandboxAction["SANDBOX_COMPLETED"] = "sandbox_completed";
    ProphecySandboxAction["THREAT_DETECTED"] = "threat_detected";
    ProphecySandboxAction["SIGNATURE_CREATED"] = "signature_created";
    ProphecySandboxAction["MODEL_UPDATED"] = "model_updated";
    ProphecySandboxAction["UNAUTHORIZED_ACCESS"] = "unauthorized_access";
    ProphecySandboxAction["DATA_LEAK_ATTEMPT"] = "data_leak_attempt";
})(ProphecySandboxAction || (exports.ProphecySandboxAction = ProphecySandboxAction = {}));
//# sourceMappingURL=types.js.map