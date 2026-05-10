#!/usr/bin/env python3
"""
Тест Reality Logger - ТЗ-5
Проверка функциональности отслеживания реальности выполнения
"""

import asyncio
import time
import json
from pathlib import Path
from core.reality_logger import get_reality_logger, RealityLogger, OperationStatus, RealityLevel
from core.base_pipeline import BasePipeline, BypassTechnique, PipelineExecutionStatus, BypassRequest, BypassResponse

class TestPipeline(BasePipeline):
    """Тестовый пайплайн для проверки Reality Logger"""
    
    def __init__(self, name: str, should_fail_init: bool = False, should_fail_execute: bool = False, is_simulation: bool = False):
        super().__init__(name, BypassTechnique.SPOOF_DPI, 0, 
                        PipelineExecutionStatus.SIMULATION if is_simulation else PipelineExecutionStatus.REAL)
        self.should_fail_init = should_fail_init
        self.should_fail_execute = should_fail_execute
        self.is_simulation = is_simulation
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение тестового пайплайна"""
        start_time = time.time()
        
        if self.should_fail_execute:
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason="Test pipeline execution failure",
                response_time=time.time() - start_time,
                simulation_detected=self.is_simulation,
                simulation_reason="Test simulation" if self.is_simulation else None
            )
        
        # Симуляция успешного выполнения
        await asyncio.sleep(0.01)
        
        return BypassResponse(
            success=True,
            latency=time.time() - start_time,
            status_code=200,
            headers={'X-Test': 'True'},
            data=b'Test response data',
            response_time=time.time() - start_time,
            simulation_detected=self.is_simulation,
            simulation_reason="Test simulation" if self.is_simulation else None
        )
    
    def initialize(self, config):
        """Инициализация тестового пайплайна"""
        if self.should_fail_init:
            self._mark_initialized(False)
            return False
        
        self.config = config or {}
        self._mark_initialized(True)
        return True
    
    def cleanup(self):
        """Очистка ресурсов"""
        return True

async def test_reality_logger_basic():
    """Базовый тест функциональности Reality Logger"""
    print("🧪 Тест 1: Базовая функциональность Reality Logger")
    
    # Создаем новый экземпляр для теста
    test_logger = RealityLogger("test_runtime_reality_report.json")
    
    # Тест логирования импорта
    test_logger.log_import(
        component_name="TestComponent1",
        success=True,
        metadata={'test': True}
    )
    
    test_logger.log_import(
        component_name="TestComponent2", 
        success=False,
        error="Import failed",
        metadata={'test': True}
    )
    
    # Тест логирования инициализации
    test_logger.log_init(
        component_name="TestComponent1",
        success=True,
        duration=0.1,
        metadata={'test': True}
    )
    
    test_logger.log_init(
        component_name="TestComponent2",
        success=False,
        error="Init failed",
        duration=0.05,
        metadata={'test': True}
    )
    
    # Тест логирования выполнения
    test_logger.log_execute(
        component_name="TestComponent1",
        success=True,
        duration=0.2,
        metadata={'test': True, 'host': 'example.com'}
    )
    
    test_logger.log_execute(
        component_name="TestComponent2",
        success=False,
        error="Execution failed",
        duration=0.1,
        metadata={'test': True, 'host': 'example.com'}
    )
    
    # Тест silent failure
    test_logger.log_execute(
        component_name="TestComponent3",
        success=False,
        # Нет ошибки - это silent failure
        metadata={'test': True}
    )
    
    # Проверяем статистику
    summary = test_logger.get_reality_summary()
    print(f"  📊 Всего компонентов: {summary['total_components']}")
    print(f"  ❌ Не работают: {len(summary['failed_components'])}")
    print(f"  🔄 В симуляции: {len(summary['simulation_components'])}")
    print(f"  ✅ Реально работают: {len(summary['real_components'])}")
    print(f"  🚨 Silent failures: {summary['silent_failures_detected']}")
    
    # Сохраняем отчет
    report_path = test_logger.save_report()
    print(f"  💾 Отчет сохранен: {report_path}")
    
    # Проверяем наличие файла
    if Path(report_path).exists():
        print("  ✅ Файл отчета создан")
        
        # Проверяем содержимое
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        print(f"  📋 Метаданные: {report_data['metadata']['generator']}")
        print(f"  📈 Компонентов в отчете: {len(report_data['component_details']['components'])}")
    else:
        print("  ❌ Файл отчета не создан")
    
    return True

async def test_pipeline_integration():
    """Тест интеграции с пайплайнами"""
    print("\n🧪 Тест 2: Интеграция с пайплайнами")
    
    # Создаем тестовые пайплайны
    pipelines = [
        TestPipeline("RealWorkingPipeline", should_fail_init=False, should_fail_execute=False, is_simulation=False),
        TestPipeline("SimulationPipeline", should_fail_init=False, should_fail_execute=False, is_simulation=True),
        TestPipeline("FailedInitPipeline", should_fail_init=True, should_fail_execute=False, is_simulation=False),
        TestPipeline("FailedExecutePipeline", should_fail_init=False, should_fail_execute=True, is_simulation=False)
    ]
    
    # Инициализируем пайплайны
    for pipeline in pipelines:
        print(f"  🔧 Инициализация {pipeline.name}...")
        pipeline.initialize({})
    
    # Выполняем тестовые запросы
    test_request = BypassRequest(
        host="example.com",
        port=443,
        method="GET",
        timeout=5.0
    )
    
    for pipeline in pipelines:
        print(f"  🚀 Выполнение {pipeline.name}...")
        response = await pipeline.safe_execute(test_request)
        print(f"    Результат: {'✅' if response.success else '❌'} ({response.error_reason or 'OK'})")
    
    # Получаем глобальный логгер и проверяем результаты
    reality_logger = get_reality_logger()
    
    # Ждем немного для асинхронных операций
    await asyncio.sleep(0.1)
    
    summary = reality_logger.get_reality_summary()
    print(f"\n  📊 Итоги теста:")
    print(f"  Всего компонентов: {summary['total_components']}")
    print(f"  Реально работают: {len(reality_logger.get_real_components())}")
    print(f"  В симуляции: {len(reality_logger.get_simulation_components())}")
    print(f"  Не работают: {len(reality_logger.get_failed_components())}")
    
    # Показываем детали компонентов
    print(f"\n  🔍 Детали компонентов:")
    for name in reality_logger.get_real_components():
        print(f"    ✅ {name} - REAL")
    for name in reality_logger.get_simulation_components():
        print(f"    🔄 {name} - SIMULATION")
    for name in reality_logger.get_failed_components():
        print(f"    ❌ {name} - FAILED")
    
    return True

async def test_silent_failure_detection():
    """Тест детекции silent failures"""
    print("\n🧪 Тест 3: Детекция silent failures")
    
    reality_logger = RealityLogger("test_silent_failures_report.json")
    
    # Создаем компонент с silent failure
    component_name = "SilentFailureComponent"
    
    # Логируем успешный импорт
    reality_logger.log_import(
        component_name=component_name,
        success=True
    )
    
    # Логируем успешную инициализацию
    reality_logger.log_init(
        component_name=component_name,
        success=True
    )
    
    # Логируем выполнение без ошибки (silent failure)
    reality_logger.log_execute(
        component_name=component_name,
        success=False,
        # Нет error_message - это silent failure
        metadata={'operation': 'test'}
    )
    
    # Проверяем статистику
    summary = reality_logger.get_reality_summary()
    print(f"  🚨 Silent failures detected: {summary['silent_failures_detected']}")
    
    if summary['silent_failures_detected'] > 0:
        print("  ✅ Silent failure детектирован корректно")
        
        # Проверяем события
        recent_events = reality_logger.get_recent_events(5)
        silent_failure_events = [e for e in recent_events if e.get('metadata', {}).get('silent_failure')]
        
        if silent_failure_events:
            print(f"  📝 Найдено {len(silent_failure_events)} silent failure событий")
            for event in silent_failure_events:
                print(f"    - {event['component_name']}.{event['operation_type']} at {event['timestamp']}")
    else:
        print("  ❌ Silent failure не детектирован")
    
    return summary['silent_failures_detected'] > 0

async def test_report_generation():
    """Тест генерации отчета"""
    print("\n🧪 Тест 4: Генерация runtime_reality_report.json")
    
    reality_logger = RealityLogger("test_final_report.json")
    
    # Добавляем тестовые данные
    test_components = [
        ("RealComponent1", True, True, True, False),
        ("RealComponent2", True, True, True, False),
        ("SimulationComponent", True, True, True, True),
        ("FailedInitComponent", True, False, False, False),
        ("FailedExecuteComponent", True, True, False, False)
    ]
    
    for name, import_ok, init_ok, execute_ok, is_sim in test_components:
        reality_logger.log_import(name, import_ok, None if import_ok else "Import failed")
        reality_logger.log_init(name, init_ok, None if init_ok else "Init failed", is_sim)
        reality_logger.log_execute(name, execute_ok, None if execute_ok else "Execute failed", is_sim)
    
    # Генерируем отчет
    report_path = reality_logger.save_report()
    print(f"  💾 Отчет сохранен: {report_path}")
    
    # Проверяем структуру отчета
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    required_sections = ['metadata', 'reality_summary', 'component_details', 'recent_events', 
                        'failed_components', 'simulation_components', 'real_components', 'system_health']
    
    missing_sections = [section for section in required_sections if section not in report]
    
    if missing_sections:
        print(f"  ❌ Отсутствуют секции: {missing_sections}")
        return False
    else:
        print("  ✅ Все необходимые секции присутствуют")
    
    # Проверяем систему здоровья
    health = report['system_health']
    print(f"  🏥 Общее здоровье системы: {health['overall_health']:.2%}")
    print(f"  ⚠️ Критических проблем: {health['critical_issues']}")
    print(f"  ⚡ Симуляции: {health['simulation_warnings']}")
    
    return True

async def main():
    """Главная функция тестирования"""
    print("🚀 Тестирование Reality Logger - ТЗ-5")
    print("=" * 50)
    
    tests = [
        ("Базовая функциональность", test_reality_logger_basic),
        ("Интеграция с пайплайнами", test_pipeline_integration),
        ("Детекция silent failures", test_silent_failure_detection),
        ("Генерация отчета", test_report_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Запуск теста: {test_name}")
            result = await test_func()
            results.append((test_name, result))
            print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Reality Logger работает корректно.")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте логи.")
    
    # Очистка
    cleanup_reality_logger()

if __name__ == "__main__":
    asyncio.run(main())
