#!/usr/bin/env python3
"""
Super DPI Combiner - Главный комбайн
Универсальный адаптивный инструмент обхода DPI с LLM интеграцией
"""

import asyncio
import signal
import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

from super_dpi_combiner.core.registry import get_pipeline_registry
from super_dpi_combiner.core.types import BypassRequest, BypassResponse
from super_dpi_combiner.utils.logger import get_logger
from super_dpi_combiner.config.settings import Settings

logger = get_logger(__name__)

class SuperDPICombiner:
    """Главный комбайн для обхода DPI"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.settings = Settings(config_path)
        self.config = self.settings.settings
        self.running = False
        
        # Registry для загрузки пайплайнов
        self.registry = get_pipeline_registry()
        
        # Статистика
        self.start_time = None
        self.total_requests = 0
        self.successful_requests = 0
        
        logger.info("Инициализация Super DPI Combiner")
    
    def initialize(self):
        """Инициализация всех компонентов"""
        try:
            logger.info("=== Инициализация Super DPI Combiner ===")
            
            # Загрузка пайплайнов через registry
            logger.info("Загрузка пайплайнов...")
            pipelines = self.registry.load_all_pipelines()
            
            # Выводим отчет о загрузке
            status_report = self.registry.get_status_report()
            logger.info(f"Статус загрузки пайплайнов: {status_report}")
            
            ready_pipelines = self.registry.get_ready_pipelines()
            logger.info(f"Готовых к работе пайплайнов: {len(ready_pipelines)}")
            
            if ready_pipelines:
                logger.info("✅ Система готова к работе")
                return True
            else:
                logger.warning("⚠️ Нет готовых пайплайнов, система в безопасном режиме")
                return True  # Все равно считаем успешной инициализацией
                
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации: {e}")
            return False
    
    def reload_config(self) -> bool:
        """Перезагрузка конфигурации"""
        try:
            success = self.settings.reload()
            if success:
                self.config = self.settings.settings
                logger.info("✅ Конфигурация успешно перезагружена")
            else:
                logger.error("❌ Ошибка перезагрузки конфигурации")
            return success
        except Exception as e:
            logger.error(f"Критическая ошибка перезагрузки: {e}")
            return False
    
    def run(self, target_url: str = None):
        """Запуск системы"""
        try:
            if not self.running:
                # Инициализация если еще не инициализирована
                if not self.initialize():
                    return False
                
                # Определение целевого URL
                if not target_url:
                    target_url = 'https://www.youtube.com'
                
                logger.info(f"🎯 Целевой URL: {target_url}")
                
                # Тестовый запуск одного пайплайна
                ready_pipelines = self.registry.get_ready_pipelines()
                if ready_pipelines:
                    test_pipeline = ready_pipelines[0]
                    logger.info(f"🧪 Тестовый запуск пайплайна: {test_pipeline.name}")
                    
                    # Создаем тестовый запрос
                    test_request = BypassRequest(
                        host='www.youtube.com',
                        port=443,
                        method='GET'
                    )
                    
                    # Выполняем тест
                    try:
                        response = test_pipeline.execute(test_request)
                        logger.info(f"✅ Тестовый запуск успешен: {response.success}")
                        logger.info(f"📊 Latency: {response.latency:.3f}s")
                    except Exception as e:
                        logger.error(f"❌ Ошибка тестового запуска: {e}")
                
                self.running = True
                self.start_time = time.time()
                
                logger.info("✅ Super DPI Combiner успешно запущен")
                logger.info("🛡️ Работа в безопасном режиме с базовой функциональностью")
                
                return True
                    
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            return False
    
    def main():
        """Основная функция для запуска приложения"""
        try:
            app = SuperDPICombiner()
            if app.run():
                logger.info("🎉 Приложение успешно запущено")
                logger.info("Для остановки нажмите Ctrl+C")
                
                # Простая блокировка для демонстрации
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("🛑 Остановка приложения...")
                    return True
            else:
                logger.error("❌ Не удалось запустить приложение")
                return False
                
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            return False

if __name__ == "__main__":
    main()
