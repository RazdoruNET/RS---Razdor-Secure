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
from core.http_client import HTTPClient

class HostHeaderPipeline(BasePipeline):
    """Пайплайн для подмены Host заголовка"""
    
    def __init__(self):
        super().__init__("HostHeader", BypassTechnique.DOMAIN_FRONTING, priority=2)
        self.host_overrides = []
        self.selected_host = ""
        self.http_client = HTTPClient(timeout=15.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальной подменой Host заголовка"""
        start_time = time.time()
        
        try:
            # Инициализируем HTTP клиент
            await self.http_client.initialize()
            
            # Выбираем Host для подмены
            self.selected_host = random.choice(self.host_overrides)
            
            # Создаем заголовки с подменой Host
            headers = request.headers.copy() if request.headers else {}
            headers['Host'] = self.selected_host
            headers['X-Original-Host'] = request.host
            headers['X-Forwarded-Host'] = request.host
            
            # Добавляем стандартные заголовки для обхода
            headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            
            # Создаем URL для запроса
            url = f"https://{self.selected_host}/"
            
            # Выполняем запрос с подмененным Host
            success, status_code, response_headers, response_data, response_time = await self.http_client.make_request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.data,
                allow_redirects=True
            )
            
            # Анализируем ответ
            success = success and status_code in [200, 201, 202, 301, 302]
            
            return BypassResponse(
                success=success,
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Original-Host': request.host,
                    'X-Fake-Host': self.selected_host,
                    'Host': self.selected_host,
                    'X-SNI-Bypass': 'enabled'
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
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
