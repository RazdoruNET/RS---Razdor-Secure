#!/usr/bin/env python3
"""
RSecure Neural Security Core
Multi-layer specialized neural network with convolutions for security analysis
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers
from typing import Dict, List, Tuple, Optional, Any
import json
import pickle
import threading
import time
from datetime import datetime
from collections import deque
import logging

class RSecureNeuralCore:
    def __init__(self, model_dir: str = "./models", config: Dict = None):
        self.model_dir = model_dir
        self.config = config or self._get_default_config()
        
        # Create model directory
        import os
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize model components
        self.models = {}
        self.data_buffers = {
            'network': deque(maxlen=1000),
            'process': deque(maxlen=1000),
            'file': deque(maxlen=1000),
            'system': deque(maxlen=1000)
        }
        
        # Analysis results
        self.analysis_results = {
            'threat_level': 0.0,
            'anomalies': [],
            'predictions': {},
            'confidence_scores': {}
        }
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_neural')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(f'{model_dir}/neural_analysis.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize models
        self._initialize_models()
        
        # Analysis thread
        self.analysis_thread = None
        self.running = False
    
    def _get_default_config(self) -> Dict:
        return {
            'sequence_length': 50,
            'feature_dim': 64,
            'num_classes': 5,  # benign, suspicious, malicious, critical, unknown
            'learning_rate': 0.001,
            'batch_size': 32,
            'epochs': 100,
            'analysis_interval': 5,  # seconds
            'threat_threshold': 0.7,
            'ensemble_voting': 'weighted'
        }
    
    def _initialize_models(self):
        """Initialize specialized neural network models"""
        try:
            # Network traffic analyzer
            self.models['network'] = self._build_network_analyzer()
            
            # Process behavior analyzer
            self.models['process'] = self._build_process_analyzer()
            
            # File integrity analyzer
            self.models['file'] = self._build_file_analyzer()
            
            # System state analyzer
            self.models['system'] = self._build_system_analyzer()
            
            # Ensemble model for final decision
            self.models['ensemble'] = self._build_ensemble_model()
            
            # Load pre-trained weights if available
            self._load_models()
            
            self.logger.info("RSecure neural models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing neural models: {e}")
            # Create dummy models as fallback
            self._create_fallback_models()
    
    def _build_network_analyzer(self) -> keras.Model:
        """Build specialized network traffic analyzer with 1D convolutions"""
        # Input: sequence of network features
        input_layer = layers.Input(shape=(self.config['sequence_length'], self.config['feature_dim']))
        
        # First convolutional block - temporal patterns
        x = layers.Conv1D(64, 3, activation='relu', padding='same')(input_layer)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        x = layers.Dropout(0.2)(x)
        
        # Second convolutional block - protocol patterns
        x = layers.Conv1D(128, 5, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        x = layers.Dropout(0.3)(x)
        
        # Third convolutional block - traffic patterns
        x = layers.Conv1D(256, 7, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.GlobalMaxPooling1D()(x)
        x = layers.Dropout(0.4)(x)
        
        # Dense layers for classification
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.5)(x)
        
        # Output: threat classification
        output = layers.Dense(self.config['num_classes'], activation='softmax', name='network_output')(x)
        
        model = keras.Model(inputs=input_layer, outputs=output)
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_process_analyzer(self) -> keras.Model:
        """Build specialized process behavior analyzer"""
        # Input: process features sequence
        input_layer = layers.Input(shape=(self.config['sequence_length'], self.config['feature_dim']))
        
        # LSTM for temporal process behavior
        x = layers.LSTM(64, return_sequences=True)(input_layer)
        x = layers.Dropout(0.2)(x)
        
        # Conv1D for pattern extraction
        x = layers.Conv1D(128, 3, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        
        # Attention mechanism
        attention = layers.MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
        x = layers.Add()([x, attention])
        x = layers.LayerNormalization()(x)
        
        # Global pooling
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.3)(x)
        
        # Dense layers
        x = layers.Dense(64, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.4)(x)
        
        # Output
        output = layers.Dense(self.config['num_classes'], activation='softmax', name='process_output')(x)
        
        model = keras.Model(inputs=input_layer, outputs=output)
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_file_analyzer(self) -> keras.Model:
        """Build specialized file integrity analyzer"""
        # Input: file change patterns
        input_layer = layers.Input(shape=(self.config['sequence_length'], self.config['feature_dim']))
        
        # 1D convolutions for file pattern detection
        x = layers.Conv1D(32, 3, activation='relu', padding='same')(input_layer)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        
        # Deeper convolutions for fine-grained patterns
        x = layers.Conv1D(64, 5, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv1D(64, 5, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        
        # Residual connection
        residual = x
        x = layers.Conv1D(64, 3, activation='relu', padding='same')(x)
        x = layers.Add()([x, residual])
        x = layers.LayerNormalization()(x)
        
        # Global features
        x = layers.GlobalMaxPooling1D()(x)
        x = layers.Dropout(0.3)(x)
        
        # Dense layers
        x = layers.Dense(32, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.4)(x)
        
        # Output
        output = layers.Dense(self.config['num_classes'], activation='softmax', name='file_output')(x)
        
        model = keras.Model(inputs=input_layer, outputs=output)
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_system_analyzer(self) -> keras.Model:
        """Build specialized system state analyzer"""
        # Input: system metrics
        input_layer = layers.Input(shape=(self.config['sequence_length'], self.config['feature_dim']))
        
        # Temporal convolutions
        x = layers.Conv1D(48, 7, activation='relu', padding='same')(input_layer)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(2)(x)
        
        # Dilated convolutions for long-range patterns
        x = layers.Conv1D(96, 3, dilation_rate=2, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv1D(96, 3, dilation_rate=4, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        
        # Self-attention
        attention = layers.MultiHeadAttention(num_heads=3, key_dim=32)(x, x)
        x = layers.Add()([x, attention])
        x = layers.LayerNormalization()(x)
        
        # Feature extraction
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.3)(x)
        
        # Dense layers
        x = layers.Dense(48, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.4)(x)
        
        # Output
        output = layers.Dense(self.config['num_classes'], activation='softmax', name='system_output')(x)
        
        model = keras.Model(inputs=input_layer, outputs=output)
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_ensemble_model(self) -> keras.Model:
        """Build ensemble model combining all specialized models"""
        # Inputs from all specialized models
        network_input = layers.Input(shape=(self.config['num_classes'],), name='network_features')
        process_input = layers.Input(shape=(self.config['num_classes'],), name='process_features')
        file_input = layers.Input(shape=(self.config['num_classes'],), name='file_features')
        system_input = layers.Input(shape=(self.config['num_classes'],), name='system_features')
        
        # Concatenate all features
        combined = layers.Concatenate()([network_input, process_input, file_input, system_input])
        
        # Meta-learner layers
        x = layers.Dense(64, activation='relu')(combined)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(32, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        # Final output
        output = layers.Dense(self.config['num_classes'], activation='softmax', name='final_output')(x)
        
        model = keras.Model(
            inputs=[network_input, process_input, file_input, system_input],
            outputs=output
        )
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
    
    def _load_models(self):
        """Load pre-trained model weights"""
        try:
            for model_name, model in self.models.items():
                if model is not None:
                    model_path = f"{self.model_dir}/{model_name}_weights.h5"
                    if os.path.exists(model_path):
                        model.load_weights(model_path)
                        self.logger.info(f"Loaded weights for {model_name} model")
        except Exception as e:
            self.logger.error(f"Error loading model weights: {e}")
    
    def save_models(self):
        """Save model weights"""
        try:
            for model_name, model in self.models.items():
                if model is not None:
                    model_path = f"{self.model_dir}/{model_name}_weights.h5"
                    model.save_weights(model_path)
                    self.logger.info(f"Saved weights for {model_name} model")
        except Exception as e:
            self.logger.error(f"Error saving model weights: {e}")
    
    def start_analysis(self):
        """Start continuous analysis thread"""
        if self.running:
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        self.logger.info("RSecure neural analysis started")
    
    def stop_analysis(self):
        """Stop analysis thread"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=10)
        self.logger.info("RSecure neural analysis stopped")
    
    def _analysis_loop(self):
        """Main analysis loop"""
        while self.running:
            try:
                # Analyze each data type
                network_result = self._analyze_data_type('network')
                process_result = self._analyze_data_type('process')
                file_result = self._analyze_data_type('file')
                system_result = self._analyze_data_type('system')
                
                # Ensemble decision
                ensemble_result = self._ensemble_decision([
                    network_result, process_result, file_result, system_result
                ])
                
                # Update analysis results
                self.analysis_results.update({
                    'timestamp': datetime.now().isoformat(),
                    'network_analysis': network_result,
                    'process_analysis': process_result,
                    'file_analysis': file_result,
                    'system_analysis': system_result,
                    'ensemble_result': ensemble_result,
                    'threat_level': ensemble_result.get('threat_score', 0.0)
                })
                
                # Log high threat levels
                if ensemble_result.get('threat_score', 0) > self.config['threat_threshold']:
                    self.logger.warning(f"High threat detected: {ensemble_result}")
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
            
            time.sleep(self.config['analysis_interval'])
    
    def _analyze_data_type(self, data_type: str) -> Dict:
        """Analyze specific data type"""
        try:
            buffer = self.data_buffers[data_type]
            if len(buffer) < self.config['sequence_length']:
                return {'status': 'insufficient_data', 'threat_score': 0.0}
            
            # Prepare data
            data = np.array(list(buffer)[-self.config['sequence_length']:])
            if data.shape[1] != self.config['feature_dim']:
                # Pad or truncate features
                if data.shape[1] < self.config['feature_dim']:
                    padding = np.zeros((data.shape[0], self.config['feature_dim'] - data.shape[1]))
                    data = np.hstack([data, padding])
                else:
                    data = data[:, :self.config['feature_dim']]
            
            # Reshape for model
            data = data.reshape(1, self.config['sequence_length'], self.config['feature_dim'])
            
            # Get prediction
            model = self.models[data_type]
            if model is not None:
                prediction = model.predict(data, verbose=0)[0]
                threat_class = np.argmax(prediction)
                threat_score = prediction[2] + prediction[3]  # malicious + critical
                
                return {
                    'status': 'success',
                    'prediction': prediction.tolist(),
                    'threat_class': int(threat_class),
                    'threat_score': float(threat_score),
                    'confidence': float(np.max(prediction))
                }
            else:
                # Fallback rule-based analysis
                return self._fallback_analysis(data_type, data)
                
        except Exception as e:
            self.logger.error(f"Error analyzing {data_type} data: {e}")
            return {'status': 'error', 'threat_score': 0.0}
    
    def _fallback_analysis(self, data_type: str, data: np.ndarray) -> Dict:
        """Fallback rule-based analysis"""
        # Simple statistical analysis
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        # Simple heuristic
        threat_score = min(1.0, (std_val / (mean_val + 1e-6)) * 0.1)
        
        return {
            'status': 'fallback',
            'threat_score': float(threat_score),
            'confidence': 0.5,
            'mean': float(mean_val),
            'std': float(std_val)
        }
    
    def _ensemble_decision(self, results: List[Dict]) -> Dict:
        """Combine results from all models"""
        valid_results = [r for r in results if r.get('status') == 'success']
        
        if not valid_results:
            return {'status': 'no_valid_results', 'threat_score': 0.0}
        
        # Weighted voting based on confidence
        total_weight = 0
        weighted_threat = 0
        
        for result in valid_results:
            confidence = result.get('confidence', 0.5)
            threat_score = result.get('threat_score', 0.0)
            
            weight = confidence ** 2  # Square confidence for emphasis
            total_weight += weight
            weighted_threat += threat_score * weight
        
        if total_weight > 0:
            final_threat = weighted_threat / total_weight
        else:
            final_threat = 0.0
        
        # Determine threat level
        if final_threat > 0.8:
            threat_level = 'critical'
        elif final_threat > 0.6:
            threat_level = 'malicious'
        elif final_threat > 0.4:
            threat_level = 'suspicious'
        elif final_threat > 0.2:
            threat_level = 'benign'
        else:
            threat_level = 'safe'
        
        return {
            'status': 'success',
            'threat_score': float(final_threat),
            'threat_level': threat_level,
            'confidence': float(total_weight / len(valid_results)),
            'individual_results': valid_results
        }
    
    def add_data(self, data_type: str, features: np.ndarray):
        """Add data for analysis"""
        if data_type in self.data_buffers:
            # Ensure features have correct dimension
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            # Add each feature vector to buffer
            for feature in features:
                self.data_buffers[data_type].append(feature)
    
    def get_analysis_results(self) -> Dict:
        """Get current analysis results"""
        return self.analysis_results.copy()
    
    def train_models(self, training_data: Dict):
        """Train models with provided data"""
        try:
            for data_type, (X, y) in training_data.items():
                if data_type in self.models and self.models[data_type] is not None:
                    self.logger.info(f"Training {data_type} model...")
                    self.models[data_type].fit(
                        X, y,
                        batch_size=self.config['batch_size'],
                        epochs=self.config['epochs'],
                        validation_split=0.2,
                        verbose=1
                    )
            
            # Save trained models
            self.save_models()
            self.logger.info("Model training completed")
            
        except Exception as e:
            self.logger.error(f"Error training models: {e}")

# Feature extraction utilities
class FeatureExtractor:
    @staticmethod
    def extract_network_features(connection_data: Dict) -> np.ndarray:
        """Extract features from network connection data"""
        features = []
        
        # Basic connection features
        features.append(connection_data.get('remote_port', 0) / 65535)
        features.append(connection_data.get('local_port', 0) / 65535)
        features.append(1 if connection_data.get('status') == 'ESTABLISHED' else 0)
        
        # Protocol features
        protocol = connection_data.get('protocol', 'tcp').lower()
        features.append(1 if protocol == 'tcp' else 0)
        features.append(1 if protocol == 'udp' else 0)
        features.append(1 if protocol == 'icmp' else 0)
        
        # Address features
        remote_ip = connection_data.get('remote_address', '').split(':')[0]
        features.append(1 if remote_ip.startswith('192.168.') else 0)  # Private IP
        features.append(1 if remote_ip.startswith('10.') else 0)  # Private IP
        features.append(1 if remote_ip.startswith('172.') else 0)  # Private IP
        
        # Process features
        features.append(len(connection_data.get('process_name', '')) / 50)
        features.append(len(connection_data.get('cmdline', [])) / 10)
        
        # Pad to required dimension
        while len(features) < 64:
            features.append(0.0)
        
        return np.array(features[:64])
    
    @staticmethod
    def extract_process_features(process_data: Dict) -> np.ndarray:
        """Extract features from process data"""
        features = []
        
        # CPU and memory usage
        features.append(process_data.get('cpu_percent', 0) / 100)
        features.append(process_data.get('memory_percent', 0) / 100)
        features.append(process_data.get('memory_rss', 0) / (1024**3))  # GB
        
        # Process characteristics
        features.append(len(process_data.get('name', '')) / 50)
        features.append(len(process_data.get('cmdline', [])) / 20)
        features.append(process_data.get('pid', 0) / 32768)
        features.append(process_data.get('parent_pid', 0) / 32768)
        
        # User information
        user = process_data.get('user', '')
        features.append(1 if 'root' in user.lower() else 0)
        features.append(1 if 'admin' in user.lower() else 0)
        features.append(1 if 'system' in user.lower() else 0)
        
        # Process type indicators
        name = process_data.get('name', '').lower()
        suspicious_processes = ['nc', 'netcat', 'telnet', 'ftp', 'wget', 'curl']
        for proc in suspicious_processes:
            features.append(1 if proc in name else 0)
        
        # Pad to required dimension
        while len(features) < 64:
            features.append(0.0)
        
        return np.array(features[:64])
    
    @staticmethod
    def extract_file_features(file_data: Dict) -> np.ndarray:
        """Extract features from file integrity data"""
        features = []
        
        # File characteristics
        features.append(len(file_data.get('file_path', '')) / 200)
        features.append(file_data.get('size', 0) / (1024**2))  # MB
        
        # Path characteristics
        path = file_data.get('file_path', '').lower()
        critical_paths = ['/etc/', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/', '/system/']
        for critical_path in critical_paths:
            features.append(1 if critical_path in path else 0)
        
        # File type indicators
        extensions = ['.exe', '.sh', '.py', '.pl', '.rb', '.conf', '.cfg', '.ini']
        for ext in extensions:
            features.append(1 if path.endswith(ext) else 0)
        
        # Hash characteristics (simplified)
        file_hash = file_data.get('hash', '')
        features.append(len(file_hash) / 64)
        
        # Event type
        event = file_data.get('event', '').lower()
        features.append(1 if event == 'modified' else 0)
        features.append(1 if event == 'created' else 0)
        features.append(1 if event == 'deleted' else 0)
        
        # Pad to required dimension
        while len(features) < 64:
            features.append(0.0)
        
        return np.array(features[:64])
    
    @staticmethod
    def extract_system_features(system_data: Dict) -> np.ndarray:
        """Extract features from system data"""
        features = []
        
        # System resources
        features.append(system_data.get('cpu_percent', 0) / 100)
        features.append(system_data.get('memory_percent', 0) / 100)
        features.append(system_data.get('disk_percent', 0) / 100)
        
        # Load average
        load_avg = system_data.get('load_average', [0, 0, 0])
        features.append(load_avg[0] / 10 if len(load_avg) > 0 else 0)
        features.append(load_avg[1] / 10 if len(load_avg) > 1 else 0)
        features.append(load_avg[2] / 10 if len(load_avg) > 2 else 0)
        
        # Network traffic
        features.append(system_data.get('bytes_sent', 0) / (1024**3))  # GB
        features.append(system_data.get('bytes_recv', 0) / (1024**3))  # GB
        features.append(system_data.get('packets_sent', 0) / 1000000)
        features.append(system_data.get('packets_recv', 0) / 1000000)
        
        # Process count
        features.append(system_data.get('process_count', 0) / 1000)
        features.append(system_data.get('connection_count', 0) / 1000)
        
        # Time-based features
        import time
        current_time = time.time()
        features.append((current_time % 86400) / 86400)  # Time of day
        features.append((current_time % 604800) / 604800)  # Day of week
        
        # Pad to required dimension
        while len(features) < 64:
            features.append(0.0)
        
        return np.array(features[:64])

if __name__ == "__main__":
    # Example usage
    neural_core = RSecureNeuralCore()
    neural_core.start_analysis()
    
    # Example data
    network_data = {
        'remote_port': 443,
        'local_port': 54321,
        'status': 'ESTABLISHED',
        'protocol': 'tcp',
        'remote_address': '192.168.1.100:443',
        'process_name': 'chrome',
        'cmdline': ['chrome', '--no-sandbox']
    }
    
    # Extract and add features
    features = FeatureExtractor.extract_network_features(network_data)
    neural_core.add_data('network', features)
    
    try:
        while True:
            results = neural_core.get_analysis_results()
            print(f"Threat Level: {results.get('threat_level', 'unknown')}")
            time.sleep(10)
    except KeyboardInterrupt:
        neural_core.stop_analysis()
