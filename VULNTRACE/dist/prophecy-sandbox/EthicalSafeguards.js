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
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.EthicalSafeguards = void 0;
const types_1 = require("../security/types");
const events_1 = require("events");
const crypto = __importStar(require("crypto"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class EthicalSafeguards extends events_1.EventEmitter {
    constructor(config, accessControl) {
        super();
        this.licenseInfo = null;
        this.moralCompassRules = [];
        this.consentRecords = new Map();
        this.ethicalViolations = [];
        this.config = config;
        this.accessControl = accessControl;
        this.loadLicenseInfo();
        this.initializeMoralCompass();
    }
    loadLicenseInfo() {
        try {
            const licensePath = path.join(process.env.HOME || '', '.prophecy-sandbox', 'license.json');
            if (fs.existsSync(licensePath)) {
                const data = fs.readFileSync(licensePath, 'utf8');
                this.licenseInfo = JSON.parse(data);
            }
        }
        catch (error) {
            console.warn('Failed to load license info:', error);
        }
    }
    initializeMoralCompass() {
        if (!this.config.enableMoralCompass)
            return;
        this.moralCompassRules = [
            {
                id: 'no_real_targets',
                name: 'No Real Targets',
                description: 'Cannot target real organizations or systems',
                check: this.checkNoRealTargets.bind(this),
                severity: 'critical'
            },
            {
                id: 'no_zero_day',
                name: 'No Zero-Day Exploits',
                description: 'Cannot generate zero-day exploits without explicit permission',
                check: this.checkNoZeroDay.bind(this),
                severity: 'high'
            },
            {
                id: 'no_civilian_targets',
                name: 'No Civilian Targets',
                description: 'Cannot target civilian infrastructure or systems',
                check: this.checkNoCivilianTargets.bind(this),
                severity: 'critical'
            },
            {
                id: 'no_financial_crime',
                name: 'No Financial Crime',
                description: 'Cannot generate code for financial crimes',
                check: this.checkNoFinancialCrime.bind(this),
                severity: 'critical'
            },
            {
                id: 'research_only',
                name: 'Research Only',
                description: 'All generated code must be for research purposes only',
                check: this.checkResearchOnly.bind(this),
                severity: 'medium'
            }
        ];
    }
    async validateGenerationRequest(userId, request) {
        const violations = [];
        const warnings = [];
        // Check license
        if (this.config.requireLicenseActivation) {
            const licenseValid = await this.validateLicense();
            if (!licenseValid) {
                violations.push(this.createViolation('license_invalid', 'Valid license required for sample generation', { userId, request }, 'blocked'));
            }
        }
        // Check consent
        if (this.config.requireExplicitConsent) {
            const hasConsent = await this.checkExplicitConsent(userId, request);
            if (!hasConsent) {
                violations.push(this.createViolation('consent_missing', 'Explicit consent required for this operation', { userId, request }, 'blocked'));
            }
        }
        // Check target restrictions
        const targetViolation = this.checkTargetRestrictions(request.target, userId);
        if (targetViolation) {
            violations.push(targetViolation);
        }
        // Check complexity limits
        const complexityViolation = this.checkComplexityLimits(request);
        if (complexityViolation) {
            violations.push(complexityViolation);
        }
        // Apply moral compass
        if (this.config.enableMoralCompass) {
            const moralViolations = await this.applyMoralCompass(request, userId);
            violations.push(...moralViolations);
        }
        // Log all validation attempts
        await this.logEthicalCheck(userId, request, violations, warnings);
        // Take action based on violations
        if (violations.some(v => v.action === 'blocked')) {
            await this.handleBlockedRequest(userId, request, violations);
            return { allowed: false, violations, warnings };
        }
        if (violations.some(v => v.action === 'warned')) {
            await this.handleWarnedRequest(userId, request, violations);
            return { allowed: true, violations, warnings };
        }
        return { allowed: true, violations, warnings };
    }
    async validateLicense() {
        if (!this.licenseInfo) {
            return false;
        }
        // Check if license is activated
        if (!this.licenseInfo.activated) {
            return false;
        }
        // Check expiration
        const now = new Date();
        const expiresAt = new Date(this.licenseInfo.expiresAt);
        if (now > expiresAt) {
            return false;
        }
        // Verify license signature (simplified)
        try {
            const licenseData = JSON.stringify({
                licenseKey: this.licenseInfo.licenseKey,
                organization: this.licenseInfo.organization,
                issuedAt: this.licenseInfo.issuedAt,
                expiresAt: this.licenseInfo.expiresAt
            });
            // In real implementation, would verify cryptographic signature
            return true;
        }
        catch (error) {
            return false;
        }
    }
    async checkExplicitConsent(userId, request) {
        const consentKey = `${userId}-${request.type}-${request.target || 'general'}`;
        const consent = this.consentRecords.get(consentKey);
        if (!consent) {
            return false;
        }
        // Check if consent is still valid (24 hours)
        const now = new Date();
        const consentTime = new Date(consent.timestamp);
        const hoursDiff = (now.getTime() - consentTime.getTime()) / (1000 * 60 * 60);
        return hoursDiff <= 24;
    }
    checkTargetRestrictions(target, userId) {
        if (!target)
            return null;
        // Check forbidden targets
        for (const forbidden of this.config.forbiddenTargets) {
            if (target.toLowerCase().includes(forbidden.toLowerCase())) {
                return this.createViolation('target_restriction', `Target "${target}" is forbidden by policy`, { target, userId, forbidden }, 'blocked');
            }
        }
        // Check if target is in allowed list (if specified)
        if (this.config.allowedTargets.length > 0) {
            const isAllowed = this.config.allowedTargets.some(allowed => target.toLowerCase().includes(allowed.toLowerCase()));
            if (!isAllowed) {
                return this.createViolation('target_restriction', `Target "${target}" is not in the allowed targets list`, { target, userId, allowedTargets: this.config.allowedTargets }, 'blocked');
            }
        }
        return null;
    }
    checkComplexityLimits(request) {
        if (request.complexityLevel > this.config.maxComplexityLevel) {
            return this.createViolation('complexity_limit', `Requested complexity level ${request.complexityLevel} exceeds maximum ${this.config.maxComplexityLevel}`, { request, maxComplexity: this.config.maxComplexityLevel }, 'warned');
        }
        return null;
    }
    async applyMoralCompass(request, userId) {
        const violations = [];
        for (const rule of this.moralCompassRules) {
            try {
                const violation = await rule.check(request, userId);
                if (violation) {
                    violations.push(violation);
                }
            }
            catch (error) {
                console.warn(`Moral compass rule ${rule.id} failed:`, error);
            }
        }
        return violations;
    }
    // Moral compass rule implementations
    async checkNoRealTargets(request, userId) {
        const realWorldPatterns = [
            /bank|paypal|stripe|financial/i,
            /hospital|medical|healthcare/i,
            /government|federal|state|police/i,
            /school|university|education/i,
            /power|electric|utility|infrastructure/i,
            /airline|airport|transportation/i
        ];
        for (const pattern of realWorldPatterns) {
            if (pattern.test(request.target || '') || pattern.test(request.description || '')) {
                return this.createViolation('moral_compass', `Request targets real-world critical infrastructure: ${pattern.source}`, { request, pattern: pattern.source }, 'blocked');
            }
        }
        return null;
    }
    async checkNoZeroDay(request, userId) {
        const zeroDayIndicators = [
            'zero day',
            '0day',
            'zero-day',
            'novel exploit',
            'unknown vulnerability',
            'undiscovered'
        ];
        const text = `${request.description} ${request.target || ''}`.toLowerCase();
        for (const indicator of zeroDayIndicators) {
            if (text.includes(indicator)) {
                return this.createViolation('moral_compass', `Request appears to target zero-day vulnerabilities: ${indicator}`, { request, indicator }, 'blocked');
            }
        }
        return null;
    }
    async checkNoCivilianTargets(request, userId) {
        const civilianPatterns = [
            /civilian|citizen|public/i,
            /residential|home|personal/i,
            /consumer|customer|user/i
        ];
        for (const pattern of civilianPatterns) {
            if (pattern.test(request.target || '') || pattern.test(request.description || '')) {
                return this.createViolation('moral_compass', `Request targets civilian systems: ${pattern.source}`, { request, pattern: pattern.source }, 'blocked');
            }
        }
        return null;
    }
    async checkNoFinancialCrime(request, userId) {
        const financialCrimePatterns = [
            /fraud|scam|phishing/i,
            /money laundering|crypto theft/i,
            /ransomware|extortion/i,
            /identity theft|credit card/i
        ];
        const text = `${request.description} ${request.target || ''}`.toLowerCase();
        for (const pattern of financialCrimePatterns) {
            if (text.includes(pattern.source)) {
                return this.createViolation('moral_compass', `Request appears to facilitate financial crime: ${pattern.source}`, { request, pattern: pattern.source }, 'blocked');
            }
        }
        return null;
    }
    async checkResearchOnly(request, userId) {
        const nonResearchIndicators = [
            'production',
            'deploy',
            'attack',
            'real world',
            'live'
        ];
        const text = `${request.description} ${request.target || ''}`.toLowerCase();
        for (const indicator of nonResearchIndicators) {
            if (text.includes(indicator)) {
                return this.createViolation('moral_compass', `Request appears to be for non-research purposes: ${indicator}`, { request, indicator }, 'warned');
            }
        }
        return null;
    }
    createViolation(type, description, context, action) {
        const violation = {
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            type,
            severity: this.getViolationSeverity(type),
            description,
            context,
            action
        };
        this.ethicalViolations.push(violation);
        this.emit('ethicalViolation', violation);
        return violation;
    }
    getViolationSeverity(type) {
        const severityMap = {
            'target_restriction': 'critical',
            'complexity_limit': 'medium',
            'consent_missing': 'high',
            'license_invalid': 'critical',
            'moral_compass': 'critical'
        };
        return severityMap[type] || 'medium';
    }
    async handleBlockedRequest(userId, request, violations) {
        // Log security violation
        await this.accessControl.createSecurityViolation(userId, types_1.SecurityViolationType.UNAUTHORIZED_ACCESS, `Request blocked by ethical safeguards: ${violations.map(v => v.description).join(', ')}`, {
            workspaceRoot: '',
            filePath: '',
            isTrusted: false,
            hasUserConsent: false,
            auditLogEnabled: true
        });
        // Emit event for monitoring
        this.emit('requestBlocked', { userId, request, violations });
    }
    async handleWarnedRequest(userId, request, violations) {
        // Log warning
        console.warn(`Ethical warning for user ${userId}:`, violations.map(v => v.description));
        // Emit event for monitoring
        this.emit('requestWarned', { userId, request, violations });
    }
    async logEthicalCheck(userId, request, violations, warnings) {
        if (!this.config.auditAllActions)
            return;
        const logEntry = {
            timestamp: new Date().toISOString(),
            userId,
            request,
            violations: violations.map(v => ({ id: v.id, type: v.type, description: v.description })),
            warnings,
            outcome: violations.some(v => v.action === 'blocked') ? 'blocked' : 'allowed'
        };
        // Log to file
        try {
            const logPath = path.join(process.env.HOME || '', '.prophecy-sandbox', 'ethical-audit.log');
            await fs.promises.appendFile(logPath, JSON.stringify(logEntry) + '\n');
        }
        catch (error) {
            console.warn('Failed to log ethical check:', error);
        }
    }
    // Public API methods
    async grantExplicitConsent(userId, request) {
        const consentKey = `${userId}-${request.type}-${request.target || 'general'}`;
        const consent = {
            id: crypto.randomUUID(),
            userId,
            request,
            timestamp: new Date().toISOString(),
            ipAddress: 'localhost', // Would be extracted from request
            userAgent: 'prophecy-sandbox-cli'
        };
        this.consentRecords.set(consentKey, consent);
        this.emit('consentGranted', consent);
    }
    async activateLicense(licenseKey, organization) {
        try {
            // Validate license key format (simplified)
            if (!licenseKey || licenseKey.length < 32) {
                return false;
            }
            // Create license info
            this.licenseInfo = {
                licenseKey,
                organization,
                issuedAt: new Date().toISOString(),
                expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1 year
                features: ['sample-generation', 'threat-analysis', 'learning'],
                restrictions: ['research-only', 'no-real-targets'],
                activated: true,
                activationId: crypto.randomUUID()
            };
            // Save license info
            const licensePath = path.join(process.env.HOME || '', '.prophecy-sandbox', 'license.json');
            await fs.promises.mkdir(path.dirname(licensePath), { recursive: true });
            await fs.promises.writeFile(licensePath, JSON.stringify(this.licenseInfo, null, 2));
            this.emit('licenseActivated', this.licenseInfo);
            return true;
        }
        catch (error) {
            console.error('Failed to activate license:', error);
            return false;
        }
    }
    getLicenseInfo() {
        return this.licenseInfo ? { ...this.licenseInfo } : null;
    }
    getEthicalViolations(limit) {
        return limit ? this.ethicalViolations.slice(-limit) : [...this.ethicalViolations];
    }
    getMoralCompassRules() {
        return [...this.moralCompassRules];
    }
    async reset() {
        this.consentRecords.clear();
        this.ethicalViolations = [];
        this.licenseInfo = null;
        // Remove license file
        try {
            const licensePath = path.join(process.env.HOME || '', '.prophecy-sandbox', 'license.json');
            if (fs.existsSync(licensePath)) {
                await fs.promises.unlink(licensePath);
            }
        }
        catch (error) {
            console.warn('Failed to remove license file:', error);
        }
    }
}
exports.EthicalSafeguards = EthicalSafeguards;
//# sourceMappingURL=EthicalSafeguards.js.map