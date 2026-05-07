# 🔧 Установка и настройка

## 📋 Содержание

- [Системные требования](#системные-требования)
- [Установка](#установка)
- [Проверка установки](#проверка-установки)
- [Конфигурация](#конфигурация)
- [Устранение проблем](#устранение-проблем)

## 🖥️ Системные требования

### Минимальные требования
- **Python**: 3.7 или выше
- **RAM**: 512MB (для файлов до 10MB)
- **Disk**: 100MB свободного пространства
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

### Рекомендуемые требования
- **Python**: 3.9+
- **RAM**: 2GB+ (для больших бандлов)
- **CPU**: 4+ cores (для параллельного анализа)
- **Disk**: 1GB+ свободного пространства

## 📦 Установка

### Способ 1: Клонирование репозитория

```bash
# Клонирование репозитория
git clone https://github.com/razdor/RS---Razdor-Secure.git
cd RS---Razdor-Secure/Infiltrator

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки
python3 infiltrator_v2.py --help
```

### Способ 2: Установка через pip

```bash
# Установка из репозитория
pip install git+https://github.com/razdor/RS---Razdor-Secure.git#subdirectory=Infiltrator

# Проверка установки
infiltrator --help
```

### Способ 3: Ручная установка

```bash
# Скачивание файлов
curl -O https://raw.githubusercontent.com/razdor/RS---Razdor-Secure/main/Infiltrator/infiltrator_v2.py
curl -O https://raw.githubusercontent.com/razdor/RS---Razdor-Secure/main/Infiltrator/requirements.txt

# Установка зависимостей
pip install -r requirements.txt

# Сделать исполняемым
chmod +x infiltrator_v2.py
```

## 📋 Зависимости

### Основные зависимости
```txt
# requirements.txt
ast>=1.0
json>=2.0
re>=2.0
os>=1.0
sys>=1.0
subprocess>=0.1
tempfile>=0.1
hashlib>=1.0
base64>=1.0
typing>=3.7
dataclasses>=0.6
collections>=1.0
pathlib>=1.0
```

### Опциональные зависимости
```txt
# requirements-optional.txt
aiohttp>=3.8.0      # Асинхронная HTTP поддержка
aiofiles>=0.8.0    # Асинхронная работа с файлами
esprima>=4.0.0     # Расширенный JavaScript парсинг
escodegen>=1.14.0  # Генерация JavaScript кода
cryptography>=3.4.0 # Усиленное шифрование
```

### Установка опциональных зависимостей
```bash
pip install -r requirements-optional.txt
```

## ✅ Проверка установки

### Базовая проверка
```bash
# Проверка версии Python
python3 --version

# Проверка установки
python3 infiltrator_v2.py --help
```

### Тестовый запуск
```bash
# Создание тестового файла
echo 'console.log("test");' > test.js

# Запуск анализа
python3 infiltrator_v2.py test.js

# Проверка результатов
cat infiltrator_results.json
```

### Расширенная проверка
```bash
# Тест с обфусцированным кодом
python3 infiltrator_v2.py test_bundle.js --stealth

# Проверка всех функций
python3 -c "
import infiltrator_v2
print('INFILTRATOR успешно импортирован')
"
```

## ⚙️ Конфигурация

### Файл конфигурации

Создайте файл `config.json`:

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

### Переменные окружения

```bash
# Установка переменных окружения
export INFILTRATOR_CONFIG_PATH="/path/to/config.json"
export INFILTRATOR_LOG_LEVEL="INFO"
export INFILTRATOR_OUTPUT_DIR="/path/to/output"
export INFILTRATOR_MAX_WORKERS="8"
```

### Конфигурация через Python

```python
# config.py
from infiltrator_v2 import InfiltratorConfig

config = InfiltratorConfig(
    max_bundle_size=100*1024*1024,  # 100MB
    enable_stealth=True,
    encryption_key=b"your-secret-key",
    parallel_analysis=True,
    max_workers=8,
    timeout_seconds=600
)
```

## 🐳 Docker установка

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "infiltrator_v2.py"]
```

### Сборка и запуск
```bash
# Сборка образа
docker build -t infiltrator .

# Запуск контейнера
docker run -v $(pwd)/data:/app/data infiltrator test_bundle.js

# Интерактивный режим
docker run -it --rm -v $(pwd):/app infiltrator bash
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  infiltrator:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - INFILTRATOR_LOG_LEVEL=DEBUG
    command: python3 infiltrator_v2.py /app/data/bundle.js
```

## 🔧 Настройка производительности

### Оптимизация памяти
```python
# Для больших файлов (>50MB)
config = InfiltratorConfig(
    max_bundle_size=200*1024*1024,  # 200MB
    parallel_analysis=False,         # Отключить параллелизм
    timeout_seconds=1200             # Увеличить таймаут
)
```

### Параллельная обработка
```python
# Для многоядерных систем
import multiprocessing

config = InfiltratorConfig(
    parallel_analysis=True,
    max_workers=multiprocessing.cpu_count(),
    timeout_seconds=300
)
```

### Настройка для CI/CD
```yaml
# .github/workflows/infiltrator.yml
name: Infiltrator Analysis
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
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run analysis
      run: python3 infiltrator_v2.js bundle.js --stealth
```

## 🚨 Устранение проблем

### Проблема: ImportError

```bash
# Ошибка
ImportError: No module named 'infiltrator_v2'

# Решение
export PYTHONPATH="${PYTHONPATH}:/path/to/infiltrator"
python3 infiltrator_v2.py bundle.js
```

### Проблема: Memory Error

```bash
# Ошибка
MemoryError: Unable to allocate array

# Решение
python3 infiltrator_v2.py bundle.js --max-size 10485760
```

### Проблема: Permission Denied

```bash
# Ошибка
PermissionError: [Errno 13] Permission denied

# Решение
chmod +x infiltrator_v2.py
sudo python3 infiltrator_v2.py bundle.js
```

### Проблема: Slow Analysis

```python
# Решение: Оптимизация конфигурации
config = InfiltratorConfig(
    parallel_analysis=True,
    max_workers=2,  # Уменьшить для медленных систем
    timeout_seconds=600
)
```

### Проблема: False Positives

```python
# Решение: Настройка паттернов
config = InfiltratorConfig(
    enable_stealth=False,  # Отключить агрессивный анализ
    enable_source_map_recovery=True
)
```

## 📊 Мониторинг производительности

### Профилирование
```bash
# Профилирование CPU
python3 -m cProfile -o profile.stats infiltrator_v2.py bundle.js

# Анализ результатов
python3 -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

### Мониторинг памяти
```bash
# Мониторинг использования памяти
python3 -m memory_profiler infiltrator_v2.py bundle.js
```

### Логирование
```python
# Включение детального логирования
import logging
logging.basicConfig(level=logging.DEBUG)

# Запуск с логами
python3 infiltrator_v2.py bundle.js --stealth 2>&1 | tee analysis.log
```

## 🔄 Обновление

### Обновление через Git
```bash
# Обновление до последней версии
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt --upgrade
```

### Обновление через pip
```bash
# Обновление пакета
pip install --upgrade git+https://github.com/razdor/RS---Razdor-Secure.git#subdirectory=Infiltrator
```

## 📞 Поддержка

Если у вас возникли проблемы с установкой:

1. Проверьте [системные требования](#системные-требования)
2. Посмотрите [устранение проблем](#устранение-проблем)
3. Создайте [issue на GitHub](https://github.com/razdor/RS---Razdor-Secure/issues)
4. Свяжитесь с [поддержкой](mailto:support@razdor.net)

---

**[← Назад к документации](README.md) • [Руководство пользователя →](user-guide.md)**
