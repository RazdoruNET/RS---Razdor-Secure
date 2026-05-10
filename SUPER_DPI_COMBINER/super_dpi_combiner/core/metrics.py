#!/usr/bin/env python3
"""
Structured Metrics System - Структурированные метрики runtime
JSON-only format, без debug output
"""

import time
import threading
import json
from typing import Dict, Any, List
from dataclasses import dataclass, field
from .runtime_config import get_runtime_config

@dataclass(slots=True)
class RuntimeMetrics:
    """Метрики runtime"""
    
    # Runtime metrics
    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    avg_latency: float = 0.0
    
    # Network metrics
    bytes_sent: int = 0
    bytes_received: int = 0
    sockets_opened: int = 0
    sockets_closed: int = 0
    
    # Fragmentation metrics
    fragments_sent: int = 0
    avg_fragment_size: float = 0.0
    fragmentation_ratio: float = 0.0
    
    # Performance metrics
    min_latency: float = 0.0
    max_latency: float = 0.0
    p95_latency: float = 0.0
    
    # Timestamp
    last_updated: float = field(default_factory=time.time)

class MetricsCollector:
    """Коллектор метрик"""
    
    def __init__(self):
        self.metrics = RuntimeMetrics()
        self.lock = threading.Lock()
        self.history: List[Dict[str, Any]] = []
        
    def record_request_start(self, pipeline: str):
        """Записать начало запроса"""
        with self.lock:
            self.metrics.requests_total += 1
            self._add_history_event("request_start", {
                "pipeline": pipeline,
                "timestamp": time.time()
            })
    
    def record_request_success(self, pipeline: str, latency: float, bytes_sent: int = 0, bytes_received: int = 0):
        """Записать успешный запрос"""
        with self.lock:
            self.metrics.requests_success += 1
            self.metrics.bytes_sent += bytes_sent
            self.metrics.bytes_received += bytes_received
            
            # Обновляем latency метрики
            self._update_latency_metrics(latency)
            
            self._add_history_event("request_success", {
                "pipeline": pipeline,
                "latency": latency,
                "bytes_sent": bytes_sent,
                "bytes_received": bytes_received,
                "timestamp": time.time()
            })
    
    def record_request_failure(self, pipeline: str, error: str):
        """Записать неудачный запрос"""
        with self.lock:
            self.metrics.requests_failed += 1
            self._add_history_event("request_failure", {
                "pipeline": pipeline,
                "error": error,
                "timestamp": time.time()
            })
    
    def record_socket_opened(self):
        """Записать открытие сокета"""
        with self.lock:
            self.metrics.sockets_opened += 1
            self._add_history_event("socket_opened", {
                "timestamp": time.time()
            })
    
    def record_socket_closed(self):
        """Записать закрытие сокета"""
        with self.lock:
            self.metrics.sockets_closed += 1
            self._add_history_event("socket_closed", {
                "timestamp": time.time()
            })
    
    def record_fragment_sent(self, fragment_size: int):
        """Записать отправленный фрагмент"""
        with self.lock:
            self.metrics.fragments_sent += 1
            
            # Обновляем метрики фрагментации
            total_bytes = self.metrics.fragments_sent * fragment_size
            self.metrics.avg_fragment_size = total_bytes / self.metrics.fragments_sent if self.metrics.fragments_sent > 0 else 0
            
            if self.metrics.bytes_sent > 0:
                self.metrics.fragmentation_ratio = self.metrics.fragments_sent / (self.metrics.bytes_sent / fragment_size)
            
            self._add_history_event("fragment_sent", {
                "fragment_size": fragment_size,
                "timestamp": time.time()
            })
    
    def _update_latency_metrics(self, latency: float):
        """Обновить метрики latency"""
        if self.metrics.requests_total == 1:
            # Первый запрос
            self.metrics.min_latency = latency
            self.metrics.max_latency = latency
            self.metrics.p95_latency = latency
            self.metrics.avg_latency = latency
        else:
            # Обновляем min/max
            self.metrics.min_latency = min(self.metrics.min_latency, latency)
            self.metrics.max_latency = max(self.metrics.max_latency, latency)
            
            # Обновляем среднее
            self.metrics.avg_latency = (self.metrics.avg_latency * (self.metrics.requests_total - 1) + latency) / self.metrics.requests_total
            
            # P95 (упрощённое вычисление)
            # Для точного P95 нужен массив всех latency, но это сложно без storage
            # Используем approximation: max_latency * 0.95
            self.metrics.p95_latency = self.metrics.max_latency * 0.95
    
    def _add_history_event(self, event_type: str, data: Dict[str, Any]):
        """Добавить событие в историю"""
        config = get_runtime_config()
        
        if config.enable_detailed_metrics:
            event = {
                "type": event_type,
                "timestamp": data["timestamp"],
                "data": data
            }
            
            self.history.append(event)
            
            # Ограничиваем историю
            if len(self.history) > config.metrics_retention_count:
                self.history = self.history[-config.metrics_retention_count:]
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Получить снепшот метрик"""
        with self.lock:
            return {
                "timestamp": time.time(),
                "runtime": {
                    "requests_total": self.metrics.requests_total,
                    "requests_success": self.metrics.requests_success,
                    "requests_failed": self.metrics.requests_failed,
                    "success_rate": (self.metrics.requests_success / self.metrics.requests_total * 100) if self.metrics.requests_total > 0 else 0,
                    "avg_latency": self.metrics.avg_latency,
                    "min_latency": self.metrics.min_latency,
                    "max_latency": self.metrics.max_latency,
                    "p95_latency": self.metrics.p95_latency
                },
                "network": {
                    "bytes_sent": self.metrics.bytes_sent,
                    "bytes_received": self.metrics.bytes_received,
                    "sockets_opened": self.metrics.sockets_opened,
                    "sockets_closed": self.metrics.sockets_closed,
                    "active_sockets": self.metrics.sockets_opened - self.metrics.sockets_closed
                },
                "fragmentation": {
                    "fragments_sent": self.metrics.fragments_sent,
                    "avg_fragment_size": self.metrics.avg_fragment_size,
                    "fragmentation_ratio": self.metrics.fragmentation_ratio
                },
                "history_count": len(self.history)
            }
    
    def reset_metrics(self):
        """Сбросить метрики"""
        with self.lock:
            self.metrics = RuntimeMetrics()
            self.history.clear()
            self._add_history_event("metrics_reset", {
                "timestamp": time.time()
            })

# Global metrics collector
_global_metrics_collector: MetricsCollector = None

def get_metrics_collector() -> MetricsCollector:
    """Получить глобальный коллектор метрик"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector
