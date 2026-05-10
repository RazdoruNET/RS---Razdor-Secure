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
import sys
import os

# Add parent directory to path for logger import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_tracer
from .network_reality_verifier import NetworkRealityVerifier, NetworkOperation
from .simulation_detector import get_simulation_detector

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

class BasePipeline(abc.ABC):
    """Базовый абстрактный класс для всех пайплайнов обхода DPI"""
    
    def __init__(self, name: str, technique: BypassTechnique, priority: int = 0, execution_status: PipelineExecutionStatus = PipelineExecutionStatus.SIMULATION):
        self.name = name
        self.technique = technique
        self.priority = priority
        self.status = PipelineStatus.IDLE
        self.execution_status = execution_status
        self.metrics = PipelineMetrics()
        self.config = {}
        self.lock = threading.Lock()
        
        # Внутреннее состояние
        self._start_time = None
        self._active_connections = {}
        self._performance_history = []
        self._initialized = False  # Флаг инициализации
        
        # Tracer for pipeline execution
        self.tracer = get_tracer(f"pipeline.{name}")
        
        # TASK 8.3 - Network Reality Verifier
        self.network_verifier = NetworkRealityVerifier()
        
        # TASK 8.4 - Simulation Detector
        self.simulation_detector = get_simulation_detector()
        
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
    
    def _validate_initialized(self) -> bool:
        """
        Проверка инициализации пайплайна
        
        Returns:
            bool: True если пайплайн инициализирован
        """
        return hasattr(self, '_initialized') and self._initialized
    
    async def safe_execute(self, request: BypassRequest, timeout: float = 30.0) -> BypassResponse:
        """
        Безопасное выполнение с изоляцией ошибок и таймаутом
        
        Args:
            request: Запрос на обход DPI
            timeout: Максимальное время выполнения
            
        Returns:
            BypassResponse: Результат выполнения (всегда валидный)
        """
        start_time = time.time()
        
        # Create execution trace for this run
        trace = self.create_execution_trace()
        await trace.start_execution()
        
        # Start pipeline trace
        trace_id = self.tracer.start_pipeline(
            self.name,
            host=request.host,
            port=request.port,
            method=request.method,
            timeout=timeout,
            technique=self.technique.value
        )
        
        # Проверка инициализации
        if not self._validate_initialized():
            error_msg = f"Pipeline {self.name} not initialized"
            await trace.add_error("PIPELINE_NOT_INITIALIZED", error_msg)
            self.tracer.finish_pipeline(trace_id, "fail", error=error_msg)
            await trace.end_execution(success=False, final_status="not_initialized")
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=error_msg,
                response_time=time.time() - start_time
            )
        
        try:
            # Выполняем с таймаутом
            response = await asyncio.wait_for(self.execute(request), timeout=timeout)
            
            # Убеждаемся что ответ валидный
            if not isinstance(response, BypassResponse):
                error_msg = f"Invalid response type from {self.name}"
                await trace.add_error("INVALID_RESPONSE_TYPE", error_msg)
                self.tracer.finish_pipeline(trace_id, "fail", error=error_msg)
                await trace.end_execution(success=False, final_status="invalid_response")
                return BypassResponse(
                    success=False,
                    latency=time.time() - start_time,
                    error_reason=error_msg,
                    response_time=time.time() - start_time
                )
            
            # Обновляем latency и response_time
            response_latency = time.time() - start_time
            response.latency = response_latency
            response.response_time = response_latency
            
            # TASK 8.3 - Network Reality Verification
            await self._verify_network_reality(response, request)
            
            # TASK 8.4 - Simulation Detection
            await self._detect_simulation(response, request, trace)
            
            # Finish trace with success
            status = "success" if response.success else "fail"
            error = response.error_reason if not response.success else None
            self.tracer.finish_pipeline(trace_id, status, 
                                       error=error,
                                       status_code=response.status_code,
                                       response_size=len(response.data) if response.data else 0)
            
            # End execution trace
            final_status = "success" if response.success else "failed"
            await trace.end_execution(success=response.success, final_status=final_status)
            
            return response
            
        except asyncio.TimeoutError:
            error_msg = f"Pipeline {self.name} execution timeout ({timeout}s)"
            await trace.add_timeout("pipeline_execution", timeout)
            self.tracer.finish_pipeline(trace_id, "fail", error=error_msg)
            await trace.end_execution(success=False, final_status="timeout")
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=error_msg,
                response_time=time.time() - start_time
            )
        except Exception as e:
            error_msg = f"Pipeline {self.name} execution error: {str(e)}"
            await trace.add_error("PIPELINE_EXECUTION_ERROR", error_msg, {
                'exception_type': type(e).__name__,
                'exception_args': str(e.args)
            })
            self.tracer.finish_pipeline(trace_id, "fail", error=error_msg)
            await trace.end_execution(success=False, final_status="error")
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=error_msg,
                response_time=time.time() - start_time
            )
    
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
    
    def _mark_initialized(self, success: bool):
        """
        Отметка о статусе инициализации
        
        Args:
            success: Успешность инициализации
        """
        self._initialized = success
        if success:
            self.set_status(PipelineStatus.IDLE)
        else:
            self.set_status(PipelineStatus.FAILED)
    
    async def _verify_network_reality(self, response: BypassResponse, request: BypassRequest):
        """
        TASK 8.3 - Верификация реальности сетевых операций
        
        Args:
            response: Ответ от пайплайна
            request: Исходный запрос
        """
        try:
            # Создаем операцию для верификации на основе ответа
            operation = NetworkOperation(
                operation_type="connect",  # По умолчанию проверяем подключение
                claimed_success=response.success,
                timestamp=time.time(),
                target_host=request.host,
                target_port=request.port
            )
            
            # Если есть данные в ответе, проверяем получение
            if response.data and len(response.data) > 0:
                operation.operation_type = "recv"
                operation.claimed_bytes = len(response.data)
            
            # Выполняем верификацию
            verification_result = await self.network_verifier.verify_network_operation(operation)
            
            # Устанавливаем флаг верификации в ответ
            response.network_verified = verification_result.network_verified
            
            # Логируем результат
            if verification_result.network_verified:
                self.tracer.logger.info(f"✅ Network reality verified for {self.name}")
            else:
                self.tracer.logger.warning(f"⚠️ Network reality NOT verified for {self.name}")
                
        except Exception as e:
            self.tracer.logger.error(f"❌ Network reality verification failed: {e}")
            response.network_verified = False
    
    async def _detect_simulation(self, response: BypassResponse, request: BypassRequest, trace):
        """
        TASK 8.4 - Детекция симуляций
        
        Args:
            response: Ответ от пайплайна
            request: Исходный запрос
            trace: Execution trace для анализа
        """
        try:
            # Выполняем анализ симуляции
            detection_result = self.simulation_detector.analyze_pipeline_execution(
                execution_trace=trace,
                response_success=response.success,
                pipeline_name=self.name
            )
            
            # Устанавливаем результаты в ответ
            response.simulation_detected = detection_result.simulation_detected
            response.simulation_reason = detection_result.reason
            
            # Логируем результат
            if detection_result.simulation_detected:
                self.tracer.logger.warning(
                    f"⚠️ SIMULATION DETECTED in {self.name}: {detection_result.reason} "
                    f"(confidence: {detection_result.confidence:.2f})"
                )
                trace.add_error("SIMULATION_DETECTED", detection_result.reason, detection_result.details)
            else:
                self.tracer.logger.info(f"✅ No simulation detected in {self.name}")
                
        except Exception as e:
            self.tracer.logger.error(f"❌ Simulation detection failed: {e}")
            response.simulation_detected = False
            response.simulation_reason = None
    
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
                'execution_status': self.execution_status.value,
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
    
    def create_execution_trace(self) -> ExecutionTrace:
        """Create new execution trace for this pipeline"""
        self.execution_trace = ExecutionTrace(self.name)
        return self.execution_trace
    
    def get_execution_trace(self) -> Optional[ExecutionTrace]:
        """Get current execution trace"""
        return self.execution_trace
    
    def clear_execution_trace(self):
        """Clear current execution trace"""
        self.execution_trace = None
    
    def __str__(self) -> str:
        return f"Pipeline({self.name}, {self.technique.value}, Priority: {self.priority})"
    
    def __repr__(self) -> str:
        return self.__str__()
