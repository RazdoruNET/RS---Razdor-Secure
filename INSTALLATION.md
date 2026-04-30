# 🚀 Установка и Запуск RSecure

## 🌟 Обзор Системы

RSecure - это революционная система безопасности с:
- 🧠 **Нейросетевым анализом** и LLM интеграцией
- 🔓 **DPI обходом** (10+ методов)
- 🛡️ **VPN и прокси** поддержкой
- 🔐 **Обфускацией трафика** и стеганографией
- 🌐 **Tor интеграцией** и hidden сервисами
- ⚡ **Адаптивной защитой** с обучением

## 📋 Системные Требования

### Минимальные Требования:
- **Python 3.11+** (рекомендуется 3.11.5+)
- **macOS/Linux** (Windows частичная поддержка)
- **8GB RAM** (16GB+ рекомендуется для DPI обхода)
- **2GB дискового пространства**
- **Доступ в интернет**

### Рекомендуемые Требования:
- **Python 3.11.8+**
- **16GB+ RAM**
- **4+ CPU ядра**
- **SSD диск**
- **Стабильное интернет соединение**

## 🔧 Быстрая Установка (5 минут)

### Шаг 1: Подготовка Системы

```bash
# 1.1 Клонирование репозитория
git clone https://github.com/your-repo/rsecure.git
cd rsecure

# 1.2 Создание виртуального окружения
python3.11 -m venv rsecure_env
source rsecure_env/bin/activate  # macOS/Linux
# rsecure_env\Scripts\activate  # Windows

# 1.3 Обновление pip
pip install --upgrade pip
```

### Шаг 2: Установка Базовых Зависимостей

```bash
# 2.1 Установка основных зависимостей
pip install -r requirements.txt

# 2.2 Дополнительные зависимости для DPI обхода
pip install cryptography stem pysocks requests

# 2.3 Зависимости для нейросетей
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 2.4 Опционально: TensorFlow для продвинутых функций
pip install tensorflow>=2.10.0
```

### Шаг 3: Установка Внешних Сервисов

```bash
# 3.1 Установка Ollama (для LLM анализа)
# macOS
brew install ollama && brew services start ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
sudo systemctl start ollama

# 3.2 Скачивание моделей Ollama
ollama pull qwen2.5-coder:1.5b
ollama pull gemma2:2b
ollama pull codeqwen

# 3.3 Установка Tor (для анонимности)
# macOS
brew install tor && brew services start tor

# Linux
sudo apt install tor  # Debian/Ubuntu
sudo yum install tor  # Fedora/CentOS
sudo systemctl start tor

# 3.4 Проверка установки
tor --version
ollama list
```

## 📚 Полная Список Зависимостей

### Основные зависимости:
- `torch>=2.0.0` - нейросети и тензорные вычисления
- `scikit-learn>=1.3.0` - ML алгоритмы
- `cryptography>=41.0.0` - шифрование и обфускация
- `stem>=1.8.0` - Tor контроллер
- `psutil>=5.9.0` - мониторинг системы
- `scapy>=2.5.0` - анализ сетевых пакетов
- `requests>=2.31.0` - HTTP запросы
- `flask>=2.3.0` - веб-интерфейс
- `numpy>=1.24.0`, `pandas>=2.0.0` - обработка данных

### Дополнительные зависимости:
- `pysocks>=1.7.1` - SOCKS прокси
- `pyyaml>=6.0` - конфигурация
- `matplotlib>=3.7.0` - визуализация
- `seaborn>=0.12.0` - статистическая визуализация
- `jupyter>=1.0.0` - notebooks для анализа
- `pytest>=7.4.0` - тестирование

### Опциональные зависимости:
- `tensorflow>=2.13.0` - продвинутые нейросети
- `opencv-python>=4.8.0` - компьютерное зрение
- `sounddevice>=0.4.6` - аудио мониторинг
- `pillow>=10.0.0` - обработка изображений
- `websockets>=11.0.0` - real-time коммуникации

## 🚀 Запуск Системы

### Вариант 1: Полная система с дешбордом (рекомендуется)

```bash
# Запуск с полным функционалом
python run_rsecure_with_dashboard.py

# Или с конфигурацией
python run_rsecure_with_dashboard.py --config rsecure_config.json
```

**Запускает:**
- ✅ Все модули безопасности RSecure
- ✅ DPI обход и обфускацию
- ✅ VPN/Tor интеграцию
- ✅ Нейросетевой анализ
- ✅ Веб-дашборд на http://127.0.0.1:5001
- ✅ Автоматическую корреляцию данных

### Вариант 2: Только дашборд (минимальный режим)

```bash
python simple_dashboard.py
```

**Запускает:**
- 📊 Базовый дашборд на http://127.0.0.1:5000
- 📈 Системные метрики
- 🌐 Базовый сетевой мониторинг

### Вариант 3: Консольный режим

```bash
cd rsecure
python rsecure_main.py
```

**Запускает:**
- 🛡️ Все модули безопасности без веб-интерфейса
- 📝 Консольный вывод
- 🔍 Интерактивный режим

### Вариант 4: DPI обход режим

```bash
python ollama_rsecure.py
```

**Запускает:**
- 🔓 DPI bypass функциональность
- 🧠 LLM интеграцию
- 🌐 Tor/VPN маршрутизацию

## 🎯 Первоначальная Настройка

### Шаг 1: Проверка Установки

```bash
# Проверка Python
python --version

# Проверка зависимостей
pip list | grep -E "(torch|cryptography|stem|scikit)"

# Проверка Ollama
curl http://localhost:11434/api/tags

# Проверка Tor
curl -s --socks5 127.0.0.1:9050 http://httpbin.org/ip
```

### Шаг 2: Базовая Конфигурация

Создайте `rsecure_config.json`:

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
    "enabled": true,
    "default_method": "adaptive",
    "tor_enabled": true
  },
  "traffic_obfuscation": {
    "enabled": true,
    "default_method": "aes"
  },
  "ollama": {
    "enabled": true,
    "host": "localhost",
    "port": 11434,
    "models": ["qwen2.5-coder:1.5b", "gemma2:2b"]
  }
}
```

## 🌐 Веб-Интерфейс и API

### Основной Дашборд

**URL:** http://127.0.0.1:5001

**Функции:**
- 🖥️ **Системный мониторинг** - CPU, память, диск в реальном времени
- 🌐 **Сетевая активность** - соединения, интерфейсы, трафик
- 🛡️ **Статус защиты** - активные модули, уровень угроз
- 🔓 **DPI bypass** - статус обхода, методы, статистика
- 🌐 **Tor/VPN статус** - circuits, соединения, hidden сервисы
- 📊 **Аналитика** - графики, метрики, тренды
- ⚠️ **Оповещения** - реальные уведомления о угрозах

### API Endpoints

```bash
# Системный статус
GET /api/status

# Метрики производительности
GET /api/metrics

# DPI bypass статус
GET /api/dpi_bypass/status
GET /api/dpi_bypass/methods
GET /api/dpi_bypass/history

# VPN/Proxy статус
GET /api/vpn/status
GET /api/proxy/status

# Tor статус
GET /api/tor/status
GET /api/tor/circuits
GET /api/tor/hidden_services

# Обфускация
GET /api/obfuscation/status
POST /api/obfuscation/obfuscate

# Угрозы и безопасность
GET /api/threats
GET /api/security_events
GET /api/vulnerabilities

# Логи
GET /api/logs?type=security&lines=100
GET /api/logs?type=dpi_bypass&lines=50

# Нейросетевой анализ
GET /api/neural/status
POST /api/neural/analyze

# LLM анализ
GET /api/llm/status
POST /api/llm/query
```

### WebSocket Endpoints

```bash
# Real-time метрики
WS /ws/metrics

# Real-time события безопасности
WS /ws/security_events

# Real-time DPI bypass статус
WS /ws/dpi_bypass

# Real-time Tor статус
WS /ws/tor
```

## 📁 Структура Проекта

```
rsecure/
├── 📋 README.md                       # Основная документация
├── 📚 USER_GUIDE.md                  # Руководство пользователя
├── ⚙️ INSTALLATION.md                # Этот файл установки
├── 🚀 run_rsecure_with_dashboard.py   # Интегрированный лаунчер
├── 📊 simple_dashboard.py              # Простой дашборд
├── 🧪 test_rsecure.py                  # Тесты системы
├── rsecure/
│   ├── 🎯 rsecure_main.py              # Основная система
│   ├── 🛠️ utils/
│   │   ├── 📊 dashboard.py             # Веб-дашборд
│   │   └── 📝 monitoring_logger.py     # Логирование
│   ├── 🔧 modules/                      # Модули безопасности
│   │   ├── 🔍 detection/                # Детекция угроз
│   │   │   ├── 🎣 phishing_detector.py
│   │   │   ├── 💻 system_detector.py
│   │   │   └── 🛡️ cvu_intelligence.py
│   │   ├── 🛡️ defense/                  # Защита
│   │   │   ├── 🌐 network_defense.py
│   │   │   ├── 🤖 llm_defense.py
│   │   │   ├── 🔓 dpi_bypass.py           # DPI обход (10+ методов)
│   │   │   ├── 🔐 traffic_obfuscation.py  # Обфускация трафика
│   │   │   ├── 🌐 tor_integration.py       # Tor интеграция
│   │   │   ├── 🛡️ vpn_proxy.py             # VPN и прокси
│   │   │   └── 🎮 system_control.py
│   │   ├── 📈 monitoring/               # Мониторинг
│   │   │   ├── 🎵 audio_stream_monitor.py
│   │   │   └── 📹 audio_video_monitor.py
│   │   ├── 🧠 protection/               # Психологическая защита
│   │   │   └── 🛡️ psychological_protection.py
│   │   ├── 🔬 analysis/                 # Анализ безопасности
│   │   │   └── 📊 security_analytics.py
│   │   └── 🔔 notification/             # Уведомления
│   │       └── 🍎 macos_notifications.py
│   ├── 🧠 core/                         # Нейросетевое ядро
│   │   ├── 🧬 neural_security_core.py
│   │   ├── 🎮 reinforcement_learning.py
│   │   └── 🤖 ollama_integration.py   # Интеграция с Ollama
│   ├── ⚙️ config/                       # Конфигурация
│   │   └── 🛡️ offline_threats.json
│   └── 🧪 tests/                        # Тесты
│       ├── 🔍 test_dpi_bypass.py          # Тесты DPI обхода
│       ├── 🛡️ test_vpn_proxy.py            # Тесты VPN/прокси
│       ├── 🔐 test_traffic_obfuscation.py # Тесты обфускации
│       ├── 🌐 test_tor_integration.py     # Тесты Tor
│       └── 🧪 rsecure_test.py
├── 📋 templates/
│   └── 🌐 dashboard.html               # HTML шаблон
├── 🎨 assets/
│   └── 🖼️ we_razdor_logo.png            # Логотип
├── 🧪 mock_libs/                       # Mock библиотеки
│   └── 🧬 tensorflow.py                # Для тестов без TensorFlow
├── 📚 docs/                             # Документация
│   ├── 📖 README.md
│   ├── 🏗️ architecture/
│   │   └── 📋 overview.md
│   ├── 🔬 research/
│   │   ├── 🔬 scientific-foundations.md
│   │   └── 🧠 neural-wave-scientific-foundations.md
│   ├── 🛡️ defense/
│   │   ├── 🔓 dpi-bypass-guide.md        # DPI обход руководство
│   │   ├── 🛡️ vpn-proxy-guide.md         # VPN/прокси руководство
│   │   ├── 🔐 traffic-obfuscation-guide.md # Обфускация руководство
│   │   ├── 🌐 tor-integration-guide.md    # Tor интеграция руководство
│   │   ├── 🧠 neural-wave-protection.md
│   │   ├── 🛡️ wifi-antipositioning-defense.md
│   │   └── 🎭 psychological-protection.md
│   └── 📚 algorithms/
│       ├── 📈 behavioral-analysis.md
│       └── 🌊 spectral-analysis.md
├── 📝 logs/                              # Логи системы
└── 🧪 rsecure_models/                    # Модели RSecure
    ├── 🔍 rsecure-scanner.modelfile
    ├── 🤖 rsecure-analyst.modelfile
    └── 🛡️ rsecure-security.modelfile
```

## 🛡️ Модули Безопасности

### 🔓 DPI Обход и Сетевая Свобода
- **DPI Bypass Engine** - 10+ методов обхода инспекции
- **Traffic Obfuscation** - AES, ChaCha20, стеганография
- **VPN & Proxy Manager** - OpenVPN, WireGuard, SOCKS5, Shadowsocks
- **Tor Integration** - полный контроль Tor сети
- **Protocol Mimicry** - мимикрия под легальные протоколы
- **Multi-layer Protection** - комбинирование методов

### 🧠 Нейросетевая Защита
- **Neural Security Core** - многослойные нейросети
- **Reinforcement Learning** - адаптивное обучение
- **Ollama Integration** - LLM анализ угроз
- **Hybrid Analysis** - комбинация нейросетей и LLM
- **Real-time Processing** - обработка в реальном времени

### 🌐 Сетевая Защита
- **Network Defense** - активная защита от атак
- **Port Scanning Detection** - детекция сканирования портов
- **DDoS Protection** - защита от DDoS атак
- **Intrusion Detection** - детекция вторжений
- **Firewall Management** - управление файрволом

### 🔍 Детекция Угроз
- **Phishing Detector** - нейросетевая детекция фишинга
- **System Detector** - мониторинг системных угроз
- **Vulnerability Scanner** - сканирование уязвимостей
- **Malware Detection** - детекция вредоносного ПО
- **Anomaly Detection** - обнаружение аномалий

### 🛡️ Продвинутая Защита
- **WiFi Anti-Positioning** - защита от WiFi отражений
- **Psychological Protection** - защита от психологических атак
- **LLM Defense** - защита от атак на языковые модели
- **Visual Security** - защита от визуальных атак
- **Audio/Video Monitor** - мониторинг медиа-устройств

### 📊 Аналитика и Мониторинг
- **Security Analytics** - анализ событий безопасности
- **Performance Monitoring** - мониторинг производительности
- **Threat Intelligence** - интеллект угроз
- **Behavioral Analysis** - анализ поведения

### 🔔 Управление и Оповещения
- **Dashboard Interface** - веб-интерфейс управления
- **REST API** - программный интерфейс
- **Real-time Alerts** - оповещения в реальном времени
- **macOS Notifications** - системные уведомления
- **Email Notifications** - email оповещения

## 🔧 Устранение Неполадок

### 🚨 Частые Проблемы

#### 1. Ошибки при Установке

**Проблема:** `pip install` ошибки

**Решение:**
```bash
# Обновите pip
pip install --upgrade pip setuptools wheel

# Установите по одному
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install scikit-learn cryptography stem
pip install psutil scapy flask requests

# Используйте virtualenv
python3.11 -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements.txt
```

#### 2. Ollama Не Запускается

**Проблема:** `Ollama connection failed`

**Решение:**
```bash
# Проверка статуса Ollama
brew services list | grep ollama  # macOS
sudo systemctl status ollama     # Linux

# Перезапуск Ollama
brew services restart ollama      # macOS
sudo systemctl restart ollama     # Linux

# Проверка порта
curl http://localhost:11434/api/tags

# Переустановка при необходимости
brew reinstall ollama  # macOS
```

#### 3. Tor Не Подключается

**Проблема:** `Tor connection failed`

**Решение:**
```bash
# Проверка статуса Tor
brew services list | grep tor    # macOS
sudo systemctl status tor        # Linux

# Проверка портов
telnet 127.0.0.1 9050  # SOCKS
telnet 127.0.0.1 9051  # Control

# Перезапуск Tor
brew services restart tor        # macOS
sudo systemctl restart tor      # Linux

# Проверка конфигурации
cat /usr/local/etc/tor/torrc  # macOS
cat /etc/tor/torrc           # Linux
```

#### 4. DPI Обход Не Работает

**Проблема:** `DPI bypass failed`

**Решение:**
```python
# Диагностика
from rsecure.modules.defense.dpi_bypass import DPIBypassEngine

engine = DPIBypassEngine()
diagnostic = engine.diagnose_connection("target.com", 80)
print(diagnostic)

# Попробовать другие методы
methods = ["tor_routing", "vpn_tunneling", "fragmentation"]
for method in methods:
    config.method = method
    if engine.bypass_dpi(config):
        print(f"Успешно: {method}")
        break
```

#### 5. Высокая Загрузка CPU

**Проблема:** Высокое использование CPU

**Решение:**
```json
{
  "neural_core": {
    "batch_processing": true,
    "max_threads": 2,
    "gpu_acceleration": false
  },
  "dpi_bypass": {
    "max_concurrent_bypasses": 3,
    "timeout": 30
  }
}
```

#### 6. Проблемы с Портами

**Проблема:** Порт 5000/5001 занят

**Решение:**
```bash
# Найти занятые порты
lsof -i :5000
lsof -i :5001

# Изменить порт в скрипте
# В run_rsecure_with_dashboard.py:
self.dashboard.run(host='127.0.0.1', port=5002, debug=False)

# Или использовать другой порт
python run_rsecure_with_dashboard.py --port 5003
```

### 🔍 Диагностика Системы

```bash
#!/bin/bash
# Полная диагностика RSecure
echo "🔍 Диагностика RSecure"
echo "========================="

# Проверка Python
echo "🐍 Python:"
python --version

# Проверка зависимостей
echo "\n📦 Зависимости:"
pip list | grep -E "(torch|scikit|cryptography|stem|flask)"

# Проверка Ollama
echo "\n🤖 Ollama:"
curl -s http://localhost:11434/api/tags | head -5

# Проверка Tor
echo "\n🌐 Tor:"
curl -s --socks5 127.0.0.1:9050 http://httpbin.org/ip | head -5

# Проверка памяти
echo "\n💾 Память:"
free -h 2>/dev/null || vm_stat 2>/dev/null || echo "N/A"

# Проверка диска
echo "\n💾 Диск:"
df -h .
except ImportError as e:
    print(f'❌ Отсутствует зависимость: {e}')
"

# 3. Проверка Ollama
curl -s http://localhost:11434/api/tags | jq -r '.models[0].name' 2>/dev/null || echo "❌ Ollama недоступен"

# 4. Проверка Tor
curl -s --socks5 127.0.0.1:9050 http://httpbin.org/ip | jq -r '.origin' 2>/dev/null || echo "❌ Tor недоступен"
```

### Запуск Тестового Сценария

```python
#!/usr/bin/env python3
# test_rsecure_installation.py

import sys
import requests
import time

def test_installation():
    print("🧪 Тестирование установки RSecure")
    print("=" * 40)
    
    tests = [
        ("Python версия", test_python_version),
        ("Зависимости", test_dependencies),
        ("Ollama подключение", test_ollama),
        ("Tor подключение", test_tor),
        ("DPI обход", test_dpi_bypass),
        ("Веб-интерфейс", test_web_interface)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "✅" if result else "❌"
            print(f"{status} {test_name}: {'OK' if result else 'FAILED'}")
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Итоги
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 RSecure полностью готов к использованию!")
        return True
    else:
        print("⚠️ Есть проблемы, требующие внимания")
        return False

def test_python_version():
    version = sys.version_info
    return version.major >= 3 and version.minor >= 11

def test_dependencies():
    try:
        import torch, cryptography, stem, flask, scikit_learn
        return True
    except ImportError:
        return False

def test_ollama():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_tor():
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 9050))
        sock.close()
        return result == 0
    except:
        return False

def test_dpi_bypass():
    try:
        from rsecure.modules.defense.dpi_bypass import DPIBypassEngine
        engine = DPIBypassEngine()
        return True
    except ImportError:
        return False

def test_web_interface():
    try:
        response = requests.get("http://127.0.0.1:5001/api/status", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    test_installation()
```

## 📚 Дополнительные Ресурсы

### 📖 Документация
- [📋 USER_GUIDE.md](USER_GUIDE.md) - полное руководство пользователя
- [🔓 DPI Bypass Guide](docs/defense/dpi-bypass-guide.md) - DPI обход
- [🛡️ VPN/Proxy Guide](docs/defense/vpn-proxy-guide.md) - VPN и прокси
- [🔐 Traffic Obfuscation Guide](docs/defense/traffic-obfuscation-guide.md) - обфускация
- [🌐 Tor Integration Guide](docs/defense/tor-integration-guide.md) - Tor интеграция
- [🏗️ Architecture Overview](docs/architecture/overview.md) - архитектура системы

### 🧪 Примеры Кода
```bash
# Запуск примеров
python examples/dpi_bypass_example.py
python examples/vpn_setup_example.py
python examples/tor_hidden_service_example.py
python examples/traffic_obfuscation_example.py
```

### 🎮 Интерактивные Тесты
```bash
# Запуск интерактивных тестов
python -m pytest tests/ -v --tb=short

# Тесты с покрытием
python -m pytest tests/ --cov=rsecure --cov-report=html

# Нагрузочные тесты
python tests/performance/load_test.py
```

## 🎉 Поздравляем!

Вы успешно установили RSecure - революционную систему безопасности с DPI обходом и нейросетевым анализом!

**Следующие шаги:**
1. 📖 Изучите [USER_GUIDE.md](USER_GUIDE.md)
2. 🚀 Запустите систему: `python run_rsecure_with_dashboard.py`
3. 🌐 Откройте дашборд: http://127.0.0.1:5001
4. 🔓 Настройте DPI обход для ваших нужд
5. 🛡️ Конфигурируйте защиту под ваши угрозы

**Помните:** RSecure - мощный инструмент. Используйте его ответственно и в соответствии с законодательством.

**Поддержка:**
- 📖 Документация: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/rsecure/issues)
- 💬 Сообщество: [Discord](https://discord.gg/rsecure)
- 📧 Email: support@rsecure.dev

**Безопасных вам подключений!** 🛡️
