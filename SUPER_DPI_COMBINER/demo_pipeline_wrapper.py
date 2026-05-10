#!/usr/bin/env python3
"""
Демонстрация Pipeline Truth Wrapper
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth import enable_instrumentation, get_io_monitor
from core.truth.pipeline_wrapper import (
    execute_with_truth, 
    wrap_pipeline, 
    get_truth_registry,
    ValidationLevel,
    ExecutionStatus
)
from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse, BypassTechnique

class DemoPipeline(BasePipeline):
    """Демо пайплайн с реальными I/O операциями"""
    
    def __init__(self, name: str):
        super().__init__(name, BypassTechnique.SPOOF_DPI)
        self._initialized = True
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальными сетевыми операциями"""
        import socket
        import time
        
        try:
            # Реальное сетевое подключение
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            # Подключение к реальному хосту
            sock.connect((request.host, request.port))
            
            # Отправка HTTP запроса
            http_request = f"GET / HTTP/1.1\r\nHost: {request.host}\r\nConnection: close\r\n\r\n"
            bytes_sent = sock.send(http_request.encode())
            
            # Получение ответа
            response_data = b""
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response_data += chunk
            
            sock.close()
            
            return BypassResponse(
                success=True,
                latency=0.1,
                status_code=200,
                data=response_data,
                technique_used=self.technique.value
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                latency=0.05,
                error_reason=str(e),
                technique_used=self.technique.value
            )
    
    def initialize(self, config):
        return True
    
    def cleanup(self):
        return True

async def demo_basic_execution():
    """Демонстрация базового выполнения с трассировкой"""
    print("=== Basic Execution with Truth ===")
    
    # Включаем инструментирование
    enable_instrumentation()
    
    # Создаем пайплайн
    pipeline = DemoPipeline("demo_basic")
    pipeline.initialize({})
    
    # Создаем запрос
    request = BypassRequest(
        host="www.google.com",
        port=80,
        method="GET"
    )
    
    try:
        # Выполняем с трассировкой
        response, trace = await execute_with_truth(
            pipeline, 
            request, 
            validation_level=ValidationLevel.STRICT
        )
        
        print(f"✓ Execution completed")
        print(f"  Pipeline: {trace.pipeline_name}")
        print(f"  Status: {trace.status.value}")
        print(f"  Duration: {trace.total_duration:.3f}s")
        print(f"  Steps: {len(trace.steps)}")
        
        # I/O валидация
        if trace.io_validation:
            print(f"  Real I/O: {trace.io_validation.has_real_io}")
            print(f"  I/O Operations: {trace.io_validation.total_operations}")
            print(f"  Bytes transferred: {sum(trace.io_validation.bytes_transferred.values())}")
        
        # Показываем ключевые шаги
        print("\n  Key steps:")
        for step in trace.steps:
            status = "✓" if step.success else "✗"
            print(f"    {status} {step.name}")
        
    except Exception as e:
        print(f"✗ Execution failed: {e}")

async def demo_wrapped_pipeline():
    """Демонстрация обернутого пайплайна"""
    print("\n=== Wrapped Pipeline Demo ===")
    
    # Создаем и оборачиваем пайплайн
    original = DemoPipeline("demo_wrapped")
    original.initialize({})
    
    wrapped = wrap_pipeline(original, ValidationLevel.COMPREHENSIVE)
    
    request = BypassRequest(
        host="www.google.com",
        port=80,
        method="GET"
    )
    
    try:
        # Выполняем через обертку
        response = await wrapped.execute(request)
        
        print(f"✓ Wrapped pipeline executed")
        print(f"  Response success: {response.success}")
        
        # Получаем трассировку
        trace = wrapped.get_last_trace()
        if trace:
            print(f"  Trace ID: {trace.trace_id}")
            print(f"  Validation level: comprehensive")
            print(f"  Validation passed: {trace.status == ExecutionStatus.SUCCESS}")
            
    except Exception as e:
        print(f"✗ Wrapped pipeline failed: {e}")

async def demo_registry():
    """Демонстрация реестра пайплайнов"""
    print("\n=== Pipeline Registry Demo ===")
    
    registry = get_truth_registry()
    
    # Создаем несколько пайплайнов
    pipelines = []
    for i in range(3):
        pipeline = DemoPipeline(f"registry_demo_{i+1}")
        pipeline.initialize({})
        wrapped = wrap_pipeline(pipeline, ValidationLevel.STRICT)
        pipelines.append(wrapped)
    
    # Выполняем все пайплайны
    request = BypassRequest(host="www.google.com", port=80, method="GET")
    
    for i, wrapped in enumerate(pipelines, 1):
        try:
            await wrapped.execute(request)
            print(f"  ✓ Pipeline {i} executed")
        except Exception as e:
            print(f"  ✗ Pipeline {i} failed: {e}")
    
    # Показываем статистику реестра
    stats = registry.get_statistics()
    print(f"\n  Registry Statistics:")
    print(f"    Total pipelines: {stats['total_pipelines']}")
    print(f"    Total executions: {stats['total_executions']}")
    print(f"    Success rate: {stats['success_rate']:.1%}")
    
    # История выполнений
    history = registry.get_execution_history(count=5)
    print(f"    Recent executions: {len(history)}")

async def demo_validation_levels():
    """Демонстрация уровней валидации"""
    print("\n=== Validation Levels Demo ===")
    
    pipeline = DemoPipeline("validation_demo")
    pipeline.initialize({})
    
    request = BypassRequest(host="www.google.com", port=80, method="GET")
    
    levels = [
        (ValidationLevel.BASIC, "Basic"),
        (ValidationLevel.STRICT, "Strict"),
        (ValidationLevel.COMPREHENSIVE, "Comprehensive")
    ]
    
    for level, name in levels:
        try:
            response, trace = await execute_with_truth(
                pipeline, request, validation_level=level
            )
            
            print(f"  {name} validation: {trace.status.value}")
            
            if trace.io_validation:
                errors = len(trace.io_validation.validation_errors)
                print(f"    Validation errors: {errors}")
                if errors > 0:
                    for error in trace.io_validation.validation_errors[:2]:
                        print(f"      - {error}")
            
        except Exception as e:
            print(f"  {name} validation: failed ({e})")

async def demo_error_handling():
    """Демонстрация обработки ошибок"""
    print("\n=== Error Handling Demo ===")
    
    # Создаем пайплайн с ошибкой
    class FailingPipeline(DemoPipeline):
        async def execute(self, request: BypassRequest) -> BypassResponse:
            raise RuntimeError("Simulated pipeline failure")
    
    pipeline = FailingPipeline("failing_demo")
    pipeline.initialize({})
    
    request = BypassRequest(host="www.google.com", port=80, method="GET")
    
    try:
        response, trace = await execute_with_truth(
            pipeline, request, validation_level=ValidationLevel.STRICT
        )
        
        print(f"✓ Error handling completed")
        print(f"  Status: {trace.status.value}")
        print(f"  Error: {trace.error}")
        
    except Exception as e:
        print(f"✗ Error handling failed: {e}")

async def main():
    """Основная демонстрация"""
    print("Pipeline Truth Wrapper Demonstration")
    print("=" * 50)
    
    await demo_basic_execution()
    await demo_wrapped_pipeline()
    await demo_registry()
    await demo_validation_levels()
    await demo_error_handling()
    
    print("\n=== Demo Complete ===")
    
    # Финальная статистика
    monitor = get_io_monitor()
    stats = monitor.get_statistics()
    
    print(f"\nFinal Statistics:")
    print(f"  Total I/O operations: {stats['total_operations']}")
    print(f"  Real I/O detected: {stats['io_operations_in_session']}")
    
    # Статистика реестра
    registry = get_truth_registry()
    registry_stats = registry.get_statistics()
    print(f"  Registered pipelines: {registry_stats['total_pipelines']}")
    print(f"  Registry executions: {registry_stats['total_executions']}")

if __name__ == "__main__":
    asyncio.run(main())
