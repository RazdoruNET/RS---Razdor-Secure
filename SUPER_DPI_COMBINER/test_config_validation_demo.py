#!/usr/bin/env python3
"""
Демонстрация работы валидации конфигурации
"""

import json
from pathlib import Path
from config.settings import Settings
from config.config_validator import ConfigValidator, SafeConfigLoader

def test_validation_demo():
    """Демонстрация валидации конфигурации"""
    
    print("=== Демонстрация валидации конфигурации ===\n")
    
    # 1. Тест валидации корректной конфигурации
    print("1. Тест корректной конфигурации:")
    valid_config = {
        "system": {
            "mode": "production",
            "debug": False,
            "log_level": "INFO",
            "max_workers": 20,
            "timeout": 30.0
        },
        "engine": {
            "max_workers": 20,
            "mode": "adaptive",
            "auto_optimization": True,
            "optimization_interval": 300
        },
        "llm": {
            "enabled": True,
            "url": "http://localhost:11434",
            "model": "llama2",
            "timeout": 30.0
        }
    }
    
    validator = ConfigValidator()
    is_valid, validated_config = validator.validate_config(valid_config)
    report = validator.get_validation_report()
    
    print(f"   Валидность: {is_valid}")
    print(f"   Ошибок: {report['errors_count']}")
    print(f"   Предупреждений: {report['warnings_count']}")
    print()
    
    # 2. Тест невалидной конфигурации
    print("2. Тест невалидной конфигурации:")
    invalid_config = {
        "system": {
            "mode": "invalid_mode",  # Некорректное значение
            "debug": "not_boolean",   # Неверный тип
            "max_workers": -5,        # Отрицательное значение
            "timeout": 500.0          # Слишком большое значение
        },
        "engine": {
            "max_workers": 2000,      # Превышает максимум
            "mode": "invalid_engine"  # Некорректный режим
        },
        "llm": {
            "enabled": True,
            # Отсутствуют обязательные url и model
        }
    }
    
    validator = ConfigValidator()
    is_valid, validated_config = validator.validate_config(invalid_config)
    report = validator.get_validation_report()
    
    print(f"   Валидность: {is_valid}")
    print(f"   Ошибок: {report['errors_count']}")
    print(f"   Предупреждений: {report['warnings_count']}")
    
    if report['errors']:
        print("   Ошибки:")
        for error in report['errors']:
            print(f"     - {error['path']}: {error['message']}")
    
    if report['warnings']:
        print("   Предупреждения:")
        for warning in report['warnings']:
            print(f"     - {warning['path']}: {warning['message']}")
    print()
    
    # 3. Тест SafeConfigLoader
    print("3. Тест SafeConfigLoader:")
    loader = SafeConfigLoader()
    
    # Сохраняем невалидную конфигурацию во временный файл
    temp_config_path = Path("temp_invalid_config.json")
    with open(temp_config_path, 'w') as f:
        json.dump(invalid_config, f)
    
    success, config, validation_report = loader.load_config(temp_config_path)
    
    print(f"   Успешная загрузка: {success}")
    print(f"   Использована безопасная конфигурация: {not success}")
    print(f"   Ошибок в отчете: {validation_report['errors_count']}")
    
    # Удаляем временный файл
    temp_config_path.unlink()
    print()
    
    # 4. Тест Settings класса
    print("4. Тест Settings класса:")
    
    # Создаем временный конфигурационный файл
    temp_settings_path = Path("temp_settings.json")
    test_config = {
        "system": {
            "mode": "development",
            "debug": True,
            "log_level": "DEBUG",
            "max_workers": 15,
            "timeout": 25.0
        },
        "engine": {
            "max_workers": 15,
            "mode": "performance",
            "auto_optimization": True,
            "optimization_interval": 200
        }
    }
    
    with open(temp_settings_path, 'w') as f:
        json.dump(test_config, f)
    
    settings = Settings(str(temp_settings_path))
    
    print(f"   Конфигурация валидна: {settings.is_valid()}")
    print(f"   Количество ошибок: {len(settings.get_errors())}")
    print(f"   Количество предупреждений: {len(settings.get_warnings())}")
    
    # Тест безопасного получения значений
    max_workers = settings.get("engine.max_workers", 20)
    print(f"   Max workers (безопасное получение): {max_workers}")
    
    # Тест валидации при установке
    set_success = settings.set("engine.max_workers", 25)
    print(f"   Установка нового значения: {set_success}")
    
    # Т попытка установить невалидное значение
    set_invalid = settings.set("engine.max_workers", -5)
    print(f"   Установка невалидного значения: {set_invalid}")
    
    # Удаляем временный файл
    temp_settings_path.unlink()
    print()
    
    # 5. Демонстрация значений по умолчанию
    print("5. Демонстрация применения значений по умолчанию:")
    minimal_config = {
        "system": {
            "mode": "production"
        }
    }
    
    validator = ConfigValidator()
    is_valid, validated_config = validator.validate_config(minimal_config)
    
    print("   Исходная конфигурация:")
    print(json.dumps(minimal_config, indent=2))
    print("\n   Конфигурация после применения значений по умолчанию:")
    print(json.dumps(validated_config, indent=2))
    print()
    
    print("=== Демонстрация завершена ===")

if __name__ == "__main__":
    test_validation_demo()
