#!/usr/bin/env python3
"""
Shared types for Super DPI Combiner
Extracted to break circular imports between core and pipelines
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

class PipelineStatus(Enum):
    """Статусы пайплайна"""
    IDLE = "idle"
    ACTIVE = "active"
    FAILED = "failed"
    OPTIMIZING = "optimizing"

class PipelineExecutionStatus(Enum):
    """Статус выполнения пайплайна - реальность операций"""
    REAL = "REAL"          # Выполняет реальные сетевые операции
    PARTIAL = "PARTIAL"    # Частично реальные операции
    SIMULATION = "SIMULATION"  # Только симуляция/заглушки

class BypassTechnique(Enum):
    """Типы техник обхода"""
    SPOOF_DPI = "spoof_dpi"
    DOMAIN_FRONTING = "domain_fronting"
    PROTOCOL_OBFUSCATION = "protocol_obfuscation"
    TOR_INTEGRATION = "tor_integration"
    OMEGA_TRANSPORT = "omega_transport"
    ADAPTIVE = "adaptive"
    DARKNET = "darknet"
    SECRET_DATABASES = "secret_databases"
    ADVANCED_OBFUSCATION = "advanced_obfuscation"
    BLOCKCHAIN_INTEGRATION = "blockchain_integration"

@dataclass
class PipelineMetrics:
    """Метрики производительности пайплайна"""
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    last_success: float = 0.0
    last_failure: float = 0.0
    active_connections: int = 0

@dataclass
class BypassRequest:
    """Запрос на обход DPI"""
    host: str
    port: int
    method: str = "GET"
    headers: Dict[str, str] = None
    data: bytes = None
    timeout: float = 30.0

@dataclass
class BypassResponse:
    """Стандартизированный ответ от пайплайна"""
    success: bool
    latency: float = 0.0  # Обязательное поле latency
    status_code: int = 0
    headers: Dict[str, str] = None
    data: bytes = None
    error_reason: str = None  # Переименовано из error для стандартизации
    technique_used: str = None
    response_time: float = 0.0  # Оставлено для обратной совместимости
    network_verified: bool = False  # TASK 8.3 - Network Reality Verifier
    simulation_detected: bool = False  # TASK 8.4 - Simulation Detector
    simulation_reason: str = None  # TASK 8.4 - Simulation Detector
