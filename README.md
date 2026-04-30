# RSecure - Advanced Security System

<img src="assets/we_razdor_logo.png" alt="Logo" width="100%">

**RSecure - революционная комплексная система безопасности с нейросетевым анализом, обучением с подкреплением, DPI обходом и многоуровневой защитой от цифровых и психологических угроз.**

*Проект разработан **WE RAZDOR** с уникальным подходом к безопасности через множественные слои защиты и передовые методы обхода ограничений.*

## 🛡️ Ключевые слои защиты

### 🧠 **Нейроволновая защита**
- Мониторинг WiFi/Bluetooth интерфейсов
- Детекция электромагнитных аномалий
- Анализ воздействия на мозговые волны
- Биометрическая корреляция угроз
- [Подробнее →](docs/defense/neural-wave-protection.md)

### 🛡️ **Антипозиционирование (защита от WiFi отражений)**
- Защита от определения местоположения через WiFi отражения
- Обфускация канальной информации состояния (CSI)
- Генерация синтетических многолучевых помех
- Рандомизация фазы и амплитуды сигнала
- [Подробнее →](docs/wifi-antipositioning-defense.md)

### 🔓 **DPI Обход и Сетевая Свобода**
- Фрагментация пакетов для обхода инспекции
- TLS SNI Splitting для обхода блокировок
- Обфускация HTTP заголовков и Domain Fronting
- Цепочки прокси и VPN маршрутизация
- Tor интеграция с кастомными circuits
- Шифрование трафика (AES, ChaCha20)
- Мимикрия протоколов (SSH, FTP, SMTP)
- Стеганография и многослойная обфускация
- [Подробнее →](docs/defense/dpi-bypass-guide.md)

### � **Психологическая защита**
- Мониторинг нейронных весов через поведенческий анализ
- Анализ аудио потоков с нейро-детекцией
- Защита от weight adjustment атак
- [Подробнее →](docs/defense/psychical-protection.md)

### 🎥 **Визуальная безопасность**
- Мониторинг мерцаний и яркости экрана
- Защита от атак через зрительный канал
- Фильтрация и нормализация экрана
- [Подробнее →](docs/defense/visual-security.md)

### 🤖 **Защита от LLM атак**
- Детекция prompt injection атак
- Анализ паттернов GPT/Claude/Gemini
- Защита от adversarial атак
- [Подробнее →](docs/defense/llm-defense.md)

### 🌐 **Активная сетевая оборона**
- Обнаружение port scanning и DDoS атак
- Автоматическая блокировка вредоносных IP
- Honeypot сервисы и ловушки
- Интеллектуальная фильтрация трафика
- Адаптивная защита от сетевых угроз
- [Подробнее →](docs/defense/network-defense.md)

### 🎣 **Защита от фишинга**
- Нейросетевой анализ контента страниц
- Обнаружение подозрительных доменов
- Проверка поведения веб-ресурсов
- [Подробнее →](docs/detection/phishing-detector.md)

### 🧬 **Нейросетевое ядро**
- Многослойные сверточные сети
- Обучение с подкреплением (Reinforcement Learning)
- Ансамблевая модель решений
- Ollama интеграция с LLM анализом
- Адаптивные нейронные архитектуры
- [Подробнее →](docs/core-modules/neural-security-core.md)

## ⚙️ Быстрый старт

### Системные требования
- **Python 3.11+** (рекомендуется)
- **macOS/Linux** (Windows частичная поддержка)
- **8GB+ RAM** (16GB+ рекомендуется для DPI обхода)
- **Ollama** (для LLM анализа)
- **Tor** (для анонимных соединений)
- **OpenSSL** (для шифрования)

### Установка
```bash
# Клонирование и установка
git clone <repository>
cd windsurf-project-3

# Создание окружения
python3.11 -m venv rsecure_env
source rsecure_env/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Установка Ollama
brew install ollama && brew services start ollama
ollama pull qwen2.5-coder:1.5b
ollama pull gemma2:2b

# Установка Tor (macOS)
brew install tor && brew services start tor

# Установка дополнительных зависимостей
pip install cryptography stem pysocks requests
```

### Запуск
```bash
# Основной режим
python rsecure/rsecure_main.py

# С веб-дешбордом
python run_rsecure_with_dashboard.py

# Простой дешборд
python simple_dashboard.py
```

## ✅ Статус компонентов

### Работающие модули:
- ✅ System Detection (автоопределение системы)
- ✅ Neural Security Core (многослойные нейросети)
- ✅ Ollama Integration (LLM анализ)
- ✅ Visual Security (защита от визуальных атак)
- ✅ Network Defense (активная оборона)
- ✅ Web Dashboard (мониторинг в реальном времени)
- ✅ DPI Bypass Engine (10+ методов обхода)
- ✅ VPN & Proxy Manager (OpenVPN, WireGuard, SOCKS5)
- ✅ Traffic Obfuscation (AES, ChaCha20, стеганография)
- ✅ Tor Integration (полный контроль сети)
- ✅ WiFi Anti-Positioning (защита от отражений)

### Доступные LLM модели:
- 🤖 qwen2.5-coder:1.5b (анализ кода)
- 🤖 jarvis_secure:latest (безопасность)
- 🤖 gemma2:2b (общий анализ)
- 🤖 codeqwen:latest (анализ программ)

### DPI Обход методы:
- 🔓 Фрагментация пакетов
- 🔓 TLS SNI Splitting
- 🔓 HTTP Header Obfuscation
- 🔓 Domain Fronting
- 🔓 Proxy Chaining
- 🔓 Tor Routing
- 🔓 VPN Tunneling
- 🔓 Protocol Mimicking
- 🔓 Encoded Payload
- 🔓 Stealth Ports

## 🌐 Веб-дешборд

Запуск дешборда для мониторинга в реальном времени:
```bash
python simple_dashboard.py
# Откройте http://127.0.0.1:5000
```

**Функции:**
- 🖥️ Мониторинг системы в реальном времени
- 📊 Использование ресурсов (CPU, память, диск)
- 🌐 Сетевая активность и соединения
- ⚠️ Уровень угроз и статус безопасности
- 🔄 Автообновление каждые 10 секунд

## 📚 Документация

### Основные модули:
- [Архитектура системы](docs/architecture/overview.md)
- [Нейросетевое ядро](docs/core-modules/neural-security-core.md)
- [Ollama интеграция](docs/core-modules/ollama-integration.md)
- [Обучение с подкреплением](docs/core-modules/reinforcement-learning.md)
- [🔓 DPI Обход - полное руководство](docs/defense/dpi-bypass-guide.md)
- [🛡️ VPN и Прокси интеграция](docs/defense/vpn-proxy-guide.md)
- [🔐 Обфускация трафика](docs/defense/traffic-obfuscation-guide.md)
- [🌐 Tor интеграция](docs/defense/tor-integration-guide.md)

### Модули защиты:
- [Психологическая защита](docs/defense/psychical-protection.md)
- [🧠 Нейроволновая защита](docs/defense/neural-wave-protection.md)
- [🛡️ Антипозиционирование (защита от WiFi отражений)](docs/wifi-antipositioning-defense.md)
- [Визуальная безопасность](docs/defense/visual-security.md)
- [Защита от LLM атак](docs/defense/llm-defense.md)
- [Сетевая оборона](docs/defense/network-defense.md)
- [Мониторинг устройств](docs/monitoring/audio-video-monitor.md)
- [🔓 DPI Обход - технические детали](docs/defense/dpi-bypass-technical.md)
- [🌐 Анонимность и приватность](docs/defense/anonymity-privacy.md)

### Научные исследования:
- [🔬 Научные основания](docs/research/scientific-foundations.md)
- [🧠 Нейроволновые исследования](docs/research/neural-wave-scientific-foundations.md)

### Алгоритмы и методы:
- [Анализ поведения](docs/algorithms/behavioral-analysis.md)
- [Спектральный анализ](docs/algorithms/spectral-analysis.md)
- [Нейросетевые архитектуры](docs/neural/architectures.md)

### Технические спецификации:
- [🛡️ Нейроволновая защита - тех. спецификации](docs/defense/neural-wave-technical-specs.md)

### Детекторы:
- [Детектор системы](docs/detection/system-detector.md)
- [Фишинг-детектор](docs/detection/phishing-detector.md)

## ⚙️ Конфигурация

Основной файл конфигурации `rsecure_config.json`:
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
    "default_method": "fragmentation",
    "tor_enabled": true,
    "vpn_enabled": false
  },
  "traffic_obfuscation": {
    "enabled": true,
    "default_method": "aes",
    "encryption_key": "auto_generated"
  }
}
```

## 🏗️ Структура проекта

```
rsecure/
├── core/                    # Основные модули
│   ├── neural_security_core.py
│   └── ollama_integration.py
├── modules/
│   ├── detection/          # Детекторы угроз
│   ├── defense/            # Модули защиты
│   │   ├── dpi_bypass.py           # DPI обход (10+ методов)
│   │   ├── vpn_proxy.py             # VPN и прокси
│   │   ├── traffic_obfuscation.py  # Обфускация трафика
│   │   └── tor_integration.py       # Tor интеграция
│   └── analysis/           # Аналитика
├── tests/                   # Тесты
│   ├── test_dpi_bypass.py          # Тесты DPI обхода
│   ├── test_vpn_proxy.py            # Тесты VPN/прокси
│   ├── test_traffic_obfuscation.py # Тесты обфускации
│   └── test_tor_integration.py     # Тесты Tor
├── docs/                    # Документация
├── assets/                  # Ресурсы
└── rsecure_main.py         # Основной файл
```

## 🔧 Разработка

### Тестирование
```bash
# Все тесты
python -m pytest tests/ -v

# Тесты DPI обхода
python -m pytest tests/test_dpi_bypass.py -v

# Тесты VPN и прокси
python -m pytest tests/test_vpn_proxy.py -v

# Тесты обфускации
python -m pytest tests/test_traffic_obfuscation.py -v

# Тесты Tor интеграции
python -m pytest tests/test_tor_integration.py -v

# Тестирование производительности
python -m pytest tests/ -k performance
```

### Вклад в проект
- Улучшение нейросетевых архитектур
- Распознавание новых типов атак
- Оптимизация производительности
- Дополнительные платформы
- 🔓 Новые методы DPI обхода
- 🛡️ Улучшение VPN/прокси протоколов
- 🌐 Расширение Tor функциональности
- 🔐 Новые алгоритмы шифрования и обфускации

## ⚠️ Лицензия и Предупреждение

RSecure - экспериментальная система безопасности. Используйте на свой страх и риск.

**ВАЖНО:** Модули DPI обхода предназначены для:
- Исследовательских целей
- Тестирования безопасности
- Обхода легитимных ограничений
- Защиты приватности

**Ответственность:** Пользователь несет полную ответственность за использование модулей обхода в соответствии с законодательством своей страны.

---

## 👨‍💻 О создателе WE RAZDOR

**WE RAZDOR** - разработчик с уникальным подходом к безопасности, использующий множественные перспективы для создания комплексных систем защиты.

**Философия проекта:** RSecure создана с глубоким пониманием современных угроз и стремлением предоставить надежную защиту для тех, кто в ней нуждается.

**Миссия:** Создание интеллектуальных систем безопасности, способных адаптироваться к новым угрозам и обеспечивать надежную защиту для пользователей.

---

## 💖 ПОДДЕРЖКА РАЗРАБОТЧИКА:

Если вы цените работу и хотите поддержать развитие проекта RSecure:

**BTC:** `1EKpztjQoSZ3XUB8snvKo6db1kFkViNi1L`

Ваша поддержка помогает продолжать разработку и улучшение системы безопасности.

---

**Важно**: RSecure является мощной системой безопасности с DPI обходом. Тщательно тестируйте в безопасной среде перед использованием в production.

**Безопасность:**
- Используйте в тестовой среде
- Проверяйте законодательство страны
- Не используйте для незаконных действий
- Тестируйте все методы обхода аккуратно