# SQL Injection Auditor - Руководство для Начинающих

## 🎯 Что это за инструмент?

**SQL Injection Auditor** - это автоматизированный инструмент для поиска уязвимостей SQL injection в веб-приложениях. Он помогает найти "дыры" в безопасности сайтов, которые могут быть использованы злоумышленниками для кражи данных.

## 🚀 Быстрый Старт

### Установка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd sql_injection_auditor

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### Первый Запуск

```bash
# Базовый скан сайта
python main.py -u https://example.com

# Скан с подробным выводом
python main.py -u https://example.com --verbose
```

## 📖 Основные Команды

### Базовое Использование

```bash
# Скан одного URL (пассивный режим)
python main.py -u https://example.com --mode passive

# Полный краулинг и скан (активный режим)
python main.py -u https://example.com --mode active

# Скан с глубиной краулинга
python main.py -u https://example.com --mode active --crawl-depth 3
```

### Конфигурация

```bash
# Использование кастомного конфига
python main.py -u https://example.com --config my_config.json

# Enterprise режим с продвинутой безопасностью
python main.py -u https://example.com --config enterprise_config.json
```

## 🔍 Что Ищет Инструмент?

### Типы SQL Injection

1. **Error-Based** - Ошибки базы данных в ответе
2. **Boolean-Based** - Разные ответы на true/false запросы
3. **Time-Based** - Задержка ответа при истинном условии
4. **Union-Based** - Объединение результатов запросов

### Поддерживаемые Базы Данных

- MySQL
- PostgreSQL
- MSSQL (Microsoft SQL Server)
- Oracle

## 📊 Результаты Сканирования

После завершения сканирования инструмент создает:

1. **JSON отчет** - `reports/scan_report_<timestamp>.json`
2. **PDF отчет** - `reports/scan_report_<timestamp>.pdf` (если установлен ReportLab)

### Пример Результата

```json
{
  "target": "https://example.com",
  "status": "completed",
  "vulnerabilities_found": 2,
  "vulnerabilities": [
    {
      "url": "https://example.com/search.php",
      "parameter": "q",
      "injection_type": "error_based",
      "database_type": "mysql",
      "confidence": 0.9,
      "severity": "high"
    }
  ]
}
```

## ⚠️ Важные Предупреждения

### Этическое Использование

- ✅ Сканируйте только сайты, которые ВЫ владеете или имеете разрешение
- ✅ Используйте только для образовательных целей
- ✅ Сообщайте о найденных уязвимостях владельцам сайтов
- ❌ НЕ используйте для незаконных действий
- ❌ НЕ сканируйте сайты без разрешения

### Риски Использования

- Сайт может заблокировать ваш IP
- Слишком агрессивное сканирование может "положить" сайт
- Найденные уязвимости должны быть исправлены, а не использованы

## 🔧 Настройка для Начинающих

### config.json - Основные Настройки

```json
{
  "crawl_delay": 2.0,
  "crawl_depth": 2,
  "timeout": 30,
  "database_types": ["mysql", "postgresql"],
  "verify_vulnerabilities": true,
  "enable_waf_bypass": false
}
```

### Рекомендуемые Настройки для Начинающих

```json
{
  "crawl_delay": 3.0,
  "crawl_depth": 1,
  "timeout": 30,
  "database_types": ["mysql"],
  "verify_vulnerabilities": true,
  "enable_waf_bypass": false
}
```

## 🎓 Понимание Результатов

### Уровни Уязвимостей

- **High** - Критическая уязвимость, требует немедленного исправления
- **Medium** - Уязвимость средней важности
- **Low** - Низкий риск, но стоит исправить

### Confidence Score

- **0.9-1.0** - Очень высокая вероятность уязвимости
- **0.7-0.9** - Высокая вероятность
- **0.5-0.7** - Средняя вероятность, требует проверки
- **< 0.5** - Низкая вероятность, возможно ложное срабатывание

## 🛠️ Поиск и Решение Проблем

### Общие Проблемы

**Проблема:** `ModuleNotFoundError: No module named 'requests'`
**Решение:** Установите зависимости: `pip install -r requirements.txt`

**Проблема:** `Connection timeout`
**Решение:** Увеличьте timeout в config.json

**Проблема:** Сайт блокирует сканер
**Решение:** Увеличьте crawl_delay и уменьшите crawl_depth

## 📚 Следующие Шаги

После освоения базового использования:

1. Изучите **Advanced User Guide** для углубленных функций
2. Настройте **Enterprise Security Mode** для продвинутой безопасности
3. Изучите **Security Architecture** для понимания внутренней работы
4. Настройте **Custom Payloads** для специфических сценариев

## 🆘 Где Получить Помощь

- Проверьте логи в консоли
- Изучите отчеты в папке `reports/`
- Прочитайте документацию для продвинутых пользователей
- Проверьте конфигурационные файлы

## ⚡ Быстрые Советы

1. **Начинайте с пассивного режима** - меньше нагрузки на сайт
2. **Используйте задержки** - не "бомбите" сайт запросами
3. **Проверяйте результаты** - не все найденное - настоящие уязвимости
4. **Сохраняйте отчеты** - для анализа и сравнения
5. **Будьте этичны** - сканируйте только с разрешения

---

**Важно:** Этот инструмент создан для образовательных целей и легального тестирования безопасности. Используйте его ответственно!
