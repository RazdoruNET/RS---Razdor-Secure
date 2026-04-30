#!/usr/bin/env python3
"""
RSecure Phishing Attack Detection Layer
Advanced phishing detection using neural networks and behavioral analysis
"""

import re
import json
import time
import logging
import hashlib
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

@dataclass
class PhishingThreat:
    """Phishing threat information"""
    url: str
    threat_type: str
    confidence: float
    risk_score: float
    indicators: List[str]
    timestamp: datetime
    source: str
    metadata: Dict

class RSecurePhishingDetector:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Threat intelligence
        self.blacklisted_domains = set()
        self.suspicious_patterns = set()
        self.whitelisted_domains = set()
        
        # Neural network model
        self.model = None
        self.vectorizer = None
        
        # Detection history
        self.detection_history = []
        self.blocked_urls = set()
        
        # Threading
        self.running = False
        self.update_thread = None
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_phishing')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./phishing_detector.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize components
        self._initialize_neural_network()
        self._load_threat_intelligence()
    
    def _get_default_config(self) -> Dict:
        return {
            'model_path': './models/phishing_detector.h5',
            'update_interval': 3600,  # 1 hour
            'confidence_threshold': 0.7,
            'risk_threshold': 0.8,
            'max_url_length': 2048,
            'enable_real_time_detection': True,
            'enable_url_analysis': True,
            'enable_content_analysis': True,
            'enable_behavioral_analysis': True
        }
    
    def _initialize_neural_network(self):
        """Initialize neural network for phishing detection"""
        try:
            # Input layers
            url_input = layers.Input(shape=(200,), name='url_input')
            content_input = layers.Input(shape=(500,), name='content_input')
            behavior_input = layers.Input(shape=(50,), name='behavior_input')
            
            # URL analysis branch
            url_dense = layers.Dense(128, activation='relu')(url_input)
            url_dense = layers.Dropout(0.3)(url_dense)
            url_dense = layers.Dense(64, activation='relu')(url_dense)
            
            # Content analysis branch
            content_dense = layers.Dense(256, activation='relu')(content_input)
            content_dense = layers.Dropout(0.4)(content_dense)
            content_dense = layers.Dense(128, activation='relu')(content_dense)
            
            # Behavioral analysis branch
            behavior_dense = layers.Dense(64, activation='relu')(behavior_input)
            behavior_dense = layers.Dropout(0.2)(behavior_dense)
            behavior_dense = layers.Dense(32, activation='relu')(behavior_dense)
            
            # Concatenate branches
            concatenated = layers.concatenate([url_dense, content_dense, behavior_dense])
            
            # Final layers
            x = layers.Dense(128, activation='relu')(concatenated)
            x = layers.Dropout(0.5)(x)
            x = layers.Dense(64, activation='relu')(x)
            x = layers.Dense(32, activation='relu')(x)
            
            # Output layer
            output = layers.Dense(1, activation='sigmoid', name='phishing_probability')(x)
            
            # Create model
            self.model = keras.Model(
                inputs=[url_input, content_input, behavior_input],
                outputs=output
            )
            
            # Compile model
            self.model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', 'precision', 'recall']
            )
            
            self.logger.info("Neural network initialized for phishing detection")
            
        except Exception as e:
            self.logger.error(f"Error initializing neural network: {e}")
    
    def _load_threat_intelligence(self):
        """Load threat intelligence data"""
        try:
            # Load blacklisted domains
            self._load_blacklist()
            
            # Load suspicious patterns
            self._load_patterns()
            
            # Load whitelisted domains
            self._load_whitelist()
            
            self.logger.info(f"Loaded {len(self.blacklisted_domains)} blacklisted domains")
            
        except Exception as e:
            self.logger.error(f"Error loading threat intelligence: {e}")
    
    def _load_blacklist(self):
        """Load blacklisted domains"""
        # Common phishing indicators
        phishing_indicators = [
            'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
            'paypal-secure.com', 'secure-paypal.com', 'paypal-security.com',
            'microsoft-security.com', 'secure-microsoft.com',
            'google-secure.com', 'secure-google.com',
            'amazon-secure.com', 'secure-amazon.com',
            'facebook-secure.com', 'secure-facebook.com'
        ]
        
        self.blacklisted_domains.update(phishing_indicators)
    
    def _load_patterns(self):
        """Load suspicious URL patterns"""
        patterns = [
            r'https?://[^/]*\.tk',
            r'https?://[^/]*\.ml',
            r'https?://[^/]*\.ga',
            r'https?://[^/]*\.cf',
            r'https?://.*secure.*\.com',
            r'https?://.*verify.*\.com',
            r'https?://.*account.*\.com',
            r'https?://.*login.*\.com',
            r'https?://.*signin.*\.com',
            r'https?://.*update.*\.com',
            r'https?://.*confirm.*\.com',
            r'https?://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+',
            r'https?://.*\.bit\.ly',
            r'https?://.*\.tinyurl\.com',
            r'https?://.*\.t\.co'
        ]
        
        self.suspicious_patterns.update(patterns)
    
    def _load_whitelist(self):
        """Load whitelisted domains"""
        legitimate_domains = [
            'google.com', 'microsoft.com', 'apple.com', 'amazon.com',
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
            'github.com', 'stackoverflow.com', 'reddit.com', 'wikipedia.org',
            'youtube.com', 'netflix.com', 'spotify.com', 'dropbox.com'
        ]
        
        self.whitelisted_domains.update(legitimate_domains)
    
    def start_detection(self):
        """Start phishing detection"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        self.logger.info("Phishing detection started")
    
    def stop_detection(self):
        """Stop phishing detection"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=30)
        self.logger.info("Phishing detection stopped")
    
    def _update_loop(self):
        """Main update loop"""
        while self.running:
            try:
                self._update_threat_intelligence()
                time.sleep(self.config['update_interval'])
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                time.sleep(300)
    
    def _update_threat_intelligence(self):
        """Update threat intelligence from external sources"""
        try:
            # This would integrate with threat intelligence APIs
            # For now, we'll use static data
            pass
        except Exception as e:
            self.logger.error(f"Error updating threat intelligence: {e}")
    
    def analyze_url(self, url: str, content: str = None, context: Dict = None) -> PhishingThreat:
        """Analyze URL for phishing indicators"""
        try:
            # Basic URL validation
            if not url or len(url) > self.config['max_url_length']:
                return self._create_safe_threat(url)
            
            # Extract features
            url_features = self._extract_url_features(url)
            content_features = self._extract_content_features(content) if content else np.zeros(500)
            behavior_features = self._extract_behavior_features(context) if context else np.zeros(50)
            
            # Rule-based detection
            rule_based_score = self._rule_based_detection(url, content, context)
            
            # Neural network detection
            nn_score = self._neural_network_detection(url_features, content_features, behavior_features)
            
            # Combine scores
            final_score = self._combine_scores(rule_based_score, nn_score)
            
            # Determine threat type
            threat_type = self._classify_threat_type(url, content, final_score)
            
            # Extract indicators
            indicators = self._extract_indicators(url, content, final_score)
            
            # Create threat object
            threat = PhishingThreat(
                url=url,
                threat_type=threat_type,
                confidence=final_score,
                risk_score=self._calculate_risk_score(final_score, indicators),
                indicators=indicators,
                timestamp=datetime.now(),
                source='RSecure Phishing Detector',
                metadata={
                    'rule_based_score': rule_based_score,
                    'nn_score': nn_score,
                    'features': {
                        'url_features': url_features.tolist() if hasattr(url_features, 'tolist') else url_features,
                        'content_features': content_features.tolist() if hasattr(content_features, 'tolist') else content_features,
                        'behavior_features': behavior_features.tolist() if hasattr(behavior_features, 'tolist') else behavior_features
                    }
                }
            )
            
            # Log detection
            if final_score > self.config['confidence_threshold']:
                self.logger.warning(f"Phishing threat detected: {url} (confidence: {final_score:.3f})")
                self.detection_history.append(threat)
            
            return threat
            
        except Exception as e:
            self.logger.error(f"Error analyzing URL {url}: {e}")
            return self._create_safe_threat(url)
    
    def _extract_url_features(self, url: str) -> np.ndarray:
        """Extract features from URL"""
        try:
            parsed = urlparse(url)
            features = []
            
            # URL length
            features.append(len(url))
            
            # Domain length
            features.append(len(parsed.netloc))
            
            # Path length
            features.append(len(parsed.path))
            
            # Number of subdomains
            subdomain_count = len(parsed.netloc.split('.')) - 2
            features.append(subdomain_count)
            
            # Number of special characters
            special_chars = len(re.findall(r'[^a-zA-Z0-9\-\.\/]', url))
            features.append(special_chars)
            
            # Number of digits
            digits = len(re.findall(r'\d', url))
            features.append(digits)
            
            # HTTPS indicator
            features.append(1 if parsed.scheme == 'https' else 0)
            
            # IP address in URL
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            features.append(1 if re.search(ip_pattern, url) else 0)
            
            # Suspicious keywords
            suspicious_keywords = ['secure', 'verify', 'account', 'login', 'signin', 'update', 'confirm']
            keyword_count = sum(1 for keyword in suspicious_keywords if keyword in url.lower())
            features.append(keyword_count)
            
            # Domain entropy
            domain_entropy = self._calculate_entropy(parsed.netloc)
            features.append(domain_entropy)
            
            # URL entropy
            url_entropy = self._calculate_entropy(url)
            features.append(url_entropy)
            
            # Presence of @ symbol
            features.append(1 if '@' in url else 0)
            
            # Presence of - symbol in domain
            features.append(1 if '-' in parsed.netloc else 0)
            
            # Top-level domain
            tld = parsed.netloc.split('.')[-1] if '.' in parsed.netloc else ''
            suspicious_tlds = ['tk', 'ml', 'ga', 'cf', 'biz', 'info', 'work']
            features.append(1 if tld in suspicious_tlds else 0)
            
            # Pad to 200 features
            while len(features) < 200:
                features.append(0.0)
            
            return np.array(features[:200])
            
        except Exception as e:
            self.logger.error(f"Error extracting URL features: {e}")
            return np.zeros(200)
    
    def _extract_content_features(self, content: str) -> np.ndarray:
        """Extract features from content"""
        try:
            if not content:
                return np.zeros(500)
            
            features = []
            
            # Content length
            features.append(len(content))
            
            # Number of links
            link_count = len(re.findall(r'<a[^>]*href', content, re.IGNORECASE))
            features.append(link_count)
            
            # Number of forms
            form_count = len(re.findall(r'<form', content, re.IGNORECASE))
            features.append(form_count)
            
            # Number of input fields
            input_count = len(re.findall(r'<input', content, re.IGNORECASE))
            features.append(input_count)
            
            # Number of scripts
            script_count = len(re.findall(r'<script', content, re.IGNORECASE))
            features.append(script_count)
            
            # Suspicious keywords in content
            suspicious_keywords = [
                'verify', 'confirm', 'update', 'secure', 'account', 'login',
                'password', 'credit card', 'social security', 'bank account',
                'urgent', 'immediate', 'suspended', 'blocked', 'limited'
            ]
            
            keyword_count = sum(1 for keyword in suspicious_keywords if keyword.lower() in content.lower())
            features.append(keyword_count)
            
            # Presence of password fields
            password_fields = len(re.findall(r'type=["\']password["\']', content, re.IGNORECASE))
            features.append(password_fields)
            
            # Presence of hidden fields
            hidden_fields = len(re.findall(r'type=["\']hidden["\']', content, re.IGNORECASE))
            features.append(hidden_fields)
            
            # External resources
            external_resources = len(re.findall(r'src=["\']http', content, re.IGNORECASE))
            features.append(external_resources)
            
            # Content entropy
            content_entropy = self._calculate_entropy(content)
            features.append(content_entropy)
            
            # Pad to 500 features
            while len(features) < 500:
                features.append(0.0)
            
            return np.array(features[:500])
            
        except Exception as e:
            self.logger.error(f"Error extracting content features: {e}")
            return np.zeros(500)
    
    def _extract_behavior_features(self, context: Dict) -> np.ndarray:
        """Extract behavioral features"""
        try:
            if not context:
                return np.zeros(50)
            
            features = []
            
            # Time of day
            hour = datetime.now().hour
            features.append(hour)
            
            # Day of week
            day_of_week = datetime.now().weekday()
            features.append(day_of_week)
            
            # Referrer information
            referrer = context.get('referrer', '')
            features.append(len(referrer))
            
            # User agent
            user_agent = context.get('user_agent', '')
            features.append(len(user_agent))
            
            # IP information
            ip = context.get('ip', '')
            features.append(len(ip))
            
            # Geographic location (if available)
            location = context.get('location', {})
            features.append(len(str(location)))
            
            # Previous visits
            previous_visits = context.get('previous_visits', 0)
            features.append(previous_visits)
            
            # Session duration
            session_duration = context.get('session_duration', 0)
            features.append(session_duration)
            
            # Number of clicks
            clicks = context.get('clicks', 0)
            features.append(clicks)
            
            # Time spent on page
            time_on_page = context.get('time_on_page', 0)
            features.append(time_on_page)
            
            # Pad to 50 features
            while len(features) < 50:
                features.append(0.0)
            
            return np.array(features[:50])
            
        except Exception as e:
            self.logger.error(f"Error extracting behavioral features: {e}")
            return np.zeros(50)
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        try:
            if not text:
                return 0.0
            
            # Count character frequencies
            char_counts = {}
            for char in text:
                char_counts[char] = char_counts.get(char, 0) + 1
            
            # Calculate entropy
            entropy = 0.0
            text_length = len(text)
            
            for count in char_counts.values():
                probability = count / text_length
                entropy -= probability * np.log2(probability)
            
            return entropy
            
        except Exception:
            return 0.0
    
    def _rule_based_detection(self, url: str, content: str, context: Dict) -> float:
        """Rule-based phishing detection"""
        score = 0.0
        
        try:
            # Check blacklisted domains
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if domain in self.blacklisted_domains:
                score += 0.8
            
            # Check suspicious patterns
            for pattern in self.suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    score += 0.3
            
            # Check whitelisted domains
            if domain in self.whitelisted_domains:
                score -= 0.5
            
            # Check for IP address in URL
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            if re.search(ip_pattern, url):
                score += 0.4
            
            # Check for @ symbol
            if '@' in url:
                score += 0.3
            
            # Check URL length
            if len(url) > 100:
                score += 0.2
            
            # Check domain entropy
            domain_entropy = self._calculate_entropy(domain)
            if domain_entropy > 3.5:
                score += 0.2
            
            # Check content if available
            if content:
                # Check for password fields
                if 'password' in content.lower():
                    score += 0.1
                
                # Check for suspicious keywords
                suspicious_keywords = ['verify', 'confirm', 'update', 'secure', 'account']
                keyword_count = sum(1 for keyword in suspicious_keywords if keyword in content.lower())
                score += min(keyword_count * 0.1, 0.3)
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error in rule-based detection: {e}")
            return 0.0
    
    def _neural_network_detection(self, url_features: np.ndarray, content_features: np.ndarray, behavior_features: np.ndarray) -> float:
        """Neural network based detection"""
        try:
            if self.model is None:
                return 0.0
            
            # Prepare input
            url_input = np.expand_dims(url_features, axis=0)
            content_input = np.expand_dims(content_features, axis=0)
            behavior_input = np.expand_dims(behavior_features, axis=0)
            
            # Make prediction
            prediction = self.model.predict([url_input, content_input, behavior_input], verbose=0)
            
            return float(prediction[0][0])
            
        except Exception as e:
            self.logger.error(f"Error in neural network detection: {e}")
            return 0.0
    
    def _combine_scores(self, rule_based: float, neural: float) -> float:
        """Combine rule-based and neural network scores"""
        # Weighted combination
        combined = (rule_based * 0.6) + (neural * 0.4)
        return min(combined, 1.0)
    
    def _classify_threat_type(self, url: str, content: str, score: float) -> str:
        """Classify the type of phishing threat"""
        try:
            if score < 0.3:
                return 'safe'
            elif score < 0.5:
                return 'suspicious'
            elif score < 0.7:
                return 'phishing'
            else:
                return 'high_risk_phishing'
                
        except Exception:
            return 'unknown'
    
    def _extract_indicators(self, url: str, content: str, score: float) -> List[str]:
        """Extract phishing indicators"""
        indicators = []
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Domain indicators
            if domain in self.blacklisted_domains:
                indicators.append('blacklisted_domain')
            
            if len(domain) > 30:
                indicators.append('long_domain')
            
            if re.search(r'\d', domain):
                indicators.append('numeric_domain')
            
            # URL indicators
            if len(url) > 100:
                indicators.append('long_url')
            
            if '@' in url:
                indicators.append('at_symbol')
            
            if re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', url):
                indicators.append('ip_address')
            
            # Content indicators
            if content:
                if 'password' in content.lower():
                    indicators.append('password_field')
                
                if 'credit card' in content.lower():
                    indicators.append('credit_card_field')
                
                if len(re.findall(r'<form', content, re.IGNORECASE)) > 1:
                    indicators.append('multiple_forms')
            
            # Score indicators
            if score > 0.8:
                indicators.append('high_confidence')
            elif score > 0.6:
                indicators.append('medium_confidence')
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error extracting indicators: {e}")
            return []
    
    def _calculate_risk_score(self, confidence: float, indicators: List[str]) -> float:
        """Calculate overall risk score"""
        try:
            base_score = confidence
            
            # Adjust based on indicators
            high_risk_indicators = ['blacklisted_domain', 'ip_address', 'high_confidence']
            medium_risk_indicators = ['long_domain', 'at_symbol', 'password_field']
            
            for indicator in indicators:
                if indicator in high_risk_indicators:
                    base_score += 0.1
                elif indicator in medium_risk_indicators:
                    base_score += 0.05
            
            return min(base_score, 1.0)
            
        except Exception:
            return confidence
    
    def _create_safe_threat(self, url: str) -> PhishingThreat:
        """Create a safe threat object"""
        return PhishingThreat(
            url=url,
            threat_type='safe',
            confidence=0.0,
            risk_score=0.0,
            indicators=[],
            timestamp=datetime.now(),
            source='RSecure Phishing Detector',
            metadata={}
        )
    
    def get_detection_statistics(self) -> Dict:
        """Get detection statistics"""
        try:
            total_detections = len(self.detection_history)
            high_risk_count = len([t for t in self.detection_history if t.risk_score > 0.7])
            blocked_count = len(self.blocked_urls)
            
            # Recent detections (last 24 hours)
            recent_time = datetime.now() - timedelta(hours=24)
            recent_detections = [t for t in self.detection_history if t.timestamp > recent_time]
            
            return {
                'total_detections': total_detections,
                'high_risk_detections': high_risk_count,
                'blocked_urls': blocked_count,
                'recent_detections_24h': len(recent_detections),
                'blacklisted_domains': len(self.blacklisted_domains),
                'suspicious_patterns': len(self.suspicious_patterns),
                'whitelisted_domains': len(self.whitelisted_domains),
                'detection_running': self.running
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    detector = RSecurePhishingDetector()
    detector.start_detection()
    
    # Test URL analysis
    test_urls = [
        "https://www.google.com",
        "https://secure-paypal.com/login",
        "http://192.168.1.1/admin",
        "https://verify-account-urgent.com"
    ]
    
    for url in test_urls:
        threat = detector.analyze_url(url)
        print(f"URL: {url}")
        print(f"Threat Type: {threat.threat_type}")
        print(f"Confidence: {threat.confidence:.3f}")
        print(f"Risk Score: {threat.risk_score:.3f}")
        print(f"Indicators: {threat.indicators}")
        print("-" * 50)
    
    # Get statistics
    stats = detector.get_detection_statistics()
    print(f"Statistics: {stats}")
    
    detector.stop_detection()
