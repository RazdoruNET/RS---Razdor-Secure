# 🎯 Быстрый старт

## 📋 Установка за 5 минут

### Шаг 1: Установка

```bash
# Глобальная установка
npm install -g sqlguard-pro

# Или локальная установка
npm install sqlguard-pro
```

### Шаг 2: Инициализация

```bash
# Создание конфигурационного файла
sqlguard init

# Интерактивная настройка
sqlguard init --interactive
```

### Шаг 3: Первое сканирование

```bash
# Сканирование одного файла
sqlguard analyze file.sql

# Сканирование директории
sqlguard analyze --directory ./src

# Сканирование с выводом в HTML
sqlguard analyze --directory . --format html --output report.html
```

---

## ⚡ Быстрое использование

### Анализ SQL файла

```bash
# Базовый анализ
sqlguard analyze queries.sql

# С указанием типа БД
sqlguard analyze queries.sql --database mysql

# С детальной информацией
sqlguard analyze queries.sql --verbose --format json
```

### Анализ проекта

```bash
# Все SQL файлы в проекте
sqlguard analyze --directory ./project

# С определенными паттернами
sqlguard analyze --directory ./project --patterns "*.sql,*.js"

# Исключая директории
sqlguard analyze --directory ./project --exclude "node_modules,dist"
```

### Генерация отчетов

```bash
# HTML отчет
sqlguard analyze --directory . --format html --output security-report.html

# PDF отчет
sqlguard analyze --directory . --format pdf --output security-report.pdf

# SARIF для CI/CD
sqlguard analyze --directory . --format sarif --output security-results.sarif
```

---

## 🔧 Конфигурация

### Базовый конфигурационный файл

```json
{
  "database": "mysql",
  "securityLevel": "medium",
  "outputFormat": "html",
  "excludePatterns": [
    "node_modules/**",
    "dist/**",
    "*.min.js"
  ],
  "rules": {
    "sqlInjection": {
      "enabled": true,
      "severity": "high"
    },
    "performance": {
      "enabled": true,
      "threshold": 1000
    }
  }
}
```

### Сохранение конфигурации

```bash
# Создание файла конфигурации
sqlguard config --init

# Установка параметров
sqlguard config set database postgresql
sqlguard config set securityLevel high
sqlguard config set outputFormat json

# Просмотр конфигурации
sqlguard config --list
```

---

## 🎯 Примеры использования

### Node.js проект

```bash
# Анализ всех SQL файлов
sqlguard analyze --directory ./models --database postgresql

# Проверка миграций
sqlguard analyze --directory ./migrations --verbose

# Генерация отчета для команды
sqlguard analyze --directory . --format html --output team-report.html
```

### Python проект

```bash
# Анализ Django моделей
sqlguard analyze --directory ./myapp/models --database mysql

# Проверка SQLAlchemy запросов
sqlguard analyze --directory ./models --database postgresql

# Анализ raw SQL в Python файлах
sqlguard analyze --directory ./ --patterns "*.py" --database mysql
```

### Java проект

```bash
# Анализ MyBatis мапперов
sqlguard analyze --directory ./src/main/resources/mapper --database mysql

# Проверка JPA репозиториев
sqlguard analyze --directory ./src/main/java --database postgresql

# Анализ всех SQL файлов
sqlguard analyze --directory . --patterns "*.sql" --database oracle
```

---

## 📊 Интерпретация результатов

### Структура отчета

```json
{
  "summary": {
    "totalFiles": 15,
    "vulnerabilities": {
      "critical": 2,
      "high": 5,
      "medium": 8,
      "low": 3
    },
    "score": 6.8
  },
  "files": [
    {
      "path": "models/user.js",
      "vulnerabilities": [
        {
          "type": "SQL Injection",
          "severity": "High",
          "line": 23,
          "description": "Concatenation of user input in SQL query",
          "recommendation": "Use parameterized queries"
        }
      ]
    }
  ]
}
```

### Приоритеты исправления

1. **Critical** - Немедленное исправление
2. **High** - Исправить в течение 24 часов
3. **Medium** - Исправить в течение недели
4. **Low** - Исправить при следующем релизе

---

## 🚀 Интеграция с CI/CD

### GitHub Actions

```yaml
name: SQL Security Scan
on: [push, pull_request]

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
          sqlguard analyze --directory . --format sarif --output security-results.sarif
      - name: Upload Results
        uses: github/codeql-action/upload-sarif@v1
        with:
          sarif_file: security-results.sarif
```

### Jenkins Pipeline

```groovy
pipeline {
  agent any
  stages {
    stage('SQL Security Scan') {
      steps {
        sh 'npm install -g sqlguard-pro'
        sh 'sqlguard analyze --directory . --format html --output security-report.html'
        publishHTML([
          allowMissing: false,
          alwaysLinkToLastBuild: true,
          reportDir: '.',
          reportFiles: 'security-report.html',
          reportName: 'SQL Security Report'
        ])
      }
    }
  }
}
```

---

## 🔍 Расширенные возможности

### Кастомные правила

```javascript
// sqlguard-rules.js
module.exports = [
  {
    name: 'Custom SQL Injection Pattern',
    pattern: /query\s*\(\s*['"]\s*\+\s*.*\s*\+\s*['"]/i,
    severity: 'High',
    message: 'Potential SQL injection through string concatenation'
  },
  {
    name: 'Hardcoded Password',
    pattern: /password\s*=\s*['"][^'"]{8,}['"]/i,
    severity: 'Critical',
    message: 'Hardcoded password detected'
  }
];
```

### Использование кастомных правил

```bash
# Применение кастомных правил
sqlguard analyze --directory . --rules ./sqlguard-rules.js

# Комбинация со встроенными правилами
sqlguard analyze --directory . --rules ./sqlguard-rules.js --include-built-in
```

---

## ⚠️ Частые проблемы

### Установка

**Проблема:** Permission denied
```bash
# Решение: Используйте sudo или npx
sudo npm install -g sqlguard-pro
# или
npx sqlguard-pro analyze file.sql
```

**Проблема:** Команда не найдена
```bash
# Решение: Проверьте PATH
echo $PATH
# или используйте полный путь
~/.npm-global/bin/sqlguard-pro analyze file.sql
```

### Сканирование

**Проблема:** Нет результатов
```bash
# Решение: Проверьте паттерны файлов
sqlguard analyze --directory . --patterns "*.sql,*.js,*.py" --verbose

# Проверьте исключения
sqlguard analyze --directory . --exclude "" --verbose
```

**Проблема:** Ложные срабатывания
```bash
# Решение: Настройте уровень безопасности
sqlguard analyze --directory . --security-level low

# или отключите конкретные правила
sqlguard analyze --directory . --disable-rule sql-injection-basic
```

---

## 📚 Следующие шаги

1. **Изучите документацию:**
   - [Руководство для новичков](./beginner-guide.md)
   - [Руководство для среднего уровня](./intermediate-guide.md)

2. **Настройте IDE:**
   - [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=sqlguard-pro.vscode)
   - [JetBrains Plugin](https://plugins.jetbrains.com/plugin/12345-sqlguard-pro)

3. **Интегрируйте с процессами:**
   - Настройте CI/CD пайплайны
   - Создайте шаблоны отчетов
   - Обучите команду использованию

---

## 🆘 Поддержка

- **Документация:** [https://docs.sqlguard-pro.com](https://docs.sqlguard-pro.com)
- **GitHub Issues:** [sqlguard-pro/issues](https://github.com/sqlguard-pro/sqlguard-pro/issues)
- **Discord:** [discord.gg/sqlguard](https://discord.gg/sqlguard)
- **Email:** [support@sqlguard-pro.com](mailto:support@sqlguard-pro.com)

---

*Последнее обновление: 9 мая 2026*
