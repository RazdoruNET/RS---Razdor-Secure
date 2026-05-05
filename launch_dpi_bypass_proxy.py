#!/usr/bin/env python3
"""
DPI-Bypass Proxy Launcher
Скрипт запуска прокси-сервера для маршрутизации всего трафика через DPI-Bypass Combiner v2.0
Делает недоступный контент доступным без VPN
"""

import sys
import os
import threading
import socket
import time
import json
import argparse
from pathlib import Path

# Добавляем путь к модулю rsecure
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

from rsecure.modules.defense.dpi_bypass_combiner_v2 import DPIBypassCombinerV2


class DPIBypassProxy:
    """Прокси-сервер для маршрутизации трафика через DPI-Bypass"""
    
    def __init__(self, listen_port=8080, log_file=None):
        self.listen_port = listen_port
        self.log_file = log_file
        self.dpi_combiner = DPIBypassCombinerV2()
        self.running = False
        self.stats = {
            "total_requests": 0,
            "successful_bypasses": 0,
            "direct_access": 0,
            "failed_requests": 0,
            "start_time": time.time()
        }
        
    def start(self):
        """Запуск прокси-сервера"""
        self.running = True
        print(f"🚀 Запускаю DPI-Bypass Proxy на порту {self.listen_port}")
        print(f"📍 Настройка прокси в браузере: 127.0.0.1:{self.listen_port}")
        print(f"🔥 Весь трафик будет маршрутизироваться через DPI-Bypass")
        print(f"📊 Статистика будет доступна по адресу: http://127.0.0.1:{self.listen_port}/stats")
        print(f"⏹️ Остановка: Ctrl+C")
        print(f"=" * 60)
        
        try:
            # Создаем серверный сокет
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', self.listen_port))
            server_socket.listen(5)
            
            print(f"✅ Прокси-сервер запущен и готов к работе!")
            
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    # Обрабатываем каждый запрос в отдельном потоке
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print(f"\n⏹️ Получен сигнал остановки...")
                    break
                except Exception as e:
                    print(f"❌ Ошибка при принятии подключения: {e}")
                    
        except Exception as e:
            print(f"❌ Ошибка запуска сервера: {e}")
        finally:
            self.running = False
            if 'server_socket' in locals():
                server_socket.close()
            self.print_final_stats()
    
    def handle_client(self, client_socket, client_address):
        """Обработка клиентского запроса"""
        try:
            # Получаем HTTP запрос от клиента
            request_data = client_socket.recv(4096).decode('utf-8')
            
            if not request_data:
                return
            
            # Парсим HTTP запрос
            request_lines = request_data.split('\n')
            if not request_lines:
                return
                
            request_line = request_lines[0]
            parts = request_line.split(' ')
            
            if len(parts) < 3:
                return
                
            method, url, version = parts[0], parts[1], parts[2]
            
            # Обработка специальных запросов
            if url == '/stats':
                self.send_stats_response(client_socket)
                return
            
            # Извлекаем хост из заголовков или URL
            host = self.extract_host(request_lines, url)
            
            if not host:
                self.send_error_response(client_socket, 400, "Bad Request")
                return
            
            self.stats["total_requests"] += 1
            print(f"🌐 Запрос: {method} {host} от {client_address[0]}")
            
            # Маршрутизируем через DPI-Bypass
            response = self.route_through_dpi_bypass(host, method, request_data)
            
            # Отправляем ответ клиенту
            client_socket.send(response)
            
        except Exception as e:
            print(f"❌ Ошибка обработки клиента {client_address}: {e}")
            self.stats["failed_requests"] += 1
        finally:
            client_socket.close()
    
    def extract_host(self, request_lines, url):
        """Извлечение хоста из запроса"""
        # Сначала ищем в заголовках
        for line in request_lines:
            if line.lower().startswith('host:'):
                return line.split(':', 1)[1].strip()
        
        # Если нет в заголовках, извлекаем из URL
        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]
        
        if '/' in url:
            return url.split('/')[0]
        
        return url
    
    def route_through_dpi_bypass(self, host, method, request_data):
        """Маршрутизация запроса через DPI-Bypass"""
        try:
            print(f"🔄 Маршрутизация {host} через DPI-Bypass...")
            
            # Проверяем и обходим DPI
            bypass_result = self.dpi_combiner.bypass_target(host)
            
            if bypass_result.get("direct_access", False):
                print(f"   ✅ {host} доступен напрямую")
                self.stats["direct_access"] += 1
                return self.make_direct_request(host, request_data)
            
            elif bypass_result.get("final_success", False):
                print(f"   🎯 {host} успешно обойден через {bypass_result.get('successful_chain')}")
                self.stats["successful_bypasses"] += 1
                return self.make_direct_request(host, request_data)
            
            else:
                print(f"   ❌ Не удалось обойти {host}")
                self.stats["failed_requests"] += 1
                return self.make_error_response(f"Не удалось обойти DPI для {host}")
                
        except Exception as e:
            print(f"❌ Ошибка маршрутизации {host}: {e}")
            self.stats["failed_requests"] += 1
            return self.make_error_response(f"Ошибка маршрутизации: {e}")
    
    def make_direct_request(self, host, request_data):
        """Прямой запрос к хосту"""
        try:
            # Создаем соединение с целевым хостом
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            
            # Определяем порт
            port = 443 if ":443" in host or request_data.startswith("GET https") else 80
            if ":" in host and not host.endswith(":443") and not host.endswith(":80"):
                host = host.split(":")[0]
            
            target_socket.connect((host, port))
            
            # Для HTTPS используем SSL
            if port == 443:
                import ssl
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                target_socket = context.wrap_socket(target_socket, server_hostname=host)
            
            # Отправляем запрос
            target_socket.send(request_data.encode())
            
            # Получаем ответ
            response_data = b""
            while True:
                chunk = target_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            target_socket.close()
            return response_data
            
        except Exception as e:
            return self.make_error_response(f"Ошибка запроса к {host}: {e}")
    
    def send_stats_response(self, client_socket):
        """Отправка статистики"""
        uptime = time.time() - self.stats["start_time"]
        
        html_stats = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DPI-Bypass Proxy Статистика</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .stats {{ background: #2a2a2a; padding: 20px; border-radius: 10px; margin: 10px 0; }}
                .stat-item {{ margin: 10px 0; display: flex; justify-content: space-between; }}
                .success {{ color: #4CAF50; }}
                .warning {{ color: #FF9800; }}
                .error {{ color: #F44336; }}
                h1 {{ text-align: center; color: #00BCD4; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔥 DPI-Bypass Proxy Статистика</h1>
                <div class="stats">
                    <div class="stat-item">
                        <span>⏱️ Время работы:</span>
                        <span>{uptime:.1f} сек</span>
                    </div>
                    <div class="stat-item">
                        <span>🌐 Всего запросов:</span>
                        <span>{self.stats['total_requests']}</span>
                    </div>
                    <div class="stat-item success">
                        <span>✅ Успешных обходов:</span>
                        <span>{self.stats['successful_bypasses']}</span>
                    </div>
                    <div class="stat-item">
                        <span>🔓 Прямой доступ:</span>
                        <span>{self.stats['direct_access']}</span>
                    </div>
                    <div class="stat-item error">
                        <span>❌ Неудачных запросов:</span>
                        <span>{self.stats['failed_requests']}</span>
                    </div>
                </div>
                <div class="stats">
                    <h3>🎯 Статус DPI-Bypass:</h3>
                    <pre>{json.dumps(self.dpi_combiner.get_status(), indent=2, ensure_ascii=False)}</pre>
                </div>
            </div>
        </body>
        </html>
        """
        
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(html_stats.encode())}\r\n\r\n{html_stats}"
        client_socket.send(response.encode())
    
    def send_error_response(self, client_socket, code, message):
        """Отправка ошибки"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error {code}</title></head>
        <body>
            <h1>Error {code}</h1>
            <p>{message}</p>
        </body>
        </html>
        """
        response = f"HTTP/1.1 {code} Error\r\nContent-Type: text/html\r\nContent-Length: {len(html)}\r\n\r\n{html}"
        client_socket.send(response.encode())
    
    def make_error_response(self, message):
        """Создание HTTP ответа с ошибкой"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>DPI-Bypass Error</title></head>
        <body>
            <h1>DPI-Bypass Error</h1>
            <p>{message}</p>
        </body>
        </html>
        """
        return f"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/html\r\nContent-Length: {len(html)}\r\n\r\n{html}".encode()
    
    def print_final_stats(self):
        """Вывод финальной статистики"""
        print(f"\n📊 Финальная статистика:")
        print(f"=" * 40)
        print(f"🌐 Всего запросов: {self.stats['total_requests']}")
        print(f"✅ Успешных обходов: {self.stats['successful_bypasses']}")
        print(f"🔓 Прямой доступ: {self.stats['direct_access']}")
        print(f"❌ Неудачных запросов: {self.stats['failed_requests']}")
        uptime = time.time() - self.stats["start_time"]
        print(f"⏱️ Время работы: {uptime:.1f} сек")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="DPI-Bypass Proxy Launcher")
    parser.add_argument("--port", type=int, default=8080, help="Порт для прокси-сервера (по умолчанию: 8080)")
    parser.add_argument("--log", type=str, help="Файл для логирования")
    
    args = parser.parse_args()
    
    # Проверяем права администратора для работы с сетью
    if os.geteuid() != 0:
        print("⚠️ Внимание: Для лучшей производительности рекомендуется запускать от имени администратора")
        print("🔧 Используйте: sudo python3 launch_dpi_bypass_proxy.py")
        print()
    
    # Создаем и запускаем прокси
    proxy = DPIBypassProxy(listen_port=args.port, log_file=args.log)
    
    try:
        proxy.start()
    except KeyboardInterrupt:
        print(f"\n⏹️ Прокси-сервер остановлен")


if __name__ == "__main__":
    main()
