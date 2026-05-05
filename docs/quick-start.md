# 🚀 БЫСТРЫЙ СТАРТ

## 📋 **СИСТЕМНЫЕ ТРЕБОВАНИЯ**

### Минимальные требования:
- **ОС**: macOS 10.15+
- **Python**: 3.11+
- **RAM**: 8GB+
- **Storage**: 2GB+

### Рекомендуемые требования:
- **ОС**: macOS 12.0+
- **Python**: 3.11+
- **RAM**: 16GB+
- **Storage**: 5GB+
- **SDR**: HackRF One или RTL-SDR

## ⚡ **УСТАНОВКА ЗА 5 МИНУТ**

```bash
# 1. Клонирование репозитория
git clone https://github.com/WE-RAZDOR/RSecure.git
cd RSecure

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Запуск базовой защиты
python rsecure/rsecure_main.py
```

## 🎯 **ВАРИАНТЫ ЗАПУСКА**

### Базовая защита
```bash
# Основной модуль RSecure
python rsecure/rsecure_main.py
```

### С панелью управления
```bash
# Запуск с дашбордом
python scripts/startup/run_rsecure_with_dashboard.py
```

### DPI обход
```bash
# Запуск DPI обхода
python scripts/startup/run_dpi_bypass_daemon.py
```

### Минимальная конфигурация
```bash
# Легкая версия для слабых систем
python scripts/minimal_rsecure.py
```

### Максимальная конфигурация
```bash
# Полная функциональность
python scripts/maximal_rsecure.py
```

### Ollama интеграция
```bash
# С нейросетевыми моделями
python scripts/ollama_rsecure.py
```

## 🛠️ **ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА**

### Установка Ollama
```bash
# macOS
brew install ollama && brew services start ollama

# Linux
sudo apt install ollama && sudo systemctl start ollama

# Загрузка моделей
ollama pull qwen2.5-coder:1.5b
ollama pull gemma2:2b
```

### Установка Tor
```bash
# macOS
brew install tor && brew services start tor

# Linux
sudo apt install tor && sudo systemctl start tor
```

### Настройка прокси
```bash
# HTTP прокси
python scripts/startup/setup_http_proxy.py

# Системный прокси
python scripts/startup/setup_system_proxy.py
```

## 📊 **ПАНЕЛИ УПРАВЛЕНИЯ**

### Продвинутый дашборд
```bash
python scripts/dashboard_tools/advanced_dashboard.py
```

### Оптимизированный дашборд
```bash
python scripts/dashboard_tools/optimized_dashboard.py
```

### Русский дашборд
```bash
python scripts/dashboard_tools/russian_dashboard.py
```

## 🔧 **ПРОКСИ ИНСТРУМЕНТЫ**

### Fin Storm прокси
```bash
python scripts/proxy_tools/fin_storm_proxy.py
```

### Улучшенный прокси
```bash
python scripts/proxy_tools/enhanced_fin_storm_proxy.py
```

### White Ghost прокси
```bash
python scripts/proxy_tools/white_ghost_proxy.py
```

## 🧪 **ТЕСТИРОВАНИЕ**

### Запуск всех тестов
```bash
python -m pytest tests/
```

### Интеграционные тесты
```bash
python -m pytest tests/integration/
```

### Модульные тесты
```bash
python -m pytest tests/unit/
```

### DPI тестирование
```bash
./advanced_dpi_test.sh
./test_dpi_modules.sh
```

## 📝 **КОНФИГУРАЦИЯ**

### Основной конфиг
```bash
# Копирование шаблона
cp config/templates/rsecure_config.template.json config/rsecure_config.json

# Редактирование
nano config/rsecure_config.json
```

### Логи и мониторинг
```bash
# Просмотр логов приложения
tail -f logs/application/rsecure_main.log

# Просмотр логов безопасности
tail -f logs/security/security.log

# Просмотр логов DPI обхода
tail -f logs/dpi_bypass/dpi_bypass.log
```

## 🚨 **УРОВНИ ДОСТУПА**

- **COSMIC TOP SECRET**: Высший уровень доступа
- **TOP SECRET // SCI**: Секретные материалы проекта Орфей
- **TOP SECRET**: Техническая документация и код
- **SECRET**: Операционные протоколы
- **CONFIDENTIAL**: Общая информация о проекте
- **UNCLASSIFIED**: Публично доступные материалы

## ⚠️ **ПРЕДУПРЕЖДЕНИЕ**

**Ответственность:** Пользователь несет полную юридическую ответственность за свои действия. Администрация проекта не несет ответственности за неправомерное использование материалов.

**🚨 Используйте только в законных целях и в соответствии с законодательством вашей страны.**

---

## 📚 **ПОЛЕЗНЫЕ ССЫЛКИ**

- [Руководство пользователя](../USER_GUIDE.md)
- [Структура проекта](../FINAL_PROJECT_STRUCTURE.md)
- [Интеграция модулей](../rsecure_modules_integration_guide.md)
- [Документация по установке](setup/INSTALLATION.md)
- [Настройка браузера](setup/BROWSER_SETUP.md)

---

**© 2026 WE RAZDOR. Все права защищены.**
