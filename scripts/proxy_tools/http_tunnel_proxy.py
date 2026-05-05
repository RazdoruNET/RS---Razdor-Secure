#!/usr/bin/env python3
"""
HTTP туннель без SSL вмешательства
Простая прокси которая работает как HTTP туннель
"""

import socket
import threading
import select
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

class HTTPTunnelHandler(BaseHTTPRequestHandler):
    """HTTP туннель без SSL обработки"""
    
    def do_GET(self):
        self.handle_tunnel()
    
    def do_POST(self):
        self.handle_tunnel()
    
    def do_HEAD(self):
        self.handle_tunnel()
    
    def do_CONNECT(self):
        """CONNECT туннель - просто проксирование TCP"""
        try:
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 CONNECT туннель к {host}:{port}")
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем TCP туннель без SSL
            self.create_tcp_tunnel(host, port)
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def create_tcp_tunnel(self, target_host, target_port):
        """Простой TCP туннель"""
        try:
            # Создаем сокет к цели
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(30)
            
            # Прямое подключение
            remote_sock.connect((target_host, target_port))
            
            print(f"✅ TCP туннель создан для {target_host}:{target_port}")
            
            # Простая ретрансляция байтов
            self.relay_bytes(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка TCP туннеля: {e}")
            raise
    
    def relay_bytes(self, client_sock, remote_sock):
        """Ретрансляция байтов без анализа"""
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
                        
                        # Отправляем данные как есть без обработки
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
    
    def handle_tunnel(self):
        """Обработка обычных HTTP запросов"""
        try:
            # Извлекаем хост из запроса
            host = self.headers.get('Host', '')
            if not host:
                self.send_error(400, "Bad Request")
                return
            
            print(f"🌐 HTTP запрос к {host}{self.path}")
            
            # Создаем соединение
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            # Определяем порт
            if ':' in host:
                host, port = host.split(':')
                port = int(port)
            else:
                port = 80
            
            sock.connect((host, port))
            
            # Пересылаем запрос как есть
            request = f"{self.command} {self.path} HTTP/1.1\r\n"
            for header, value in self.headers.items():
                request += f"{header}: {value}\r\n"
            request += "\r\n"
            
            sock.send(request.encode())
            
            # Получаем ответ
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
    """Запуск HTTP туннеля"""
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаю HTTP ТУННЕЛЬ...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    print(f"🔧 Принцип работы:")
    print(f"   ✅ TCP туннель для HTTPS (CONNECT)")
    print(f"   ✅ HTTP проксирование для HTTP")
    print(f"   ✅ Никакого SSL вмешательства")
    print(f"   ✅ Максимальная совместимость")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 50)
    
    try:
        server = ThreadedHTTPServer((host, port), HTTPTunnelHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
