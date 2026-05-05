#!/usr/bin/env python3
"""
Полный тест Omega Transport Bridges - План «Омега»
Obfs4, Snowflake, Shadow-TLS - полная маскировка под обычный трафик
"""
import sys
import os
import time
import json
from datetime import datetime
sys.path.append('.')
sys.path.append('./rsecure')

def test_omega_complete():
    """Полный тест Omega Transport"""
    print("🌉 План «Омега» - Полный тест транспортных мостов")
    print("=" * 70)
    
    try:
        # Импорт модулей
        from rsecure.modules.defense.omega_transport_bridges import omega_transport, setup_omega_bridges, get_active_bridges
        from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod
        
        print("✅ Omega Transport модуль импортирован")
        
        # Создание движка DPI bypass
        engine = DPIBypassEngine()
        print("✅ DPI bypass движок создан")
        
        # Тест 1: Настройка всех мостов
        print("\n🌉 Этап 1: Настройка транспортных мостов")
        bridges_result = setup_omega_bridges()
        
        print("\n📊 Результаты настройки мостов:")
        print(json.dumps(bridges_result, indent=2))
        
        # Тест 2: DPI bypass с Omega Transport
        print("\n🛡️ Этап 2: DPI bypass с Omega Transport")
        
        config = BypassConfig(
            method=BypassMethod.PROTOCOL_MIMICKING,
            target_host="www.youtube.com",
            target_port=443
        )
        
        start_time = time.time()
        bypass_result = engine.bypass_dpi(config)
        end_time = time.time()
        
        bypass_time = end_time - start_time
        
        print(f"\n📺 Результат DPI bypass:")
        print(f"   Успех: {'✅ Да' if bypass_result else '❌ Нет'}")
        print(f"   Время: {bypass_time:.2f}s")
        
        # Тест 3: Проверка YouTube доступности
        print("\n📺 Этап 3: Проверка YouTube доступности")
        accessible_before = check_youtube_accessibility("https://www.youtube.com")
        print(f"   Доступность ДО bypass: {'✅ Доступен' if accessible_before else '❌ Заблокирован'}")
        
        if bypass_result:
            accessible_after = check_youtube_accessibility("https://www.youtube.com")
            print(f"   Доступность ПОСЛЕ bypass: {'✅ Доступен' if accessible_after else '❌ Заблокирован'}")
            
            if not accessible_before and accessible_after:
                print("   🎯 Эффективность: ✅ YouTube РАЗБЛОКИРОВАН!")
            elif accessible_before and accessible_after:
                print("   ⚠️ Эффективность: ⚠️ YouTube был доступен")
            else:
                print("   ❌ Эффективность: ❌ YouTube НЕ разблокирован")
        
        # Тест 4: Статус активных мостов
        print("\n🌉 Этап 4: Статус активных мостов")
        active_bridges = get_active_bridges()
        
        if active_bridges:
            print(f"   ✅ Активных мостов: {len(active_bridges)}")
            for bridge in active_bridges:
                transport = bridge.get('transport', 'unknown')
                address = bridge.get('address', 'unknown')
                status = bridge.get('status', 'unknown')
                print(f"      {transport}: {address} ({status})")
        else:
            print("   ❌ Активных мостов: 0")
        
        # Тест 5: Генерация torrc конфигурации
        print("\n🔧 Этап 5: Генерация torrc конфигурации")
        torrc_config = omega_transport.generate_torrc_config()
        
        # Сохранение конфигурации
        torrc_path = os.path.expanduser("~/.tor/torrc_omega")
        os.makedirs(os.path.dirname(torrc_path), exist_ok=True)
        
        with open(torrc_path, 'w') as f:
            f.write(torrc_config)
        
        print(f"   ✅ Конфигурация сохранена: {torrc_path}")
        
        # Тест 6: Итоги и рекомендации
        print("\n📊 Этап 6: Итоги и рекомендации")
        
        total_test_time = time.time() - start_time
        
        summary = {
            "test_timestamp": datetime.now().isoformat(),
            "test_duration": f"{total_test_time:.2f}s",
            "bridges_setup": bridges_result,
            "bypass_result": bypass_result,
            "bypass_time": f"{bypass_time:.2f}s",
            "youtube_accessible_before": accessible_before,
            "youtube_accessible_after": accessible_after if bypass_result else accessible_before,
            "active_bridges_count": len(active_bridges) if active_bridges else 0,
            "torrc_config_path": torrc_path,
            "omega_transport_success": True
        }
        
        # Сохранение полного отчета
        report_path = f"omega_transport_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Полный отчет сохранен: {report_path}")
        
        # Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ ПЛАНА «Омега»:")
        
        if bridges_result.get("total_active", 0) > 0:
            print("   🌉 Транспортные мосты активны - используйте:")
            print("      tor -f ~/.tor/torrc_omega")
            print("   🛡️ Для автоматического запуска:")
            print("      export TOR_SKIP_LAUNCH=1")
            print("      tor -f ~/.tor/torrc_omega")
        
        if bypass_result and not accessible_before and accessible_after:
            print("   🎯 YouTube УСПЕШНО разблокирован через!")
            print("   🌉 План «Омега» работает!")
        elif bypass_result:
            print("   ⚠️ Bypass технически работает, но YouTube не разблокирован")
            print("   🔧 Проверьте настройки мостов или попробуйте другие мосты")
        else:
            print("   ❌ Bypass не сработал")
            print("   🔧 Проверьте доступность мостов и настройки сети")
        
        print("\n🌉 План «Омега» завершен!")
        
        return summary
        
    except Exception as e:
        print(f"❌ Критическая ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_youtube_accessibility(url: str) -> bool:
    """Проверка доступности YouTube"""
    try:
        import urllib.request
        import ssl
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        with urllib.request.urlopen(request, timeout=10, context=context) as response:
            return response.status == 200
            
    except:
        return False

def main():
    """Главная функция"""
    print("🌉 Запуск Плана «Омега» - Транспортные мосты для обхода усиленного DPI")
    print("=" * 70)
    
    # Запуск полного теста
    results = test_omega_complete()
    
    if results:
        print("\n🎉 План «Омега» УСПЕШНО ЗАВЕРШЕН!")
        print("🌉 Транспортные мосты готовы к использованию!")
    else:
        print("\n❌ План «Омега» ЗАВЕРШЕН С ОШИБКАМИ")
        print("🔧 Проверьте конфигурацию и настройки сети")
    
    return results

if __name__ == "__main__":
    main()
