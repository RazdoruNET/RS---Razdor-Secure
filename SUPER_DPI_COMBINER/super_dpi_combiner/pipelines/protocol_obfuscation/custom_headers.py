"""
Custom Headers Pipeline - Обфускация HTTP заголовков
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

class CustomHeadersPipeline(SafePipeline):
    """Пайплайн для обфускации HTTP заголовков"""
    
    def __init__(self):
        super().__init__("CustomHeaders", BypassTechnique.PROTOCOL_OBFUSCATION, priority=2, execution_status=PipelineExecutionStatus.REAL)
        self.custom_headers = []
        self.random_order = True
        self.http_client = HTTPClient(timeout=15.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальными кастомными заголовками"""
        start_time = time.time()
        
        try:
            # Инициализируем HTTP клиент
            await self.http_client.initialize()
            
            # Формируем кастомные заголовки
            headers_to_use = self.custom_headers.copy()
            
            if self.random_order:
                random.shuffle(headers_to_use)
            
            # Создаем базовые заголовки
            headers = request.headers.copy() if request.headers else {}
            
            # Добавляем кастомные заголовки
            for header in headers_to_use[:15]:  # Ограничиваем количество
                headers[header['name']] = header['value']
            
            # Добавляем стандартные заголовки для обхода
            headers.update({
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'DNT': '1'
            })
            
            # Создаем URL для запроса
            url = f"https://{request.host}:{request.port}/"
            
            # Выполняем запрос с кастомными заголовками
            success, status_code, response_headers, response_data, response_time = await self.http_client.make_request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.data,
                allow_redirects=True
            )
            
            # Анализируем ответ
            success = success and status_code in [200, 201, 202, 301, 302]
            
            # Формируем использованные заголовки для ответа
            used_headers = {}
            for header in headers_to_use[:10]:
                used_headers[header['name']] = header['value']
            
            return BypassResponse(
                success=success,
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers=used_headers
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"Custom headers error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.random_order = config.get('random_order', True)
        
        # Генерируем кастомные заголовки
        self.custom_headers = [
            {'name': 'X-Forwarded-For', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Real-IP', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Client-IP', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Originating-IP', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Remote-IP', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Remote-Addr', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Cluster-Client-IP', 'value': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"},
            {'name': 'X-Forwarded-Proto', 'value': random.choice(['https', 'http'])},
            {'name': 'X-Forwarded-Host', 'value': random.choice(['cdn.google.com', 'www.google.com', 'cloudflare.com'])},
            {'name': 'X-Forwarded-Server', 'value': random.choice(['nginx', 'apache', 'cloudflare'])},
            {'name': 'X-Content-Type-Options', 'value': 'nosniff'},
            {'name': 'X-XSS-Protection', 'value': '1; mode=block'},
            {'name': 'X-Frame-Options', 'value': 'SAMEORIGIN'},
            {'name': 'Strict-Transport-Security', 'value': 'max-age=31536000; includeSubDomains'},
            {'name': 'Content-Security-Policy', 'value': "default-src 'self'"},
            {'name': 'Referrer-Policy', 'value': 'strict-origin-when-cross-origin'},
            {'name': 'Permissions-Policy', 'value': 'geolocation=()'},
            {'name': 'Cache-Control', 'value': 'no-cache, no-store, must-revalidate'},
            {'name': 'Pragma', 'value': 'no-cache'},
            {'name': 'Expires', 'value': '0'},
            {'name': 'Accept-Language', 'value': random.choice(['en-US,en;q=0.9', 'ru-RU,ru;q=0.9,en;q=0.8'])},
            {'name': 'Accept-Encoding', 'value': 'gzip, deflate, br'},
            {'name': 'DNT', 'value': '1'},
            {'name': 'Sec-CH-UA', 'value': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"'},
            {'name': 'Sec-CH-UA-Mobile', 'value': '?0'},
            {'name': 'Sec-CH-UA-Platform', 'value': '"macOS"'},
            {'name': 'Sec-Fetch-Dest', 'value': 'document'},
            {'name': 'Sec-Fetch-Mode', 'value': 'navigate'},
            {'name': 'Sec-Fetch-Site', 'value': 'none'},
            {'name': 'Sec-Fetch-User', 'value': '?1'},
            {'name': 'Upgrade-Insecure-Requests', 'value': '1'},
            {'name': 'Sec-GPC', 'value': '1'},
            {'name': 'Save-Data', 'value': 'on'},
            {'name': 'Device-Memory', 'value': '8'},
            {'name': 'Viewport-Width', 'value': '1920'},
            {'name': 'Viewport-Height', 'value': '1080'},
        ]
        
        print(f"✅ CustomHeaders инициализирован: {len(self.custom_headers)} заголовков")
        return True
    
    def _get_random_user_agent(self) -> str:
        """Получение случайного User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0)'
        ]
        return random.choice(user_agents)
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
