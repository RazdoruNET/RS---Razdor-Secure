#!/usr/bin/env python3
"""
Runtime Contracts - Immutable definitions for Super DPI Combiner
Только essential types без лишней функциональности
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from enum import Enum

class PipelineStatus(Enum):
    """Статус пайплайна - только essential"""
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"

@dataclass(slots=True)
class Request:
    """Immutable Request contract"""
    host: str
    port: int
    method: str = "GET"
    path: str = "/"
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    timeout: float = 10.0

@dataclass(slots=True)
class Response:
    """Immutable Response contract"""
    success: bool
    status_code: int = 0
    latency: float = 0.0
    pipeline: str = ""
    error: Optional[str] = None
    data: bytes = b""
    headers: Dict[str, str] = field(default_factory=dict)

class BasePipeline(ABC):
    """Minimal Base Pipeline - только essential interface"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = PipelineStatus.IDLE
        
    @abstractmethod
    async def execute(self, request: Request) -> Response:
        """
        Выполнить запрос - только реальная работа
        Никакой симуляции, никаких fallback
        """
        pass
        
    def get_status(self) -> PipelineStatus:
        """Получить текущий статус"""
        return self.status
        
    def set_status(self, status: PipelineStatus) -> None:
        """Установить статус"""
        self.status = status
