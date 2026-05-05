#!/usr/bin/env python3
"""
System Proxy Manager for White-Ghost
Настраивает системный прокси для ВСЕГО трафика компьютера
"""

import subprocess
import sys
import os
import json
import time
import signal
import argparse
from pathlib import Path


class SystemProxyManager:
    """Менеджер системного прокси macOS"""
    
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 1080
        self.backup_file = Path.home() / ".white_ghost_proxy_backup.json"
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
        """Сохранение текущих настроек прокси для всех интерфейсов"""
        print("💾 Сохраняю текущие настройки прокси...")
        
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
                
                # Получаем настройки SOCKS прокси
                socks_result = subprocess.run([
                    "networksetup", "-getsocksfirewallproxy", service
                ], capture_output=True, text=True, check=True)
                
                self.original_settings[service] = {
                    "http": http_result.stdout,
                    "https": https_result.stdout,
                    "socks": socks_result.stdout
                }
                
            except subprocess.CalledProcessError:
                continue
        
        # Сохраняем в файл
        try:
            with open(self.backup_file, 'w') as f:
                json.dump(self.original_settings, f, indent=2)
            print(f"✅ Настройки сохранены в {self.backup_file}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
            return False
    
    def restore_all_settings(self):
        """Восстановление всех сохраненных настроек прокси"""
        if not self.backup_file.exists():
            print("⚠️ Файл резервной копии не найден")
            return False
        
        try:
            print("🔄 Восстанавливаю настройки прокси...")
            
            with open(self.backup_file, 'r') as f:
                settings = json.load(f)
            
            for service, service_settings in settings.items():
                try:
                    # Восстанавливаем HTTP прокси
                    if "Enabled: Yes" in service_settings["http"]:
                        # Извлекаем адрес и порт
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
                    
                    # Восстанавливаем SOCKS прокси
                    if "Enabled: Yes" in service_settings["socks"]:
                        lines = service_settings["socks"].split('\n')
                        server = ""
                        port = ""
                        for line in lines:
                            if line.startswith("Server:"):
                                server = line.split(":")[1].strip()
                            elif line.startswith("Port:"):
                                port = line.split(":")[1].strip()
                        
                        if server and port:
                            subprocess.run([
                                "networksetup", "-setsocksfirewallproxy", service, server, port
                            ], check=True)
                            subprocess.run([
                                "networksetup", "-setsocksfirewallproxystate", service, "on"
                            ], check=True)
                    else:
                        subprocess.run([
                            "networksetup", "-setsocksfirewallproxystate", service, "off"
                        ], check=True)
                        
                except subprocess.CalledProcessError:
                    continue
            
            print("✅ Настройки прокси восстановлены")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка восстановления настроек: {e}")
            return False
    
    def setup_full_system_proxy(self):
        """Настройка системного прокси для ВСЕГО трафика"""
        print("🔧 Настраиваю системный прокси для ВСЕГО трафика...")
        
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
                
                # Настраиваем SOCKS прокси (для полного трафика)
                subprocess.run([
                    "networksetup", "-setsocksfirewallproxy", service,
                    self.proxy_host, str(self.proxy_port)
                ], check=True)
                
                # Включаем все прокси
                subprocess.run([
                    "networksetup", "-setwebproxystate", service, "on"
                ], check=True)
                
                subprocess.run([
                    "networksetup", "-setsecurewebproxystate", service, "on"
                ], check=True)
                
                subprocess.run([
                    "networksetup", "-setsocksfirewallproxystate", service, "on"
                ], check=True)
                
                success_count += 1
                print(f"   ✅ {service} настроен")
                
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Ошибка настройки {service}: {e}")
                continue
        
        print(f"📊 Настроено интерфейсов: {success_count}/{len(services)}")
        return success_count > 0
    
    def disable_all_proxy(self):
        """Отключение всех прокси"""
        print("🔌 Отключаю все прокси...")
        
        services = self.get_all_network_services()
        success_count = 0
        
        for service in services:
            try:
                # Отключаем все типы прокси
                subprocess.run([
                    "networksetup", "-setwebproxystate", service, "off"
                ], check=False)
                
                subprocess.run([
                    "networksetup", "-setsecurewebproxystate", service, "off"
                ], check=False)
                
                subprocess.run([
                    "networksetup", "-setsocksfirewallproxystate", service, "off"
                ], check=False)
                
                success_count += 1
                
            except:
                continue
        
        print(f"📊 Отключено интерфейсов: {success_count}/{len(services)}")
    
    def get_proxy_status(self):
        """Получение текущего статуса прокси"""
        print("📊 СТАТУС СИСТЕМНОГО ПРОКСИ:")
        print("=" * 50)
        
        services = self.get_all_network_services()
        
        for service in services:
            try:
                # Проверяем HTTP прокси
                http_result = subprocess.run([
                    "networksetup", "-getwebproxy", service
                ], capture_output=True, text=True, check=True)
                
                # Проверяем SOCKS прокси
                socks_result = subprocess.run([
                    "networksetup", "-getsocksfirewallproxy", service
                ], capture_output=True, text=True, check=True)
                
                http_enabled = "Enabled: Yes" in http_result.stdout
                socks_enabled = "Enabled: Yes" in socks_result.stdout
                
                status_icon = "🟢" if (http_enabled or socks_enabled) else "🔴"
                print(f"   {status_icon} {service}")
                
                if http_enabled or socks_enabled:
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
        
        print(f"\n🎯 Целевой прокси: {self.proxy_host}:{self.proxy_port}")
    
    def test_proxy_connection(self):
        """Тестирование соединения через прокси"""
        print("🧪 Тестирую соединение через прокси...")
        
        try:
            import urllib.request
            import urllib.error
            
            # Создаем запрос через прокси
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'http://{self.proxy_host}:{self.proxy_port}',
                'https': f'http://{self.proxy_host}:{self.proxy_port}',
                'ftp': f'http://{self.proxy_host}:{self.proxy_port}'
            })
            
            opener = urllib.request.build_opener(proxy_handler)
            
            # Тестовый запрос
            request = urllib.request.Request('http://httpbin.org/ip')
            request.add_header('User-Agent', 'White-Ghost-Proxy/1.0')
            
            with opener.open(request, timeout=10) as response:
                data = response.read().decode('utf-8')
                print(f"   ✅ Прокси работает: {data}")
                return True
                
        except Exception as e:
            print(f"   ❌ Ошибка прокси: {e}")
            return False
    
    def show_network_info(self):
        """Показ информации о сети"""
        print("🌐 ИНФОРМАЦИЯ О СЕТИ:")
        print("=" * 30)
        
        try:
            # Получаем текущий IP
            result = subprocess.run([
                "ifconfig", "en0"
            ], capture_output=True, text=True)
            
            if "inet " in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "inet " in line and not "127.0.0.1" in line:
                        ip = line.split()[1]
                        print(f"   🌍 IP адрес: {ip}")
                        break
            
            # Показываем шлюз
            result = subprocess.run([
                "netstat", "-nr"
            ], capture_output=True, text=True)
            
            if "default" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith("default"):
                        gateway = line.split()[1]
                        print(f"   🚪 Шлюз: {gateway}")
                        break
                        
        except:
            print("   ❓ Не удалось получить информацию о сети")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='System Proxy Manager for White-Ghost')
    parser.add_argument('--setup', action='store_true', help='Настроить системный прокси')
    parser.add_argument('--restore', action='store_true', help='Восстановить настройки')
    parser.add_argument('--disable', action='store_true', help='Отключить все прокси')
    parser.add_argument('--status', action='store_true', help='Показать статус')
    parser.add_argument('--test', action='store_true', help='Тестировать прокси')
    parser.add_argument('--info', action='store_true', help='Информация о сети')
    parser.add_argument('--host', default='127.0.0.1', help='Хост прокси')
    parser.add_argument('--port', type=int, default=1080, help='Порт прокси')
    
    args = parser.parse_args()
    
    manager = SystemProxyManager()
    manager.proxy_host = args.host
    manager.proxy_port = args.port
    
    if args.status:
        manager.get_proxy_status()
    elif args.setup:
        manager.backup_current_settings()
        manager.setup_full_system_proxy()
        print(f"\n🎯 СИСТЕМНЫЙ ПРОКСИ НАСТРОЕН!")
        print(f"🌐 ВЕСЬ трафик идет через {manager.proxy_host}:{manager.proxy_port}")
        print(f"🔄 Для восстановления: python3 {sys.argv[0]} --restore")
    elif args.restore:
        manager.restore_all_settings()
    elif args.disable:
        manager.disable_all_proxy()
    elif args.test:
        manager.test_proxy_connection()
    elif args.info:
        manager.show_network_info()
    else:
        print("Используйте --help для просмотра доступных команд")


if __name__ == "__main__":
    main()
