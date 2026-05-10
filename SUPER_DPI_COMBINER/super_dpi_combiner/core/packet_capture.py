#!/usr/bin/env python3
"""
Packet Capture Layer - Встроенный packet capture audit layer
Фиксирует TCP операции без внешних зависимостей
"""

import time
import socket
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

@dataclass(slots=True)
class PacketEvent:
    """Packet event для аудита"""
    timestamp: float
    event: str
    bytes: int
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    data_preview: Optional[str] = None
    chunk_index: Optional[int] = None

class PacketCaptureLayer:
    """Layer для захвата packet событий"""
    
    def __init__(self):
        self.events: List[PacketEvent] = []
        self.lock = threading.Lock()
        self.enabled = False
        
    def enable(self):
        """Включить packet capture"""
        with self.lock:
            self.enabled = True
            self.events.clear()
    
    def disable(self):
        """Отключить packet capture"""
        with self.lock:
            self.enabled = False
    
    def log_connect(self, address: tuple):
        """Логировать connect"""
        if not self.enabled:
            return
            
        event = PacketEvent(
            timestamp=time.time(),
            event="socket_connect",
            bytes=0,
            remote_host=address[0],
            remote_port=address[1]
        )
        
        with self.lock:
            self.events.append(event)
    
    def log_send(self, data: bytes, chunk_index: Optional[int] = None):
        """Логировать send"""
        if not self.enabled:
            return
            
        event = PacketEvent(
            timestamp=time.time(),
            event="socket_send",
            bytes=len(data),
            data_preview=data[:32].hex() if len(data) > 0 else None,
            chunk_index=chunk_index
        )
        
        with self.lock:
            self.events.append(event)
    
    def log_recv(self, data: bytes):
        """Логировать recv"""
        if not self.enabled:
            return
            
        event = PacketEvent(
            timestamp=time.time(),
            event="socket_recv",
            bytes=len(data) if data else 0,
            data_preview=data[:32].hex() if data else None
        )
        
        with self.lock:
            self.events.append(event)
    
    def log_close(self):
        """Логировать close"""
        if not self.enabled:
            return
            
        event = PacketEvent(
            timestamp=time.time(),
            event="socket_close",
            bytes=0
        )
        
        with self.lock:
            self.events.append(event)
    
    def get_events(self) -> List[PacketEvent]:
        """Получить все события"""
        with self.lock:
            return self.events.copy()
    
    def clear_events(self):
        """Очистить события"""
        with self.lock:
            self.events.clear()
    
    def analyze_fragmentation(self) -> Dict:
        """Анализировать фрагментацию"""
        events = self.get_events()
        send_events = [e for e in events if e.event == "socket_send"]
        
        if not send_events:
            return {
                'fragments_sent': 0,
                'total_bytes': 0,
                'avg_fragment_size': 0,
                'fragmentation_detected': False
            }
        
        # Анализируем фрагментацию
        fragment_sizes = [e.bytes for e in send_events]
        total_bytes = sum(fragment_sizes)
        avg_fragment_size = total_bytes / len(fragment_sizes) if fragment_sizes else 0
        
        # Проверяем что это действительно фрагментация
        fragmentation_detected = len(set(fragment_sizes)) > 1 if fragment_sizes else False
        
        return {
            'fragments_sent': len(send_events),
            'total_bytes': total_bytes,
            'avg_fragment_size': avg_fragment_size,
            'fragmentation_detected': fragmentation_detected,
            'fragment_sizes': fragment_sizes
        }

# Global packet capture layer
_global_capture_layer: Optional[PacketCaptureLayer] = None

def get_packet_capture_layer() -> PacketCaptureLayer:
    """Получить глобальный packet capture layer"""
    global _global_capture_layer
    if _global_capture_layer is None:
        _global_capture_layer = PacketCaptureLayer()
    return _global_capture_layer

def enable_packet_capture():
    """Включить глобальный packet capture"""
    get_packet_capture_layer().enable()

def disable_packet_capture():
    """Отключить глобальный packet capture"""
    get_packet_capture_layer().disable()

def get_capture_events() -> List[PacketEvent]:
    """Получить все захваченные события"""
    return get_packet_capture_layer().get_events()

def clear_capture_events():
    """Очистить захваченные события"""
    get_packet_capture_layer().clear_events()

def analyze_capture() -> Dict:
    """Анализировать захваченные события"""
    return get_packet_capture_layer().analyze_fragmentation()
