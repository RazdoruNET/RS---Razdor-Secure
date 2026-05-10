"""
HTTP Fragmentation Pipeline - Фрагментация HTTP запросов
"""

import asyncio
import time
import random
import socket
import logging
from typing import Dict, Any
from dataclasses import dataclass

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse
from core.http_client import TCPClient

@dataclass
class FragmentationConfig:
    """Конфигурация фрагментации"""
    fragment_size: int = 256
    fragment_delay: float = 0.001
    random_padding: bool = False

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
            
            # Устанавливаем соединение (TCP для HTTP, TLS для HTTPS)
            if request.port == 443:
                # HTTPS - используем TLS
                reader, writer = await self.tcp_client.create_tls_connection(request.host, request.port)
            else:
                # HTTP - используем plain TCP
                reader, writer = await self.tcp_client.create_connection(request.host, request.port)
            
            # Отправляем фрагменты с задержкой и настройками TCP
            for i, fragment in enumerate(fragments):
                # Устанавливаем TCP_NODELAY для гарантии фрагментации
                sock = writer.get_extra_info('socket')
                if sock:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                await self.tcp_client.send_data(writer, fragment)
                await asyncio.sleep(self.config.fragment_delay)
                
                # Padding отключен - ломает HTTP протокол
                # Для реальной packet fragmentation нужны raw sockets
                # asyncio stream не даёт контроля над packet boundaries
            
            # Получаем ответ полностью (все чанки)
            chunks = []
            while True:
                chunk = await asyncio.wait_for(
                    self.tcp_client.receive_data(reader, 8192),
                    timeout=30.0
                )
                if not chunk:
                    break
                chunks.append(chunk)
            
            response_data = b''.join(chunks)
            
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
        self.config = FragmentationConfig(**config)
        
        logger.info(f"HTTPFragmentation initialized: size={self.config.fragment_size}, delay={self.config.fragment_delay}, padding={self.config.random_padding}")
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
        """Разбиение данных на фрагменты"""
        fragments = []
        for i in range(0, len(data), fragment_size):
            fragment = data[i:i + fragment_size]
            fragments.append(fragment)
        return fragments
    
    def _parse_http_status(self, response_data: bytes) -> int:
        """Корректный парсинг HTTP статуса из ответа"""
        if not response_data:
            return 0
        
        try:
            # Ищем status line
            first_line = response_data.split(b'\r\n', 1)[0]
            
            # Парсим с помощью regex
            import re
            match = re.search(rb'HTTP/\d\.\d\s+(\d+)', first_line)
            if match:
                return int(match.group(1))
            
            # Fallback: ищем первое число после HTTP/
            parts = first_line.split(b' ')
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
            
            return 0
        except Exception:
            return 0
    
    def _generate_padding(self, size: int) -> bytes:
        """Генерация случайного дополнения"""
        return bytes([random.randint(0, 255) for _ in range(size)])
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.tcp_client:
            await self.tcp_client.cleanup()
        return True
