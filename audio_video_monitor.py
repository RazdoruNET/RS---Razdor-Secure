#!/usr/bin/env python3
"""
RSecure Audio/Video Device Monitoring Layer
Advanced monitoring of audio/video devices including capacitor-based microphone detection
"""

import os
import sys
import time
import logging
import threading
import subprocess
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import psutil

@dataclass
class DeviceInfo:
    """Device information"""
    device_id: str
    device_type: str
    name: str
    status: str
    last_seen: datetime
    suspicious_indicators: List[str]
    risk_level: str
    metadata: Dict

@dataclass
class CapacitorAnalysis:
    """Capacitor analysis results"""
    device_id: str
    capacitor_count: int
    suspicious_capacitors: List[Dict]
    microphone_potential: float
    risk_assessment: str
    timestamp: datetime

class RSecureAudioVideoMonitor:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Device tracking
        self.known_devices = {}
        self.active_devices = {}
        self.blocked_devices = set()
        
        # Capacitor analysis
        self.capacitor_database = {}
        self.suspicious_capacitor_types = set()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_audio_video')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./audio_video_monitor.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize components
        self._initialize_capacitor_database()
        self._load_known_devices()
    
    def _get_default_config(self) -> Dict:
        return {
            'monitoring_interval': 30,  # seconds
            'device_timeout': 300,  # 5 minutes
            'capacitor_scan_interval': 60,  # 1 minute
            'risk_threshold': 0.7,
            'enable_audio_monitoring': True,
            'enable_video_monitoring': True,
            'enable_capacitor_analysis': True,
            'enable_hardware_scanning': True,
            'enable_process_monitoring': True
        }
    
    def _initialize_capacitor_database(self):
        """Initialize capacitor database for microphone detection"""
        try:
            # Known microphone capacitor types and characteristics
            self.suspicious_capacitor_types = {
                'electret_mic': {
                    'capacitance_range': (1e-12, 100e-12),  # 1-100pF
                    'voltage_range': (1.5, 12),  # 1.5-12V
                    'frequency_response': (20, 20000),  # 20Hz-20kHz
                    'indicators': ['JFET', 'FET', 'electret', 'microphone']
                },
                'condenser_mic': {
                    'capacitance_range': (10e-12, 500e-12),  # 10-500pF
                    'voltage_range': (12, 48),  # 12-48V
                    'frequency_response': (20, 20000),
                    'indicators': ['phantom_power', 'condenser', 'XLR']
                },
                'mems_mic': {
                    'capacitance_range': (0.1e-12, 10e-12),  # 0.1-10pF
                    'voltage_range': (1.8, 3.3),  # 1.8-3.3V
                    'frequency_response': (100, 10000),
                    'indicators': ['MEMS', 'silicon', 'digital']
                },
                'piezo_mic': {
                    'capacitance_range': (100e-12, 1000e-12),  # 100-1000pF
                    'voltage_range': (0.1, 5),  # 0.1-5V
                    'frequency_response': (100, 15000),
                    'indicators': ['piezo', 'crystal', 'ceramic']
                }
            }
            
            self.logger.info("Capacitor database initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing capacitor database: {e}")
    
    def _load_known_devices(self):
        """Load known devices database"""
        try:
            # This would load from a database file
            # For now, we'll use empty database
            self.known_devices = {}
            self.logger.info("Known devices database loaded")
            
        except Exception as e:
            self.logger.error(f"Error loading known devices: {e}")
    
    def start_monitoring(self):
        """Start audio/video monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Audio/video monitoring started")
    
    def stop_monitoring(self):
        """Stop audio/video monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=30)
        self.logger.info("Audio/video monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Scan for audio devices
                if self.config['enable_audio_monitoring']:
                    self._scan_audio_devices()
                
                # Scan for video devices
                if self.config['enable_video_monitoring']:
                    self._scan_video_devices()
                
                # Hardware scanning
                if self.config['enable_hardware_scanning']:
                    self._scan_hardware_devices()
                
                # Process monitoring
                if self.config['enable_process_monitoring']:
                    self._monitor_audio_processes()
                
                # Capacitor analysis
                if self.config['enable_capacitor_analysis']:
                    self._analyze_capacitors()
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _scan_audio_devices(self):
        """Scan for audio devices"""
        try:
            platform = sys.platform
            
            if platform == 'darwin':  # macOS
                self._scan_macos_audio()
            elif platform == 'linux':
                self._scan_linux_audio()
            else:
                self.logger.warning(f"Audio scanning not supported on {platform}")
                
        except Exception as e:
            self.logger.error(f"Error scanning audio devices: {e}")
    
    def _scan_macos_audio(self):
        """Scan audio devices on macOS"""
        try:
            # Use system_profiler to get audio devices
            result = subprocess.run(
                ['system_profiler', 'SPAudioDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self._process_macos_audio_data(data)
                
        except Exception as e:
            self.logger.error(f"Error scanning macOS audio: {e}")
    
    def _scan_linux_audio(self):
        """Scan audio devices on Linux"""
        try:
            # Check /proc/asound/devices
            if os.path.exists('/proc/asound/devices'):
                with open('/proc/asound/devices', 'r') as f:
                    devices = f.read()
                    self._process_linux_audio_data(devices)
            
            # Check /dev/snd/
            if os.path.exists('/dev/snd/'):
                snd_devices = os.listdir('/dev/snd/')
                self._process_linux_snd_devices(snd_devices)
                
        except Exception as e:
            self.logger.error(f"Error scanning Linux audio: {e}")
    
    def _process_macos_audio_data(self, data: Dict):
        """Process macOS audio data"""
        try:
            audio_data = data.get('SPAudioDataType', [])
            
            for item in audio_data:
                if '_items' in item:
                    for device in item['_items']:
                        self._process_audio_device(device, 'macos')
                        
        except Exception as e:
            self.logger.error(f"Error processing macOS audio data: {e}")
    
    def _process_linux_audio_data(self, devices: str):
        """Process Linux audio data"""
        try:
            lines = devices.strip().split('\n')
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        device_info = {
                            'device_id': parts[1] if len(parts) > 1 else 'unknown',
                            'device_type': parts[2] if len(parts) > 2 else 'unknown',
                            'name': ' '.join(parts[3:]) if len(parts) > 3 else 'unknown'
                        }
                        self._process_audio_device(device_info, 'linux')
                        
        except Exception as e:
            self.logger.error(f"Error processing Linux audio data: {e}")
    
    def _process_linux_snd_devices(self, devices: List[str]):
        """Process Linux /dev/snd/ devices"""
        try:
            for device in devices:
                if device.startswith('pcm') or device.startswith('control'):
                    device_info = {
                        'device_id': device,
                        'device_type': 'audio',
                        'name': f'/dev/snd/{device}'
                    }
                    self._process_audio_device(device_info, 'linux')
                    
        except Exception as e:
            self.logger.error(f"Error processing Linux snd devices: {e}")
    
    def _scan_video_devices(self):
        """Scan for video devices"""
        try:
            platform = sys.platform
            
            if platform == 'darwin':  # macOS
                self._scan_macos_video()
            elif platform == 'linux':
                self._scan_linux_video()
            else:
                self.logger.warning(f"Video scanning not supported on {platform}")
                
        except Exception as e:
            self.logger.error(f"Error scanning video devices: {e}")
    
    def _scan_macos_video(self):
        """Scan video devices on macOS"""
        try:
            # Use system_profiler to get camera devices
            result = subprocess.run(
                ['system_profiler', 'SPCameraDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self._process_macos_video_data(data)
                
        except Exception as e:
            self.logger.error(f"Error scanning macOS video: {e}")
    
    def _scan_linux_video(self):
        """Scan video devices on Linux"""
        try:
            # Check /dev/video*
            video_devices = []
            for i in range(10):  # Check /dev/video0 to /dev/video9
                device_path = f'/dev/video{i}'
                if os.path.exists(device_path):
                    video_devices.append(device_path)
            
            for device in video_devices:
                device_info = {
                    'device_id': device,
                    'device_type': 'video',
                    'name': device
                }
                self._process_video_device(device_info, 'linux')
                
        except Exception as e:
            self.logger.error(f"Error scanning Linux video: {e}")
    
    def _process_macos_video_data(self, data: Dict):
        """Process macOS video data"""
        try:
            camera_data = data.get('SPCameraDataType', [])
            
            for item in camera_data:
                if '_items' in item:
                    for device in item['_items']:
                        self._process_video_device(device, 'macos')
                        
        except Exception as e:
            self.logger.error(f"Error processing macOS video data: {e}")
    
    def _scan_hardware_devices(self):
        """Scan for hardware devices"""
        try:
            platform = sys.platform
            
            if platform == 'darwin':
                self._scan_macos_hardware()
            elif platform == 'linux':
                self._scan_linux_hardware()
                
        except Exception as e:
            self.logger.error(f"Error scanning hardware devices: {e}")
    
    def _scan_macos_hardware(self):
        """Scan hardware devices on macOS"""
        try:
            # Use system_profiler to get hardware info
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self._process_hardware_data(data)
                
        except Exception as e:
            self.logger.error(f"Error scanning macOS hardware: {e}")
    
    def _scan_linux_hardware(self):
        """Scan hardware devices on Linux"""
        try:
            # Check /proc/cpuinfo, /proc/meminfo, etc.
            # Check for USB devices
            if os.path.exists('/proc/bus/usb/devices'):
                with open('/proc/bus/usb/devices', 'r') as f:
                    usb_devices = f.read()
                    self._process_linux_usb_devices(usb_devices)
                    
        except Exception as e:
            self.logger.error(f"Error scanning Linux hardware: {e}")
    
    def _process_linux_usb_devices(self, devices: str):
        """Process Linux USB devices"""
        try:
            lines = devices.strip().split('\n')
            current_device = {}
            
            for line in lines:
                if line.startswith('T:'):
                    # New device
                    if current_device:
                        self._process_usb_device(current_device)
                    current_device = {'type': 'usb'}
                elif line.startswith('P:'):
                    # Product
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        current_device['product'] = parts[1].strip()
                elif line.startswith('I:'):
                    # Interface
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        current_device['interface'] = parts[1].strip()
            
            # Process last device
            if current_device:
                self._process_usb_device(current_device)
                
        except Exception as e:
            self.logger.error(f"Error processing Linux USB devices: {e}")
    
    def _process_usb_device(self, device: Dict):
        """Process USB device information"""
        try:
            product = device.get('product', '').lower()
            interface = device.get('interface', '').lower()
            
            # Check for audio/video devices
            audio_keywords = ['audio', 'microphone', 'mic', 'speaker', 'headset']
            video_keywords = ['camera', 'video', 'webcam', 'capture']
            
            is_audio = any(keyword in product or keyword in interface for keyword in audio_keywords)
            is_video = any(keyword in product or keyword in interface for keyword in video_keywords)
            
            if is_audio or is_video:
                device_type = 'audio' if is_audio else 'video'
                device_info = {
                    'device_id': f"usb_{hash(product) % 10000}",
                    'device_type': device_type,
                    'name': product or 'Unknown USB Device',
                    'interface': interface
                }
                
                if is_audio:
                    self._process_audio_device(device_info, 'usb')
                else:
                    self._process_video_device(device_info, 'usb')
                    
        except Exception as e:
            self.logger.error(f"Error processing USB device: {e}")
    
    def _monitor_audio_processes(self):
        """Monitor processes that access audio devices"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # Check for audio-related processes
                    audio_keywords = [
                        'audio', 'microphone', 'mic', 'recording', 'voice',
                        'sound', 'speaker', 'headphone', 'pulseaudio', 'coreaudio'
                    ]
                    
                    if any(keyword in cmdline.lower() for keyword in audio_keywords):
                        self._process_audio_process(proc.info, cmdline)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error monitoring audio processes: {e}")
    
    def _analyze_capacitors(self):
        """Analyze capacitors for microphone detection"""
        try:
            platform = sys.platform
            
            if platform == 'darwin':
                self._analyze_macos_capacitors()
            elif platform == 'linux':
                self._analyze_linux_capacitors()
                
        except Exception as e:
            self.logger.error(f"Error analyzing capacitors: {e}")
    
    def _analyze_macos_capacitors(self):
        """Analyze capacitors on macOS"""
        try:
            # Use system_profiler to get hardware details
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self._process_macos_capacitor_data(data)
                
        except Exception as e:
            self.logger.error(f"Error analyzing macOS capacitors: {e}")
    
    def _analyze_linux_capacitors(self):
        """Analyze capacitors on Linux"""
        try:
            # Check for hardware information
            if os.path.exists('/proc/asound/cards'):
                with open('/proc/asound/cards', 'r') as f:
                    cards = f.read()
                    self._process_linux_capacitor_data(cards)
                    
            # Check for I2C devices
            if os.path.exists('/sys/class/i2c-adapter/'):
                self._scan_i2c_devices()
                
        except Exception as e:
            self.logger.error(f"Error analyzing Linux capacitors: {e}")
    
    def _scan_i2c_devices(self):
        """Scan I2C devices for capacitor analysis"""
        try:
            i2c_path = '/sys/class/i2c-adapter/'
            
            if os.path.exists(i2c_path):
                for adapter in os.listdir(i2c_path):
                    adapter_path = os.path.join(i2c_path, adapter)
                    
                    if os.path.isdir(adapter_path):
                        # Scan for I2C devices
                        device_path = os.path.join(adapter_path, 'device')
                        if os.path.exists(device_path):
                            self._analyze_i2c_device(device_path)
                            
        except Exception as e:
            self.logger.error(f"Error scanning I2C devices: {e}")
    
    def _analyze_i2c_device(self, device_path: str):
        """Analyze I2C device for capacitors"""
        try:
            # Read device name and modalias
            name_file = os.path.join(device_path, 'name')
            modalias_file = os.path.join(device_path, 'modalias')
            
            device_name = ''
            modalias = ''
            
            if os.path.exists(name_file):
                with open(name_file, 'r') as f:
                    device_name = f.read().strip()
            
            if os.path.exists(modalias_file):
                with open(modalias_file, 'r') as f:
                    modalias = f.read().strip()
            
            # Check for audio/microphone related devices
            audio_keywords = ['audio', 'mic', 'microphone', 'codec', 'sound']
            
            if any(keyword in device_name.lower() or keyword in modalias.lower() 
                   for keyword in audio_keywords):
                
                analysis = self._create_capacitor_analysis(
                    device_name, modalias, 'i2c'
                )
                
                self.capacitor_database[device_name] = analysis
                
        except Exception as e:
            self.logger.error(f"Error analyzing I2C device {device_path}: {e}")
    
    def _create_capacitor_analysis(self, device_name: str, modalias: str, bus_type: str) -> CapacitorAnalysis:
        """Create capacitor analysis for device"""
        try:
            # Simulate capacitor analysis
            # In a real implementation, this would read actual hardware values
            
            suspicious_indicators = []
            microphone_potential = 0.0
            
            # Check for microphone indicators
            mic_keywords = ['microphone', 'mic', 'audio', 'codec', 'sound']
            if any(keyword in device_name.lower() or keyword in modalias.lower() 
                   for keyword in mic_keywords):
                microphone_potential += 0.3
                suspicious_indicators.append('audio_device')
            
            # Check for capacitor-related indicators
            cap_keywords = ['capacitor', 'electret', 'mems', 'piezo']
            if any(keyword in device_name.lower() or keyword in modalias.lower() 
                   for keyword in cap_keywords):
                microphone_potential += 0.4
                suspicious_indicators.append('capacitor_type')
            
            # Check for suspicious characteristics
            if 'codec' in modalias.lower():
                microphone_potential += 0.2
                suspicious_indicators.append('audio_codec')
            
            # Determine risk assessment
            if microphone_potential > 0.7:
                risk_assessment = 'high'
            elif microphone_potential > 0.4:
                risk_assessment = 'medium'
            else:
                risk_assessment = 'low'
            
            return CapacitorAnalysis(
                device_id=device_name,
                capacitor_count=1,  # Simplified
                suspicious_capacitors=[{
                    'type': 'unknown',
                    'location': bus_type,
                    'indicators': suspicious_indicators
                }],
                microphone_potential=microphone_potential,
                risk_assessment=risk_assessment,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error creating capacitor analysis: {e}")
            return CapacitorAnalysis(
                device_id=device_name,
                capacitor_count=0,
                suspicious_capacitors=[],
                microphone_potential=0.0,
                risk_assessment='unknown',
                timestamp=datetime.now()
            )
    
    def _process_audio_device(self, device: Dict, source: str):
        """Process audio device information"""
        try:
            device_id = device.get('device_id', 'unknown')
            
            # Check if device is blocked
            if device_id in self.blocked_devices:
                return
            
            # Create device info
            device_info = DeviceInfo(
                device_id=device_id,
                device_type='audio',
                name=device.get('name', 'Unknown Audio Device'),
                status='active',
                last_seen=datetime.now(),
                suspicious_indicators=[],
                risk_level='low',
                metadata={
                    'source': source,
                    'raw_data': device
                }
            )
            
            # Analyze for suspicious indicators
            self._analyze_device_suspiciousness(device_info)
            
            # Update active devices
            self.active_devices[device_id] = device_info
            
            # Log new device
            if device_id not in self.known_devices:
                self.logger.info(f"New audio device detected: {device_info.name} ({device_id})")
                self.known_devices[device_id] = device_info
                
        except Exception as e:
            self.logger.error(f"Error processing audio device: {e}")
    
    def _process_video_device(self, device: Dict, source: str):
        """Process video device information"""
        try:
            device_id = device.get('device_id', 'unknown')
            
            # Check if device is blocked
            if device_id in self.blocked_devices:
                return
            
            # Create device info
            device_info = DeviceInfo(
                device_id=device_id,
                device_type='video',
                name=device.get('name', 'Unknown Video Device'),
                status='active',
                last_seen=datetime.now(),
                suspicious_indicators=[],
                risk_level='low',
                metadata={
                    'source': source,
                    'raw_data': device
                }
            )
            
            # Analyze for suspicious indicators
            self._analyze_device_suspiciousness(device_info)
            
            # Update active devices
            self.active_devices[device_id] = device_info
            
            # Log new device
            if device_id not in self.known_devices:
                self.logger.info(f"New video device detected: {device_info.name} ({device_id})")
                self.known_devices[device_id] = device_info
                
        except Exception as e:
            self.logger.error(f"Error processing video device: {e}")
    
    def _process_hardware_data(self, data: Dict):
        """Process hardware data"""
        try:
            # Extract relevant hardware information
            hardware_info = data.get('SPHardwareDataType', [])
            
            for item in hardware_info:
                if '_items' in item:
                    for hw_item in item['_items']:
                        # Check for audio/video related hardware
                        self._process_hardware_item(hw_item)
                        
        except Exception as e:
            self.logger.error(f"Error processing hardware data: {e}")
    
    def _process_hardware_item(self, item: Dict):
        """Process individual hardware item"""
        try:
            # This would analyze specific hardware components
            # For now, we'll just log the item
            name = item.get('_name', 'Unknown Hardware')
            
            # Check for audio/video related hardware
            audio_keywords = ['audio', 'sound', 'microphone', 'speaker']
            video_keywords = ['camera', 'video', 'webcam', 'capture']
            
            name_lower = name.lower()
            
            if any(keyword in name_lower for keyword in audio_keywords + video_keywords):
                self.logger.debug(f"Audio/Video hardware detected: {name}")
                
        except Exception as e:
            self.logger.error(f"Error processing hardware item: {e}")
    
    def _process_macos_capacitor_data(self, data: Dict):
        """Process macOS capacitor data"""
        try:
            # Extract hardware information for capacitor analysis
            hardware_info = data.get('SPHardwareDataType', [])
            
            for item in hardware_info:
                if '_items' in item:
                    for hw_item in item['_items']:
                        self._analyze_hardware_capacitors(hw_item)
                        
        except Exception as e:
            self.logger.error(f"Error processing macOS capacitor data: {e}")
    
    def _process_linux_capacitor_data(self, data: str):
        """Process Linux capacitor data"""
        try:
            # Parse ALSA card information
            lines = data.strip().split('\n')
            
            for line in lines:
                if 'audio' in line.lower() or 'codec' in line.lower():
                    self._analyze_audio_card(line)
                    
        except Exception as e:
            self.logger.error(f"Error processing Linux capacitor data: {e}")
    
    def _analyze_hardware_capacitors(self, item: Dict):
        """Analyze hardware for capacitors"""
        try:
            name = item.get('_name', '')
            
            # Check for audio-related hardware
            audio_keywords = ['audio', 'codec', 'sound', 'microphone']
            
            if any(keyword in name.lower() for keyword in audio_keywords):
                analysis = self._create_capacitor_analysis(name, '', 'hardware')
                self.capacitor_database[name] = analysis
                
        except Exception as e:
            self.logger.error(f"Error analyzing hardware capacitors: {e}")
    
    def _analyze_audio_card(self, card_info: str):
        """Analyze audio card for capacitors"""
        try:
            # Extract card name
            if ':' in card_info:
                card_name = card_info.split(':', 1)[1].strip()
                
                analysis = self._create_capacitor_analysis(card_name, card_info, 'alsa')
                self.capacitor_database[card_name] = analysis
                
        except Exception as e:
            self.logger.error(f"Error analyzing audio card: {e}")
    
    def _process_audio_process(self, process_info: Dict, cmdline: str):
        """Process audio-related process"""
        try:
            pid = process_info['pid']
            name = process_info['name']
            
            # Check for suspicious audio processes
            suspicious_keywords = [
                'record', 'spy', 'monitor', 'capture', 'hidden',
                'stealth', 'secret', 'background'
            ]
            
            if any(keyword in cmdline.lower() for keyword in suspicious_keywords):
                self.logger.warning(f"Suspicious audio process detected: {name} (PID: {pid})")
                
                # Create device info for the process
                device_info = DeviceInfo(
                    device_id=f"process_{pid}",
                    device_type='audio_process',
                    name=name,
                    status='suspicious',
                    last_seen=datetime.now(),
                    suspicious_indicators=['suspicious_audio_process'],
                    risk_level='medium',
                    metadata={
                        'pid': pid,
                        'cmdline': cmdline,
                        'source': 'process_monitoring'
                    }
                )
                
                self.active_devices[f"process_{pid}"] = device_info
                
        except Exception as e:
            self.logger.error(f"Error processing audio process: {e}")
    
    def _analyze_device_suspiciousness(self, device_info: DeviceInfo):
        """Analyze device for suspicious indicators"""
        try:
            suspicious_indicators = []
            risk_level = 'low'
            
            # Check device name for suspicious patterns
            name_lower = device_info.name.lower()
            
            # Hidden or stealth indicators
            if any(keyword in name_lower for keyword in ['hidden', 'stealth', 'spy', 'secret']):
                suspicious_indicators.append('suspicious_name')
                risk_level = 'high'
            
            # Unusual device types
            if device_info.device_type == 'audio' and 'virtual' in name_lower:
                suspicious_indicators.append('virtual_audio_device')
                risk_level = 'medium'
            
            # Check metadata for suspicious information
            metadata = device_info.metadata
            source = metadata.get('source', '')
            
            if source == 'usb' and 'unknown' in name_lower:
                suspicious_indicators.append('unknown_usb_device')
                risk_level = 'medium'
            
            # Update device info
            device_info.suspicious_indicators = suspicious_indicators
            device_info.risk_level = risk_level
            
            # Log suspicious devices
            if risk_level in ['medium', 'high']:
                self.logger.warning(f"Suspicious device detected: {device_info.name} ({device_info.device_id})")
                
        except Exception as e:
            self.logger.error(f"Error analyzing device suspiciousness: {e}")
    
    def block_device(self, device_id: str, reason: str = "Manual block"):
        """Block a device"""
        try:
            self.blocked_devices.add(device_id)
            
            # Remove from active devices
            if device_id in self.active_devices:
                del self.active_devices[device_id]
            
            self.logger.info(f"Device {device_id} blocked: {reason}")
            
        except Exception as e:
            self.logger.error(f"Error blocking device {device_id}: {e}")
    
    def unblock_device(self, device_id: str):
        """Unblock a device"""
        try:
            self.blocked_devices.discard(device_id)
            self.logger.info(f"Device {device_id} unblocked")
            
        except Exception as e:
            self.logger.error(f"Error unblocking device {device_id}: {e}")
    
    def get_device_status(self) -> Dict:
        """Get current device status"""
        try:
            active_audio = len([d for d in self.active_devices.values() if d.device_type == 'audio'])
            active_video = len([d for d in self.active_devices.values() if d.device_type == 'video'])
            suspicious_devices = len([d for d in self.active_devices.values() if d.risk_level in ['medium', 'high']])
            
            capacitor_analysis = len(self.capacitor_database)
            high_risk_capacitors = len([c for c in self.capacitor_database.values() 
                                     if c.risk_assessment in ['medium', 'high']])
            
            return {
                'active_audio_devices': active_audio,
                'active_video_devices': active_video,
                'suspicious_devices': suspicious_devices,
                'blocked_devices': len(self.blocked_devices),
                'capacitor_analysis_count': capacitor_analysis,
                'high_risk_capacitors': high_risk_capacitors,
                'monitoring_active': self.monitoring_active,
                'last_scan': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting device status: {e}")
            return {}
    
    def get_detailed_report(self) -> Dict:
        """Get detailed monitoring report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'active_devices': {},
                'blocked_devices': list(self.blocked_devices),
                'capacitor_analysis': {},
                'statistics': self.get_device_status()
            }
            
            # Add active devices
            for device_id, device in self.active_devices.items():
                report['active_devices'][device_id] = {
                    'name': device.name,
                    'type': device.device_type,
                    'status': device.status,
                    'risk_level': device.risk_level,
                    'suspicious_indicators': device.suspicious_indicators,
                    'last_seen': device.last_seen.isoformat(),
                    'metadata': device.metadata
                }
            
            # Add capacitor analysis
            for device_id, analysis in self.capacitor_database.items():
                report['capacitor_analysis'][device_id] = {
                    'capacitor_count': analysis.capacitor_count,
                    'microphone_potential': analysis.microphone_potential,
                    'risk_assessment': analysis.risk_assessment,
                    'timestamp': analysis.timestamp.isoformat(),
                    'suspicious_capacitors': analysis.suspicious_capacitors
                }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating detailed report: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    monitor = RSecureAudioVideoMonitor()
    monitor.start_monitoring()
    
    try:
        while True:
            status = monitor.get_device_status()
            print(f"Device Status: {status}")
            
            # Get detailed report every 60 seconds
            if int(time.time()) % 60 == 0:
                report = monitor.get_detailed_report()
                print(f"Detailed Report: {report}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        monitor.stop_monitoring()
        print("Monitoring stopped.")
