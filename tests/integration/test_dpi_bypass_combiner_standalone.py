#!/usr/bin/env python3
"""
DPI Bypass Combiner - Standalone Test Program
Автоматический тест всех техник обхода с отключенным VPN
"""
import sys
import os
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, Any

# Добавляем пути для импорта
sys.path.append('.')
sys.path.append('./rsecure')

def check_vpn_status():
    """Проверка статуса VPN"""
    print("🔍 Проверка статуса VPN...")
    
    try:
        # Проверяем VPN на macOS
        if sys.platform == "darwin":
            # Проверяем активные VPN соединения
            result = subprocess.run(["scutil", "--nc", "list"], 
                                  capture_output=True, text=True, timeout=10)
            
            if "Connected" in result.stdout:
                print("   ⚠️ VPN ОБНАРУЖЕН - рекомендуется отключить")
                print("   📝 Используйте: scutil --nc stop [VPN_NAME]")
                return True
            else:
                print("   ✅ VPN не обнаружен")
                return False
                
        elif sys.platform == "linux":
            # Проверяем tun/tap интерфейсы
            result = subprocess.run(["ip", "link", "show"], 
                                  capture_output=True, text=True, timeout=10)
            
            if "tun" in result.stdout or "tap" in result.stdout:
                print("   ⚠️ VPN ОБНАРУЖЕН - рекомендуется отключить")
                return True
            else:
                print("   ✅ VPN не обнаружен")
                return False
                
        elif sys.platform == "win32":
            # Проверяем VPN адаптеры
            result = subprocess.run(["netsh", "interface", "show", "interface"], 
                                  capture_output=True, text=True, timeout=10)
            
            if "VPN" in result.stdout and "Connected" in result.stdout:
                print("   ⚠️ VPN ОБНАРУЖЕН - рекомендуется отключить")
                return True
            else:
                print("   ✅ VPN не обнаружен")
                return False
                
    except Exception as e:
        print(f"   ⚠️ Не удалось проверить VPN: {e}")
        return False
    
    return False

def check_internet_connection():
    """Проверка интернет соединения"""
    print("🌐 Проверка интернет соединения...")
    
    try:
        import urllib.request
        import ssl
        
        # Проверяем доступ к Google
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request("https://www.google.com")
        request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        with urllib.request.urlopen(request, timeout=10, context=context) as response:
            if response.status == 200:
                print("   ✅ Интернет доступен")
                return True
            else:
                print(f"   ❌ Проблема с интернетом: {response.status}")
                return False
                
    except Exception as e:
        print(f"   ❌ Ошибка интернет соединения: {e}")
        return False

def check_youtube_blocking():
    """Проверка блокировки YouTube"""
    print("📺 Проверка блокировки YouTube...")
    
    youtube_domains = [
        "www.youtube.com",
        "m.youtube.com", 
        "music.youtube.com",
        "youtube.com"
    ]
    
    blocked_count = 0
    accessible_count = 0
    
    for domain in youtube_domains:
        try:
            import urllib.request
            import ssl
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            request = urllib.request.Request(f"https://{domain}")
            request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            with urllib.request.urlopen(request, timeout=5, context=context) as response:
                if response.status == 200:
                    print(f"   ✅ {domain}: Доступен")
                    accessible_count += 1
                else:
                    print(f"   ❌ {domain}: Заблокирован ({response.status})")
                    blocked_count += 1
                    
        except Exception as e:
            print(f"   ❌ {domain}: Заблокирован ({str(e)[:50]}...)")
            blocked_count += 1
    
    print(f"   📊 Статистика: {accessible_count} доступно, {blocked_count} заблокировано")
    
    return blocked_count > 0

def run_dpi_bypass_test(target_host: str = "www.youtube.com"):
    """Запуск теста DPI bypass"""
    print("\n🚀 Запуск DPI Bypass Combiner теста")
    print("=" * 60)
    
    try:
        # Импортируем комбайн
        from rsecure.modules.defense.dpi_bypass_combiner import run_dpi_bypass_combiner, dpi_combiner
        
        print("✅ DPI Bypass Combiner импортирован")
        
        # Запускаем автоматический обход
        report = run_dpi_bypass_combiner(target_host)
        
        # Генерируем отчет
        print("\n" + dpi_combiner.generate_report(report))
        
        return report
        
    except Exception as e:
        print(f"❌ Критическая ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_test_report(report: Dict[str, Any], filename: str = None):
    """Сохранение отчета о тесте"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dpi_bypass_combiner_test_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Отчет сохранен: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Ошибка сохранения отчета: {e}")
        return None

def generate_test_summary(report: Dict[str, Any]) -> str:
    """Генерация краткой сводки теста"""
    lines = []
    lines.append("📊 СВОДКА ТЕСТА DPI BYPASS COMBINER")
    lines.append("=" * 40)
    lines.append(f"🎯 Цель: {report['target_host']}")
    lines.append(f"⏰ Время: {report['timestamp']}")
    lines.append("")
    
    # Статус
    if report['bypass_successful']:
        lines.append("🎉 РЕЗУЛЬТАТ: УСПЕХ - YouTube РАЗБЛОКИРОВАН!")
        lines.append(f"🏆 Техника: {report.get('effective_technique', 'Unknown')}")
    else:
        lines.append("❌ РЕЗУЛЬТАТ: НЕУДАЧА - YouTube НЕ РАЗБЛОКИРОВАН")
        if report.get('successful_technique'):
            lines.append(f"⚠️ Техника сработала, но не эффективна: {report['successful_technique']}")
    
    lines.append("")
    lines.append("📈 Статистика:")
    lines.append(f"   🔄 Техник протестировано: {report['total_techniques_tried']}")
    lines.append(f"   ⏱️ Общее время: {report['total_duration']:.2f}s")
    lines.append(f"   📺 Доступность ДО: {'✅' if report['accessibility_before']['accessible'] else '❌'}")
    lines.append(f"   📺 Доступность ПОСЛЕ: {'✅' if report['accessibility_after']['accessible'] else '❌'}")
    
    lines.append("")
    lines.append("🔧 РЕКОМЕНДАЦИИ:")
    
    if report['bypass_successful']:
        lines.append("   ✅ Используйте найденную эффективную технику")
        lines.append("   🔄 Для автоматического использования настройте систему")
    else:
        lines.append("   🔍 Проверьте настройки сети и файрвола")
        lines.append("   🌐 Убедитесь что VPN отключен")
        lines.append("   🛠️ Попробуйте другие техники или обновите систему")
    
    return "\n".join(lines)

def main():
    """Главная функция"""
    print("🛡️ DPI Bypass Combiner - Standalone Test Program")
    print("=" * 60)
    print("🎯 Автоматический тест всех техник обхода DPI")
    print("⚠️  Рекомендуется отключить VPN перед запуском")
    print("")
    
    # Проверяем VPN статус
    vpn_detected = check_vpn_status()
    
    if vpn_detected:
        print("\n⚠️ ВНИМАНИЕ: VPN ОБНАРУЖЕН!")
        print("Для корректного теста рекомендуется отключить VPN")
        print("")
        
        response = input("Продолжить тест с VPN? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Тест отменен. Отключите VPN и запустите снова.")
            return
    
    # Проверяем интернет соединение
    if not check_internet_connection():
        print("❌ Тест невозможен - нет интернет соединения")
        return
    
    # Проверяем блокировку YouTube
    youtube_blocked = check_youtube_blocking()
    
    if not youtube_blocked:
        print("\n✅ YouTube доступен - DPI bypass не требуется")
        print("🎯 Тест все равно будет выполнен для проверки техник")
        print("")
        
        response = input("Продолжить тест? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Тест отменен")
            return
    
    # Определяем цель
    target = "www.youtube.com"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"🎯 Использована цель из аргументов: {target}")
    else:
        print(f"🎯 Цель по умолчанию: {target}")
    
    # Запускаем тест
    print(f"\n🚀 НАЧИНАЮ ТЕСТ DPI BYPASS ДЛЯ {target}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        report = run_dpi_bypass_test(target)
        
        if report:
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n⏱️ Общее время теста: {total_time:.2f}s")
            
            # Выводим сводку
            print("\n" + generate_test_summary(report))
            
            # Сохраняем отчеты
            json_file = save_test_report(report)
            
            # Сохраняем текстовую сводку
            if json_file:
                txt_file = json_file.replace('.json', '_summary.txt')
                try:
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write(generate_test_summary(report))
                        f.write("\n\n")
                        f.write(dpi_combiner.generate_report(report))
                    print(f"📄 Сводка сохранена: {txt_file}")
                except:
                    pass
            
            # Финальный результат
            if report['bypass_successful']:
                print("\n🎉 ТЕСТ УСПЕШЕН ЗАВЕРШЕН!")
                print("🏆 YouTube разблокирован через DPI bypass!")
            else:
                print("\n❌ ТЕСТ ЗАВЕРШЕН БЕЗ УСПЕХА")
                print("🔧 Попробуйте другие техники или проверьте настройки")
            
        else:
            print("\n❌ Тест не удался из-за критической ошибки")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Завершение программы")

if __name__ == "__main__":
    main()
