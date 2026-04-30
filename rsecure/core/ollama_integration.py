#!/usr/bin/env python3
"""
RSecure Ollama Integration
Local LLM integration for advanced security analysis
"""

import requests
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading

class OllamaSecurityAnalyzer:
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:1.5b"):
        self.ollama_url = ollama_url
        self.model = model
        self.logger = logging.getLogger('rsecure_ollama')
        self.logger.setLevel(logging.INFO)
        
        # Setup logging
        handler = logging.FileHandler('./logs/ollama_analysis.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Analysis cache
        self.analysis_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        # Verify Ollama connection
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama server is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model in model_names:
                    self.logger.info(f"Connected to Ollama with model: {self.model}")
                    return True
                else:
                    self.logger.warning(f"Model {self.model} not found. Available: {model_names}")
                    # Try to use an available model
                    if model_names:
                        self.model = model_names[0]
                        self.logger.info(f"Switched to available model: {self.model}")
                        return True
            else:
                self.logger.error("Ollama server not responding")
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
        return False
    
    def analyze_security_event(self, event_data: Dict) -> Dict:
        """Analyze security event using Ollama"""
        try:
            # Check cache first
            event_hash = hash(json.dumps(event_data, sort_keys=True))
            if event_hash in self.analysis_cache:
                cached_result = self.analysis_cache[event_hash]
                if time.time() - cached_result['timestamp'] < self.cache_timeout:
                    return cached_result['analysis']
            
            # Prepare prompt for security analysis
            prompt = self._prepare_security_prompt(event_data)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = self._parse_ollama_response(result['response'])
                
                # Cache result
                self.analysis_cache[event_hash] = {
                    'analysis': analysis,
                    'timestamp': time.time()
                }
                
                self.logger.info(f"Security analysis completed: {analysis['threat_level']}")
                return analysis
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return self._fallback_analysis(event_data)
                
        except Exception as e:
            self.logger.error(f"Error in security analysis: {e}")
            return self._fallback_analysis(event_data)
    
    def _prepare_security_prompt(self, event_data: Dict) -> str:
        """Prepare security analysis prompt"""
        prompt = f"""
You are a cybersecurity expert. Analyze the following security event and provide a detailed assessment.

Event Data:
{json.dumps(event_data, indent=2)}

Please analyze this event and provide:
1. Threat Level (safe/benign/suspicious/malicious/critical)
2. Confidence Score (0.0-1.0)
3. Risk Factors
4. Recommended Actions
5. Detailed Explanation

Respond in JSON format:
{{
    "threat_level": "suspicious",
    "confidence": 0.8,
    "risk_factors": ["factor1", "factor2"],
    "recommended_actions": ["action1", "action2"],
    "explanation": "detailed analysis"
}}
"""
        return prompt
    
    def _parse_ollama_response(self, response: str) -> Dict:
        """Parse Ollama response into structured format"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                analysis = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['threat_level', 'confidence', 'risk_factors', 'recommended_actions', 'explanation']
                for field in required_fields:
                    if field not in analysis:
                        analysis[field] = None
                
                # Normalize threat level
                valid_levels = ['safe', 'benign', 'suspicious', 'malicious', 'critical']
                if analysis['threat_level'] not in valid_levels:
                    analysis['threat_level'] = 'suspicious'
                
                # Normalize confidence
                try:
                    analysis['confidence'] = float(analysis['confidence'])
                    analysis['confidence'] = max(0.0, min(1.0, analysis['confidence']))
                except:
                    analysis['confidence'] = 0.5
                
                return analysis
            else:
                # Fallback parsing
                return {
                    'threat_level': 'suspicious',
                    'confidence': 0.5,
                    'risk_factors': ['unable_to_parse_response'],
                    'recommended_actions': ['manual_review'],
                    'explanation': response[:200]
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing Ollama response: {e}")
            return self._fallback_analysis({})
    
    def _fallback_analysis(self, event_data: Dict) -> Dict:
        """Fallback rule-based analysis"""
        return {
            'threat_level': 'suspicious',
            'confidence': 0.3,
            'risk_factors': ['ollama_unavailable'],
            'recommended_actions': ['check_ollama_status', 'manual_review'],
            'explanation': 'Ollama analysis unavailable - using fallback rule-based assessment'
        }
    
    def batch_analyze_events(self, events: List[Dict]) -> List[Dict]:
        """Analyze multiple events in batch"""
        results = []
        for event in events:
            result = self.analyze_security_event(event)
            results.append(result)
            # Small delay to avoid overwhelming Ollama
            time.sleep(0.1)
        return results
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            self.logger.error(f"Error getting models: {e}")
            return []
    
    def switch_model(self, new_model: str) -> bool:
        """Switch to different Ollama model"""
        available_models = self.get_available_models()
        if new_model in available_models:
            self.model = new_model
            self.logger.info(f"Switched to model: {new_model}")
            return True
        else:
            self.logger.error(f"Model {new_model} not available")
            return False

# Integration with RSecure Neural Core
class HybridSecurityAnalyzer:
    """Combines neural network and Ollama analysis"""
    
    def __init__(self, neural_core, ollama_analyzer):
        self.neural_core = neural_core
        self.ollama_analyzer = ollama_analyzer
        self.logger = logging.getLogger('rsecure_hybrid')
        
    def analyze_event(self, event_data: Dict, data_type: str) -> Dict:
        """Hybrid analysis using both neural and LLM approaches"""
        try:
            # Neural network analysis
            neural_result = None
            if hasattr(self.neural_core, '_analyze_data_type'):
                # Convert event data to features
                from .neural_security_core import FeatureExtractor
                
                if data_type == 'network':
                    features = FeatureExtractor.extract_network_features(event_data)
                elif data_type == 'process':
                    features = FeatureExtractor.extract_process_features(event_data)
                elif data_type == 'file':
                    features = FeatureExtractor.extract_file_features(event_data)
                elif data_type == 'system':
                    features = FeatureExtractor.extract_system_features(event_data)
                else:
                    features = None
                
                if features is not None:
                    self.neural_core.add_data(data_type, features)
                    neural_result = self.neural_core._analyze_data_type(data_type)
            
            # Ollama analysis
            ollama_result = self.ollama_analyzer.analyze_security_event(event_data)
            
            # Combine results
            combined_result = self._combine_analysis(neural_result, ollama_result)
            
            self.logger.info(f"Hybrid analysis completed: {combined_result['final_threat_level']}")
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Error in hybrid analysis: {e}")
            return {
                'final_threat_level': 'suspicious',
                'final_confidence': 0.3,
                'neural_result': None,
                'ollama_result': None,
                'error': str(e)
            }
    
    def _combine_analysis(self, neural_result: Dict, ollama_result: Dict) -> Dict:
        """Combine neural and LLM analysis results"""
        # Weight the results
        neural_weight = 0.6
        ollama_weight = 0.4
        
        # Convert threat levels to numeric scores
        threat_scores = {
            'safe': 0.0,
            'benign': 0.2,
            'suspicious': 0.4,
            'malicious': 0.6,
            'critical': 0.8
        }
        
        neural_score = 0.0
        neural_confidence = 0.0
        
        if neural_result and neural_result.get('status') == 'success':
            neural_score = neural_result.get('threat_score', 0.0)
            neural_confidence = neural_result.get('confidence', 0.0)
        
        ollama_score = threat_scores.get(ollama_result.get('threat_level', 'suspicious'), 0.4)
        ollama_confidence = ollama_result.get('confidence', 0.5)
        
        # Weighted combination
        final_score = (neural_score * neural_weight * neural_confidence + 
                      ollama_score * ollama_weight * ollama_confidence)
        
        # Convert back to threat level
        if final_score > 0.7:
            final_threat_level = 'critical'
        elif final_score > 0.5:
            final_threat_level = 'malicious'
        elif final_score > 0.3:
            final_threat_level = 'suspicious'
        elif final_score > 0.1:
            final_threat_level = 'benign'
        else:
            final_threat_level = 'safe'
        
        final_confidence = (neural_confidence * neural_weight + 
                           ollama_confidence * ollama_weight)
        
        return {
            'final_threat_level': final_threat_level,
            'final_confidence': final_confidence,
            'final_score': final_score,
            'neural_result': neural_result,
            'ollama_result': ollama_result,
            'recommendations': ollama_result.get('recommended_actions', []),
            'risk_factors': ollama_result.get('risk_factors', [])
        }

if __name__ == "__main__":
    # Test the Ollama integration
    analyzer = OllamaSecurityAnalyzer()
    
    # Test event
    test_event = {
        "timestamp": "2024-01-01T12:00:00Z",
        "event_type": "network_connection",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.1",
        "port": 22,
        "protocol": "TCP",
        "process_name": "ssh",
        "user": "admin"
    }
    
    result = analyzer.analyze_security_event(test_event)
    print("Analysis Result:")
    print(json.dumps(result, indent=2))
