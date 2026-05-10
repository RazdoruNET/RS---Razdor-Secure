#!/usr/bin/env python3
"""
TLS Chameleon Module - Маскировка отпечатков TLS через SNI splitting
"""

import asyncio
from typing import Optional
from base_module import BasePipelineModule

class TlsChameleonModule(BasePipelineModule):
    """Модуль для обхода DPI через расщепление SNI в TLS Client Hello"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Параметры модуля
        self.sni_splitting_enabled = config.get('SNI_SPLITTING_ENABLED', 'true').lower() == 'true'
        self.min_packet_size = int(config.get('MIN_PACKET_SIZE', '100'))
        
        self.logger.info(f"TlsChameleonModule initialized: sni_splitting={self.sni_splitting_enabled}")
    
    async def process(self, data: bytes, writer_srv) -> bytes:
        """
        Обработка данных с расщеплением SNI
        
        Args:
            data: Входящие байты от клиента
            writer_srv: Сокет целевого сервера
            
        Returns:
            Остаток байт для передачи следующему модулю
        """
        if not data or not self.sni_splitting_enabled:
            return data
        
        # Проверяем, это ли TLS Client Hello
        if not self._is_tls_client_hello(data):
            return data
        
        self.logger.info(f"[{self.get_module_name()}] TLS Client Hello detected, attempting SNI splitting")
        
        # Ищем SNI в Client Hello
        sni_info = self._find_sni_position(data)
        
        if sni_info is None:
            self.logger.info(f"[{self.get_module_name()}] SNI not found, sending as-is")
            return data
        
        sni_start, sni_end, sni_domain = sni_info
        
        # Расщепляем SNI
        split_point = sni_start + (sni_end - sni_start) // 2
        
        # Первая часть (до середины SNI)
        first_part = data[:split_point]
        
        # Вторая часть (остаток SNI и все остальное)
        second_part = data[split_point:]
        
        self.logger.info(f"[{self.get_module_name()}] SNI splitting: domain='{sni_domain}', "
                        f"split at offset {split_point} ({len(first_part)}/{len(second_part)} bytes)")
        
        # Отправляем первую часть
        writer_srv.write(first_part)
        await writer_srv.drain()
        
        # Небольшая задержка для имитации реальной фрагментации
        await asyncio.sleep(0.001)
        
        # Отправляем вторую часть
        writer_srv.write(second_part)
        await writer_srv.drain()
        
        self.logger.info(f"[{self.get_module_name()}] SNI splitting complete")
        
        # Возвращаем пустые байты, так как все отправлено
        return b''
    
    def _is_tls_client_hello(self, data: bytes) -> bool:
        """
        Проверка, является ли пакет TLS Client Hello
        
        Args:
            data: Байты для проверки
            
        Returns:
            True если это TLS Client Hello
        """
        if len(data) < 6:
            return False
        
        # TLS Record: Type (1) + Version (2) + Length (2)
        record_type = data[0]
        version_bytes = data[1:3]
        version_int = int.from_bytes(version_bytes, byteorder='big')
        
        # Проверяем, это ли TLS Handshake record (0x16)
        if record_type != 0x16:
            return False
        
        # Проверяем версию TLS (1.0-1.3)
        if version_int not in [0x0301, 0x0302, 0x0303, 0x0304]:
            return False
        
        # Проверяем, это ли Handshake message типа Client Hello (0x01)
        if len(data) >= 6 and data[5] != 0x01:
            return False
        
        return True
    
    def _find_sni_position(self, data: bytes) -> Optional[tuple]:
        """
        Поиск позиции SNI в TLS Client Hello
        
        Args:
            data: TLS Client Hello байты
            
        Returns:
            Кортеж (sni_start, sni_end, sni_domain) или None
        """
        try:
            # Пропускаем TLS Record header (5 байт)
            if len(data) < 5:
                return None
            
            # Пропускаем Handshake header (4 байт)
            handshake_start = 5
            if len(data) < handshake_start + 4:
                return None
            
            # Находим начало Session ID
            session_id_length = data[handshake_start + 38]
            current_pos = handshake_start + 39 + session_id_length
            
            # Находим начало Cipher Suites
            if current_pos + 2 > len(data):
                return None
            
            cipher_suites_length = int.from_bytes(data[current_pos:current_pos + 2], byteorder='big')
            current_pos += 2 + cipher_suites_length
            
            # Находим начало Compression Methods
            if current_pos + 1 > len(data):
                return None
            
            compression_methods_length = data[current_pos]
            current_pos += 1 + compression_methods_length
            
            # Находим начало Extensions
            if current_pos + 2 > len(data):
                return None
            
            extensions_length = int.from_bytes(data[current_pos:current_pos + 2], byteorder='big')
            current_pos += 2
            
            extensions_end = current_pos + extensions_length
            if extensions_end > len(data):
                return None
            
            # Ищем расширение SNI (type 0x0000)
            while current_pos + 4 <= extensions_end:
                ext_type = int.from_bytes(data[current_pos:current_pos + 2], byteorder='big')
                ext_length = int.from_bytes(data[current_pos + 2:current_pos + 4], byteorder='big')
                
                if ext_type == 0x0000:  # SNI extension
                    # Пропускаем заголовок расширения и тип SNI (0x0000)
                    sni_data_start = current_pos + 4 + 2
                    
                    if sni_data_start + 2 > extensions_end:
                        return None
                    
                    # Длина SNI
                    sni_length = int.from_bytes(data[sni_data_start:sni_data_start + 2], byteorder='big')
                    sni_start = sni_data_start + 2
                    sni_end = sni_start + sni_length
                    
                    if sni_end > extensions_end:
                        return None
                    
                    # Пропускаем первый байт (тип имени - 0x00 для hostname)
                    actual_sni_start = sni_start + 1
                    actual_sni_length = sni_length - 1
                    
                    if actual_sni_start + actual_sni_length > len(data):
                        return None
                    
                    sni_bytes = data[actual_sni_start:actual_sni_start + actual_sni_length]
                    sni_domain = sni_bytes.decode('utf-8', errors='ignore')
                    
                    return (actual_sni_start, actual_sni_start + actual_sni_length, sni_domain)
                
                # Переходим к следующему расширению
                current_pos += 4 + ext_length
            
        except Exception as e:
            self.logger.debug(f"[{self.get_module_name()}] Error parsing SNI: {e}")
        
        return None
    
    def reset_session(self):
        """Сброс состояния для новой сессии"""
        self.logger.info(f"[{self.get_module_name()}] Session reset")
