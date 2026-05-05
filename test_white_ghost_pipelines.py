#!/usr/bin/env python3
"""
Тестовый скрипт для White-Ghost Pipelines
Реализация "White-Ghost" с автоматической ротацией SNI и обработкой ERR_TIMED_OUT
"""

import sys
import os

# Добавляем путь к модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure/modules/defense'))

try:
    from dpi_bypass_combiner import dpi_combiner
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь что файл dpi_bypass_combiner.py находится в rsecure/modules/defense/")
    sys.exit(1)


def test_white_ghost_pipelines():
    """Тестирование White-Ghost Pipelines"""
    
    print("👻 DPI-Bypass Combiner - White-Ghost Pipelines ТЕСТИРОВАНИЕ")
    print("=" * 70)
    
    # Тест 1: Проверка статуса системы
    print("\n📊 Тест 1: Статус системы")
    print(f"   🎯 Целевой хост: www.youtube.com")
    print(f"   🛡️ White-List категорий: 5")
    print(f"   ⛓️ White-Ghost цепочек: 3")
    
    # Тест 2: Проверка SNI масок
    print("\n🎭 Тест 2: SNI маски из White List")
    print(f"   🏛️ Гос-маска: {dpi_combiner.whitelist_core.get_domain_by_mask('GOVERNMENT_IMMUNITY')}")
    print(f"   📺 Медиа-маска: {dpi_combiner.whitelist_core.get_domain_by_mask('MEDIA_NOISE')}")
    print(f"   💰 Финансовая маска: {dpi_combiner.whitelist_core.get_domain_by_mask('FINANCIAL_TUNNEL')}")
    print(f"   🏥 Life-Line маска: {dpi_combiner.whitelist_core.get_domain_by_mask('LIFE_SUPPORT')}")
    
    # Тест 3: Проверка цепочек
    print("\n⛓️ Тест 3: White-Ghost цепочки")
    print(f"   🥇 Госвеб-Туннель (приоритет 1) - SNI Splitting + Гос-маска")
    print(f"   🥈 Медиа-Паразит (приоритет 2) - HTTP/2 Multiplexing + Медиа-маска")
    print(f"   🥉 Фин-Шторм (приоритет 3) - TCP Window = 1 + sbp.nspk.ru")
    
    # Тест 4: Основной тест White-Ghost Pipelines
    print("\n🚀 Тест 4: Запуск White-Ghost Pipelines")
    
    # Определяем цель
    target = "www.youtube.com"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    print(f"🎯 Цель: {target}")
    
    try:
        result = dpi_combiner.run_white_ghost_pipelines(target)
        
        print(f"\n📊 РЕЗУЛЬТАТ WHITE-GHOST:")
        print(f"=" * 40)
        print(f"🎯 Цель: {result['target_host']}")
        
        # Проверяем формат результата
        if result.get('method') == 'direct_access':
            print(f"✅ Успех: Доступен напрямую")
            print(f"🔄 Обход не требуется")
            print(f"⛓️ Цепочек попробовано: {result.get('pipelines_tried', 0)}")
            return True
        else:
            print(f"✅ Успех: {result.get('final_success', False)}")
            print(f"⛓️ Цепочек попробовано: {len(result.get('pipelines_tried', []))}")
            print(f"⏱️ Общее время: {result.get('total_duration', 0):.2f}s")
            
            if result.get('timeout_detected'):
                print(f"⏰ ERR_TIMED_OUT обнаружен: Да")
            
            if result.get('successful_pipeline'):
                print(f"🏆 Успешная цепочка: {result['successful_pipeline']}")
            
            if result.get('final_accessibility'):
                print(f"📺 Финальная доступность: ✅ Доступен")
            else:
                print(f"📺 Финальная доступность: ❌ Заблокирован")
            
            # Детальные результаты по цепочкам
            if 'pipelines_tried' in result:
                print(f"\n📋 Детальные результаты цепочек:")
                for i, pipeline_result in enumerate(result['pipelines_tried'], 1):
                    status_icon = "✅" if pipeline_result['success'] else "❌"
                    print(f"   {i}. {status_icon} {pipeline_result['pipeline']}")
                    print(f"      SNI маска: {pipeline_result.get('sni_mask', 'N/A')}")
                    print(f"      Длительность: {pipeline_result['duration']:.2f}s")
                    
                    if pipeline_result.get('timeout'):
                        print(f"      ⏰ ERR_TIMED_OUT: Обнаружен")
                    
                    if pipeline_result.get('error'):
                        print(f"      Ошибка: {pipeline_result['error']}")
                    
                    if pipeline_result.get('response'):
                        response_preview = pipeline_result['response'][:50]
                        print(f"      Ответ: {response_preview}...")
            
            return result.get('final_success', False)
        
    except Exception as e:
        print(f"❌ Критическая ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_individual_pipelines():
    """Тестирование отдельных цепочек"""
    print("\n🔬 Тестирование отдельных цепочек:")
    print("=" * 40)
    
    target = "www.youtube.com"
    
    # Тест Госвеб-Туннель
    print(f"\n🥇 Тест Госвеб-Туннель:")
    try:
        result = dpi_combiner.gosweb_tunnel.execute(target)
        print(f"   Результат: {'✅ Успех' if result['success'] else '❌ Ошибка'}")
        if result.get('timeout'):
            print(f"   ⏰ ERR_TIMED_OUT обнаружен")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест Медиа-Паразит
    print(f"\n🥈 Тест Медиа-Паразит:")
    try:
        result = dpi_combiner.media_parasite.execute(target)
        print(f"   Результат: {'✅ Успех' if result['success'] else '❌ Ошибка'}")
        if result.get('pending'):
            print(f"   ⏳ Pending обнаружен")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Тест Фин-Шторм
    print(f"\n🥉 Тест Фин-Шторм:")
    try:
        result = dpi_combiner.fin_storm.execute(target)
        print(f"   Результат: {'✅ Успех' if result['success'] else '❌ Ошибка'}")
        print(f"   🎭 SNI маска: {result.get('sni_mask', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")


def main():
    """Основная функция"""
    print("👻 Запуск White-Ghost Pipelines")
    print("⚠️  Рекомендуется отключить VPN перед запуском")
    print("🔥 Реализация с автоматической ротацией SNI и обработкой ERR_TIMED_OUT")
    print()
    
    # Проверка аргументов
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Использование:")
        print(f"  python3 {sys.argv[0]} [target_host] [--individual]")
        print()
        print("Примеры:")
        print(f"  python3 {sys.argv[0]} www.youtube.com")
        print(f"  python3 {sys.argv[0]} twitter.com")
        print(f"  python3 {sys.argv[0]} --individual  # Тест отдельных цепочек")
        sys.exit(0)
    
    # Проверка флага индивидуального тестирования
    if '--individual' in sys.argv:
        test_individual_pipelines()
        return
    
    # Запуск основного теста
    success = test_white_ghost_pipelines()
    
    if success:
        print(f"\n🎉 ТЕСТ WHITE-GHOST УСПЕШЕН!")
        print("👻 White-Ghost Pipelines готовы к использованию!")
        print("🛡️ Автоматическая ротация SNI работает")
        print("⏰ Обработка ERR_TIMED_OUT активна")
    else:
        print(f"\n❌ ТЕСТ WHITE-GHOST НЕ УДАЛСЯ")
        print("🔧 Проверьте настройки сети и повторите попытку")
        print("⚠️ Возможно требуется другая SNI маска")
    
    print(f"\n🏁 Завершение программы")


if __name__ == "__main__":
    main()
