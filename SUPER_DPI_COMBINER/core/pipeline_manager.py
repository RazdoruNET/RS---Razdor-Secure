#!/usr/bin/env python3
"""
Менеджер пайплайнов с динамической загрузкой
Автоматическая подгрузка всех техник обхода DPI
"""

import os
import sys
import importlib
import inspect
import asyncio
import threading
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import json

from .base_pipeline import BasePipeline, BypassTechnique, PipelineStatus

# Импорт логгера с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger(__name__)

class PipelineManager:
    """Менеджер для динамической загрузки и управления пайплайнами"""
    
    def __init__(self, pipelines_dir: str = "pipelines"):
        self.pipelines_dir = Path(pipelines_dir)
        self.loaded_pipelines: Dict[str, BasePipeline] = {}
        self.pipeline_classes: Dict[str, Type[BasePipeline]] = {}
        self.pipeline_configs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        # Приоритеты техник
        self.technique_priorities = {
            BypassTechnique.SPOOF_DPI: 1,
            BypassTechnique.DOMAIN_FRONTING: 2,
            BypassTechnique.PROTOCOL_OBFUSCATION: 3,
            BypassTechnique.TOR_INTEGRATION: 4,
            BypassTechnique.OMEGA_TRANSPORT: 5,
            BypassTechnique.ADAPTIVE: 6
        }
        
        logger.info(f"Инициализация PipelineManager с директорией: {pipelines_dir}")
    
    def auto_load_pipelines(self) -> bool:
        """
        Автоматическая загрузка всех пайплайнов из папки
        
        Returns:
            bool: Успешность загрузки
        """
        try:
            logger.info("Начало автозагрузки пайплайнов...")
            
            # Проверяем существование директории
            if not self.pipelines_dir.exists():
                logger.error(f"Директория пайплайнов не найдена: {self.pipelines_dir}")
                return False
            
            # Загружаем конфигурации
            self._load_pipeline_configs()
            
            # Ищем все поддиректории с пайплайнами
            loaded_count = 0
            failed_count = 0
            
            for technique_dir in self.pipelines_dir.iterdir():
                if technique_dir.is_dir() and not technique_dir.name.startswith('__'):
                    technique_name = technique_dir.name
                    
                    # Пытаемся загрузить пайплайны из этой техники
                    if self._load_technique_pipelines(technique_dir):
                        loaded_count += 1
                    else:
                        failed_count += 1
            
            logger.info(f"Загрузка завершена: {loaded_count} техник, {failed_count} ошибок")
            
            # Сортируем пайплайны по приоритету
            self._sort_pipelines_by_priority()
            
            return loaded_count > 0
            
        except Exception as e:
            logger.error(f"Ошибка автозагрузки пайплайнов: {e}")
            return False
    
    def _load_pipeline_configs(self):
        """Загрузка конфигураций пайплайнов"""
        config_file = self.pipelines_dir / "pipeline_configs.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.pipeline_configs = json.load(f)
                logger.info(f"Загружены конфигурации из {config_file}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки конфигураций: {e}")
                self.pipeline_configs = {}
        else:
            # Создаем конфигурацию по умолчанию
            self.pipeline_configs = self._create_default_configs()
            self._save_pipeline_configs()
    
    def _create_default_configs(self) -> Dict[str, Any]:
        """Создание конфигураций по умолчанию"""
        return {
            "global": {
                "timeout": 30.0,
                "max_retries": 3,
                "enable_logging": True,
                "performance_monitoring": True
            },
            "spoof_dpi": {
                "enabled": True,
                "tcp_segmentation": True,
                "fake_packets": True,
                "ttl_manipulation": True
            },
            "domain_fronting": {
                "enabled": True,
                "cdn_bypass": True,
                "host_header_spoofing": True
            },
            "protocol_obfuscation": {
                "enabled": True,
                "http_fragmentation": True,
                "tls_fingerprint": True
            },
            "tor_integration": {
                "enabled": True,
                "bridge_mode": True,
                "darknet_access": True
            },
            "omega_transport": {
                "enabled": True,
                "bridge_manager": True,
                "proxy_chains": True
            },
            "adaptive": {
                "enabled": True,
                "ml_detection": True,
                "auto_switching": True
            }
        }
    
    def _save_pipeline_configs(self):
        """Сохранение конфигураций пайплайнов"""
        config_file = self.pipelines_dir / "pipeline_configs.json"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.pipeline_configs, f, indent=2, ensure_ascii=False)
            logger.info(f"Конфигурации сохранены в {config_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигураций: {e}")
    
    def _load_technique_pipelines(self, technique_dir: Path) -> bool:
        """
        Загрузка пайплайнов для конкретной техники
        
        Args:
            technique_dir: Директория техники
            
        Returns:
            bool: Успешность загрузки
        """
        technique_name = technique_dir.name
        
        try:
            # Проверяем __init__.py
            init_file = technique_dir / "__init__.py"
            if not init_file.exists():
                logger.warning(f"Отсутствует __init__.py в {technique_dir}")
                return False
            
            # Добавляем путь в sys.path
            technique_path = str(technique_dir.parent)
            if technique_path not in sys.path:
                sys.path.insert(0, technique_path)
            
            # Импортируем модуль техники
            module_name = f"pipelines.{technique_name}"
            technique_module = importlib.import_module(module_name)
            
            # Ищем классы пайплайнов в модуле
            pipeline_classes = []
            for name, obj in inspect.getmembers(technique_module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePipeline) and 
                    obj != BasePipeline):
                    pipeline_classes.append(obj)
            
            # Создаем экземпляры пайплайнов
            loaded_any = False
            for pipeline_class in pipeline_classes:
                try:
                    # Получаем конфигурацию для этой техники
                    config = self.pipeline_configs.get(technique_name, {})
                    
                    # Создаем экземпляр
                    pipeline = pipeline_class()
                    
                    # Инициализируем с конфигурацией
                    if pipeline.initialize(config):
                        self.loaded_pipelines[pipeline.name] = pipeline
                        self.pipeline_classes[pipeline.name] = pipeline_class
                        
                        logger.info(f"Загружен пайплайн: {pipeline.name}")
                        loaded_any = True
                    else:
                        logger.warning(f"Не удалось инициализировать пайплайн: {pipeline.name}")
                        
                except Exception as e:
                    logger.error(f"Ошибка создания пайплайна {pipeline_class.__name__}: {e}")
            
            return loaded_any
            
        except Exception as e:
            logger.error(f"Ошибка загрузки техники {technique_name}: {e}")
            return False
    
    def _sort_pipelines_by_priority(self):
        """Сортировка пайплайнов по приоритету"""
        with self.lock:
            sorted_pipelines = dict(sorted(
                self.loaded_pipelines.items(),
                key=lambda x: (x[1].priority, x[1].technique.value)
            ))
            self.loaded_pipelines = sorted_pipelines
    
    def get_pipeline(self, name: str) -> Optional[BasePipeline]:
        """
        Получение пайплайна по имени
        
        Args:
            name: Имя пайплайна
            
        Returns:
            BasePipeline: Экземпляр пайплайна или None
        """
        return self.loaded_pipelines.get(name)
    
    def get_pipelines_by_technique(self, technique: BypassTechnique) -> List[BasePipeline]:
        """
        Получение пайплайнов по типу техники
        
        Args:
            technique: Тип техники
            
        Returns:
            List[BasePipeline]: Список пайплайнов
        """
        return [
            pipeline for pipeline in self.loaded_pipelines.values()
            if pipeline.technique == technique
        ]
    
    def get_healthy_pipelines(self) -> List[BasePipeline]:
        """
        Получение здоровых пайплайнов
        
        Returns:
            List[BasePipeline]: Список здоровых пайплайнов
        """
        return [
            pipeline for pipeline in self.loaded_pipelines.values()
            if pipeline.is_healthy()
        ]
    
    def get_best_pipelines(self, count: int = 3) -> List[BasePipeline]:
        """
        Получение лучших пайплайнов по производительности
        
        Args:
            count: Количество лучших пайплайнов
            
        Returns:
            List[BasePipeline]: Список лучших пайплайнов
        """
        healthy_pipelines = self.get_healthy_pipelines()
        
        # Сортируем по оценке производительности
        sorted_pipelines = sorted(
            healthy_pipelines,
            key=lambda p: p.get_performance_score(),
            reverse=True
        )
        
        return sorted_pipelines[:count]
    
    async def test_all_pipelines(self) -> Dict[str, bool]:
        """
        Тестирование всех пайплайнов
        
        Returns:
            Dict[str, bool]: Результаты тестирования
        """
        logger.info("Начало тестирования всех пайплайнов...")
        
        results = {}
        tasks = []
        
        for name, pipeline in self.loaded_pipelines.items():
            task = asyncio.create_task(pipeline.health_check())
            tasks.append((name, task))
        
        # Ждем завершения всех тестов
        for name, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=30.0)
                results[name] = result
                
                if result:
                    logger.info(f"✅ Пайплайн {name} прошел тест")
                else:
                    logger.warning(f"❌ Пайплайн {name} не прошел тест")
                    
            except asyncio.TimeoutError:
                logger.error(f"⏰ Тест {name} превысил время ожидания")
                results[name] = False
            except Exception as e:
                logger.error(f"💥 Ошибка теста {name}: {e}")
                results[name] = False
        
        return results
    
    def reload_pipeline(self, name: str) -> bool:
        """
        Перезагрузка конкретного пайплайна
        
        Args:
            name: Имя пайплайна
            
        Returns:
            bool: Успешность перезагрузки
        """
        try:
            with self.lock:
                if name not in self.loaded_pipelines:
                    logger.error(f"Пайплайн {name} не найден")
                    return False
                
                old_pipeline = self.loaded_pipelines[name]
                
                # Очищаем старый пайплайн
                old_pipeline.cleanup()
                
                # Создаем новый экземпляр
                pipeline_class = self.pipeline_classes[name]
                technique_name = old_pipeline.technique.value
                config = self.pipeline_configs.get(technique_name, {})
                
                new_pipeline = pipeline_class()
                
                if new_pipeline.initialize(config):
                    self.loaded_pipelines[name] = new_pipeline
                    logger.info(f"✅ Пайплайн {name} перезагружен")
                    return True
                else:
                    logger.error(f"❌ Не удалось инициализировать {name} после перезагрузки")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка перезагрузки {name}: {e}")
            return False
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Получение полного отчета о статусе всех пайплайнов
        
        Returns:
            Dict: Детальный отчет
        """
        with self.lock:
            report = {
                'total_pipelines': len(self.loaded_pipelines),
                'healthy_pipelines': len(self.get_healthy_pipelines()),
                'techniques': {},
                'best_performers': [],
                'failed_pipelines': []
            }
            
            # Группировка по техникам
            for pipeline in self.loaded_pipelines.values():
                technique = pipeline.technique.value
                if technique not in report['techniques']:
                    report['techniques'][technique] = {
                        'count': 0,
                        'healthy': 0,
                        'pipelines': []
                    }
                
                report['techniques'][technique]['count'] += 1
                if pipeline.is_healthy():
                    report['techniques'][technique]['healthy'] += 1
                
                report['techniques'][technique]['pipelines'].append(
                    pipeline.get_status_info()
                )
            
            # Лучшие performers
            best_pipelines = self.get_best_pipelines(5)
            report['best_performers'] = [
                {'name': p.name, 'score': p.get_performance_score()}
                for p in best_pipelines
            ]
            
            # Неудачные пайплайны
            report['failed_pipelines'] = [
                name for name, pipeline in self.loaded_pipelines.items()
                if not pipeline.is_healthy()
            ]
            
            return report
    
    def cleanup_all(self) -> bool:
        """
        Очистка всех пайплайнов
        
        Returns:
            bool: Успешность очистки
        """
        logger.info("Очистка всех пайплайнов...")
        
        success_count = 0
        total_count = len(self.loaded_pipelines)
        
        for name, pipeline in self.loaded_pipelines.items():
            try:
                if pipeline.cleanup():
                    success_count += 1
                    logger.info(f"✅ Пайплайн {name} очищен")
                else:
                    logger.warning(f"⚠️ Очистка {name} не удалась")
            except Exception as e:
                logger.error(f"❌ Ошибка очистки {name}: {e}")
        
        logger.info(f"Очистка завершена: {success_count}/{total_count}")
        return success_count == total_count
