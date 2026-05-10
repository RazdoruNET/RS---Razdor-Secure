"""
HTTP Fragmentation Pipeline - Фрагментация HTTP протокола
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
from core.http_client import HTTPClient, TCPClient

class HTTPFragmentationPipeline(BasePipeline):
    """Пайплайн для фрагментации HTTP протокола"""
    
    def __init__(self):
        super().__init__("HTTPFragProtocol", BypassTechnique.PROTOCOL_OBFUSCATION, priority=1)
        self.chunk_size = 256
        self.random_padding = True
        self.header_obfuscation = True
        self.http_client = HTTPClient(timeout=15.0)
        self.tcp_client = TCPClient(timeout=10.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение реальной HTTP фрагментации"""
        start_time = time.time()
        
        try:
            # Создаем фрагментированный HTTP запрос
            fragmented_request = self._create_fragmented_request(request)
            
            # Разбиваем на чанки
            chunks = self._chunk_data(fragmented_request, self.chunk_size)
            
            # Устанавливаем TCP соединение для фрагментации
            reader, writer = await self.tcp_client.create_connection(request.host, request.port)
            
            # Отправляем чанки с задержкой для обхода DPI
            for i, chunk in enumerate(chunks):
                # Добавляем случайное дополнение если включено
                if self.random_padding:
                    padding = self._generate_padding(random.randint(1, 16))
                    chunk += padding
                
                await self.tcp_client.send_data(writer, chunk)
                await asyncio.sleep(0.001)  # Небольшая задержка между чанками
            
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
                    'X-Chunks': str(len(chunks)),
                    'X-Chunk-Size': str(self.chunk_size),
                    'X-Obfuscation': str(self.header_obfuscation),
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
        self.chunk_size = config.get('chunk_size', 256)
        self.random_padding = config.get('random_padding', True)
        self.header_obfuscation = config.get('header_obfuscation', True)
        
        print(f"✅ HTTPFragProtocol инициализирован: chunk={self.chunk_size}")
        return True
    
    def _create_fragmented_request(self, request: BypassRequest) -> bytes:
        """Создание фрагментированного HTTP запроса"""
        headers = request.headers or {}
        
        # Обфускация заголовков если включена
        if self.header_obfuscation:
            headers = self._obfuscate_headers(headers)
        
        # Формируем HTTP запрос с фрагментацией
        http_lines = [
            f"{request.method} / HTTP/1.1",
            f"Host: {request.host}",
            f"Connection: close",
            f"User-Agent: {self._get_random_user_agent()}",
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            f"Accept-Language: en-US,en;q=0.5",
            f"Cache-Control: no-cache",
            f"Pragma: no-cache"
        ]
        
        # Добавляем обфусцированные заголовки
        for key, value in headers.items():
            http_lines.append(f"{key}: {value}")
        
        # Добавляем пустую строку и тело запроса
        http_lines.append("")
        if request.data:
            http_lines.append(request.data.decode('utf-8', errors='ignore'))
        
        return "\r\n".join(http_lines).encode('utf-8')
    
    def _obfuscate_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Обфускация HTTP заголовков"""
        obfuscated = {}
        
        for key, value in headers.items():
            # Случайная капитализация
            obfuscated_key = ''.join(
                c.upper() if random.random() < 0.5 else c.lower() 
                for c in key
            )
            
            # Добавляем случайные пробелы
            if random.random() < 0.3:
                obfuscated_key = f" {obfuscated_key}"
            if random.random() < 0.3:
                obfuscated_key = f"{obfuscated_key} "
            
            obfuscated[obfuscated_key] = value
        
        return obfuscated
    
    def _get_random_user_agent(self) -> str:
        """Получение случайного User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101'
        ]
        return random.choice(user_agents)
    
    def _chunk_data(self, data: bytes, chunk_size: int) -> list:
        """Разбиение данных на чанки"""
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
    
    def _generate_padding(self, size: int) -> bytes:
        """Генерация случайного дополнения"""
        return bytes([random.randint(0, 255) for _ in range(size)])
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        await self.http_client.initialize()
        
        self.chunk_size = config.get('chunk_size', 256)
        self.random_padding = config.get('random_padding', True)
        self.header_obfuscation = config.get('header_obfuscation', True)
        
        print(f"✅ HTTPFragProtocol инициализирован: chunk={self.chunk_size}")
        return True
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        await self.http_client.cleanup()
        return True
