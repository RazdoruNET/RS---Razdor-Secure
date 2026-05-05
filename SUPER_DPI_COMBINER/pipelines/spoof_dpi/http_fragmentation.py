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

class HTTPFragmentationPipeline(BasePipeline):
    """Пайплайн для фрагментации HTTP запросов"""
    
    def __init__(self):
        super().__init__("HTTPFragmentation", BypassTechnique.SPOOF_DPI, priority=3)
        self.fragment_size = 256
        self.fragment_delay = 0.001
        self.random_padding = True
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение HTTP фрагментации"""
        start_time = time.time()
        
        try:
            # Имитация фрагментации HTTP запроса
            if request.data:
                data_size = len(request.data)
                fragments_needed = (data_size + self.fragment_size - 1) // self.fragment_size
            else:
                fragments_needed = 1
            
            # Отправляем фрагменты с задержкой
            for i in range(fragments_needed):
                await asyncio.sleep(self.fragment_delay)
                
                # Случайное дополнение если включено
                if self.random_padding and random.random() < 0.3:
                    await asyncio.sleep(0.001)  # Padding delay
            
            # Имитация успешного ответа
            response_time = time.time() - start_time
            
            # Вероятность успеха зависит от фрагментации
            success_probability = 0.35
            if self.fragment_size < 512:
                success_probability += 0.2
            if self.random_padding:
                success_probability += 0.1
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-Fragments': str(fragments_needed),
                    'X-Fragment-Size': str(self.fragment_size)
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
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
