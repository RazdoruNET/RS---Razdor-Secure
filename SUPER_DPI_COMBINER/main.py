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

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from core.pipeline_manager import PipelineManager
from core.multi_thread_engine import MultiThreadEngine, EngineMode
from core.llm_integration import LLMIntegration
from core.base_pipeline import BypassRequest, BypassResponse
from utils.logger import get_logger

logger = get_logger(__name__)

class SuperDPICombiner:
    """Главный комбайн для обхода DPI"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config = {}
        self.running = False
        
        # Компоненты
        self.pipeline_manager = None
        self.llm_integration = None
        self.engine = None
        
        # Статистика
        self.start_time = None
        self.total_requests = 0
        self.successful_requests = 0
        
        logger.info("Инициализация Super DPI Combiner")
    
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            logger.info("=== Инициализация Super DPI Combiner ===")
            
            # Загрузка конфигурации
            await self._load_config()
            
            # Инициализация LLM
            ollama_url = self.config.get('llm', {}).get('url', 'http://localhost:11434')
            ollama_model = self.config.get('llm', {}).get('model', 'llama2')
            
            self.llm_integration = LLMIntegration(
                ollama_url=ollama_url,
                model=ollama_model
            )
            
            if await self.llm_integration.initialize():
                logger.info("✅ LLM интеграция инициализирована")
            else:
                logger.warning("⚠️ LLM недоступен, работа без ИИ")
            
            # Инициализация менеджера пайплайнов
            pipelines_dir = self.config.get('pipelines', {}).get('directory', 'pipelines')
            self.pipeline_manager = PipelineManager(pipelines_dir)
            
            if self.pipeline_manager.auto_load_pipelines():
                logger.info("✅ Менеджер пайплайнов инициализирован")
            else:
                raise Exception("Не удалось загрузить пайплайны")
            
            # Инициализация движка
            max_workers = self.config.get('engine', {}).get('max_workers', 20)
            engine_mode = EngineMode(
                self.config.get('engine', {}).get('mode', 'adaptive')
            )
            
            self.engine = MultiThreadEngine(
                max_workers=max_workers,
                mode=engine_mode
            )
            
            logger.info("✅ Многопоточный движок инициализирован")
            logger.info("=== Инициализация завершена ===")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            return False
    
    async def _load_config(self):
        """Загрузка конфигурации"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Конфигурация загружена из {self.config_path}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки конфигурации: {e}")
                self.config = self._get_default_config()
        else:
            logger.info("Использование конфигурации по умолчанию")
            self.config = self._get_default_config()
            
            # Создаем файл конфигурации
            await self._save_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            "engine": {
                "max_workers": 20,
                "mode": "adaptive",
                "auto_optimization": True,
                "optimization_interval": 300
            },
            "pipelines": {
                "directory": "pipelines",
                "auto_generation": True,
                "max_generations": 5,
                "templates_per_technique": 50
            },
            "llm": {
                "enabled": True,
                "url": "http://localhost:11434",
                "model": "llama2",
                "auto_analysis": True,
                "optimization_requests": True
            },
            "targets": {
                "default_urls": [
                    "https://www.youtube.com",
                    "https://m.youtube.com",
                    "https://youtu.be"
                ],
                "test_interval": 60,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/combiner.log",
                "max_file_size": "100MB"
            }
        }
    
    async def _save_config(self):
        """Сохранение конфигурации"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Конфигурация сохранена в {self.config_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    async def start(self, target_url: str = None):
        """
        Запуск комбайна
        
        Args:
            target_url: Целевой URL для тестирования
        """
        if self.running:
            logger.warning("Комбайн уже запущен")
            return False
        
        logger.info("🚀 Запуск Super DPI Combiner...")
        
        try:
            # Инициализация
            if not await self.initialize():
                return False
            
            # Определение целевого URL
            if not target_url:
                target_url = self.config.get('targets', {}).get('default_urls', ['https://www.youtube.com'])[0]
            
            logger.info(f"🎯 Целевой URL: {target_url}")
            
            # Запуск движка с автоматической оптимизацией
            if await self.engine.start(target_url):
                self.running = True
                self.start_time = time.time()
                
                logger.info("✅ Super DPI Combiner успешно запущен")
                logger.info(f"📊 Статистика: http://localhost:8080/stats")
                logger.info(f"🔧 Управление: http://localhost:8080/control")
                
                # Запуск веб-интерфейса
                await self._start_web_interface()
                
                return True
            else:
                logger.error("❌ Не удалось запустить движок")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            return False
    
    async def _start_web_interface(self):
        """Запуск веб-интерфейса управления"""
        from aiohttp import web
        
        async def handle_stats(request):
            """Обработчик статистики"""
            if self.engine:
                stats = self.engine.get_engine_status()
                return web.json_response(stats)
            else:
                return web.json_response({"error": "Engine not running"})
        
        async def handle_control(request):
            """Обработчик управления"""
            if request.method == 'POST':
                try:
                    data = await request.json()
                    command = data.get('command')
                    
                    if command == 'optimize':
                        target_url = data.get('target_url', 'https://www.youtube.com')
                        await self._optimize_pipelines(target_url)
                        return web.json_response({"status": "optimization started"})
                    
                    elif command == 'switch_mode':
                        mode = data.get('mode', 'adaptive')
                        self.engine.set_mode(EngineMode(mode))
                        return web.json_response({"status": "mode switched"})
                    
                    elif command == 'reload_pipelines':
                        await self._reload_pipelines()
                        return web.json_response({"status": "pipelines reloaded"})
                    
                    else:
                        return web.json_response({"error": "unknown command"})
                        
                except Exception as e:
                    return web.json_response({"error": str(e)})
            
            elif request.method == 'GET':
                # Возвращаем статус
                status = {
                    'running': self.running,
                    'uptime': time.time() - self.start_time if self.start_time else 0,
                    'total_requests': self.total_requests,
                    'success_rate': (self.successful_requests / self.total_requests) if self.total_requests > 0 else 0,
                    'llm_status': self.llm_integration.get_status() if self.llm_integration else None,
                    'pipeline_count': len(self.pipeline_manager.loaded_pipelines) if self.pipeline_manager else 0
                }
                return web.json_response(status)
        
        async def handle_test_request(request):
            """Обработчик тестовых запросов"""
            if request.method == 'POST':
                try:
                    data = await request.json()
                    test_url = data.get('url', 'https://www.youtube.com')
                    
                    if self.engine:
                        test_request = BypassRequest(
                            host=test_url.split('//')[1].split('/')[0] if '//' in test_url else test_url.split('/')[0],
                            port=443,
                            method='HEAD',
                            timeout=30.0
                        )
                        
                        response = await self.engine.process_request({
                            'host': test_request.host,
                            'port': test_request.port,
                            'method': test_request.method,
                            'timeout': test_request.timeout
                        })
                        
                        return web.json_response({
                            'success': response.success if response else False,
                            'status_code': response.status_code if response else 0,
                            'response_time': response.response_time if response else 0,
                            'technique_used': response.technique_used if response else None,
                            'error': response.error if response else None
                        })
                    else:
                        return web.json_response({"error": "Engine not running"})
                        
                except Exception as e:
                    return web.json_response({"error": str(e)})
        
        # Создаем приложение
        app = web.Application()
        app.router.add_get('/stats', handle_stats)
        app.router.add_get('/control', handle_control)
        app.router.add_post('/control', handle_control)
        app.router.add_get('/test', handle_test_request)
        app.router.add_post('/test', handle_test_request)
        
        # Запускаем веб-сервер
        runner = web.AppRunner(app)
        site = web.TCPSite(runner, 'localhost', 8080)
        
        await site.start()
        logger.info("🌐 Веб-интерфейс запущен на http://localhost:8080")
    
    async def _optimize_pipelines(self, target_url: str):
        """Оптимизация пайплайнов через LLM"""
        if not self.llm_integration:
            logger.warning("LLM недоступен для оптимизации")
            return
        
        try:
            logger.info(f"🧠 Запуск оптимизации пайплайнов для {target_url}")
            
            # Получаем текущую статистику
            if self.engine:
                engine_status = self.engine.get_engine_status()
                pipeline_stats = engine_status.get('stats', {})
                
                # Запрашиваем рекомендации LLM
                recommendations = await self.llm_integration.get_pipeline_recommendations(
                    list(self.pipeline_manager.loaded_pipelines.values()),
                    target_url
                )
                
                if recommendations:
                    logger.info(f"📋 Получено {len(recommendations)} рекомендаций от LLM")
                    
                    for rec in recommendations:
                        technique = rec.get('technique')
                        priority = rec.get('priority', 5)
                        parameters = rec.get('parameters', {})
                        
                        logger.info(f"  🎯 {technique} (приоритет: {priority})")
                        
                        # Здесь можно добавить логику применения рекомендаций
                        
                else:
                    logger.warning("⚠️ LLM не предоставил рекомендации")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации: {e}")
    
    async def _reload_pipelines(self):
        """Перезагрузка пайплайнов"""
        try:
            logger.info("🔄 Перезагрузка пайплайнов...")
            
            if self.pipeline_manager:
                # Очищаем старые пайплайны
                await self.pipeline_manager.cleanup_all()
                
                # Загружаем новые
                if self.pipeline_manager.auto_load_pipelines():
                    logger.info("✅ Пайплайны перезагружены")
                    
                    # Перезапускаем движок с новыми пайплайнами
                    if self.engine:
                        await self.engine.stop()
                        await asyncio.sleep(2)
                        
                        target_url = self.config.get('targets', {}).get('default_urls', ['https://www.youtube.com'])[0]
                        await self.engine.start(target_url)
                else:
                    logger.error("❌ Не удалось перезагрузить пайплайны")
            
        except Exception as e:
            logger.error(f"Ошибка перезагрузки: {e}")
    
    async def stop(self):
        """Остановка комбайна"""
        if not self.running:
            return
        
        logger.info("🛑 Остановка Super DPI Combiner...")
        
        self.running = False
        
        # Остановка движка
        if self.engine:
            await self.engine.stop()
        
        # Очистка LLM
        if self.llm_integration:
            await self.llm_integration.cleanup()
        
        # Очистка менеджера пайплайнов
        if self.pipeline_manager:
            self.pipeline_manager.cleanup_all()
        
        # Вывод финальной статистики
        if self.start_time:
            uptime = time.time() - self.start_time
            logger.info(f"📊 Финальная статистика:")
            logger.info(f"  Время работы: {uptime:.1f}s")
            logger.info(f"  Всего запросов: {self.total_requests}")
            logger.info(f"  Успешных: {self.successful_requests}")
            logger.info(f"  Успешность: {(self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0:.1f}%")
        
        logger.info("✅ Super DPI Combiner остановлен")
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса комбайна"""
        status = {
            'running': self.running,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'success_rate': (self.successful_requests / self.total_requests) if self.total_requests > 0 else 0,
            'components': {
                'pipeline_manager': self.pipeline_manager is not None,
                'llm_integration': self.llm_integration is not None,
                'engine': self.engine is not None
            }
        }
        
        if self.engine:
            status['engine'] = self.engine.get_engine_status()
        
        if self.llm_integration:
            status['llm'] = self.llm_integration.get_status()
        
        if self.pipeline_manager:
            status['pipelines'] = self.pipeline_manager.get_status_report()
        
        return status

# Обработчики сигналов
combiner_instance = None

def signal_handler(signum, frame):
    """Обработчик сигналов для грациозной остановки"""
    logger.info(f"Получен сигнал {signum}, остановка...")
    
    if combinor_instance:
        # Создаем задачу для остановки
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(combiner_instance.stop())
        else:
            loop.run_until_complete(combiner_instance.stop())

async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Super DPI Combiner - Универсальный обход DPI')
    parser.add_argument('--config', default='config/settings.json', help='Путь к конфигурации')
    parser.add_argument('--target', help='Целевой URL для тестирования')
    parser.add_argument('--mode', choices=['auto_select', 'performance', 'reliability', 'adaptive'], 
                       default='adaptive', help='Режим работы движка')
    parser.add_argument('--workers', type=int, default=20, help='Количество рабочих потоков')
    parser.add_argument('--no-llm', action='store_true', help='Отключить LLM интеграцию')
    parser.add_argument('--status', action='store_true', help='Показать статус и выйти')
    
    args = parser.parse_args()
    
    global combinor_instance
    combinor_instance = SuperDPICombiner(args.config)
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.status:
            # Показываем статус
            status = combinor_instance.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return
        
        # Отключаем LLM если указано
        if args.no_llm:
            combinor_instance.config['llm']['enabled'] = False
        
        # Устанавливаем режим
        if args.mode:
            combinor_instance.config['engine']['mode'] = args.mode
        
        # Устанавливаем количество потоков
        if args.workers:
            combinor_instance.config['engine']['max_workers'] = args.workers
        
        # Запускаем комбайн
        success = await combinor_instance.start(args.target)
        
        if success:
            # Бесконечный цикл работы
            while combinor_instance.running:
                await asyncio.sleep(1)
        else:
            logger.error("❌ Не удалось запустить комбайн")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Остановка по Ctrl+C")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        if combinor_instance:
            await combinor_instance.stop()

if __name__ == "__main__":
    # Проверяем зависимости
    try:
        import aiohttp
    except ImportError:
        print("❌ Требуется aiohttp: pip install aiohttp")
        sys.exit(1)
    
    # Запускаем
    asyncio.run(main())
