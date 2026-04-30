#!/usr/bin/env python3
"""
RSecure Reinforcement Learning Security Module
Implements reinforcement learning for adaptive security decision making
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import threading
import time
import json
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from collections import deque, defaultdict
import random
from dataclasses import dataclass

@dataclass
class SecurityState:
    """Security environment state"""
    system_resources: np.ndarray
    network_activity: np.ndarray
    process_behavior: np.ndarray
    threat_indicators: np.ndarray
    vulnerability_context: np.ndarray
    historical_performance: np.ndarray

@dataclass
class SecurityAction:
    """Security action that can be taken"""
    action_id: int
    action_name: str
    resource_cost: float
    effectiveness_potential: float
    risk_level: float

class RSecureReinforcementLearning:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Environment setup
        self.state_dim = self.config['state_dim']
        self.action_dim = self.config['action_dim']
        
        # Define security actions
        self.actions = self._define_security_actions()
        
        # RL components
        self.q_network = None
        self.target_network = None
        self.memory = deque(maxlen=self.config['memory_size'])
        self.epsilon = self.config['epsilon_start']
        self.epsilon_decay = self.config['epsilon_decay']
        self.epsilon_min = self.config['epsilon_min']
        
        # Training parameters
        self.gamma = self.config['gamma']
        self.learning_rate = self.config['learning_rate']
        self.batch_size = self.config['batch_size']
        self.target_update_freq = self.config['target_update_freq']
        
        # Performance tracking
        self.training_history = []
        self.action_history = deque(maxlen=1000)
        self.reward_history = deque(maxlen=1000)
        
        # Threading
        self.training_thread = None
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_rl')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./reinforcement_learning.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize networks
        self._initialize_networks()
        
        # Load existing model if available
        self._load_model()
    
    def _get_default_config(self) -> Dict:
        return {
            'state_dim': 128,
            'action_dim': 20,
            'memory_size': 10000,
            'epsilon_start': 1.0,
            'epsilon_decay': 0.995,
            'epsilon_min': 0.01,
            'gamma': 0.95,
            'learning_rate': 0.001,
            'batch_size': 32,
            'target_update_freq': 100,
            'training_interval': 10,
            'save_interval': 100,
            'model_path': './rl_models',
            'min_experiences': 1000
        }
    
    def _define_security_actions(self) -> List[SecurityAction]:
        """Define available security actions"""
        return [
            SecurityAction(0, "monitor_only", 0.1, 0.3, 0.0),
            SecurityAction(1, "log_alert", 0.2, 0.5, 0.1),
            SecurityAction(2, "block_ip_temporarily", 0.4, 0.7, 0.2),
            SecurityAction(3, "block_permanently", 0.6, 0.8, 0.4),
            SecurityAction(4, "kill_process", 0.7, 0.9, 0.5),
            SecurityAction(5, "quarantine_file", 0.5, 0.8, 0.3),
            SecurityAction(6, "isolate_system", 0.9, 0.95, 0.8),
            SecurityAction(7, "restart_service", 0.3, 0.6, 0.2),
            SecurityAction(8, "update_firewall_rules", 0.4, 0.7, 0.3),
            SecurityAction(9, "increase_monitoring", 0.2, 0.4, 0.1),
            SecurityAction(10, "request_human_intervention", 0.1, 0.3, 0.0),
            SecurityAction(11, "scan_for_malware", 0.3, 0.6, 0.2),
            SecurityAction(12, "patch_vulnerability", 0.5, 0.8, 0.3),
            SecurityAction(13, "backup_critical_data", 0.4, 0.5, 0.1),
            SecurityAction(14, "disable_compromised_service", 0.6, 0.8, 0.4),
            SecurityAction(15, "enable_additional_logging", 0.2, 0.3, 0.0),
            SecurityAction(16, "throttle_network", 0.5, 0.6, 0.3),
            SecurityAction(17, "scan_internal_network", 0.4, 0.7, 0.2),
            SecurityAction(18, "update_signatures", 0.3, 0.5, 0.1),
            SecurityAction(19, "do_nothing", 0.0, 0.0, 0.0),
        ]
    
    def _initialize_networks(self):
        """Initialize Q-network and target network"""
        # Q-network
        self.q_network = self._build_q_network()
        
        # Target network
        self.target_network = self._build_q_network()
        self.update_target_network()
        
        # Optimizer
        self.optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        
        # Loss function
        self.loss_function = keras.losses.Huber()
    
    def _build_q_network(self) -> keras.Model:
        """Build deep Q-network"""
        # Input layer
        state_input = layers.Input(shape=(self.state_dim,))
        
        # Dense layers
        x = layers.Dense(256, activation='relu')(state_input)
        x = layers.Dropout(0.2)(x)
        x = layers.BatchNormalization()(x)
        
        x = layers.Dense(512, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        x = layers.BatchNormalization()(x)
        
        x = layers.Dense(256, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        x = layers.BatchNormalization()(x)
        
        # Dueling architecture
        # State value stream
        value_stream = layers.Dense(128, activation='relu')(x)
        value_stream = layers.Dense(1, activation='linear')(value_stream)
        
        # Advantage stream
        advantage_stream = layers.Dense(128, activation='relu')(x)
        advantage_stream = layers.Dense(self.action_dim, activation='linear')(advantage_stream)
        
        # Combine streams
        q_values = value_stream + (advantage_stream - tf.reduce_mean(advantage_stream, axis=1, keepdims=True))
        
        model = keras.Model(inputs=state_input, outputs=q_values)
        return model
    
    def update_target_network(self):
        """Update target network with Q-network weights"""
        self.target_network.set_weights(self.q_network.get_weights())
    
    def state_to_vector(self, state: SecurityState) -> np.ndarray:
        """Convert security state to vector representation"""
        # Combine all state components
        vector = np.concatenate([
            state.system_resources,
            state.network_activity,
            state.process_behavior,
            state.threat_indicators,
            state.vulnerability_context,
            state.historical_performance
        ])
        
        # Ensure correct dimension
        if len(vector) < self.state_dim:
            vector = np.pad(vector, (0, self.state_dim - len(vector)))
        elif len(vector) > self.state_dim:
            vector = vector[:self.state_dim]
        
        return vector.astype(np.float32)
    
    def choose_action(self, state: SecurityState, training: bool = True) -> Tuple[int, SecurityAction]:
        """Choose action using epsilon-greedy policy"""
        state_vector = self.state_to_vector(state)
        state_vector = np.expand_dims(state_vector, axis=0)
        
        if training and random.random() < self.epsilon:
            # Explore: random action
            action_id = random.randint(0, self.action_dim - 1)
        else:
            # Exploit: best action
            q_values = self.q_network.predict(state_vector, verbose=0)
            action_id = np.argmax(q_values[0])
        
        return action_id, self.actions[action_id]
    
    def remember(self, state: SecurityState, action_id: int, reward: float, 
                 next_state: SecurityState, done: bool):
        """Store experience in replay memory"""
        state_vector = self.state_to_vector(state)
        next_state_vector = self.state_to_vector(next_state)
        
        experience = (state_vector, action_id, reward, next_state_vector, done)
        self.memory.append(experience)
    
    def calculate_reward(self, state: SecurityState, action: SecurityAction, 
                       next_state: SecurityState, outcome: Dict) -> float:
        """Calculate reward for action"""
        reward = 0.0
        
        # Base reward from outcome
        threat_reduction = outcome.get('threat_reduction', 0.0)
        system_impact = outcome.get('system_impact', 0.0)
        false_positive = outcome.get('false_positive', False)
        effectiveness = outcome.get('effectiveness', 0.0)
        
        # Reward for threat reduction
        reward += threat_reduction * 10.0
        
        # Penalty for system impact
        reward -= system_impact * 5.0
        
        # Penalty for false positives
        if false_positive:
            reward -= 20.0
        
        # Reward for effectiveness
        reward += effectiveness * 5.0
        
        # Cost-benefit analysis
        cost_penalty = action.resource_cost * 2.0
        reward -= cost_penalty
        
        # Bonus for appropriate risk level
        if action.risk_level <= 0.3 and effectiveness > 0.7:
            reward += 5.0  # Low risk, high effectiveness
        
        # Penalty for overkill
        if action.risk_level > 0.7 and threat_reduction < 0.3:
            reward -= 10.0  # High risk, low effectiveness
        
        return reward
    
    def replay(self):
        """Train the model using replay memory"""
        if len(self.memory) < self.config['min_experiences']:
            return
        
        # Sample batch
        minibatch = random.sample(self.memory, self.batch_size)
        
        # Prepare training data
        states = np.array([experience[0] for experience in minibatch])
        actions = np.array([experience[1] for experience in minibatch])
        rewards = np.array([experience[2] for experience in minibatch])
        next_states = np.array([experience[3] for experience in minibatch])
        dones = np.array([experience[4] for experience in minibatch])
        
        # Compute target Q-values
        target_q_values = self.q_network.predict(states, verbose=0)
        
        # Get next Q-values from target network
        next_q_values = self.target_network.predict(next_states, verbose=0)
        max_next_q = np.max(next_q_values, axis=1)
        
        # Update targets
        for i in range(self.batch_size):
            if dones[i]:
                target_q_values[i, actions[i]] = rewards[i]
            else:
                target_q_values[i, actions[i]] = rewards[i] + self.gamma * max_next_q[i]
        
        # Train the model
        with tf.GradientTape() as tape:
            current_q_values = self.q_network(states)
            loss = self.loss_function(target_q_values, current_q_values)
        
        # Compute and apply gradients
        gradients = tape.gradient(loss, self.q_network.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.q_network.trainable_variables))
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # Record training
        self.training_history.append({
            'loss': float(loss),
            'epsilon': self.epsilon,
            'timestamp': datetime.now().isoformat()
        })
    
    def start_training(self):
        """Start continuous training"""
        if self.running:
            return
        
        self.running = True
        self.training_thread = threading.Thread(target=self._training_loop, daemon=True)
        self.training_thread.start()
        
        self.logger.info("RSecure reinforcement learning training started")
    
    def stop_training(self):
        """Stop training"""
        self.running = False
        if self.training_thread:
            self.training_thread.join(timeout=30)
        self.logger.info("RSecure reinforcement learning training stopped")
    
    def _training_loop(self):
        """Main training loop"""
        update_counter = 0
        
        while self.running:
            try:
                # Perform replay training
                self.replay()
                
                # Update target network
                update_counter += 1
                if update_counter >= self.target_update_freq:
                    self.update_target_network()
                    update_counter = 0
                    self.logger.debug("Target network updated")
                
                # Save model periodically
                if len(self.training_history) % self.config['save_interval'] == 0:
                    self._save_model()
                
                time.sleep(self.config['training_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in training loop: {e}")
    
    def _save_model(self):
        """Save the trained model"""
        try:
            import os
            os.makedirs(self.config['model_path'], exist_ok=True)
            
            # Save Q-network
            self.q_network.save(f"{self.config['model_path']}/q_network.h5")
            
            # Save training history
            with open(f"{self.config['model_path']}/training_history.pkl", 'wb') as f:
                pickle.dump(self.training_history, f)
            
            # Save configuration
            config_data = {
                'epsilon': self.epsilon,
                'training_history': self.training_history[-100:],  # Last 100 entries
                'config': self.config
            }
            
            with open(f"{self.config['model_path']}/rl_config.json", 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Model saved to {self.config['model_path']}")
            
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load existing model if available"""
        try:
            import os
            
            if not os.path.exists(f"{self.config['model_path']}/q_network.h5"):
                self.logger.info("No existing model found, starting fresh")
                return
            
            # Load Q-network
            self.q_network = keras.models.load_model(f"{self.config['model_path']}/q_network.h5")
            
            # Load configuration
            if os.path.exists(f"{self.config['model_path']}/rl_config.json"):
                with open(f"{self.config['model_path']}/rl_config.json", 'r') as f:
                    config_data = json.load(f)
                    self.epsilon = config_data.get('epsilon', self.epsilon)
            
            # Update target network
            self.update_target_network()
            
            self.logger.info("Model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
    
    def get_action_recommendation(self, state: SecurityState, top_k: int = 3) -> List[Tuple[int, SecurityAction, float]]:
        """Get top-k action recommendations with Q-values"""
        state_vector = self.state_to_vector(state)
        state_vector = np.expand_dims(state_vector, axis=0)
        
        q_values = self.q_network.predict(state_vector, verbose=0)[0]
        
        # Get top actions
        top_indices = np.argsort(q_values)[::-1][:top_k]
        
        recommendations = []
        for action_id in top_indices:
            action = self.actions[action_id]
            q_value = q_values[action_id]
            recommendations.append((action_id, action, float(q_value)))
        
        return recommendations
    
    def evaluate_policy(self, test_states: List[SecurityState]) -> Dict:
        """Evaluate current policy on test states"""
        total_reward = 0.0
        action_counts = defaultdict(int)
        
        for state in test_states:
            action_id, action = self.choose_action(state, training=False)
            action_counts[action.action_name] += 1
            
            # Simulate outcome (simplified)
            simulated_reward = np.random.normal(0, 1)  # Placeholder
            total_reward += simulated_reward
        
        avg_reward = total_reward / len(test_states) if test_states else 0.0
        
        return {
            'average_reward': avg_reward,
            'action_distribution': dict(action_counts),
            'epsilon': self.epsilon,
            'training_samples': len(self.memory),
            'model_performance': self.training_history[-1] if self.training_history else None
        }
    
    def get_training_statistics(self) -> Dict:
        """Get training statistics"""
        if not self.training_history:
            return {'status': 'no_training_data'}
        
        recent_history = self.training_history[-100:]  # Last 100 entries
        
        losses = [entry['loss'] for entry in recent_history]
        epsilons = [entry['epsilon'] for entry in recent_history]
        
        return {
            'total_training_steps': len(self.training_history),
            'recent_average_loss': np.mean(losses) if losses else 0.0,
            'recent_min_loss': np.min(losses) if losses else 0.0,
            'recent_max_loss': np.max(losses) if losses else 0.0,
            'current_epsilon': self.epsilon,
            'memory_size': len(self.memory),
            'last_training': self.training_history[-1]['timestamp'] if self.training_history else None
        }

if __name__ == "__main__":
    # Example usage
    rl_agent = RSecureReinforcementLearning()
    rl_agent.start_training()
    
    # Create example state
    example_state = SecurityState(
        system_resources=np.random.rand(20),
        network_activity=np.random.rand(20),
        process_behavior=np.random.rand(20),
        threat_indicators=np.random.rand(20),
        vulnerability_context=np.random.rand(20),
        historical_performance=np.random.rand(28)
    )
    
    try:
        while True:
            # Get action recommendation
            recommendations = rl_agent.get_action_recommendation(example_state)
            print(f"Top recommendations: {recommendations}")
            
            # Get training statistics
            stats = rl_agent.get_training_statistics()
            print(f"Training stats: {stats}")
            
            time.sleep(30)
    except KeyboardInterrupt:
        rl_agent.stop_training()
