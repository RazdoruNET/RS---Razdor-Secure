# 🚀 Первое сканирование с Prophecy Sentinel

Пошаговое руководство по проведению первого сканирования

---

## 🎯 Цель этого руководства

Научиться:
- ✅ Запускать базовое сканирование
- ✅ Читать и понимать результаты
- ✅ Проверять найденные уязвимости
- ✅ Сохранять и анализировать отчеты

---

## 📋 Подготовка к сканированию

### 🔐 Проверка разрешений
**ВАЖНО**: Убедитесь, что у вас есть право сканировать цель!

✅ **Разрешенные цели для обучения**:
- `localhost:8080` (DVWA)
- `localhost:3000` (Juice Shop)
- `testphp.vulnwebapp.com` (публичный тестовый сайт)

❌ **Запрещено без разрешения**:
- Продуктивные сайты компаний
- Государственные сайты
- Сайты других пользователей

### 🏗️ Запуск тестовой среды
```bash
# Запуск DVWA
docker-compose -f docker-compose.dvwa.yml up -d

# Проверка доступности
curl http://localhost:8080
```

---

## 🚀 Первое сканирование

### 📊 Базовая команда
```bash
node ProphecySentinel.js <target>
```

### 🎯 Примеры сканирования

#### 1. Тестовое сканирование DVWA
```bash
node ProphecySentinel.js localhost:8080
```

#### 2. Тестовое сканирование Juice Shop
```bash
node ProphecySentinel.js localhost:3000
```

#### 3. Публичный тестовый сайт
```bash
node ProphecySentinel.js testphp.vulnwebapp.com
```

---

## 📊 Что происходит во время сканирования

### 🔄 Этапы сканирования

#### Этап 1: Тестирование соединения
```
🌐 Phase 1: Connectivity testing...
✅ Target reachable
```

#### Этап 2: Параллельное тестирование
```
🔍 Phase 2: Parallel vulnerability testing...
📊 Parallel testing results:
  SQL Injection: ✅ (16 tests)
  XSS: ✅ (40 tests)
  Directory Traversal: ✅ (0 tests)
  File Inclusion: ✅ (4 tests)
  Security Headers: ✅ (7 tests)
```

#### Этап 3: Анализ конфигурации
```
⚙️ Phase 3: Advanced configuration analysis...
🖥️  Server: Apache/2.4.41
🔧 Technology: PHP/7.4.3
```

#### Этап 4: Перечисление сервисов
```
🛠️ Phase 4: Smart service enumeration...
🚨 Configuration_File FOUND: /config.php
🚨  FOUND: /robots.txt
```

#### Этап 5: Корреляция доказательств
```
🔍 Phase 5: Evidence correlation and false-positive suppression...
📊 Filtered 7 findings from 15 groups
```

#### Этап 6: Генерация отчета
```
📋 Phase 6: Professional reporting...
================================================================================
📋 PROPHECY SENTINEL SCAN REPORT
================================================================================
```

---

## 📊 Чтение результатов

### 🎯 Основные метрики
```
🎯 Target: localhost:8080
📅 Date: 2026-05-09T10:40:56.478Z
🔍 Total vulnerabilities found: 7

🚨 Critical: 0
⚠️  High: 3
⚠️  Medium: 4
🔸 Low: 0
```

### 🔍 Детальная разбивка по уязвимостям

#### SQL Injection
```
SQL_INJECTION: 2 vulnerabilities
  1. /login [HIGH]
     Status: 200
     Evidence: SQL error detected
     Confidence: 90%
     Payload: 1' AND '1'='1
```

#### XSS
```
XSS: 4 vulnerabilities
  1. /search [MEDIUM]
     Status: 200
     Evidence: Script tag with alert detected
     Confidence: 60%
     Payload: <script>alert("XSS")</script>
```

#### File Inclusion
```
FILE_INCLUSION: 1 vulnerabilities
  1. /include [HIGH]
     Status: 200
     Evidence: System command output detected
     Confidence: 90%
     Payload: data://text/plain;base64,SGVsbG8gV29ybGQ=
```

---

## 📈 CVSS оценка рисков

### 🎯 Оценка по типам уязвимостей
```
📈 CVSS Scoring Summary:
  SQL_INJECTION: 8.9
  XSS: 5.9
  FILE_INCLUSION: 8.4
  Overall Risk Score: 7.7/10.0
```

### 🎨 Интерпретация CVSS
- **0.1-3.9**: Низкий риск
- **4.0-6.9**: Средний риск
- **7.0-8.9**: Высокий риск
- **9.0-10.0**: Критический риск

---

## 💡 Рекомендации по результатам

### 🚨 Высокий приоритет
```
🟠 HIGH PRIORITY:
  1. Patch within 24-48 hours
  2. Implement compensating controls
  3. Security team review required
```

### 🟡 Средний приоритет
```
🟡 MEDIUM PRIORITY:
  1. Patch within 1-2 weeks
  2. Update security policies
  3. Developer training
```

---

## 📁 Сохранение результатов

### 📄 Автоматическое сохранение
Результаты автоматически сохраняются в:
- `scan_results.json` - детальный отчет в JSON
- Консольный вывод - краткий отчет

### 📊 Ручное сохранение
```bash
# Сохранение в файл
node ProphecySentinel.js localhost:8080 > scan_report.txt

# Сохранение только JSON
node ProphecySentinel.js localhost:8080 2>/dev/null | jq '.scanReport' > report.json
```

---

## 🧪 Проверка найденных уязвимостей

### 🔍 Ручная проверка SQL Injection
```bash
# Тестирование найденной уязвимости
curl -X POST "http://localhost:8080/login" \
  -d "username=admin&password=1' OR '1'='1"
```

### 🎭 Ручная проверка XSS
```bash
# Тестирование XSS в параметре
curl "http://localhost:8080/search?q=<script>alert(1)</script>"
```

### 📁 Ручная проверка File Inclusion
```bash
# Тестирование LFI
curl "http://localhost:8080/include?file=../../../etc/passwd"
```

---

## 🛠️ Расширенные опции сканирования

### ⚙️ Изменение параметров
```javascript
// Создание custom-scan.js
const ProphecySentinel = require('./ProphecySentinel');

const sentinel = new ProphecySentinel();

// Настройка параметров
sentinel.concurrencyLimit = 3;        // Уменьшить нагрузку
sentinel.rateLimitDelay = 2000;       // Увеличить задержку
sentinel.confidenceThreshold = 0.7;    // Повысить порог уверенности

// Запуск сканирования
sentinel.initialize('localhost:8080')
  .then(() => sentinel.performEnhancedScan())
  .catch(console.error);
```

### 🎯 Специфические тесты
```javascript
// Только SQL Injection
await sentinel.testSQLInjection();

// Только XSS
await sentinel.testXSS();

// Только заголовки
await sentinel.testSecurityHeaders();
```

---

## 🐛 Устранение проблем

### ❌ Частые ошибки при первом сканировании

#### Ошибка: "Target not reachable"
```
❌ Target not reachable by any method
```
**Решение**:
- Проверьте доступность цели: `curl http://target`
- Убедитесь, что порт открыт: `telnet target 80`
- Проверьте сетевое соединение

#### Ошибка: "Permission denied"
```
❌ Error: connect EACCES
```
**Решение**:
- Используйте `sudo` если необходимо
- Проверьте права на файлы
- Используйте порт > 1024

#### Ошибка: "No vulnerabilities found"
```
🔍 Total vulnerabilities found: 0
```
**Решение**:
- Снизьте порог уверенности: `sentinel.confidenceThreshold = 0.3`
- Проверьте, что цель действительно уязвима
- Используйте тестовые цели

---

## 📊 Анализ результатов

### 📈 Метрики качества
```javascript
// Анализ результатов
const fs = require('fs');
const results = JSON.parse(fs.readFileSync('scan_results.json'));

const totalVulns = results.scanReport.vulnerabilityDetails;
const highRisk = Object.values(totalVulns).filter(v => v.severity === 'HIGH').length;
const mediumRisk = Object.values(totalVulns).filter(v => v.severity === 'MEDIUM').length;

console.log(`Высокий риск: ${highRisk}`);
console.log(`Средний риск: ${mediumRisk}`);
console.log(`Общий риск: ${results.scanReport.executiveSummary.overallRiskScore}/10.0`);
```

### 📊 Визуализация результатов
```javascript
// Создание простого графика
const results = JSON.parse(fs.readFileSync('scan_results.json'));
const vulnTypes = Object.keys(results.scanReport.vulnerabilityDetails);

console.log('📊 Распределение уязвимостей:');
vulnTypes.forEach(type => {
  const count = results.scanReport.vulnerabilityDetails[type].count;
  const bar = '█'.repeat(count);
  console.log(`${type}: ${bar} (${count})`);
});
```

---

## 🎯 Следующие шаги

### 📚 Изучение найденных уязвимостей
1. [SQL Injection - подробное руководство](./sql-injection-basics.md)
2. [XSS - подробное руководство](./xss-basics.md)
3. [File Inclusion - подробное руководство](./other-vulnerabilities.md)

### 🛡️ Практика валидации
1. [Основы валидации](./basic-validation.md)
2. [Продвинутые техники](../intermediate/validation-techniques.md)

### 📊 Продвинутый анализ
1. [Анализ отчетов](./understanding-results.md)
2. [Метрики и KPI](../intermediate/metrics-analysis.md)

---

## 💡 Советы для первого сканирования

### ✨ Лучшие практики
- Начинайте с тестовых целей
- Сохраняйте все результаты
- Ведите заметки о находках
- Не бойтесь экспериментировать

### 🛡️ Безопасность
- Всегда получайте разрешение
- Используйте изолированные сети
- Не сохраняйте чувствительные данные
- Регулярно обновляйте инструмент

---

## 🆘 Помощь

Если у вас возникли проблемы:

- 📖 [Документация](../technical/README.md)
- 💬 [GitHub Discussions](https://github.com/prophecy-sentinel/prophecy-sentinel/discussions)
- 🐛 [GitHub Issues](https://github.com/prophecy-sentinel/prophecy-sentinel/issues)

---

## 🎯 Поздравляем! 🎉

Вы успешно провели первое сканирование с Prophecy Sentinel!

**Что вы узнали**:
- ✅ Как запускать сканирование
- ✅ Как читать результаты
- ✅ Как интерпретировать CVSS оценки
- ✅ Как сохранять и анализировать отчеты

**Следующие шаги**:
- 📚 Изучите [основы безопасности](./security-basics.md)
- 🔍 Практикуйтесь на [тестовых целях](./safe-environment.md)
- 🎭 Попробуйте [валидацию уязвимостей](./basic-validation.md)

---

**Готовы к следующему уровню? Перейдите к [основам безопасности](./security-basics.md)!** 🚀
