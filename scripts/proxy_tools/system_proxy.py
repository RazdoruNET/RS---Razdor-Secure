#!/usr/bin/env python3
"""
Прокси с системными SSL настройками для macOS LibreSSL
"""

import socket
import ssl
import threading
import select
import subprocess
import platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

class SystemProxyHandler(BaseHTTPRequestHandler):
    """Прокси с системными SSL настройками"""
    
    def do_GET(self):
        self.handle_proxy_request()
    
    def do_POST(self):
        self.handle_proxy_request()
    
    def do_CONNECT(self):
        """CONNECT с системными SSL настройками"""
        try:
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 HTTPS CONNECT к {host}:{port}")
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем туннель
            self.create_system_tunnel(host, port)
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def create_system_tunnel(self, target_host, target_port):
        """Туннель с системными SSL настройками"""
        try:
            # Создаем сокет
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(20)
            
            # Подключаемся
            remote_sock.connect((target_host, target_port))
            
            # Если HTTPS, используем системные настройки SSL
            if target_port == 443:
                ssl_sock = self.create_system_ssl(remote_sock, target_host)
                remote_sock = ssl_sock
            
            print(f"✅ Туннель создан для {target_host}:{target_port}")
            self.relay_data(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка туннеля: {e}")
            raise
    
    def create_system_ssl(self, sock, hostname):
        """Создание SSL с системными настройками"""
        # Проверяем систему
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Для macOS LibreSSL используем системные настройки
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Не устанавливаем минимальную версию - используем системную
            # Не устанавливаем cipher suites - используем системные
            
            try:
                return context.wrap_socket(sock, server_hostname=hostname)
            except ssl.SSLError as e:
                print(f"   ⚠️ Пробуем без SNI: {e}")
                # Fallback без SNI
                return context.wrap_socket(sock, server_hostname=None)
        
        else:
            # Для других систем
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            try:
                return context.wrap_socket(sock, server_hostname=hostname)
            except ssl.SSLError:
                return context.wrap_socket(sock, server_hostname=None)
    
    def relay_data(self, client_sock, remote_sock):
        """Ретрансляция данных"""
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
            sock.settimeout(20)
            
            sock.connect((host, port))
            
            if port == 443:
                ssl_sock = self.create_system_ssl(sock, host)
                sock = ssl_sock
            
            # HTTP запрос
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

def check_system_info():
    """Проверка системной информации"""
    system = platform.system()
    print(f"🖥️  Система: {system}")
    
    if system == "Darwin":
        try:
            # Проверяем версию LibreSSL
            result = subprocess.run(['openssl', 'version'], capture_output=True, text=True)
            print(f"🔐 OpenSSL/LibreSSL: {result.stdout.strip()}")
        except:
            print("🔐 OpenSSL/LibreSSL: не определено")
    
    print(f"🐍 Python: {platform.python_version()}")
    
    # Проверяем SSL
    try:
        print(f"🔧 SSL: {ssl.OPENSSL_VERSION}")
    except:
        print("🔧 SSL: информация недоступна")

def main():
    """Запуск системной прокси"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаю СИСТЕМНУЮ прокси...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    
    check_system_info()
    
    print(f"🔧 Настройки:")
    print(f"   ✅ Системные SSL/TLS настройки")
    print(f"   ✅ Автоопределение cipher suites")
    print(f"   ✅ Fallback без SNI")
    print(f"   ✅ Совместимость с macOS LibreSSL")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        server = ThreadedHTTPServer((host, port), SystemProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
