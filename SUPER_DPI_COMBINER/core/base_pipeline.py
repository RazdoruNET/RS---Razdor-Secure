#!/usr/bin/env python3
"""
Базовый класс пайплайна для обхода DPI
Фундамент для всех техник обхода Deep Packet Inspection
"""

import abc
import asyncio
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class PipelineStatus(Enum):
    """Статусы пайплайна"""
    IDLE = "idle"
    ACTIVE = "active"
    FAILED = "failed"
    OPTIMIZING = "optimizing"

class BypassTechnique(Enum):
    """Типы техник обхода"""
    SPOOF_DPI = "spoof_dpi"
    DOMAIN_FRONTING = "domain_fronting"
    PROTOCOL_OBFUSCATION = "protocol_obfuscation"
    TOR_INTEGRATION = "tor_integration"
    OMEGA_TRANSPORT = "omega_transport"
    ADAPTIVE = "adaptive"

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
    """Ответ от пайплайна"""
    success: bool
    status_code: int = 0
    headers: Dict[str, str] = None
    data: bytes = None
    response_time: float = 0.0
    error: str = None
    technique_used: str = None

class BasePipeline(abc.ABC):
    """Базовый абстрактный класс для всех пайплайнов обхода DPI"""
    
    def __init__(self, name: str, technique: BypassTechnique, priority: int = 0):
        self.name = name
        self.technique = technique
        self.priority = priority
        self.status = PipelineStatus.IDLE
        self.metrics = PipelineMetrics()
        self.config = {}
        self.lock = threading.Lock()
        
        # Внутреннее состояние
        self._start_time = None
        self._active_connections = {}
        self._performance_history = []
        
    @abc.abstractmethod
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """
        Основной метод выполнения пайплайна
        
        Args:
            request: Запрос на обход DPI
            
        Returns:
            BypassResponse: Результат выполнения
        """
        pass
    
    @abc.abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Инициализация пайплайна с конфигурацией
        
        Args:
            config: Конфигурация пайплайна
            
        Returns:
            bool: Успешность инициализации
        """
        pass
    
    @abc.abstractmethod
    def cleanup(self) -> bool:
        """
        Очистка ресурсов пайплайна
        
        Returns:
            bool: Успешность очистки
        """
        pass
    
    def update_metrics(self, success: bool, response_time: float):
        """Обновление метрик производительности"""
        with self.lock:
            self.metrics.total_requests += 1
            
            if success:
                self.metrics.last_success = time.time()
                self.metrics.success_rate = (
                    (self.metrics.total_requests - self.metrics.failed_requests) 
                    / self.metrics.total_requests
                )
            else:
                self.metrics.failed_requests += 1
                self.metrics.last_failure = time.time()
                self.metrics.success_rate = (
                    (self.metrics.total_requests - self.metrics.failed_requests) 
                    / self.metrics.total_requests
                )
            
            # Обновление среднего времени отклика
            if self.metrics.avg_response_time == 0:
                self.metrics.avg_response_time = response_time
            else:
                self.metrics.avg_response_time = (
                    self.metrics.avg_response_time * 0.8 + response_time * 0.2
                )
            
            # Сохранение в историю
            self._performance_history.append({
                'timestamp': time.time(),
                'success': success,
                'response_time': response_time
            })
            
            # Ограничение истории
            if len(self._performance_history) > 1000:
                self._performance_history = self._performance_history[-1000:]
    
    def get_performance_score(self) -> float:
        """
        Расчет общей оценки производительности
        
        Returns:
            float: Оценка от 0.0 до 1.0
        """
        with self.lock:
            # Веса для разных метрик
            success_weight = 0.5
            speed_weight = 0.3
            stability_weight = 0.2
            
            # Нормализация времени отклика (меньше = лучше)
            speed_score = max(0, 1 - (self.metrics.avg_response_time / 10.0))
            
            # Стабильность на основе последних 10 запросов
            recent_history = self._performance_history[-10:]
            if len(recent_history) >= 5:
                recent_success = sum(1 for h in recent_history if h['success'])
                stability_score = recent_success / len(recent_history)
            else:
                stability_score = self.metrics.success_rate
            
            # Общая оценка
            total_score = (
                self.metrics.success_rate * success_weight +
                speed_score * speed_weight +
                stability_score * stability_weight
            )
            
            return min(1.0, max(0.0, total_score))
    
    def is_healthy(self) -> bool:
        """
        Проверка здоровья пайплайна
        
        Returns:
            bool: Состояние пайплайна
        """
        with self.lock:
            # Пайплайн здоров если:
            # 1. Успешность > 30%
            # 2. Среднее время < 30 секунд
            # 3. Не было фатальных ошибок
            # 4. Есть недавние успешные запросы
            
            if self.metrics.total_requests < 5:
                return True  # Недостаточно данных для оценки
            
            time_since_last_success = time.time() - self.metrics.last_success
            recent_success = time_since_last_success < 300  # 5 минут
            
            return (
                self.metrics.success_rate > 0.3 and
                self.metrics.avg_response_time < 30.0 and
                self.status != PipelineStatus.FAILED and
                (recent_success or self.metrics.total_requests < 10)
            )
    
    async def health_check(self) -> bool:
        """
        Асинхронная проверка здоровья
        
        Returns:
            bool: Результат проверки
        """
        try:
            # Создаем тестовый запрос
            test_request = BypassRequest(
                host="www.google.com",
                port=443,
                method="HEAD",
                timeout=5.0
            )
            
            # Выполняем тест
            response = await self.execute(test_request)
            
            # Обновляем метрики
            self.update_metrics(response.success, response.response_time)
            
            return response.success
            
        except Exception as e:
            self.update_metrics(False, 0.0)
            return False
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Получение детальной информации о статусе
        
        Returns:
            Dict: Информация о пайплайне
        """
        with self.lock:
            return {
                'name': self.name,
                'technique': self.technique.value,
                'priority': self.priority,
                'status': self.status.value,
                'metrics': {
                    'success_rate': self.metrics.success_rate,
                    'avg_response_time': self.metrics.avg_response_time,
                    'total_requests': self.metrics.total_requests,
                    'failed_requests': self.metrics.failed_requests,
                    'active_connections': self.metrics.active_connections,
                    'performance_score': self.get_performance_score()
                },
                'config': self.config,
                'healthy': self.is_healthy(),
                'last_success': self.metrics.last_success,
                'last_failure': self.metrics.last_failure
            }
    
    def reset_metrics(self):
        """Сброс метрик производительности"""
        with self.lock:
            self.metrics = PipelineMetrics()
            self._performance_history = []
    
    def set_status(self, status: PipelineStatus):
        """Установка статуса пайплайна"""
        with self.lock:
            self.status = status
    
    def __str__(self) -> str:
        return f"Pipeline({self.name}, {self.technique.value}, Priority: {self.priority})"
    
    def __repr__(self) -> str:
        return self.__str__()
