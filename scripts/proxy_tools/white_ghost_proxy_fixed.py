#!/usr/bin/env python3
"""
White-Ghost Proxy Fixed Version
Исправленная версия с HTTP прокси и диагностикой ERR_PROXY_CONNECTION_FAILED
"""

import socket
import ssl
import threading
import time
import select
import struct
import sys
import os
import argparse
from typing import Dict, List, Optional, Tuple, Any
import urllib.parse
import http.server
import socketserver

# Добавляем путь к модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure/modules/defense'))

try:
    from dpi_bypass_combiner import DPIBypassCombiner
except ImportError as e:
    print(f"❌ Ошибка импорта DPI-Bypass Combiner: {e}")
    sys.exit(1)


class WhiteGhostHTTPProxy(http.server.BaseHTTPRequestHandler):
    """HTTP прокси для White-Ghost"""
    
    def __init__(self, *args, **kwargs):
        self.dpi_combiner = DPIBypassCombiner()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Обработка GET запросов"""
        self.handle_request('GET')
    
    def do_POST(self):
        """Обработка POST запросов"""
        self.handle_request('POST')
    
    def do_CONNECT(self):
        """Обработка HTTPS CONNECT запросов"""
        try:
            # Извлекаем хост и порт из запроса
            host_port = self.path.split(':')
            if len(host_port) != 2:
                self.send_error(400, "Bad Request")
                return
            
            host = host_port[0]
            port = int(host_port[1])
            
            print(f"🔗 HTTPS CONNECT: {host}:{port}")
            
            # Определяем нужно ли использовать White-Ghost
            if self.should_use_white_ghost(host):
                print(f"   👻 Использую White-Ghost для {host}")
                success = self.handle_https_white_ghost(host, port)
            else:
                print(f"   🌐 Прямое соединение с {host}")
                success = self.handle_https_direct(host, port)
            
            if not success:
                self.send_error(502, "Bad Gateway")
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            self.send_error(500, "Internal Server Error")
    
    def handle_request(self, method):
        """Обработка HTTP запросов"""
        try:
            # Извлекаем URL
            url = self.path
            if not url.startswith('http'):
                url = f"http://{self.headers.get('Host', '')}{url}"
            
            parsed_url = urllib.parse.urlparse(url)
            host = parsed_url.hostname
            port = parsed_url.port or 80
            
            print(f"🔗 {method} {url}")
            
            # Определяем нужно ли использовать White-Ghost
            if self.should_use_white_ghost(host):
                print(f"   👻 Использую White-Ghost для {host}")
                success = self.handle_http_white_ghost(method, url, parsed_url)
            else:
                print(f"   🌐 Прямое соединение с {host}")
                success = self.handle_http_direct(method, url, parsed_url)
            
            if not success:
                self.send_error(502, "Bad Gateway")
                
        except Exception as e:
            print(f"❌ Ошибка {method}: {e}")
            self.send_error(500, "Internal Server Error")
    
    def should_use_white_ghost(self, hostname: str) -> bool:
        """Определяет нужно ли использовать White-Ghost"""
        hostname = hostname.lower()
        
        # Список доменов для обхода
        white_ghost_domains = {
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'youtu.be', 'ytimg.com', 'googlevideo.com',
            'googleapis.com', 'gstatic.com', 'ggpht.com'
        }
        
        # Проверяем точное совпадение
        if hostname in white_ghost_domains:
            return True
        
        # Проверяем поддомены
        for domain in white_ghost_domains:
            if hostname.endswith('.' + domain) or hostname.endswith(domain):
                return True
        
        return False
    
    def handle_http_white_ghost(self, method: str, url: str, parsed_url) -> bool:
        """Обработка HTTP через White-Ghost"""
        try:
            # Используем White-Ghost для создания соединения
            host = parsed_url.hostname
            port = parsed_url.port or 80
            
            # Создаем сокет через White-Ghost
            remote_socket = self.create_white_ghost_socket(host, port, use_https=False)
            if not remote_socket:
                return False
            
            # Отправляем запрос
            request_line = f"{method} {parsed_url.path} HTTP/1.1\r\n"
            headers = dict(self.headers)
            headers['Host'] = host
            
            request = request_line
            for key, value in headers.items():
                request += f"{key}: {value}\r\n"
            request += "\r\n"
            
            remote_socket.send(request.encode())
            
            # Получаем ответ и пересылаем клиенту
            self.forward_response(remote_socket)
            
            remote_socket.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка White-Ghost HTTP: {e}")
            return False
    
    def handle_http_direct(self, method: str, url: str, parsed_url) -> bool:
        """Обработка HTTP напрямую"""
        try:
            host = parsed_url.hostname
            port = parsed_url.port or 80
            
            # Создаем прямое соединение
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, port))
            
            # Отправляем запрос
            request_line = f"{method} {parsed_url.path} HTTP/1.1\r\n"
            headers = dict(self.headers)
            headers['Host'] = host
            
            request = request_line
            for key, value in headers.items():
                request += f"{key}: {value}\r\n"
            request += "\r\n"
            
            remote_socket.send(request.encode())
            
            # Получаем ответ и пересылаем клиенту
            self.forward_response(remote_socket)
            
            remote_socket.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка прямого HTTP: {e}")
            return False
    
    def handle_https_white_ghost(self, host: str, port: int) -> bool:
        """Обработка HTTPS через White-Ghost"""
        try:
            # Создаем соединение через White-Ghost
            remote_socket = self.create_white_ghost_socket(host, port, use_https=True)
            if not remote_socket:
                return False
            
            # Отправляем успешный ответ
            self.send_response(200, "Connection established")
            
            # Перенаправляем данные между клиентом и удаленным сервером
            self.relay_data(self.connection, remote_socket)
            
            remote_socket.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка White-Ghost HTTPS: {e}")
            return False
    
    def handle_https_direct(self, host: str, port: int) -> bool:
        """Обработка HTTPS напрямую"""
        try:
            # Создаем прямое соединение
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, port))
            
            # Отправляем успешный ответ
            self.send_response(200, "Connection established")
            
            # Перенаправляем данные между клиентом и удаленным сервером
            self.relay_data(self.connection, remote_socket)
            
            remote_socket.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка прямого HTTPS: {e}")
            return False
    
    def create_white_ghost_socket(self, target_host: str, target_port: int, use_https: bool = True) -> Optional[socket.socket]:
        """Создание сокета через White-Ghost"""
        try:
            # Пробуем разные цепочки White-Ghost
            pipelines = [
                self.dpi_combiner.fin_storm,      # Приоритет 1: Фин-Шторм
                self.dpi_combiner.gosweb_tunnel,  # Приоритет 2: Госвеб-Туннель
                self.dpi_combiner.media_parasite  # Приоритет 3: Медиа-Паразит
            ]
            
            for pipeline in pipelines:
                try:
                    print(f"      🔄 Пробую цепочку: {pipeline.name}")
                    
                    # Создаем базовый сокет
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # Применяем техники цепочки
                    if hasattr(pipeline, 'rotate_sni_mask'):
                        sni_mask = pipeline.rotate_sni_mask()
                        sock.connect((target_host, target_port))
                        
                        if use_https:
                            context = ssl.create_default_context()
                            context.check_hostname = False
                            context.verify_mode = ssl.CERT_NONE
                            
                            ssl_sock = context.wrap_socket(sock, server_hostname=sni_mask)
                            print(f"      ✅ Цепочка '{pipeline.name}' успешна")
                            return ssl_sock
                        else:
                            print(f"      ✅ Цепочка '{pipeline.name}' успешна")
                            return sock
                    else:
                        sock.connect((target_host, target_port))
                        return sock
                        
                except Exception as e:
                    print(f"      ❌ Цепочка '{pipeline.name}' ошибка: {e}")
                    continue
            
            print(f"      ❌ Все White-Ghost цепочки не сработали")
            return None
            
        except Exception as e:
            print(f"      ❌ Ошибка создания сокета: {e}")
            return None
    
    def forward_response(self, remote_socket: socket.socket):
        """Пересылка ответа от сервера клиенту"""
        try:
            response = remote_socket.recv(8192)
            while response:
                self.wfile.write(response)
                response = remote_socket.recv(8192)
        except:
            pass
    
    def relay_data(self, client_socket: socket.socket, remote_socket: socket.socket):
        """Перенаправление данных между сокетами"""
        try:
            sockets = [client_socket, remote_socket]
            timeout = 300
            
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                
                if not readable:
                    break
                
                for sock in readable:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            return True
                        
                        # Отправляем данные другому сокету
                        if sock is client_socket:
                            remote_socket.send(data)
                        else:
                            client_socket.send(data)
                            
                    except:
                        return False
                        
        except:
            pass
        finally:
            try:
                remote_socket.close()
            except:
                pass
        
        return True


class WhiteGhostProxyFixed:
    """Исправленный White-Ghost Proxy с HTTP и SOCKS5"""
    
    def __init__(self, http_port: int = 8080, socks_port: int = 1080):
        self.http_port = http_port
        self.socks_port = socks_port
        self.http_server = None
        self.socks_server = None
        self.running = False
        
        # Статистика
        self.stats = {
            'connections': 0,
            'white_ghost_used': 0,
            'direct_used': 0,
            'errors': 0
        }
    
    def start_http_proxy(self):
        """Запуск HTTP прокси"""
        try:
            print(f"🚀 Запускаю HTTP прокси на порту {self.http_port}")
            
            with socketserver.TCPServer(("", self.http_port), WhiteGhostHTTPProxy) as httpd:
                self.http_server = httpd
                print(f"✅ HTTP прокси запущен на 127.0.0.1:{self.http_port}")
                
                # Запускаем в отдельном потоке
                import threading
                thread = threading.Thread(target=httpd.serve_forever)
                thread.daemon = True
                thread.start()
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка запуска HTTP прокси: {e}")
            return False
    
    def start_socks_proxy(self):
        """Запуск SOCKS5 прокси"""
        try:
            print(f"🚀 Запускаю SOCKS5 прокси на порту {self.socks_port}")
            
            # Создаем SOCKS5 сервер
            self.socks_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socks_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socks_server.bind(("", self.socks_port))
            self.socks_server.listen(5)
            
            print(f"✅ SOCKS5 прокси запущен на 127.0.0.1:{self.socks_port}")
            
            # Запускаем в отдельном потоке
            import threading
            thread = threading.Thread(target=self.socks5_handler)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка запуска SOCKS5 прокси: {e}")
            return False
    
    def socks5_handler(self):
        """Обработчик SOCKS5 соединений"""
        while self.running:
            try:
                client_socket, client_address = self.socks_server.accept()
                print(f"🔗 Новое SOCKS5 соединение от {client_address[0]}:{client_address[1]}")
                
                # Создаем поток для обработки клиента
                client_thread = threading.Thread(
                    target=self.handle_socks5_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.stats['connections'] += 1
                
            except OSError:
                break
            except Exception as e:
                print(f"❌ Ошибка SOCKS5: {e}")
    
    def handle_socks5_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Обработка SOCKS5 клиента"""
        try:
            # SOCKS5 рукопожатие
            if not self.socks5_handshake(client_socket):
                return
            
            # SOCKS5 запрос
            if not self.socks5_request(client_socket):
                return
            
            # Получаем целевой адрес
            target_host, target_port = self.get_target_address(client_socket)
            if not target_host:
                return
            
            print(f"🎯 SOCKS5 запрос: {target_host}:{target_port}")
            
            # Создаем соединение
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((target_host, target_port))
            
            # Отправляем успешный ответ
            response = b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + struct.pack('>H', 0)
            client_socket.send(response)
            
            # Перенаправляем данные
            self.relay_data(client_socket, remote_socket)
            
        except Exception as e:
            print(f"❌ Ошибка SOCKS5 клиента: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def socks5_handshake(self, client_socket: socket.socket) -> bool:
        """SOCKS5 рукопожатие"""
        try:
            data = client_socket.recv(262)
            if len(data) < 3 or data[0] != 5:
                return False
            
            client_socket.send(b'\x05\x00')
            return True
        except:
            return False
    
    def socks5_request(self, client_socket: socket.socket) -> bool:
        """SOCKS5 запрос"""
        try:
            data = client_socket.recv(262)
            if len(data) < 10 or data[0] != 5 or data[1] != 1:
                return False
            
            response = b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + struct.pack('>H', 0)
            client_socket.send(response)
            return True
        except:
            return False
    
    def get_target_address(self, client_socket: socket.socket) -> Tuple[str, int]:
        """Получение целевого адреса"""
        try:
            data = client_socket.recv(262)
            if len(data) < 7:
                return None, None
            
            addr_type = data[3]
            
            if addr_type == 1:  # IPv4
                if len(data) < 10:
                    return None, None
                host = socket.inet_ntoa(data[4:8])
                port = struct.unpack('>H', data[8:10])[0]
            elif addr_type == 3:  # Доменное имя
                if len(data) < 5:
                    return None, None
                domain_len = data[4]
                if len(data) < 5 + domain_len + 2:
                    return None, None
                host = data[5:5+domain_len].decode('utf-8')
                port = struct.unpack('>H', data[5+domain_len:5+domain_len+2])[0]
            else:
                return None, None
            
            return host, port
            
        except:
            return None, None
    
    def relay_data(self, client_socket: socket.socket, remote_socket: socket.socket):
        """Перенаправление данных"""
        try:
            sockets = [client_socket, remote_socket]
            timeout = 300
            
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                
                if not readable:
                    break
                
                for sock in readable:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            return
                        
                        if sock is client_socket:
                            remote_socket.send(data)
                        else:
                            client_socket.send(data)
                            
                    except:
                        return
                        
        except:
            pass
        finally:
            try:
                remote_socket.close()
            except:
                pass
    
    def start(self):
        """Запуск обоих прокси"""
        print("👻 White-Ghost Proxy Fixed Version")
        print("=" * 50)
        
        self.running = True
        
        # Запускаем HTTP прокси
        if not self.start_http_proxy():
            return False
        
        # Запускаем SOCKS5 прокси
        if not self.start_socks_proxy():
            return False
        
        print(f"\n🎯 Оба прокси запущены:")
        print(f"   🌐 HTTP прокси: 127.0.0.1:{self.http_port}")
        print(f"   🧦 SOCKS5 прокси: 127.0.0.1:{self.socks_port}")
        print(f"\n📋 Используйте HTTP прокси для лучшей совместимости")
        print(f"⏹️ Нажмите Ctrl+C для остановки")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n⏹️ Остановка прокси...")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Остановка прокси"""
        self.running = False
        
        if self.http_server:
            self.http_server.shutdown()
        
        if self.socks_server:
            self.socks_server.close()
        
        print(f"📊 Статистика:")
        print(f"   🔗 Всего соединений: {self.stats['connections']}")
        print(f"   👻 White-Ghost использован: {self.stats['white_ghost_used']}")
        print(f"   🌐 Прямых соединений: {self.stats['direct_used']}")
        print(f"   ❌ Ошибок: {self.stats['errors']}")
        print(f"🏁 Прокси остановлен")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='White-Ghost Proxy Fixed Version')
    parser.add_argument('--http-port', type=int, default=8080, help='Порт HTTP прокси')
    parser.add_argument('--socks-port', type=int, default=1080, help='Порт SOCKS5 прокси')
    parser.add_argument('--test', action='store_true', help='Тестировать прокси')
    
    args = parser.parse_args()
    
    proxy = WhiteGhostProxyFixed(args.http_port, args.socks_port)
    
    if args.test:
        print("🧪 Тестирование прокси...")
        # Здесь можно добавить тесты
        return
    
    proxy.start()


if __name__ == "__main__":
    main()
