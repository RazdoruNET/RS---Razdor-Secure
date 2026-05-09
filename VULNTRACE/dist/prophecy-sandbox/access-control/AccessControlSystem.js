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
exports.AccessControlSystem = void 0;
const jwt = __importStar(require("jsonwebtoken"));
const crypto = __importStar(require("crypto"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const types_1 = require("../security/types");
const events_1 = require("events");
class AccessControlSystem extends events_1.EventEmitter {
    constructor(config) {
        super();
        this.activeSessions = new Map();
        this.accessAttempts = [];
        this.config = config;
        this.generateRazdorKeys();
        this.loadAccessAttempts();
    }
    generateRazdorKeys() {
        // Generate or load RAZDOR's cryptographic key pair
        const keyPath = path.join(path.dirname(this.config.auditLogPath), 'razdor-keys');
        try {
            if (fs.existsSync(path.join(keyPath, 'private.pem'))) {
                this.razdorPrivateKey = fs.readFileSync(path.join(keyPath, 'private.pem'), 'utf8');
                this.razdorPublicKey = fs.readFileSync(path.join(keyPath, 'public.pem'), 'utf8');
            }
            else {
                // Generate new key pair
                const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
                    modulusLength: 4096,
                    publicKeyEncoding: { type: 'spki', format: 'pem' },
                    privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
                });
                this.razdorPrivateKey = privateKey;
                this.razdorPublicKey = publicKey;
                // Save keys
                fs.mkdirSync(keyPath, { recursive: true });
                fs.writeFileSync(path.join(keyPath, 'private.pem'), privateKey);
                fs.writeFileSync(path.join(keyPath, 'public.pem'), publicKey);
                // Secure permissions
                fs.chmodSync(path.join(keyPath, 'private.pem'), 0o600);
                fs.chmodSync(path.join(keyPath, 'public.pem'), 0o644);
            }
        }
        catch (error) {
            console.error('Failed to initialize RAZDOR keys:', error);
            throw new Error('Access control system initialization failed');
        }
    }
    async authenticateRazdor(signature, challenge) {
        // Verify RAZDOR's signature using the public key
        const isValid = this.verifySignature(challenge, signature, this.razdorPublicKey);
        if (!isValid) {
            await this.logAccessAttempt({
                id: crypto.randomUUID(),
                timestamp: new Date().toISOString(),
                source: 'razdor-auth',
                action: 'authenticate',
                resource: 'prophecy-sandbox',
                success: false,
                reason: 'Invalid signature'
            });
            throw new Error('RAZDOR authentication failed');
        }
        // Create RAZDOR session with full permissions
        const token = this.createToken({
            userId: 'razdor',
            role: 'razdor',
            permissions: this.getRazdorPermissions()
        });
        await this.logAccessAttempt({
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            userId: 'razdor',
            source: 'razdor-auth',
            action: 'authenticate',
            resource: 'prophecy-sandbox',
            success: true,
            tokenValidated: true
        });
        this.emit('razdorAuthenticated', token);
        return token;
    }
    async validateToken(token) {
        try {
            const decoded = jwt.verify(token, this.config.jwtSecret);
            const session = this.activeSessions.get(decoded.userId);
            if (!session) {
                throw new Error('Session not found');
            }
            // Check if session is locked
            if (session.lockedUntil && new Date(session.lockedUntil) > new Date()) {
                throw new Error('Account locked');
            }
            // Update last activity
            session.lastActivity = new Date().toISOString();
            this.activeSessions.set(decoded.userId, session);
            return session;
        }
        catch (error) {
            await this.logAccessAttempt({
                id: crypto.randomUUID(),
                timestamp: new Date().toISOString(),
                source: 'token-validation',
                action: 'validate',
                resource: 'prophecy-sandbox',
                success: false,
                reason: error.message,
                tokenValidated: false
            });
            return null;
        }
    }
    async checkPermission(userId, resource, action, context) {
        const session = this.activeSessions.get(userId);
        if (!session) {
            return false;
        }
        // Check if user is locked
        if (session.lockedUntil && new Date(session.lockedUntil) > new Date()) {
            return false;
        }
        // Check permissions
        const hasPermission = session.permissions.some(permission => {
            const resourceMatch = this.matchResource(permission.resource, resource);
            const actionMatch = permission.action === action || permission.action === '*';
            const conditionsMatch = this.checkConditions(permission.conditions, context);
            return resourceMatch && actionMatch && conditionsMatch;
        });
        const attempt = {
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            userId,
            source: 'permission-check',
            action,
            resource,
            success: hasPermission,
            reason: hasPermission ? undefined : 'Insufficient permissions'
        };
        await this.logAccessAttempt(attempt);
        if (!hasPermission) {
            this.handleFailedAccess(userId);
            this.emit('accessDenied', attempt);
        }
        return hasPermission;
    }
    async createSecurityViolation(userId, violationType, message, context) {
        const violation = {
            type: violationType,
            message,
            context,
            timestamp: new Date().toISOString(),
            blocked: true
        };
        // Log security violation
        await this.logAccessAttempt({
            id: crypto.randomUUID(),
            timestamp: violation.timestamp,
            userId,
            source: 'security-violation',
            action: 'violation',
            resource: 'prophecy-sandbox',
            success: false,
            reason: `${violationType}: ${message}`
        });
        // Take appropriate action based on violation type
        this.handleSecurityViolation(userId, violationType);
        this.emit('securityViolation', violation);
    }
    createToken(userData) {
        const payload = {
            userId: userData.userId,
            role: userData.role,
            permissions: userData.permissions
        };
        const token = jwt.sign(payload, this.config.jwtSecret, {
            expiresIn: this.config.tokenExpiration,
            issuer: 'prophecy-sandbox',
            audience: 'cascade-swe-1.5'
        });
        const now = new Date();
        const expiresAt = new Date(now.getTime() + this.parseExpirationTime(this.config.tokenExpiration));
        const authToken = {
            token,
            userId: userData.userId,
            role: userData.role,
            permissions: userData.permissions,
            issuedAt: now.toISOString(),
            expiresAt: expiresAt.toISOString()
        };
        // Store session
        this.activeSessions.set(userData.userId, {
            userId: userData.userId,
            role: userData.role,
            permissions: userData.permissions,
            loginTime: now.toISOString(),
            lastActivity: now.toISOString(),
            failedAttempts: 0
        });
        return authToken;
    }
    getRazdorPermissions() {
        return [
            { resource: '*', action: '*', conditions: { owner: 'razdor' } },
            { resource: 'prophecy-sandbox', action: 'admin' },
            { resource: 'samples', action: ['generate', 'execute', 'analyze'] },
            { resource: 'techniques', action: ['create', 'modify', 'delete'] },
            { resource: 'signatures', action: ['create', 'modify', 'delete'] },
            { resource: 'access-control', action: 'admin' },
            { resource: 'audit-logs', action: 'read' }
        ];
    }
    verifySignature(data, signature, publicKey) {
        try {
            return crypto.verify('sha256', Buffer.from(data), publicKey, Buffer.from(signature, 'base64'));
        }
        catch (error) {
            return false;
        }
    }
    matchResource(permissionResource, requestedResource) {
        if (permissionResource === '*')
            return true;
        if (permissionResource === requestedResource)
            return true;
        // Support wildcard patterns
        const regex = new RegExp(permissionResource.replace('*', '.*'));
        return regex.test(requestedResource);
    }
    checkConditions(conditions, context) {
        if (!conditions)
            return true;
        if (!context)
            return false;
        for (const [key, value] of Object.entries(conditions)) {
            if (context[key] !== value) {
                return false;
            }
        }
        return true;
    }
    handleFailedAccess(userId) {
        const session = this.activeSessions.get(userId);
        if (!session)
            return;
        session.failedAttempts++;
        // Lock account if too many failed attempts
        if (session.failedAttempts >= this.config.maxFailedAttempts) {
            session.lockedUntil = new Date(Date.now() + this.config.lockoutDuration).toISOString();
            this.emit('accountLocked', { userId, lockedUntil: session.lockedUntil });
        }
        this.activeSessions.set(userId, session);
    }
    handleSecurityViolation(userId, violationType) {
        switch (violationType) {
            case types_1.SecurityViolationType.UNAUTHORIZED_ACCESS:
                // Immediate lockout for unauthorized access
                const session = this.activeSessions.get(userId);
                if (session) {
                    session.lockedUntil = new Date(Date.now() + this.config.lockoutDuration * 2).toISOString();
                    this.activeSessions.set(userId, session);
                }
                break;
            case types_1.SecurityViolationType.DATA_EXPORT_ATTEMPT:
                // Immediate termination and lockout
                this.terminateSession(userId);
                break;
            case types_1.SecurityViolationType.AUTO_MODIFICATION_ATTEMPT:
                // Warning and temporary lockout
                this.handleFailedAccess(userId);
                break;
            default:
                // Log and monitor
                break;
        }
    }
    terminateSession(userId) {
        this.activeSessions.delete(userId);
        this.emit('sessionTerminated', { userId, reason: 'security_violation' });
    }
    parseExpirationTime(expiration) {
        // Parse expiration time (e.g., '24h', '7d', '30m')
        const match = expiration.match(/^(\\d+)([hdwms])$/);
        if (!match)
            return 24 * 60 * 60 * 1000; // Default 24 hours
        const [, amount, unit] = match;
        const multipliers = { h: 3600000, d: 86400000, w: 604800000, m: 60000, s: 1000 };
        return parseInt(amount) * (multipliers[unit] || 3600000);
    }
    async logAccessAttempt(attempt) {
        this.accessAttempts.push(attempt);
        // Keep only recent attempts (last 1000)
        if (this.accessAttempts.length > 1000) {
            this.accessAttempts = this.accessAttempts.slice(-1000);
        }
        // Write to audit log
        try {
            const logEntry = `${attempt.timestamp} [${attempt.success ? 'ALLOW' : 'DENY'}] ${attempt.userId || 'anonymous'} ${attempt.action} ${attempt.resource}${attempt.reason ? ` - ${attempt.reason}` : ''}\n`;
            await fs.promises.appendFile(this.config.auditLogPath, logEntry);
        }
        catch (error) {
            console.error('Failed to write access attempt to audit log:', error);
        }
        this.emit('accessAttemptLogged', attempt);
    }
    loadAccessAttempts() {
        try {
            if (fs.existsSync(this.config.auditLogPath)) {
                const content = fs.readFileSync(this.config.auditLogPath, 'utf8');
                const lines = content.trim().split('\n');
                for (const line of lines) {
                    if (line.trim()) {
                        // Parse log entry (simplified)
                        const parts = line.split(' ');
                        if (parts.length >= 4) {
                            const timestamp = parts[0] + ' ' + parts[1];
                            const status = parts[2].replace('[', '').replace(']', '');
                            const userId = parts[3];
                            const action = parts[4];
                            const resource = parts[5];
                            const success = status === 'ALLOW';
                            this.accessAttempts.push({
                                id: crypto.randomUUID(),
                                timestamp,
                                userId: userId !== 'anonymous' ? userId : undefined,
                                source: 'audit-log',
                                action,
                                resource,
                                success,
                                tokenValidated: success
                            });
                        }
                    }
                }
            }
        }
        catch (error) {
            console.warn('Failed to load access attempts:', error);
        }
    }
    // Public API methods
    getActiveSessions() {
        return Array.from(this.activeSessions.values());
    }
    getAccessAttempts(limit) {
        return limit ? this.accessAttempts.slice(-limit) : this.accessAttempts;
    }
    getRazdorPublicKey() {
        return this.razdorPublicKey;
    }
    async revokeToken(userId) {
        this.terminateSession(userId);
        await this.logAccessAttempt({
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            userId,
            source: 'token-revocation',
            action: 'revoke',
            resource: 'prophecy-sandbox',
            success: true
        });
    }
    async unlockAccount(userId) {
        const session = this.activeSessions.get(userId);
        if (session) {
            session.lockedUntil = undefined;
            session.failedAttempts = 0;
            this.activeSessions.set(userId, session);
            await this.logAccessAttempt({
                id: crypto.randomUUID(),
                timestamp: new Date().toISOString(),
                userId,
                source: 'account-unlock',
                action: 'unlock',
                resource: 'prophecy-sandbox',
                success: true
            });
        }
    }
    generateChallenge() {
        return crypto.randomBytes(32).toString('base64');
    }
    async shutdown() {
        // Terminate all active sessions
        for (const userId of this.activeSessions.keys()) {
            this.terminateSession(userId);
        }
        // Save final audit log
        await this.logAccessAttempt({
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            source: 'system',
            action: 'shutdown',
            resource: 'prophecy-sandbox',
            success: true
        });
        console.log('Access control system shutdown completed');
    }
}
exports.AccessControlSystem = AccessControlSystem;
//# sourceMappingURL=AccessControlSystem.js.map