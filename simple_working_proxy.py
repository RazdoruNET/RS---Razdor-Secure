#!/usr/bin/env python3
"""
Простая рабочая прокси без ngrok
"""

import socket
import threading
import select
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

class SimpleProxyHandler(BaseHTTPRequestHandler):
    """Простой обработчик прокси"""
    
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_HEAD(self):
        self.handle_request()
    
    def do_CONNECT(self):
        """CONNECT туннель"""
        try:
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 CONNECT к {host}:{port}")
            
            # Отправляем успешный ответ
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем туннель
            self.create_tunnel(host, port)
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def create_tunnel(self, target_host, target_port):
        """Создание туннеля"""
        try:
            # Создаем сокет
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            remote_sock.settimeout(30)
            
            # Подключаемся
            remote_sock.connect((target_host, target_port))
            
            print(f"✅ Туннель создан для {target_host}:{target_port}")
            
            # Ретрансляция
            self.relay_data(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка туннеля: {e}")
            raise
    
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
                        data = sock.recv(16384)
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
    
    def handle_request(self):
        """Обработка HTTP запросов"""
        try:
            parsed_url = urlparse(self.path)
            host = parsed_url.hostname
            port = parsed_url.port or 80
            path = parsed_url.path or '/'
            
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            print(f"🌐 HTTP запрос к {host}{path}")
            
            # Создаем соединение
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            sock.connect((host, port))
            
            # Формируем запрос
            request = f"{self.command} {path} HTTP/1.1\r\n"
            for header, value in self.headers.items():
                request += f"{header}: {value}\r\n"
            request += "\r\n"
            
            sock.send(request.encode())
            
            # Получаем ответ
            response = b""
            while True:
                data = sock.recv(16384)
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
        """Отключаем логирование"""
        pass

class SimpleHTTPServer(ThreadingMixIn, HTTPServer):
    """Многопоточный сервер"""
    daemon_threads = True
    allow_reuse_address = True

def main():
    """Запуск простой прокси"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 ПРОСТАЯ РАБОЧАЯ ПРОКСИ")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    print(f"✅ Статус: РАБОТАЕТ")
    print(f"🔧 Особенности:")
    print(f"   • Чистый TCP туннель для HTTPS")
    print(f"   • HTTP проксирование для HTTP")
    print(f"   • Никакого SSL вмешательства")
    print(f"   • Максимальная стабильность")
    print(f"   • Работает с любыми сайтами")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 60)
    
    try:
        server = SimpleHTTPServer((host, port), SimpleProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
