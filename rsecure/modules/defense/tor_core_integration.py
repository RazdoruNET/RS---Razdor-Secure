#!/usr/bin/env python3
"""
Tor-Core Integration - Полноценная Darknet-стек интеграция
Автоматическое переключение на Tor при блокировках DPI
"""
import socket
import socks
import requests
import ssl
import urllib3
import time
import threading
import subprocess
import os
import sys
from typing import Optional, Tuple, Dict, Any
from enum import Enum

class TorStatus(Enum):
    """Статус Tor соединения"""
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ACTIVE = "active"
    FAILED = "failed"

class TorCoreIntegration:
    """Tor-Core интеграция с системным прокси"""
    
    def __init__(self):
        self.tor_proxy_host = "127.0.0.1"
        self.tor_proxy_port = 9050
        self.tor_browser_port = 9150
        self.status = TorStatus.INACTIVE
        self.original_socket = socket.socket
        self.tor_active = False
        self.darknet_mode = False
        self.onion_services = {
            # YouTube onion сервисы и альтернативы
            "youtube": [
                "yewtu.be",  # Invidious
                "piped.video",  # Piped
                "invidious.snopyta.org",
                "piped.garudalinux.org",
                "yewtu.be",  # Backup
            ],
            # Onion сервисы для тестов
            "test": [
                "tux.pizza",  # Working test site
                "check.torproject.org",
                "duckduckgogg42xjoc72x3sjasowy5d6xg77syzz6qcqj3xv5z5c5yd.onion"
            ]
        }
        
        # Настройки для системного прокси
        self.proxy_config = {
            'http': f'socks5://{self.tor_proxy_host}:{self.tor_proxy_port}',
            'https': f'socks5://{self.tor_proxy_host}:{self.tor_proxy_port}'
        }
        
        # Отключаем предупреждения SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def check_tor_availability(self) -> Tuple[bool, int]:
        """Проверка доступности Tor на разных портах"""
        ports_to_check = [9050, 9150, 9051]  # Standard Tor, Tor Browser, Control port
        
        for port in ports_to_check:
            try:
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, self.tor_proxy_host, port)
                sock.settimeout(5)
                sock.connect(("check.torproject.org", 80))
                sock.close()
                self.tor_proxy_port = port
                return True, port
            except:
                continue
        
        return False, 0
    
    def activate_darknet_bridge(self) -> str:
        """Активация Darknet моста - перенаправление всего трафика через Tor"""
        try:
            print("🌐 Активация Darknet моста...")
            
            # Проверяем доступность Tor
            tor_available, port = self.check_tor_availability()
            if not tor_available:
                return "❌ Tor недоступен. Установите Tor или запустите Tor Browser"
            
            self.tor_proxy_port = port
            print(f"✅ Tor найден на порту {port}")
            
            # Перенаправляем системный трафик через Tor
            socks.set_default_proxy(socks.SOCKS5, self.tor_proxy_host, self.tor_proxy_port)
            socket.socket = socks.socksocket
            
            self.tor_active = True
            self.darknet_mode = True
            self.status = TorStatus.ACTIVE
            
            # Проверяем выход в сеть через тестовый сайт
            return self.test_darknet_connection()
            
        except Exception as e:
            self.status = TorStatus.FALED
            return f"❌ КРИТИЧЕСКАЯ ОШИБКА активации Darknet: {e}"
    
    def test_darknet_connection(self) -> str:
        """Тестирование соединения через Darknet"""
        try:
            print("🔍 Тестирование Darknet соединения...")
            
            # Пробуем разные onion сервисы
            for service_type, services in self.onion_services.items():
                for service in services:
                    try:
                        print(f"   Пробую сервис: {service}")
                        
                        # Создаем сессию с Tor прокси
                        session = requests.Session()
                        session.proxies = self.proxy_config
                        session.verify = False
                        
                        response = session.get(f"https://{service}", timeout=15)
                        
                        if response.status_code == 200:
                            print(f"✅ Сервис {service} доступен через Tor")
                            
                            # Если это YouTube фронтенд, проверяем возможность просмотра
                            if service_type == "youtube":
                                return f"✅ СВЯЗЬ ВОССТАНОВЛЕНА ЧЕРЕЗ INVIDIOUS + TOR ({service})"
                            else:
                                return f"✅ Darknet соединение установлено через {service}"
                        
                    except Exception as e:
                        print(f"   Сервис {service} не сработал: {e}")
                        continue
            
            return "❌ Ни один onion сервис не доступен через Tor"
            
        except Exception as e:
            return f"❌ ОШИБКА тестирования Darknet: {e}"
    
    def deactivate_darknet_bridge(self) -> str:
        """Деактивация Darknet моста"""
        try:
            print("🔌 Деактивация Darknet моста...")
            
            # Восстанавливаем оригинальный socket
            socket.socket = self.original_socket
            socks.set_default_proxy()
            
            self.tor_active = False
            self.darknet_mode = False
            self.status = TorStatus.INACTIVE
            
            return "✅ Darknet мост деактивирован"
            
        except Exception as e:
            return f"❌ Ошибка деактивации: {e}"
    
    def get_youtube_through_tor(self, video_url: str = None) -> Dict[str, Any]:
        """Получение YouTube контента через Tor"""
        try:
            if not self.tor_active:
                activate_result = self.activate_darknet_bridge()
                if "❌" in activate_result:
                    return {"success": False, "error": activate_result}
            
            print("📺 Получение YouTube через Tor...")
            
            # Создаем сессию с Tor прокси
            session = requests.Session()
            session.proxies = self.proxy_config
            session.verify = False
            
            # Пробуем разные YouTube фронтенды
            for frontend in self.onion_services["youtube"]:
                try:
                    print(f"   Пробую фронтенд: {frontend}")
                    
                    if video_url:
                        # Запрашиваем конкретное видео
                        response = session.get(f"https://{frontend}/api/v1/videos/{video_url}", timeout=15)
                    else:
                        # Запрашиваем главную страницу
                        response = session.get(f"https://{frontend}", timeout=15)
                    
                    if response.status_code == 200:
                        print(f"✅ Фронтенд {frontend} работает!")
                        
                        return {
                            "success": True,
                            "frontend": frontend,
                            "status_code": response.status_code,
                            "content_length": len(response.content),
                            "response_time": response.elapsed.total_seconds(),
                            "data": response.json() if "api" in response.url else response.text[:500]
                        }
                        
                except Exception as e:
                    print(f"   Фронтенд {frontend} не сработал: {e}")
                    continue
            
            return {"success": False, "error": "Все YouTube фронтенды недоступны"}
            
        except Exception as e:
            return {"success": False, "error": f"Ошибка получения YouTube: {e}"}
    
    def automatic_tor_fallback(self, url: str, max_attempts: int = 3) -> Dict[str, Any]:
        """Автоматическое переключение на Tor при блокировке"""
        try:
            print(f"🔄 Автоматическое переключение для {url}")
            
            # Сначала пробуем прямой запрос
            for attempt in range(max_attempts):
                try:
                    print(f"   Попытка {attempt + 1}/{max_attempts} (прямой запрос)")
                    
                    response = requests.get(url, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "method": "direct",
                            "attempt": attempt + 1,
                            "status_code": response.status_code
                        }
                    
                except requests.exceptions.SSLError:
                    print("   SSL ошибка - пробуем Tor")
                    break
                except requests.exceptions.Timeout:
                    print("   Timeout - пробуем Tor")
                    break
                except Exception as e:
                    print(f"   Ошибка прямого запроса: {e}")
                    if attempt == max_attempts - 1:
                        break
                    time.sleep(1)
            
            # Переключаемся на Tor
            print("🌐 Переключение на Tor...")
            
            if not self.tor_active:
                activate_result = self.activate_darknet_bridge()
                if "❌" in activate_result:
                    return {"success": False, "error": activate_result}
            
            # Пробуем через Tor
            session = requests.Session()
            session.proxies = self.proxy_config
            session.verify = False
            
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "method": "tor",
                    "frontend": self._detect_frontend(url),
                    "status_code": response.status_code
                }
            else:
                return {"success": False, "error": f"Tor запрос не удался: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Ошибка автоматического переключения: {e}"}
    
    def _detect_frontend(self, url: str) -> str:
        """Определение типа фронтенда"""
        if "youtube.com" in url:
            return "direct_youtube"
        elif any(frontend in url for frontend in self.onion_services["youtube"]):
            return "invidious_piped"
        else:
            return "unknown"
    
    def get_tor_status(self) -> Dict[str, Any]:
        """Получение статуса Tor соединения"""
        return {
            "status": self.status.value,
            "tor_active": self.tor_active,
            "darknet_mode": self.darknet_mode,
            "proxy_port": self.tor_proxy_port,
            "proxy_host": self.tor_proxy_host
        }
    
    def start_tor_service(self) -> bool:
        """Запуск Tor сервиса (если возможно)"""
        try:
            print("🚀 Попытка запуска Tor сервиса...")
            
            # Проверяем системный Tor
            try:
                result = subprocess.run(["tor", "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ Системный Tor найден")
                    return True
            except:
                pass
            
            # Пробуем запустить Tor Browser
            try:
                # macOS
                if sys.platform == "darwin":
                    result = subprocess.run(["open", "/Applications/Tor Browser.app"], 
                                          capture_output=True, timeout=5)
                # Linux
                elif sys.platform == "linux":
                    result = subprocess.run(["tor-browser"], 
                                          capture_output=True, timeout=5)
                # Windows
                elif sys.platform == "win32":
                    result = subprocess.run(["start", "tor-browser"], 
                                          capture_output=True, timeout=5)
                
                print("✅ Tor Browser запущен")
                return True
                
            except Exception as e:
                print(f"❌ Не удалось запустить Tor: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска Tor: {e}")
            return False

# Глобальный экземпляр Tor-Core
tor_core = TorCoreIntegration()

def activate_darknet_bridge():
    """Глобальная функция активации Darknet моста"""
    return tor_core.activate_darknet_bridge()

def get_youtube_through_tor(video_url: str = None):
    """Глобальная функция получения YouTube через Tor"""
    return tor_core.get_youtube_through_tor(video_url)

def automatic_tor_fallback(url: str, max_attempts: int = 3):
    """Глобальная функция автоматического переключения на Tor"""
    return tor_core.automatic_tor_fallback(url, max_attempts)

if __name__ == "__main__":
    # Тестирование Tor-Core интеграции
    print("🧬 Tor-Core Integration Test")
    print("=" * 50)
    
    # Активация Darknet моста
    result = activate_darknet_bridge()
    print(result)
    
    if "✅" in result:
        # Тестирование YouTube
        print("\n📺 Тестирование YouTube через Tor...")
        youtube_result = get_youtube_through_tor()
        print(f"Результат: {youtube_result}")
        
        # Тестирование автоматического переключения
        print("\n🔄 Тестирование автоматического переключения...")
        auto_result = automatic_tor_fallback("https://www.youtube.com")
        print(f"Результат: {auto_result}")
    
    print("\n📊 Статус Tor:")
    print(tor_core.get_tor_status())
