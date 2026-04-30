#!/usr/bin/env python3
"""
RSecure Enhanced Version
Advanced security system with custom Ollama models and maximum functionality
"""

import os
import sys
import time
import logging
import json
import threading
import requests
from datetime import datetime
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

class EnhancedRSecure:
    """Enhanced RSecure with custom models and advanced features"""
    
    def __init__(self):
        self.running = False
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.load_config()
        
        # Ollama configuration
        self.ollama_url = self.config.get('ollama', {}).get('server_url', 'http://localhost:11434')
        self.available_models = []
        self.custom_models = []
        self.current_model = self.config.get('ollama', {}).get('default_model', 'rsecure-security')
        
        # Security components
        self.security_events = []
        self.threats_detected = []
        self.analysis_cache = {}
        
        # Metrics
        self.metrics = {
            'start_time': datetime.now(),
            'events_processed': 0,
            'threats_detected': 0,
            'llm_analyses': 0,
            'model_switches': 0,
            'cache_hits': 0
        }
        
        # Analysis modules
        self.analysis_modules = {
            'security': 'rsecure-security',
            'analyst': 'rsecure-analyst', 
            'scanner': 'rsecure-scanner'
        }
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_dir / 'rsecure_enhanced.log'),
                logging.FileHandler(log_dir / 'security_analysis.log'),
                logging.FileHandler(log_dir / 'threats.log')
            ]
        )
    
    def load_config(self):
        """Load configuration from file"""
        config_file = Path("config/rsecure_config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading config: {e}, using defaults")
        
        # Default configuration
        return {
            "ollama": {
                "server_url": "http://localhost:11434",
                "default_model": "rsecure-security",
                "fallback_models": ["qwen2.5-coder:1.5b", "rsecure-analyst"],
                "timeout": 30
            },
            "security": {
                "monitoring_interval": 30,
                "threat_threshold": 0.7,
                "auto_response": True,
                "cache_duration": 300
            },
            "modules": {
                "threat_detection": {"enabled": True},
                "vulnerability_scanning": {"enabled": True},
                "behavioral_analysis": {"enabled": True},
                "network_monitoring": {"enabled": True},
                "compliance_checking": {"enabled": True}
            }
        }
    
    def check_ollama_status(self):
        """Check Ollama server and available models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                self.available_models = [model['name'] for model in models]
                
                # Identify custom RSecure models
                self.custom_models = [model for model in self.available_models 
                                   if model.startswith('rsecure-')]
                
                self.logger.info(f"🤖 Ollama connected: {len(self.available_models)} models")
                self.logger.info(f"🛡️  Custom RSecure models: {len(self.custom_models)}")
                
                # Check if default model is available
                if self.current_model not in self.available_models:
                    self.logger.warning(f"Default model {self.current_model} not found")
                    # Find fallback
                    for fallback in self.config['ollama']['fallback_models']:
                        if fallback in self.available_models:
                            self.current_model = fallback
                            self.logger.info(f"Switched to fallback model: {fallback}")
                            break
                
                return True
            else:
                self.logger.error(f"❌ Ollama returned HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Cannot connect to Ollama: {e}")
            return False
    
    def analyze_with_custom_model(self, event_data, analysis_type="security", model_name=None):
        """Analyze event with custom RSecure model"""
        
        # Use specified model or default
        target_model = model_name or self.current_model
        
        # Check cache
        cache_key = f"{hash(str(event_data))}_{target_model}"
        if cache_key in self.analysis_cache:
            cache_time = self.analysis_cache[cache_key]['timestamp']
            if (datetime.now() - cache_time).seconds < self.config['security']['cache_duration']:
                self.metrics['cache_hits'] += 1
                return self.analysis_cache[cache_key]['result']
        
        try:
            self.metrics['llm_analyses'] += 1
            
            # Prepare analysis prompt based on type and model
            if analysis_type == "security":
                prompt = self._prepare_security_prompt(event_data)
            elif analysis_type == "vulnerability":
                prompt = self._prepare_vulnerability_prompt(event_data)
            elif analysis_type == "threat_hunting":
                prompt = self._prepare_threat_hunting_prompt(event_data)
            else:
                prompt = self._prepare_general_prompt(event_data)
            
            # Make request to Ollama
            payload = {
                "model": target_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2 if target_model.startswith('rsecure-') else 0.3,
                    "top_p": 0.8,
                    "num_ctx": 4096
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.config['ollama']['timeout']
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                # Parse structured response
                analysis = self._parse_analysis_response(analysis_text, target_model)
                
                # Cache result
                self.analysis_cache[cache_key] = {
                    'result': analysis,
                    'timestamp': datetime.now()
                }
                
                self.logger.info(f"🧠 Analysis completed with {target_model}")
                return analysis
                
            else:
                self.logger.error(f"❌ Analysis request failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Analysis error with {target_model}: {e}")
            return None
    
    def _prepare_security_prompt(self, event_data):
        """Prepare security analysis prompt"""
        return f"""Analyze this security event using RSecure methodology:

EVENT DATA:
{json.dumps(event_data, indent=2)}

ANALYSIS REQUIREMENTS:
1. Threat Level Assessment (low/medium/high/critical)
2. Attack Classification and MITRE ATT&CK mapping
3. Risk Factors and Impact Assessment
4. Immediate Response Actions
5. Long-term Security Recommendations
6. Compliance Implications

Respond with structured JSON analysis following RSecure framework."""
    
    def _prepare_vulnerability_prompt(self, event_data):
        """Prepare vulnerability scanning prompt"""
        return f"""Perform comprehensive vulnerability assessment:

TARGET DATA:
{json.dumps(event_data, indent=2)}

ASSESSMENT SCOPE:
1. Network Service Enumeration
2. Configuration Review
3. CVE Matching and Scoring
4. Exploitability Assessment
5. Remediation Prioritization
6. Compliance Framework Alignment

Provide detailed vulnerability report with CVSS scores and specific fix recommendations."""
    
    def _prepare_threat_hunting_prompt(self, event_data):
        """Prepare threat hunting prompt"""
        return f"""Advanced threat hunting analysis:

HUNTING DATA:
{json.dumps(event_data, indent=2)}

HUNTING METHODOLOGY:
1. Pattern Recognition and Anomaly Detection
2. Lateral Movement Analysis
3. Persistence Mechanisms Identification
4. Command and Control Detection
5. Data Exfiltration Indicators
6. Threat Actor Attribution

Apply threat intelligence frameworks and provide actionable hunting leads."""
    
    def _prepare_general_prompt(self, event_data):
        """Prepare general analysis prompt"""
        return f"""RSecure comprehensive analysis:

DATA:
{json.dumps(event_data, indent=2)}

Provide security-focused analysis with risk assessment and recommendations."""
    
    def _parse_analysis_response(self, response_text, model_name):
        """Parse structured analysis response"""
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
                
                # Add metadata
                analysis['metadata'] = {
                    'model_used': model_name,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'response_length': len(response_text)
                }
                
                return analysis
            else:
                # Fallback for non-JSON responses
                return {
                    'raw_analysis': response_text,
                    'metadata': {
                        'model_used': model_name,
                        'analysis_timestamp': datetime.now().isoformat(),
                        'response_type': 'unstructured'
                    }
                }
                
        except json.JSONDecodeError:
            return {
                'raw_analysis': response_text,
                'metadata': {
                    'model_used': model_name,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'parse_error': True
                }
            }
    
    def collect_comprehensive_events(self):
        """Collect comprehensive security events"""
        events = []
        
        try:
            import psutil
            
            # System metrics
            system_metrics = {
                'type': 'system_metrics',
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'timestamp': datetime.now().isoformat()
            }
            events.append(system_metrics)
            
            # Network connections analysis
            connections = psutil.net_connections()
            suspicious_connections = []
            
            for conn in connections:
                try:
                    if conn.status == 'ESTABLISHED':
                        if conn.raddr and conn.raddr.port in [22, 3389, 5432, 3306]:
                            suspicious_connections.append({
                                'type': 'sensitive_connection',
                                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}",
                                'status': conn.status,
                                'risk_factor': 'high',
                                'timestamp': datetime.now().isoformat()
                            })
                        elif conn.laddr and conn.laddr.port > 10000:
                            suspicious_connections.append({
                                'type': 'high_port_connection',
                                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                                'status': conn.status,
                                'risk_factor': 'medium',
                                'timestamp': datetime.now().isoformat()
                            })
                except (AttributeError, IndexError):
                    continue
            
            events.extend(suspicious_connections[:10])  # Limit to top 10
            
            # Process analysis
            high_risk_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    # High resource usage
                    if proc_info.get('cpu_percent', 0) > 80 or proc_info.get('memory_percent', 0) > 20:
                        high_risk_processes.append({
                            'type': 'high_resource_process',
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info.get('cpu_percent', 0),
                            'memory_percent': proc_info.get('memory_percent', 0),
                            'cmdline': proc_info.get('cmdline', []),
                            'risk_factor': 'medium',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # Suspicious process names
                    suspicious_names = ['nc', 'netcat', 'ncat', 'telnetd', 'sshd', 'bash', 'sh']
                    if proc_info.get('name') and any(s in proc_info['name'].lower() for s in suspicious_names):
                        high_risk_processes.append({
                            'type': 'suspicious_process',
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': proc_info.get('cmdline', []),
                            'risk_factor': 'high',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            events.extend(high_risk_processes[:5])  # Limit to top 5
            
        except ImportError:
            self.logger.warning("psutil not available for system monitoring")
        except Exception as e:
            self.logger.error(f"Error collecting events: {e}")
        
        return events
    
    def switch_analysis_model(self, analysis_type="security"):
        """Switch to appropriate analysis model"""
        target_model = self.analysis_modules.get(analysis_type, self.current_model)
        
        if target_model != self.current_model and target_model in self.available_models:
            self.current_model = target_model
            self.metrics['model_switches'] += 1
            self.logger.info(f"🔄 Switched to {target_model} for {analysis_type} analysis")
            return True
        elif target_model not in self.available_models:
            self.logger.warning(f"Model {target_model} not available")
            return False
        
        return True
    
    def process_events_with_enhanced_analysis(self, events):
        """Process events with enhanced analysis"""
        processed_events = []
        
        for event in events:
            self.metrics['events_processed'] += 1
            
            # Determine analysis type and switch model accordingly
            event_type = event.get('type', 'unknown')
            
            if event_type in ['system_metrics']:
                analysis_type = 'general'
                model_name = 'rsecure-analyst'
            elif event_type in ['sensitive_connection', 'suspicious_process']:
                analysis_type = 'security'
                model_name = 'rsecure-security'
            elif event_type in ['high_port_connection', 'high_resource_process']:
                analysis_type = 'vulnerability'
                model_name = 'rsecure-scanner'
            else:
                analysis_type = 'threat_hunting'
                model_name = 'rsecure-analyst'
            
            # Switch to appropriate model
            self.switch_analysis_model(analysis_type)
            
            # Analyze event
            analysis = self.analyze_with_custom_model(event, analysis_type, model_name)
            
            if analysis:
                event['enhanced_analysis'] = analysis
                
                # Check for threats
                threat_level = self._extract_threat_level(analysis)
                if threat_level in ['medium', 'high', 'critical']:
                    threat_event = {
                        'event': event,
                        'analysis': analysis,
                        'threat_level': threat_level,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.threats_detected.append(threat_event)
                    self.metrics['threats_detected'] += 1
                    
                    self.logger.warning(f"🚨 THREAT DETECTED: {threat_level.upper()}")
                    self.logger.warning(f"   Event: {event_type}")
                    self.logger.warning(f"   Model: {model_name}")
            
            processed_events.append(event)
        
        return processed_events
    
    def _extract_threat_level(self, analysis):
        """Extract threat level from analysis"""
        if 'threat_level' in analysis:
            return analysis['threat_level'].lower()
        elif 'risk_level' in analysis:
            return analysis['risk_level'].lower()
        elif 'severity' in analysis:
            return analysis['severity'].lower()
        else:
            return 'low'
    
    def enhanced_monitoring_loop(self):
        """Enhanced monitoring loop with model switching"""
        self.logger.info("🔄 Starting enhanced monitoring with custom models...")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                
                # Collect comprehensive events
                events = self.collect_comprehensive_events()
                
                # Process with enhanced analysis
                if events:
                    processed = self.process_events_with_enhanced_analysis(events)
                    self.security_events.extend(processed)
                    
                    # Log summary
                    self.logger.info(f"📊 Cycle {cycle_count}: {len(events)} events processed")
                    if len(self.threats_detected) > 0:
                        self.logger.warning(f"🚨 Total threats: {len(self.threats_detected)}")
                
                # Display enhanced status
                if cycle_count % 3 == 0:
                    self.display_enhanced_status()
                
                # Cleanup old cache entries
                if cycle_count % 10 == 0:
                    self._cleanup_cache()
                
                # Wait for next cycle
                time.sleep(self.config['security']['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Enhanced monitoring loop error: {e}")
                time.sleep(10)
    
    def _cleanup_cache(self):
        """Clean up old cache entries"""
        current_time = datetime.now()
        cache_duration = self.config['security']['cache_duration']
        
        keys_to_remove = []
        for key, value in self.analysis_cache.items():
            if (current_time - value['timestamp']).seconds > cache_duration:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.analysis_cache[key]
        
        if keys_to_remove:
            self.logger.info(f"🧹 Cleaned {len(keys_to_remove)} old cache entries")
    
    def display_enhanced_status(self):
        """Display enhanced system status"""
        uptime = datetime.now() - self.metrics['start_time']
        
        print(f"\n🛡️  RSecure Enhanced Status:")
        print(f"   ⏱️  Uptime: {uptime}")
        print(f"   📈 Events processed: {self.metrics['events_processed']}")
        print(f"   🧠 LLM analyses: {self.metrics['llm_analyses']}")
        print(f"   🚨 Threats detected: {self.metrics['threats_detected']}")
        print(f"   🔄 Model switches: {self.metrics['model_switches']}")
        print(f"   💾 Cache hits: {self.metrics['cache_hits']}")
        print(f"   🤖 Current model: {self.current_model}")
        print(f"   📦 Available models: {len(self.available_models)}")
        print(f"   🛡️  Custom models: {len(self.custom_models)}")
        
        if self.custom_models:
            print(f"   📋 Custom models: {', '.join(self.custom_models)}")
    
    def get_comprehensive_threat_summary(self):
        """Get comprehensive threat summary"""
        if not self.threats_detected:
            return {"total_threats": 0, "summary": "No threats detected"}
        
        summary = {
            'total_threats': len(self.threats_detected),
            'by_level': {},
            'by_type': {},
            'by_model': {},
            'recent_threats': [],
            'timeline': []
        }
        
        for threat in self.threats_detected[-10:]:  # Last 10 threats
            level = threat['threat_level']
            event_type = threat['event'].get('type', 'unknown')
            model_used = threat['analysis'].get('metadata', {}).get('model_used', 'unknown')
            
            # Count by level
            if level not in summary['by_level']:
                summary['by_level'][level] = 0
            summary['by_level'][level] += 1
            
            # Count by type
            if event_type not in summary['by_type']:
                summary['by_type'][event_type] = 0
            summary['by_type'][event_type] += 1
            
            # Count by model
            if model_used not in summary['by_model']:
                summary['by_model'][model_used] = 0
            summary['by_model'][model_used] += 1
            
            # Add to recent
            summary['recent_threats'].append({
                'timestamp': threat['timestamp'],
                'type': event_type,
                'level': level,
                'model': model_used
            })
            
            # Add to timeline
            summary['timeline'].append({
                'time': threat['timestamp'],
                'threat': level,
                'event': event_type
            })
        
        return summary
    
    def start(self):
        """Start enhanced RSecure"""
        self.logger.info("🛡️  Starting Enhanced RSecure with custom models...")
        
        # Check Ollama connection
        if not self.check_ollama_status():
            self.logger.error("❌ Cannot connect to Ollama. Please ensure Ollama is running.")
            return False
        
        self.running = True
        
        # Start enhanced monitoring
        monitor_thread = threading.Thread(target=self.enhanced_monitoring_loop, daemon=True)
        monitor_thread.start()
        
        self.logger.info("✅ Enhanced RSecure started successfully")
        return monitor_thread
    
    def stop(self):
        """Stop enhanced RSecure"""
        self.logger.info("🛑 Stopping Enhanced RSecure...")
        self.running = False
        
        # Log final metrics
        self.logger.info(f"📊 Final metrics: {self.metrics}")
        
        # Log threat summary
        threat_summary = self.get_comprehensive_threat_summary()
        self.logger.info(f"🚨 Comprehensive threat summary: {threat_summary}")
        
        self.logger.info("✅ Enhanced RSecure stopped")

def main():
    """Main function"""
    print("🛡️  RSecure Enhanced - Advanced Security System")
    print("=" * 60)
    print("🤖 Custom-trained security models")
    print("🧠 Intelligent threat analysis")
    print("🔄 Dynamic model switching")
    print("📊 Comprehensive monitoring")
    print("💾 Analysis caching")
    print("=" * 60)
    
    # Create enhanced RSecure instance
    rsecure = EnhancedRSecure()
    
    try:
        # Start system
        monitor_thread = rsecure.start()
        
        if not monitor_thread:
            print("❌ Failed to start Enhanced RSecure")
            return
        
        print("\n✅ Enhanced RSecure is running!")
        print(f"🤖 Available models: {len(rsecure.available_models)}")
        print(f"🛡️  Custom models: {len(rsecure.custom_models)}")
        print(f"📋 Current model: {rsecure.current_model}")
        
        if rsecure.custom_models:
            print(f"📦 Custom models: {', '.join(rsecure.custom_models)}")
        
        print("\n🔄 Analysis modules:")
        for analysis_type, model in rsecure.analysis_modules.items():
            status = "✅" if model in rsecure.available_models else "❌"
            print(f"   {status} {analysis_type}: {model}")
        
        print("\nPress Ctrl+C to stop")
        
        # Keep main thread alive
        while rsecure.running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping Enhanced RSecure...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        rsecure.stop()
        print("✅ Enhanced RSecure stopped successfully")

if __name__ == "__main__":
    main()
