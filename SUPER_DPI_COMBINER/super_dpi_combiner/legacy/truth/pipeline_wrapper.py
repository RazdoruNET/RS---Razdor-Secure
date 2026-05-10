#!/usr/bin/env python3
"""
Pipeline Truth Wrapper - единый API слой для всех пайплайнов
Обеспечивает унифицированную обертку с трассировкой и валидацией
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Tuple, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from datetime import datetime

from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse
from core.truth.instrumentation import get_io_monitor, IOOperationType, require_real_io, async_require_real_io
from core.truth.metrics_engine import get_truth_metrics_engine
from core.execution_trace import ExecutionTrace as CoreExecutionTrace

class ExecutionStatus(Enum):
    """Статусы выполнения пайплайна"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID = "invalid"

class ValidationLevel(Enum):
    """Уровни валидации"""
    BASIC = "basic"           # Базовая проверка
    STRICT = "strict"         # Строгая проверка с I/O
    COMPREHENSIVE = "comprehensive"  # Полная проверка

@dataclass
class ExecutionStep:
    """Шаг выполнения пайплайна"""
    step_id: str
    name: str
    timestamp: float
    duration: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IOValidationResult:
    """Результат валидации I/O операций"""
    has_real_io: bool
    total_operations: int
    operation_types: Dict[str, int]
    bytes_transferred: Dict[str, int]
    errors_detected: int
    validation_errors: List[str] = field(default_factory=list)

@dataclass
class PipelineExecutionTrace:
    """Трассировка выполнения пайплайна"""
    trace_id: str
    pipeline_name: str
    pipeline_type: str
    request: BypassRequest
    response: Optional[BypassResponse] = None
    
    # Метрики времени
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    
    # Статус и ошибки
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None
    
    # Шаги выполнения
    steps: List[ExecutionStep] = field(default_factory=list)
    
    # I/O валидация
    io_validation: Optional[IOValidationResult] = None
    
    # Метаданные
    thread_id: int = field(default_factory=threading.get_ident)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, name: str, success: bool = True, error: Optional[str] = None, 
                 metadata: Dict[str, Any] = None) -> str:
        """Добавить шаг выполнения"""
        step_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Вычисляем длительность шага
        duration = 0.0
        if self.steps:
            last_step = self.steps[-1]
            duration = timestamp - (last_step.timestamp + last_step.duration)
        
        step = ExecutionStep(
            step_id=step_id,
            name=name,
            timestamp=timestamp,
            duration=duration,
            success=success,
            error=error,
            metadata=metadata or {}
        )
        
        self.steps.append(step)
        return step_id
    
    def finish(self, status: ExecutionStatus, response: Optional[BypassResponse] = None, 
               error: Optional[str] = None):
        """Завершить трассировку"""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        self.status = status
        self.response = response
        self.error = error
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить сводную информацию о трассировке"""
        return {
            'trace_id': self.trace_id,
            'pipeline_name': self.pipeline_name,
            'pipeline_type': self.pipeline_type,
            'status': self.status.value,
            'total_duration': self.total_duration,
            'steps_count': len(self.steps),
            'successful_steps': sum(1 for s in self.steps if s.success),
            'failed_steps': sum(1 for s in self.steps if not s.success),
            'has_io_validation': self.io_validation is not None,
            'has_real_io': self.io_validation.has_real_io if self.io_validation else False,
            'thread_id': self.thread_id
        }

class PipelineValidator:
    """Валидатор выполнения пайплайнов"""
    
    def __init__(self):
        self.io_monitor = get_io_monitor()
    
    def validate_io_operations(self, trace: PipelineExecutionTrace, 
                              level: ValidationLevel = ValidationLevel.STRICT) -> IOValidationResult:
        """Валидация I/O операций"""
        
        # Получаем статистику I/O операций
        stats = self.io_monitor.get_statistics()
        recent_ops = self.io_monitor.get_recent_operations(100)
        
        # Фильтруем операции за время выполнения трассировки
        execution_ops = [
            op for op in recent_ops 
            if op.timestamp >= trace.start_time and (trace.end_time is None or op.timestamp <= trace.end_time)
        ]
        
        # Если операций в временном окне нет, используем все недавние операции
        if not execution_ops:
            execution_ops = recent_ops
        
        # Базовая валидация
        total_operations = len(execution_ops)
        operation_types = {}
        bytes_transferred = {}
        errors_detected = 0
        validation_errors = []
        
        for op in execution_ops:
            op_type = op.operation_type.value
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
            bytes_transferred[op_type] = bytes_transferred.get(op_type, 0) + op.data_size
            
            if not op.success:
                errors_detected += 1
        
        # Проверка наличия реальных I/O операций
        has_real_io = total_operations > 0 or stats['io_operations_in_session']
        
        # Строгая валидация
        if level in [ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
            if not has_real_io:
                validation_errors.append("No real I/O operations detected")
            
            if total_operations == 0:
                validation_errors.append("No I/O operations recorded")
            
            # Проверка на минимальный объем данных
            total_bytes = sum(bytes_transferred.values())
            if total_bytes == 0:
                validation_errors.append("No bytes transferred")
        
        # Комплексная валидация
        if level == ValidationLevel.COMPREHENSIVE:
            # Проверка на баланс отправки/получения
            send_bytes = bytes_transferred.get('socket_send', 0) + bytes_transferred.get('asyncio_write', 0)
            recv_bytes = bytes_transferred.get('socket_recv', 0) + bytes_transferred.get('asyncio_read', 0)
            
            if send_bytes > 0 and recv_bytes == 0:
                validation_errors.append("Data sent but no data received")
            
            # Проверка на ошибки
            error_rate = errors_detected / max(1, total_operations)
            if error_rate > 0.5:
                validation_errors.append(f"High error rate: {error_rate:.2%}")
        
        return IOValidationResult(
            has_real_io=has_real_io,
            total_operations=total_operations,
            operation_types=operation_types,
            bytes_transferred=bytes_transferred,
            errors_detected=errors_detected,
            validation_errors=validation_errors
        )
    
    def validate_response(self, trace: PipelineExecutionTrace) -> List[str]:
        """Валидация ответа пайплайна"""
        validation_errors = []
        
        if not trace.response:
            validation_errors.append("No response received")
            return validation_errors
        
        response = trace.response
        
        # Проверка обязательных полей
        if not hasattr(response, 'success'):
            validation_errors.append("Response missing 'success' field")
        
        if not hasattr(response, 'latency'):
            validation_errors.append("Response missing 'latency' field")
        
        # Проверка логических значений
        if hasattr(response, 'success') and response.success and not trace.io_validation:
            validation_errors.append("Success reported but no I/O validation")
        
        if hasattr(response, 'latency') and response.latency <= 0:
            validation_errors.append("Invalid latency value")
        
        return validation_errors
    
    def validate_trace(self, trace: PipelineExecutionTrace, 
                      level: ValidationLevel = ValidationLevel.STRICT) -> List[str]:
        """Комплексная валидация трассировки"""
        validation_errors = []
        
        # Базовые проверки
        if not trace.trace_id:
            validation_errors.append("Missing trace ID")
        
        if not trace.pipeline_name:
            validation_errors.append("Missing pipeline name")
        
        if trace.start_time <= 0:
            validation_errors.append("Invalid start time")
        
        if trace.end_time and trace.end_time <= trace.start_time:
            validation_errors.append("Invalid end time")
        
        # Валидация I/O операций
        io_validation = self.validate_io_operations(trace, level)
        trace.io_validation = io_validation
        
        validation_errors.extend(io_validation.validation_errors)
        
        # Валидация ответа
        response_errors = self.validate_response(trace)
        validation_errors.extend(response_errors)
        
        return validation_errors

async def execute_with_truth(pipeline: BasePipeline, 
                           request: BypassRequest,
                           validation_level: ValidationLevel = ValidationLevel.STRICT,
                           timeout: Optional[float] = None) -> Tuple[BypassResponse, PipelineExecutionTrace]:
    """
    Унифицированная обертка выполнения пайплайна с трассировкой и валидацией
    
    Args:
        pipeline: Пайплайн для выполнения
        request: Запрос на обход DPI
        validation_level: Уровень валидации
        timeout: Таймаут выполнения
        
    Returns:
        Tuple[BypassResponse, PipelineExecutionTrace]: Результат и трассировка
    """
    
    # Создаем трассировку
    trace = PipelineExecutionTrace(
        trace_id=str(uuid.uuid4()),
        pipeline_name=pipeline.name,
        pipeline_type=pipeline.technique.value,
        request=request
    )
    
    # Создаем core execution trace для метрик
    core_trace = CoreExecutionTrace(pipeline.name)
    core_trace.start_execution()
    
    validator = PipelineValidator()
    
    try:
        # Шаг 1: Валидация входных данных
        trace.add_step("input_validation", True)
        
        # Шаг 2: Проверка инициализации пайплайна
        if not pipeline._validate_initialized():
            raise RuntimeError(f"Pipeline {pipeline.name} not initialized")
        trace.add_step("pipeline_check", True)
        
        # Шаг 3: Сброс сессии I/O мониторинга
        get_io_monitor().reset_session()
        trace.add_step("io_session_reset", True)
        
        # Шаг 4: Выполнение пайплайна
        trace.add_step("pipeline_execution_start", True)
        
        if timeout:
            response = await asyncio.wait_for(pipeline.execute(request), timeout=timeout)
        else:
            response = await pipeline.execute(request)
        
        trace.add_step("pipeline_execution_complete", True, metadata={
            'response_success': response.success,
            'response_latency': getattr(response, 'latency', 0),
            'status_code': getattr(response, 'status_code', 0)
        })
        
        # Шаг 5: Валидация I/O операций
        trace.add_step("io_validation_start", True)
        io_validation = validator.validate_io_operations(trace, validation_level)
        trace.io_validation = io_validation
        trace.add_step("io_validation_complete", True, metadata={
            'has_real_io': io_validation.has_real_io,
            'total_operations': io_validation.total_operations,
            'errors_detected': io_validation.errors_detected
        })
        
        # Шаг 6: Финальная валидация
        trace.add_step("final_validation_start", True)
        validation_errors = validator.validate_trace(trace, validation_level)
        
        if validation_errors:
            trace.add_step("final_validation_failed", False, 
                          error="; ".join(validation_errors),
                          metadata={'validation_errors': validation_errors})
            trace.finish(ExecutionStatus.INVALID, response, "Validation failed")
        else:
            trace.add_step("final_validation_complete", True)
            trace.finish(ExecutionStatus.SUCCESS, response)
        
        # Шаг 7: Запись в truth-based metrics engine
        try:
            metrics_engine = get_truth_metrics_engine()
            response_success = response.success if response else False
            
            # Завершаем core trace и используем его для метрик
            core_trace.end_execution(response_success, "completed" if response_success else "failed")
            
            await metrics_engine.record_pipeline_run(
                pipeline_name=pipeline.name,
                execution_trace=core_trace,
                response_success=response_success,
                validation_level=validation_level.value,
                timeout=timeout
            )
            trace.add_step("metrics_recorded", True)
        except Exception as e:
            trace.add_step("metrics_recording_failed", False, error=str(e))
        
        return response, trace
        
    except asyncio.TimeoutError:
        trace.add_step("pipeline_execution_timeout", False, error=f"Timeout after {timeout}s")
        trace.finish(ExecutionStatus.TIMEOUT, None, f"Execution timeout: {timeout}s")
        raise
        
    except Exception as e:
        trace.add_step("pipeline_execution_failed", False, error=str(e))
        trace.finish(ExecutionStatus.FAILED, None, str(e))
        raise

class TruthWrapperRegistry:
    """Реестр обернутых пайплайнов"""
    
    def __init__(self):
        self._wrapped_pipelines: Dict[str, BasePipeline] = {}
        self._execution_history: List[PipelineExecutionTrace] = []
        self._lock = threading.Lock()
    
    def register_pipeline(self, pipeline: BasePipeline):
        """Зарегистрировать пайплайн в реестре"""
        with self._lock:
            self._wrapped_pipelines[pipeline.name] = pipeline
    
    def get_pipeline(self, name: str) -> Optional[BasePipeline]:
        """Получить пайплайн по имени"""
        with self._lock:
            return self._wrapped_pipelines.get(name)
    
    def add_execution_trace(self, trace: PipelineExecutionTrace):
        """Добавить трассировку в историю"""
        with self._lock:
            self._execution_history.append(trace)
            # Ограничиваем историю
            if len(self._execution_history) > 1000:
                self._execution_history = self._execution_history[-1000:]
    
    def get_execution_history(self, pipeline_name: Optional[str] = None, 
                            count: int = 100) -> List[PipelineExecutionTrace]:
        """Получить историю выполнений"""
        with self._lock:
            history = self._execution_history
            
            if pipeline_name:
                history = [t for t in history if t.pipeline_name == pipeline_name]
            
            return history[-count:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по реестру"""
        with self._lock:
            total_executions = len(self._execution_history)
            successful_executions = sum(1 for t in self._execution_history if t.status == ExecutionStatus.SUCCESS)
            failed_executions = sum(1 for t in self._execution_history if t.status == ExecutionStatus.FAILED)
            
            pipeline_stats = {}
            for trace in self._execution_history:
                name = trace.pipeline_name
                if name not in pipeline_stats:
                    pipeline_stats[name] = {'total': 0, 'success': 0, 'failed': 0}
                
                pipeline_stats[name]['total'] += 1
                if trace.status == ExecutionStatus.SUCCESS:
                    pipeline_stats[name]['success'] += 1
                elif trace.status == ExecutionStatus.FAILED:
                    pipeline_stats[name]['failed'] += 1
            
            return {
                'total_pipelines': len(self._wrapped_pipelines),
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': successful_executions / max(1, total_executions),
                'pipeline_statistics': pipeline_stats
            }

# Глобальный реестр
_truth_registry = TruthWrapperRegistry()

def get_truth_registry() -> TruthWrapperRegistry:
    """Получить глобальный реестр обернутых пайплайнов"""
    return _truth_registry

def wrap_pipeline(pipeline: BasePipeline, 
                 validation_level: ValidationLevel = ValidationLevel.STRICT) -> BasePipeline:
    """Создать обертку для пайплайна"""
    
    class WrappedPipeline(BasePipeline):
        """Обернутый пайплайн с трассировкой"""
        
        def __init__(self, original: BasePipeline):
            # Копируем все атрибуты из оригинального пайплайна
            super().__init__(
                name=original.name + "_wrapped",
                technique=original.technique,
                priority=original.priority,
                execution_status=original.execution_status
            )
            
            self.original_pipeline = original
            self.validation_level = validation_level
            
            # Копируем конфигурацию
            self.config = original.config.copy()
            self._initialized = original._initialized
            
            # Регистрируем в реестре
            get_truth_registry().register_pipeline(self)
        
        async def execute(self, request: BypassRequest) -> BypassResponse:
            """Выполнение с трассировкой"""
            response, trace = await execute_with_truth(
                self.original_pipeline, 
                request, 
                self.validation_level
            )
            
            # Добавляем трассировку в историю
            get_truth_registry().add_execution_trace(trace)
            
            return response
        
        def initialize(self, config: Dict[str, Any]) -> bool:
            """Инициализация обернутого пайплайна"""
            result = self.original_pipeline.initialize(config)
            self._initialized = result
            return result
        
        def cleanup(self) -> bool:
            """Очистка ресурсов"""
            return self.original_pipeline.cleanup()
        
        def get_last_trace(self) -> Optional[PipelineExecutionTrace]:
            """Получить последнюю трассировку"""
            history = get_truth_registry().get_execution_history(self.name, 1)
            return history[0] if history else None
    
    return WrappedPipeline(pipeline)
