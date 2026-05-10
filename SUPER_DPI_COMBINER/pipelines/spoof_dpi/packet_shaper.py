"""
Packet Shaper Pipeline - TCP сегментация и манипуляция пакетами
"""

import asyncio
import time
import random
import socket
import ssl
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import SafePipeline, BypassTechnique, BypassRequest, BypassResponse, PipelineExecutionStatus
from core.http_client import TCPClient

class PacketShaperPipeline(SafePipeline):
    """Пайплайн для TCP сегментации и манипуляции пакетами"""
    
    def __init__(self):
        super().__init__("PacketShaper", BypassTechnique.SPOOF_DPI, priority=1, execution_status=PipelineExecutionStatus.REAL)
        self.segment_size = 1
        self.fake_ttl = 64
        self.delay_between_segments = 0.001
        self.tcp_client = TCPClient(timeout=10.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение реальной TCP сегментации"""
        start_time = time.time()
        
        try:
            # Создаем HTTP запрос для сегментации
            http_request = self._create_segmented_http_request(request)
            
            # Разбиваем запрос на сегменты
            segments = self._segment_request(http_request, self.segment_size)
            
            # Устанавливаем TCP соединение
            reader, writer = await self.tcp_client.create_connection(request.host, request.port)
            
            # Отправляем сегменты с задержкой
            for i, segment in enumerate(segments):
                await self.tcp_client.send_data(writer, segment)
                await asyncio.sleep(self.delay_between_segments)
                
                # Манипуляция TTL через опции сокета
                if self.fake_ttl != 64:
                    sock = writer.get_extra_info('socket')
                    if sock:
                        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.fake_ttl)
            
            # Получаем ответ
            response_data = await self.tcp_client.receive_data(reader, 8192)
            
            # Закрываем соединение
            await self.tcp_client.close_connection(writer)
            
            response_time = time.time() - start_time
            
            # Анализируем ответ
            success = len(response_data) > 0 and b'200' in response_data[:100]
            status_code = 200 if success else 403
            
            return BypassResponse(
                success=success,
                latency=response_time,
                status_code=status_code,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Segments': str(len(segments)),
                    'X-Segment-Size': str(self.segment_size),
                    'X-TTL': str(self.fake_ttl)
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=f"Packet shaper error: {str(e)}"
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.segment_size = config.get('tcp_segmentation', 1)
        self.fake_ttl = config.get('fake_ttl', 1)
        self.delay_between_segments = config.get('packet_delay', 0.001)
        
        self.tracer.info(f"PacketShaper initialized: segments={self.segment_size}, ttl={self.fake_ttl}")
        self._mark_initialized(True)
        return True
    
    def _create_segmented_http_request(self, request: BypassRequest) -> bytes:
        """Создание HTTP запроса для сегментации"""
        headers = request.headers or {}
        
        # Формируем HTTP запрос
        http_lines = [
            f"{request.method} / HTTP/1.1",
            f"Host: {request.host}",
            f"Connection: close",
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ]
        
        # Добавляем дополнительные заголовки
        for key, value in headers.items():
            http_lines.append(f"{key}: {value}")
        
        # Добавляем пустую строку и тело запроса
        http_lines.append("")
        if request.data:
            http_lines.append(request.data.decode('utf-8', errors='ignore'))
        
        return "\r\n".join(http_lines).encode('utf-8')
    
    def _segment_request(self, data: bytes, segment_size: int) -> list:
        """Разбиение данных на сегменты"""
        if segment_size <= 1:
            return [data]
        
        segments = []
        for i in range(0, len(data), segment_size):
            segment = data[i:i + segment_size]
            segments.append(segment)
        
        return segments
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.tcp_client:
            await self.tcp_client.cleanup()
        return True
