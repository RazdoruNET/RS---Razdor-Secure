#!/usr/bin/env python3
"""
System Proxy Setup Script
Автоматическая настройка системного прокси для DPI-Bypass на macOS
"""

import subprocess
import sys
import os
import argparse
import time


class SystemProxyManager:
    """Менеджер системных настроек прокси"""
    
    def __init__(self, proxy_port=8080):
        self.proxy_port = proxy_port
        self.proxy_host = "127.0.0.1"
        
    def get_current_proxy_settings(self):
        """Получение текущих настроек прокси"""
        try:
            # Получаем настройки для Wi-Fi
            result = subprocess.run([
                "networksetup", "-getwebproxy", "Wi-Fi"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print("❌ Не удалось получить настройки прокси")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка получения настроек: {e}")
            return None
    
    def enable_http_proxy(self):
        """Включение HTTP прокси"""
        try:
            print(f"🔧 Включаю HTTP прокси: {self.proxy_host}:{self.proxy_port}")
            
            # Включаем HTTP прокси
            subprocess.run([
                "networksetup", "-setwebproxy", "Wi-Fi", 
                self.proxy_host, str(self.proxy_port)
            ], check=True)
            
            # Включаем прокси
            subprocess.run([
                "networksetup", "-setwebproxystate", "Wi-Fi", "on"
            ], check=True)
            
            print("✅ HTTP прокси включен")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка включения HTTP прокси: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def enable_https_proxy(self):
        """Включение HTTPS прокси"""
        try:
            print(f"🔧 Включаю HTTPS прокси: {self.proxy_host}:{self.proxy_port}")
            
            # Включаем HTTPS прокси
            subprocess.run([
                "networksetup", "-setsecurewebproxy", "Wi-Fi",
                self.proxy_host, str(self.proxy_port)
            ], check=True)
            
            # Включаем прокси
            subprocess.run([
                "networksetup", "-setsecurewebproxystate", "Wi-Fi", "on"
            ], check=True)
            
            print("✅ HTTPS прокси включен")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка включения HTTPS прокси: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def disable_proxy(self):
        """Отключение прокси"""
        try:
            print("🔧 Отключаю системный прокси...")
            
            # Отключаем HTTP прокси
            subprocess.run([
                "networksetup", "-setwebproxystate", "Wi-Fi", "off"
            ], check=True)
            
            # Отключаем HTTPS прокси
            subprocess.run([
                "networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"
            ], check=True)
            
            print("✅ Системный прокси отключен")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка отключения прокси: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def enable_bypass_domains(self):
        """Настройка доменов для обхода прокси"""
        try:
            bypass_domains = [
                "localhost",
                "127.0.0.1",
                "*.local",
                "*.ru",
                "gosuslugi.ru",
                "nalog.gov.ru",
                "sbp.nspk.ru",
                "rutube.ru",
                "yandex.ru"
            ]
            
            bypass_list = " ".join(bypass_domains)
            
            print(f"🔧 Настраиваю обход прокси для доменов: {bypass_list}")
            
            subprocess.run([
                "networksetup", "-setproxybypassdomains", "Wi-Fi", bypass_list
            ], check=True)
            
            print("✅ Домены для обхода настроены")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка настройки обхода: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def setup_full_proxy(self):
        """Полная настройка прокси"""
        print("🚀 Начинаю настройку системного прокси для DPI-Bypass...")
        print("=" * 50)
        
        # Проверяем права администратора
        if os.geteuid() != 0:
            print("❌ Требуются права администратора для настройки системного прокси")
            print("🔧 Используйте: sudo python3 setup_system_proxy.py")
            return False
        
        success = True
        
        # Показываем текущие настройки
        print("\n📋 Текущие настройки прокси:")
        current = self.get_current_proxy_settings()
        if current:
            print(current)
        
        # Включаем HTTP прокси
        if not self.enable_http_proxy():
            success = False
        
        # Включаем HTTPS прокси
        if not self.enable_https_proxy():
            success = False
        
        # Настраиваем обход для локальных доменов
        if not self.enable_bypass_domains():
            success = False
        
        if success:
            print("\n✅ Системный прокси успешно настроен!")
            print(f"🌐 Весь трафик теперь маршрутизируется через DPI-Bypass")
            print(f"📍 Прокси: {self.proxy_host}:{self.proxy_port}")
            print(f"🔄 Для отключения используйте: sudo python3 setup_system_proxy.py --disable")
        else:
            print("\n❌ Ошибка настройки системного прокси")
        
        return success
    
    def show_status(self):
        """Показать статус прокси"""
        print("📊 Статус системного прокси:")
        print("=" * 30)
        
        try:
            # HTTP прокси статус
            result = subprocess.run([
                "networksetup", "-getwebproxystate", "Wi-Fi"
            ], capture_output=True, text=True)
            
            http_enabled = "Enabled" in result.stdout
            print(f"🌐 HTTP прокси: {'✅ Включен' if http_enabled else '❌ Выключен'}")
            
            # HTTPS прокси статус
            result = subprocess.run([
                "networksetup", "-getsecurewebproxystate", "Wi-Fi"
            ], capture_output=True, text=True)
            
            https_enabled = "Enabled" in result.stdout
            print(f"🔒 HTTPS прокси: {'✅ Включен' if https_enabled else '❌ Выключен'}")
            
            # Детальные настройки
            if http_enabled or https_enabled:
                print("\n📋 Детальные настройки:")
                current = self.get_current_proxy_settings()
                if current:
                    print(current)
                    
        except Exception as e:
            print(f"❌ Ошибка получения статуса: {e}")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="System Proxy Setup for DPI-Bypass")
    parser.add_argument("--port", type=int, default=8080, help="Порт прокси (по умолчанию: 8080)")
    parser.add_argument("--disable", action="store_true", help="Отключить прокси")
    parser.add_argument("--status", action="store_true", help="Показать статус")
    
    args = parser.parse_args()
    
    manager = SystemProxyManager(proxy_port=args.port)
    
    if args.status:
        manager.show_status()
    elif args.disable:
        manager.disable_proxy()
    else:
        manager.setup_full_proxy()


if __name__ == "__main__":
    main()
