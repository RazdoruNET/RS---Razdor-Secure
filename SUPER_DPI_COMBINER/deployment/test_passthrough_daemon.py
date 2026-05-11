#!/usr/bin/env python3
"""
Simplified SOCKS5 daemon for passthrough testing - no pipeline processing
"""

import asyncio
import socket
import struct
import logging
import sys
from pathlib import Path

class SimpleSOCKS5Daemon:
    """Упрощенный SOCKS5 прокси для тестирования transport layer"""
    
    async def _readexact(self, reader, n):
        """Helper to read exactly n bytes from StreamReader"""
        return await reader.readexactly(n)

    def __init__(self, listen_port=1081):
        self.listen_port = listen_port
        self.running = False
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Simple SOCKS5 daemon initialized: port={self.listen_port}")
    
    async def handle_socks5_client(self, reader, writer):
        """Основной обработчик клиентского соединения"""
        client_addr = writer.get_extra_info('peername')
        writer_cl = writer
        writer_srv = None
        
        self.logger.info(f"[SOCKS5] New client connection from {client_addr}")
        
        try:
            # Настраиваем сокет для стабильной работы
            sock = writer.get_extra_info('socket')
            if sock:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Шаг 1: Handshake
            if not await self.handle_socks5_handshake(reader, writer):
                return
            
            # Шаг 2: Чтение запроса
            target_host, target_port = await self.parse_socks5_request(reader, writer)
            if not target_host or not target_port:
                return
            
            self.logger.info(f"[SOCKS5] Target {target_host}:{target_port} extracted")
            
            # Шаг 3: Ответ об успехе
            if not await self.send_success_reply(writer):
                return
            
            # Шаг 4: Простая трансляция без pipeline
            await self.proxy_connection_passthrough(reader, writer, target_host, target_port)
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Error handling client {client_addr}: {e}")
            
        finally:
            # Централизованная очистка
            for w in [writer_srv, writer_cl]:
                if w:
                    try:
                        w.close()
                        await w.wait_closed()
                    except Exception:
                        pass
            self.logger.info(f"[SOCKS5] Client {client_addr} disconnected")
    
    async def handle_socks5_handshake(self, reader, writer):
        """Шаг 1: Handshake"""
        try:
            auth_header = await reader.read(2)
            if len(auth_header) < 2:
                return False

            version, nmethods = auth_header[0], auth_header[1]
            if version != 0x05:
                return False

            if nmethods > 0:
                methods = await reader.read(nmethods)
            
            # Отвечаем: метод 0x00 (Без авторизации)
            writer.write(b"\x05\x00")
            await writer.drain()
            
            return True
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Handshake failed: {e}")
            return False
    
    async def parse_socks5_request(self, reader, writer):
        """Шаг 2: Чтение запроса"""
        try:
            req_header = await self._readexact(reader, 4)
            version = req_header[0]
            cmd = req_header[1]
            atyp = req_header[3]

            if version != 0x05 or cmd != 0x01:
                return None, None

            target_host = None
            target_port = None

            if atyp == 0x01:  # IPv4
                raw_ip = await self._readexact(reader, 4)
                raw_port = await self._readexact(reader, 2)
                target_host = ".".join(map(str, raw_ip))
                target_port = int.from_bytes(raw_port, 'big')

            elif atyp == 0x03:  # Доменное имя
                len_byte = await self._readexact(reader, 1)
                domain_length = len_byte[0]
                raw_domain = await self._readexact(reader, domain_length)
                target_host = raw_domain.decode('utf-8', errors='ignore')
                raw_port = await self._readexact(reader, 2)
                target_port = int.from_bytes(raw_port, 'big')

            elif atyp == 0x04:  # IPv6
                raw_ipv6 = await self._readexact(reader, 16)
                raw_port = await self._readexact(reader, 2)
                target_host = socket.inet_ntop(socket.AF_INET6, raw_ipv6)
                target_port = int.from_bytes(raw_port, 'big')

            else:
                return None, None

            # Фильтр рекурсии
            if target_host in ("0.0.0.0", "127.0.0.1", "localhost"):
                return None, None

            self.logger.info(f"[SOCKS5] Parsed target: {target_host}:{target_port}")
            return target_host, target_port

        except Exception as e:
            self.logger.error(f"[SOCKS5] Request parsing failed: {e}")
            return None, None
    
    async def send_success_reply(self, writer):
        """Шаг 3: Ответ об успехе"""
        try:
            response = b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00'
            writer.write(response)
            await writer.drain()
            return True
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Reply failed: {e}")
            return False
    
    async def proxy_connection_passthrough(self, client_reader, client_writer, target_host, target_port):
        """Шаг 4: Простая трансляция без pipeline"""
        try:
            # Открываем соединение с целевым сервером
            self.logger.info(f"[SOCKS5] Connecting to {target_host}:{target_port}")
            
            upstream_reader, upstream_writer = await asyncio.wait_for(
                asyncio.open_connection(target_host, target_port),
                timeout=5.0
            )
            
            # Настраиваем upstream сокет
            sock = upstream_writer.get_extra_info('socket')
            if sock:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Сохраняем для cleanup
            writer_srv = upstream_writer
            
            self.logger.info(f"[SOCKS5] Connected to {target_host}:{target_port}")
            
            # Создаем задачи для двунаправленной пересылки
            tasks = [
                asyncio.create_task(self.forward_data(client_reader, upstream_writer, "client->upstream")),
                asyncio.create_task(self.forward_data(upstream_reader, client_writer, "upstream->client"))
            ]
            
            # Ждем завершения любой задачи
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info(f"[SOCKS5] Proxy session completed")
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Proxy connection failed: {e}")
    
    async def forward_data(self, reader, writer, direction):
        """Простая пересылка данных"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                self.logger.debug(f"[SOCKS5] Forwarding {len(data)} bytes ({direction})")
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            self.logger.error(f"[SOCKS5] Forward error ({direction}): {e}")
    
    async def start_server(self):
        """Запуск SOCKS5 сервера"""
        self.logger.info(f"Starting SOCKS5 server on port {self.listen_port}")
        
        server = await asyncio.start_server(
            self.handle_socks5_client,
            '0.0.0.0',
            self.listen_port,
            reuse_address=True
        )
        
        self.running = True
        self.logger.info(f"SOCKS5 server listening on 0.0.0.0:{self.listen_port}")
        
        return server
    
    async def run(self):
        """Запуск демона"""
        try:
            server = await self.start_server()
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"Daemon failed: {e}")
            return 1
        
        return 0

if __name__ == "__main__":
    daemon = SimpleSOCKS5Daemon()
    sys.exit(asyncio.run(daemon.run()))
