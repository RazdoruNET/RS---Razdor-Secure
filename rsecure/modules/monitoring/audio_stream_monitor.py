#!/usr/bin/env python3
"""
RSecure Audio Stream Monitor
Real-time audio analysis for propaganda and psychological manipulation detection
"""

import os
import sys
import time
import logging
import threading
import subprocess
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
    print("Warning: TensorFlow not available - audio monitor using basic mode")

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from collections import deque
import json

@dataclass
class AudioThreat:
    """Audio threat information"""
    threat_type: str
    source_app: str
    confidence: float
    severity: str
    audio_indicators: List[str]
    transcription: str
    timestamp: datetime
    duration: float
    metadata: Dict

class RSecureAudioStreamMonitor:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Audio monitoring
        self.monitoring_active = False
        self.audio_buffer = deque(maxlen=1000)
        self.active_streams = {}
        
        # Neural networks for audio analysis
        self.audio_analyzer = None
        self.speech_detector = None
        self.propaganda_detector = None
        
        # Audio patterns database
        self.propaganda_patterns = {}
        self.manipulation_audio_patterns = set()
        self.suspicious_frequencies = set()
        
        # Transcription service
        self.transcription_engine = None
        
        # Threat history
        self.audio_threats = deque(maxlen=5000)
        self.blocked_applications = set()
        
        # Threading
        self.monitoring_thread = None
        self.analysis_thread = None
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_audio_monitor')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./audio_stream_monitor.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize components
        self._initialize_neural_networks()
        self._load_audio_patterns()
    
    def _get_default_config(self) -> Dict:
        return {
            'monitoring_interval': 1.0,  # seconds
            'audio_buffer_size': 1024,
            'sample_rate': 44100,
            'confidence_threshold': 0.7,
            'propaganda_threshold': 0.8,
            'enable_real_time_analysis': True,
            'enable_transcription': True,
            'enable_frequency_analysis': True,
            'enable_speech_detection': True,
            'suspicious_apps': ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter'],
            'max_recording_duration': 30  # seconds
        }
    
    def _initialize_neural_networks(self):
        """Initialize neural networks for audio analysis"""
        try:
            # Audio analyzer for general threats
            self.audio_analyzer = self._create_audio_analyzer()
            
            # Speech detector
            self.speech_detector = self._create_speech_detector()
            
            # Propaganda detector
            self.propaganda_detector = self._create_propaganda_detector()
            
            self.logger.info("Audio neural networks initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing audio neural networks: {e}")
    
    def _create_audio_analyzer(self):
        """Create audio analysis neural network"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available - using basic audio analysis")
            return None
            
        try:
            # Input for audio spectrograms
            audio_input = tf.keras.layers.Input(shape=(128, 128, 1), name='audio_input')
            
            # Convolutional layers for feature extraction
            x = tf.keras.layers.Conv2D(32, (3, 3), activation='relu')(audio_input)
            x = tf.keras.layers.MaxPooling2D((2, 2))(x)
            x = tf.keras.layers.Conv2D(64, (3, 3), activation='relu')(x)
            x = tf.keras.layers.MaxPooling2D((2, 2))(x)
            x = tf.keras.layers.Conv2D(128, (3, 3), activation='relu')(x)
            x = tf.keras.layers.MaxPooling2D((2, 2))(x)
            
            # Flatten and dense layers
            x = tf.keras.layers.Flatten()(x)
            x = tf.keras.layers.Dense(256, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.5)(x)
            x = tf.keras.layers.Dense(128, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.3)(x)
            x = tf.keras.layers.Dense(64, activation='relu')(x)
            
            # Output layers
            threat_type = tf.keras.layers.Dense(5, activation='softmax', name='threat_type')(x)
            confidence = tf.keras.layers.Dense(1, activation='sigmoid', name='confidence')(x)
            
            model = tf.keras.Model(
                inputs=audio_input,
                outputs=[threat_type, confidence]
            )
            
            model.compile(
                optimizer='adam',
                loss={
                    'threat_type': 'categorical_crossentropy',
                    'confidence': 'binary_crossentropy'
                },
                metrics={
                    'threat_type': 'accuracy',
                    'confidence': 'accuracy'
                }
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error creating audio analyzer: {e}")
            return None
    
    def _create_speech_detector(self):
        """Create speech detection neural network"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available - using basic speech detection")
            return None
            
        try:
            model = tf.keras.Sequential([
                tf.keras.layers.LSTM(128, return_sequences=True, input_shape=(None, 1)),
                tf.keras.layers.LSTM(64),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.3),
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
            self.logger.error(f"Error creating speech detector: {e}")
            return None
    
    def _create_propaganda_detector(self):
        """Create propaganda detection neural network"""
        if not TENSORFLOW_AVAILABLE:
            print("Warning: TensorFlow not available - using basic propaganda detection")
            return None
            
        try:
            model = tf.keras.Sequential([
                tf.keras.layers.Conv1D(64, 3, activation='relu', input_shape=(None, 1)),
                tf.keras.layers.MaxPooling1D(2),
                tf.keras.layers.Conv1D(128, 3, activation='relu'),
                tf.keras.layers.MaxPooling1D(2),
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
            self.logger.error(f"Error creating propaganda detector: {e}")
            return None
    
    def _load_audio_patterns(self):
        """Load audio manipulation patterns"""
        try:
            # Propaganda audio patterns
            self.propaganda_patterns = {
                'repetitive_phrases': [
                    'we must', 'they want', 'the truth is', 'wake up',
                    'open your eyes', 'the real story', 'hidden truth'
                ],
                'emotional_triggers': [
                    'fear', 'anger', 'hope', 'change', 'revolution',
                    'freedom', 'tyranny', 'oppression', 'liberation'
                ],
                'authority_claims': [
                    'experts say', 'scientists confirm', 'studies show',
                    'official sources', 'insider information', 'classified'
                ],
                'us_vs_them': [
                    'they', 'them', 'those people', 'the elite',
                    'the system', 'the establishment', 'the powers'
                ],
                'conspiracy_indicators': [
                    'secret', 'hidden', 'covered up', 'they don\'t want',
                    'the truth about', 'what they\'re hiding', 'exposed'
                ]
            }
            
            # Suspicious frequency patterns (Hz)
            self.suspicious_frequencies = {
                'subliminal': [17.5, 20.0, 22.5],  # Subliminal frequencies
                'hypnotic': [4.0, 6.0, 8.0],      # Hypnotic frequencies
                'stress': [40.0, 50.0, 60.0],      # Stress-inducing frequencies
                'manipulation': [100.0, 150.0, 200.0]  # Manipulation frequencies
            }
            
            # Audio manipulation patterns
            self.manipulation_audio_patterns = {
                'binaural_beats': 'binaural',
                'isochronic_tones': 'isochronic',
                'subliminal_messages': 'subliminal',
                'neuro_linguistic_programming': 'nlp',
                'emotional_frequency_manipulation': 'emotional_freq'
            }
            
            self.logger.info("Audio patterns loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading audio patterns: {e}")
    
    def start_monitoring(self):
        """Start audio stream monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        
        self.monitoring_thread.start()
        self.analysis_thread.start()
        
        self.logger.info("Audio stream monitoring started")
    
    def stop_monitoring(self):
        """Stop audio stream monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=30)
        if self.analysis_thread:
            self.analysis_thread.join(timeout=30)
        
        self.logger.info("Audio stream monitoring stopped")
    
    def _monitoring_loop(self):
        """Main audio monitoring loop"""
        while self.monitoring_active:
            try:
                # Detect active audio streams
                self._detect_audio_streams()
                
                # Capture audio from suspicious applications
                self._capture_audio_streams()
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _detect_audio_streams(self):
        """Detect active audio streams"""
        try:
            platform = sys.platform
            
            if platform == 'darwin':  # macOS
                self._detect_macos_audio_streams()
            elif platform == 'linux':
                self._detect_linux_audio_streams()
            
        except Exception as e:
            self.logger.error(f"Error detecting audio streams: {e}")
    
    def _detect_macos_audio_streams(self):
        """Detect audio streams on macOS"""
        try:
            # Use system_profiler to get audio devices
            result = subprocess.run(
                ['system_profiler', 'SPAudioDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self._process_macos_audio_data(data)
            
            # Check for active applications using audio
            self._check_macos_audio_apps()
            
        except Exception as e:
            self.logger.error(f"Error detecting macOS audio streams: {e}")
    
    def _detect_linux_audio_streams(self):
        """Detect audio streams on Linux"""
        try:
            # Check /proc/asound/cards
            if os.path.exists('/proc/asound/cards'):
                with open('/proc/asound/cards', 'r') as f:
                    cards = f.read()
                    self._process_linux_audio_cards(cards)
            
            # Check pulseaudio if available
            self._check_pulseaudio_streams()
            
        except Exception as e:
            self.logger.error(f"Error detecting Linux audio streams: {e}")
    
    def _check_macos_audio_apps(self):
        """Check which applications are using audio on macOS"""
        try:
            # Use lsof to find processes using audio devices
            result = subprocess.run(
                ['lsof', '+D', '/dev', '|', 'grep', '-i', 'audio'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self._process_audio_process_line(line)
            
        except Exception as e:
            self.logger.error(f"Error checking macOS audio apps: {e}")
    
    def _process_audio_process_line(self, line: str):
        """Process audio process line"""
        try:
            parts = line.split()
            if len(parts) >= 2:
                pid = parts[1]
                app_name = ' '.join(parts[8:]) if len(parts) > 8 else 'unknown'
                
                # Check if it's a suspicious application
                app_name_lower = app_name.lower()
                for suspicious_app in self.config['suspicious_apps']:
                    if suspicious_app in app_name_lower:
                        self.active_streams[pid] = {
                            'app_name': app_name,
                            'pid': pid,
                            'last_seen': datetime.now(),
                            'audio_captured': False
                        }
                        break
            
        except Exception as e:
            self.logger.error(f"Error processing audio process line: {e}")
    
    def _capture_audio_streams(self):
        """Capture audio from active streams"""
        try:
            for pid, stream_info in list(self.active_streams.items()):
                if not stream_info['audio_captured']:
                    # Attempt to capture audio
                    audio_data = self._capture_process_audio(pid, stream_info['app_name'])
                    if audio_data is not None:
                        self.audio_buffer.append({
                            'pid': pid,
                            'app_name': stream_info['app_name'],
                            'audio_data': audio_data,
                            'timestamp': datetime.now()
                        })
                        stream_info['audio_captured'] = True
            
        except Exception as e:
            self.logger.error(f"Error capturing audio streams: {e}")
    
    def _capture_process_audio(self, pid: str, app_name: str) -> Optional[np.ndarray]:
        """Capture audio from specific process"""
        try:
            platform = sys.platform
            
            if platform == 'darwin':
                return self._capture_macos_audio(pid, app_name)
            elif platform == 'linux':
                return self._capture_linux_audio(pid, app_name)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturing process audio: {e}")
            return None
    
    def _capture_macos_audio(self, pid: str, app_name: str) -> Optional[np.ndarray]:
        """Capture audio on macOS"""
        try:
            # Use SoX (Sound eXchange) to capture audio
            # This is a simplified approach - in practice would need more sophisticated method
            
            # For demonstration, create dummy audio data
            duration = min(self.config['max_recording_duration'], 5)  # 5 seconds max
            sample_rate = self.config['sample_rate']
            samples = int(duration * sample_rate)
            
            # Generate dummy audio data (in real implementation would capture actual audio)
            audio_data = np.random.normal(0, 0.1, samples).astype(np.float32)
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error capturing macOS audio: {e}")
            return None
    
    def _capture_linux_audio(self, pid: str, app_name: str) -> Optional[np.ndarray]:
        """Capture audio on Linux"""
        try:
            # Use ALSA or PulseAudio to capture audio
            # Simplified approach for demonstration
            
            duration = min(self.config['max_recording_duration'], 5)
            sample_rate = self.config['sample_rate']
            samples = int(duration * sample_rate)
            
            # Generate dummy audio data (in real implementation would capture actual audio)
            audio_data = np.random.normal(0, 0.1, samples).astype(np.float32)
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error capturing Linux audio: {e}")
            return None
    
    def _analysis_loop(self):
        """Audio analysis loop"""
        while self.monitoring_active:
            try:
                # Process audio buffer
                if self.audio_buffer:
                    audio_item = self.audio_buffer.popleft()
                    self._analyze_audio_data(audio_item)
                
                time.sleep(0.1)  # Fast analysis loop
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                time.sleep(1)
    
    def _analyze_audio_data(self, audio_item: Dict):
        """Analyze captured audio data"""
        try:
            audio_data = audio_item['audio_data']
            app_name = audio_item['app_name']
            pid = audio_item['pid']
            
            # Convert to spectrogram
            spectrogram = self._create_spectrogram(audio_data)
            
            # Speech detection
            speech_confidence = self._detect_speech(audio_data)
            
            # Propaganda detection
            propaganda_confidence = self._detect_propaganda(audio_data)
            
            # Frequency analysis
            frequency_analysis = self._analyze_frequencies(audio_data)
            
            # Transcription if enabled
            transcription = ""
            if self.config['enable_transcription'] and speech_confidence > 0.5:
                transcription = self._transcribe_audio(audio_data)
            
            # Combine results
            combined_confidence = max(speech_confidence, propaganda_confidence)
            
            # Check for manipulation patterns
            manipulation_indicators = self._detect_audio_manipulation(audio_data, frequency_analysis)
            
            # Determine threat type and severity
            threat_type = self._classify_audio_threat(
                speech_confidence, propaganda_confidence, manipulation_indicators, transcription
            )
            
            severity = self._determine_audio_severity(
                combined_confidence, manipulation_indicators, threat_type
            )
            
            # Create threat object
            if combined_confidence > self.config['confidence_threshold']:
                threat = AudioThreat(
                    threat_type=threat_type,
                    source_app=app_name,
                    confidence=combined_confidence,
                    severity=severity,
                    audio_indicators=manipulation_indicators,
                    transcription=transcription,
                    timestamp=datetime.now(),
                    duration=len(audio_data) / self.config['sample_rate'],
                    metadata={
                        'pid': pid,
                        'speech_confidence': speech_confidence,
                        'propaganda_confidence': propaganda_confidence,
                        'frequency_analysis': frequency_analysis
                    }
                )
                
                self.audio_threats.append(threat)
                self.logger.warning(f"Audio threat detected: {threat_type} from {app_name} (confidence: {combined_confidence:.3f})")
        
        except Exception as e:
            self.logger.error(f"Error analyzing audio data: {e}")
    
    def _create_spectrogram(self, audio_data: np.ndarray) -> np.ndarray:
        """Create spectrogram from audio data"""
        try:
            # Simplified spectrogram creation
            # In real implementation would use FFT or librosa
            
            # Create dummy spectrogram (128x128)
            spectrogram = np.random.rand(128, 128).astype(np.float32)
            
            return spectrogram
            
        except Exception as e:
            self.logger.error(f"Error creating spectrogram: {e}")
            return np.zeros((128, 128), dtype=np.float32)
    
    def _detect_speech(self, audio_data: np.ndarray) -> float:
        """Detect speech in audio data"""
        try:
            if self.speech_detector is None:
                return 0.0
            
            # Prepare input
            audio_input = audio_data.reshape(-1, 1)
            
            # Make prediction
            prediction = self.speech_detector.predict(
                np.expand_dims(audio_input, axis=0),
                verbose=0
            )
            
            return float(prediction[0][0])
            
        except Exception as e:
            self.logger.error(f"Error detecting speech: {e}")
            return 0.0
    
    def _detect_propaganda(self, audio_data: np.ndarray) -> float:
        """Detect propaganda in audio data"""
        try:
            if self.propaganda_detector is None:
                return 0.0
            
            # Prepare input
            audio_input = audio_data.reshape(-1, 1)
            
            # Make prediction
            prediction = self.propaganda_detector.predict(
                np.expand_dims(audio_input, axis=0),
                verbose=0
            )
            
            return float(prediction[0][0])
            
        except Exception as e:
            self.logger.error(f"Error detecting propaganda: {e}")
            return 0.0
    
    def _analyze_frequencies(self, audio_data: np.ndarray) -> Dict:
        """Analyze frequency content of audio"""
        try:
            # Simplified frequency analysis
            # In real implementation would use FFT
            
            frequency_analysis = {
                'dominant_frequencies': [440.0, 880.0, 1760.0],  # Dummy frequencies
                'suspicious_frequencies': [],
                'frequency_peaks': [],
                'spectral_centroid': 1000.0,
                'spectral_rolloff': 2000.0,
                'zero_crossing_rate': 0.1
            }
            
            # Check for suspicious frequencies
            for freq_category, freqs in self.suspicious_frequencies.items():
                for freq in freqs:
                    if freq in frequency_analysis['dominant_frequencies']:
                        frequency_analysis['suspicious_frequencies'].append({
                            'frequency': freq,
                            'category': freq_category
                        })
            
            return frequency_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing frequencies: {e}")
            return {}
    
    def _transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio to text"""
        try:
            # Simplified transcription
            # In real implementation would use speech-to-text API
            
            # Dummy transcription for demonstration
            transcriptions = [
                "we must wake up to the truth",
                "they are hiding something from us",
                "the system wants to control us",
                "open your eyes and see the reality",
                "this is what they don't want you to know"
            ]
            
            import random
            return random.choice(transcriptions) if random.random() > 0.7 else ""
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def _detect_audio_manipulation(self, audio_data: np.ndarray, frequency_analysis: Dict) -> List[str]:
        """Detect audio manipulation techniques"""
        indicators = []
        
        try:
            # Check for suspicious frequencies
            suspicious_freqs = frequency_analysis.get('suspicious_frequencies', [])
            if suspicious_freqs:
                for freq_info in suspicious_freqs:
                    indicators.append(f"suspicious_frequency_{freq_info['category']}")
            
            # Check for binaural beats (simplified)
            if len(audio_data) > 1000:
                # Check for frequency differences that could indicate binaural beats
                indicators.append("potential_binaural_beats")
            
            # Check for repetitive patterns
            if self._detect_repetitive_patterns(audio_data):
                indicators.append("repetitive_audio_patterns")
            
            # Check for unusual volume dynamics
            if self._detect_unusual_dynamics(audio_data):
                indicators.append("unusual_volume_dynamics")
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error detecting audio manipulation: {e}")
            return []
    
    def _detect_repetitive_patterns(self, audio_data: np.ndarray) -> bool:
        """Detect repetitive patterns in audio"""
        try:
            # Simplified pattern detection
            # In real implementation would use autocorrelation or other methods
            
            # Check for periodicity
            if len(audio_data) > 1000:
                # Dummy implementation
                return np.random.random() > 0.8
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting repetitive patterns: {e}")
            return False
    
    def _detect_unusual_dynamics(self, audio_data: np.ndarray) -> bool:
        """Detect unusual volume dynamics"""
        try:
            # Check for sudden volume changes or unusual compression
            volume_changes = np.diff(np.abs(audio_data))
            sudden_changes = np.sum(np.abs(volume_changes) > np.std(volume_changes) * 3)
            
            return sudden_changes > len(audio_data) * 0.01
            
        except Exception as e:
            self.logger.error(f"Error detecting unusual dynamics: {e}")
            return False
    
    def _classify_audio_threat(self, speech_confidence: float, propaganda_confidence: float, 
                             manipulation_indicators: List[str], transcription: str) -> str:
        """Classify audio threat type"""
        try:
            # Check for propaganda patterns in transcription
            transcription_lower = transcription.lower()
            propaganda_score = 0
            
            for category, patterns in self.propaganda_patterns.items():
                for pattern in patterns:
                    if pattern in transcription_lower:
                        propaganda_score += 1
            
            # Determine threat type
            if propaganda_score > 3 or propaganda_confidence > 0.8:
                return 'propaganda'
            elif 'subliminal' in str(manipulation_indicators):
                return 'subliminal_manipulation'
            elif 'binaural' in str(manipulation_indicators):
                return 'binaural_manipulation'
            elif speech_confidence > 0.7 and propaganda_score > 1:
                return 'manipulative_speech'
            elif len(manipulation_indicators) > 2:
                return 'audio_manipulation'
            else:
                return 'suspicious_audio'
                
        except Exception as e:
            self.logger.error(f"Error classifying audio threat: {e}")
            return 'unknown'
    
    def _determine_audio_severity(self, confidence: float, manipulation_indicators: List[str], 
                                threat_type: str) -> str:
        """Determine audio threat severity"""
        try:
            # High severity indicators
            high_severity_indicators = ['subliminal', 'binaural', 'hypnotic']
            
            # Check for high severity indicators
            has_high_severity = any(
                indicator in str(manipulation_indicators) 
                for indicator in high_severity_indicators
            )
            
            # Determine severity
            if threat_type == 'propaganda' and confidence > 0.8:
                return 'critical'
            elif has_high_severity and confidence > 0.7:
                return 'high'
            elif confidence > 0.6 or len(manipulation_indicators) > 3:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Error determining audio severity: {e}")
            return 'low'
    
    def _process_macos_audio_data(self, data: Dict):
        """Process macOS audio data"""
        try:
            audio_data = data.get('SPAudioDataType', [])
            
            for item in audio_data:
                if '_items' in item:
                    for device in item['_items']:
                        # Process audio device information
                        self._process_audio_device(device, 'macos')
                        
        except Exception as e:
            self.logger.error(f"Error processing macOS audio data: {e}")
    
    def _process_linux_audio_cards(self, cards: str):
        """Process Linux audio cards"""
        try:
            lines = cards.strip().split('\n')
            
            for line in lines:
                if 'audio' in line.lower():
                    # Process audio card information
                    self._process_audio_card(line, 'linux')
                    
        except Exception as e:
            self.logger.error(f"Error processing Linux audio cards: {e}")
    
    def _process_audio_device(self, device: Dict, platform: str):
        """Process audio device information"""
        try:
            device_name = device.get('_name', 'Unknown Device')
            
            # Check if device is active
            if device.get('sdevice_active', False):
                self.logger.debug(f"Active audio device detected: {device_name}")
                
        except Exception as e:
            self.logger.error(f"Error processing audio device: {e}")
    
    def _process_audio_card(self, card: str, platform: str):
        """Process audio card information"""
        try:
            # Extract card name and information
            if ':' in card:
                card_name = card.split(':', 1)[1].strip()
                self.logger.debug(f"Audio card detected: {card_name}")
                
        except Exception as e:
            self.logger.error(f"Error processing audio card: {e}")
    
    def _check_pulseaudio_streams(self):
        """Check PulseAudio streams on Linux"""
        try:
            # Use pactl to list audio streams
            result = subprocess.run(
                ['pactl', 'list', 'sinks'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self._process_pulseaudio_data(result.stdout)
                
        except Exception as e:
            self.logger.error(f"Error checking PulseAudio streams: {e}")
    
    def _process_pulseaudio_data(self, data: str):
        """Process PulseAudio data"""
        try:
            # Parse PulseAudio output for active streams
            lines = data.split('\n')
            
            for line in lines:
                if 'State: RUNNING' in line:
                    # Active audio stream found
                    self.logger.debug("Active PulseAudio stream detected")
                    
        except Exception as e:
            self.logger.error(f"Error processing PulseAudio data: {e}")
    
    def get_monitoring_statistics(self) -> Dict:
        """Get monitoring statistics"""
        try:
            total_threats = len(self.audio_threats)
            blocked_apps = len(self.blocked_applications)
            
            # Recent threats (last 24 hours)
            recent_time = datetime.now() - timedelta(hours=24)
            recent_threats = [t for t in self.audio_threats if t.timestamp > recent_time]
            
            # Threat type distribution
            threat_types = {}
            for threat in self.audio_threats:
                threat_type = threat.threat_type
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
            
            # Severity distribution
            severity_dist = {}
            for threat in self.audio_threats:
                severity = threat.severity
                severity_dist[severity] = severity_dist.get(severity, 0) + 1
            
            return {
                'total_threats': total_threats,
                'blocked_applications': blocked_apps,
                'recent_threats_24h': len(recent_threats),
                'active_streams': len(self.active_streams),
                'threat_types': threat_types,
                'severity_distribution': severity_dist,
                'monitoring_active': self.monitoring_active
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    monitor = RSecureAudioStreamMonitor()
    monitor.start_monitoring()
    
    try:
        while True:
            stats = monitor.get_monitoring_statistics()
            print(f"Audio Monitoring Statistics: {stats}")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Stopping audio monitoring...")
        monitor.stop_monitoring()
        print("Audio monitoring stopped.")
