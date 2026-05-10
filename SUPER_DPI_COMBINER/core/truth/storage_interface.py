#!/usr/bin/env python3
"""
Truth Storage Interface - интеграция с pipeline wrapper
Автоматическое сохранение результатов выполнения
"""

import time
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

from core.truth.storage import get_truth_storage, create_execution_result, ExecutionResult, TruthStorage
from core.truth.instrumentation import get_io_monitor
from core.truth.pipeline_wrapper import ExecutionTrace, ExecutionStatus, IOValidationResult

class TruthStorageInterface:
    """Интерфейс для интеграции хранилища с pipeline wrapper"""
    
    def __init__(self, db_path: str = "truth_storage.db"):
        self.storage = get_truth_storage(db_path)
        self.io_monitor = get_io_monitor()
        self.logger = logging.getLogger("truth_storage_interface")
    
    def create_execution_from_trace(self, trace: ExecutionTrace) -> Optional[ExecutionResult]:
        """Создать результат выполнения из трассировки"""
        try:
            # Определяем статус выполнения
            success = trace.status == ExecutionStatus.SUCCESS
            
            # Проверяем верификацию сети
            network_verified = self._check_network_verification(trace)
            
            # Определяем флаг симуляции
            simulation_flag = self._check_simulation_flag(trace)
            
            # Собираем метаданные
            metadata = self._collect_metadata(trace)
            
            # Получаем статистику I/O
            io_stats = self.io_monitor.get_statistics()
            io_operations_count = io_stats.get('total_operations', 0)
            
            # Создаем результат выполнения
            result = create_execution_result(
                execution_id=trace.trace_id,
                pipeline=trace.pipeline_name,
                success=success,
                network_verified=network_verified,
                simulation_flag=simulation_flag,
                metadata=metadata,
                io_operations_count=io_operations_count,
                execution_duration=trace.total_duration or 0.0,
                error_message=trace.error
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create execution from trace: {e}")
            return None
    
    def store_trace(self, trace: ExecutionTrace) -> bool:
        """Сохранить трассировку выполнения"""
        try:
            result = self.create_execution_from_trace(trace)
            if result:
                return self.storage.store_execution(result)
            return False
        except Exception as e:
            self.logger.error(f"Failed to store trace: {e}")
            return False
    
    def _check_network_verification(self, trace: ExecutionTrace) -> bool:
        """Проверить верификацию сети"""
        if trace.io_validation:
            return trace.io_validation.has_real_io
        return False
    
    def _check_simulation_flag(self, trace: ExecutionTrace) -> bool:
        """Определить флаг симуляции"""
        # Проверяем метаданные на наличие флага симуляции
        if 'simulation_mode' in trace.metadata:
            return trace.metadata['simulation_mode']
        
        # Проверяем наличие реальных I/O операций
        if trace.io_validation:
            return not trace.io_validation.has_real_io
        
        # Проверяем статистику I/O монитора
        io_stats = self.io_monitor.get_statistics()
        return not io_stats.get('io_operations_in_session', False)
    
    def _collect_metadata(self, trace: ExecutionTrace) -> Dict[str, Any]:
        """Собрать метаданные из трассировки"""
        metadata = {
            'pipeline_type': trace.pipeline_type,
            'thread_id': trace.thread_id,
            'start_time': trace.start_time,
            'end_time': trace.end_time,
            'steps_count': len(trace.steps),
            'status': trace.status.value
        }
        
        # Добавляем информацию о запросе
        if trace.request:
            metadata['request_info'] = {
                'host': getattr(trace.request, 'host', None),
                'port': getattr(trace.request, 'port', None),
                'method': getattr(trace.request, 'method', None),
                'headers_count': len(getattr(trace.request, 'headers', {}))
            }
        
        # Добавляем информацию о ответе
        if trace.response:
            metadata['response_info'] = {
                'status_code': getattr(trace.response, 'status_code', None),
                'response_size': len(getattr(trace.response, 'data', b'')),
                'headers_count': len(getattr(trace.response, 'headers', {}))
            }
        
        # Добавляем I/O валидацию
        if trace.io_validation:
            metadata['io_validation'] = {
                'has_real_io': trace.io_validation.has_real_io,
                'total_operations': trace.io_validation.total_operations,
                'operation_types': trace.io_validation.operation_types,
                'bytes_transferred': trace.io_validation.bytes_transferred,
                'errors_detected': trace.io_validation.errors_detected
            }
        
        # Добавляем информацию о шагах
        if trace.steps:
            step_metadata = []
            for step in trace.steps:
                step_metadata.append({
                    'name': step.name,
                    'success': step.success,
                    'duration': step.duration,
                    'error': step.error
                })
            metadata['steps'] = step_metadata
        
        # Объединяем с существующими метаданными
        metadata.update(trace.metadata)
        
        return metadata
    
    def get_pipeline_statistics(self, pipeline: str) -> Dict[str, Any]:
        """Получить статистику по конкретному pipeline"""
        try:
            executions = self.storage.get_executions_by_pipeline(pipeline, limit=1000)
            
            if not executions:
                return {
                    'pipeline': pipeline,
                    'total_executions': 0,
                    'success_rate': 0,
                    'network_verification_rate': 0,
                    'simulation_rate': 0,
                    'avg_duration': 0,
                    'avg_io_operations': 0
                }
            
            total_executions = len(executions)
            successful_executions = sum(1 for e in executions if e.success)
            network_verified_executions = sum(1 for e in executions if e.network_verified)
            simulation_executions = sum(1 for e in executions if e.simulation_flag)
            
            total_duration = sum(e.execution_duration for e in executions)
            total_io_operations = sum(e.io_operations_count for e in executions)
            
            return {
                'pipeline': pipeline,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'success_rate': successful_executions / total_executions,
                'network_verified_executions': network_verified_executions,
                'network_verification_rate': network_verified_executions / total_executions,
                'simulation_executions': simulation_executions,
                'simulation_rate': simulation_executions / total_executions,
                'avg_duration': total_duration / total_executions,
                'avg_io_operations': total_io_operations / total_executions
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get pipeline statistics: {e}")
            return {}
    
    def get_execution_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Получить сводную информацию о выполнении"""
        try:
            execution = self.storage.get_execution(execution_id)
            if not execution:
                return None
            
            return {
                'execution_id': execution.execution_id,
                'pipeline': execution.pipeline,
                'success': execution.success,
                'network_verified': execution.network_verified,
                'simulation_flag': execution.simulation_flag,
                'timestamp': execution.timestamp,
                'duration': execution.execution_duration,
                'io_operations': execution.io_operations_count,
                'error': execution.error_message,
                'metadata': execution.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get execution summary: {e}")
            return None
    
    def export_pipeline_data(self, pipeline: str, output_path: str) -> bool:
        """Экспортировать данные конкретного pipeline"""
        try:
            return self.storage.export_to_jsonl(output_path, pipeline)
        except Exception as e:
            self.logger.error(f"Failed to export pipeline data: {e}")
            return False
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Очистка старых данных"""
        try:
            return self.storage.cleanup_old_executions(days_old)
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0

# Декоратор для автоматического сохранения результатов
def auto_store_execution(db_path: str = "truth_storage.db"):
    """Декоратор для автоматического сохранения результатов выполнения"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Инициализируем хранилище
            storage = TruthStorage(db_path)
            interface = TruthStorageInterface(db_path)
            
            # Создаем базовую трассировку
            execution_id = str(uuid.uuid4())
            pipeline_name = func.__name__
            
            try:
                # Выполняем функцию
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Создаем результат выполнения
                execution_result = create_execution_result(
                    execution_id=execution_id,
                    pipeline=pipeline_name,
                    success=True,
                    network_verified=interface.io_monitor.verify_real_io(),
                    simulation_flag=not interface.io_monitor.verify_real_io(),
                    metadata={'args_count': len(args), 'kwargs_keys': list(kwargs.keys())},
                    io_operations_count=interface.io_monitor.get_statistics().get('total_operations', 0),
                    execution_duration=duration
                )
                
                # Сохраняем результат
                storage.store_execution(execution_result)
                
                return result
                
            except Exception as e:
                # Сохраняем ошибку
                execution_result = create_execution_result(
                    execution_id=execution_id,
                    pipeline=pipeline_name,
                    success=False,
                    network_verified=False,
                    simulation_flag=True,
                    metadata={'args_count': len(args), 'kwargs_keys': list(kwargs.keys())},
                    io_operations_count=interface.io_monitor.get_statistics().get('total_operations', 0),
                    execution_duration=time.time() - start_time,
                    error_message=str(e)
                )
                
                storage.store_execution(execution_result)
                raise
        
        return wrapper
    return decorator

# Глобальный экземпляр интерфейса
_storage_interface = None

def get_storage_interface(db_path: str = "truth_storage.db") -> TruthStorageInterface:
    """Получить экземпляр интерфейса хранилища"""
    global _storage_interface
    if _storage_interface is None:
        _storage_interface = TruthStorageInterface(db_path)
    return _storage_interface
