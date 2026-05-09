"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BehavioralGraphBuilder = void 0;
const uuid_1 = require("uuid");
class BehavioralGraphBuilder {
    constructor(config) {
        this.nodes = new Map();
        this.adjacencyList = new Map();
        this.clusters = [];
        this.config = config;
    }
    buildGraph(syscalls, networkActivity, fileChanges, logs) {
        // Clear previous state
        this.nodes.clear();
        this.adjacencyList.clear();
        this.clusters = [];
        // Convert all events to nodes
        this.createNodesFromSyscalls(syscalls);
        this.createNodesFromNetwork(networkActivity);
        this.createNodesFromFileChanges(fileChanges);
        this.createNodesFromLogs(logs);
        // Build temporal relationships
        this.buildTemporalRelationships();
        // Build semantic relationships
        this.buildSemanticRelationships();
        // Apply clustering if enabled
        if (this.config.enableClustering) {
            this.applyClustering();
        }
        // Limit graph size
        this.limitGraphSize();
        return Array.from(this.nodes.values());
    }
    createNodesFromSyscalls(syscalls) {
        for (const syscall of syscalls) {
            const node = {
                id: (0, uuid_1.v4)(),
                type: 'syscall',
                description: this.formatSyscallDescription(syscall),
                timestamp: syscall.timestamp,
                children: [],
                metadata: {
                    syscall: syscall.syscall,
                    args: syscall.args,
                    result: syscall.result,
                    process: syscall.process,
                    category: this.categorizeSyscall(syscall.syscall),
                    risk: this.assessSyscallRisk(syscall)
                }
            };
            this.nodes.set(node.id, node);
            this.adjacencyList.set(node.id, new Set());
        }
    }
    createNodesFromNetwork(networkActivity) {
        for (const network of networkActivity) {
            const node = {
                id: (0, uuid_1.v4)(),
                type: 'network',
                description: this.formatNetworkDescription(network),
                timestamp: network.timestamp,
                children: [],
                metadata: {
                    protocol: network.protocol,
                    destination: network.destination,
                    port: network.port,
                    size: network.size,
                    blocked: network.blocked,
                    category: this.categorizeNetworkActivity(network),
                    risk: this.assessNetworkRisk(network)
                }
            };
            this.nodes.set(node.id, node);
            this.adjacencyList.set(node.id, new Set());
        }
    }
    createNodesFromFileChanges(fileChanges) {
        for (const fileChange of fileChanges) {
            const node = {
                id: (0, uuid_1.v4)(),
                type: 'file',
                description: this.formatFileDescription(fileChange),
                timestamp: fileChange.timestamp,
                children: [],
                metadata: {
                    action: fileChange.action,
                    path: fileChange.path,
                    hash: fileChange.hash,
                    size: fileChange.size,
                    category: this.categorizeFileChange(fileChange),
                    risk: this.assessFileRisk(fileChange)
                }
            };
            this.nodes.set(node.id, node);
            this.adjacencyList.set(node.id, new Set());
        }
    }
    createNodesFromLogs(logs) {
        for (const log of logs) {
            const node = {
                id: (0, uuid_1.v4)(),
                type: 'log',
                description: `[${log.level.toUpperCase()}] ${log.message}`,
                timestamp: log.timestamp,
                children: [],
                metadata: {
                    level: log.level,
                    source: log.source,
                    message: log.message,
                    category: this.categorizeLogEntry(log),
                    risk: this.assessLogRisk(log)
                }
            };
            this.nodes.set(node.id, node);
            this.adjacencyList.set(node.id, new Set());
        }
    }
    buildTemporalRelationships() {
        const sortedNodes = Array.from(this.nodes.values())
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        for (let i = 0; i < sortedNodes.length - 1; i++) {
            const currentNode = sortedNodes[i];
            const nextNode = sortedNodes[i + 1];
            const timeDiff = new Date(nextNode.timestamp).getTime() - new Date(currentNode.timestamp).getTime();
            // Connect nodes if they're within time window
            if (timeDiff <= this.config.timeWindow) {
                this.addEdge(currentNode.id, nextNode.id, 'temporal', timeDiff);
            }
        }
    }
    buildSemanticRelationships() {
        const nodeArray = Array.from(this.nodes.values());
        for (let i = 0; i < nodeArray.length; i++) {
            for (let j = i + 1; j < nodeArray.length; j++) {
                const node1 = nodeArray[i];
                const node2 = nodeArray[j];
                const similarity = this.calculateSemanticSimilarity(node1, node2);
                if (similarity >= this.config.minSimilarity) {
                    this.addEdge(node1.id, node2.id, 'semantic', similarity);
                }
            }
        }
    }
    calculateSemanticSimilarity(node1, node2) {
        let similarity = 0;
        // Type similarity
        if (node1.type === node2.type) {
            similarity += 0.3;
        }
        // Category similarity
        const category1 = node1.metadata.category;
        const category2 = node2.metadata.category;
        if (category1 === category2) {
            similarity += 0.3;
        }
        // Process similarity
        const process1 = node1.metadata.process;
        const process2 = node2.metadata.process;
        if (process1 && process2 && process1 === process2) {
            similarity += 0.2;
        }
        // Description similarity (simple text similarity)
        const textSimilarity = this.calculateTextSimilarity(node1.description, node2.description);
        similarity += textSimilarity * 0.2;
        return Math.min(similarity, 1.0);
    }
    calculateTextSimilarity(text1, text2) {
        const words1 = new Set(text1.toLowerCase().split(/\s+/));
        const words2 = new Set(text2.toLowerCase().split(/\s+/));
        const intersection = new Set([...words1].filter(word => words2.has(word)));
        const union = new Set([...words1, ...words2]);
        return intersection.size / union.size;
    }
    addEdge(fromId, toId, type, weight) {
        const fromAdj = this.adjacencyList.get(fromId);
        if (fromAdj) {
            fromAdj.add(toId);
            // Update node children
            const fromNode = this.nodes.get(fromId);
            if (fromNode && !fromNode.children.includes(toId)) {
                fromNode.children.push(toId);
            }
        }
    }
    applyClustering() {
        const nodeArray = Array.from(this.nodes.values());
        const visited = new Set();
        for (const node of nodeArray) {
            if (visited.has(node.id))
                continue;
            const cluster = this.findCluster(node, visited);
            if (cluster.nodes.length >= this.config.clusterThreshold) {
                this.clusters.push(cluster);
            }
        }
    }
    findCluster(startNode, visited) {
        const cluster = {
            id: (0, uuid_1.v4)(),
            nodes: [],
            type: 'sequential',
            description: '',
            confidence: 0
        };
        const queue = [startNode];
        const clusterNodes = new Map();
        while (queue.length > 0) {
            const node = queue.shift();
            if (visited.has(node.id))
                continue;
            visited.add(node.id);
            clusterNodes.set(node.id, node);
            cluster.nodes.push(node.id);
            // Add neighbors
            const neighbors = this.adjacencyList.get(node.id);
            if (neighbors) {
                for (const neighborId of neighbors) {
                    const neighbor = this.nodes.get(neighborId);
                    if (neighbor && !visited.has(neighborId)) {
                        queue.push(neighbor);
                    }
                }
            }
        }
        // Determine cluster type and description
        cluster.type = this.determineClusterType(Array.from(clusterNodes.values()));
        cluster.description = this.generateClusterDescription(cluster, Array.from(clusterNodes.values()));
        cluster.confidence = this.calculateClusterConfidence(Array.from(clusterNodes.values()));
        return cluster;
    }
    determineClusterType(nodes) {
        const typeCounts = new Map();
        for (const node of nodes) {
            typeCounts.set(node.type, (typeCounts.get(node.type) || 0) + 1);
        }
        const dominantType = Array.from(typeCounts.entries())
            .sort((a, b) => b[1] - a[1])[0][0];
        // Determine behavior pattern
        if (dominantType === 'syscall') {
            return this.analyzeSyscallPattern(nodes);
        }
        else if (dominantType === 'network') {
            return 'parallel';
        }
        else if (dominantType === 'file') {
            return this.analyzeFilePattern(nodes);
        }
        return 'sequential';
    }
    analyzeSyscallPattern(nodes) {
        const syscalls = nodes.filter(n => n.type === 'syscall');
        // Check for conditional patterns
        const conditionalSyscalls = syscalls.filter(n => n.metadata.syscall === 'brk' ||
            n.metadata.syscall === 'mmap' ||
            n.metadata.syscall === 'access');
        if (conditionalSyscalls.length > syscalls.length * 0.3) {
            return 'conditional';
        }
        // Check for loop patterns
        const loopSyscalls = syscalls.filter(n => n.metadata.syscall === 'write' ||
            n.metadata.syscall === 'read' ||
            n.metadata.syscall === 'lseek');
        if (loopSyscalls.length > syscalls.length * 0.5) {
            return 'loop';
        }
        return 'sequential';
    }
    analyzeFilePattern(nodes) {
        const fileNodes = nodes.filter(n => n.type === 'file');
        // Check for sequential file operations
        const sequentialOps = ['create', 'modify', 'delete'];
        let isSequential = true;
        for (let i = 0; i < fileNodes.length - 1; i++) {
            const current = fileNodes[i].metadata.action;
            const next = fileNodes[i + 1].metadata.action;
            const currentIndex = sequentialOps.indexOf(current);
            const nextIndex = sequentialOps.indexOf(next);
            if (currentIndex >= nextIndex) {
                isSequential = false;
                break;
            }
        }
        return isSequential ? 'sequential' : 'parallel';
    }
    generateClusterDescription(cluster, nodes) {
        const dominantType = nodes[0]?.type || 'unknown';
        const actionCounts = new Map();
        for (const node of nodes) {
            if (node.type === 'syscall') {
                const syscall = node.metadata.syscall;
                actionCounts.set(syscall, (actionCounts.get(syscall) || 0) + 1);
            }
            else if (node.type === 'file') {
                const action = node.metadata.action;
                actionCounts.set(action, (actionCounts.get(action) || 0) + 1);
            }
        }
        const topAction = Array.from(actionCounts.entries())
            .sort((a, b) => b[1] - a[1])[0];
        if (topAction) {
            return `${dominantType} cluster dominated by ${topAction[0]} (${topAction[1]} occurrences)`;
        }
        return `${dominantType} cluster with ${nodes.length} nodes`;
    }
    calculateClusterConfidence(nodes) {
        if (nodes.length === 0)
            return 0;
        // Confidence based on coherence and consistency
        const types = new Set(nodes.map(n => n.type));
        const typeConsistency = 1 - (types.size / nodes.length);
        const timeSpan = new Date(nodes[nodes.length - 1].timestamp).getTime() -
            new Date(nodes[0].timestamp).getTime();
        const temporalCoherence = Math.max(0, 1 - (timeSpan / (this.config.timeWindow * 10)));
        return (typeConsistency + temporalCoherence) / 2;
    }
    limitGraphSize() {
        if (this.nodes.size <= this.config.maxNodes)
            return;
        // Keep nodes with highest degree centrality
        const nodeDegrees = new Map();
        for (const [nodeId, neighbors] of this.adjacencyList) {
            nodeDegrees.set(nodeId, neighbors.size);
        }
        const sortedNodes = Array.from(nodeDegrees.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, this.config.maxNodes);
        const nodesToKeep = new Set(sortedNodes.map(([nodeId]) => nodeId));
        // Remove nodes and edges
        for (const nodeId of this.nodes.keys()) {
            if (!nodesToKeep.has(nodeId)) {
                this.nodes.delete(nodeId);
                this.adjacencyList.delete(nodeId);
            }
        }
        // Clean up edges to removed nodes
        for (const [nodeId, neighbors] of this.adjacencyList) {
            for (const neighborId of neighbors) {
                if (!nodesToKeep.has(neighborId)) {
                    neighbors.delete(neighborId);
                }
            }
        }
    }
    // Helper methods for categorization and risk assessment
    formatSyscallDescription(syscall) {
        const args = syscall.args.slice(0, 3).join(', '); // Limit args for readability
        return `${syscall.syscall}(${args}) = ${syscall.result}`;
    }
    formatNetworkDescription(network) {
        const status = network.blocked ? '[BLOCKED]' : '[ALLOWED]';
        return `${status} ${network.protocol.toUpperCase()} to ${network.destination}:${network.port} (${network.size} bytes)`;
    }
    formatFileDescription(fileChange) {
        const size = fileChange.size ? ` (${fileChange.size} bytes)` : '';
        return `${fileChange.action.toUpperCase()} ${fileChange.path}${size}`;
    }
    categorizeSyscall(syscall) {
        const categories = {
            'memory': ['mmap', 'brk', 'malloc', 'free'],
            'file': ['open', 'read', 'write', 'close', 'lseek', 'stat'],
            'network': ['socket', 'connect', 'bind', 'listen', 'accept', 'send', 'recv'],
            'process': ['fork', 'exec', 'wait', 'exit', 'kill'],
            'system': ['gettimeofday', 'uname', 'getpid']
        };
        for (const [category, syscalls] of Object.entries(categories)) {
            if (syscalls.some(s => syscall.includes(s))) {
                return category;
            }
        }
        return 'other';
    }
    categorizeNetworkActivity(network) {
        if (network.blocked)
            return 'blocked';
        if (network.port === 80 || network.port === 443)
            return 'web';
        if (network.port === 22)
            return 'ssh';
        if (network.port === 21)
            return 'ftp';
        if (network.port === 25)
            return 'smtp';
        return 'unknown';
    }
    categorizeFileChange(fileChange) {
        if (fileChange.path.startsWith('/etc/'))
            return 'config';
        if (fileChange.path.startsWith('/tmp/'))
            return 'temp';
        if (fileChange.path.startsWith('/home/'))
            return 'user';
        if (fileChange.path.startsWith('/var/'))
            return 'system';
        return 'unknown';
    }
    categorizeLogEntry(log) {
        return log.source;
    }
    assessSyscallRisk(syscall) {
        const riskySyscalls = [
            'ptrace', 'process_vm_writev', 'execve', 'mount', 'umount',
            'setuid', 'setgid', 'chmod', 'chown', 'creat'
        ];
        if (riskySyscalls.includes(syscall.syscall)) {
            return 0.8;
        }
        const moderateRiskSyscalls = [
            'open', 'write', 'connect', 'bind', 'socket'
        ];
        if (moderateRiskSyscalls.includes(syscall.syscall)) {
            return 0.5;
        }
        return 0.1;
    }
    assessNetworkRisk(network) {
        if (network.blocked)
            return 0.9;
        if (network.size > 1024 * 1024)
            return 0.7; // > 1MB
        if (network.destination === 'unknown')
            return 0.6;
        return 0.2;
    }
    assessFileRisk(fileChange) {
        const riskyPaths = ['/etc/passwd', '/etc/shadow', '/etc/sudoers'];
        if (riskyPaths.some(path => fileChange.path.includes(path))) {
            return 0.9;
        }
        if (fileChange.action === 'delete')
            return 0.6;
        if (fileChange.action === 'modify')
            return 0.4;
        return 0.1;
    }
    assessLogRisk(log) {
        if (log.level === 'error')
            return 0.7;
        if (log.level === 'warn')
            return 0.4;
        return 0.1;
    }
    // Public API methods
    getGraphMetrics() {
        const nodeCount = this.nodes.size;
        let edgeCount = 0;
        let totalDegree = 0;
        for (const neighbors of this.adjacencyList.values()) {
            edgeCount += neighbors.size;
            totalDegree += neighbors.size;
        }
        const averageDegree = nodeCount > 0 ? totalDegree / nodeCount : 0;
        return {
            nodeCount,
            edgeCount,
            averageDegree,
            clusteringCoefficient: this.calculateClusteringCoefficient(),
            pathLength: this.calculateAveragePathLength(),
            modularity: this.calculateModularity()
        };
    }
    calculateClusteringCoefficient() {
        let totalCoefficient = 0;
        let nodeCount = 0;
        for (const [nodeId, neighbors] of this.adjacencyList) {
            if (neighbors.size < 2)
                continue;
            let triangles = 0;
            const neighborArray = Array.from(neighbors);
            for (let i = 0; i < neighborArray.length; i++) {
                for (let j = i + 1; j < neighborArray.length; j++) {
                    const neighbor1 = neighborArray[i];
                    const neighbor2 = neighborArray[j];
                    if (this.adjacencyList.get(neighbor1)?.has(neighbor2)) {
                        triangles++;
                    }
                }
            }
            const possibleTriangles = (neighbors.size * (neighbors.size - 1)) / 2;
            totalCoefficient += triangles / possibleTriangles;
            nodeCount++;
        }
        return nodeCount > 0 ? totalCoefficient / nodeCount : 0;
    }
    calculateAveragePathLength() {
        // Simplified calculation - would use BFS for exact path lengths
        const nodeCount = this.nodes.size;
        if (nodeCount === 0)
            return 0;
        // Estimate based on connectivity
        const edgeCount = Array.from(this.adjacencyList.values())
            .reduce((sum, neighbors) => sum + neighbors.size, 0);
        const density = edgeCount / (nodeCount * (nodeCount - 1));
        return density > 0 ? 1 / density : nodeCount;
    }
    calculateModularity() {
        // Simplified modularity calculation
        // Real implementation would use community detection algorithms
        return this.clusters.length > 0 ? 0.5 : 0;
    }
    getClusters() {
        return [...this.clusters];
    }
    getNodes() {
        return Array.from(this.nodes.values());
    }
    getAdjacencyList() {
        const result = new Map();
        for (const [nodeId, neighbors] of this.adjacencyList) {
            result.set(nodeId, new Set(neighbors));
        }
        return result;
    }
}
exports.BehavioralGraphBuilder = BehavioralGraphBuilder;
//# sourceMappingURL=BehavioralGraphBuilder.js.map