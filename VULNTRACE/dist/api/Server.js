"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.APIServer = void 0;
const express_1 = __importDefault(require("express"));
const http_1 = require("http");
const socket_io_1 = require("socket.io");
const SQLVulnerabilityScanner_1 = require("../core/SQLVulnerabilityScanner");
const SQLParser_1 = require("../parser/SQLParser");
const types_1 = require("../types");
const ConfigManager_1 = require("../config/ConfigManager");
const SecurityManager_1 = require("../security/SecurityManager");
class APIServer {
    constructor(port = 3000, workspaceRoot = process.cwd()) {
        this.port = port;
        this.workspaceRoot = workspaceRoot;
        this.app = (0, express_1.default)();
        this.httpServer = (0, http_1.createServer)(this.app);
        this.io = new socket_io_1.Server(this.httpServer, {
            cors: {
                origin: '*',
                methods: ['GET', 'POST']
            }
        });
        this.configManager = new ConfigManager_1.ConfigManager();
        const securityConfig = {
            readonly: true,
            requireConfirmation: true,
            enableAuditLogging: true,
            trustedWorkspaces: [workspaceRoot],
            blockExternalRequests: true,
            offlineMode: true,
            ethicalWarningAccepted: false
        };
        this.securityManager = new SecurityManager_1.SecurityManager(workspaceRoot, securityConfig);
        this.scanner = new SQLVulnerabilityScanner_1.SQLVulnerabilityScanner(this.configManager.getConfig(), workspaceRoot);
        this.sqlParser = new SQLParser_1.SQLParser(this.configManager.getConfig());
        this.setupMiddleware();
        this.setupRoutes();
        this.setupWebSocket();
        this.setupErrorHandling();
    }
    setupMiddleware() {
        this.app.use(express_1.default.json({ limit: '10mb' }));
        this.app.use(express_1.default.urlencoded({ extended: true }));
        this.app.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
            next();
        });
    }
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                security: this.scanner.getSecurityStatus()
            });
        });
        // Analyze single file
        this.app.post('/api/analyze/file', async (req, res) => {
            try {
                const { filePath, content, database } = req.body;
                if (!filePath || !content) {
                    return res.status(400).json({ error: 'filePath and content are required' });
                }
                const context = {
                    filePath,
                    content,
                    database: database || types_1.DatabaseType.GENERIC
                };
                const result = await this.scanner.analyze(context);
                res.json(result);
            }
            catch (error) {
                res.status(500).json({
                    error: 'Analysis failed',
                    message: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Analyze multiple files
        this.app.post('/api/analyze/batch', async (req, res) => {
            try {
                const { files } = req.body;
                if (!files || !Array.isArray(files)) {
                    return res.status(400).json({ error: 'files array is required' });
                }
                const results = await this.scanner.analyzeMultipleFiles(files);
                res.json({ results, total: results.length });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Batch analysis failed',
                    message: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Generate report
        this.app.post('/api/report/generate', async (req, res) => {
            try {
                const { result, format } = req.body;
                if (!result) {
                    return res.status(400).json({ error: 'result is required' });
                }
                const report = await this.scanner.generateReport(result, format || 'json');
                res.type(format === 'html' ? 'text/html' : 'application/json');
                res.send(report);
            }
            catch (error) {
                res.status(500).json({
                    error: 'Report generation failed',
                    message: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Get configuration
        this.app.get('/api/config', (req, res) => {
            res.json(this.scanner.getConfig());
        });
        // Update configuration
        this.app.put('/api/config', (req, res) => {
            try {
                const updates = req.body;
                this.scanner.updateConfig(updates);
                res.json({ success: true, config: this.scanner.getConfig() });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Configuration update failed',
                    message: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Get security status
        this.app.get('/api/security/status', (req, res) => {
            res.json(this.scanner.getSecurityStatus());
        });
        // Get ethical guidelines
        this.app.get('/api/security/guidelines', (req, res) => {
            res.json({ guidelines: this.scanner.getEthicalGuidelines() });
        });
        // Accept ethical warning
        this.app.post('/api/security/accept-warning', async (req, res) => {
            try {
                this.scanner.updateSecurityConfig({ ethicalWarningAccepted: true });
                res.json({ success: true });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to accept ethical warning',
                    message: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Get supported databases
        this.app.get('/api/databases', (req, res) => {
            res.json({
                databases: ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite', 'generic']
            });
        });
        // Validate SQL syntax
        this.app.post('/api/validate', async (req, res) => {
            try {
                const { sql, database } = req.body;
                if (!sql) {
                    return res.status(400).json({ error: 'sql is required' });
                }
                const dbType = database || types_1.DatabaseType.GENERIC;
                const isValid = this.sqlParser.validateSQL(sql, dbType);
                // Additional parsing to get more details
                let parseError = null;
                let ast = null;
                try {
                    const context = {
                        filePath: 'validation.sql',
                        content: sql,
                        database: dbType
                    };
                    const queries = await this.sqlParser.parseQueries(context);
                    ast = queries.length > 0 ? queries[0].ast : null;
                }
                catch (parseErr) {
                    parseError = parseErr instanceof Error ? parseErr.message : 'Parse error';
                }
                res.json({
                    valid: isValid && !parseError,
                    database: dbType,
                    message: parseError || 'SQL validation completed successfully',
                    ast: ast ? 'AST generated successfully' : null,
                    parseError
                });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Validation failed',
                    message: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
    }
    setupWebSocket() {
        this.io.on('connection', (socket) => {
            console.log(`Client connected: ${socket.id}`);
            // Initialize scanner when client connects
            socket.on('initialize', async () => {
                try {
                    await this.scanner.initialize();
                    socket.emit('initialized', {
                        success: true,
                        security: this.scanner.getSecurityStatus()
                    });
                }
                catch (error) {
                    socket.emit('error', {
                        message: error instanceof Error ? error.message : 'Initialization failed'
                    });
                }
            });
            // Real-time analysis
            socket.on('analyze', async (data) => {
                try {
                    const context = {
                        filePath: data.filePath,
                        content: data.content,
                        database: data.database || types_1.DatabaseType.GENERIC
                    };
                    const result = await this.scanner.analyze(context);
                    socket.emit('analysis-complete', result);
                }
                catch (error) {
                    socket.emit('analysis-error', {
                        message: error instanceof Error ? error.message : 'Analysis failed'
                    });
                }
            });
            // Incremental analysis (for real-time editing)
            socket.on('analyze-incremental', async (data) => {
                try {
                    const context = {
                        filePath: data.filePath,
                        content: data.content,
                        database: data.database || types_1.DatabaseType.GENERIC
                    };
                    // Analyze only the changed line/context
                    const result = await this.scanner.analyze(context);
                    // Filter vulnerabilities to only those near the changed line
                    const nearbyVulnerabilities = result.vulnerabilities.filter(v => Math.abs(v.line - data.line) <= 5);
                    socket.emit('incremental-result', {
                        vulnerabilities: nearbyVulnerabilities,
                        line: data.line
                    });
                }
                catch (error) {
                    socket.emit('incremental-error', {
                        message: error instanceof Error ? error.message : 'Incremental analysis failed'
                    });
                }
            });
            // Get vulnerability details
            socket.on('get-vulnerability-details', (data) => {
                // Fetch detailed information about a specific vulnerability
                // In a real implementation, this would store vulnerability details or fetch from cache
                const vulnerabilityDetails = {
                    id: data.vulnerabilityId,
                    title: 'SQL Vulnerability',
                    description: 'Detailed analysis of the SQL vulnerability',
                    severity: 'HIGH',
                    recommendation: 'Use parameterized queries',
                    exploitExample: 'SELECT * FROM users WHERE id = 1 OR 1=1',
                    fixExample: 'SELECT * FROM users WHERE id = ?',
                    references: [
                        'CWE-89: SQL Injection',
                        'OWASP A03:2021 - Injection',
                        'https://owasp.org/www-community/attacks/SQL_Injection'
                    ],
                    additionalContext: 'This vulnerability occurs when user input is directly concatenated into SQL queries without proper sanitization.'
                };
                socket.emit('vulnerability-details', vulnerabilityDetails);
            });
            // Ignore vulnerability
            socket.on('ignore-vulnerability', (data) => {
                this.scanner.updateConfig({
                    ignoredRules: [...this.scanner.getConfig().ignoredRules, data.vulnerabilityId]
                });
                socket.emit('vulnerability-ignored', { id: data.vulnerabilityId });
            });
            // Get configuration
            socket.on('get-config', () => {
                socket.emit('config', this.scanner.getConfig());
            });
            // Update configuration
            socket.on('update-config', (data) => {
                this.scanner.updateConfig(data);
                socket.emit('config-updated', this.scanner.getConfig());
            });
            // Disconnect handler
            socket.on('disconnect', () => {
                console.log(`Client disconnected: ${socket.id}`);
            });
        });
    }
    setupErrorHandling() {
        this.app.use((err, req, res, next) => {
            console.error('API Error:', err);
            res.status(500).json({
                error: 'Internal server error',
                message: err.message
            });
        });
    }
    start() {
        return new Promise((resolve) => {
            this.httpServer.listen(this.port, () => {
                console.log(`SQL Vulnerability Scanner API server running on port ${this.port}`);
                console.log(`WebSocket server ready for connections`);
                resolve();
            });
        });
    }
    stop() {
        return new Promise((resolve) => {
            this.httpServer.close(() => {
                console.log('API server stopped');
                this.io.close();
                resolve();
            });
        });
    }
    getScanner() {
        return this.scanner;
    }
    getIO() {
        return this.io;
    }
}
exports.APIServer = APIServer;
//# sourceMappingURL=Server.js.map