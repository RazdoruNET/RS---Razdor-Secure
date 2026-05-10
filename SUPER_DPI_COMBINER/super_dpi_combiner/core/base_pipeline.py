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
import sys
import os

from .types import (
    PipelineStatus, PipelineExecutionStatus, BypassTechnique,
    PipelineMetrics, BypassRequest, BypassResponse
)

from super_dpi_combiner.utils.logger import get_tracer
from .network_reality_verifier import NetworkRealityVerifier, NetworkOperation
from .execution_trace import ExecutionTrace
from .reality_logger import get_reality_logger

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
        
        # Reality Logger for ТЗ-5
        self.reality_logger = get_reality_logger()
        
        # TASK 8.3 - Network Reality Verifier
        self.network_verifier = NetworkRealityVerifier()
        
        # TASK 8.4 - Simulation Detector (lazy import to avoid circular dependency)
        from core.simulation_detector import get_simulation_detector
        self.simulation_detector = get_simulation_detector()
        
        # Log import for Reality Logger
        try:
            self.reality_logger.log_import(
                component_name=self.name,
                success=True,
                is_simulation=(self.execution_status == PipelineExecutionStatus.SIMULATION),
                metadata={
                    'technique': self.technique.value,
                    'priority': self.priority,
                    'execution_status': self.execution_status.value
                }
            )
        except Exception as e:
            # Fallback logging if reality logger fails
            print(f"Reality Logger import logging failed for {self.name}: {e}")
        
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
            
            # Log execution for Reality Logger
            try:
                self.reality_logger.log_execute(
                    component_name=self.name,
                    success=response.success,
                    error=error,
                    is_simulation=response.simulation_detected,
                    duration=response_latency,
                    metadata={
                        'technique': self.technique.value,
                        'status_code': response.status_code,
                        'network_verified': response.network_verified,
                        'simulation_detected': response.simulation_detected,
                        'simulation_reason': response.simulation_reason,
                        'host': request.host,
                        'port': request.port,
                        'method': request.method
                    }
                )
            except Exception as e:
                # Fallback logging if reality logger fails
                print(f"Reality Logger execute logging failed for {self.name}: {e}")
            
            return response
            
        except asyncio.TimeoutError:
            error_msg = f"Pipeline {self.name} execution timeout ({timeout}s)"
            await trace.add_timeout("pipeline_execution", timeout)
            self.tracer.finish_pipeline(trace_id, "fail", error=error_msg)
            await trace.end_execution(success=False, final_status="timeout")
            
            # Log timeout for Reality Logger
            try:
                self.reality_logger.log_execute(
                    component_name=self.name,
                    success=False,
                    error=error_msg,
                    is_simulation=False,
                    duration=timeout,
                    metadata={
                        'technique': self.technique.value,
                        'error_type': 'TIMEOUT',
                        'timeout_duration': timeout,
                        'host': request.host,
                        'port': request.port,
                        'method': request.method
                    }
                )
            except Exception as e:
                print(f"Reality Logger timeout logging failed for {self.name}: {e}")
            
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
            
            # Log exception for Reality Logger
            try:
                self.reality_logger.log_execute(
                    component_name=self.name,
                    success=False,
                    error=error_msg,
                    is_simulation=False,
                    duration=time.time() - start_time,
                    metadata={
                        'technique': self.technique.value,
                        'error_type': type(e).__name__,
                        'exception_args': str(e.args),
                        'host': request.host,
                        'port': request.port,
                        'method': request.method
                    }
                )
            except Exception as re:
                print(f"Reality Logger exception logging failed for {self.name}: {re}")
            
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
        
        # Log initialization for Reality Logger
        try:
            self.reality_logger.log_init(
                component_name=self.name,
                success=success,
                is_simulation=(self.execution_status == PipelineExecutionStatus.SIMULATION),
                metadata={
                    'technique': self.technique.value,
                    'priority': self.priority,
                    'config_keys': list(self.config.keys()) if self.config else []
                }
            )
        except Exception as e:
            # Fallback logging if reality logger fails
            print(f"Reality Logger init logging failed for {self.name}: {e}")
        
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


class SafePipeline(BasePipeline):
    """
    Безопасная реализация BasePipeline с заглушками
    Используется как временная замена для сломанных пайплайнов
    """
    
    def __init__(self, name: str = "SafePipeline", technique: BypassTechnique = BypassTechnique.SPOOF_DPI, priority: int = 0, execution_status: PipelineExecutionStatus = PipelineExecutionStatus.SIMULATION):
        # Skip BasePipeline init to avoid circular imports
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
        self._initialized = False
        
        # Simple tracer without complex dependencies
        class SimpleLogger:
            def info(self, msg, **kwargs): print(f"[INFO] {msg}")
            def warning(self, msg, **kwargs): print(f"[WARN] {msg}")
            def error(self, msg, **kwargs): print(f"[ERROR] {msg}")
            def debug(self, msg, **kwargs): print(f"[DEBUG] {msg}")
        
        class SimpleTracer:
            def __init__(self):
                self.logger = SimpleLogger()
            def start_pipeline(self, *args, **kwargs): 
                return f"trace_{name}_{time.time()}"
            def finish_pipeline(self, *args, **kwargs): 
                pass
            # Add direct methods for compatibility
            def info(self, msg, **kwargs): 
                self.logger.info(msg, **kwargs)
            def warning(self, msg, **kwargs): 
                self.logger.warning(msg, **kwargs)
            def error(self, msg, **kwargs): 
                self.logger.error(msg, **kwargs)
            def debug(self, msg, **kwargs): 
                self.logger.debug(msg, **kwargs)
        
        self.tracer = SimpleTracer()
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """
        Безопасное выполнение - возвращает заглушку без сетевых операций
        """
        import time
        start_time = time.time()
        
        # Симуляция обработки
        await asyncio.sleep(0.001)  # Минимальная задержка для реалистичности
        
        return BypassResponse(
            success=True,
            latency=time.time() - start_time,
            status_code=200,
            headers={'X-Safe-Pipeline': 'true', 'X-Simulation': 'true'},
            data=b'SafePipeline: NO NETWORK - Simulation response',
            technique_used=self.name,
            network_verified=False,
            simulation_detected=True,
            simulation_reason="SafePipeline simulation mode"
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Безопасная инициализация - всегда успешна
        """
        self.config = config
        self._initialized = True
        self.tracer.logger.info(f"✅ {self.name} initialized safely (NO NETWORK)")
        return True
    
    def _mark_initialized(self, success: bool):
        """Отметка о статусе инициализации"""
        self._initialized = success
        if success:
            self.status = PipelineStatus.IDLE
        else:
            self.status = PipelineStatus.FAILED
    
    def _validate_initialized(self) -> bool:
        """Проверка инициализации пайплайна"""
        return self._initialized
