"""
Утилита логирования для Super DPI Combiner
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def get_logger(name: str, log_file: Optional[str] = None, level: str = "INFO"):
    """
    Создание и конфигурация логгера
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        level: Уровень логирования
        
    Returns:
        logging.Logger: Сконфигурированный логгер
    """
    logger = logging.getLogger(name)
    
    # Устанавливаем уровень
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Формат
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
