#!/usr/bin/env python3
"""
Тестирование Tor-Core интеграции
"""
import sys
import os
sys.path.append('.')
sys.path.append('./rsecure')

def test_tor_core_integration():
    """Тестирование Tor-Core интеграции"""
    try:
        print("🧬 Tor-Core Integration Test")
        print("=" * 50)
        
        # Импортируем Tor-Core
        from rsecure.modules.defense.tor_core_integration import tor_core, activate_darknet_bridge, get_youtube_through_tor, automatic_tor_fallback
        print("✅ Tor-Core импортирован успешно")
        
        # Тест 1: Активация Darknet моста
        print("\n🌐 Тест 1: Активация Darknet моста")
        activate_result = activate_darknet_bridge()
        print(f"Результат: {activate_result}")
        
        # Тест 2: Получение YouTube через Tor
        print("\n📺 Тест 2: Получение YouTube через Tor")
        youtube_result = get_youtube_through_tor()
        print(f"Результат: {youtube_result}")
        
        # Тест 3: Автоматическое переключение на Tor
        print("\n🔄 Тест 3: Автоматическое переключение на Tor")
        auto_result = automatic_tor_fallback("https://www.youtube.com")
        print(f"Результат: {auto_result}")
        
        # Тест 4: Статус Tor
        print("\n📊 Тест 4: Статус Tor соединения")
        status = tor_core.get_tor_status()
        print(f"Статус: {status}")
        
        # Тест 5: DPI bypass с Tor-Core
        print("\n🛡️ Тест 5: DPI bypass с Tor-Core")
        from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod
        
        engine = DPIBypassEngine()
        config = BypassConfig(
            method=BypassMethod.PROTOCOL_MIMICKING,
            target_host="www.youtube.com",
            target_port=443
        )
        
        bypass_result = engine.bypass_dpi(config)
        print(f"Bypass результат: {bypass_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования Tor-Core: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dpi_bypass_with_tor():
    """Тестирование DPI bypass с Tor-Core"""
    try:
        print("\n🛡️ DPI Bypass с Tor-Core Test")
        print("=" * 50)
        
        from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod
        
        engine = DPIBypassEngine()
        config = BypassConfig(
            method=BypassMethod.PROTOCOL_MIMICKING,
            target_host="www.youtube.com",
            target_port=443
        )
        
        print("🔄 Запуск DPI bypass с Tor-Core...")
        result = engine.bypass_dpi(config)
        
        print(f"✅ DPI bypass завершен: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка DPI bypass: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов Tor-Core интеграции")
    
    # Тест 1: Tor-Core интеграция
    success1 = test_tor_core_integration()
    
    # Тест 2: DPI bypass с Tor-Core
    success2 = test_dpi_bypass_with_tor()
    
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ТЕСТОВ")
    print(f"Tor-Core интеграция: {'✅ УСПЕХ' if success1 else '❌ ОШИБКА'}")
    print(f"DPI bypass с Tor-Core: {'✅ УСПЕХ' if success2 else '❌ ОШИБКА'}")
    
    if success1 and success2:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ - Tor-Core готов к работе!")
    else:
        print("⚠️ Некоторые тесты не пройдены - проверьте конфигурацию")
