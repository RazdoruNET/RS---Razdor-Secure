# EVENT HORIZON - API Reference

## 📚 Обзор API

EVENT HORIZON предоставляет несколько уровней API:
- **Command Line Interface (CLI)** - командная строка
- **Python API** - программный интерфейс на Python
- **REST API** - HTTP интерфейс
- **Configuration API** - конфигурационный интерфейс

## 🔧 Command Line Interface (CLI)

### Основные команды

#### Запуск изолированного теста
```bash
python -m src.main --target http://mock-target:9000
```

**Параметры:**
- `--target` - целевой URL (обязательно)
- `--scenario` - путь к файлу сценария (опционально)
- `--mode` - режим выполнения (isolated/authorized)
- `--validate-isolation` - валидация изолированной среды
- `--validate-authorization` - валидация авторизации
- `--authorization-dir` - директория с документами авторизации

#### Примеры использования

```bash
# Базовый запуск
python -m src.main --target http://localhost:9000

# Со сценарием
python -m src.main --target http://localhost:9000 --scenario scenarios/basic_auth_test.yaml

# Авторизованный аудит
python -m src.main --mode authorized --target https://example.com

# Валидация авторизации
python -m src.main --validate-authorization --target https://example.com
```

## 🐍 Python API

### Основные модули

#### architecture.formal_state_model

**FormalStateModel**
```python
from architecture.formal_state_model import FormalStateModel, DomainType, StateTransition

# Инициализация
cycle_manager = ExecutionCycleManager()
state_model = FormalStateModel(cycle_manager)

# Создание состояния
state = state_model.create_state(
    domain_states={DomainType.EXECUTION: {'status': 'active'}},
    resource_usage=ResourceCost(cpu_cycles=1000, memory_bytes=1024, ...)
)

# Переход состояния
new_state = state_model.transition_state(
    transition_type=StateTransition.EXECUTE,
    domain=DomainType.EXECUTION,
    data={'request_id': 'req-001'},
    actor_id='actor-001',
    resource_cost=ResourceCost(cpu_cycles=500, memory_bytes=512, ...)
)

# Валидация инвариантов
invariant = SystemInvariant(
    invariant_id="no_self_modification",
    description="Система не должна модифицировать саму себя",
    domain=DomainType.CONTROL,
    validator=lambda state: True,
    violation_severity="critical"
)
state_model.add_invariant(invariant)
```

**Методы:**
- `add_invariant(invariant: SystemInvariant) -> str` - добавление инварианта
- `create_state(domain_states, resource_usage) -> SystemState` - создание состояния
- `transition_state(transition_type, domain, data, actor_id, resource_cost) -> SystemState` - переход состояния
- `validate_transition(...)` - валидация перехода
- `get_state_history(...)` - получение истории состояний
- `verify_state_integrity() -> Dict` - верификация целостности состояния
- `export_state_model(filename)` - экспорт модели состояния

#### architecture.control_plane

**TestScenarioPlanner**
```python
from architecture.control_plane import TestScenarioPlanner

# Инициализация
planner = TestScenarioPlanner(cycle_manager, event_log, oracle)

# Создание контракта
contract = await planner.create_execution_contract(
    requirements={'test_types': ['authentication_stress'], 'target_system': 'http://target'},
    constraints=SystemConstraints(...)
)

# Валидация контракта
is_valid = await planner.validate_contract(contract)
```

#### architecture.data_plane

**PureExecutionEngine**
```python
from architecture.data_plane import PureExecutionEngine, RequestContext

# Инициализация
engine = PureExecutionEngine(cycle_manager, backpressure_controller)

# Выполнение запроса
context = RequestContext(
    request_id='req-001',
    execution_contract_id='contract-001',
    timestamp=time.time(),
    backpressure_level=0.0
)

result = await engine.execute_validated_request(context, request_data)

# Пакетное выполнение
results = await engine.execute_batch(requests)
```

#### architecture.observation_plane

**CausalGraphBuilder**
```python
from architecture.observation_plane import CausalGraphBuilder, CausalEvent, EventType

# Инициализация
causal_graph = CausalGraphBuilder(cycle_manager)

# Добавление события
event = CausalEvent(
    event_id='event-001',
    timestamp=time.time(),
    event_type=EventType.REQUEST_START,
    plane=PlaneType.DATA,
    causation_id='parent-event-001',
    correlation_id='corr-001',
    system_state={'cpu': 0.5},
    data={'url': 'https://example.com'}
)

await causal_graph.add_event(event)

# Анализ причинно-следственных связей
root_cause = await causal_graph.find_root_cause('event-001')
patterns = await causal_graph.analyze_event_patterns()
anomalies = await causal_graph.detect_anomalies()
```

**SystemPressureMonitor**
```python
from architecture.observation_plane import SystemPressureMonitor

# Инициализация
monitor = SystemPressureMonitor(cycle_manager)

# Запись давления
await monitor.record_pressure_reading({
    'cpu_saturation': 0.7,
    'memory_pressure': 0.5,
    'event_loop_latency': 0.1
})

# Получение текущего давления
current = monitor.get_current_pressure()

# Анализ трендов
trends = monitor.get_pressure_trends(window_minutes=30)
```

#### architecture.immutable_log

**ImmutableEventLog**
```python
from architecture.immutable_log import ImmutableEventLog, EventType

# Инициализация
event_log = ImmutableEventLog('./data/events')
await event_log.initialize()

# Добавление события
event = await event_log.append(
    event_type=EventType.CONTRACT_CREATED,
    plane='control',
    data={'contract_id': 'contract-001'}
)

# Replay событий
stream = await event_log.replay(from_timestamp=0.0)
async for event in stream:
    print(event)

# Верификация целостности
integrity = await event_log.verify_chain_integrity()
```

#### architecture.external_oracle

**ProductionMetricsOracle**
```python
from architecture.external_oracle import ProductionMetricsOracle, OracleManager

# Инициализация
oracle_config = {
    'type': 'production_metrics',
    'production_endpoint': 'https://metrics.example.com',
    'baselines': {'error_rate': 0.05, 'response_time_p95': 2.0},
    'tolerance_threshold': 0.2
}

oracle = ProductionMetricsOracle(oracle_config)

# Валидация контракта
result = await oracle.validate_contract(contract)

# Получение ground truth
ground_truth = await oracle.get_ground_truth('error_rate')
```

**OracleManager**
```python
# Инициализация с несколькими oracle
manager = OracleManager({
    'primary': {'type': 'production_metrics', ...},
    'secondary': {'type': 'manual_verification', ...}
})

# Валидация с основным oracle
result = await manager.validate_contract(contract)

# Валидация со всеми oracle
results = await manager.validate_with_all_oracles(contract)
```

#### authorized_audit

**AuthorizedAuditOrchestrator**
```python
from authorized_audit import AuthorizedAuditOrchestrator

# Инициализация
orchestrator = AuthorizedAuditOrchestrator('./authorization')

# Запуск авторизованного аудита
report = await orchestrator.run_authorized_audit(
    target_url='https://example.com',
    scenario_file='scenarios/authorized_test.yaml'
)
```

**AuthorizationValidator**
```python
from authorized_audit import AuthorizationValidator

# Инициализация
validator = AuthorizationValidator('./authorization')

# Валидация авторизации
authorization = validator.validate_authorization('https://example.com')

# Генерация шаблона авторизации
template = validator.generate_authorization_template('https://example.com')
```

## 🌐 REST API

### Endpoints

#### POST /api/v1/execute
Выполнение теста.

**Request:**
```json
{
  "target_url": "https://example.com",
  "test_type": "authentication_stress",
  "parameters": {
    "concurrency": 50,
    "duration": 300
  }
}
```

**Response:**
```json
{
  "execution_id": "exec-001",
  "status": "completed",
  "results": {
    "total_requests": 1000,
    "success_rate": 0.95,
    "error_rate": 0.05
  }
}
```

#### GET /api/v1/status
Статус системы.

**Response:**
```json
{
  "status": "healthy",
  "active_requests": 10,
  "system_pressure": 0.3,
  "uptime": 3600
}
```

#### GET /api/v1/metrics
Метрики в формате Prometheus.

**Response:**
```
event_horizon_requests_total 1000
event_horizon_request_duration_seconds_sum 150.5
event_horizon_errors_total 50
```

#### POST /api/v1/authorize
Валидация авторизации.

**Request:**
```json
{
  "target_url": "https://example.com",
  "authorization_data": {...}
}
```

**Response:**
```json
{
  "valid": true,
  "authorization_id": "AUTH-001",
  "status": "verified"
}
```

## 📝 Configuration API

### YAML Configuration

**Основной конфигурационный файл** (`config/event_horizon.yaml`):

```yaml
system:
  mode: "isolated"  # isolated | authorized
  log_level: "INFO"

execution:
  max_concurrent_requests: 100
  max_request_timeout: 30.0
  rate_limit: 10.0

safety:
  max_error_rate: 0.1
  max_response_time_p95: 5.0
  circuit_breaker_threshold: 0.2

observability:
  prometheus_port: 8080
  grafana_enabled: true
  log_retention_days: 7

resources:
  max_cpu_usage: 0.8
  max_memory_usage: 0.7
  max_network_bandwidth: 1000000000  # 1 Gbps
```

### Environment Variables

```bash
EVENT_HORIZON_MODE=isolated
EVENT_HORIZON_LOG_LEVEL=INFO
EVENT_HORIZON_TARGET_URL=http://localhost:9000
EVENT_HORIZON_PROMETHEUS_PORT=8080
EVENT_HORIZON_REDIS_URL=redis://localhost:6379
```

## 🔒 Error Codes

| Код | Описание | Решение |
|-----|----------|---------|
| AUTH-001 | Отсутствует авторизация | Предоставьте документы авторизации |
| AUTH-002 | Авторизация просрочена | Обновите авторизацию |
| AUTH-003 | Цель не в области действия | Проверьте authorised_targets.txt |
| SAFE-001 | Превышен лимит ресурсов | Уменьшите нагрузку |
| SAFE-002 | Уровень ошибок слишком высок | Остановите тест и проверьте систему |
| SAFE-003 | Превышено время выполнения | Уменьшите длительность теста |
| INV-001 | Нарушен инвариант | Проверьте системное состояние |
| INV-002 | Недопустимый переход состояния | Проверьте логику переходов |
| ISO-001 | Цель не изолирована | Используйте изолированную среду |

## 📊 Data Structures

### SystemState
```python
@dataclass(frozen=True)
class SystemState:
    state_hash: str
    timestamp: float
    domain_states: Dict[DomainType, Dict[str, Any]]
    resource_usage: ResourceCost
    active_transitions: List[str]
    invariants: List[str]
```

### ExecutionContract
```python
@dataclass(frozen=True)
class ExecutionContract:
    contract_id: str
    created_at: float
    input_hash: str
    deterministic_seed: int
    constraints_hash: str
    execution_plan: Dict[str, Any]
    expected_invariants: List[str]
    oracle_validation_required: bool
```

### ResourceCost
```python
@dataclass(frozen=True)
class ResourceCost:
    cpu_cycles: int
    memory_bytes: int
    network_bytes: int
    time_units: float
    io_operations: int
```

### CausalEvent
```python
@dataclass(frozen=True)
class CausalEvent:
    event_id: str
    timestamp: float
    event_type: EventType
    plane: PlaneType
    causation_id: Optional[str]
    correlation_id: str
    system_state: Dict[str, Any]
    data: Dict[str, Any]
```

## 🔗 Примеры использования

### Полный рабочий пример

```python
import asyncio
from architecture.formal_state_model import FormalStateModel
from architecture.core_constraints import ExecutionCycleManager
from architecture.control_plane import TestScenarioPlanner

async def main():
    # Инициализация
    cycle_manager = ExecutionCycleManager()
    state_model = FormalStateModel(cycle_manager)
    
    # Создание контракта
    planner = TestScenarioPlanner(cycle_manager, event_log, oracle)
    contract = await planner.create_execution_contract(requirements, constraints)
    
    # Валидация
    is_valid = await planner.validate_contract(contract)
    
    # Выполнение
    engine = PureExecutionEngine(cycle_manager, backpressure_controller)
    results = await engine.execute_batch(requests)
    
    # Анализ
    causal_graph = CausalGraphBuilder(cycle_manager)
    root_cause = await causal_graph.find_root_cause(event_id)

asyncio.run(main())
```

## 📞 Поддержка API

Для вопросов по API:
- Документация: `docs/api/`
- Примеры: `examples/`
- GitHub Issues: для баг-репортов
