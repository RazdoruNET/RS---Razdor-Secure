#!/usr/bin/env python3
"""
RSecure macOS Notifications Module
Native macOS popup notifications for psychological manipulation warnings
"""

import os
import sys
import subprocess
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class NotificationData:
    """Notification data structure"""
    title: str
    subtitle: str
    message: str
    severity: str
    icon_path: Optional[str] = None
    sound: Optional[str] = None
    timeout: int = 5

class RSecureMacOSNotifications:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Notification settings
        self.enabled = True
        self.last_notification_time = None
        self.notification_cooldown = 30  # seconds
        self.notification_queue = []
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_notifications')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./macos_notifications.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Check if running on macOS
        self.is_macos = sys.platform == 'darwin'
        if not self.is_macos:
            self.logger.warning("Not running on macOS, notifications disabled")
            self.enabled = False
        
        # Initialize notification system
        self._initialize_notification_system()
    
    def _get_default_config(self) -> Dict:
        return {
            'enabled': True,
            'notification_cooldown': 30,
            'default_timeout': 5,
            'enable_sound': True,
            'enable_icon': True,
            'severity_levels': {
                'low': {'sound': 'Glass', 'timeout': 3},
                'medium': {'sound': 'Ping', 'timeout': 5},
                'high': {'sound': 'Basso', 'timeout': 7},
                'critical': {'sound': 'Sosumi', 'timeout': 10}
            }
        }
    
    def _initialize_notification_system(self):
        """Initialize macOS notification system"""
        try:
            if not self.is_macos:
                return
            
            # Test osascript availability
            result = subprocess.run(
                ['osascript', '-e', 'return "available"'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.logger.info("macOS notification system initialized")
            else:
                self.logger.error("Failed to initialize macOS notifications")
                self.enabled = False
                
        except Exception as e:
            self.logger.error(f"Error initializing notification system: {e}")
            self.enabled = False
    
    def send_psychological_threat_notification(self, threat_data: Dict) -> bool:
        """Send notification for psychological threat detection"""
        try:
            if not self.enabled or not self.is_macos:
                return False
            
            # Check cooldown
            if self._is_in_cooldown():
                self.logger.debug("Notification cooldown active")
                return False
            
            # Determine notification content based on threat type
            notification = self._create_psychological_notification(threat_data)
            
            # Send notification
            success = self._send_notification(notification)
            
            if success:
                self.last_notification_time = datetime.now()
                self.logger.info(f"Psychological threat notification sent: {notification.title}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending psychological threat notification: {e}")
            return False
    
    def _create_psychological_notification(self, threat_data: Dict) -> NotificationData:
        """Create notification content for psychological threat"""
        threat_type = threat_data.get('threat_type', 'unknown')
        confidence = threat_data.get('confidence', 0.0)
        severity = threat_data.get('severity', 'medium')
        source = threat_data.get('source', 'unknown')
        brain_signal = threat_data.get('brain_signal', '')
        
        # Determine notification content based on threat type
        if 'weight_adjustment' in threat_type:
            title = "⚠️ ПОПЫТКА ПЕРЕНАСТРОЙКИ СОЗНАНИЯ"
            subtitle = "Обнаружена попытка изменения весов нейронов"
            message = f"Источник: {source}\nУверенность: {confidence:.1%}\n{brain_signal}"
        elif 'propaganda' in threat_type:
            title = "🎧 ОБНАРУЖЕНА ПРОПАГАНДА"
            subtitle = "Аудио поток содержит манипулятивный контент"
            message = f"Источник: {source}\nУверенность: {confidence:.1%}\n{brain_signal}"
        elif 'subliminal' in threat_type:
            title = "🧠 СУБЛИМИНАЛЬНОЕ ВОЗДЕЙСТВИЕ"
            subtitle = "Обнаружены скрытые психологические сигналы"
            message = f"Источник: {source}\nУверенность: {confidence:.1%}\n{brain_signal}"
        elif 'manipulative_speech' in threat_type:
            title = "🗣️ МАНИПУЛЯТИВНАЯ РЕЧЬ"
            subtitle = "Обнаружены паттерны психологического воздействия"
            message = f"Источник: {source}\nУверенность: {confidence:.1%}\n{brain_signal}"
        elif 'brain_signal' in threat_type:
            title = "🧠 МОЗГОВОЙ СИГНАЛ"
            subtitle = "Обнаружена попытка воздействия на мозг"
            message = f"Источник: {source}\nУверенность: {confidence:.1%}\n{brain_signal}"
        else:
            title = "🔍 ПОДОЗРИТЕЛЬНАЯ АКТИВНОСТЬ"
            subtitle = "Обнаружена потенциальная психологическая манипуляция"
            message = f"Источник: {source}\nУверенность: {confidence:.1%}\n{brain_signal}"
        
        # Adjust for severity
        if severity == 'critical':
            title = "🚨 " + title
            subtitle = "КРИТИЧЕСКАЯ УГРОЗА: " + subtitle
        elif severity == 'high':
            title = "⚠️ " + title
            subtitle = "ВЫСОКИЙ РИСК: " + subtitle
        
        # Get sound and timeout for severity
        severity_config = self.config['severity_levels'].get(severity, {})
        sound = severity_config.get('sound', 'Ping') if self.config['enable_sound'] else None
        timeout = severity_config.get('timeout', self.config['default_timeout'])
        
        return NotificationData(
            title=title,
            subtitle=subtitle,
            message=message,
            severity=severity,
            sound=sound,
            timeout=timeout
        )
    
    def _send_notification(self, notification: NotificationData) -> bool:
        """Send notification using macOS osascript"""
        try:
            # Build osascript command
            script = self._build_notification_script(notification)
            
            # Execute the script
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Notification sent successfully: {notification.title}")
                return True
            else:
                self.logger.error(f"Failed to send notification: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing notification script: {e}")
            return False
    
    def _build_notification_script(self, notification: NotificationData) -> str:
        """Build AppleScript for notification"""
        script_parts = [
            'display notification',
            f'"{self._escape_applescript_string(notification.message)}"',
            f'with title "{self._escape_applescript_string(notification.title)}"',
            f'subtitle "{self._escape_applescript_string(notification.subtitle)}"'
        ]
        
        # Add sound if specified
        if notification.sound:
            script_parts.append(f'sound name "{notification.sound}"')
        
        # Add timeout (macOS doesn't support timeout directly, but we can use it for our tracking)
        # This is handled by our cooldown system
        
        return ' '.join(script_parts)
    
    def _escape_applescript_string(self, text: str) -> str:
        """Escape string for AppleScript"""
        # Replace problematic characters
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        return text
    
    def _is_in_cooldown(self) -> bool:
        """Check if notification cooldown is active"""
        if not self.last_notification_time:
            return False
        
        time_since_last = (datetime.now() - self.last_notification_time).total_seconds()
        return time_since_last < self.notification_cooldown
    
    def send_audio_threat_notification(self, audio_threat_data: Dict) -> bool:
        """Send notification for audio threat detection"""
        try:
            if not self.enabled or not self.is_macos:
                return False
            
            # Check cooldown
            if self._is_in_cooldown():
                return False
            
            # Create audio-specific notification
            notification = self._create_audio_notification(audio_threat_data)
            
            # Send notification
            success = self._send_notification(notification)
            
            if success:
                self.last_notification_time = datetime.now()
                self.logger.info(f"Audio threat notification sent: {notification.title}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending audio threat notification: {e}")
            return False
    
    def _create_audio_notification(self, audio_threat_data: Dict) -> NotificationData:
        """Create notification content for audio threat"""
        threat_type = audio_threat_data.get('threat_type', 'unknown')
        confidence = audio_threat_data.get('confidence', 0.0)
        severity = audio_threat_data.get('severity', 'medium')
        source_app = audio_threat_data.get('source_app', 'unknown')
        transcription = audio_threat_data.get('transcription', '')
        
        # Determine notification content based on threat type
        if threat_type == 'propaganda':
            title = "🎧 ПРОПАГАНДА В АУДИО"
            subtitle = "Обнаружена пропаганда в аудио потоке"
            message = f"Приложение: {source_app}\nУверенность: {confidence:.1%}"
            if transcription:
                message += f"\nТекст: {transcription[:100]}..."
        elif threat_type == 'subliminal_manipulation':
            title = "🧠 СУБЛИМИНАЛ В АУДИО"
            subtitle = "Обнаружены скрытые аудио сигналы"
            message = f"Приложение: {source_app}\nУверенность: {confidence:.1%}"
        elif threat_type == 'binaural_manipulation':
            title = "🎧 БИНАУРАЛЬНЫЕ РИТМЫ"
            subtitle = "Обнаружены бинауральные частоты"
            message = f"Приложение: {source_app}\nУверенность: {confidence:.1%}"
        else:
            title = "🔍 ПОДОЗРИТЕЛЬНЫЙ АУДИО"
            subtitle = "Обнаружена подозрительная аудио активность"
            message = f"Приложение: {source_app}\nУверенность: {confidence:.1%}"
        
        # Adjust for severity
        if severity == 'critical':
            title = "🚨 " + title
            subtitle = "КРИТИЧЕСКАЯ УГРОЗА: " + subtitle
        elif severity == 'high':
            title = "⚠️ " + title
            subtitle = "ВЫСОКИЙ РИСК: " + subtitle
        
        # Get sound and timeout for severity
        severity_config = self.config['severity_levels'].get(severity, {})
        sound = severity_config.get('sound', 'Ping') if self.config['enable_sound'] else None
        timeout = severity_config.get('timeout', self.config['default_timeout'])
        
        return NotificationData(
            title=title,
            subtitle=subtitle,
            message=message,
            severity=severity,
            sound=sound,
            timeout=timeout
        )
    
    def send_custom_notification(self, title: str, subtitle: str, message: str, 
                               severity: str = 'medium', sound: str = None) -> bool:
        """Send custom notification"""
        try:
            if not self.enabled or not self.is_macos:
                return False
            
            # Check cooldown
            if self._is_in_cooldown():
                return False
            
            # Create notification
            severity_config = self.config['severity_levels'].get(severity, {})
            notification_sound = sound or (severity_config.get('sound') if self.config['enable_sound'] else None)
            timeout = severity_config.get('timeout', self.config['default_timeout'])
            
            notification = NotificationData(
                title=title,
                subtitle=subtitle,
                message=message,
                severity=severity,
                sound=notification_sound,
                timeout=timeout
            )
            
            # Send notification
            success = self._send_notification(notification)
            
            if success:
                self.last_notification_time = datetime.now()
                self.logger.info(f"Custom notification sent: {title}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending custom notification: {e}")
            return False
    
    def test_notification(self) -> bool:
        """Send test notification"""
        return self.send_custom_notification(
            title="🌑 RSecure Тест",
            subtitle="Проверка системы уведомлений",
            message="RSecure psychological protection is active",
            severity="low"
        )
    
    def set_cooldown(self, seconds: int):
        """Set notification cooldown period"""
        self.notification_cooldown = max(0, seconds)
        self.logger.info(f"Notification cooldown set to {seconds} seconds")
    
    def enable_notifications(self, enabled: bool = True):
        """Enable or disable notifications"""
        self.enabled = enabled and self.is_macos
        self.logger.info(f"Notifications {'enabled' if self.enabled else 'disabled'}")

# Singleton instance for easy access
_notification_instance = None

def get_notification_instance(config: Dict = None) -> RSecureMacOSNotifications:
    """Get singleton notification instance"""
    global _notification_instance
    if _notification_instance is None:
        _notification_instance = RSecureMacOSNotifications(config)
    return _notification_instance

def send_psychological_threat_alert(threat_data: Dict) -> bool:
    """Quick function to send psychological threat alert"""
    notifier = get_notification_instance()
    return notifier.send_psychological_threat_notification(threat_data)

def send_audio_threat_alert(audio_threat_data: Dict) -> bool:
    """Quick function to send audio threat alert"""
    notifier = get_notification_instance()
    return notifier.send_audio_threat_notification(audio_threat_data)

if __name__ == "__main__":
    # Test notification system
    print("Testing RSecure macOS Notifications...")
    
    notifier = RSecureMacOSNotifications()
    
    # Test basic notification
    notifier.test_notification()
    
    # Test psychological threat notification
    test_threat = {
        'threat_type': 'weight_adjustment',
        'confidence': 0.85,
        'severity': 'high',
        'source': 'test_application',
        'brain_signal': '⚠️ WEIGHT_ADJUSTMENT_ATTEMPT_DETECTED'
    }
    
    notifier.send_psychological_threat_notification(test_threat)
    
    # Test audio threat notification
    test_audio_threat = {
        'threat_type': 'propaganda',
        'confidence': 0.75,
        'severity': 'medium',
        'source_app': 'test_app',
        'transcription': 'this is test propaganda content'
    }
    
    notifier.send_audio_threat_notification(test_audio_threat)
    
    print("Test notifications sent!")
