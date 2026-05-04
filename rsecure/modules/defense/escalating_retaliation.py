#!/usr/bin/env python3
"""
Escalating Retaliation System
Advanced retaliation with graduated force escalation
"""

import os
import sys
import socket
import threading
import time
import logging
import subprocess
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import requests
import psutil
from pathlib import Path

class RetaliationLevel(Enum):
    """Levels of retaliation force"""
    WARNING = 1          # Initial warning
    DISRUPTION = 2       # Service disruption
    ISOLATION = 3        # Network isolation
    SYSTEM_DAMAGE = 4    # System component damage
    EQUIPMENT_DISABLE = 5 # Complete equipment disable
    TOTAL_BLOCKADE = 6   # Full blockade and destruction

class ThreatResponse(Enum):
    """Threat response effectiveness"""
    NO_RESPONSE = "no_response"
    MINOR_RESPONSE = "minor_response"
    MODERATE_RESPONSE = "moderate_response"
    STRONG_RESPONSE = "strong_response"
    COMPLETE_NEUTRALIZATION = "complete_neutralization"

@dataclass
class EscalationStep:
    """Single escalation step"""
    level: RetaliationLevel
    attack_type: str
    payload: Dict
    duration: int
    effectiveness_check: bool
    next_level_timeout: int

@dataclass
class TargetStatus:
    """Target status tracking"""
    target_ip: str
    current_level: RetaliationLevel
    attack_count: int
    last_attack_time: datetime
    response_level: ThreatResponse
    neutralized: bool
    equipment_disabled: bool
    blocked_ports: Set[int]
    compromised_services: Set[str]
    system_integrity: float  # 0.0 = destroyed, 1.0 = intact

class EscalatingRetaliationSystem:
    """Advanced retaliation with graduated force escalation"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Target management
        self.active_targets = {}
        self.target_history = []
        self.neutralized_targets = set()
        
        # Escalation management
        self.escalation_steps = self._initialize_escalation_steps()
        self.current_attacks = {}
        self.escalation_threads = {}
        
        # Attack modules
        self.network_attacks = NetworkAttackModule()
        self.system_attacks = SystemAttackModule()
        self.equipment_attacks = EquipmentAttackModule()
        
        # Monitoring
        self.response_monitor = ResponseMonitor()
        self.effectiveness_tracker = EffectivenessTracker()
        
        # Threading
        self.running = False
        self.monitoring_thread = None
        
        # Setup logging
        self.setup_logging()
        
        # Initialize attack modules
        self._initialize_modules()
    
    def _get_default_config(self) -> Dict:
        return {
            'auto_escalation': True,
            'escalation_threshold': 0.7,
            'max_escalation_level': 6,  # Total blockade
            'response_timeout': 30,  # 30 seconds per level
            'effectiveness_threshold': 0.8,
            'force_escalation_on_failure': True,
            'equipment_disable_enabled': True,
            'total_blockade_enabled': True,
            'monitoring_interval': 10,
            'max_concurrent_attacks': 10
        }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('escalating_retaliation')
        self.logger.setLevel(logging.INFO)
        
        # Multiple handlers for different aspects
        handlers = [
            logging.FileHandler(log_dir / 'escalation.log'),
            logging.FileHandler(log_dir / 'equipment_disable.log'),
            logging.FileHandler(log_dir / 'total_blockade.log')
        ]
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        for handler in handlers:
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _initialize_escalation_steps(self) -> List[EscalationStep]:
        """Initialize graduated escalation steps"""
        return [
            EscalationStep(
                level=RetaliationLevel.WARNING,
                attack_type="warning_notification",
                payload={
                    'type': 'fake_alerts',
                    'message': '⚠️ ВАША ДЕЯТЕЛЬНОСТЬ ОБНАРУЖЕНА - НЕМЕДЛЕННО ПРЕКРАТИТЕ!',
                    'severity': 'high'
                },
                duration=60,
                effectiveness_check=True,
                next_level_timeout=30
            ),
            EscalationStep(
                level=RetaliationLevel.DISRUPTION,
                attack_type="service_disruption",
                payload={
                    'type': 'port_blocking',
                    'target_ports': [80, 443, 22],
                    'block_duration': 300
                },
                duration=180,
                effectiveness_check=True,
                next_level_timeout=60
            ),
            EscalationStep(
                level=RetaliationLevel.ISOLATION,
                attack_type="network_isolation",
                payload={
                    'type': 'ip_blocking',
                    'block_method': 'firewall',
                    'isolation_duration': 600
                },
                duration=300,
                effectiveness_check=True,
                next_level_timeout=90
            ),
            EscalationStep(
                level=RetaliationLevel.SYSTEM_DAMAGE,
                attack_type="system_damage",
                payload={
                    'type': 'process_termination',
                    'target_processes': ['sshd', 'httpd', 'mysqld'],
                    'force_kill': True
                },
                duration=240,
                effectiveness_check=True,
                next_level_timeout=120
            ),
            EscalationStep(
                level=RetaliationLevel.EQUIPMENT_DISABLE,
                attack_type="equipment_disable",
                payload={
                    'type': 'hardware_disable',
                    'target_interfaces': ['eth0', 'wlan0'],
                    'disable_method': 'driver_unload'
                },
                duration=300,
                effectiveness_check=True,
                next_level_timeout=150
            ),
            EscalationStep(
                level=RetaliationLevel.TOTAL_BLOCKADE,
                attack_type="total_blockade",
                payload={
                    'type': 'complete_system_disable',
                    'disable_method': 'firmware_corruption',
                    'permanent': True
                },
                duration=600,
                effectiveness_check=True,
                next_level_timeout=180
            )
        ]
    
    def _initialize_modules(self):
        """Initialize attack modules"""
        try:
            self.network_attacks.initialize(self.config.get('network_attacks', {}))
            self.system_attacks.initialize(self.config.get('system_attacks', {}))
            self.equipment_attacks.initialize(self.config.get('equipment_attacks', {}))
            
            self.logger.info("🔥 Escalation retaliation modules initialized")
        except Exception as e:
            self.logger.error(f"Error initializing escalation modules: {e}")
    
    def start_escalation_system(self):
        """Start escalation retaliation system"""
        if self.running:
            return
        
        self.running = True
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("🔥 Escalating retaliation system started")
        self.logger.info(f"⚡ Auto-escalation: {'ENABLED' if self.config['auto_escalation'] else 'DISABLED'}")
        self.logger.info(f"🎯 Max escalation level: {self.config['max_escalation_level']}")
        self.logger.info(f"💥 Equipment disable: {'ENABLED' if self.config['equipment_disable_enabled'] else 'DISABLED'}")
        self.logger.info(f"🚫 Total blockade: {'ENABLED' if self.config['total_blockade_enabled'] else 'DISABLED'}")
    
    def stop_escalation_system(self):
        """Stop escalation retaliation system"""
        self.running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        # Stop all escalation threads
        for thread_id, thread in self.escalation_threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("🛑 Escalating retaliation system stopped")
    
    def add_target(self, target_info: Dict) -> bool:
        """Add target for escalating retaliation"""
        try:
            target_ip = target_info.get('ip')
            if not target_ip:
                return False
            
            # Initialize target status
            target_status = TargetStatus(
                target_ip=target_ip,
                current_level=RetaliationLevel.WARNING,
                attack_count=0,
                last_attack_time=datetime.now(),
                response_level=ThreatResponse.NO_RESPONSE,
                neutralized=False,
                equipment_disabled=False,
                blocked_ports=set(),
                compromised_services=set(),
                system_integrity=1.0
            )
            
            self.active_targets[target_ip] = target_status
            self.logger.warning(f"🎯 Added target for escalating retaliation: {target_ip}")
            
            # Start escalation process
            if self.config['auto_escalation']:
                self._start_escalation(target_ip)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding target: {e}")
            return False
    
    def _start_escalation(self, target_ip: str):
        """Start escalation process for target"""
        try:
            target_status = self.active_targets.get(target_ip)
            if not target_status:
                return
            
            # Start escalation thread
            escalation_thread = threading.Thread(
                target=self._escalation_loop,
                args=(target_ip,),
                daemon=True
            )
            
            self.escalation_threads[target_ip] = escalation_thread
            escalation_thread.start()
            
            self.logger.info(f"🔥 Started escalation process for {target_ip}")
            
        except Exception as e:
            self.logger.error(f"Error starting escalation for {target_ip}: {e}")
    
    def _escalation_loop(self, target_ip: str):
        """Main escalation loop for target"""
        try:
            target_status = self.active_targets.get(target_ip)
            if not target_status:
                return
            
            while self.running and not target_status.neutralized:
                current_step = self.escalation_steps[target_status.current_level.value - 1]
                
                # Execute current level attack
                success = self._execute_escalation_step(target_ip, current_step)
                
                if success:
                    target_status.attack_count += 1
                    target_status.last_attack_time = datetime.now()
                    
                    # Wait for response
                    time.sleep(current_step.next_level_timeout)
                    
                    # Check effectiveness
                    if current_step.effectiveness_check:
                        response = self._check_target_response(target_ip)
                        target_status.response_level = response
                        
                        # Determine if escalation is needed
                        if self._should_escalate(target_status, response):
                            self._escalate_to_next_level(target_ip)
                        else:
                            # Target is responding appropriately
                            self.logger.info(f"✅ Target {target_ip} responding appropriately at level {target_status.current_level.name}")
                            break
                    else:
                        # Auto-escalate
                        self._escalate_to_next_level(target_ip)
                else:
                    self.logger.error(f"❌ Failed to execute escalation step for {target_ip}")
                    if self.config['force_escalation_on_failure']:
                        self._escalate_to_next_level(target_ip)
                
                # Check if target is neutralized
                if target_status.system_integrity <= 0.1:
                    target_status.neutralized = True
                    self.neutralized_targets.add(target_ip)
                    self.logger.critical(f"🚫 Target {target_ip} COMPLETELY NEUTRALIZED")
                    break
                
                # Check max escalation level
                if target_status.current_level.value >= self.config['max_escalation_level']:
                    self.logger.critical(f"💥 Target {target_ip} reached MAXIMUM escalation level")
                    break
            
            # Move to history
            if target_ip in self.active_targets:
                self.target_history.append(self.active_targets.pop(target_ip))
            
        except Exception as e:
            self.logger.error(f"Error in escalation loop for {target_ip}: {e}")
    
    def _execute_escalation_step(self, target_ip: str, step: EscalationStep) -> bool:
        """Execute specific escalation step"""
        try:
            self.logger.warning(f"🔥 Executing {step.level.name} against {target_ip}")
            
            success = False
            
            if step.level in [RetaliationLevel.WARNING, RetaliationLevel.DISRUPTION]:
                success = self.network_attacks.execute_attack(target_ip, step.payload)
            elif step.level == RetaliationLevel.ISOLATION:
                success = self.network_attacks.execute_attack(target_ip, step.payload)
            elif step.level == RetaliationLevel.SYSTEM_DAMAGE:
                success = self.system_attacks.execute_attack(target_ip, step.payload)
            elif step.level == RetaliationLevel.EQUIPMENT_DISABLE:
                if self.config['equipment_disable_enabled']:
                    success = self.equipment_attacks.execute_attack(target_ip, step.payload)
                else:
                    self.logger.warning("Equipment disable is disabled")
                    success = False
            elif step.level == RetaliationLevel.TOTAL_BLOCKADE:
                if self.config['total_blockade_enabled']:
                    success = self.equipment_attacks.execute_attack(target_ip, step.payload)
                else:
                    self.logger.warning("Total blockade is disabled")
                    success = False
            
            if success:
                self.logger.info(f"✅ Successfully executed {step.level.name} against {target_ip}")
            else:
                self.logger.error(f"❌ Failed to execute {step.level.name} against {target_ip}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing escalation step: {e}")
            return False
    
    def _check_target_response(self, target_ip: str) -> ThreatResponse:
        """Check target's response to attacks"""
        try:
            # Simulate response checking
            response_level = random.choice([
                ThreatResponse.NO_RESPONSE,
                ThreatResponse.MINOR_RESPONSE,
                ThreatResponse.MODERATE_RESPONSE,
                ThreatResponse.STRONG_RESPONSE,
                ThreatResponse.COMPLETE_NEUTRALIZATION
            ])
            
            # Update target status
            target_status = self.active_targets.get(target_ip)
            if target_status:
                if response_level == ThreatResponse.COMPLETE_NEUTRALIZATION:
                    target_status.system_integrity = 0.0
                    target_status.neutralized = True
                elif response_level == ThreatResponse.STRONG_RESPONSE:
                    target_status.system_integrity = max(0.0, target_status.system_integrity - 0.3)
                elif response_level == ThreatResponse.MODERATE_RESPONSE:
                    target_status.system_integrity = max(0.0, target_status.system_integrity - 0.2)
                elif response_level == ThreatResponse.MINOR_RESPONSE:
                    target_status.system_integrity = max(0.0, target_status.system_integrity - 0.1)
            
            self.logger.info(f"📊 Target {target_ip} response: {response_level.value}")
            return response_level
            
        except Exception as e:
            self.logger.error(f"Error checking target response: {e}")
            return ThreatResponse.NO_RESPONSE
    
    def _should_escalate(self, target_status: TargetStatus, response: ThreatResponse) -> bool:
        """Determine if escalation should continue"""
        # Don't escalate if target is neutralized
        if target_status.neutralized:
            return False
        
        # Don't escalate if target is responding strongly
        if response in [ThreatResponse.STRONG_RESPONSE, ThreatResponse.COMPLETE_NEUTRALIZATION]:
            return False
        
        # Escalate if no response or weak response
        if response in [ThreatResponse.NO_RESPONSE, ThreatResponse.MINOR_RESPONSE]:
            return True
        
        # Check effectiveness threshold
        if target_status.system_integrity > self.config['effectiveness_threshold']:
            return True
        
        return False
    
    def _escalate_to_next_level(self, target_ip: str):
        """Escalate to next level"""
        try:
            target_status = self.active_targets.get(target_ip)
            if not target_status:
                return
            
            current_level = target_status.current_level
            next_level_value = current_level.value + 1
            
            if next_level_value <= self.config['max_escalation_level']:
                target_status.current_level = RetaliationLevel(next_level_value)
                self.logger.warning(f"⬆️ Escalated {target_ip} to {target_status.current_level.name}")
            else:
                self.logger.critical(f"🔥 {target_ip} already at maximum escalation level")
                
        except Exception as e:
            self.logger.error(f"Error escalating {target_ip}: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Monitor active targets
                for target_ip, target_status in list(self.active_targets.items()):
                    # Check if target is still active
                    if not self._is_target_active(target_ip):
                        target_status.neutralized = True
                        self.neutralized_targets.add(target_ip)
                        self.logger.info(f"✅ Target {target_ip} neutralized - no longer active")
                
                # Clean up completed escalation threads
                completed_threads = []
                for thread_id, thread in self.escalation_threads.items():
                    if not thread.is_alive():
                        completed_threads.append(thread_id)
                
                for thread_id in completed_threads:
                    del self.escalation_threads[thread_id]
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config['monitoring_interval'])
    
    def _is_target_active(self, target_ip: str) -> bool:
        """Check if target is still active/threatening"""
        try:
            # Simulate target activity check
            # In real scenario, this would check network traffic, system logs, etc.
            return random.choice([True, False, False])  # 33% chance still active
            
        except Exception as e:
            self.logger.error(f"Error checking target activity: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get escalation system status"""
        return {
            'running': self.running,
            'active_targets': len(self.active_targets),
            'neutralized_targets': len(self.neutralized_targets),
            'current_attacks': len(self.current_attacks),
            'escalation_threads': len(self.escalation_threads),
            'target_history': len(self.target_history),
            'configuration': {
                'auto_escalation': self.config['auto_escalation'],
                'max_escalation_level': self.config['max_escalation_level'],
                'equipment_disable_enabled': self.config['equipment_disable_enabled'],
                'total_blockade_enabled': self.config['total_blockade_enabled']
            }
        }
    
    def get_target_details(self, target_ip: str) -> Optional[Dict]:
        """Get detailed information about target"""
        target_status = self.active_targets.get(target_ip)
        if not target_status:
            return None
        
        return {
            'target_ip': target_status.target_ip,
            'current_level': target_status.current_level.name,
            'attack_count': target_status.attack_count,
            'last_attack_time': target_status.last_attack_time.isoformat(),
            'response_level': target_status.response_level.value,
            'neutralized': target_status.neutralized,
            'equipment_disabled': target_status.equipment_disabled,
            'blocked_ports': list(target_status.blocked_ports),
            'compromised_services': list(target_status.compromised_services),
            'system_integrity': target_status.system_integrity
        }


class NetworkAttackModule:
    """Network attack module for escalation"""
    
    def __init__(self):
        self.logger = logging.getLogger('network_escalation')
    
    def initialize(self, config: Dict):
        """Initialize network attack module"""
        self.config = config
        self.logger.info("Network escalation module initialized")
    
    def execute_attack(self, target_ip: str, payload: Dict) -> bool:
        """Execute network attack"""
        try:
            attack_type = payload.get('type')
            
            if attack_type == 'fake_alerts':
                return self._send_fake_alerts(target_ip, payload)
            elif attack_type == 'port_blocking':
                return self._block_ports(target_ip, payload)
            elif attack_type == 'ip_blocking':
                return self._block_ip(target_ip, payload)
            else:
                self.logger.warning(f"Unknown network attack type: {attack_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing network attack: {e}")
            return False
    
    def _send_fake_alerts(self, target_ip: str, payload: Dict) -> bool:
        """Send fake alerts to target"""
        try:
            message = payload.get('message', '⚠️ ВАША ДЕЯТЕЛЬНОСТЬ ОБНАРУЖЕНА')
            self.logger.warning(f"📢 Sending fake alert to {target_ip}: {message}")
            
            # Simulate sending alerts
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending fake alerts: {e}")
            return False
    
    def _block_ports(self, target_ip: str, payload: Dict) -> bool:
        """Block specific ports on target"""
        try:
            target_ports = payload.get('target_ports', [80, 443])
            self.logger.warning(f"🚫 Blocking ports {target_ports} on {target_ip}")
            
            # Simulate port blocking
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"Error blocking ports: {e}")
            return False
    
    def _block_ip(self, target_ip: str, payload: Dict) -> bool:
        """Block target IP"""
        try:
            block_method = payload.get('block_method', 'firewall')
            self.logger.warning(f"🔒 Blocking IP {target_ip} using {block_method}")
            
            # Simulate IP blocking
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"Error blocking IP: {e}")
            return False


class SystemAttackModule:
    """System attack module for escalation"""
    
    def __init__(self):
        self.logger = logging.getLogger('system_escalation')
    
    def initialize(self, config: Dict):
        """Initialize system attack module"""
        self.config = config
        self.logger.info("System escalation module initialized")
    
    def execute_attack(self, target_ip: str, payload: Dict) -> bool:
        """Execute system attack"""
        try:
            attack_type = payload.get('type')
            
            if attack_type == 'process_termination':
                return self._terminate_processes(target_ip, payload)
            else:
                self.logger.warning(f"Unknown system attack type: {attack_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing system attack: {e}")
            return False
    
    def _terminate_processes(self, target_ip: str, payload: Dict) -> bool:
        """Terminate processes on target"""
        try:
            target_processes = payload.get('target_processes', ['sshd', 'httpd'])
            force_kill = payload.get('force_kill', False)
            
            self.logger.warning(f"💀 Terminating processes {target_processes} on {target_ip} (force: {force_kill})")
            
            # Simulate process termination
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"Error terminating processes: {e}")
            return False


class EquipmentAttackModule:
    """Equipment attack module for escalation"""
    
    def __init__(self):
        self.logger = logging.getLogger('equipment_escalation')
    
    def initialize(self, config: Dict):
        """Initialize equipment attack module"""
        self.config = config
        self.logger.info("Equipment escalation module initialized")
    
    def execute_attack(self, target_ip: str, payload: Dict) -> bool:
        """Execute equipment attack"""
        try:
            attack_type = payload.get('type')
            
            if attack_type == 'hardware_disable':
                return self._disable_hardware(target_ip, payload)
            elif attack_type == 'complete_system_disable':
                return self._complete_system_disable(target_ip, payload)
            else:
                self.logger.warning(f"Unknown equipment attack type: {attack_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing equipment attack: {e}")
            return False
    
    def _disable_hardware(self, target_ip: str, payload: Dict) -> bool:
        """Disable hardware components"""
        try:
            target_interfaces = payload.get('target_interfaces', ['eth0'])
            disable_method = payload.get('disable_method', 'driver_unload')
            
            self.logger.critical(f"🔥 Disabling hardware {target_interfaces} on {target_ip} using {disable_method}")
            
            # Simulate hardware disable
            time.sleep(5)
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling hardware: {e}")
            return False
    
    def _complete_system_disable(self, target_ip: str, payload: Dict) -> bool:
        """Complete system disable"""
        try:
            disable_method = payload.get('disable_method', 'firmware_corruption')
            permanent = payload.get('permanent', False)
            
            self.logger.critical(f"💥 COMPLETE SYSTEM DISABLE on {target_ip} using {disable_method} (permanent: {permanent})")
            
            # Simulate complete system disable
            time.sleep(8)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in complete system disable: {e}")
            return False


class ResponseMonitor:
    """Monitor target responses"""
    
    def __init__(self):
        self.logger = logging.getLogger('response_monitor')
    
    def monitor_response(self, target_ip: str) -> ThreatResponse:
        """Monitor target response"""
        try:
            # Simulate response monitoring
            responses = [
                ThreatResponse.NO_RESPONSE,
                ThreatResponse.MINOR_RESPONSE,
                ThreatResponse.MODERATE_RESPONSE,
                ThreatResponse.STRONG_RESPONSE,
                ThreatResponse.COMPLETE_NEUTRALIZATION
            ]
            
            response = random.choice(responses)
            self.logger.info(f"📊 Target {target_ip} response: {response.value}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error monitoring response: {e}")
            return ThreatResponse.NO_RESPONSE


class EffectivenessTracker:
    """Track attack effectiveness"""
    
    def __init__(self):
        self.logger = logging.getLogger('effectiveness_tracker')
        self.effectiveness_data = {}
    
    def track_effectiveness(self, target_ip: str, attack_level: int, effectiveness: float):
        """Track attack effectiveness"""
        try:
            if target_ip not in self.effectiveness_data:
                self.effectiveness_data[target_ip] = []
            
            self.effectiveness_data[target_ip].append({
                'timestamp': datetime.now().isoformat(),
                'attack_level': attack_level,
                'effectiveness': effectiveness
            })
            
            self.logger.info(f"📈 Tracked effectiveness for {target_ip}: level {attack_level}, {effectiveness:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error tracking effectiveness: {e}")
    
    def get_effectiveness_history(self, target_ip: str) -> List[Dict]:
        """Get effectiveness history for target"""
        return self.effectiveness_data.get(target_ip, [])
