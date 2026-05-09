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
exports.WebDashboard = void 0;
const events_1 = require("events");
const express = __importStar(require("express"));
const socketio = __importStar(require("socket.io"));
const path = __importStar(require("path"));
class WebDashboard extends events_1.EventEmitter {
    constructor(config, accessControl) {
        super();
        this.config = config;
        this.accessControl = accessControl;
        this.app = express();
        this.setupExpress();
        this.initializeData();
    }
    setupExpress() {
        // Middleware
        this.app.use(express.json());
        this.app.use(express.static(path.join(__dirname, 'public')));
        // Authentication middleware
        this.app.use('/api', this.authenticateMiddleware.bind(this));
        // Setup routes
        this.setupRoutes();
    }
    async authenticateMiddleware(req, res, next) {
        const token = req.headers.authorization?.replace('Bearer ', '');
        if (!token) {
            res.status(401).json({ error: 'No token provided' });
            return;
        }
        const session = await this.accessControl.validateToken(token);
        if (!session) {
            res.status(401).json({ error: 'Invalid token' });
            return;
        }
        // Add user info to request
        req.user = session;
        next();
    }
    setupRoutes() {
        // API Routes
        this.app.get('/api/status', this.getStatus.bind(this));
        this.app.get('/api/executions', this.getExecutions.bind(this));
        this.app.get('/api/executions/:id', this.getExecution.bind(this));
        this.app.get('/api/samples', this.getSamples.bind(this));
        this.app.get('/api/analytics', this.getAnalytics.bind(this));
        this.app.get('/api/alerts', this.getAlerts.bind(this));
        this.app.post('/api/alerts/:id/acknowledge', this.acknowledgeAlert.bind(this));
        this.app.get('/api/metrics', this.getMetrics.bind(this));
        // Dashboard route
        this.app.get('/', this.serveDashboard.bind(this));
        // Error handling
        this.app.use((err, req, res, next) => {
            console.error('Dashboard error:', err);
            res.status(500).json({ error: 'Internal server error' });
        });
    }
    async serveDashboard(req, res) {
        res.sendFile(path.join(__dirname, 'public', 'index.html'));
    }
    async getStatus(req, res) {
        res.json(this.dashboardData.systemStatus);
    }
    async getExecutions(req, res) {
        const limit = parseInt(req.query.limit) || 50;
        const executions = this.dashboardData.activeExecutions.slice(-limit);
        res.json(executions);
    }
    async getExecution(req, res) {
        const executionId = req.params.id;
        const execution = this.dashboardData.activeExecutions.find(e => e.id === executionId);
        if (!execution) {
            res.status(404).json({ error: 'Execution not found' });
            return;
        }
        res.json(execution);
    }
    async getSamples(req, res) {
        const limit = parseInt(req.query.limit) || 100;
        const samples = this.dashboardData.recentSamples.slice(-limit);
        res.json(samples);
    }
    async getAnalytics(req, res) {
        const timeframe = req.query.timeframe || '24h';
        const trends = this.getThreatTrends(timeframe);
        res.json(trends);
    }
    async getAlerts(req, res) {
        const unacknowledgedOnly = req.query.unacknowledged === 'true';
        let alerts = this.dashboardData.alerts;
        if (unacknowledgedOnly) {
            alerts = alerts.filter(alert => !alert.acknowledged);
        }
        res.json(alerts);
    }
    async acknowledgeAlert(req, res) {
        const alertId = req.params.id;
        const alert = this.dashboardData.alerts.find(a => a.id === alertId);
        if (!alert) {
            res.status(404).json({ error: 'Alert not found' });
            return;
        }
        alert.acknowledged = true;
        res.json({ success: true });
    }
    async getMetrics(req, res) {
        res.json(this.dashboardData.learningMetrics);
    }
    getThreatTrends(timeframe) {
        // Generate threat trends based on timeframe
        const now = new Date();
        const timeframes = {
            '1h': 60 * 60 * 1000,
            '24h': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000,
            '30d': 30 * 24 * 60 * 60 * 1000
        };
        const duration = timeframes[timeframe] || timeframes['24h'];
        const startTime = new Date(now.getTime() - duration);
        // Generate sample trend data
        const trends = [];
        const interval = duration / 24; // 24 data points
        for (let i = 0; i < 24; i++) {
            const timestamp = new Date(startTime.getTime() + (i * interval));
            trends.push({
                timestamp: timestamp.toISOString(),
                riskScore: Math.random() * 100,
                techniqueCount: Math.floor(Math.random() * 10),
                anomalyCount: Math.floor(Math.random() * 5)
            });
        }
        return trends;
    }
    initializeData() {
        this.dashboardData = {
            activeExecutions: [],
            recentSamples: [],
            threatTrends: [],
            learningMetrics: {
                totalSamplesAnalyzed: 0,
                successfulDetections: 0,
                falsePositives: 0,
                falseNegatives: 0,
                averageRiskScore: 0,
                techniqueEvolutionCount: 0,
                signatureEvolutionCount: 0,
                lastUpdateTime: new Date().toISOString()
            },
            systemStatus: {
                sandboxRunning: false,
                activeExecutions: 0,
                totalSamples: 0,
                learningActive: false,
                lastUpdate: new Date().toISOString()
            },
            alerts: []
        };
    }
    async start() {
        return new Promise((resolve, reject) => {
            this.server = this.app.listen(this.config.port, this.config.host, () => {
                console.log(`Prophecy Sandbox Dashboard started on http://${this.config.host}:${this.config.port}`);
                // Setup Socket.IO for real-time updates
                this.setupSocketIO();
                // Start periodic updates
                if (this.config.enableRealTimeUpdates) {
                    this.startPeriodicUpdates();
                }
                resolve();
            });
            this.server.on('error', reject);
        });
    }
    setupSocketIO() {
        this.io = new socketio.Server(this.server, {
            cors: { origin: "*", methods: ["GET", "POST"] }
        });
        this.io.on('connection', (socket) => {
            console.log('Dashboard client connected');
            // Send initial data
            socket.emit('dashboard-update', this.dashboardData);
            socket.on('disconnect', () => {
                console.log('Dashboard client disconnected');
            });
        });
    }
    startPeriodicUpdates() {
        this.updateTimer = setInterval(() => {
            this.updateDashboardData();
            this.io.emit('dashboard-update', this.dashboardData);
        }, this.config.refreshInterval);
    }
    updateDashboardData() {
        // Update system status
        this.dashboardData.systemStatus.lastUpdate = new Date().toISOString();
        this.dashboardData.systemStatus.activeExecutions = this.dashboardData.activeExecutions.length;
        this.dashboardData.systemStatus.totalSamples = this.dashboardData.recentSamples.length;
        // Clean up old data
        this.cleanupOldData();
    }
    cleanupOldData() {
        // Keep only recent items
        if (this.dashboardData.activeExecutions.length > this.config.maxHistoryItems) {
            this.dashboardData.activeExecutions = this.dashboardData.activeExecutions.slice(-this.config.maxHistoryItems);
        }
        if (this.dashboardData.recentSamples.length > this.config.maxHistoryItems) {
            this.dashboardData.recentSamples = this.dashboardData.recentSamples.slice(-this.config.maxHistoryItems);
        }
        if (this.dashboardData.alerts.length > 100) {
            this.dashboardData.alerts = this.dashboardData.alerts.slice(-100);
        }
    }
    // Public methods for updating dashboard data
    updateExecution(execution) {
        const existingIndex = this.dashboardData.activeExecutions.findIndex(e => e.id === execution.id);
        if (existingIndex >= 0) {
            this.dashboardData.activeExecutions[existingIndex] = execution;
        }
        else {
            this.dashboardData.activeExecutions.push(execution);
        }
        // Emit real-time update
        if (this.io) {
            this.io.emit('execution-update', execution);
        }
        // Check for alerts
        this.checkForAlerts(execution);
    }
    updateSample(sample) {
        const existingIndex = this.dashboardData.recentSamples.findIndex(s => s.id === sample.id);
        if (existingIndex >= 0) {
            this.dashboardData.recentSamples[existingIndex] = sample;
        }
        else {
            this.dashboardData.recentSamples.push(sample);
        }
        // Emit real-time update
        if (this.io) {
            this.io.emit('sample-update', sample);
        }
    }
    updateMetrics(metrics) {
        this.dashboardData.learningMetrics = metrics;
        // Emit real-time update
        if (this.io) {
            this.io.emit('metrics-update', metrics);
        }
    }
    addAlert(alert) {
        const fullAlert = {
            ...alert,
            id: require('crypto').randomUUID()
        };
        this.dashboardData.alerts.unshift(fullAlert);
        // Emit real-time update
        if (this.io) {
            this.io.emit('alert', fullAlert);
        }
    }
    checkForAlerts(execution) {
        // High risk score alert
        if (execution.analysisResults.riskScore >= 80) {
            this.addAlert({
                timestamp: new Date().toISOString(),
                severity: 'critical',
                title: 'High Risk Sample Detected',
                message: `Sample ${execution.sampleId} has risk score ${execution.analysisResults.riskScore}`,
                acknowledged: false
            });
        }
        // Execution failure alert
        if (execution.status === 'failed') {
            this.addAlert({
                timestamp: new Date().toISOString(),
                severity: 'medium',
                title: 'Sample Execution Failed',
                message: `Execution ${execution.id} failed to complete`,
                acknowledged: false
            });
        }
        // Anomaly alert
        if (execution.analysisResults.anomalies.length > 5) {
            this.addAlert({
                timestamp: new Date().toISOString(),
                severity: 'high',
                title: 'Multiple Anomalies Detected',
                message: `Sample ${execution.sampleId} exhibits ${execution.analysisResults.anomalies.length} anomalous behaviors`,
                acknowledged: false
            });
        }
    }
    async stop() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        if (this.io) {
            this.io.close();
        }
        if (this.server) {
            return new Promise((resolve) => {
                this.server.close(resolve);
            });
        }
    }
    getDashboardData() {
        return { ...this.dashboardData };
    }
}
exports.WebDashboard = WebDashboard;
//# sourceMappingURL=WebDashboard.js.map