#!/usr/bin/env python3
"""
DPI-Evading SOCKS5 Proxy Daemon - RFC 1928 Implementation
Кросс-платформенный SOCKS5 прокси с wire fragmentation для обхода DPI
"""

import sys
import asyncio
import socket
import struct
import logging
import json
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import existing fragmentation runtime
from verification.tcp_segment_working import TCPSegmentAnalyzer

class SOCKS5Daemon:
    """Универсальный SOCKS5 прокси с wire fragmentation"""
    
    def __init__(self, listen_port=1080, chunk_size=30, chunk_delay=0.005):
        # Read from environment variables
        self.listen_port = int(os.environ.get('LISTEN_PORT', str(listen_port)))
        self.chunk_size = int(os.environ.get('CHUNK_SIZE', str(chunk_size)))
        self.chunk_delay = float(os.environ.get('CHUNK_DELAY', str(chunk_delay)))
        self.running = False
        self.connections = {}
        
        # Используем существующий fragment analyzer
        self.segment_analyzer = TCPSegmentAnalyzer()
        
        # Configure logging to stdout only (for docker logs)
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"SOCKS5 daemon initialized: port={self.listen_port}, chunk_size={self.chunk_size}, chunk_delay={self.chunk_delay}")
    
    async def handle_client(self, reader, writer):
        """Handle SOCKS5 client connection with wire fragmentation"""
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"[SOCKS5] New client connection from {client_addr}")
        
        try:
            # Шаг 1: Handshake (Приветствие)
            if not await self.handle_socks5_handshake(reader, writer):
                return
            
            # Шаг 2: Чтение запроса и извлечение назначения
            target_host, target_port = await self.parse_socks5_request(reader, writer)
            if not target_host or not target_port:
                return
            
            self.logger.info(f"[SOCKS5] Target {target_host}:{target_port} extracted")
            
            # Шаг 3: Ответ об успехе и запуск фрагментации
            if not await self.send_success_reply(writer):
                return
            
            # Шаг 4: Трансляция и Фрагментация
            await self.proxy_connection(reader, writer, target_host, target_port)
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Error handling client {client_addr}: {e}")
        finally:
            writer.close()
            self.logger.info(f"[SOCKS5] Client {client_addr} disconnected")
    
    async def handle_socks5_handshake(self, reader, writer):
        """Шаг 1: Handshake (Приветствие)"""
        try:
            # Читаем первые 2 байта: Версия + Количество методов
            auth_header = await reader.readexactly(2)
            
            # Проверяем версию (должна быть 0x05)
            if auth_header[0] != 0x05:
                self.logger.error(f"[SOCKS5] Unsupported SOCKS version: {auth_header[0]:02x}")
                return False
            
            # Читаем доступные методы аутентификации
            nmethods = auth_header[1]
            if nmethods > 0:
                methods = await reader.readexactly(nmethods)
                self.logger.debug(f"[SOCKS5] Auth methods: {[hex(m) for m in methods]}")
            
            # Отвечаем клиенту, что работаем без авторизации
            writer.write(b'\x05\x00')  # VER=5, METHOD=0 (No auth)
            await writer.drain()
            
            self.logger.info(f"[SOCKS5] Handshake successful: No auth method selected")
            return True
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Handshake failed: {e}")
            return False
    
    async def parse_socks5_request(self, reader, writer):
        """Шаг 2: Чтение запроса и извлечение назначения (RFC 1928)"""
        try:
            # Читаем фиксированную часть заголовка запроса (4 байта)
            req_header = await reader.readexactly(4)
            
            version = req_header[0]  # Версия (0x05)
            cmd = req_header[1]      # Команда (0x01 = CONNECT)
            rsv = req_header[2]       # Резерв (0x00)
            atyp = req_header[3]     # Тип адреса (ATYP)
            
            self.logger.debug(f"[SOCKS5] Request: version={version:02x}, cmd={cmd:02x}, atyp={atyp:02x}")
            
            # Проверяем версию и команду
            if version != 0x05:
                self.logger.error(f"[SOCKS5] Unsupported SOCKS version: {version:02x}")
                return None, None
            
            if cmd != 0x01:
                self.logger.error(f"[SOCKS5] Unsupported command: {cmd:02x} (only CONNECT supported)")
                return None, None
            
            # Извлекаем целевой хост в зависимости от ATYP
            target_host = None
            target_port = None
            
            if atyp == 0x01:  # IPv4
                # Читаем 4 байта IP и 2 байта порта
                raw_ip = await reader.readexactly(4)
                raw_port = await reader.readexactly(2)
                target_host = socket.inet_ntoa(raw_ip)
                target_port = int.from_bytes(raw_port, 'big')
                
            elif atyp == 0x03:  # Доменное имя (самый частый случай для браузеров)
                # Читаем 1 байт длины домена
                len_byte = await reader.readexactly(1)
                domain_len = len_byte[0]
                
                # Читаем сам домен
                raw_domain = await reader.readexactly(domain_len)
                target_host = raw_domain.decode('utf-8')
                
                # Читаем 2 байта порта
                raw_port = await reader.readexactly(2)
                target_port = int.from_bytes(raw_port, 'big')
                
            elif atyp == 0x04:  # IPv6
                # Читаем 16 байт IPv6 и 2 байта порта
                raw_ipv6 = await reader.readexactly(16)
                raw_port = await reader.readexactly(2)
                target_host = socket.inet_ntop(socket.AF_INET6, raw_ipv6)
                target_port = int.from_bytes(raw_port, 'big')
                
            else:
                self.logger.error(f"[SOCKS5] Unsupported address type: {atyp:02x}")
                return None, None
            
            self.logger.info(f"[SOCKS5] Parsed target: {target_host}:{target_port}")
            return target_host, target_port
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Request parsing failed: {e}")
            return None, None
    
    async def send_success_reply(self, writer):
        """Шаг 3: Ответ об успехе"""
        try:
            # Отправляем подтверждение успеха SOCKS5 (10 байт)
            # VER=5, REP=0 (Success), RSV=0, ATYP=1, ADDR=0.0.0.0:0
            response = b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00'
            writer.write(response)
            await writer.drain()
            
            self.logger.info(f"[SOCKS5] Success reply sent")
            return True
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Reply failed: {e}")
            return False
    
    async def proxy_connection(self, client_reader, client_writer, target_host, target_port):
        """Шаг 4: Трансляция и фрагментация данных"""
        try:
            # Открываем реальное соединение с целевым сервером
            self.logger.info(f"[SOCKS5] Connecting to {target_host}:{target_port}")
            try:
                upstream_reader, upstream_writer = await asyncio.wait_for(
                    asyncio.open_connection(target_host, target_port),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                self.logger.error(f"[SOCKS5] Connection timeout to {target_host}:{target_port}")
                return
            except Exception as e:
                self.logger.error(f"[SOCKS5] Connection failed to {target_host}:{target_port}: {e}")
                return
            
            # Выставляем сокету сервера TCP_NODELAY = 1
            upstream_socket = upstream_writer.get_extra_info('socket')
            if upstream_socket:
                upstream_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            self.logger.info(f"[SOCKS5] Connected to {target_host}:{target_port}")
            
            # Передаем управление WIRE_LEVEL_VERIFIED_FRAGMENTATION_RUNTIME
            await asyncio.gather(
                self.forward_client_to_upstream(client_reader, upstream_writer),
                self.forward_upstream_to_client(upstream_reader, client_writer),
            )
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Proxy connection failed: {e}")
    
    async def forward_client_to_upstream(self, client_reader, upstream_writer):
        """Пересылка данных от клиента к серверу с фрагментацией"""
        try:
            while True:
                data = await client_reader.read(4096)
                if not data:
                    break
                
                self.logger.info(f"[SOCKS5] Received {len(data)} bytes from client")
                
                # Отправляем с wire-level фрагментацией
                await self.send_with_fragmentation(upstream_writer, data)
                
        except Exception as e:
            self.logger.error(f"[SOCKS5] Client->Upstream error: {e}")
        finally:
            upstream_writer.close()
    
    async def forward_upstream_to_client(self, upstream_reader, client_writer):
        """Пересылка данных от сервера к клиенту (passthrough)"""
        try:
            while True:
                data = await upstream_reader.read(4096)
                if not data:
                    break
                
                self.logger.info(f"[SOCKS5] Received {len(data)} bytes from upstream")
                
                # Отправляем клиенту без фрагментации (максимальная скорость)
                client_writer.write(data)
                await client_writer.drain()
                
        except Exception as e:
            self.logger.error(f"[SOCKS5] Upstream->Client error: {e}")
        finally:
            client_writer.close()
    
    async def send_with_fragmentation(self, writer, data):
        """Отправка данных с wire-level фрагментацией"""
        total_sent = 0
        fragment_count = 0
        
        self.logger.info(f"[SOCKS5] DEBUG: Starting fragmentation - data_size={len(data)}, chunk_size={self.chunk_size}, chunk_size_type={type(self.chunk_size)}")
        
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            
            # Отправляем чанк
            writer.write(chunk)
            await writer.drain()
            
            fragment_count += 1
            total_sent += len(chunk)
            
            self.logger.info(f"[SOCKS5] DEBUG: Sent fragment {fragment_count}: {len(chunk)} bytes (range {i}-{i+self.chunk_size})")
            
            # Принудительная задержка между чанками
            if self.chunk_delay > 0:
                await asyncio.sleep(self.chunk_delay)
        
        self.logger.info(f"[SOCKS5] Fragmentation complete: {fragment_count} fragments, {total_sent} bytes")
    
    async def start_server(self):
        """Запуск SOCKS5 сервера"""
        self.logger.info(f"Starting SOCKS5 server on port {self.listen_port}")
        
        # Используем стандартный asyncio.start_server
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.listen_port,
            reuse_address=True,
            reuse_port=True
        )
        
        self.running = True
        self.logger.info(f"SOCKS5 server listening on 0.0.0.0:{self.listen_port}")
        self.logger.info("SOCKS5 daemon started successfully")
        
        return server
    
    async def stop_server(self):
        """Остановка SOCKS5 сервера"""
        self.running = False
        self.logger.info("Stopping SOCKS5 daemon")
        
        if hasattr(self, 'server') and self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.logger.info("SOCKS5 daemon stopped")
    
    def signal_handler(self, signum, frame):
        """Обработка сигналов завершения"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run(self):
        """Запуск SOCKS5 демона"""
        try:
            # Запускаем сервер
            self.server = await self.start_server()
            
            # Работаем до остановки
            async with self.server:
                await self.server.serve_forever()
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"Daemon failed: {e}")
            return 1
        
        return 0

def main():
    """Точка входа"""
    daemon = SOCKS5Daemon()
    
    # Устанавливаем обработчики сигналов
    import signal
    signal.signal(signal.SIGTERM, daemon.signal_handler)
    signal.signal(signal.SIGINT, daemon.signal_handler)
    
    try:
        # Запускаем сервер
        return asyncio.run(daemon.run())
    except KeyboardInterrupt:
        daemon.logger.info("Received interrupt, shutting down...")
    except Exception as e:
        daemon.logger.error(f"Daemon failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
