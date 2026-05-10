#!/usr/bin/env python3
"""
Pipeline Manager - Управление динамическими конвейерами модулей
"""

import os
import sys
import importlib
import logging
from typing import List, Dict, Any

# Add modules path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
from base_module import BasePipelineModule

class PipelineManager:
    """Менеджер конвейеров модулей обработки трафика"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pipeline_chain: List[BasePipelineModule] = []
        self.module_configs: Dict[str, Dict[str, Any]] = {}
        self.session_active = False
        self.bytes_processed = 0
        self.selective_threshold = int(os.environ.get('SELECTIVE_THRESHOLD', '3000'))
        
        # Регистрация доступных модулей
        self.available_modules = {
            'jitter_fragmentation': 'modules.jitter_fragmentation.JitterFragmentationModule',
            'fake_packet': 'modules.fake_packet.FakePacketModule', 
            'sni_modifier': 'modules.sni_case_modifier.SniCaseModifierModule',
        }
        
        self.logger.info("PipelineManager initialized")
    
    def load_pipeline_config(self) -> bool:
        """
        Загрузка конфигурации конвейера из переменных окружения
        
        Returns:
            True если конфигурация загружена успешно
        """
        # Читаем порядок модулей
        pipeline_order = os.environ.get('PIPELINE_ORDER', 'jitter_fragmentation')
        module_names = [name.strip() for name in pipeline_order.split(',') if name.strip()]
        
        if not module_names:
            self.logger.error("No modules specified in PIPELINE_ORDER")
            return False
        
        self.logger.info(f"Loading pipeline: {' -> '.join(module_names)}")
        
        # Загружаем конфигурацию для каждого модуля
        self._load_module_configs()
        
        # Динамически импортируем и создаем модули
        try:
            self.pipeline_chain = []
            for module_name in module_names:
                if module_name not in self.available_modules:
                    self.logger.error(f"Unknown module: {module_name}")
                    return False
                
                # Динамический импорт модуля
                module_path = self.available_modules[module_name]
                module_class = self._dynamic_import(module_path)
                
                if module_class is None:
                    self.logger.error(f"Failed to import module: {module_name}")
                    return False
                
                # Создаем экземпляр модуля с конфигурацией
                config = self.module_configs.get(module_name, {})
                module_instance = module_class(config)
                
                self.pipeline_chain.append(module_instance)
                self.logger.info(f"Loaded module: {module_instance.get_module_name()}")
            
            self.logger.info(f"Pipeline initialized: {' -> '.join([m.get_module_name() for m in self.pipeline_chain])}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load pipeline: {e}")
            return False
    
    def _load_module_configs(self):
        """Загрузка конфигурации для всех модулей из переменных окружения"""
        # Собираем все переменные окружения
        env_vars = dict(os.environ)
        
        # Конфигурация для jitter_fragmentation
        jitter_config = {
            'MIN_CHUNK_SIZE': env_vars.get('MIN_CHUNK_SIZE', '40'),
            'MAX_CHUNK_SIZE': env_vars.get('MAX_CHUNK_SIZE', '150'),
            'MIN_CHUNK_DELAY': env_vars.get('MIN_CHUNK_DELAY', '0.001'),
            'MAX_CHUNK_DELAY': env_vars.get('MAX_CHUNK_DELAY', '0.003'),
            'SELECTIVE_THRESHOLD': env_vars.get('SELECTIVE_THRESHOLD', '3000'),
        }
        
        # Конфигурация для fake_packet
        fake_packet_config = {
            'FAKE_PACKET_BYTES': env_vars.get('FAKE_PACKET_BYTES', '0x160301000500000000'),
        }
        
        # Конфигурация для sni_modifier
        sni_modifier_config = {
            'CASE_MODIFY_PROBABILITY': env_vars.get('CASE_MODIFY_PROBABILITY', '0.7'),
        }
        
        self.module_configs = {
            'jitter_fragmentation': jitter_config,
            'fake_packet': fake_packet_config,
            'sni_modifier': sni_modifier_config,
        }
        
        self.logger.info(f"Module configs loaded: {list(self.module_configs.keys())}")
    
    def _dynamic_import(self, module_path: str):
        """
        Динамический импорт класса модуля
        
        Args:
            module_path: Путь к модулю в формате package.module.Class
            
        Returns:
            Класс модуля или None в случае ошибки
        """
        try:
            # Разделяем путь на пакет, модуль и класс
            parts = module_path.split('.')
            if len(parts) < 3:
                return None
            
            package_name = '.'.join(parts[:-2])
            module_name = parts[-2]
            class_name = parts[-1]
            
            # Импортируем модуль
            module = importlib.import_module(f".{module_name}", package=package_name)
            
            # Получаем класс
            module_class = getattr(module, class_name)
            
            return module_class
            
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to import {module_path}: {e}")
            return None
    
    async def process_data(self, data: bytes, writer_srv) -> bool:
        """
        Обработка данных через конвейер модулей
        
        Args:
            data: Входящие байты от клиента
            writer_srv: Сокет целевого сервера
            
        Returns:
            True если данные обработаны, False если нужно прервать
        """
        if not data:
            return False
        
        # Проверяем порог селективной обработки
        if self.session_active and self.bytes_processed >= self.selective_threshold:
            self.logger.info(f"[Pipeline] Threshold {self.selective_threshold}B reached. Switching to Passthrough.")
            # Отправляем данные напрямую без обработки
            writer_srv.write(data)
            await writer_srv.drain()
            self.bytes_processed += len(data)
            return True
        
        # Запускаем сессию если это первый пакет
        if not self.session_active:
            self.session_active = True
            self.bytes_processed = 0
            self.logger.info("[Pipeline] Session started")
        
        current_data = data
        
        # Проходим через все модули конвейера
        for module in self.pipeline_chain:
            try:
                self.logger.info(f"[{module.get_module_name()}] Processing {len(current_data)} bytes")
                
                # Обрабатываем данные через модуль
                current_data = await module.process(current_data, writer_srv)
                
                # Если модуль вернул пустые данные, значит он сам отправил их
                if not current_data:
                    self.logger.info(f"[{module.get_module_name()}] Module consumed data, ending pipeline")
                    break
                
                self.logger.info(f"[{module.get_module_name()}] Output {len(current_data)} bytes")
                
            except Exception as e:
                self.logger.error(f"[{module.get_module_name()}] Error: {e}")
                return False
        
        # Обновляем счетчик обработанных байт
        self.bytes_processed += len(data)
        
        # Если остались данные после конвейера, отправляем их
        if current_data:
            writer_srv.write(current_data)
            await writer_srv.drain()
        
        return True
    
    def reset_session(self):
        """Сброс сессии для нового соединения"""
        self.session_active = False
        self.bytes_processed = 0
        
        # Сбрасываем состояние всех модулей
        for module in self.pipeline_chain:
            if hasattr(module, 'reset_session'):
                module.reset_session()
        
        self.logger.info("[Pipeline] Session reset")
    
    def get_pipeline_info(self) -> str:
        """Возвращает информацию о загруженном конвейере"""
        if not self.pipeline_chain:
            return "No pipeline loaded"
        
        module_names = [module.get_module_name() for module in self.pipeline_chain]
        return " -> ".join(module_names)
