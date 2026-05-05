"""
I2P Garlic Routing Pipeline - Garlic routing через I2P
"""

import asyncio
import time
import random
import hashlib
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class I2PGarlicPipeline(BasePipeline):
    """Пайплайн для Garlic Routing через I2P"""
    
    def __init__(self):
        super().__init__("I2PGarlic", BypassTechnique.TOR_INTEGRATION, priority=10)
        self.i2p_routers = []
        self.garlic_cloves = 0
        self.tunnel_depth = 3
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение через I2P Garlic Routing"""
        start_time = time.time()
        
        try:
            # Выбираем случайный I2P router
            router = random.choice(self.i2p_routers)
            
            # Создаем garlic cloves (вложенные сообщения)
            self.garlic_cloves = random.randint(3, 7)
            
            # Garlic routing - многослойное шифрование
            for i in range(self.tunnel_depth):
                await asyncio.sleep(0.008)  # Каждый слой шифрования
                # Имитация создания garlic clove
                await asyncio.sleep(0.002)
            
            # Отправка через I2P сеть
            await asyncio.sleep(0.015)
            
            response_time = time.time() - start_time
            
            # I2P очень надежен для анонимности
            success_probability = 0.7
            if self.garlic_cloves > 5:
                success_probability += 0.1
            if self.tunnel_depth >= 3:
                success_probability += 0.05
            
            success = random.random() < success_probability
            
            # Генерируем I2P адрес для ответа
            i2p_address = self._generate_i2p_address()
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 503,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-I2P-Router': router,
                    'X-Garlic-Cloves': str(self.garlic_cloves),
                    'X-Tunnel-Depth': str(self.tunnel_depth),
                    'X-I2P-Address': i2p_address,
                    'X-Network': 'I2P'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"I2P garlic routing error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _generate_i2p_address(self) -> str:
        """Генерация I2P адреса"""
        # I2P адреса - 52 символа Base32
        chars = 'abcdefghijklmnopqrstuvwxyz234567'
        address = ''.join(random.choice(chars) for _ in range(52))
        return f"{address}.b32.i2p"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.i2p_routers = config.get('i2p_routers', [
            'router1.i2p.net:4567',
            'router2.i2p.net:4567',
            'router3.i2p.net:4567',
            'router4.i2p.net:4567',
            'router5.i2p.net:4567',
            'i2p-prod.i2p.net:4567',
            'i2p-dev.i2p.net:4567',
            'reseed.i2p.net:4567',
            'seed.i2p.net:4567',
            'bootstrap.i2p.net:4567'
        ])
        self.tunnel_depth = config.get('tunnel_depth', 3)
        
        print(f"✅ I2PGarlic инициализирован: {len(self.i2p_routers)} роутеров, глубина={self.tunnel_depth}")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
