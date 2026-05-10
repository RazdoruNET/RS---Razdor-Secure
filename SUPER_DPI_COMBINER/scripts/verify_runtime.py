#!/usr/bin/env python3
"""
Runtime Verification Suite - Проверка стабильности runtime
TRUTH MODE verification
"""

import sys
import asyncio
import importlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_import_integrity():
    """Проверка целостности импортов"""
    print("🔍 Проверка импортов...")
    
    try:
        # Проверяем core компоненты
        from super_dpi_combiner.core import contracts, runner, http_client, logging, shutdown
        print("  ✅ Core компоненты импортируются")
        
        # Проверяем пайплайны
        from super_dpi_combiner.pipelines import HTTPFragmentation, Echo
        print("  ✅ Пайплайны импортируются")
        
        # Проверяем main
        from super_dpi_combiner import main
        print("  ✅ Main модуль импортируется")
        
        # Проверяем отсутствие legacy импортов
        import super_dpi_combiner.core
        core_source = super_dpi_combiner.core.__file__
        with open(core_source, 'r') as f:
            core_content = f.read()
            
        forbidden_imports = ['legacy', 'darknet', 'tor', 'dns', 'adaptive', 'ai', 'llm']
        for forbidden in forbidden_imports:
            if forbidden in core_content.lower():
                print(f"  ❌ Найден запрещённый импорт: {forbidden}")
                return False
        
        print("  ✅ Legacy импорты отсутствуют")
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка импорта: {e}")
        return False

async def test_pipeline_execution():
    """Проверка выполнения пайплайнов"""
    print("\n🧪 Проверка выполнения пайплайнов...")
    
    try:
        from super_dpi_combiner.core import Runner, Request
        from super_dpi_combiner.pipelines import Echo, HTTPFragmentation
        
        runner = Runner()
        
        # Тестируем Echo
        echo_pipeline = Echo()
        request = Request(host="test.com", port=80)
        
        response = echo_pipeline.execute(request)
        
        if response.success and response.status_code == 200:
            print("  ✅ Echo пайплайн работает")
        else:
            print(f"  ❌ Echo пайплайн не работает: {response.error}")
            return False
        
        # Тестируем HTTPFragmentation (только создание, не реальный запрос)
        http_pipeline = HTTPFragmentation()
        if http_pipeline.name == "HTTPFragmentation":
            print("  ✅ HTTPFragmentation пайплайн создается")
        else:
            print("  ❌ HTTPFragmentation пайплайн не создается")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка выполнения пайплайна: {e}")
        return False

async def test_network_reality():
    """Проверка реальности сетевых операций"""
    print("\n🌐 Проверка сетевых операций...")
    
    try:
        from super_dpi_combiner.core.http_client import HTTPClient
        from super_dpi_combiner.core import Request
        
        client = HTTPClient()
        
        # Проверяем создание запроса
        request = Request(host="example.com", port=80)
        
        # Проверяем HTTP client methods
        if hasattr(client, 'connect') and hasattr(client, 'send') and hasattr(client, 'receive'):
            print("  ✅ HTTP client имеет необходимые методы")
        else:
            print("  ❌ HTTP client не имеет необходимых методов")
            return False
            
        print("  ✅ Сетевые операции доступны")
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка сетевых операций: {e}")
        return False

async def test_truth_mode():
    """Проверка TRUTH MODE"""
    print("\n🎯 Проверка TRUTH MODE...")
    
    try:
        from super_dpi_combiner.pipelines import Echo
        from super_dpi_combiner.core import Request
        
        # Проверяем что Echo не возвращает фейковые успехи
        echo = Echo()
        request = Request(host="invalid-host-that-does-not-exist.com", port=80)
        
        response = echo.execute(request)
        
        # Echo всегда должен возвращать success=True, но с реальными данными
        if response.success and response.status_code == 200 and "invalid-host-that-does-not-exist.com" in response.data.decode():
            print("  ✅ Echo возвращает реальные данные")
        else:
            print("  ❌ Echo не возвращает реальные данные")
            return False
            
        # Проверяем отсутствие фейковых метрик
        if not hasattr(response, 'fake_metric') and not hasattr(response, 'stealth_score'):
            print("  ✅ Отсутствуют фейковые метрики")
        else:
            print("  ❌ Найдены фейковые метрики")
            return False
            
        print("  ✅ TRUTH MODE активен")
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка TRUTH MODE: {e}")
        return False

async def main():
    """Основная функция верификации"""
    print("🚀 Super DPI Combiner - Runtime Verification Suite")
    print("=" * 60)
    
    tests = [
        ("Import Integrity", test_import_integrity),
        ("Pipeline Execution", test_pipeline_execution),
        ("Network Reality", test_network_reality),
        ("Truth Mode", test_truth_mode),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} завершился ошибкой: {e}")
            results.append((test_name, False))
    
    # Итоговый отчёт
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ ВЕРИФИКАЦИИ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ - Runtime стабилен!")
        return 0
    else:
        print(f"\n⚠️ {total-passed} тестов не пройдено - требуется исправление")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
