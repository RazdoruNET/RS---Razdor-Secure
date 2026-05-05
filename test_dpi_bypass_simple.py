#!/usr/bin/env python3
"""
Простой тест DPI bypass с Tor-Core интеграцией
"""
import sys
import os
sys.path.append('.')
sys.path.append('./rsecure')

def test_dpi_bypass_simple():
    """Простой тест DPI bypass"""
    print("🚀 RSecure DPI Bypass Simple Test")
    print("=" * 50)
    
    try:
        # Импорт модулей
        from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod
        print("✅ DPI bypass модуль импортирован")
        
        # Создание движка
        engine = DPIBypassEngine()
        print("✅ DPI bypass движок создан")
        
        # Тестирование Tor-Core
        print("\n🧬 Тестирование Tor-Core интеграции...")
        try:
            from rsecure.modules.defense.tor_core_integration import activate_darknet_bridge
            tor_result = activate_darknet_bridge()
            print(f"   Tor-Core: {tor_result}")
        except Exception as e:
            print(f"   Tor-Core ошибка: {e}")
        
        # Тестирование YouTube доступности
        print("\n📺 Тестирование YouTube доступности...")
        try:
            import urllib.request
            import ssl
            
            url = "https://www.youtube.com"
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            with urllib.request.urlopen(request, timeout=10, context=context) as response:
                accessible = response.status == 200
                print(f"   YouTube доступность: {'✅ Доступен' if accessible else '❌ Заблокирован'}")
                
        except Exception as e:
            print(f"   YouTube доступность: ❌ Заблокирован ({e})")
        
        # Тестирование DPI bypass методов
        print("\n🛡️ Тестирование DPI bypass методов...")
        
        methods = [
            BypassMethod.PROTOCOL_MIMICKING,
            BypassMethod.DOMAIN_FRONTING,
            BypassMethod.TLS_SNI_SPLITTING
        ]
        
        for method in methods:
            print(f"\n🔄 Тестирование: {method.value}")
            
            try:
                config = BypassConfig(
                    method=method,
                    target_host="www.youtube.com",
                    target_port=443
                )
                
                result = engine.bypass_dpi(config)
                print(f"   Результат: {'✅ Успех' if result else '❌ Ошибка'}")
                
            except Exception as e:
                print(f"   Ошибка: {e}")
        
        print("\n✅ Тест завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dpi_bypass_simple()
