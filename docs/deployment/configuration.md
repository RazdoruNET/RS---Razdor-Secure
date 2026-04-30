# Configuration and Deployment Guide

## Обзор

Это руководство описывает конфигурацию и развертывание системы RSecure, включая установку зависимостей, настройку компонентов, развертывание в различных средах и эксплуатацию.

## Требования к системе

### Минимальные требования

- **ОС**: macOS 10.14+ или Linux (Ubuntu 18.04+, CentOS 7+)
- **Python**: 3.11+ (для TensorFlow совместимости)
- **RAM**: 4GB минимум, 8GB рекомендуется
- **Диск**: 10GB свободного пространства
- **CPU**: 2 ядра минимум, 4 ядра рекомендуется

### Рекомендуемые требования

- **ОС**: macOS 12+ или Ubuntu 20.04+
- **Python**: 3.11
- **RAM**: 16GB+
- **Диск**: 50GB SSD
- **CPU**: 8 ядер+

### Зависимости

#### Обязательные
- Python 3.11+
- pip (Python package manager)
- git

#### Опциональные
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA CUDA Toolkit (для GPU ускорения)
- Ollama (для LLM интеграции)

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/razdoru-net/rsecure.git
cd rsecure
```

### 2. Создание виртуального окружения

```bash
# Создание виртуального окружения
python3.11 -m venv rsecure-env

# Активация
source rsecure-env/bin/activate  # Linux/macOS
# или
rsecure-env\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
# Установка базовых зависимостей
pip install -r requirements.txt

# Для TensorFlow (если < Python 3.12)
pip install "tensorflow>=2.10.0,<2.15.0"
pip install "keras>=2.10.0,<2.15.0"

# Для Ollama интеграции
pip install ollama-python

# Для разработки
pip install -r requirements-dev.txt
```

### 4. Установка Ollama (опционально)

```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama сервиса
ollama serve &

# Загрузка моделей
ollama pull qwen2.5-coder:1.5b
ollama pull gemma2:2b
```

## Конфигурация

### 1. Основной конфигурационный файл

Создайте файл `rsecure_config.json`:

```json
{
  "system": {
    "debug": false,
    "log_level": "INFO",
    "max_workers": 4,
    "data_dir": "./data",
    "models_dir": "./models",
    "logs_dir": "./logs"
  },
  "system_detection": {
    "enabled": true,
    "auto_configure": true
  },
  "neural_core": {
    "enabled": true,
    "model_path": "./models/neural_core.h5",
    "confidence_threshold": 0.7,
    "batch_size": 32,
    "analysis_interval": 5,
    "enable_gpu": false,
    "models": {
      "network_analyzer": {
        "enabled": true,
        "input_shape": [64],
        "conv_filters": [32, 64, 128],
        "lstm_units": 64
      },
      "process_detector": {
        "enabled": true,
        "input_shape": [32],
        "dense_units": [64, 32]
      },
      "file_monitor": {
        "enabled": true,
        "input_shape": [128],
        "conv_filters": [16, 32]
      }
    }
  },
  "reinforcement_learning": {
    "enabled": true,
    "model_path": "./models/rl_agent.h5",
    "state_dim": 128,
    "action_dim": 20,
    "epsilon_start": 1.0,
    "epsilon_decay": 0.995,
    "epsilon_min": 0.01,
    "gamma": 0.95,
    "learning_rate": 0.001,
    "batch_size": 32,
    "memory_size": 10000,
    "target_update_freq": 100,
    "training_interval": 10,
    "save_interval": 100
  },
  "ollama_integration": {
    "enabled": true,
    "ollama_url": "http://localhost:11434",
    "default_model": "qwen2.5-coder:1.5b",
    "fallback_model": "gemma2:2b",
    "cache_timeout": 300,
    "max_content_length": 10000
  },
  "network_defense": {
    "enabled": true,
    "monitored_ports": [22, 80, 443, 3389, 1433, 3306, 5432, 6379, 27017],
    "auto_block_threshold": 10,
    "block_duration": 3600,
    "max_block_duration": 86400,
    "packet_capture_size": 65535,
    "analysis_interval": 5,
    "enable_honeypot": true,
    "honeypot_ports": [8080, 8888, 9999],
    "enable_rate_limiting": true,
    "rate_limit_threshold": 100,
    "enable_port_scanning_detection": true,
    "enable_ddos_detection": true,
    "enable_brute_force_detection": true,
    "enable_anomaly_detection": true
  },
  "phishing_detection": {
    "enabled": true,
    "model_path": "./models/phishing_detector.h5",
    "confidence_threshold": 0.7,
    "risk_threshold": 0.8,
    "max_url_length": 2048,
    "enable_real_time_detection": true,
    "enable_url_analysis": true,
    "enable_content_analysis": true,
    "enable_behavioral_analysis": true
  },
  "llm_defense": {
    "enabled": true,
    "model_path": "./models/llm_defense.h5",
    "confidence_threshold": 0.7,
    "severity_threshold": 0.8,
    "max_content_length": 10000,
    "enable_pattern_detection": true,
    "enable_content_analysis": true,
    "enable_behavior_analysis": true,
    "enable_adversarial_detection": true,
    "update_interval": 300,
    "block_duration": 3600
  },
  "audio_video_monitoring": {
    "enabled": true,
    "monitoring_interval": 30,
    "device_timeout": 300,
    "capacitor_scan_interval": 60,
    "risk_threshold": 0.7,
    "enable_audio_monitoring": true,
    "enable_video_monitoring": true,
    "enable_capacitor_analysis": true,
    "enable_hardware_scanning": true,
    "enable_process_monitoring": true
  },
  "system_monitoring": {
    "enabled": true,
    "log_dir": "/var/log/security_monitor",
    "log_interval": 1,
    "network_scan_interval": 30,
    "file_scan_interval": 60,
    "max_log_size": 104857600,
    "log_retention_days": 30,
    "monitor_paths": [
      "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin",
      "/System/Library", "/Library", "/Applications"
    ],
    "network_ports": [22, 80, 443, 3306, 5432, 6379, 27017],
    "alert_threshold": 0.8
  },
  "analytics": {
    "enabled": true,
    "db_path": "./security_analytics.db",
    "analysis_interval": 60,
    "trend_window": 24,
    "alert_threshold": 0.7,
    "report_retention_days": 90,
    "auto_correlation": true,
    "ml_enabled": true,
    "export_formats": ["json", "html", "pdf"]
  },
  "notifications": {
    "enabled": true,
    "notification_cooldown": 30,
    "default_timeout": 5,
    "enable_sound": true,
    "enable_icon": true,
    "severity_levels": {
      "low": {"sound": "Glass", "timeout": 3},
      "medium": {"sound": "Ping", "timeout": 5},
      "high": {"sound": "Basso", "timeout": 7},
      "critical": {"sound": "Sosumi", "timeout": 10}
    }
  },
  "api": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "cors_enabled": true,
    "rate_limit": 100,
    "api_key_required": true,
    "websocket_enabled": true
  }
}
```

### 2. Конфигурация для разных сред

#### Разработка (development)

```json
{
  "system": {
    "debug": true,
    "log_level": "DEBUG"
  },
  "api": {
    "debug": true,
    "api_key_required": false
  },
  "neural_core": {
    "batch_size": 16,
    "analysis_interval": 10
  }
}
```

#### Тестирование (testing)

```json
{
  "system": {
    "debug": true,
    "log_level": "INFO"
  },
  "neural_core": {
    "enabled": false
  },
  "reinforcement_learning": {
    "enabled": false
  }
}
```

#### Продакшн (production)

```json
{
  "system": {
    "debug": false,
    "log_level": "WARNING"
  },
  "api": {
    "debug": false,
    "api_key_required": true,
    "rate_limit": 1000
  },
  "neural_core": {
    "enable_gpu": true,
    "batch_size": 64
  }
}
```

## Развертывание

### 1. Локальное развертывание

```bash
# Запуск основной системы
python rsecure_main.py

# Запуск с конфигурацией
python rsecure_main.py --config rsecure_config.json

# Запуск в режиме отладки
python rsecure_main.py --debug
```

### 2. Docker развертывание

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p data models logs

# Установка прав доступа
RUN chmod +x rsecure_main.py

# Открытие портов
EXPOSE 8080

# Запуск
CMD ["python", "rsecure_main.py"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  rsecure:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
      - ./rsecure_config.json:/app/rsecure_config.json
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  ollama_data:
```

#### Запуск Docker

```bash
# Сборка образа
docker build -t rsecure .

# Запуск с Docker Compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f rsecure
```

### 3. Системный сервис (systemd)

#### Создание сервиса

```bash
# Создание файла сервиса
sudo nano /etc/systemd/system/rsecure.service
```

```ini
[Unit]
Description=RSecure Security System
After=network.target

[Service]
Type=simple
User=rsecure
Group=rsecure
WorkingDirectory=/opt/rsecure
ExecStart=/opt/rsecure/rsecure-env/bin/python rsecure_main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Управление сервисом

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable rsecure

# Запуск сервиса
sudo systemctl start rsecure

# Проверка статуса
sudo systemctl status rsecure

# Просмотр логов
sudo journalctl -u rsecure -f
```

### 4. Kubernetes развертывание

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rsecure
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rsecure
  template:
    metadata:
      labels:
        app: rsecure
    spec:
      containers:
      - name: rsecure
        image: rsecure:latest
        ports:
        - containerPort: 8080
        env:
        - name: PYTHONPATH
          value: "/app"
        volumeMounts:
        - name: config
          mountPath: /app/rsecure_config.json
          subPath: rsecure_config.json
        - name: data
          mountPath: /app/data
        - name: models
          mountPath: /app/models
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
      volumes:
      - name: config
        configMap:
          name: rsecure-config
      - name: data
        persistentVolumeClaim:
          claimName: rsecure-data
      - name: models
        persistentVolumeClaim:
          claimName: rsecure-models
---
apiVersion: v1
kind: Service
metadata:
  name: rsecure-service
spec:
  selector:
    app: rsecure
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

## Мониторинг и логирование

### 1. Структура логов

```
logs/
├── rsecure_main.log          # Основной лог системы
├── neural_analysis.log       # Нейросетевой анализ
├── reinforcement_learning.log # Обучение с подкреплением
├── network_defense.log       # Сетевая защита
├── phishing_detector.log     # Детекция фишинга
├── llm_defense.log          # LLM защита
├── audio_video_monitor.log   # Аудио/видео мониторинг
├── system_monitoring.log     # Системный мониторинг
├── analytics.log            # Аналитика
└── notifications.log         # Уведомления
```

### 2. Конфигурация логирования

```python
# В rsecure_config.json
{
  "logging": {
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
      "standard": {
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
      },
      "detailed": {
        "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "level": "INFO",
        "formatter": "standard",
        "stream": "ext://sys.stdout"
      },
      "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "level": "DEBUG",
        "formatter": "detailed",
        "filename": "./logs/rsecure_main.log",
        "maxBytes": 10485760,
        "backupCount": 5
      }
    },
    "loggers": {
      "rsecure": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
        "propagate": false
      }
    },
    "root": {
      "level": "INFO",
      "handlers": ["console"]
    }
  }
}
```

### 3. Мониторинг с Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rsecure'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

## Безопасность

### 1. API ключи

```bash
# Генерация API ключа
python -c "
import secrets
print(f'API Key: rs_{secrets.token_urlsafe(24)}')
"

# Установка в конфигурации
export RSECURE_API_KEY="rs_your_api_key_here"
```

### 2. Права доступа

```bash
# Создание пользователя rsecure
sudo useradd -r -s /bin/false rsecure

# Настройка прав доступа
sudo chown -R rsecure:rsecure /opt/rsecure
sudo chmod 750 /opt/rsecure
```

### 3. Брандмауэр

```bash
# Настройка UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw enable

# Настройка iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

## Оптимизация производительности

### 1. Настройка TensorFlow

```python
# В конфигурации
{
  "neural_core": {
    "enable_gpu": true,
    "gpu_memory_growth": true,
    "mixed_precision": true,
    "tensorrt_optimization": true
  }
}
```

### 2. Кэширование

```python
# Redis конфигурация
{
  "cache": {
    "enabled": true,
    "redis_url": "redis://localhost:6379",
    "cache_size": 1000,
    "ttl": 3600
  }
}
```

### 3. Оптимизация памяти

```python
# В rsecure_config.json
{
  "system": {
    "max_workers": 4,
    "memory_limit": "8GB",
    "gc_threshold": 0.8
  }
}
```

## Тестирование развертывания

### 1. Проверка компонентов

```bash
# Проверка статуса системы
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/status

# Проверка нейросетевого ядра
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/neural/status

# Проверка API доступности
curl -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/health
```

### 2. Нагрузочное тестирование

```bash
# Установка Apache Benchmark
sudo apt-get install apache2-utils

# Нагрузочный тест API
ab -n 1000 -c 10 -H "X-API-Key: $API_KEY" http://localhost:8080/api/v1/status
```

### 3. Интеграционные тесты

```python
# test_deployment.py
import requests
import json

def test_deployment():
    base_url = "http://localhost:8080/api/v1"
    api_key = "your-api-key"
    headers = {"X-API-Key": api_key}
    
    # Тест статуса
    response = requests.get(f"{base_url}/status", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "running"
    
    # Тест анализа
    event_data = {
        "event_type": "test",
        "data": {"test": True}
    }
    response = requests.post(f"{base_url}/detection/analyze", 
                           json=event_data, headers=headers)
    assert response.status_code == 200
    
    print("All tests passed!")

if __name__ == "__main__":
    test_deployment()
```

## Обслуживание

### 1. Обновление системы

```bash
# Обновление кода
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Перезапуск сервиса
sudo systemctl restart rsecure
```

### 2. Резервное копирование

```bash
# Скрипт резервного копирования
#!/bin/bash
BACKUP_DIR="/backup/rsecure"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание бэкапа
mkdir -p $BACKUP_DIR/$DATE

# Копирование конфигурации
cp rsecure_config.json $BACKUP_DIR/$DATE/

# Копирование моделей
cp -r models/ $BACKUP_DIR/$DATE/

# Копирование данных
cp -r data/ $BACKUP_DIR/$DATE/

# Копирование логов
cp -r logs/ $BACKUP_DIR/$DATE/

# Архивирование
tar -czf $BACKUP_DIR/rsecure_backup_$DATE.tar.gz $BACKUP_DIR/$DATE/
rm -rf $BACKUP_DIR/$DATE

echo "Backup completed: $BACKUP_DIR/rsecure_backup_$DATE.tar.gz"
```

### 3. Мониторинг здоровья

```bash
# health_check.sh
#!/bin/bash

API_KEY="your-api-key"
BASE_URL="http://localhost:8080/api/v1"

# Проверка статуса
STATUS=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/status" | jq -r '.status')

if [ "$STATUS" != "running" ]; then
    echo "CRITICAL: RSecure is not running"
    exit 2
fi

# Проверка нагрузки
CPU=$(curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/monitoring/system" | jq -r '.system_resources.cpu_percent')

if (( $(echo "$CPU > 90" | bc -l) )); then
    echo "WARNING: High CPU usage: $CPU%"
fi

echo "Health check passed"
exit 0
```

## Устранение неисправностей

### 1. Общие проблемы

#### Проблема: ImportError: No module named 'tensorflow'

**Решение:**
```bash
# Проверка версии Python
python --version

# Установка совместимой версии TensorFlow
pip install "tensorflow>=2.10.0,<2.15.0"

# Или использование Python < 3.12
python3.11 -m venv venv
source venv/bin/activate
pip install tensorflow
```

#### Проблема: Permission denied

**Решение:**
```bash
# Изменение прав доступа
sudo chown -R $USER:$USER /opt/rsecure
sudo chmod -R 755 /opt/rsecure

# Или запуск с sudo
sudo python rsecure_main.py
```

#### Проблема: Port already in use

**Решение:**
```bash
# Проверка порта
sudo netstat -tulpn | grep 8080

# Изменение порта в конфигурации
sed -i 's/"port": 8080/"port": 8081/' rsecure_config.json
```

### 2. Проблемы с нейросетями

#### Проблема: CUDA out of memory

**Решение:**
```json
{
  "neural_core": {
    "enable_gpu": false,
    "batch_size": 16
  }
}
```

#### Проблема: Model not found

**Решение:**
```bash
# Проверка наличия моделей
ls -la models/

# Скачивание предобученных моделей
python download_models.py
```

### 3. Проблемы с Ollama

#### Проблема: Connection refused

**Решение:**
```bash
# Проверка статуса Ollama
ollama ps

# Запуск Ollama
ollama serve

# Проверка порта
curl http://localhost:11434/api/tags
```

---

Это руководство обеспечивает полное понимание процесса конфигурации и развертывания RSecure, от установки до эксплуатации и обслуживания.
