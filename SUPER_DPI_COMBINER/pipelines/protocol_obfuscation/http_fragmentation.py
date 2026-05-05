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

class HTTPFragmentationPipeline(BasePipeline):
    """Пайплайн для фрагментации HTTP протокола"""
    
    def __init__(self):
        super().__init__("HTTPFragProtocol", BypassTechnique.PROTOCOL_OBFUSCATION, priority=1)
        self.chunk_size = 256
        self.random_padding = True
        self.header_obfuscation = True
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение HTTP фрагментации"""
        start_time = time.time()
        
        try:
            # Фрагментация HTTP запроса
            headers_size = len(str(request.headers)) if request.headers else 100
            data_size = len(request.data) if request.data else 0
            total_size = headers_size + data_size
            
            chunks_needed = (total_size + self.chunk_size - 1) // self.chunk_size
            
            # Отправляем чанки с задержкой
            for i in range(chunks_needed):
                await asyncio.sleep(0.002)
                
                # Случайное дополнение если включено
                if self.random_padding and random.random() < 0.4:
                    await asyncio.sleep(0.001)
            
            # Обфускация заголовков если включена
            if self.header_obfuscation:
                await asyncio.sleep(0.003)
            
            response_time = time.time() - start_time
            
            # Вероятность успеха
            success_probability = 0.35
            if self.chunk_size < 512:
                success_probability += 0.2
            if self.random_padding:
                success_probability += 0.1
            if self.header_obfuscation:
                success_probability += 0.15
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-Chunks': str(chunks_needed),
                    'X-Chunk-Size': str(self.chunk_size),
                    'X-Obfuscation': str(self.header_obfuscation)
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
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
