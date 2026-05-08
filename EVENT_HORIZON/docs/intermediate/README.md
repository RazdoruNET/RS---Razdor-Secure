# EVENT HORIZON - Руководство среднего уровня

## 🎯 Для кого это руководство

Это руководство предназначено для пользователей, которые:
- Уже освоили базовые концепции EVENT HORIZON
- Понимают основы веб-безопасности
- Хотят настроить и оптимизировать тестирование
- Интересуются архитектурой системы

## 🏗️ Архитектурные концепции

### Разделение на плоскости (Planes)

EVENT HORIZON использует архитектуру с разделением на четыре плоскости:

#### 1. Control Plane (Плоскость управления)
- **Назначение**: Планирование и принятие решений
- **Компоненты**: DeterministicPlanner, ExecutionContract
- **Ключевая особенность**: Детерминированное поведение, неизменяемые контракты

#### 2. Data Plane (Плоскость данных)
- **Назначение**: Чистое выполнение запросов
- **Компоненты**: PureExecutionEngine, RequestPool
- **Ключевая особенность**: Никакой логики принятия решений, только выполнение

#### 3. Observation Plane (Плоскость наблюдения)
- **Назначение**: Сбор и анализ данных
- **Компоненты**: CausalGraphBuilder, SystemPressureMonitor
- **Ключевая особенность**: Read-only, не может влиять на систему

#### 4. Planning Plane (Плоскость планирования)
- **Назначение**: Создание тестовых планов
- **Компоненты**: TestPlanner, SystemConstraints
- **Ключевая особенность**: Внешняя валидация через Oracle

### Формальная модель состояния

Система использует формальную модель состояния для обеспечения безопасности:

```python
# Пример использования формальной модели состояния
from architecture.formal_state_model import FormalStateModel, DomainType

state_model = FormalStateModel(cycle_manager)
state = state_model.create_state(
    domain_states={DomainType.EXECUTION: {'status': 'active'}},
    resource_usage=ResourceCost(cpu_cycles=1000, memory_bytes=1024, ...)
)
```

**Преимущества:**
- Неизменяемость состояния (immutability)
- Формальная проверка переходов
- Контроль ресурсов
- Аудит всех изменений

## 🔧 Расширенная настройка

### Конфигурация сценариев тестов

Сценарии определяются в YAML-файлах в директории `scenarios/`:

```yaml
name: "Advanced Authentication Test"
success_criteria:
  min_success_rate: 0.95
  max_response_time_p95: 2.0
safety_limits:
  max_error_rate: 0.05
  max_concurrent_requests: 50
test_scenarios:
  - name: "stress_test"
    test_type: "authentication_stress"
    parameters:
      auth_methods: ["basic", "bearer"]
      concurrency: 50
```

### Настройка ресурсов

Ресурсы настраиваются в формальной модели состояния:

```python
# Настройка бюджетов ресурсов
resource_budgets = {
    'execution': ResourceBudget(
        max_cpu_cycles=2000000,
        max_memory_bytes=200 * 1024 * 1024,  # 200MB
        max_network_bytes=50 * 1024 * 1024,   # 50MB
        max_time_units=120.0
    )
}
```

### Настройка Oracle (внешняя валидация)

Oracle обеспечивает внешнюю валидацию решений:

```python
from architecture.external_oracle import ProductionMetricsOracle, OracleManager

oracle_config = {
    'type': 'production_metrics',
    'production_endpoint': 'https://metrics.example.com',
    'baselines': {
        'error_rate': 0.05,
        'response_time_p95': 2.0
    },
    'tolerance_threshold': 0.2
}

oracle = ProductionMetricsOracle(oracle_config)
oracle_manager = OracleManager({'primary': oracle_config})
```

## 🚀 Продвинутое использование

### Создание собственных сценариев

#### Шаг 1: Определите тип теста

```yaml
# scenarios/custom_test.yaml
name: "Custom Security Test"
test_type: "custom_vulnerability_scan"
target_endpoint: "https://target.example.com"
```

#### Шаг 2: Настройте параметры

```yaml
parameters:
  scan_depth: "medium"
  target_paths: ["/api/v1/users", "/api/v1/auth"]
  methods: ["GET", "POST", "PUT"]
```

#### Шаг 3: Определите критерии успеха

```yaml
success_criteria:
  no_critical_vulnerabilities: true
  response_time_p95: 3.0
  error_rate: 0.01
```

#### Шаг 4: Установите ограничения безопасности

```yaml
safety_limits:
  max_requests: 5000
  max_concurrent: 25
  rate_limit: 5  # запросов в секунду
  duration: 1800  # 30 минут
```

### Интеграция с CI/CD

#### GitHub Actions

```yaml
# .github/workflows/security-test.yml
name: Security Testing

on: [push, pull_request]

jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run security tests
        run: python -m src.main --target http://localhost:9000 --scenario scenarios/basic_auth_test.yaml
```

#### Docker Compose интеграция

```yaml
# docker-compose.yml
services:
  app:
    # ... конфигурация приложения
  
  security-test:
    build: .
    command: python -m src.main --target http://app:8080
    depends_on:
      - app
```

## 📊 Мониторинг и анализ

### Использование Prometheus

EVENT HORIZON экспортирует метрики в формате Prometheus:

```bash
# Доступ к метрикам
curl http://localhost:8080/metrics
```

**Основные метрики:**
- `event_horizon_requests_total` - общее количество запросов
- `event_horizon_request_duration_seconds` - время выполнения запросов
- `event_horizon_errors_total` - количество ошибок
- `event_horizon_active_requests` - количество активных запросов

### Настройка Grafana

1. Откройте Grafana: http://localhost:3000
2. Добавьте Prometheus как источник данных
3. Импортируйте дашборд из `docker/grafana/dashboards/`

### Анализ логов

Структурированные логи хранятся в JSON формате:

```bash
# Просмотр логов
cat logs/event_horizon.log | jq '.'
```

**Поля логов:**
- `timestamp` - время события
- `level` - уровень логирования
- `message` - сообщение
- `correlation_id` - ID корреляции
- `plane` - плоскость, где произошло событие
- `data` - дополнительные данные

## 🔒 Продвинутая безопасность

### Настройка инвариантов системы

Инварианты гарантируют соблюдение правил безопасности:

```python
from architecture.formal_state_model import SystemInvariant

def no_self_modification_invariant(state: SystemState) -> bool:
    """Проверяет, что система не модифицирует сама себя"""
    return state.get_domain_state(DomainType.CONTROL).get('self_modified', False)

invariant = SystemInvariant(
    invariant_id="no_self_modification",
    description="Система не должна модифицировать саму себя",
    domain=DomainType.CONTROL,
    validator=no_self_modification_invariant,
    violation_severity="critical"
)

state_model.add_invariant(invariant)
```

### Настройка границ доменов

Границы доменов контролируют, какие операции разрешены:

```python
from architecture.formal_state_model import DomainBoundary

execution_boundary = DomainBoundary(
    allowed_operations=[StateTransition.EXECUTE],
    allowed_data_types=['request_config', 'execution_result'],
    max_data_size=512 * 1024,  # 512KB
    read_only=False
)

state_model.domain_boundaries[DomainType.EXECUTION] = execution_boundary
```

### Валидация причинно-следственных связей

Causal Graph Builder отслеживает причинно-следственные связи:

```python
from architecture.observation_plane import CausalGraphBuilder, CausalEvent

causal_graph = CausalGraphBuilder(cycle_manager)

event = CausalEvent(
    event_id="event-001",
    timestamp=time.time(),
    event_type=EventType.REQUEST_START,
    plane=PlaneType.DATA,
    causation_id="parent-event-001",
    correlation_id="correlation-001",
    system_state={"cpu": 0.5, "memory": 0.3},
    data={"url": "https://example.com"}
)

await causal_graph.add_event(event)

# Анализ причинно-следственных связей
root_cause = await causal_graph.find_root_cause("event-001")
```

## 🐛 Отладка

### Включение детального логирования

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("EVENT_HORIZON")
```

### Трассировка выполнения

```python
# Включение трассировки
import sys
sys.settrace(lambda *args: None)  # Отключить
# Или используйте tracing библиотеки
```

### Анализ состояния системы

```python
# Получение текущего состояния
current_state = formal_state_model.current_state
print(current_state.to_dict())

# Проверка целостности состояния
integrity_report = formal_state_model.verify_state_integrity()
print(integrity_report)
```

## 📈 Оптимизация производительности

### Настройка пула соединений

```python
from architecture.async_engine.request_pool import RequestPool

request_pool = RequestPool(max_concurrent=100, timeout=30.0)
```

### Оптимизация rate limiting

```python
from architecture.async_engine.rate_limiter import RateLimiter

rate_limiter = RateLimiter(rate=10, burst=20)  # 10 req/s, burst 20
```

### Кэширование результатов

```python
# Используйте Redis для кэширования
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

## 🎓 Следующие шаги

После освоения среднего уровня:

1. Изучите [документацию профессионального уровня](../advanced/README.md)
2. Изучите [API reference](../api/README.md)
3. Изучите архитектурные ограничения
4. Разработайте собственные плагины

## 💡 Лучшие практики

1. **Всегда используйте изолированную среду** для начального тестирования
2. **Начинайте с консервативных лимитов** и увеличивайте постепенно
3. **Мониторируйте ресурсы** во время выполнения тестов
4. **Анализируйте логи** для понимания поведения системы
5. **Документируйте свои сценарии** для повторного использования

## 🔗 Полезные ресурсы

- [Архитектурные ограничения](../../ARCHITECTURAL_ROOT_CAUSE.md)
- [Протокол авторизации](../../AUTHORIZATION_PROTOCOL.md)
- [Примеры сценариев](../../scenarios/)
- [API документация](../api/README.md)
