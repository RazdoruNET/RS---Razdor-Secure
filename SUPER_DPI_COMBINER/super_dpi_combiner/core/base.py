#!/usr/bin/env python3
"""
Base Pipeline - Минимальный базовый класс
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class Request:
    """Минимальный запрос"""
    host: str
    port: int
    method: str = "GET"
    data: bytes = None
    timeout: float = 30.0

@dataclass 
class Response:
    """Минимальный ответ"""
    success: bool
    latency: float = 0.0
    status_code: int = 0
    data: bytes = None
    error: str = None

class BasePipeline(ABC):
    """Минимальный базовый пайплайн"""
    
    def __init__(self, name: str):
        self.name = name
        self.last_latency = 0.0
        
    @abstractmethod
    def execute(self, request: Request) -> Response:
        """Выполнить запрос"""
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        return {
            'name': self.name,
            'last_latency': self.last_latency
        }
