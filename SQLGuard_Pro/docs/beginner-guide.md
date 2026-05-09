# Руководство для новичков - SQLGuard Pro

## Содержание

1. [Введение](#введение)
2. [Установка](#установка)
3. [Первый запуск](#первый-запуск)
4. [Основные концепции](#основные-концепции)
5. [Практические примеры](#практические-примеры)
6. [Частые вопросы](#частые-вопросы)
7. [Следующие шаги](#следующие-шаги)

## Введение

### Что такое SQLGuard Pro?

SQLGuard Pro - это инструмент, который помогает находить проблемы безопасности в SQL-коде. Представьте его как детектор для вашего SQL-кода, который предупреждает о потенциальных уязвимостях до того, как они станут проблемой.

### Зачем он нужен?

- **Безопасность**: Находит SQL-инъекции и другие уязвимости
- **Качество кода**: Помогает писать лучший SQL-код
- **Обучение**: Учит лучшим практикам безопасности
- **Экономия времени**: Находит проблемы на ранней стадии

### Как это работает?

```
Ваш SQL-код → Анализатор → Отчет с проблемами → Рекомендации по исправлению
```

## Установка

### Требования

- Node.js версии 16 или выше
- Текстовый редактор (рекомендуется VS Code или Cascade SWE-1.5)
- Базовые знания SQL

### Шаг 1: Установка через npm

Откройте терминал и выполните:

```bash
npm install -g sqlguard-pro
```

### Шаг 2: Проверка установки

```bash
sqlguard --version
```

Если вы видите версию, установка прошла успешно!

### Шаг 3: Интеграция с редактором

**Для VS Code:**
1. Откройте VS Code
2. Перейдите в Extensions (Ctrl+Shift+X)
3. Найдите "SQLGuard Pro"
4. Нажмите Install

**Для Cascade SWE-1.5:**
Интеграция происходит автоматически при установке npm пакета.

## Первый запуск

### Создание тестового файла

Создайте файл `test.sql` со следующим содержимым:

```sql
-- Пример с уязвимостью
SELECT * FROM users WHERE username = '${username}' AND password = '${password}';
```

### Запуск анализа

**Через командную строку:**
```bash
sqlguard analyze test.sql
```

**Через Cascade SWE-1.5:**
1. Откройте файл `test.sql`
2. Нажмите `Ctrl+Shift+P`
3. Введите "SQLGuard: Analyze Current File"
4. Нажмите Enter

### Что вы увидите?

После анализа вы получите отчет примерно такого вида:

```json
{
  "vulnerabilities": [
    {
      "type": "SQL_INJECTION",
      "severity": "CRITICAL",
      "title": "SQL Injection Vulnerability",
      "description": "Direct string concatenation creates SQL injection risk",
      "line": 2,
      "column": 38,
      "recommendation": "Use parameterized queries instead of string concatenation"
    }
  ],
  "statistics": {
    "totalQueries": 1,
    "vulnerabilitiesFound": 1,
    "analysisTime": "45ms"
  }
}
```

## Основные концепции

### Уязвимости

#### Что такое уязвимость?

Уязвимость - это слабое место в коде, которое может быть использовано злоумышленниками.

#### Основные типы уязвимостей:

1. **SQL Injection (SQLi)**
   - Самая опасная уязвимость
   - Позволяет выполнять произвольный SQL-код
   - Пример: `' OR '1'='1`

2. **Hardcoded Credentials**
   - Встроенные в код пароли и ключи
   - Пример: `password = 'admin123'`

3. **Missing Input Validation**
   - Отсутствие проверки входных данных
   - Пример: принятие любых данных от пользователя

### Уровни критичности

- **🚨 Critical** - Немедленная угроза безопасности
- **⚠️ High** - Серьезная проблема
- **📡 Medium** - Важная, но не критическая
- **ℹ️ Low** - Минимальная проблема

### Правила хорошего SQL-кода

#### ✅ Правильно:
```sql
-- Использование параметризованных запросов
SELECT * FROM users WHERE username = ? AND password = ?;

-- Использование хранимых процедур
CALL authenticate_user(?, ?);

-- Валидация входных данных
SELECT * FROM users WHERE user_id = CAST(? AS INTEGER);
```

#### ❌ Неправильно:
```sql
-- Прямая конкатенация строк
SELECT * FROM users WHERE username = ''' + username + ''';

-- Встроенные пароли
SELECT * FROM admin WHERE password = 'secret123';

-- Отсутствие валидации
SELECT * FROM products WHERE price = user_input;
```

## Практические примеры

### Пример 1: Поиск и исправление SQL Injection

**Проблемный код:**
```sql
-- vulnerable_query.sql
SELECT * FROM products WHERE category = '${user_category}';
```

**Анализ:**
```bash
sqlguard analyze vulnerable_query.sql
```

**Результат:**
```
🚨 CRITICAL: SQL Injection Vulnerability
Строка: 1, колонка: 40
Описание: Прямая конкатенация строк создает риск SQL-инъекции
Рекомендация: Используйте параметризованные запросы
```

**Исправленный код:**
```sql
-- secure_query.sql
SELECT * FROM products WHERE category = ?;
```

### Пример 2: Анализ целого проекта

**Структура проекта:**
```
my-project/
├── database/
│   ├── users.sql
│   ├── products.sql
│   └── orders.sql
├── config/
│   └── database.sql
└── reports/
    └── analytics.sql
```

**Запуск анализа:**
```bash
sqlguard analyze --directory ./my-project
```

**Генерация HTML отчета:**
```bash
sqlguard analyze --directory ./my-project --format html --output security-report.html
```

### Пример 3: CI/CD интеграция

**GitHub Actions (.github/workflows/security.yml):**
```yaml
name: SQL Security Check

on:
  push:
    paths: ['**/*.sql']
  pull_request:
    paths: ['**/*.sql']

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
          
      - name: Install SQLGuard Pro
        run: npm install -g sqlguard-pro
        
      - name: Run Security Scan
        run: |
          sqlguard analyze --directory . --format json --output results.json
          
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: security-report
          path: results.json
```

## Частые вопросы

### Q: SQLGuard Pro замедляет мою работу?

**A:** Нет, анализ происходит в фоновом режиме. Большинство файлов анализируется за доли секунды.

### Q: Нужно ли подключение к интернету?

**A:** Нет, SQLGuard Pro работает полностью офлайн. Ваши SQL-файлы никогда не покидают ваш компьютер.

### Q: Может ли SQLGuard Pro исправить код за меня?

**A:** SQLGuard Pro только находит проблемы и дает рекомендации. Исправление кода остается за разработчиком.

### Q: Какие базы данных поддерживаются?

**A:** MySQL, PostgreSQL, MSSQL, Oracle, SQLite. Поддерживаются специфичные для каждой СУБД конструкции.

### Q: Как часто обновляются правила?

**A:** Правила безопасности обновляются автоматически каждый месяц. Включены последние угрозы OWASP Top 10.

### Q: Что делать с ложными срабатываниями?

**A:** 
1. Проверьте, действительно ли это ложное срабатывание
2. Если да - можно игнорировать конкретное правило
3. Сообщите о ложном срабатывании разработчикам

### Q: Как анализировать большие проекты?

**A:**
- Используйте `--max-concurrent` для контроля нагрузки
- Включите кэширование `--cache`
- Анализируйте по частям, если проект очень большой

## Следующие шаги

### Изучение дополнительных возможностей

1. **Продвинутая конфигурация**
   - Создайте файл `.sqlguard.json`
   - Настройте уровни безопасности
   - Добавьте собственные правила

2. **Интеграция с IDE**
   - Настройте горячие клавиши
   - Кастомизируйте подсветку
   - Используйте быстрые исправления

3. **Автоматизация**
   - Настройте pre-commit хуки
   - Интегрируйте в CI/CD пайплайн
   - Создайте кастомные отчеты

### Рекомендуемые ресурсы

1. **Документация:**
   - [Полное руководство](./intermediate-guide.md)
   - [API документация](./api-reference.md)
   - [Примеры кода](../examples/)

2. **Обучение безопасности:**
   - [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
   - [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
   - [Лучшие практики SQL](https://www.w3schools.com/sql/sql_injection.asp)

3. **Сообщество:**
   - [GitHub Discussions](https://github.com/your-org/sqlguard-pro/discussions)
   - [Discord сервер](https://discord.gg/sqlguard)
   - [Stack Overflow тег](https://stackoverflow.com/questions/tagged/sqlguard-pro)

### Практические задания

1. **Базовое задание:**
   - Создайте 5 SQL-файлов с разными уязвимостями
   - Проанализируйте их с помощью SQLGuard Pro
   - Исправьте все найденные проблемы

2. **Продвинутое задание:**
   - Настройте CI/CD пайплайн с автоматической проверкой
   - Создайте собственное правило анализа
   - Сгенерируйте кастомный отчет

3. **Экспертное задание:**
   - Интегрируйте SQLGuard Pro в существующий проект
   - Настройте мониторинг в реальном времени
   - Создайте дашборд безопасности

---

**Поздравляем!** Вы освоили основы SQLGuard Pro. Теперь вы готовы писать более безопасный SQL-код.

*Продолжайте обучение в [руководстве для среднего уровня](./intermediate-guide.md)*
