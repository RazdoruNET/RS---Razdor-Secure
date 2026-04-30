# Python API Documentation

## Обзор

RSecure Python API предоставляет программный интерфейс для интеграции функций безопасности RSecure в Python приложения. API включает все основные компоненты: нейросетевое ядро, обучение с подкреплением, детекцию угроз, защиту и аналитику.

## Установка

```bash
pip install rsecure-api
```

## Базовая настройка

```python
from rsecure import RSecureClient

# Создание клиента
client = RSecureClient(
    api_url="http://localhost:8080",
    api_key="your-api-key-here"
)

# Проверка соединения
status = client.get_status()
print(f"RSecure status: {status['status']}")
```

## Основные компоненты

### RSecureClient

Основной класс для взаимодействия с RSecure.

```python
class RSecureClient:
    def __init__(self, api_url: str, api_key: str, timeout: int = 30):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'X-API-Key': api_key})
```

### Контекст менеджер

```python
from rsecure import RSecureClient

# Использование контекст менеджера
with RSecureClient("http://localhost:8080", "api-key") as client:
    status = client.get_status()
    threats = client.get_threats()
    print(f"Active threats: {len(threats)}")
```

## Мониторинг

### Системный мониторинг

```python
# Получение системных метрик
metrics = client.get_system_metrics(interval=5)
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_percent']}%")

# Получение событий мониторинга
events = client.get_monitoring_events(
    limit=100,
    severity="high"
)

for event in events:
    print(f"Event: {event['event_type']} - {event['severity']}")
```

### Потоковый мониторинг

```python
# Потоковый мониторинг событий
for event in client.stream_events():
    if event['severity'] == 'critical':
        print(f"Critical event: {event['description']}")
        # Обработка критического события
        handle_critical_event(event)
```

### Callback функции

```python
# Установка callback для событий
def on_security_event(event):
    """Обработчик событий безопасности"""
    if event['threat_score'] > 0.8:
        send_alert(event)

client.set_event_callback(on_security_event)

# Начало мониторинга
client.start_monitoring()
```

## Детекция угроз

### Анализ событий

```python
# Анализ сетевого события
network_event = {
    'event_type': 'network_connection',
    'data': {
        'source_ip': '192.168.1.100',
        'target_port': 22,
        'protocol': 'TCP',
        'payload_size': 1024
    },
    'context': {
        'timestamp': '2024-01-01T12:00:00Z',
        'user_agent': 'Mozilla/5.0...'
    }
}

analysis = client.analyze_event(network_event)
if analysis['threat_assessment']['is_threat']:
    print(f"Threat detected: {analysis['threat_assessment']['threat_type']}")
    print(f"Confidence: {analysis['threat_assessment']['confidence']}")
```

### Пакетный анализ

```python
# Анализ множественных событий
events = [
    {'event_type': 'network_connection', 'data': {...}},
    {'event_type': 'process_start', 'data': {...}},
    {'event_type': 'file_access', 'data': {...}}
]

results = client.analyze_events_batch(events)
for result in results:
    if result['threat_assessment']['is_threat']:
        print(f"Threat in event {result['analysis_id']}")
```

### Фишинг детекция

```python
# Анализ URL на фишинг
url_analysis = client.analyze_url(
    url="https://secure-paypal.com/login",
    context={
        'user_agent': 'Mozilla/5.0...',
        'referrer': 'email'
    }
)

if url_analysis['threat_type'] != 'safe':
    print(f"Phishing detected: {url_analysis['threat_type']}")
    print(f"Confidence: {url_analysis['confidence']}")
```

## Защита

### Управление правилами

```python
# Получение правил защиты
rules = client.get_defense_rules()
for rule in rules:
    print(f"Rule: {rule['name']} - {rule['action']}")

# Создание нового правила
new_rule = {
    'name': 'Custom Port Scan Rule',
    'type': 'port_scan',
    'condition': {
        'threshold': 5,
        'time_window': 60
    },
    'action': 'block_ip',
    'severity': 'high',
    'enabled': True
}

rule_id = client.create_defense_rule(new_rule)
print(f"Rule created: {rule_id}")
```

### Блокировка IP

```python
# Блокировка IP адреса
client.block_ip(
    ip="192.168.1.100",
    reason="Port scanning detected",
    duration=3600  # 1 час
)

# Разблокировка IP
client.unblock_ip("192.168.1.100")

# Получение списка заблокированных IP
blocked_ips = client.get_blocked_ips()
print(f"Blocked IPs: {blocked_ips}")
```

### Honeypot управление

```python
# Настройка honeypot
client.configure_honeypot(
    enabled=True,
    ports=[8080, 8888, 9999],
    log_connections=True
)

# Получение honeypot логов
honeypot_logs = client.get_honeypot_logs(limit=50)
for log in honeypot_logs:
    print(f"Honeypot hit from {log['source_ip']}")
```

## Нейросетевое ядро

### Предсказания

```python
# Получение предсказания от нейросети
prediction = client.neural_predict(
    data_type="network",
    features=[0.1, 0.2, 0.3, 0.4, 0.5],
    context={
        'timestamp': '2024-01-01T12:00:00Z',
        'source': 'network_monitor'
    }
)

print(f"Threat probability: {prediction['threat_probability']}")
print(f"Confidence: {prediction['confidence']}")
print(f"Risk factors: {prediction['risk_factors']}")
```

### Обучение моделей

```python
# Обучение нейросети на новых данных
training_data = [
    {'features': [0.1, 0.2, 0.3], 'label': 0},
    {'features': [0.8, 0.9, 0.7], 'label': 1}
]

training_result = client.train_neural_model(
    model_type="network_analyzer",
    training_data=training_data,
    epochs=100
)

print(f"Training completed: {training_result['accuracy']}")
```

### Модель информация

```python
# Получение информации о моделях
models_info = client.get_neural_models()
for model in models_info:
    print(f"Model: {model['name']}")
    print(f"Type: {model['type']}")
    print(f"Accuracy: {model['accuracy']}")
    print(f"Status: {model['status']}")
```

## Обучение с подкреплением

### Получение действий

```python
# Получение рекомендованного действия
state = {
    'threat_level': 0.8,
    'system_load': 0.3,
    'active_threats': 5,
    'available_resources': 0.9
}

action = client.get_rl_action(
    state=state,
    context={
        'threat_type': 'network_intrusion',
        'urgency': 'high'
    }
)

print(f"Recommended action: {action['recommended_action']}")
print(f"Confidence: {action['confidence']}")
print(f"Expected outcome: {action['expected_outcome']}")
```

### Обучение RL агента

```python
# Обучение RL агента на опыте
experience = {
    'state': state,
    'action': 'block_ip',
    'reward': 0.8,
    'next_state': next_state,
    'done': False
}

training_result = client.train_rl_agent(
    experiences=[experience],
    episodes=100
)

print(f"Training completed: {training_result['average_reward']}")
```

### RL статистика

```python
# Получение статистики RL агента
rl_stats = client.get_rl_statistics()
print(f"Episodes completed: {rl_stats['episodes_completed']}")
print(f"Current epsilon: {rl_stats['current_epsilon']}")
print(f"Average reward: {rl_stats['average_reward']}")
```

## Аналитика

### Тренды

```python
# Получение трендов
trends = client.get_analytics_trends(period="24h")
print(f"Total events: {trends['events']['total']}")
print(f"Trend direction: {trends['events']['trend_direction']}")

# Визуализация трендов
import matplotlib.pyplot as plt

hours = [item['hour'] for item in trends['events']['hourly']]
counts = [item['count'] for item in trends['events']['hourly']]

plt.plot(hours, counts)
plt.title('Security Events Trend (24h)')
plt.xlabel('Hour')
plt.ylabel('Event Count')
plt.show()
```

### Отчеты

```python
# Генерация отчета
report_request = {
    'type': 'comprehensive',
    'period': '24h',
    'format': 'html',
    'include_sections': ['summary', 'trends', 'threats']
}

report_id = client.generate_report(report_request)
print(f"Report generating: {report_id}")

# Проверка статуса отчета
report_status = client.get_report_status(report_id)
if report_status['status'] == 'completed':
    # Скачивание отчета
    report_content = client.download_report(report_id)
    with open(f"report_{report_id}.html", 'w') as f:
        f.write(report_content)
```

### Угрозовая разведка

```python
# Обновление угрозовой разведки
threat_intel = {
    'indicator': '192.168.1.100',
    'indicator_type': 'ip',
    'threat_type': 'malware_c2',
    'confidence': 0.9,
    'sources': ['internal_analysis', 'external_feed']
}

client.update_threat_intelligence(threat_intel)

# Поиск индикаторов
search_results = client.search_threat_indicators(
    query="192.168.1",
    indicator_type="ip"
)

for result in search_results:
    print(f"Indicator: {result['indicator']} - {result['threat_type']}")
```

## LLM интеграция

### Анализ с Ollama

```python
# Анализ события с LLM
llm_analysis = client.llm_analyze_event(
    event_data=network_event,
    model="qwen2.5-coder:1.5b",
    context={
        'previous_events': recent_events,
        'system_state': current_state
    }
)

print(f"LLM threat level: {llm_analysis['threat_level']}")
print(f"Explanation: {llm_analysis['explanation']}")
```

### Гибридный анализ

```python
# Комбинированный анализ (нейросеть + LLM)
hybrid_result = client.hybrid_analyze_event(
    event_data=network_event,
    neural_weight=0.6,
    llm_weight=0.4
)

print(f"Final threat level: {hybrid_result['final_threat_level']}")
print(f"Neural confidence: {hybrid_result['neural_result']['confidence']}")
print(f"LLM confidence: {hybrid_result['llm_result']['confidence']}")
```

## Аудио/видео мониторинг

### Мониторинг устройств

```python
# Получение статуса A/V устройств
av_status = client.get_av_monitoring_status()
print(f"Active devices: {av_status['active_devices']}")
print(f"Risk levels: {av_status['risk_levels']}")

# Получение списка устройств
devices = client.get_av_devices()
for device in devices:
    if device['risk_level'] != 'low':
        print(f"Suspicious device: {device['name']}")
        print(f"Risk: {device['risk_level']}")
```

### Анализ конденсаторов

```python
# Анализ конденсаторов микрофона
capacitor_analysis = client.analyze_capacitors(
    device_id="audio_device_001",
    analysis_type="microphone_detection"
)

print(f"Microphone potential: {capacitor_analysis['microphone_potential']}")
print(f"Risk assessment: {capacitor_analysis['risk_assessment']}")
```

## Уведомления

### Настройка уведомлений

```python
# Настройка webhook уведомлений
webhook_config = {
    'url': 'https://your-webhook.example.com/security',
    'events': ['threat_detected', 'system_alert'],
    'format': 'json',
    'retry_count': 3
}

client.set_webhook_notification(webhook_config)

# Настройка email уведомлений
email_config = {
    'smtp_server': 'smtp.example.com',
    'smtp_port': 587,
    'username': 'security@example.com',
    'password': 'password',
    'recipients': ['admin@example.com']
}

client.set_email_notification(email_config)
```

### Отправка уведомлений

```python
# Отправка кастомного уведомления
client.send_notification(
    title="Custom Security Alert",
    message="Suspicious activity detected",
    severity="high",
    channels=['webhook', 'email']
)
```

## Конфигурация

### Управление конфигурацией

```python
# Получение текущей конфигурации
config = client.get_configuration()
print(f"Monitoring interval: {config['monitoring']['interval']}")

# Обновление конфигурации
new_config = {
    'monitoring': {
        'interval': 30,
        'enable_network_monitoring': True,
        'enable_process_monitoring': True
    }
}

client.update_configuration(new_config)
```

### Профили конфигурации

```python
# Создание профиля конфигурации
profile = {
    'name': 'high_security',
    'settings': {
        'neural_core': {
            'confidence_threshold': 0.8,
            'enable_real_time_analysis': True
        },
        'defense': {
            'auto_block_threshold': 5,
            'block_duration': 7200
        }
    }
}

profile_id = client.create_configuration_profile(profile)

# Применение профиля
client.apply_configuration_profile(profile_id)
```

## Обработка ошибок

### Исключения

```python
from rsecure.exceptions import (
    RSecureAPIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

try:
    threats = client.get_threats()
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
except RSecureAPIError as e:
    print(f"API error: {e}")
```

### Retry механизм

```python
from rsecure import RSecureClient
from rsecure.utils import retry_on_error

@retry_on_error(max_attempts=3, delay=1)
def get_threats_with_retry():
    return client.get_threats()

threats = get_threats_with_retry()
```

## Логирование

### Настройка логирования

```python
import logging
from rsecure import setup_logging

# Настройка логирования RSecure
setup_logging(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    file='rsecure_client.log'
)

# Использование логирования
logger = logging.getLogger('rsecure')
logger.info("Starting RSecure client")
```

### Асинхронные операции

```python
import asyncio
from rsecure import AsyncRSecureClient

async def main():
    client = AsyncRSecureClient("http://localhost:8080", "api-key")
    
    # Асинхронное получение статуса
    status = await client.get_status()
    print(f"Status: {status['status']}")
    
    # Асинхронный анализ событий
    tasks = []
    for event in events:
        task = client.analyze_event(event)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    for result in results:
        if result['threat_assessment']['is_threat']:
            print(f"Threat detected: {result['analysis_id']}")

asyncio.run(main())
```

## Примеры использования

### Полный пример мониторинга

```python
from rsecure import RSecureClient
import time

def main():
    # Инициализация клиента
    client = RSecureClient("http://localhost:8080", "api-key")
    
    # Проверка статуса
    status = client.get_status()
    if status['status'] != 'running':
        print("RSecure is not running")
        return
    
    # Настройка callback для критических событий
    def handle_critical_event(event):
        print(f"CRITICAL: {event['description']}")
        # Отправка уведомления
        client.send_notification(
            title="Critical Security Event",
            message=event['description'],
            severity="critical"
        )
    
    client.set_event_callback(handle_critical_event)
    
    # Начало мониторинга
    client.start_monitoring()
    
    try:
        while True:
            # Получение активных угроз
            threats = client.get_threats(active_only=True)
            print(f"Active threats: {len(threats)}")
            
            # Получение системных метрик
            metrics = client.get_system_metrics()
            print(f"System load: CPU={metrics['cpu_percent']}%, Memory={metrics['memory_percent']}%")
            
            time.sleep(60)  # Проверка каждую минуту
            
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        client.stop_monitoring()

if __name__ == "__main__":
    main()
```

### Интеграция с Flask

```python
from flask import Flask, request, jsonify
from rsecure import RSecureClient

app = Flask(__name__)
rsecure = RSecureClient("http://localhost:8080", "api-key")

@app.route('/analyze', methods=['POST'])
def analyze_event():
    event_data = request.json
    analysis = rsecure.analyze_event(event_data)
    return jsonify(analysis)

@app.route('/threats', methods=['GET'])
def get_threats():
    threats = rsecure.get_threats()
    return jsonify(threats)

@app.route('/block-ip', methods=['POST'])
def block_ip():
    ip = request.json.get('ip')
    reason = request.json.get('reason', 'Manual block')
    rsecure.block_ip(ip, reason)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
```

### Интеграция с Django

```python
# settings.py
RSECURE_CONFIG = {
    'API_URL': 'http://localhost:8080',
    'API_KEY': 'your-api-key',
    'TIMEOUT': 30
}

# views.py
from django.http import JsonResponse
from rsecure import RSecureClient

def security_dashboard(request):
    client = RSecureClient(
        api_url=settings.RSECURE_CONFIG['API_URL'],
        api_key=settings.RSECURE_CONFIG['API_KEY']
    )
    
    context = {
        'status': client.get_status(),
        'threats': client.get_threats(limit=10),
        'metrics': client.get_system_metrics()
    }
    
    return render(request, 'security/dashboard.html', context)

def analyze_security_event(request):
    if request.method == 'POST':
        event_data = json.loads(request.body)
        client = RSecureClient(
            api_url=settings.RSECURE_CONFIG['API_URL'],
            api_key=settings.RSECURE_CONFIG['API_KEY']
        )
        
        analysis = client.analyze_event(event_data)
        return JsonResponse(analysis)
```

## Тестирование

### Unit тесты

```python
import unittest
from unittest.mock import Mock, patch
from rsecure import RSecureClient

class TestRSecureClient(unittest.TestCase):
    def setUp(self):
        self.client = RSecureClient("http://localhost:8080", "test-key")
    
    @patch('requests.Session.get')
    def test_get_status(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'running'}
        mock_get.return_value = mock_response
        
        status = self.client.get_status()
        self.assertEqual(status['status'], 'running')
    
    @patch('requests.Session.post')
    def test_analyze_event(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'threat_assessment': {'is_threat': False}
        }
        mock_post.return_value = mock_response
        
        event = {'event_type': 'test', 'data': {}}
        analysis = self.client.analyze_event(event)
        self.assertFalse(analysis['threat_assessment']['is_threat'])

if __name__ == '__main__':
    unittest.main()
```

### Интеграционные тесты

```python
import pytest
from rsecure import RSecureClient

@pytest.fixture
def client():
    return RSecureClient("http://localhost:8080", "test-key")

def test_connection(client):
    status = client.get_status()
    assert status['status'] in ['running', 'stopped']

def test_threat_analysis(client):
    event = {
        'event_type': 'network_connection',
        'data': {'source_ip': '192.168.1.1', 'target_port': 80}
    }
    analysis = client.analyze_event(event)
    assert 'threat_assessment' in analysis
    assert 'confidence' in analysis['threat_assessment']
```

## Производительность

### Оптимизация запросов

```python
# Использование пул соединений
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

client = RSecureClient("http://localhost:8080", "api-key")

# Настройка retry стратегии
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
client.session.mount("http://", adapter)
client.session.mount("https://", adapter)
```

### Кэширование

```python
from functools import lru_cache
from rsecure import RSecureClient

class CachedRSecureClient(RSecureClient):
    @lru_cache(maxsize=100)
    def get_status(self):
        return super().get_status()
    
    @lru_cache(maxsize=50)
    def get_defense_rules(self):
        return super().get_defense_rules()

client = CachedRSecureClient("http://localhost:8080", "api-key")
```

## Поддержка

- **Документация**: `https://rsecure.readthedocs.io`
- **Примеры**: `https://github.com/rsecure/python-examples`
- **Сообщество**: `https://discord.gg/rsecure`
- **Issues**: `https://github.com/rsecure/python-api/issues`

---

RSecure Python API предоставляет мощный и гибкий интерфейс для интеграции функций безопасности RSecure в Python приложения, с полной поддержкой всех основных компонентов и продвинутых возможностей.
