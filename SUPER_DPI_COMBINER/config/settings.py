"""
Настройки конфигурации для Super DPI Combiner
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from config.config_validator import SafeConfigLoader

logger = logging.getLogger(__name__)

class Settings:
    """Класс для управления настройками с валидацией"""
    
    def __init__(self, config_file: str = "settings.json"):
        self.config_file = Path(config_file)
        self.loader = SafeConfigLoader()
        self.settings = {}
        self.validation_report = {}
        self._load_settings()
    
    def _load_settings(self):
        """Загрузка и валидация настроек"""
        try:
            success, config, validation_report = self.loader.load_config(self.config_file)
            self.settings = config
            self.validation_report = validation_report
            
            if success:
                logger.info("Конфигурация успешно загружена и провалидирована")
            else:
                logger.warning("Использована безопасная конфигурация из-за ошибок валидации")
                
        except Exception as e:
            logger.error(f"Критическая ошибка при загрузке настроек: {e}")
            self.settings = self.loader.safe_config
            self.validation_report = {
                "is_valid": False,
                "errors_count": 1,
                "warnings_count": 0,
                "errors": [{"path": "root", "message": f"Critical loading error: {e}", "severity": "error"}],
                "warnings": [],
                "timestamp": "unknown"
            }
    
    def reload(self) -> bool:
        """Перезагрузка настроек с валидацией"""
        try:
            self._load_settings()
            return self.validation_report.get("is_valid", False)
        except Exception as e:
            logger.error(f"Ошибка перезагрузки настроек: {e}")
            return False
    
    def save(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """Сохранение настроек в файл с валидацией"""
        if settings is None:
            settings = self.settings
        
        # Валидируем перед сохранением
        is_valid, validated_settings = self.loader.validator.validate_config(settings)
        
        if not is_valid:
            logger.error("Невозможно сохранить невалидную конфигурацию")
            return False
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Конфигурация сохранена в {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            return False
    
    def _merge_settings(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Слияние настроек по умолчанию с загруженными"""
        def merge_dict(d1, d2):
            result = d1.copy()
            for key, value in d2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dict(default, loaded)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Получение значения по пути (разделенному точками) с защитой от None"""
        if not key_path or not isinstance(key_path, str):
            logger.warning(f"Invalid key_path: {key_path}")
            return default
        
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                if isinstance(value, dict) and key in value and value[key] is not None:
                    value = value[key]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"Error getting value for {key_path}: {e}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Установка значения по пути (разделенному точками) с валидацией"""
        if not key_path or not isinstance(key_path, str):
            logger.error(f"Invalid key_path: {key_path}")
            return False
        
        if value is None:
            logger.warning(f"Attempting to set None value for {key_path}")
            return False
        
        keys = key_path.split('.')
        current = self.settings
        
        try:
            # Создаем путь если нужно
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                elif not isinstance(current[key], dict):
                    logger.error(f"Path conflict: {key_path} (expected dict at {key})")
                    return False
                current = current[key]
            
            # Устанавливаем значение
            final_key = keys[-1]
            old_value = current.get(final_key)
            current[final_key] = value
            
            # Валидируем изменения
            temp_config = self.settings.copy()
            is_valid, _ = self.loader.validator.validate_config(temp_config)
            
            if not is_valid:
                # Откатываем изменения если невалидно
                if old_value is not None:
                    current[final_key] = old_value
                else:
                    current.pop(final_key, None)
                logger.error(f"Invalid value for {key_path}, changes reverted")
                return False
            
            logger.debug(f"Set {key_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting value for {key_path}: {e}")
            return False
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Получить отчет валидации"""
        return self.validation_report
    
    def is_valid(self) -> bool:
        """Проверить валидность текущей конфигурации"""
        return self.validation_report.get("is_valid", False)
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Получить список ошибок"""
        return self.validation_report.get("errors", [])
    
    def get_warnings(self) -> List[Dict[str, Any]]:
        """Получить список предупреждений"""
        return self.validation_report.get("warnings", [])
