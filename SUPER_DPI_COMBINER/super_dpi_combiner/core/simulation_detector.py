#!/usr/bin/env python3
"""
Simulation Detector - TASK 8.4
Автоматическое обнаружение симуляций и заглушек в пайплайнах

Детекторы:
- Отсутствие socket calls
- Return success без I/O
- Sleep-only pipelines
- Try/except без side effects
"""

import time
import sys
import os
import ast
import inspect
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.execution_trace import ExecutionTrace
from core.truth.instrumentation import IOMonitor, get_io_monitor, IOOperationType

class SimulationReason(Enum):
    """Причины обнаружения симуляции"""
    NO_SOCKET_CALLS = "no network syscall observed"
    NO_IO_OPERATIONS = "no I/O operations performed"
    SLEEP_ONLY_PIPELINE = "sleep-only pipeline detected"
    TRY_EXCEPT_NO_SIDE_EFFECTS = "try/except without side effects"
    SUCCESS_WITHOUT_NETWORK = "success returned without network operations"
    MOCK_RESPONSE_PATTERN = "mock response pattern detected"

@dataclass
class SimulationDetectionResult:
    """Результат детекции симуляции"""
    simulation_detected: bool
    reason: Optional[str] = None
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        result = {
            "simulation_detected": self.simulation_detected
        }
        if self.reason:
            result["reason"] = self.reason
        if self.confidence > 0:
            result["confidence"] = self.confidence
        if self.details:
            result["details"] = self.details
        return result

class SimulationDetector:
    """
    Детектор симуляций для пайплайнов
    
    Анализирует execution traces и I/O monitoring data для обнаружения
    заглушек и симуляций вместо реальных сетевых операций.
    """
    
    def __init__(self):
        self.io_monitor = get_io_monitor()
        self.lock = threading.Lock()
        self.detection_history: List[Dict[str, Any]] = []
        
    def analyze_pipeline_execution(
        self, 
        execution_trace: ExecutionTrace,
        response_success: bool,
        pipeline_name: str
    ) -> SimulationDetectionResult:
        """
        Анализ выполнения пайплайна на предмет симуляции
        
        Args:
            execution_trace: Trace выполнения пайплайна
            response_success: Успешность ответа
            pipeline_name: Имя пайплайна
            
        Returns:
            SimulationDetectionResult: Результат детекции
        """
        start_time = time.time()
        
        # Сбрасываем сессию I/O монитора перед анализом
        self.io_monitor.reset_session()
        
        # Выполняем все детекторы
        detection_results = []
        
        # 1. Детектор отсутствия socket calls
        socket_result = self._detect_no_socket_calls(execution_trace)
        detection_results.append(socket_result)
        
        # 2. Детектор отсутствия I/O операций
        io_result = self._detect_no_io_operations(execution_trace)
        detection_results.append(io_result)
        
        # 3. Детектор sleep-only pipelines
        sleep_result = self._detect_sleep_only_pipeline(execution_trace)
        detection_results.append(sleep_result)
        
        # 4. Детектор try/except без side effects
        try_except_result = self._detect_try_except_no_side_effects(execution_trace)
        detection_results.append(try_except_result)
        
        # 5. Детектор успеха без сетевых операций
        success_without_network = self._detect_success_without_network(
            execution_trace, response_success
        )
        detection_results.append(success_without_network)
        
        # Агрегируем результаты
        final_result = self._aggregate_detections(detection_results, pipeline_name)
        
        # Сохраняем в историю
        with self.lock:
            self.detection_history.append({
                'pipeline_name': pipeline_name,
                'timestamp': time.time(),
                'result': final_result.to_dict(),
                'analysis_duration': time.time() - start_time,
                'individual_results': [r.to_dict() for r in detection_results]
            })
        
        return final_result
    
    def _detect_no_socket_calls(self, execution_trace: ExecutionTrace) -> SimulationDetectionResult:
        """
        Детектор 1: Отсутствие socket calls
        
        Проверяет отсутствие системных вызовов socket в execution trace
        """
        with self.lock:
            # Проверяем syscalls в I/O мониторе
            syscalls = list(self.io_monitor.syscall_records)
            
            socket_syscalls = [
                s for s in syscalls 
                if 'socket' in s.syscall_name.lower()
            ]
            
            # Проверяем network events в execution trace
            network_events = execution_trace.network_events
            
            has_socket_operations = len(socket_syscalls) > 0 or len(network_events) > 0
            
            if not has_socket_operations:
                return SimulationDetectionResult(
                    simulation_detected=True,
                    reason=SimulationReason.NO_SOCKET_CALLS.value,
                    confidence=0.95,
                    details={
                        'socket_syscalls_count': len(socket_syscalls),
                        'network_events_count': len(network_events),
                        'total_syscalls': len(syscalls)
                    }
                )
            
            return SimulationDetectionResult(
                simulation_detected=False,
                confidence=0.1,
                details={
                    'socket_syscalls_count': len(socket_syscalls),
                    'network_events_count': len(network_events)
                }
            )
    
    def _detect_no_io_operations(self, execution_trace: ExecutionTrace) -> SimulationDetectionResult:
        """
        Детектор 2: Отсутствие I/O операций
        
        Проверяет отсутствие любых I/O операций в execution trace
        """
        with self.lock:
            # Проверяем I/O операции в мониторе
            io_operations = list(self.io_monitor.records)
            
            # Проверяем network send/receive events
            network_send_events = [
                e for e in execution_trace.network_events
                if e.event_type.value in ['send_data', 'receive_data']
            ]
            
            has_io_operations = len(io_operations) > 0 or len(network_send_events) > 0
            
            if not has_io_operations:
                return SimulationDetectionResult(
                    simulation_detected=True,
                    reason=SimulationReason.NO_IO_OPERATIONS.value,
                    confidence=0.90,
                    details={
                        'io_operations_count': len(io_operations),
                        'network_send_events_count': len(network_send_events),
                        'io_operations_in_session': self.io_monitor.verify_real_io()
                    }
                )
            
            return SimulationDetectionResult(
                simulation_detected=False,
                confidence=0.1,
                details={
                    'io_operations_count': len(io_operations),
                    'network_send_events_count': len(network_send_events)
                }
            )
    
    def _detect_sleep_only_pipeline(self, execution_trace: ExecutionTrace) -> SimulationDetectionResult:
        """
        Детектор 3: Sleep-only pipelines
        
        Проверяет что пайплайн только выполняет sleep без реальных операций
        """
        duration = execution_trace.get_duration()
        
        # Проверяем наличие реальных операций
        has_real_operations = (
            len(execution_trace.network_events) > 0 or
            len([e for e in execution_trace.events if e.event_type.value in ['network_send', 'network_receive']]) > 0
        )
        
        # Если только sleep и нет реальных операций
        if duration > 0.1 and not has_real_operations:
            # Проверяем что это действительно только sleep (нет других событий кроме таймаутов)
            non_timeout_events = [
                e for e in execution_trace.events 
                if e.event_type.value != 'timeout'
            ]
            
            # Если только таймауты и нет сетевых операций
            if len(non_timeout_events) <= 2:  # pipeline_start и pipeline_end
                return SimulationDetectionResult(
                    simulation_detected=True,
                    reason=SimulationReason.SLEEP_ONLY_PIPELINE.value,
                    confidence=0.85,
                    details={
                        'duration': duration,
                        'network_events_count': len(execution_trace.network_events),
                        'non_timeout_events_count': len(non_timeout_events),
                        'timeout_events_count': len(execution_trace._timeout_events)
                    }
                )
        
        return SimulationDetectionResult(
            simulation_detected=False,
            confidence=0.1,
            details={
                'duration': duration,
                'has_real_operations': has_real_operations
            }
        )
    
    def _detect_try_except_no_side_effects(self, execution_trace: ExecutionTrace) -> SimulationDetectionResult:
        """
        Детектор 4: Try/except без side effects
        
        Анализирует паттерны try/except которые не выполняют реальных операций
        """
        # Проверяем на наличие ошибок без реальных операций
        error_count = len(execution_trace.errors)
        network_operations_count = len(execution_trace.network_events)
        
        # Если есть ошибки но нет сетевых операций - подозрительно
        if error_count > 0 and network_operations_count == 0:
            # Проверяем что ошибки не связаны с сетью
            network_related_errors = [
                e for e in execution_trace.errors
                if 'connection' in e.error_message.lower() or 
                   'socket' in e.error_message.lower() or
                   'network' in e.error_message.lower()
            ]
            
            # Если ошибки не сетевые и нет сетевых операций
            if len(network_related_errors) == 0:
                return SimulationDetectionResult(
                    simulation_detected=True,
                    reason=SimulationReason.TRY_EXCEPT_NO_SIDE_EFFECTS.value,
                    confidence=0.75,
                    details={
                        'error_count': error_count,
                        'network_operations_count': network_operations_count,
                        'network_related_errors': len(network_related_errors),
                        'error_types': [e.error_type for e in execution_trace.errors]
                    }
                )
        
        return SimulationDetectionResult(
            simulation_detected=False,
            confidence=0.1,
            details={
                'error_count': error_count,
                'network_operations_count': network_operations_count
            }
        )
    
    def _detect_success_without_network(
        self, 
        execution_trace: ExecutionTrace,
        response_success: bool
    ) -> SimulationDetectionResult:
        """
        Детектор 5: Success без сетевых операций
        
        Проверяет что пайплайн вернул успех без выполнения сетевых операций
        """
        if not response_success:
            return SimulationDetectionResult(
                simulation_detected=False,
                confidence=0.0,
                details={'response_success': False}
            )
        
        # Проверяем наличие успешных сетевых операций
        successful_connections = [
            e for e in execution_trace.network_events
            if e.event_type.value == 'connect_success'
        ]
        
        network_send_events = [
            e for e in execution_trace.network_events
            if e.event_type.value == 'send_data'
        ]
        
        has_network_operations = len(successful_connections) > 0 or len(network_send_events) > 0
        
        if response_success and not has_network_operations:
            return SimulationDetectionResult(
                simulation_detected=True,
                reason=SimulationReason.SUCCESS_WITHOUT_NETWORK.value,
                confidence=0.90,
                details={
                    'response_success': response_success,
                    'successful_connections': len(successful_connections),
                    'network_send_events': len(network_send_events),
                    'total_network_events': len(execution_trace.network_events)
                }
            )
        
        return SimulationDetectionResult(
            simulation_detected=False,
            confidence=0.1,
            details={
                'response_success': response_success,
                'has_network_operations': has_network_operations
            }
        )
    
    def _aggregate_detections(
        self,
        detection_results: List[SimulationDetectionResult],
        pipeline_name: str
    ) -> SimulationDetectionResult:
        """
        Агрегация результатов от всех детекторов
        
        Args:
            detection_results: Результаты от отдельных детекторов
            pipeline_name: Имя пайплайна
            
        Returns:
            SimulationDetectionResult: Финальный результат
        """
        # Фильтруем только детектированные симуляции
        detected_simulations = [r for r in detection_results if r.simulation_detected]
        
        if not detected_simulations:
            return SimulationDetectionResult(
                simulation_detected=False,
                confidence=0.0,
                details={
                    'pipeline_name': pipeline_name,
                    'detectors_checked': len(detection_results),
                    'all_detectors_passed': True
                }
            )
        
        # Берем результат с наивысшей уверенностью
        highest_confidence = max(detected_simulations, key=lambda x: x.confidence)
        
        # Агрегируем детали от всех детекторов
        all_details = {
            'pipeline_name': pipeline_name,
            'total_detections': len(detected_simulations),
            'individual_detections': [r.details for r in detected_simulations]
        }
        
        # Добавляем детали от выбранного детектора
        all_details.update(highest_confidence.details)
        
        return SimulationDetectionResult(
            simulation_detected=True,
            reason=highest_confidence.reason,
            confidence=highest_confidence.confidence,
            details=all_details
        )
    
    def get_detection_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить историю детекций"""
        with self.lock:
            return self.detection_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику детекций"""
        with self.lock:
            total_detections = len(self.detection_history)
            simulations_detected = sum(
                1 for h in self.detection_history 
                if h['result'].get('simulation_detected', False)
            )
            
            reason_counts = {}
            for history in self.detection_history:
                if history['result'].get('simulation_detected', False):
                    reason = history['result'].get('reason', 'unknown')
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            return {
                'total_detections': total_detections,
                'simulations_detected': simulations_detected,
                'simulation_rate': (simulations_detected / total_detections) if total_detections > 0 else 0,
                'reason_distribution': reason_counts,
                'average_analysis_duration': sum(
                    h['analysis_duration'] for h in self.detection_history
                ) / total_detections if total_detections > 0 else 0
            }

# Глобальный экземпляр детектора
_simulation_detector = SimulationDetector()

def get_simulation_detector() -> SimulationDetector:
    """Получить экземпляр детектора симуляций"""
    return _simulation_detector
