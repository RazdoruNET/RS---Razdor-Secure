# 🎯 DPI Тестирование: Руководство и Инструменты

Документация по использованию скриптов для тестирования всех доступных модулей обхода DPI на доступность YouTube и других сайтов.

## 📁 Файлы тестирования

### 1. `test_dpi_modules.sh` - Базовое тестирование
Основной скрипт для быстрой проверки всех модулей на доступность YouTube.

**Возможности:**
- Тестирование 7 модулей обхода DPI
- Проверка доступности YouTube
- Автоматический запуск/остановка модулей
- Сохранение логов в `test_results/dpi_bypass/`
- Создание сводного отчета

### 2. `advanced_dpi_test.sh` - Расширенное тестирование
Углубленное тестирование с проверкой множественных сайтов.

**Возможности:**
- Тестирование 10+ сайтов
- 3 попытки для каждого сайта
- Измерение времени отклика
- Создание HTML отчета
- Детальная статистика

### 3. `port_manager.sh` - Управление портами
Утилита для управления портами и диагностики конфликтов.

**Возможности:**
- Проверка занятых портов
- Убийство процессов на портах
- Автоматический выбор свободных портов
- Мониторинг состояния портов

## 🚀 Использование

### Базовое тестирование
```bash
# Запуск базового тестирования
./test_dpi_modules.sh

# Показать справку
./test_dpi_modules.sh --help

# Очистить результаты
./test_dpi_modules.sh --clean

# Проверить порты перед тестированием
./port_manager.sh --check
```

### Расширенное тестирование
```bash
# Запуск расширенного тестирования
./advanced_dpi_test.sh

# Быстрое тестирование (только YouTube)
./advanced_dpi_test.sh --quick

# Показать справку
./advanced_dpi_test.sh --help

# Очистить старые результаты
./advanced_dpi_test.sh --clean

# Тестирование с управлением портами
./port_manager.sh --auto-cleanup
./advanced_dpi_test.sh --port-check
```

### Тестирование через новые скрипты
```bash
# Тестирование через минимальную конфигурацию
python3 scripts/minimal_rsecure.py --test-dpi

# Тестирование через максимальную конфигурацию
python3 scripts/maximal_rsecure.py --test-dpi

# Тестирование с Ollama интеграцией
python3 scripts/ollama_rsecure.py --test-dpi
```

## 📊 Модули для тестирования

| Модуль | Порт | Тип | Описание |
|---------|------|------|----------|
| White Ghost | 1080 | SOCKS5 | Основной SOCKS5 прокси |
| Enhanced Fin Storm | 8080 | HTTP | Улучшенный Fin Storm |
| Fin Storm | 8081 | HTTP | Базовый Fin Storm |
| Robust | 8082 | HTTP | Устойчивый прокси |
| Ultimate | 8083 | HTTP | Максимальная функциональность |
| Simple Working | 8084 | HTTP | Простая рабочая версия |
| White Ghost Fixed | 1081 | SOCKS5 | Исправленная версия |

## 🌐 Сайты для тестирования

### Базовое тестирование:
- `https://www.youtube.com`

### Расширенное тестирование:
- `https://www.youtube.com`
- `https://m.youtube.com`
- `https://youtu.be`
- `https://www.google.com`
- `https://www.github.com`
- `https://www.reddit.com`
- `https://www.twitter.com`
- `https://www.instagram.com`
- `https://www.facebook.com`
- `https://www.wikipedia.org`

## 📁 Результаты тестирования

### Структура папок:
```
RS---Razdor-Secure/
├── test_results/
│   ├── dpi_bypass/
│   │   ├── white_ghost_proxy_20231205_143022.log
│   │   ├── enhanced_fin_storm_proxy_20231205_143045.log
│   │   ├── test_summary_20231205_143200.txt
│   │   ├── detailed_20231205_143000/
│   │   │   ├── white_ghost_proxy_youtube.com.txt
│   │   │   ├── enhanced_fin_storm_proxy_m.youtube.com.txt
│   │   │   └── ...
│   │   └── advanced_summary_20231205_143200.html
│   └── summaries/
│       ├── performance_metrics.json
│       └── success_rates.txt
```

### Формат логов:
```
=== Тестирование YouTube через White Ghost ===
Время: Tue Dec  5 14:30:22 MSK 2023
Прокси: socks5://127.0.0.1:1080

HTTP код: 200
Время ответа: 2.5 секунд
HTTP код: 200/301/302

Итоги:
Успешных модулей: 5/7
```

## 🔧 Зависимости

Для работы скриптов требуются:
- `curl` - для HTTP запросов
- `lsof` - для проверки портов
- `python3` - для запуска модулей
- `bc` - для математических вычислений (расширенный тест)

Установка на macOS:
```bash
brew install curl lsof bc
```

## 📊 Критерии успеха

### Базовое тестирование:
- ✅ HTTP код 200/301/302
- ✅ Время ответа < 30 секунд
- ✅ Стабильное подключение

### Расширенное тестирование:
- ✅ Успешность ≥ 67% (2/3 попыток)
- ✅ Среднее время < 15 секунд
- ✅ Стабильность на множественных сайтах

## 🛠️ Диагностика проблем

### Модуль не запускается:
```bash
# Проверить зависимости Python
python3 -c "import sys; print(sys.version)"

# Проверить наличие модуля
ls -la scripts/proxy_tools/
```

### Прокси не отвечает:
```bash
# Проверить порт
lsof -i :1080

# Проверить вручную
curl -x socks5://127.0.0.1:1080 https://www.youtube.com
```

### YouTube блокируется:
```bash
# Проверить без прокси
curl -I https://www.youtube.com

# Проверить DNS
nslookup www.youtube.com
```

## 📈 Анализ результатов

### Успешный модуль:
```
✅ White Ghost: YouTube доступен (2s)
Время ответа: 2 секунд
HTTP код: 200/301/302
```

### Неуспешный модуль:
```
❌ Fin Storm: YouTube недоступен
Ошибка подключения
```

### HTML отчет:
Расширенный тест создает визуальный HTML отчет с:
- Статистикой по модулям
- Графиками успешности
- Детальными логами
- Сравнительной таблицей

## 🔄 Автоматизация

### Cron для регулярного тестирования:
```bash
# Добавить в crontab
0 */6 * * * /Users/razdor/Documents/GitHub/RS---Razdor-Secure/test_dpi_modules.sh

# Каждые 6 часов запускать базовое тестирование
```

### Bash функция для быстрого запуска:
```bash
# Добавить в ~/.bashrc или ~/.zshrc
dpi_test() {
    cd /Users/razdor/Documents/GitHub/RS---Razdor-Secure
    ./test_dpi_modules.sh
}

# Использование:
dpi_test
```

### Новые функции автоматизации:
```bash
# Тестирование через порт менеджер
dpi_test_auto() {
    cd /Users/razdor/Documents/GitHub/RS---Razdor-Secure
    ./port_manager.sh --auto-cleanup
    ./test_dpi_modules.sh
}

# Тестирование всех конфигураций
dpi_test_all() {
    cd /Users/razdor/Documents/GitHub/RS---Razdor-Secure
    
    echo "🧪 Тестирование минимальной конфигурации..."
    python3 scripts/minimal_rsecure.py --test-dpi
    
    echo "🚀 Тестирование максимальной конфигурации..."
    python3 scripts/maximal_rsecure.py --test-dpi
    
    echo "🤖 Тестирование Ollama интеграции..."
    python3 scripts/ollama_rsecure.py --test-dpi
}
```

## ⚠️ Важные замечания

1. **Отключите VPN** перед тестированием для чистых результатов
2. **Брандмауэр** может блокировать локальные порты
3. **Сетевые проблемы** могут влиять на результаты
4. **Время суток** может влиять на доступность YouTube
5. **Множественные запуски** могут конфликтовать по портам

## 🎯 Рекомендации

1. **Начните с базового тестирования** для быстрой оценки
2. **Используйте расширенное тестирование** для детального анализа
3. **Проверяйте логи** для диагностики проблем
4. **Тестируйте в разное время** для стабильности
5. **Сохраняйте результаты** для сравнения

## 📞 Поддержка

При проблемах:
1. Проверьте зависимости (`brew install curl lsof bc`)
2. Убедитесь что Python 3 установлен
3. Проверьте права доступа к скриптам (`chmod +x`)
4. Просмотрите логи в `test_results/dpi_bypass/`
5. Используйте `port_manager.sh` для диагностики портов
6. Проверьте `DPI_ANALYSIS_REPORT.md` для анализа проблем

### Новые возможности:
- **SUPER_DPI_COMBINER/**: Улучшенный комбинер с 50+ файлами
- **Множественные скрипты запуска**: minimal/maximal/ollama/enhanced
- **Централизованное управление портами**: port_manager.sh
- **Расширенная документация**: docs/quick-start.md, system-requirements.md

### Быстрая диагностика:
```bash
# Полная проверка системы
./port_manager.sh --full-check
./test_dpi_modules.sh --diagnose

# Тестирование всех конфигураций
python3 scripts/minimal_rsecure.py --test-all
python3 scripts/maximal_rsecure.py --test-all
```

---

**Проект готов к тестированию с улучшенной структурой!** 🚀
