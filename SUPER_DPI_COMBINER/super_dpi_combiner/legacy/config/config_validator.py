#!/usr/bin/env python3
"""
Валидатор конфигурации для Super DPI Combiner
Ручная валидация без внешних библиотек
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigValidationError:
    """Класс для представления ошибки валидации"""
    
    def __init__(self, path: str, message: str, severity: str = "error"):
        self.path = path
        self.message = message
        self.severity = severity  # error, warning, info
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp
        }

class ConfigSchema:
    """Схема валидации конфигурации"""
    
    # Базовые типы
    TYPE_STRING = "string"
    TYPE_INTEGER = "integer"
    TYPE_FLOAT = "float"
    TYPE_BOOLEAN = "boolean"
    TYPE_ARRAY = "array"
    TYPE_OBJECT = "object"
    TYPE_URL = "url"
    TYPE_IP = "ip"
    TYPE_PORT = "port"
    TYPE_LOG_LEVEL = "log_level"
    TYPE_ENGINE_MODE = "engine_mode"
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Получить полную схему конфигурации"""
        return {
            "system": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": True,
                "properties": {
                    "mode": {
                        "type": ConfigSchema.TYPE_STRING,
                        "required": True,
                        "allowed": ["production", "development", "testing"]
                    },
                    "debug": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": False
                    },
                    "log_level": {
                        "type": ConfigSchema.TYPE_LOG_LEVEL,
                        "required": False,
                        "default": "INFO"
                    },
                    "max_workers": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 20,
                        "min": 1,
                        "max": 1000
                    },
                    "timeout": {
                        "type": ConfigSchema.TYPE_FLOAT,
                        "required": False,
                        "default": 30.0,
                        "min": 0.1,
                        "max": 300.0
                    }
                }
            },
            "engine": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "max_workers": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 20,
                        "min": 1,
                        "max": 1000
                    },
                    "mode": {
                        "type": ConfigSchema.TYPE_ENGINE_MODE,
                        "required": False,
                        "default": "adaptive"
                    },
                    "auto_optimization": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": True
                    },
                    "optimization_interval": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 300,
                        "min": 10,
                        "max": 3600
                    }
                }
            },
            "pipelines": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "directory": {
                        "type": ConfigSchema.TYPE_STRING,
                        "required": False,
                        "default": "pipelines"
                    },
                    "auto_load": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": True
                    },
                    "enabled": {
                        "type": ConfigSchema.TYPE_ARRAY,
                        "required": False,
                        "default": [],
                        "item_type": ConfigSchema.TYPE_STRING
                    },
                    "auto_generation": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": True
                    },
                    "max_generations": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 5,
                        "min": 1,
                        "max": 50
                    },
                    "templates_per_technique": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 50,
                        "min": 1,
                        "max": 1000
                    }
                }
            },
            "network": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "dns_servers": {
                        "type": ConfigSchema.TYPE_ARRAY,
                        "required": False,
                        "default": ["8.8.8.8", "8.8.4.4"],
                        "item_type": ConfigSchema.TYPE_IP
                    },
                    "user_agents": {
                        "type": ConfigSchema.TYPE_ARRAY,
                        "required": False,
                        "default": [],
                        "item_type": ConfigSchema.TYPE_STRING
                    },
                    "proxy": {
                        "type": ConfigSchema.TYPE_OBJECT,
                        "required": False,
                        "properties": {
                            "enabled": {
                                "type": ConfigSchema.TYPE_BOOLEAN,
                                "required": False,
                                "default": False
                            },
                            "http_proxy": {
                                "type": ConfigSchema.TYPE_URL,
                                "required": False,
                                "default": ""
                            },
                            "https_proxy": {
                                "type": ConfigSchema.TYPE_URL,
                                "required": False,
                                "default": ""
                            },
                            "socks_proxy": {
                                "type": ConfigSchema.TYPE_URL,
                                "required": False,
                                "default": ""
                            }
                        }
                    }
                }
            },
            "llm": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "enabled": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": True
                    },
                    "url": {
                        "type": ConfigSchema.TYPE_URL,
                        "required": False,
                        "default": "http://localhost:11434"
                    },
                    "model": {
                        "type": ConfigSchema.TYPE_STRING,
                        "required": False,
                        "default": "llama2"
                    },
                    "timeout": {
                        "type": ConfigSchema.TYPE_FLOAT,
                        "required": False,
                        "default": 30.0,
                        "min": 1.0,
                        "max": 300.0
                    },
                    "auto_analysis": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": True
                    },
                    "optimization_requests": {
                        "type": ConfigSchema.TYPE_BOOLEAN,
                        "required": False,
                        "default": True
                    }
                }
            },
            "targets": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "default_urls": {
                        "type": ConfigSchema.TYPE_ARRAY,
                        "required": False,
                        "default": ["https://www.youtube.com"],
                        "item_type": ConfigSchema.TYPE_URL
                    },
                    "test_interval": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 60,
                        "min": 1,
                        "max": 3600
                    },
                    "timeout": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 30,
                        "min": 1,
                        "max": 300
                    }
                }
            },
            "logging": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "level": {
                        "type": ConfigSchema.TYPE_LOG_LEVEL,
                        "required": False,
                        "default": "INFO"
                    },
                    "file": {
                        "type": ConfigSchema.TYPE_STRING,
                        "required": False,
                        "default": "logs/combiner.log"
                    },
                    "max_file_size": {
                        "type": ConfigSchema.TYPE_STRING,
                        "required": False,
                        "default": "100MB"
                    }
                }
            },
            "security": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "max_concurrent_requests": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 100,
                        "min": 1,
                        "max": 10000
                    },
                    "rate_limit": {
                        "type": ConfigSchema.TYPE_OBJECT,
                        "required": False,
                        "properties": {
                            "enabled": {
                                "type": ConfigSchema.TYPE_BOOLEAN,
                                "required": False,
                                "default": True
                            },
                            "requests_per_minute": {
                                "type": ConfigSchema.TYPE_INTEGER,
                                "required": False,
                                "default": 60,
                                "min": 1,
                                "max": 10000
                            },
                            "burst_size": {
                                "type": ConfigSchema.TYPE_INTEGER,
                                "required": False,
                                "default": 10,
                                "min": 1,
                                "max": 1000
                            }
                        }
                    },
                    "allowed_hosts": {
                        "type": ConfigSchema.TYPE_ARRAY,
                        "required": False,
                        "default": ["localhost", "127.0.0.1"],
                        "item_type": ConfigSchema.TYPE_STRING
                    }
                }
            },
            "testing": {
                "type": ConfigSchema.TYPE_OBJECT,
                "required": False,
                "properties": {
                    "target_urls": {
                        "type": ConfigSchema.TYPE_ARRAY,
                        "required": False,
                        "default": ["https://httpbin.org/ip"],
                        "item_type": ConfigSchema.TYPE_URL
                    },
                    "timeout": {
                        "type": ConfigSchema.TYPE_FLOAT,
                        "required": False,
                        "default": 10.0,
                        "min": 1.0,
                        "max": 60.0
                    },
                    "retries": {
                        "type": ConfigSchema.TYPE_INTEGER,
                        "required": False,
                        "default": 3,
                        "min": 0,
                        "max": 10
                    }
                }
            }
        }

class ConfigValidator:
    """Основной класс валидатора конфигурации"""
    
    def __init__(self):
        self.schema = ConfigSchema.get_schema()
        self.errors: List[ConfigValidationError] = []
        self.warnings: List[ConfigValidationError] = []
        
    def validate_config(self, config: Dict[str, Any], config_path: str = "root") -> Tuple[bool, Dict[str, Any]]:
        """
        Валидация конфигурации
        
        Returns:
            Tuple[bool, Dict[str, Any]]: (is_valid, validated_config)
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Создаем копию конфигурации для применения значений по умолчанию
        validated_config = self._apply_defaults(config.copy())
        
        # Валидируем корневой уровень
        self._validate_object(validated_config, self.schema, config_path)
        
        # Дополнительные проверки
        self._validate_cross_dependencies(validated_config)
        
        is_valid = len(self.errors) == 0
        
        if not is_valid:
            logger.error(f"Конфигурация невалидна: {len(self.errors)} ошибок")
        
        return is_valid, validated_config
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Применение значений по умолчанию"""
        def apply_defaults_recursive(config_part: Dict[str, Any], schema_part: Dict[str, Any]) -> Dict[str, Any]:
            if not isinstance(schema_part, dict) or "properties" not in schema_part:
                return config_part
            
            for key, prop_schema in schema_part["properties"].items():
                if key not in config_part and "default" in prop_schema:
                    config_part[key] = prop_schema["default"]
                elif key in config_part and isinstance(config_part[key], dict) and isinstance(prop_schema, dict):
                    if prop_schema.get("type") == ConfigSchema.TYPE_OBJECT:
                        config_part[key] = apply_defaults_recursive(config_part[key], prop_schema)
            
            return config_part
        
        return apply_defaults_recursive(config, {"properties": self.schema})
    
    def _validate_object(self, config: Dict[str, Any], schema: Dict[str, Any], path: str):
        """Валидация объекта"""
        if not isinstance(config, dict):
            self._add_error(path, f"Ожидался объект, получен {type(config).__name__}")
            return
        
        # Проверяем обязательные поля
        if schema.get("required", False) and not config:
            self._add_error(path, "Обязательный объект отсутствует")
            return
        
        properties = schema.get("properties", {})
        
        # Проверяем каждое свойство
        for key, value in config.items():
            if key in properties:
                self._validate_value(value, properties[key], f"{path}.{key}")
            else:
                self._add_warning(f"{path}.{key}", f"Неизвестное свойство: {key}")
        
        # Проверяем отсутствующие обязательные свойства
        for key, prop_schema in properties.items():
            if prop_schema.get("required", False) and key not in config:
                self._add_error(f"{path}.{key}", f"Обязательное свойство отсутствует: {key}")
    
    def _validate_value(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация значения"""
        expected_type = schema.get("type")
        
        if expected_type == ConfigSchema.TYPE_STRING:
            self._validate_string(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_INTEGER:
            self._validate_integer(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_FLOAT:
            self._validate_float(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_BOOLEAN:
            self._validate_boolean(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_ARRAY:
            self._validate_array(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_OBJECT:
            self._validate_object(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_URL:
            self._validate_url(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_IP:
            self._validate_ip(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_PORT:
            self._validate_port(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_LOG_LEVEL:
            self._validate_log_level(value, schema, path)
        elif expected_type == ConfigSchema.TYPE_ENGINE_MODE:
            self._validate_engine_mode(value, schema, path)
        else:
            self._add_warning(path, f"Неизвестный тип: {expected_type}")
    
    def _validate_string(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация строки"""
        if not isinstance(value, str):
            self._add_error(path, f"Ожидалась строка, получен {type(value).__name__}")
            return
        
        # Проверяем разрешенные значения
        if "allowed" in schema and value not in schema["allowed"]:
            self._add_error(path, f"Значение '{value}' не разрешено. Разрешено: {schema['allowed']}")
        
        # Проверяем минимальную длину
        if "min_length" in schema and len(value) < schema["min_length"]:
            self._add_error(path, f"Минимальная длина: {schema['min_length']}, текущая: {len(value)}")
        
        # Проверяем максимальную длину
        if "max_length" in schema and len(value) > schema["max_length"]:
            self._add_error(path, f"Максимальная длина: {schema['max_length']}, текущая: {len(value)}")
        
        # Проверяем паттерн
        if "pattern" in schema and not re.match(schema["pattern"], value):
            self._add_error(path, f"Значение не соответствует паттерну: {schema['pattern']}")
    
    def _validate_integer(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация целого числа"""
        if not isinstance(value, int) or isinstance(value, bool):
            self._add_error(path, f"Ожидалось целое число, получен {type(value).__name__}")
            return
        
        # Проверяем минимум
        if "min" in schema and value < schema["min"]:
            self._add_error(path, f"Минимальное значение: {schema['min']}, текущее: {value}")
        
        # Проверяем максимум
        if "max" in schema and value > schema["max"]:
            self._add_error(path, f"Максимальное значение: {schema['max']}, текущее: {value}")
        
        # Проверяем разрешенные значения
        if "allowed" in schema and value not in schema["allowed"]:
            self._add_error(path, f"Значение {value} не разрешено. Разрешено: {schema['allowed']}")
    
    def _validate_float(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация вещественного числа"""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            self._add_error(path, f"Ожидалось число, получен {type(value).__name__}")
            return
        
        # Проверяем минимум
        if "min" in schema and value < schema["min"]:
            self._add_error(path, f"Минимальное значение: {schema['min']}, текущее: {value}")
        
        # Проверяем максимум
        if "max" in schema and value > schema["max"]:
            self._add_error(path, f"Максимальное значение: {schema['max']}, текущее: {value}")
    
    def _validate_boolean(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация булевого значения"""
        if not isinstance(value, bool):
            self._add_error(path, f"Ожидалось булево значение, получен {type(value).__name__}")
    
    def _validate_array(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация массива"""
        if not isinstance(value, list):
            self._add_error(path, f"Ожидался массив, получен {type(value).__name__}")
            return
        
        # Проверяем минимальную длину
        if "min_items" in schema and len(value) < schema["min_items"]:
            self._add_error(path, f"Минимальное количество элементов: {schema['min_items']}, текущее: {len(value)}")
        
        # Проверяем максимальную длину
        if "max_items" in schema and len(value) > schema["max_items"]:
            self._add_error(path, f"Максимальное количество элементов: {schema['max_items']}, текущее: {len(value)}")
        
        # Валидируем элементы
        item_type = schema.get("item_type", ConfigSchema.TYPE_STRING)
        item_schema = {"type": item_type}
        
        for i, item in enumerate(value):
            self._validate_value(item, item_schema, f"{path}[{i}]")
    
    def _validate_url(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация URL"""
        if not isinstance(value, str):
            self._add_error(path, f"Ожидался URL (строка), получен {type(value).__name__}")
            return
        
        if value == "":
            return  # Пустая строка разрешена для опциональных URL
        
        # Простая валидация URL
        url_pattern = r'^(https?|socks[45])://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, value):
            self._add_error(path, f"Некорректный URL: {value}")
    
    def _validate_ip(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация IP-адреса"""
        if not isinstance(value, str):
            self._add_error(path, f"Ожидался IP-адрес (строка), получен {type(value).__name__}")
            return
        
        # IPv4 паттерн
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        
        # IPv6 паттерн (упрощенный)
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        if not (re.match(ipv4_pattern, value) or re.match(ipv6_pattern, value)):
            self._add_error(path, f"Некорректный IP-адрес: {value}")
    
    def _validate_port(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация порта"""
        if not isinstance(value, int) or isinstance(value, bool):
            self._add_error(path, f"Ожидался порт (целое число), получен {type(value).__name__}")
            return
        
        if not (1 <= value <= 65535):
            self._add_error(path, f"Порт должен быть в диапазоне 1-65535, получен: {value}")
    
    def _validate_log_level(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация уровня логирования"""
        if not isinstance(value, str):
            self._add_error(path, f"Ожидался уровень логирования (строка), получен {type(value).__name__}")
            return
        
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in allowed_levels:
            self._add_error(path, f"Некорректный уровень логирования: {value}. Разрешено: {allowed_levels}")
    
    def _validate_engine_mode(self, value: Any, schema: Dict[str, Any], path: str):
        """Валидация режима движка"""
        if not isinstance(value, str):
            self._add_error(path, f"Ожидался режим движка (строка), получен {type(value).__name__}")
            return
        
        allowed_modes = ["auto_select", "performance", "reliability", "adaptive"]
        if value not in allowed_modes:
            self._add_error(path, f"Некорректный режим движка: {value}. Разрешено: {allowed_modes}")
    
    def _validate_cross_dependencies(self, config: Dict[str, Any]):
        """Валидация перекрестных зависимостей"""
        # Проверка LLM конфигурации
        llm_config = config.get("llm", {})
        if llm_config.get("enabled", False):
            if not llm_config.get("url"):
                self._add_error("llm.url", "URL обязателен при включенном LLM")
            if not llm_config.get("model"):
                self._add_error("llm.model", "Модель обязателен при включенном LLM")
        
        # Проверка прокси конфигурации
        network_config = config.get("network", {})
        proxy_config = network_config.get("proxy", {})
        if proxy_config.get("enabled", False):
            has_proxy = any([
                proxy_config.get("http_proxy"),
                proxy_config.get("https_proxy"),
                proxy_config.get("socks_proxy")
            ])
            if not has_proxy:
                self._add_warning("network.proxy", "Прокси включен, но не настроен")
        
        # Проверка рабочих потоков
        max_workers_system = config.get("system", {}).get("max_workers", 50)
        max_workers_engine = config.get("engine", {}).get("max_workers", 20)
        
        if max_workers_engine > max_workers_system:
            self._add_warning("engine.max_workers", 
                            f"Рабочих потоков движка ({max_workers_engine}) больше системных ({max_workers_system})")
        
        # Проверка безопасности
        security_config = config.get("security", {})
        if security_config.get("max_concurrent_requests", 100) > 1000:
            self._add_warning("security.max_concurrent_requests", 
                            "Высокое количество одновременных запросов может повлиять на производительность")
    
    def _add_error(self, path: str, message: str):
        """Добавление ошибки"""
        self.errors.append(ConfigValidationError(path, message, "error"))
        logger.error(f"Config validation error at {path}: {message}")
    
    def _add_warning(self, path: str, message: str):
        """Добавление предупреждения"""
        self.warnings.append(ConfigValidationError(path, message, "warning"))
        logger.warning(f"Config validation warning at {path}: {message}")
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Получить отчет валидации"""
        return {
            "is_valid": len(self.errors) == 0,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "timestamp": datetime.now().isoformat()
        }

class SafeConfigLoader:
    """Безопасный загрузчик конфигурации с fallback"""
    
    def __init__(self):
        self.validator = ConfigValidator()
        self.safe_config = self._get_safe_config()
    
    def load_config(self, config_path: Union[str, Path]) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        """
        Загрузка конфигурации с валидацией и fallback
        
        Returns:
            Tuple[bool, Dict[str, Any], Dict[str, Any]]: 
            (success, config, validation_report)
        """
        config_path = Path(config_path)
        
        try:
            # Пытаемся загрузить конфигурацию
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    raw_config = json.load(f)
                logger.info(f"Конфигурация загружена из {config_path}")
            else:
                logger.warning(f"Файл конфигурации не найден: {config_path}")
                raw_config = {}
            
            # Валидируем конфигурацию
            is_valid, validated_config = self.validator.validate_config(raw_config)
            
            if is_valid:
                logger.info("Конфигурация прошла валидацию")
                return True, validated_config, self.validator.get_validation_report()
            else:
                logger.error("Конфигурация не прошла валидацию, используем safe mode")
                return False, self.safe_config, self.validator.get_validation_report()
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return False, self.safe_config, {
                "is_valid": False,
                "errors_count": 1,
                "warnings_count": 0,
                "errors": [{"path": "root", "message": f"JSON parsing error: {e}", "severity": "error"}],
                "warnings": [],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Критическая ошибка загрузки конфигурации: {e}")
            return False, self.safe_config, {
                "is_valid": False,
                "errors_count": 1,
                "warnings_count": 0,
                "errors": [{"path": "root", "message": f"Critical error: {e}", "severity": "error"}],
                "warnings": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_safe_config(self) -> Dict[str, Any]:
        """Безопасная конфигурация по умолчанию"""
        return {
            "system": {
                "mode": "production",
                "debug": False,
                "log_level": "INFO",
                "max_workers": 10,
                "timeout": 30.0
            },
            "engine": {
                "max_workers": 10,
                "mode": "adaptive",
                "auto_optimization": False,
                "optimization_interval": 600
            },
            "pipelines": {
                "directory": "pipelines",
                "auto_load": True,
                "enabled": [],
                "auto_generation": False,
                "max_generations": 1,
                "templates_per_technique": 10
            },
            "llm": {
                "enabled": False,
                "url": "http://localhost:11434",
                "model": "llama2",
                "timeout": 30.0,
                "auto_analysis": False,
                "optimization_requests": False
            },
            "network": {
                "dns_servers": ["8.8.8.8", "8.8.4.4"],
                "user_agents": [],
                "proxy": {
                    "enabled": False,
                    "http_proxy": "",
                    "https_proxy": "",
                    "socks_proxy": ""
                }
            },
            "targets": {
                "default_urls": ["https://www.youtube.com"],
                "test_interval": 300,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/combiner.log",
                "max_file_size": "100MB"
            },
            "security": {
                "max_concurrent_requests": 50,
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 30,
                    "burst_size": 5
                },
                "allowed_hosts": ["localhost", "127.0.0.1"]
            },
            "testing": {
                "target_urls": ["https://httpbin.org/ip"],
                "timeout": 10.0,
                "retries": 1
            }
        }
