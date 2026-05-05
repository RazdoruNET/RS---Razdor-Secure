#!/usr/bin/env python3
"""
Полный тест DPI bypass с Tor-Core интеграцией
Включает все методы обхода и автоматическое переключение на Darknet
"""
import sys
import os
import time
import json
from datetime import datetime
sys.path.append('.')
sys.path.append('./rsecure')

class DPIBypassCompleteTest:
    """Полный тест DPI bypass с Tor-Core"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        
    def test_youtube_domains(self) -> dict:
        """Проверка доступности YouTube доменов"""
        print("🔍 Проверка доступности YouTube доменов...")
        
        import urllib.request
        import ssl
        
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
        accessible_count = 0
        
        for domain, description in domains.items():
            try:
                url = f"https://{domain}"
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                
                with urllib.request.urlopen(request, timeout=10, context=context) as response:
                    if response.status == 200:
                        results[domain] = {
                            "accessible": True,
                            "description": description,
                            "url": url
                        }
                        accessible_count += 1
                        print(f"   ✅ Доступен: {domain} ({description})")
                    else:
                        results[domain] = {
                            "accessible": False,
                            "description": description,
                            "url": url
                        }
                        print(f"   ❌ Заблокирован: {domain} ({description})")
                        
            except Exception as e:
                results[domain] = {
                    "accessible": False,
                    "description": description,
                    "url": f"https://{domain}",
                    "error": str(e)
                }
                print(f"   ❌ Ошибка проверки {url}: {e}")
        
        print(f"✅ Найдено {accessible_count} доступных доменов")
        return results
    
    def test_tor_core_integration(self) -> dict:
        """Тестирование Tor-Core интеграции"""
        print("\n🧬 Тестирование Tor-Core интеграции...")
        
        try:
            from rsecure.modules.defense.tor_core_integration import tor_core, activate_darknet_bridge, get_youtube_through_tor, automatic_tor_fallback
            
            # Активация Darknet моста
            print("🌐 Активация Darknet моста...")
            activate_result = activate_darknet_bridge()
            print(f"   {activate_result}")
            
            # Получение YouTube через Tor
            print("📺 Получение YouTube через Tor...")
            youtube_result = get_youtube_through_tor()
            print(f"   Результат: {youtube_result}")
            
            # Автоматическое переключение
            print("🔄 Автоматическое переключение на Tor...")
            auto_result = automatic_tor_fallback("https://www.youtube.com")
            print(f"   Результат: {auto_result}")
            
            # Статус Tor
            print("📊 Статус Tor соединения...")
            status = tor_core.get_tor_status()
            print(f"   Статус: {status}")
            
            return {
                "success": True,
                "activate_result": activate_result,
                "youtube_result": youtube_result,
                "auto_result": auto_result,
                "tor_status": status
            }
            
        except Exception as e:
            print(f"❌ Tor-Core интеграция не сработала: {e}")
            return {"success": False, "error": str(e)}
    
    def test_dpi_bypass_methods(self, target_host: str = "www.youtube.com") -> dict:
        """Тестирование всех DPI bypass методов"""
        print(f"\n🛡️ Тестирование DPI bypass методов для {target_host}...")
        
        try:
            from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod
            
            # Проверка доступности до bypass
            accessible_before = self._check_youtube_accessibility(f"https://{target_host}")
            print(f"📺 YouTube доступность ДО bypass: {'✅ Доступен' if accessible_before else '❌ Заблокирован'}")
            
            # Все методы для тестирования
            methods = [
                BypassMethod.PROTOCOL_MIMICKING,  # Теперь включает Tor-Core
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
                
                start_time = time.time()
                try:
                    # Создаем конфигурацию
                    config = BypassConfig(
                        method=method,
                        target_host=target_host,
                        target_port=443
                    )
                    
                    # Запускаем bypass
                    engine = DPIBypassEngine()
                    bypass_result = engine.bypass_dpi(config)
                    
                    end_time = time.time()
                    time_taken = end_time - start_time
                    
                    # Проверяем доступность после bypass
                    accessible_after = self._check_youtube_accessibility(f"https://{target_host}")
                    
                    results[method.value] = {
                        "success": bypass_result,
                        "effective": bypass_result and accessible_after and not accessible_before,
                        "time_taken": time_taken,
                        "accessible_before": accessible_before,
                        "accessible_after": accessible_after
                    }
                    
                    if bypass_result:
                        print(f"   ✅ Успех: {method.value} (время: {time_taken:.2f}s)")
                        if accessible_after and not accessible_before:
                            print(f"   🎯 Эффективен: Разблокировал YouTube!")
                            successful_method = method.value
                        else:
                            print(f"   ⚠️ Неэффективен: Не разблокировал YouTube")
                    else:
                        print(f"   ❌ Ошибка: {method.value} (время: {time_taken:.2f}s)")
                        print(f"   ⚠️ Неэффективен: Не разблокировал YouTube")
                        
                except Exception as e:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    
                    results[method.value] = {
                        "success": False,
                        "effective": False,
                        "time_taken": time_taken,
                        "accessible_before": accessible_before,
                        "accessible_after": accessible_before,
                        "error": str(e)
                    }
                    print(f"   ❌ Ошибка: {method.value} (время: {time_taken:.2f}s)")
                    print(f"   ⚠️ Неэффективен: Не разблокирован YouTube")
            
            # Финальная проверка
            accessible_final = self._check_youtube_accessibility(f"https://{target_host}")
            print(f"\n📺 YouTube доступность ПОСЛЕ всех тестов: {'✅ Доступен' if accessible_final else '❌ Заблокирован'}")
            
            return {
                "target_host": target_host,
                "accessible_before": accessible_before,
                "accessible_after": accessible_final,
                "successful_method": successful_method,
                "bypass_effective": successful_method is not None,
                "methods": results
            }
            
        except Exception as e:
            print(f"❌ Ошибка тестирования DPI bypass: {e}")
            return {"error": str(e)}
    
    def _check_youtube_accessibility(self, url: str) -> bool:
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
    
    def generate_report(self, domain_results: dict, tor_results: dict, bypass_results: dict) -> dict:
        """Генерация полного отчета"""
        timestamp = datetime.now().isoformat()
        
        report = {
            "timestamp": timestamp,
            "test_duration": str(datetime.now() - self.start_time),
            "domain_accessibility": domain_results,
            "tor_core_integration": tor_results,
            "bypass_test": bypass_results
        }
        
        # Сохранение в файл
        filename = f"dpi_bypass_complete_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Полный отчет сохранен в: {filename}")
        return report
    
    def print_summary(self, report: dict):
        """Вывод итогов теста"""
        print("\n" + "=" * 60)
        print("📊 ПОЛНЫЕ ИТОГИ ТЕСТА DPI BYPASS С TOR-CORE")
        print("=" * 60)
        
        # Статистика доменов
        domains = report["domain_accessibility"]
        accessible_domains = sum(1 for d in domains.values() if d.get("accessible", False))
        total_domains = len(domains)
        
        print(f"🌐 YouTube домены: {accessible_domains}/{total_domains} доступны")
        
        # Tor-Core статус
        tor_success = report["tor_core_integration"].get("success", False)
        print(f"🧬 Tor-Core интеграция: {'✅ УСПЕХ' if tor_success else '❌ ОШИБКА'}")
        
        # DPI bypass результаты
        bypass_test = report.get("bypass_test", {})
        if bypass_test:
            target = bypass_test.get("target_host", "unknown")
            effective = bypass_test.get("bypass_effective", False)
            successful_method = bypass_test.get("successful_method")
            
            print(f"🎯 Цель: {target}")
            print(f"🛡️ Эффективность: {'✅ РАБОТАЕТ' if effective else '❌ НЕ РАБОТАЕТ'}")
            
            if successful_method:
                print(f"🏆 Успешный метод: {successful_method}")
            else:
                print("❌ Успешный метод не найден")
        
        # Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ:")
        if accessible_domains == 0:
            print("   🌐 Все YouTube домены заблокированы - используйте Tor-Core")
        elif accessible_domains < total_domains:
            print(f"   🔄 {total_domains - accessible_domains} доменов заблокированы - попробуйте альтернативные")
        else:
            print("   ✅ YouTube доступен - DPI bypass не требуется")
        
        if not tor_success:
            print("   🧬 Установите Tor или запустите Tor Browser для Darknet доступа")
        
        if not bypass_test.get("bypass_effective", False):
            print("   🛡️ Попробуйте другие методы обхода или проверьте настройки сети")
    
    def run_complete_test(self, target_host: str = "www.youtube.com"):
        """Запуск полного теста"""
        print("🚀 RSecure DPI Bypass Complete Test with Tor-Core")
        print("=" * 60)
        
        # Тест 1: Доступность доменов
        domain_results = self.test_youtube_domains()
        
        # Тест 2: Tor-Core интеграция
        tor_results = self.test_tor_core_integration()
        
        # Тест 3: DPI bypass методы
        bypass_results = self.test_dpi_bypass_methods(target_host)
        
        # Генерация отчета
        report = self.generate_report(domain_results, tor_results, bypass_results)
        
        # Вывод итогов
        self.print_summary(report)
        
        return report

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Полный тест DPI bypass с Tor-Core')
    parser.add_argument('--target', default='www.youtube.com', help='Целевой хост для теста')
    parser.add_argument('--verbose', action='store_true', help='Детальный вывод')
    
    args = parser.parse_args()
    
    # Запуск теста
    tester = DPIBypassCompleteTest()
    results = tester.run_complete_test(args.target)
    
    return results

if __name__ == "__main__":
    main()
