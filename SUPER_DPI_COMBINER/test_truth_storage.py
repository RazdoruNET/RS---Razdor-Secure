#!/usr/bin/env python3
"""
Test Truth Storage Layer - comprehensive testing
"""

import os
import sys
import time
import tempfile
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth.storage import TruthStorage, create_execution_result, get_truth_storage
from core.truth.storage_interface import TruthStorageInterface, get_storage_interface, auto_store_execution
from core.truth.instrumentation import enable_instrumentation, get_io_monitor

def test_storage_basic_operations():
    """Тест базовых операций хранилища"""
    print("=== Testing Storage Basic Operations ===")
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        storage = TruthStorage(db_path)
        
        # Создаем тестовый результат
        result = create_execution_result(
            execution_id="test_001",
            pipeline="test_pipeline",
            success=True,
            network_verified=True,
            simulation_flag=False,
            metadata={"test": True, "version": "1.0"},
            io_operations_count=5,
            execution_duration=2.5
        )
        
        # Тест сохранения
        assert storage.store_execution(result), "Failed to store execution"
        print("✓ Execution stored successfully")
        
        # Тест получения
        retrieved = storage.get_execution("test_001")
        assert retrieved is not None, "Failed to retrieve execution"
        assert retrieved.execution_id == "test_001", "Execution ID mismatch"
        assert retrieved.success == True, "Success flag mismatch"
        assert retrieved.network_verified == True, "Network verification mismatch"
        assert retrieved.simulation_flag == False, "Simulation flag mismatch"
        print("✓ Execution retrieved successfully")
        
        # Тест получения по pipeline
        pipeline_executions = storage.get_executions_by_pipeline("test_pipeline")
        assert len(pipeline_executions) == 1, "Pipeline execution count mismatch"
        print("✓ Pipeline executions retrieved successfully")
        
        # Тест статистики
        stats = storage.get_statistics()
        assert stats['total_executions'] == 1, "Total executions count mismatch"
        assert stats['successful_executions'] == 1, "Successful executions count mismatch"
        assert stats['success_rate'] == 1.0, "Success rate mismatch"
        print("✓ Statistics calculated successfully")
        
    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("✓ Basic operations test passed\n")

def test_storage_interface_integration():
    """Тест интеграции с интерфейсом"""
    print("=== Testing Storage Interface Integration ===")
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        interface = TruthStorageInterface(db_path)
        
        # Создаем тестовую трассировку
        from core.truth.pipeline_wrapper import ExecutionTrace, ExecutionStatus, IOValidationResult
        from core.base_pipeline import BypassRequest, BypassResponse
        
        request = BypassRequest(
            host="example.com",
            port=80,
            method="GET",
            headers={"User-Agent": "test"}
        )
        
        response = BypassResponse(
            success=True,
            status_code=200,
            headers={"Content-Type": "text/html"},
            data=b"<html>Test</html>"
        )
        
        io_validation = IOValidationResult(
            has_real_io=True,
            total_operations=3,
            operation_types={"socket_send": 1, "socket_recv": 2},
            bytes_transferred={"socket_send": 100, "socket_recv": 500},
            errors_detected=0
        )
        
        trace = ExecutionTrace(
            trace_id="trace_001",
            pipeline_name="test_pipeline",
            pipeline_type="http_bypass",
            request=request,
            response=response,
            status=ExecutionStatus.SUCCESS,
            io_validation=io_validation,
            metadata={"test_mode": True}
        )
        
        trace.end_time = time.time()
        trace.total_duration = 1.5
        
        # Тест сохранения трассировки
        assert interface.store_trace(trace), "Failed to store trace"
        print("✓ Trace stored successfully")
        
        # Тест получения сводной информации
        summary = interface.get_execution_summary("trace_001")
        assert summary is not None, "Failed to get execution summary"
        assert summary['pipeline'] == "test_pipeline", "Pipeline name mismatch"
        assert summary['success'] == True, "Success flag mismatch"
        assert summary['network_verified'] == True, "Network verification mismatch"
        assert summary['simulation_flag'] == False, "Simulation flag mismatch"
        print("✓ Execution summary retrieved successfully")
        
        # Тест статистики pipeline
        pipeline_stats = interface.get_pipeline_statistics("test_pipeline")
        assert pipeline_stats['total_executions'] == 1, "Pipeline executions count mismatch"
        assert pipeline_stats['success_rate'] == 1.0, "Pipeline success rate mismatch"
        print("✓ Pipeline statistics calculated successfully")
        
    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("✓ Interface integration test passed\n")

def test_storage_query_functionality():
    """Тест функциональности запросов"""
    print("=== Testing Storage Query Functionality ===")
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        storage = TruthStorage(db_path)
        
        # Создаем несколько тестовых результатов
        test_results = [
            create_execution_result(
                execution_id="test_001",
                pipeline="pipeline_a",
                success=True,
                network_verified=True,
                simulation_flag=False,
                io_operations_count=5,
                execution_duration=1.0
            ),
            create_execution_result(
                execution_id="test_002",
                pipeline="pipeline_a",
                success=False,
                network_verified=False,
                simulation_flag=True,
                io_operations_count=0,
                execution_duration=0.5,
                error_message="Connection failed"
            ),
            create_execution_result(
                execution_id="test_003",
                pipeline="pipeline_b",
                success=True,
                network_verified=True,
                simulation_flag=False,
                io_operations_count=10,
                execution_duration=2.0
            ),
            create_execution_result(
                execution_id="test_004",
                pipeline="pipeline_b",
                success=True,
                network_verified=False,
                simulation_flag=True,
                io_operations_count=0,
                execution_duration=0.1
            )
        ]
        
        # Сохраняем все результаты
        for result in test_results:
            storage.store_execution(result)
        
        print(f"✓ Stored {len(test_results)} test executions")
        
        # Тест успешных выполнений
        successful = storage.get_successful_executions()
        assert len(successful) == 3, "Successful executions count mismatch"
        print("✓ Successful executions retrieved successfully")
        
        # Тест выполнений с верифицированной сетью
        network_verified = storage.get_network_verified_executions()
        assert len(network_verified) == 2, "Network verified executions count mismatch"
        print("✓ Network verified executions retrieved successfully")
        
        # Тест выполнений в режиме симуляции
        simulation = storage.get_simulation_executions()
        assert len(simulation) == 2, "Simulation executions count mismatch"
        print("✓ Simulation executions retrieved successfully")
        
        # Тест последних выполнений
        recent = storage.get_recent_executions(limit=2)
        assert len(recent) == 2, "Recent executions count mismatch"
        print("✓ Recent executions retrieved successfully")
        
    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("✓ Query functionality test passed\n")

def test_storage_export_functionality():
    """Тест функциональности экспорта"""
    print("=== Testing Storage Export Functionality ===")
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    # Создаем временный файл для экспорта
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as tmp_export:
        export_path = tmp_export.name
    
    try:
        storage = TruthStorage(db_path)
        
        # Создаем тестовые результаты
        test_results = [
            create_execution_result(
                execution_id="export_001",
                pipeline="export_pipeline",
                success=True,
                network_verified=True,
                simulation_flag=False,
                metadata={"export_test": True}
            ),
            create_execution_result(
                execution_id="export_002",
                pipeline="export_pipeline",
                success=False,
                network_verified=False,
                simulation_flag=True,
                error_message="Export test error"
            )
        ]
        
        # Сохраняем результаты
        for result in test_results:
            storage.store_execution(result)
        
        # Экспортируем в JSONL
        assert storage.export_to_jsonl(export_path, "export_pipeline"), "Failed to export to JSONL"
        print("✓ Data exported to JSONL successfully")
        
        # Проверяем содержимое файла
        with open(export_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 2, "Export file line count mismatch"
            
            # Парсим все строки
            parsed_lines = [json.loads(line) for line in lines]
            
            # Проверяем, что оба execution_id присутствуют
            execution_ids = [line['execution_id'] for line in parsed_lines]
            assert "export_001" in execution_ids, "export_001 not found in export"
            assert "export_002" in execution_ids, "export_002 not found in export"
            
            # Проверяем, что все строки относятся к правильному pipeline
            for line in parsed_lines:
                assert line['pipeline'] == "export_pipeline", f"Wrong pipeline in export: {line['pipeline']}"
            
            # Проверяем, что есть один успешный и один неуспешный результат
            success_count = sum(1 for line in parsed_lines if line['success'] == True)
            failure_count = sum(1 for line in parsed_lines if line['success'] == False)
            assert success_count == 1, f"Expected 1 success, got {success_count}"
            assert failure_count == 1, f"Expected 1 failure, got {failure_count}"
        
        print("✓ Export file content verified successfully")
        
    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(export_path):
            os.unlink(export_path)
    
    print("✓ Export functionality test passed\n")

def test_auto_store_decorator():
    """Тест декоратора автоматического сохранения"""
    print("=== Testing Auto Store Decorator ===")
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Включаем инструментирование
        enable_instrumentation()
        
        @auto_store_execution(db_path)
        def test_function(x, y):
            """Тестовая функция с декоратором"""
            # Симулируем некоторые операции
            time.sleep(0.1)
            return x + y
        
        # Выполняем функцию
        result = test_function(2, 3)
        assert result == 5, "Function result mismatch"
        print("✓ Decorated function executed successfully")
        
        # Проверяем, что результат был сохранен
        storage = TruthStorage(db_path)
        executions = storage.get_recent_executions(limit=1)
        assert len(executions) == 1, "No execution stored by decorator"
        
        execution = executions[0]
        assert execution.pipeline == "test_function", "Pipeline name mismatch"
        assert execution.success == True, "Success flag mismatch"
        assert execution.execution_duration > 0, "Duration not recorded"
        print("✓ Execution auto-stored successfully")
        
    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("✓ Auto store decorator test passed\n")

def test_storage_cleanup_functionality():
    """Тест функциональности очистки"""
    print("=== Testing Storage Cleanup Functionality ===")
    
    # Создаем временную базу данных
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        storage = TruthStorage(db_path)
        
        # Создаем тестовый результат с старой меткой времени
        old_timestamp = time.time() - (35 * 24 * 60 * 60)  # 35 дней назад
        
        old_result = create_execution_result(
            execution_id="old_execution",
            pipeline="test_pipeline",
            success=True,
            network_verified=True,
            simulation_flag=False
        )
        old_result.timestamp = old_timestamp
        
        # Создаем свежий результат
        new_result = create_execution_result(
            execution_id="new_execution",
            pipeline="test_pipeline",
            success=True,
            network_verified=True,
            simulation_flag=False
        )
        
        # Сохраняем оба результата
        storage.store_execution(old_result)
        storage.store_execution(new_result)
        
        # Проверяем, что оба результата сохранены
        all_executions = storage.get_recent_executions(limit=100)
        assert len(all_executions) == 2, "Both executions should be stored initially"
        print("✓ Both old and new executions stored")
        
        # Выполняем очистку (удаляем старше 30 дней)
        deleted_count = storage.cleanup_old_executions(days_old=30)
        assert deleted_count == 1, "Should delete exactly 1 old execution"
        print(f"✓ Cleaned up {deleted_count} old executions")
        
        # Проверяем, что остался только новый результат
        remaining_executions = storage.get_recent_executions(limit=100)
        assert len(remaining_executions) == 1, "Should have 1 remaining execution"
        assert remaining_executions[0].execution_id == "new_execution", "Wrong execution remaining"
        print("✓ Only new execution remains after cleanup")
        
    finally:
        # Очистка
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("✓ Cleanup functionality test passed\n")

def run_all_tests():
    """Запустить все тесты"""
    print("🧪 Starting Truth Storage Layer Tests\n")
    
    try:
        test_storage_basic_operations()
        test_storage_interface_integration()
        test_storage_query_functionality()
        test_storage_export_functionality()
        test_auto_store_decorator()
        test_storage_cleanup_functionality()
        
        print("🎉 All tests passed successfully!")
        print("\n📋 Test Summary:")
        print("✓ Basic storage operations")
        print("✓ Interface integration")
        print("✓ Query functionality")
        print("✓ Export functionality")
        print("✓ Auto-store decorator")
        print("✓ Cleanup functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
