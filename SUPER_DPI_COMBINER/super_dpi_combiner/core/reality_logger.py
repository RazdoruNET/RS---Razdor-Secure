#!/usr/bin/env python3
"""
Reality Logger - ТЗ-5 REALITY LOGGER
Контроль выполнения системы с различением:
- что работает
- что симуляция  
- что падает

Логирует:
- import success/fail
- init success/fail
- execute success/fail

Генерирует runtime_reality_report.json
Запрещает silent failures
"""

import time
import json
import threading
import traceback
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque

class OperationType(Enum):
    """Типы операций для трекинга"""
    IMPORT = "import"
    INIT = "init"
    EXECUTE = "execute"
    CLEANUP = "cleanup"

class OperationStatus(Enum):
    """Статусы операций"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SIMULATION = "simulation"

class RealityLevel(Enum):
    """Уровни реальности выполнения"""
    REAL = "REAL"          # Реальные сетевые операции
    PARTIAL = "PARTIAL"    # Частично реальные операции
    SIMULATION = "SIMULATION"  # Только симуляция
    FAILED = "FAILED"      # Полностью не работает

@dataclass
class OperationEvent:
    """Событие операции"""
    timestamp: float
    operation_type: OperationType
    component_name: str
    status: OperationStatus
    reality_level: RealityLevel
    duration: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'operation_type': self.operation_type.value,
            'component_name': self.component_name,
            'status': self.status.value,
            'reality_level': self.reality_level.value,
            'duration': self.duration,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'metadata': self.metadata
        }

@dataclass
class ComponentReality:
    """Информация о реальности компонента"""
    name: str
    import_status: OperationStatus = OperationStatus.FAILURE
    init_status: OperationStatus = OperationStatus.FAILURE
    execute_status: OperationStatus = OperationStatus.FAILURE
    reality_level: RealityLevel = RealityLevel.FAILED
    last_activity: float = field(default_factory=time.time)
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    simulation_operations: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Успешность операций"""
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations
    
    def update_reality_level(self):
        """Обновление уровня реальности на основе статусов"""
        if self.import_status == OperationStatus.FAILURE:
            self.reality_level = RealityLevel.FAILED
        elif self.init_status == OperationStatus.FAILURE:
            self.reality_level = RealityLevel.FAILED
        elif self.execute_status == OperationStatus.FAILURE:
            self.reality_level = RealityLevel.FAILED
        elif all(status == OperationStatus.SUCCESS for status in [self.import_status, self.init_status, self.execute_status]):
            self.reality_level = RealityLevel.REAL
        elif any(status == OperationStatus.SIMULATION for status in [self.import_status, self.init_status, self.execute_status]):
            self.reality_level = RealityLevel.SIMULATION
        else:
            self.reality_level = RealityLevel.PARTIAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'import_status': self.import_status.value,
            'init_status': self.init_status.value,
            'execute_status': self.execute_status.value,
            'reality_level': self.reality_level.value,
            'last_activity': self.last_activity,
            'total_operations': self.total_operations,
            'successful_operations': self.successful_operations,
            'failed_operations': self.failed_operations,
            'simulation_operations': self.simulation_operations,
            'success_rate': self.success_rate,
            'errors': self.errors[-10:]  # Последние 10 ошибок
        }

class RealityLogger:
    """
    Reality Logger - основной класс для трекинга реальности выполнения
    
    Особенности:
    - Логирует все import/init/execute операции
    - Определяет уровень реальности компонентов
    - Генерирует runtime_reality_report.json
    - Запрещает silent failures
    """
    
    def __init__(self, report_file: str = "runtime_reality_report.json"):
        self.report_file = Path(report_file)
        self.components: Dict[str, ComponentReality] = {}
        self.events: deque = deque(maxlen=10000)  # Последние 10000 событий
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Статистика
        self._total_imports = 0
        self._successful_imports = 0
        self._total_inits = 0
        self._successful_inits = 0
        self._total_executions = 0
        self._successful_executions = 0
        self._silent_failures_detected = 0
        
        # Флаг для автоматического сохранения
        self._auto_save_enabled = True
        self._save_interval = 30.0  # секунд
        self._last_save_time = time.time()
        
        # Запускаем фоновое сохранение
        self._start_auto_save()
    
    def log_import(self, component_name: str, success: bool, error: Optional[str] = None, 
                  is_simulation: bool = False, metadata: Dict[str, Any] = None):
        """Логирование операции импорта"""
        with self.lock:
            self._total_imports += 1
            if success:
                self._successful_imports += 1
            
            # Создаем или получаем компонент
            if component_name not in self.components:
                self.components[component_name] = ComponentReality(name=component_name)
            
            component = self.components[component_name]
            component.import_status = OperationStatus.SUCCESS if success else OperationStatus.FAILURE
            component.last_activity = time.time()
            component.total_operations += 1
            
            if success:
                component.successful_operations += 1
                status = OperationStatus.SUCCESS
                reality = RealityLevel.REAL if not is_simulation else RealityLevel.SIMULATION
            else:
                component.failed_operations += 1
                status = OperationStatus.FAILURE
                reality = RealityLevel.FAILED
                if error:
                    component.errors.append(f"IMPORT: {error}")
            
            # Обновляем уровень реальности
            component.update_reality_level()
            
            # Создаем событие
            event = OperationEvent(
                timestamp=time.time(),
                operation_type=OperationType.IMPORT,
                component_name=component_name,
                status=status,
                reality_level=reality,
                error_message=error,
                stack_trace=traceback.format_exc() if error else None,
                metadata=metadata or {}
            )
            
            self.events.append(event)
            
            # Проверяем на silent failure
            if not success and not error:
                self._detect_silent_failure(component_name, "import", event)
            
            # Автосохранение
            if self._should_auto_save():
                self._save_report_async()
    
    def log_init(self, component_name: str, success: bool, error: Optional[str] = None,
                 is_simulation: bool = False, duration: float = 0.0, metadata: Dict[str, Any] = None):
        """Логирование операции инициализации"""
        with self.lock:
            self._total_inits += 1
            if success:
                self._successful_inits += 1
            
            # Создаем или получаем компонент
            if component_name not in self.components:
                self.components[component_name] = ComponentReality(name=component_name)
            
            component = self.components[component_name]
            component.init_status = OperationStatus.SUCCESS if success else OperationStatus.FAILURE
            component.last_activity = time.time()
            component.total_operations += 1
            
            if success:
                component.successful_operations += 1
                status = OperationStatus.SUCCESS
                reality = RealityLevel.REAL if not is_simulation else RealityLevel.SIMULATION
            else:
                component.failed_operations += 1
                status = OperationStatus.FAILURE
                reality = RealityLevel.FAILED
                if error:
                    component.errors.append(f"INIT: {error}")
            
            # Обновляем уровень реальности
            component.update_reality_level()
            
            # Создаем событие
            event = OperationEvent(
                timestamp=time.time(),
                operation_type=OperationType.INIT,
                component_name=component_name,
                status=status,
                reality_level=reality,
                duration=duration,
                error_message=error,
                stack_trace=traceback.format_exc() if error else None,
                metadata=metadata or {}
            )
            
            self.events.append(event)
            
            # Проверяем на silent failure
            if not success and not error:
                self._detect_silent_failure(component_name, "init", event)
            
            # Автосохранение
            if self._should_auto_save():
                self._save_report_async()
    
    def log_execute(self, component_name: str, success: bool, error: Optional[str] = None,
                    is_simulation: bool = False, duration: float = 0.0, metadata: Dict[str, Any] = None):
        """Логирование операции выполнения"""
        with self.lock:
            self._total_executions += 1
            if success:
                self._successful_executions += 1
            
            # Создаем или получаем компонент
            if component_name not in self.components:
                self.components[component_name] = ComponentReality(name=component_name)
            
            component = self.components[component_name]
            component.execute_status = OperationStatus.SUCCESS if success else OperationStatus.FAILURE
            component.last_activity = time.time()
            component.total_operations += 1
            
            if success:
                component.successful_operations += 1
                status = OperationStatus.SUCCESS
                reality = RealityLevel.REAL if not is_simulation else RealityLevel.SIMULATION
            else:
                component.failed_operations += 1
                status = OperationStatus.FAILURE
                reality = RealityLevel.FAILED
                if error:
                    component.errors.append(f"EXECUTE: {error}")
            
            # Обновляем уровень реальности
            component.update_reality_level()
            
            # Создаем событие
            event = OperationEvent(
                timestamp=time.time(),
                operation_type=OperationType.EXECUTE,
                component_name=component_name,
                status=status,
                reality_level=reality,
                duration=duration,
                error_message=error,
                stack_trace=traceback.format_exc() if error else None,
                metadata=metadata or {}
            )
            
            self.events.append(event)
            
            # Проверяем на silent failure
            if not success and not error:
                self._detect_silent_failure(component_name, "execute", event)
            
            # Автосохранение
            if self._should_auto_save():
                self._save_report_async()
    
    def _detect_silent_failure(self, component_name: str, operation: str, event: OperationEvent):
        """Детектирование и логирование silent failures"""
        self._silent_failures_detected += 1
        
        # Добавляем информацию о silent failure в событие
        event.metadata['silent_failure'] = True
        event.metadata['silent_failure_operation'] = operation
        
        # Логируем как критическое событие
        print(f"🚨 SILENT FAILURE DETECTED: {component_name}.{operation} at {event.timestamp}")
        print(f"   Stack trace: {event.stack_trace}")
        
        # Добавляем ошибку в компонент
        if component_name in self.components:
            self.components[component_name].errors.append(
                f"SILENT_FAILURE in {operation}: No error message provided"
            )
    
    def _should_auto_save(self) -> bool:
        """Проверка необходимости автосохранения"""
        if not self._auto_save_enabled:
            return False
        
        current_time = time.time()
        if current_time - self._last_save_time >= self._save_interval:
            self._last_save_time = current_time
            return True
        return False
    
    def _save_report_async(self):
        """Асинхронное сохранение отчета"""
        try:
            # В реальной реализации здесь можно использовать asyncio.create_task
            # Но для простоты сохраняем синхронно
            self.save_report()
        except Exception as e:
            print(f"Failed to auto-save reality report: {e}")
    
    def _start_auto_save(self):
        """Запуск фонового автосохранения"""
        def auto_save_worker():
            while self._auto_save_enabled:
                time.sleep(self._save_interval)
                if self._auto_save_enabled:
                    try:
                        self.save_report()
                    except Exception as e:
                        print(f"Auto-save failed: {e}")
        
        thread = threading.Thread(target=auto_save_worker, daemon=True)
        thread.start()
    
    def get_reality_summary(self) -> Dict[str, Any]:
        """Получение сводки реальности системы"""
        with self.lock:
            # Считаем компоненты по уровням реальности
            reality_counts = defaultdict(int)
            for component in self.components.values():
                reality_counts[component.reality_level.value] += 1
            
            # Статистика операций
            import_success_rate = (self._successful_imports / self._total_imports) if self._total_imports > 0 else 0
            init_success_rate = (self._successful_inits / self._total_inits) if self._total_inits > 0 else 0
            execute_success_rate = (self._successful_executions / self._total_executions) if self._total_executions > 0 else 0
            
            return {
                'timestamp': time.time(),
                'uptime': time.time() - self.start_time,
                'total_components': len(self.components),
                'reality_distribution': dict(reality_counts),
                'operation_statistics': {
                    'imports': {
                        'total': self._total_imports,
                        'successful': self._successful_imports,
                        'success_rate': import_success_rate
                    },
                    'inits': {
                        'total': self._total_inits,
                        'successful': self._successful_inits,
                        'success_rate': init_success_rate
                    },
                    'executions': {
                        'total': self._total_executions,
                        'successful': self._successful_executions,
                        'success_rate': execute_success_rate
                    }
                },
                'silent_failures_detected': self._silent_failures_detected,
                'total_events': len(self.events)
            }
    
    def get_component_details(self) -> Dict[str, Any]:
        """Получение детальной информации о компонентах"""
        with self.lock:
            return {
                'components': {name: component.to_dict() for name, component in self.components.items()},
                'component_count': len(self.components)
            }
    
    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """Получение последних событий"""
        with self.lock:
            recent_events = list(self.events)[-count:]
            return [event.to_dict() for event in recent_events]
    
    def get_failed_components(self) -> List[str]:
        """Получение списка неработающих компонентов"""
        with self.lock:
            return [
                name for name, component in self.components.items()
                if component.reality_level == RealityLevel.FAILED
            ]
    
    def get_simulation_components(self) -> List[str]:
        """Получение списка компонентов в режиме симуляции"""
        with self.lock:
            return [
                name for name, component in self.components.items()
                if component.reality_level == RealityLevel.SIMULATION
            ]
    
    def get_real_components(self) -> List[str]:
        """Получение списка реально работающих компонентов"""
        with self.lock:
            return [
                name for name, component in self.components.items()
                if component.reality_level == RealityLevel.REAL
            ]
    
    def save_report(self) -> str:
        """
        Сохранение runtime_reality_report.json
        
        Returns:
            str: Путь к сохраненному файлу
        """
        with self.lock:
            report = {
                'metadata': {
                    'generated_at': time.time(),
                    'generator': 'RealityLogger ТЗ-5',
                    'version': '1.0.0',
                    'uptime': time.time() - self.start_time
                },
                'reality_summary': self.get_reality_summary(),
                'component_details': self.get_component_details(),
                'recent_events': self.get_recent_events(50),
                'failed_components': self.get_failed_components(),
                'simulation_components': self.get_simulation_components(),
                'real_components': self.get_real_components(),
                'system_health': {
                    'overall_health': len(self.get_real_components()) / len(self.components) if self.components else 0,
                    'critical_issues': len(self.get_failed_components()),
                    'simulation_warnings': len(self.get_simulation_components())
                }
            }
            
            # Сохраняем в файл
            self.report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            return str(self.report_file)
    
    def cleanup(self):
        """Очистка ресурсов"""
        self._auto_save_enabled = False
        # Финальное сохранение
        self.save_report()

# Глобальный экземпляр
_global_reality_logger: Optional[RealityLogger] = None

def get_reality_logger(report_file: str = "runtime_reality_report.json") -> RealityLogger:
    """Получение глобального экземпляра RealityLogger"""
    global _global_reality_logger
    if _global_reality_logger is None:
        _global_reality_logger = RealityLogger(report_file)
    return _global_reality_logger

def cleanup_reality_logger():
    """Очистка глобального экземпляра"""
    global _global_reality_logger
    if _global_reality_logger:
        _global_reality_logger.cleanup()
        _global_reality_logger = None
