#!/usr/bin/env python3
"""
Прокси с интеграцией ngrok для обхода DPI
"""

import socket
import threading
import select
import subprocess
import time
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

class NgrokProxyHandler(BaseHTTPRequestHandler):
    """Прокси с ngrok интеграцией"""
    
    def __init__(self, request, client_address, server):
        self.server_class = server
        self.ngrok_url = getattr(server, 'ngrok_url', None)
        super().__init__(request, client_address, server)
    
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_HEAD(self):
        self.handle_request()
    
    def do_CONNECT(self):
        """CONNECT через ngrok если нужно"""
        try:
            host_port = self.path.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            
            print(f"🔗 CONNECT к {host}:{port}")
            
            # Проверяем заблокированные сайты
            if self.is_blocked_site(host):
                print(f"🚨 {host} заблокирован, используем ngrok")
                return self.handle_ngrok_connect(host, port)
            else:
                print(f"✅ {host} доступен напрямую")
                return self.handle_direct_connect(host, port)
                
        except Exception as e:
            print(f"❌ Ошибка CONNECT: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def is_blocked_site(self, host):
        """Проверяем заблокированные сайты"""
        blocked_sites = [
            'youtube.com', 'www.youtube.com', 'youtu.be',
            'vk.com', 'www.vk.com', 'm.vk.com',
            'facebook.com', 'www.facebook.com',
            'instagram.com', 'www.instagram.com',
            'twitter.com', 'www.twitter.com',
            'telegram.org', 't.me'
        ]
        
        return any(blocked in host for blocked in host.lower())
    
    def handle_direct_connect(self, target_host, target_port):
        """Прямое подключение"""
        try:
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем прямой туннель
            self.create_tunnel(target_host, target_port)
            
        except Exception as e:
            print(f"❌ Ошибка прямого подключения: {e}")
            raise
    
    def handle_ngrok_connect(self, target_host, target_port):
        """Подключение через ngrok"""
        try:
            if not self.ngrok_url:
                print("❌ Ngrok URL недоступен")
                self.send_error(503, "Ngrok not available")
                return
            
            # Отправляем 200 Connection established
            self.wfile.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
            
            # Создаем туннель через ngrok
            self.create_ngrok_tunnel(target_host, target_port)
            
        except Exception as e:
            print(f"❌ Ошибка ngrok подключения: {e}")
            raise
    
    def create_tunnel(self, target_host, target_port):
        """Создание прямого туннеля"""
        try:
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(30)
            
            remote_sock.connect((target_host, target_port))
            
            print(f"✅ Прямой туннель создан для {target_host}:{target_port}")
            self.relay_data(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка туннеля: {e}")
            raise
    
    def create_ngrok_tunnel(self, target_host, target_port):
        """Создание туннеля через ngrok"""
        try:
            # Подключаемся к ngrok серверу
            ngrok_host = self.ngrok_url.split('//')[1].split(':')[0]
            ngrok_port = 80  # Ngrok HTTP порт
            
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(30)
            
            remote_sock.connect((ngrok_host, ngrok_port))
            
            # Создаем HTTP запрос к ngrok прокси
            ngrok_request = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
            ngrok_request += f"Host: {ngrok_host}\r\n"
            ngrok_request += "Proxy-Connection: Keep-Alive\r\n\r\n"
            
            remote_sock.send(ngrok_request.encode())
            
            # Получаем ответ
            response = remote_sock.recv(1024)
            if b"200" not in response:
                raise Exception(f"Ngrok connect failed: {response}")
            
            print(f"✅ Ngrok туннель создан для {target_host}:{target_port}")
            self.relay_data(self.connection, remote_sock)
            
        except Exception as e:
            print(f"❌ Ошибка ngrok туннеля: {e}")
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
            
            # Проверяем блокировку
            if self.is_blocked_site(host):
                print(f"🚨 {host} заблокирован, используем ngrok")
                return self.handle_ngrok_http(host, port, path)
            else:
                print(f"✅ {host} доступен напрямую")
                return self.handle_direct_http(host, port, path)
                
        except Exception as e:
            print(f"❌ Ошибка HTTP запроса: {e}")
            try:
                self.send_error(500, f"Proxy Error: {str(e)}")
            except:
                pass
    
    def handle_direct_http(self, host, port, path):
        """Прямой HTTP запрос"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            sock.connect((host, port))
            
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            sock.send(request.encode())
            
            response = b""
            while True:
                data = sock.recv(16384)
                if not data:
                    break
                response += data
            
            sock.close()
            
            if response:
                self.wfile.write(response)
                print(f"✅ Прямой HTTP успешен для {host}")
            else:
                self.send_error(500, "No response")
                
        except Exception as e:
            print(f"❌ Ошибка прямого HTTP: {e}")
            raise
    
    def handle_ngrok_http(self, host, port, path):
        """HTTP запрос через ngrok"""
        try:
            if not self.ngrok_url:
                print("❌ Ngrok URL недоступен")
                self.send_error(503, "Ngrok not available")
                return
            
            ngrok_host = self.ngrok_url.split('//')[1].split(':')[0]
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            sock.connect((ngrok_host, 80))
            
            # HTTP запрос через ngrok
            request = f"GET http://{host}:{port}{path} HTTP/1.1\r\n"
            request += f"Host: {host}\r\n"
            request += "Proxy-Connection: Keep-Alive\r\n\r\n"
            
            sock.send(request.encode())
            
            response = b""
            while True:
                data = sock.recv(16384)
                if not data:
                    break
                response += data
            
            sock.close()
            
            if response:
                self.wfile.write(response)
                print(f"✅ Ngrok HTTP успешен для {host}")
            else:
                self.send_error(500, "No response")
                
        except Exception as e:
            print(f"❌ Ошибка ngrok HTTP: {e}")
            raise
    
    def log_message(self, format, *args):
        """Минимальное логирование"""
        pass

class NgrokHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP сервер с ngrok поддержкой"""
    daemon_threads = True
    allow_reuse_address = True

def start_ngrok():
    """Запуск ngrok туннеля"""
    try:
        print("🚀 Запускаем ngrok...")
        
        # Запускаем ngrok
        process = subprocess.Popen([
            'ngrok', 'http', '8080', 
            '--log=stdout',
            '--log-format=json'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Ждем получения URL
        ngrok_url = None
        for line in process.stdout:
            try:
                data = json.loads(line)
                if data.get('addr'):
                    ngrok_url = f"https://{data['addr']}"
                    print(f"✅ Ngrok URL: {ngrok_url}")
                    return ngrok_url
            except:
                continue
        
        # Fallback: пробуем получить URL из API
        time.sleep(3)
        try:
            response = requests.get('http://127.0.0.1:4040/api/tunnels')
            tunnels = response.json()
            if tunnels['tunnels']:
                ngrok_url = tunnels['tunnels'][0]['public_url']
                print(f"✅ Ngrok URL (API): {ngrok_url}")
                return ngrok_url
        except:
            pass
        
        print("❌ Не удалось получить ngrok URL")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка запуска ngrok: {e}")
        return None

def check_ngrok():
    """Проверяем доступность ngrok"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        print(f"🔧 Ngrok: {result.stdout.strip()}")
        return True
    except:
        print("❌ Ngrok не найден. Установите:")
        print("   brew install ngrok")
        print("   или скачайте с https://ngrok.com/download")
        return False

def main():
    """Запуск прокси с ngrok"""
    if not check_ngrok():
        return
    
    host = "127.0.0.1"
    port = 8080
    
    print(f"🚀 Запускаем ПРОКСИ + NGROK...")
    print(f"📍 Адрес: {host}:{port}")
    print(f"🌐 Для браузера: http://{host}:{port}")
    
    # Запускаем ngrok в отдельном потоке
    ngrok_thread = threading.Thread(target=start_ngrok)
    ngrok_thread.daemon = True
    ngrok_thread.start()
    
    # Ждем ngrok
    time.sleep(5)
    
    # Проверяем ngrok URL
    ngrok_url = None
    try:
        response = requests.get('http://127.0.0.1:4040/api/tunnels')
        tunnels = response.json()
        if tunnels['tunnels']:
            ngrok_url = tunnels['tunnels'][0]['public_url']
    except:
        pass
    
    if not ngrok_url:
        print("⚠️ Ngrok URL не получен, работаем в режиме прямой прокси")
    
    print(f"🔧 Режим работы:")
    print(f"   ✅ Прямое подключение для доступных сайтов")
    print(f"   🚨 Ngrok обход для заблокированных")
    print(f"   📋 Заблокированные: YouTube, VK, Facebook, Twitter")
    print(f"⚡ Нажмите Ctrl+C для остановки")
    print("-" * 60)
    
    try:
        server = NgrokHTTPServer((host, port), NgrokProxyHandler)
        server.ngrok_url = ngrok_url
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Остановка сервера...")
        server.shutdown()
        print(f"✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

if __name__ == "__main__":
    main()
