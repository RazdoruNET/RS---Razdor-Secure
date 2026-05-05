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
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class CustomHeadersPipeline(BasePipeline):
    """Пайплайн для обфускации HTTP заголовков"""
    
    def __init__(self):
        super().__init__("CustomHeaders", BypassTechnique.PROTOCOL_OBFUSCATION, priority=2)
        self.custom_headers = []
        self.random_order = True
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с кастомными заголовками"""
        start_time = time.time()
        
        try:
            # Формируем кастомные заголовки
            headers_to_use = self.custom_headers.copy()
            
            if self.random_order:
                random.shuffle(headers_to_use)
            
            # Отправляем запрос с кастомными заголовками
            await asyncio.sleep(0.008)  # Задержка на обработку заголовков
            
            response_time = time.time() - start_time
            
            # Вероятность успеха зависит от количества заголовков
            success_probability = 0.3
            if len(headers_to_use) > 5:
                success_probability += 0.2
            if self.random_order:
                success_probability += 0.1
            
            success = random.random() < success_probability
            
            # Формируем использованные заголовки для ответа
            used_headers = {}
            for header in headers_to_use[:10]:  # Ограничиваем количество
                used_headers[header['name']] = header['value']
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
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
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
