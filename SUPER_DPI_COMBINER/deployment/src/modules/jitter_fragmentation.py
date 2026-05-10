#!/usr/bin/env python3
"""
Jitter Fragmentation Module - Динамическая фрагментация с jitter
"""

import random
import asyncio
from base_module import BasePipelineModule

class JitterFragmentationModule(BasePipelineModule):
    """Модуль динамической фрагментации с jitter"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Параметры динамического jitter
        self.min_chunk_size = int(config.get('MIN_CHUNK_SIZE', '40'))
        self.max_chunk_size = int(config.get('MAX_CHUNK_SIZE', '150'))
        self.min_chunk_delay = float(config.get('MIN_CHUNK_DELAY', '0.001'))
        self.max_chunk_delay = float(config.get('MAX_CHUNK_DELAY', '0.003'))
        
        # Порог селективной фрагментации
        self.fragmentation_threshold = int(config.get('SELECTIVE_THRESHOLD', '3000'))
        
        # Счетчик байт для сессии
        self.bytes_sent = 0
        
        self.logger.info(f"JitterFragmentationModule initialized: chunk_size={self.min_chunk_size}-{self.max_chunk_size}, delay={self.min_chunk_delay}-{self.max_chunk_delay}s")
    
    async def process(self, data: bytes, writer_srv) -> bytes:
        """
        Обработка данных с динамической фрагментацией
        
        Args:
            data: Входящие байты от клиента
            writer_srv: Сокет целевого сервера
            
        Returns:
            Пустой байтовый массив (модуль сам отправляет данные)
        """
        if not data:
            return b''
        
        # Определяем, сколько байт можно фрагментировать в рамках порога
        remaining_threshold = self.fragmentation_threshold - self.bytes_sent
        data_to_fragment = min(len(data), remaining_threshold)
        
        self.logger.info(f"[{self.get_module_name()}] Processing {len(data)} bytes, fragmenting {data_to_fragment} (threshold remaining: {remaining_threshold})")
        
        # Фрагментация с динамическим jitter
        i = 0
        fragment_count = 0
        
        while i < data_to_fragment:
            # Динамический размер чанка
            current_chunk_size = random.randint(self.min_chunk_size, self.max_chunk_size)
            chunk_end = min(i + current_chunk_size, data_to_fragment)
            chunk = data[i:chunk_end]
            
            # Отправляем чанк
            writer_srv.write(chunk)
            await writer_srv.drain()
            
            fragment_count += 1
            self.bytes_sent += len(chunk)
            
            self.logger.info(f"[{self.get_module_name()}] Jitter fragment {fragment_count}: {len(chunk)} bytes (random_size={current_chunk_size})")
            
            # Динамическая задержка
            current_delay = random.uniform(self.min_chunk_delay, self.max_chunk_delay)
            if current_delay > 0:
                await asyncio.sleep(current_delay)
            
            i = chunk_end
        
        # Если остались данные за пределами порога, отправляем их без фрагментации
        if data_to_fragment < len(data):
            remaining_data = data[data_to_fragment:]
            self.logger.info(f"[{self.get_module_name()}] Passthrough: sending {len(remaining_data)} bytes without fragmentation")
            writer_srv.write(remaining_data)
            await writer_srv.drain()
            self.bytes_sent += len(remaining_data)
        
        self.logger.info(f"[{self.get_module_name()}] Complete: {fragment_count} fragments, total_session_bytes: {self.bytes_sent}")
        
        # Возвращаем пустой массив, так как модуль сам отправил все данные
        return b''
    
    def reset_session(self):
        """Сброс счетчика для новой сессии"""
        self.bytes_sent = 0
        self.logger.info(f"[{self.get_module_name()}] Session reset")
