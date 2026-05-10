#!/usr/bin/env python3
"""
HTTP Client - Стабилизированный клиент с реальными сетевыми операциями
Только asyncio, без внешних зависимостей
"""

import asyncio
import ssl
import socket
from typing import Optional
from .contracts import Request, Response

class HTTPClient:
    """Минимальный HTTP клиент с реальными сетевыми операциями"""
    
    def __init__(self):
        self.reader = None
        self.writer = None
        self.ssl_context = ssl.create_default_context()
        
    async def connect(
        self,
        host: str,
        port: int,
        ssl_enabled: bool = False,
        timeout: float = 10.0
    ) -> bool:
        """Подключиться к серверу"""
        try:
            target = (host, port)
            
            if ssl_enabled:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(target, ssl=self.ssl_context),
                    timeout=timeout
                )
            else:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(target),
                    timeout=timeout
                )
                
            return True
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            return False
            
    async def send(self, data: bytes) -> bool:
        """Отправить данные"""
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True
        except Exception:
            return False
            
    async def receive(self, limit: int = 8192) -> bytes:
        """Получить данные"""
        try:
            data = await asyncio.wait_for(
                self.reader.read(limit),
                timeout=10.0
            )
            return data
        except asyncio.TimeoutError:
            return b""
            
    async def close(self) -> None:
        """Закрыть соединение"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            
    async def make_request(
        self,
        request: Request,
        ssl_enabled: bool = False
    ) -> Response:
        """Сделать HTTP запрос"""
        try:
            # Подключаемся
            connected = await self.connect(
                request.host,
                request.port,
                ssl_enabled,
                request.timeout
            )
            
            if not connected:
                return Response(
                    success=False,
                    error=f"Connection failed to {request.host}:{request.port}"
                )
            
            # Формируем HTTP запрос
            http_request = (
                f"{request.method} {request.path} HTTP/1.1\r\n"
                f"Host: {request.host}\r\n"
                f"Connection: close\r\n"
            )
            
            # Добавляем headers
            for key, value in request.headers.items():
                http_request += f"{key}: {value}\r\n"
                
            http_request += "\r\n"
            
            # Отправляем запрос
            request_sent = await self.send(http_request.encode())
            if not request_sent:
                return Response(
                    success=False,
                    error="Failed to send request"
                )
            
            # Получаем ответ
            response_data = await self.receive()
            
            # Закрываем соединение
            await self.close()
            
            # Парсим HTTP ответ
            if response_data:
                response_text = response_data.decode('utf-8', errors='ignore')
                lines = response_text.split('\r\n')
                
                if lines:
                    status_line = lines[0]
                    parts = status_line.split(' ')
                    
                    status_code = 0
                    if len(parts) >= 2:
                        try:
                            status_code = int(parts[1])
                        except ValueError:
                            status_code = 0
                    
                    # Ищем конец headers
                    body_start = -1
                    for i, line in enumerate(lines):
                        if line.strip() == '':
                            body_start = i + 1
                            break
                    
                    body = b""
                    if body_start > 0 and body_start < len(lines):
                        body = '\r\n'.join(lines[body_start:]).encode()
                    
                    return Response(
                        success=True,
                        status_code=status_code,
                        data=body,
                        latency=0.0  # Will be set by caller
                    )
            else:
                return Response(
                    success=False,
                    error="No response received"
                )
                
        except Exception as e:
            await self.close()
            return Response(
                success=False,
                error=f"HTTP Client error: {e}"
            )
