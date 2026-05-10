#!/usr/bin/env python3
"""
SNI Case Modifier Module - Изменение регистра HTTP заголовков для обхода DPI
"""

import random
from base_module import BasePipelineModule

class SniCaseModifierModule(BasePipelineModule):
    """Модуль для хаотичного изменения регистра HTTP заголовков"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Параметры модуля
        self.modification_probability = float(config.get('CASE_MODIFY_PROBABILITY', '0.7'))
        
        # Список HTTP заголовков для модификации
        self.target_headers = [
            b'host:',
            b'connection:',
            b'user-agent:',
            b'accept:',
            b'accept-language:',
            b'accept-encoding:',
            b'cookie:',
            b'referer:',
            b'authorization:',
            b'content-type:',
            b'content-length:',
            b'x-forwarded-for:',
            b'x-real-ip:',
        ]
        
        self.logger.info(f"SniCaseModifierModule initialized: probability={self.modification_probability}")
    
    async def process(self, data: bytes, writer_srv) -> bytes:
        """
        Обработка данных с изменением регистра HTTP заголовков
        
        Args:
            data: Входящие байты от клиента
            writer_srv: Сокет целевого сервера (не используется)
            
        Returns:
            Модифицированные данные
        """
        if not data:
            return data
        
        # Проверяем, есть ли HTTP заголовки в данных
        data_lower = data.lower()
        if not (b'http/1.' in data_lower or b'get ' in data_lower or b'post ' in data_lower):
            # Не HTTP трафик, возвращаем как есть
            return data
        
        # Применяем модификацию регистра
        modified_data = self._modify_case_randomly(data)
        
        if modified_data != data:
            self.logger.info(f"[{self.get_module_name()}] Modified case in HTTP headers")
        
        return modified_data
    
    def _modify_case_randomly(self, data: bytes) -> bytes:
        """
        Случайное изменение регистра букв в HTTP заголовках
        
        Args:
            data: Исходные байты
            
        Returns:
            Модифицированные байты
        """
        if random.random() > self.modification_probability:
            return data
        
        result = bytearray(data)
        i = 0
        
        while i < len(data):
            # Ищем начало HTTP заголовка
            found_header = False
            for header in self.target_headers:
                if i + len(header) <= len(data) and data[i:i+len(header)].lower() == header:
                    found_header = True
                    header_end = i + len(header)
                    
                    # Модифицируем регистр букв в заголовке
                    for j in range(i, header_end):
                        char_byte = data[j:j+1]
                        # Проверяем, является ли байт буквой (A-Z, a-z)
                        if (65 <= char_byte[0] <= 90) or (97 <= char_byte[0] <= 122):
                            # Случайно выбираем регистр
                            if random.random() < 0.5:
                                result[j] = char_byte.upper()
                            else:
                                result[j] = char_byte.lower()
                    
                    i = header_end
                    break
            
            if not found_header:
                i += 1
        
        return bytes(result)
    
    def reset_session(self):
        """Сброс состояния для новой сессии"""
        self.logger.info(f"[{self.get_module_name()}] Session reset")
