#!/usr/bin/env python3
"""
Fake Packet Module - Инъекция мусорных TLS данных для сбивания DPI
"""

import os
from base_module import BasePipelineModule

class FakePacketModule(BasePipelineModule):
    """Модуль для инъекции мусорных TLS данных"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Параметры модуля
        self.fake_packet_hex = config.get('FAKE_PACKET_BYTES', '0x160301000500000000')
        self.first_packet_sent = False
        
        # Конвертируем hex строку в байты
        try:
            # Удаляем префикс 0x если есть
            hex_str = self.fake_packet_hex.replace('0x', '')
            self.fake_packet_bytes = bytes.fromhex(hex_str)
            self.logger.info(f"FakePacketModule initialized: fake_packet={self.fake_packet_hex} ({len(self.fake_packet_bytes)} bytes)")
        except ValueError as e:
            self.logger.error(f"FakePacketModule: Invalid hex format for FAKE_PACKET_BYTES: {e}")
            # Используем значение по умолчанию
            self.fake_packet_bytes = bytes.fromhex('160301000500000000')
            self.logger.info(f"FakePacketModule: Using default fake packet: {len(self.fake_packet_bytes)} bytes")
    
    async def process(self, data: bytes, writer_srv) -> bytes:
        """
        Обработка данных с инъекцией мусорного пакета
        
        Args:
            data: Входящие байты от клиента
            writer_srv: Сокет целевого сервера
            
        Returns:
            Исходные данные для передачи следующему модулю
        """
        if not data:
            return data
        
        # Проверяем, это первый пакет в сессии
        if self.is_first_packet(data) and not self.first_packet_sent:
            self.logger.info(f"[{self.get_module_name()}] First packet detected, injecting fake packet ({len(self.fake_packet_bytes)} bytes)")
            
            # Отправляем мусорный пакет
            writer_srv.write(self.fake_packet_bytes)
            await writer_srv.drain()
            
            self.first_packet_sent = True
            self.logger.info(f"[{self.get_module_name()}] Fake packet injected successfully")
        
        # Передаем исходные данные дальше без изменений
        return data
    
    def reset_session(self):
        """Сброс флага для новой сессии"""
        self.first_packet_sent = False
        self.logger.info(f"[{self.get_module_name()}] Session reset - ready for new fake packet injection")
