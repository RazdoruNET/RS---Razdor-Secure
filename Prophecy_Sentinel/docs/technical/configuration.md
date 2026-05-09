# ⚙️ Конфигурация

## 📋 Обзор

Prophecy Sentinel предоставляет гибкую систему конфигурации для адаптации под различные сценарии использования и требования безопасности.

---

## 🔧 Файлы конфигурации

### Основной конфигурационный файл

**Расположение:** `config/sentinel.json`

```json
{
  "scanner": {
    "timeout": 30000,
    "concurrency": 5,
    "userAgent": "ProphecySentinel/1.0",
    "maxDepth": 3,
    "followRedirects": true,
    "verifySSL": true
  },
  "modules": {
    "xss": {
      "enabled": true,
      "payloads": ["<script>alert(1)</script>", "javascript:alert(1)"],
      "contexts": ["html", "javascript", "attribute"]
    },
    "sqli": {
      "enabled": true,
      "payloads": ["'", "OR 1=1", "UNION SELECT"],
      "databases": ["mysql", "postgresql", "mssql"]
    },
    "lfi": {
      "enabled": true,
      "payloads": ["../../../etc/passwd", "..%2F..%2F..%2Fetc%2Fpasswd"],
      "filters": [".log", ".txt", ".conf"]
    }
  },
  "reporting": {
    "format": "html",
    "includeScreenshots": true,
    "includeEvidence": true,
    "template": "default"
  },
  "security": {
    "apiKey": "",
    "rateLimit": 100,
    "allowedHosts": ["*"],
    "blockedHosts": []
  }
}
```

---

## 🎯 Настройки сканера

### Базовые параметры

```javascript
const sentinel = new ProphecySentinel({
  // Таймауты
  timeout: 30000,              // Таймаут запросов (ms)
  connectionTimeout: 10000,      // Таймаут соединения (ms)
  readTimeout: 20000,           // Таймаут чтения (ms)
  
  // Производительность
  concurrency: 5,                // Параллельные запросы
  maxRetries: 3,                // Количество повторов
  retryDelay: 1000,             // Задержка между повторами (ms)
  
  // Поведение
  maxDepth: 3,                  // Максимальная глубина
  followRedirects: true,         // Следовать редиректам
  verifySSL: true,               // Проверять SSL сертификаты
  userAgent: "ProphecySentinel/1.0" // User-Agent
});
```

### Продвинутые параметры

```javascript
const sentinel = new ProphecySentinel({
  // Заголовки запросов
  headers: {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive'
  },
  
  // Прокси и сеть
  proxy: {
    host: '127.0.0.1',
    port: 8080,
    protocol: 'http',
    auth: {
      username: 'user',
      password: 'pass'
    }
  },
  
  // Cookies и сессии
  cookies: [
    {
      name: 'session',
      value: 'abc123',
      domain: 'example.com',
      path: '/'
    }
  ],
  
  // Пользовательская аутентификация
  auth: {
    type: 'basic', // basic, bearer, custom
    username: 'user',
    password: 'pass',
    token: 'Bearer token'
  }
});
```

---

## 🔍 Модули сканирования

### XSS Module Configuration

```javascript
const xssConfig = {
  enabled: true,
  
  // Типы XSS для проверки
  types: ['reflected', 'stored', 'dom'],
  
  // Контексты инъекции
  contexts: ['html', 'javascript', 'attribute', 'css', 'url'],
  
  // Кастомные payload'ы
  payloads: [
    '<script>alert(1)</script>',
    'javascript:alert(1)',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '";alert(1);//'
  ],
  
  // Эвристики
  heuristics: {
    checkForReflection: true,
    checkForDOMManipulation: true,
    checkForEventHandlers: true
  },
  
  // Подтверждение
  confirmation: {
    browserTimeout: 10000,
    screenshotOnSuccess: true,
    consoleLogCapture: true
  }
};
```

### SQL Injection Module Configuration

```javascript
const sqliConfig = {
  enabled: true,
  
  // Типы инъекций
  types: ['boolean', 'time', 'union', 'error', 'stacked'],
  
  // Базы данных
  databases: {
    mysql: {
      enabled: true,
      version: '5.7+',
      syntax: 'mysql'
    },
    postgresql: {
      enabled: true,
      version: '10+',
      syntax: 'postgresql'
    },
    mssql: {
      enabled: true,
      version: '2016+',
      syntax: 't-sql'
    }
  },
  
  // Payload'ы
  payloads: {
    boolean: ["' AND 1=1 --", "' AND 1=2 --"],
    time: ["' AND SLEEP(5) --", "'; WAITFOR DELAY '00:00:05' --"],
    union: ["' UNION SELECT 1,2,3 --", "' UNION SELECT NULL,NULL,NULL --"],
    error: ["'", "\"", "' OR 1=1 --"]
  },
  
  // Тайминг анализ
  timing: {
    threshold: 5000,        // Порог времени (ms)
    retries: 3,              // Количество попыток
    variance: 0.2            // Допустимая вариация
  }
};
```

### Directory Traversal Module Configuration

```javascript
const lfiConfig = {
  enabled: true,
  
  // Payload'ы для разных ОС
  payloads: {
    linux: [
      '../../../etc/passwd',
      '../../../etc/shadow',
      '../../../proc/version',
      '../../../var/log/apache2/access.log'
    ],
    windows: [
      '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
      '..\\..\\..\\boot.ini',
      '..\\..\\..\\windows\\win.ini'
    ]
  },
  
  // Кодировки
  encodings: ['plain', 'url', 'double-url', 'unicode'],
  
  // Фильтры файлов
  fileFilters: ['.log', '.txt', '.conf', '.ini', '.passwd'],
  
  // Обнаружение
  detection: {
    successPatterns: ['root:x:0:0', '[boot loader]', 'for 16-bit app'],
    errorPatterns: ['Permission denied', 'No such file', 'Access denied']
  }
};
```

---

## 📊 Настройки отчетности

### Форматы отчетов

```javascript
const reportingConfig = {
  // Основной формат
  format: 'html', // html, json, pdf, sarif, xml
  
  // Шаблоны
  template: 'default', // default, executive, technical, custom
  
  // Включаемые секции
  sections: {
    summary: true,
    vulnerabilities: true,
    evidence: true,
    recommendations: true,
    screenshots: true,
    networkLogs: false,
    fullRequestResponse: false
  },
  
  // Фильтрация
  filters: {
    minSeverity: 'Medium', // Critical, High, Medium, Low
    includeConfirmed: true,
    includeUnconfirmed: false,
    maxResults: 100
  },
  
  // Экспорт
  export: {
    filename: 'security-report-{timestamp}',
    directory: './reports',
    compress: true,
    encrypt: false
  }
};
```

### Кастомные шаблоны

```javascript
// Создание кастомного шаблона
const customTemplate = {
  name: 'Company Template',
  header: `
    <div class="company-header">
      <h1>{{companyName}} Security Report</h1>
      <p>Generated: {{timestamp}}</p>
    </div>
  `,
  vulnerability: `
    <div class="vulnerability">
      <h3>{{type}} - {{severity}}</h3>
      <p><strong>URL:</strong> {{url}}</p>
      <p><strong>Description:</strong> {{description}}</p>
      <p><strong>Recommendation:</strong> {{recommendation}}</p>
    </div>
  `,
  footer: `
    <div class="company-footer">
      <p>Generated by Prophecy Sentinel</p>
    </div>
  `
};

sentinel.setReportingTemplate(customTemplate);
```

---

## 🛡️ Настройки безопасности

### Аутентификация и авторизация

```javascript
const securityConfig = {
  // API ключи
  apiKeys: {
    sentinel: process.env.SENTINEL_API_KEY,
    openai: process.env.OPENAI_API_KEY,
    virustotal: process.env.VIRUSTOTAL_API_KEY
  },
  
  // Rate limiting
  rateLimiting: {
    enabled: true,
    requestsPerMinute: 100,
    burstSize: 20,
    penaltyTime: 60000
  },
  
  // Белые и черные списки
  accessControl: {
    allowedHosts: [
      '*.example.com',
      'api.internal.com'
    ],
    blockedHosts: [
      'malicious-site.com',
      '*.phishing.net'
    ],
    allowedIPs: ['192.168.1.0/24'],
    blockedIPs: ['192.168.1.100']
  }
};
```

### Шифрование и хранение

```javascript
const encryptionConfig = {
  // Шифрование отчетов
  reports: {
    encrypt: true,
    algorithm: 'aes-256-gcm',
    keyDerivation: 'pbkdf2',
    iterations: 100000
  },
  
  // Хранение данных
  storage: {
    type: 'file', // file, database, cloud
    path: './data',
    retention: 30, // дней
    compression: true
  },
  
  // Логирование
  logging: {
    level: 'info', // debug, info, warn, error
    format: 'json',
    rotation: 'daily',
    maxFiles: 30
  }
};
```

---

## 🔌 Интеграция с IDE

### VS Code Extension

```json
// .vscode/settings.json
{
  "prophecy-sentinel.enabled": true,
  "prophecy-sentinel.autoScan": true,
  "prophecy-sentinel.scanOnSave": false,
  "prophecy-sentinel.showNotifications": true,
  "prophecy-sentinel.severityThreshold": "Medium",
  "prophecy-sentinel.excludePatterns": [
    "node_modules/**",
    "dist/**",
    "*.min.js"
  ]
}
```

### JetBrains IDE Plugin

```xml
<!-- plugin.xml -->
<idea-plugin>
  <id>com.prophecy.sentinel</id>
  <name>Prophecy Sentinel</name>
  <vendor>Prophecy Security</vendor>
  
  <extensions defaultExtensionNs="com.intellij">
    <projectService 
      serviceImplementation="com.prophecy.sentinel.ScanService"/>
    <toolWindow 
      id="Prophecy Sentinel" 
      secondary="true" 
      icon="/icons/sentinel.png"/>
  </extensions>
</idea-plugin>
```

---

## 🚀 CI/CD Конфигурация

### GitHub Actions

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: |
        cd Prophecy_Sentinel
        npm install
    
    - name: Configure scanner
      run: |
        cat > config.json << EOF
        {
          "scanner": {
            "timeout": 30000,
            "concurrency": 3
          },
          "reporting": {
            "format": "sarif",
            "minSeverity": "Medium"
          }
        }
        EOF
    
    - name: Run security scan
      run: |
        cd Prophecy_Sentinel
        node ProphecySentinel.js --config config.json --target ${{ env.TARGET_URL }}
      env:
        TARGET_URL: ${{ secrets.TARGET_URL }}
        SENTINEL_API_KEY: ${{ secrets.SENTINEL_API_KEY }}
    
    - name: Upload SARIF file
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: Prophecy_Sentinel/security-results.sarif
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
  agent any
  
  environment {
    SENTINEL_API_KEY = credentials('sentinel-api-key')
    TARGET_URL = credentials('target-url')
  }
  
  stages {
    stage('Security Scan') {
      steps {
        script {
          dir('Prophecy_Sentinel') {
            sh 'npm install'
            
            // Создание конфигурации
            writeFile file: 'config.json', text: """
              {
                "scanner": {
                  "timeout": 30000,
                  "concurrency": 5
                },
                "reporting": {
                  "format": "html",
                  "includeScreenshots": true
                }
              }
            """
            
            // Запуск сканирования
            sh """
              node ProphecySentinel.js \\
                --config config.json \\
                --target ${env.TARGET_URL} \\
                --output security-report.html
            """
            
            // Публикация отчета
            publishHTML([
              allowMissing: false,
              alwaysLinkToLastBuild: true,
              keepAll: true,
              reportDir: '.',
              reportFiles: 'security-report.html',
              reportName: 'Security Scan Report'
            ])
          }
        }
      }
    }
  }
  
  post {
    always {
      archiveArtifacts artifacts: 'Prophecy_Sentinel/security-report.*', fingerprint: true
    }
  }
}
```

---

## 🔧 Управление конфигурацией

### Environment Variables

```bash
# .env
SENTINEL_API_KEY=your-api-key
SENTINEL_CONFIG_PATH=./config/sentinel.json
SENTINEL_LOG_LEVEL=info
SENTINEL_REPORTS_DIR=./reports
SENTINEL_MAX_CONCURRENCY=5
SENTINEL_TIMEOUT=30000

# Database configuration (if using)
SENTINEL_DB_TYPE=sqlite
SENTINEL_DB_PATH=./data/sentinel.db

# External services
OPENAI_API_KEY=your-openai-key
VIRUSTOTAL_API_KEY=your-virustotal-key
```

### Программная конфигурация

```javascript
const { ConfigManager } = require('./src/config/ConfigManager');

// Загрузка конфигурации
const config = new ConfigManager();

// Из разных источников
await config.loadFromFile('./config.json');
await config.loadFromEnvironment();
await config.loadFromDatabase('configurations');

// Динамическая конфигурация
config.set('scanner.timeout', 60000);
config.set('modules.xss.enabled', false);

// Валидация конфигурации
const validation = config.validate();
if (!validation.valid) {
  console.error('Configuration errors:', validation.errors);
  process.exit(1);
}

// Сохранение конфигурации
await config.save('./config-updated.json');
```

---

## 📈 Мониторинг и метрики

### Метрики производительности

```javascript
const metricsConfig = {
  enabled: true,
  
  // Типы метрик
  types: [
    'scan_duration',
    'vulnerabilities_found',
    'requests_per_second',
    'memory_usage',
    'cpu_usage'
  ],
  
  // Экспорт метрик
  export: {
    prometheus: {
      enabled: true,
      port: 9090,
      path: '/metrics'
    },
    datadog: {
      enabled: false,
      apiKey: process.env.DATADOG_API_KEY
    }
  },
  
  // Агрегация
  aggregation: {
    interval: 60000, // ms
    retention: 86400000 // 24 часа
  }
};
```

### Алерты и уведомления

```javascript
const alertsConfig = {
  enabled: true,
  
  channels: {
    email: {
      enabled: true,
      smtp: {
        host: process.env.SMTP_HOST,
        port: 587,
        secure: false,
        auth: {
          user: process.env.SMTP_USER,
          pass: process.env.SMTP_PASS
        }
      },
      recipients: ['security@company.com']
    },
    
    slack: {
      enabled: true,
      webhook: process.env.SLACK_WEBHOOK,
      channel: '#security-alerts'
    },
    
    teams: {
      enabled: false,
      webhook: process.env.TEAMS_WEBHOOK
    }
  },
  
  triggers: {
    criticalVulnerability: true,
    scanFailure: true,
    performanceIssue: false
  }
};
```

---

## 🛠️ Отладка и troubleshooting

### Режим отладки

```javascript
const debugConfig = {
  enabled: true,
  
  // Уровень детализации
  level: 'verbose', // error, warn, info, debug, verbose
  
  // Компоненты для отладки
  components: [
    'scanner',
    'xss-module',
    'sqli-module',
    'report-generator',
    'network-client'
  ],
  
  // Вывод
  output: {
    console: true,
    file: './debug.log',
    maxFileSize: '10MB',
    maxFiles: 5
  },
  
  // Дополнительная информация
  includeRequestResponse: true,
  includeStackTrace: true,
  includeMemoryUsage: true
};
```

### Диагностика проблем

```bash
# Проверка конфигурации
node ProphecySentinel.js --check-config

# Тест подключения
node ProphecySentinel.js --test-connection --target https://example.com

# Валидация модулей
node ProphecySentinel.js --validate-modules

# Диагностика производительности
node ProphecySentinel.js --benchmark --target https://example.com
```

---

## 📚 Примеры конфигураций

### Конфигурация для разработки

```json
{
  "scanner": {
    "timeout": 10000,
    "concurrency": 2,
    "maxDepth": 2
  },
  "modules": {
    "xss": { "enabled": true },
    "sqli": { "enabled": true },
    "lfi": { "enabled": false }
  },
  "reporting": {
    "format": "console",
    "minSeverity": "Low"
  },
  "debug": {
    "enabled": true,
    "level": "debug"
  }
}
```

### Конфигурация для продакшена

```json
{
  "scanner": {
    "timeout": 60000,
    "concurrency": 10,
    "maxDepth": 5,
    "followRedirects": true
  },
  "modules": {
    "xss": { "enabled": true },
    "sqli": { "enabled": true },
    "lfi": { "enabled": true },
    "directory": { "enabled": true }
  },
  "reporting": {
    "format": "sarif",
    "minSeverity": "Medium",
    "includeScreenshots": true
  },
  "security": {
    "rateLimiting": { "enabled": true },
    "encryption": { "enabled": true }
  },
  "alerts": {
    "enabled": true,
    "channels": ["email", "slack"]
  }
}
```

---

*Последнее обновление: 9 мая 2026*
