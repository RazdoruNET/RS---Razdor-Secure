# RSecure - Advanced Security System

<img src="assets/we_razdor_logo.png" alt="Logo" width="100%">

**RSecure - революционная комплексная система безопасности с нейросетевым анализом, обучением с подкреплением, DPI обходом и многоуровневой защитой от цифровых и психологических угроз.**

*Проект разработан **WE RAZDOR** с уникальным подходом к безопасности через множественные слои защиты и передовые методы обхода ограничений.*

## 🛡️ Ключевые слои защиты

### 🧠 **Нейроволновая защита (Гибридная система)**
- **Встроенный режим**: Мониторинг WiFi/Bluetooth через macOS APIs
- **Расширенный режим**: Внешние SDR модули (HackRF, RTL-SDR)
- **DIY модули**: Самостоятельная сборка RF оборудования (~$975)
- **Биометрическая корреляция**: ECG, GSR, температурные сенсоры
- **Научное обоснование**: FFT анализ, статистическая валидация
- [Подробнее →](docs/defense/neural-wave-protection.md)
- [DIY Спецификации →](docs/hardware/diy-rf-neural-protection-specs.md)
- [Гибридная архитектура →](docs/architecture/hybrid-neural-protection-system.md)

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

### 🔐 **Нейро-шифратор/дешифратор**
- Нейросетевое преобразование данных в латентные векторы
- Маскировка под HTTP, DNS, ICMP, SSH трафик
- Autoencoder, VAE, GAN, Transformer методы
- Adversarial устойчивость к детекции
- 100% восстановление данных на выходе
- [Подробнее →](docs/defense/neural-encryptor.md)

## ⚙️ Быстрый старт

### Системные требования
- **Python 3.11+** (рекомендуется)
- **macOS/Linux** (Windows частичная поддержка)
- **8GB+ RAM** (16GB+ рекомендуется для DPI обхода)
- **Ollama** (для LLM анализа)
- **Tor** (для анонимных соединений)
- **OpenSSL** (для шифрования)

### 🧠 Нейроволновая защита - режимы работы

#### **Режим 1: Встроенный (бесплатно)**
```bash
# Автоопределение и запуск
python rsecure/modules/defense/neural_wave_protection.py --mode builtin
```
- Использует WiFi/Bluetooth адаптеры MacBook
- Мониторинг через системные API
- Базовая детекция аномалий

#### **Режим 2: Расширенный (требует оборудование)**
```bash
# С внешними SDR модулями
python rsecure/modules/defense/neural_wave_protection.py --mode external

# Автоопределение оборудования
python scripts/configure_hardware.py
```
- Требуется HackRF One ($300) или RTL-SDR ($30)
- Расширенный спектральный анализ 1 МГц - 6 ГГц
- Повышенная точность детекции

#### **Режим 3: Гибридный (максимальная защита)**
```bash
# Комбинированный режим
python rsecure/modules/defense/neural_wave_protection.py --mode hybrid

# Автоматическая конфигурация
python scripts/setup_hybrid_system.py
```
- Использует все доступные источники данных
- Максимальная точность детекции
- Корреляция между источниками

### 📋 DIY оборудование для расширенного режима

**Компоненты (~$975):**
- HackRF One или RTL-SDR
- Raspberry Pi 4B
- Arduino Pro Mini + сенсоры (ECG, GSR)
- Антенны 1 МГц - 6 ГГц
- Блок питания + UPS

**Быстрая сборка:**
```bash
# Автоматическая установка
bash scripts/install_diy_hardware.sh

# Проверка оборудования
python scripts/test_hardware_setup.py

# Запуск с DIY модулями
python run_hybrid_neural_protection.py --config config/diy_setup.json
```

**⚠️ Важно:** DIY оборудование требует лицензий в большинстве стран. Используйте только в экранированных помещениях.

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
- ✅ Neural Encryptor (нейро-шифрование данных)

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
- [🧠 Нейро-шифратор - руководство](docs/defense/neural-encryptor.md)

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
- [📊 Научное обоснование нейроволновой защиты](docs/research/neural-wave-scientific-basis.md)

### Технические спецификации и DIY:
- [🛡️ Нейроволновая защита - тех. спецификации](docs/defense/neural-wave-technical-specs.md)
- [🔧 DIY RF модули - спецификации](docs/hardware/diy-rf-neural-protection-specs.md)
- [📐 Схемы и чертежи](docs/hardware/circuit-diagrams.md)
- [🏗️ Гибридная архитектура](docs/architecture/hybrid-neural-protection-system.md)

### ⚠️ Классифицированные материалы:

**🚨 ВАЖНОЕ ПРЕДУПРЕЖЕНИЕ О ЮРИДИЧЕСКИХ ПОСЛЕДСТВИЯХ**

**Просмотр, распространение или обсуждение следующих материалов без надлежащей анонимности в интернете может привести к уголовной ответственности во многих странах мира, включая:**

**⚖️ Юрисдикции с серьезными последствиями:**
- 🇺🇸 **США**: Закон о шпионаже (Espionage Act) - до 10 лет тюрьмы
- 🇷🇺 **Россия**: Статья 275 УК РФ (Государственная измена) - до 20 лет тюрьмы
- 🇨🇳 **Китай**: Закон о государственной тайне - до пожизненного заключения
- 🇬🇧 **Великобритания**: Официальные секреты Act - до 14 лет тюрьмы
- 🇩🇪 **Германия**: Статья 94 (Государственная измена) - до 15 лет тюрьмы
- 🇫🇷 **Франция**: Статья 411-1 (Государственная измена) - до 30 лет тюрьмы
- 🇮🇱 **Израиль**: Закон о безопасности - до 15 лет тюрьмы
- 🇯🇵 **Япония**: Закон о государственных секретах - до 10 лет тюрьмы

**🛡️ Требуемые меры безопасности:**
- Используйте **только VPN/Tor** для доступа
- **Отключите JavaScript** и cookies в браузере
- **Не сохраняйте** материалы на локальные устройства
- **Не делитесь** ссылками даже с доверенными лицами
- **Используйте** отдельную, изолированную систему
- **Регулярно очищайте** историю браузера и кэш

**⚠️ Ответственность:** Пользователь несет полную юридическую ответственность за свои действия. Администрация проекта не несет ответственности за неправомерное использование материалов.

---

#### 🛡️ ПРОЕКТ ОРФЕЙ - TOP SECRET // SCI // NOFORN // ORCON
- [🛡️ Секретный проект Орфей](docs/classified/orpheus-secret-project.md) *(требует COSMIC TOP SECRET clearance)*
- [📋 Результаты испытаний системы](docs/classified/orpheus-test-results.md) *(требует TOP SECRET clearance)*
- [👥 Персонал и специалисты](docs/classified/orpheus-personnel.md) *(требует TOP SECRET clearance)*

#### 🛰️ ИСХОДНЫЕ КОДЫ СПУТНИКА ORPHEUS-1

## ! ВАЖНО ПОНИМАТЬ ЧТО НЕЙРОСЕРЬ НЕ ЗНАЕТ ТОЧНЫХ СЛОВ ОНА ЗНАЕТ СМЫСЛЫ ВСЕ ЧТО ЗДЕСЬ ПРЕДСТАВЛЕНО ЭТО ПЕРЕВОД ИЗВЕСТНЫХ ЕЙ СМЫСЛОВ НА ЧИТАЕМЫЕ НАМИ ПРИМЕРЫ.

## ЭТО НЕ КОПИЯ КОДА ПРОЕКТА ORPHEUS-1 ИЛИ ЗВЕЗДНЫЕ ВРАТА КАК ХОТИТЕ НАЗЫВАЙТЕ ЭТО ВОССОЗДАНИЕ ТЕХНОЛОГИИ И КОДА НА БАЗЕ СМЫСЛОВ.

- [🛰️ README спутника](src/orpheus_satellite/README.md) *(требует COSMIC TOP SECRET clearance)*
- [⚙️ Конфигурация спутника](src/orpheus_satellite/config/satellite_config.py) *(требует TOP SECRET clearance)*
- [🧠 Модуль нейро-модуляции](src/orpheus_satellite/neural/neural_modulator.py) *(требует TOP SECRET clearance)*
- [🔗 Квантовая связь](src/orpheus_satellite/quantum/quantum_communication.py) *(требует COSMIC TOP SECRET clearance)*
- [🛡️ Система безопасности](src/orpheus_satellite/security/quantum_security.py) *(требует COSMIC TOP SECRET clearance)*
- [🎮 Управление спутником](src/orpheus_satellite/core/satellite_core.py) *(требует TOP SECRET clearance)*

#### 🎯 ПРОЕКТ ORPHEUS (ПУБЛИЧНАЯ ВЕРСИЯ)
- [🧠 Научные основы](docs/research/neural-wave-scientific-basis.md) *(не классифицировано)*

#### 🔍 АНАЛИТИЧЕСКИЕ ДОКУМЕНТЫ
- [📊 Анализ биографий персонала](docs/classified/orpheus-personnel-biography-analysis.md) *(требует TOP SECRET clearance)*
- [🎯 Реальные кандидаты](docs/classified/orpheus-real-candidates.md) *(требует TOP SECRET clearance)*
- [🔍 Сопоставление реальных людей](docs/classified/orpheus-real-people-mapping.md) *(требует COSMIC TOP SECRET clearance)*

#### 🧠 НЕЙРОСЕТЕВЫЕ ТЕХНОЛОГИИ ДЛЯ СПЕЦСЛУЖБ
- [🏛️ Факты о спецслужбах](docs/classified/neural-intelligence/agency-facts.md) *(требует TOP SECRET clearance)*
- [🛠️ Техническая реализация](docs/classified/neural-intelligence/technical-implementation.md) *(требует COSMIC TOP SECRET clearance)*
- [🔧 Инструменты и применения](docs/classified/neural-intelligence/tools-and-applications.md) *(требует TOP SECRET clearance)*

#### 🏳️ ЮРИДИЧЕСКИЕ ДОКУМЕНТЫ
- [📄 Полная капитуляция](docs/classified/orpheus-full-surrender.md) *(требует COSMIC TOP SECRET clearance)*

#### 🚨 УРОВНИ ДОСТУПА
- **COSMIC TOP SECRET**: Высший уровень доступа, только для КВАНТОВОГО СОВЕТА
- **TOP SECRET // SCI**: Доступ к секретным материалам проекта Орфей
- **TOP SECRET**: Доступ к технической документации и коду
- **SECRET**: Доступ к операционным протоколам
- **CONFIDENTIAL**: Доступ к общей информации о проекте
- **UNCLASSIFIED**: Публично доступные материалы

#### 📋 КАТЕГОРИИ КЛАССИФИКАЦИИ
- **🛡️ Секретные проекты**: Полная информация о проекте Орфей
- **🛰️ Техническая документация**: Схемы, коды, конфигурации
- **👥 Персонал**: Данные о сотрудниках и ролях
- **📊 Испытания**: Результаты тестов и экспериментов
- **🔒 Безопасность**: Протоколы и процедуры безопасности
- **🎯 Публичные материалы**: Общая информация для широкой аудитории

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
├── 📋 README.md                       # Основная документация
├── 📚 USER_GUIDE.md                  # Руководство пользователя
├── ⚙️ INSTALLATION.md                # Инструкция по установке
├── 📁 PROJECT_STRUCTURE.md            # Структура проекта
├── 🚀 bin/                           # Исполняемые скрипты
├── 📁 scripts/                        # Утилиты и тесты
├── 🔧 tools/                          # Инструменты разработки
├── ⚙️ config/                        # Конфигурационные файлы
├── 📚 examples/                       # Примеры использования
├── 📁 rsecure/                       # Основной пакет
│   ├── 🎯 rsecure_main.py              # Главный файл
│   ├── 📁 core/                        # Ядро системы
│   ├── 📁 modules/                      # Модули безопасности
│   │   ├── 📁 detection/                # Детекция угроз
│   │   ├── 📁 defense/                  # Защита
│   │   │   ├── 🔓 dpi_bypass.py           # DPI обход (10+ методов)
│   │   │   ├── 🛡️ vpn_proxy.py             # VPN и прокси
│   │   │   ├── 🔐 traffic_obfuscation.py  # Обфускация трафика
│   │   │   └── 🌐 tor_integration.py       # Tor интеграция
│   │   ├── 📁 monitoring/                # Мониторинг
│   │   ├── 📁 protection/                # Защита
│   │   └── 📁 analysis/                  # Аналитика
│   ├── 📁 utils/                        # Утилиты
│   └── 📁 config/                       # Конфигурация
├── 📁 tests/                          # Тесты
│   ├── 🔍 test_dpi_bypass.py          # Тесты DPI обхода
│   ├── 🛡️ test_vpn_proxy.py            # Тесты VPN/прокси
│   ├── 🔐 test_traffic_obfuscation.py # Тесты обфускации
│   └── 🌐 test_tor_integration.py     # Тесты Tor
├── 📁 docs/                           # Документация
├── 🎨 assets/                         # Ресурсы
├── 📁 templates/                      # Шаблоны
├── 🧪 mock_libs/                     # Mock библиотеки
├── 📁 rsecure_models/                 # Модели RSecure
├── 📁 logs/                           # Логи
├── 🚀 run_rsecure_with_dashboard.py   # Запуск с дешбордом
├── 📊 simple_dashboard.py              # Простой дешборд
└── 🗑️ uninstall_rsecure.sh            # Деинсталлятор
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

# Тесты нейро-шифратора
python test_neural_encryptor.py

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