"""
Host Header Pipeline - Подмена Host заголовка
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

class HostHeaderPipeline(BasePipeline):
    """Пайплайн для подмены Host заголовка"""
    
    def __init__(self):
        super().__init__("HostHeader", BypassTechnique.DOMAIN_FRONTING, priority=2)
        self.host_overrides = []
        self.selected_host = ""
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с подменой Host заголовка"""
        start_time = time.time()
        
        try:
            # Выбираем случайный Host для подмены
            self.selected_host = random.choice(self.host_overrides)
            
            # Имитация запроса с подмененным Host
            await asyncio.sleep(0.01)
            
            # Имитация успешного ответа
            response_time = time.time() - start_time
            
            # Вероятность успеха зависит от Host
            success_probability = 0.4
            if 'google' in self.selected_host:
                success_probability += 0.2
            elif 'facebook' in self.selected_host:
                success_probability += 0.15
            elif 'cloudflare' in self.selected_host:
                success_probability += 0.1
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-Original-Host': request.host,
                    'X-Fake-Host': self.selected_host,
                    'Host': self.selected_host
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"Host header error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.host_overrides = config.get('host_overrides', [
            'www.google.com',
            'www.youtube.com',
            'www.facebook.com',
            'www.cloudflare.com',
            'cdn.jsdelivr.net'
        ])
        
        print(f"✅ HostHeader инициализирован: {len(self.host_overrides)} Host заголовков")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
