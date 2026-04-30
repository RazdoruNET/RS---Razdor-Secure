#!/usr/bin/env python3
"""
RSecure Main Integration Module
Integrates all RSecure components into unified security system
"""

import os
import sys
import time
import threading
import logging
import json
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import RSecure modules
from system_detector import SystemDetector
from monitoring_logger import RSecureLogger
from neural_security_core import RSecureNeuralCore, FeatureExtractor
from security_analytics import RSecureAnalytics, SecurityEvent
from system_control import RSecureSystemControl
from cvu_intelligence import RSecureCVU
from reinforcement_learning import RSecureReinforcementLearning, SecurityState, SecurityAction
from network_defense import RSecureNetworkDefense

class RSecureMain:
    """Main RSecure security system integration"""
    
    def __init__(self, config_path: str = "./rsecure_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup main logging first
        self._setup_logging()
        
        # Initialize components
        self.system_detector = None
        self.neural_core = None
        self.analytics = None
        self.system_control = None
        self.cvu_intelligence = None
        self.rl_agent = None
        self.network_defense = None
        
        # System state
        self.system_info = {}
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Component threads
        self.component_threads = []
        
        # Performance metrics
        self.metrics = {
            'start_time': datetime.now(),
            'events_processed': 0,
            'threats_detected': 0,
            'actions_taken': 0,
            'neural_predictions': 0,
            'rl_decisions': 0
        }
        
        self.logger.info("RSecure main system initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            'system_detection': {
                'enabled': True,
                'config_file': './system_config.json'
            },
            'monitoring': {
                'enabled': True,
                'log_dir': '/var/log/rsecure',
                'log_interval': 1,
                'network_scan_interval': 30,
                'file_scan_interval': 60
            },
            'neural_core': {
                'enabled': True,
                'model_dir': './models',
                'analysis_interval': 5,
                'threat_threshold': 0.7
            },
            'analytics': {
                'enabled': True,
                'db_path': './rsecure_analytics.db',
                'analysis_interval': 60
            },
            'system_control': {
                'enabled': True,
                'auto_kill_threshold': 0.9,
                'auto_block_threshold': 0.8,
                'quarantine_dir': './quarantine'
            },
            'cvu_intelligence': {
                'enabled': True,
                'save_dir': './data',
                'interval_min': 7,
                'max_results': 100
            },
            'reinforcement_learning': {
                'enabled': True,
                'training_interval': 10,
                'model_path': './rl_models'
            },
            'network_defense': {
                'enabled': True,
                'monitored_ports': [22, 80, 443, 3389],
                'auto_block_threshold': 10,
                'block_duration': 3600
            },
            'integration': {
                'enable_ml_decisions': True,
                'enable_auto_response': True,
                'enable_correlation': True,
                'decision_threshold': 0.8
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for section, values in loaded_config.items():
                        if section in default_config:
                            default_config[section].update(values)
                        else:
                            default_config[section] = values
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
        
        return default_config
    
    def _setup_logging(self):
        """Setup main logging system"""
        # Create logs directory
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('rsecure_main')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / 'rsecure_main.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
    
    def initialize_components(self):
        """Initialize all RSecure components"""
        try:
            self.logger.info("Initializing RSecure components...")
            
            # System detection
            if self.config['system_detection']['enabled']:
                self.system_detector = SystemDetector()
                self.system_info = self.system_detector.detect_system()
                self.logger.info(f"System detected: {self.system_info['type']}")
            
            # Monitoring logger
            if self.config['monitoring']['enabled']:
                monitoring_config = self.config['monitoring']
                self.monitoring_logger = RSecureLogger(
                    log_dir=monitoring_config['log_dir'],
                    config=monitoring_config
                )
                self.monitoring_logger.add_alert_callback(self._handle_security_alert)
                self.logger.info("Monitoring logger initialized")
            
            # Neural core
            if self.config['neural_core']['enabled']:
                neural_config = self.config['neural_core']
                self.neural_core = RSecureNeuralCore(
                    model_dir=neural_config['model_dir'],
                    config=neural_config
                )
                self.neural_core.start_analysis()
                self.logger.info("Neural core initialized")
            
            # Analytics
            if self.config['analytics']['enabled']:
                self.analytics = RSecureAnalytics(
                    db_path=self.config['analytics']['db_path'],
                    config=self.config['analytics']
                )
                self.analytics.start_analysis()
                self.logger.info("Analytics initialized")
            
            # System control
            if self.config['system_control']['enabled']:
                self.system_control = RSecureSystemControl(
                    config=self.config['system_control']
                )
                self.system_control.start_control()
                self.logger.info("System control initialized")
            
            # CVU intelligence
            if self.config['cvu_intelligence']['enabled']:
                self.cvu_intelligence = RSecureCVU(
                    config=self.config['cvu_intelligence']
                )
                self.cvu_intelligence.start_intelligence()
                self.logger.info("CVU intelligence initialized")
            
            # Reinforcement learning (temporarily disabled due to TF compatibility)
            if False and self.config['reinforcement_learning']['enabled']:
                self.rl_agent = RSecureReinforcementLearning(
                    config=self.config['reinforcement_learning']
                )
                self.rl_agent.start_training()
                self.logger.info("Reinforcement learning initialized")
            
            # Network defense
            if self.config['network_defense']['enabled']:
                self.network_defense = RSecureNetworkDefense(
                    config=self.config['network_defense']
                )
                self.network_defense.start_defense()
                self.logger.info("Network defense initialized")
            
            self.logger.info("All RSecure components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def start(self):
        """Start RSecure system"""
        try:
            if self.running:
                self.logger.warning("RSecure is already running")
                return
            
            # Initialize components
            self.initialize_components()
            
            # Start integration loop
            self.running = True
            self.integration_thread = threading.Thread(
                target=self._integration_loop,
                daemon=True
            )
            self.integration_thread.start()
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.info("RSecure system started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting RSecure: {e}")
            raise
    
    def stop(self):
        """Stop RSecure system"""
        try:
            if not self.running:
                return
            
            self.logger.info("Stopping RSecure system...")
            
            # Set shutdown event
            self.shutdown_event.set()
            self.running = False
            
            # Stop components
            if self.network_defense:
                self.network_defense.stop_defense()
            
            if self.rl_agent:
                self.rl_agent.stop_training()
            
            if self.cvu_intelligence:
                self.cvu_intelligence.stop_intelligence()
            
            if self.system_control:
                self.system_control.stop_control()
            
            if self.analytics:
                self.analytics.stop_analysis()
            
            if self.neural_core:
                self.neural_core.stop_analysis()
            
            if hasattr(self, 'monitoring_logger') and self.monitoring_logger:
                self.monitoring_logger.stop_monitoring()
            
            # Wait for integration thread
            if hasattr(self, 'integration_thread'):
                self.integration_thread.join(timeout=10)
            
            self.logger.info("RSecure system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping RSecure: {e}")
    
    def _integration_loop(self):
        """Main integration loop"""
        self.logger.info("Integration loop started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Process system state
                self._process_system_state()
                
                # Correlate events
                if self.config['integration']['enable_correlation']:
                    self._correlate_events()
                
                # Make ML-based decisions
                if self.config['integration']['enable_ml_decisions']:
                    self._make_ml_decisions()
                
                # Execute auto-response
                if self.config['integration']['enable_auto_response']:
                    self._execute_auto_response()
                
                # Update metrics
                self._update_metrics()
                
                # Sleep
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in integration loop: {e}")
                time.sleep(10)
    
    def _process_system_state(self):
        """Process current system state"""
        try:
            # Get monitoring data
            if hasattr(self, 'monitoring_logger') and self.monitoring_logger:
                recent_logs = self.monitoring_logger.get_recent_logs('rsecure', 50)
                self._process_monitoring_data(recent_logs)
            
            # Get neural analysis
            if self.neural_core:
                neural_results = self.neural_core.get_analysis_results()
                self._process_neural_results(neural_results)
            
            # Get CVU threats
            if self.cvu_intelligence:
                cvu_threats = self.cvu_intelligence.get_active_threats(20, 5.0)
                self._process_cvu_threats(cvu_threats)
            
            # Get network defense status
            if self.network_defense:
                defense_status = self.network_defense.get_defense_status()
                self._process_defense_status(defense_status)
        
        except Exception as e:
            self.logger.error(f"Error processing system state: {e}")
    
    def _process_monitoring_data(self, logs: List[str]):
        """Process monitoring logs"""
        try:
            for log_entry in logs:
                # Parse log entry and extract features
                if 'ALERT:' in log_entry:
                    self.metrics['events_processed'] += 1
                    
                    # Extract features for neural analysis
                    features = self._extract_features_from_log(log_entry)
                    if features is not None and self.neural_core:
                        self.neural_core.add_data('system', features)
        
        except Exception as e:
            self.logger.error(f"Error processing monitoring data: {e}")
    
    def _process_neural_results(self, results: Dict):
        """Process neural analysis results"""
        try:
            if not results:
                return
            
            threat_level = results.get('threat_level', 0.0)
            self.metrics['neural_predictions'] += 1
            
            # Check if threat level exceeds threshold
            if threat_level > self.config['integration']['decision_threshold']:
                self.metrics['threats_detected'] += 1
                
                # Create security event
                event = SecurityEvent(
                    timestamp=datetime.now().isoformat(),
                    event_type="neural_threat_detected",
                    severity="high" if threat_level > 0.8 else "medium",
                    source="neural_core",
                    description=f"Neural analysis detected threat level: {threat_level:.3f}",
                    threat_score=threat_level,
                    confidence=results.get('confidence', 0.5),
                    details=results
                )
                
                if self.analytics:
                    self.analytics.add_security_event(event)
        
        except Exception as e:
            self.logger.error(f"Error processing neural results: {e}")
    
    def _process_cvu_threats(self, threats: List[Dict]):
        """Process CVU vulnerability threats"""
        try:
            for threat in threats:
                if threat.get('final_risk', 0) > 7.0:  # High risk threshold
                    event = SecurityEvent(
                        timestamp=datetime.now().isoformat(),
                        event_type="vulnerability_threat",
                        severity="high",
                        source="cvu_intelligence",
                        description=f"High risk vulnerability: {threat.get('id', 'Unknown')}",
                        threat_score=threat.get('final_risk', 0),
                        confidence=threat.get('trust', 0.5),
                        details=threat
                    )
                    
                    if self.analytics:
                        self.analytics.add_security_event(event)
        
        except Exception as e:
            self.logger.error(f"Error processing CVU threats: {e}")
    
    def _process_defense_status(self, status: Dict):
        """Process network defense status"""
        try:
            active_threats = status.get('active_threats', 0)
            if active_threats > 0:
                self.metrics['threats_detected'] += active_threats
        
        except Exception as e:
            self.logger.error(f"Error processing defense status: {e}")
    
    def _correlate_events(self):
        """Correlate security events"""
        try:
            if not self.analytics:
                return
            
            # Get recent events for correlation
            # This would implement more sophisticated correlation logic
            pass
        
        except Exception as e:
            self.logger.error(f"Error correlating events: {e}")
    
    def _make_ml_decisions(self):
        """Make ML-based security decisions"""
        try:
            if not self.rl_agent:
                return
            
            # Create security state
            state = self._create_security_state()
            
            # Get action recommendation
            recommendations = self.rl_agent.get_action_recommendation(state, top_k=3)
            
            if recommendations:
                self.metrics['rl_decisions'] += 1
                
                # Log top recommendation
                best_action = recommendations[0]
                self.logger.info(f"RL recommendation: {best_action[1].action_name} (Q-value: {best_action[2]:.3f})")
                
                # Execute action if confidence is high
                if best_action[2] > self.config['integration']['decision_threshold']:
                    self._execute_rl_action(best_action)
        
        except Exception as e:
            self.logger.error(f"Error making ML decisions: {e}")
    
    def _create_security_state(self) -> SecurityState:
        """Create security state for RL agent"""
        try:
            # System resources
            system_resources = self._get_system_resources_vector()
            
            # Network activity
            network_activity = self._get_network_activity_vector()
            
            # Process behavior
            process_behavior = self._get_process_behavior_vector()
            
            # Threat indicators
            threat_indicators = self._get_threat_indicators_vector()
            
            # Vulnerability context
            vulnerability_context = self._get_vulnerability_context_vector()
            
            # Historical performance
            historical_performance = self._get_historical_performance_vector()
            
            return SecurityState(
                system_resources=system_resources,
                network_activity=network_activity,
                process_behavior=process_behavior,
                threat_indicators=threat_indicators,
                vulnerability_context=vulnerability_context,
                historical_performance=historical_performance
            )
        
        except Exception as e:
            self.logger.error(f"Error creating security state: {e}")
            # Return default state
            return SecurityState(
                system_resources=[0.0] * 20,
                network_activity=[0.0] * 20,
                process_behavior=[0.0] * 20,
                threat_indicators=[0.0] * 20,
                vulnerability_context=[0.0] * 20,
                historical_performance=[0.0] * 28
            )
    
    def _get_system_resources_vector(self) -> List[float]:
        """Get system resources as vector"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent() / 100.0
            memory = psutil.virtual_memory()
            memory_percent = memory.percent / 100.0
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent / 100.0
            
            # Create 20-dimensional vector
            vector = [
                cpu_percent, memory_percent, disk_percent,
                # Add more system metrics...
            ] + [0.0] * 17
            
            return vector[:20]
        
        except Exception:
            return [0.0] * 20
    
    def _get_network_activity_vector(self) -> List[float]:
        """Get network activity as vector"""
        try:
            import psutil
            
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent / (1024**3)  # GB
            bytes_recv = net_io.bytes_recv / (1024**3)  # GB
            
            vector = [bytes_sent, bytes_recv] + [0.0] * 18
            return vector[:20]
        
        except Exception:
            return [0.0] * 20
    
    def _get_process_behavior_vector(self) -> List[float]:
        """Get process behavior as vector"""
        try:
            import psutil
            
            process_count = len(psutil.pids()) / 1000.0  # Normalize
            vector = [process_count] + [0.0] * 19
            return vector[:20]
        
        except Exception:
            return [0.0] * 20
    
    def _get_threat_indicators_vector(self) -> List[float]:
        """Get threat indicators as vector"""
        try:
            # Get threat indicators from various components
            neural_threat = 0.0
            if self.neural_core:
                results = self.neural_core.get_analysis_results()
                neural_threat = results.get('threat_level', 0.0)
            
            defense_threats = 0.0
            if self.network_defense:
                status = self.network_defense.get_defense_status()
                defense_threats = status.get('active_threats', 0) / 100.0
            
            vector = [neural_threat, defense_threats] + [0.0] * 18
            return vector[:20]
        
        except Exception:
            return [0.0] * 20
    
    def _get_vulnerability_context_vector(self) -> List[float]:
        """Get vulnerability context as vector"""
        try:
            cvu_threats = 0.0
            if self.cvu_intelligence:
                threats = self.cvu_intelligence.get_active_threats(10, 5.0)
                cvu_threats = len(threats) / 10.0
            
            vector = [cvu_threats] + [0.0] * 19
            return vector[:20]
        
        except Exception:
            return [0.0] * 20
    
    def _get_historical_performance_vector(self) -> List[float]:
        """Get historical performance as vector"""
        try:
            # Performance metrics
            uptime = (datetime.now() - self.metrics['start_time']).total_seconds() / 86400.0  # Days
            events_per_hour = self.metrics['events_processed'] / max(uptime * 24, 1)
            
            vector = [uptime, events_per_hour] + [0.0] * 26
            return vector[:28]
        
        except Exception:
            return [0.0] * 28
    
    def _execute_rl_action(self, recommendation: Tuple[int, SecurityAction, float]):
        """Execute RL-recommended action"""
        try:
            action_id, action, q_value = recommendation
            
            self.logger.info(f"Executing RL action: {action.action_name}")
            
            if action.action_name == "block_ip_temporarily":
                # This would need IP address from context
                pass
            elif action.action_name == "kill_process":
                # This would need process ID from context
                pass
            elif action.action_name == "quarantine_file":
                # This would need file path from context
                pass
            elif action.action_name == "increase_monitoring":
                # Increase monitoring frequency
                pass
            elif action.action_name == "request_human_intervention":
                # Request human intervention
                self.logger.warning("RL agent requesting human intervention")
            
            self.metrics['actions_taken'] += 1
            
        except Exception as e:
            self.logger.error(f"Error executing RL action: {e}")
    
    def _execute_auto_response(self):
        """Execute automatic security responses"""
        try:
            # Check for high-threat situations requiring immediate response
            if self.neural_core:
                results = self.neural_core.get_analysis_results()
                threat_level = results.get('threat_level', 0.0)
                
                if threat_level > 0.9:  # Critical threat
                    self.logger.critical("Critical threat detected - initiating auto-response")
                    
                    # Isolate system if necessary
                    if self.system_control:
                        self.system_control.isolate_system("Critical neural threat detected")
        
        except Exception as e:
            self.logger.error(f"Error in auto-response: {e}")
    
    def _update_metrics(self):
        """Update system metrics"""
        try:
            # Update metrics periodically
            pass
        
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _extract_features_from_log(self, log_entry: str) -> Optional[List[float]]:
        """Extract features from log entry"""
        try:
            # Simple feature extraction from log
            # In production, this would be more sophisticated
            features = []
            
            # Log length
            features.append(len(log_entry) / 1000.0)
            
            # Alert indicators
            alert_keywords = ['critical', 'high', 'error', 'threat', 'attack']
            for keyword in alert_keywords:
                features.append(1.0 if keyword in log_entry.lower() else 0.0)
            
            # Pad to 64 dimensions
            while len(features) < 64:
                features.append(0.0)
            
            return features[:64]
        
        except Exception:
            return None
    
    def _handle_security_alert(self, alert: Dict):
        """Handle security alerts from monitoring"""
        try:
            self.metrics['events_processed'] += 1
            
            # Process alert through neural core
            if self.neural_core:
                features = self._extract_features_from_alert(alert)
                if features:
                    self.neural_core.add_data('system', features)
            
            # Create security event for analytics
            if self.analytics:
                event = SecurityEvent(
                    timestamp=alert.get('timestamp', datetime.now().isoformat()),
                    event_type=alert.get('type', 'security_alert'),
                    severity=alert.get('severity', 'medium'),
                    source=alert.get('source', 'monitoring'),
                    description=alert.get('data', {}).get('description', 'Security alert'),
                    threat_score=0.5,  # Default, would be calculated
                    confidence=0.7,
                    details=alert
                )
                self.analytics.add_security_event(event)
        
        except Exception as e:
            self.logger.error(f"Error handling security alert: {e}")
    
    def _extract_features_from_alert(self, alert: Dict) -> Optional[List[float]]:
        """Extract features from security alert"""
        try:
            features = []
            
            # Alert type
            alert_type = alert.get('type', '')
            types = ['network', 'process', 'file', 'system']
            for t in types:
                features.append(1.0 if t in alert_type.lower() else 0.0)
            
            # Severity
            severity = alert.get('severity', 'medium')
            severity_map = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
            features.append(severity_map.get(severity, 0.5))
            
            # Pad to 64 dimensions
            while len(features) < 64:
                features.append(0.0)
            
            return features[:64]
        
        except Exception:
            return None
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def get_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            status = {
                'system_info': self.system_info,
                'running': self.running,
                'uptime': (datetime.now() - self.metrics['start_time']).total_seconds(),
                'metrics': self.metrics,
                'components': {}
            }
            
            # Add component statuses
            if self.logger:
                status['components']['monitoring'] = 'running' if self.logger.running else 'stopped'
            
            if self.neural_core:
                status['components']['neural_core'] = 'running' if self.neural_core.running else 'stopped'
            
            if self.analytics:
                status['components']['analytics'] = 'running' if self.analytics.running else 'stopped'
            
            if self.system_control:
                status['components']['system_control'] = 'running' if self.system_control.running else 'stopped'
            
            if self.cvu_intelligence:
                status['components']['cvu_intelligence'] = 'running' if self.cvu_intelligence.running else 'stopped'
            
            if self.rl_agent:
                status['components']['reinforcement_learning'] = 'running' if self.rl_agent.running else 'stopped'
            
            if self.network_defense:
                status['components']['network_defense'] = 'running' if self.network_defense.running else 'stopped'
            
            return status
        
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

def main():
    """Main entry point"""
    print("RSecure - Advanced Security System")
    print("=" * 50)
    
    # Create and start RSecure
    rsecure = RSecureMain()
    
    try:
        rsecure.start()
        
        print("RSecure is running. Press Ctrl+C to stop.")
        
        # Main loop
        while rsecure.running:
            time.sleep(10)
            
            # Print status periodically
            status = rsecure.get_status()
            print(f"Status: {status['metrics']['events_processed']} events processed, "
                  f"{status['metrics']['threats_detected']} threats detected")
    
    except KeyboardInterrupt:
        print("\nShutting down RSecure...")
        rsecure.stop()
        print("RSecure stopped.")
    
    except Exception as e:
        print(f"Error: {e}")
        rsecure.stop()

if __name__ == "__main__":
    main()
