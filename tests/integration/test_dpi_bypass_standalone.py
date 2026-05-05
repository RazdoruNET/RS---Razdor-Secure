#!/usr/bin/env python3
"""
RSecure DPI Bypass Standalone Test Script
Независимый тест DPI bypass для проверки реальной разблокировки YouTube
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

from modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod

class StandaloneDPIBypassTest:
    def __init__(self):
        self.bypass_engine = DPIBypassEngine()
        self.results = {}
        
    def test_youtube_accessibility(self, url: str) -> bool:
        """Test specific URL accessibility"""
        try:
            import urllib.request
            import ssl
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10, context=context) as response:
                status_code = response.getcode()
                return status_code in [200, 301, 302]
                
        except Exception as e:
            print(f"❌ Ошибка проверки {url}: {e}")
            return False
    
    def test_all_youtube_domains(self) -> dict:
        """Test all YouTube domains"""
        print("🔍 Проверка доступности YouTube доменов...")
        
        domains = {
            "www.youtube.com": "Основной домен",
            "m.youtube.com": "Мобильная версия",
            "music.youtube.com": "YouTube Music",
            "youtube.com": "Без www",
            "www.youtubekids.com": "YouTube Kids",
            "www.youtube-nocookie.com": "Без cookie",
            "studio.youtube.com": "YouTube Studio",
            "tv.youtube.com": "YouTube TV"
        }
        
        results = {}
        for domain, description in domains.items():
            url = f"https://{domain}"
            accessible = self.test_youtube_accessibility(url)
            results[domain] = {
                "accessible": accessible,
                "description": description,
                "url": url
            }
            
            status = "✅ Доступен" if accessible else "❌ Заблокирован"
            print(f"   {status}: {domain} ({description})")
        
        return results
    
    def test_dpi_bypass_methods(self, target_host: str = "www.youtube.com") -> dict:
        """Test all DPI bypass methods"""
        print(f"\n🛡️ Тестирование DPI bypass методов для {target_host}...")
        
        # Test accessibility before bypass
        accessible_before = self.test_youtube_accessibility(f"https://{target_host}")
        print(f"📺 YouTube доступность ДО bypass: {'✅ Доступен' if accessible_before else '❌ Заблокирован'}")
        
        # All bypass methods to test (prioritize GoodbyeDPI and Zapret techniques)
        methods = [
            BypassMethod.PROTOCOL_MIMICKING,  # Now includes GoodbyeDPI + Zapret
            BypassMethod.DOMAIN_FRONTING,
            BypassMethod.TLS_SNI_SPLITTING,
            BypassMethod.FRAGMENTATION,
            BypassMethod.STEALTH_PORTS,
            BypassMethod.HTTP_HEADER_OBFUSCATION,
            BypassMethod.ENCODED_PAYLOAD
        ]
        
        results = {}
        successful_method = None
        
        for method in methods:
            print(f"\n🔄 Тестирование метода: {method.value}")
            
            config = BypassConfig(
                method=method,
                target_host=target_host,
                target_port=443,
                fragment_size=512,
                delay_ms=50
            )
            
            try:
                start_time = time.time()
                success = self.bypass_engine.bypass_dpi(config)
                end_time = time.time()
                
                # Test accessibility after this method
                accessible_after = self.test_youtube_accessibility(f"https://{target_host}")
                
                method_effective = (not accessible_before) and accessible_after
                
                results[method.value] = {
                    "success": success,
                    "effective": method_effective,
                    "time_taken": end_time - start_time,
                    "accessible_before": accessible_before,
                    "accessible_after": accessible_after
                }
                
                status = "✅ Успех" if success else "❌ Ошибка"
                effective = "🎯 Эффективен" if method_effective else "⚠️ Неэффективен"
                print(f"   {status}: {method.value} (время: {end_time - start_time:.2f}s)")
                print(f"   {effective}: {'Разблокировал' if method_effective else 'Не разблокировал'} YouTube")
                
                if method_effective:
                    successful_method = method.value
                    print(f"🎉 НАЙДЕН РАБОТАЮЩИЙ МЕТОД: {method.value}")
                    break
                    
            except Exception as e:
                print(f"   ❌ Ошибка метода {method.value}: {e}")
                results[method.value] = {
                    "success": False,
                    "effective": False,
                    "error": str(e),
                    "time_taken": 0,
                    "accessible_before": accessible_before,
                    "accessible_after": accessible_before
                }
        
        # Final accessibility test
        final_accessible = self.test_youtube_accessibility(f"https://{target_host}")
        print(f"\n📺 YouTube доступность ПОСЛЕ всех тестов: {'✅ Доступен' if final_accessible else '❌ Заблокирован'}")
        
        return {
            "target_host": target_host,
            "accessible_before": accessible_before,
            "accessible_after": final_accessible,
            "successful_method": successful_method,
            "bypass_effective": (not accessible_before) and final_accessible,
            "methods": results
        }
    
    def run_full_test(self) -> None:
        """Run complete DPI bypass test"""
        print("🚀 RSecure DPI Bypass Standalone Test")
        print("=" * 50)
        
        # Test all YouTube domains
        domain_results = self.test_all_youtube_domains()
        
        # Find best target (most accessible)
        accessible_domains = [d for d, info in domain_results.items() if info["accessible"]]
        
        if not accessible_domains:
            print("\n❌ ВСЕ YouTube домены заблокированы!")
            target_host = "www.youtube.com"  # Try anyway
        else:
            print(f"\n✅ Найдено {len(accessible_domains)} доступных доменов")
            target_host = accessible_domains[0]  # Use first accessible
            print(f"🎯 Целевой домен: {target_host}")
        
        # Test DPI bypass methods
        bypass_results = self.test_dpi_bypass_methods(target_host)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 ИТОГИ ТЕСТА")
        print("=" * 50)
        
        print(f"🎯 Цель: {bypass_results['target_host']}")
        print(f"📺 Доступность до: {'✅' if bypass_results['accessible_before'] else '❌'}")
        print(f"📺 Доступность после: {'✅' if bypass_results['accessible_after'] else '❌'}")
        print(f"🛡️ Успешный метод: {bypass_results['successful_method'] or 'Нет'}")
        print(f"🎯 Эффективность: {'✅ РАБОТАЕТ' if bypass_results['bypass_effective'] else '❌ НЕ РАБОТАЕТ'}")
        
        if bypass_results['successful_method']:
            print(f"\n🎉 DPI bypass РЕАЛЬНО РАЗБЛОКИРОВАЛ YouTube!")
            print(f"✅ Использован метод: {bypass_results['successful_method']}")
        else:
            print(f"\n❌ DPI bypass НЕ РАЗБЛОКИРОВАЛ YouTube")
            print("⚠️ Попробуйте другие методы или проверьте настройки сети")
        
        # Save results to file
        self.save_results(domain_results, bypass_results)
    
    def save_results(self, domain_results: dict, bypass_results: dict) -> None:
        """Save test results to JSON file"""
        try:
            import json
            from datetime import datetime
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "domain_accessibility": domain_results,
                "bypass_test": bypass_results
            }
            
            filename = f"dpi_bypass_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Результаты сохранены в: {filename}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")

def main():
    parser = argparse.ArgumentParser(description='RSecure DPI Bypass Standalone Test')
    parser.add_argument('--target', '-t', default='www.youtube.com', 
                       help='Целевой хост для теста (default: www.youtube.com)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Детальный вывод')
    
    args = parser.parse_args()
    
    tester = StandaloneDPIBypassTest()
    
    try:
        tester.run_full_test()
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
