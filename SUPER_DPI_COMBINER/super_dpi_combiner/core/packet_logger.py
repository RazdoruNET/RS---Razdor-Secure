#!/usr/bin/env python3
"""
Packet-Level Logging - JSONL only format
Никаких print debugging, fake timing, synthetic metrics
"""

import json
import time
import threading
from typing import Dict, Any, Optional
from pathlib import Path

class PacketLogger:
    """JSONL packet logger"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or "runtime_packets.jsonl"
        self.lock = threading.Lock()
        self.enabled = False
        
        # Создаем log файл
        Path(self.log_file).touch(exist_ok=True)
    
    def enable(self):
        """Включить логирование"""
        with self.lock:
            self.enabled = True
            self._log_event("logger_enabled", {
                "timestamp": time.time()
            })
    
    def disable(self):
        """Отключить логирование"""
        with self.lock:
            if self.enabled:
                self._log_event("logger_disabled", {
                    "timestamp": time.time()
                })
                self.enabled = False
    
    def log_socket_connect(self, host: str, port: int, pipeline: Optional[str] = None):
        """Логировать socket connect"""
        if not self.enabled:
            return
            
        self._log_event("socket_connect", {
            "ts": time.time(),
            "event": "socket_connect",
            "remote_host": host,
            "remote_port": port,
            "pipeline": pipeline
        })
    
    def log_socket_send(self, bytes_count: int, data_preview: str, pipeline: Optional[str] = None):
        """Логировать socket send"""
        if not self.enabled:
            return
            
        self._log_event("socket_send", {
            "ts": time.time(),
            "event": "socket_send",
            "bytes": bytes_count,
            "data_preview": data_preview,
            "pipeline": pipeline
        })
    
    def log_socket_recv(self, bytes_count: int, data_preview: str, pipeline: Optional[str] = None):
        """Логировать socket recv"""
        if not self.enabled:
            return
            
        self._log_event("socket_recv", {
            "ts": time.time(),
            "event": "socket_recv",
            "bytes": bytes_count,
            "data_preview": data_preview,
            "pipeline": pipeline
        })
    
    def log_socket_close(self, pipeline: Optional[str] = None):
        """Логировать socket close"""
        if not self.enabled:
            return
            
        self._log_event("socket_close", {
            "ts": time.time(),
            "event": "socket_close",
            "pipeline": pipeline
        })
    
    def log_pipeline_start(self, pipeline: str, host: str, port: int):
        """Логировать начало pipeline"""
        if not self.enabled:
            return
            
        self._log_event("pipeline_start", {
            "ts": time.time(),
            "event": "pipeline_start",
            "pipeline": pipeline,
            "host": host,
            "port": port
        })
    
    def log_pipeline_finish(self, pipeline: str, success: bool, latency: float, status_code: int, error: Optional[str] = None):
        """Логировать завершение pipeline"""
        if not self.enabled:
            return
            
        event_data = {
            "ts": time.time(),
            "event": "pipeline_finish",
            "pipeline": pipeline,
            "success": success,
            "latency": latency,
            "status_code": status_code
        }
        
        if error:
            event_data["error"] = error
            
        self._log_event("pipeline_finish", event_data)
    
    def log_fragment_sent(self, fragment_size: int, fragment_index: int, pipeline: str):
        """Логировать отправленный фрагмент"""
        if not self.enabled:
            return
            
        self._log_event("fragment_sent", {
            "ts": time.time(),
            "event": "fragment_sent",
            "fragment_size": fragment_size,
            "fragment_index": fragment_index,
            "pipeline": pipeline
        })
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Записать событие в JSONL"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))
                f.write('\n')
        except Exception as e:
            # Не используем print - это нарушает правила
            pass

# Global packet logger
_global_packet_logger: Optional[PacketLogger] = None

def get_packet_logger() -> PacketLogger:
    """Получить глобальный packet logger"""
    global _global_packet_logger
    if _global_packet_logger is None:
        _global_packet_logger = PacketLogger()
    return _global_packet_logger

def enable_packet_logging(log_file: Optional[str] = None):
    """Включить глобальное packet logging"""
    global _global_packet_logger
    if _global_packet_logger is None:
        _global_packet_logger = PacketLogger(log_file)
    _global_packet_logger.enable()

def disable_packet_logging():
    """Отключить глобальное packet logging"""
    get_packet_logger().disable()

def log_socket_connect(host: str, port: int, pipeline: Optional[str] = None):
    """Логировать socket connect"""
    get_packet_logger().log_socket_connect(host, port, pipeline)

def log_socket_send(bytes_count: int, data_preview: str, pipeline: Optional[str] = None):
    """Логировать socket send"""
    get_packet_logger().log_socket_send(bytes_count, data_preview, pipeline)

def log_socket_recv(bytes_count: int, data_preview: str, pipeline: Optional[str] = None):
    """Логировать socket recv"""
    get_packet_logger().log_socket_recv(bytes_count, data_preview, pipeline)

def log_socket_close(pipeline: Optional[str] = None):
    """Логировать socket close"""
    get_packet_logger().log_socket_close(pipeline)

def log_pipeline_start(pipeline: str, host: str, port: int):
    """Логировать начало pipeline"""
    get_packet_logger().log_pipeline_start(pipeline, host, port)

def log_pipeline_finish(pipeline: str, success: bool, latency: float, status_code: int, error: Optional[str] = None):
    """Логировать завершение pipeline"""
    get_packet_logger().log_pipeline_finish(pipeline, success, latency, status_code, error)

def log_fragment_sent(fragment_size: int, fragment_index: int, pipeline: str):
    """Логировать отправленный фрагмент"""
    get_packet_logger().log_fragment_sent(fragment_size, fragment_index, pipeline)
