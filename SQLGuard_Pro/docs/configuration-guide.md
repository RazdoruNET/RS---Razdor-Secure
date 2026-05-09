# ⚙️ Конфигурация

## 📋 Обзор

SQLGuard Pro предоставляет мощную систему конфигурации для адаптации под различные проекты и требования безопасности.

---

## 🔧 Файлы конфигурации

### Основной конфигурационный файл

**Расположение:** `sqlguard.config.json` (в корне проекта)

```json
{
  "database": {
    "type": "mysql",
    "version": "8.0",
    "charset": "utf8mb4"
  },
  "security": {
    "level": "medium",
    "strictMode": false,
    "enableAI": true
  },
  "analysis": {
    "depth": 3,
    "patterns": ["*.sql", "*.js", "*.py", "*.java"],
    "exclude": ["node_modules", "dist", "*.min.js"]
  },
  "reporting": {
    "format": "html",
    "output": "./reports",
    "template": "default"
  },
  "performance": {
    "concurrency": 4,
    "timeout": 30000,
    "cache": true
  }
}
```

---

## 🎯 Настройки базы данных

### MySQL

```json
{
  "database": {
    "type": "mysql",
    "version": "8.0",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "features": {
      "windowFunctions": true,
      "cte": true,
      "jsonFunctions": true
    },
    "rules": {
      "sqlInjection": {
        "enabled": true,
        "patterns": [
          "union_select",
          "boolean_blind",
          "time_based",
          "error_based"
        ]
      }
    }
  }
}
```

### PostgreSQL

```json
{
  "database": {
    "type": "postgresql",
    "version": "14",
    "charset": "utf8",
    "features": {
      "windowFunctions": true,
      "cte": true,
      "jsonb": true,
      "arrays": true
    },
    "rules": {
      "sqlInjection": {
        "enabled": true,
        "patterns": [
          "union_select",
          "boolean_blind",
          "time_based",
          "error_based"
        ]
      }
    }
  }
}
```

### Microsoft SQL Server

```json
{
  "database": {
    "type": "mssql",
    "version": "2019",
    "features": {
      "windowFunctions": true,
      "cte": true,
      "json": true,
      "pivot": true
    },
    "rules": {
      "sqlInjection": {
        "enabled": true,
        "patterns": [
          "union_select",
          "boolean_blind",
          "time_based",
          "error_based",
          "stacked_queries"
        ]
      }
    }
  }
}
```

---

## 🔒 Настройки безопасности

### Уровни безопасности

```json
{
  "security": {
    "level": "high", // low, medium, high, strict
    "strictMode": false,
    "enableAI": true,
    "aiConfig": {
      "provider": "openai",
      "model": "gpt-4",
      "maxTokens": 2000,
      "temperature": 0.1
    }
  }
}
```

### Детальная настройка правил

```json
{
  "rules": {
    "sqlInjection": {
      "enabled": true,
      "severity": "high",
      "patterns": {
        "stringConcatenation": {
          "enabled": true,
          "severity": "critical",
          "patterns": [
            "\\+\\s*['\"]",
            "concat\\s*\\(",
            "\\|\\|\\s*['\"]"
          ]
        },
        "dynamicQuery": {
          "enabled": true,
          "severity": "high",
          "patterns": [
            "eval\\s*\\(",
            "execute\\s*\\(",
            "sp_executesql"
          ]
        },
        "hardcodedCredentials": {
          "enabled": true,
          "severity": "critical",
          "patterns": [
            "password\\s*=\\s*['\"][^'\"]{8,}['\"]",
            "secret\\s*=\\s*['\"][^'\"]{16,}['\"]"
          ]
        }
      }
    },
    "performance": {
      "enabled": true,
      "rules": {
        "selectStar": {
          "enabled": true,
          "severity": "medium",
          "excludeViews": true
        },
        "missingIndex": {
          "enabled": true,
          "severity": "medium",
          "minTableRows": 1000
        },
        "nPlusOne": {
          "enabled": true,
          "severity": "high",
          "threshold": 5
        }
      }
    }
  }
}
```

---

## 📊 Настройки анализа

### Паттерны файлов и директорий

```json
{
  "analysis": {
    "patterns": [
      "*.sql",
      "*.js",
      "*.ts",
      "*.py",
      "*.java",
      "*.php",
      "*.rb",
      "*.go",
      "*.cs"
    ],
    "exclude": {
      "directories": [
        "node_modules",
        "dist",
        "build",
        "target",
        ".git",
        "vendor",
        "__pycache__"
      ],
      "files": [
        "*.min.js",
        "*.min.css",
        "*.bundle.js",
        "*.test.js",
        "*.spec.js"
      ]
    },
    "depth": 5,
    "maxFileSize": "10MB"
  }
}
```

### Кастомные правила

```json
{
  "customRules": [
    {
      "name": "Custom SQL Pattern",
      "description": "Detect specific SQL pattern in our codebase",
      "severity": "high",
      "pattern": "executeQuery\\s*\\(\\s*['\"]",
      "languages": ["javascript", "typescript"],
      "recommendation": "Use parameterized queries instead of string concatenation",
      "examples": {
        "bad": "executeQuery('SELECT * FROM users WHERE id = ' + id)",
        "good": "executeQuery('SELECT * FROM users WHERE id = ?', [id])"
      }
    }
  ]
}
```

---

## 📈 Настройки производительности

### Параллельная обработка

```json
{
  "performance": {
    "concurrency": {
      "enabled": true,
      "maxWorkers": 4,
      "queueSize": 100,
      "timeout": 30000
    },
    "cache": {
      "enabled": true,
      "type": "memory", // memory, redis, file
      "ttl": 3600,
      "maxSize": "100MB"
    },
    "memory": {
      "limit": "512MB",
      "gcInterval": 60000
    }
  }
}
```

### Оптимизация для больших проектов

```json
{
  "performance": {
    "batchSize": 100,
    "incremental": true,
    "checkpoint": true,
    "resumeOnError": true,
    "progressReporting": true
  }
}
```

---

## 📋 Настройки отчетности

### Форматы отчетов

```json
{
  "reporting": {
    "format": "html", // html, json, pdf, sarif, xml, csv
    "output": "./reports",
    "filename": "security-report-{timestamp}",
    "template": "default", // default, executive, technical, custom
    "compression": true,
    "encryption": {
      "enabled": false,
      "algorithm": "aes-256-gcm",
      "password": "report-password"
    }
  }
}
```

### Кастомные шаблоны

```json
{
  "reporting": {
    "customTemplates": {
      "company": {
        "header": "<h1>{{companyName}} Security Report</h1>",
        "footer": "<p>Generated by SQLGuard Pro</p>",
        "styles": "company-styles.css",
        "logo": "company-logo.png"
      }
    },
    "sections": {
      "summary": true,
      "vulnerabilities": true,
      "recommendations": true,
      "statistics": true,
      "codeExamples": true,
      "fixes": true
    }
  }
}
```

### Фильтрация результатов

```json
{
  "reporting": {
    "filters": {
      "severity": {
        "min": "medium", // low, medium, high, critical
        "include": ["medium", "high", "critical"]
      },
      "confidence": {
        "min": 0.7
      },
      "categories": {
        "include": ["sql-injection", "performance", "security"],
        "exclude": ["style"]
      },
      "files": {
        "include": ["src/**"],
        "exclude": ["test/**", "docs/**"]
      }
    }
  }
}
```

---

## 🔌 Интеграция с IDE

### VS Code

```json
// .vscode/settings.json
{
  "sqlguard-pro.enabled": true,
  "sqlguard-pro.autoScan": true,
  "sqlguard-pro.scanOnSave": false,
  "sqlguard-pro.showNotifications": true,
  "sqlguard-pro.severityThreshold": "medium",
  "sqlguard-pro.configFile": "./sqlguard.config.json",
  "sqlguard-pro.excludePatterns": [
    "node_modules/**",
    "dist/**",
    "*.min.js"
  ],
  "sqlguard-pro.quickFix": {
    "enabled": true,
    "autoApply": false
  }
}
```

### JetBrains IDE

```xml
<!-- .idea/sqlguard-pro.xml -->
<application>
  <component name="SqlGuardProSettings">
    <option name="enabled" value="true" />
    <option name="configFile" value="$PROJECT_DIR$/sqlguard.config.json" />
    <option name="autoScan" value="true" />
    <option name="severityThreshold" value="medium" />
  </component>
</application>
```

---

## 🔗 Интеграция с CI/CD

### GitHub Actions

```yaml
# .github/workflows/sqlguard.yml
name: SQLGuard Pro Security Scan
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        database: [mysql, postgresql, mssql]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install SQLGuard Pro
      run: npm install -g sqlguard-pro
    
    - name: Create config for ${{ matrix.database }}
      run: |
        cat > sqlguard-${{ matrix.database }}.json << EOF
        {
          "database": {
            "type": "${{ matrix.database }}"
          },
          "security": {
            "level": "high",
            "strictMode": true
          },
          "reporting": {
            "format": "sarif",
            "output": "./reports"
          }
        }
        EOF
    
    - name: Run security scan
      run: |
        sqlguard analyze \
          --config sqlguard-${{ matrix.database }}.json \
          --directory . \
          --output security-${{ matrix.database }}.sarif
      env:
        SQLGUARD_API_KEY: ${{ secrets.SQLGUARD_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    
    - name: Upload SARIF results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: security-${{ matrix.database }}.sarif
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
  agent any
  
  environment {
    SQLGUARD_API_KEY = credentials('sqlguard-api-key')
    OPENAI_API_KEY = credentials('openai-api-key')
  }
  
  stages {
    stage('Security Scan') {
      parallel {
        stage('MySQL') {
          steps {
            script {
              scanDatabase('mysql')
            }
          }
        }
        stage('PostgreSQL') {
          steps {
            script {
              scanDatabase('postgresql')
            }
          }
        }
        stage('MSSQL') {
          steps {
            script {
              scanDatabase('mssql')
            }
          }
        }
      }
    }
  }
  
  post {
    always {
      script {
        publishHTML([
          allowMissing: false,
          alwaysLinkToLastBuild: true,
          keepAll: true,
          reportDir: 'reports',
          reportFiles: '*.html',
          reportName: 'SQLGuard Pro Security Reports'
        ])
      }
    }
  }
}

def scanDatabase(dbType) {
  sh """
    npm install -g sqlguard-pro
    
    cat > sqlguard-${dbType}.json << EOF
    {
      "database": {
        "type": "${dbType}"
      },
      "security": {
        "level": "high",
        "enableAI": true
      },
      "reporting": {
        "format": "html",
        "output": "./reports/${dbType}"
      }
    }
    EOF
    
    sqlguard analyze \\
      --config sqlguard-${dbType}.json \\
      --directory . \\
      --output ./reports/${dbType}/security-report.html
  """
}
```

---

## 🔧 Управление конфигурацией

### Environment Variables

```bash
# .env
SQLGUARD_CONFIG_PATH=./config/sqlguard.json
SQLGUARD_API_KEY=your-api-key
SQLGUARD_LOG_LEVEL=info
SQLGUARD_REPORTS_DIR=./reports
SQLGUARD_CACHE_ENABLED=true
SQLGUARD_CONCURRENCY=4

# Database specific
SQLGUARD_DB_TYPE=mysql
SQLGUARD_DB_VERSION=8.0

# AI Integration
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4

# Performance
SQLGUARD_MEMORY_LIMIT=512MB
SQLGUARD_TIMEOUT=30000
SQLGUARD_CACHE_TTL=3600
```

### Программная конфигурация

```javascript
// config/sqlguard.js
const path = require('path');
const { loadConfig } = require('sqlguard-pro/config');

const config = loadConfig({
  // Базовые настройки
  database: {
    type: process.env.SQLGUARD_DB_TYPE || 'mysql',
    version: process.env.SQLGUARD_DB_VERSION || '8.0'
  },
  
  // Безопасность
  security: {
    level: process.env.SQLGUARD_SECURITY_LEVEL || 'medium',
    strictMode: process.env.SQLGUARD_STRICT_MODE === 'true',
    enableAI: process.env.SQLGUARD_AI_ENABLED !== 'false'
  },
  
  // Производительность
  performance: {
    concurrency: parseInt(process.env.SQLGUARD_CONCURRENCY) || 4,
    timeout: parseInt(process.env.SQLGUARD_TIMEOUT) || 30000,
    cache: {
      enabled: process.env.SQLGUARD_CACHE_ENABLED !== 'false',
      ttl: parseInt(process.env.SQLGUARD_CACHE_TTL) || 3600
    }
  },
  
  // Отчетность
  reporting: {
    format: process.env.SQLGUARD_REPORT_FORMAT || 'html',
    output: process.env.SQLGUARD_REPORTS_DIR || './reports'
  }
});

// Валидация конфигурации
const { validateConfig } = require('sqlguard-pro/validation');
const validation = validateConfig(config);

if (!validation.valid) {
  console.error('Configuration errors:', validation.errors);
  process.exit(1);
}

module.exports = config;
```

### Динамическая конфигурация

```javascript
const { ConfigManager } = require('sqlguard-pro/config');

class DynamicConfig extends ConfigManager {
  constructor() {
    super();
    this.watchers = new Map();
  }
  
  // Загрузка конфигурации из разных источников
  async load() {
    // Из файла
    await this.loadFromFile('./sqlguard.config.json');
    
    // Из environment variables
    this.loadFromEnvironment();
    
    // Из remote конфига
    await this.loadFromRemote('https://config.company.com/sqlguard.json');
    
    // Из database
    await this.loadFromDatabase('configurations');
    
    return this.config;
  }
  
  // Watch для изменений конфигурации
  watch(path, callback) {
    if (this.watchers.has(path)) {
      return this.watchers.get(path);
    }
    
    const watcher = require('chokidar').watch(path);
    watcher.on('change', async () => {
      await this.load();
      callback(this.config);
    });
    
    this.watchers.set(path, watcher);
    return watcher;
  }
  
  // Remote конфигурация
  async loadFromRemote(url) {
    try {
      const response = await fetch(url);
      const remoteConfig = await response.json();
      this.merge(remoteConfig);
    } catch (error) {
      console.warn('Failed to load remote config:', error.message);
    }
  }
  
  // Конфигурация из базы данных
  async loadFromDatabase(table) {
    try {
      const dbConfig = await this.db.query(`SELECT * FROM ${table} WHERE active = 1`);
      this.merge(dbConfig);
    } catch (error) {
      console.warn('Failed to load database config:', error.message);
    }
  }
}

// Использование
const configManager = new DynamicConfig();

// Загрузка конфигурации
await configManager.load();

// Watch для изменений
configManager.watch('./sqlguard.config.json', (newConfig) => {
  console.log('Configuration updated:', newConfig);
});

// Получение конфигурации
const config = configManager.get();
```

---

## 📊 Мониторинг и метрики

### Метрики конфигурации

```javascript
const { MetricsCollector } = require('sqlguard-pro/metrics');

const metrics = new MetricsCollector({
  enabled: true,
  interval: 60000, // 1 минута
  outputs: ['console', 'prometheus', 'file']
});

// Сбор метрик конфигурации
metrics.collect('config', () => ({
  databaseType: config.database.type,
  securityLevel: config.security.level,
  concurrency: config.performance.concurrency,
  aiEnabled: config.security.enableAI
}));

// Сбор метрик производительности
metrics.collect('performance', () => ({
  memoryUsage: process.memoryUsage(),
  cpuUsage: process.cpuUsage(),
  scanDuration: lastScanDuration,
  filesProcessed: filesProcessedCount
}));
```

### Алерты на основе конфигурации

```javascript
const { AlertManager } = require('sqlguard-pro/alerts');

const alertManager = new AlertManager({
  channels: ['email', 'slack', 'teams'],
  rules: [
    {
      name: 'High Security Level',
      condition: (config) => config.security.level === 'high',
      message: 'High security level enabled - increased false positives possible',
      severity: 'info'
    },
    {
      name: 'AI Disabled',
      condition: (config) => !config.security.enableAI,
      message: 'AI analysis disabled - reduced detection accuracy',
      severity: 'warning'
    },
    {
      name: 'Low Concurrency',
      condition: (config) => config.performance.concurrency < 2,
      message: 'Low concurrency setting - slower scans',
      severity: 'warning'
    }
  ]
});

// Проверка конфигурации
alertManager.checkConfig(config);
```

---

## 🛠️ Отладка конфигурации

### Валидация конфигурации

```bash
# Проверка конфигурационного файла
sqlguard config --validate --file sqlguard.config.json

# Проверка environment variables
sqlguard config --validate --env

# Детальная валидация
sqlguard config --validate --verbose
```

### Тестирование конфигурации

```bash
# Тест с конкретной конфигурацией
sqlguard analyze \
  --config test-config.json \
  --directory ./test-files \
  --dry-run

# Сравнение конфигураций
sqlguard config diff config1.json config2.json

# Показ текущей конфигурации
sqlguard config show
```

### Диагностика проблем

```javascript
const { ConfigDiagnostics } = require('sqlguard-pro/diagnostics');

const diagnostics = new ConfigDiagnostics();

// Проверка всех аспектов конфигурации
const report = await diagnostics.runFullCheck();

if (report.issues.length > 0) {
  console.log('Configuration issues found:');
  report.issues.forEach(issue => {
    console.log(`- ${issue.severity}: ${issue.message}`);
    console.log(`  Recommendation: ${issue.recommendation}`);
  });
} else {
  console.log('✅ Configuration is valid');
}
```

---

## 📚 Примеры конфигураций

### Конфигурация для разработки

```json
{
  "database": {
    "type": "mysql"
  },
  "security": {
    "level": "low",
    "strictMode": false,
    "enableAI": false
  },
  "analysis": {
    "depth": 2,
    "patterns": ["*.sql", "*.js"],
    "exclude": ["node_modules", "test"]
  },
  "performance": {
    "concurrency": 2,
    "timeout": 15000,
    "cache": false
  },
  "reporting": {
    "format": "console",
    "verbose": true
  }
}
```

### Конфигурация для продакшена

```json
{
  "database": {
    "type": "postgresql",
    "version": "14"
  },
  "security": {
    "level": "strict",
    "strictMode": true,
    "enableAI": true,
    "aiConfig": {
      "provider": "openai",
      "model": "gpt-4",
      "maxTokens": 4000
    }
  },
  "analysis": {
    "depth": 10,
    "patterns": ["*.sql", "*.js", "*.ts", "*.py", "*.java"],
    "exclude": ["node_modules", "dist", "build", "*.test.*"]
  },
  "performance": {
    "concurrency": 8,
    "timeout": 60000,
    "cache": {
      "enabled": true,
      "type": "redis",
      "ttl": 7200
    }
  },
  "reporting": {
    "format": "sarif",
    "output": "./reports",
    "encryption": {
      "enabled": true,
      "algorithm": "aes-256-gcm"
    },
    "filters": {
      "severity": {
        "min": "medium"
      }
    }
  }
}
```

### Конфигурация для CI/CD

```json
{
  "database": {
    "type": "mysql"
  },
  "security": {
    "level": "high",
    "strictMode": true,
    "enableAI": false
  },
  "analysis": {
    "depth": 5,
    "patterns": ["*.sql", "*.js", "*.ts"],
    "exclude": ["node_modules", "dist", "coverage"]
  },
  "performance": {
    "concurrency": 4,
    "timeout": 30000,
    "cache": false
  },
  "reporting": {
    "format": "sarif",
    "output": "./security-results",
    "filters": {
      "severity": {
        "min": "medium"
      }
    }
  }
}
```

---

## 🔄 Обновление конфигурации

### Автоматические обновления

```javascript
const { ConfigUpdater } = require('sqlguard-pro/config-updater');

const updater = new ConfigUpdater({
  configFile: './sqlguard.config.json',
  backupPath: './config-backups',
  updateUrl: 'https://releases.sqlguard-pro.com/config/latest'
});

// Проверка обновлений
await updater.checkForUpdates();

// Применение обновлений
await updater.applyUpdates();
```

### Миграция конфигурации

```bash
# Миграция со старой версии
sqlguard config migrate --from-version 1.0 --to-version 2.0

# Проверка совместимости
sqlguard config check-compatibility --version 2.0
```

---

*Последнее обновление: 9 мая 2026*
