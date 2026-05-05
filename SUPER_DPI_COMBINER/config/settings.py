"""
Настройки конфигурации для Super DPI Combiner
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Settings:
    """Класс для управления настройками"""
    
    def __init__(self, config_file: str = "settings.json"):
        self.config_file = Path(config_file)
        self.settings = self._load_default_settings()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Загрузка настроек по умолчанию"""
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
    
    def load(self) -> Dict[str, Any]:
        """Загрузка настроек из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Объединяем с настройками по умолчанию
                    return self._merge_settings(self.settings, loaded_settings)
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")
                return self.settings
        else:
            return self.settings
    
    def save(self, settings: Dict[str, Any]) -> bool:
        """Сохранение настроек в файл"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
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
        """Получение значения по пути (разделенному точками)"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> bool:
        """Установка значения по пути (разделенному точками)"""
        keys = key_path.split('.')
        current = self.settings
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return True
