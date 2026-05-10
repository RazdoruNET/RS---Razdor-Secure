#!/usr/bin/env python3
"""
HTTP Fragmentation Pipeline - Реальная фрагментация HTTP запросов
Никакой симуляции - только настоящие сетевые операции
"""

import asyncio
import socket
import time
from ..core.contracts import BasePipeline, Request, Response
from ..core.packet_capture import get_packet_capture_layer

class HTTPFragmentation(BasePipeline):
    """Пайплайн реальной фрагментации HTTP запросов"""
    
    def __init__(self):
        super().__init__("HTTPFragmentation")
        self.chunk_size = 100  # bytes
        
    def execute(self, request: Request) -> Response:
        """Выполнить реальную фрагментацию"""
        start_time = time.time()
        
        try:
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(request.timeout)
            
            # Подключаемся
            sock.connect((request.host, request.port))
            get_packet_capture_layer().log_connect((request.host, request.port))
            
            # Формируем HTTP запрос
            http_request = f"{request.method} {request.path} HTTP/1.1\r\n"
            http_request += f"Host: {request.host}\r\n"
            http_request += "Connection: close\r\n"
            http_request += "\r\n"
            
            # Фрагментируем и отправляем
            request_bytes = http_request.encode()
            
            for i in range(0, len(request_bytes), self.chunk_size):
                chunk = request_bytes[i:i + self.chunk_size]
                sock.send(chunk)
                get_packet_capture_layer().log_send(chunk, chunk_index=i//self.chunk_size)
                time.sleep(0.001)  # Реальная задержка между чанками
            
            # Получаем ответ
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                get_packet_capture_layer().log_recv(chunk)
            
            # Закрываем сокет
            sock.close()
            get_packet_capture_layer().log_close()
            # Парсим HTTP ответ
            if response_data:
                response_text = response_data.decode('utf-8', errors='ignore')
                first_line = response_text.split('\r\n')[0]
                if '200' in first_line:
                    return Response(
                        success=True,
                        status_code=200,
                        data=response_data,
                        pipeline=self.name
                    )
                else:
                    return Response(
                        success=False,
                        status_code=int(first_line.split()[1]) if len(first_line.split()) > 1 else 0,
                        data=response_data,
                        pipeline=self.name,
                        error=f"HTTP {first_line.split()[1] if len(first_line.split()) > 1 else 'Unknown'}"
                    )
            else:
                return Response(
                    success=False,
                    error="Нет ответа от сервера",
                    pipeline=self.name
                )
                
        except Exception as e:
            return Response(
                success=False,
                error=f"HTTP Fragmentation error: {e}",
                pipeline=self.name
            )
