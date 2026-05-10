#!/usr/bin/env python3
"""
Тест стабилизации движка пайплайнов
Проверка всех требований из ТЗ #1
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Добавляем путь к core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse, BypassTechnique, PipelineStatus
from core.pipeline_manager import PipelineManager

class TestPipeline(BasePipeline):
    """Тестовый пайплайн для проверки стабилизации"""
    
    def __init__(self, name: str, should_fail_init: bool = False, should_fail_execute: bool = False, execution_delay: float = 0.0):
        super().__init__(name, BypassTechnique.SPOOF_DPI)
        self.should_fail_init = should_fail_init
        self.should_fail_execute = should_fail_execute
        self.execution_delay = execution_delay
    
    def initialize(self, config):
        """Инициализация с возможным провалом"""
        if self.should_fail_init:
            self._mark_initialized(False)
            return False
        
        self.config = config
        self._mark_initialized(True)
        return True
    
    async def execute(self, request):
        """Выполнение с возможным провалом"""
        if not self._validate_initialized():
            raise Exception("Pipeline not initialized")
        
        if self.should_fail_execute:
            raise Exception("Intentional execution failure")
        
        if self.execution_delay > 0:
            await asyncio.sleep(self.execution_delay)
        
        return BypassResponse(
            success=True,
            status_code=200,
            data=b"test response",
            technique_used=self.name
        )
    
    def cleanup(self):
        """Очистка ресурсов"""
        return True

class InvalidPipeline:
    """Невалидный пайплайн - не наследуется от BasePipeline"""
    def __init__(self):
        self.name = "invalid"
    
    def initialize(self, config):
        return True
    
    async def execute(self, request):
        return BypassResponse(success=True)

class IncompletePipeline(BasePipeline):
    """Неполный пайплайн - missing methods"""
    def __init__(self):
        super().__init__("incomplete", BypassTechnique.SPOOF_DPI)
    
    def initialize(self, config):
        return True
    # Отсутствует метод execute и cleanup

async def test_lifecycle_contract():
    """Тест строгого контракта жизненного цикла"""
    print("🧪 Тест 1: Строгий контракт жизненного цикла")
    
    # 1. Проверка execute без initialize
    pipeline = TestPipeline("test_no_init")
    
    # Пытаемся выполнить без инициализации
    request = BypassRequest(host="test.com", port=443)
    response = await pipeline.safe_execute(request)
    
    assert not response.success
    assert "not initialized" in response.error
    print("✅ Execute без initialize заблокирован")
    
    # 2. Проверка успешной инициализации
    pipeline2 = TestPipeline("test_valid")
    assert pipeline2.initialize({})
    assert pipeline2._validate_initialized()
    assert pipeline2.status == PipelineStatus.IDLE
    print("✅ Успешная инициализация работает")
    
    # 3. Проверка провальной инициализации
    pipeline3 = TestPipeline("test_fail_init", should_fail_init=True)
    assert not pipeline3.initialize({})
    assert not pipeline3._validate_initialized()
    assert pipeline3.status == PipelineStatus.FAILED
    print("✅ Провальная инициализация обрабатывается")

async def test_error_isolation():
    """Тест изоляции ошибок"""
    print("\n🧪 Тест 2: Изоляция ошибок")
    
    # 1. Проверка исключений в execute
    pipeline = TestPipeline("test_error", should_fail_execute=True)
    pipeline.initialize({})
    
    request = BypassRequest(host="test.com", port=443)
    response = await pipeline.safe_execute(request)
    
    assert not response.success
    assert "error" in response.error.lower()
    assert isinstance(response, BypassResponse)
    print("✅ Исключения превращаются в BypassResponse")
    
    # 2. Проверка таймаутов
    pipeline2 = TestPipeline("test_timeout", execution_delay=2.0)
    pipeline2.initialize({})
    
    request2 = BypassRequest(host="test.com", port=443)
    response2 = await pipeline2.safe_execute(request2, timeout=0.5)
    
    assert not response2.success
    assert "timeout" in response2.error.lower()
    print("✅ Таймауты обрабатываются")

async def test_pipeline_validation():
    """Тест валидации пайплайнов при загрузке"""
    print("\n🧪 Тест 3: Валидация пайплайнов при загрузке")
    
    # Создаем временную директорию для тестов
    test_dir = Path("test_pipelines")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Создаем тестовый модуль с валидным пайплайном
        with open(test_dir / "__init__.py", "w") as f:
            f.write("")
        
        with open(test_dir / "test_module.py", "w") as f:
            f.write("""
from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse, BypassTechnique

class ValidTestPipeline(BasePipeline):
    def __init__(self):
        super().__init__("valid_test", BypassTechnique.SPOOF_DPI)
    
    def initialize(self, config):
        self._mark_initialized(True)
        return True
    
    async def execute(self, request):
        return BypassResponse(success=True)
    
    def cleanup(self):
        return True

class InvalidTestPipeline:
    def __init__(self):
        self.name = "invalid"
""")
        
        # Создаем PipelineManager и тестируем загрузку
        manager = PipelineManager(pipelines_dir=str(test_dir))
        
        # Подменяем путь поиска для теста
        sys.path.insert(0, str(test_dir))
        
        # Импортируем тестовый модуль
        import test_module
        
        # Тестируем валидацию
        valid_class = test_module.ValidTestPipeline
        invalid_class = test_module.InvalidTestPipeline
        
        # Валидация должна пройти для валидного класса
        is_valid, error = manager._validate_pipeline_interface(valid_class)
        assert is_valid, f"Valid pipeline should pass validation: {error}"
        print("✅ Валидный пайплайн проходит проверку")
        
        # Валидация должна провалиться для невалидного класса
        is_valid, error = manager._validate_pipeline_interface(invalid_class)
        assert not is_valid, "Invalid pipeline should fail validation"
        print("✅ Невалидный пайплайн отклоняется")
        
    finally:
        # Очистка
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

async def test_engine_resilience():
    """Тест устойчивости движка к ошибкам"""
    print("\n🧪 Тест 4: Устойчивость движка")
    
    # Создаем пайплайны с разными проблемами
    good_pipeline = TestPipeline("good_pipeline")
    good_pipeline.initialize({})
    
    bad_pipeline = TestPipeline("bad_pipeline", should_fail_execute=True)
    bad_pipeline.initialize({})
    
    slow_pipeline = TestPipeline("slow_pipeline", execution_delay=1.0)
    slow_pipeline.initialize({})
    
    # Тестируем что ошибки не крашат систему
    pipelines = [good_pipeline, bad_pipeline, slow_pipeline]
    
    for pipeline in pipelines:
        request = BypassRequest(host="test.com", port=443)
        
        try:
            response = await pipeline.safe_execute(request, timeout=0.5)
            assert isinstance(response, BypassResponse)
            print(f"✅ {pipeline.name}: {response.success} ({'error' if not response.success else 'ok'})")
        except Exception as e:
            print(f"❌ {pipeline.name}: Unexpected exception: {e}")
            raise

async def test_partial_failure():
    """Тест работы при частичных отказах"""
    print("\n🧪 Тест 5: Работа при частичных отказах")
    
    # Создаем несколько пайплайнов, некоторые из которых не работают
    pipelines = []
    
    # 50% рабочих, 50% нерабочих
    for i in range(10):
        if i % 2 == 0:
            pipeline = TestPipeline(f"good_{i}")
            pipeline.initialize({})
            pipelines.append(pipeline)
        else:
            pipeline = TestPipeline(f"bad_{i}", should_fail_execute=True)
            pipeline.initialize({})
            pipelines.append(pipeline)
    
    # Проверяем что система продолжает работать
    success_count = 0
    total_requests = 0
    
    for pipeline in pipelines:
        request = BypassRequest(host="test.com", port=443)
        response = await pipeline.safe_execute(request)
        
        total_requests += 1
        if response.success:
            success_count += 1
    
    # Половина должна работать
    assert success_count == 5, f"Expected 5 successes, got {success_count}"
    assert total_requests == 10, f"Expected 10 total requests, got {total_requests}"
    
    print(f"✅ Система работает при частичных отказах: {success_count}/{total_requests} успешно")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов стабилизации движка пайплайнов\n")
    
    try:
        await test_lifecycle_contract()
        await test_error_isolation()
        await test_pipeline_validation()
        await test_engine_resilience()
        await test_partial_failure()
        
        print("\n🎉 Все тесты пройдены!")
        print("✅ Стабилизация движка соответствует требованиям ТЗ #1")
        
    except Exception as e:
        print(f"\n❌ Тест провален: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
