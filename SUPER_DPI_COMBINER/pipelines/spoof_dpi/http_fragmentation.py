"""
HTTP Fragmentation Pipeline - Фрагментация HTTP запросов
"""

import asyncio
import time
import random
import socket
import logging
import re
from typing import Dict, Any
from dataclasses import dataclass

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse
from core.http_client import TCPClient

from enum import Enum

class FragmentMode(Enum):
    """Режимы фрагментации"""
    FIXED = "fixed"
    RANDOM = "random"
    HEADER_BODY_SPLIT = "header_body_split"
    BYTE_BY_BYTE = "byte_by_byte"

@dataclass
class FragmentationConfig:
    """Конфигурация фрагментации"""
    fragment_size: int = 256
    fragment_delay: float = 0.001
    random_padding: bool = False
    fragment_mode: FragmentMode = FragmentMode.FIXED
    jitter_range: tuple = (0.8, 1.2)  # Random jitter для задержек

logger = logging.getLogger(__name__)

class HTTPFragmentationPipeline(BasePipeline):
    """Пайплайн для фрагментации HTTP запросов"""
    
    def __init__(self):
        super().__init__("HTTPFragmentation", BypassTechnique.SPOOF_DPI, priority=3)
        self.config = FragmentationConfig()
        self.tcp_client = TCPClient(timeout=10.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение реальной HTTP фрагментации"""
        start_time = time.time()
        
        writer = None
        reader = None
        
        try:
            # Создаем HTTP запрос для фрагментации
            http_request = self._create_fragmented_request(request)
            
            # Разбиваем на фрагменты
            fragments = self._fragment_data(http_request, self.config.fragment_size)
            
            # Устанавливаем соединение (TCP для HTTP, TLS для HTTPS) с валидацией
            try:
                if request.port == 443:
                    # HTTPS - используем TLS
                    connection_result = await self.tcp_client.create_tls_connection(request.host, request.port)
                else:
                    # HTTP - используем plain TCP
                    connection_result = await self.tcp_client.create_connection(request.host, request.port)
                
                # Валидируем результат соединения
                if not isinstance(connection_result, tuple) or len(connection_result) != 2:
                    raise ConnectionError(f"Invalid connection result: {connection_result}")
                
                reader, writer = connection_result
                
            except Exception as e:
                logger.error(f"Connection failed: {str(e)}")
                raise
            
            # Устанавливаем TCP_NODELAY один раз для гарантии фрагментации
            sock = writer.get_extra_info('socket')
            if sock:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Отправляем фрагменты с задержкой и jitter
            for i, fragment in enumerate(fragments):
                await self.tcp_client.send_data(writer, fragment)
                
                # Добавляем jitter к задержке для имитации реального трафика
                jitter_delay = random.uniform(*self.config.jitter_range)
                actual_delay = self.config.fragment_delay * jitter_delay
                await asyncio.sleep(actual_delay)
                
                # Padding отключен - ломает HTTP протокол
                # Для реальной packet fragmentation нужны raw sockets
                # asyncio stream не даёт контроля над packet boundaries
            
            # Получаем ответ полностью (надежное чтение с защитой от бесконечного цикла)
            buffer = bytearray()
            max_response_size = 10 * 1024 * 1024  # 10MB лимит
            start_read_time = time.time()
            max_read_time = 60.0  # 60 секунд максимум на чтение
            
            while True:
                # Проверяем таймаут чтения
                elapsed = time.time() - start_read_time
                if elapsed > max_read_time:
                    logger.warning(f"Response read timeout after {elapsed:.1f}s")
                    break
                
                # Проверяем размер буфера
                if len(buffer) > max_response_size:
                    logger.warning(f"Response too large: {len(buffer)} bytes, truncating")
                    break
                
                try:
                    chunk = await asyncio.wait_for(
                        reader.read(8192),
                        timeout=5.0  # Таймаут на каждый chunk
                    )
                    if not chunk:
                        break
                    buffer.extend(chunk)
                except asyncio.TimeoutError:
                    logger.warning("Chunk read timeout, ending response read")
                    break
            
            response_data = bytes(buffer)
            
            response_time = time.time() - start_time
            
            # Анализируем ответ с корректным парсингом status line
            status_code = self._parse_http_status(response_data)
            success = 200 <= status_code < 400
            
            return BypassResponse(
                success=success,
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Fragments': str(len(fragments)),
                    'X-Fragment-Size': str(self.config.fragment_size),
                    'X-Fragment-Delay': str(self.config.fragment_delay),
                    'X-Random-Padding': str(self.config.random_padding)
                }
            )
            
        except Exception as e:
            logger.error(f"HTTP fragmentation error: {str(e)}")
            return BypassResponse(
                success=False,
                error=f"HTTP fragmentation error: {str(e)}",
                response_time=time.time() - start_time
            )
        finally:
            # Гарантированное закрытие соединения
            if writer:
                try:
                    await self.tcp_client.close_connection(writer)
                except Exception as e:
                    logger.error(f"Error closing connection: {str(e)}")
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        try:
            self.config = FragmentationConfig(
                fragment_size=config.get('fragment_size', 256),
                fragment_delay=config.get('fragment_delay', 0.001),
                random_padding=config.get('random_padding', False),
                # Безопасный парсинг FragmentMode с fallback
                mode_str = config.get('fragment_mode', 'FIXED').upper()
                try:
                    fragment_mode = FragmentMode[mode_str]
                except KeyError:
                    logger.warning(f"Unknown fragment mode '{mode_str}', falling back to FIXED")
                    fragment_mode = FragmentMode.FIXED
                jitter_range=config.get('jitter_range', (0.8, 1.2))
            )
        except Exception as e:
            logger.error(f"Invalid config: {str(e)}")
            return False
        
        logger.info(f"HTTPFragmentation initialized: size={self.config.fragment_size}, delay={self.config.fragment_delay}, mode={self.config.fragment_mode.value}")
        return True
    
    def _create_fragmented_request(self, request: BypassRequest) -> bytes:
        """Создание HTTP запроса для фрагментации"""
        headers = request.headers or {}
        path = getattr(request, 'path', '/')
        
        # Формируем базовые заголовки
        request_headers = {
            "Host": request.host,
            "Connection": "close",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            **headers
        }
        
        # Добавляем Content-Length если есть тело
        body = request.data or b""
        if body:
            request_headers["Content-Length"] = str(len(body))
            if "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/octet-stream"
        
        # Собираем HTTP запрос как bytes
        lines = [f"{request.method} {path} HTTP/1.1".encode()]
        
        for key, value in request_headers.items():
            lines.append(f"{key}: {value}".encode())
        
        lines.append(b"")  # Пустая строка перед телом
        
        # Собираем полный запрос
        request_bytes = b"\r\n".join(lines) + b"\r\n" + body
        
        return request_bytes
    
    def _fragment_data(self, data: bytes, fragment_size: int) -> list:
        """Разбиение данных на фрагменты с учётом режима"""
        fragments = []
        
        if self.config.fragment_mode == FragmentMode.HEADER_BODY_SPLIT:
            # Разделяем headers и body
            split_pos = data.find(b'\r\n\r\n')
            if split_pos != -1:
                headers = data[:split_pos]
                body = data[split_pos + 4:]
                fragments.append(headers)
                if body:
                    fragments.append(body)
            else:
                fragments.append(data)
        elif self.config.fragment_mode == FragmentMode.BYTE_BY_BYTE:
            # Побайтовая фрагментация с защитой от перегрузки
            if len(data) > 4096:  # Защита от перегрузки event loop
                logger.warning(f"Data too large for BYTE_BY_BYTE mode: {len(data)} bytes, falling back to FIXED")
                # Fallback на FIXED режим
                for i in range(0, len(data), self.config.fragment_size):
                    fragment = data[i:i + self.config.fragment_size]
                    fragments.append(fragment)
            else:
                for byte in data:
                    fragments.append(bytes([byte]))
        elif self.config.fragment_mode == FragmentMode.RANDOM:
            # Случайные размеры фрагментов
            pos = 0
            while pos < len(data):
                size = random.randint(1, min(fragment_size, len(data) - pos))
                fragments.append(data[pos:pos + size])
                pos += size
        else:  # FIXED
            # Фиксированная фрагментация
            for i in range(0, len(data), fragment_size):
                fragment = data[i:i + fragment_size]
                fragments.append(fragment)
        
        return fragments
    
    def _parse_http_status(self, response_data: bytes) -> int:
        """Устойчивый парсинг HTTP статуса из ответа"""
        if not response_data:
            return 0
        
        try:
            # Ищем status line в первых 10 строках (для устойчивости к garbage)
            lines = response_data.split(b"\r\n")
            
            for line in lines[:10]:
                match = re.search(rb'HTTP/\d\.\d\s+(\d+)', line)
                if match:
                    return int(match.group(1))
            
            # Fallback: ищем первое число после HTTP/
            for line in lines[:5]:
                parts = line.split(b' ')
                if len(parts) >= 2 and b'HTTP/' in parts[0]:
                    try:
                        return int(parts[1])
                    except ValueError:
                        pass
            
            return 0
        except Exception:
            return 0
    
        
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.tcp_client:
            await self.tcp_client.cleanup()
        return True
