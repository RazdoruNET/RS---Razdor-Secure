"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SECURITY_CONSTANTS = void 0;
// Security configuration constants
exports.SECURITY_CONSTANTS = {
    // Timeouts in milliseconds
    USER_INPUT_TIMEOUT: 30000,
    NETWORK_REQUEST_TIMEOUT: 10000,
    ANALYSIS_TIMEOUT: 300000,
    // File paths
    LICENSE_PATH: '.prophecy-sandbox/license.json',
    AUDIT_LOG_PATH: '.prophecy-sandbox/audit.log',
    ETHICAL_WARNING_PATH: '.prophecy-sandbox/ethical-warning.json',
    // Buffer sizes
    DEFAULT_BUFFER_SIZE: 8192,
    NETWORK_BUFFER_SIZE: 65536,
    LOG_BUFFER_SIZE: 1024,
    // Retry counts
    MAX_RETRY_ATTEMPTS: 3,
    MAX_AUTH_ATTEMPTS: 5,
    // File size limits
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
    MAX_LOG_SIZE: 10 * 1024 * 1024, // 10MB
    // Network settings
    MAX_CONCURRENT_REQUESTS: 10,
    RATE_LIMIT_WINDOW: 60000, // 1 minute
    // Security thresholds
    MAX_RISK_SCORE: 100,
    CRITICAL_RISK_THRESHOLD: 80,
    HIGH_RISK_THRESHOLD: 60,
    MEDIUM_RISK_THRESHOLD: 40,
    // ML model settings
    FEATURE_VECTOR_SIZE: 256,
    MODEL_TRAINING_EPOCHS: 100,
    MODEL_BATCH_SIZE: 32,
    // Docker settings
    DEFAULT_MEMORY_LIMIT: '512m',
    DEFAULT_CPU_LIMIT: '0.5',
    DEFAULT_TIMEOUT: 60000, // 1 minute
    // Cryptographic settings
    DEFAULT_KEY_SIZE: 2048,
    DEFAULT_SALT_SIZE: 32,
    DEFAULT_IV_SIZE: 16,
    // Fuzzing settings
    MAX_FUZZING_INPUTS: 1000,
    MAX_FUZZING_DURATION: 300000, // 5 minutes
    // Monitoring settings
    MONITORING_INTERVAL: 5000, // 5 seconds
    STATS_COLLECTION_INTERVAL: 10000, // 10 seconds
    // Cache settings
    CACHE_TTL: 3600000, // 1 hour
    MAX_CACHE_SIZE: 1000,
    // Logging levels
    LOG_LEVELS: {
        ERROR: 'error',
        WARN: 'warn',
        INFO: 'info',
        DEBUG: 'debug'
    },
    // Event types
    EVENT_TYPES: {
        SECURITY_VIOLATION: 'security_violation',
        AUDIT_LOG: 'audit_log',
        ANALYSIS_STARTED: 'analysis_started',
        ANALYSIS_COMPLETED: 'analysis_completed',
        THREAT_DETECTED: 'threat_detected',
        SYSTEM_ERROR: 'system_error'
    },
    // Status codes
    STATUS_CODES: {
        SUCCESS: 'success',
        ERROR: 'error',
        WARNING: 'warning',
        PENDING: 'pending',
        BLOCKED: 'blocked',
        TIMEOUT: 'timeout'
    }
};
//# sourceMappingURL=constants.js.map