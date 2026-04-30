#!/usr/bin/env python3
"""
Minimal RSecure Implementation
Working version with basic functionality
"""

import os
import sys
import time
import logging
import json
import threading
from datetime import datetime
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

class MinimalRSecure:
    """Minimal working RSecure system"""
    
    def __init__(self):
        self.running = False
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('rsecure.log')
            ]
        )
    
    def check_system_info(self):
        """Get system information"""
        try:
            import psutil
            import platform
            
            return {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat()
            }
        except ImportError as e:
            self.logger.error(f"Missing psutil: {e}")
            return None
    
    def check_ollama_status(self):
        """Check Ollama server status"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return {
                    'status': 'running',
                    'models': [m['name'] for m in models],
                    'count': len(models)
                }
            else:
                return {'status': 'error', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def basic_security_scan(self):
        """Perform basic security scan"""
        self.logger.info("Performing basic security scan...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'scan_results': {}
        }
        
        # Check network connections
        try:
            import psutil
            connections = psutil.net_connections()
            suspicious = [conn for conn in connections if conn.status == 'LISTEN' and conn.laddr.port > 10000]
            results['scan_results']['network'] = {
                'total_connections': len(connections),
                'listening_ports': len([c for c in connections if c.status == 'LISTEN']),
                'suspicious_high_ports': len(suspicious)
            }
        except Exception as e:
            results['scan_results']['network'] = {'error': str(e)}
        
        # Check running processes
        try:
            import psutil
            processes = list(psutil.process_iter(['pid', 'name', 'cmdline']))
            suspicious_names = ['nc', 'netcat', 'ncat', 'telnetd', 'sshd']
            suspicious_processes = [p for p in processes if p.info['name'] and any(s in p.info['name'].lower() for s in suspicious_names)]
            results['scan_results']['processes'] = {
                'total_processes': len(processes),
                'suspicious_processes': len(suspicious_processes),
                'suspicious_list': [p.info['name'] for p in suspicious_processes]
            }
        except Exception as e:
            results['scan_results']['processes'] = {'error': str(e)}
        
        return results
    
    def start_monitoring(self):
        """Start basic monitoring"""
        self.running = True
        self.logger.info("🛡️  RSecure monitoring started")
        
        def monitor_loop():
            while self.running:
                try:
                    # Get system info
                    sys_info = self.check_system_info()
                    if sys_info:
                        self.logger.info(f"System: CPU {sys_info['cpu_percent']:.1f}% | Memory {sys_info['memory_percent']:.1f}%")
                    
                    # Check Ollama
                    ollama_status = self.check_ollama_status()
                    if ollama_status['status'] == 'running':
                        self.logger.info(f"Ollama: {ollama_status['count']} models available")
                    
                    # Sleep for monitoring interval
                    time.sleep(30)
                    
                except Exception as e:
                    self.logger.error(f"Monitor error: {e}")
                    time.sleep(10)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        return monitor_thread
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.logger.info("🛑 RSecure monitoring stopped")
    
    def run_security_scan(self):
        """Run a one-time security scan"""
        self.logger.info("🔍 Starting security scan...")
        results = self.basic_security_scan()
        
        # Log results
        self.logger.info("Security scan results:")
        for category, data in results['scan_results'].items():
            if 'error' in data:
                self.logger.warning(f"  {category}: {data['error']}")
            else:
                self.logger.info(f"  {category}: {data}")
        
        return results

def main():
    """Main function"""
    print("🛡️  RSecure - Minimal Security System")
    print("=" * 50)
    
    # Create RSecure instance
    rsecure = MinimalRSecure()
    
    # Initial security scan
    scan_results = rsecure.run_security_scan()
    
    # Check Ollama status
    ollama_status = rsecure.check_ollama_status()
    print(f"\n🤖 Ollama Status: {ollama_status['status']}")
    if ollama_status['status'] == 'running':
        print(f"   Available models: {ollama_status['count']}")
        for model in ollama_status['models'][:3]:  # Show first 3
            print(f"   - {model}")
    
    # Start monitoring
    print("\n🚀 Starting continuous monitoring...")
    print("Press Ctrl+C to stop\n")
    
    try:
        monitor_thread = rsecure.start_monitoring()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping RSecure...")
        rsecure.stop()
        print("✅ RSecure stopped successfully")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        rsecure.stop()

if __name__ == "__main__":
    main()
