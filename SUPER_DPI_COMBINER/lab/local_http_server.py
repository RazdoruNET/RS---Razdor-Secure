#!/usr/bin/env python3
"""
Local HTTP Server - Детерминированный сервер для DPI экспериментов
Работает без nginx/apache
"""

import sys
import time
import socket
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class LocalHTTPServer:
    """Детерминированный HTTP сервер"""
    
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.request_count = 0
        
    def handle_request(self, client_socket, client_address):
        """Обработать HTTP запрос"""
        try:
            # Получаем запрос
            request_data = client_socket.recv(4096)
            if not request_data:
                return
                
            self.request_count += 1
            
            # Логируем raw request
            print(f"[SERVER] Request #{self.request_count} from {client_address}")
            print(f"[SERVER] Raw request: {request_data[:200]}...")
            
            # Парсим первую строку
            request_lines = request_data.decode('utf-8', errors='ignore').split('\r\n')
            if request_lines:
                first_line = request_lines[0]
                print(f"[SERVER] First line: {first_line}")
            
            # Формируем deterministic response
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 13\r\n"
                "Connection: close\r\n"
                "\r\n"
                "Hello, World!"
            ).encode('utf-8')
            
            # Отправляем response
            client_socket.send(response)
            print(f"[SERVER] Response sent to {client_address}")
            
        except Exception as e:
            print(f"[SERVER] Error handling request: {e}")
        finally:
            client_socket.close()
    
    def start(self):
        """Запустить сервер"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            print(f"[SERVER] Started on {self.host}:{self.port}")
            print(f"[SERVER] Server PID: {os.getpid()}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"[SERVER] New connection from {client_address}")
                    
                    # Обрабатываем запрос в отдельном потоке
                    client_thread = threading.Thread(
                        target=self.handle_request,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except OSError as e:
                    if self.running:
                        print(f"[SERVER] Accept error: {e}")
                    break
                    
        except Exception as e:
            print(f"[SERVER] Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                print("[SERVER] Server stopped")
    
    def stop(self):
        """Остановить сервер"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

def test_server():
    """Тестировать сервер"""
    print("🚀 Local HTTP Server Test")
    print("Цель: Детерминированный сервер для DPI экспериментов")
    print("=" * 60)
    
    server = LocalHTTPServer()
    
    try:
        # Запускаем сервер в фоновом потоке
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Даем время на запуск
        time.sleep(1)
        
        # Тестируем соединение
        print("📤 Testing server connection...")
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.connect(("127.0.0.1", 8080))
        
        # Отправляем тестовый запрос
        test_request = "GET /test HTTP/1.1\r\nHost: localhost:8080\r\n\r\n"
        test_socket.send(test_request.encode())
        
        # Получаем ответ
        response = test_socket.recv(4096)
        print(f"📥 Test response: {response}")
        
        test_socket.close()
        
        print("✅ Server test successful")
        
        # Оставляем сервер работать
        print("📡 Server running... Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server")
            server.stop()
            
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        server.stop()
        return False
    
    return True

def main():
    """Основная функция"""
    success = test_server()
    return 0 if success else 1

if __name__ == "__main__":
    import os
    sys.exit(main())
