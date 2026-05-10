#!/usr/bin/env python3
"""
Truth Storage Layer Demo - демонстрация возможностей хранения результатов выполнения
"""

import os
import sys
import time
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth.storage import TruthStorage, create_execution_result, get_truth_storage
from core.truth.storage_interface import TruthStorageInterface, get_storage_interface, auto_store_execution
from core.truth.instrumentation import enable_instrumentation, get_io_monitor
from core.truth.pipeline_wrapper import ExecutionTrace, ExecutionStatus, IOValidationResult
from core.base_pipeline import BypassRequest, BypassResponse

def demo_basic_storage_operations():
    """Демонстрация базовых операций хранения"""
    print("=== Truth Storage Layer Demo ===\n")
    
    # Создаем хранилище
    storage = TruthStorage("demo_truth_storage.db")
    
    print("1. Creating and storing execution results...")
    
    # Создаем несколько тестовых результатов
    test_results = [
        create_execution_result(
            execution_id="demo_001",
            pipeline="http_bypass",
            success=True,
            network_verified=True,
            simulation_flag=False,
            metadata={
                "target": "example.com",
                "technique": "domain_fronting",
                "response_time": 1.2
            },
            io_operations_count=8,
            execution_duration=2.5
        ),
        create_execution_result(
            execution_id="demo_002", 
            pipeline="tor_integration",
            success=True,
            network_verified=True,
            simulation_flag=False,
            metadata={
                "target": "darknet-site.onion",
                "technique": "tor_bridges",
                "circuit_length": 3
            },
            io_operations_count=15,
            execution_duration=8.7
        ),
        create_execution_result(
            execution_id="demo_003",
            pipeline="protocol_obfuscation",
            success=False,
            network_verified=False,
            simulation_flag=True,
            metadata={
                "target": "blocked-site.com",
                "technique": "tls_obfuscation",
                "error_type": "connection_timeout"
            },
            io_operations_count=0,
            execution_duration=0.5,
            error_message="Connection timeout after 30 seconds"
        )
    ]
    
    # Сохраняем результаты
    for result in test_results:
        storage.store_execution(result)
        print(f"   ✓ Stored {result.execution_id}: {result.pipeline} - {'SUCCESS' if result.success else 'FAILED'}")
    
    print(f"\n2. Retrieving execution results...")
    
    # Получаем конкретное выполнение
    retrieved = storage.get_execution("demo_001")
    if retrieved:
        print(f"   ✓ Retrieved {retrieved.execution_id}")
        print(f"     Pipeline: {retrieved.pipeline}")
        print(f"     Success: {retrieved.success}")
        print(f"     Network Verified: {retrieved.network_verified}")
        print(f"     Simulation Flag: {retrieved.simulation_flag}")
        print(f"     Duration: {retrieved.execution_duration}s")
        print(f"     I/O Operations: {retrieved.io_operations_count}")
    
    print(f"\n3. Query operations...")
    
    # Получаем успешные выполнения
    successful = storage.get_successful_executions()
    print(f"   ✓ Successful executions: {len(successful)}")
    
    # Получаем выполнения с верифицированной сетью
    network_verified = storage.get_network_verified_executions()
    print(f"   ✓ Network verified executions: {len(network_verified)}")
    
    # Получаем выполнения в режиме симуляции
    simulation = storage.get_simulation_executions()
    print(f"   ✓ Simulation executions: {len(simulation)}")
    
    print(f"\n4. Statistics...")
    
    # Получаем общую статистику
    stats = storage.get_statistics()
    print(f"   ✓ Total executions: {stats['total_executions']}")
    print(f"   ✓ Success rate: {stats['success_rate']:.2%}")
    print(f"   ✓ Network verification rate: {stats['network_verification_rate']:.2%}")
    print(f"   ✓ Simulation rate: {stats['simulation_rate']:.2%}")
    
    print(f"\n5. Pipeline statistics...")
    for pipeline_stat in stats['pipeline_statistics']:
        print(f"   ✓ {pipeline_stat['pipeline']}:")
        print(f"     Total: {pipeline_stat['total']}")
        print(f"     Success rate: {pipeline_stat['success_rate']:.2%}")
        print(f"     Avg duration: {pipeline_stat['avg_duration']:.2f}s")

def demo_interface_integration():
    """Демонстрация интеграции с pipeline wrapper"""
    print("\n=== Interface Integration Demo ===\n")
    
    interface = TruthStorageInterface("demo_truth_storage.db")
    
    print("1. Creating execution trace...")
    
    # Создаем тестовую трассировку
    request = BypassRequest(
        host="github.com",
        port=443,
        method="GET",
        headers={"User-Agent": "Truth-Demo/1.0"}
    )
    
    response = BypassResponse(
        success=True,
        status_code=200,
        headers={"Content-Type": "text/html"},
        data=b"<html><body>GitHub Page</body></html>",
        latency=1.5,
        network_verified=True,
        simulation_detected=False
    )
    
    io_validation = IOValidationResult(
        has_real_io=True,
        total_operations=12,
        operation_types={
            "socket_send": 4,
            "socket_recv": 6,
            "http_request": 1,
            "http_response": 1
        },
        bytes_transferred={
            "socket_send": 1024,
            "socket_recv": 8192
        },
        errors_detected=0
    )
    
    trace = ExecutionTrace(
        trace_id="trace_demo_001",
        pipeline_name="github_bypass",
        pipeline_type="https_obfuscation",
        request=request,
        response=response,
        status=ExecutionStatus.SUCCESS,
        io_validation=io_validation,
        metadata={
            "demo_mode": True,
            "technique_used": "tls_fragmentation",
            "bypass_level": "advanced"
        }
    )
    
    trace.end_time = time.time()
    trace.total_duration = 2.3
    
    # Сохраняем трассировку
    if interface.store_trace(trace):
        print("   ✓ Trace stored successfully")
    else:
        print("   ✗ Failed to store trace")
    
    print("\n2. Getting execution summary...")
    
    # Получаем сводную информацию
    summary = interface.get_execution_summary("trace_demo_001")
    if summary:
        print(f"   ✓ Execution ID: {summary['execution_id']}")
        print(f"   ✓ Pipeline: {summary['pipeline']}")
        print(f"   ✓ Success: {summary['success']}")
        print(f"   ✓ Network Verified: {summary['network_verified']}")
        print(f"   ✓ Simulation Flag: {summary['simulation_flag']}")
        print(f"   ✓ Duration: {summary['duration']:.2f}s")
        print(f"   ✓ I/O Operations: {summary['io_operations']}")
    
    print("\n3. Pipeline-specific statistics...")
    
    # Получаем статистику по pipeline
    pipeline_stats = interface.get_pipeline_statistics("github_bypass")
    if pipeline_stats:
        print(f"   ✓ Pipeline: {pipeline_stats['pipeline']}")
        print(f"   ✓ Total executions: {pipeline_stats['total_executions']}")
        print(f"   ✓ Success rate: {pipeline_stats['success_rate']:.2%}")
        print(f"   ✓ Network verification rate: {pipeline_stats['network_verification_rate']:.2%}")
        print(f"   ✓ Avg duration: {pipeline_stats['avg_duration']:.2f}s")

def demo_auto_store_decorator():
    """Демонстрация декоратора автоматического сохранения"""
    print("\n=== Auto Store Decorator Demo ===\n")
    
    # Включаем инструментирование
    enable_instrumentation()
    
    @auto_store_execution("demo_truth_storage.db")
    def demo_bypass_function(target_url: str, technique: str):
        """Демонстрационная функция обхода"""
        print(f"   Executing bypass for {target_url} using {technique}...")
        
        # Симулируем выполнение
        time.sleep(0.2)
        
        # Симулируем результат
        success = target_url.endswith(".com")  # Простая логика для демонстрации
        
        if success:
            print(f"   ✓ Bypass successful for {target_url}")
            return {"status": "success", "url": target_url}
        else:
            raise Exception(f"Bypass failed for {target_url}")
    
    print("1. Testing successful execution...")
    
    try:
        result = demo_bypass_function("https://example.com", "domain_fronting")
        print(f"   ✓ Function result: {result}")
    except Exception as e:
        print(f"   ✗ Function failed: {e}")
    
    print("\n2. Testing failed execution...")
    
    try:
        result = demo_bypass_function("https://blocked-site.xyz", "protocol_obfuscation")
        print(f"   ✓ Function result: {result}")
    except Exception as e:
        print(f"   ✓ Function failed as expected: {e}")
    
    print("\n3. Checking stored results...")
    
    storage = TruthStorage("demo_truth_storage.db")
    recent_executions = storage.get_recent_executions(limit=5)
    
    print(f"   ✓ Total recent executions: {len(recent_executions)}")
    for execution in recent_executions:
        if execution.pipeline == "demo_bypass_function":
            print(f"     - {execution.execution_id}: {'SUCCESS' if execution.success else 'FAILED'}")
            print(f"       Duration: {execution.execution_duration:.3f}s")
            print(f"       I/O Operations: {execution.io_operations_count}")
            if execution.error_message:
                print(f"       Error: {execution.error_message}")

def demo_export_functionality():
    """Демонстрация функциональности экспорта"""
    print("\n=== Export Functionality Demo ===\n")
    
    storage = TruthStorage("demo_truth_storage.db")
    
    print("1. Exporting all data to JSONL...")
    
    # Экспортируем все данные
    if storage.export_to_jsonl("demo_all_executions.jsonl"):
        print("   ✓ All executions exported to demo_all_executions.jsonl")
        
        # Показываем несколько строк из файла
        with open("demo_all_executions.jsonl", 'r') as f:
            lines = f.readlines()
            print(f"   ✓ Exported {len(lines)} executions")
            
            if lines:
                print("   ✓ Sample execution:")
                sample = json.loads(lines[0])
                print(f"     ID: {sample['execution_id']}")
                print(f"     Pipeline: {sample['pipeline']}")
                print(f"     Success: {sample['success']}")
                print(f"     Network Verified: {sample['network_verified']}")
    else:
        print("   ✗ Failed to export all executions")
    
    print("\n2. Exporting specific pipeline data...")
    
    # Экспортируем данные конкретного pipeline
    if storage.export_to_jsonl("demo_http_bypass.jsonl", "http_bypass"):
        print("   ✓ HTTP bypass executions exported to demo_http_bypass.jsonl")
        
        with open("demo_http_bypass.jsonl", 'r') as f:
            lines = f.readlines()
            print(f"   ✓ Exported {len(lines)} HTTP bypass executions")
    else:
        print("   ✗ Failed to export HTTP bypass executions")

def demo_cleanup_functionality():
    """Демонстрация функциональности очистки"""
    print("\n=== Cleanup Functionality Demo ===\n")
    
    storage = TruthStorage("demo_truth_storage.db")
    
    print("1. Current storage statistics...")
    
    stats = storage.get_statistics()
    print(f"   ✓ Total executions: {stats['total_executions']}")
    
    print("\n2. Creating old execution for cleanup test...")
    
    # Создаем старое выполнение (35 дней назад)
    old_result = create_execution_result(
        execution_id="old_demo_001",
        pipeline="cleanup_test",
        success=True,
        network_verified=True,
        simulation_flag=False
    )
    old_result.timestamp = time.time() - (35 * 24 * 60 * 60)  # 35 дней назад
    
    storage.store_execution(old_result)
    print("   ✓ Created old execution (35 days ago)")
    
    # Проверяем количество выполнений
    stats_after_old = storage.get_statistics()
    print(f"   ✓ Total executions after adding old one: {stats_after_old['total_executions']}")
    
    print("\n3. Running cleanup (remove older than 30 days)...")
    
    deleted_count = storage.cleanup_old_executions(days_old=30)
    print(f"   ✓ Cleaned up {deleted_count} old executions")
    
    # Проверяем количество выполнений после очистки
    stats_after_cleanup = storage.get_statistics()
    print(f"   ✓ Total executions after cleanup: {stats_after_cleanup['total_executions']}")

def cleanup_demo_files():
    """Очистка демо-файлов"""
    print("\n=== Cleanup Demo Files ===\n")
    
    demo_files = [
        "demo_truth_storage.db",
        "demo_all_executions.jsonl", 
        "demo_http_bypass.jsonl"
    ]
    
    for file_path in demo_files:
        if os.path.exists(file_path):
            os.unlink(file_path)
            print(f"   ✓ Removed {file_path}")
        else:
            print(f"   - {file_path} not found")

def main():
    """Главная функция демонстрации"""
    print("🧬 Truth Storage Layer - Complete Demo")
    print("=" * 50)
    
    try:
        # Запускаем все демонстрации
        demo_basic_storage_operations()
        demo_interface_integration()
        demo_auto_store_decorator()
        demo_export_functionality()
        demo_cleanup_functionality()
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("\n📋 Features demonstrated:")
        print("✓ SQLite-based storage with execution results")
        print("✓ Query functionality (success, network verified, simulation)")
        print("✓ Statistics and pipeline analytics")
        print("✓ Integration with pipeline wrapper traces")
        print("✓ Auto-store decorator for functions")
        print("✓ JSONL export functionality")
        print("✓ Cleanup of old data")
        print("✓ Thread-safe operations")
        
        # Спрашиваем об очистке
        print("\n🧹 Cleanup demo files? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response == 'y' or response == 'yes':
                cleanup_demo_files()
            else:
                print("   Demo files preserved for inspection")
        except (KeyboardInterrupt, EOFError):
            print("\n   Demo files preserved for inspection")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
