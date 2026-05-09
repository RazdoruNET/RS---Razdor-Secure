import { SecurityContext, SecurityViolationType } from '../security/types';
import { EventEmitter } from 'events';
export interface AccessControlConfig {
    jwtSecret: string;
    tokenExpiration: string;
    requireRazdorAuth: boolean;
    maxFailedAttempts: number;
    lockoutDuration: number;
    auditLogPath: string;
    razdorPublicKey?: string;
}
export interface AuthToken {
    token: string;
    userId: string;
    role: 'razdor' | 'admin' | 'analyst' | 'readonly';
    permissions: Permission[];
    issuedAt: string;
    expiresAt: string;
}
export interface Permission {
    resource: string;
    action: string;
    conditions?: Record<string, any>;
}
export interface AccessAttempt {
    id: string;
    timestamp: string;
    userId?: string;
    source: string;
    action: string;
    resource: string;
    success: boolean;
    reason?: string;
    tokenValidated?: boolean;
}
export interface UserSession {
    userId: string;
    role: string;
    permissions: Permission[];
    loginTime: string;
    lastActivity: string;
    failedAttempts: number;
    lockedUntil?: string;
}
export declare class AccessControlSystem extends EventEmitter {
    private config;
    private activeSessions;
    private accessAttempts;
    private razdorPrivateKey;
    private razdorPublicKey;
    constructor(config: AccessControlConfig);
    private generateRazdorKeys;
    authenticateRazdor(signature: string, challenge: string): Promise<AuthToken>;
    validateToken(token: string): Promise<UserSession | null>;
    checkPermission(userId: string, resource: string, action: string, context?: Record<string, any>): Promise<boolean>;
    createSecurityViolation(userId: string, violationType: SecurityViolationType, message: string, context: SecurityContext): Promise<void>;
    private createToken;
    private getRazdorPermissions;
    private verifySignature;
    private matchResource;
    private checkConditions;
    private handleFailedAccess;
    private handleSecurityViolation;
    private terminateSession;
    private parseExpirationTime;
    private logAccessAttempt;
    private loadAccessAttempts;
    getActiveSessions(): UserSession[];
    getAccessAttempts(limit?: number): AccessAttempt[];
    getRazdorPublicKey(): string;
    revokeToken(userId: string): Promise<void>;
    unlockAccount(userId: string): Promise<void>;
    generateChallenge(): string;
    shutdown(): Promise<void>;
}
//# sourceMappingURL=AccessControlSystem.d.ts.map