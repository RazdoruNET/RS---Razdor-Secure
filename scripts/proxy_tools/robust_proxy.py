#!/usr/bin/env python3
"""
Улучшенная прокси с исправлением DNS и SSL проблем
"""

import socket
import ssl
import threading
import select
import random
import time
import sys
import urllib.request
import urllib.error
# import dns.resolver  # Закомментировано для избежания зависимости
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

# Импортируем пайплайны
# Динамическое определение пути к проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from rsecure.modules.defense.dpi_bypass_combiner import (
        GoswebTunnelPipeline,
        MediaParasitePipeline, 
        FinStormPipeline
    )
    DPI_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ DPI модули недоступны: {e}")
    print("🔄 Работа в режиме обычного прокси")
    DPI_MODULES_AVAILABLE = False

class RobustProxyHandler(BaseHTTPRequestHandler):
    """Улучшенный обработчик с исправленными проблемами"""
    
    def __init__(self, request, client_address, server):
        self.server_class = server
        # Только рабочие пайплайны если доступны
        self.pipelines = []
        if DPI_MODULES_AVAILABLE:
            self.pipelines = [
                FinStormPipeline(),            # Приоритет 1: Фин-Шторм (самый стабильный)
                MediaParasitePipeline(),       # Приоритет 2: Медиа-Паразит
                GoswebTunnelPipeline(),        # Приоритет 3: Госвеб-Туннель
            ]
            print("✅ DPI пайплайны загружены")
        else:
            print("⚠️ Работа в режиме обычного прокси")
        super().__init__(request, client_address, server)
    
    def do_GET(self):
        self.handle_proxy_request()
    
    def do_POST(self):
        self.handle_proxy_request()
    
    def do_CONNECT(self):
        """Улучшенная обработка HTTPS с fallback"""
        try:
            # Извлекаем хост и порт
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 HTTPS CONNECT к {host}:{port}")
            
            # Сначала пробуем прямое подключение
            if self.try_direct_connect(host, port):
                return
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Пробуем пайплайны
            success = self.try_pipelines_tunnel(host, port)
            
            if not success:
                print(f"❌ Все методы не сработали для {host}:{port}")
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def try_direct_connect(self, host, port):
        """Пробуем прямое подключение без прокси"""
        try:
            print(f"🔄 Пробую прямое подключение к {host}:{port}")
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            # Резолвим IP адрес
            ip = self.resolve_host(host)
            if not ip:
                print(f"❌ Не удалось резолвить {host}")
                return False
            
            sock.connect((ip, port))
            
            # Если HTTPS, создаем TLS
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                
                ssl_sock = context.wrap_socket(sock, server_hostname=host)
                remote_sock = ssl_sock
            else:
                remote_sock = sock
            
            print(f"✅ Прямое подключение успешно!")
            self.relay_data(self.connection, remote_sock)
            return True
            
        except Exception as e:
            print(f"❌ Прямое подключение не удалось: {e}")
            return False
    
    def resolve_host(self, host):
        """Улучшенный DNS резолвинг с fallback"""
        try:
            # Сначала пробуем стандартный DNS
            ip = socket.gethostbyname(host)
            return ip
        except socket.gaierror:
            # Пробуем Google DNS API
            try:
                import requests
                response = requests.get(f"https://dns.google/resolve?name={host}&type=A")
                if response.status_code == 200:
                    data = response.json()
                    if 'Answer' in data:
                        return data['Answer'][0]['data']
            except:
                pass
            
            # Последний шанс - hardcoded IP для популярных сайтов
            hardcoded_ips = {
                'www.youtube.com': '172.217.16.14',
                'youtube.com': '172.217.16.14',
                'www.google.com': '142.250.185.78',
                'google.com': '142.250.185.78',
                'vk.com': '87.240.139.194',
                'www.vk.com': '87.240.139.194',
                'www.google.ru': '142.250.185.99',
                'google.ru': '142.250.185.99',
                'accounts.youtube.com': '172.217.16.14',
                'www.gstatic.com': '142.250.184.238'
            }
            return hardcoded_ips.get(host)
        
        return None
    
    def try_pipelines_tunnel(self, target_host, target_port):
        """Пробует пайплайны с улучшенной обработкой ошибок"""
        for i, pipeline in enumerate(self.pipelines):
            try:
                print(f"⛓️ [{i+1}/3] Пробую пайплайн: {pipeline.name}")
                
                # Резолвим хост
                ip = self.resolve_host(target_host)
                if not ip:
                    print(f"❌ Не удалось резолвить {target_host}")
                    continue
                
                # Создаем туннель через пайплайн
                if self.create_pipeline_tunnel(pipeline, target_host, target_port, ip):
                    print(f"✅ Пайплайн '{pipeline.name}' успешен!")
                    return True
                    
            except Exception as e:
                print(f"❌ Пайплайн '{pipeline.name}' ошибка: {e}")
                continue
                
            time.sleep(0.5)
        
        return False
    
    def create_pipeline_tunnel(self, pipeline, target_host, target_port, ip):
        """Создание туннеля с IP адресом"""
        try:
            # Выполняем пайплайн для проверки
            result = pipeline.execute(target_host)
            
            if not result.get('success', False):
                return False
            
            # Создаем сокет с IP
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Настройки пайплайна
            if pipeline.name == "Фин-Шторм":
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256)
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256)
                try:
                    remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, 1)
                except:
                    pass
            elif pipeline.name == "Медиа-Паразит":
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 512)
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512)
            elif pipeline.name == "Госвеб-Туннель":
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
            
            # Подключаемся к IP
            remote_sock.connect((ip, target_port))
            
            # TLS с улучшенными настройками
            if target_port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.maximum_version = ssl.TLSVersion.TLSv1_3
                
                # Добавляем поддержку слабых cipher suites если нужно
                context.set_ciphers('DEFAULT@SECLEVEL=1')
                
                # SNI маскировка
                if pipeline.name == "Фин-Шторм":
                    sni_mask = "sbp.nspk.ru"
                elif pipeline.name == "Медиа-Паразит":
                    sni_mask = "vk.com"
                elif pipeline.name == "Госвеб-Туннель":
                    sni_mask = "gosuslugi.ru"
                else:
                    sni_mask = target_host
                
                print(f"🎭 SNI маскировка под: {sni_mask}")
                ssl_sock = context.wrap_socket(remote_sock, server_hostname=sni_mask)
                remote_sock = ssl_sock
            
            # Создаем туннель
            self.relay_data(self.connection, remote_sock)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка туннеля {pipeline.name}: {e}")
            return False
    
    def relay_data(self, client_sock, remote_sock):
        """Улучшенная ретрансляция данных"""
        try:
            sockets = [client_sock, remote_sock]
            timeout = 300
            
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                
                if not readable:
                    break
                
                for sock in readable:
                    try:
                        data = sock.recv(8192)
                        if not data:
                            return
                        
                        if sock is client_sock:
                            remote_sock.send(data)
                        else:
                            client_sock.send(data)
                            
                    except Exception:
                        return
                        
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
                remote_sock.close()
            except:
                pass
    
    def handle_proxy_request(self):
        """Обработка HTTP запросов с улучшенным резолвингом"""
        try:
            parsed_url = urlparse(self.path)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            path = parsed_url.path or '/'
            
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            print(f"🌐 HTTP запрос к {host}:{port}{path}")
            
            # Резолвим хост
            ip = self.resolve_host(host)
            if not ip:
                print(f"❌ Не удалось резолвить {host}")
                self.send_error(500, "DNS resolution failed")
                return
            
            # Пробуем прямое подключение
            if self.try_direct_http(host, port, path, ip):
                return
            
            # Пробуем пайплайны
            for i, pipeline in enumerate(self.pipelines):
                try:
                    print(f"⛓️ [{i+1}/3] Пробую пайплайн: {pipeline.name}")
                    
                    response = self.make_pipeline_request(pipeline, host, port, path, ip, self.command)
                    
                    if response:
                        self.wfile.write(response)
                        print(f"✅ Пайплайн '{pipeline.name}' успешен!")
                        return
                        
                except Exception as e:
                    print(f"❌ Пайплайн '{pipeline.name}' ошибка: {e}")
                    continue
                    
                time.sleep(0.5)
            
            print(f"❌ Все методы не сработали для {host}")
            self.send_error(500, "All methods failed")
            
        except Exception as e:
            print(f"❌ Ошибка HTTP запроса: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def try_direct_http(self, host, port, path, ip):
        """Прямое HTTP подключение"""
        try:
            print(f"🔄 Пробую прямое HTTP подключение")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, port))
            
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                sock = context.wrap_socket(sock, server_hostname=host)
            
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())
            
            response = b""
            while True:
                data = sock.recv(8192)
                if not data:
                    break
                response += data
            
            sock.close()
            
            if b"HTTP" in response:
                self.wfile.write(response)
                print(f"✅ Прямое HTTP подключение успешно!")
                return True
                
        except Exception as e:
            print(f"❌ Прямое HTTP подключение не удалось: {e}")
        
        return False
    
    def make_pipeline_request(self, pipeline, host, port, path, ip, method='GET'):
        """HTTP запрос через пайплайн с IP"""
        try:
            result = pipeline.execute(host)
            
            if not result.get('success', False):
                return None
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Настройки пайплайна
            if pipeline.name == "Фин-Шторм":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256)
                try:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, 1)
                except:
                    pass
            
            sock.connect((ip, port))
            
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.set_ciphers('DEFAULT@SECLEVEL=1')
                
                if pipeline.name == "Фин-Шторм":
                    sni_mask = "sbp.nspk.ru"
                elif pipeline.name == "Медиа-Паразит":
                    sni_mask = "vk.com"
                elif pipeline.name == "Госвеб-Туннель":
                    sni_mask = "gosuslugi.ru"
                else:
                    sni_mask = host
                
                sock = context.wrap_socket(sock, server_hostname=sni_mask)
            
            headers = {
                f"{method} {path} HTTP/1.1",
                f"Host: {host}",
                "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) [SBPApp/1.5.0]",
                "Accept: */*",
                "Connection: close",
                "", ""
            }
            
            if pipeline.name == "Фин-Шторм":
                headers.insert(-2, "X-Banking-Request: true")
                headers.insert(-2, f"X-Transaction-ID: {random.randint(100000, 999999)}")
                headers.insert(-2, "X-Financial-Priority: high")
            
            request = "\r\n".join(headers)
            sock.send(request.encode())
            
            response = b""
            while True:
                data = sock.recv(8192)
                if not data:
                    break
                response += data
            
            sock.close()
            return response
            
        except Exception as e:
            print(f"❌ Ошибка запроса {pipeline.name}: {e}")
            return None
    
    def log_message(self, format, *args):
        """Кастомное логирование"""
        pass  # Отключаем лишние логи

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Многопоточный HTTP сервер"""
    daemon_threads = True

def main():
    """Запуск улучшенной прокси"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаю УЛУЧШЕННУЮ прокси с исправленными проблемами...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    print(f"🔧 Исправления:")
    print(f"   ✅ DNS резолвинг с fallback")
    print(f"   ✅ SSL/TLS улучшения")
    print(f"   ✅ Прямое подключение")
    print(f"   ✅ Hardcoded IP для популярных сайтов")
    print(f"⛓️ Пайплайны: Фин-Шторм → Медиа-Паразит → Госвеб-Туннель")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        server = ThreadedHTTPServer((host, port), RobustProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
