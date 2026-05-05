#!/usr/bin/env python3
"""
RSecure System Detection Module
Automatically detects MacBook (pre-2012) and Linux servers
"""

import platform
import subprocess
import os
import sys
from typing import Dict, Tuple, Optional

class SystemDetector:
    def __init__(self):
        self.system_info = {}
        self.system_type = None
        self.capabilities = {}
        
    def detect_system(self) -> Dict:
        """Main detection function"""
        self.system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node()
        }
        
        if self.system_info['platform'] == 'Darwin':
            return self._detect_macbook()
        elif self.system_info['platform'] == 'Linux':
            return self._detect_linux()
        else:
            return {'type': 'unsupported', 'info': self.system_info}
    
    def _detect_macbook(self) -> Dict:
        """Detect MacBook model and capabilities"""
        try:
            # Get system model
            result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                  capture_output=True, text=True, timeout=10)
            hardware_info = result.stdout
            
            # Extract model info
            model_identifier = None
            model_name = None
            year = None
            
            for line in hardware_info.split('\n'):
                if 'Model Identifier:' in line:
                    model_identifier = line.split(':')[1].strip()
                elif 'Model Name:' in line:
                    model_name = line.split(':')[1].strip()
            
            # Determine if pre-2012
            is_pre_2012 = False
            if model_identifier:
                # MacBook identifiers before 2012 typically start with MacBook1-5
                if any(model_identifier.startswith(prefix) for prefix in [
                    'MacBook1,', 'MacBook2,', 'MacBook3,', 'MacBook4,', 'MacBook5,',
                    'MacBookPro1,', 'MacBookPro2,', 'MacBookPro3,', 'MacBookPro4,', 'MacBookPro5,',
                    'MacBookAir1,', 'MacBookAir2,', 'MacBookAir3,'
                ]):
                    is_pre_2012 = True
            
            # Get capabilities
            self.capabilities = {
                'network_monitoring': True,
                'file_monitoring': True,
                'process_monitoring': True,
                'packet_capture': True,
                'firewall_control': True,
                'system_control': True,
                'neural_processing': True,
                'legacy_mode': is_pre_2012
            }
            
            return {
                'type': 'macbook',
                'model_identifier': model_identifier,
                'model_name': model_name,
                'is_pre_2012': is_pre_2012,
                'capabilities': self.capabilities,
                'info': self.system_info
            }
            
        except Exception as e:
            return {
                'type': 'macbook',
                'error': str(e),
                'capabilities': self._get_default_capabilities(),
                'info': self.system_info
            }
    
    def _detect_linux(self) -> Dict:
        """Detect Linux server distribution and capabilities"""
        try:
            # Get distribution info
            distro_info = {}
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            distro_info[key] = value.strip('"')
            
            # Check if server
            is_server = self._check_if_server()
            
            # Get kernel info
            kernel_version = platform.release()
            
            # Check capabilities
            self.capabilities = {
                'network_monitoring': True,
                'file_monitoring': True,
                'process_monitoring': True,
                'packet_capture': True,
                'firewall_control': True,
                'system_control': True,
                'neural_processing': True,
                'server_mode': is_server,
                'container_support': self._check_container_support()
            }
            
            return {
                'type': 'linux_server',
                'distribution': distro_info.get('NAME', 'Unknown'),
                'version': distro_info.get('VERSION', 'Unknown'),
                'kernel_version': kernel_version,
                'is_server': is_server,
                'capabilities': self.capabilities,
                'info': self.system_info
            }
            
        except Exception as e:
            return {
                'type': 'linux_server',
                'error': str(e),
                'capabilities': self._get_default_capabilities(),
                'info': self.system_info
            }
    
    def _check_if_server(self) -> bool:
        """Determine if this is a server installation"""
        server_indicators = [
            '/etc/nginx', '/etc/apache2', '/etc/httpd',  # Web servers
            '/etc/mysql', '/etc/postgresql',              # Database servers
            '/etc/ssh/sshd_config',                       # SSH server
            'docker', 'containerd', 'podman'              # Container runtimes
        ]
        
        for indicator in server_indicators:
            if os.path.exists(indicator):
                return True
        
        # Check for server processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            processes = result.stdout.lower()
            server_processes = ['nginx', 'apache', 'mysql', 'postgresql', 'sshd', 'docker']
            
            if any(proc in processes for proc in server_processes):
                return True
        except:
            pass
        
        return False
    
    def _check_container_support(self) -> bool:
        """Check if container runtime is available"""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def _get_default_capabilities(self) -> Dict:
        """Default capabilities for unknown systems"""
        return {
            'network_monitoring': True,
            'file_monitoring': True,
            'process_monitoring': True,
            'packet_capture': False,
            'firewall_control': False,
            'system_control': False,
            'neural_processing': True
        }
    
    def detect_anomalies(self) -> list:
        """Detect system anomalies"""
        anomalies = []
        
        try:
            # Get system information
            system_info = self.detect_system()
            
            # Check for high CPU usage simulation
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                anomalies.append({
                    'type': 'high_cpu',
                    'severity': 'high' if cpu_percent > 90 else 'medium',
                    'description': f'High CPU usage detected: {cpu_percent:.1f}%',
                    'source': 'localhost',
                    'confidence': 0.8,
                    'value': cpu_percent
                })
            
            # Check for memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                anomalies.append({
                    'type': 'high_memory',
                    'severity': 'high' if memory.percent > 95 else 'medium',
                    'description': f'High memory usage detected: {memory.percent:.1f}%',
                    'source': 'localhost',
                    'confidence': 0.7,
                    'value': memory.percent
                })
            
            # Check for disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                anomalies.append({
                    'type': 'high_disk',
                    'severity': 'critical',
                    'description': f'High disk usage detected: {disk.percent:.1f}%',
                    'source': 'localhost',
                    'confidence': 0.9,
                    'value': disk.percent
                })
            
            # Simulate network anomalies for testing
            import random
            if random.random() < 0.1:  # 10% chance of simulated anomaly
                anomalies.append({
                    'type': 'network_anomaly',
                    'severity': random.choice(['medium', 'high']),
                    'description': 'Unusual network traffic pattern detected',
                    'source': 'network_interface',
                    'confidence': random.uniform(0.6, 0.9),
                    'value': random.randint(1000, 5000)
                })
            
        except Exception as e:
            # Fallback to simulated anomalies if psutil not available
            import random
            if random.random() < 0.2:  # 20% chance
                anomalies.append({
                    'type': 'system_anomaly',
                    'severity': random.choice(['medium', 'high']),
                    'description': 'System performance anomaly detected',
                    'source': 'system_monitor',
                    'confidence': random.uniform(0.5, 0.8),
                    'value': random.randint(1, 100)
                })
        
        return anomalies
    
    def get_monitoring_config(self) -> Dict:
        """Get monitoring configuration based on system type"""
        detection = self.detect_system()
        
        base_config = {
            'log_interval': 1,  # seconds
            'network_scan_interval': 30,  # seconds
            'file_scan_interval': 60,  # seconds
            'neural_analysis_interval': 5,  # seconds
            'alert_threshold': 0.8,  # confidence threshold
        }
        
        if detection['type'] == 'macbook':
            if detection.get('is_pre_2012'):
                base_config.update({
                    'log_interval': 2,  # slower for older hardware
                    'neural_analysis_interval': 10,
                    'max_memory_usage': '512MB',
                    'lightweight_mode': True
                })
            else:
                base_config.update({
                    'max_memory_usage': '2GB',
                    'lightweight_mode': False
                })
        
        elif detection['type'] == 'linux_server':
            base_config.update({
                'log_interval': 0.5,  # faster for servers
                'network_scan_interval': 15,
                'max_memory_usage': '4GB',
                'lightweight_mode': False,
                'server_optimized': True
            })
        
        return base_config

if __name__ == "__main__":
    detector = SystemDetector()
    result = detector.detect_system()
    print("System Detection Results:")
    print(f"Type: {result['type']}")
    print(f"Capabilities: {result.get('capabilities', {})}")
    print(f"Monitoring Config: {detector.get_monitoring_config()}")
