#!/usr/bin/env python3
"""
Тестирование Pipeline Truth Wrapper
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

class TestPipeline(BasePipeline):
    """Тестовый пайплайн для демонстрации"""
    
    def __init__(self, name: str, should_fail: bool = False):
        super().__init__(name, BypassTechnique.SPOOF_DPI)
        self.should_fail = should_fail
        self._initialized = True
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение пайплайна с реальными I/O операциями"""
        import socket
        
        try:
            # Создаем реальный socket для I/O операций
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.should_fail:
                raise RuntimeError("Simulated pipeline failure")
            
            # Подключаемся к реальному хосту
            sock.connect(("www.google.com", 80))
            
            # Отправляем данные
            http_request = f"GET / HTTP/1.1\r\nHost: {request.host}\r\n\r\n"
            bytes_sent = sock.send(http_request.encode())
            
            # Получаем ответ
            response_data = sock.recv(1024)
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

class MockPipeline(BasePipeline):
        """Мок пайплайн без реальных I/O операций"""
        
        def __init__(self, name: str):
            super().__init__(name, BypassTechnique.DOMAIN_FRONTING)
            self._initialized = True
        
        async def execute(self, request: BypassRequest) -> BypassResponse:
            """Мок выполнение без I/O"""
            return BypassResponse(
                success=True,
                latency=0.001,
                status_code=200,
                data=b"Mock response",
                technique_used=self.technique.value
            )
        
        def initialize(self, config):
            return True
        
        def cleanup(self):
            return True

async def test_execute_with_truth():
    """Тестирование функции execute_with_truth"""
    print("=== Testing execute_with_truth ===")
    
    # Включаем инструментирование
    enable_instrumentation()
    
    # Создаем тестовый пайплайн
    pipeline = TestPipeline("test_pipeline")
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
        
        print(f"✓ Execution completed successfully")
        print(f"  Response success: {response.success}")
        print(f"  Response latency: {response.latency}s")
        print(f"  Trace status: {trace.status.value}")
        print(f"  Total duration: {trace.total_duration:.3f}s")
        print(f"  Steps count: {len(trace.steps)}")
        
        # Проверяем I/O валидацию
        if trace.io_validation:
            print(f"  Real I/O detected: {trace.io_validation.has_real_io}")
            print(f"  Total I/O operations: {trace.io_validation.total_operations}")
            print(f"  Bytes transferred: {sum(trace.io_validation.bytes_transferred.values())}")
        
        # Показываем шаги
        print("\n  Execution steps:")
        for i, step in enumerate(trace.steps, 1):
            status = "✓" if step.success else "✗"
            print(f"    {i}. {status} {step.name} ({step.duration:.3f}s)")
        
    except Exception as e:
        print(f"✗ Execution failed: {e}")

async def test_pipeline_wrapper():
    """Тестирование обертки пайплайна"""
    print("\n=== Testing Pipeline Wrapper ===")
    
    # Создаем и оборачиваем пайплайн
    original_pipeline = TestPipeline("wrapped_test")
    original_pipeline.initialize({})
    
    wrapped_pipeline = wrap_pipeline(original_pipeline, ValidationLevel.STRICT)
    
    # Создаем запрос
    request = BypassRequest(
        host="www.google.com",
        port=80,
        method="GET"
    )
    
    try:
        # Выполняем через обертку
        response = await wrapped_pipeline.execute(request)
        
        print(f"✓ Wrapped pipeline execution completed")
        print(f"  Response success: {response.success}")
        
        # Получаем последнюю трассировку
        last_trace = wrapped_pipeline.get_last_trace()
        if last_trace:
            print(f"  Last trace status: {last_trace.status.value}")
            print(f"  Real I/O in last trace: {last_trace.io_validation.has_real_io if last_trace.io_validation else False}")
        
    except Exception as e:
        print(f"✗ Wrapped pipeline execution failed: {e}")

async def test_validation_levels():
    """Тестирование уровней валидации"""
    print("\n=== Testing Validation Levels ===")
    
    pipeline = TestPipeline("validation_test")
    pipeline.initialize({})
    
    request = BypassRequest(
        host="www.google.com",
        port=80,
        method="GET"
    )
    
    validation_levels = [
        ValidationLevel.BASIC,
        ValidationLevel.STRICT,
        ValidationLevel.COMPREHENSIVE
    ]
    
    for level in validation_levels:
        try:
            response, trace = await execute_with_truth(
                pipeline, 
                request, 
                validation_level=level
            )
            
            print(f"✓ {level.value} validation: {trace.status.value}")
            if trace.io_validation:
                print(f"  Validation errors: {len(trace.io_validation.validation_errors)}")
            
        except Exception as e:
            print(f"✗ {level.value} validation failed: {e}")

async def test_registry():
    """Тестирование реестра обернутых пайплайнов"""
    print("\n=== Testing Registry ===")
    
    registry = get_truth_registry()
    
    # Создаем несколько пайплайнов
    pipelines = [
        TestPipeline("registry_test_1"),
        TestPipeline("registry_test_2"),
        MockPipeline("mock_test")
    ]
    
    for pipeline in pipelines:
        pipeline.initialize({})
        wrapped = wrap_pipeline(pipeline)
        
        # Выполняем для создания истории
        request = BypassRequest(host="www.google.com", port=80, method="GET")
        try:
            await wrapped.execute(request)
        except:
            pass  # Игнорируем ошибки для мок пайплайна
    
    # Получаем статистику
    stats = registry.get_statistics()
    print(f"✓ Registry statistics:")
    print(f"  Total pipelines: {stats['total_pipelines']}")
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    
    # Получаем историю
    history = registry.get_execution_history(count=5)
    print(f"  Recent executions: {len(history)}")
    
    for i, trace in enumerate(history[-3:], 1):
        print(f"    {i}. {trace.pipeline_name}: {trace.status.value}")

async def test_error_handling():
    """Тестирование обработки ошибок"""
    print("\n=== Testing Error Handling ===")
    
    # Тест с failing пайплайном
    failing_pipeline = TestPipeline("failing_test", should_fail=True)
    failing_pipeline.initialize({})
    
    request = BypassRequest(
        host="www.google.com",
        port=80,
        method="GET"
    )
    
    try:
        response, trace = await execute_with_truth(
            failing_pipeline, 
            request, 
            validation_level=ValidationLevel.STRICT
        )
        
        print(f"✓ Error handling test completed")
        print(f"  Response success: {response.success}")
        print(f"  Trace status: {trace.status.value}")
        print(f"  Error: {trace.error}")
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")

async def main():
    """Основная функция тестирования"""
    print("Pipeline Truth Wrapper Test Suite")
    print("=" * 50)
    
    await test_execute_with_truth()
    await test_pipeline_wrapper()
    await test_validation_levels()
    await test_registry()
    await test_error_handling()
    
    print("\n=== Test Suite Complete ===")
    
    # Финальная статистика
    monitor = get_io_monitor()
    final_stats = monitor.get_statistics()
    
    print(f"\nFinal I/O Statistics:")
    print(f"  Total operations: {final_stats['total_operations']}")
    print(f"  Real I/O in session: {final_stats['io_operations_in_session']}")

if __name__ == "__main__":
    asyncio.run(main())
