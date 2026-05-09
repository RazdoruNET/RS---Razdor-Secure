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
exports.ProphecySandbox = void 0;
const SecurityManager_1 = require("../security/SecurityManager");
const AccessControlSystem_1 = require("./access-control/AccessControlSystem");
const MaliciousCodeConstructor_1 = require("./constructor/MaliciousCodeConstructor");
const SandboxEnvironment_1 = require("./sandbox/SandboxEnvironment");
const ThreatAnalyzer_1 = require("./analyzer/ThreatAnalyzer");
const SelfLearningSystem_1 = require("./learning/SelfLearningSystem");
const WebDashboard_1 = require("./dashboard/WebDashboard");
const CLIInterface_1 = require("./cli/CLIInterface");
const events_1 = require("events");
const path = __importStar(require("path"));
class ProphecySandbox extends events_1.EventEmitter {
    constructor(workspaceRoot, baseSecurityConfig, config) {
        super();
        this.isInitialized = false;
        this.isRunning = false;
        this.config = config;
        // Initialize security components
        this.securityManager = new SecurityManager_1.SecurityManager(workspaceRoot, baseSecurityConfig);
        this.auditLogger = this.securityManager.getAuditLogger();
        // Initialize Prophecy Sandbox components
        this.initializeComponents(workspaceRoot);
        // Setup event handlers
        this.setupEventHandlers();
    }
    initializeComponents(workspaceRoot) {
        const auditLogPath = path.join(workspaceRoot, '.prophecy-sandbox', 'audit.log');
        // Initialize access control
        this.accessControl = new AccessControlSystem_1.AccessControlSystem({
            ...this.config.accessControl,
            auditLogPath
        });
        // Initialize constructor
        this.constructor = new MaliciousCodeConstructor_1.MaliciousCodeConstructor();
        // Initialize sandbox environment
        this.sandbox = new SandboxEnvironment_1.SandboxEnvironment(this.config.sandbox);
        // Initialize analyzer
        this.analyzer = new ThreatAnalyzer_1.ThreatAnalyzer(this.config.analysis);
        // Initialize learning system
        const learningDataPath = path.join(workspaceRoot, '.prophecy-sandbox', 'learning-data.json');
        this.learningSystem = new SelfLearningSystem_1.SelfLearningSystem({
            ...this.config.learning,
            modelPersistencePath: learningDataPath
        });
        // Initialize dashboard
        this.dashboard = new WebDashboard_1.WebDashboard(this.config.dashboard, this.accessControl);
        // Initialize CLI
        this.cli = new CLIInterface_1.CLIInterface(this.accessControl, this.constructor, this.sandbox, this.analyzer, this.learningSystem, this.config.cli);
    }
    setupEventHandlers() {
        // Sandbox events
        this.sandbox.on('executionStarted', this.handleExecutionStarted.bind(this));
        this.sandbox.on('executionCompleted', this.handleExecutionCompleted.bind(this));
        this.sandbox.on('executionTerminated', this.handleExecutionTerminated.bind(this));
        // Access control events
        this.accessControl.on('razdorAuthenticated', this.handleRazdorAuthenticated.bind(this));
        this.accessControl.on('accessDenied', this.handleAccessDenied.bind(this));
        this.accessControl.on('securityViolation', this.handleSecurityViolation.bind(this));
        // Learning system events
        this.learningSystem.on('modelUpdated', this.handleModelUpdated.bind(this));
        // Dashboard events
        this.dashboard.on('alert', this.handleDashboardAlert.bind(this));
    }
    async initialize() {
        try {
            console.log('Initializing Prophecy Sandbox...');
            // Check if enabled
            if (!this.config.enabled) {
                console.log('Prophecy Sandbox is disabled');
                return false;
            }
            // Initialize security manager
            const securityInitialized = await this.securityManager.initialize();
            if (!securityInitialized) {
                console.error('Security manager initialization failed');
                return false;
            }
            // Initialize sandbox environment
            await this.sandbox.initialize();
            // Start dashboard if configured
            if (this.config.dashboard.port > 0) {
                await this.dashboard.start();
            }
            // Log initialization
            await this.logProphecyAction('SANDBOX_STARTED', {
                workspaceRoot: this.securityManager['workspaceRoot'],
                config: this.config
            });
            this.isInitialized = true;
            this.isRunning = true;
            console.log('Prophecy Sandbox initialized successfully');
            this.emit('initialized');
            return true;
        }
        catch (error) {
            console.error('Failed to initialize Prophecy Sandbox:', error);
            await this.logProphecyAction('SANDBOX_INITIALIZATION_FAILED', {
                error: error.message
            });
            return false;
        }
    }
    async generateSample(templateId, generationConfig, userId) {
        this.ensureInitialized();
        // Check permissions
        const hasPermission = await this.accessControl.checkPermission(userId, 'samples', 'generate');
        if (!hasPermission) {
            throw new Error('Insufficient permissions to generate samples');
        }
        // Generate sample
        const sample = await this.constructor.generateSample(templateId, generationConfig);
        // Log action
        await this.logProphecyAction('SAMPLE_GENERATED', {
            sampleId: sample.id,
            templateId,
            userId,
            threatLevel: sample.metadata.threatLevel
        });
        // Update dashboard
        this.dashboard.updateSample(sample);
        return sample;
    }
    async executeSample(sample, userId) {
        this.ensureInitialized();
        // Check permissions
        const hasPermission = await this.accessControl.checkPermission(userId, 'samples', 'execute');
        if (!hasPermission) {
            throw new Error('Insufficient permissions to execute samples');
        }
        // Execute sample
        const execution = await this.sandbox.executeSample(sample);
        // Analyze execution
        const analysis = await this.analyzer.analyzeExecution(execution);
        execution.analysisResults = analysis;
        // Process with learning system
        await this.learningSystem.processExecution(execution, analysis);
        // Log action
        await this.logProphecyAction('SANDBOX_COMPLETED', {
            executionId: execution.id,
            sampleId: sample.id,
            userId,
            riskScore: analysis.riskScore,
            techniquesCount: analysis.techniques.length
        });
        // Update dashboard
        this.dashboard.updateExecution(execution);
        return execution;
    }
    async getExecution(executionId, userId) {
        this.ensureInitialized();
        // Check permissions
        const hasPermission = await this.accessControl.checkPermission(userId, 'executions', 'read');
        if (!hasPermission) {
            throw new Error('Insufficient permissions to read executions');
        }
        return this.sandbox.getExecution(executionId);
    }
    async getMetrics(userId) {
        this.ensureInitialized();
        // Check permissions
        const hasPermission = await this.accessControl.checkPermission(userId, 'metrics', 'read');
        if (!hasPermission) {
            throw new Error('Insufficient permissions to read metrics');
        }
        return this.learningSystem.getMetrics();
    }
    async runCLI(argv) {
        this.ensureInitialized();
        await this.cli.run(argv);
    }
    ensureInitialized() {
        if (!this.isInitialized) {
            throw new Error('Prophecy Sandbox is not initialized');
        }
    }
    async logProphecyAction(action, metadata) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            action: action,
            analysisType: 'combined',
            metadata: {
                workspaceRoot: this.securityManager['workspaceRoot'],
                userAgent: 'prophecy-sandbox',
                version: '1.0.0',
                ...metadata
            }
        };
        await this.auditLogger.logEntry(logEntry);
    }
    // Event handlers
    async handleExecutionStarted(execution) {
        await this.logProphecyAction('SANDBOX_STARTED', {
            executionId: execution.id,
            sampleId: execution.sampleId
        });
    }
    async handleExecutionCompleted(execution) {
        await this.logProphecyAction('SANDBOX_COMPLETED', {
            executionId: execution.id,
            sampleId: execution.sampleId,
            riskScore: execution.analysisResults.riskScore
        });
    }
    async handleExecutionTerminated(execution) {
        await this.logProphecyAction('SANDBOX_COMPLETED', {
            executionId: execution.id,
            sampleId: execution.sampleId,
            terminated: true
        });
    }
    async handleRazdorAuthenticated(token) {
        await this.logProphecyAction('UNAUTHORIZED_ACCESS', {
            userId: token.userId,
            authenticated: true,
            role: token.role
        });
    }
    async handleAccessDenied(attempt) {
        await this.logProphecyAction('UNAUTHORIZED_ACCESS', {
            userId: attempt.userId,
            action: attempt.action,
            resource: attempt.resource,
            reason: attempt.reason
        });
    }
    async handleSecurityViolation(violation) {
        await this.logProphecyAction('DATA_EXPORT_ATTEMPT', {
            violationType: violation.type,
            message: violation.message,
            userId: violation.context.userId
        });
        // Create security alert
        this.dashboard.addAlert({
            timestamp: violation.timestamp,
            severity: 'critical',
            title: 'Security Violation Detected',
            message: violation.message,
            acknowledged: false
        });
    }
    async handleModelUpdated(data) {
        await this.logProphecyAction('MODEL_UPDATED', {
            modelType: data.type,
            version: data.version
        });
        // Update dashboard metrics
        const metrics = this.learningSystem.getMetrics();
        this.dashboard.updateMetrics(metrics);
    }
    handleDashboardAlert(alert) {
        this.emit('alert', alert);
    }
    // Integration with Cascade SWE-1.5
    async integrateWithCascade() {
        if (!this.config.integration.cascadeHooks) {
            return;
        }
        // Setup Cascade hooks integration
        this.setupCascadeHooks();
        // Setup native image understanding integration
        if (this.config.integration.nativeImageUnderstanding) {
            this.setupNativeImageUnderstanding();
        }
        // Setup Fast Context integration
        if (this.config.integration.fastContext) {
            this.setupFastContext();
        }
        // Setup RBAC integration
        if (this.config.integration.rbac) {
            this.setupRBAC();
        }
        // Setup Codemaps integration
        if (this.config.integration.codemaps) {
            this.setupCodemaps();
        }
    }
    setupCascadeHooks() {
        // Hook into Cascade's logging and policy systems
        console.log('Setting up Cascade Hooks integration...');
    }
    setupNativeImageUnderstanding() {
        // Integrate with Cascade's native image understanding for visual attack analysis
        console.log('Setting up Native Image Understanding integration...');
    }
    setupFastContext() {
        // Integrate with Cascade's Fast Context for rapid analysis
        console.log('Setting up Fast Context integration...');
    }
    setupRBAC() {
        // Integrate with Cascade's RBAC system
        console.log('Setting up RBAC integration...');
    }
    setupCodemaps() {
        // Integrate with Cascade's Codemaps for attack graph visualization
        console.log('Setting up Codemaps integration...');
    }
    async shutdown() {
        if (!this.isRunning) {
            return;
        }
        console.log('Shutting down Prophecy Sandbox...');
        try {
            // Stop dashboard
            await this.dashboard.stop();
            // Shutdown sandbox
            await this.sandbox.shutdown();
            // Shutdown access control
            await this.accessControl.shutdown();
            // Shutdown security manager
            await this.securityManager.shutdown();
            // Log shutdown
            await this.logProphecyAction('SANDBOX_COMPLETED', {
                shutdown: true
            });
            this.isRunning = false;
            console.log('Prophecy Sandbox shutdown completed');
        }
        catch (error) {
            console.error('Error during shutdown:', error);
        }
    }
    getAccessControl() {
        return this.accessControl;
    }
    getDashboard() {
        return this.dashboard;
    }
    getConfig() {
        return { ...this.config };
    }
    isReady() {
        return this.isInitialized && this.isRunning;
    }
}
exports.ProphecySandbox = ProphecySandbox;
//# sourceMappingURL=ProphecySandbox.js.map