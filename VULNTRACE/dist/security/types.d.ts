export interface SecurityConfig {
    readonly: boolean;
    requireConfirmation: boolean;
    enableAuditLogging: boolean;
    trustedWorkspaces: string[];
    blockExternalRequests: boolean;
    offlineMode: boolean;
    ethicalWarningAccepted: boolean;
    auditLogPath?: string;
}
export interface AuditLogEntry {
    timestamp: string;
    action: 'scan_started' | 'scan_completed' | 'file_analyzed' | 'vulnerability_found';
    filePath?: string;
    fileSize?: number;
    queryCount?: number;
    vulnerabilityCount?: number;
    analysisType: 'static' | 'gpt' | 'combined';
    duration?: number;
    metadata: {
        workspaceRoot: string;
        userAgent: string;
        version: string;
    };
}
export interface SecurityContext {
    workspaceRoot: string;
    filePath: string;
    isTrusted: boolean;
    hasUserConsent: boolean;
    auditLogEnabled: boolean;
}
export interface EthicalUsageWarning {
    id: string;
    title: string;
    message: string;
    acceptedAt?: string;
    version: string;
}
export declare enum SecurityViolationType {
    EXTERNAL_REQUEST_BLOCKED = "external_request_blocked",
    UNTRUSTED_WORKSPACE = "untrusted_workspace",
    MISSING_CONSENT = "missing_consent",
    AUTO_MODIFICATION_ATTEMPT = "auto_modification_attempt",
    DATA_EXPORT_ATTEMPT = "data_export_attempt"
}
export interface SecurityViolation {
    type: SecurityViolationType;
    message: string;
    context: SecurityContext;
    timestamp: string;
    blocked: boolean;
}
export interface SandboxConfig {
    enabled: boolean;
    isolationLevel: 'container' | 'vm' | 'process';
    networkIsolated: boolean;
    autoDestroy: boolean;
    maxExecutionTime: number;
    resourceLimits: {
        memory: string;
        cpu: string;
        disk: string;
    };
}
export interface MaliciousSample {
    id: string;
    name: string;
    type: 'virus' | 'trojan' | 'rootkit' | 'exploit' | 'backdoor';
    language: 'python' | 'javascript' | 'cpp' | 'powershell' | 'bash';
    code: string;
    metadata: {
        generatedAt: string;
        generationMethod: string;
        parentIds?: string[];
        mutations: number;
        threatLevel: 'low' | 'medium' | 'high' | 'critical';
    };
}
export interface SandboxExecution {
    id: string;
    sampleId: string;
    startTime: string;
    endTime?: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'terminated';
    containerId?: string;
    logs: SandboxLogEntry[];
    systemCalls: SystemCallRecord[];
    networkActivity: NetworkActivityRecord[];
    fileChanges: FileChangeRecord[];
    analysisResults: ThreatAnalysisResult;
}
export interface SandboxLogEntry {
    timestamp: string;
    level: 'debug' | 'info' | 'warn' | 'error';
    source: string;
    message: string;
}
export interface SystemCallRecord {
    timestamp: string;
    syscall: string;
    args: string[];
    result: number;
    process: string;
}
export interface NetworkActivityRecord {
    timestamp: string;
    protocol: 'tcp' | 'udp' | 'icmp';
    source: string;
    destination: string;
    port: number;
    size: number;
    blocked: boolean;
}
export interface FileChangeRecord {
    timestamp: string;
    action: 'create' | 'modify' | 'delete' | 'rename';
    path: string;
    hash?: string;
    size?: number;
}
export interface ThreatAnalysisResult {
    behaviorGraph: BehaviorNode[];
    techniques: AttackTechnique[];
    anomalies: SecurityAnomaly[];
    signatures: ThreatSignature[];
    riskScore: number;
    summary: string;
}
export interface BehaviorNode {
    id: string;
    type: string;
    description: string;
    timestamp: string;
    children: string[];
    metadata: Record<string, any>;
}
export interface AttackTechnique {
    id: string;
    name: string;
    description: string;
    category: string;
    confidence: number;
    evidence: string[];
}
export interface SecurityAnomaly {
    id: string;
    type: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    timestamp: string;
    context: Record<string, any>;
}
export interface ThreatSignature {
    id: string;
    name: string;
    pattern: string;
    type: 'behavioral' | 'structural' | 'network';
    confidence: number;
    applicable: boolean;
}
export declare enum ProphecySandboxAction {
    SAMPLE_GENERATED = "sample_generated",
    SANDBOX_STARTED = "sandbox_started",
    SANDBOX_COMPLETED = "sandbox_completed",
    THREAT_DETECTED = "threat_detected",
    SIGNATURE_CREATED = "signature_created",
    MODEL_UPDATED = "model_updated",
    UNAUTHORIZED_ACCESS = "unauthorized_access",
    DATA_LEAK_ATTEMPT = "data_leak_attempt"
}
//# sourceMappingURL=types.d.ts.map