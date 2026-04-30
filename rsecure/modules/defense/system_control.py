#!/usr/bin/env python3
"""
RSecure System Control Module
Provides direct system control capabilities for security response
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import psutil
import json
from pathlib import Path

class RSecureSystemControl:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.running = False
        self.control_thread = None
        
        # Action queue
        self.action_queue = []
        self.action_lock = threading.Lock()
        
        # Process tracking
        self.monitored_processes = {}
        self.blocked_processes = set()
        self.killed_processes = {}
        
        # Network controls
        self.blocked_ips = set()
        self.blocked_ports = set()
        self.allowed_connections = {}
        
        # File system controls
        self.protected_files = set()
        self.quarantined_files = {}
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_control')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./system_control.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # System detection
        self.system_type = self._detect_system_type()
        
    def _get_default_config(self) -> Dict:
        return {
            'auto_kill_threshold': 0.9,
            'auto_block_threshold': 0.8,
            'quarantine_dir': './quarantine',
            'max_kill_attempts': 3,
            'kill_timeout': 10,
            'network_block_duration': 3600,  # 1 hour
            'require_confirmation': False,
            'log_all_actions': True
        }
    
    def _detect_system_type(self) -> str:
        """Detect system type for appropriate commands"""
        import platform
        return platform.system()
    
    def start_control(self):
        """Start system control service"""
        if self.running:
            return
        
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        
        # Create quarantine directory
        Path(self.config['quarantine_dir']).mkdir(exist_ok=True)
        
        self.logger.info("RSecure system control started")
    
    def stop_control(self):
        """Stop system control service"""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=10)
        self.logger.info("RSecure system control stopped")
    
    def _control_loop(self):
        """Main control loop"""
        while self.running:
            try:
                # Process action queue
                self._process_action_queue()
                
                # Monitor system state
                self._monitor_system_state()
                
                # Enforce security policies
                self._enforce_policies()
                
            except Exception as e:
                self.logger.error(f"Error in control loop: {e}")
            
            time.sleep(1)
    
    def _process_action_queue(self):
        """Process pending security actions"""
        with self.action_lock:
            if not self.action_queue:
                return
            
            actions = self.action_queue.copy()
            self.action_queue.clear()
        
        for action in actions:
            try:
                self._execute_action(action)
            except Exception as e:
                self.logger.error(f"Error executing action {action}: {e}")
    
    def _execute_action(self, action: Dict):
        """Execute a security action"""
        action_type = action.get('type')
        target = action.get('target')
        severity = action.get('severity', 'medium')
        
        self.logger.info(f"Executing action: {action_type} on {target}")
        
        if action_type == 'kill_process':
            self._kill_process(target, action)
        elif action_type == 'block_ip':
            self._block_ip(target, action)
        elif action_type == 'block_port':
            self._block_port(target, action)
        elif action_type == 'quarantine_file':
            self._quarantine_file(target, action)
        elif action_type == 'isolate_system':
            self._isolate_system(action)
        elif action_type == 'shutdown_network':
            self._shutdown_network(action)
        elif action_type == 'restart_service':
            self._restart_service(target, action)
        else:
            self.logger.warning(f"Unknown action type: {action_type}")
    
    def kill_process(self, pid: int, reason: str = "", threat_score: float = 0.0):
        """Queue process termination"""
        action = {
            'type': 'kill_process',
            'target': pid,
            'reason': reason,
            'threat_score': threat_score,
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _kill_process(self, pid: int, action: Dict):
        """Kill a process"""
        try:
            # Check if process exists
            if not psutil.pid_exists(pid):
                self.logger.warning(f"Process {pid} does not exist")
                return
            
            process = psutil.Process(pid)
            
            # Log process details
            process_info = {
                'pid': pid,
                'name': process.name(),
                'cmdline': process.cmdline(),
                'parent': process.ppid(),
                'user': process.username(),
                'reason': action.get('reason', ''),
                'threat_score': action.get('threat_score', 0.0)
            }
            
            self.logger.info(f"Killing process: {process_info}")
            
            # Attempt graceful termination first
            for attempt in range(self.config['max_kill_attempts']):
                try:
                    process.terminate()
                    process.wait(timeout=self.config['kill_timeout'])
                    break
                except psutil.TimeoutExpired:
                    if attempt < self.config['max_kill_attempts'] - 1:
                        self.logger.warning(f"Process {pid} did not terminate gracefully, attempt {attempt + 1}")
                        time.sleep(1)
                    else:
                        # Force kill
                        process.kill()
                        process.wait(timeout=5)
            
            # Record the action
            self.killed_processes[pid] = {
                'timestamp': datetime.now().isoformat(),
                'process_info': process_info,
                'action': action
            }
            
            self.logger.info(f"Successfully killed process {pid}")
            
        except Exception as e:
            self.logger.error(f"Error killing process {pid}: {e}")
    
    def block_ip(self, ip: str, reason: str = "", duration: int = None):
        """Queue IP blocking"""
        action = {
            'type': 'block_ip',
            'target': ip,
            'reason': reason,
            'duration': duration or self.config['network_block_duration'],
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _block_ip(self, ip: str, action: Dict):
        """Block an IP address"""
        try:
            if ip in self.blocked_ips:
                self.logger.warning(f"IP {ip} is already blocked")
                return
            
            # Add to blocked set
            self.blocked_ips.add(ip)
            
            # System-specific blocking
            if self.system_type == 'Darwin':
                # macOS pfctl
                cmd = f"sudo pfctl -t blocklist -T add {ip}"
            elif self.system_type == 'Linux':
                # Linux iptables
                cmd = f"sudo iptables -A INPUT -s {ip} -j DROP"
            else:
                self.logger.error(f"Unsupported system for IP blocking: {self.system_type}")
                return
            
            # Execute blocking command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully blocked IP {ip}")
                
                # Schedule unblocking
                duration = action.get('duration', self.config['network_block_duration'])
                if duration > 0:
                    threading.Timer(duration, self._unblock_ip, args=[ip]).start()
            else:
                self.logger.error(f"Failed to block IP {ip}: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip}: {e}")
    
    def _unblock_ip(self, ip: str):
        """Unblock an IP address"""
        try:
            if ip not in self.blocked_ips:
                return
            
            # Remove from blocked set
            self.blocked_ips.remove(ip)
            
            # System-specific unblocking
            if self.system_type == 'Darwin':
                cmd = f"sudo pfctl -t blocklist -T delete {ip}"
            elif self.system_type == 'Linux':
                cmd = f"sudo iptables -D INPUT -s {ip} -j DROP"
            else:
                return
            
            # Execute unblocking command
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.logger.info(f"Unblocked IP {ip}")
            
        except Exception as e:
            self.logger.error(f"Error unblocking IP {ip}: {e}")
    
    def block_port(self, port: int, reason: str = "", duration: int = None):
        """Queue port blocking"""
        action = {
            'type': 'block_port',
            'target': port,
            'reason': reason,
            'duration': duration or self.config['network_block_duration'],
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _block_port(self, port: int, action: Dict):
        """Block a port"""
        try:
            if port in self.blocked_ports:
                self.logger.warning(f"Port {port} is already blocked")
                return
            
            self.blocked_ports.add(port)
            
            # System-specific port blocking
            if self.system_type == 'Darwin':
                # macOS pfctl
                cmd = f"sudo pfctl -f - << EOF\nblock in on any port {port}\nEOF"
            elif self.system_type == 'Linux':
                # Linux iptables
                cmd = f"sudo iptables -A INPUT -p tcp --dport {port} -j DROP"
            else:
                self.logger.error(f"Unsupported system for port blocking: {self.system_type}")
                return
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully blocked port {port}")
                
                # Schedule unblocking
                duration = action.get('duration', self.config['network_block_duration'])
                if duration > 0:
                    threading.Timer(duration, self._unblock_port, args=[port]).start()
            else:
                self.logger.error(f"Failed to block port {port}: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error blocking port {port}: {e}")
    
    def _unblock_port(self, port: int):
        """Unblock a port"""
        try:
            if port not in self.blocked_ports:
                return
            
            self.blocked_ports.remove(port)
            
            if self.system_type == 'Darwin':
                cmd = f"sudo pfctl -f - << EOF\npass in on any port {port}\nEOF"
            elif self.system_type == 'Linux':
                cmd = f"sudo iptables -D INPUT -p tcp --dport {port} -j DROP"
            else:
                return
            
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.logger.info(f"Unblocked port {port}")
            
        except Exception as e:
            self.logger.error(f"Error unblocking port {port}: {e}")
    
    def quarantine_file(self, file_path: str, reason: str = ""):
        """Queue file quarantine"""
        action = {
            'type': 'quarantine_file',
            'target': file_path,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _quarantine_file(self, file_path: str, action: Dict):
        """Quarantine a suspicious file"""
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File {file_path} does not exist")
                return
            
            # Generate quarantine filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            quarantine_path = os.path.join(
                self.config['quarantine_dir'],
                f"{timestamp}_{filename}"
            )
            
            # Move file to quarantine
            import shutil
            shutil.move(file_path, quarantine_path)
            
            # Record quarantine info
            self.quarantined_files[file_path] = {
                'quarantine_path': quarantine_path,
                'original_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'reason': action.get('reason', ''),
                'size': os.path.getsize(quarantine_path)
            }
            
            # Set restrictive permissions
            os.chmod(quarantine_path, 0o000)
            
            self.logger.info(f"Quarantined file {file_path} to {quarantine_path}")
            
        except Exception as e:
            self.logger.error(f"Error quarantining file {file_path}: {e}")
    
    def isolate_system(self, reason: str = ""):
        """Queue system isolation"""
        action = {
            'type': 'isolate_system',
            'target': 'system',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _isolate_system(self, action: Dict):
        """Isolate system from network"""
        try:
            self.logger.warning(f"SYSTEM ISOLATION INITIATED: {action.get('reason', '')}")
            
            # Block all incoming traffic
            if self.system_type == 'Darwin':
                # macOS pfctl
                subprocess.run("sudo pfctl -f /dev/stdin << EOF\nblock in all\npass out all\nEOF", 
                             shell=True)
            elif self.system_type == 'Linux':
                # Linux iptables
                subprocess.run("sudo iptables -P INPUT DROP", shell=True)
                subprocess.run("sudo iptables -P FORWARD DROP", shell=True)
                subprocess.run("sudo iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT", shell=True)
            
            self.logger.warning("System isolated from network")
            
        except Exception as e:
            self.logger.error(f"Error isolating system: {e}")
    
    def shutdown_network(self, reason: str = ""):
        """Queue network shutdown"""
        action = {
            'type': 'shutdown_network',
            'target': 'network',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _shutdown_network(self, action: Dict):
        """Shutdown network interfaces"""
        try:
            self.logger.critical(f"NETWORK SHUTDOWN INITIATED: {action.get('reason', '')}")
            
            # Get network interfaces
            interfaces = psutil.net_if_addrs().keys()
            
            for interface in interfaces:
                if interface == 'lo':  # Skip loopback
                    continue
                
                # Bring down interface
                if self.system_type == 'Darwin':
                    subprocess.run(f"sudo ifconfig {interface} down", shell=True)
                elif self.system_type == 'Linux':
                    subprocess.run(f"sudo ip link set {interface} down", shell=True)
            
            self.logger.critical("All network interfaces shutdown")
            
        except Exception as e:
            self.logger.error(f"Error shutting down network: {e}")
    
    def restart_service(self, service_name: str, reason: str = ""):
        """Queue service restart"""
        action = {
            'type': 'restart_service',
            'target': service_name,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        with self.action_lock:
            self.action_queue.append(action)
    
    def _restart_service(self, service_name: str, action: Dict):
        """Restart a system service"""
        try:
            self.logger.info(f"Restarting service {service_name}")
            
            if self.system_type == 'Darwin':
                # macOS launchctl
                subprocess.run(f"sudo launchctl unload /System/Library/LaunchDaemons/{service_name}.plist", 
                             shell=True)
                time.sleep(2)
                subprocess.run(f"sudo launchctl load /System/Library/LaunchDaemons/{service_name}.plist", 
                             shell=True)
            elif self.system_type == 'Linux':
                # Linux systemd
                subprocess.run(f"sudo systemctl restart {service_name}", shell=True)
            
            self.logger.info(f"Successfully restarted service {service_name}")
            
        except Exception as e:
            self.logger.error(f"Error restarting service {service_name}: {e}")
    
    def _monitor_system_state(self):
        """Monitor system for security violations"""
        try:
            # Monitor processes
            self._monitor_processes()
            
            # Monitor network connections
            self._monitor_connections()
            
            # Monitor file system
            self._monitor_filesystem()
            
        except Exception as e:
            self.logger.error(f"Error monitoring system state: {e}")
    
    def _monitor_processes(self):
        """Monitor for suspicious processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pid = proc.info['pid']
                    
                    # Check if process should be blocked
                    if pid in self.blocked_processes:
                        self.kill_process(pid, "Blocked process detected")
                        continue
                    
                    # Check for suspicious process names
                    name = proc.info.get('name', '').lower()
                    cmdline = proc.info.get('cmdline', [])
                    
                    suspicious_indicators = [
                        'nc', 'netcat', 'telnet', 'ftp', 'tftp',
                        'nmap', 'wireshark', 'tcpdump'
                    ]
                    
                    if any(indicator in name for indicator in suspicious_indicators):
                        self.logger.warning(f"Suspicious process detected: {name} (PID: {pid})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error monitoring processes: {e}")
    
    def _monitor_connections(self):
        """Monitor network connections"""
        try:
            connections = psutil.net_connections()
            
            for conn in connections:
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                    
                    # Check if IP is blocked
                    if remote_ip in self.blocked_ips:
                        self.kill_process(conn.pid, f"Connection to blocked IP {remote_ip}")
                        continue
                    
                    # Check for suspicious ports
                    if remote_port in [4444, 5555, 6666, 7777, 8888, 9999]:
                        self.logger.warning(f"Suspicious connection to {remote_ip}:{remote_port}")
                        
        except Exception as e:
            self.logger.error(f"Error monitoring connections: {e}")
    
    def _monitor_filesystem(self):
        """Monitor file system for suspicious activity"""
        try:
            # Check quarantine directory
            quarantine_dir = Path(self.config['quarantine_dir'])
            if quarantine_dir.exists():
                for file_path in quarantine_dir.glob("*"):
                    if file_path.is_file():
                        # Ensure quarantine files remain inaccessible
                        current_perms = oct(file_path.stat().st_mode)[-3:]
                        if current_perms != '000':
                            file_path.chmod(0o000)
                            
        except Exception as e:
            self.logger.error(f"Error monitoring filesystem: {e}")
    
    def _enforce_policies(self):
        """Enforce security policies"""
        try:
            # Auto-blocking based on threat scores
            # This would integrate with the neural core
            pass
            
        except Exception as e:
            self.logger.error(f"Error enforcing policies: {e}")
    
    def get_system_status(self) -> Dict:
        """Get current system control status"""
        return {
            'blocked_ips': list(self.blocked_ips),
            'blocked_ports': list(self.blocked_ports),
            'killed_processes': len(self.killed_processes),
            'quarantined_files': len(self.quarantined_files),
            'pending_actions': len(self.action_queue),
            'system_type': self.system_type,
            'running': self.running
        }
    
    def restore_quarantined_file(self, file_path: str) -> bool:
        """Restore a quarantined file"""
        try:
            if file_path not in self.quarantined_files:
                self.logger.error(f"File {file_path} not found in quarantine")
                return False
            
            quarantine_info = self.quarantined_files[file_path]
            quarantine_path = quarantine_info['quarantine_path']
            
            if not os.path.exists(quarantine_path):
                self.logger.error(f"Quarantined file {quarantine_path} not found")
                return False
            
            # Restore permissions
            os.chmod(quarantine_path, 0o644)
            
            # Move back to original location
            import shutil
            shutil.move(quarantine_path, file_path)
            
            # Remove from quarantine records
            del self.quarantined_files[file_path]
            
            self.logger.info(f"Restored quarantined file {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring file {file_path}: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    control = RSecureSystemControl()
    control.start_control()
    
    # Example actions
    control.kill_process(1234, "Suspicious process", 0.9)
    control.block_ip("192.168.1.100", "Malicious IP detected")
    control.quarantine_file("/tmp/suspicious.exe", "Malware detected")
    
    try:
        while True:
            status = control.get_system_status()
            print(f"System Status: {status}")
            time.sleep(10)
    except KeyboardInterrupt:
        control.stop_control()
