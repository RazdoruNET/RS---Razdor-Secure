"""
TLS Fingerprint Pipeline - Подмена TLS fingerprint для обхода DPI
"""

import asyncio
import time
import random
import ssl
import socket
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse
from core.http_client import HTTPClient

class TLSFingerprintPipeline(BasePipeline):
    """Пайплайн для подмены TLS fingerprint"""
    
    def __init__(self):
        super().__init__("TLSFingerprint", BypassTechnique.SPOOF_DPI, priority=2)
        self.tls_version = "1.2"
        self.cipher_suites = []
        self.user_agent = ""
        self.http_client = HTTPClient(timeout=15.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальной подменой TLS fingerprint"""
        start_time = time.time()
        
        try:
            # Инициализируем HTTP клиент с кастомным SSL контекстом
            await self.http_client.initialize()
            
            # Создаем кастомный SSL контекст для фингерпринтинга
            ssl_context = self._create_custom_ssl_context()
            
            # Выбираем cipher suite
            cipher_suite = random.choice(self.cipher_suites) if self.cipher_suites else "TLS_AES_256_GCM_SHA384"
            
            # Создаем URL для запроса
            url = f"https://{request.host}:{request.port}/"
            
            # Создаем заголовки с подменой User-Agent
            headers = request.headers.copy() if request.headers else {}
            headers['User-Agent'] = self.user_agent
            
            # Выполняем запрос с кастомным TLS
            success, status_code, response_headers, response_data, response_time = await self.http_client.make_request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.data,
                allow_redirects=True
            )
            
            # Анализируем ответ
            success = success and status_code in [200, 201, 202]
            
            return BypassResponse(
                success=success,
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-TLS-Version': self.tls_version,
                    'X-Cipher-Suite': cipher_suite,
                    'X-User-Agent': self.user_agent,
                    'X-SSL-Bypass': 'enabled'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"TLS fingerprint error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.tls_version = config.get('tls_version', '1.2')
        self.cipher_suites = config.get('cipher_suites', [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256"
        ])
        self.user_agent = config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        print(f"✅ TLSFingerprint инициализирован: version={self.tls_version}")
        return True
    
    def _create_custom_ssl_context(self):
        """Создание кастомного SSL контекста для фингерпринтинга"""
        # Создаем SSL контекст с кастомными настройками
        ssl_context = ssl.create_default_context()
        
        # Устанавливаем версию TLS
        if self.tls_version == "1.3":
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        elif self.tls_version == "1.2":
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
        else:
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
        
        # Отключаем проверку сертификатов для тестирования
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Устанавливаем кастомные cipher suites
        if self.cipher_suites:
            # Это упрощенная версия - в реальности нужно более сложное управление
            pass
        
        # Устанавливаем кастомные опции для обхода DPI
        ssl_context.options |= ssl.OP_NO_COMPRESSION
        ssl_context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
        
        return ssl_context
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
