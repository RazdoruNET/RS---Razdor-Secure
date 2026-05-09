# 📚 API Reference

## 🎯 Обзор API

Prophecy Sentinel предоставляет мощный API для программной интеграции и автоматизации сканирования безопасности.

---

## 🔧 Основные классы

### ProphecySentinel

Основной класс для выполнения сканирования безопасности.

```javascript
const ProphecySentinel = require('../ProphecySentinel');

const sentinel = new ProphecySentinel({
  target: 'https://example.com',
  options: {
    timeout: 30000,
    concurrency: 5,
    userAgent: 'ProphecySentinel/1.0'
  }
});
```

#### Конструктор

**Параметры:**
- `target` (string): Целевой URL или путь к файлам
- `options` (object): Дополнительные опции сканирования

**Опции:**
```javascript
{
  timeout: 30000,           // Таймаут запросов (ms)
  concurrency: 5,            // Количество параллельных запросов
  userAgent: 'Custom Agent', // User-Agent строка
  headers: {},              // Дополнительные заголовки
  proxy: null,              // Прокси сервер
  verbose: false,           // Подробный вывод
  outputFormat: 'json'       // Формат вывода
}
```

#### Методы

##### scan(target, options)
Выполняет сканирование указанной цели.

**Параметры:**
- `target` (string): Цель сканирования
- `options` (object): Опции сканирования

**Возвращает:** `Promise<ScanResult>`

```javascript
const result = await sentinel.scan('https://example.com', {
  scanTypes: ['xss', 'sqli', 'directory'],
  depth: 3
});
```

##### generateReport(result, format)
Генерирует отчет в указанном формате.

**Параметры:**
- `result` (ScanResult): Результаты сканирования
- `format` (string): Формат отчета ('json', 'html', 'pdf', 'sarif')

**Возвращает:** `Promise<string>`

```javascript
const htmlReport = await sentinel.generateReport(result, 'html');
fs.writeFileSync('report.html', htmlReport);
```

---

## 🔍 VulnerabilityScanner

Класс для обнаружения уязвимостей.

```javascript
const { VulnerabilityScanner } = require('../src/core/VulnerabilityScanner');

const scanner = new VulnerabilityScanner({
  enabledModules: ['xss', 'sqli', 'lfi'],
  sensitivity: 'medium'
});
```

### Методы

#### detectVulnerabilities(content, context)
Обнаруживает уязвимости в указанном контенте.

**Параметры:**
- `content` (string): Анализируемый контент
- `context` (object): Контекст анализа

**Возвращает:** `Promise<Vulnerability[]>`

```javascript
const vulnerabilities = await scanner.detectVulnerabilities(htmlContent, {
  url: 'https://example.com/page',
  method: 'GET'
});
```

---

## 🎭 PlaywrightXSSConfirmation

Класс для подтверждения XSS уязвимостей через браузер.

```javascript
const { PlaywrightXSSConfirmation } = require('../src/confirmation/PlaywrightXSSConfirmation');

const xssConfirm = new PlaywrightXSSConfirmation({
  headless: true,
  timeout: 10000
});
```

### Методы

#### confirmXSS(url, payload, parameter)
Подтверждает XSS уязвимость.

**Параметры:**
- `url` (string): URL для тестирования
- `payload` (string): XSS payload
- `parameter` (string): Параметр для инъекции

**Возвращает:** `Promise<XSSResult>`

```javascript
const result = await xssConfirm.confirmXSS(
  'https://example.com/search',
  '<script>alert(1)</script>',
  'query'
);

console.log(`XSS подтвержден: ${result.confirmed}`);
```

---

## 📊 Типы данных

### ScanResult

```javascript
{
  scanId: 'uuid-v4',
  timestamp: '2026-05-09T15:20:00Z',
  target: 'https://example.com',
  duration: 45000,
  vulnerabilities: [
    {
      id: 'vuln-1',
      type: 'XSS',
      severity: 'High',
      confidence: 0.95,
      url: 'https://example.com/search',
      parameter: 'query',
      payload: '<script>alert(1)</script>',
      evidence: 'alert() executed in browser',
      cwe: 'CWE-79',
      cvss: 7.5
    }
  ],
  summary: {
    total: 1,
    critical: 0,
    high: 1,
    medium: 0,
    low: 0
  }
}
```

### Vulnerability

```javascript
{
  id: 'unique-id',
  type: 'XSS|SQLi|LFI|Directory Traversal',
  severity: 'Critical|High|Medium|Low',
  confidence: 0.0-1.0,
  url: 'https://example.com/vulnerable',
  method: 'GET|POST|PUT|DELETE',
  parameter: 'param-name',
  payload: 'malicious-payload',
  evidence: 'evidence-of-vulnerability',
  description: 'detailed-description',
  recommendation: 'how-to-fix',
  cwe: 'CWE-ID',
  cvss: 0.0-10.0,
  references: ['https://owasp.org/...']
}
```

### XSSResult

```javascript
{
  confirmed: true,
  url: 'https://example.com/search',
  payload: '<script>alert(1)</script>',
  parameter: 'query',
  executionTime: 1500,
  browserInfo: {
    name: 'chromium',
    version: '90.0.4430.0'
  },
  screenshot: 'base64-screenshot',
  consoleLogs: ['XSS payload executed successfully']
}
```

---

## 🔧 Конфигурация

### ConfigManager

Класс для управления конфигурацией.

```javascript
const { ConfigManager } = require('../src/config/ConfigManager');

const config = new ConfigManager('./config.json');
```

#### Методы

##### load(path)
Загружает конфигурацию из файла.

```javascript
await config.load('./config.json');
```

##### get(key, defaultValue)
Получает значение конфигурации.

```javascript
const timeout = config.get('scanner.timeout', 30000);
```

##### set(key, value)
Устанавливает значение конфигурации.

```javascript
config.set('scanner.timeout', 60000);
```

---

## 📈 Метрики и отчеты

### MetricsCollector

Класс для сбора метрик сканирования.

```javascript
const { MetricsCollector } = require('../src/analysis/MetricsCollector');

const metrics = new MetricsCollector();
```

#### Методы

##### recordScan(result)
Записывает метрики сканирования.

```javascript
metrics.recordScan(scanResult);
```

##### getMetrics()
Получает собранные метрики.

```javascript
const scanMetrics = metrics.getMetrics();
console.log(`Всего сканирований: ${scanMetrics.totalScans}`);
```

---

## 🔌 Интеграция с CI/CD

### GitHub Actions

```yaml
name: Security Scan
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
      - name: Install dependencies
        run: npm install
      - name: Run security scan
        run: |
          node ProphecySentinel.js --target ${{ secrets.TARGET_URL }} \
            --format sarif \
            --output security-results.sarif
      - name: Upload results
        uses: github/codeql-action/upload-sarif@v1
        with:
          sarif_file: security-results.sarif
```

### Jenkins Pipeline

```groovy
pipeline {
  agent any
  stages {
    stage('Security Scan') {
      steps {
        sh 'npm install'
        sh 'node ProphecySentinel.js --target ${TARGET_URL} --format json --output report.json'
        publishHTML([
          allowMissing: false,
          alwaysLinkToLastBuild: true,
          keepAll: true,
          reportDir: '.',
          reportFiles: 'report.html',
          reportName: 'Security Report'
        ])
      }
    }
  }
}
```

---

## 🛡️ Безопасность API

### Аутентификация

```javascript
const sentinel = new ProphecySentinel({
  apiKey: process.env.SENTINEL_API_KEY,
  apiSecret: process.env.SENTINEL_API_SECRET
});
```

### Rate Limiting

API автоматически применяет rate limiting для предотвращения злоупотреблений:

- **100 запросов в минуту** для бесплатной версии
- **1000 запросов в минуту** для профессиональной версии
- **Без ограничений** для enterprise версии

### Шифрование

Все API запросы шифруются с помощью TLS 1.3. Данные передаются в зашифрованном виде.

---

## 🚨 Обработка ошибок

### Common Errors

```javascript
try {
  const result = await sentinel.scan(target);
} catch (error) {
  switch (error.code) {
    case 'TIMEOUT':
      console.error('Таймаут сканирования');
      break;
    case 'NETWORK_ERROR':
      console.error('Ошибка сети');
      break;
    case 'INVALID_TARGET':
      console.error('Неверная цель');
      break;
    case 'RATE_LIMIT':
      console.error('Превышен лимит запросов');
      break;
    default:
      console.error('Неизвестная ошибка:', error.message);
  }
}
```

### Error Codes

- `TIMEOUT`: Таймаут операции
- `NETWORK_ERROR`: Ошибка сети
- `INVALID_TARGET`: Неверный формат цели
- `RATE_LIMIT`: Превышен лимит запросов
- `AUTHENTICATION_FAILED`: Ошибка аутентификации
- `PERMISSION_DENIED`: Недостаточно прав
- `INTERNAL_ERROR`: Внутренняя ошибка

---

## 📚 Примеры использования

### Базовое сканирование

```javascript
const ProphecySentinel = require('../ProphecySentinel');

async function basicScan() {
  const sentinel = new ProphecySentinel();
  
  try {
    const result = await sentinel.scan('https://example.com');
    console.log(`Найдено уязвимостей: ${result.vulnerabilities.length}`);
    
    // Генерация HTML отчета
    const report = await sentinel.generateReport(result, 'html');
    fs.writeFileSync('security-report.html', report);
  } catch (error) {
    console.error('Ошибка сканирования:', error.message);
  }
}

basicScan();
```

### Продвинутое сканирование

```javascript
const ProphecySentinel = require('../ProphecySentinel');

async function advancedScan() {
  const sentinel = new ProphecySentinel({
    timeout: 60000,
    concurrency: 10,
    headers: {
      'Authorization': 'Bearer token',
      'User-Agent': 'Custom Scanner'
    }
  });
  
  const options = {
    scanTypes: ['xss', 'sqli', 'lfi', 'directory'],
    depth: 5,
    followRedirects: true,
    verifySSL: false
  };
  
  const result = await sentinel.scan('https://api.example.com', options);
  
  // Фильтрация критических уязвимостей
  const criticalVulns = result.vulnerabilities.filter(v => v.severity === 'Critical');
  
  if (criticalVulns.length > 0) {
    console.log('⚠️ Найдены критические уязвимости:');
    criticalVulns.forEach(vuln => {
      console.log(`- ${vuln.type} в ${vuln.url}`);
    });
  }
}

advancedScan();
```

---

## 🔗 Дополнительные ресурсы

- [GitHub Repository](https://github.com/prophecy-sentinel/prophecy-sentinel)
- [Discord Community](https://discord.gg/prophecy-sentinel)
- [Documentation](https://docs.prophecy-sentinel.com)
- [API Examples](https://github.com/prophecy-sentinel/examples)

---

*Последнее обновление: 9 мая 2026*
