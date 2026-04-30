# REST API Documentation

## Обзор

RSecure REST API предоставляет программный интерфейс для доступа к функциям безопасности системы. API поддерживает управление всеми основными компонентами, включая мониторинг, анализ, детекцию угроз и генерацию отчетов.

## Базовая информация

- **Base URL**: `http://localhost:8080/api/v1`
- **Authentication**: API Key (Header: `X-API-Key`)
- **Content-Type**: `application/json`
- **Rate Limit**: 100 запросов в минуту

## Аутентификация

### API Key

```bash
curl -H "X-API-Key: your-api-key-here" \
     http://localhost:8080/api/v1/status
```

### Получение API Key

```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "secure_password"}' \
     http://localhost:8080/api/v1/auth/login
```

**Response:**
```json
{
  "status": "success",
  "api_key": "rs_1234567890abcdef",
  "expires_in": 86400
}
```

## Эндпоинты

### Системный статус

#### GET /status

Получение текущего статуса системы RSecure.

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8080/api/v1/status
```

**Response:**
```json
{
  "status": "running",
  "version": "1.0.0",
  "uptime": 86400,
  "components": {
    "neural_core": "active",
    "reinforcement_learning": "active",
    "network_defense": "active",
    "phishing_detector": "active",
    "system_monitoring": "active"
  },
  "metrics": {
    "events_processed": 15000,
    "threats_detected": 250,
    "actions_taken": 180
  }
}
```

### Мониторинг

#### GET /monitoring/system

Получение системных метрик.

**Параметры:**
- `interval` (optional): Интервал в минутах (по умолчанию: 5)

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8080/api/v1/monitoring/system?interval=10"
```

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "system_resources": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 30.1,
    "load_average": [1.2, 1.5, 1.8]
  },
  "network": {
    "active_connections": 25,
    "bytes_sent": 1048576,
    "bytes_received": 2097152
  },
  "processes": {
    "total": 150,
    "running": 120,
    "suspicious": 2
  }
}
```

#### GET /monitoring/events

Получение событий мониторинга.

**Параметры:**
- `limit` (optional): Количество событий (по умолчанию: 100)
- `severity` (optional): Фильтр по серьезности (low, medium, high, critical)
- `event_type` (optional): Тип события

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8080/api/v1/monitoring/events?limit=50&severity=high"
```

**Response:**
```json
{
  "total_events": 1500,
  "events": [
    {
      "id": 12345,
      "timestamp": "2024-01-01T12:00:00Z",
      "event_type": "network_connection",
      "severity": "high",
      "source": "network_defense",
      "description": "Suspicious connection from 192.168.1.100",
      "details": {
        "source_ip": "192.168.1.100",
        "target_port": 22,
        "protocol": "TCP"
      }
    }
  ]
}
```

### Детекция угроз

#### GET /detection/threats

Получение списка обнаруженных угроз.

**Параметры:**
- `active_only` (optional): Только активные угрозы (true/false)
- `threat_type` (optional): Тип угрозы
- `limit` (optional): Количество угроз (по умолчанию: 100)

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8080/api/v1/detection/threats?active_only=true"
```

**Response:**
```json
{
  "total_threats": 25,
  "active_threats": 8,
  "threats": [
    {
      "id": "threat_001",
      "threat_type": "network_intrusion",
      "severity": "high",
      "confidence": 0.85,
      "status": "active",
      "source_ip": "192.168.1.100",
      "first_seen": "2024-01-01T12:00:00Z",
      "last_seen": "2024-01-01T12:15:00Z",
      "indicators": ["port_scan", "brute_force"],
      "actions_taken": ["ip_blocked"]
    }
  ]
}
```

#### POST /detection/analyze

Анализ события на предмет угроз.

**Request Body:**
```json
{
  "event_type": "network_connection",
  "data": {
    "source_ip": "192.168.1.100",
    "target_port": 22,
    "protocol": "TCP",
    "payload_size": 1024
  },
  "context": {
    "timestamp": "2024-01-01T12:00:00Z",
    "user_agent": "Mozilla/5.0...",
    "referrer": "https://example.com"
  }
}
```

**Пример запроса:**
```bash
curl -X POST \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d @event.json \
     http://localhost:8080/api/v1/detection/analyze
```

**Response:**
```json
{
  "analysis_id": "analysis_12345",
  "threat_assessment": {
    "is_threat": true,
    "threat_type": "network_intrusion",
    "severity": "high",
    "confidence": 0.82,
    "risk_score": 0.78
  },
  "indicators": [
    {
      "type": "port_scan",
      "confidence": 0.9,
      "description": "Multiple port access attempts"
    }
  ],
  "recommendations": [
    "Block source IP",
    "Increase monitoring",
    "Investigate further"
  ]
}
```

### Защита

#### GET /defense/rules

Получение правил защиты.

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8080/api/v1/defense/rules
```

**Response:**
```json
{
  "total_rules": 15,
  "rules": [
    {
      "id": "rule_001",
      "name": "Port Scan Detection",
      "type": "port_scan",
      "enabled": true,
      "threshold": 10,
      "action": "block_ip",
      "severity": "medium",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### POST /defense/rules

Создание нового правила защиты.

**Request Body:**
```json
{
  "name": "Custom Port Scan Rule",
  "type": "port_scan",
  "condition": {
    "threshold": 5,
    "time_window": 60
  },
  "action": "block_ip",
  "severity": "high",
  "enabled": true
}
```

**Пример запроса:**
```bash
curl -X POST \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d @rule.json \
     http://localhost:8080/api/v1/defense/rules
```

**Response:**
```json
{
  "status": "success",
  "rule_id": "rule_016",
  "message": "Rule created successfully"
}
```

#### PUT /defense/rules/{rule_id}

Обновление существующего правила.

**Пример запроса:**
```bash
curl -X PUT \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"enabled": false}' \
     http://localhost:8080/api/v1/defense/rules/rule_001
```

#### DELETE /defense/rules/{rule_id}

Удаление правила защиты.

**Пример запроса:**
```bash
curl -X DELETE \
     -H "X-API-Key: your-api-key" \
     http://localhost:8080/api/v1/defense/rules/rule_001
```

### Аналитика

#### GET /analytics/trends

Получение трендов безопасности.

**Параметры:**
- `period` (optional): Период (1h, 24h, 7d, 30d)
- `metric` (optional): Метрика (events, threats, severity)

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8080/api/v1/analytics/trends?period=24h"
```

**Response:**
```json
{
  "period": "24h",
  "trends": {
    "events": {
      "total": 1500,
      "hourly": [
        {"hour": "00:00", "count": 45},
        {"hour": "01:00", "count": 52}
      ],
      "trend_direction": "increasing",
      "trend_slope": 0.15
    },
    "threats": {
      "total": 25,
      "by_type": {
        "network_intrusion": 10,
        "phishing": 8,
        "malware": 7
      }
    }
  }
}
```

#### GET /analytics/reports

Получение списка отчетов.

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8080/api/v1/analytics/reports
```

**Response:**
```json
{
  "reports": [
    {
      "id": "report_001",
      "type": "comprehensive",
      "generated_at": "2024-01-01T12:00:00Z",
      "period": "24h",
      "format": "html",
      "download_url": "/api/v1/analytics/reports/report_001/download"
    }
  ]
}
```

#### POST /analytics/reports

Генерация нового отчета.

**Request Body:**
```json
{
  "type": "comprehensive",
  "period": "24h",
  "format": "html",
  "include_sections": [
    "summary",
    "trends",
    "threats",
    "recommendations"
  ]
}
```

**Пример запроса:**
```bash
curl -X POST \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d @report_request.json \
     http://localhost:8080/api/v1/analytics/reports
```

**Response:**
```json
{
  "report_id": "report_002",
  "status": "generating",
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

### Neural Core

#### GET /neural/status

Получение статуса нейросетевого ядра.

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8080/api/v1/neural/status
```

**Response:**
```json
{
  "status": "active",
  "models_loaded": true,
  "active_models": [
    "network_traffic_analyzer",
    "process_behavior_detector",
    "file_integrity_checker",
    "system_state_monitor"
  ],
  "performance": {
    "predictions_per_second": 150,
    "average_confidence": 0.78,
    "model_accuracy": 0.85
  }
}
```

#### POST /neural/predict

Получение предсказания от нейросети.

**Request Body:**
```json
{
  "data_type": "network",
  "features": [0.1, 0.2, 0.3, 0.4, 0.5],
  "context": {
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "network_monitor"
  }
}
```

**Пример запроса:**
```bash
curl -X POST \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d @prediction.json \
     http://localhost:8080/api/v1/neural/predict
```

**Response:**
```json
{
  "prediction_id": "pred_12345",
  "threat_probability": 0.75,
  "confidence": 0.82,
  "threat_type": "network_intrusion",
  "risk_factors": [
    "unusual_port_access",
    "high_connection_frequency"
  ],
  "recommendations": [
    "Monitor source IP",
    "Increase logging"
  ]
}
```

### Reinforcement Learning

#### GET /rl/status

Получение статуса RL агента.

**Пример запроса:**
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8080/api/v1/rl/status
```

**Response:**
```json
{
  "status": "training",
  "episodes_completed": 1500,
  "current_epsilon": 0.15,
  "average_reward": 0.75,
  "model_performance": {
    "accuracy": 0.82,
    "precision": 0.78,
    "recall": 0.85
  }
}
```

#### POST /rl/action

Получение рекомендованного действия.

**Request Body:**
```json
{
  "state": {
    "threat_level": 0.8,
    "system_load": 0.3,
    "active_threats": 5,
    "available_resources": 0.9
  },
  "context": {
    "timestamp": "2024-01-01T12:00:00Z",
    "threat_type": "network_intrusion"
  }
}
```

**Пример запроса:**
```bash
curl -X POST \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d @action_request.json \
     http://localhost:8080/api/v1/rl/action
```

**Response:**
```json
{
  "action_id": "action_001",
  "recommended_action": "block_ip",
  "confidence": 0.85,
  "expected_outcome": {
    "threat_reduction": 0.9,
    "system_impact": 0.2,
    "false_positive_risk": 0.1
  },
  "alternative_actions": [
    {
      "action": "monitor_and_alert",
      "confidence": 0.65,
      "expected_outcome": {
        "threat_reduction": 0.3,
        "system_impact": 0.05
      }
    }
  ]
}
```

## WebSocket API

### Подключение

```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/ws');
ws.onopen = function() {
    // Аутентификация
    ws.send(JSON.stringify({
        type: 'auth',
        api_key: 'your-api-key'
    }));
};
```

### Поток событий

```javascript
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'security_event') {
        console.log('Security event:', data.event);
    }
};
```

### Подписка на события

```javascript
// Подписка на события мониторинга
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['monitoring', 'threats', 'alerts']
}));
```

## Коды ошибок

| Код | Описание | Решение |
|-----|-----------|---------|
| 200 | OK | Успешный запрос |
| 201 | Created | Ресурс создан |
| 400 | Bad Request | Неверный формат запроса |
| 401 | Unauthorized | Неверный API ключ |
| 403 | Forbidden | Недостаточно прав |
| 404 | Not Found | Ресурс не найден |
| 429 | Too Many Requests | Превышен лимит запросов |
| 500 | Internal Server Error | Внутренняя ошибка сервера |

## Примеры использования

### Python

```python
import requests

# Аутентификация
auth_response = requests.post(
    'http://localhost:8080/api/v1/auth/login',
    json={'username': 'admin', 'password': 'secure_password'}
)
api_key = auth_response.json()['api_key']

headers = {'X-API-Key': api_key}

# Получение статуса
status = requests.get(
    'http://localhost:8080/api/v1/status',
    headers=headers
)
print(status.json())

# Анализ события
event_data = {
    'event_type': 'network_connection',
    'data': {
        'source_ip': '192.168.1.100',
        'target_port': 22,
        'protocol': 'TCP'
    }
}

analysis = requests.post(
    'http://localhost:8080/api/v1/detection/analyze',
    json=event_data,
    headers=headers
)
print(analysis.json())
```

### JavaScript

```javascript
// Аутентификация
const authResponse = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'admin',
        password: 'secure_password'
    })
});
const {api_key} = await authResponse.json();

// Получение статуса
const status = await fetch('/api/v1/status', {
    headers: {'X-API-Key': api_key}
});
const statusData = await status.json();
console.log(statusData);

// WebSocket подключение
const ws = new WebSocket('ws://localhost:8080/api/v1/ws');
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'auth',
        api_key: api_key,
        subscribe: ['threats', 'alerts']
    }));
};
```

### Bash

```bash
#!/bin/bash

# Получение API ключа
API_KEY=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "secure_password"}' \
    http://localhost:8080/api/v1/auth/login | \
    jq -r '.api_key')

# Получение статуса
curl -s -H "X-API-Key: $API_KEY" \
    http://localhost:8080/api/v1/status | \
    jq '.components'

# Получение активных угроз
curl -s -H "X-API-Key: $API_KEY" \
    "http://localhost:8080/api/v1/detection/threats?active_only=true" | \
    jq '.threats[] | {threat_type, severity, source_ip}'
```

## Ограничения

- **Rate Limit**: 100 запросов в минуту
- **Payload Size**: Максимум 10MB
- **WebSocket Connections**: Максимум 10 одновременных подключений
- **Report Generation**: Максимум 5 отчетов в час

## Версионирование

API использует семантическое версионирование:

- **v1.0.x**: Стабильная версия с обратной совместимостью
- **v1.1.x**: Новые функции с обратной совместимостью
- **v2.0.x**: Крупные изменения без обратной совместимости

## Поддержка

Для получения поддержки по API:
- Документация: `http://localhost:8080/docs/api`
- Примеры: `http://localhost:8080/docs/examples`
- Тестирование: `http://localhost:8080/api/v1/test`

---

RSecure REST API предоставляет полный программный доступ ко всем функциям системы безопасности, позволяя интегрировать RSecure в существующие системы автоматизации и мониторинга.
