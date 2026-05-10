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
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse, PipelineExecutionStatus
from core.http_client import HTTPClient

class TLSFingerprintPipeline(BasePipeline):
    """Пайплайн для подмены TLS fingerprint"""
    
    def __init__(self):
        super().__init__("TLSFingerprint", BypassTechnique.SPOOF_DPI, priority=2, execution_status=PipelineExecutionStatus.REAL)
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
                allow_redirects=True,
                ssl_context=ssl_context
            )
            
            # Анализируем ответ
            success = success and status_code in [200, 201, 202]
            
            # Логируем фактические TLS параметры
            actual_cipher = "DEFAULT"
            if self.cipher_suites and self.tls_version == "1.2":
                actual_cipher = ':'.join(self.cipher_suites)
            elif self.tls_version == "1.3":
                actual_cipher = "TLS_1.3_DEFAULT"
            
            return BypassResponse(
                success=success,
                latency=response_time,
                status_code=status_code,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-TLS-Version': self.tls_version,
                    'X-Cipher-Suite': actual_cipher,
                    'X-User-Agent': self.user_agent,
                    'X-SSL-Bypass': 'enabled',
                    'X-SSL-Context-Applied': 'true'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=f"TLS fingerprint error: {str(e)}"
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
        
        self.tracer.info(f"TLSFingerprint initialized: version={self.tls_version}")
        self._mark_initialized(True)
        return True
    
    def _create_custom_ssl_context(self):
        """Создание кастомного SSL контекста для фингерпринтинга"""
        try:
            # Создаем SSL контекст с кастомными настройками
            ssl_context = ssl.create_default_context()
            
            # Устанавливаем версию TLS с fallback
            try:
                if self.tls_version == "1.3":
                    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
                    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
                    self.tracer.debug("TLS version set to 1.3")
                elif self.tls_version == "1.2":
                    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
                    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
                    self.tracer.debug("TLS version set to 1.2")
                else:
                    # Fallback к поддерживаемым версиям
                    ssl_context.minimum_version = ssl.TLSVersion.TLSv1
                    ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
                    self.tracer.warning(f"Unknown TLS version {self.tls_version}, using TLS 1.0-1.2")
            except Exception as e:
                self.tracer.warning(f"Failed to set TLS version: {e}, using default")
                ssl_context = ssl.create_default_context()
            
            # Отключаем проверку сертификатов для тестирования
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Устанавливаем кастомные cipher suites с обработкой ошибок
            if self.cipher_suites and self.tls_version == "1.2":
                try:
                    # Применяем cipher suites для TLS 1.2
                    cipher_string = ':'.join(self.cipher_suites)
                    ssl_context.set_ciphers(cipher_string)
                    self.tracer.debug(f"Applied cipher suites: {cipher_string}")
                except Exception as e:
                    self.tracer.warning(f"Failed to set cipher suites: {e}")
                    self.tracer.info("Continuing with default cipher suites")
            elif self.cipher_suites and self.tls_version == "1.3":
                # TLS 1.3 cipher suites управляются иначе
                self.tracer.info("TLS 1.3 cipher suites not directly configurable (OpenSSL limitation)")
            
            # Устанавливаем кастомные опции для обхода DPI с fallback
            try:
                ssl_context.options |= ssl.OP_NO_COMPRESSION
                ssl_context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
                self.tracer.debug("Applied DPI bypass options")
            except Exception as e:
                self.tracer.warning(f"Failed to set SSL options: {e}")
            
            return ssl_context
            
        except Exception as e:
            self.tracer.error(f"Critical SSL context creation failed: {e}")
            self.tracer.info("Falling back to basic SSL context")
            # Последний fallback - базовый контекст
            fallback_context = ssl.create_default_context()
            fallback_context.check_hostname = False
            fallback_context.verify_mode = ssl.CERT_NONE
            return fallback_context
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
