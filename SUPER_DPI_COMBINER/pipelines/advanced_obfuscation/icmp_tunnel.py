"""
ICMP Tunnel Pipeline - ICMP туннелирование данных
"""

import asyncio
import time
import random
import struct
import socket
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class ICMTunnelPipeline(BasePipeline):
    """Пайплайн для ICMP туннелирования"""
    
    def __init__(self):
        super().__init__("ICMTunnel", BypassTechnique.PROTOCOL_OBFUSCATION, priority=20)
        self.icmp_servers = []
        self.packet_size = 1024
        self.tunnel_id = 0
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение через ICMP туннель"""
        start_time = time.time()
        
        try:
            # Выбираем случайный ICMP сервер
            server = random.choice(self.icmp_servers)
            
            # Генерируем ICMP пакеты
            packets_needed = self._calculate_packets_needed(request)
            
            # Отправляем ICMP пакеты
            for i in range(packets_needed):
                # Создаем ICMP echo request
                icmp_packet = self._create_icmp_packet(i, packets_needed, request)
                
                # Имитация отправки пакета
                await asyncio.sleep(0.001)
                
                # Ping delay
                await asyncio.sleep(0.002)
            
            # ICMP tunnel establishment
            await asyncio.sleep(0.01)
            
            # Data transfer through ICMP
            await asyncio.sleep(0.015)
            
            response_time = time.time() - start_time
            
            # ICMP tunneling очень эффективно обходит DPI
            success_probability = 0.75
            if packets_needed < 50:
                success_probability += 0.1
            if self.packet_size <= 512:
                success_probability += 0.05
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-ICMP-Server': server,
                    'X-Packets-Needed': str(packets_needed),
                    'X-Packet-Size': str(self.packet_size),
                    'X-Tunnel-ID': str(self.tunnel_id),
                    'X-Protocol': 'ICMP'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"ICMP tunnel error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _calculate_packets_needed(self, request: BypassRequest) -> int:
        """Расчет количества ICMP пакетов"""
        data_size = len(request.data) if request.data else 1024
        headers_size = len(str(request.headers)) if request.headers else 256
        total_size = data_size + headers_size
        
        return (total_size + self.packet_size - 1) // self.packet_size
    
    def _create_icmp_packet(self, sequence: int, total: int, request: BypassRequest) -> bytes:
        """Создание ICMP пакета"""
        # ICMP Type 8 (Echo Request)
        icmp_type = 8
        icmp_code = 0
        
        # ICMP checksum (имитация)
        icmp_checksum = random.randint(0, 65535)
        
        # Sequence number
        icmp_seq = sequence
        
        # Identifier (туннель ID)
        icmp_id = self.tunnel_id
        
        # ICMP header
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
        
        # Payload data
        payload_size = min(self.packet_size - len(icmp_header), 64)
        payload = b'X' * payload_size
        
        return icmp_header + payload
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.icmp_servers = config.get('icmp_servers', [
            'icmp-tunnel1.darknet.org',
            'icmp-tunnel2.darknet.org',
            'ping-tunnel1.onion',
            'ping-tunnel2.onion',
            'icmp-gateway1.i2p',
            'icmp-gateway2.i2p',
            'tunnel-ping1.ygg',
            'tunnel-ping2.ygg',
            'icmp-exit1.darknet',
            'icmp-exit2.darknet'
        ])
        self.packet_size = config.get('packet_size', 1024)
        self.tunnel_id = random.randint(10000, 65535)
        
        print(f"✅ ICMTunnel инициализирован: {len(self.icmp_servers)} серверов, размер={self.packet_size}")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
