"""
DNS Tunnel Pipeline - DNS туннелирование данных
"""

import asyncio
import time
import random
import base64
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class DNSTunnelPipeline(BasePipeline):
    """Пайплайн для DNS туннелирования"""
    
    def __init__(self):
        super().__init__("DNSTunnel", BypassTechnique.PROTOCOL_OBFUSCATION, priority=21)
        self.dns_servers = []
        self.domain = ""
        self.encoding_type = "base32"
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение через DNS туннель"""
        start_time = time.time()
        
        try:
            # Выбираем случайный DNS сервер
            server = random.choice(self.dns_servers)
            
            # Кодируем данные для DNS
            encoded_data = self._encode_data(request)
            
            # Разбиваем на DNS запросы
            dns_queries = self._split_into_queries(encoded_data)
            
            # Отправляем DNS запросы
            for i, query in enumerate(dns_queries):
                # Создаем DNS subdomain
                subdomain = f"{i}.{query}.{self.domain}"
                
                # Имитация DNS запроса
                await asyncio.sleep(0.005)
                
                # DNS TTL delay
                await asyncio.sleep(0.002)
            
            # DNS tunnel establishment
            await asyncio.sleep(0.02)
            
            # Data transfer through DNS
            await asyncio.sleep(0.025)
            
            response_time = time.time() - start_time
            
            # DNS tunneling очень эффективно обходит DPI
            success_probability = 0.7
            if len(dns_queries) < 100:
                success_probability += 0.1
            if self.encoding_type == 'base32':
                success_probability += 0.05
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-DNS-Server': server,
                    'X-Domain': self.domain,
                    'X-Queries': str(len(dns_queries)),
                    'X-Encoding': self.encoding_type,
                    'X-Protocol': 'DNS'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"DNS tunnel error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _encode_data(self, request: BypassRequest) -> str:
        """Кодирование данных для DNS"""
        # Собираем все данные
        data_parts = [
            request.host,
            str(request.port),
            request.method,
            str(request.headers) if request.headers else "",
            request.data.decode('utf-8', errors='ignore') if request.data else ""
        ]
        
        combined_data = '|'.join(data_parts)
        
        # Кодируем в соответствии с типом
        if self.encoding_type == 'base32':
            return base64.b32encode(combined_data.encode()).decode()
        elif self.encoding_type == 'base64':
            return base64.b64encode(combined_data.encode()).decode()
        elif self.encoding_type == 'hex':
            return combined_data.encode().hex()
        else:
            return combined_data
    
    def _split_into_queries(self, encoded_data: str) -> list:
        """Разбиение данных на DNS запросы"""
        max_label_length = 63  # Максимальная длина DNS label
        queries = []
        
        for i in range(0, len(encoded_data), max_label_length):
            chunk = encoded_data[i:i + max_label_length]
            queries.append(chunk)
        
        return queries
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.dns_servers = config.get('dns_servers', [
            '8.8.8.8',      # Google DNS
            '1.1.1.1',      # Cloudflare DNS
            '208.67.222.222', # OpenDNS
            '9.9.9.9',      # Quad9 DNS
            '1.0.0.1',      # DNSCrypt
            '208.67.220.220', # OpenDNS secondary
            '64.6.64.6',     # Verisign DNS
            '8.26.56.26',    # Comodo DNS
            '84.200.69.80'    # DNS.WATCH
        ])
        
        self.domain = config.get('tunnel_domain', 'tunnel.darknet.org')
        self.encoding_type = config.get('encoding_type', 'base32')
        
        print(f"✅ DNSTunnel инициализирован: {len(self.dns_servers)} DNS серверов, домен={self.domain}")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
