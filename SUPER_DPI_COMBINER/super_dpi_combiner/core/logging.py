#!/usr/bin/env python3
"""
Structured Logging - Простое структурированное логирование
Без AI, без метрик, только факты
"""

import sys
import time
from datetime import datetime
from typing import Optional

class Logger:
    """Простой логгер для runtime"""
    
    def __init__(self, name: str):
        self.name = name
        
    def _log(self, level: str, message: str, pipeline: Optional[str] = None):
        """Универсальный метод логирования"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if pipeline:
            print(f"[{timestamp}] [{level}] [{self.name}:{pipeline}] {message}")
        else:
            print(f"[{timestamp}] [{level}] [{self.name}] {message}")
    
    def info(self, message: str, pipeline: Optional[str] = None):
        """Информационное сообщение"""
        self._log("INFO", message, pipeline)
        
    def error(self, message: str, pipeline: Optional[str] = None):
        """Сообщение об ошибке"""
        self._log("ERROR", message, pipeline)
        
    def success(self, message: str, pipeline: Optional[str] = None, latency: Optional[float] = None):
        """Сообщение об успехе"""
        if latency is not None:
            message = f"{message} ({latency:.3f}s)"
        self._log("SUCCESS", message, pipeline)

# Global logger instance
_global_logger = None

def get_logger(name: str) -> Logger:
    """Получить логгер для модуля"""
    return Logger(name)
