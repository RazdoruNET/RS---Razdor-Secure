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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CLIInterface = void 0;
const commander_1 = require("commander");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const chalk = __importStar(require("chalk"));
const cli_table3_1 = __importDefault(require("cli-table3"));
class CLIInterface {
    constructor(accessControl, codeConstructor, sandbox, analyzer, learningSystem, config) {
        this.accessControl = accessControl;
        this.codeConstructor = codeConstructor;
        this.sandbox = sandbox;
        this.analyzer = analyzer;
        this.learningSystem = learningSystem;
        this.config = config;
        this.setupCommands();
    }
    setupCommands() {
        this.program = new commander_1.Command();
        this.program
            .name('prophecy-sandbox')
            .description('Prophecy Sandbox CLI - Threat prediction and analysis system')
            .version('1.0.0');
        // Authentication commands
        this.program
            .command('auth')
            .description('Authentication commands')
            .addCommand(this.createAuthChallengeCommand())
            .addCommand(this.createAuthLoginCommand());
        // Sample generation commands
        this.program
            .command('generate')
            .description('Generate malicious samples')
            .addCommand(this.createGenerateSampleCommand())
            .addCommand(this.createListTemplatesCommand());
        // Sandbox execution commands
        this.program
            .command('execute')
            .description('Execute samples in sandbox')
            .addCommand(this.createExecuteSampleCommand())
            .addCommand(this.createListExecutionsCommand())
            .addCommand(this.createGetExecutionCommand());
        // Analysis commands
        this.program
            .command('analyze')
            .description('Analyze threats and results')
            .addCommand(this.createAnalyzeExecutionCommand())
            .addCommand(this.createListTechniquesCommand())
            .addCommand(this.createListSignaturesCommand());
        // Learning commands
        this.program
            .command('learning')
            .description('Self-learning system commands')
            .addCommand(this.createGetMetricsCommand())
            .addCommand(this.createGetInsightsCommand())
            .addCommand(this.createResetLearningCommand());
        // System commands
        this.program
            .command('system')
            .description('System management commands')
            .addCommand(this.createStatusCommand())
            .addCommand(this.createInitCommand())
            .addCommand(this.createShutdownCommand());
        // Configuration
        this.program
            .option('-f, --format <format>', 'Output format (json|table|csv)', this.config.outputFormat)
            .option('-v, --verbose', 'Verbose output', this.config.verbose)
            .option('-c, --config <path>', 'Configuration file path', this.config.configPath);
    }
    createAuthChallengeCommand() {
        return new commander_1.Command('challenge')
            .description('Generate authentication challenge')
            .action(async () => {
            try {
                const challenge = this.accessControl.generateChallenge();
                console.log(chalk.green('Authentication Challenge:'));
                console.log(challenge);
                console.log(chalk.yellow('Sign this challenge with your RAZDOR private key and use "auth login"'));
            }
            catch (error) {
                console.error(chalk.red('Error generating challenge:'), error.message);
                process.exit(1);
            }
        });
    }
    createAuthLoginCommand() {
        return new commander_1.Command('login')
            .description('Authenticate with RAZDOR signature')
            .requiredOption('-s, --signature <signature>', 'RAZDOR signature of challenge')
            .requiredOption('-c, --challenge <challenge>', 'Authentication challenge')
            .action(async (options) => {
            try {
                const token = await this.accessControl.authenticateRazdor(options.signature, options.challenge);
                if (this.config.outputFormat === 'json') {
                    console.log(JSON.stringify(token, null, 2));
                }
                else {
                    console.log(chalk.green('Authentication successful!'));
                    console.log('Token:', token.token);
                    console.log('Expires:', token.expiresAt);
                    if (this.config.autoSave) {
                        this.saveToken(token.token);
                        console.log(chalk.blue('Token saved to ~/.prophecy-sandbox-token'));
                    }
                }
            }
            catch (error) {
                console.error(chalk.red('Authentication failed:'), error.message);
                process.exit(1);
            }
        });
    }
    createGenerateSampleCommand() {
        return new commander_1.Command('sample')
            .description('Generate a malicious sample')
            .requiredOption('-t, --template <templateId>', 'Template ID')
            .option('-l, --threat-level <level>', 'Threat level (low|medium|high|critical)', 'medium')
            .option('-e, --evasion', 'Include evasion techniques')
            .option('-m, --mutation-rate <rate>', 'Mutation rate (0.0-1.0)', '0.1')
            .option('-o, --output <file>', 'Output file path')
            .action(async (options) => {
            try {
                await this.ensureAuthenticated();
                const config = {
                    targetThreatLevel: options.threatLevel,
                    includeEvasion: options.evasion,
                    mutationRate: parseFloat(options.mutationRate),
                    maxComplexity: 5,
                    allowedTechniques: []
                };
                const sample = await this.constructor.generateSample(options.template, config);
                if (options.output) {
                    await fs.promises.writeFile(options.output, sample.code);
                    console.log(chalk.green(`Sample saved to ${options.output}`));
                }
                this.outputSample(sample);
            }
            catch (error) {
                console.error(chalk.red('Error generating sample:'), error.message);
                process.exit(1);
            }
        });
    }
    createListTemplatesCommand() {
        return new commander_1.Command('templates')
            .description('List available templates')
            .action(async () => {
            try {
                await this.ensureAuthenticated();
                const templates = this.constructor.getAvailableTemplates();
                if (this.config.outputFormat === 'json') {
                    console.log(JSON.stringify(templates, null, 2));
                }
                else {
                    const table = new cli_table3_1.default({
                        head: ['ID', 'Name', 'Type', 'Language', 'Evasion Techniques'],
                        colWidths: [20, 25, 15, 15, 25]
                    });
                    templates.forEach(template => {
                        table.push([
                            template.id,
                            template.name,
                            template.type,
                            template.language,
                            template.evasionTechniques.length.toString()
                        ]);
                    });
                    console.log(chalk.blue('Available Templates:'));
                    console.log(table.toString());
                }
            }
            catch (error) {
                console.error(chalk.red('Error listing templates:'), error.message);
                process.exit(1);
            }
        });
    }
    createExecuteSampleCommand() {
        return new commander_1.Command('sample')
            .description('Execute a sample in the sandbox')
            .requiredOption('-s, --sample <sampleId>', 'Sample ID or file path')
            .option('-t, --timeout <seconds>', 'Execution timeout', '30')
            .action(async (options) => {
            try {
                await this.ensureAuthenticated();
                let sample;
                if (fs.existsSync(options.sample)) {
                    // Load from file
                    const code = await fs.promises.readFile(options.sample, 'utf8');
                    sample = {
                        id: path.basename(options.sample),
                        name: path.basename(options.sample),
                        type: 'backdoor',
                        language: 'python',
                        code,
                        metadata: {
                            generatedAt: new Date().toISOString(),
                            generationMethod: 'file-import',
                            mutations: 0,
                            threatLevel: 'medium'
                        }
                    };
                }
                else {
                    // Load by ID (would need to be stored somewhere)
                    throw new Error('Sample ID not found. Use file path instead.');
                }
                console.log(chalk.yellow('Executing sample in sandbox...'));
                const execution = await this.sandbox.executeSample(sample);
                this.outputExecution(execution);
            }
            catch (error) {
                console.error(chalk.red('Error executing sample:'), error.message);
                process.exit(1);
            }
        });
    }
    createListExecutionsCommand() {
        return new commander_1.Command('list')
            .description('List recent executions')
            .option('-l, --limit <limit>', 'Number of executions to show', '10')
            .action(async (options) => {
            try {
                await this.ensureAuthenticated();
                const executions = this.sandbox.getActiveExecutions()
                    .slice(-parseInt(options.limit));
                if (this.config.outputFormat === 'json') {
                    console.log(JSON.stringify(executions, null, 2));
                }
                else {
                    const table = new cli_table3_1.default({
                        head: ['ID', 'Sample ID', 'Status', 'Start Time', 'Risk Score'],
                        colWidths: [20, 20, 15, 20, 10]
                    });
                    executions.forEach(execution => {
                        table.push([
                            execution.id,
                            execution.sampleId,
                            execution.status,
                            new Date(execution.startTime).toLocaleString(),
                            execution.analysisResults.riskScore.toString()
                        ]);
                    });
                    console.log(chalk.blue('Recent Executions:'));
                    console.log(table.toString());
                }
            }
            catch (error) {
                console.error(chalk.red('Error listing executions:'), error.message);
                process.exit(1);
            }
        });
    }
    createGetExecutionCommand() {
        return new commander_1.Command('get')
            .description('Get execution details')
            .requiredOption('-i, --id <executionId>', 'Execution ID')
            .action(async (options) => {
            try {
                await this.ensureAuthenticated();
                const execution = this.sandbox.getExecution(options.id);
                if (!execution) {
                    console.error(chalk.red('Execution not found'));
                    process.exit(1);
                }
                this.outputExecution(execution, true);
            }
            catch (error) {
                console.error(chalk.red('Error getting execution:'), error.message);
                process.exit(1);
            }
        });
    }
    createAnalyzeExecutionCommand() {
        return new commander_1.Command('execution')
            .description('Analyze execution results')
            .requiredOption('-i, --id <executionId>', 'Execution ID')
            .action(async (options) => {
            try {
                await this.ensureAuthenticated();
                const execution = this.sandbox.getExecution(options.id);
                if (!execution) {
                    console.error(chalk.red('Execution not found'));
                    process.exit(1);
                }
                const analysis = await this.analyzer.analyzeExecution(execution);
                this.outputAnalysis(analysis);
            }
            catch (error) {
                console.error(chalk.red('Error analyzing execution:'), error.message);
                process.exit(1);
            }
        });
    }
    createListTechniquesCommand() {
        return new commander_1.Command('techniques')
            .description('List known attack techniques')
            .action(async () => {
            try {
                await this.ensureAuthenticated();
                const techniques = this.analyzer.getTechniqueDatabase();
                if (this.config.outputFormat === 'json') {
                    console.log(JSON.stringify(techniques, null, 2));
                }
                else {
                    const table = new cli_table3_1.default({
                        head: ['ID', 'Name', 'Category', 'Patterns'],
                        colWidths: [20, 25, 20, 35]
                    });
                    techniques.forEach(technique => {
                        const totalPatterns = technique.syscallPatterns.length +
                            technique.networkPatterns.length +
                            technique.filePatterns.length;
                        table.push([
                            technique.id,
                            technique.name,
                            technique.category,
                            totalPatterns.toString()
                        ]);
                    });
                    console.log(chalk.blue('Known Attack Techniques:'));
                    console.log(table.toString());
                }
            }
            catch (error) {
                console.error(chalk.red('Error listing techniques:'), error.message);
                process.exit(1);
            }
        });
    }
    createListSignaturesCommand() {
        return new commander_1.Command('signatures')
            .description('List threat signatures')
            .action(async () => {
            try {
                await this.ensureAuthenticated();
                const signatures = this.analyzer.getSignatureDatabase();
                if (this.config.outputFormat === 'json') {
                    console.log(JSON.stringify(signatures, null, 2));
                }
                else {
                    const table = new cli_table3_1.default({
                        head: ['ID', 'Name', 'Type', 'Pattern'],
                        colWidths: [20, 25, 15, 40]
                    });
                    signatures.forEach(signature => {
                        table.push([
                            signature.id,
                            signature.name,
                            signature.type,
                            signature.pattern.substring(0, 37) + (signature.pattern.length > 37 ? '...' : '')
                        ]);
                    });
                    console.log(chalk.blue('Threat Signatures:'));
                    console.log(table.toString());
                }
            }
            catch (error) {
                console.error(chalk.red('Error listing signatures:'), error.message);
                process.exit(1);
            }
        });
    }
    createGetMetricsCommand() {
        return new commander_1.Command('metrics')
            .description('Get learning system metrics')
            .action(async () => {
            try {
                await this.ensureAuthenticated();
                const metrics = this.learningSystem.getMetrics();
                if (this.config.outputFormat === 'json') {
                    console.log(JSON.stringify(metrics, null, 2));
                }
                else {
                    console.log(chalk.blue('Learning System Metrics:'));
                    console.log(`Total Samples Analyzed: ${metrics.totalSamplesAnalyzed}`);
                    console.log(`Successful Detections: ${metrics.successfulDetections}`);
                    console.log(`False Positives: ${metrics.falsePositives}`);
                    console.log(`False Negatives: ${metrics.falseNegatives}`);
                    console.log(`Average Risk Score: ${metrics.averageRiskScore.toFixed(2)}`);
                    console.log(`Technique Evolutions: ${metrics.techniqueEvolutionCount}`);
                    console.log(`Signature Evolutions: ${metrics.signatureEvolutionCount}`);
                    console.log(`Last Update: ${new Date(metrics.lastUpdateTime).toLocaleString()}`);
                }
            }
            catch (error) {
                console.error(chalk.red('Error getting metrics:'), error.message);
                process.exit(1);
            }
        });
    }
    createGetInsightsCommand() {
        return new commander_1.Command('insights')
            .description('Get learning system insights')
            .action(async () => {
            try {
                await this.ensureAuthenticated();
                const insights = this.learningSystem.getLearningInsights();
                console.log(chalk.blue('Learning System Insights:'));
                insights.forEach((insight, index) => {
                    console.log(`${index + 1}. ${insight}`);
                });
            }
            catch (error) {
                console.error(chalk.red('Error getting insights:'), error.message);
                process.exit(1);
            }
        });
    }
    createResetLearningCommand() {
        return new commander_1.Command('reset')
            .description('Reset learning system')
            .option('--confirm', 'Confirm reset operation')
            .action(async (options) => {
            try {
                await this.ensureAuthenticated();
                if (!options.confirm) {
                    console.error(chalk.red('This will reset all learning data. Use --confirm to proceed.'));
                    process.exit(1);
                }
                await this.learningSystem.reset();
                console.log(chalk.green('Learning system reset successfully'));
            }
            catch (error) {
                console.error(chalk.red('Error resetting learning system:'), error.message);
                process.exit(1);
            }
        });
    }
    createStatusCommand() {
        return new commander_1.Command('status')
            .description('Show system status')
            .action(async () => {
            try {
                const executions = this.sandbox.getActiveExecutions();
                const metrics = this.learningSystem.getMetrics();
                const sessions = this.accessControl.getActiveSessions();
                console.log(chalk.blue('Prophecy Sandbox Status:'));
                console.log(`Active Executions: ${executions.length}`);
                console.log(`Total Samples Analyzed: ${metrics.totalSamplesAnalyzed}`);
                console.log(`Active Sessions: ${sessions.length}`);
                console.log(`System Uptime: ${process.uptime().toFixed(2)} seconds`);
                if (this.config.verbose) {
                    console.log(chalk.yellow('\\nDetailed Information:'));
                    executions.forEach(execution => {
                        console.log(`  - ${execution.id}: ${execution.status} (${execution.sampleId})`);
                    });
                }
            }
            catch (error) {
                console.error(chalk.red('Error getting status:'), error.message);
                process.exit(1);
            }
        });
    }
    createInitCommand() {
        return new commander_1.Command('init')
            .description('Initialize Prophecy Sandbox')
            .action(async () => {
            try {
                console.log(chalk.yellow('Initializing Prophecy Sandbox...'));
                await this.sandbox.initialize();
                console.log(chalk.green('Prophecy Sandbox initialized successfully'));
            }
            catch (error) {
                console.error(chalk.red('Error initializing sandbox:'), error.message);
                process.exit(1);
            }
        });
    }
    createShutdownCommand() {
        return new commander_1.Command('shutdown')
            .description('Shutdown Prophecy Sandbox')
            .option('--confirm', 'Confirm shutdown operation')
            .action(async (options) => {
            try {
                if (!options.confirm) {
                    console.error(chalk.red('This will shutdown the Prophecy Sandbox. Use --confirm to proceed.'));
                    process.exit(1);
                }
                console.log(chalk.yellow('Shutting down Prophecy Sandbox...'));
                await this.sandbox.shutdown();
                await this.accessControl.shutdown();
                console.log(chalk.green('Prophecy Sandbox shutdown successfully'));
            }
            catch (error) {
                console.error(chalk.red('Error during shutdown:'), error.message);
                process.exit(1);
            }
        });
    }
    async ensureAuthenticated() {
        const token = this.loadToken();
        if (!token) {
            console.error(chalk.red('Authentication required. Run "prophecy-sandbox auth login" first.'));
            process.exit(1);
        }
        const session = await this.accessControl.validateToken(token);
        if (!session) {
            console.error(chalk.red('Invalid or expired token. Run "prophecy-sandbox auth login" again.'));
            process.exit(1);
        }
    }
    loadToken() {
        try {
            const tokenPath = path.join(process.env.HOME || '', '.prophecy-sandbox-token');
            if (fs.existsSync(tokenPath)) {
                return fs.readFileSync(tokenPath, 'utf8').trim();
            }
        }
        catch (error) {
            // Token file doesn't exist or can't be read
        }
        return null;
    }
    saveToken(token) {
        try {
            const tokenPath = path.join(process.env.HOME || '', '.prophecy-sandbox-token');
            fs.writeFileSync(tokenPath, token);
            fs.chmodSync(tokenPath, 0o600); // Secure permissions
        }
        catch (error) {
            console.warn(chalk.yellow('Warning: Could not save token to file'));
        }
    }
    outputSample(sample) {
        if (this.config.outputFormat === 'json') {
            console.log(JSON.stringify(sample, null, 2));
        }
        else {
            console.log(chalk.blue('Generated Sample:'));
            console.log(`ID: ${sample.id}`);
            console.log(`Name: ${sample.name}`);
            console.log(`Type: ${sample.type}`);
            console.log(`Language: ${sample.language}`);
            console.log(`Threat Level: ${sample.metadata.threatLevel}`);
            console.log(`Generated: ${new Date(sample.metadata.generatedAt).toLocaleString()}`);
            if (this.config.verbose) {
                console.log(chalk.yellow('\\nSample Code:'));
                console.log(sample.code);
            }
        }
    }
    outputExecution(execution, detailed = false) {
        if (this.config.outputFormat === 'json') {
            console.log(JSON.stringify(execution, null, 2));
        }
        else {
            console.log(chalk.blue('Execution Details:'));
            console.log(`ID: ${execution.id}`);
            console.log(`Sample ID: ${execution.sampleId}`);
            console.log(`Status: ${execution.status}`);
            console.log(`Start Time: ${new Date(execution.startTime).toLocaleString()}`);
            if (execution.endTime) {
                console.log(`End Time: ${new Date(execution.endTime).toLocaleString()}`);
            }
            console.log(`Risk Score: ${execution.analysisResults.riskScore}`);
            if (detailed) {
                console.log(chalk.yellow('\\nAnalysis Results:'));
                console.log(`Summary: ${execution.analysisResults.summary}`);
                console.log(`Techniques Found: ${execution.analysisResults.techniques.length}`);
                console.log(`Anomalies Detected: ${execution.analysisResults.anomalies.length}`);
                console.log(`Signatures Matched: ${execution.analysisResults.signatures.length}`);
                if (this.config.verbose) {
                    console.log(chalk.yellow('\\nTechniques:'));
                    execution.analysisResults.techniques.forEach(technique => {
                        console.log(`  - ${technique.name} (${technique.confidence.toFixed(2)})`);
                    });
                    console.log(chalk.yellow('\\nAnomalies:'));
                    execution.analysisResults.anomalies.forEach(anomaly => {
                        console.log(`  - ${anomaly.description} (${anomaly.severity})`);
                    });
                }
            }
        }
    }
    outputAnalysis(analysis) {
        if (this.config.outputFormat === 'json') {
            console.log(JSON.stringify(analysis, null, 2));
        }
        else {
            console.log(chalk.blue('Threat Analysis Results:'));
            console.log(`Risk Score: ${analysis.riskScore}/100`);
            console.log(`Summary: ${analysis.summary}`);
            console.log(chalk.yellow('\\nAttack Techniques:'));
            const techniquesTable = new cli_table3_1.default({
                head: ['Name', 'Category', 'Confidence'],
                colWidths: [25, 20, 15]
            });
            analysis.techniques.forEach(technique => {
                techniquesTable.push([
                    technique.name,
                    technique.category,
                    technique.confidence.toFixed(2)
                ]);
            });
            console.log(techniquesTable.toString());
            console.log(chalk.yellow('\\nSecurity Anomalies:'));
            const anomaliesTable = new cli_table3_1.default({
                head: ['Type', 'Severity', 'Description'],
                colWidths: [20, 15, 45]
            });
            analysis.anomalies.forEach(anomaly => {
                anomaliesTable.push([
                    anomaly.type,
                    anomaly.severity,
                    anomaly.description
                ]);
            });
            console.log(anomaliesTable.toString());
        }
    }
    async run(argv) {
        try {
            await this.program.parseAsync(argv);
        }
        catch (error) {
            console.error(chalk.red('CLI Error:'), error.message);
            process.exit(1);
        }
    }
}
exports.CLIInterface = CLIInterface;
//# sourceMappingURL=CLIInterface.js.map