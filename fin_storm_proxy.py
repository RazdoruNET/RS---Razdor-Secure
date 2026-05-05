#!/usr/bin/env python3
"""
Локальная прокси на базе модуля Фин-Шторм для обхода DPI
Поддерживает HTTP/HTTPS прокси для браузера
"""

import socket
import ssl
import threading
import select
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
import sys

class FinStormProxyHandler(BaseHTTPRequestHandler):
    """Обработчик прокси запросов с техниками Фин-Шторм"""
    
    def __init__(self, request, client_address, server):
        self.server_class = server
        super().__init__(request, client_address, server)
    
    def do_GET(self):
        self.handle_proxy_request()
    
    def do_POST(self):
        self.handle_proxy_request()
    
    def do_CONNECT(self):
        """Обработка HTTPS CONNECT запросов"""
        try:
            # Извлекаем хост и порт из CONNECT запроса
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 HTTPS CONNECT к {host}:{port}")
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем туннель с техниками Фин-Шторм
            self.create_fin_storm_tunnel(host, port)
            
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            self.send_error(500, f"Proxy Error: {str(e)}")
    
    def create_fin_storm_tunnel(self, target_host, target_port):
        """Создание туннеля с техниками Фин-Шторм"""
        try:
            print(f"⛓️ Создаю Фин-Шторм туннель к {target_host}")
            
            # Этап 1: Создаем сокет с настройками Фин-Шторм
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Минимальные буферы
            remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256)
            remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256)
            remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # TCP Window Scaling = 1
            try:
                remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, 1)
            except:
                pass
            
            # Подключаемся к целевому хосту
            remote_sock.connect((target_host, target_port))
            
            # Если это HTTPS (порт 443), применяем SNI маскировку
            if target_port == 443:
                print(f"🎭 Применяю SNI маскировку под sbp.nspk.ru")
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                remote_sock = context.wrap_socket(remote_sock, server_hostname="sbp.nspk.ru")
            
            # Этап 2: Создаем туннель между клиентом и сервером
            self.relay_data(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка туннеля: {e}")
            raise
    
    def relay_data(self, client_sock, remote_sock):
        """Ретрансляция данных между клиентом и сервером"""
        try:
            sockets = [client_sock, remote_sock]
            timeout = 300  # 5 минут таймаут
            
            while True:
                # Используем select для мониторинга сокетов
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)
                
                if exceptional:
                    break
                
                if not readable:
                    # Таймаут
                    break
                
                for sock in readable:
                    try:
                        data = sock.recv(8192)
                        if not data:
                            # Соединение закрыто
                            return
                        
                        # Отправляем данные другому сокету
                        if sock is client_sock:
                            remote_sock.send(data)
                        else:
                            client_sock.send(data)
                            
                    except Exception as e:
                        print(f"❌ Ошибка ретрансляции: {e}")
                        return
                        
        except Exception as e:
            print(f"❌ Ошибка туннеля: {e}")
        finally:
            try:
                client_sock.close()
                remote_sock.close()
            except:
                pass
    
    def handle_proxy_request(self):
        """Обработка HTTP запросов"""
        try:
            # Парсим URL
            parsed_url = urlparse(self.path)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            path = parsed_url.path or '/'
            
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            print(f"🌐 HTTP запрос к {host}:{port}{path}")
            
            # Создаем соединение с техниками Фин-Шторм
            response = self.make_fin_storm_request(host, port, path, self.command)
            
            # Отправляем ответ клиенту
            self.wfile.write(response)
            
        except Exception as e:
            print(f"❌ Ошибка HTTP запроса: {e}")
            self.send_error(500, f"Proxy Error: {str(e)}")
    
    def make_fin_storm_request(self, host, port, path, method='GET'):
        """Выполнение HTTP запроса с техниками Фин-Шторм"""
        try:
            # Создаем сокет с настройками Фин-Шторм
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Минимальные буферы
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # TCP Window Scaling = 1
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, 1)
            except:
                pass
            
            sock.connect((host, port))
            
            # Если HTTPS, добавляем TLS с SNI маскировкой
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname="sbp.nspk.ru")
            
            # Формируем HTTP запрос с банковскими заголовками
            headers = {
                f"{method} {path} HTTP/1.1",
                f"Host: {host}",
                "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) [SBPApp/1.5.0]",
                "Accept: */*",
                "X-Banking-Request: true",
                f"X-Transaction-ID: {random.randint(100000, 999999)}",
                "X-Financial-Priority: high",
                "Connection: close",
                "", ""
            }
            
            request = "\r\n".join(headers)
            sock.send(request.encode())
            
            # Получаем ответ
            response = b""
            while True:
                data = sock.recv(8192)
                if not data:
                    break
                response += data
            
            sock.close()
            return response
            
        except Exception as e:
            print(f"❌ Ошибка запроса Фин-Шторм: {e}")
            raise
    
    def log_message(self, format, *args):
        """Кастомное логирование"""
        print(f"📋 {format % args}")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Многопоточный HTTP сервер"""
    daemon_threads = True

def main():
    """Запуск прокси сервера"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаю Фин-Шторм прокси сервер...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    print(f"🔧 Для HTTPS: CONNECT метод поддерживается")
    print(f"⛓️ Техники: TCP Window=1, SNI=sbp.nspk.ru, Banking headers")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        server = ThreadedHTTPServer((host, port), FinStormProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
