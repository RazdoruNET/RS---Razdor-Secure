#!/usr/bin/env python3
"""
Полный системный прокси White-Ghost
Настраивает ВЕСЬ трафик компьютера через White-Ghost Proxy
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path


class FullSystemProxyLauncher:
    """Запускатель полного системного прокси"""
    
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 1080
        self.proxy_process = None
        self.system_manager = None
        
        # Импортируем менеджер системного прокси
        sys.path.insert(0, os.path.dirname(__file__))
        try:
            from system_proxy_manager import SystemProxyManager
            self.system_manager = SystemProxyManager()
        except ImportError:
            print("❌ Не удалось импортировать SystemProxyManager")
            sys.exit(1)
    
    def check_admin_rights(self):
        """Проверка прав администратора"""
        try:
            # Пробуем выполнить команду, требующую прав
            result = subprocess.run([
                "networksetup", "-listallnetworkservices"
            ], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def start_proxy_server(self):
        """Запуск SOCKS5 прокси сервера"""
        try:
            print("🚀 Запускаю White-Ghost SOCKS5 прокси...")
            
            proxy_script = os.path.join(os.path.dirname(__file__), 'white_ghost_proxy.py')
            
            self.proxy_process = subprocess.Popen([
                sys.executable, proxy_script,
                '--host', self.proxy_host,
                '--port', str(self.proxy_port)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Ждем запуска
            time.sleep(3)
            
            if self.proxy_process.poll() is None:
                print("✅ SOCKS5 прокси запущен")
                return True
            else:
                print("❌ Не удалось запустить SOCKS5 прокси")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска прокси: {e}")
            return False
    
    def setup_system_proxy(self):
        """Настройка системного прокси для ВСЕГО трафика"""
        try:
            print("🔧 Настраиваю системный прокси для ВСЕГО трафика...")
            
            # Сохраняем текущие настройки
            if not self.system_manager.backup_current_settings():
                print("❌ Не удалось сохранить настройки")
                return False
            
            # Настраиваем полный системный прокси
            if not self.system_manager.setup_full_system_proxy():
                print("❌ Не удалось настроить системный прокси")
                return False
            
            print("✅ Системный прокси настроен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки системного прокси: {e}")
            return False
    
    def verify_setup(self):
        """Проверка настройки"""
        print("🧪 Проверяю настройку...")
        
        # Проверяем статус прокси
        self.system_manager.get_proxy_status()
        
        # Тестируем соединение
        if self.system_manager.test_proxy_connection():
            print("✅ Прокси работает корректно")
            return True
        else:
            print("❌ Прокси не работает")
            return False
    
    def show_instructions(self):
        """Показ инструкций"""
        print("\n📋 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ:")
        print("=" * 50)
        print("🎯 ВЕСЬ трафик компьютера теперь идет через White-Ghost!")
        print("🌐 Все приложения (браузеры, мессенджеры, игры) используют прокси")
        print("📺 YouTube и другие сайты будут работать через обход")
        print()
        print("🔍 Проверка:")
        print("   • Откройте https://www.youtube.com")
        print("   • Откройте https://httpbin.org/ip")
        print("   • Проверьте IP адрес - должен отличаться")
        print()
        print("⏹️ Остановка:")
        print("   • Нажмите Ctrl+C здесь")
        print("   • Или запустите: python3 start_full_system_proxy.py --stop")
        print()
        print("⚠️ ВАЖНО:")
        print("   • Все сетевые соединения идут через прокси")
        print("   • Скорость может быть ниже обычной")
        print("   • Некоторые приложения могут потребовать перезапуска")
    
    def stop_all(self):
        """Полная остановка"""
        print("\n⏹️ Останавливаю полный системный прокси...")
        
        # Останавливаем SOCKS5 прокси
        if self.proxy_process:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
                print("✅ SOCKS5 прокси остановлен")
            except subprocess.TimeoutExpired:
                print("⚠️ Принудительная остановка прокси...")
                self.proxy_process.kill()
                self.proxy_process.wait()
            except:
                pass
            finally:
                self.proxy_process = None
        
        # Восстанавливаем системные настройки
        if self.system_manager:
            try:
                self.system_manager.restore_all_settings()
                print("✅ Системные настройки восстановлены")
            except:
                print("⚠️ Не удалось восстановить настройки")
        
        print("🏁 Полный системный прокси остановлен")
    
    def run(self):
        """Основной запуск"""
        print("🌐 ПОЛНЫЙ СИСТЕМНЫЙ ПРОКСИ WHITE-GHOST")
        print("=" * 50)
        print("⚠️ ВНИМАНИЕ: ВЕСЬ трафик компьютера будет идти через прокси!")
        print()
        
        # Проверка прав администратора
        if not self.check_admin_rights():
            print("❌ Требуются права администратора!")
            print("📝 Запустите с sudo:")
            print(f"   sudo python3 {sys.argv[0]}")
            sys.exit(1)
        
        print("✅ Права администратора подтверждены")
        
        # Запуск SOCKS5 прокси
        if not self.start_proxy_server():
            sys.exit(1)
        
        # Настройка системного прокси
        if not self.setup_system_proxy():
            self.stop_all()
            sys.exit(1)
        
        # Проверка настройки
        if not self.verify_setup():
            print("⚠️ Настройка не прошла проверку, но продолжаю...")
        
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
    parser = argparse.ArgumentParser(description='Полный системный прокси White-Ghost')
    parser.add_argument('--stop', action='store_true', help='Остановить и восстановить')
    parser.add_argument('--status', action='store_true', help='Показать статус')
    parser.add_argument('--test', action='store_true', help='Тестировать прокси')
    parser.add_argument('--host', default='127.0.0.1', help='Хост прокси')
    parser.add_argument('--port', type=int, default=1080, help='Порт прокси')
    
    args = parser.parse_args()
    
    if args.stop:
        print("⏹️ Останавливаю полный системный прокси...")
        try:
            from system_proxy_manager import SystemProxyManager
            manager = SystemProxyManager()
            manager.restore_all_settings()
            
            # Останавливаем процессы
            subprocess.run(["pkill", "-f", "white_ghost_proxy.py"], check=False)
            
            print("✅ Системный прокси остановлен")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return
    
    if args.status:
        try:
            from system_proxy_manager import SystemProxyManager
            manager = SystemProxyManager()
            manager.get_proxy_status()
            manager.test_proxy_connection()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return
    
    if args.test:
        try:
            from system_proxy_manager import SystemProxyManager
            manager = SystemProxyManager()
            manager.test_proxy_connection()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        return
    
    # Запуск полного системного прокси
    launcher = FullSystemProxyLauncher()
    launcher.proxy_host = args.host
    launcher.proxy_port = args.port
    
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
