#!/usr/bin/env python3
"""
Простая прокси с минимальными настройками для стабильной работы
"""

import socket
import ssl
import threading
import select
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

class SimpleProxyHandler(BaseHTTPRequestHandler):
    """Простой обработчик с базовыми настройками"""
    
    def do_GET(self):
        self.handle_proxy_request()
    
    def do_POST(self):
        self.handle_proxy_request()
    
    def do_CONNECT(self):
        """Простая обработка HTTPS с минимальными настройками"""
        try:
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 HTTPS CONNECT к {host}:{port}")
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем туннель с минимальными настройками
            self.create_simple_tunnel(host, port)
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def create_simple_tunnel(self, target_host, target_port):
        """Создание простого туннеля"""
        try:
            # Создаем сокет с базовыми настройками
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(15)  # Увеличенный таймаут
            
            # Подключаемся напрямую
            remote_sock.connect((target_host, target_port))
            
            # Если HTTPS, создаем TLS с совместимыми настройками
            if target_port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # Максимально совместимые настройки
                context.minimum_version = ssl.TLSVersion.TLSv1_0
                context.maximum_version = ssl.TLSVersion.TLSv1_3
                
                # Широкий набор cipher suites
                context.set_ciphers('ALL:@SECLEVEL=0')
                
                # Отключаем SNI для проблемных сайтов
                try:
                    ssl_sock = context.wrap_socket(remote_sock, server_hostname=target_host)
                except ssl.SSLError:
                    # Если SNI вызывает проблемы, пробуем без него
                    ssl_sock = context.wrap_socket(remote_sock, server_hostname=None)
                
                remote_sock = ssl_sock
            
            print(f"✅ Туннель создан для {target_host}:{target_port}")
            self.relay_data(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка туннеля: {e}")
            raise
    
    def relay_data(self, client_sock, remote_sock):
        """Ретрансляция данных с обработкой ошибок"""
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
                            
                    except (ConnectionResetError, BrokenPipeError):
                        return
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
        """Обработка HTTP запросов"""
        try:
            parsed_url = urlparse(self.path)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            path = parsed_url.path or '/'
            
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            print(f"🌐 HTTP запрос к {host}:{port}{path}")
            
            # Создаем соединение
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            
            sock.connect((host, port))
            
            if port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.minimum_version = ssl.TLSVersion.TLSv1_0
                context.set_ciphers('ALL:@SECLEVEL=0')
                
                try:
                    sock = context.wrap_socket(sock, server_hostname=host)
                except ssl.SSLError:
                    sock = context.wrap_socket(sock, server_hostname=None)
            
            # Простой HTTP запрос
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())
            
            response = b""
            while True:
                data = sock.recv(8192)
                if not data:
                    break
                response += data
            
            sock.close()
            
            if response:
                self.wfile.write(response)
                print(f"✅ HTTP запрос успешен для {host}")
            else:
                self.send_error(500, "No response")
                
        except Exception as e:
            print(f"❌ Ошибка HTTP запроса: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def log_message(self, format, *args):
        """Минимальное логирование"""
        pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Многопоточный HTTP сервер"""
    daemon_threads = True

def main():
    """Запуск простой прокси"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаю ПРОСТУЮ прокси...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    print(f"🔧 Настройки:")
    print(f"   ✅ Минимальные SSL/TLS настройки")
    print(f"   ✅ Широкий набор cipher suites")
    print(f"   ✅ Fallback без SNI")
    print(f"   ✅ Увеличенные таймауты")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 40)
    
    try:
        server = ThreadedHTTPServer((host, port), SimpleProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
