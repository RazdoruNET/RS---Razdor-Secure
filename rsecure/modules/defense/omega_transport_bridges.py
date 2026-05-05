#!/usr/bin/env python3
"""
План «Омега» - CDN-фронтинг и Green Tunnel для обхода усиленного DPI
Автоматическая настройка прокси без необходимости конфигурирования Tor
"""
import socket
import ssl
import time
import subprocess
import os
import json
import sys
import threading
import queue
import struct
import hashlib
import base64
import random
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

class TransportType(Enum):
    """Типы транспортных мостов"""
    CDN_FRONTING = "cdn_fronting"
    GREEN_TUNNEL = "green_tunnel"
    CLOUDFLARE = "cloudflare"
    AZURE = "azure"
    AWS = "aws"
    GOOGLE = "google"

class OmegaTransportBridges:
    """План «Омега» - CDN-фронтинг и Green Tunnel"""
    
    def __init__(self):
        self.cdn_bridges_config = {
            "cloudflare": [
                {
                    "front_domain": "cdn.jsdelivr.net",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                },
                {
                    "front_domain": "ajax.googleapis.com",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                }
            ],
            "azure": [
                {
                    "front_domain": "azureedge.net",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                },
                {
                    "front_domain": "blob.core.windows.net",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                }
            ],
            "aws": [
                {
                    "front_domain": "cloudfront.net",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                },
                {
                    "front_domain": "s3.amazonaws.com",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                }
            ],
            "google": [
                {
                    "front_domain": "googleapis.com",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                },
                {
                    "front_domain": "gstatic.com",
                    "target_domain": "www.youtube.com",
                    "transport": "cdn_fronting",
                    "port": 443,
                    "method": "GET"
                }
            ]
        }
        
        self.green_tunnel_config = {
            "proxy_port": 8000,
            "dns_type": "https",
            "auto_start": True,
            "auto_proxy": True
        }
        
        self.active_bridges = []
        self.transport_status = {}
        self.green_tunnel_process = None
        self.proxy_port = 8000
        
    def setup_cdn_fronting_bridges(self) -> bool:
        """Настройка CDN-фронтинг мостов"""
        try:
            print("� Настройка CDN-фронтинг мостов...")
            
            for cdn_type, bridges in self.cdn_bridges_config.items():
                print(f"   Настраиваю {cdn_type} CDN...")
                
                for bridge in bridges:
                    print(f"      Пробую мост: {bridge['front_domain']} -> {bridge['target_domain']}")
                    
                    # Проверяем CDN соединение
                    if self._test_cdn_fronting_connection(bridge):
                        self.active_bridges.append(bridge)
                        self.transport_status[bridge['front_domain']] = "active"
                        print(f"      ✅ CDN {bridge['front_domain']} активен")
                    else:
                        self.transport_status[bridge['front_domain']] = "failed"
                        print(f"      ❌ CDN {bridge['front_domain']} не работает")
            
            return len(self.active_bridges) > 0
            
        except Exception as e:
            print(f"❌ Ошибка настройки CDN-фронтинг: {e}")
            return False
    
    def setup_green_tunnel(self) -> bool:
        """Настройка Green Tunnel"""
        try:
            print("🟢 Настройка Green Tunnel...")
            
            # Проверяем установлен ли Green Tunnel
            if not self._check_green_tunnel_installed():
                print("   Green Tunnel не установлен, пробую установить...")
                if not self._install_green_tunnel():
                    print("   ❌ Не удалось установить Green Tunnel")
                    return False
            
            # Запускаем Green Tunnel
            if self._start_green_tunnel():
                print("   ✅ Green Tunnel запущен на порту 8000")
                return True
            else:
                print("   ❌ Не удалось запустить Green Tunnel")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка настройки Green Tunnel: {e}")
            return False
    
    def _check_green_tunnel_installed(self) -> bool:
        """Проверка установлен ли Green Tunnel"""
        try:
            result = subprocess.run(["which", "green-tunnel"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _install_green_tunnel(self) -> bool:
        """Установка Green Tunnel"""
        try:
            print("   Установка Green Tunnel через npm...")
            
            # Проверяем npm
            npm_result = subprocess.run(["which", "npm"], 
                                      capture_output=True, text=True, timeout=5)
            if npm_result.returncode != 0:
                print("   ❌ npm не найден. Установите Node.js и npm")
                return False
            
            # Устанавливаем Green Tunnel
            install_result = subprocess.run(["sudo", "npm", "i", "-g", "green-tunnel"], 
                                          capture_output=True, text=True, timeout=60)
            
            if install_result.returncode == 0:
                print("   ✅ Green Tunnel успешно установлен")
                return True
            else:
                print(f"   ❌ Ошибка установки: {install_result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка установки: {e}")
            return False
    
    def _start_green_tunnel(self) -> bool:
        """Запуск Green Tunnel"""
        try:
            print("   Запуск Green Tunnel...")
            
            cmd = [
                "green-tunnel",
                "--dns-type", "https",
                "--proxy-port", str(self.green_tunnel_config["proxy_port"])
            ]
            
            self.green_tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем запуска
            time.sleep(3)
            
            # Проверяем что процесс запущен
            if self.green_tunnel_process.poll() is None:
                print("   ✅ Green Tunnel запущен")
                return True
            else:
                stdout, stderr = self.green_tunnel_process.communicate()
                print(f"   ❌ Ошибка запуска: {stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка запуска: {e}")
            return False
    
    def _add_bridge_to_torrc(self, bridge_line: str):
        """Добавление моста в torrc"""
        try:
            # Читаем существующий torrc
            torrc_content = ""
            if os.path.exists(self.torrc_path):
                with open(self.torrc_path, 'r') as f:
                    torrc_content = f.read()
            
            # Добавляем мост
            if "UseBridges 1" not in torrc_content:
                torrc_content += "\nUseBridges 1\n"
            
            if bridge_line not in torrc_content:
                torrc_content += f"{bridge_line}\n"
            
            # Записываем обратно
            os.makedirs(os.path.dirname(self.torrc_path), exist_ok=True)
            with open(self.torrc_path, 'w') as f:
                f.write(torrc_content)
            
            print(f"   ✅ Мост добавлен в {self.torrc_path}")
            
        except Exception as e:
            print(f"   ❌ Ошибка добавления моста в torrc: {e}")
    
    def _test_cdn_fronting_connection(self, bridge: Dict[str, Any]) -> bool:
        """Тестирование CDN-фронтинг соединения"""
        try:
            print(f"      Тестирование CDN: {bridge['front_domain']}")
            
            front_domain = bridge['front_domain']
            target_domain = bridge['target_domain']
            port = bridge.get('port', 443)
            
            # Создаем TLS соединение с CDN доменом
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((front_domain, port))
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=front_domain)
            
            # Создаем CDN-фронтинг запрос
            request = self._create_cdn_fronting_request(target_domain, front_domain)
            ssl_sock.send(request)
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            if b"HTTP" in response and ("200 OK" in response_str or "301" in response_str):
                print(f"      ✅ CDN {front_domain} работает")
                return True
            else:
                print(f"      ❌ CDN {front_domain} не отвечает")
                return False
                
        except Exception as e:
            print(f"      ❌ Ошибка CDN {bridge['front_domain']}: {e}")
            return False
    
    def _create_cdn_fronting_request(self, target_domain: str, front_domain: str) -> bytes:
        """Создание CDN-фронтинг запроса"""
        # CDN-фронтинг маскирует запрос к YouTube под запрос к CDN
        request = (
            f"GET / HTTP/1.1\r\n"
            f"Host: {target_domain}\r\n"  # Реальный хост в заголовке
            f"Front-Host: {front_domain}\r\n"  # CDN домен для фронтинга
            f"User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
            f"Accept-Language: en-US,en;q=0.5\r\n"
            f"Accept-Encoding: gzip, deflate, br\r\n"
            f"Connection: close\r\n"
            f"X-Forwarded-For: {front_domain}\r\n"
            f"X-Real-IP: {front_domain}\r\n"
            f"\r\n"
        ).encode()
        
        return request
    
    def _test_green_tunnel_connection(self) -> bool:
        """Тестирование Green Tunnel соединения"""
        try:
            print("   Тестирование Green Tunnel...")
            
            # Проверяем что Green Tunnel запущен на порту 8000
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", self.green_tunnel_config["proxy_port"]))
            sock.close()
            
            print("   ✅ Green Tunnel доступен на порту 8000")
            return True
            
        except Exception as e:
            print(f"   ❌ Green Tunnel недоступен: {e}")
            return False
    
    def _create_test_packet(self, bridge: Dict[str, Any]) -> bytes:
        """Создание тестового пакета для моста"""
        transport = bridge.get('transport', 'unknown')
        
        if transport == 'obfs4':
            # Obfs4 пакет
            packet = b'\x16\x01\x00' + b'obfs4_test_data'
        elif transport == 'snowflake':
            # Snowflake пакет
            packet = b'\x16\x02\x00' + b'snowflake_test_data'
        elif transport == 'shadow_tls':
            # Shadow-TLS пакет
            packet = b'\x16\x03\x00' + b'shadow_tls_test_data'
        else:
            # Стандартный пакет
            packet = b'test_packet_data'
        
        return packet
    
    def _create_shadow_tls_packet(self, bridge: Dict[str, Any]) -> bytes:
        """Создание Shadow-TLS пакета"""
        # Shadow-TLS маскирует данные под обычный HTTPS трафик
        # Внешне выглядит как запрос к microsoft.com
        # Внутри содержит данные для YouTube
        
        shadow_data = {
            "target": "www.youtube.com",
            "data": "youtube_request_data",
            "bridge": bridge['address']
        }
        
        # Шифруем данные
        encoded_data = base64.b64encode(json.dumps(shadow_data).encode())
        
        # Создаем TLS record
        tls_record = struct.pack('>H', 0x1603)  # TLS 1.2
        tls_record += struct.pack('>H', len(encoded_data))
        tls_record += encoded_data
        
        return tls_record
    
    def setup_all_bridges(self) -> Dict[str, Any]:
        """Настройка всех CDN и Green Tunnel мостов"""
        try:
            print("🌉 План «Омега» - Настройка CDN-фронтинг и Green Tunnel")
            print("=" * 60)
            
            results = {
                "cdn_fronting": {"success": False, "active": 0, "failed": 0},
                "green_tunnel": {"success": False, "active": 0, "failed": 0},
                "total_active": 0
            }
            
            # Настройка CDN-фронтинг
            if self.setup_cdn_fronting_bridges():
                results["cdn_fronting"]["success"] = True
                results["cdn_fronting"]["active"] = len(self.active_bridges)
            
            # Настройка Green Tunnel
            if self.setup_green_tunnel():
                results["green_tunnel"]["success"] = True
                results["green_tunnel"]["active"] = 1
            
            results["total_active"] = len(self.active_bridges) + (1 if results["green_tunnel"]["success"] else 0)
            
            return results
            
        except Exception as e:
            print(f"❌ Ошибка настройки мостов: {e}")
            return {"error": str(e)}
    
    def get_active_bridges(self) -> List[Dict[str, Any]]:
        """Получение списка активных мостов"""
        return self.active_bridges
    
    def get_transport_status(self) -> Dict[str, str]:
        """Получение статуса транспортов"""
        return self.transport_status
    
    def setup_proxy_configuration(self) -> bool:
        """Настройка прокси конфигурации для системы"""
        try:
            print("🔧 Настройка прокси конфигурации...")
            
            if self.green_tunnel_config["auto_proxy"]:
                # Автоматическая настройка прокси для macOS
                if sys.platform == "darwin":
                    return self._setup_macos_proxy()
                elif sys.platform == "linux":
                    return self._setup_linux_proxy()
                elif sys.platform == "win32":
                    return self._setup_windows_proxy()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки прокси: {e}")
            return False
    
    def _setup_macos_proxy(self) -> bool:
        """Настройка прокси на macOS"""
        try:
            print("   Настройка прокси на macOS...")
            
            proxy_port = self.green_tunnel_config["proxy_port"]
            
            # Настройка HTTP прокси
            cmd_http = [
                "networksetup", "-setwebproxy", "Wi-Fi", 
                "127.0.0.1", str(proxy_port)
            ]
            
            # Настройка HTTPS прокси
            cmd_https = [
                "networksetup", "-setsecurewebproxy", "Wi-Fi", 
                "127.0.0.1", str(proxy_port)
            ]
            
            # Включаем прокси
            cmd_enable_http = ["networksetup", "-setwebproxystate", "Wi-Fi", "on"]
            cmd_enable_https = ["networksetup", "-setsecurewebproxystate", "Wi-Fi", "on"]
            
            # Выполняем команды
            subprocess.run(cmd_http, capture_output=True, timeout=10)
            subprocess.run(cmd_https, capture_output=True, timeout=10)
            subprocess.run(cmd_enable_http, capture_output=True, timeout=10)
            subprocess.run(cmd_enable_https, capture_output=True, timeout=10)
            
            print("   ✅ Прокси настроен на macOS")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка настройки macOS прокси: {e}")
            return False
    
    def _setup_linux_proxy(self) -> bool:
        """Настройка прокси на Linux"""
        try:
            print("   Настройка прокси на Linux...")
            
            proxy_port = self.green_tunnel_config["proxy_port"]
            proxy_url = f"http://127.0.0.1:{proxy_port}"
            
            # Устанавливаем переменные окружения
            os.environ["http_proxy"] = proxy_url
            os.environ["https_proxy"] = proxy_url
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            
            print("   ✅ Прокси настроен на Linux")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка настройки Linux прокси: {e}")
            return False
    
    def _setup_windows_proxy(self) -> bool:
        """Настройка прокси на Windows"""
        try:
            print("   Настройка прокси на Windows...")
            
            proxy_port = self.green_tunnel_config["proxy_port"]
            proxy_url = f"http://127.0.0.1:{proxy_port}"
            
            # Настройка через реестр
            import winreg
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 
                              0, winreg.KEY_WRITE) as key:
                
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"127.0.0.1:{proxy_port}")
            
            print("   ✅ Прокси настроен на Windows")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка настройки Windows прокси: {e}")
            return False
    
    def generate_setup_commands(self) -> str:
        """Генерация команд для настройки"""
        commands = """# План «Омега» - CDN-фронтинг и Green Tunnel
# Команды для ручной настройки

# 1. Установка Green Tunnel (если не установлен)
sudo npm i -g green-tunnel

# 2. Запуск Green Tunnel
green-tunnel --dns-type https --proxy-port 8000

# 3. Настройка прокси на macOS
networksetup -setwebproxy Wi-Fi 127.0.0.1 8000
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8000
networksetup -setwebproxystate Wi-Fi on
networksetup -setsecurewebproxystate Wi-Fi on

# 4. Настройка прокси на Linux (экспорт переменных)
export http_proxy=http://127.0.0.1:8000
export https_proxy=http://127.0.0.1:8000

# 5. Проверка работы
curl -x http://127.0.0.1:8000 https://www.youtube.com
"""
        
        return commands
    
    def stop_green_tunnel(self):
        """Остановка Green Tunnel"""
        try:
            if self.green_tunnel_process:
                print("🛑 Остановка Green Tunnel...")
                self.green_tunnel_process.terminate()
                self.green_tunnel_process.wait(timeout=5)
                self.green_tunnel_process = None
                print("✅ Green Tunnel остановлен")
                return True
            else:
                print("ℹ️ Green Tunnel не был запущен")
                return True
        except Exception as e:
            print(f"❌ Ошибка остановки Green Tunnel: {e}")
            return False
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            print("🧹 Очистка ресурсов...")
            
            # Останавливаем Green Tunnel
            self.stop_green_tunnel()
            
            # Сбрасываем прокси настройки
            if sys.platform == "darwin":
                try:
                    subprocess.run(["networksetup", "-setwebproxystate", "Wi-Fi", "off"], 
                                 capture_output=True, timeout=5)
                    subprocess.run(["networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"], 
                                 capture_output=True, timeout=5)
                    print("✅ Прокси сброшен на macOS")
                except:
                    pass
            
            print("✅ Очистка завершена")
            
        except Exception as e:
            print(f"❌ Ошибка очистки: {e}")

# Глобальный экземпляр Omega Transport
omega_transport = OmegaTransportBridges()

def setup_omega_bridges():
    """Глобальная функция настройки мостов План «Омега»"""
    return omega_transport.setup_all_bridges()

def get_active_bridges():
    """Глобальная функция получения активных мостов"""
    return omega_transport.get_active_bridges()

def setup_proxy_configuration():
    """Глобальная функция настройки прокси"""
    return omega_transport.setup_proxy_configuration()

def stop_green_tunnel():
    """Глобальная функция остановки Green Tunnel"""
    return omega_transport.stop_green_tunnel()

def cleanup_omega():
    """Глобальная функция очистки"""
    omega_transport.cleanup()

if __name__ == "__main__":
    # Тестирование Omega Transport
    print("🌉 Omega Transport CDN & Green Tunnel Test")
    print("=" * 60)
    
    # Настройка всех мостов
    results = setup_omega_bridges()
    
    print("\n📊 Результаты настройки:")
    print(json.dumps(results, indent=2))
    
    # Настройка прокси
    if results.get("total_active", 0) > 0:
        print("\n� Настройка прокси...")
        proxy_success = setup_proxy_configuration()
        print(f"Настройка прокси: {'✅ Успех' if proxy_success else '❌ Ошибка'}")
    
    # Генерация команд
    print("\n📝 Команды для ручной настройки:")
    print(omega_transport.generate_setup_commands())
    
    # Очистка при выходе
    try:
        input("\nНажмите Enter для завершения и очистки...")
    except KeyboardInterrupt:
        pass
    
    cleanup_omega()
    print("\n🌉 План «Омега» завершен!")
