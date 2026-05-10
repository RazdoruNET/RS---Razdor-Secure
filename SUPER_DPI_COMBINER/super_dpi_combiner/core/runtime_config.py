#!/usr/bin/env python3
"""
Runtime Configuration - Детерминированная конфигурация runtime
Запрещено: random jitter, hidden retries, implicit fallback
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum

class RuntimeMode(Enum):
    """Режимы runtime"""
    TRUTH_MODE = "truth_mode"
    SIMULATION_MODE = "simulation_mode"
    DEBUG_MODE = "debug_mode"

@dataclass(slots=True)
class RuntimeConfig:
    """Детерминированная конфигурация runtime"""
    
    # Core runtime flags
    truth_mode: bool = True
    allow_simulation: bool = False
    allow_random_delays: bool = False
    allow_hidden_retries: bool = False
    allow_implicit_fallback: bool = False
    
    # Network configuration
    enable_packet_capture: bool = False
    enable_detailed_logging: bool = True
    connection_timeout: float = 10.0
    max_retries: int = 0  # 0 = no retries
    
    # Fragmentation configuration
    default_chunk_size: int = 100
    enable_adaptive_fragmentation: bool = False
    enable_random_jitter: bool = False
    min_inter_send_delay: float = 0.001
    max_inter_send_delay: float = 0.001
    
    # Background tasks
    enable_background_tasks: bool = False
    max_concurrent_tasks: int = 1
    
    # Metrics configuration
    enable_detailed_metrics: bool = False
    enable_performance_monitoring: bool = True
    metrics_retention_count: int = 1000
    
    # Debug configuration
    enable_debug_logging: bool = False
    enable_packet_tracing: bool = False
    enable_socket_inspection: bool = False
    
    def validate(self) -> Dict[str, Any]:
        """Валидировать конфигурацию"""
        violations = []
        
        # Проверяем запрещённые комбинации
        if not self.truth_mode and self.allow_simulation:
            violations.append("TRUTH_MODE must be True when ALLOW_SIMULATION is False")
        
        if self.allow_random_delays and self.truth_mode:
            violations.append("RANDOM_DELAYS not allowed in TRUTH_MODE")
        
        if self.allow_hidden_retries and self.truth_mode:
            violations.append("HIDDEN_RETRIES not allowed in TRUTH_MODE")
        
        if self.enable_background_tasks and self.truth_mode:
            violations.append("BACKGROUND_TASKS not allowed in TRUTH_MODE")
        
        if self.max_retries > 0 and self.truth_mode:
            violations.append("MAX_RETRIES > 0 not allowed in TRUTH_MODE")
        
        return {
            'valid': len(violations) == 0,
            'violations': violations
        }
    
    def get_mode(self) -> RuntimeMode:
        """Получить текущий режим"""
        if self.truth_mode and not self.allow_simulation:
            return RuntimeMode.TRUTH_MODE
        elif self.allow_simulation:
            return RuntimeMode.SIMULATION_MODE
        elif self.enable_debug_logging:
            return RuntimeMode.DEBUG_MODE
        else:
            return RuntimeMode.TRUTH_MODE
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь"""
        return {
            'runtime_mode': self.get_mode().value,
            'truth_mode': self.truth_mode,
            'allow_simulation': self.allow_simulation,
            'allow_random_delays': self.allow_random_delays,
            'allow_hidden_retries': self.allow_hidden_retries,
            'enable_packet_capture': self.enable_packet_capture,
            'connection_timeout': self.connection_timeout,
            'max_retries': self.max_retries,
            'default_chunk_size': self.default_chunk_size,
            'enable_background_tasks': self.enable_background_tasks,
            'enable_detailed_metrics': self.enable_detailed_metrics
        }

# Global runtime configuration
_global_config: RuntimeConfig = None

def get_runtime_config() -> RuntimeConfig:
    """Получить глобальную конфигурацию runtime"""
    global _global_config
    if _global_config is None:
        _global_config = RuntimeConfig()
    return _global_config

def set_runtime_config(config: RuntimeConfig):
    """Установить глобальную конфигурацию runtime"""
    global _global_config
    validation = config.validate()
    if not validation['valid']:
        raise ValueError(f"Invalid runtime configuration: {validation['violations']}")
    _global_config = config

def reset_runtime_config():
    """Сбросить конфигурацию runtime к значениям по умолчанию"""
    global _global_config
    _global_config = RuntimeConfig()
