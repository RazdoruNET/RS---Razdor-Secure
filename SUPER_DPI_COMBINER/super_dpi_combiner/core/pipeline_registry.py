#!/usr/bin/env python3
"""
Pipeline Registry - Async Safe Discovery System
Реестр пайплайнов с безопасной загрузкой и отслеживанием статусов
"""

import os
import sys
import importlib
import inspect
import asyncio
import time
from typing import Dict, List, Optional, Any, Type
from enum import Enum
from pathlib import Path

from .base_pipeline import BasePipeline, BypassTechnique, PipelineExecutionStatus, SafePipeline
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger


class PipelineRegistryStatus(Enum):
    """Статусы пайплайнов в реестре"""
    READY = "READY"          # Готов к использованию
    BROKEN = "BROKEN"        # Сломан, не может быть загружен
    SIMULATED = "SIMULATED"  # Работает в режиме симуляции


class PipelineInfo:
    """Информация о пайплайне в реестре"""
    
    def __init__(self, 
                 name: str,
                 module_path: str,
                 class_name: str,
                 status: PipelineRegistryStatus = PipelineRegistryStatus.BROKEN,
                 pipeline_class: Optional[Type[BasePipeline]] = None,
                 error_message: str = None):
        self.name = name
        self.module_path = module_path
        self.class_name = class_name
        self.status = status
        self.pipeline_class = pipeline_class
        self.error_message = error_message
        self.load_time = None
        self.instance_count = 0
        self.last_error = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации"""
        return {
            'name': self.name,
            'module_path': self.module_path,
            'class_name': self.class_name,
            'status': self.status.value,
            'load_time': self.load_time,
            'instance_count': self.instance_count,
            'last_error': self.last_error,
            'has_pipeline_class': self.pipeline_class is not None
        }


class PipelineRegistry:
    """
    Реестр пайплайнов с безопасной асинхронной загрузкой
    """
    
    def __init__(self, pipelines_dir: str = None):
        self.logger = get_logger("PipelineRegistry")
        self.pipelines_dir = pipelines_dir or os.path.join(os.path.dirname(__file__), '..', 'pipelines')
        self._registry: Dict[str, PipelineInfo] = {}
        self._discovery_completed = False
        self._discovery_lock = asyncio.Lock()
        
    async def discover_pipelines(self) -> Dict[str, PipelineInfo]:
        """
        Автоматическое обнаружение и загрузка пайплайнов
        
        Returns:
            Dict[str, PipelineInfo]: Словарь с информацией о пайплайнах
        """
        async with self._discovery_lock:
            if self._discovery_completed:
                return self._registry
                
            self.logger.info(f"🔍 Starting pipeline discovery in: {self.pipelines_dir}")
            
            # Очищаем реестр перед новым обнаружением
            self._registry.clear()
            
            # Получаем все Python файлы в директории pipelines
            pipeline_files = self._find_pipeline_files()
            
            self.logger.info(f"📁 Found {len(pipeline_files)} pipeline files to analyze")
            
            # Загружаем каждый пайплайн безопасно
            for pipeline_file in pipeline_files:
                await self._safe_load_pipeline(pipeline_file)
            
            self._discovery_completed = True
            
            # Выводим статистику
            await self._log_discovery_stats()
            
            return self._registry
    
    def _find_pipeline_files(self) -> List[str]:
        """
        Поиск всех файлов пайплайнов в директории pipelines
        
        Returns:
            List[str]: Список путей к файлам пайплайнов
        """
        pipeline_files = []
        pipelines_path = Path(self.pipelines_dir)
        
        if not pipelines_path.exists():
            self.logger.warning(f"Pipelines directory not found: {self.pipelines_dir}")
            return pipeline_files
        
        # Рекурсивный поиск всех .py файлов, кроме __init__.py
        for py_file in pipelines_path.rglob("*.py"):
            if py_file.name != "__init__.py":
                pipeline_files.append(str(py_file))
        
        return pipeline_files
    
    async def _safe_load_pipeline(self, pipeline_file: str):
        """
        Безопасная загрузка пайплайна с обработкой ошибок
        
        Args:
            pipeline_file: Путь к файлу пайплайна
        """
        start_time = time.time()
        
        try:
            # Получаем информацию о модуле
            module_info = self._extract_module_info(pipeline_file)
            
            if not module_info:
                return
            
            module_name, class_name, pipeline_name = module_info
            
            self.logger.debug(f"🔄 Loading pipeline: {pipeline_name} from {module_name}")
            
            # Пробуем импортировать модуль
            module = await self._safe_import_module(module_name)
            
            if not module:
                return
            
            # Ищем класс пайплайна
            pipeline_class = await self._safe_get_pipeline_class(module, class_name)
            
            if not pipeline_class:
                return
            
            # Определяем статус пайплайна
            status = await self._determine_pipeline_status(pipeline_class)
            
            # Создаем запись в реестре
            pipeline_info = PipelineInfo(
                name=pipeline_name,
                module_path=pipeline_file,
                class_name=class_name,
                status=status,
                pipeline_class=pipeline_class
            )
            
            pipeline_info.load_time = time.time() - start_time
            
            self._registry[pipeline_name] = pipeline_info
            
            self.logger.info(f"✅ Pipeline loaded: {pipeline_name} ({status.value})")
            
        except Exception as e:
            error_msg = f"Pipeline loading failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            # Создаем запись о сломанном пайплайне
            pipeline_name = Path(pipeline_file).stem
            pipeline_info = PipelineInfo(
                name=pipeline_name,
                module_path=pipeline_file,
                class_name="Unknown",
                status=PipelineRegistryStatus.BROKEN,
                error_message=error_msg
            )
            pipeline_info.last_error = error_msg
            pipeline_info.load_time = time.time() - start_time
            
            self._registry[pipeline_name] = pipeline_info
    
    def _extract_module_info(self, pipeline_file: str) -> Optional[tuple]:
        """
        Извлечение информации о модуле из пути к файлу
        
        Args:
            pipeline_file: Путь к файлу пайплайна
            
        Returns:
            Optional[tuple]: (module_name, class_name, pipeline_name)
        """
        try:
            # Получаем относительный путь от pipelines директории
            pipelines_path = Path(self.pipelines_dir)
            file_path = Path(pipeline_file)
            relative_path = file_path.relative_to(pipelines_path)
            
            # Преобразуем путь в имя модуля
            module_parts = list(relative_path.parts[:-1])  # Все кроме имени файла
            module_name = ".".join(module_parts + [file_path.stem])
            
            # Определяем имя класса по имени файла
            class_name = self._to_class_name(file_path.stem)
            pipeline_name = file_path.stem
            
            return module_name, class_name, pipeline_name
            
        except Exception as e:
            self.logger.error(f"Failed to extract module info from {pipeline_file}: {e}")
            return None
    
    def _to_class_name(self, snake_case: str) -> str:
        """Преобразование snake_case в CamelCase"""
        return ''.join(word.capitalize() for word in snake_case.replace('_', ' ').split())
    
    async def _safe_import_module(self, module_name: str) -> Optional[Any]:
        """
        Безопасный импорт модуля
        
        Args:
            module_name: Имя модуля для импорта
            
        Returns:
            Optional[Any]: Импортированный модуль или None
        """
        try:
            # Добавляем путь к pipelines в sys.path если нужно
            pipelines_dir = os.path.dirname(self.pipelines_dir)
            if pipelines_dir not in sys.path:
                sys.path.insert(0, pipelines_dir)
            
            # Импортируем модуль
            module = importlib.import_module(f"pipelines.{module_name}")
            
            self.logger.debug(f"✅ Module imported: pipelines.{module_name}")
            return module
            
        except ImportError as e:
            self.logger.error(f"❌ Import failed for pipelines.{module_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error importing pipelines.{module_name}: {e}")
            return None
    
    async def _safe_get_pipeline_class(self, module: Any, class_name: str) -> Optional[Type[BasePipeline]]:
        """
        Безопасное получение класса пайплайна из модуля
        
        Args:
            module: Импортированный модуль
            class_name: Имя класса для поиска
            
        Returns:
            Optional[Type[BasePipeline]]: Класс пайплайна или None
        """
        try:
            # Ищем класс в модуле
            if hasattr(module, class_name):
                pipeline_class = getattr(module, class_name)
                
                # Проверяем что это класс и наследуется от BasePipeline
                if (inspect.isclass(pipeline_class) and 
                    issubclass(pipeline_class, BasePipeline) and 
                    pipeline_class != BasePipeline and
                    pipeline_class != SafePipeline):
                    
                    self.logger.debug(f"✅ Pipeline class found: {class_name}")
                    return pipeline_class
                else:
                    self.logger.warning(f"⚠️ Class {class_name} found but not a valid BasePipeline subclass")
                    return None
            else:
                # Ищем любой класс наследующий BasePipeline
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (obj != BasePipeline and 
                        obj != SafePipeline and 
                        issubclass(obj, BasePipeline)):
                        self.logger.debug(f"✅ Found alternative pipeline class: {name}")
                        return obj
                
                self.logger.warning(f"⚠️ No BasePipeline subclass found in module")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting pipeline class {class_name}: {e}")
            return None
    
    async def _determine_pipeline_status(self, pipeline_class: Type[BasePipeline]) -> PipelineRegistryStatus:
        """
        Определение статуса пайплайна
        
        Args:
            pipeline_class: Класс пайплайна
            
        Returns:
            PipelineRegistryStatus: Статус пайплайна
        """
        try:
            # Проверяем execution_status по умолчанию
            # Создаем временный экземпляр для проверки
            temp_instance = pipeline_class.__new__(pipeline_class)
            
            # Проверяем атрибут execution_status если он есть
            if hasattr(temp_instance, 'execution_status'):
                execution_status = getattr(temp_instance, 'execution_status')
                if execution_status == PipelineExecutionStatus.REAL:
                    return PipelineRegistryStatus.READY
                elif execution_status == PipelineExecutionStatus.SIMULATION:
                    return PipelineRegistryStatus.SIMULATED
            
            # Проверяем имя класса на наличие признаков симуляции
            class_name = pipeline_class.__name__.lower()
            if 'safe' in class_name or 'mock' in class_name or 'test' in class_name:
                return PipelineRegistryStatus.SIMULATED
            
            # Проверяем наследование от SafePipeline
            if issubclass(pipeline_class, SafePipeline):
                return PipelineRegistryStatus.SIMULATED
            
            # По умолчанию считаем готовым
            return PipelineRegistryStatus.READY
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not determine pipeline status: {e}")
            return PipelineRegistryStatus.BROKEN
    
    async def _log_discovery_stats(self):
        """Логирование статистики обнаружения"""
        total = len(self._registry)
        ready = sum(1 for p in self._registry.values() if p.status == PipelineRegistryStatus.READY)
        broken = sum(1 for p in self._registry.values() if p.status == PipelineRegistryStatus.BROKEN)
        simulated = sum(1 for p in self._registry.values() if p.status == PipelineRegistryStatus.SIMULATED)
        
        self.logger.info(f"📊 Pipeline Discovery Complete:")
        self.logger.info(f"   Total: {total}")
        self.logger.info(f"   ✅ Ready: {ready}")
        self.logger.info(f"   ❌ Broken: {broken}")
        self.logger.info(f"   🔧 Simulated: {simulated}")
        
        # Выводим список готовых пайплайнов
        ready_pipelines = [name for name, info in self._registry.items() 
                          if info.status == PipelineRegistryStatus.READY]
        if ready_pipelines:
            self.logger.info(f"🚀 Loadable pipelines: {', '.join(ready_pipelines)}")
    
    def get_pipeline_info(self, name: str) -> Optional[PipelineInfo]:
        """
        Получение информации о пайплайне по имени
        
        Args:
            name: Имя пайплайна
            
        Returns:
            Optional[PipelineInfo]: Информация о пайплайне или None
        """
        return self._registry.get(name)
    
    def get_all_pipelines(self) -> Dict[str, PipelineInfo]:
        """Получение всех пайплайнов из реестра"""
        return self._registry.copy()
    
    def get_ready_pipelines(self) -> Dict[str, PipelineInfo]:
        """Получение только готовых к использованию пайплайнов"""
        return {name: info for name, info in self._registry.items() 
                if info.status == PipelineRegistryStatus.READY}
    
    def get_broken_pipelines(self) -> Dict[str, PipelineInfo]:
        """Получение сломанных пайплайнов"""
        return {name: info for name, info in self._registry.items() 
                if info.status == PipelineRegistryStatus.BROKEN}
    
    def get_simulated_pipelines(self) -> Dict[str, PipelineInfo]:
        """Получение симулированных пайплайнов"""
        return {name: info for name, info in self._registry.items() 
                if info.status == PipelineRegistryStatus.SIMULATED}
    
    def create_pipeline_instance(self, name: str, **kwargs) -> Optional[BasePipeline]:
        """
        Создание экземпляра пайплайна
        
        Args:
            name: Имя пайплайна
            **kwargs: Аргументы для конструктора
            
        Returns:
            Optional[BasePipeline]: Экземпляр пайплайна или None
        """
        pipeline_info = self.get_pipeline_info(name)
        
        if not pipeline_info:
            self.logger.error(f"Pipeline {name} not found in registry")
            return None
        
        if pipeline_info.status == PipelineRegistryStatus.BROKEN:
            self.logger.error(f"Cannot create instance of broken pipeline {name}")
            return None
        
        if not pipeline_info.pipeline_class:
            self.logger.error(f"No pipeline class available for {name}")
            return None
        
        try:
            instance = pipeline_info.pipeline_class(**kwargs)
            pipeline_info.instance_count += 1
            self.logger.info(f"✅ Created instance of {name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create instance of {name}: {e}")
            return None
    
    async def test_pipeline(self, name: str) -> bool:
        """
        Тестирование пайплайна
        
        Args:
            name: Имя пайплайна
            
        Returns:
            bool: Результат теста
        """
        try:
            instance = self.create_pipeline_instance(name)
            if not instance:
                return False
            
            # Пробуем инициализировать
            init_result = instance.initialize({})
            
            # Пробуем выполнить health check если доступен
            if hasattr(instance, 'health_check'):
                health_result = await instance.health_check()
                return init_result and health_result
            
            return init_result
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline test failed for {name}: {e}")
            return False
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """
        Получение сводной информации о реестре
        
        Returns:
            Dict[str, Any]: Сводная информация
        """
        total = len(self._registry)
        ready = len(self.get_ready_pipelines())
        broken = len(self.get_broken_pipelines())
        simulated = len(self.get_simulated_pipelines())
        
        return {
            'total_pipelines': total,
            'ready_pipelines': ready,
            'broken_pipelines': broken,
            'simulated_pipelines': simulated,
            'discovery_completed': self._discovery_completed,
            'pipelines_dir': self.pipelines_dir,
            'ready_pipeline_names': list(self.get_ready_pipelines().keys()),
            'broken_pipeline_names': list(self.get_broken_pipelines().keys()),
            'simulated_pipeline_names': list(self.get_simulated_pipelines().keys())
        }


# Глобальный экземпляр реестра
PIPELINE_REGISTRY = PipelineRegistry()


async def discover_and_load_pipelines() -> Dict[str, PipelineInfo]:
    """
    Удобная функция для обнаружения и загрузки пайплайнов
    
    Returns:
        Dict[str, PipelineInfo]: Реестр загруженных пайплайнов
    """
    return await PIPELINE_REGISTRY.discover_pipelines()


def get_pipeline_registry() -> PipelineRegistry:
    """Получение глобального экземпляра реестра"""
    return PIPELINE_REGISTRY
