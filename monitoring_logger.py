#!/usr/bin/env python3
"""
RSecure Continuous System Monitoring and Network Activity Logger
Provides real-time logging of system events, network traffic, and file changes
"""

import os
import sys
import time
import json
import threading
import subprocess
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
import socket
import psutil
import platform

class RSecureLogger:
    def __init__(self, log_dir: str = "/var/log/security_monitor", config: Dict = None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = config or self._get_default_config()
        self.running = False
        self.threads = []
        
        # Setup logging
        self._setup_logging()
        
        # Initialize monitoring components
        self.network_connections = set()
        self.process_registry = {}
        self.file_hashes = {}
        self.system_baseline = {}
        
        # Alert callbacks
        self.alert_callbacks = []
        
    def _get_default_config(self) -> Dict:
        return {
            'log_interval': 1,
            'network_scan_interval': 30,
            'file_scan_interval': 60,
            'max_log_size': 100 * 1024 * 1024,  # 100MB
            'log_retention_days': 30,
            'monitor_paths': [
                '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin',
                '/System/Library', '/Library', '/Applications'
            ],
            'network_ports': [22, 80, 443, 3306, 5432, 6379, 27017],
            'alert_threshold': 0.8
        }
    
    def _setup_logging(self):
        """Setup structured logging"""
        # Main security log
        self.rsecure_log = logging.getLogger('rsecure_monitor')
        self.rsecure_log.setLevel(logging.INFO)
        
        # File handler for main log
        main_handler = logging.FileHandler(
            self.log_dir / 'rsecure_main.log',
            mode='a',
            encoding='utf-8'
        )
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.rsecure_log.addHandler(main_handler)
        
        # Network log
        self.network_log = logging.getLogger('network_monitor')
        self.network_log.setLevel(logging.INFO)
        network_handler = logging.FileHandler(
            self.log_dir / 'network_activity.log',
            mode='a',
            encoding='utf-8'
        )
        network_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.network_log.addHandler(network_handler)
        
        # Process log
        self.process_log = logging.getLogger('process_monitor')
        self.process_log.setLevel(logging.INFO)
        process_handler = logging.FileHandler(
            self.log_dir / 'process_activity.log',
            mode='a',
            encoding='utf-8'
        )
        process_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.process_log.addHandler(process_handler)
        
        # File integrity log
        self.file_log = logging.getLogger('file_monitor')
        self.file_log.setLevel(logging.INFO)
        file_handler = logging.FileHandler(
            self.log_dir / 'file_integrity.log',
            mode='a',
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.file_log.addHandler(file_handler)
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        if self.running:
            return
        
        self.running = True
        self.rsecure_log.info("Starting RSecure monitoring system")
        
        # Start monitoring threads
        threads_config = [
            (self._monitor_system_resources, self.config['log_interval']),
            (self._monitor_network_connections, self.config['network_scan_interval']),
            (self._monitor_processes, self.config['log_interval']),
            (self._monitor_file_integrity, self.config['file_scan_interval']),
            (self._monitor_system_logs, self.config['log_interval']),
            (self._monitor_network_traffic, self.config['network_scan_interval'])
        ]
        
        for target, interval in threads_config:
            thread = threading.Thread(target=target, args=(interval,), daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # Create system baseline
        self._create_system_baseline()
        
        self.rsecure_log.info("RSecure monitoring system started successfully")
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        self.running = False
        self.rsecure_log.info("Stopping RSecure monitoring system")
        
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.rsecure_log.info("RSecure monitoring system stopped")
    
    def _monitor_system_resources(self, interval: int):
        """Monitor CPU, memory, disk usage"""
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_stats = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used,
                    'memory_total': memory.total,
                    'disk_percent': disk.percent,
                    'disk_used': disk.used,
                    'disk_total': disk.total,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
                
                self.rsecure_log.info(f"SYSTEM_STATS: {json.dumps(system_stats)}")
                
                # Check for anomalies
                if cpu_percent > 90 or memory.percent > 90:
                    self._trigger_rsecure_alert('HIGH_RESOURCE_USAGE', system_stats)
                
            except Exception as e:
                self.rsecure_log.error(f"Error monitoring system resources: {e}")
            
            time.sleep(interval)
    
    def _monitor_network_connections(self, interval: int):
        """Monitor network connections"""
        while self.running:
            try:
                current_connections = set()
                connections = psutil.net_connections()
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        conn_key = (conn.laddr, conn.raddr, conn.pid)
                        current_connections.add(conn_key)
                        
                        # Log new connections
                        if conn_key not in self.network_connections:
                            conn_info = {
                                'timestamp': datetime.now().isoformat(),
                                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                                'status': conn.status,
                                'pid': conn.pid,
                                'process_name': self._get_process_name(conn.pid) if conn.pid else "Unknown"
                            }
                            
                            self.network_log.info(f"NEW_CONNECTION: {json.dumps(conn_info)}")
                            
                            # Check suspicious connections
                            self._check_suspicious_connection(conn_info)
                
                # Check for closed connections
                closed_connections = self.network_connections - current_connections
                for conn in closed_connections:
                    conn_info = {
                        'timestamp': datetime.now().isoformat(),
                        'local_address': f"{conn[0].ip}:{conn[0].port}",
                        'remote_address': f"{conn[1].ip}:{conn[1].port}" if conn[1] else "N/A",
                        'pid': conn[2],
                        'event': 'CONNECTION_CLOSED'
                    }
                    self.network_log.info(f"CONNECTION_CLOSED: {json.dumps(conn_info)}")
                
                self.network_connections = current_connections
                
            except Exception as e:
                self.rsecure_log.error(f"Error monitoring network connections: {e}")
            
            time.sleep(interval)
    
    def _monitor_processes(self, interval: int):
        """Monitor process creation and termination"""
        while self.running:
            try:
                current_processes = {}
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                    try:
                        pinfo = proc.info
                        pid = pinfo['pid']
                        current_processes[pid] = pinfo
                        
                        # Check for new processes
                        if pid not in self.process_registry:
                            process_info = {
                                'timestamp': datetime.now().isoformat(),
                                'pid': pid,
                                'name': pinfo['name'],
                                'cmdline': pinfo['cmdline'],
                                'event': 'PROCESS_STARTED',
                                'parent_pid': proc.ppid(),
                                'user': proc.username()
                            }
                            
                            self.process_log.info(f"NEW_PROCESS: {json.dumps(process_info)}")
                            
                            # Check suspicious processes
                            self._check_suspicious_process(process_info)
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Check for terminated processes
                terminated_pids = set(self.process_registry.keys()) - set(current_processes.keys())
                for pid in terminated_pids:
                    process_info = {
                        'timestamp': datetime.now().isoformat(),
                        'pid': pid,
                        'name': self.process_registry[pid].get('name', 'Unknown'),
                        'event': 'PROCESS_TERMINATED'
                    }
                    self.process_log.info(f"PROCESS_TERMINATED: {json.dumps(process_info)}")
                
                self.process_registry = current_processes
                
            except Exception as e:
                self.rsecure_log.error(f"Error monitoring processes: {e}")
            
            time.sleep(interval)
    
    def _monitor_file_integrity(self, interval: int):
        """Monitor file integrity in critical paths"""
        while self.running:
            try:
                for path in self.config['monitor_paths']:
                    if os.path.exists(path):
                        self._scan_directory(path)
                
            except Exception as e:
                self.rsecure_log.error(f"Error monitoring file integrity: {e}")
            
            time.sleep(interval)
    
    def _scan_directory(self, directory: str):
        """Scan directory for file changes"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Calculate file hash
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        
                        file_key = file_path
                        
                        if file_key in self.file_hashes:
                            if self.file_hashes[file_key] != file_hash:
                                file_info = {
                                    'timestamp': datetime.now().isoformat(),
                                    'file_path': file_path,
                                    'old_hash': self.file_hashes[file_key],
                                    'new_hash': file_hash,
                                    'event': 'FILE_MODIFIED'
                                }
                                
                                self.file_log.info(f"FILE_MODIFIED: {json.dumps(file_info)}")
                                self._trigger_alert('FILE_INTEGRITY_VIOLATION', file_info)
                        else:
                            # New file
                            self.file_hashes[file_key] = file_hash
                            file_info = {
                                'timestamp': datetime.now().isoformat(),
                                'file_path': file_path,
                                'hash': file_hash,
                                'event': 'FILE_CREATED'
                            }
                            self.file_log.info(f"FILE_CREATED: {json.dumps(file_info)}")
                    
                    except (OSError, PermissionError):
                        continue
                        
        except Exception as e:
            self.file_log.error(f"Error scanning directory {directory}: {e}")
    
    def _monitor_system_logs(self, interval: int):
        """Monitor system logs for security events"""
        while self.running:
            try:
                system = platform.system()
                
                if system == 'Darwin':
                    log_files = ['/var/log/system.log', '/var/log/install.log']
                elif system == 'Linux':
                    log_files = ['/var/log/auth.log', '/var/log/syslog', '/var/log/messages']
                else:
                    log_files = []
                
                for log_file in log_files:
                    if os.path.exists(log_file):
                        self._parse_system_log(log_file)
                
            except Exception as e:
                self.rsecure_log.error(f"Error monitoring system logs: {e}")
            
            time.sleep(interval)
    
    def _parse_system_log(self, log_file: str):
        """Parse system log for security events"""
        try:
            # This is a simplified implementation
            # In production, you'd want to use log parsing libraries
            # and track file positions to avoid re-reading
            
            security_keywords = [
                'failed', 'denied', 'attack', 'intrusion', 'breach',
                'unauthorized', 'malware', 'virus', 'trojan', 'rootkit'
            ]
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if any(keyword in line.lower() for keyword in security_keywords):
                        log_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'source': log_file,
                            'message': line.strip(),
                            'event': 'SECURITY_LOG_ENTRY'
                        }
                        self.rsecure_log.warning(f"SECURITY_EVENT: {json.dumps(log_entry)}")
                        
        except Exception as e:
            self.rsecure_log.error(f"Error parsing system log {log_file}: {e}")
    
    def _monitor_network_traffic(self, interval: int):
        """Monitor network traffic statistics"""
        while self.running:
            try:
                net_io = psutil.net_io_counters()
                interfaces = psutil.net_io_counters(pernic=True)
                
                traffic_stats = {
                    'timestamp': datetime.now().isoformat(),
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'interfaces': {}
                }
                
                for interface, stats in interfaces.items():
                    traffic_stats['interfaces'][interface] = {
                        'bytes_sent': stats.bytes_sent,
                        'bytes_recv': stats.bytes_recv,
                        'packets_sent': stats.packets_sent,
                        'packets_recv': stats.packets_recv
                    }
                
                self.network_log.info(f"TRAFFIC_STATS: {json.dumps(traffic_stats)}")
                
            except Exception as e:
                self.rsecure_log.error(f"Error monitoring network traffic: {e}")
            
            time.sleep(interval)
    
    def _create_system_baseline(self):
        """Create baseline of system state"""
        try:
            self.system_baseline = {
                'timestamp': datetime.now().isoformat(),
                'hostname': socket.gethostname(),
                'platform': platform.platform(),
                'users': self._get_system_users(),
                'installed_packages': self._get_installed_packages(),
                'running_services': self._get_running_services(),
                'open_ports': self._get_open_ports()
            }
            
            baseline_file = self.log_dir / 'system_baseline.json'
            with open(baseline_file, 'w') as f:
                json.dump(self.system_baseline, f, indent=2)
            
            self.rsecure_log.info("System baseline created successfully")
            
        except Exception as e:
            self.rsecure_log.error(f"Error creating system baseline: {e}")
    
    def _get_process_name(self, pid: int) -> str:
        """Get process name from PID"""
        try:
            return psutil.Process(pid).name()
        except:
            return "Unknown"
    
    def _check_suspicious_connection(self, conn_info: Dict):
        """Check if connection is suspicious"""
        suspicious_indicators = [
            'remote_address' in conn_info and any(
                port in conn_info['remote_address'] for port in [':4444', ':5555', ':6666', ':7777', ':8888', ':9999']
            ),
            'process_name' in conn_info and conn_info['process_name'] in [
                'nc', 'netcat', 'telnet', 'ftp', 'tftp'
            ]
        ]
        
        if any(suspicious_indicators):
            self._trigger_rsecure_alert('SUSPICIOUS_NETWORK_CONNECTION', conn_info)
    
    def _check_suspicious_process(self, process_info: Dict):
        """Check if process is suspicious"""
        suspicious_names = [
            'nc', 'netcat', 'telnet', 'ftp', 'tftp', 'wget', 'curl',
            'ssh', 'scp', 'rsync', 'python', 'perl', 'ruby'
        ]
        
        if process_info.get('name') in suspicious_names:
            self._trigger_rsecure_alert('SUSPICIOUS_PROCESS', process_info)
    
    def _get_system_users(self) -> List[str]:
        """Get list of system users"""
        try:
            if platform.system() == 'Darwin':
                result = subprocess.run(['dscl', '.', 'list', '/Users'], 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(['cat', '/etc/passwd'], 
                                      capture_output=True, text=True)
            
            return result.stdout.strip().split('\n')
        except:
            return []
    
    def _get_installed_packages(self) -> List[str]:
        """Get list of installed packages"""
        try:
            if platform.system() == 'Darwin':
                result = subprocess.run(['brew', 'list'], capture_output=True, text=True)
            else:
                result = subprocess.run(['dpkg', '-l'], capture_output=True, text=True)
            
            return result.stdout.strip().split('\n')
        except:
            return []
    
    def _get_running_services(self) -> List[str]:
        """Get list of running services"""
        try:
            if platform.system() == 'Darwin':
                result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
            else:
                result = subprocess.run(['systemctl', 'list-units', '--type=service', '--state=running'], 
                                      capture_output=True, text=True)
            
            return result.stdout.strip().split('\n')
        except:
            return []
    
    def _get_open_ports(self) -> List[str]:
        """Get list of open ports"""
        try:
            result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
            return result.stdout.strip().split('\n')
        except:
            return []
    
    def _trigger_rsecure_alert(self, alert_type: str, data: Dict):
        """Trigger security alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'data': data,
            'severity': self._get_alert_severity(alert_type)
        }
        
        self.rsecure_log.warning(f"ALERT: {json.dumps(alert)}")
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.rsecure_log.error(f"Error in alert callback: {e}")
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """Get alert severity level"""
        severity_map = {
            'HIGH_RESOURCE_USAGE': 'medium',
            'SUSPICIOUS_NETWORK_CONNECTION': 'high',
            'SUSPICIOUS_PROCESS': 'high',
            'FILE_INTEGRITY_VIOLATION': 'critical',
            'SECURITY_LOG_ENTRY': 'medium'
        }
        return severity_map.get(alert_type, 'low')
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def get_recent_logs(self, log_type: str = 'security', lines: int = 100) -> List[str]:
        """Get recent log entries"""
        log_files = {
            'rsecure': 'rsecure_main.log',
            'network': 'network_activity.log',
            'process': 'process_activity.log',
            'file': 'file_integrity.log'
        }
        
        if log_type not in log_files:
            return []
        
        log_file = self.log_dir / log_files[log_type]
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except:
            return []

if __name__ == "__main__":
    # Example usage
    logger = RSecureLogger()
    
    def print_alert(alert):
        print(f"ALERT: {alert['type']} - {alert['severity']}")
    
    logger.add_alert_callback(print_alert)
    logger.start_monitoring()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.stop_monitoring()
