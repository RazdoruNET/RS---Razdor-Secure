#!/usr/bin/env python3
"""
RSecure Psychological Protection Layer
Detection of psychological manipulation and consciousness weight adjustment attempts
"""

import re
import json
import time
import logging
import threading
import numpy as np
import sys
import os

# Add mock libraries to path for Python 3.14 compatibility
mock_path = os.path.join(os.path.dirname(__file__), '../../mock_libs')
if mock_path not in sys.path:
    sys.path.insert(0, mock_path)

# Optional TensorFlow import
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available - psychological protection using basic mode")

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from collections import deque

# Import audio stream monitor
try:
    from audio_stream_monitor import RSecureAudioStreamMonitor, AudioThreat
except ImportError:
    RSecureAudioStreamMonitor = None
    AudioThreat = None

# Import macOS notifications
try:
    from macos_notifications import get_notification_instance, send_psychological_threat_alert, send_audio_threat_alert
except ImportError:
    get_notification_instance = None
    send_psychological_threat_alert = None
    send_audio_threat_alert = None

@dataclass
class PsychologicalThreat:
    """Psychological threat information"""
    threat_type: str
    manipulation_technique: str
    confidence: float
    severity: str
    brain_signal: str
    content_indicators: List[str]
    timestamp: datetime
    source: str
    metadata: Dict

class RSecurePsychologicalProtection:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Psychological patterns database
        self.manipulation_patterns = {}
        self.consciousness_weight_patterns = set()
        self.brain_signal_patterns = {}
        
        # Neural networks for detection
        self.content_analyzer = None
        self.pattern_detector = None
        self.consciousness_monitor = None
        
        # Detection history
        self.threat_history = deque(maxlen=10000)
        self.blocked_sources = set()
        
        # Brain signal monitoring
        self.brain_signals = {}
        self.weight_adjustment_attempts = 0
        
        # Threading
        self.running = False
        self.monitoring_thread = None
        
        # Audio stream monitoring
        self.audio_monitor = None
        self.audio_threats = deque(maxlen=1000)
        
        # macOS notifications
        self.notification_system = None
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_psychological')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./psychological_protection.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize components
        self._initialize_neural_networks()
        self._load_psychological_patterns()
        self._initialize_audio_monitor()
        self._initialize_notification_system()
    
    def _get_default_config(self) -> Dict:
        return {
            'sensitivity_level': 0.7,
            'brain_signal_threshold': 0.6,
            'weight_adjustment_threshold': 0.8,
            'content_analysis_interval': 30,
            'enable_brain_monitoring': True,
            'enable_pattern_detection': True,
            'enable_consciousness_protection': True,
            'soft_signal_mode': True,
            'enable_audio_monitoring': True,
            'audio_monitoring_interval': 5,
            'audio_confidence_threshold': 0.6,
            'enable_notifications': True,
            'notification_cooldown': 30
        }
    
    def _initialize_neural_networks(self):
        """Initialize neural networks for psychological protection"""
        try:
            # Content analyzer for manipulation detection
            self.content_analyzer = self._create_content_analyzer()
            
            # Pattern detector for psychological techniques
            self.pattern_detector = self._create_pattern_detector()
            
            # Consciousness weight monitor
            self.consciousness_monitor = self._create_consciousness_monitor()
            
            self.logger.info("Neural networks initialized for psychological protection")
            
        except Exception as e:
            self.logger.error(f"Error initializing neural networks: {e}")
    
    def _create_content_analyzer(self):
        """Create content analysis neural network"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available - using basic content analysis")
            return None
            
        try:
            model = tf.keras.Sequential([
                tf.keras.layers.Embedding(10000, 256, input_length=1000),
                tf.keras.layers.LSTM(128, return_sequences=True),
                tf.keras.layers.LSTM(64),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.4),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error creating content analyzer: {e}")
            return None
    
    def _create_pattern_detector(self):
        """Create pattern detection neural network"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available - using basic pattern detection")
            return None
            
        try:
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(256, activation='relu', input_shape=(200,)),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error creating pattern detector: {e}")
            return None
    
    def _create_consciousness_monitor(self):
        """Create consciousness weight monitoring neural network"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available - using basic consciousness monitoring")
            return None
            
        try:
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu', input_shape=(100,)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(8, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error creating consciousness monitor: {e}")
            return None
    
    def _initialize_audio_monitor(self):
        """Initialize audio stream monitor"""
        try:
            if self.config.get('enable_audio_monitoring', True) and RSecureAudioStreamMonitor:
                self.audio_monitor = RSecureAudioStreamMonitor(
                    config={
                        'monitoring_interval': self.config.get('audio_monitoring_interval', 5),
                        'confidence_threshold': self.config.get('audio_confidence_threshold', 0.6),
                        'enable_real_time_analysis': True,
                        'enable_transcription': True,
                        'suspicious_apps': ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter']
                    }
                )
                self.logger.info("Audio stream monitor initialized")
            else:
                self.logger.info("Audio monitoring disabled")
        except Exception as e:
            self.logger.error(f"Error initializing audio monitor: {e}")
    
    def _initialize_notification_system(self):
        """Initialize macOS notification system"""
        try:
            if self.config.get('enable_notifications', True) and get_notification_instance:
                self.notification_system = get_notification_instance({
                    'enabled': True,
                    'notification_cooldown': self.config.get('notification_cooldown', 30),
                    'enable_sound': True,
                    'enable_icon': True
                })
                self.logger.info("macOS notification system initialized")
            else:
                self.logger.info("Notifications disabled")
        except Exception as e:
            self.logger.error(f"Error initializing notification system: {e}")
    
    def _load_psychological_patterns(self):
        """Load psychological manipulation patterns"""
        try:
            # Authority manipulation patterns
            authority_patterns = [
                r'expert\s+says',
                r'doctor\s+recommends',
                r'scientist\s+proves',
                r'authority\s+figures',
                r'official\s+source',
                r'government\s+report',
                r'medical\s+professional',
                r'certified\s+expert'
            ]
            
            # Social proof patterns
            social_proof_patterns = [
                r'everyone\s+is\s+doing',
                r'most\s+people\s+agree',
                r'popular\s+opinion',
                r'trending\s+now',
                r'viral\s+content',
                r'millions\s+believe',
                r'social\s+proof',
                r'peer\s+pressure'
            ]
            
            # Scarcity patterns
            scarcity_patterns = [
                r'limited\s+time',
                r'only\s+\d+\s+left',
                r'almost\s+gone',
                r'running\s+out',
                r'last\s+chance',
                r'exclusive\s+offer',
                r'urgent\s+action',
                r'don\'t\s+miss\s+out'
            ]
            
            # Emotional manipulation patterns
            emotional_patterns = [
                r'feel\s+guilty',
                r'should\s+feel',
                r'it\'s\s+wrong\s+if',
                r'moral\s+obligation',
                r'emotional\s+blackmail',
                r'guilt\s+trip',
                r'shame\s+tactic',
                r'fear\s+mongering'
            ]
            
            # Cognitive dissonance patterns
            dissonance_patterns = [
                r'contradictory\s+beliefs',
                r'cognitive\s+dissonance',
                r'mental\s+conflict',
                r'confusing\s+information',
                r'paradoxical\s+thinking',
                r'double\s+think',
                r'contradictory\s+logic',
                r'mind\s+bending'
            ]
            
            # Consciousness weight adjustment patterns
            weight_adjustment_patterns = [
                r'change\s+your\s+mind',
                r'reprogram\s+your\s+brain',
                r'rewire\s+your\s+thinking',
                r'alter\s+consciousness',
                r'modify\s+perception',
                r'brain\s+washing',
                r'mind\s+control',
                r'consciousness\s+shift'
            ]
            
            # Brain signal patterns
            brain_signal_patterns = [
                r'subliminal\s+message',
                r'hidden\s+suggestion',
                r'unconscious\s+programming',
                r'subconscious\s+trigger',
                r'neural\s+programming',
                r'brain\s+wave',
                r'mental\s+suggestion',
                r'psychological\s+trigger'
            ]
            
            self.manipulation_patterns = {
                'authority': authority_patterns,
                'social_proof': social_proof_patterns,
                'scarcity': scarcity_patterns,
                'emotional': emotional_patterns,
                'dissonance': dissonance_patterns,
                'weight_adjustment': weight_adjustment_patterns,
                'brain_signal': brain_signal_patterns
            }
            
            self.consciousness_weight_patterns.update(weight_adjustment_patterns)
            self.brain_signal_patterns = {
                'subliminal': brain_signal_patterns
            }
            
            self.logger.info(f"Loaded {len(self.manipulation_patterns)} manipulation pattern categories")
            
        except Exception as e:
            self.logger.error(f"Error loading psychological patterns: {e}")
    
    def start_protection(self):
        """Start psychological protection"""
        if self.running:
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start audio monitoring if enabled
        if self.audio_monitor:
            self.audio_monitor.start_monitoring()
        
        self.logger.info("Psychological protection started")
    
    def stop_protection(self):
        """Stop psychological protection"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=30)
        
        # Stop audio monitoring if enabled
        if self.audio_monitor:
            self.audio_monitor.stop_monitoring()
        
        self.logger.info("Psychological protection stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Update patterns
                self._update_patterns()
                
                # Clean old data
                self._cleanup_old_data()
                
                # Process audio threats
                if self.audio_monitor:
                    self._process_audio_threats()
                
                time.sleep(self.config['content_analysis_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _process_audio_threats(self):
        """Process audio threats from audio monitor"""
        try:
            if not self.audio_monitor:
                return
            
            # Get recent audio threats
            audio_stats = self.audio_monitor.get_monitoring_statistics()
            
            # Check for new threats
            if audio_stats.get('total_threats', 0) > 0:
                # Create psychological threat from audio threat
                self._convert_audio_to_psychological_threats()
                
        except Exception as e:
            self.logger.error(f"Error processing audio threats: {e}")
    
    def _convert_audio_to_psychological_threats(self):
        """Convert audio threats to psychological threats"""
        try:
            if not hasattr(self.audio_monitor, 'audio_threats'):
                return
            
            # Process recent audio threats
            for audio_threat in list(self.audio_monitor.audio_threats)[-10:]:  # Last 10 threats
                # Check if already processed
                if not any(t.timestamp == audio_threat.timestamp for t in self.threat_history):
                    # Convert to psychological threat
                    psych_threat = PsychologicalThreat(
                        threat_type=f"audio_{audio_threat.threat_type}",
                        manipulation_technique="audio_manipulation",
                        confidence=audio_threat.confidence,
                        severity=audio_threat.severity,
                        brain_signal=self._generate_audio_brain_signal(audio_threat),
                        content_indicators=audio_threat.audio_indicators + ['audio_source'],
                        timestamp=audio_threat.timestamp,
                        source=audio_threat.source_app,
                        metadata={
                            'audio_duration': audio_threat.duration,
                            'transcription': audio_threat.transcription,
                            'audio_metadata': audio_threat.metadata
                        }
                    )
                    
                    self.threat_history.append(psych_threat)
                    self.logger.warning(f"Audio psychological threat: {audio_threat.threat_type} from {audio_threat.source_app}")
                    
                    # Generate soft brain signal
                    if self.config['soft_signal_mode']:
                        self._generate_soft_brain_signal(psych_threat)
                    
                    # Send notification for high-severity audio threats
                    if self.notification_system and audio_threat.severity in ['high', 'critical']:
                        self._send_audio_threat_notification(audio_threat)
                    
        except Exception as e:
            self.logger.error(f"Error converting audio to psychological threats: {e}")
    
    def _generate_audio_brain_signal(self, audio_threat) -> str:
        """Generate brain signal for audio threat"""
        try:
            if audio_threat.threat_type == 'propaganda':
                return "🎧 AUDIO_PROPAGANDA_DETECTED"
            elif audio_threat.threat_type == 'subliminal_manipulation':
                return "🎧 SUBLIMINAL_AUDIO_DETECTED"
            elif audio_threat.threat_type == 'binaural_manipulation':
                return "🎧 BINAURAL_MANIPULATION_DETECTED"
            elif audio_threat.severity == 'critical':
                return "⚠️ CRITICAL_AUDIO_THREAT"
            elif audio_threat.severity == 'high':
                return "⚠️ HIGH_AUDIO_RISK"
            else:
                return "🔍 SUSPICIOUS_AUDIO_CONTENT"
                
        except Exception as e:
            self.logger.error(f"Error generating audio brain signal: {e}")
            return "❌ AUDIO_SIGNAL_ERROR"
    
    def analyze_content(self, content: str, source: str = None, context: Dict = None) -> PsychologicalThreat:
        """Analyze content for psychological manipulation"""
        try:
            if not content:
                return self._create_safe_threat(content, source)
            
            # Pattern-based detection
            pattern_results = self._detect_manipulation_patterns(content)
            
            # Content analysis
            content_results = self._analyze_content_for_manipulation(content)
            
            # Consciousness weight analysis
            weight_results = self._analyze_consciousness_weight_adjustment(content)
            
            # Brain signal analysis
            brain_results = self._analyze_brain_signals(content)
            
            # Combine results
            combined_results = self._combine_analysis_results(
                pattern_results, content_results, weight_results, brain_results
            )
            
            # Determine threat type and severity
            threat_type = self._classify_threat_type(combined_results)
            manipulation_technique = self._identify_manipulation_technique(combined_results)
            severity = self._determine_severity(combined_results)
            confidence = combined_results.get('confidence', 0.0)
            
            # Generate brain signal
            brain_signal = self._generate_brain_signal(combined_results)
            
            # Extract content indicators
            content_indicators = self._extract_content_indicators(content, combined_results)
            
            # Create threat object
            threat = PsychologicalThreat(
                threat_type=threat_type,
                manipulation_technique=manipulation_technique,
                confidence=confidence,
                severity=severity,
                brain_signal=brain_signal,
                content_indicators=content_indicators,
                timestamp=datetime.now(),
                source=source or 'unknown',
                metadata=combined_results
            )
            
            # Log high-confidence threats
            if confidence > self.config['sensitivity_level']:
                self.logger.warning(f"Psychological threat detected: {threat_type} from {source} (confidence: {confidence:.3f})")
                self.threat_history.append(threat)
                
                # Generate soft brain signal
                if self.config['soft_signal_mode']:
                    self._generate_soft_brain_signal(threat)
            
            return threat
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {e}")
            return self._create_safe_threat(content, source)
    
    def _detect_manipulation_patterns(self, content: str) -> Dict:
        """Detect manipulation patterns in content"""
        results = {
            'matches': [],
            'categories': {},
            'confidence': 0.0
        }
        
        try:
            content_lower = content.lower()
            
            for category, patterns in self.manipulation_patterns.items():
                category_matches = []
                category_confidence = 0.0
                
                for pattern in patterns:
                    matches = re.findall(pattern, content_lower, re.IGNORECASE)
                    if matches:
                        category_matches.extend(matches)
                        category_confidence += len(matches) * 0.1
                
                if category_matches:
                    results['categories'][category] = {
                        'matches': category_matches,
                        'confidence': min(category_confidence, 1.0)
                    }
                    results['matches'].extend(category_matches)
            
            # Calculate overall confidence
            if results['categories']:
                results['confidence'] = max(
                    cat['confidence'] for cat in results['categories'].values()
                )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting manipulation patterns: {e}")
            return results
    
    def _analyze_content_for_manipulation(self, content: str) -> Dict:
        """Analyze content using neural networks"""
        results = {
            'manipulation_type': 'unknown',
            'confidence': 0.0,
            'features': {}
        }
        
        try:
            if self.content_analyzer is None:
                return results
            
            # Extract features
            features = self._extract_content_features(content)
            
            # Make prediction
            prediction = self.content_analyzer.predict(
                np.expand_dims(features, axis=0),
                verbose=0
            )
            
            confidence = float(prediction[0][0])
            
            # Classify manipulation type
            if confidence > 0.7:
                manipulation_type = 'high_risk'
            elif confidence > 0.4:
                manipulation_type = 'medium_risk'
            else:
                manipulation_type = 'low_risk'
            
            results['manipulation_type'] = manipulation_type
            results['confidence'] = confidence
            results['features'] = features.tolist()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {e}")
            return results
    
    def _analyze_consciousness_weight_adjustment(self, content: str) -> Dict:
        """Analyze content for consciousness weight adjustment attempts"""
        results = {
            'weight_adjustment_detected': False,
            'confidence': 0.0,
            'patterns': []
        }
        
        try:
            content_lower = content.lower()
            
            # Check for weight adjustment patterns
            pattern_matches = []
            for pattern in self.consciousness_weight_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    pattern_matches.extend(matches)
            
            if pattern_matches:
                results['weight_adjustment_detected'] = True
                results['patterns'] = pattern_matches
                results['confidence'] = min(len(pattern_matches) * 0.2, 1.0)
            
            # Neural network analysis
            if self.consciousness_monitor is not None:
                features = self._extract_consciousness_features(content)
                prediction = self.consciousness_monitor.predict(
                    np.expand_dims(features, axis=0),
                    verbose=0
                )
                
                nn_confidence = float(prediction[0][0])
                results['confidence'] = max(results['confidence'], nn_confidence)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing consciousness weight adjustment: {e}")
            return results
    
    def _analyze_brain_signals(self, content: str) -> Dict:
        """Analyze content for brain signal patterns"""
        results = {
            'brain_signal_detected': False,
            'signal_type': 'unknown',
            'confidence': 0.0,
            'patterns': []
        }
        
        try:
            content_lower = content.lower()
            
            # Check for brain signal patterns
            signal_matches = []
            for signal_type, patterns in self.brain_signal_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content_lower, re.IGNORECASE)
                    if matches:
                        signal_matches.extend(matches)
                        results['signal_type'] = signal_type
            
            if signal_matches:
                results['brain_signal_detected'] = True
                results['patterns'] = signal_matches
                results['confidence'] = min(len(signal_matches) * 0.15, 1.0)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing brain signals: {e}")
            return results
    
    def _extract_content_features(self, content: str) -> np.ndarray:
        """Extract features from content for neural analysis"""
        try:
            features = []
            
            # Text length
            features.append(len(content))
            
            # Word count
            words = content.split()
            features.append(len(words))
            
            # Sentence count
            sentences = re.split(r'[.!?]+', content)
            features.append(len(sentences))
            
            # Average word length
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            features.append(avg_word_length)
            
            # Punctuation ratio
            punctuation_count = len(re.findall(r'[.!?]', content))
            punctuation_ratio = punctuation_count / len(content) if content else 0
            features.append(punctuation_ratio)
            
            # Question ratio
            question_count = len(re.findall(r'\?', content))
            question_ratio = question_count / len(content) if content else 0
            features.append(question_ratio)
            
            # Exclamation ratio
            exclamation_count = len(re.findall(r'!', content))
            exclamation_ratio = exclamation_count / len(content) if content else 0
            features.append(exclamation_ratio)
            
            # Capitalization ratio
            uppercase_count = len(re.findall(r'[A-Z]', content))
            uppercase_ratio = uppercase_count / len(content) if content else 0
            features.append(uppercase_ratio)
            
            # Digit ratio
            digit_count = len(re.findall(r'\d', content))
            digit_ratio = digit_count / len(content) if content else 0
            features.append(digit_ratio)
            
            # Manipulation keyword count
            manipulation_keywords = [
                'should', 'must', 'need', 'have to', 'supposed to',
                'everyone', 'nobody', 'always', 'never', 'only'
            ]
            keyword_count = sum(1 for keyword in manipulation_keywords if keyword in content.lower())
            features.append(keyword_count)
            
            # Pad to 1000 features
            while len(features) < 1000:
                features.append(0.0)
            
            return np.array(features[:1000])
            
        except Exception as e:
            self.logger.error(f"Error extracting content features: {e}")
            return np.zeros(1000)
    
    def _extract_consciousness_features(self, content: str) -> np.ndarray:
        """Extract consciousness-related features"""
        try:
            features = []
            
            # Weight adjustment keywords
            weight_keywords = [
                'change', 'modify', 'alter', 'reprogram', 'rewire',
                'shift', 'transform', 'convert', 'adjust', 'calibrate'
            ]
            
            # Consciousness keywords
            consciousness_keywords = [
                'mind', 'brain', 'consciousness', 'awareness', 'perception',
                'thought', 'thinking', 'belief', 'opinion', 'viewpoint'
            ]
            
            # Control keywords
            control_keywords = [
                'control', 'influence', 'persuade', 'convince', 'manipulate',
                'guide', 'direct', 'steer', 'shape', 'mold'
            ]
            
            content_lower = content.lower()
            
            # Count keywords
            weight_count = sum(1 for keyword in weight_keywords if keyword in content_lower)
            consciousness_count = sum(1 for keyword in consciousness_keywords if keyword in content_lower)
            control_count = sum(1 for keyword in control_keywords if keyword in content_lower)
            
            features.extend([weight_count, consciousness_count, control_count])
            
            # Text statistics
            features.append(len(content))
            features.append(len(content.split()))
            
            # Pattern complexity
            unique_words = len(set(content_lower.split()))
            total_words = len(content_lower.split())
            complexity_ratio = unique_words / total_words if total_words > 0 else 0
            features.append(complexity_ratio)
            
            # Pad to 100 features
            while len(features) < 100:
                features.append(0.0)
            
            return np.array(features[:100])
            
        except Exception as e:
            self.logger.error(f"Error extracting consciousness features: {e}")
            return np.zeros(100)
    
    def _combine_analysis_results(self, pattern_results: Dict, content_results: Dict, 
                                weight_results: Dict, brain_results: Dict) -> Dict:
        """Combine results from all analysis methods"""
        combined = {
            'pattern_analysis': pattern_results,
            'content_analysis': content_results,
            'weight_analysis': weight_results,
            'brain_analysis': brain_results,
            'confidence': 0.0,
            'risk_score': 0.0
        }
        
        try:
            # Calculate weighted confidence
            pattern_confidence = pattern_results.get('confidence', 0.0)
            content_confidence = content_results.get('confidence', 0.0)
            weight_confidence = weight_results.get('confidence', 0.0)
            brain_confidence = brain_results.get('confidence', 0.0)
            
            # Weighted combination
            combined['confidence'] = (
                pattern_confidence * 0.3 +
                content_confidence * 0.3 +
                weight_confidence * 0.2 +
                brain_confidence * 0.2
            )
            
            # Calculate risk score
            risk_factors = 0
            if weight_results.get('weight_adjustment_detected', False):
                risk_factors += 1
            if brain_results.get('brain_signal_detected', False):
                risk_factors += 1
            if pattern_confidence > 0.6:
                risk_factors += 1
            
            combined['risk_score'] = min(combined['confidence'] + (risk_factors * 0.1), 1.0)
            
            return combined
            
        except Exception as e:
            self.logger.error(f"Error combining results: {e}")
            return combined
    
    def _classify_threat_type(self, results: Dict) -> str:
        """Classify threat type based on analysis results"""
        try:
            # Check for weight adjustment
            weight_analysis = results.get('weight_analysis', {})
            if weight_analysis.get('weight_adjustment_detected', False):
                return 'consciousness_weight_adjustment'
            
            # Check for brain signals
            brain_analysis = results.get('brain_analysis', {})
            if brain_analysis.get('brain_signal_detected', False):
                return 'brain_signal_manipulation'
            
            # Check pattern categories
            pattern_categories = results.get('pattern_analysis', {}).get('categories', {})
            if pattern_categories:
                highest_confidence = 0
                best_category = 'unknown'
                
                for category, data in pattern_categories.items():
                    if data['confidence'] > highest_confidence:
                        highest_confidence = data['confidence']
                        best_category = category
                
                if highest_confidence > 0.5:
                    return f'{best_category}_manipulation'
            
            # Default classification
            confidence = results.get('confidence', 0.0)
            if confidence > 0.7:
                return 'psychological_manipulation'
            elif confidence > 0.4:
                return 'suspicious_content'
            else:
                return 'safe'
                
        except Exception as e:
            self.logger.error(f"Error classifying threat type: {e}")
            return 'unknown'
    
    def _identify_manipulation_technique(self, results: Dict) -> str:
        """Identify specific manipulation technique"""
        try:
            pattern_categories = results.get('pattern_analysis', {}).get('categories', {})
            
            if pattern_categories:
                highest_confidence = 0
                best_technique = 'unknown'
                
                for technique, data in pattern_categories.items():
                    if data['confidence'] > highest_confidence:
                        highest_confidence = data['confidence']
                        best_technique = technique
                
                return best_technique
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error identifying manipulation technique: {e}")
            return 'unknown'
    
    def _determine_severity(self, results: Dict) -> str:
        """Determine threat severity"""
        try:
            confidence = results.get('confidence', 0.0)
            risk_score = results.get('risk_score', 0.0)
            
            # Check for high-risk indicators
            weight_analysis = results.get('weight_analysis', {})
            brain_analysis = results.get('brain_analysis', {})
            
            weight_detected = weight_analysis.get('weight_adjustment_detected', False)
            brain_detected = brain_analysis.get('brain_signal_detected', False)
            
            # Determine severity
            if risk_score > 0.8 or (weight_detected and brain_detected):
                return 'critical'
            elif risk_score > 0.6 or weight_detected:
                return 'high'
            elif risk_score > 0.4 or brain_detected:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Error determining severity: {e}")
            return 'low'
    
    def _generate_brain_signal(self, results: Dict) -> str:
        """Generate brain signal for user awareness"""
        try:
            confidence = results.get('confidence', 0.0)
            risk_score = results.get('risk_score', 0.0)
            
            # Check for specific threat types
            weight_analysis = results.get('weight_analysis', {})
            brain_analysis = results.get('brain_analysis', {})
            
            if weight_analysis.get('weight_adjustment_detected', False):
                return "⚠️ WEIGHT_ADJUSTMENT_ATTEMPT_DETECTED"
            
            if brain_analysis.get('brain_signal_detected', False):
                return "🧠 BRAIN_SIGNAL_MANIPULATION_DETECTED"
            
            if risk_score > 0.7:
                return "⚠️ HIGH_PSYCHOLOGICAL_RISK"
            elif risk_score > 0.5:
                return "🔍 PSYCHOLOGICAL_MANIPULATION_SUSPECTED"
            else:
                return "✅ CONTENT_SAFE"
                
        except Exception as e:
            self.logger.error(f"Error generating brain signal: {e}")
            return "❌ SIGNAL_ERROR"
    
    def _extract_content_indicators(self, content: str, results: Dict) -> List[str]:
        """Extract content indicators"""
        indicators = []
        
        try:
            # Pattern indicators
            pattern_categories = results.get('pattern_analysis', {}).get('categories', {})
            for category, data in pattern_categories.items():
                if data['confidence'] > 0.3:
                    indicators.append(f'{category}_pattern')
            
            # Content indicators
            content_confidence = results.get('content_analysis', {}).get('confidence', 0.0)
            if content_confidence > 0.5:
                indicators.append('manipulative_content')
            
            # Weight adjustment indicators
            weight_analysis = results.get('weight_analysis', {})
            if weight_analysis.get('weight_adjustment_detected', False):
                indicators.append('consciousness_weight_adjustment')
            
            # Brain signal indicators
            brain_analysis = results.get('brain_analysis', {})
            if brain_analysis.get('brain_signal_detected', False):
                indicators.append('brain_signal_manipulation')
            
            return list(set(indicators))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error extracting content indicators: {e}")
            return []
    
    def _generate_soft_brain_signal(self, threat: PsychologicalThreat):
        """Generate soft brain signal for user awareness"""
        try:
            # Create subtle notification
            signal_strength = threat.confidence * 100
            
            # Log the signal
            self.logger.info(f"Soft brain signal generated: {threat.brain_signal} (strength: {signal_strength:.1f}%)")
            
            # Store signal for monitoring
            self.brain_signals[threat.timestamp] = {
                'signal': threat.brain_signal,
                'strength': signal_strength,
                'threat_type': threat.threat_type,
                'source': threat.source
            }
            
            # Send macOS notification for high-severity threats
            if self.notification_system and threat.severity in ['high', 'critical']:
                self._send_psychological_threat_notification(threat)
            
            # Increment weight adjustment attempts counter
            if 'weight_adjustment' in threat.threat_type:
                self.weight_adjustment_attempts += 1
            
        except Exception as e:
            self.logger.error(f"Error generating soft brain signal: {e}")
    
    def _send_psychological_threat_notification(self, threat: PsychologicalThreat):
        """Send macOS notification for psychological threat"""
        try:
            if not self.notification_system:
                return
            
            # Prepare threat data for notification
            threat_data = {
                'threat_type': threat.threat_type,
                'confidence': threat.confidence,
                'severity': threat.severity,
                'source': threat.source,
                'brain_signal': threat.brain_signal,
                'content_indicators': threat.content_indicators
            }
            
            # Send notification
            success = self.notification_system.send_psychological_threat_notification(threat_data)
            
            if success:
                self.logger.info(f"Psychological threat notification sent: {threat.threat_type}")
            else:
                self.logger.warning(f"Failed to send psychological threat notification")
                
        except Exception as e:
            self.logger.error(f"Error sending psychological threat notification: {e}")
    
    def _send_audio_threat_notification(self, audio_threat):
        """Send macOS notification for audio threat"""
        try:
            if not self.notification_system:
                return
            
            # Prepare audio threat data for notification
            audio_threat_data = {
                'threat_type': audio_threat.threat_type,
                'confidence': audio_threat.confidence,
                'severity': audio_threat.severity,
                'source_app': audio_threat.source_app,
                'transcription': audio_threat.transcription,
                'audio_indicators': audio_threat.audio_indicators
            }
            
            # Send notification
            success = self.notification_system.send_audio_threat_notification(audio_threat_data)
            
            if success:
                self.logger.info(f"Audio threat notification sent: {audio_threat.threat_type}")
            else:
                self.logger.warning(f"Failed to send audio threat notification")
                
        except Exception as e:
            self.logger.error(f"Error sending audio threat notification: {e}")
    
    def _create_safe_threat(self, content: str, source: str) -> PsychologicalThreat:
        """Create a safe threat object"""
        return PsychologicalThreat(
            threat_type='safe',
            manipulation_technique='none',
            confidence=0.0,
            severity='low',
            brain_signal='✅ CONTENT_SAFE',
            content_indicators=[],
            timestamp=datetime.now(),
            source=source or 'unknown',
            metadata={}
        )
    
    def _update_patterns(self):
        """Update patterns from external sources"""
        try:
            # This would integrate with threat intelligence APIs
            # For now, we'll use static patterns
            pass
        except Exception as e:
            self.logger.error(f"Error updating patterns: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data"""
        try:
            # Remove old brain signals
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.brain_signals = {
                k: v for k, v in self.brain_signals.items() 
                if k > cutoff_time
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_protection_statistics(self) -> Dict:
        """Get protection statistics"""
        try:
            total_threats = len(self.threat_history)
            blocked_sources = len(self.blocked_sources)
            
            # Recent threats (last 24 hours)
            recent_time = datetime.now() - timedelta(hours=24)
            recent_threats = [t for t in self.threat_history if t.timestamp > recent_time]
            
            # Threat type distribution
            threat_types = {}
            for threat in self.threat_history:
                threat_type = threat.threat_type
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
            
            # Severity distribution
            severity_dist = {}
            for threat in self.threat_history:
                severity = threat.severity
                severity_dist[severity] = severity_dist.get(severity, 0) + 1
            
            return {
                'total_threats': total_threats,
                'blocked_sources': blocked_sources,
                'recent_threats_24h': len(recent_threats),
                'threat_types': threat_types,
                'severity_distribution': severity_dist,
                'weight_adjustment_attempts': self.weight_adjustment_attempts,
                'brain_signals_count': len(self.brain_signals),
                'protection_running': self.running
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    protection = RSecurePsychologicalProtection()
    protection.start_protection()
    
    # Test content analysis
    test_contents = [
        "Everyone believes this is true, so you should too.",
        "Experts say you must change your mind about this topic.",
        "This content will rewire your brain and alter your consciousness.",
        "Normal informational content about security.",
        "Limited time offer! Don't miss out on this exclusive deal!"
    ]
    
    for i, content in enumerate(test_contents):
        threat = protection.analyze_content(content, f"test_source_{i}")
        print(f"Content: {content[:50]}...")
        print(f"Threat Type: {threat.threat_type}")
        print(f"Manipulation Technique: {threat.manipulation_technique}")
        print(f"Confidence: {threat.confidence:.3f}")
        print(f"Severity: {threat.severity}")
        print(f"Brain Signal: {threat.brain_signal}")
        print(f"Indicators: {threat.content_indicators}")
        print("-" * 50)
    
    # Get statistics
    stats = protection.get_protection_statistics()
    print(f"Statistics: {stats}")
    
    protection.stop_protection()
