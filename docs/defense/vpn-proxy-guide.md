# 🛡️ VPN и Прокси - Полное Руководство

## Обзор

RSecure предоставляет comprehensive систему VPN и прокси интеграции с поддержкой множественных протоколов, автоматической маршрутизацией и advanced функциями безопасности.

## 🚀 Поддерживаемые Прокси

### HTTP/HTTPS Прокси

**Базовая конфигурация:**
```python
from rsecure.modules.defense.vpn_proxy import ProxyServer, ProxyConfig, ProxyType

config = ProxyConfig(
    proxy_type=ProxyType.HTTP,
    host="0.0.0.0",
    port=8080,
    username="user",      # Опционально
    password="pass"       # Опционально
)

proxy = ProxyServer(config)
proxy.start()
```

**Особенности:**
- ✅ Поддержка HTTP CONNECT метода
- ✅ Аутентификация Basic/Digest
- ✅ SSL/TLS туннелирование
- ✅ Заголовок X-Forwarded-For

### SOCKS4/SOCKS5 Прокси

**SOCKS5 конфигурация:**
```python
config = ProxyConfig(
    proxy_type=ProxyType.SOCKS5,
    host="0.0.0.0",
    port=1080,
    username="user",
    password="pass"
)

proxy = ProxyServer(config)
proxy.start()
```

**Возможности SOCKS5:**
- ✅ Аутентификация (None, Username/Password)
- ✅ Поддержка IPv4/IPv6/доменных имен
- ✅ UDP ассоциации
- ✅ BIND команды для серверов

### Shadowsocks Прокси

**Конфигурация Shadowsocks:**
```python
config = ProxyConfig(
    proxy_type=ProxyType.SHADOWSOCKS,
    host="0.0.0.0",
    port=8388,
    encryption="aes-256-cfb",
    password="your_password"
)

proxy = ProxyServer(config)
proxy.start()
```

**Поддерживаемые алгоритмы:**
- ✅ aes-256-cfb
- ✅ aes-128-cfb
- ✅ chacha20-ietf-poly1305
- ✅ xchacha20-ietf-poly1305

### V2Ray Прокси

**V2Ray конфигурация:**
```python
config = ProxyConfig(
    proxy_type=ProxyType.V2RAY,
    host="0.0.0.0",
    port=10086,
    protocol="vmess",
    uuid="your-uuid-here",
    alter_id=64
)

proxy = ProxyServer(config)
proxy.start()
```

### Trojan Прокси

**Trojan конфигурация:**
```python
config = ProxyConfig(
    proxy_type=ProxyType.TROJAN,
    host="0.0.0.0",
    port=443,
    password="your_password",
    ssl_cert="path/to/cert.pem",
    ssl_key="path/to/key.pem"
)

proxy = ProxyServer(config)
proxy.start()
```

## 🔐 Поддерживаемые VPN

### OpenVPN

**Создание конфигурации:**
```python
from rsecure.modules.defense.vpn_proxy import VPNManager, VPNConfig, VPNType

vpn_manager = VPNManager()

config = VPNConfig(
    vpn_type=VPNType.OPENVPN,
    server_host="vpn.example.com",
    server_port=1194,
    protocol="udp",
    cipher="aes-256-cbc",
    auth="sha256",
    config_file="/path/to/openvpn.conf"
)

# Создание файла конфигурации
vpn_manager.create_vpn_config(config, "/tmp/my_openvpn.conf")

# Подключение
connection_id = vpn_manager.connect_vpn(config)
```

**OpenVPN особенности:**
- ✅ Поддержка UDP/TCP
- ✅ Множественные алгоритмы шифрования
- ✅ TLS аутентификация
- ✅ Компрессия LZO/ZLIB

### WireGuard

**WireGuard конфигурация:**
```python
config = VPNConfig(
    vpn_type=VPNType.WIREGUARD,
    server_host="vpn.example.com",
    server_port=51820,
    protocol="udp",
    config_file="/path/to/wg0.conf"
)

vpn_manager.create_vpn_config(config, "/tmp/my_wg.conf")
connection_id = vpn_manager.connect_vpn(config)
```

**WireGuard преимущества:**
- ✅ Высокая производительность
- ✅ Минимальная кодовая база
- ✅ Современная криптография
- ✅ Простая конфигурация

### IKEv2/IPSec

**IKEv2 конфигурация:**
```python
config = VPNConfig(
    vpn_type=VPNType.IKEV2,
    server_host="vpn.example.com",
    server_port=500,
    protocol="udp",
    config_file="/etc/ipsec.conf"
)

vpn_manager.create_vpn_config(config, "/tmp/ikev2.conf")
connection_id = vpn_manager.connect_vpn(config)
```

### SSTP

**SSTP конфигурация:**
```python
config = VPNConfig(
    vpn_type=VPNType.SSTP,
    server_host="vpn.example.com",
    server_port=443,
    protocol="tcp"
)

connection_id = vpn_manager.connect_vpn(config)
```

## 🌐 Цепочки Прокси

### Создание Цепочки

```python
from rsecure.modules.defense.vpn_proxy import ProxyChain

chain = ProxyChain()

# Добавление прокси в цепочку
chain.add_proxy(ProxyConfig(
    proxy_type=ProxyType.HTTP,
    host="proxy1.example.com",
    port=8080
))

chain.add_proxy(ProxyConfig(
    proxy_type=ProxyType.SOCKS5,
    host="proxy2.example.com",
    port=1080
))

chain.add_proxy(ProxyConfig(
    proxy_type=ProxyType.SHADOWSOCKS,
    host="proxy3.example.com",
    port=8388
))

# Создание цепочки
chain.create_chain([0, 1, 2])  # Использовать все прокси

# Подключение через цепочку
sock = chain.connect_through_chain("target.com", 80)
```

### Динамические Цепочки

```python
# Автоматический выбор прокси
working_proxies = chain.test_all_proxies()
best_chain = chain.optimize_chain(working_proxies)

# Балансировка нагрузки
load_balanced_chain = chain.create_load_balanced_chain(
    working_proxies,
    strategy="round_robin"
)
```

## 🔄 Менеджер Сетевых Маршрутов

### Автоматическая Маршрутизация

```python
from rsecure.modules.defense.vpn_proxy import NetworkBypassManager

manager = NetworkBypassManager()

# Автоматический выбор оптимального маршрута
bypass_id = manager.create_bypass_route(
    target_host="example.com",
    target_port=80,
    method="auto"  # Автоматический выбор
)

status = manager.get_bypass_status(bypass_id)
```

### Приоритеты Маршрутизации

```python
# Настройка приоритетов
route_priorities = {
    "direct": 1,        # Прямое соединение
    "proxy": 2,         # Через прокси
    "vpn": 3,           # Через VPN
    "tor": 4,           # Через Tor
    "chain": 5          # Через цепочку
}

manager.set_route_priorities(route_priorities)
```

### Отказоустойчивость

```python
# Настройка отказоустойчивости
failover_config = {
    "enabled": True,
    "max_retries": 3,
    "retry_delay": 5,
    "health_check_interval": 30,
    "auto_failover": True
}

manager.configure_failover(failover_config)
```

## 🔧 Продвинутая Конфигурация

### Пулы Прокси

```python
# Создание пула прокси
proxy_pool = ProxyPool()

# Добавление прокси в пул
proxies = [
    {"host": "proxy1.com", "port": 8080, "type": "http"},
    {"host": "proxy2.com", "port": 1080, "type": "socks5"},
    {"host": "proxy3.com", "port": 8388, "type": "shadowsocks"}
]

for proxy_info in proxies:
    proxy_pool.add_proxy(proxy_info)

# Тестирование пула
working_proxies = proxy_pool.test_pool()
print(f"Working proxies: {len(working_proxies)}")

# Получение лучшего прокси
best_proxy = proxy_pool.get_best_proxy("example.com", 80)
```

### Географическая Маршрутизация

```python
# Настройка гео-маршрутизации
geo_config = {
    "us": ["proxy1.com", "proxy2.com"],
    "eu": ["proxy3.com", "proxy4.com"],
    "asia": ["proxy5.com", "proxy6.com"]
}

geo_router = GeoRouter(geo_config)

# Маршрутизация через указанный регион
proxy = geo_router.get_proxy_for_region("us", "example.com")
```

### Временая Маршрутизация

```python
# Настройка временной маршрутизации
time_config = {
    "peak_hours": {
        "start": "09:00",
        "end": "18:00",
        "preferred_methods": ["direct", "proxy"]
    },
    "off_hours": {
        "start": "18:01",
        "end": "08:59",
        "preferred_methods": ["vpn", "tor"]
    }
}

time_router = TimeRouter(time_config)
method = time_router.get_recommended_method()
```

## 📊 Мониторинг и Аналитика

### Метрики Производительности

```python
# Получение статистики прокси
proxy_stats = manager.get_proxy_statistics()

for proxy_id, stats in proxy_stats.items():
    print(f"Proxy {proxy_id}:")
    print(f"  Success rate: {stats['success_rate']}%")
    print(f"  Average latency: {stats['avg_latency']}ms")
    print(f"  Total connections: {stats['total_connections']}")
    print(f"  Failed connections: {stats['failed_connections']}")
```

### Health Checks

```python
# Настройка health checks
health_config = {
    "interval": 30,  # секунды
    "timeout": 5,    # секунды
    "retries": 3,
    "test_targets": ["google.com", "cloudflare.com"]
}

manager.configure_health_checks(health_config)

# Получение health статуса
health_status = manager.get_health_status()
for proxy_id, status in health_status.items():
    print(f"Proxy {proxy_id}: {status['status']}")
```

### Алерты и Уведомления

```python
# Настройка алертов
alert_config = {
    "proxy_failure_threshold": 0.1,  # 10% failure rate
    "latency_threshold": 1000,       # 1000ms
    "notification_methods": ["email", "webhook"]
}

manager.configure_alerts(alert_config)
```

## 🔒 Безопасность и Шифрование

### SSL/TLS Конфигурация

```python
# Настройка SSL для прокси
ssl_config = {
    "cert_file": "/path/to/cert.pem",
    "key_file": "/path/to/key.pem",
    "ca_file": "/path/to/ca.pem",
    "verify_peers": True,
    "cipher_suites": [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256"
    ]
}

proxy.configure_ssl(ssl_config)
```

### Аутентификация

```python
# Настройка множественной аутентификации
auth_config = {
    "methods": ["basic", "digest", "ntlm"],
    "user_database": "/path/to/users.db",
    "session_timeout": 3600,
    "max_attempts": 3,
    "lockout_time": 900
}

proxy.configure_authentication(auth_config)
```

### IP Фильтрация

```python
# Белый список IP
whitelist = [
    "192.168.1.0/24",
    "10.0.0.0/8",
    "172.16.0.0/12"
]

proxy.set_ip_whitelist(whitelist)

# Черный список IP
blacklist = [
    "192.168.1.100",
    "10.0.0.50"
]

proxy.set_ip_blacklist(blacklist)
```

## 🚀 Оптимизация Производительности

### Connection Pooling

```python
# Настройка пула соединений
pool_config = {
    "max_connections": 100,
    "max_idle_time": 300,
    "connection_timeout": 30,
    "keep_alive": True
}

proxy.configure_connection_pool(pool_config)
```

### Кэширование

```python
# Настройка кэширования
cache_config = {
    "dns_cache_size": 1000,
    "dns_cache_ttl": 300,
    "connection_cache_size": 500,
    "connection_cache_ttl": 60
}

proxy.configure_cache(cache_config)
```

### Сжатие

```python
# Настройка сжатия
compression_config = {
    "enabled": True,
    "algorithms": ["gzip", "deflate", "brotli"],
    "min_size": 1024,
    "level": 6
}

proxy.configure_compression(compression_config)
```

## 🛠️ Управление и Автоматизация

### REST API

```python
# Запуск API сервера
api_server = ProxyAPIManager()
api_server.start(host="0.0.0.0", port=8080)

# API эндпоинты:
# GET  /api/proxies          - список прокси
# POST /api/proxies          - добавить прокси
# GET  /api/proxies/{id}      - информация о прокси
# PUT  /api/proxies/{id}      - обновить прокси
# DELETE /api/proxies/{id}      - удалить прокси
# GET  /api/routes            - список маршрутов
# POST /api/routes            - создать маршрут
```

### Автоматическое Управление

```python
# Автоматическая ротация прокси
rotation_config = {
    "enabled": True,
    "interval": 3600,  # 1 час
    "strategy": "random",
    "health_check_before_rotation": True
}

manager.configure_rotation(rotation_config)
```

### Конфигурация через YAML

```yaml
# proxy_config.yaml
proxies:
  - id: proxy1
    type: http
    host: proxy1.example.com
    port: 8080
    auth:
      username: user1
      password: pass1
    ssl:
      enabled: true
      verify: true
  
  - id: proxy2
    type: socks5
    host: proxy2.example.com
    port: 1080
    auth:
      username: user2
      password: pass2

routes:
  - id: route1
    chain: [proxy1, proxy2]
    targets: ["*.com", "*.org"]
    priority: 1

health_checks:
  interval: 30
  timeout: 5
  targets:
    - google.com
    - cloudflare.com
```

```python
# Загрузка конфигурации
manager.load_config_from_yaml("proxy_config.yaml")
```

## 📈 Тестирование и Диагностика

### Тестирование Прокси

```python
# Комплексное тестирование
test_results = manager.test_all_proxies()

for proxy_id, result in test_results.items():
    print(f"Proxy {proxy_id}:")
    print(f"  Status: {result['status']}")
    print(f"  Latency: {result['latency']}ms")
    print(f"  Bandwidth: {result['bandwidth']} Mbps")
    print(f"  Supported protocols: {result['protocols']}")
```

### Диагностика Соединений

```python
# Диагностика проблем с соединением
diagnosis = manager.diagnose_connection(
    target_host="example.com",
    target_port=80,
    timeout=10
)

print(f"Diagnosis: {diagnosis['result']}")
print(f"Issues: {diagnosis['issues']}")
print(f"Recommendations: {diagnosis['recommendations']}")
```

### Нагрузочное Тестирование

```python
# Нагрузочное тестирование
load_test_config = {
    "concurrent_connections": 100,
    "duration": 60,  # секунды
    "target_host": "example.com",
    "target_port": 80
}

results = manager.load_test(load_test_config)
print(f"Average response time: {results['avg_response_time']}ms")
print(f"Success rate: {results['success_rate']}%")
print(f"Throughput: {results['throughput']} req/s")
```

## 🔧 Устранение Неполадок

### Частые Проблемы

#### 1. Прокси Не Подключается
```python
# Диагностика прокси
proxy_diagnosis = manager.diagnose_proxy(proxy_id)
print(proxy_diagnosis)

# Возможные решения:
# - Проверить доступность хоста
# - Проверить порт
# - Проверить аутентификацию
# - Проверить SSL/TLS настройки
```

#### 2. Медленная Скорость
```python
# Оптимизация скорости
optimization = manager.optimize_for_speed()
print(f"Optimized configuration: {optimization}")

# Рекомендации:
# - Использовать географически близкие прокси
# - Включить сжатие
# - Оптимизировать размер буферов
# - Использовать connection pooling
```

#### 3. Высокий Rate Failure
```python
# Анализ причин отказов
failure_analysis = manager.analyze_failures(proxy_id)
print(f"Common failure reasons: {failure_analysis['reasons']}")

# Решения:
# - Ротация прокси
# - Настройка retry логики
# - Увеличение таймаутов
# - Использование резервных прокси
```

### Логирование и Отладка

```python
# Включение детального логирования
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Получение логов соединений
connection_logs = manager.get_connection_logs(proxy_id)
for log in connection_logs:
    print(f"{log['timestamp']}: {log['event']} - {log['details']}")
```

## 🎯 Лучшие Практики

### 1. Выбор Прокси
- Используйте географически близкие прокси для скорости
- Комбинируйте разные типы прокси для надежности
- Регулярно тестируйте и обновляйте прокси списки

### 2. Безопасность
- Всегда используйте SSL/TLS для прокси соединений
- Применяйте сильную аутентификацию
- Регулярно ротируйте учетные данные

### 3. Производительность
- Используйте connection pooling
- Включайте сжатие для больших данных
- Оптимизируйте таймауты и буферы

### 4. Отказоустойчивость
- Настраивайте health checks
- Используйте автоматическую ротацию
- Имейте резервные прокси

---

Это руководство предоставляет comprehensive обзор VPN и прокси функциональности в RSecure. Для дополнительной информации смотрите [DPI обход](dpi-bypass-guide.md) и [Tor интеграцию](tor-integration-guide.md).
