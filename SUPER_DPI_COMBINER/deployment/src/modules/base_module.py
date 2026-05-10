#!/usr/bin/env python3
"""
Base Pipeline Module - Абстрактный класс для всех модулей конвейера
"""

from abc import ABC, abstractmethod
import asyncio
import logging

class BasePipelineModule(ABC):
    """Базовый класс для всех модулей обработки трафика"""
    
    def __init__(self, config: dict):
        """
        Инициализация модуля с конфигурацией
        
        Args:
            config: Словарь с параметрами модуля из переменных окружения
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def process(self, data: bytes, writer_srv) -> bytes:
        """
        Обработка байтового буфера
        
        Args:
            data: Входящая порция байт от клиента (или предыдущего модуля)
            writer_srv: Асинхронный сокет целевого сервера (для модулей, которые сами отправляют чанки)
        
        Returns:
            Остаток байт для передачи следующему модулю
        """
        raise NotImplementedError
    
    def get_module_name(self) -> str:
        """Возвращает имя модуля для логирования"""
        return self.__class__.__name__
    
    def is_first_packet(self, data: bytes) -> bool:
        """
        Определяет, является ли это первым пакетом в сессии
        
        Args:
            data: Байтовый буфер для анализа
            
        Returns:
            True если это первый пакет (на основе эвристики)
        """
        # Простая эвристика: первый пакет обычно содержит TLS Client Hello или HTTP запрос
        return len(data) > 0 and (
            data.startswith(b'\x16\x03') or  # TLS Handshake
            data.startswith(b'GET ') or     # HTTP GET
            data.startswith(b'POST ') or    # HTTP POST
            data.startswith(b'HEAD ') or    # HTTP HEAD
            data.startswith(b'PUT ') or     # HTTP PUT
            data.startswith(b'DELETE ') or  # HTTP DELETE
            data.startswith(b'OPTIONS ') or # HTTP OPTIONS
            data.startswith(b'PATCH ') or    # HTTP PATCH
            data.startswith(b'CONNECT ')     # HTTP CONNECT
        )
