"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ThreatAnalyzer = void 0;
const uuid_1 = require("uuid");
const BehavioralGraphBuilder_1 = require("./BehavioralGraphBuilder");
class ThreatAnalyzer {
    constructor(config) {
        this.techniqueDatabase = new Map();
        this.signatureDatabase = new Map();
        this.config = config;
        this.graphConfig = {
            maxNodes: 1000,
            timeWindow: 5000, // 5 seconds
            minSimilarity: 0.3,
            enableClustering: true,
            clusterThreshold: 5
        };
        this.graphBuilder = new BehavioralGraphBuilder_1.BehavioralGraphBuilder(this.graphConfig);
        this.loadTechniqueDatabase();
        this.loadSignatureDatabase();
    }
    async analyzeExecution(execution) {
        const result = {
            behaviorGraph: [],
            techniques: [],
            anomalies: [],
            signatures: [],
            riskScore: 0,
            summary: ''
        };
        try {
            // Build behavior graph
            if (this.config.enableBehavioralAnalysis) {
                result.behaviorGraph = await this.buildBehaviorGraph(execution);
            }
            // Identify attack techniques
            result.techniques = await this.identifyAttackTechniques(execution);
            // Detect anomalies
            if (this.config.enableAnomalyDetection) {
                result.anomalies = await this.detectAnomalies(execution);
            }
            // Match signatures
            if (this.config.enableSignatureMatching) {
                result.signatures = await this.matchSignatures(execution);
            }
            // Calculate risk score
            result.riskScore = this.calculateRiskScore(result);
            // Generate summary
            result.summary = this.generateSummary(result);
        }
        catch (error) {
            console.error('Threat analysis failed:', error);
            result.summary = `Analysis failed: ${error.message}`;
        }
        return result;
    }
    async buildBehaviorGraph(execution) {
        // Use real behavioral graph builder
        const behaviorNodes = this.graphBuilder.buildGraph(execution.systemCalls, execution.networkActivity, execution.fileChanges, execution.logs);
        // Enhance nodes with additional metadata
        const enhancedNodes = behaviorNodes.map(node => ({
            ...node,
            metadata: {
                ...node.metadata,
                riskScore: this.calculateNodeRisk(node),
                anomalyScore: this.calculateNodeAnomalyScore(node)
            }
        }));
        return enhancedNodes;
    }
    calculateNodeRisk(node) {
        let risk = 0;
        // Base risk by type
        const typeRisks = { syscall: 0.3, network: 0.5, file: 0.2, log: 0.1 };
        risk += typeRisks[node.type] || 0.1;
        // Risk from metadata
        if (node.metadata.risk) {
            risk += node.metadata.risk * 0.5;
        }
        // Risk from connections
        const degree = node.children.length;
        risk += Math.min(degree / 10, 0.2);
        return Math.min(risk, 1.0);
    }
    calculateNodeAnomalyScore(node) {
        let anomaly = 0;
        // Check for unusual patterns
        if (node.type === 'syscall' && node.metadata.syscall === 'ptrace') {
            anomaly += 0.8;
        }
        if (node.type === 'network' && node.metadata.blocked) {
            anomaly += 0.7;
        }
        if (node.type === 'file' && node.metadata.action === 'delete') {
            anomaly += 0.5;
        }
        return Math.min(anomaly, 1.0);
    }
    buildNodeRelationships(nodes) {
        // Sort nodes by timestamp
        const sortedNodes = nodes.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        // Connect sequential nodes
        for (let i = 0; i < sortedNodes.length - 1; i++) {
            const currentNode = sortedNodes[i];
            const nextNode = sortedNodes[i + 1];
            // Connect if within reasonable time window (5 seconds)
            const timeDiff = new Date(nextNode.timestamp).getTime() - new Date(currentNode.timestamp).getTime();
            if (timeDiff <= 5000) {
                currentNode.children.push(nextNode.id);
            }
        }
    }
    async identifyAttackTechniques(execution) {
        const techniques = [];
        for (const [techniqueId, pattern] of this.techniqueDatabase) {
            const confidence = this.calculateTechniqueConfidence(execution, pattern);
            if (confidence > 0.5) { // Threshold for technique detection
                const evidence = this.gatherEvidence(execution, pattern);
                techniques.push({
                    id: techniqueId,
                    name: pattern.name,
                    description: pattern.description,
                    category: pattern.category,
                    confidence,
                    evidence
                });
            }
        }
        return techniques.sort((a, b) => b.confidence - a.confidence);
    }
    calculateTechniqueConfidence(execution, pattern) {
        let totalScore = 0;
        let maxScore = 0;
        // Check syscall patterns
        if (pattern.syscallPatterns.length > 0) {
            maxScore += pattern.syscallPatterns.length;
            for (const syscallPattern of pattern.syscallPatterns) {
                if (this.matchesPattern(execution.systemCalls, 'syscall', syscallPattern)) {
                    totalScore++;
                }
            }
        }
        // Check network patterns
        if (pattern.networkPatterns.length > 0) {
            maxScore += pattern.networkPatterns.length;
            for (const networkPattern of pattern.networkPatterns) {
                if (this.matchesPattern(execution.networkActivity, 'network', networkPattern)) {
                    totalScore++;
                }
            }
        }
        // Check file patterns
        if (pattern.filePatterns.length > 0) {
            maxScore += pattern.filePatterns.length;
            for (const filePattern of pattern.filePatterns) {
                if (this.matchesPattern(execution.fileChanges, 'file', filePattern)) {
                    totalScore++;
                }
            }
        }
        return maxScore > 0 ? totalScore / maxScore : 0;
    }
    matchesPattern(records, recordType, pattern) {
        // Simple pattern matching - in real implementation would be more sophisticated
        const regex = new RegExp(pattern.replace('*', '.*'), 'i');
        for (const record of records) {
            let text = '';
            switch (recordType) {
                case 'syscall':
                    text = `${record.syscall} ${record.args.join(' ')}`;
                    break;
                case 'network':
                    text = `${record.destination}:${record.port}`;
                    break;
                case 'file':
                    text = record.path;
                    break;
            }
            if (regex.test(text)) {
                return true;
            }
        }
        return false;
    }
    gatherEvidence(execution, pattern) {
        const evidence = [];
        // Gather matching syscalls
        for (const syscallPattern of pattern.syscallPatterns) {
            const matches = execution.systemCalls.filter(syscall => this.matchesPattern([syscall], 'syscall', syscallPattern));
            if (matches.length > 0) {
                evidence.push(`Syscall pattern matched: ${syscallPattern} (${matches.length} occurrences)`);
            }
        }
        // Gather matching network activity
        for (const networkPattern of pattern.networkPatterns) {
            const matches = execution.networkActivity.filter(network => this.matchesPattern([network], 'network', networkPattern));
            if (matches.length > 0) {
                evidence.push(`Network pattern matched: ${networkPattern} (${matches.length} occurrences)`);
            }
        }
        // Gather matching file changes
        for (const filePattern of pattern.filePatterns) {
            const matches = execution.fileChanges.filter(fileChange => this.matchesPattern([fileChange], 'file', filePattern));
            if (matches.length > 0) {
                evidence.push(`File pattern matched: ${filePattern} (${matches.length} occurrences)`);
            }
        }
        return evidence;
    }
    async detectAnomalies(execution) {
        const anomalies = [];
        // Detect unusual syscall patterns
        const syscallAnomalies = this.detectSyscallAnomalies(execution.systemCalls);
        anomalies.push(...syscallAnomalies);
        // Detect unusual network activity
        const networkAnomalies = this.detectNetworkAnomalies(execution.networkActivity);
        anomalies.push(...networkAnomalies);
        // Detect unusual file activity
        const fileAnomalies = this.detectFileAnomalies(execution.fileChanges);
        anomalies.push(...fileAnomalies);
        return anomalies;
    }
    detectSyscallAnomalies(syscalls) {
        const anomalies = [];
        const syscallCounts = new Map();
        // Count syscalls
        for (const syscall of syscalls) {
            syscallCounts.set(syscall.syscall, (syscallCounts.get(syscall.syscall) || 0) + 1);
        }
        // Detect high-frequency syscalls
        for (const [syscall, count] of syscallCounts) {
            if (count > 1000) { // Threshold for high frequency
                anomalies.push({
                    id: (0, uuid_1.v4)(),
                    type: 'high_frequency_syscall',
                    description: `High frequency syscall detected: ${syscall} (${count} calls)`,
                    severity: 'medium',
                    timestamp: new Date().toISOString(),
                    context: { syscall, count }
                });
            }
        }
        // Detect suspicious syscalls
        const suspiciousSyscalls = ['ptrace', 'process_vm_writev', 'execve', 'mount'];
        for (const suspicious of suspiciousSyscalls) {
            if (syscallCounts.has(suspicious)) {
                anomalies.push({
                    id: (0, uuid_1.v4)(),
                    type: 'suspicious_syscall',
                    description: `Suspicious syscall detected: ${suspicious}`,
                    severity: 'high',
                    timestamp: new Date().toISOString(),
                    context: { syscall: suspicious }
                });
            }
        }
        return anomalies;
    }
    detectNetworkAnomalies(networkActivity) {
        const anomalies = [];
        // Detect external connections
        const externalConnections = networkActivity.filter(activity => !activity.destination.startsWith('127.') &&
            !activity.destination.startsWith('192.168.') &&
            !activity.destination.startsWith('10.') &&
            !activity.blocked);
        if (externalConnections.length > 0) {
            anomalies.push({
                id: (0, uuid_1.v4)(),
                type: 'external_connection',
                description: `External network connection detected: ${externalConnections[0].destination}:${externalConnections[0].port}`,
                severity: 'high',
                timestamp: externalConnections[0].timestamp,
                context: { connections: externalConnections.length }
            });
        }
        // Detect high-volume data transfer
        const highVolumeTransfers = networkActivity.filter(activity => activity.size > 1024 * 1024); // > 1MB
        if (highVolumeTransfers.length > 0) {
            anomalies.push({
                id: (0, uuid_1.v4)(),
                type: 'high_volume_transfer',
                description: `High volume data transfer detected: ${highVolumeTransfers[0].size} bytes`,
                severity: 'medium',
                timestamp: highVolumeTransfers[0].timestamp,
                context: { size: highVolumeTransfers[0].size }
            });
        }
        return anomalies;
    }
    detectFileAnomalies(fileChanges) {
        const anomalies = [];
        // Detect suspicious file locations
        const suspiciousPaths = ['/etc/', '/usr/bin/', '/bin/', '/sbin/', '/boot/'];
        for (const fileChange of fileChanges) {
            for (const suspiciousPath of suspiciousPaths) {
                if (fileChange.path.startsWith(suspiciousPath)) {
                    anomalies.push({
                        id: (0, uuid_1.v4)(),
                        type: 'suspicious_file_location',
                        description: `File operation in suspicious location: ${fileChange.path}`,
                        severity: 'high',
                        timestamp: fileChange.timestamp,
                        context: { path: fileChange.path, action: fileChange.action }
                    });
                }
            }
        }
        // Detect rapid file changes
        const changesPerSecond = this.calculateFileChangeRate(fileChanges);
        if (changesPerSecond > 10) {
            anomalies.push({
                id: (0, uuid_1.v4)(),
                type: 'rapid_file_changes',
                description: `Rapid file changes detected: ${changesPerSecond} changes/second`,
                severity: 'medium',
                timestamp: new Date().toISOString(),
                context: { rate: changesPerSecond }
            });
        }
        return anomalies;
    }
    calculateFileChangeRate(fileChanges) {
        if (fileChanges.length < 2)
            return 0;
        const startTime = new Date(fileChanges[0].timestamp).getTime();
        const endTime = new Date(fileChanges[fileChanges.length - 1].timestamp).getTime();
        const durationSeconds = (endTime - startTime) / 1000;
        return durationSeconds > 0 ? fileChanges.length / durationSeconds : 0;
    }
    async matchSignatures(execution) {
        const matchedSignatures = [];
        for (const signature of this.signatureDatabase.values()) {
            const confidence = this.calculateSignatureConfidence(execution, signature);
            if (confidence > 0.7) { // Higher threshold for signatures
                matchedSignatures.push({
                    ...signature,
                    confidence,
                    applicable: true
                });
            }
        }
        return matchedSignatures;
    }
    calculateSignatureConfidence(execution, signature) {
        // Simple signature matching - in real implementation would be more sophisticated
        const regex = new RegExp(signature.pattern, 'i');
        let matches = 0;
        let totalChecks = 0;
        // Check against behavior graph
        for (const node of execution.analysisResults.behaviorGraph) {
            totalChecks++;
            if (regex.test(node.description)) {
                matches++;
            }
        }
        // Check against logs
        for (const log of execution.logs) {
            totalChecks++;
            if (regex.test(log.message)) {
                matches++;
            }
        }
        return totalChecks > 0 ? matches / totalChecks : 0;
    }
    calculateRiskScore(result) {
        let score = 0;
        // Add score for detected techniques
        for (const technique of result.techniques) {
            score += technique.confidence * 20;
        }
        // Add score for anomalies
        for (const anomaly of result.anomalies) {
            const severityScores = { low: 5, medium: 10, high: 20, critical: 30 };
            score += severityScores[anomaly.severity] || 0;
        }
        // Add score for matched signatures
        for (const signature of result.signatures) {
            score += signature.confidence * 15;
        }
        // Add score for behavior complexity
        score += Math.min(result.behaviorGraph.length / 10, 20);
        return Math.min(Math.round(score), 100);
    }
    generateSummary(result) {
        const parts = [];
        if (result.techniques.length > 0) {
            parts.push(`Detected ${result.techniques.length} attack technique(s)`);
        }
        if (result.anomalies.length > 0) {
            parts.push(`Found ${result.anomalies.length} security anomaly(ies)`);
        }
        if (result.signatures.length > 0) {
            parts.push(`Matched ${result.signatures.length} threat signature(s)`);
        }
        if (result.behaviorGraph.length > 0) {
            parts.push(`Analyzed ${result.behaviorGraph.length} behavior node(s)`);
        }
        const riskLevel = this.getRiskLevel(result.riskScore);
        parts.push(`Overall risk level: ${riskLevel} (${result.riskScore}/100)`);
        return parts.join('. ');
    }
    getRiskLevel(score) {
        if (score >= 80)
            return 'Critical';
        if (score >= 60)
            return 'High';
        if (score >= 40)
            return 'Medium';
        if (score >= 20)
            return 'Low';
        return 'Minimal';
    }
    loadTechniqueDatabase() {
        // Load known attack techniques from database
        const techniques = [
            {
                id: 'reverse_shell',
                name: 'Reverse Shell',
                category: 'execution',
                syscallPatterns: ['socket', 'connect', 'dup2'],
                networkPatterns: ['.*:4444', '.*:8080'],
                filePatterns: [],
                description: 'Establishes reverse shell connection to C2 server'
            },
            {
                id: 'file_encryption',
                name: 'File Encryption',
                category: 'impact',
                syscallPatterns: ['open', 'write', 'close'],
                networkPatterns: [],
                filePatterns: ['.*\\.encrypted', '.*\\.locked'],
                description: 'Encrypts files to prevent access'
            },
            {
                id: 'privilege_escalation',
                name: 'Privilege Escalation',
                category: 'privilege-escalation',
                syscallPatterns: ['setuid', 'setgid', 'execve'],
                networkPatterns: [],
                filePatterns: ['/etc/passwd', '/etc/shadow'],
                description: 'Attempts to gain elevated privileges'
            },
            {
                id: 'persistence',
                name: 'Persistence Mechanism',
                category: 'persistence',
                syscallPatterns: ['chmod', 'chown'],
                networkPatterns: [],
                filePatterns: ['/etc/rc\\.d/', '/etc/init\\.d/', '.*\\.service'],
                description: 'Establishes persistence on the system'
            }
        ];
        for (const technique of techniques) {
            this.techniqueDatabase.set(technique.id, technique);
        }
    }
    loadSignatureDatabase() {
        // Load known threat signatures
        const signatures = [
            {
                id: 'powershell_reverse_shell',
                name: 'PowerShell Reverse Shell',
                pattern: 'powershell.*-nop.*-w hidden.*-c.*IEX',
                type: 'behavioral',
                confidence: 0,
                applicable: false
            },
            {
                id: 'python_backdoor',
                name: 'Python Backdoor',
                pattern: 'socket.*connect.*subprocess',
                type: 'structural',
                confidence: 0,
                applicable: false
            },
            {
                id: 'keylogger_pattern',
                name: 'Keylogger Pattern',
                pattern: 'keydown.*keypress.*onkeydown',
                type: 'behavioral',
                confidence: 0,
                applicable: false
            }
        ];
        for (const signature of signatures) {
            this.signatureDatabase.set(signature.id, signature);
        }
    }
    addSignature(signature) {
        this.signatureDatabase.set(signature.id, signature);
    }
    addTechnique(technique) {
        this.techniqueDatabase.set(technique.id, technique);
    }
    getTechniqueDatabase() {
        return Array.from(this.techniqueDatabase.values());
    }
    getSignatureDatabase() {
        return Array.from(this.signatureDatabase.values());
    }
}
exports.ThreatAnalyzer = ThreatAnalyzer;
//# sourceMappingURL=ThreatAnalyzer.js.map