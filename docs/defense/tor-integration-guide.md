# 🌐 Tor Интеграция - Полное Руководство

## Обзор

RSecure предоставляет comprehensive Tor интеграцию с полным контролем над сетью, кастомными circuits, bridge поддержкой и advanced функциями анонимности.

## 🚀 Основная Tor Интеграция

### Запуск Tor Сервера

```python
from rsecure.modules.defense.tor_integration import TorIntegrationManager

tor_manager = TorIntegrationManager()

# Запуск Tor с кастомной конфигурацией
tor_config = {
    'SocksPort': '9050',
    'ControlPort': '9051',
    'CookieAuthentication': '1',
    'ExitNodes': '{us}',
    'NewCircuitPeriod': '30',
    'MaxCircuitDirtiness': '600'
}

if tor_manager.start_tor():
    print("Tor успешно запущен")
else:
    print("Ошибка запуска Tor")
```

### Базовое Анонимное Соединение

```python
# Создание анонимного соединения
connection_id = tor_manager.create_anonymous_connection(
    target_host="example.com",
    target_port=80
)

if connection_id:
    print(f"Анонимное соединение установлено: {connection_id}")
    
    # Проверка статуса
    status = tor_manager.get_tor_status()
    print(f"Tor статус: {status}")
```

## 🔮 Управление Tor Circuits

### Создание Кастомных Circuits

```python
from rsecure.modules.defense.tor_integration import TorCircuitConfig, TorCircuitType

# Стандартный circuit
standard_config = TorCircuitConfig(
    circuit_type=TorCircuitType.STANDARD,
    path_length=3,
    exit_country="us"
)

circuit_id = tor_manager.controller.create_circuit(standard_config)
print(f"Создан circuit: {circuit_id}")

# Long-lived circuit для постоянных соединений
long_lived_config = TorCircuitConfig(
    circuit_type=TorCircuitType.LONG_LIVED,
    path_length=3,
    purpose="long-lived"
)

# High-bandwidth circuit для больших объемов данных
high_bw_config = TorCircuitConfig(
    circuit_type=TorCircuitType.HIGH_BANDWIDTH,
    path_length=2,  # Короче для скорости
    purpose="high-bandwidth"
)
```

### Выбор Узлов (Node Selection)

```python
# Получение доступных узлов
nodes = tor_manager.controller.get_nodes()

# Фильтрация по типам
guard_nodes = [n for n in nodes if TorNodeType.GUARD in n.flags]
exit_nodes = [n for n in nodes if TorNodeType.EXIT in n.flags]
middle_nodes = [n for n in nodes if TorNodeType.MIDDLE in n.flags]

# Выбор лучших узлов по bandwidth
best_guards = sorted(guard_nodes, key=lambda x: x.bandwidth, reverse=True)[:5]
best_exits = sorted(exit_nodes, key=lambda x: x.bandwidth, reverse=True)[:5]

# Создание circuit с лучшими узлами
custom_config = TorCircuitConfig(
    circuit_type=TorCircuitType.STANDARD,
    specific_nodes=[
        best_guards[0].fingerprint,
        best_exits[0].fingerprint
    ],
    path_length=2
)
```

### Географическая Маршрутизация

```python
# Circuit через определенные страны
geo_config = TorCircuitConfig(
    circuit_type=TorCircuitType.STANDARD,
    exit_country="de",  # Выход через Германию
    avoid_countries=["cn", "ru", "ir"]  # Избегать этих стран
)

# Multi-region circuit
def create_multi_region_circuit():
    # Entry через Европу
    entry_nodes = [n for n in nodes if n.ip_address.startswith(("193.", "176.", "185."))]
    # Exit через США
    us_exits = [n for n in exit_nodes if n.ip_address.startswith(("104.", "172.", "198."))]
    
    if entry_nodes and us_exits:
        config = TorCircuitConfig(
            specific_nodes=[entry_nodes[0].fingerprint, us_exits[0].fingerprint],
            path_length=2
        )
        return tor_manager.controller.create_circuit(config)
    return None
```

## 🌉 Bridge Поддержка

### Управление Bridges

```python
from rsecure.modules.defense.tor_integration import TorBridgeManager

bridge_manager = TorBridgeManager()

# Добавление различных типов bridges
bridges = [
    "obfs4 192.168.1.1:80 cert=abc123 iat-mode=0",
    "obfs4 192.168.1.2:443 cert=def456 iat-mode=0",
    "meek 192.168.1.3:80 url=https://meek-reflect.appspot.com/ front=cloudflare.com",
    "snowflake 192.168.1.4:80"
]

for bridge_line in bridges:
    bridge_manager.add_bridge(bridge_line)

# Получение рабочих bridges
working_bridges = bridge_manager.get_working_bridges()
print(f"Рабочих bridges: {len(working_bridges)}")
```

### Bridge Тестирование

```python
# Тестирование всех bridges
def test_all_bridges():
    results = []
    for bridge in bridge_manager.bridges:
        is_working = bridge_manager.test_bridge(bridge)
        results.append({
            'bridge': bridge,
            'working': is_working,
            'type': bridge['type'],
            'latency': measure_bridge_latency(bridge) if is_working else None
        })
    
    # Сортировка по производительности
    working_results = [r for r in results if r['working']]
    return sorted(working_results, key=lambda x: x['latency'] or float('inf'))

def measure_bridge_latency(bridge_info):
    """Измерение задержки bridge"""
    import time
    start_time = time.time()
    
    if bridge_manager.test_bridge(bridge_info):
        return (time.time() - start_time) * 1000  # мс
    return None

best_bridges = test_all_bridges()
print(f"Лучшие bridges: {[b['bridge']['ip'] for b in best_bridges[:3]]}")
```

### Автоматическая Bridge Конфигурация

```python
# Автоматическая настройка Tor с bridges
def setup_tor_with_bridges():
    # Получение лучших bridges
    best_bridges = bridge_manager.get_working_bridges()
    
    if not best_bridges:
        print("Нет рабочих bridges")
        return False
    
    # Настройка Tor с bridges
    bridge_lines = [bridge['line'] for bridge in best_bridges[:3]]
    
    tor_config_with_bridges = {
        'SocksPort': '9050',
        'ControlPort': '9051',
        'UseBridges': '1',
        'Bridge': bridge_lines,
        'ClientTransportPlugin': 'obfs4 exec /usr/bin/obfs4proxy managed'
    }
    
    return tor_manager.start_tor_with_config(tor_config_with_bridges)

success = setup_tor_with_bridges()
if success:
    print("Tor успешно настроен с bridges")
```

## 🔐 Плагируемые Транспорты (Pluggable Transports)

### Обфускационные Транспорты

```python
from rsecure.modules.defense.tor_integration import TorPluggableTransport

transport_manager = TorPluggableTransport()

# Регистрация Obfs4
transport_manager.register_transport(
    "obfs4",
    "/usr/local/bin/obfs4proxy",
    ["--logLevel", "INFO"]
)

# Регистрация Meek
transport_manager.register_transport(
    "meek",
    "/usr/local/bin/meek-client",
    ["--url", "https://meek-reflect.appspot.com/"]
)

# Регистрация Snowflake
transport_manager.register_transport(
    "snowflake",
    "/usr/local/bin/snowflake-client",
    ["--broker", "snowflake-broker.bamsoftware.com"]
)
```

### Запуск Транспортов

```python
# Запуск Obfs4 на порту 8080
if transport_manager.start_transport("obfs4", 8080):
    print("Obfs4 транспорт запущен на порту 8080")

# Запуск Meek на порту 8081
if transport_manager.start_transport("meek", 8081):
    print("Meek транспорт запущен на порту 8081")

# Запуск Snowflake на порту 8082
if transport_manager.start_transport("snowflake", 8082):
    print("Snowflake транспорт запущен на порту 8082")
```

### Мониторинг Транспортов

```python
# Проверка статуса транспортов
def check_transport_status():
    status = {}
    for transport_name, transport_info in transport_manager.running_transports.items():
        process = transport_info['process']
        if process.poll() is None:  # Процесс все еще работает
            status[transport_name] = {
                'status': 'running',
                'port': transport_info['port'],
                'pid': transport_info['pid']
            }
        else:
            status[transport_name] = {
                'status': 'stopped',
                'exit_code': process.poll()
            }
    
    return status

transport_status = check_transport_status()
for name, info in transport_status.items():
    print(f"{name}: {info['status']} (порт: {info.get('port', 'N/A')})")
```

## 🛡️ Hidden Сервисы

### Создание Hidden Сервисов

```python
from rsecure.modules.defense.tor_integration import TorHiddenService

hidden_service = TorHiddenService()

# Создание web hidden сервиса
if hidden_service.create_hidden_service(
    service_id="web_service",
    local_port=8080,
    virtual_port=80
):
    print("Web hidden сервис создан")
    
    # Получение .onion адреса
    onion_address = hidden_service.get_onion_address("web_service")
    if onion_address:
        print(f"Сервис доступен по адресу: {onion_address}")
```

### Управление Сервисами

```python
# Создание нескольких сервисов
services = [
    {"id": "web", "local_port": 8080, "virtual_port": 80},
    {"id": "ssh", "local_port": 22, "virtual_port": 22},
    {"id": "ftp", "local_port": 21, "virtual_port": 21}
]

for service in services:
    if hidden_service.create_hidden_service(**service):
        onion_addr = hidden_service.get_onion_address(service["id"])
        print(f"{service['id']}: {onion_addr}")

# Получение всех сервисов
all_services = hidden_service.services
for service_id, service_info in all_services.items():
    print(f"{service_id}: {service_info['onion_address']}")
```

### Автоматическая Конфигурация Hidden Сервисов

```python
# Создание hidden сервиса с автоматической генерацией ключей
def create_advanced_hidden_service(service_id, local_port, virtual_port=80):
    import tempfile
    import shutil
    
    # Создание временной директории для сервиса
    service_dir = tempfile.mkdtemp(prefix=f"tor_hidden_{service_id}_")
    
    if hidden_service.create_hidden_service(
        service_id=service_id,
        local_port=local_port,
        virtual_port=virtual_port,
        service_dir=service_dir
    ):
        # Ожидание генерации .onion адреса
        import time
        time.sleep(5)
        
        onion_address = hidden_service.get_onion_address(service_id)
        return {
            'service_id': service_id,
            'onion_address': onion_address,
            'service_dir': service_dir,
            'local_port': local_port,
            'virtual_port': virtual_port
        }
    
    return None

# Создание продвинутого сервиса
advanced_service = create_advanced_hidden_service(
    "advanced_web",
    local_port=8080,
    virtual_port=443
)

if advanced_service:
    print(f"Продвинутый сервис: {advanced_service['onion_address']}")
```

## 🌍 Tor Клиент

### HTTP Запросы через Tor

```python
from rsecure.modules.defense.tor_integration import TorClient

tor_client = TorClient()

# Базовый HTTP запрос
status_code, response = tor_client.http_request(
    method="GET",
    url="http://example.com",
    headers={"User-Agent": "RSecure/1.0"}
)

print(f"Status: {status_code}")
print(f"Response length: {len(response)} bytes")

# HTTPS запрос
status_code, response = tor_client.http_request(
    method="GET",
    url="https://httpbin.org/ip",
    circuit_id="1234567890"  # Через конкретный circuit
)

print(f"Status: {status_code}")
print(f"Response: {response.decode()}")
```

### SOCKS5 Соединения

```python
# Создание SOCKS5 соединения через Tor
sock = tor_client.create_socks_connection(
    host="example.com",
    port=80,
    circuit_id="1234567890"  # Опционально: через конкретный circuit
)

if sock:
    try:
        # Отправка HTTP запроса
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        sock.send(request)
        
        # Получение ответа
        response = sock.recv(4096)
        print(f"Response: {response.decode()}")
        
    finally:
        sock.close()
```

### Множественные Параллельные Запросы

```python
import threading
import queue

class TorWorkerPool:
    def __init__(self, num_workers=5):
        self.num_workers = num_workers
        self.work_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def _worker(self, worker_id):
        client = TorClient()
        
        while True:
            try:
                task = self.work_queue.get(timeout=1)
                if task is None:
                    break
                
                url, method, headers, data = task
                status_code, response = client.http_request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data
                )
                
                self.result_queue.put({
                    'worker_id': worker_id,
                    'url': url,
                    'status_code': status_code,
                    'response': response
                })
                
            except queue.Empty:
                continue
            except Exception as e:
                self.result_queue.put({
                    'worker_id': worker_id,
                    'error': str(e)
                })
    
    def add_request(self, url, method="GET", headers=None, data=None):
        self.work_queue.put((url, method, headers, data))
    
    def get_result(self, timeout=10):
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def shutdown(self):
        for _ in range(self.num_workers):
            self.work_queue.put(None)
        
        for worker in self.workers:
            worker.join()

# Использование пула
pool = TorWorkerPool(num_workers=10)

# Добавление запросов
urls = [
    "http://example.com",
    "http://httpbin.org/ip",
    "http://httpbin.org/user-agent",
    "http://httpbin.org/headers"
]

for url in urls:
    pool.add_request(url)

# Получение результатов
results = []
for _ in range(len(urls)):
    result = pool.get_result()
    if result and 'error' not in result:
        results.append(result)
        print(f"Worker {result['worker_id']}: {result['url']} -> {result['status_code']}")

pool.shutdown()
```

## 📊 Мониторинг и Аналитика

### Мониторинг Сети

```python
# Получение детальной статистики Tor
def get_tor_network_stats():
    status = tor_manager.get_tor_status()
    
    # Дополнительная статистика
    network_status = tor_manager.controller.get_network_status()
    circuits = tor_manager.controller.circuits
    streams = tor_manager.controller.streams
    
    stats = {
        'tor_running': status['tor_running'],
        'controller_connected': status['controller_connected'],
        'active_circuits': len(circuits),
        'active_streams': len(streams),
        'network_status': network_status,
        'circuit_details': []
    }
    
    # Детальная информация о circuits
    for circuit_id, circuit_info in circuits.items():
        stats['circuit_details'].append({
            'id': circuit_id,
            'status': circuit_info['status'],
            'purpose': circuit_info.get('purpose', 'unknown'),
            'path_length': len(circuit_info.get('path', [])),
            'build_flags': circuit_info.get('build_flags', [])
        })
    
    return stats

network_stats = get_tor_network_stats()
print(f"Активных circuits: {network_stats['active_circuits']}")
print(f"Активных streams: {network_stats['active_streams']}")
```

### Производительность Circuits

```python
import time

def measure_circuit_performance(circuit_id, test_url="http://httpbin.org/ip"):
    """Измерение производительности circuit"""
    start_time = time.time()
    
    status_code, response = tor_client.http_request(
        "GET", test_url, circuit_id=circuit_id
    )
    
    end_time = time.time()
    
    return {
        'circuit_id': circuit_id,
        'latency': (end_time - start_time) * 1000,  # мс
        'status_code': status_code,
        'response_size': len(response) if response else 0
    }

# Тестирование всех circuits
circuit_performance = []
for circuit_id in tor_manager.controller.circuits:
    perf = measure_circuit_performance(circuit_id)
    circuit_performance.append(perf)

# Сортировка по производительности
best_circuits = sorted(circuit_performance, key=lambda x: x['latency'])
print(f"Лучший circuit: {best_circuits[0]['circuit_id']} ({best_circuits[0]['latency']:.2f}ms)")
```

### Health Monitoring

```python
def tor_health_check():
    """Комплексная проверка здоровья Tor"""
    health_status = {
        'tor_process': False,
        'controller_connection': False,
        'socks_port': False,
        'circuit_creation': False,
        'connectivity': False,
        'bridges': 0,
        'hidden_services': 0
    }
    
    # Проверка процесса Tor
    if tor_manager.tor_process and tor_manager.tor_process.poll() is None:
        health_status['tor_process'] = True
    
    # Проверка подключения контроллера
    if tor_manager.controller.connected:
        health_status['controller_connection'] = True
    
    # Проверка SOCKS порта
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("127.0.0.1", 9050))
        sock.close()
        health_status['socks_port'] = result == 0
    except:
        pass
    
    # Проверка создания circuit
    try:
        test_config = TorCircuitConfig(circuit_type=TorCircuitType.STANDARD)
        circuit_id = tor_manager.controller.create_circuit(test_config)
        if circuit_id:
            health_status['circuit_creation'] = True
            tor_manager.controller.close_circuit(circuit_id)
    except:
        pass
    
    # Проверка подключения через Tor
    try:
        status_code, _ = tor_client.http_request("GET", "http://httpbin.org/ip")
        health_status['connectivity'] = status_code == 200
    except:
        pass
    
    # Подсчет bridges и hidden сервисов
    health_status['bridges'] = len(tor_manager.bridge_manager.bridges)
    health_status['hidden_services'] = len(tor_manager.hidden_service.services)
    
    return health_status

health = tor_health_check()
print("Tor Health Status:")
for key, value in health.items():
    status = "✅" if value else "❌"
    print(f"  {key}: {status}")
```

## 🔧 Конфигурация и Оптимизация

### Продвинутая Конфигурация Tor

```python
# Оптимальная конфигурация для производительности
performance_config = {
    'SocksPort': '9050',
    'ControlPort': '9051',
    'CookieAuthentication': '1',
    'NumCPUs': '4',  # Использовать 4 CPU ядра
    'MaxMemInQueues': '2 GB',
    'CircuitBuildTimeout': '30',
    'LearnCircuitBuildTimeout': '0',
    'CircuitIdleTimeout': '600',
    'MaxCircuitDirtiness': '300',
    'NewCircuitPeriod': '60',
    'EnforceDistinctSubnets': '1',
    'AllowSingleHopCircuits': '0',
    'AllowSingleHopExits': '0'
}

# Конфигурация для максимальной анонимности
privacy_config = {
    'SocksPort': '9050',
    'ControlPort': '9051',
    'CookieAuthentication': '1',
    'StrictNodes': '1',
    'ExitNodes': '{ch},{de},{nl}',
    'ExcludeNodes': '{us},{gb}',
    'ExcludeExitNodes': '{us},{gb}',
    'UseEntryGuards': '1',
    'NumEntryGuards': '3',
    'UseGuardFraction': '1',
    'UseEntryGuards': '1',
    'UseEntryGuards': '1',
    'GuardLifetime': '2592000',  # 30 дней
    'NumCircuits': '6'
}

# Конфигурация для high-bandwidth использования
bandwidth_config = {
    'SocksPort': '9050',
    'ControlPort': '9051',
    'CookieAuthentication': '1',
    'CircuitStreamTimeout': '60',
    'CircuitBuildTimeout': '20',
    'MaxCircuitDirtiness': '300',
    'NewCircuitPeriod': '30',
    'NumCircuits': '8',
    'UseEntryGuards': '0',  # Для скорости
    'AllowSingleHopCircuits': '1'  # Для скорости
}
```

### Автоматическая Оптимизация

```python
class TorOptimizer:
    def __init__(self, tor_manager):
        self.tor_manager = tor_manager
        self.performance_history = []
    
    def measure_performance(self):
        """Измерение текущей производительности"""
        start_time = time.time()
        
        # Тестовый запрос
        status_code, response = self.tor_manager.client.http_request(
            "GET", "http://httpbin.org/ip"
        )
        
        latency = (time.time() - start_time) * 1000
        
        return {
            'timestamp': time.time(),
            'latency': latency,
            'success': status_code == 200,
            'response_size': len(response) if response else 0
        }
    
    def optimize_for_speed(self):
        """Оптимизация для скорости"""
        config = bandwidth_config.copy()
        return self.tor_manager.start_tor_with_config(config)
    
    def optimize_for_privacy(self):
        """Оптимизация для приватности"""
        config = privacy_config.copy()
        return self.tor_manager.start_tor_with_config(config)
    
    def auto_optimize(self):
        """Автоматическая оптимизация на основе истории"""
        if len(self.performance_history) < 10:
            return False
        
        # Анализ производительности
        avg_latency = sum(p['latency'] for p in self.performance_history) / len(self.performance_history)
        success_rate = sum(p['success'] for p in self.performance_history) / len(self.performance_history)
        
        # Решение об оптимизации
        if avg_latency > 5000:  # > 5 секунд
            print("Высокая задержка, оптимизация для скорости...")
            return self.optimize_for_speed()
        elif success_rate < 0.8:  # < 80% успеха
            print("Низкая成功率, оптимизация для надежности...")
            return self.optimize_for_speed()
        else:
            print("Производительность в норме")
            return True

# Использование оптимизатора
optimizer = TorOptimizer(tor_manager)

# Сбор метрик
for _ in range(10):
    perf = optimizer.measure_performance()
    optimizer.performance_history.append(perf)
    time.sleep(1)

# Автоматическая оптимизация
optimizer.auto_optimize()
```

## 🚨 Безопасность и Предупреждения

### Безопасное Использование

```python
class SecureTorManager:
    def __init__(self, tor_manager):
        self.tor_manager = tor_manager
        self.security_policies = {
            'allow_clearnet': False,
            'max_circuit_lifetime': 3600,  # 1 час
            'require_https': True,
            'block_malicious_domains': True,
            'enable_circuit_rotation': True,
            'rotation_interval': 1800  # 30 минут
        }
    
    def is_domain_safe(self, domain):
        """Проверка безопасности домена"""
        malicious_domains = [
            'malware.example.com',
            'phishing.example.com'
        ]
        
        return domain not in malicious_domains
    
    def validate_request(self, url):
        """Валидация запроса"""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # Проверка HTTPS
        if self.security_policies['require_https'] and parsed.scheme != 'https':
            return False, "Только HTTPS разрешен"
        
        # Проверка домена
        if self.security_policies['block_malicious_domains']:
            if not self.is_domain_safe(parsed.netloc):
                return False, "Домен заблокирован"
        
        return True, "OK"
    
    def secure_request(self, method, url, **kwargs):
        """Безопасный запрос через Tor"""
        # Валидация
        is_valid, reason = self.validate_request(url)
        if not is_valid:
            raise SecurityError(f"Запрос отклонен: {reason}")
        
        # Выполнение запроса
        return self.tor_manager.client.http_request(method, url, **kwargs)

# Использование безопасного менеджера
secure_tor = SecureTorManager(tor_manager)

try:
    status, response = secure_tor.secure_request(
        "GET", "https://example.com"
    )
    print(f"Успешный запрос: {status}")
except SecurityError as e:
    print(f"Ошибка безопасности: {e}")
```

### Ротация и Обновление

```python
# Автоматическая ротация circuits
def setup_circuit_rotation():
    """Настройка автоматической ротации circuits"""
    import threading
    
    def rotation_worker():
        while True:
            try:
                # Закрытие старых circuits
                old_circuits = list(tor_manager.controller.circuits.keys())
                for circuit_id in old_circuits:
                    tor_manager.controller.close_circuit(circuit_id)
                
                # Создание новых circuits
                for _ in range(3):  # 3 новых circuits
                    config = TorCircuitConfig(circuit_type=TorCircuitType.STANDARD)
                    tor_manager.controller.create_circuit(config)
                
                print("Circuits ротированы")
                time.sleep(1800)  # 30 минут
                
            except Exception as e:
                print(f"Ошибка ротации: {e}")
                time.sleep(60)  # Повторить через 1 минуту
    
    rotation_thread = threading.Thread(target=rotation_worker)
    rotation_thread.daemon = True
    rotation_thread.start()

# Запуск ротации
setup_circuit_rotation()
```

## 🎯 Лучшие Практики

### 1. Выбор Exit Nodes
- Используйте надежные exit nodes с высоким bandwidth
- Избегайте узлов в странах с ограниченным интернетом
- Регулярно обновляйте списки исключенных узлов

### 2. Управление Circuits
- Создавайте отдельные circuits для разных задач
- Используйте long-lived circuits для постоянных соединений
- Регулярно ротируйте circuits для безопасности

### 3. Bridge Использование
- Используйте несколько bridges для надежности
- Регулярно тестируйте производительность bridges
- Комбинируйте разные типы transports

### 4. Hidden Сервисы
- Используйте сильные ключи для hidden сервисов
- Регулярно создавайте backup приватных ключей
- Мониторите доступность сервисов

### 5. Производительность
- Оптимизируйте конфигурацию под ваши задачи
- Используйте connection pooling для множественных запросов
- Мониторите latency и success rate

---

Это руководство предоставляет comprehensive обзор Tor интеграции в RSecure. Для дополнительной информации смотрите [DPI обход](dpi-bypass-guide.md) и [VPN/прокси](vpn-proxy-guide.md).
