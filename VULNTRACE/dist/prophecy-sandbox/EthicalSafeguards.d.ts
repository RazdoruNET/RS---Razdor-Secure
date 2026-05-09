import { AccessControlSystem } from './access-control/AccessControlSystem';
import { EventEmitter } from 'events';
export interface EthicalConfig {
    enableMoralCompass: boolean;
    requireLicenseActivation: boolean;
    allowedTargets: string[];
    forbiddenTargets: string[];
    maxComplexityLevel: number;
    requireExplicitConsent: boolean;
    auditAllActions: boolean;
    autoBlockSuspicious: boolean;
}
export interface LicenseInfo {
    licenseKey: string;
    organization: string;
    issuedAt: string;
    expiresAt: string;
    features: string[];
    restrictions: string[];
    activated: boolean;
    activationId?: string;
}
export interface EthicalViolation {
    id: string;
    timestamp: string;
    type: 'target_restriction' | 'complexity_limit' | 'consent_missing' | 'license_invalid' | 'moral_compass';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    context: any;
    action: 'blocked' | 'warned' | 'logged';
}
export declare class EthicalSafeguards extends EventEmitter {
    private config;
    private accessControl;
    private licenseInfo;
    private moralCompassRules;
    private consentRecords;
    private ethicalViolations;
    constructor(config: EthicalConfig, accessControl: AccessControlSystem);
    private loadLicenseInfo;
    private initializeMoralCompass;
    validateGenerationRequest(userId: string, request: GenerationRequest): Promise<EthicalValidationResult>;
    private validateLicense;
    private checkExplicitConsent;
    private checkTargetRestrictions;
    private checkComplexityLimits;
    private applyMoralCompass;
    private checkNoRealTargets;
    private checkNoZeroDay;
    private checkNoCivilianTargets;
    private checkNoFinancialCrime;
    private checkResearchOnly;
    private createViolation;
    private getViolationSeverity;
    private handleBlockedRequest;
    private handleWarnedRequest;
    private logEthicalCheck;
    grantExplicitConsent(userId: string, request: GenerationRequest): Promise<void>;
    activateLicense(licenseKey: string, organization: string): Promise<boolean>;
    getLicenseInfo(): LicenseInfo | null;
    getEthicalViolations(limit?: number): EthicalViolation[];
    getMoralCompassRules(): MoralCompassRule[];
    reset(): Promise<void>;
}
interface GenerationRequest {
    type: string;
    target?: string;
    description: string;
    complexityLevel: number;
    userId: string;
}
interface EthicalValidationResult {
    allowed: boolean;
    violations: EthicalViolation[];
    warnings: string[];
}
interface MoralCompassRule {
    id: string;
    name: string;
    description: string;
    check: (request: GenerationRequest, userId: string) => Promise<EthicalViolation | null>;
    severity: EthicalViolation['severity'];
}
export {};
//# sourceMappingURL=EthicalSafeguards.d.ts.map