# Установка и Запуск RSecure

## 📋 Текущий статус

Дашборд успешно запущен и показывает:
- ✅ **Системные метрики**: CPU, память, диск
- ✅ **Сетевая активность**: соединения, интерфейсы, трафик
- ✅ **Угрозы**: активные угрозы, заблокированные IP
- ✅ **CVU Intelligence**: уязвимости из NVD, GHSA, CISA KEV
- ✅ **Логи**: последние события системы

## ⚠️ Режим работы

В данный момент дашборд работает в **автономном режиме** (без модулей безопасности RSecure), так как не установлены все зависимости.

## 🚀 Полная установка

Для включения всех модулей безопасности установите зависимости:

```bash
pip install -r requirements.txt
```

Основные зависимости:
- `scikit-learn>=1.0.0` - для ML-алгоритмов
- `scapy>=2.4.5` - для анализа сетевых пакетов
- `psutil>=5.8.0` - для мониторинга системы
- `numpy>=1.21.0`, `pandas>=1.3.0`, `scipy>=1.7.0` - для обработки данных

**Важно**: `tensorflow>=2.10.0` временно недоступен в requirements.txt из-за несовместимости с Python 3.14. Для полной функциональности нейросетевого ядра используйте Python <3.12.

## 📊 Запуск системы

### Вариант 1: Интегрированный запуск (рекомендуется)

```bash
python3 run_rsecure_with_dashboard.py
```

Запускает:
- Модули безопасности RSecure (если зависимости установлены)
- Веб-дашборд на http://127.0.0.1:5001
- Автоматическую корреляцию данных

### Вариант 2: Только дашборд (автономный режим)

```bash
python3 simple_dashboard.py
```

Запускает простой дашборд на http://127.0.0.1:5000 с базовыми метриками.

### Вариант 3: Полная система RSecure

```bash
cd rsecure
python3 rsecure_main.py
```

Запускает только модули безопасности без веб-интерфейса.

## 🔧 API Endpoints

Дашборд предоставляет следующие API:

- `GET /api/status` - статус системы
- `GET /api/metrics` - метрики (CPU, RAM, Disk)
- `GET /api/threats` - информация об угрозах
- `GET /api/network` - сетевая активность
- `GET /api/cvu` - CVU Intelligence
- `GET /api/logs?type=rsecure&lines=10` - логи

## 📁 Структура проекта

```
windsurf-project-3/
├── run_rsecure_with_dashboard.py  # Интегрированный лаунчер
├── simple_dashboard.py             # Простой дашборд
├── test_rsecure.py                 # Тесты системы
├── rsecure/
│   ├── rsecure_main.py            # Основная система
│   ├── utils/
│   │   ├── dashboard.py           # Веб-дашборд
│   │   └── monitoring_logger.py   # Логирование
│   ├── modules/                    # Модули безопасности
│   │   ├── detection/             # Детекция угроз
│   │   │   ├── phishing_detector.py
│   │   │   ├── system_detector.py
│   │   │   └── cvu_intelligence.py
│   │   ├── defense/               # Защита
│   │   │   ├── network_defense.py
│   │   │   ├── llm_defense.py
│   │   │   └── system_control.py
│   │   ├── monitoring/            # Мониторинг
│   │   │   ├── audio_stream_monitor.py
│   │   │   └── audio_video_monitor.py
│   │   ├── protection/            # Психологическая защита
│   │   │   └── psychological_protection.py
│   │   ├── analysis/              # Анализ безопасности
│   │   │   └── security_analytics.py
│   │   └── notification/          # Уведомления
│   │       └── macos_notifications.py
│   ├── core/                      # Нейросетевое ядро
│   │   ├── neural_security_core.py
│   │   ├── reinforcement_learning.py
│   │   └── ollama_integration.py  # Интеграция с Ollama
│   ├── config/                    # Конфигурация
│   │   └── offline_threats.json
│   └── tests/                     # Тесты
│       └── rsecure_test.py
├── templates/
│   └── dashboard.html             # HTML шаблон
├── assets/
│   └── we_razdor_logo.png         # Логотип
├── mock_libs/                     # Mock библиотеки
│   └── tensorflow.py              # Для тестов без TensorFlow
└── logs/                          # Логи системы
```

## 🛡️ Модули безопасности (при полной установке)

1. **Neural Security Core** - нейросетевой анализ угроз
2. **Reinforcement Learning** - адаптивная защита
3. **Ollama Integration** - гибридный анализ с LLM
4. **Network Defense** - активная сетевая защита
5. **CVU Intelligence** - мониторинг уязвимостей
6. **Phishing Detector** - детекция фишинга
7. **System Detector** - детекция системных угроз
8. **LLM Defense** - защита от LLM атак
9. **Audio/Video Monitor** - мониторинг медиа-устройств
10. **Psychological Protection** - защита от психологических атак
11. **Security Analytics** - анализ безопасности
12. **macOS Notifications** - системные уведомления

## 📝 Решение проблем

### Порт 5000 занят (macOS AirPlay)

Система автоматически использует порт 5001. Если порт занят, измените в `run_rsecure_with_dashboard.py`:
```python
self.dashboard.run(host='127.0.0.1', port=5002, debug=False)
```

### Ошибки импорта tensorflow

Для полной функциональности установите Python <3.12 и TensorFlow:
```bash
# Создайте виртуальное окружение с Python 3.11
python3.11 -m venv tf_env
source tf_env/bin/activate
pip install tensorflow>=2.10.0
```

или используйте автономный режим (дашборд будет работать без модулей безопасности).

### Интеграция с Ollama (дополнительно)

Для расширенного анализа угроз с помощью LLM:
```bash
# Установите Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запустите Ollama сервер
ollama serve

# Скачайте модели
ollama pull qwen2.5-coder:1.5b
ollama pull codeqwen
```

Система автоматически обнаружит Ollama на localhost:11434 и использует гибридный анализ.

### Нет данных в логах

Убедитесь, что директория `logs/` существует и есть права записи:
```bash
mkdir -p logs
chmod 755 logs
```
