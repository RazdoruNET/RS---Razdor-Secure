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
exports.SelfLearningSystem = void 0;
const uuid_1 = require("uuid");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class SelfLearningSystem {
    constructor(config) {
        this.learningData = [];
        this.techniquePerformance = new Map();
        this.signaturePerformance = new Map();
        this.config = config;
        this.metrics = this.initializeMetrics();
        this.loadLearningData();
    }
    async processExecution(execution, analysisResult) {
        // Store learning data point
        const dataPoint = {
            id: (0, uuid_1.v4)(),
            timestamp: new Date().toISOString(),
            executionId: execution.id,
            sampleId: execution.sampleId,
            riskScore: analysisResult.riskScore,
            techniques: analysisResult.techniques,
            anomalies: analysisResult.anomalies,
            signatures: analysisResult.signatures,
            behaviorComplexity: analysisResult.behaviorGraph.length
        };
        this.learningData.push(dataPoint);
        this.updateMetrics(dataPoint);
        // Update technique performance
        this.updateTechniquePerformance(analysisResult.techniques);
        // Update signature performance
        this.updateSignaturePerformance(analysisResult.signatures);
        // Trigger learning if enough data
        if (this.learningData.length >= this.config.minSamplesForLearning) {
            await this.triggerLearningCycle();
        }
        // Save learning data periodically
        if (this.learningData.length % 10 === 0) {
            await this.saveLearningData();
        }
    }
    async evolveTechniques(techniques) {
        if (!this.config.enableTechniqueLearning) {
            return { evolved: false, changes: [], confidence: 0, newVersion: '1.0.0' };
        }
        const evolvedTechniques = [];
        const changes = [];
        for (const technique of techniques) {
            const performance = this.techniquePerformance.get(technique.id);
            if (performance && performance.successRate < 0.6) {
                // Technique needs improvement
                const evolved = await this.evolveTechnique(technique, performance);
                if (evolved) {
                    evolvedTechniques.push(evolved);
                    changes.push(`Evolved technique: ${technique.name}`);
                }
            }
            else {
                evolvedTechniques.push(technique);
            }
        }
        const confidence = changes.length > 0 ? this.calculateEvolutionConfidence(changes) : 0;
        return {
            evolved: changes.length > 0,
            changes,
            confidence,
            newVersion: this.generateVersionNumber()
        };
    }
    async evolveSignatures(signatures) {
        if (!this.config.enableSignatureEvolution) {
            return { evolved: false, changes: [], confidence: 0, newVersion: '1.0.0' };
        }
        const evolvedSignatures = [];
        const changes = [];
        for (const signature of signatures) {
            const performance = this.signaturePerformance.get(signature.id);
            if (performance && performance.falsePositiveRate > 0.3) {
                // Signature needs refinement
                const evolved = await this.evolveSignature(signature, performance);
                if (evolved) {
                    evolvedSignatures.push(evolved);
                    changes.push(`Refined signature: ${signature.name}`);
                }
            }
            else {
                evolvedSignatures.push(signature);
            }
        }
        const confidence = changes.length > 0 ? this.calculateEvolutionConfidence(changes) : 0;
        return {
            evolved: changes.length > 0,
            changes,
            confidence,
            newVersion: this.generateVersionNumber()
        };
    }
    async optimizeGeneration(templates) {
        if (!this.config.enableAdaptiveGeneration) {
            return templates;
        }
        const optimizedTemplates = [];
        for (const template of templates) {
            const optimization = await this.optimizeTemplate(template);
            optimizedTemplates.push(optimization);
        }
        return optimizedTemplates;
    }
    async evolveTechnique(technique, performance) {
        // Analyze failure patterns and improve technique
        const evolved = { ...technique };
        // Add new patterns based on learning data
        const newPatterns = this.generateNewPatterns(technique, performance);
        if (newPatterns.length > 0) {
            evolved.syscallPatterns = [...evolved.syscallPatterns, ...newPatterns.syscall];
            evolved.networkPatterns = [...evolved.networkPatterns, ...newPatterns.network];
            evolved.filePatterns = [...evolved.filePatterns, ...newPatterns.file];
            return evolved;
        }
        return null;
    }
    async evolveSignature(signature, performance) {
        // Refine signature to reduce false positives
        const evolved = { ...signature };
        // Make pattern more specific
        if (performance.falsePositiveRate > 0.5) {
            evolved.pattern = this.makePatternMoreSpecific(signature.pattern);
            return evolved;
        }
        return null;
    }
    async optimizeTemplate(template) {
        // Optimize template based on performance metrics
        const optimized = { ...template };
        // Add successful evasion techniques
        const successfulTechniques = this.getSuccessfulEvasionTechniques(template.type);
        if (successfulTechniques.length > 0) {
            optimized.evasionTechniques = [...optimized.evasionTechniques, ...successfulTechniques];
        }
        return optimized;
    }
    generateNewPatterns(technique, performance) {
        const newPatterns = {
            syscall: [],
            network: [],
            file: []
        };
        // Analyze failed detections to generate new patterns
        const recentFailures = this.learningData
            .filter(dp => dp.riskScore > 50) // High risk but not detected
            .slice(-10);
        for (const failure of recentFailures) {
            // Extract patterns from failed detections
            // This is simplified - real implementation would use ML
            if (Math.random() < this.config.learningRate) {
                newPatterns.syscall.push(`new_syscall_${Date.now()}`);
                newPatterns.network.push(`new_network_${Date.now()}`);
                newPatterns.file.push(`new_file_${Date.now()}`);
            }
        }
        return newPatterns;
    }
    makePatternMoreSpecific(pattern) {
        // Add more specific constraints to reduce false positives
        // This is simplified - real implementation would use pattern analysis
        return pattern.replace(/\*/g, '[^\\s]*');
    }
    getSuccessfulEvasionTechniques(malwareType) {
        // Return evasion techniques that have been successful for this malware type
        // This would be based on historical performance data
        return [
            {
                id: 'learned-evasion-' + Date.now(),
                name: 'Learned Evasion Technique',
                description: 'Automatically learned evasion technique',
                implementation: '// Learned implementation',
                category: 'polymorphism'
            }
        ];
    }
    async triggerLearningCycle() {
        console.log('Triggering learning cycle...');
        // Perform various learning tasks
        await this.analyzeTrends();
        await this.updateModels();
        await this.generateInsights();
        // Reset learning data to prevent memory issues
        if (this.learningData.length > 1000) {
            this.learningData = this.learningData.slice(-500);
        }
    }
    async analyzeTrends() {
        // Analyze trends in threat evolution
        const recentData = this.learningData.slice(-50);
        // Calculate trend metrics
        const avgRisk = recentData.reduce((sum, dp) => sum + dp.riskScore, 0) / recentData.length;
        const techniqueDiversity = new Set(recentData.flatMap(dp => dp.techniques.map(t => t.id))).size;
        console.log(`Trend Analysis - Avg Risk: ${avgRisk.toFixed(2)}, Technique Diversity: ${techniqueDiversity}`);
    }
    async updateModels() {
        // Update internal models based on learning data
        // This would involve machine learning model updates
        console.log('Updating learning models...');
    }
    async generateInsights() {
        // Generate insights from learning data
        const insights = this.generateLearningInsights();
        console.log('Learning Insights:', insights);
    }
    generateLearningInsights() {
        const insights = [];
        // Analyze most common techniques
        const techniqueCounts = new Map();
        for (const dataPoint of this.learningData) {
            for (const technique of dataPoint.techniques) {
                techniqueCounts.set(technique.id, (techniqueCounts.get(technique.id) || 0) + 1);
            }
        }
        const topTechniques = Array.from(techniqueCounts.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
        insights.push(`Top techniques: ${topTechniques.map(([id, count]) => `${id} (${count})`).join(', ')}`);
        // Analyze risk trends
        const recentRisk = this.learningData.slice(-10).map(dp => dp.riskScore);
        const avgRecentRisk = recentRisk.reduce((sum, risk) => sum + risk, 0) / recentRisk.length;
        insights.push(`Recent average risk score: ${avgRecentRisk.toFixed(2)}`);
        return insights;
    }
    updateMetrics(dataPoint) {
        this.metrics.totalSamplesAnalyzed++;
        this.metrics.averageRiskScore = this.calculateAverageRiskScore();
        this.metrics.lastUpdateTime = new Date().toISOString();
    }
    updateTechniquePerformance(techniques) {
        for (const technique of techniques) {
            const performance = this.techniquePerformance.get(technique.id) || {
                techniqueId: technique.id,
                detectionCount: 0,
                successCount: 0,
                falsePositiveCount: 0,
                successRate: 0,
                lastUpdated: new Date().toISOString()
            };
            performance.detectionCount++;
            if (technique.confidence > 0.7) {
                performance.successCount++;
            }
            performance.successRate = performance.detectionCount > 0
                ? performance.successCount / performance.detectionCount
                : 0;
            performance.lastUpdated = new Date().toISOString();
            this.techniquePerformance.set(technique.id, performance);
        }
    }
    updateSignaturePerformance(signatures) {
        for (const signature of signatures) {
            const performance = this.signaturePerformance.get(signature.id) || {
                signatureId: signature.id,
                matchCount: 0,
                falsePositiveCount: 0,
                truePositiveCount: 0,
                falsePositiveRate: 0,
                precision: 0,
                lastUpdated: new Date().toISOString()
            };
            performance.matchCount++;
            if (signature.applicable) {
                performance.truePositiveCount++;
            }
            else {
                performance.falsePositiveCount++;
            }
            performance.falsePositiveRate = performance.matchCount > 0
                ? performance.falsePositiveCount / performance.matchCount
                : 0;
            performance.precision = performance.matchCount > 0
                ? performance.truePositiveCount / performance.matchCount
                : 0;
            performance.lastUpdated = new Date().toISOString();
            this.signaturePerformance.set(signature.id, performance);
        }
    }
    calculateAverageRiskScore() {
        if (this.learningData.length === 0)
            return 0;
        const totalRisk = this.learningData.reduce((sum, dp) => sum + dp.riskScore, 0);
        return totalRisk / this.learningData.length;
    }
    calculateEvolutionConfidence(changes) {
        // Calculate confidence based on amount of data and learning rate
        const dataFactor = Math.min(this.learningData.length / 100, 1.0);
        const changeFactor = Math.min(changes.length / 5, 1.0);
        return (dataFactor * this.config.learningRate + changeFactor * (1 - this.config.learningRate)) / 2;
    }
    generateVersionNumber() {
        // Generate semantic version based on evolution count
        const major = Math.floor(this.metrics.techniqueEvolutionCount / 10);
        const minor = this.metrics.techniqueEvolutionCount % 10;
        const patch = Math.floor(Math.random() * 10);
        return `${major}.${minor}.${patch}`;
    }
    initializeMetrics() {
        return {
            totalSamplesAnalyzed: 0,
            successfulDetections: 0,
            falsePositives: 0,
            falseNegatives: 0,
            averageRiskScore: 0,
            techniqueEvolutionCount: 0,
            signatureEvolutionCount: 0,
            lastUpdateTime: new Date().toISOString()
        };
    }
    loadLearningData() {
        try {
            if (fs.existsSync(this.config.modelPersistencePath)) {
                const data = fs.readFileSync(this.config.modelPersistencePath, 'utf8');
                const parsed = JSON.parse(data);
                this.learningData = parsed.learningData || [];
                this.metrics = parsed.metrics || this.metrics;
                // Load performance data
                if (parsed.techniquePerformance) {
                    this.techniquePerformance = new Map(Object.entries(parsed.techniquePerformance));
                }
                if (parsed.signaturePerformance) {
                    this.signaturePerformance = new Map(Object.entries(parsed.signaturePerformance));
                }
                console.log(`Loaded ${this.learningData.length} learning data points`);
            }
        }
        catch (error) {
            console.warn('Failed to load learning data:', error);
        }
    }
    async saveLearningData() {
        try {
            const dir = path.dirname(this.config.modelPersistencePath);
            if (!fs.existsSync(dir)) {
                await fs.promises.mkdir(dir, { recursive: true });
            }
            const data = {
                learningData: this.learningData,
                metrics: this.metrics,
                techniquePerformance: Object.fromEntries(this.techniquePerformance),
                signaturePerformance: Object.fromEntries(this.signaturePerformance),
                savedAt: new Date().toISOString()
            };
            await fs.promises.writeFile(this.config.modelPersistencePath, JSON.stringify(data, null, 2));
            console.log('Learning data saved successfully');
        }
        catch (error) {
            console.error('Failed to save learning data:', error);
        }
    }
    getMetrics() {
        return { ...this.metrics };
    }
    getLearningInsights() {
        return this.generateLearningInsights();
    }
    getTechniquePerformance() {
        return new Map(this.techniquePerformance);
    }
    getSignaturePerformance() {
        return new Map(this.signaturePerformance);
    }
    async reset() {
        this.learningData = [];
        this.techniquePerformance.clear();
        this.signaturePerformance.clear();
        this.metrics = this.initializeMetrics();
        try {
            if (fs.existsSync(this.config.modelPersistencePath)) {
                await fs.promises.unlink(this.config.modelPersistencePath);
            }
        }
        catch (error) {
            console.warn('Failed to reset learning data:', error);
        }
    }
}
exports.SelfLearningSystem = SelfLearningSystem;
//# sourceMappingURL=SelfLearningSystem.js.map