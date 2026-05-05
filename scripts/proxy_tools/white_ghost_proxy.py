#!/usr/bin/env python3
"""
White-Ghost SOCKS5 Proxy
Локальный прокси для пропускания трафика через White-Ghost Pipelines
Позволяет открывать YouTube в браузере
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

# Добавляем путь к модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure/modules/defense'))

try:
    from dpi_bypass_combiner import DPIBypassCombiner
except ImportError as e:
    print(f"❌ Ошибка импорта DPI-Bypass Combiner: {e}")
    sys.exit(1)


class WhiteGhostSocks5Proxy:
    """SOCKS5 прокси с White-Ghost Pipelines"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 1080):
        self.host = host
        self.port = port
        self.dpi_combiner = DPIBypassCombiner()
        self.running = False
        self.server_socket = None
        
        # Список доменов для обхода через White-Ghost
        self.white_ghost_domains = {
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'youtu.be', 'ytimg.com', 'googlevideo.com',
            'googleapis.com', 'gstatic.com', 'ggpht.com'
        }
        
        # Статистика
        self.stats = {
            'connections': 0,
            'white_ghost_used': 0,
            'direct_used': 0,
            'errors': 0
        }
    
    def start(self):
        """Запуск SOCKS5 прокси"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            
            print(f"👻 White-Ghost SOCKS5 Proxy запущен")
            print(f"🌐 Адрес: {self.host}:{self.port}")
            print(f"🎯 Обходит: {', '.join(list(self.white_ghost_domains)[:3])}...")
            print(f"🔧 Настройте браузер на SOCKS5 прокси {self.host}:{self.port}")
            print(f"⏹️  Нажмите Ctrl+C для остановки")
            print("=" * 50)
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"🔗 Новое соединение от {client_address[0]}:{client_address[1]}")
                    
                    # Создаем поток для обработки клиента
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    self.stats['connections'] += 1
                    
                except OSError:
                    break
                    
        except Exception as e:
            print(f"❌ Ошибка запуска прокси: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Остановка прокси"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        print(f"\n📊 Статистика:")
        print(f"   🔗 Всего соединений: {self.stats['connections']}")
        print(f"   👻 White-Ghost использован: {self.stats['white_ghost_used']}")
        print(f"   🌐 Прямых соединений: {self.stats['direct_used']}")
        print(f"   ❌ Ошибок: {self.stats['errors']}")
        print(f"🏁 Прокси остановлен")
    
    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Обработка клиента"""
        try:
            # SOCKS5 рукопожатие
            if not self.socks5_handshake(client_socket):
                client_socket.close()
                self.stats['errors'] += 1
                return
            
            # SOCKS5 запрос
            if not self.socks5_request(client_socket):
                client_socket.close()
                self.stats['errors'] += 1
                return
            
            # Получаем целевой адрес
            target_host, target_port = self.get_target_address(client_socket)
            if not target_host:
                client_socket.close()
                self.stats['errors'] += 1
                return
            
            print(f"🎯 Запрос: {target_host}:{target_port}")
            
            # Определяем нужно ли использовать White-Ghost
            use_white_ghost = self.should_use_white_ghost(target_host)
            
            if use_white_ghost:
                print(f"   👻 Использую White-Ghost для {target_host}")
                self.stats['white_ghost_used'] += 1
                success = self.handle_white_ghost_connection(client_socket, target_host, target_port)
            else:
                print(f"   🌐 Прямое соединение с {target_host}")
                self.stats['direct_used'] += 1
                success = self.handle_direct_connection(client_socket, target_host, target_port)
            
            if not success:
                self.stats['errors'] += 1
                
        except Exception as e:
            print(f"❌ Ошибка обработки клиента {client_address}: {e}")
            self.stats['errors'] += 1
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def socks5_handshake(self, client_socket: socket.socket) -> bool:
        """SOCKS5 рукопожатие"""
        try:
            # Получаем приветствие клиента
            data = client_socket.recv(262)
            if len(data) < 3:
                return False
            
            # Проверяем версию SOCKS5
            if data[0] != 5:
                return False
            
            # Отправляем ответ (без аутентификации)
            client_socket.send(b'\x05\x00')
            return True
            
        except:
            return False
    
    def socks5_request(self, client_socket: socket.socket) -> bool:
        """Обработка SOCKS5 запроса"""
        try:
            # Получаем запрос
            data = client_socket.recv(262)
            if len(data) < 10:
                return False
            
            # Проверяем версию и команду
            if data[0] != 5 or data[1] != 1:  # CONNECT
                return False
            
            # Отправляем успешный ответ
            response = b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + struct.pack('>H', 0)
            client_socket.send(response)
            return True
            
        except:
            return False
    
    def get_target_address(self, client_socket: socket.socket) -> Tuple[str, int]:
        """Получение целевого адреса из SOCKS5 запроса"""
        try:
            # Получаем запрос еще раз для извлечения адреса
            # В реальном SOCKS5 нужно сохранить данные из предыдущего запроса
            # Для упрощения используем альтернативный метод
            
            # Читаем данные запроса
            data = client_socket.recv(262)
            if len(data) < 7:
                return None, None
            
            # Адрес тип
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
    
    def should_use_white_ghost(self, hostname: str) -> bool:
        """Определяет нужно ли использовать White-Ghost для домена"""
        hostname = hostname.lower()
        
        # Проверяем точное совпадение
        if hostname in self.white_ghost_domains:
            return True
        
        # Проверяем поддомены
        for domain in self.white_ghost_domains:
            if hostname.endswith('.' + domain) or hostname.endswith(domain):
                return True
        
        return False
    
    def handle_white_ghost_connection(self, client_socket: socket.socket, target_host: str, target_port: int) -> bool:
        """Обработка соединения через White-Ghost"""
        try:
            # Используем White-Ghost Pipelines для установки соединения
            print(f"   ⛓️ Запускаю White-Ghost цепочки для {target_host}")
            
            # Пробуем разные цепочки White-Ghost
            pipelines = [
                self.dpi_combiner.gosweb_tunnel,
                self.dpi_combiner.media_parasite,
                self.dpi_combiner.fin_storm
            ]
            
            for pipeline in pipelines:
                try:
                    # Создаем соединение через цепочку
                    remote_socket = self.create_white_ghost_socket(pipeline, target_host, target_port)
                    if remote_socket:
                        print(f"   ✅ Цепочка '{pipeline.name}' успешна")
                        return self.relay_data(client_socket, remote_socket)
                        
                except Exception as e:
                    print(f"   ❌ Цепочка '{pipeline.name}' ошибка: {e}")
                    continue
            
            print(f"   ❌ Все White-Ghost цепочки не сработали")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка White-Ghost соединения: {e}")
            return False
    
    def create_white_ghost_socket(self, pipeline, target_host: str, target_port: int) -> Optional[socket.socket]:
        """Создание сокета через White-Ghost цепочку"""
        try:
            # Создаем базовый сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Применяем техники цепочки
            if hasattr(pipeline, 'create_fragmented_socket_with_sni'):
                # Для Госвеб-Туннель
                sni_mask = pipeline.rotate_sni_mask("GOVERNMENT")
                sock = pipeline.create_fragmented_socket_with_sni(target_host, sni_mask)
                
                # TLS handshake
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                ssl_sock = context.wrap_socket(sock, server_hostname=sni_mask)
                return ssl_sock
                
            elif hasattr(pipeline, 'rotate_sni_mask'):
                # Для других цепочек
                sni_mask = pipeline.rotate_sni_mask()
                sock.connect((target_host, target_port))
                
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                ssl_sock = context.wrap_socket(sock, server_hostname=sni_mask)
                return ssl_sock
            
            else:
                # Прямое соединение
                sock.connect((target_host, target_port))
                return sock
                
        except Exception as e:
            print(f"   ❌ Ошибка создания сокета: {e}")
            return None
    
    def handle_direct_connection(self, client_socket: socket.socket, target_host: str, target_port: int) -> bool:
        """Обработка прямого соединения"""
        try:
            print(f"   🌐 Создаю прямое соединение с {target_host}:{target_port}")
            
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((target_host, target_port))
            
            return self.relay_data(client_socket, remote_socket)
            
        except Exception as e:
            print(f"   ❌ Ошибка прямого соединения: {e}")
            return False
    
    def relay_data(self, client_socket: socket.socket, remote_socket: socket.socket) -> bool:
        """Перенаправление данных между сокетами"""
        try:
            sockets = [client_socket, remote_socket]
            timeout = 300  # 5 минут
            
            while True:
                # Используем select для ожидания данных
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
                        
        except Exception as e:
            print(f"   ❌ Ошибка перенаправления данных: {e}")
            return False
        finally:
            try:
                remote_socket.close()
            except:
                pass
        
        return True


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='White-Ghost SOCKS5 Proxy')
    parser.add_argument('--host', default='127.0.0.1', help='Хост прокси (по умолчанию: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=1080, help='Порт прокси (по умолчанию: 1080)')
    parser.add_argument('--list', action='store_true', help='Показать домены для обхода')
    
    args = parser.parse_args()
    
    if args.list:
        proxy = WhiteGhostSocks5Proxy()
        print("🎯 Домены для обхода через White-Ghost:")
        for domain in sorted(proxy.white_ghost_domains):
            print(f"   • {domain}")
        return
    
    # Создаем и запускаем прокси
    proxy = WhiteGhostSocks5Proxy(args.host, args.port)
    
    try:
        proxy.start()
    except KeyboardInterrupt:
        print(f"\n⏹️  Получен сигнал остановки")
        proxy.stop()


if __name__ == "__main__":
    main()
