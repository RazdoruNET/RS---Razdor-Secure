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
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class AutoSwitchPipeline(BasePipeline):
    """Пайплайн для автоматического переключения техник"""
    
    def __init__(self):
        super().__init__("AutoSwitch", BypassTechnique.ADAPTIVE, priority=1)
        self.available_techniques = []
        self.current_technique = ""
        self.switch_threshold = 0.3
        self.success_history = []
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с автоматическим переключением"""
        start_time = time.time()
        
        try:
            # Выбираем текущую технику
            self.current_technique = random.choice(self.available_techniques)
            
            # Имитация выполнения текущей техники
            if self.current_technique == 'spoof_dpi':
                await asyncio.sleep(0.015)
                success_prob = 0.4
            elif self.current_technique == 'domain_fronting':
                await asyncio.sleep(0.02)
                success_prob = 0.45
            elif self.current_technique == 'protocol_obfuscation':
                await asyncio.sleep(0.018)
                success_prob = 0.35
            elif self.current_technique == 'tor_integration':
                await asyncio.sleep(0.05)
                success_prob = 0.6
            elif self.current_technique == 'omega_transport':
                await asyncio.sleep(0.03)
                success_prob = 0.45
            else:
                await asyncio.sleep(0.025)
                success_prob = 0.4
            
            # Адаптивная корректировка на основе истории
            if len(self.success_history) > 10:
                recent_success = sum(self.success_history[-10:]) / 10
                if recent_success < self.switch_threshold:
                    success_prob += 0.1  # Увеличиваем шанс успеха при переключении
            
            success = random.random() < success_prob
            
            # Сохраняем в историю
            self.success_history.append(1 if success else 0)
            if len(self.success_history) > 100:
                self.success_history = self.success_history[-100:]
            
            response_time = time.time() - start_time
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-Current-Technique': self.current_technique,
                    'X-Auto-Switch': 'enabled',
                    'X-Success-Rate': f"{sum(self.success_history[-10:]) / min(10, len(self.success_history)):.2f}"
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"Auto switch error: {str(e)}",
                response_time=time.time() - start_time
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
        
        print(f"✅ AutoSwitch инициализирован: {len(self.available_techniques)} техник")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
