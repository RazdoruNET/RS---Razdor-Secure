#!/usr/bin/env python3
"""
Запуск исправленного White-Ghost Proxy
Решение проблемы ERR_PROXY_CONNECTION_FAILED
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path


class FixedProxyLauncher:
    """Запускатель исправленного прокси"""
    
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.http_port = 8080
        self.socks_port = 1080
        self.proxy_process = None
        
        # Импортируем настройщик HTTP прокси
        sys.path.insert(0, os.path.dirname(__file__))
        try:
            from setup_http_proxy import HTTPProxySetup
            self.http_setup = HTTPProxySetup()
        except ImportError:
            print("❌ Не удалось импортировать HTTPProxySetup")
            sys.exit(1)
    
    def check_admin_rights(self):
        """Проверка прав администратора"""
        try:
            result = subprocess.run([
                "networksetup", "-listallnetworkservices"
            ], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def start_fixed_proxy(self):
        """Запуск исправленного прокси"""
        try:
            print("🚀 Запускаю исправленный White-Ghost Proxy...")
            
            proxy_script = os.path.join(os.path.dirname(__file__), 'white_ghost_proxy_fixed.py')
            
            self.proxy_process = subprocess.Popen([
                sys.executable, proxy_script,
                '--http-port', str(self.http_port),
                '--socks-port', str(self.socks_port)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Ждем запуска
            time.sleep(3)
            
            if self.proxy_process.poll() is None:
                print("✅ Исправленный прокси запущен")
                return True
            else:
                print("❌ Не удалось запустить прокси")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска прокси: {e}")
            return False
    
    def setup_http_proxy_system(self):
        """Настройка системного HTTP прокси"""
        try:
            print("🔧 Настраиваю системный HTTP прокси...")
            
            # Сохраняем текущие настройки
            if not self.http_setup.backup_current_settings():
                print("❌ Не удалось сохранить настройки")
                return False
            
            # Настраиваем HTTP прокси
            if not self.http_setup.setup_http_proxy():
                print("❌ Не удалось настроить HTTP прокси")
                return False
            
            print("✅ Системный HTTP прокси настроен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки HTTP прокси: {e}")
            return False
    
    def verify_setup(self):
        """Проверка настройки"""
        print("🧪 Проверяю настройку...")
        
        # Проверяем статус
        self.http_setup.get_status()
        
        # Тестируем HTTP прокси
        if self.http_setup.test_http_proxy():
            print("✅ HTTP прокси работает корректно")
            return True
        else:
            print("❌ HTTP прокси не работает")
            return False
    
    def show_instructions(self):
        """Показ инструкций"""
        print("\n📋 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ:")
        print("=" * 50)
        print("🎯 ИСПРАВЛЕННЫЙ ПРОКСИ ЗАПУЩЕН!")
        print("🌐 Используется HTTP прокси вместо SOCKS5")
        print("🔧 Это решает проблему ERR_PROXY_CONNECTION_FAILED")
        print()
        print("📊 Настройки:")
        print(f"   🌐 HTTP прокси: {self.proxy_host}:{self.http_port}")
        print(f"   🧦 SOCKS5 прокси: {self.proxy_host}:{self.socks_port}")
        print()
        print("🌐 Браузеры должны работать без ошибок:")
        print("   • Safari (использует системные настройки)")
        print("   • Chrome (использует системные настройки)")
        print("   • Firefox (настроить вручную HTTP прокси)")
        print()
        print("🔍 Проверка:")
        print("   • Откройте https://www.youtube.com")
        print("   • Откройте https://httpbin.org/ip")
        print("   • ERR_PROXY_CONNECTION_FAILED должно исчезнуть")
        print()
        print("⏹️ Остановка:")
        print("   • Нажмите Ctrl+C здесь")
        print("   • Или запустите: python3 start_fixed_proxy.py --stop")
        print()
        print("📋 Firefox ручная настройка:")
        print("   • Настройки → Общие → Параметры сети")
        print("   • Ручная настройка прокси")
        print("   • HTTP прокси: 127.0.0.1, порт 8080")
        print("   • HTTPS прокси: 127.0.0.1, порт 8080")
    
    def stop_all(self):
        """Полная остановка"""
        print("\n⏹️ Останавливаю исправленный прокси...")
        
        # Останавливаем прокси
        if self.proxy_process:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
                print("✅ Прокси остановлен")
            except subprocess.TimeoutExpired:
                print("⚠️ Принудительная остановка прокси...")
                self.proxy_process.kill()
                self.proxy_process.wait()
            except:
                pass
            finally:
                self.proxy_process = None
        
        # Восстанавливаем системные настройки
        if self.http_setup:
            try:
                self.http_setup.restore_settings()
                print("✅ Системные настройки восстановлены")
            except:
                print("⚠️ Не удалось восстановить настройки")
        
        print("🏁 Исправленный прокси остановлен")
    
    def run(self):
        """Основной запуск"""
        print("🔧 ИСПРАВЛЕННЫЙ WHITE-GHOST PROXY")
        print("=" * 50)
        print("🎯 Решение проблемы ERR_PROXY_CONNECTION_FAILED")
        print("🌐 Используем HTTP прокси вместо SOCKS5")
        print()
        
        # Проверка прав администратора
        if not self.check_admin_rights():
            print("❌ Требуются права администратора!")
            print("📝 Запустите с sudo:")
            print(f"   sudo python3 {sys.argv[0]}")
            sys.exit(1)
        
        print("✅ Права администратора подтверждены")
        
        # Запуск исправленного прокси
        if not self.start_fixed_proxy():
            sys.exit(1)
        
        # Настройка системного HTTP прокси
        if not self.setup_http_proxy_system():
            self.stop_all()
            sys.exit(1)
        
        # Проверка настройки
        if not self.verify_setup():
            print("⚠️ Настройка не прошла проверку, но продолжаем...")
        
        # Показываем инструкции
        self.show_instructions()
        
        # Ожидание сигнала остановки
        try:
            print("\n⏹️ Нажмите Ctrl+C для остановки...")
            while self.proxy_process and self.proxy_process.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Получен сигнал остановки")
        finally:
            self.stop_all()
        
        return True


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Исправленный White-Ghost Proxy')
    parser.add_argument('--stop', action='store_true', help='Остановить и восстановить')
    parser.add_argument('--status', action='store_true', help='Показать статус')
    parser.add_argument('--test', action='store_true', help='Тестировать прокси')
    parser.add_argument('--host', default='127.0.0.1', help='Хост прокси')
    parser.add_argument('--http-port', type=int, default=8080, help='Порт HTTP прокси')
    parser.add_argument('--socks-port', type=int, default=1080, help='Порт SOCKS5 прокси')
    
    args = parser.parse_args()
    
    if args.stop:
        print("⏹️ Останавливаю исправленный прокси...")
        try:
            from setup_http_proxy import HTTPProxySetup
            setup = HTTPProxySetup()
            setup.restore_settings()
            
            # Останавливаем процессы
            subprocess.run(["pkill", "-f", "white_ghost_proxy_fixed.py"], check=False)
            
            print("✅ Исправленный прокси остановлен")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return
    
    if args.status:
        try:
            from setup_http_proxy import HTTPProxySetup
            setup = HTTPProxySetup()
            setup.get_status()
            setup.test_http_proxy()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return
    
    if args.test:
        try:
            from setup_http_proxy import HTTPProxySetup
            setup = HTTPProxySetup()
            setup.test_http_proxy()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return
    
    # Запуск исправленного прокси
    launcher = FixedProxyLauncher()
    launcher.proxy_host = args.host
    launcher.http_port = args.http_port
    launcher.socks_port = args.socks_port
    
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n⏹️ Прерывание пользователем")
        launcher.stop_all()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        launcher.stop_all()


if __name__ == "__main__":
    main()
