#!/usr/bin/env python3
"""
RSecure Active Network Defense Module
Provides proactive network defense capabilities with automated response
"""

import os
import sys
import socket
import struct
import threading
import time
import logging
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, deque
import scapy.all as scapy
import psutil
import netifaces
from dataclasses import dataclass

@dataclass
class NetworkThreat:
    """Network threat information"""
    source_ip: str
    target_port: int
    attack_type: str
    severity: str
    confidence: float
    packet_count: int
    first_seen: datetime
    last_seen: datetime
    metadata: Dict

@dataclass
class DefenseRule:
    """Network defense rule"""
    rule_id: str
    name: str
    condition: Dict
    action: str
    severity: str
    enabled: bool
    created_at: datetime

class RSecureNetworkDefense:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Network interfaces
        self.interfaces = self._get_network_interfaces()
        
        # Threat tracking
        self.active_threats = {}
        self.threat_history = deque(maxlen=10000)
        self.blocked_ips = set()
        self.monitored_ports = set(self.config['monitored_ports'])
        
        # Defense rules
        self.defense_rules = []
        self.custom_rules = []
        
        # Packet capture
        self.capture_thread = None
        self.analysis_thread = None
        self.packet_queue = deque(maxlen=10000)
        
        # Statistics
        self.stats = {
            'packets_captured': 0,
            'threats_detected': 0,
            'attacks_blocked': 0,
            'rules_triggered': 0,
            'start_time': datetime.now()
        }
        
        # Threading
        self.running = False
        
        # Setup logging
        log_dir = Path('./logs/security')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('rsecure_network_defense')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_dir / 'network_defense.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize defense rules
        self._initialize_defense_rules()
        
        # System detection
        self.system_type = self._detect_system_type()
    
    def _get_default_config(self) -> Dict:
        return {
            'monitored_ports': [22, 80, 443, 3389, 1433, 3306, 5432, 6379, 27017],
            'auto_block_threshold': 10,  # packets per minute
            'block_duration': 3600,  # 1 hour
            'max_block_duration': 86400,  # 24 hours
            'packet_capture_size': 65535,
            'analysis_interval': 5,  # seconds
            'enable_honeypot': True,
            'honeypot_ports': [8080, 8888, 9999],
            'enable_rate_limiting': True,
            'rate_limit_threshold': 100,  # connections per minute
            'enable_port_scanning_detection': True,
            'enable_ddos_detection': True,
            'enable_brute_force_detection': True,
            'enable_anomaly_detection': True
        }
    
    def _get_network_interfaces(self) -> List[Dict]:
        """Get available network interfaces"""
        interfaces = []
        
        try:
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        interfaces.append({
                            'name': interface,
                            'ip': addr['addr'],
                            'netmask': addr['netmask'],
                            'broadcast': addr.get('broadcast', '')
                        })
        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
        
        return interfaces
    
    def _detect_system_type(self) -> str:
        """Detect system type for appropriate commands"""
        import platform
        return platform.system()
    
    def _initialize_defense_rules(self):
        """Initialize default defense rules"""
        default_rules = [
            DefenseRule(
                rule_id="port_scan_detection",
                name="Port Scanning Detection",
                condition={
                    'type': 'port_scan',
                    'threshold': 10,
                    'time_window': 60
                },
                action="block_ip",
                severity="medium",
                enabled=True,
                created_at=datetime.now()
            ),
            DefenseRule(
                rule_id="brute_force_detection",
                name="Brute Force Attack Detection",
                condition={
                    'type': 'brute_force',
                    'threshold': 5,
                    'time_window': 300
                },
                action="block_ip",
                severity="high",
                enabled=True,
                created_at=datetime.now()
            ),
            DefenseRule(
                rule_id="ddos_detection",
                name="DDoS Attack Detection",
                condition={
                    'type': 'ddos',
                    'threshold': 1000,
                    'time_window': 60
                },
                action="block_ip",
                severity="critical",
                enabled=True,
                created_at=datetime.now()
            ),
            DefenseRule(
                rule_id="suspicious_traffic",
                name="Suspicious Traffic Pattern",
                condition={
                    'type': 'anomaly',
                    'threshold': 0.8
                },
                action="monitor_and_alert",
                severity="medium",
                enabled=True,
                created_at=datetime.now()
            )
        ]
        
        self.defense_rules = default_rules
    
    def start_defense(self):
        """Start network defense system"""
        if self.running:
            return
        
        self.running = True
        
        # Start packet capture
        self.capture_thread = threading.Thread(target=self._packet_capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start packet analysis
        self.analysis_thread = threading.Thread(target=self._packet_analysis_loop, daemon=True)
        self.analysis_thread.start()
        
        # Start honeypot if enabled
        if self.config['enable_honeypot']:
            self._start_honeypot()
        
        self.logger.info("RSecure network defense started")
    
    def stop_defense(self):
        """Stop network defense system"""
        self.running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=10)
        
        if self.analysis_thread:
            self.analysis_thread.join(timeout=10)
        
        self.logger.info("RSecure network defense stopped")
    
    def _packet_capture_loop(self):
        """Main packet capture loop"""
        try:
            # Create packet filter
            filter_expr = self._build_packet_filter()
            
            # Start packet capture
            scapy.sniff(
                filter=filter_expr,
                prn=self._process_packet,
                store=False,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            self.logger.error(f"Error in packet capture: {e}")
    
    def _build_packet_filter(self) -> str:
        """Build BPF filter for packet capture"""
        filters = []
        
        # Monitor specific ports
        port_filters = []
        for port in self.monitored_ports:
            port_filters.append(f"port {port}")
        
        if port_filters:
            filters.append(f"({' or '.join(port_filters)})")
        
        # Add honeypot ports
        if self.config['enable_honeypot']:
            honeypot_filters = []
            for port in self.config['honeypot_ports']:
                honeypot_filters.append(f"port {port}")
            
            if honeypot_filters:
                filters.append(f"({' or '.join(honeypot_filters)})")
        
        return " and ".join(filters) if filters else "tcp or udp"
    
    def _process_packet(self, packet):
        """Process captured packet"""
        try:
            self.stats['packets_captured'] += 1
            
            # Extract packet information
            packet_info = self._extract_packet_info(packet)
            
            if packet_info:
                self.packet_queue.append(packet_info)
        
        except Exception as e:
            self.logger.error(f"Error processing packet: {e}")
    
    def _extract_packet_info(self, packet) -> Optional[Dict]:
        """Extract information from packet"""
        try:
            info = {
                'timestamp': datetime.now(),
                'size': len(packet),
                'protocol': 'unknown'
            }
            
            # IP layer
            if packet.haslayer(scapy.IP):
                info.update({
                    'src_ip': packet[scapy.IP].src,
                    'dst_ip': packet[scapy.IP].dst,
                    'protocol': packet[scapy.IP].proto
                })
            
            # TCP layer
            if packet.haslayer(scapy.TCP):
                info.update({
                    'src_port': packet[scapy.TCP].sport,
                    'dst_port': packet[scapy.TCP].dport,
                    'flags': packet[scapy.TCP].flags,
                    'protocol': 'tcp'
                })
            
            # UDP layer
            elif packet.haslayer(scapy.UDP):
                info.update({
                    'src_port': packet[scapy.UDP].sport,
                    'dst_port': packet[scapy.UDP].dport,
                    'protocol': 'udp'
                })
            
            # Payload analysis
            if packet.haslayer(scapy.Raw):
                payload = packet[scapy.Raw].load
                info.update({
                    'payload_size': len(payload),
                    'payload_hash': hash(payload) % 10000
                })
            
            return info
        
        except Exception as e:
            self.logger.error(f"Error extracting packet info: {e}")
            return None
    
    def _packet_analysis_loop(self):
        """Main packet analysis loop"""
        while self.running:
            try:
                # Process packet queue
                packets_to_process = []
                
                while self.packet_queue and len(packets_to_process) < 100:
                    packets_to_process.append(self.packet_queue.popleft())
                
                if packets_to_process:
                    self._analyze_packets(packets_to_process)
                
                time.sleep(self.config['analysis_interval'])
            
            except Exception as e:
                self.logger.error(f"Error in packet analysis: {e}")
    
    def _analyze_packets(self, packets: List[Dict]):
        """Analyze packets for threats"""
        try:
            # Group packets by source IP
            packets_by_source = defaultdict(list)
            for packet in packets:
                src_ip = packet.get('src_ip')
                if src_ip:
                    packets_by_source[src_ip].append(packet)
            
            # Analyze each source
            for src_ip, source_packets in packets_by_source.items():
                self._analyze_source_packets(src_ip, source_packets)
            
        except Exception as e:
            self.logger.error(f"Error analyzing packets: {e}")
    
    def _analyze_source_packets(self, src_ip: str, packets: List[Dict]):
        """Analyze packets from specific source"""
        try:
            # Detect port scanning
            if self.config['enable_port_scanning_detection']:
                self._detect_port_scanning(src_ip, packets)
            
            # Detect brute force attacks
            if self.config['enable_brute_force_detection']:
                self._detect_brute_force(src_ip, packets)
            
            # Detect DDoS attacks
            if self.config['enable_ddos_detection']:
                self._detect_ddos(src_ip, packets)
            
            # Detect anomalies
            if self.config['enable_anomaly_detection']:
                self._detect_anomalies(src_ip, packets)
            
        except Exception as e:
            self.logger.error(f"Error analyzing source packets: {e}")
    
    def _detect_port_scanning(self, src_ip: str, packets: List[Dict]):
        """Detect port scanning activity"""
        try:
            # Count unique destination ports
            unique_ports = set()
            syn_packets = 0
            
            for packet in packets:
                dst_port = packet.get('dst_port')
                flags = packet.get('flags', 0)
                
                if dst_port:
                    unique_ports.add(dst_port)
                
                # Count SYN packets (potential port scan)
                if flags & 0x02:  # SYN flag
                    syn_packets += 1
            
            # Check threshold
            if len(unique_ports) >= self.config['auto_block_threshold']:
                threat = NetworkThreat(
                    source_ip=src_ip,
                    target_port=0,  # Multiple ports
                    attack_type="port_scan",
                    severity="medium",
                    confidence=0.8,
                    packet_count=len(packets),
                    first_seen=min(p['timestamp'] for p in packets),
                    last_seen=max(p['timestamp'] for p in packets),
                    metadata={
                        'unique_ports': len(unique_ports),
                        'syn_packets': syn_packets
                    }
                )
                
                self._handle_threat(threat)
        
        except Exception as e:
            self.logger.error(f"Error detecting port scanning: {e}")
    
    def _detect_brute_force(self, src_ip: str, packets: List[Dict]):
        """Detect brute force attacks"""
        try:
            # Group by target port
            packets_by_port = defaultdict(list)
            for packet in packets:
                dst_port = packet.get('dst_port')
                if dst_port:
                    packets_by_port[dst_port].append(packet)
            
            # Check each port for brute force patterns
            for dst_port, port_packets in packets_by_port.items():
                # Look for repeated connection attempts
                connection_attempts = 0
                failed_attempts = 0
                
                for packet in port_packets:
                    flags = packet.get('flags', 0)
                    
                    # SYN packets (connection attempts)
                    if flags & 0x02:
                        connection_attempts += 1
                    
                    # RST packets (failed connections)
                    if flags & 0x04:
                        failed_attempts += 1
                
                # Check brute force threshold
                if connection_attempts >= 5 and failed_attempts >= 3:
                    threat = NetworkThreat(
                        source_ip=src_ip,
                        target_port=dst_port,
                        attack_type="brute_force",
                        severity="high",
                        confidence=0.9,
                        packet_count=len(port_packets),
                        first_seen=min(p['timestamp'] for p in port_packets),
                        last_seen=max(p['timestamp'] for p in port_packets),
                        metadata={
                            'connection_attempts': connection_attempts,
                            'failed_attempts': failed_attempts
                        }
                    )
                    
                    self._handle_threat(threat)
        
        except Exception as e:
            self.logger.error(f"Error detecting brute force: {e}")
    
    def _detect_ddos(self, src_ip: str, packets: List[Dict]):
        """Detect DDoS attacks"""
        try:
            # Calculate packet rate
            if len(packets) < 2:
                return
            
            time_span = (packets[-1]['timestamp'] - packets[0]['timestamp']).total_seconds()
            if time_span == 0:
                return
            
            packet_rate = len(packets) / time_span
            
            # Check DDoS threshold
            if packet_rate >= 100:  # 100 packets per second
                threat = NetworkThreat(
                    source_ip=src_ip,
                    target_port=0,
                    attack_type="ddos",
                    severity="critical",
                    confidence=0.95,
                    packet_count=len(packets),
                    first_seen=packets[0]['timestamp'],
                    last_seen=packets[-1]['timestamp'],
                    metadata={
                        'packet_rate': packet_rate,
                        'time_span': time_span
                    }
                )
                
                self._handle_threat(threat)
        
        except Exception as e:
            self.logger.error(f"Error detecting DDoS: {e}")
    
    def _detect_anomalies(self, src_ip: str, packets: List[Dict]):
        """Detect anomalous traffic patterns"""
        try:
            # Analyze packet sizes
            packet_sizes = [p.get('size', 0) for p in packets]
            
            if len(packet_sizes) < 10:
                return
            
            # Calculate statistics
            avg_size = sum(packet_sizes) / len(packet_sizes)
            size_variance = sum((x - avg_size) ** 2 for x in packet_sizes) / len(packet_sizes)
            
            # Check for unusual patterns
            if size_variance > avg_size * 2:  # High variance
                threat = NetworkThreat(
                    source_ip=src_ip,
                    target_port=0,
                    attack_type="anomaly",
                    severity="medium",
                    confidence=0.7,
                    packet_count=len(packets),
                    first_seen=packets[0]['timestamp'],
                    last_seen=packets[-1]['timestamp'],
                    metadata={
                        'avg_packet_size': avg_size,
                        'size_variance': size_variance,
                        'anomaly_type': 'size_variance'
                    }
                )
                
                self._handle_threat(threat)
        
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
    
    def _handle_threat(self, threat: NetworkThreat):
        """Handle detected threat"""
        try:
            self.stats['threats_detected'] += 1
            
            # Check if threat already exists
            threat_key = f"{threat.source_ip}:{threat.attack_type}"
            
            if threat_key in self.active_threats:
                # Update existing threat
                existing_threat = self.active_threats[threat_key]
                existing_threat.packet_count += threat.packet_count
                existing_threat.last_seen = threat.last_seen
                existing_threat.confidence = max(existing_threat.confidence, threat.confidence)
            else:
                # New threat
                self.active_threats[threat_key] = threat
            
            # Apply defense rules
            self._apply_defense_rules(threat)
            
            # Log threat
            self.logger.warning(f"Threat detected: {threat.attack_type} from {threat.source_ip}")
            
        except Exception as e:
            self.logger.error(f"Error handling threat: {e}")
    
    def _apply_defense_rules(self, threat: NetworkThreat):
        """Apply defense rules to threat"""
        try:
            for rule in self.defense_rules:
                if not rule.enabled:
                    continue
                
                if self._evaluate_rule_condition(rule.condition, threat):
                    self._execute_defense_action(rule.action, threat)
                    self.stats['rules_triggered'] += 1
        
        except Exception as e:
            self.logger.error(f"Error applying defense rules: {e}")
    
    def _evaluate_rule_condition(self, condition: Dict, threat: NetworkThreat) -> bool:
        """Evaluate if rule condition matches threat"""
        try:
            condition_type = condition.get('type')
            
            if condition_type == threat.attack_type:
                threshold = condition.get('threshold', 0)
                
                if threat.attack_type == 'port_scan':
                    return threat.metadata.get('unique_ports', 0) >= threshold
                elif threat.attack_type == 'brute_force':
                    return threat.metadata.get('connection_attempts', 0) >= threshold
                elif threat.attack_type == 'ddos':
                    return threat.metadata.get('packet_rate', 0) >= threshold
                elif threat.attack_type == 'anomaly':
                    return threat.confidence >= threshold
            
            return False
        
        except Exception as e:
            self.logger.error(f"Error evaluating rule condition: {e}")
            return False
    
    def _execute_defense_action(self, action: str, threat: NetworkThreat):
        """Execute defense action"""
        try:
            if action == "block_ip":
                self._block_ip(threat.source_ip, threat.attack_type)
            elif action == "monitor_and_alert":
                self._monitor_and_alert(threat)
            elif action == "rate_limit":
                self._rate_limit_ip(threat.source_ip)
            elif action == "redirect_to_honeypot":
                self._redirect_to_honeypot(threat.source_ip)
            
        except Exception as e:
            self.logger.error(f"Error executing defense action {action}: {e}")
    
    def _block_ip(self, ip: str, reason: str = ""):
        """Block IP address"""
        try:
            if ip in self.blocked_ips:
                return
            
            self.blocked_ips.add(ip)
            self.stats['attacks_blocked'] += 1
            
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
                self.logger.info(f"Blocked IP {ip} due to {reason}")
                
                # Schedule unblocking
                threading.Timer(self.config['block_duration'], self._unblock_ip, args=[ip]).start()
            else:
                self.logger.error(f"Failed to block IP {ip}: {result.stderr}")
        
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip}: {e}")
    
    def _unblock_ip(self, ip: str):
        """Unblock IP address"""
        try:
            if ip not in self.blocked_ips:
                return
            
            self.blocked_ips.remove(ip)
            
            # System-specific unblocking
            if self.system_type == 'Darwin':
                cmd = f"sudo pfctl -t blocklist -T delete {ip}"
            elif self.system_type == 'Linux':
                cmd = f"sudo iptables -D INPUT -s {ip} -j DROP"
            else:
                return
            
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.logger.info(f"Unblocked IP {ip}")
        
        except Exception as e:
            self.logger.error(f"Error unblocking IP {ip}: {e}")
    
    def _monitor_and_alert(self, threat: NetworkThreat):
        """Monitor threat and send alert"""
        self.logger.warning(f"ALERT: {threat.attack_type} from {threat.source_ip} - Confidence: {threat.confidence}")
    
    def _rate_limit_ip(self, ip: str):
        """Apply rate limiting to IP"""
        try:
            if self.system_type == 'Linux':
                # Rate limiting with iptables
                cmd = f"sudo iptables -A INPUT -s {ip} -m limit --limit 10/min --limit-burst 20 -j ACCEPT"
                subprocess.run(cmd, shell=True, capture_output=True, text=True)
                self.logger.info(f"Applied rate limiting to IP {ip}")
        
        except Exception as e:
            self.logger.error(f"Error rate limiting IP {ip}: {e}")
    
    def _redirect_to_honeypot(self, ip: str):
        """Redirect IP to honeypot"""
        try:
            # This would redirect suspicious traffic to honeypot
            self.logger.info(f"Redirected IP {ip} to honeypot")
        
        except Exception as e:
            self.logger.error(f"Error redirecting IP {ip}: {e}")
    
    def _start_honeypot(self):
        """Start honeypot services"""
        try:
            # Start honeypot on configured ports
            for port in self.config['honeypot_ports']:
                honeypot_thread = threading.Thread(
                    target=self._run_honeypot,
                    args=(port,),
                    daemon=True
                )
                honeypot_thread.start()
            
            self.logger.info("Honeypot services started")
        
        except Exception as e:
            self.logger.error(f"Error starting honeypot: {e}")
    
    def _run_honeypot(self, port: int):
        """Run honeypot on specific port"""
        try:
            # Create simple honeypot server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(5)
            
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    self.logger.info(f"Honeypot connection from {address} on port {port}")
                    
                    # Log connection details
                    threat = NetworkThreat(
                        source_ip=address[0],
                        target_port=port,
                        attack_type="honeypot_access",
                        severity="medium",
                        confidence=1.0,
                        packet_count=1,
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        metadata={'honeypot_port': port}
                    )
                    
                    self._handle_threat(threat)
                    client_socket.close()
                
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.error(f"Error running honeypot on port {port}: {e}")
    
    def add_custom_rule(self, rule: DefenseRule):
        """Add custom defense rule"""
        self.custom_rules.append(rule)
        self.defense_rules.append(rule)
        self.logger.info(f"Added custom rule: {rule.name}")
    
    def get_defense_status(self) -> Dict:
        """Get current defense status"""
        return {
            'active_threats': len(self.active_threats),
            'blocked_ips': len(self.blocked_ips),
            'statistics': self.stats,
            'monitored_ports': list(self.monitored_ports),
            'defense_rules': len(self.defense_rules),
            'running': self.running,
            'uptime': (datetime.now() - self.stats['start_time']).total_seconds()
        }
    
    def get_threat_summary(self) -> List[Dict]:
        """Get summary of active threats"""
        threats = []
        
        for threat_key, threat in self.active_threats.items():
            threats.append({
                'source_ip': threat.source_ip,
                'attack_type': threat.attack_type,
                'severity': threat.severity,
                'confidence': threat.confidence,
                'packet_count': threat.packet_count,
                'first_seen': threat.first_seen.isoformat(),
                'last_seen': threat.last_seen.isoformat(),
                'metadata': threat.metadata
            })
        
        return threats

if __name__ == "__main__":
    # Example usage
    defense = RSecureNetworkDefense()
    defense.start_defense()
    
    try:
        while True:
            status = defense.get_defense_status()
            print(f"Defense Status: {status}")
            
            threats = defense.get_threat_summary()
            print(f"Active Threats: {len(threats)}")
            
            time.sleep(30)
    except KeyboardInterrupt:
        defense.stop_defense()
