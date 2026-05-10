"""
HTTP Fragmentation Pipeline - Фрагментация HTTP запросов
"""

import asyncio
import time
import random
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse
from core.http_client import TCPClient

class HTTPFragmentationPipeline(BasePipeline):
    """Пайплайн для фрагментации HTTP запросов"""
    
    def __init__(self):
        super().__init__("HTTPFragmentation", BypassTechnique.SPOOF_DPI, priority=3)
        self.fragment_size = 256
        self.fragment_delay = 0.001
        self.random_padding = True
        self.tcp_client = TCPClient(timeout=10.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение реальной HTTP фрагментации"""
        start_time = time.time()
        
        try:
            # Создаем HTTP запрос для фрагментации
            http_request = self._create_fragmented_request(request)
            
            # Разбиваем на фрагменты
            fragments = self._fragment_data(http_request, self.fragment_size)
            
            # Устанавливаем TCP соединение
            reader, writer = await self.tcp_client.create_connection(request.host, request.port)
            
            # Отправляем фрагменты с задержкой
            for i, fragment in enumerate(fragments):
                # Добавляем случайное дополнение если включено
                if self.random_padding:
                    padding = self._generate_padding(random.randint(1, 16))
                    fragment += padding
                
                await self.tcp_client.send_data(writer, fragment)
                await asyncio.sleep(self.fragment_delay)
            
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
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Fragments': str(len(fragments)),
                    'X-Fragment-Size': str(self.fragment_size),
                    'X-Padding': str(self.random_padding)
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"HTTP fragmentation error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.fragment_size = config.get('fragment_size', 256)
        self.fragment_delay = config.get('fragment_delay', 0.001)
        self.random_padding = config.get('random_padding', True)
        
        print(f"✅ HTTPFragmentation инициализирован: size={self.fragment_size}, padding={self.random_padding}")
        return True
    
    def _create_fragmented_request(self, request: BypassRequest) -> bytes:
        """Создание HTTP запроса для фрагментации"""
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
    
    def _fragment_data(self, data: bytes, fragment_size: int) -> list:
        """Разбиение данных на фрагменты"""
        fragments = []
        for i in range(0, len(data), fragment_size):
            fragment = data[i:i + fragment_size]
            fragments.append(fragment)
        return fragments
    
    def _generate_padding(self, size: int) -> bytes:
        """Генерация случайного дополнения"""
        return bytes([random.randint(0, 255) for _ in range(size)])
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
