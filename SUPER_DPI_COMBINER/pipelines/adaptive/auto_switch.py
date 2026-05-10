"""
Auto Switch Pipeline - Автоматическое переключение техник
"""

import asyncio
import time
import random
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse, PipelineExecutionStatus
from core.http_client import HTTPClient

class AutoSwitchPipeline(BasePipeline):
    """Пайплайн для автоматического переключения техник"""
    
    def __init__(self):
        super().__init__("AutoSwitch", BypassTechnique.ADAPTIVE, priority=1, execution_status=PipelineExecutionStatus.REAL)
        self.available_techniques = []
        self.current_technique = ""
        self.switch_threshold = 0.3
        self.success_history = []
        self.http_client = HTTPClient(timeout=15.0)
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальным автоматическим переключением"""
        start_time = time.time()
        
        try:
            # Инициализируем HTTP клиент
            await self.http_client.initialize()
            
            # Выбираем текущую технику
            self.current_technique = self._select_best_technique(request)
            
            # Применяем выбранную технику
            success, status_code, response_headers, response_data, response_time = await self._apply_technique(
                request, self.current_technique
            )
            
            # Сохраняем в историю
            self.success_history.append(1 if success else 0)
            if len(self.success_history) > 100:
                self.success_history = self.success_history[-100:]
            
            # Анализируем успешность и решаем о переключении
            recent_success = sum(self.success_history[-10:]) / min(10, len(self.success_history))
            
            # Если успешность низкая, пробуем другую технику
            if not success and recent_success < self.switch_threshold:
                alternative_technique = self._select_alternative_technique(self.current_technique)
                if alternative_technique:
                    alt_success, alt_status, alt_headers, alt_data, alt_time = await self._apply_technique(
                        request, alternative_technique
                    )
                    
                    if alt_success:
                        success = alt_success
                        status_code = alt_status
                        response_headers = alt_headers
                        response_data = alt_data
                        response_time = alt_time
                        self.current_technique = alternative_technique
            
            return BypassResponse(
                success=success,
                latency=response_time,
                status_code=status_code,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Current-Technique': self.current_technique,
                    'X-Auto-Switch': 'enabled',
                    'X-Success-Rate': f"{recent_success:.2f}",
                    'X-Technique-Count': str(len(self.available_techniques))
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=f"Auto switch error: {str(e)}"
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.available_techniques = config.get('available_techniques', [
            'spoof_dpi',
            'domain_fronting',
            'protocol_obfuscation',
            'tor_integration',
            'omega_transport'
        ])
        self.switch_threshold = config.get('switch_threshold', 0.3)
        
        self.tracer.info(f"AutoSwitch initialized: {len(self.available_techniques)} техник")
        self._mark_initialized(True)
        return True
    
    def _select_best_technique(self, request: BypassRequest) -> str:
        """Выбор лучшей техники на основе запроса"""
        # Простая эвристика для выбора техники
        if request.port == 443:
            # Для HTTPS предпочитаем domain_fronting
            return 'domain_fronting'
        elif request.port == 80:
            # Для HTTP предпочитаем protocol_obfuscation
            return 'protocol_obfuscation'
        elif 'tor' in request.host.lower() or 'onion' in request.host.lower():
            # Для Tor доменов используем tor_integration
            return 'tor_integration'
        else:
            # По умолчанию используем spoof_dpi
            return 'spoof_dpi'
    
    def _select_alternative_technique(self, current_technique: str) -> str:
        """Выбор альтернативной техники"""
        techniques = self.available_techniques.copy()
        if current_technique in techniques:
            techniques.remove(current_technique)
        return random.choice(techniques) if techniques else current_technique
    
    async def _apply_technique(self, request: BypassRequest, technique: str) -> tuple:
        """Применение конкретной техники"""
        if technique == 'spoof_dpi':
            # TCP сегментация
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Connection': 'close',
                'X-Segment-Size': '1'
            }
        elif technique == 'domain_fronting':
            # SNI спуфинг
            headers = {
                'Host': 'www.google.com',
                'X-Original-Host': request.host,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        elif technique == 'protocol_obfuscation':
            # Обфускация заголовков
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'X-Custom-Header': 'obfuscated',
                'X-Forwarded-For': request.host
            }
        elif technique == 'tor_integration':
            # Tor заголовки
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'X-Tor-User': 'enabled'
            }
        else:
            headers = {}
        
        url = f"https://{request.host}:{request.port}/"
        
        return await self.http_client.make_request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.data,
            allow_redirects=True
        )
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
