# 📚 RSecure - Полное Руководство Пользователя

## 🌟 Добро пожаловать в RSecure!

RSecure - это революционная система безопасности с нейросетевым анализом, DPI обходом и многоуровневой защитой. Это руководство поможет вам освоить все возможности системы.

## 🚀 Быстрый Старт

### Системные Требования

- **Python 3.11+** (рекомендуется 3.11.5+)
- **macOS/Linux** (Windows частичная поддержка)
- **8GB+ RAM** (16GB+ рекомендуется для DPI обхода)
- **2GB+ дискового пространства**
- **Доступ в интернет** (для LLM и Tor)

### Установка за 5 Минут

```bash
# 1. Клонирование репозитория
git clone https://github.com/your-repo/rsecure.git
cd rsecure

# 2. Создание виртуального окружения
python3.11 -m venv rsecure_env
source rsecure_env/bin/activate  # macOS/Linux
# rsecure_env\Scripts\activate  # Windows

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Установка Ollama
brew install ollama && brew services start ollama  # macOS
# sudo apt install ollama && sudo systemctl start ollama  # Linux
ollama pull qwen2.5-coder:1.5b
ollama pull gemma2:2b

# 5. Установка Tor (опционально)
brew install tor && brew services start tor  # macOS
# sudo apt install tor && sudo systemctl start tor  # Linux

# 6. Запуск RSecure
python rsecure/rsecure_main.py
```

## 🎯 Первые Шаги

### 1. Запуск Базовой Защиты

```bash
# Простой запуск с базовыми настройками
python rsecure/rsecure_main.py

# Запуск с веб-дешбордом
python run_rsecure_with_dashboard.py

# Запуск простого дешборда
python simple_dashboard.py
```

### 2. Проверка Работоспособности

После запуска вы должны увидеть:

```
🛡️ RSecure Security System Started
✅ Neural Security Core: Active
✅ Ollama Integration: Connected
✅ System Detection: Running
✅ Network Defense: Active
🌐 Web Dashboard: http://127.0.0.1:5000
```

### 3. Открытие Веб-Дешборда

Откройте браузер и перейдите на `http://127.0.0.1:5000`

Вы увидите:
- 🖥️ Мониторинг системы в реальном времени
- 📊 Графики использования ресурсов
- 🌐 Сетевая активность
- ⚠️ Уровень угроз
- 🔄 Статус модулей

## 🔧 Конфигурация

### Базовая Конфигурация

Откройте `rsecure_config.json`:

```json
{
  "system_detection": {"enabled": true},
  "monitoring": {
    "enabled": true,
    "log_interval": 1,
    "network_scan_interval": 30
  },
  "neural_core": {
    "enabled": true,
    "threat_threshold": 0.7
  },
  "network_defense": {
    "enabled": true,
    "monitored_ports": [22, 80, 443]
  },
  "dpi_bypass": {
    "enabled": false,
    "default_method": "fragmentation"
  },
  "traffic_obfuscation": {
    "enabled": false,
    "default_method": "aes"
  }
}
```

### Включение DPI Обхода

Для включения DPI обхода измените конфигурацию:

```json
{
  "dpi_bypass": {
    "enabled": true,
    "default_method": "adaptive",
    "tor_enabled": true,
    "vpn_enabled": false,
    "auto_rotate_methods": true
  }
}
```

### Настройка Оповещений

```json
{
  "notifications": {
    "enabled": true,
    "methods": ["desktop", "email"],
    "threshold": 0.8,
    "cooldown": 300
  }
}
```

## 🔓 DPI Обход - Пошаговая Инструкция

### Шаг 1: Базовый Обход

```python
from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod

# Создание движка обхода
engine = DPIBypassEngine()

# Базовая конфигурация
config = BypassConfig(
    method=BypassMethod.FRAGMENTATION,
    target_host="example.com",
    target_port=80,
    fragment_size=256,
    delay_ms=50
)

# Запуск обхода
success = engine.bypass_dpi(config)
print(f"Обход успешен: {success}")
```

### Шаг 2: Автоматический Выбор Метода

```python
from rsecure.modules.defense.dpi_bypass import AdvancedBypassTechniques

advanced = AdvancedBypassTechniques()

# Автоматический выбор лучшего метода
config = BypassConfig(
    method=BypassMethod.ADAPTIVE,
    target_host="blocked-site.com",
    target_port=443
)

success = advanced.adaptive_bypass(config)
```

### Шаг 3: Многослойная Защита

```python
# Комбинирование с обфускацией
from rsecure.modules.defense.traffic_obfuscation import AdvancedObfuscation, ObfuscationMethod

obfuscator = AdvancedObfuscation()

# Создание многослойной защиты
data = b"secret data"
obfuscated = obfuscator.create_layered_obfuscation(
    data,
    [
        ObfuscationMethod.ZLIB,      # Сжатие
        ObfuscationMethod.BASE64,    # Кодирование
        ObfuscationMethod.AES,       # Шифрование
        ObfuscationMethod.XOR        # Дополнительная обфускация
    ]
)
```

## 🛡️ VPN и Прокси Использование

### Шаг 1: Настройка Прокси

```python
from rsecure.modules.defense.vpn_proxy import ProxyServer, ProxyConfig, ProxyType

# HTTP прокси
config = ProxyConfig(
    proxy_type=ProxyType.HTTP,
    host="0.0.0.0",
    port=8080,
    username="user",
    password="pass"
)

proxy = ProxyServer(config)
proxy.start()
print(f"Прокси запущен на порту {config.port}")
```

### Шаг 2: VPN Подключение

```python
from rsecure.modules.defense.vpn_proxy import VPNManager, VPNConfig, VPNType

vpn_manager = VPNManager()

# OpenVPN конфигурация
config = VPNConfig(
    vpn_type=VPNType.OPENVPN,
    server_host="vpn.example.com",
    server_port=1194,
    protocol="udp"
)

# Подключение
connection_id = vpn_manager.connect_vpn(config)
print(f"VPN подключен: {connection_id}")
```

### Шаг 3: Цепочки Прокси

```python
from rsecure.modules.defense.vpn_proxy import ProxyChain

chain = ProxyChain()

# Добавление прокси в цепочку
chain.add_proxy(ProxyConfig(ProxyType.HTTP, "proxy1.com", 8080))
chain.add_proxy(ProxyConfig(ProxyType.SOCKS5, "proxy2.com", 1080))

# Создание цепочки
chain.create_chain([0, 1])

# Подключение через цепочку
sock = chain.connect_through_chain("target.com", 80)
```

## 🌐 Tor Анонимность

### Шаг 1: Запуск Tor

```python
from rsecure.modules.defense.tor_integration import TorIntegrationManager

tor_manager = TorIntegrationManager()

# Запуск Tor
if tor_manager.start_tor():
    print("Tor успешно запущен")
    
    # Проверка статуса
    status = tor_manager.get_tor_status()
    print(f"Tor circuits: {status['circuits']}")
```

### Шаг 2: Создание Hidden Сервиса

```python
# Создание hidden сервиса
onion_address = tor_manager.create_hidden_service(
    "my_service", 
    local_port=8080
)

print(f"Hidden сервис: {onion_address}")
```

### Шаг 3: Анонимные Запросы

```python
# HTTP запрос через Tor
status_code, response = tor_manager.client.http_request(
    "GET", "http://httpbin.org/ip"
)

print(f"Status: {status_code}")
print(f"Response: {response.decode()}")
```

## 🔐 Обфускация Трафика

### Базовая Обфускация

```python
from rsecure.modules.defense.traffic_obfuscation import TrafficObfuscator, ObfuscationConfig, ObfuscationMethod

obfuscator = TrafficObfuscator()

# AES шифрование
config = ObfuscationConfig(
    method=ObfuscationMethod.AES,
    encryption_key=b"your_32_byte_secret_key_here!!"
)

data = b"secret information"
encrypted = obfuscator.obfuscate_data(data, config)
```

### Мимикрия Протоколов

```python
# Маскировка под HTTP
config = ObfuscationConfig(
    method=ObfuscationMethod.PROTOCOL_MIMICKING,
    protocol_mimic=ProtocolType.HTTP
)

http_mimicked = obfuscator.obfuscate_data(data, config)
```

### Стеганография

```python
# Скрытие данных в изображении
config = ObfuscationConfig(
    method=ObfuscationMethod.STEGANOGRAPHY,
    steganography_medium="image"
)

hidden = obfuscator.obfuscate_data(data, config)
```

## 📊 Мониторинг и Аналитика

### Просмотр Статистики

```python
# Получение статистики DPI обхода
from rsecure.modules.defense.dpi_bypass import BypassManager

manager = BypassManager()
history = manager.get_bypass_history()

for bypass in history[-5:]:  # Последние 5
    print(f"{bypass['method']}: {bypass['success']} - {bypass['target']}")
```

### Health Checks

```python
# Проверка здоровья системы
def health_check():
    checks = {
        'neural_core': check_neural_core(),
        'ollama': check_ollama(),
        'tor': check_tor(),
        'proxies': check_proxies()
    }
    
    for component, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component}: {'OK' if status else 'FAILED'}")

health_check()
```

### Метрики Производительности

```python
# Получение метрик
def get_performance_metrics():
    import psutil
    import time
    
    # Системные метрики
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Метрики RSecure
    rsecure_metrics = {
        'active_connections': len(manager.active_connections),
        'bypass_success_rate': calculate_success_rate(),
        'avg_latency': calculate_avg_latency()
    }
    
    return {
        'cpu': cpu_percent,
        'memory': memory_percent,
        'disk': disk_usage,
        'rsecure': rsecure_metrics
    }

metrics = get_performance_metrics()
print(f"CPU: {metrics['cpu']}%")
print(f"Memory: {metrics['memory']}%")
print(f"Success Rate: {metrics['rsecure']['bypass_success_rate']}%")
```

## 🚨 Устранение Неполадок

### Частые Проблемы

#### 1. Ollama Не Запускается

**Проблема:** `Ollama connection failed`

**Решение:**
```bash
# Проверка статуса Ollama
brew services list | grep ollama

# Перезапуск Ollama
brew services restart ollama

# Проверка порта
curl http://localhost:11434/api/tags
```

#### 2. Tor Не Подключается

**Проблема:** `Tor connection failed`

**Решение:**
```bash
# Проверка статуса Tor
brew services list | grep tor

# Перезапуск Tor
brew services restart tor

# Проверка портов
telnet 127.0.0.1 9050
telnet 127.0.0.1 9051
```

#### 3. DPI Обход Не Работает

**Проблема:** `Bypass failed`

**Решение:**
```python
# Диагностика
diagnostic = engine.diagnose_connection(target_host, target_port)
print(diagnostic)

# Попробовать другой метод
methods = [BypassMethod.TOR_ROUTING, BypassMethod.VPN_TUNNELING]
for method in methods:
    config.method = method
    if engine.bypass_dpi(config):
        print(f"Успешно с методом: {method.value}")
        break
```

#### 4. Высокая Загрузка CPU

**Проблема:** Высокая загрузка процессора

**Решение:**
```python
# Оптимизация производительности
config = {
    "neural_core": {
        "batch_processing": True,
        "max_threads": 2,
        "gpu_acceleration": False
    },
    "dpi_bypass": {
        "max_concurrent_bypasses": 3,
        "timeout": 30
    }
}

# Обновление конфигурации
update_config(config)
```

### Логирование и Отладка

### Включение Детального Логирования

```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rsecure.log'),
        logging.StreamHandler()
    ]
)

# Логирование RSecure
logger = logging.getLogger('rsecure')
logger.info("RSecure запущен")
```

### Просмотр Логов

```bash
# Просмотр логов в реальном времени
tail -f rsecure.log

# Поиск ошибок
grep "ERROR" rsecure.log

# Поиск DPI обхода
grep "bypass" rsecure.log
```

### Диагностика Системы

```python
def full_system_diagnostic():
    """Полная диагностика системы"""
    print("🔍 Полная диагностика RSecure")
    print("=" * 50)
    
    # 1. Проверка Python
    print(f"Python version: {sys.version}")
    
    # 2. Проверка зависимостей
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch не установлен")
    
    try:
        import stem
        print(f"✅ Stem (Tor): {stem.__version__}")
    except ImportError:
        print("❌ Stem не установлен")
    
    # 3. Проверка Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama: подключен")
        else:
            print("❌ Ollama: ошибка подключения")
    except:
        print("❌ Ollama: недоступен")
    
    # 4. Проверка Tor
    try:
        import stem.socket
        controller = stem.socket.ControlPort(port=9051)
        controller.authenticate()
        print("✅ Tor: подключен")
        controller.close()
    except:
        print("❌ Tor: недоступен")
    
    # 5. Проверка памяти
    import psutil
    memory = psutil.virtual_memory()
    print(f"📊 Memory: {memory.percent}% использовано")
    
    # 6. Проверка диска
    disk = psutil.disk_usage('/')
    print(f"💾 Disk: {disk.percent}% использовано")

full_system_diagnostic()
```

## 🎯 Продвинутое Использование

### Автоматизация

```python
# Автоматический обход с ротацией
import threading
import time

def auto_bypass_worker():
    """Автоматический обход в фоне"""
    while True:
        try:
            # Получение списка целей
            targets = get_blocked_sites()
            
            for target in targets:
                # Попытка обхода
                config = BypassConfig(
                    method=BypassMethod.ADAPTIVE,
                    target_host=target['host'],
                    target_port=target['port']
                )
                
                success = engine.bypass_dpi(config)
                
                # Логирование результата
                log_bypass_attempt(target, success)
                
                # Задержка между попытками
                time.sleep(1)
            
            # Пауза между циклами
            time.sleep(300)  # 5 минут
            
        except Exception as e:
            print(f"Ошибка auto bypass: {e}")
            time.sleep(60)

# Запуск автоматизации
auto_thread = threading.Thread(target=auto_bypass_worker)
auto_thread.daemon = True
auto_thread.start()
```

### Планировщик Задач

```python
# Планировщик для регулярных задач
import schedule
import time

def daily_security_scan():
    """Ежедневное сканирование безопасности"""
    print("🔍 Запуск ежедневного сканирования...")
    
    # Проверка всех систем
    health_check()
    
    # Тестирование методов обхода
    test_bypass_methods()
    
    # Обновление баз данных
    update_threat_database()
    
    print("✅ Сканирование завершено")

def weekly_optimization():
    """Еженедельная оптимизация"""
    print("⚡ Запуск еженедельной оптимизации...")
    
    # Оптимизация конфигурации
    optimize_configuration()
    
    # Очистка логов
    cleanup_logs()
    
    # Обновление зависимостей
    update_dependencies()
    
    print("✅ Оптимизация завершена")

# Настройка расписания
schedule.every().day.at("02:00").do(daily_security_scan)
schedule.every().sunday.at("03:00").do(weekly_optimization)

# Запуск планировщика
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Интеграция с Другими Системами

```python
# API для внешних систем
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/bypass', methods=['POST'])
def api_bypass():
    """API для DPI обхода"""
    data = request.json
    
    config = BypassConfig(
        method=BypassMethod(data['method']),
        target_host=data['target_host'],
        target_port=data['target_port']
    )
    
    success = engine.bypass_dpi(config)
    
    return jsonify({
        'success': success,
        'method': data['method'],
        'target': f"{data['target_host']}:{data['target_port']}"
    })

@app.route('/api/status', methods=['GET'])
def api_status():
    """API статуса системы"""
    return jsonify({
        'neural_core': check_neural_core(),
        'ollama': check_ollama(),
        'tor': check_tor(),
        'active_bypasses': len(manager.active_bypasses)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## 🔒 Безопасность и Лучшие Практики

### 1. Регулярные Обновления

```bash
# Обновление RSecure
git pull origin main
pip install -r requirements.txt

# Обновление Ollama моделей
ollama pull qwen2.5-coder:latest
```

### 2. Резервное Копирование

```bash
# Создание бэкапа конфигурации
cp rsecure_config.json rsecure_config.json.backup

# Бэкап логов
tar -czf logs_backup.tar.gz *.log
```

### 3. Мониторинг Безопасности

```python
def security_monitoring():
    """Мониторинг безопасности"""
    
    # Проверка на аномалии
    anomalies = detect_anomalies()
    
    # Проверка целостности
    integrity = check_integrity()
    
    # Проверка утечек
    leaks = check_data_leaks()
    
    if anomalies or not integrity or leaks:
        send_security_alert(anomalies, integrity, leaks)
```

### 4. Оптимизация Производительности

```python
def performance_tuning():
    """Настройка производительности"""
    
    # Оптимизация нейросети
    if torch.cuda.is_available():
        torch.set_num_threads(4)
    
    # Оптимизация памяти
    import gc
    gc.collect()
    
    # Настройка кэширования
    enable_caching()
```

## 📞 Поддержка и Сообщество

### Получение Помощи

1. **Документация:** `docs/` директория
2. **Примеры:** `examples/` директория  
3. **Тесты:** `tests/` директория
4. **Issues:** GitHub Issues

### Сообщение об Ошибках

При сообщении об ошибках включите:

```bash
# Системная информация
python --version
pip list | grep -E "(torch|stem|cryptography)"

# Логи RSecure
tail -n 100 rsecure.log

# Диагностика
python -c "
from rsecure.modules.defense.dpi_bypass import DPIBypassEngine
engine = DPIBypassEngine()
print(engine.get_system_info())
"
```

### Участие в Разработке

1. Fork репозитория
2. Создание feature branch
3. Внесение изменений
4. Создание Pull Request

---

## 🎉 Поздравляем!

Вы теперь готовы использовать RSecure для максимальной безопасности и анонимности. Начните с базовых функций и постепенно изучайте продвинутые возможности.

**Помните:** RSecure - мощный инструмент. Используйте его ответственно и в соответствии с законодательством вашей страны.

**Следующие шаги:**
- 📖 Изучите [документацию](docs/)
- 🔧 Попробуйте [примеры](examples/)
- 🧪 Запустите [тесты](tests/)
- 🌐 Присоединяйтесь к [сообществу](https://github.com/your-repo/rsecure)

**Безопасных вам подключений!** 🛡️
