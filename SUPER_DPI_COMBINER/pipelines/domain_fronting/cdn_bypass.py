"""
CDN Bypass Pipeline - Обход через CDN маскировку
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

class CDNBypassPipeline(BasePipeline):
    """Пайплайн для обхода через CDN маскировку"""
    
    def __init__(self):
        super().__init__("CDNBypass", BypassTechnique.DOMAIN_FRONTING, priority=1)
        self.cdn_domains = []
        self.selected_cdn = ""
        self.http_client = HTTPClient(timeout=15.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение реального CDN обхода"""
        start_time = time.time()
        
        try:
            # Выбираем CDN и создаем URL для domain fronting
            cdn_config = self._select_cdn_config()
            
            # Создаем заголовки для domain fronting
            fronting_headers = self._create_fronting_headers(request, cdn_config)
            
            # Формируем URL через CDN
            fronting_url = f"https://{cdn_config['cdn_domain']}/"
            
            # Выполняем запрос через CDN
            success, status_code, response_headers, response_data, response_time = await self.http_client.make_request(
                method=request.method,
                url=fronting_url,
                headers=fronting_headers,
                data=request.data,
                allow_redirects=True
            )
            
            # Анализируем ответ на предмет успешного обхода
            bypass_success = self._analyze_bypass_success(response_headers, response_data)
            
            return BypassResponse(
                success=bypass_success,
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-CDN': cdn_config['cdn_domain'],
                    'X-Fronting': 'enabled',
                    'X-Target-Host': request.host,
                    'X-Fronting-Type': cdn_config['fronting_type']
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"CDN bypass error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _select_cdn_config(self) -> Dict[str, str]:
        """Выбор конфигурации CDN для domain fronting"""
        cdn_configs = [
            {
                'cdn_domain': 'cdn.jsdelivr.net',
                'fronting_type': 'host_header',
                'target_header': 'X-Original-Host'
            },
            {
                'cdn_domain': 'ajax.googleapis.com',
                'fronting_type': 'host_override',
                'target_header': 'Host'
            },
            {
                'cdn_domain': 'cdnjs.cloudflare.com',
                'fronting_type': 'sni_spoof',
                'target_header': 'X-Forwarded-Host'
            },
            {
                'cdn_domain': 'unpkg.com',
                'fronting_type': 'path_based',
                'target_header': 'X-Real-Host'
            }
        ]
        
        return random.choice(cdn_configs)
    
    def _create_fronting_headers(self, request: BypassRequest, cdn_config: Dict[str, str]) -> Dict[str, str]:
        """Создание заголовков для domain fronting"""
        headers = request.headers.copy() if request.headers else {}
        
        # Domain Fronting техники
        if cdn_config['fronting_type'] == 'host_header':
            headers['Host'] = request.host
            headers[cdn_config['target_header']] = request.host
        elif cdn_config['fronting_type'] == 'host_override':
            headers['Host'] = cdn_config['cdn_domain']
            headers[cdn_config['target_header']] = request.host
        elif cdn_config['fronting_type'] == 'sni_spoof':
            headers['Host'] = cdn_config['cdn_domain']
            headers['X-Forwarded-Host'] = request.host
            headers['X-Original-Host'] = request.host
        elif cdn_config['fronting_type'] == 'path_based':
            headers['Host'] = cdn_config['cdn_domain']
            headers['X-Real-Host'] = request.host
        
        # Добавляем стандартные заголовки для обхода
        headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        return headers
    
    def _analyze_bypass_success(self, response_headers: Dict[str, str], response_data: bytes) -> bool:
        """Анализ успешности обхода на основе ответа"""
        # Проверяем статус код
        if '200' in str(response_headers):
            return True
        
        # Проверяем наличие контента
        if len(response_data) > 1000:
            return True
        
        # Проверяем заголовки CDN
        cdn_indicators = ['cloudflare', 'fastly', 'akamai', 'cloudfront', 'azure']
        for header_value in response_headers.values():
            if any(indicator in header_value.lower() for indicator in cdn_indicators):
                return True
        
        return False
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        await self.http_client.initialize()
        
        self.cdn_domains = config.get('cdn_domains', [
            'cdn.jsdelivr.net',
            'ajax.googleapis.com', 
            'cdnjs.cloudflare.com',
            'unpkg.com',
            'raw.githubusercontent.com'
        ])
        
        print(f"✅ CDNBypass инициализирован: {len(self.cdn_domains)} CDN доменов")
        return True
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        await self.http_client.cleanup()
        return True
