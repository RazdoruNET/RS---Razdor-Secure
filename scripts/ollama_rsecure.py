#!/usr/bin/env python3
"""
RSecure Ollama Integration
Focused version with Ollama LLM integration for security analysis
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

class OllamaRSecure:
    """RSecure with Ollama LLM integration"""
    
    def __init__(self):
        self.running = False
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Ollama configuration - Local server
        self.ollama_url = "http://127.0.0.1:11434"
        self.available_models = []
        self.current_model = "rsecure-security:latest"
        self.server_type = "local"
        
        # Security events
        self.security_events = []
        self.threats_detected = []
        
        # Metrics
        self.metrics = {
            'start_time': datetime.now(),
            'events_processed': 0,
            'llm_analyses': 0,
            'threats_detected': 0,
            'ollama_requests': 0
        }
        
    def setup_logging(self):
        """Setup logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_dir / 'ollama_rsecure.log'),
                logging.FileHandler(log_dir / 'security_analysis.log')
            ]
        )
    
    def check_ollama_status(self):
        """Check local Ollama server status and available models"""
        try:
            # Check Ollama API directly
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                self.logger.info(f"🤖 Local Ollama connected: {len(self.available_models)} models available")
                self.logger.info(f"📦 Available models: {', '.join(self.available_models[:3])}")
                return True
            else:
                self.logger.error(f"❌ Ollama API returned HTTP {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Cannot connect to local Ollama: {e}")
            return False
    
    def analyze_with_ollama(self, event_data, analysis_type="security"):
        """Analyze security event with Ollama"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                self.metrics['ollama_requests'] += 1
                self.logger.info(f"🤖 Запрос к Ollama #{self.metrics['ollama_requests']}: {analysis_type} (попытка {attempt + 1}/{max_retries})")
                
                # Prepare prompt based on analysis type
                if analysis_type == "security":
                    prompt = f"""
                    Analyze this security event and provide threat assessment:
                    
                    Event Data: {json.dumps(event_data, indent=2)}
                    
                    Please analyze:
                    1. Threat level (low/medium/high/critical)
                    2. Attack type if applicable
                    3. Recommended actions
                    4. Risk factors
                    
                    Respond in JSON format:
                    {{
                        "threat_level": "string",
                        "attack_type": "string",
                        "confidence": 0.0-1.0,
                        "recommended_actions": ["string"],
                        "risk_factors": ["string"],
                        "analysis": "string"
                    }}
                    """
                elif analysis_type == "system":
                    prompt = f"""
                    Analyze this system activity for security concerns:
                    
                    System Data: {json.dumps(event_data, indent=2)}
                    
                    Focus on:
                    1. Unusual processes or connections
                    2. Resource usage anomalies
                    3. Security vulnerabilities
                    4. Potential malware indicators
                    
                    Respond in JSON format:
                    {{
                        "security_concerns": ["string"],
                        "risk_level": "low/medium/high/critical",
                        "anomalies": ["string"],
                        "recommendations": ["string"]
                    }}
                    """
                
                # Make request to Ollama
                payload = {
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                }
                
                # Make API request to Ollama
                self.logger.info(f"📤 Отправка запроса к {self.ollama_url}/api/generate с моделью {self.current_model}")
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=120
                )
                
                self.logger.info(f"📥 Получен ответ HTTP {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    analysis_text = result.get('response', '')
                    
                    self.logger.info(f"📝 Ответ от Ollama: {analysis_text[:200]}...")
                    
                    # Try to parse JSON response
                    try:
                        # Extract JSON from response
                        start_idx = analysis_text.find('{')
                        end_idx = analysis_text.rfind('}') + 1
                        if start_idx != -1 and end_idx != -1:
                            json_str = analysis_text[start_idx:end_idx]
                            analysis = json.loads(json_str)
                            self.logger.info(f"✅ JSON успешно разобран: {list(analysis.keys())}")
                        else:
                            analysis = {"raw_analysis": analysis_text}
                            self.logger.warning("⚠️ Не найден JSON в ответе, использован raw_analysis")
                    except json.JSONDecodeError as e:
                        analysis = {"raw_analysis": analysis_text, "json_error": str(e)}
                        self.logger.warning(f"⚠️ Ошибка парсинга JSON: {e}")
                    
                    self.metrics['llm_analyses'] += 1
                    self.logger.info(f"🧠 LLM анализ #{self.metrics['llm_analyses']} завершен для {analysis_type}")
                    return analysis
                    
                else:
                    error_text = response.text if response.text else "No error text"
                    self.logger.error(f"❌ Запрос к Ollama провален: HTTP {response.status_code}")
                    self.logger.error(f"📄 Текст ошибки: {error_text[:200]}")
                    return None
                    
            except requests.exceptions.ReadTimeout as e:
                self.logger.warning(f"⏰ Таймаут запроса к Ollama (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"🔄 Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    self.logger.error(f"❌ Все попытки завершились таймаутом")
                    return None
            except Exception as e:
                self.logger.error(f"❌ Критическая ошибка LLM анализа (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"🔄 Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    import traceback
                    self.logger.error(f"🔍 Traceback: {traceback.format_exc()}")
                    return None
    
    def collect_system_events(self):
        """Collect system security events"""
        events = []
        
        try:
            import psutil
            
            # Network connections
            connections = psutil.net_connections()
            suspicious_connections = []
            
            for conn in connections:
                try:
                    if conn.status == 'ESTABLISHED':
                        if conn.laddr and conn.laddr.port > 10000:
                            suspicious_connections.append({
                                'type': 'network',
                                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                                'status': conn.status,
                                'timestamp': datetime.now().isoformat()
                            })
                except (AttributeError, IndexError):
                    continue
            
            events.extend(suspicious_connections)
            
            # Running processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 50 or proc_info['memory_percent'] > 10:
                        processes.append({
                            'type': 'process',
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent'],
                            'timestamp': datetime.now().isoformat()
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            events.extend(processes[:5])  # Limit to top 5
            
            # System metrics
            system_info = {
                'type': 'system_metrics',
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat()
            }
            
            events.append(system_info)
            
        except ImportError:
            self.logger.warning("psutil not available for system monitoring")
        except Exception as e:
            self.logger.error(f"Error collecting system events: {e}")
        
        return events
    
    def simulate_security_events(self):
        """Simulate security events for demonstration"""
        simulated_events = [
            {
                'type': 'network_intrusion',
                'source_ip': '192.168.1.100',
                'target_port': 22,
                'attack_pattern': 'brute_force',
                'attempts': 15,
                'timestamp': datetime.now().isoformat()
            },
            {
                'type': 'malware_detection',
                'file_path': '/tmp/suspicious_file.exe',
                'hash': 'a1b2c3d4e5f6...',
                'signature_match': True,
                'timestamp': datetime.now().isoformat()
            },
            {
                'type': 'anomalous_behavior',
                'user': 'admin',
                'action': 'privilege_escalation',
                'risk_score': 0.85,
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Return random event
        import random
        return [random.choice(simulated_events)]
    
    def process_events(self, events):
        """Process events with LLM analysis"""
        processed_events = []
        
        for event in events:
            self.metrics['events_processed'] += 1
            
            # Analyze with Ollama
            analysis = self.analyze_with_ollama(event, "security")
            
            if analysis:
                event['llm_analysis'] = analysis
                
                # Check for threats
                threat_level = analysis.get('threat_level', 'low').lower()
                if threat_level in ['medium', 'high', 'critical']:
                    self.threats_detected.append({
                        'event': event,
                        'analysis': analysis,
                        'timestamp': datetime.now().isoformat()
                    })
                    self.metrics['threats_detected'] += 1
                    
                    self.logger.warning(f"🚨 THREAT DETECTED: {threat_level.upper()}")
                    self.logger.warning(f"   Event: {event.get('type', 'unknown')}")
                    self.logger.warning(f"   Analysis: {analysis.get('analysis', 'No analysis')}")
            
            processed_events.append(event)
        
        return processed_events
    
    def monitor_loop(self):
        """Main monitoring loop with Ollama integration"""
        self.logger.info("🔄 Starting Ollama-powered monitoring loop...")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                
                # Collect real system events
                system_events = self.collect_system_events()
                
                # Add simulated events periodically for demonstration
                if cycle_count % 5 == 0:
                    simulated = self.simulate_security_events()
                    system_events.extend(simulated)
                    self.logger.info(f"🎭 Added {len(simulated)} simulated events for testing")
                
                # Process events with LLM
                if system_events:
                    processed = self.process_events(system_events)
                    self.security_events.extend(processed)
                    
                    # Log summary
                    self.logger.info(f"📊 Cycle {cycle_count}: Processed {len(system_events)} events")
                    if len(self.threats_detected) > 0:
                        self.logger.warning(f"🚨 Total threats detected: {len(self.threats_detected)}")
                
                # Display status
                if cycle_count % 3 == 0:
                    self.display_status()
                
                # Wait for next cycle
                time.sleep(20)  # 20 seconds between cycles
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(10)
    
    def display_status(self):
        """Display current system status"""
        uptime = datetime.now() - self.metrics['start_time']
        
        print(f"\n📊 RSecure Local Ollama Status:")
        print(f"   ⏱️  Uptime: {uptime}")
        print(f"   �️  Server type: {self.server_type}")
        print(f"   📈 Events processed: {self.metrics['events_processed']}")
        print(f"   🧠 LLM analyses: {self.metrics['llm_analyses']}")
        print(f"   🚨 Threats detected: {self.metrics['threats_detected']}")
        print(f"   🤖 Ollama requests: {self.metrics['ollama_requests']}")
        print(f"   📦 Current model: {self.current_model}")
        print(f"   💾 Available models: {len(self.available_models)}")
        print(f"   🔗 Provider: Local Ollama Server")
    
    def switch_model(self, model_name):
        """Switch to different Ollama model"""
        if model_name in self.available_models:
            self.current_model = model_name
            self.logger.info(f"🔄 Switched to model: {model_name}")
            return True
        else:
            self.logger.error(f"❌ Model {model_name} not available")
            return False
    
    def get_threat_summary(self):
        """Get summary of detected threats"""
        if not self.threats_detected:
            return "No threats detected"
        
        summary = {
            'total_threats': len(self.threats_detected),
            'by_level': {},
            'by_type': {},
            'recent_threats': []
        }
        
        for threat in self.threats_detected[-5:]:  # Last 5 threats
            analysis = threat['analysis']
            level = analysis.get('threat_level', 'unknown')
            event_type = threat['event'].get('type', 'unknown')
            
            # Count by level
            if level not in summary['by_level']:
                summary['by_level'][level] = 0
            summary['by_level'][level] += 1
            
            # Count by type
            if event_type not in summary['by_type']:
                summary['by_type'][event_type] = 0
            summary['by_type'][event_type] += 1
            
            # Add to recent
            summary['recent_threats'].append({
                'timestamp': threat['timestamp'],
                'type': event_type,
                'level': level,
                'analysis': analysis.get('analysis', 'No analysis')
            })
        
        return summary
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        if not self.running:
            self.running = True
            monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            monitor_thread.start()
            self.logger.info("🔄 Monitoring thread started")
            return monitor_thread
        else:
            self.logger.warning("⚠️ Monitoring is already running")
            return None
    
    def start(self):
        """Start Ollama RSecure"""
        self.logger.info("🛡️  Starting RSecure with Ollama integration...")
        
        # Check Ollama connection
        if not self.check_ollama_status():
            self.logger.error("❌ Cannot connect to Ollama. Please ensure Ollama is running.")
            return False
        
        self.start_monitoring()
        
        self.logger.info("✅ RSecure Ollama integration started successfully")
        return True
    
    def stop(self):
        """Stop Ollama RSecure"""
        self.logger.info("🛑 Stopping RSecure Ollama integration...")
        self.running = False
        
        # Log final metrics
        self.logger.info(f"📊 Final metrics: {self.metrics}")
        
        # Log threat summary
        threat_summary = self.get_threat_summary()
        self.logger.info(f"🚨 Threat summary: {threat_summary}")
        
        self.logger.info("✅ RSecure Ollama integration stopped")

def main():
    """Main function"""
    print("🛡️  RSecure - Ollama Integration")
    print("=" * 50)
    print("🤖 AI-powered security analysis with local LLM")
    print("🧠 Real-time threat detection and analysis")
    print("📊 Intelligent security monitoring")
    print("=" * 50)
    
    # Create RSecure instance
    rsecure = OllamaRSecure()
    
    try:
        # Start system
        monitor_thread = rsecure.start()
        
        if not monitor_thread:
            print("❌ Failed to start RSecure Ollama integration")
            return
        
        print("\n✅ RSecure Ollama is running!")
        print("🤖 Available models:")
        for i, model in enumerate(rsecure.available_models[:5]):  # Show first 5
            current = " (current)" if model == rsecure.current_model else ""
            print(f"   {i+1}. {model}{current}")
        
        print(f"\n📊 Total models available: {len(rsecure.available_models)}")
        print("Press Ctrl+C to stop\n")
        
        # Keep main thread alive
        while rsecure.running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping RSecure Ollama...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        rsecure.stop()
        print("✅ RSecure Ollama stopped successfully")

if __name__ == "__main__":
    main()
