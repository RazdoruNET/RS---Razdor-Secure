#!/usr/bin/env python3
"""
Тестовый скрипт для DPI-Bypass Combiner v2.0 "White-Ghost"
Zero-Dependency реализация для macOS User-Space
"""

import sys
import os

# Добавляем путь к модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure/modules/defense'))

try:
    from dpi_bypass_combiner_v2 import dpi_combiner_v2
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь что файл dpi_bypass_combiner_v2.py находится в rsecure/modules/defense/")
    sys.exit(1)


def test_v2_system():
    """Тестирование DPI-Bypass Combiner v2.0"""
    
    print("👻 DPI-Bypass Combiner v2.0 'White-Ghost' - ТЕСТИРОВАНИЕ")
    print("=" * 60)
    
    # Тест 1: Проверка статуса системы
    print("\n📊 Тест 1: Статус системы")
    status = dpi_combiner_v2.get_status()
    print(f"   Версия: {status['version']}")
    print(f"   Whitelist доменов: {status['whitelist_domains']} категорий")
    print(f"   Активных цепочек: {status['active_chains']}")
    print(f"   Текущие маски: {list(status['current_masks'].keys())[:3]}...")
    
    # Тест 2: Проверка WhitelistEngine
    print("\n🎭 Тест 2: WhitelistEngine")
    print(f"   Гос-маска: {dpi_combiner_v2.whitelist_engine.get_mask('GOVERNMENT')}")
    print(f"   Медиа-маска: {dpi_combiner_v2.whitelist_engine.get_mask('TELECOM')}")
    print(f"   Финансовая маска: {dpi_combiner_v2.whitelist_engine.get_mask('FINANCIAL')}")
    print(f"   Life-Line маска: {dpi_combiner_v2.whitelist_engine.get_mask('MEDICAL')}")
    
    # Тест 3: Проверка цепочек
    print("\n🔗 Тест 3: Цепочки обхода")
    for chain in dpi_combiner_v2.auto_switcher.chains:
        print(f"   📋 {chain.name} (приоритет {chain.priority})")
    
    # Тест 4: Основной тест обхода
    print("\n🚀 Тест 4: Обход цели")
    
    # Определяем цель
    target = "www.youtube.com"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    print(f"🎯 Цель: {target}")
    
    try:
        result = dpi_combiner_v2.bypass_target(target)
        
        print(f"\n📊 РЕЗУЛЬТАТ:")
        print(f"=" * 30)
        print(f"🎯 Цель: {result['target_host']}")
        
        # Проверяем формат результата
        if result.get('direct_access', False):
            print(f"✅ Успех: Доступен напрямую")
            print(f"🔄 Обход не требуется")
            return True
        else:
            print(f"✅ Успех: {result.get('final_success', False)}")
            print(f"🔄 Цепочек попробовано: {len(result.get('chains_tried', []))}")
            
            if result.get('successful_chain'):
                print(f"🏆 Успешная цепочка: {result['successful_chain']}")
            
            print(f"⏱️ Общее время: {result.get('total_duration', 0):.2f}s")
            
            if result.get('lifeline_activated'):
                print(f"🏥 Life-Line активирован: Да")
            
            # Детальные результаты по цепочкам
            if 'chains_tried' in result:
                print(f"\n📋 Детальные результаты:")
                for chain_result in result['chains_tried']:
                    status_icon = "✅" if chain_result['success'] else "❌"
                    print(f"   {status_icon} {chain_result['name']} ({chain_result['priority']}) - {chain_result['stage_completed']}")
                    if chain_result['error']:
                        print(f"      Ошибка: {chain_result['error']}")
            
            return result.get('final_success', False)
        
    except Exception as e:
        print(f"❌ Критическая ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Основная функция"""
    print("👻 Запуск DPI-Bypass Combiner v2.0 'White-Ghost'")
    print("⚠️  Рекомендуется отключить VPN перед запуском")
    print("🔥 Zero-Dependency реализация для macOS User-Space")
    print()
    
    # Проверка аргументов
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Использование:")
        print(f"  python3 {sys.argv[0]} [target_host]")
        print()
        print("Примеры:")
        print(f"  python3 {sys.argv[0]} www.youtube.com")
        print(f"  python3 {sys.argv[0]} google.com")
        print(f"  python3 {sys.argv[0]} twitter.com")
        sys.exit(0)
    
    # Запуск теста
    success = test_v2_system()
    
    if success:
        print(f"\n🎉 ТЕСТ УСПЕШЕН!")
        print("👻 DPI-Bypass Combiner v2.0 готов к использованию!")
    else:
        print(f"\n❌ ТЕСТ НЕ УДАЛСЯ")
        print("🔧 Проверьте настройки сети и повторите попытку")
    
    print(f"\n🏁 Завершение программы")


if __name__ == "__main__":
    main()
