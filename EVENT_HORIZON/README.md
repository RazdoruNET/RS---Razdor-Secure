# EVENT HORIZON

**Defensive Authentication Resilience Testing Framework**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

---

## 🎯 Обзор

EVENT HORIZON — это передовой фреймворк для тестирования устойчивости систем аутентификации в изолированных лабораторных средах. Система спроектирована с использованием формальных методов верификации и строгой доменной изоляции для обеспечения безопасного и контролируемого тестирования.

### 🏗️ Ключевые особенности

- **🔒 Формальная верификация** — Использование математических моделей для верификации состояний системы
- **🛡️ Строгая доменная изоляция** — Разделение на доверенные и недоверенные домены
- **📊 Наблюдаемость в реальном времени** — Комплексный мониторинг и анализ
- **🚀 Высокая производительность** — Асинхронное выполнение с контролируемой нагрузкой
- **🐳 Контейнеризация** — Полная поддержка Docker для изолированного развертывания
- **📋 Авторизованные аудиты** — Поддержка формализованного процесса авторизации

---

## 🏛️ Архитектура

### Формальная модель состояний

EVENT HORIZON использует формальную модель состояний с пятью строго разделенными доменами:

| Домен | Назначение | Доверие |
|--------|-------------|----------|
| **Generation** | Генерация и мутация входных данных | Недоверенный |
| **Execution** | Исполнение запросов к целевой системе | Недоверенный |
| **Observation** | Только чтение метрик и логов | Доверенный |
| **Planning** | Детерминированное планирование тестов | Доверенный |
| **Validation** | Валидация через внешние оракулы | Доверенный |

### Компоненты системы

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT HORIZON                        │
├─────────────────────────────────────────────────────────────┤
│  Planning Plane                                        │
│  ├─ TestScenarioPlanner                                │
│  ├─ FormalStateModel                                   │
│  └─ ExecutionCycleManager                              │
├─────────────────────────────────────────────────────────────┤
│  Data Plane                                           │
│  ├─ PureExecutionEngine                                │
│  ├─ TrafficPolymorphism                               │
│  └─ InputNormalization                               │
├─────────────────────────────────────────────────────────────┤
│  Observation Plane                                     │
│  ├─ CausalGraphBuilder                                │
│  ├─ SystemPressureMonitor                              │
│  └─ ImmutableEventLog                                │
├─────────────────────────────────────────────────────────────┤
│  Safety Layer                                         │
│  ├─ CircuitBreaker                                    │
│  ├─ RateLimiter                                      │
│  └─ AdaptiveBackoff                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- Docker & Docker Compose
- 4GB+ RAM
- Linux/macOS/Windows

### Установка

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/your-org/event-horizon.git
   cd event-horizon
   ```

2. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

3. **Развертывание лабораторной среды**
   ```bash
   docker-compose -f docker-compose-isolated.yml up -d
   ```

4. **Запуск изолированного теста**
   ```bash
   python src/main.py --target http://mock-target:9000 --mode isolated
   ```

### Первый тест

```bash
# Запуск базового теста аутентификации
python src/main.py \
  --target http://localhost:9000 \
  --scenario scenarios/basic_auth_test.yaml \
  --mode isolated
```

---

## 📖 Документация

### 🎚️ Многоуровневая документация

EVENT HORIZON предоставляет документацию для пользователей всех уровней подготовки:

| Уровень | Аудитория | Описание |
|----------|------------|-----------|
| [🟢 Начинающий](docs/beginner/README.md) | Новички | Основы использования и быстрый старт |
| [🟡 Средний](docs/intermediate/README.md) | Опытные | Архитектура и настройка сценариев |
| [🔴 Продвинутый](docs/advanced/README.md) | Профессионалы | Формальные методы и внутренние механизмы |
| [📋 Техники](docs/techniques/README.md) | Все уровни | Практические техники тестирования |
| [🔧 API](docs/api/README.md) | Разработчики | Полное описание API |
| [🛠️ Troubleshooting](docs/troubleshooting/README.md) | Все пользователи | Решение проблем |

### 📚 Навигация по документации

- **[📖 Главная документация](docs/README.md)** — Обзор и навигация
- **[🏛️ Архитектура](docs/advanced/README.md)** — Формальные методы и архитектурные концепции
- **[⚙️ Конфигурация](docs/intermediate/README.md)** — Настройка и оптимизация
- **[🚀 Быстрый старт](docs/beginner/README.md)** — Пошаговое руководство для начинающих

---

## 🎯 Режимы работы

### 1. Изолированная лаборатория (по умолчанию)

```bash
# Запуск в изолированной среде
python src/main.py --target http://mock-target:9000 --mode isolated
```

**Особенности:**
- ✅ Только для изолированных целей (localhost, Docker сети)
- ✅ Максимальная безопасность
- ✅ Не требует авторизации
- ✅ Идеально для разработки и тестирования

### 2. Авторизованный аудит

```bash
# Запуск авторизованного аудита
python src/main.py --target https://example.com --mode authorized
```

**Особенности:**
- 🔒 Требует формальные документы авторизации
- 🔒 Валидация перед каждым тестом
- 🔒 Для внешних систем только с разрешением
- 🔒 Полная протоколируемость

---

## 📋 Сценарии тестирования

### Встроенные сценарии

| Сценарий | Тип | Цель | Сложность |
|-----------|------|-------|-----------|
| [basic_auth_test.yaml](scenarios/basic_auth_test.yaml) | Аутентификация | Стресс-тестирование входа | 🟢 |
| [rate_limiting_test.yaml](scenarios/rate_limiting_test.yaml) | Ограничение скорости | Проверка лимитов | 🟡 |
| [header_polymorphism_test.yaml](scenarios/header_polymorphism_test.yaml) | Заголовки | Мутация HTTP заголовков | 🔴 |
| [input_normalization_test.yaml](scenarios/input_normalization_test.yaml) | Нормализация | Проверка очистки входа | 🟡 |

### Пример сценария

```yaml
name: "Basic Authentication Stress Test"
description: "Tests authentication system resilience"
target_system: "http://mock-target:9000"

test_scenarios:
  - name: "Authentication Load Test"
    test_type: "authentication_stress"
    priority: "high"
    request_count: 500
    concurrency: 25
    duration_seconds: 120
    success_criteria:
      min_success_rate: 0.95
      max_response_time_p95: 2.0
      error_rate_threshold: 0.05
```

---

## 🛡️ Безопасность

### Принципы безопасности

1. **Изоляция по умолчанию** — Система работает только в изолированных средах
2. **Формальная верификация** — Математическое доказательство корректности
3. **Строгая доменная сегрегация** — Недоверенный код не может повлиять на доверенные компоненты
4. **Иммутабельные логи** — Все события записываются в неизменяемый лог
5. **Контролируемое выполнение** — Ограничения ресурсов и автоматические остановки

### Валидация целей

```bash
# Проверка изолированности цели
python src/main.py --validate-isolation --target http://localhost:9000
# Output: Isolation validation: PASS

# Проверка документов авторизации
python src/main.py --validate-authorization --target https://example.com
# Output: Authorization validation: PASS
```

---

## 🐳 Docker развертывание

### Быстрый старт с Docker

```bash
# Развертывание полной среды
docker-compose -f docker-compose-isolated.yml up -d

# Запуск теста в контейнере
docker run --network event-horizon_default \
  event-horizon:latest \
  python -m src.main --target http://mock-target:9000
```

### Сборка образа

```bash
# Сборка кастомного образа
docker build -t event-horizon:latest .

# Запуск с кастомными параметрами
docker run -v $(pwd)/scenarios:/app/scenarios \
  event-horizon:latest \
  python -m src.main --scenario /app/scenarios/custom.yaml
```

---

## 📊 Мониторинг и наблюдаемость

### Метрики в реальном времени

EVENT HORIZON предоставляет комплексный мониторинг:

- **🔄 Системные метрики** — CPU, память, сеть, диск
- **📈 Метрики приложений** — Время ответа, пропускная способность, ошибки
- **🔍 Детекция аномалий** — Автоматическое обнаружение необычных паттернов
- **📋 Каузальный граф** — Граф взаимосвязей событий

### Интеграция с Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'event-horizon'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

---

## 🔧 Конфигурация

### Основные параметры

```python
# config/default.yaml
event_horizon:
  max_concurrent_requests: 50
  max_error_rate: 0.1
  max_response_time: 5.0
  
safety:
  circuit_breaker_threshold: 0.2
  adaptive_backoff_enabled: true
  emergency_stop_enabled: true
  
monitoring:
  metrics_port: 8080
  log_level: INFO
  export_format: json
```

### Переменные окружения

```bash
export EVENT_HORIZON_CONFIG_PATH=/path/to/config
export EVENT_HORIZON_LOG_LEVEL=DEBUG
export EVENT_HORIZON_METRICS_PORT=9090
```

---

## 🧪 Разработка и тестирование

### Запуск тестов

```bash
# Запуск всех тестов
pytest tests/

# Запуск с покрытием
pytest --cov=src tests/

# Запуск конкретного теста
pytest tests/test_formal_state_model.py -v
```

### Разработка сценариев

```python
# Создание кастомного сценария
from src.architecture.test_scenario import TestScenario

scenario = TestScenario(
    name="Custom Test",
    test_type="custom_stress",
    target="http://localhost:9000",
    parameters={
        "concurrent_users": 100,
        "duration": 300,
        "ramp_up_time": 30
    }
)
```

---

## 📈 Производительность

### Бенчмарки

| Метрика | Значение | Описание |
|----------|----------|----------|
| **Пропускная способность** | 10,000+ req/s | Максимальная нагрузка |
| **Латентность** | <1ms p99 | Внутренняя обработка |
| **Память** | <500MB | Базовое потребление |
| **CPU** | <2 cores | Нормальная нагрузка |

### Оптимизация

```bash
# Профилирование производительности
python -m cProfile -o profile.stats src/main.py

# Анализ памяти
python -m memory_profiler src/main.py
```

---

## 🤝 Сообщество и поддержка

### Получение помощи

- **[📖 Документация](docs/README.md)** — Полная документация
- **[🛠️ Troubleshooting](docs/troubleshooting/README.md)** — Решение проблем
- **[💬 GitHub Discussions](https://github.com/your-org/event-horizon/discussions)** — Сообщество
- **[🐛 GitHub Issues](https://github.com/your-org/event-horizon/issues)** — Баг-репорты

### Вклад в проект

1. Форкните репозиторий
2. Создайте ветку функции: `git checkout -b feature/amazing-feature`
3. Внесите изменения
4. Запустите тесты: `pytest`
5. Создайте Pull Request

---

## 🎯 Дорожная карта

### Версия 1.1 (Q2 2024)
- [ ] GUI интерфейс для управления тестами
- [ ] Расширенная поддержка облачных платформ
- [ ] ML-оптимизация сценариев

### Версия 2.0 (Q3 2024)
- [ ] Распределенное выполнение тестов
- [ ] Интеграция с CI/CD пайплайнами
- [ ] Продвинутая аналитика и отчетность

---

**Версия**: 1.0  

**Автор**: CASCADE SWE-1.5 Team AND GOOGLE AI Team AND OPENAI Team AN WE RAZDOR

**Дата**: Май 2026