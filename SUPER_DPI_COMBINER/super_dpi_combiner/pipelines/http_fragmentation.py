#!/usr/bin/env python3
"""
HTTP Fragmentation Pipeline - Реальная фрагментация HTTP запросов
"""

import socket
import time
import random
from ..core.base import BasePipeline, Request, Response

class HTTPFragmentation(BasePipeline):
    """Пайплайн фрагментации HTTP запросов"""
    
    def __init__(self):
        super().__init__("HTTPFragmentation")
        self.chunk_size = 100  # bytes
        
    def execute(self, request: Request) -> Response:
        """Выполнить фрагментированный HTTP запрос"""
        try:
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(request.timeout)
            
            # Подключаемся
            sock.connect((request.host, request.port))
            
            # Формируем HTTP запрос
            http_request = f"{request.method} / HTTP/1.1\r\n"
            http_request += f"Host: {request.host}\r\n"
            http_request += "Connection: close\r\n"
            http_request += "\r\n"
            
            # Фрагментируем запрос
            request_bytes = http_request.encode()
            
            # Отправляем чанками
            for i in range(0, len(request_bytes), self.chunk_size):
                chunk = request_bytes[i:i + self.chunk_size]
                sock.send(chunk)
                time.sleep(0.001)  # Небольшая задержка между чанками
            
            # Получаем ответ
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            sock.close()
            
            # Парсим HTTP ответ
            if response_data:
                first_line = response_data.split(b'\r\n')[0].decode()
                if '200' in first_line:
                    return Response(
                        success=True,
                        status_code=200,
                        data=response_data
                    )
                else:
                    return Response(
                        success=False,
                        status_code=int(first_line.split()[1]) if len(first_line.split()) > 1 else 0,
                        data=response_data
                    )
            else:
                return Response(
                    success=False,
                    error="Нет ответа от сервера"
                )
                
        except Exception as e:
            return Response(
                success=False,
                error=f"HTTP Fragmentation ошибка: {e}"
            )
