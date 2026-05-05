#!/usr/bin/env python3
"""
Настройка HTTP прокси для решения ERR_PROXY_CONNECTION_FAILED
Использует HTTP прокси вместо SOCKS5 для лучшей совместимости
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path


class HTTPProxySetup:
    """Настройщик HTTP прокси"""
    
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 8080  # HTTP порт вместо SOCKS5
        self.backup_file = Path.home() / ".white_ghost_http_proxy_backup.json"
        self.original_settings = {}
        
        # Список всех сетевых интерфейсов macOS
        self.network_services = [
            "Wi-Fi", "Ethernet", "Thunderbolt Ethernet",
            "USB 10/100/1000 LAN", "Bluetooth PAN", "Personal Hotspot"
        ]
    
    def get_all_network_services(self):
        """Получение всех активных сетевых служб"""
        try:
            result = subprocess.run([
                "networksetup", "-listallnetworkservices"
            ], capture_output=True, text=True, check=True)
            
            services = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('*'):
                    services.append(line)
            
            return services
            
        except subprocess.CalledProcessError:
            return self.network_services
    
    def backup_current_settings(self):
        """Сохранение текущих настроек прокси"""
        print("💾 Сохраняю текущие настройки HTTP прокси...")
        
        services = self.get_all_network_services()
        self.original_settings = {}
        
        for service in services:
            try:
                # Получаем настройки HTTP прокси
                http_result = subprocess.run([
                    "networksetup", "-getwebproxy", service
                ], capture_output=True, text=True, check=True)
                
                # Получаем настройки HTTPS прокси
                https_result = subprocess.run([
                    "networksetup", "-getsecurewebproxy", service
                ], capture_output=True, text=True, check=True)
                
                self.original_settings[service] = {
                    "http": http_result.stdout,
                    "https": https_result.stdout
                }
                
            except subprocess.CalledProcessError:
                continue
        
        # Сохраняем в файл
        try:
            import json
            with open(self.backup_file, 'w') as f:
                json.dump(self.original_settings, f, indent=2)
            print(f"✅ Настройки сохранены в {self.backup_file}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
            return False
    
    def setup_http_proxy(self):
        """Настройка HTTP прокси для всех интерфейсов"""
        print("🔧 Настраиваю HTTP прокси для всех интерфейсов...")
        
        services = self.get_all_network_services()
        success_count = 0
        
        for service in services:
            try:
                print(f"   🌐 Настраиваю {service}...")
                
                # Настраиваем HTTP прокси
                subprocess.run([
                    "networksetup", "-setwebproxy", service,
                    self.proxy_host, str(self.proxy_port)
                ], check=True)
                
                # Настраиваем HTTPS прокси
                subprocess.run([
                    "networksetup", "-setsecurewebproxy", service,
                    self.proxy_host, str(self.proxy_port)
                ], check=True)
                
                # Включаем прокси
                subprocess.run([
                    "networksetup", "-setwebproxystate", service, "on"
                ], check=True)
                
                subprocess.run([
                    "networksetup", "-setsecurewebproxystate", service, "on"
                ], check=True)
                
                # Отключаем SOCKS прокси (если был включен)
                subprocess.run([
                    "networksetup", "-setsocksfirewallproxystate", service, "off"
                ], check=False)
                
                success_count += 1
                print(f"   ✅ {service} настроен")
                
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Ошибка настройки {service}: {e}")
                continue
        
        print(f"📊 Настроено интерфейсов: {success_count}/{len(services)}")
        return success_count > 0
    
    def restore_settings(self):
        """Восстановление настроек"""
        if not self.backup_file.exists():
            print("⚠️ Файл резервной копии не найден")
            return False
        
        try:
            print("🔄 Восстанавливаю настройки прокси...")
            
            import json
            with open(self.backup_file, 'r') as f:
                settings = json.load(f)
            
            for service, service_settings in settings.items():
                try:
                    # Восстанавливаем HTTP прокси
                    if "Enabled: Yes" in service_settings["http"]:
                        lines = service_settings["http"].split('\n')
                        server = ""
                        port = ""
                        for line in lines:
                            if line.startswith("Server:"):
                                server = line.split(":")[1].strip()
                            elif line.startswith("Port:"):
                                port = line.split(":")[1].strip()
                        
                        if server and port:
                            subprocess.run([
                                "networksetup", "-setwebproxy", service, server, port
                            ], check=True)
                            subprocess.run([
                                "networksetup", "-setwebproxystate", service, "on"
                            ], check=True)
                    else:
                        subprocess.run([
                            "networksetup", "-setwebproxystate", service, "off"
                        ], check=True)
                    
                    # Восстанавливаем HTTPS прокси
                    if "Enabled: Yes" in service_settings["https"]:
                        lines = service_settings["https"].split('\n')
                        server = ""
                        port = ""
                        for line in lines:
                            if line.startswith("Server:"):
                                server = line.split(":")[1].strip()
                            elif line.startswith("Port:"):
                                port = line.split(":")[1].strip()
                        
                        if server and port:
                            subprocess.run([
                                "networksetup", "-setsecurewebproxy", service, server, port
                            ], check=True)
                            subprocess.run([
                                "networksetup", "-setsecurewebproxystate", service, "on"
                            ], check=True)
                    else:
                        subprocess.run([
                            "networksetup", "-setsecurewebproxystate", service, "off"
                        ], check=True)
                        
                except subprocess.CalledProcessError:
                    continue
            
            print("✅ Настройки прокси восстановлены")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка восстановления настроек: {e}")
            return False
    
    def get_status(self):
        """Получение статуса HTTP прокси"""
        print("📊 СТАТУС HTTP ПРОКСИ:")
        print("=" * 40)
        
        services = self.get_all_network_services()
        
        for service in services:
            try:
                # Проверяем HTTP прокси
                http_result = subprocess.run([
                    "networksetup", "-getwebproxy", service
                ], capture_output=True, text=True, check=True)
                
                http_enabled = "Enabled: Yes" in http_result.stdout
                
                status_icon = "🟢" if http_enabled else "🔴"
                print(f"   {status_icon} {service}")
                
                if http_enabled:
                    lines = http_result.stdout.split('\n')
                    for line in lines:
                        if line.startswith("Server:"):
                            server = line.split(":")[1].strip()
                            print(f"      🌐 HTTP: {server}")
                        elif line.startswith("Port:"):
                            port = line.split(":")[1].strip()
                            print(f"      📡 Порт: {port}")
                
            except:
                print(f"   ❓ {service} - недоступен")
        
        print(f"\n🎯 Целевой HTTP прокси: {self.proxy_host}:{self.proxy_port}")
    
    def test_http_proxy(self):
        """Тестирование HTTP прокси"""
        print("🧪 Тестирую HTTP прокси...")
        
        try:
            import urllib.request
            import urllib.error
            
            # Создаем запрос через HTTP прокси
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'http://{self.proxy_host}:{self.proxy_port}',
                'https': f'http://{self.proxy_host}:{self.proxy_port}'
            })
            
            opener = urllib.request.build_opener(proxy_handler)
            
            # Тестовый запрос
            request = urllib.request.Request('http://httpbin.org/ip')
            request.add_header('User-Agent', 'White-Ghost-HTTP-Proxy/1.0')
            
            with opener.open(request, timeout=10) as response:
                data = response.read().decode('utf-8')
                print(f"   ✅ HTTP прокси работает: {data}")
                return True
                
        except Exception as e:
            print(f"   ❌ Ошибка HTTP прокси: {e}")
            return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Настройка HTTP прокси для White-Ghost')
    parser.add_argument('--setup', action='store_true', help='Настроить HTTP прокси')
    parser.add_argument('--restore', action='store_true', help='Восстановить настройки')
    parser.add_argument('--status', action='store_true', help='Показать статус')
    parser.add_argument('--test', action='store_true', help='Тестировать прокси')
    parser.add_argument('--host', default='127.0.0.1', help='Хост прокси')
    parser.add_argument('--port', type=int, default=8080, help='Порт прокси')
    
    args = parser.parse_args()
    
    setup = HTTPProxySetup()
    setup.proxy_host = args.host
    setup.proxy_port = args.port
    
    if args.status:
        setup.get_status()
    elif args.setup:
        setup.backup_current_settings()
        setup.setup_http_proxy()
        print(f"\n🎯 HTTP ПРОКСИ НАСТРОЕН!")
        print(f"🌐 Используйте HTTP прокси: {setup.proxy_host}:{setup.proxy_port}")
        print(f"🔄 Для восстановления: python3 {sys.argv[0]} --restore")
    elif args.restore:
        setup.restore_settings()
    elif args.test:
        setup.test_http_proxy()
    else:
        print("Используйте --help для просмотра доступных команд")


if __name__ == "__main__":
    main()
