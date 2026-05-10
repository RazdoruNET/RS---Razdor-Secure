#!/usr/bin/env python3
"""
Pipeline Registry - Normalized pipeline discovery and loading system
Provides safe import loading and pipeline status tracking
"""

import os
import sys
import importlib
import inspect
import threading
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from enum import Enum

from .types import BypassTechnique, PipelineStatus
from .base_pipeline import BasePipeline
from .safe_pipeline import SafePipeline
from super_dpi_combiner.utils.logger import get_logger

logger = get_logger(__name__)

class PipelineLoadStatus(Enum):
    """Статус загрузки пайплайна"""
    READY = "READY"          # Успешно загружен и готов к работе
    BROKEN = "BROKEN"        # Ошибка при загрузке или импорте
    SKIPPED = "SKIPPED"      # Пропущен (например, отсутствует BasePipeline)
    UNKNOWN = "UNKNOWN"      # Статус не определен

class PipelineInfo:
    """Информация о загруженном пайплайне"""
    
    def __init__(self, name: str, module_path: str, pipeline_class: Type[BasePipeline] = None):
        self.name = name
        self.module_path = module_path
        self.pipeline_class = pipeline_class
        self.status = PipelineLoadStatus.UNKNOWN
        self.error_message = None
        self.load_time = None
        self.instance = None
        
    def mark_ready(self, instance: BasePipeline = None):
        """Отметить пайплайн как готовый к работе"""
        self.status = PipelineLoadStatus.READY
        self.instance = instance
        
    def mark_broken(self, error_message: str):
        """Отметить пайплайн как сломанный"""
        self.status = PipelineLoadStatus.BROKEN
        self.error_message = error_message
        
    def mark_skipped(self, reason: str):
        """Отметить пайплайн как пропущенный"""
        self.status = PipelineLoadStatus.SKIPPED
        self.error_message = reason

class PipelineRegistry:
    """Реестр пайплайнов с безопасной загрузкой"""
    
    def __init__(self, pipelines_dir: str = None):
        if pipelines_dir is None:
            # Default to the pipelines directory within the package
            pipelines_dir = Path(__file__).parent.parent / "pipelines"
        
        self.pipelines_dir = Path(pipelines_dir)
        self.pipelines: Dict[str, PipelineInfo] = {}
        self.lock = threading.Lock()
        
        logger.info(f"Инициализация PipelineRegistry с директорией: {self.pipelines_dir}")
    
    def discover_pipelines(self) -> List[str]:
        """
        Обнаружение всех пайплайнов в директории pipelines
        
        Returns:
            List[str]: Список найденных путей к модулям пайплайнов
        """
        discovered = []
        
        if not self.pipelines_dir.exists():
            logger.warning(f"Директория пайплайнов не существует: {self.pipelines_dir}")
            return discovered
        
        # Рекурсивный обход всех поддиректорий
        for technique_dir in self.pipelines_dir.iterdir():
            if technique_dir.is_dir() and not technique_dir.name.startswith('_'):
                # Ищем .py файлы в поддиректориях
                for py_file in technique_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        # Формируем путь модуля
                        relative_path = py_file.relative_to(self.pipelines_dir.parent)
                        module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")
                        discovered.append(module_path)
        
        logger.info(f"Обнаружено пайплайнов: {len(discovered)}")
        return discovered
    
    def safe_import_pipeline(self, module_path: str) -> Optional[Type[BasePipeline]]:
        """
        Безопасный импорт пайплайна с обработкой ошибок
        
        Args:
            module_path: Путь к модулю пайплайна (например, "super_dpi_combiner.pipelines.spoof_dpi.http_fragmentation")
            
        Returns:
            Optional[Type[BasePipeline]]: Класс пайплайна или None в случае ошибки
        """
        try:
            # Импортируем модуль
            module = importlib.import_module(module_path)
            
            # Ищем классы, наследующие BasePipeline
            pipeline_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Проверяем, что класс является подклассом BasePipeline и не является самим BasePipeline
                if (issubclass(obj, BasePipeline) and 
                    obj.__module__ == module.__name__ and
                    obj != BasePipeline and 
                    obj != SafePipeline):
                    pipeline_classes.append(obj)
            
            if not pipeline_classes:
                logger.warning(f"В модуле {module_path} не найдено классов, наследующих BasePipeline")
                return None
            
            # Берем первый найденный класс пайплайна
            pipeline_class = pipeline_classes[0]
            logger.info(f"Найден пайплайн {pipeline_class.__name__} в модуле {module_path}")
            return pipeline_class
            
        except ImportError as e:
            logger.error(f"Ошибка импорта модуля {module_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при загрузке пайплайна из {module_path}: {e}")
            return None
    
    def load_pipeline(self, module_path: str) -> PipelineInfo:
        """
        Загрузка одного пайплайна
        
        Args:
            module_path: Путь к модулю пайплайна
            
        Returns:
            PipelineInfo: Информация о загруженном пайплайне
        """
        import time
        start_time = time.time()
        
        # Извлекаем имя пайплайна из пути модуля
        pipeline_name = module_path.split(".")[-1]
        info = PipelineInfo(pipeline_name, module_path)
        
        try:
            # Безопасный импорт
            pipeline_class = self.safe_import_pipeline(module_path)
            
            if pipeline_class is None:
                info.mark_skipped("Не найден класс, наследующий BasePipeline")
                return info
            
            # Пытаемся создать экземпляр для проверки
            try:
                # Определяем технику по пути
                technique_parts = module_path.split(".")
                if len(technique_parts) >= 3:
                    technique_name = technique_parts[2].upper()
                    try:
                        technique = BypassTechnique[technique_name]
                    except KeyError:
                        technique = BypassTechnique.SPOOF_DPI  # Default
                else:
                    technique = BypassTechnique.SPOOF_DPI
                
                # Создаем экземпляр с SafePipeline в качестве запасного варианта
                instance = pipeline_class(pipeline_name, technique)
                
                # Проверяем базовую функциональность
                if hasattr(instance, 'initialize') and callable(instance.initialize):
                    init_result = instance.initialize()
                    if not init_result:
                        logger.warning(f"Пайплайн {pipeline_name} не прошел инициализацию")
                
                info.mark_ready(instance)
                logger.info(f"Пайплайн {pipeline_name} успешно загружен")
                
            except Exception as e:
                # Если не удалось создать экземпляр, используем SafePipeline
                logger.warning(f"Не удалось создать экземпляр {pipeline_name}: {e}, используем SafePipeline")
                try:
                    technique = BypassTechnique.SPOOF_DPI
                    safe_instance = SafePipeline(pipeline_name, technique)
                    info.mark_ready(safe_instance)
                    logger.info(f"Для {pipeline_name} использован SafePipeline")
                except Exception as safe_error:
                    info.mark_broken(f"Ошибка при создании SafePipeline: {safe_error}")
            
        except Exception as e:
            info.mark_broken(str(e))
        
        info.load_time = time.time() - start_time
        return info
    
    def load_all_pipelines(self) -> Dict[str, PipelineInfo]:
        """
        Загрузка всех обнаруженных пайплайнов
        
        Returns:
            Dict[str, PipelineInfo]: Словарь с информацией о всех пайплайнах
        """
        discovered = self.discover_pipelines()
        
        with self.lock:
            self.pipelines.clear()
            
            for module_path in discovered:
                info = self.load_pipeline(module_path)
                self.pipelines[info.name] = info
                
                # Логируем статус
                if info.status == PipelineLoadStatus.READY:
                    logger.info(f"✓ {info.name}: READY")
                elif info.status == PipelineLoadStatus.BROKEN:
                    logger.error(f"✗ {info.name}: BROKEN - {info.error_message}")
                elif info.status == PipelineLoadStatus.SKIPPED:
                    logger.warning(f"⊘ {info.name}: SKIPPED - {info.error_message}")
        
        return self.pipelines
    
    def get_ready_pipelines(self) -> List[BasePipeline]:
        """
        Получить список готовых к работе пайплайнов
        
        Returns:
            List[BasePipeline]: Список экземпляров готовых пайплайнов
        """
        ready = []
        with self.lock:
            for info in self.pipelines.values():
                if info.status == PipelineLoadStatus.READY and info.instance:
                    ready.append(info.instance)
        return ready
    
    def get_pipeline_info(self, name: str) -> Optional[PipelineInfo]:
        """
        Получить информацию о пайплайне по имени
        
        Args:
            name: Имя пайплайна
            
        Returns:
            Optional[PipelineInfo]: Информация о пайплайне или None
        """
        with self.lock:
            return self.pipelines.get(name)
    
    def get_status_report(self) -> Dict[str, int]:
        """
        Получить отчет о статусах загрузки
        
        Returns:
            Dict[str, int]: Счетчик по статусам
        """
        report = {status.value: 0 for status in PipelineLoadStatus}
        
        with self.lock:
            for info in self.pipelines.values():
                report[info.status.value] += 1
                
        return report

# Глобальный экземпляр реестра
_registry_instance = None
_registry_lock = threading.Lock()

def get_pipeline_registry() -> PipelineRegistry:
    """
    Получить глобальный экземпляр реестра пайплайнов (singleton)
    
    Returns:
        PipelineRegistry: Экземпляр реестра
    """
    global _registry_instance
    
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = PipelineRegistry()
    
    return _registry_instance
