#!/usr/bin/env python3
"""
RSecure Test Version - Simplified for testing without heavy dependencies
Tests core functionality without TensorFlow/Scapy requirements
"""

import os
import sys
import time
import threading
import logging
import json
import subprocess
import platform
from datetime import datetime
from pathlib import Path

class RSecureTest:
    """Simplified RSecure test version"""
    
    def __init__(self):
        self.running = False
        self.metrics = {
            'start_time': datetime.now(),
            'events_processed': 0,
            'threats_detected': 0,
            'system_checks': 0
        }
        
        # Setup logging
        self._setup_logging()
        
        # System detection
        self.system_info = self._detect_system()
        
        self.logger.info("RSecure Test Version Initialized")
        self.logger.info(f"System: {self.system_info}")
    
    def _setup_logging(self):
        """Setup logging system"""
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('rsecure_test')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / 'rsecure_test.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
    
    def _detect_system(self):
        """Detect system information"""
        try:
            system_info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor()
            }
            
            # Detect if MacBook
            if system_info['platform'] == 'Darwin':
                try:
                    result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                          capture_output=True, text=True, timeout=10)
                    hardware_info = result.stdout
                    
                    model_identifier = None
                    for line in hardware_info.split('\n'):
                        if 'Model Identifier:' in line:
                            model_identifier = line.split(':')[1].strip()
                            break
                    
                    system_info['model_identifier'] = model_identifier
                    system_info['type'] = 'macbook'
                    
                    # Check if pre-2012
                    if model_identifier and any(model_identifier.startswith(prefix) for prefix in [
                        'MacBook1,', 'MacBook2,', 'MacBook3,', 'MacBook4,', 'MacBook5,',
                        'MacBookPro1,', 'MacBookPro2,', 'MacBookPro3,', 'MacBookPro4,', 'MacBookPro5,'
                    ]):
                        system_info['is_pre_2012'] = True
                    else:
                        system_info['is_pre_2012'] = False
                
                except Exception as e:
                    self.logger.error(f"Error detecting MacBook model: {e}")
                    system_info['type'] = 'macbook'
                    system_info['is_pre_2012'] = False
            
            elif system_info['platform'] == 'Linux':
                system_info['type'] = 'linux_server'
                system_info['is_pre_2012'] = False
            
            else:
                system_info['type'] = 'unsupported'
                system_info['is_pre_2012'] = False
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"Error detecting system: {e}")
            return {'type': 'unknown', 'platform': 'unknown'}
    
    def start(self):
        """Start RSecure test system"""
        if self.running:
            self.logger.warning("RSecure is already running")
            return
        
        self.running = True
        self.logger.info("Starting RSecure Test System...")
        
        # Start monitoring threads
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.security_thread = threading.Thread(target=self._security_loop, daemon=True)
        self.security_thread.start()
        
        self.logger.info("RSecure Test System Started Successfully")
    
    def stop(self):
        """Stop RSecure test system"""
        self.running = False
        self.logger.info("RSecure Test System Stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_system_resources()
                self._check_network_connections()
                self._check_running_processes()
                self.metrics['system_checks'] += 1
                
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)
    
    def _security_loop(self):
        """Security analysis loop"""
        while self.running:
            try:
                self._analyze_security_state()
                self._check_for_anomalies()
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in security loop: {e}")
                time.sleep(15)
    
    def _check_system_resources(self):
        """Check system resources"""
        try:
            # CPU usage (simplified)
            cpu_usage = self._get_cpu_usage()
            
            # Memory usage (simplified)
            memory_usage = self._get_memory_usage()
            
            # Disk usage
            disk_usage = self._get_disk_usage()
            
            self.logger.info(f"System Resources - CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%")
            
            # Check for high resource usage
            if cpu_usage > 90 or memory_usage > 90:
                self._trigger_alert('HIGH_RESOURCE_USAGE', {
                    'cpu': cpu_usage,
                    'memory': memory_usage,
                    'disk': disk_usage
                })
        
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
    
    def _get_cpu_usage(self):
        """Get CPU usage"""
        try:
            if self.system_info['platform'] == 'Darwin':
                # macOS
                result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                      capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'CPU usage' in line:
                        # Extract CPU percentage from top output
                        parts = line.split(',')
                        if parts:
                            cpu_part = parts[0].strip()
                            if '%' in cpu_part:
                                return float(cpu_part.split('%')[0].split()[-1])
            elif self.system_info['platform'] == 'Linux':
                # Linux
                with open('/proc/loadavg', 'r') as f:
                    load_avg = float(f.read().split()[0])
                    return min(load_avg * 100, 100)  # Convert to percentage
            
            return 0.0
        except:
            return 0.0
    
    def _get_memory_usage(self):
        """Get memory usage"""
        try:
            if self.system_info['platform'] == 'Darwin':
                # macOS
                result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
                free_pages = 0
                total_pages = 0
                
                for line in result.stdout.split('\n'):
                    if 'free' in line:
                        free_pages = int(line.split(':')[1].strip().replace('.', ''))
                    elif 'Pages' in line and 'free' not in line:
                        total_pages += int(line.split(':')[1].strip().replace('.', ''))
                
                if total_pages > 0:
                    used_pages = total_pages - free_pages
                    return (used_pages / total_pages) * 100
            
            elif self.system_info['platform'] == 'Linux':
                # Linux
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    
                    total_mem = 0
                    free_mem = 0
                    
                    for line in meminfo.split('\n'):
                        if 'MemTotal:' in line:
                            total_mem = int(line.split()[1])
                        elif 'MemFree:' in line:
                            free_mem = int(line.split()[1])
                    
                    if total_mem > 0:
                        return ((total_mem - free_mem) / total_mem) * 100
            
            return 0.0
        except:
            return 0.0
    
    def _get_disk_usage(self):
        """Get disk usage"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 4:
                    usage_str = parts[4]
                    return int(usage_str.replace('%', ''))
            return 0.0
        except:
            return 0.0
    
    def _check_network_connections(self):
        """Check network connections"""
        try:
            if self.system_info['platform'] == 'Darwin':
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
            elif self.system_info['platform'] == 'Linux':
                result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True, timeout=5)
            else:
                return
            
            connections = result.stdout.split('\n')
            established_connections = [line for line in connections if 'ESTABLISHED' in line]
            
            self.logger.info(f"Network Connections - Established: {len(established_connections)}")
            
            # Check for suspicious connections
            if len(established_connections) > 50:
                self._trigger_alert('SUSPICIOUS_NETWORK_ACTIVITY', {
                    'connection_count': len(established_connections)
                })
        
        except Exception as e:
            self.logger.error(f"Error checking network connections: {e}")
    
    def _check_running_processes(self):
        """Check running processes"""
        try:
            if self.system_info['platform'] == 'Darwin':
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            elif self.system_info['platform'] == 'Linux':
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            else:
                return
            
            processes = result.stdout.split('\n')
            process_count = len([p for p in processes if p.strip()])
            
            self.logger.info(f"Running Processes: {process_count}")
            
            # Check for suspicious processes
            suspicious_keywords = ['nc', 'netcat', 'telnet', 'ftp', 'wget', 'curl']
            suspicious_processes = []
            
            for process in processes:
                for keyword in suspicious_keywords:
                    if keyword in process.lower():
                        suspicious_processes.append(process)
                        break
            
            if suspicious_processes:
                self._trigger_alert('SUSPICIOUS_PROCESS', {
                    'processes': suspicious_processes[:5]  # Limit to first 5
                })
        
        except Exception as e:
            self.logger.error(f"Error checking processes: {e}")
    
    def _analyze_security_state(self):
        """Analyze security state"""
        try:
            # Simulate security analysis
            security_score = self._calculate_security_score()
            
            self.logger.info(f"Security Score: {security_score}/100")
            
            if security_score < 70:
                self._trigger_alert('LOW_SECURITY_SCORE', {
                    'score': security_score
                })
        
        except Exception as e:
            self.logger.error(f"Error analyzing security state: {e}")
    
    def _calculate_security_score(self):
        """Calculate security score"""
        try:
            score = 100
            
            # Deduct points for various factors
            cpu_usage = self._get_cpu_usage()
            if cpu_usage > 80:
                score -= 10
            
            memory_usage = self._get_memory_usage()
            if memory_usage > 80:
                score -= 10
            
            # Check for open ports (simplified)
            if self.system_info['platform'] == 'Darwin':
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True, timeout=5)
            
            listening_ports = len([line for line in result.stdout.split('\n') if 'LISTEN' in line])
            if listening_ports > 10:
                score -= 5
            
            return max(0, score)
        
        except:
            return 50  # Default score
    
    def _check_for_anomalies(self):
        """Check for anomalies"""
        try:
            # Simulate anomaly detection
            anomalies = []
            
            # Check for unusual CPU usage pattern
            cpu_usage = self._get_cpu_usage()
            if cpu_usage > 95:
                anomalies.append('High CPU usage detected')
            
            # Check for unusual network activity
            if self.system_info['platform'] == 'Darwin':
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True, timeout=5)
            
            connections = result.stdout.split('\n')
            if len([c for c in connections if 'ESTABLISHED' in c]) > 100:
                anomalies.append('Unusual network activity')
            
            if anomalies:
                self._trigger_alert('ANOMALY_DETECTED', {
                    'anomalies': anomalies
                })
        
        except Exception as e:
            self.logger.error(f"Error checking anomalies: {e}")
    
    def _trigger_alert(self, alert_type, data):
        """Trigger security alert"""
        self.metrics['threats_detected'] += 1
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'data': data,
            'severity': self._get_alert_severity(alert_type)
        }
        
        self.logger.warning(f"ALERT: {alert_type} - {data}")
        self.metrics['events_processed'] += 1
    
    def _get_alert_severity(self, alert_type):
        """Get alert severity"""
        severity_map = {
            'HIGH_RESOURCE_USAGE': 'medium',
            'SUSPICIOUS_NETWORK_ACTIVITY': 'high',
            'SUSPICIOUS_PROCESS': 'high',
            'LOW_SECURITY_SCORE': 'medium',
            'ANOMALY_DETECTED': 'medium'
        }
        return severity_map.get(alert_type, 'low')
    
    def get_status(self):
        """Get system status"""
        uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
        
        return {
            'system_info': self.system_info,
            'running': self.running,
            'uptime_seconds': uptime,
            'metrics': self.metrics,
            'security_score': self._calculate_security_score()
        }

def main():
    """Main test function"""
    print("RSecure Test Version - Core Functionality Test")
    print("=" * 50)
    
    # Create and start RSecure test
    rsecure = RSecureTest()
    
    try:
        rsecure.start()
        
        print("RSecure Test is running. Press Ctrl+C to stop.")
        print("Testing core functionality...")
        
        # Test loop
        while rsecure.running:
            time.sleep(10)
            
            # Print status
            status = rsecure.get_status()
            print(f"\nStatus Update:")
            print(f"- System: {status['system_info']['type']}")
            print(f"- Uptime: {status['uptime_seconds']:.0f}s")
            print(f"- Events Processed: {status['metrics']['events_processed']}")
            print(f"- Threats Detected: {status['metrics']['threats_detected']}")
            print(f"- System Checks: {status['metrics']['system_checks']}")
            print(f"- Security Score: {status['security_score']}/100")
    
    except KeyboardInterrupt:
        print("\nShutting down RSecure Test...")
        rsecure.stop()
        print("RSecure Test stopped.")
    
    except Exception as e:
        print(f"Error: {e}")
        rsecure.stop()

if __name__ == "__main__":
    main()
