# RSecure - Advanced Security System

<img src="assets/we_razdor_logo.png" alt="Logo" width="100%">

**RSecure - комплексная система безопасности с нейросетевым анализом, обучением с подкреплением и многоуровневой защитой от цифровых и психологических угроз.**

*Проект разработан **WE RAZDOR** с уникальным подходом к безопасности через множественные слои защиты.*

## 🛡️ Ключевые слои защиты

### 🧠 **Психологическая защита**
- Мониторинг нейронных весов через поведенческий анализ
- Анализ аудио потоков с нейро-детекцией
- Защита от weight adjustment атак
- [Подробнее →](docs/defense/psychical-protection.md)

### 🎣 **Защита от фишинга**
- Нейросетевой анализ контента страниц
- Обнаружение подозрительных доменов
- Проверка поведения веб-ресурсов
- [Подробнее →](docs/detection/phishing-detector.md)

### 🤖 **Защита от LLM атак**
- Детекция prompt injection атак
- Анализ паттернов GPT/Claude/Gemini
- Защита от adversarial атак
- [Подробнее →](docs/defense/llm-defense.md)

### 🎥 **Визуальная безопасность**
- Мониторинг мерцаний и яркости экрана
- Защита от атак через зрительный канал
- Фильтрация и нормализация экрана
- [Подробнее →](docs/defense/visual-security.md)

### 🌐 **Активная сетевая оборона**
- Обнаружение port scanning и DDoS
- Автоматическая блокировка вредоносных IP
- Honeypot сервисы
- [Подробнее →](docs/defense/network-defense.md)

### 🧬 **Нейросетевое ядро**
- Многослойные сверточные сети
- Обучение с подкреплением
- Ансамблевая модель решений
- [Подробнее →](docs/core-modules/neural-security-core.md)

## ⚙️ Быстрый старт

### Системные требования
- **Python 3.11+** (рекомендуется)
- **macOS/Linux**
- **8GB+ RAM**
- **Ollama** (для LLM анализа)

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

### Доступные LLM модели:
- 🤖 qwen2.5-coder:1.5b (анализ кода)
- 🤖 jarvis_secure:latest (безопасность)
- 🤖 gemma2:2b (общий анализ)
- 🤖 codeqwen:latest (анализ программ)

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
- [🔬 Научные основания](docs/research/scientific-foundations.md)

### Модули защиты:
- [Психологическая защита](docs/defense/psychical-protection.md)
- [Визуальная безопасность](docs/defense/visual-security.md)
- [Защита от LLM атак](docs/defense/llm-defense.md)
- [Сетевая оборона](docs/defense/network-defense.md)
- [Мониторинг устройств](docs/monitoring/audio-video-monitor.md)

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
│   └── analysis/           # Аналитика
├── docs/                    # Документация
├── assets/                  # Ресурсы
└── rsecure_main.py         # Основной файл
```

## 🔧 Разработка

### Тестирование
```bash
python -m pytest tests/
```

### Вклад в проект
- Улучшение нейросетевых архитектур
- Распознавание новых типов атак
- Оптимизация производительности
- Дополнительные платформы

## � Лицензия

RSecure - экспериментальная система безопасности. Используйте на свой страх и риск.

---

## 👨‍💻 О создателе WE RAZDOR

**WE RAZDOR** - разработчик с уникальным подходом к безопасности, использующий множественные перспективы для создания комплексных систем защиты.

**Философия проекта:** RSecure создана с глубоким пониманием современных угроз и стремлением предоставить надежную защиту для тех, кто в ней нуждается.

**Миссия:** Создание интеллектуальных систем безопасности, способных адаптироваться к новым угрозам и обеспечивать надежную защиту для пользователей.

---

**Важно**: RSecure является мощной системой безопасности. Тщательно тестируйте в безопасной среде перед использованием в production.
