import * as tf from '@tensorflow/tfjs-node';
import { EventEmitter } from 'events';
import { SandboxExecution } from '../security/types';
export interface NeuralNetworkConfig {
    inputSize: number;
    hiddenLayers: number[];
    outputSize: number;
    activation: 'relu' | 'sigmoid' | 'tanh' | 'softmax';
    optimizer: 'adam' | 'sgd' | 'rmsprop';
    learningRate: number;
    dropout: number;
    batchSize: number;
    epochs: number;
    validationSplit: number;
}
export interface TrainingData {
    features: number[][];
    labels: number[][];
    metadata: {
        threatType: string;
        severity: 'low' | 'medium' | 'high' | 'critical';
        source: string;
        timestamp: string;
    }[];
}
export interface PredictionResult {
    threatLevel: number;
    confidence: number;
    threatType: string;
    features: number[];
    reasoning: string;
}
export declare class RealNeuralNetworkDetector extends EventEmitter {
    private model;
    private config;
    private isTraining;
    private trainingHistory;
    private featureExtractor;
    private modelPath;
    private trainingDataPath;
    constructor(config: NeuralNetworkConfig, modelPath: string, trainingDataPath: string);
    private initializeModel;
    private createModel;
    extractFeatures(execution: SandboxExecution): Promise<number[]>;
    predict(execution: SandboxExecution): Promise<PredictionResult>;
    private calculateThreatLevel;
    private classifyThreatType;
    private generateReasoning;
    train(trainingData: TrainingData): Promise<tf.History>;
    private saveModel;
    loadTrainingData(): Promise<TrainingData>;
    private generateInitialTrainingData;
    private generateBenignFeatures;
    private generateMaliciousFeatures;
    private saveTrainingData;
    updateModel(newData: TrainingData): Promise<void>;
    getModelInfo(): any;
    evaluate(testData: TrainingData): Promise<any>;
}
//# sourceMappingURL=RealNeuralNetworkDetector.d.ts.map