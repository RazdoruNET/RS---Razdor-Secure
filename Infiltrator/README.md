# 🕵️ INFILTRATOR v2.0

<div align="center">

**Production-Grade JavaScript Bundle Analysis System**

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/razdor/RS---Razdor-Secure)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-advanced-orange.svg)](docs/security.md)

</div>

## 📋 Обзор

**INFILTRATOR v2.0** - это специализированная система для анализа JavaScript-бандлов и извлечения API-эндпоинтов, разработанная с использованием продвинутых техник статического анализа. Программа предназначена для специалистов по безопасности, реверс-инжинирингу и аудиту веб-приложений.

## ✨ Ключевые возможности

### 🔍 Расширенный анализ
- **SSA IR Analysis** - Статический анализ с использованием Static Single Assignment
- **Обфускация Resistance** - Распознавание и обход обфускации кода
- **Multi-Pattern Detection** - Поиск различных паттернов API-вызовов
- **Environment Variable Extraction** - Извлечение `process.env` переменных

### 🛡️ Функции безопасности
- **Risk Assessment** - Автоматическая оценка уровня риска
- **Taint Analysis** - Отслеживание распространения данных
- **Encryption Support** - Защита результатов анализа
- **Stealth Mode** - Скрытый режим анализа

### ⚡ Производительность
- **Parallel Processing** - Параллельный анализ больших файлов
- **Memory Efficient** - Оптимизированное использование памяти
- **Configurable Limits** - Настраиваемые ограничения
- **Fast Regex Parsing** - Быстрый парсинг с регулярными выражениями

## 🚀 Быстрый старт

### Установка
```bash
# Клонирование репозитория
git clone https://github.com/razdor/RS---Razdor-Secure.git
cd RS---Razdor-Secure/Infiltrator

# Установка зависимостей
pip install -r requirements.txt
```

### Базовое использование
```bash
# Анализ JavaScript файла
python3 infiltrator_v2.py test_bundle.js

# Расширенный анализ
python3 infiltrator_v2.py test_bundle.js --stealth -o results.json
```

## 📖 Документация

### 📚 Навигация по документации
- 📖 [Руководство пользователя](docs/user-guide.md) - Подробное руководство
- 🔧 [Установка и настройка](docs/installation.md) - Инструкции по установке
- 🛠️ [Техническая документация](docs/technical.md) - Внутреннее устройство
- 🔌 [API Справочник](docs/api.md) - Программный интерфейс
- 💡 [Примеры использования](docs/examples.md) - Практические примеры

### 🎯 Быстрые ссылки
- [📋 Содержание документации](docs/README.md)
- [🔄 История изменений](CHANGELOG.md)
- [🤝 Вклад в проект](CONTRIBUTING.md)

## 📊 Пример результатов

```json
{
  "bundle_path": "test_bundle.js",
  "bundle_size": 3566,
  "endpoints": [
    {
      "call_target": "OBFUSCATED_API",
      "url": "https://api.example.com",
      "risk_level": "CRITICAL",
      "obfuscated": true
    }
  ],
  "process_env_vars": ["API_TIMEOUT", "API_BASE_URL", "NODE_ENV"],
  "risk_assessment": {
    "level": "HIGH",
    "score": 40,
    "total_endpoints": 4
  }
}
```

## 🛠️ Командная строка

```bash
# Базовый анализ
python3 infiltrator_v2.py <bundle_file>

# Расширенные опции
python3 infiltrator_v2.py <bundle_file> \
  --stealth \
  --output results.json \
  --max-size 10485760 \
  --no-encryption
```

### Опции
- `--stealth` - Включить стелс-режим
- `--output` - Указать выходной файл
- `--max-size` - Максимальный размер файла
- `--no-encryption` - Отключить шифрование

## 🏗️ Архитектура

```
INFILTRATOR v2.0
├── SSA IR Engine          # Внутреннее представление
├── RealWorld Bridge       # Мост JavaScript → SSA
├── Endpoint Extractor     # Извлечение эндпоинтов
├── Obfuscation Resistance # Противодействие обфускации
└── Risk Assessment        # Оценка рисков
```

## 🔧 Конфигурация

```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

config = InfiltratorConfig(
    max_bundle_size=50*1024*1024,  # 50MB
    enable_stealth=True,
    encryption_key=None,
    parallel_analysis=True,
    max_workers=4,
    timeout_seconds=300
)

infiltrator = InfiltratorV2(config)
results = infiltrator.analyze_bundle("bundle.js")
```

## 🎯 Применение

### 🔒 Аудит безопасности
- Поиск утечек API-эндпоинтов
- Анализ конфигурационных переменных
- Оценка уровня безопасности приложения

### 🔍 Реверс-инжиниринг
- Восстановление структуры приложения
- Анализ обфусцированного кода
- Извлечение бизнес-логики

### 📊 Комплаенс
- Проверка соответствия стандартам
- Аудит конфигураций
- Мониторинг безопасности

## 🚨 Уровни риска

| Уровень | Описание | Критерии |
|--------|----------|----------|
| 🔴 **CRITICAL** | Критический риск | Обфусцированные эндпоинты |
| 🟠 **HIGH** | Высокий риск | process.env в API вызовах |
| 🟡 **MEDIUM** | Средний риск | Стандартные API вызовы |
| 🟢 **LOW** | Низкий риск | Внутренние вызовы |

## 📄 Лицензия

Этот проект распространяется под [MIT License](LICENSE).

## ⚠️ Дисклеймер

Инструмент предназначен исключительно для законных целей безопасности. Пользователь несет полную ответственность за использование программы в соответствии с законодательством.

---

<div align="center">

**[📖 Документация](docs/README.md) • [🚀 Начать](docs/installation.md) • [🔧 API](docs/api.md)**

Made with ❤️ by WE Razdor

</div>
