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
import random
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import pipeline manager, orchestrator and web GUI
from pipeline_manager import PipelineManager
from failover_orchestrator import SmartFailoverOrchestrator
from web_gui import WebGuiServer

class SOCKS5Daemon:
    """Универсальный SOCKS5 прокси с wire fragmentation"""
    
    async def _readexact(self, reader, n):
        """Helper to read exactly n bytes from StreamReader"""
        data = await reader.read(n)
        if len(data) != n:
            raise EOFError(f"Expected {n} bytes, got {len(data)}")
        return data

    def __init__(self, listen_port=1080, orchestrator=None):
        # Read from environment variables
        self.listen_port = listen_port
        
        self.running = False
        self.connections = {}
        
        # Initialize Pipeline Manager and Orchestrator
        self.pipeline_manager = PipelineManager()
        self.orchestrator = orchestrator or SmartFailoverOrchestrator()
        
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
        self.logger.info(f"SOCKS5 daemon initialized: port={self.listen_port}")
        
        # Load base pipeline configuration (fallback)
        if self.pipeline_manager.load_pipeline_config():
            self.logger.info(f"Base pipeline loaded: {self.pipeline_manager.get_pipeline_info()}")
        else:
            self.logger.error("Failed to load base pipeline configuration")
            raise RuntimeError("Pipeline configuration failed")
    
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
            # Безопасное чтение стартового приветствия SOCKS5 (минимум 2 байта)
            auth_header = await reader.read(2)
            if len(auth_header) < 2:
                self.logger.error(f"[SOCKS5] Handshake failed: Only {len(auth_header)} bytes read")
                return False

            version, nmethods = auth_header[0], auth_header[1]
            if version != 0x05:
                self.logger.error(f"[SOCKS5] Unsupported SOCKS version: {version:02x}")
                return False

            # Читаем поддерживаемые клиентом методы авторизации
            if nmethods > 0:
                methods = await reader.read(nmethods)
                self.logger.debug(f"[SOCKS5] Auth methods: {[hex(m) for m in methods]}")
            
            # Отвечаем клиенту: Выбран метод 0x00 (Без авторизации)
            writer.write(b"\x05\x00")
            await writer.drain()
            
            self.logger.info(f"[SOCKS5] Handshake successful: No auth method selected")
            return True
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Handshake failed: {e}")
            return False
    
    async def parse_socks5_request(self, reader, writer):
        """Шаг 2: Чтение запроса и извлечение назначения (RFC 1928)"""
        try:
            # 1. Читаем строго 4 байта заголовка запроса (атомарное чтение)
            req_header = await self._readexact(reader, 4)
            version = req_header[0]
            cmd = req_header[1]
            rsv = req_header[2]
            atyp = req_header[3]  # Строгий индекс типа адреса

            self.logger.debug(f"[SOCKS5] Request: version={version:02x}, cmd={cmd:02x}, atyp={atyp:02x}")

            # Проверяем версию и команду
            if version != 0x05 or cmd != 0x01:
                # Если команда не CONNECT (0x01), закрываем сокет
                self.logger.error(f"[SOCKS5] Invalid version or command: version={version:02x}, cmd={cmd:02x}")
                return None, None

            # 2. Извлекаем хост на основе ATYP (атомарное чтение)
            target_host = None
            target_port = None

            if atyp == 0x01:  # IPv4
                raw_ip = await self._readexact(reader, 4)
                raw_port = await self._readexact(reader, 2)
                target_host = ".".join(map(str, raw_ip))
                target_port = int.from_bytes(raw_port, 'big')

            elif atyp == 0x03:  # Доменное имя (Браузеры)
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
                print(f"[SOCKS5 ERROR] Неподдерживаемый тип адреса ATYP: {atyp}")
                return None, None

            # 🔥 КРИТИЧЕСКИЙ ФИЛЬТР АНТИ-РЕКУРСИИ: Предотвращаем поломку интернета
            if target_host in ("0.0.0.0", "127.0.0.1", "localhost"):
                print(f"[SOCKS5 RECURSION DROP] Заблокирована попытка проксирования на localhost: {target_host}")
                return None, None

            # Блокируем проксирование на самого себя (self-reference)
            try:
                local_addr = writer.get_extra_info('sockname')[0]
                if target_host == local_addr:
                    print(f"[SOCKS5 RECURSION DROP] Заблокирована попытка проксирования на самого себя: {target_host}")
                    return None, None
            except Exception:
                # Если не удалось получить локальный адрес, пропускаем эту проверку
                pass

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
        """Шаг 4: Трансляция и фрагментация данных через Smart Orchestrator"""
        session = None
        try:
            # Создаем сессию через оркестратор
            domain = target_host
            self.logger.info(f"[SOCKS5] Creating session for domain: {domain}")
            session = await self.orchestrator.create_session(domain)
            
            # Загружаем динамическую конфигурацию пайплайна
            self.logger.info(f"[SOCKS5] Loading dynamic pipeline config: {session.pipeline_config}")
            if not await self.pipeline_manager.load_pipeline_from_config(session.pipeline_config):
                self.logger.error(f"[SOCKS5] Failed to load pipeline for {domain}")
                return
            
            self.logger.info(f"[SOCKS5] Session {session.session_id} created for {domain}")
            self.logger.info(f"[SOCKS5] Dynamic pipeline loaded: {self.pipeline_manager.get_pipeline_info()}")
            
            # Открываем реальное соединение с целевым сервером
            self.logger.info(f"[SOCKS5] Connecting to {target_host}:{target_port}")
            try:
                loop = asyncio.get_running_loop()

                # 1. Ограничиваем время резолва адреса DNS до 3 секунд
                addr_info = await asyncio.wait_for(
                    loop.getaddrinfo(target_host, target_port, family=socket.AF_INET, type=socket.SOCK_STREAM),
                    timeout=3.0
                )
                resolved_ipv4 = addr_info[0][4][0]

                print(f"[SOCKS5] Connecting to verified IPv4: {resolved_ipv4}:{target_port}")

                # 2. 🔥 КРИТИЧЕСКИЙ ПАТЧ: Ограничиваем время самого TCP-handshake до 3 секунд
                # Если VPNKit на macOS зависнет и задропает пакеты, wait_for спасет корутину от бесконечного ожидания
                upstream_reader, upstream_writer = await asyncio.wait_for(
                    asyncio.open_connection(resolved_ipv4, target_port),
                    timeout=3.0
                )

                # Успешное подключение — отключаем Нагла
                sock = upstream_writer.get_extra_info('socket')
                if sock:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            except asyncio.TimeoutError:
                # Перехватываем зависание Docker-сети на macOS
                print(f"[SOCKS5 TIMEOUT] Превышено время ожидания (3.0s) подключения к {target_host}. Сеть Docker Desktop заблокирована.")

                # Генерация мутации на основе текущего состояния
                current_pipeline = session.pipeline_config.get('pipeline_modules', ['fake_packet', 'sni_modifier', 'jitter_fragmentation'])
                next_pipeline = [m for m in current_pipeline if m != "fake_packet"] if "fake_packet" in current_pipeline else []
                
                # Принудительный вызов с передачей нано-контекста
                await self.orchestrator.report_failure(
                    domain=domain,
                    reason="Connection timeout",
                    current_pipeline=current_pipeline,
                    next_pipeline=next_pipeline
                )
                return

            except Exception as net_err:
                print(f"[SOCKS5 NET ERROR] Сбой подключения к {target_host}: {net_err}")
                
                # Генерация мутации на основе текущего состояния
                current_pipeline = session.pipeline_config.get('pipeline_modules', ['fake_packet', 'sni_modifier', 'jitter_fragmentation'])
                next_pipeline = [m for m in current_pipeline if m != "fake_packet"] if "fake_packet" in current_pipeline else []
                
                # Принудительный вызов с передачей нано-контекста
                await self.orchestrator.report_failure(
                    domain=domain,
                    reason="DPI Request Drop",
                    current_pipeline=current_pipeline,
                    next_pipeline=next_pipeline
                )
                return
            
            self.logger.info(f"[SOCKS5] Connected to {target_host}:{target_port}")
            
            # Сбрасываем состояние конвейера для новой сессии
            self.pipeline_manager.reset_session()
            
            # Передаем управление Pipeline Manager с отслеживанием успеха
            success = await asyncio.gather(
                self.forward_client_to_upstream(client_reader, upstream_writer, session),
                self.forward_upstream_to_client(upstream_reader, client_writer),
                return_exceptions=True
            )
            
            # Проверяем результаты
            if all(isinstance(result, Exception) for result in success):
                # Все задачи завершились с ошибками
                error = success[0]
                self.logger.error(f"[SOCKS5] Pipeline failed: {error}")
                await self.orchestrator.report_failure(domain, session.pipeline_config, "pipeline_error")
            else:
                # Хотя бы одна задача завершилась успешно
                await self.orchestrator.report_success(session)
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Proxy connection failed: {e}")
            if session:
                await self.orchestrator.report_failure(domain, session.pipeline_config, "proxy_error")
    
    async def forward_client_to_upstream(self, client_reader, upstream_writer, session):
        """Пересылка данных от клиента к серверу через Pipeline Manager"""
        bytes_sent = 0
        threshold = 3000
        
        try:
            while True:
                data = await client_reader.read(4096)
                
                # 🔥 КРИТИЧЕСКИЙ ПАТЧ: Если сервер закрыл соединение или curl прислал пустой буфер
                if not data:
                    if bytes_sent < threshold:
                        # Сессия упала НА СТАРТЕ — это 100% сетевой сбой/блокировка!
                        raise ConnectionResetError("Empty reply or premature connection close during handshake")
                    break
                
                self.logger.info(f"[SOCKS5] Received {len(data)} bytes from client")
                
                # Обрабатываем данные через конвейер модулей
                success = await self.pipeline_manager.process_data(data, upstream_writer)
                
                if not success:
                    self.logger.error("[SOCKS5] Pipeline processing failed")
                    break
                
                bytes_sent += len(data)
                
        except Exception as e:
            self.logger.error(f"[SOCKS5] Client->Upstream error: {e}")
            
            # 🔥 СВЯЗЫВАЕМ СБОЙ С ОРКЕСТРАТОРОМ И ИНСПЕКТОРОМ
            # Принудительно рапортуем оркестратору, передавая причину ошибки
            error_reason = "DPI Request Drop" if "timeout" not in str(e).lower() else "Connection timeout"
            if "empty reply" in str(e).lower() or "premature connection close" in str(e).lower():
                error_reason = "DPI Request Drop" # Пустой ответ от httpbin.org из-за задержек чанков
            
            await self.orchestrator.report_failure(session.domain, session.pipeline_config, error_reason)
            raise
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
            # Запускаем SOCKS5 сервер
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

async def main():
    """Основная функция запуска"""
    try:
        # 1. Инициализация эшелонов
        orchestrator = SmartFailoverOrchestrator()
        inspector = orchestrator.dpi_inspector  # Инспектор уже создан внутри оркестратора
        
        # Pre-seed стратегии из внешнего URL
        await orchestrator._preseed_strategies()
        
        # 2. Формируем список конкурентных задач
        tasks = []
        
        # Добавляем задачу SOCKS5-прокси (всегда активна)
        daemon = SOCKS5Daemon(orchestrator=orchestrator)
        tasks.append(daemon.run())
        print("[INIT] SOCKS5 Server added to event loop.")
        
        # 3. Правильное приведение строки из Docker-окружения к Boolean
        WEB_GUI_ENABLED = os.getenv('WEB_GUI_ENABLED', 'false').lower() in ('true', '1', 'yes')
        
        # Добавляем задачу Web GUI (строго по условию)
        if WEB_GUI_ENABLED:
            web_server = WebGuiServer(orchestrator)
            tasks.append(web_server.start())
            print("[INIT] Web GUI Server added to event loop.")
        else:
            print("[INIT] Web GUI is explicitly DISABLED via environment.")

        # Устанавливаем обработчики сигналов
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, shutting down...")
            daemon.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 4. Запускаем оба сервера параллельно в одном Event Loop без блокировок
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logging.error(f"Daemon startup failed: {e}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
