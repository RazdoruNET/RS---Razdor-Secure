#!/usr/bin/env python3
"""
Test Simulation Detector - TASK 8.4
Тестирование детектора симуляций
"""

import asyncio
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.simulation_detector import SimulationDetector, get_simulation_detector
from core.execution_trace import ExecutionTrace
from core.truth.instrumentation import IOMonitor, get_io_monitor

def test_no_socket_calls_detection():
    """Тест детектора отсутствия socket calls"""
    print("🧪 Testing no socket calls detection...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution без socket операций
    trace.start_execution()
    trace.add_error("TEST_ERROR", "Some error without network operations")
    trace.end_execution(success=True, final_status="completed")
    
    result = detector._detect_no_socket_calls(trace)
    
    assert result.simulation_detected == True, "Should detect simulation when no socket calls"
    assert result.reason == "no network syscall observed", "Reason should match"
    assert result.confidence > 0.9, "Confidence should be high"
    
    print("✅ No socket calls detection test passed")
    return result.to_dict()

def test_no_io_operations_detection():
    """Тест детектора отсутствия I/O операций"""
    print("🧪 Testing no I/O operations detection...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution без I/O операций
    trace.start_execution()
    trace.end_execution(success=True, final_status="completed")
    
    result = detector._detect_no_io_operations(trace)
    
    assert result.simulation_detected == True, "Should detect simulation when no I/O operations"
    assert result.reason == "no I/O operations performed", "Reason should match"
    
    print("✅ No I/O operations detection test passed")
    return result.to_dict()

def test_sleep_only_pipeline_detection():
    """Тест детектора sleep-only pipelines"""
    print("🧪 Testing sleep-only pipeline detection...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution с только sleep (duration > 0.1, но нет network events)
    trace.start_execution()
    time.sleep(0.2)  # Simulate sleep
    trace.end_execution(success=True, final_status="completed")
    
    result = detector._detect_sleep_only_pipeline(trace)
    
    assert result.simulation_detected == True, "Should detect simulation for sleep-only pipeline"
    assert result.reason == "sleep-only pipeline detected", "Reason should match"
    
    print("✅ Sleep-only pipeline detection test passed")
    return result.to_dict()

def test_try_except_no_side_effects_detection():
    """Тест детектора try/except без side effects"""
    print("🧪 Testing try/except without side effects detection...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution с ошибками но без сетевых операций
    trace.start_execution()
    trace.add_error("VALUE_ERROR", "Some non-network error")
    trace.add_error("TYPE_ERROR", "Another non-network error")
    trace.end_execution(success=False, final_status="failed")
    
    result = detector._detect_try_except_no_side_effects(trace)
    
    assert result.simulation_detected == True, "Should detect simulation for try/except without side effects"
    assert result.reason == "try/except without side effects", "Reason should match"
    
    print("✅ Try/except without side effects detection test passed")
    return result.to_dict()

def test_success_without_network_detection():
    """Тест детектора success без сетевых операций"""
    print("🧪 Testing success without network detection...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution с успехом но без сетевых операций
    trace.start_execution()
    trace.end_execution(success=True, final_status="completed")
    
    result = detector._detect_success_without_network(trace, response_success=True)
    
    assert result.simulation_detected == True, "Should detect simulation for success without network"
    assert result.reason == "success returned without network operations", "Reason should match"
    
    print("✅ Success without network detection test passed")
    return result.to_dict()

def test_real_pipeline_not_detected():
    """Тест что реальный пайплайн не детектируется как симуляция"""
    print("🧪 Testing real pipeline not detected as simulation...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution с реальными сетевыми операциями
    trace.start_execution()
    trace.add_connection_attempt("example.com", 443, "TCP")
    trace.add_connection_success("example.com", 443)
    trace.add_network_send("example.com", 443, 1024)
    trace.add_network_receive("example.com", 443, 2048)
    trace.end_execution(success=True, final_status="completed")
    
    result = detector.analyze_pipeline_execution(
        execution_trace=trace,
        response_success=True,
        pipeline_name="test_pipeline"
    )
    
    assert result.simulation_detected == False, "Real pipeline should not be detected as simulation"
    
    print("✅ Real pipeline not detected test passed")
    return result.to_dict()

def test_aggregation():
    """Тест агрегации результатов детекторов"""
    print("🧪 Testing result aggregation...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем execution без операций
    trace.start_execution()
    trace.end_execution(success=True, final_status="completed")
    
    result = detector.analyze_pipeline_execution(
        execution_trace=trace,
        response_success=True,
        pipeline_name="test_pipeline"
    )
    
    assert result.simulation_detected == True, "Should detect simulation"
    assert result.reason is not None, "Should have a reason"
    assert result.confidence > 0, "Should have confidence"
    assert "pipeline_name" in result.details, "Should include pipeline name in details"
    
    print("✅ Result aggregation test passed")
    return result.to_dict()

def test_statistics():
    """Тест статистики детектора"""
    print("🧪 Testing detector statistics...")
    
    detector = SimulationDetector()
    trace = ExecutionTrace("test_pipeline")
    
    # Запускаем несколько детекций
    for i in range(5):
        trace.start_execution()
        trace.end_execution(success=True, final_status="completed")
        detector.analyze_pipeline_execution(
            execution_trace=trace,
            response_success=True,
            pipeline_name=f"test_pipeline_{i}"
        )
    
    stats = detector.get_statistics()
    
    assert stats["total_detections"] == 5, "Should have 5 total detections"
    assert stats["simulations_detected"] == 5, "Should have detected 5 simulations"
    assert stats["simulation_rate"] == 1.0, "Should have 100% simulation rate"
    assert "reason_distribution" in stats, "Should have reason distribution"
    
    print("✅ Detector statistics test passed")
    return stats

async def test_integration_with_base_pipeline():
    """Тест интеграции с BasePipeline"""
    print("🧪 Testing integration with BasePipeline...")
    
    try:
        from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse, BypassTechnique
        
        # Создаем тестовый пайплайн
        class TestPipeline(BasePipeline):
            async def execute(self, request: BypassRequest) -> BypassResponse:
                # Симуляция - возвращаем успех без реальных операций
                return BypassResponse(
                    success=True,
                    latency=0.1,
                    technique_used="test"
                )
            
            def initialize(self, config):
                self._mark_initialized(True)
                return True
        
        pipeline = TestPipeline("test_pipeline", BypassTechnique.SPOOF_DPI)
        pipeline.initialize({})
        
        # Выполняем запрос
        request = BypassRequest(
            host="example.com",
            port=443,
            method="GET"
        )
        
        response = await pipeline.safe_execute(request)
        
        # Проверяем что детекция симуляции сработала
        assert response.simulation_detected == True, "Should detect simulation in mock pipeline"
        assert response.simulation_reason is not None, "Should have simulation reason"
        
        print("✅ Integration with BasePipeline test passed")
        return {"simulation_detected": response.simulation_detected, "reason": response.simulation_reason}
        
    except ImportError as e:
        print(f"⚠️ Skipping integration test due to import error: {e}")
        return {"skipped": True, "reason": str(e)}

def main():
    """Главная функция тестирования"""
    print("=" * 60)
    print("🧪 TASK 8.4 - Simulation Detector Tests")
    print("=" * 60)
    
    results = []
    
    try:
        # Запускаем все тесты
        results.append(("No socket calls", test_no_socket_calls_detection()))
        results.append(("No I/O operations", test_no_io_operations_detection()))
        results.append(("Sleep-only pipeline", test_sleep_only_pipeline_detection()))
        results.append(("Try/except no side effects", test_try_except_no_side_effects_detection()))
        results.append(("Success without network", test_success_without_network_detection()))
        results.append(("Real pipeline not detected", test_real_pipeline_not_detected()))
        results.append(("Result aggregation", test_aggregation()))
        results.append(("Statistics", test_statistics()))
        
        # Асинхронный тест интеграции
        integration_result = asyncio.run(test_integration_with_base_pipeline())
        results.append(("Integration with BasePipeline", integration_result))
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        for test_name, result in results:
            if isinstance(result, dict) and result.get("skipped"):
                print(f"⚠️ {test_name}: SKIPPED")
            else:
                print(f"✅ {test_name}: PASSED")
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("=" * 60)
        
        # Вывод примера результата детекции
        print("\n📋 Example detection result:")
        print(results[0][1])
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
