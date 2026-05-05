#!/usr/bin/env python3
"""
Улучшенная прокси на базе всех пайплайнов White-Ghost
Поддерживает HTTP/HTTPS прокси для браузера с автоматическим переключением
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
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

# Импортируем пайплайны из оригинального модуля
sys.path.append('/Users/razdor/Documents/GitHub/RS---Razdor-Secure')
from rsecure.modules.defense.dpi_bypass_combiner import (
    GoswebTunnelPipeline,
    MediaParasitePipeline, 
    FinStormPipeline
)

class EnhancedProxyHandler(BaseHTTPRequestHandler):
    """Обработчик прокси запросов с всеми пайплайнами"""
    
    def __init__(self, request, client_address, server):
        self.server_class = server
        # Инициализируем пайплайны
        self.pipelines = [
            GoswebTunnelPipeline(),    # Приоритет 1: Госвеб-Туннель
            MediaParasitePipeline(),   # Приоритет 2: Медиа-Паразит
            FinStormPipeline()         # Приоритет 3: Фин-Шторм
        ]
        super().__init__(request, client_address, server)
    
    def do_GET(self):
        self.handle_proxy_request()
    
    def do_POST(self):
        self.handle_proxy_request()
    
    def do_CONNECT(self):
        """Обработка HTTPS CONNECT запросов со всеми пайплайнами"""
        try:
            # Извлекаем хост и порт из CONNECT запроса
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 HTTPS CONNECT к {host}:{port}")
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Пробуем все пайплайны для создания туннеля
            success = self.try_all_pipelines_tunnel(host, port)
            
            if not success:
                print(f"❌ Все пайплайны не сработали для {host}:{port}")
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def try_all_pipelines_tunnel(self, target_host, target_port):
        """Пробует все пайплайны для создания туннеля"""
        for pipeline in self.pipelines:
            try:
                print(f"⛓️ Пробую пайплайн: {pipeline.name} для {target_host}")
                
                # Создаем туннель через пайплайн
                if self.create_pipeline_tunnel(pipeline, target_host, target_port):
                    print(f"✅ Пайплайн '{pipeline.name}' успешен!")
                    return True
                    
            except Exception as e:
                print(f"❌ Пайплайн '{pipeline.name}' ошибка: {e}")
                continue
                
            # Небольшая пауза между пайплайнами
            time.sleep(0.5)
        
        return False
    
    def create_pipeline_tunnel(self, pipeline, target_host, target_port):
        """Создание туннеля через конкретный пайплайн"""
        try:
            # Выполняем пайплайн для проверки доступности
            result = pipeline.execute(target_host)
            
            if not result.get('success', False):
                return False
            
            # Если пайплайн успешен, создаем реальный туннель
            # с настройками этого пайплайна
            return self.create_tunnel_with_settings(pipeline, target_host, target_port)
            
        except Exception as e:
            print(f"❌ Ошибка туннеля {pipeline.name}: {e}")
            return False
    
    def create_tunnel_with_settings(self, pipeline, target_host, target_port):
        """Создание туннеля с настройками конкретного пайплайна"""
        try:
            # Базовые настройки для всех пайплайнов
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Специфичные настройки в зависимости от пайплайна
            if pipeline.name == "Фин-Шторм":
                # Настройки Фин-Шторм
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256)
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256)
                try:
                    remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, 1)
                except:
                    pass
                    
            elif pipeline.name == "Госвеб-Туннель":
                # Настройки Госвеб-Туннель
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
                
            elif pipeline.name == "Медиа-Паразит":
                # Настройки Медиа-Паразит
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 512)
                remote_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512)
            
            # Подключаемся к целевому хосту
            remote_sock.connect((target_host, target_port))
            
            # Если это HTTPS, применяем TLS с соответствующей SNI маскировкой
            if target_port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # Выбираем SNI маску в зависимости от пайплайна
                if pipeline.name == "Фин-Шторм":
                    sni_mask = "sbp.nspk.ru"
                elif pipeline.name == "Госвеб-Туннель":
                    sni_mask = "gosuslugi.ru"
                elif pipeline.name == "Медиа-Паразит":
                    sni_mask = "vk.com"
                else:
                    sni_mask = target_host
                
                print(f"🎭 SNI маскировка под: {sni_mask}")
                remote_sock = context.wrap_socket(remote_sock, server_hostname=sni_mask)
            
            # Создаем туннель между клиентом и сервером
            self.relay_data(self.connection, remote_sock)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания туннеля: {e}")
            return False
    
    def relay_data(self, client_sock, remote_sock):
        """Ретрансляция данных между клиентом и сервером"""
        try:
            sockets = [client_sock, remote_sock]
            timeout = 300  # 5 минут таймаут
            
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
                            
                    except Exception as e:
                        return
                        
        except Exception as e:
            pass
        finally:
            try:
                client_sock.close()
                remote_sock.close()
            except:
                pass
    
    def handle_proxy_request(self):
        """Обработка HTTP запросов со всеми пайплайнами"""
        try:
            parsed_url = urlparse(self.path)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            path = parsed_url.path or '/'
            
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            print(f"🌐 HTTP запрос к {host}:{port}{path}")
            
            # Пробуем все пайплайны
            for pipeline in self.pipelines:
                try:
                    print(f"⛓️ Пробую пайплайн: {pipeline.name}")
                    
                    response = self.make_pipeline_request(pipeline, host, port, path, self.command)
                    
                    if response:
                        self.wfile.write(response)
                        print(f"✅ Пайплайн '{pipeline.name}' успешен!")
                        return
                        
                except Exception as e:
                    print(f"❌ Пайплайн '{pipeline.name}' ошибка: {e}")
                    continue
                    
                time.sleep(0.5)
            
            print(f"❌ Все пайплайны не сработали для {host}")
            self.send_error(500, "All pipelines failed")
            
        except Exception as e:
            print(f"❌ Ошибка HTTP запроса: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def make_pipeline_request(self, pipeline, host, port, path, method='GET'):
        """Выполнение HTTP запроса через конкретный пайплайн"""
        try:
            # Сначала проверяем доступность через пайплайн
            result = pipeline.execute(host)
            
            if not result.get('success', False):
                return None
            
            # Создаем сокет с настройками пайплайна
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Применяем специфичные настройки
            if pipeline.name == "Фин-Шторм":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256)
                try:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, 1)
                except:
                    pass
                    
            elif pipeline.name == "Госвеб-Туннель":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
                
            elif pipeline.name == "Медиа-Паразит":
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 512)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512)
            
            sock.connect((host, port))
            
            # Если HTTPS, добавляем TLS
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # SNI маскировка
                if pipeline.name == "Фин-Шторм":
                    sni_mask = "sbp.nspk.ru"
                elif pipeline.name == "Госвеб-Туннель":
                    sni_mask = "gosuslugi.ru"
                elif pipeline.name == "Медиа-Паразит":
                    sni_mask = "vk.com"
                else:
                    sni_mask = host
                
                sock = context.wrap_socket(sock, server_hostname=sni_mask)
            
            # Формируем HTTP запрос с заголовками пайплайна
            headers = {
                f"{method} {path} HTTP/1.1",
                f"Host: {host}",
                "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) [SBPApp/1.5.0]",
                "Accept: */*",
                "Connection: close",
                "", ""
            }
            
            # Добавляем специфичные заголовки
            if pipeline.name == "Фин-Шторм":
                headers.insert(-2, "X-Banking-Request: true")
                headers.insert(-2, f"X-Transaction-ID: {random.randint(100000, 999999)}")
                headers.insert(-2, "X-Financial-Priority: high")
            elif pipeline.name == "Медиа-Паразит":
                headers.insert(-2, "X-Media-Request: true")
                headers.insert(-2, "X-Stream-Priority: high")
            elif pipeline.name == "Госвеб-Туннель":
                headers.insert(-2, "X-Government-Request: true")
                headers.insert(-2, "X-Official-Priority: high")
            
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
            print(f"❌ Ошибка запроса {pipeline.name}: {e}")
            return None
    
    def log_message(self, format, *args):
        """Кастомное логирование"""
        print(f"📋 {format % args}")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Многопоточный HTTP сервер"""
    daemon_threads = True

def main():
    """Запуск улучшенного прокси сервера"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаю улучшенную прокси со всеми пайплайнами...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    print(f"⛓️ Пайплайны:")
    print(f"   🥇 Госвеб-Туннель (SNI=gosuslugi.ru)")
    print(f"   🥈 Медиа-Паразит (SNI=vk.com)")
    print(f"   🥉 Фин-Шторм (SNI=sbp.nspk.ru)")
    print(f"🔄 Автоматическое переключение при неудаче")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        server = ThreadedHTTPServer((host, port), EnhancedProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
