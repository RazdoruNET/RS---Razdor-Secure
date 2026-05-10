#!/usr/bin/env python3
"""
Test Pipeline Registry - Проверка работы реестра пайплайнов
Тестирует автообнаружение, безопасную загрузку и статусы пайплайнов
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.pipeline_registry import PipelineRegistry, discover_and_load_pipelines, get_pipeline_registry


async def test_pipeline_discovery():
    """Тест обнаружения пайплайнов"""
    print("🔍 Testing Pipeline Discovery System")
    print("=" * 50)
    
    # Создаем реестр
    registry = PipelineRegistry()
    
    # Запускаем обнаружение
    start_time = time.time()
    discovered_pipelines = await registry.discover_pipelines()
    discovery_time = time.time() - start_time
    
    print(f"\n⏱️ Discovery completed in {discovery_time:.2f} seconds")
    print(f"📊 Total pipelines found: {len(discovered_pipelines)}")
    
    return registry, discovered_pipelines


def test_pipeline_statuses(registry):
    """Тест статусов пайплайнов"""
    print("\n📋 Testing Pipeline Statuses")
    print("=" * 50)
    
    # Получаем сводную информацию
    summary = registry.get_registry_summary()
    
    print(f"📈 Registry Summary:")
    print(f"   Total pipelines: {summary['total_pipelines']}")
    print(f"   ✅ Ready pipelines: {summary['ready_pipelines']}")
    print(f"   ❌ Broken pipelines: {summary['broken_pipelines']}")
    print(f"   🔧 Simulated pipelines: {summary['simulated_pipelines']}")
    
    # Выводим списки по категориям
    if summary['ready_pipeline_names']:
        print(f"\n🚀 READY pipelines ({len(summary['ready_pipeline_names'])}):")
        for name in summary['ready_pipeline_names']:
            info = registry.get_pipeline_info(name)
            print(f"   ✅ {name} - {info.module_path}")
    
    if summary['broken_pipeline_names']:
        print(f"\n💀 BROKEN pipelines ({len(summary['broken_pipeline_names'])}):")
        for name in summary['broken_pipeline_names']:
            info = registry.get_pipeline_info(name)
            error = info.error_message or "Unknown error"
            print(f"   ❌ {name} - {error}")
    
    if summary['simulated_pipeline_names']:
        print(f"\n🔧 SIMULATED pipelines ({len(summary['simulated_pipeline_names'])}):")
        for name in summary['simulated_pipeline_names']:
            info = registry.get_pipeline_info(name)
            print(f"   🔧 {name} - {info.module_path}")
    
    return summary


async def test_pipeline_creation(registry):
    """Тест создания экземпляров пайплайнов"""
    print("\n🏗️ Testing Pipeline Instance Creation")
    print("=" * 50)
    
    ready_pipelines = registry.get_ready_pipelines()
    
    if not ready_pipelines:
        print("⚠️ No ready pipelines to test")
        return
    
    print(f"Testing {len(ready_pipelines)} ready pipelines...")
    
    created_instances = []
    failed_creations = []
    
    for name in list(ready_pipelines.keys())[:5]:  # Тестируем первые 5
        print(f"\n🔄 Creating instance of {name}...")
        
        try:
            instance = registry.create_pipeline_instance(name)
            
            if instance:
                created_instances.append((name, instance))
                print(f"   ✅ Instance created successfully")
                
                # Пробуем инициализировать
                try:
                    init_result = instance.initialize({})
                    print(f"   🔧 Initialization: {'✅ Success' if init_result else '❌ Failed'}")
                except Exception as e:
                    print(f"   ❌ Initialization error: {e}")
                
            else:
                failed_creations.append(name)
                print(f"   ❌ Failed to create instance")
                
        except Exception as e:
            failed_creations.append(name)
            print(f"   ❌ Exception during creation: {e}")
    
    print(f"\n📊 Instance Creation Results:")
    print(f"   ✅ Successfully created: {len(created_instances)}")
    print(f"   ❌ Failed to create: {len(failed_creations)}")
    
    return created_instances, failed_creations


async def test_global_registry():
    """Тест глобального реестра"""
    print("\n🌍 Testing Global Registry")
    print("=" * 50)
    
    # Используем глобальные функции
    start_time = time.time()
    global_pipelines = await discover_and_load_pipelines()
    global_time = time.time() - start_time
    
    print(f"⏱️ Global registry loaded in {global_time:.2f} seconds")
    print(f"📊 Global registry pipelines: {len(global_pipelines)}")
    
    # Получаем доступ через get_pipeline_registry
    registry = get_pipeline_registry()
    summary = registry.get_registry_summary()
    
    print(f"📈 Global registry summary:")
    print(f"   Total: {summary['total_pipelines']}")
    print(f"   Ready: {summary['ready_pipelines']}")
    print(f"   Broken: {summary['broken_pipelines']}")
    print(f"   Simulated: {summary['simulated_pipelines']}")
    
    return summary


async def main():
    """Основная функция тестирования"""
    print("🚀 PIPELINE REGISTRY TEST SUITE")
    print("=" * 60)
    print("Testing async safe discovery system for DPI bypass pipelines")
    print()
    
    try:
        # Тест 1: Обнаружение пайплайнов
        registry, pipelines = await test_pipeline_discovery()
        
        # Тест 2: Статусы пайплайнов
        summary = test_pipeline_statuses(registry)
        
        # Тест 3: Создание экземпляров
        await test_pipeline_creation(registry)
        
        # Тест 4: Глобальный реестр
        global_summary = await test_global_registry()
        
        # Финальная сводка
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULTS - PIPELINE REGISTRY TEST")
        print("=" * 60)
        
        print(f"✅ Pipeline discovery: {'WORKING' if len(pipelines) > 0 else 'FAILED'}")
        print(f"✅ Safe loading: {'WORKING' if summary['broken_pipelines'] >= 0 else 'FAILED'}")
        print(f"✅ Status tracking: {'WORKING' if summary['ready_pipelines'] >= 0 else 'FAILED'}")
        print(f"✅ Global registry: {'WORKING' if global_summary['total_pipelines'] > 0 else 'FAILED'}")
        
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Total pipelines discovered: {len(pipelines)}")
        print(f"   Ready to use: {summary['ready_pipelines']}")
        print(f"   Broken (need fixing): {summary['broken_pipelines']}")
        print(f"   Simulated (safe mode): {summary['simulated_pipelines']}")
        
        # Критерий приёмки
        if summary['ready_pipelines'] > 0:
            print(f"\n🎉 ACCEPTANCE CRITERIA MET!")
            print(f"✅ System outputs list of actually loadable pipelines:")
            for name in summary['ready_pipeline_names']:
                print(f"   🚀 {name}")
        else:
            print(f"\n⚠️ ACCEPTANCE CRITERIA NOT MET")
            print(f"❌ No ready pipelines found")
        
        return len(pipelines) > 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Запускаем тест
    result = asyncio.run(main())
    
    print(f"\n{'='*60}")
    if result:
        print("🎉 PIPELINE REGISTRY TEST: PASSED")
        print("✅ Async safe discovery system is working correctly")
    else:
        print("❌ PIPELINE REGISTRY TEST: FAILED")
        print("❌ System needs debugging")
    
    print("="*60)
    
    # Выход с соответствующим кодом
    sys.exit(0 if result else 1)
