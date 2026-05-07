# 📖 Руководство пользователя INFILTRATOR v2.0

<div align="center">

**Полное руководство по использованию системы анализа JavaScript-бандлов**

[![User Guide](https://img.shields.io/badge/guide-complete-brightgreen.svg)](https://github.com/razdor/RS---Razdor-Secure)
[![Complexity](https://img.shields.io/badge/complexity-⭐⭐-yellow.svg)](docs/README.md)

</div>

## 📋 Содержание

- [Введение](#введение)
- [Основные концепции](#основные-концепции)
- [Первый анализ](#первый-анализ)
- [Командная строка](#командная-строка)
- [Конфигурация](#конфигурация)
- [Результаты анализа](#результаты-анализа)
- [Продвинутое использование](#продвинутое-использование)
- [Лучшие практики](#лучшие-практики)

---

## 🎯 Введение

### Что такое INFILTRATOR?

**INFILTRATOR v2.0** - это специализированный инструмент для анализа JavaScript-бандлов с целью извлечения API-эндпоинтов, переменных окружения и оценки безопасности веб-приложений.

### Ключевые возможности

- 🔍 **Анализ обфусцированного кода**
- 🌐 **Извлечение API-эндпоинтов**
- 🛡️ **Оценка рисков безопасности**
- 🔐 **Шифрование результатов**
- ⚡ **Параллельная обработка**

### Для кого этот инструмент?

- **🔒 Специалисты по безопасности** - аудит веб-приложений
- **🔍 Реверс-инженеры** - анализ закрытого кода
- **📊 DevOps инженеры** - мониторинг безопасности
- **👨‍💻 Разработчики** - проверка собственных приложений

---

## 🧠 Основные концепции

### SSA (Static Single Assignment)

INFILTRATOR использует SSA IR для внутреннего представления кода:

```
# Пример SSA инструкции
api_call_1_0@local = CALL(axios.get("https://api.example.com"))
```

### Taint Analysis

Отслеживание распространения данных от источников к стокам:

```
process.env.API_KEY → tainted → axios.create() → API call
```

### Уровни риска

| Уровень | Цвет | Описание | Пример |
|---------|------|----------|--------|
| 🔴 CRITICAL | Красный | Критическая угроза | Обфусцированный эндпоинт |
| 🟠 HIGH | Оранжевый | Высокий риск | process.env в API |
| 🟡 MEDIUM | Желтый | Средний риск | Стандартный API вызов |
| 🟢 LOW | Зеленый | Низкий риск | Внутренний вызов |

---

## 🚀 Первый анализ

### Шаг 1: Подготовка

Создайте тестовый JavaScript файл:

```javascript
// test.js
const axios = require('axios');

const config = {
    apiUrl: process.env.API_BASE_URL || 'https://api.example.com',
    timeout: process.env.API_TIMEOUT || 5000
};

const api = axios.create({
    baseURL: config.apiUrl,
    timeout: config.timeout,
    headers: {
        'Authorization': 'Bearer ' + process.env.API_KEY
    }
});

module.exports = {
    getUsers: () => api.get('/users'),
    createOrder: (data) => api.post('/orders', data)
};
```

### Шаг 2: Базовый анализ

```bash
# Запуск анализа
python3 infiltrator_v2.py test.js

# Вывод
[INFILTRATOR v2.0] Analyzing bundle: test.js
[INFILTRATOR] Process.env variables found: {'API_BASE_URL', 'API_TIMEOUT', 'API_KEY'}
[INFILTRATOR] Found 3 process.env variables
[INFILTRATOR] Extracted 2 potential API endpoints
[INFILTRATOR] Results saved to: infiltrator_results.json
```

### Шаг 3: Просмотр результатов

```bash
# Просмотр результатов
cat infiltrator_results.json
```

```json
{
  "bundle_path": "test.js",
  "bundle_size": 447,
  "endpoints": [
    {
      "call_target": "axios.get",
      "url": "/users",
      "risk_level": "MEDIUM"
    },
    {
      "call_target": "axios.post",
      "url": "/orders",
      "risk_level": "MEDIUM"
    }
  ],
  "process_env_vars": ["API_BASE_URL", "API_TIMEOUT", "API_KEY"],
  "risk_assessment": {
    "level": "MEDIUM",
    "score": 10,
    "total_endpoints": 2
  }
}
```

---

## 💻 Командная строка

### Базовый синтаксис

```bash
python3 infiltrator_v2.py <bundle_file> [options]
```

### Основные опции

| Опция | Короткая | Описание | Пример |
|-------|----------|----------|--------|
| `--output` | `-o` | Выходной файл | `-o results.json` |
| `--stealth` | | Стелс-режим | `--stealth` |
| `--no-encryption` | | Отключить шифрование | `--no-encryption` |
| `--max-size` | | Макс. размер файла | `--max-size 10485760` |
| `--help` | `-h` | Помощь | `-h` |

### Примеры использования

#### Базовый анализ
```bash
python3 infiltrator_v2.js bundle.js
```

#### Расширенный анализ
```bash
python3 infiltrator_v2.js bundle.js \
  --stealth \
  --output detailed_results.json \
  --max-size 52428800
```

#### Анализ с отключенным шифрованием
```bash
python3 infiltrator_v2.js bundle.js \
  --no-encryption \
  --output plain_results.json
```

### Анализ нескольких файлов

```bash
# Анализ всех JS файлов в директории
for file in *.js; do
    python3 infiltrator_v2.js "$file" -o "results_$file.json"
done

# Использование find
find . -name "*.js" -exec infiltrator_v2.js {} -o "results_{}.json" \;
```

---

## ⚙️ Конфигурация

### Файл конфигурации

Создайте `infiltrator_config.json`:

```json
{
  "max_bundle_size": 52428800,
  "enable_stealth": true,
  "encryption_key": null,
  "output_format": "json",
  "parallel_analysis": true,
  "max_workers": 4,
  "timeout_seconds": 300,
  "enable_source_map_recovery": true,
  "enable_runtime_instrumentation": true
}
```

### Конфигурация через Python

```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Базовая конфигурация
config = InfiltratorConfig(
    enable_stealth=True,
    max_bundle_size=100*1024*1024
)

infiltrator = InfiltratorV2(config)
results = infiltrator.analyze_bundle("bundle.js")
```

### Конфигурация для разных сценариев

#### Для больших файлов
```python
config = InfiltratorConfig(
    max_bundle_size=200*1024*1024,  # 200MB
    parallel_analysis=False,        # Отключить параллелизм
    timeout_seconds=1200            # Увеличить таймаут
)
```

#### Для максимальной безопасности
```python
config = InfiltratorConfig(
    enable_stealth=True,
    encryption_key=b"your-secret-key",
    enable_source_map_recovery=True
)
```

#### Для быстрого анализа
```python
config = InfiltratorConfig(
    enable_stealth=False,
    parallel_analysis=True,
    max_workers=8,
    timeout_seconds=60
)
```

---

## 📊 Результаты анализа

### Структура результатов

```json
{
  "bundle_path": "string",
  "bundle_size": "number",
  "endpoints": "array",
  "process_env_vars": "array",
  "analysis_timestamp": "string",
  "infiltrator_version": "string",
  "risk_assessment": "object",
  "encrypted": "string (optional)"
}
```

### Детальная информация об эндпоинтах

```json
{
  "call_target": "axios.get",
  "tainted_source": "process.env",
  "arguments": ["https://api.example.com/users"],
  "url": "https://api.example.com/users",
  "location": {
    "line": 15,
    "column": 20
  },
  "instruction": "api_call_1_0@local = CALL(axios.get(...))",
  "risk_level": "HIGH",
  "obfuscated": false
}
```

### Оценка рисков

```json
{
  "level": "HIGH",
  "score": 40,
  "high_risk_endpoints": 2,
  "medium_risk_endpoints": 3,
  "total_endpoints": 5
}
```

### Интерпретация результатов

#### Уровень риска CRITICAL
- **Что означает**: Обфусцированные или скрытые эндпоинты
- **Действия**: Немедленная проверка, изменение кода

#### Уровень риска HIGH
- **Что означает**: Использование переменных окружения в API
- **Действия**: Проверка конфигурации, аудит безопасности

#### Уровень риска MEDIUM
- **Что означает**: Стандартные API вызовы
- **Действия**: Мониторинг, документирование

#### Уровень риска LOW
- **Что означает**: Внутренние вызовы
- **Действия**: Обычный мониторинг

---

## 🎯 Продвинутое использование

### Анализ обфусцированного кода

#### Пример обфусцированного кода
```javascript
// obfuscated.js
var _0x2a4b = ['\x68\x74\x74\x70\x73\x3a\x2f\x2f\x61\x70\x69\x2e\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d'];
var _0x1f2c = function(_0x3e8d) { return axios['get'](_0x2a4b[0]); };
```

#### Анализ с стелс-режимом
```bash
python3 infiltrator_v2.js obfuscated.js --stealth
```

#### Результаты
```json
{
  "endpoints": [
    {
      "call_target": "OBFUSCATED_API",
      "url": "https://api.example.com",
      "risk_level": "CRITICAL",
      "obfuscated": true
    }
  ]
}
```

### Работа с большими бандлами

#### Анализ webpack бандла
```bash
# Проверка размера
ls -lh bundle.js

# Анализ с увеличенным лимитом
python3 infiltrator_v2.js bundle.js --max-size 104857600
```

#### Параллельный анализ
```python
config = InfiltratorConfig(
    parallel_analysis=True,
    max_workers=8,
    timeout_seconds=600
)
```

### Интеграция в CI/CD

#### GitHub Actions
```yaml
name: Security Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install Infiltrator
      run: |
        git clone https://github.com/razdor/RS---Razdor-Secure.git
        cd RS---Razdor-Secure/Infiltrator
        pip install -r requirements.txt
    - name: Analyze bundles
      run: |
        find . -name "*.js" -exec python3 infiltrator_v2.js {} \;
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: security-results
        path: infiltrator_results.json
```

### Автоматизация анализа

#### Скрипт для анализа директории
```python
#!/usr/bin/env python3
import json
import os
from pathlib import Path
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

def analyze_directory(directory):
    config = InfiltratorConfig(enable_stealth=True)
    infiltrator = InfiltratorV2(config)
    
    results = []
    
    for js_file in Path(directory).glob("**/*.js"):
        print(f"Analyzing: {js_file}")
        result = infiltrator.analyze_bundle(str(js_file))
        if 'error' not in result:
            results.append(result)
    
    # Сохранение сводных результатов
    with open('directory_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analyzed {len(results)} files")
    return results

if __name__ == "__main__":
    analyze_directory("./src")
```

---

## 🎯 Лучшие практики

### 🔒 Безопасность

1. **Регулярный аудит**
   ```bash
   # Еженедельный анализ
   0 3 * * 1 /usr/bin/python3 /path/to/infiltrator_v2.js /app/bundle.js
   ```

2. **Версионирование результатов**
   ```bash
   # Сохранение с датой
   python3 infiltrator_v2.js bundle.js -o "results_$(date +%Y%m%d).json"
   ```

3. **Шифрование чувствительных данных**
   ```python
   config = InfiltratorConfig(
       encryption_key=os.environ.get('ENCRYPTION_KEY')
   )
   ```

### ⚡ Производительность

1. **Оптимизация для больших файлов**
   ```python
   config = InfiltratorConfig(
       max_bundle_size=100*1024*1024,
       parallel_analysis=False
   )
   ```

2. **Кэширование результатов**
   ```python
   import hashlib
   
   def get_file_hash(filepath):
       with open(filepath, 'rb') as f:
           return hashlib.md5(f.read()).hexdigest()
   
   # Анализ только измененных файлов
   current_hash = get_file_hash('bundle.js')
   if current_hash != last_analyzed_hash:
       results = infiltrator.analyze_bundle('bundle.js')
   ```

3. **Параллельная обработка**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   def analyze_multiple_files(files):
       with ThreadPoolExecutor(max_workers=4) as executor:
           results = list(executor.map(analyze_bundle, files))
       return results
   ```

### 📊 Мониторинг

1. **Метрики анализа**
   ```python
   def collect_metrics(results):
       metrics = {
           'total_files': len(results),
           'total_endpoints': sum(len(r['endpoints']) for r in results),
           'high_risk_count': sum(
               1 for r in results 
               for ep in r['endpoints'] 
               if ep['risk_level'] == 'HIGH'
           )
       }
       return metrics
   ```

2. **Алерты при высоком риске**
   ```python
   def check_risk_level(results):
       for result in results:
           if result['risk_assessment']['level'] == 'CRITICAL':
               send_alert(f"Critical risk in {result['bundle_path']}")
   ```

### 📝 Документирование

1. **Ведение логов**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('infiltrator.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Структурированные отчеты**
   ```python
   def generate_report(results):
       report = {
           'summary': collect_metrics(results),
           'details': results,
           'recommendations': generate_recommendations(results)
       }
       return report
   ```

---

## 🔍 Поиск и фильтрация

### Поиск по результатам

```python
def find_high_risk_endpoints(results):
    high_risk = []
    for result in results:
        for endpoint in result['endpoints']:
            if endpoint['risk_level'] in ['HIGH', 'CRITICAL']:
                high_risk.append({
                    'file': result['bundle_path'],
                    'endpoint': endpoint
                })
    return high_risk
```

### Фильтрация по URL

```python
def filter_by_domain(results, domain):
    filtered = []
    for result in results:
        filtered_result = result.copy()
        filtered_result['endpoints'] = [
            ep for ep in result['endpoints']
            if ep.get('url', '').startswith(domain)
        ]
        filtered.append(filtered_result)
    return filtered
```

---

## 🚨 Распространенные ошибки

### Ошибка: "Bundle too large"
```bash
# Решение: увеличить лимит
python3 infiltrator_v2.js large_bundle.js --max-size 104857600
```

### Ошибка: "Parse error"
```bash
# Решение: включить стелс-режим
python3 infiltrator_v2.js problematic.js --stealth
```

### Ошибка: "Memory error"
```python
# Решение: отключить параллелизм
config = InfiltratorConfig(parallel_analysis=False)
```

---

## 📞 Поддержка

### Дополнительные ресурсы
- [🔧 Установка](installation.md) - Инструкции по установке
- [⚙️ Техническая документация](technical.md) - Внутреннее устройство
- [💡 Примеры](examples.md) - Практические примеры
- [🔌 API справочник](api.md) - Программный интерфейс

### Получение помощи
- **📖 Документация** - Полное руководство
- **🐛 GitHub Issues** - Сообщить о проблеме
- **💬 GitHub Discussions** - Задать вопрос
- **📧 Email** - [support@razdor.net](mailto:support@razdor.net)

---

**[← Назад к навигации](README.md) • [Техническая документация →](technical.md)**
