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
import copy
from pathlib import Path

def apply_hard_reset_opts(writer: asyncio.StreamWriter):
    """
    Настраивает сокет для стабильной работы без агрессивного сброса
    """
    sock = writer.get_extra_info('socket')
    if sock:
        # Отключаем алгоритм Нагла
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # УДАЛЕНО: SO_LINGER - больше не используем агрессивный RST

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import pipeline manager, orchestrator and web GUI
from pipeline_manager import PipelineManager
from failover_orchestrator import SmartFailoverOrchestrator
from web_gui import WebGuiServer
from dpi_sandbox_inspector import DpiSandboxInspector

class SOCKS5Daemon:
    """Универсальный SOCKS5 прокси с wire fragmentation"""
    
    async def _readexact(self, reader, n):
        """Helper to read exactly n bytes from StreamReader"""
        return await reader.readexactly(n)

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
    
    async def handle_socks5_client(self, reader, writer):
        """Основной обработчик клиентского соединения с жесткой очисткой дескрипторов"""
        client_addr = writer.get_extra_info('peername')
        writer_cl = writer
        writer_srv = None
        
        self.logger.info(f"[SOCKS5] New client connection from {client_addr}")
        
        try:
            # Настраиваем входящий сокет клиента на жесткую очистку
            apply_hard_reset_opts(writer_cl)
            
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
            
            # Шаг 4: Трансляция и Фрагментация с жесткой очисткой
            await self.proxy_connection(reader, writer, target_host, target_port)
            
        except Exception as e:
            self.logger.error(f"[SOCKS5] Error handling client {client_addr}: {e}")
            
        finally:
            # 🔥 УЛЬТИМАТИВНЫЙ БЛОК ОЧИСТКИ ФАЙЛОВЫХ ДЕСКРИПТОРОВ (ЗАЩИТА ОТ УТЕЧЕК)
            for w in [writer_srv, writer_cl]:
                if w:
                    try:
                        w.close()
                        await w.wait_closed()  # Строгое асинхронное ожидание освобождения дескриптора ОС
                    except Exception:
                        pass  # Игнорируем повторные ошибки закрытия уже мертвых сокетов
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
            # 1. Извлекаем пайплайн и накопленный модификатор размера чанка
            domain = target_host
            self.logger.info(f"[SOCKS5] Requesting active pipeline for domain: {domain}")
            active_pipeline, chunk_modifier = await self.orchestrator.get_or_create_strategy(domain, target_port)
            
            # Динамически модифицируем конфигурацию для PipelineManager текущей сессии
            global_config = {
                'MIN_CHUNK_SIZE': 50,
                'MAX_CHUNK_SIZE': 300,
                'FRAGMENT_DELAY_MIN': 0.001,
                'FRAGMENT_DELAY_MAX': 0.003
            }
            local_config = copy.deepcopy(global_config)
            
            # Вычисляем боевые границы размера фрагментов
            base_min = int(local_config.get("MIN_CHUNK_SIZE", 50))
            base_max = int(local_config.get("MAX_CHUNK_SIZE", 300))
            
            if chunk_modifier > 0:
                base_min += chunk_modifier
                base_max += chunk_modifier

            # 🔥 СТРОГИЙ СИНТАКСИС ПЕРЕДАЧИ В ЯДРО КЛИЕНТСКОГО МОДУЛЯ
            local_config["MIN_CHUNK_SIZE"] = base_min
            local_config["MAX_CHUNK_SIZE"] = base_max

            # Явно прописываем конфигурацию внутрь module_configs для PipelineManager
            local_config["module_configs"] = {
                "jitter_fragmentation": {
                    "MIN_CHUNK_SIZE": str(base_min),
                    "MAX_CHUNK_SIZE": str(base_max),
                    "MIN_CHUNK_DELAY": str(local_config.get("FRAGMENT_DELAY_MIN", 0.001)),
                    "MAX_CHUNK_DELAY": str(local_config.get("FRAGMENT_DELAY_MAX", 0.003))
                }
            }

            # 2. Инициализируем PipelineManager с учетом калибровки
            pipeline_config = {
                'pipeline_modules': active_pipeline,
                'module_configs': local_config["module_configs"]
            }
            self.logger.info(f"[SOCKS5] Initializing pipeline with config: {pipeline_config}")
            if not await self.pipeline_manager.load_pipeline_from_config(pipeline_config):
                self.logger.error(f"[SOCKS5] Failed to load pipeline for {domain}")
                return
            
            # Создаем сессию через оркестратор
            self.logger.info(f"[SOCKS5] Creating session for domain: {domain}")
            session = await self.orchestrator.create_session(domain)
            
            self.logger.info(f"[SOCKS5] Session {session.session_id} created for {domain}")
            self.logger.info(f"[SOCKS5] Active pipeline loaded: {self.pipeline_manager.get_pipeline_info()}")
            
            # Открываем реальное соединение с целевым сервером с multi-IP fallback
            self.logger.info(f"[SOCKS5] Connecting to {target_host}:{target_port}")
            try:
                loop = asyncio.get_running_loop()

                # 1. DNS resolution с увеличенным timeout
                self.logger.info(f"[DNS] Resolving {target_host}:{target_port}")
                addr_info = await asyncio.wait_for(
                    loop.getaddrinfo(target_host, target_port, type=socket.SOCK_STREAM),
                    timeout=10.0
                )
                
                # Логируем все найденные адреса
                resolved_ips = []
                for entry in addr_info:
                    ip = entry[4][0]
                    resolved_ips.append(ip)
                
                self.logger.info(f"[DNS] {target_host} -> {', '.join(resolved_ips)}")
                
                # 2. Пробуем подключиться ко всем IP по очереди (fallback)
                last_error = None
                upstream_reader = None
                upstream_writer = None
                successful_ip = None
                
                for entry in addr_info:
                    ip = entry[4][0]
                    self.logger.info(f"[CONNECT] Trying {ip}:{target_port}")
                    
                    try:
                        upstream_reader, upstream_writer = await asyncio.wait_for(
                            asyncio.open_connection(ip, target_port),
                            timeout=15.0  # Увеличенный timeout для стабильности
                        )
                        successful_ip = ip
                        self.logger.info(f"[CONNECT] Success {ip}:{target_port}")
                        break
                        
                    except Exception as e:
                        self.logger.warning(f"[CONNECT] Failed {ip}:{target_port}: {e}")
                        last_error = e
                        continue
                
                # Если все IP недоступны
                if successful_ip is None:
                    self.logger.error(f"[CONNECT] All IPs failed for {target_host}:{target_port}")
                    raise last_error or Exception("All connection attempts failed")

                # 🔥 Применяем стабильную настройку к апстрим сокету
                apply_hard_reset_opts(upstream_writer)
                
                # 🔥 ФИКС: Сохраняем upstream writer для корректной очистки
                writer_srv = upstream_writer
                
                self.logger.info(f"[SOCKS5] Connected to {target_host}:{target_port} via {successful_ip}")

            except asyncio.TimeoutError:
                # Перехватываем зависание Docker-сети на macOS
                self.logger.error(f"[CONNECT] Timeout (15.0s) for {target_host}:{target_port}")
                
                # 🔥 ВРЕМЕННО ОТКЛЮЧАЕМ mutation trigger на connect timeout
                # Connect timeout НЕ означает DPI блокировку на этом этапе
                # НЕ вызываем orchestrator.report_failure() для стабилизации transport layer
                
                return

            except Exception as net_err:
                self.logger.error(f"[CONNECT] Connection failed to {target_host}: {net_err}")
                
                # 🔥 ВРЕМЕННО ОТКЛЮЧАЕМ mutation trigger на connection error
                # Connection error НЕ означает DPI блокировку на этом этапе
                # НЕ вызываем orchestrator.report_failure() для стабилизации transport layer
                
                return
            
            self.logger.info(f"[SOCKS5] Connected to {target_host}:{target_port}")
            
            # Сбрасываем состояние конвейера для новой сессии
            self.pipeline_manager.reset_session()
            
            # Передаем управление Pipeline Manager с улучшенным обработчиком жизненного цикла
            tasks = [
                asyncio.create_task(self.forward_client_to_upstream(client_reader, upstream_writer, session)),
                asyncio.create_task(self.forward_upstream_to_client(upstream_reader, client_writer))
            ]
            
            try:
                # Ждем завершения задач с обработкой исключений
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Отменяем ожидающие задачи при завершении одной из них
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # Проверяем результаты завершенных задач
                success_count = 0
                for task in done:
                    if task.exception() is None:
                        success_count += 1
                    else:
                        self.logger.error(f"[SOCKS5] Task failed: {task.exception()}")
                
                # Временно отключаем агрессивную DPI-классификацию для стабилизации
                # НЕ вызываем orchestrator для стабилизации transport layer
                
            except Exception as e:
                self.logger.error(f"[SOCKS5] Pipeline execution error: {e}")
                # Отменяем все задачи при критической ошибке
                for task in tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            
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
                
                # 🔥 КРИТИЧЕСКИЙ ПАТЧ: Обычный EOF - это не DPI drop
                if not data:
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
            # 🔥 ВРЕМЕННО ОТКЛЮЧАЕМ агрессивную DPI-классификацию для стабилизации transport layer
            # НЕ вызываем orchestrator на обычные ошибки соединения
            raise
    
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
            # 🔥 НЕ закрываем сокет здесь - централизованная очистка в handle_socks5_client
    
        
    async def start_server(self):
        """Запуск SOCKS5 сервера"""
        self.logger.info(f"Starting SOCKS5 server on port {self.listen_port}")
        
        # Используем стандартный asyncio.start_server без reuse_port для стабильности
        server = await asyncio.start_server(
            self.handle_socks5_client,
            '0.0.0.0',
            self.listen_port,
            reuse_address=True
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
        inspector = DpiSandboxInspector()
        orchestrator = SmartFailoverOrchestrator(inspector=inspector)
        
        # Pre-seed стратегии из внешнего URL (удалено - метод не существует)
        
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
