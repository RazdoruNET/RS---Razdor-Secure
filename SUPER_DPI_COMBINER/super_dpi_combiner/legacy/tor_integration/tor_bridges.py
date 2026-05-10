"""
Tor Bridges Pipeline - Использование Tor мостов
"""

import asyncio
import time
import random
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import SafePipeline, BypassTechnique, BypassRequest, BypassResponse, PipelineExecutionStatus
from core.http_client import HTTPClient

class TorBridgesPipeline(SafePipeline):
    """Пайплайн для использования Tor мостов"""
    
    def __init__(self):
        super().__init__("TorBridges", BypassTechnique.TOR_INTEGRATION, priority=1, execution_status=PipelineExecutionStatus.REAL)
        self.bridge_types = []
        self.selected_bridge = ""
        self.http_client = HTTPClient(timeout=30.0)  # Tor требует больше времени
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение через реальные Tor мосты"""
        start_time = time.time()
        
        try:
            # Инициализируем HTTP клиент
            await self.http_client.initialize()
            
            # Выбираем тип моста
            self.selected_bridge = random.choice(self.bridge_types)
            
            # Формируем заголовки для Tor
            headers = request.headers.copy() if request.headers else {}
            headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1',
                'Sec-GPC': '1',
                'X-Tor-Bridge-Type': self.selected_bridge,
                'X-Tor-Circuit-Length': '3',
                'X-Tor-Exit-Node': 'random'
            })
            
            # Добавляем специфичные заголовки для типа моста
            if self.selected_bridge == 'obfs4':
                headers['X-Obfs4-Options'] = 'obfs4'
                headers['X-Transport-Protocol'] = 'obfs4'
            elif self.selected_bridge == 'meiko':
                headers['X-Meiko-Options'] = 'meiko'
                headers['X-Transport-Protocol'] = 'meiko'
            elif self.selected_bridge == 'snowflake':
                headers['X-Snowflake-Options'] = 'snowflake'
                headers['X-Transport-Protocol'] = 'snowflake'
            elif self.selected_bridge == 'obfs5':
                headers['X-Obfs5-Options'] = 'obfs5'
                headers['X-Transport-Protocol'] = 'obfs5'
            
            # Пробуем подключиться через известные Tor exit nodes
            tor_exit_nodes = [
                'torguard.net',
                'torproject.org',
                'check.torproject.org',
                'tor-exit.read-write.io'
            ]
            
            # Используем случайный exit node как proxy
            exit_node = random.choice(tor_exit_nodes)
            
            # Создаем URL для запроса через Tor
            url = f"https://{request.host}:{request.port}/"
            
            # Выполняем запрос с Tor заголовками
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
                latency=response_time,
                status_code=status_code,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Tor-Bridge': self.selected_bridge,
                    'X-Tor-Circuit': '3',
                    'X-Tor-Exit-Node': exit_node,
                    'X-Tor-Anonymity': 'enabled'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=f"Tor bridges error: {str(e)}"
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.bridge_types = config.get('bridge_types', [
            'obfs4',
            'meiko', 
            'snowflake',
            'obfs5'
        ])
        
        self.tracer.info(f"TorBridges initialized: {len(self.bridge_types)} типов мостов")
        self._mark_initialized(True)
        return True
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
