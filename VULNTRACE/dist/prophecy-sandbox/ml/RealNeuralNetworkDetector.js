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
exports.RealNeuralNetworkDetector = void 0;
const tf = __importStar(require("@tensorflow/tfjs-node"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const events_1 = require("events");
class RealNeuralNetworkDetector extends events_1.EventEmitter {
    constructor(config, modelPath, trainingDataPath) {
        super();
        this.model = null;
        this.isTraining = false;
        this.trainingHistory = null;
        this.config = config;
        this.modelPath = modelPath;
        this.trainingDataPath = trainingDataPath;
        this.featureExtractor = new FeatureExtractor();
        this.initializeModel();
    }
    async initializeModel() {
        try {
            // Try to load existing model
            if (fs.existsSync(this.modelPath)) {
                this.model = await tf.loadLayersModel(`file://${this.modelPath}`);
                console.log('[ML] Loaded existing neural network model');
            }
            else {
                // Create new model
                this.createModel();
                await this.saveModel();
                console.log('[ML] Created new neural network model');
            }
        }
        catch (error) {
            console.error('[ML] Failed to initialize model:', error);
            this.createModel(); // Fallback to new model
        }
    }
    createModel() {
        this.model = tf.sequential();
        // Input layer
        this.model.add(tf.layers.dense({
            inputShape: [this.config.inputSize],
            units: this.config.hiddenLayers[0],
            activation: this.config.activation
        }));
        // Hidden layers with dropout
        for (let i = 1; i < this.config.hiddenLayers.length; i++) {
            this.model.add(tf.layers.dropout({ rate: this.config.dropout }));
            this.model.add(tf.layers.dense({
                units: this.config.hiddenLayers[i],
                activation: this.config.activation
            }));
        }
        // Output layer
        this.model.add(tf.layers.dense({
            units: this.config.outputSize,
            activation: 'softmax'
        }));
        // Compile model
        this.model.compile({
            optimizer: tf.train.adam(this.config.learningRate),
            loss: 'categoricalCrossentropy',
            metrics: ['accuracy', 'precision', 'recall']
        });
        ;
        console.log('[ML] Neural network model created');
        console.log('[ML] Model summary:');
        this.model.summary();
    }
    async extractFeatures(execution) {
        return this.featureExtractor.extractFeatures(execution);
    }
    async predict(execution) {
        if (!this.model) {
            throw new Error('Model not initialized');
        }
        try {
            const features = await this.extractFeatures(execution);
            const inputTensor = tf.tensor2d([features]);
            const prediction = this.model.predict(inputTensor);
            const probabilities = await prediction.data();
            const threatLevel = this.calculateThreatLevel(probabilities);
            const confidence = Math.max(...probabilities);
            const threatType = this.classifyThreatType(probabilities);
            const reasoning = this.generateReasoning(features, probabilities);
            // Clean up tensors
            inputTensor.dispose();
            prediction.dispose();
            const result = {
                threatLevel,
                confidence,
                threatType,
                features,
                reasoning
            };
            this.emit('prediction', result);
            return result;
        }
        catch (error) {
            console.error('[ML] Prediction failed:', error);
            throw error;
        }
    }
    calculateThreatLevel(probabilities) {
        // Weighted calculation based on different threat categories
        const weights = [0.1, 0.3, 0.6, 0.9]; // low, medium, high, critical
        let weightedSum = 0;
        for (let i = 0; i < probabilities.length; i++) {
            weightedSum += probabilities[i] * weights[i];
        }
        return weightedSum;
    }
    classifyThreatType(probabilities) {
        const categories = ['benign', 'suspicious', 'malicious', 'critical'];
        const maxIndex = probabilities.indexOf(Math.max(...probabilities));
        return categories[maxIndex];
    }
    generateReasoning(features, probabilities) {
        const reasons = [];
        // Analyze feature patterns
        if (features[0] > 0.8)
            reasons.push('High system call activity detected');
        if (features[1] > 0.7)
            reasons.push('Unusual network traffic patterns');
        if (features[2] > 0.6)
            reasons.push('Suspicious file system operations');
        if (features[3] > 0.5)
            reasons.push('Potential privilege escalation attempts');
        // Add probability-based reasoning
        const maxProb = Math.max(...probabilities);
        if (maxProb > 0.8) {
            reasons.push('High confidence threat detection');
        }
        else if (maxProb > 0.5) {
            reasons.push('Moderate confidence - requires investigation');
        }
        return reasons.join('; ') || 'No specific threats detected';
    }
    async train(trainingData) {
        if (!this.model) {
            throw new Error('Model not initialized');
        }
        if (this.isTraining) {
            throw new Error('Model is already training');
        }
        this.isTraining = true;
        this.emit('trainingStarted');
        try {
            // Convert training data to tensors
            const features = tf.tensor2d(trainingData.features);
            const labels = tf.tensor2d(trainingData.labels);
            // Train the model
            this.trainingHistory = await this.model.fit(features, labels, {
                epochs: this.config.epochs,
                batchSize: this.config.batchSize,
                validationSplit: this.config.validationSplit,
                callbacks: {
                    onEpochEnd: (epoch, logs) => {
                        this.emit('epochCompleted', epoch, logs);
                        console.log(`[ML] Epoch ${epoch + 1}/${this.config.epochs}: loss=${logs.loss.toFixed(4)}, accuracy=${logs.acc.toFixed(4)}`);
                    },
                    onTrainEnd: () => {
                        this.emit('trainingCompleted', this.trainingHistory);
                    }
                }
            });
            // Save the trained model
            await this.saveModel();
            // Clean up tensors
            features.dispose();
            labels.dispose();
            console.log('[ML] Training completed successfully');
            return this.trainingHistory;
        }
        catch (error) {
            console.error('[ML] Training failed:', error);
            throw error;
        }
        finally {
            this.isTraining = false;
        }
    }
    async saveModel() {
        if (!this.model)
            return;
        try {
            // Ensure directory exists
            const dir = path.dirname(this.modelPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            await this.model.save(`file://${this.modelPath}`);
            console.log('[ML] Model saved to:', this.modelPath);
        }
        catch (error) {
            console.error('[ML] Failed to save model:', error);
            throw error;
        }
    }
    async loadTrainingData() {
        try {
            if (!fs.existsSync(this.trainingDataPath)) {
                // Generate initial training data if none exists
                return this.generateInitialTrainingData();
            }
            const data = JSON.parse(fs.readFileSync(this.trainingDataPath, 'utf8'));
            return data;
        }
        catch (error) {
            console.error('[ML] Failed to load training data:', error);
            return this.generateInitialTrainingData();
        }
    }
    generateInitialTrainingData() {
        console.log('[ML] Generating initial training data...');
        const features = [];
        const labels = [];
        const metadata = [];
        // Generate benign samples
        for (let i = 0; i < 100; i++) {
            const feature = this.generateBenignFeatures();
            features.push(feature);
            labels.push([1, 0, 0, 0]); // One-hot encoding for benign
            metadata.push({
                threatType: 'benign',
                severity: 'low',
                source: 'synthetic',
                timestamp: new Date().toISOString()
            });
        }
        // Generate malicious samples
        for (let i = 0; i < 50; i++) {
            const feature = this.generateMaliciousFeatures();
            features.push(feature);
            labels.push([0, 0, 1, 0]); // One-hot encoding for malicious
            metadata.push({
                threatType: 'malicious',
                severity: 'high',
                source: 'synthetic',
                timestamp: new Date().toISOString()
            });
        }
        const trainingData = {
            features,
            labels,
            metadata
        };
        // Save the generated data
        this.saveTrainingData(trainingData);
        return trainingData;
    }
    generateBenignFeatures() {
        // Simulate normal system behavior
        return [
            Math.random() * 0.3, // System calls
            Math.random() * 0.4, // Network activity
            Math.random() * 0.2, // File operations
            Math.random() * 0.1, // Privilege escalation
            Math.random() * 0.3, // Memory usage
            Math.random() * 0.2, // CPU usage
            Math.random() * 0.1, // Process creation
            Math.random() * 0.2, // Registry access
            Math.random() * 0.1, // API calls
            Math.random() * 0.2 // Time patterns
        ];
    }
    generateMaliciousFeatures() {
        // Simulate malicious behavior
        return [
            0.7 + Math.random() * 0.3, // High system calls
            0.6 + Math.random() * 0.4, // High network activity
            0.5 + Math.random() * 0.5, // High file operations
            0.4 + Math.random() * 0.6, // High privilege escalation
            0.6 + Math.random() * 0.4, // High memory usage
            0.5 + Math.random() * 0.5, // High CPU usage
            0.4 + Math.random() * 0.6, // High process creation
            0.3 + Math.random() * 0.7, // High registry access
            0.4 + Math.random() * 0.6, // High API calls
            0.5 + Math.random() * 0.5 // Suspicious time patterns
        ];
    }
    saveTrainingData(data) {
        try {
            const dir = path.dirname(this.trainingDataPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(this.trainingDataPath, JSON.stringify(data, null, 2));
            console.log('[ML] Training data saved to:', this.trainingDataPath);
        }
        catch (error) {
            console.error('[ML] Failed to save training data:', error);
        }
    }
    async updateModel(newData) {
        // Load existing data
        const existingData = await this.loadTrainingData();
        // Combine with new data
        const combinedData = {
            features: [...existingData.features, ...newData.features],
            labels: [...existingData.labels, ...newData.labels],
            metadata: [...existingData.metadata, ...newData.metadata]
        };
        // Retrain the model
        await this.train(combinedData);
        console.log('[ML] Model updated with new data');
    }
    getModelInfo() {
        if (!this.model) {
            return { error: 'Model not initialized' };
        }
        return {
            inputShape: this.model.inputs[0].shape,
            outputShape: this.model.outputs[0].shape,
            layersCount: this.model.layers.length,
            parameters: this.model.countParams(),
            config: this.config,
            isTraining: this.isTraining
        };
    }
    async evaluate(testData) {
        if (!this.model) {
            throw new Error('Model not initialized');
        }
        const features = tf.tensor2d(testData.features);
        const labels = tf.tensor2d(testData.labels);
        const evaluation = this.model.evaluate(features, labels);
        const results = await Promise.all(evaluation.map(tensor => tensor.data()));
        // Clean up tensors
        features.dispose();
        labels.dispose();
        evaluation.forEach(tensor => tensor.dispose());
        return {
            loss: results[0][0],
            accuracy: results[1][0],
            precision: results[2]?.[0] || 0,
            recall: results[3]?.[0] || 0
        };
    }
}
exports.RealNeuralNetworkDetector = RealNeuralNetworkDetector;
class FeatureExtractor {
    async extractFeatures(execution) {
        const features = [];
        // System call features
        features.push(this.extractSystemCallFeatures(execution));
        // Network activity features
        features.push(this.extractNetworkFeatures(execution));
        // File system features
        features.push(this.extractFileSystemFeatures(execution));
        // Memory features
        features.push(this.extractMemoryFeatures(execution));
        // Process features
        features.push(this.extractProcessFeatures(execution));
        // Time-based features
        features.push(this.extractTimeFeatures(execution));
        // API call features
        features.push(this.extractAPIFeatures(execution));
        // Registry features
        features.push(this.extractRegistryFeatures(execution));
        // Privilege escalation features
        features.push(this.extractPrivilegeFeatures(execution));
        // Behavioral pattern features
        features.push(this.extractBehavioralFeatures(execution));
        return features;
    }
    extractSystemCallFeatures(execution) {
        // Analyze system call patterns
        const syscalls = execution.systemCalls || [];
        const suspiciousCalls = syscalls.filter(call => call.name.includes('exec') ||
            call.name.includes('ptrace') ||
            call.name.includes('mprotect'));
        return suspiciousCalls.length / Math.max(syscalls.length, 1);
    }
    extractNetworkFeatures(execution) {
        // Analyze network activity
        const network = execution.networkActivity || [];
        const suspiciousConnections = network.filter(conn => conn.destinationPort === 4444 || // Common backdoor port
            conn.destinationPort === 8080 ||
            conn.protocol === 'unknown');
        return suspiciousConnections.length / Math.max(network.length, 1);
    }
    extractFileSystemFeatures(execution) {
        // Analyze file system operations
        const fileOps = execution.fileChanges || [];
        const suspiciousOps = fileOps.filter(op => op.path.includes('/etc/') ||
            op.path.includes('/root/') ||
            op.operation === 'delete');
        return suspiciousOps.length / Math.max(fileOps.length, 1);
    }
    extractMemoryFeatures(execution) {
        // Analyze memory usage patterns
        const memory = execution.memoryUsage || { peak: 0, average: 0 };
        const suspiciousMemory = memory.peak > 100 * 1024 * 1024; // > 100MB
        return suspiciousMemory ? 1.0 : memory.average / (100 * 1024 * 1024);
    }
    extractProcessFeatures(execution) {
        // Analyze process creation patterns
        const processes = execution.processesCreated || [];
        const suspiciousProcesses = processes.filter(proc => proc.name.includes('sh') ||
            proc.name.includes('bash') ||
            proc.name.includes('cmd'));
        return suspiciousProcesses.length / Math.max(processes.length, 1);
    }
    extractTimeFeatures(execution) {
        // Analyze timing patterns
        const duration = execution.duration || 0;
        const suspiciousTiming = duration < 1000 || duration > 300000; // < 1s or > 5min
        return suspiciousTiming ? 1.0 : duration / 300000;
    }
    extractAPIFeatures(execution) {
        // Analyze API call patterns
        const apis = execution.apiCalls || [];
        const suspiciousAPIs = apis.filter(api => api.includes('CreateProcess') ||
            api.includes('VirtualAlloc') ||
            api.includes('SetWindowsHookEx'));
        return suspiciousAPIs.length / Math.max(apis.length, 1);
    }
    extractRegistryFeatures(execution) {
        // Analyze registry access patterns
        const registry = execution.registryAccess || [];
        const suspiciousKeys = registry.filter(key => key.includes('Run') ||
            key.includes('Startup') ||
            key.includes('Services'));
        return suspiciousKeys.length / Math.max(registry.length, 1);
    }
    extractPrivilegeFeatures(execution) {
        // Analyze privilege escalation attempts
        const privileges = execution.privilegeEscalation || [];
        const suspiciousPrivileges = privileges.filter(priv => priv.includes('admin') ||
            priv.includes('root') ||
            priv.includes('SYSTEM'));
        return suspiciousPrivileges.length / Math.max(privileges.length, 1);
    }
    extractBehavioralFeatures(execution) {
        // Analyze overall behavioral patterns
        const anomalies = execution.anomalies || [];
        const highSeverityAnomalies = anomalies.filter(anomaly => anomaly.severity === 'high' ||
            anomaly.severity === 'critical');
        return highSeverityAnomalies.length / Math.max(anomalies.length, 1);
    }
}
//# sourceMappingURL=RealNeuralNetworkDetector.js.map