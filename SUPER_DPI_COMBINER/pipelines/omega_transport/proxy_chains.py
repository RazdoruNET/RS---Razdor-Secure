"""
Proxy Chains Pipeline - Цепочки прокси серверов
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

class ProxyChainsPipeline(BasePipeline):
    """Пайплайн для цепочек прокси серверов"""
    
    def __init__(self):
        super().__init__("ProxyChains", BypassTechnique.OMEGA_TRANSPORT, priority=2)
        self.proxy_servers = []
        self.chain_length = 1
        self.encryption_method = "aes256"
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение через цепочки прокси"""
        start_time = time.time()
        
        try:
            # Выбираем случайные прокси для цепочки
            selected_proxies = random.sample(self.proxy_servers, 
                                        min(self.chain_length, len(self.proxy_servers)))
            
            # Имитация прохождения через цепочку прокси
            for i, proxy in enumerate(selected_proxies):
                await asyncio.sleep(0.02)  # Задержка каждого прыжка
                
                # Дополнительная задержка для шифрования
                if self.encryption_method == 'aes256':
                    await asyncio.sleep(0.005)
                elif self.encryption_method == 'chacha20':
                    await asyncio.sleep(0.003)
            
            response_time = time.time() - start_time
            
            # Вероятность успеха зависит от длины цепочки
            success_probability = 0.4
            if self.chain_length == 1:
                success_probability += 0.2
            elif self.chain_length == 2:
                success_probability += 0.1
            elif self.chain_length >= 3:
                success_probability -= 0.1
            
            # Бонус за шифрование
            if self.encryption_method in ['aes256', 'chacha20']:
                success_probability += 0.05
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-Proxy-Chain': f"{len(selected_proxies)} hops",
                    'X-Chain-Path': ' -> '.join(selected_proxies),
                    'X-Encryption': self.encryption_method
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"Proxy chains error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.proxy_servers = config.get('proxy_servers', [
            'proxy1.omega-network.com:8080',
            'proxy2.omega-network.com:8443',
            'proxy3.omega-network.com:3128',
            'proxy4.omega-network.com:1080',
            'proxy5.omega-network.com:8888',
            'proxy6.omega-network.com:9000',
            'proxy7.omega-network.com:8000',
            'proxy8.omega-network.com:8081',
            'proxy9.omega-network.com:8444',
            'proxy10.omega-network.com:3129'
        ])
        self.chain_length = config.get('proxy_chains', 1)
        self.encryption_method = config.get('encryption_methods', 'aes256')
        
        print(f"✅ ProxyChains инициализирован: {len(self.proxy_servers)} прокси, цепочка={self.chain_length}")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
