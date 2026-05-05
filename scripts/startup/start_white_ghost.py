#!/usr/bin/env python3
"""
Скрипт для запуска White-Ghost Proxy и настройки браузера
Автоматически настраивает системный прокси и открывает YouTube
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path


class WhiteGhostLauncher:
    """Запускатель White-Ghost Proxy"""
    
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 1080
        self.proxy_process = None
        self.original_proxy_settings = None
        
    def check_dependencies(self):
        """Проверка зависимостей"""
        print("🔍 Проверка зависимостей...")
        
        # Проверяем Python
        if sys.version_info < (3, 6):
            print("❌ Требуется Python 3.6+")
            return False
        
        # Проверяем наличие модуля
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure/modules/defense'))
            from dpi_bypass_combiner import DPIBypassCombiner
            print("✅ DPI-Bypass Combiner найден")
        except ImportError as e:
            print(f"❌ Ошибка импорта DPI-Bypass Combiner: {e}")
            return False
        
        return True
    
    def backup_proxy_settings(self):
        """Сохранение текущих настроек прокси"""
        try:
            print("💾 Сохраняю текущие настройки прокси...")
            
            # Получаем текущие настройки прокси macOS
            result = subprocess.run([
                'networksetup', '-getwebproxy', 'Wi-Fi'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.original_proxy_settings = result.stdout
                print("✅ Настройки прокси сохранены")
                return True
            else:
                print("⚠️ Не удалось получить настройки прокси")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
            return False
    
    def restore_proxy_settings(self):
        """Восстановление настроек прокси"""
        if not self.original_proxy_settings:
            return
            
        try:
            print("🔄 Восстанавливаю настройки прокси...")
            
            # Отключаем прокси
            subprocess.run([
                'networksetup', '-setwebproxystate', 'Wi-Fi', 'off'
            ], check=False)
            
            subprocess.run([
                'networksetup', '-setsecurewebproxystate', 'Wi-Fi', 'off'
            ], check=False)
            
            print("✅ Настройки прокси восстановлены")
            
        except Exception as e:
            print(f"❌ Ошибка восстановления настроек: {e}")
    
    def setup_system_proxy(self):
        """Настройка системного прокси"""
        try:
            print("🔧 Настраиваю системный прокси...")
            
            # Настраиваем HTTP прокси
            subprocess.run([
                'networksetup', '-setwebproxy', 'Wi-Fi',
                self.proxy_host, str(self.proxy_port)
            ], check=True)
            
            # Настраиваем HTTPS прокси
            subprocess.run([
                'networksetup', '-setsecurewebproxy', 'Wi-Fi',
                self.proxy_host, str(self.proxy_port)
            ], check=True)
            
            # Включаем прокси
            subprocess.run([
                'networksetup', '-setwebproxystate', 'Wi-Fi', 'on'
            ], check=True)
            
            subprocess.run([
                'networksetup', '-setsecurewebproxystate', 'Wi-Fi', 'on'
            ], check=True)
            
            print(f"✅ Системный прокси настроен: {self.proxy_host}:{self.proxy_port}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка настройки прокси: {e}")
            print("⚠️ Попробуйте запустить с sudo или настройте прокси вручную")
            return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def start_proxy(self):
        """Запуск White-Ghost прокси"""
        try:
            print("🚀 Запускаю White-Ghost Proxy...")
            
            # Запускаем прокси в отдельном процессе
            proxy_script = os.path.join(os.path.dirname(__file__), 'white_ghost_proxy.py')
            
            self.proxy_process = subprocess.Popen([
                sys.executable, proxy_script,
                '--host', self.proxy_host,
                '--port', str(self.proxy_port)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Ждем запуска прокси
            time.sleep(2)
            
            if self.proxy_process.poll() is None:
                print("✅ White-Ghost Proxy запущен")
                return True
            else:
                print("❌ Не удалось запустить прокси")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска прокси: {e}")
            return False
    
    def open_browser(self, url="https://www.youtube.com"):
        """Открытие браузера с YouTube"""
        try:
            print(f"🌐 Открываю {url} в браузере...")
            
            # Используем системную команду для открытия браузера
            subprocess.run(['open', url], check=True)
            
            print("✅ Браузер открыт")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка открытия браузера: {e}")
            return False
    
    def show_status(self):
        """Показ статуса прокси"""
        print("\n📊 СТАТУС WHITE-GHOST PROXY:")
        print("=" * 40)
        print(f"🌐 Прокси: {self.proxy_host}:{self.proxy_port}")
        print(f"🔄 Процесс: {'Запущен' if self.proxy_process and self.proxy_process.poll() is None else 'Остановлен'}")
        
        if self.proxy_process and self.proxy_process.poll() is None:
            print("✅ Прокси активен и готов к работе")
        else:
            print("❌ Прокси не запущен")
        
        print("\n🎯 Домены для обхода:")
        domains = [
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'youtu.be', 'ytimg.com', 'googlevideo.com',
            'googleapis.com', 'gstatic.com', 'ggpht.com'
        ]
        for domain in domains:
            print(f"   • {domain}")
    
    def stop_proxy(self):
        """Остановка прокси"""
        if self.proxy_process:
            try:
                print("⏹️ Останавливаю White-Ghost Proxy...")
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
                print("✅ Прокси остановлен")
            except subprocess.TimeoutExpired:
                print("⚠️ Принудительная остановка прокси...")
                self.proxy_process.kill()
                self.proxy_process.wait()
            except Exception as e:
                print(f"❌ Ошибка остановки: {e}")
            finally:
                self.proxy_process = None
    
    def run(self, setup_system=True, open_browser=True):
        """Основной запуск"""
        print("👻 White-Ghost Proxy Launcher")
        print("=" * 40)
        
        # Проверка зависимостей
        if not self.check_dependencies():
            return False
        
        # Сохранение настроек
        if setup_system:
            self.backup_proxy_settings()
        
        # Запуск прокси
        if not self.start_proxy():
            return False
        
        # Настройка системного прокси
        if setup_system:
            if not self.setup_system_proxy():
                print("⚠️ Продолжаю без системного прокси...")
        
        # Показ статуса
        self.show_status()
        
        # Открытие браузера
        if open_browser:
            time.sleep(1)  # Даем время прокси запуститься
            self.open_browser()
        
        print("\n🎯 White-Ghost Proxy запущен и готов к работе!")
        print("🌐 Откройте YouTube в браузере - он должен работать через прокси")
        print("⏹️ Нажмите Ctrl+C для остановки")
        
        # Ожидание сигнала остановки
        try:
            while self.proxy_process and self.proxy_process.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Получен сигнал остановки")
        finally:
            self.cleanup(restore_system=setup_system)
        
        return True
    
    def cleanup(self, restore_system=True):
        """Очистка"""
        print("\n🧹 Очистка...")
        
        # Остановка прокси
        self.stop_proxy()
        
        # Восстановление настроек
        if restore_system:
            self.restore_proxy_settings()
        
        print("✅ Очистка завершена")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='White-Ghost Proxy Launcher')
    parser.add_argument('--no-system', action='store_true', help='Не настраивать системный прокси')
    parser.add_argument('--no-browser', action='store_true', help='Не открывать браузер')
    parser.add_argument('--host', default='127.0.0.1', help='Хост прокси')
    parser.add_argument('--port', type=int, default=1080, help='Порт прокси')
    parser.add_argument('--status', action='store_true', help='Показать статус')
    parser.add_argument('--stop', action='store_true', help='Остановить прокси')
    
    args = parser.parse_args()
    
    launcher = WhiteGhostLauncher()
    launcher.proxy_host = args.host
    launcher.proxy_port = args.port
    
    if args.status:
        launcher.show_status()
        return
    
    if args.stop:
        launcher.stop_proxy()
        launcher.restore_proxy_settings()
        return
    
    # Запуск
    try:
        launcher.run(
            setup_system=not args.no_system,
            open_browser=not args.no_browser
        )
    except KeyboardInterrupt:
        print("\n⏹️ Прерывание пользователем")
        launcher.cleanup(set_system=not args.no_system)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        launcher.cleanup(set_system=not args.no_system)


if __name__ == "__main__":
    main()
