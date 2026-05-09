# Руководство для среднего уровня - SQLGuard Pro

## Содержание

1. [Продвинутая конфигурация](#продвинутая-конфигурация)
2. [Кастомные правила](#кастомные-правила)
3. [Интеграция с CI/CD](#интеграция-с-cicd)
4. [Оптимизация производительности](#оптимизация-производительности)
5. [API программирования](#api-программирования)
6. [Мониторинг и логирование](#мониторинг-и-логирование)
7. [Решение сложных проблем](#решение-сложных-проблем)

## Продвинутая конфигурация

### Файл конфигурации .sqlguard.json

Создайте файл `.sqlguard.json` в корне проекта:

```json
{
  "version": "1.0.0",
  "scanner": {
    "databaseType": "mysql",
    "securityLevel": "strict",
    "enableGPTAnalysis": true,
    "enablePerformanceAnalysis": true,
    "maxConcurrentFiles": 8,
    "cacheEnabled": true,
    "cacheTTL": 3600
  },
  "rules": {
    "enabled": [
      "SQL_INJECTION",
      "HARDCODED_CREDENTIALS",
      "MISSING_INPUT_VALIDATION",
      "DYNAMIC_SQL",
      "PERFORMANCE_ISSUES"
    ],
    "disabled": [
      "SELECT_ALL_WARNING"
    ],
    "customRulesPath": "./custom-rules/",
    "severityOverrides": {
      "DYNAMIC_SQL": "medium",
      "PERFORMANCE_ISSUES": "low"
    }
  },
  "reporting": {
    "defaultFormat": "html",
    "includeStatistics": true,
    "includeRecommendations": true,
    "includeCodeSnippets": true,
    "groupBy": "severity",
    "sortOrder": "severity"
  },
  "security": {
    "offlineMode": true,
    "auditLogging": true,
    "dataRetention": 90,
    "encryptionEnabled": true
  },
  "integrations": {
    "ide": {
      "realTimeAnalysis": true,
      "autoSaveAnalysis": true,
      "highlightSeverity": "high",
      "tooltipEnabled": true
    },
    "git": {
      "preCommitHook": true,
      "analyzeOnlyChanged": true,
      "failOnCritical": true
    }
  }
}
```

### Уровни безопасности детально

#### Strict (строгий)
```json
{
  "securityLevel": "strict",
  "settings": {
    "confidenceThreshold": 0.7,
    "includePotentialIssues": true,
    "analyzeComplexQueries": true,
    "deepAnalysis": true
  }
}
```

#### Moderate (умеренный)
```json
{
  "securityLevel": "moderate",
  "settings": {
    "confidenceThreshold": 0.8,
    "includePotentialIssues": false,
    "analyzeComplexQueries": true,
    "deepAnalysis": false
  }
}
```

#### Lenient (мягкий)
```json
{
  "securityLevel": "lenient",
  "settings": {
    "confidenceThreshold": 0.9,
    "includePotentialIssues": false,
    "analyzeComplexQueries": false,
    "deepAnalysis": false
  }
}
```

### Профили конфигурации

#### Профиль для веб-приложения
```json
{
  "profile": "web-application",
  "scanner": {
    "databaseType": "postgresql",
    "securityLevel": "strict",
    "enableGPTAnalysis": true
  },
  "rules": {
    "enabled": [
      "SQL_INJECTION",
      "XSS_VULNERABILITIES",
      "CSRF_PROTECTION",
      "SESSION_SECURITY"
    ]
  },
  "reporting": {
    "includeOWASP": true,
    "includeCompliance": ["GDPR", "SOC2"]
  }
}
```

#### Профиль для API
```json
{
  "profile": "api",
  "scanner": {
    "databaseType": "mysql",
    "securityLevel": "strict",
    "enablePerformanceAnalysis": true
  },
  "rules": {
    "enabled": [
      "RATE_LIMITING",
      "AUTHORIZATION_BYPASS",
      "DATA_EXPOSURE",
      "INPUT_VALIDATION"
    ]
  },
  "reporting": {
    "includeAPISecurity": true,
    "includeEndpointAnalysis": true
  }
}
```

## Кастомные правила

### Создание собственных правил

#### Правило на основе регулярных выражений

```javascript
// custom-rules/hardcoded-secrets.js
module.exports = {
  id: 'CUSTOM_HARDCODED_SECRETS',
  name: 'Hardcoded Secrets Detection',
  description: 'Detects hardcoded secrets in SQL queries',
  severity: 'critical',
  category: 'security',
  
  // Регулярное выражение для поиска секретов
  pattern: /(?:password|secret|token|key|api_key)\s*=\s*['"]([^'"]{8,})['"]/gi,
  
  // Типы баз данных
  databaseTypes: ['mysql', 'postgresql', 'mssql', 'oracle', 'sqlite'],
  
  // Типы запросов
  queryTypes: ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
  
  // Функция валидации
  validate: function(query, match) {
    const secret = match[1];
    
    // Проверка на очевидные тестовые значения
    const testValues = ['test', 'demo', 'example', 'sample', 'dev', 'staging'];
    if (testValues.includes(secret.toLowerCase())) {
      return null; // Игнорировать тестовые значения
    }
    
    // Проверка сложности секрета
    if (secret.length < 16) {
      return {
        severity: 'high', // Понизить критичность для коротких секретов
        confidence: 0.7
      };
    }
    
    return {
      severity: 'critical',
      confidence: 0.95
    };
  },
  
  // Рекомендация по исправлению
  recommendation: 'Use environment variables or secure configuration management instead of hardcoded secrets.',
  
  // Ссылки на документацию
  references: [
    'https://owasp.org/www-project-cheat-sheets/cheatsheets/Secrets_Management_Cheat_Sheet.html',
    'https://cwe.mitre.org/data/definitions/798.html'
  ]
};
```

#### Правило на основе AST анализа

```javascript
// custom-rules/unused-indexes.js
module.exports = {
  id: 'UNUSED_INDEXES',
  name: 'Unused Indexes Detection',
  description: 'Detects potentially unused database indexes',
  severity: 'medium',
  category: 'performance',
  
  // Функция анализа AST
  analyze: function(ast, context) {
    const issues = [];
    const indexes = context.databaseSchema?.indexes || [];
    const usedTables = this.extractUsedTables(ast);
    
    indexes.forEach(index => {
      if (!usedTables.includes(index.table)) {
        issues.push({
          type: 'UNUSED_INDEX',
          severity: 'medium',
          line: index.line,
          column: index.column,
          message: `Index '${index.name}' on table '${index.table}' appears to be unused`,
          recommendation: `Consider dropping unused index '${index.name}' to improve write performance`,
          metadata: {
            indexName: index.name,
            tableName: index.table,
            indexSize: index.size
          }
        });
      }
    });
    
    return issues;
  },
  
  // Вспомогательные функции
  extractUsedTables: function(ast) {
    const tables = new Set();
    
    function traverse(node) {
      if (node.type === 'Table') {
        tables.add(node.name);
      }
      if (node.children) {
        node.children.forEach(traverse);
      }
    }
    
    traverse(ast);
    return Array.from(tables);
  },
  
  // Требования к контексту
  requiresContext: ['databaseSchema'],
  
  // События для триггера
  triggers: ['afterSchemaAnalysis']
};
```

#### Правило на основе машинного обучения

```javascript
// custom-rules/ml-anomaly-detection.js
const ml = require('ml-regression');

module.exports = {
  id: 'ML_ANOMALY_DETECTION',
  name: 'ML-based Anomaly Detection',
  description: 'Uses machine learning to detect anomalous query patterns',
  severity: 'medium',
  category: 'anomaly',
  
  // Инициализация модели
  initialize: function() {
    this.model = new ml.RandomForest({
      nEstimators: 100,
      maxDepth: 10
    });
    
    this.features = [
      'queryLength',
      'tableCount',
      'joinCount',
      'whereClauseComplexity',
      'subqueryDepth'
    ];
    
    this.isTrained = false;
  },
  
  // Обучение модели
  train: function(historicalQueries) {
    const trainingData = historicalQueries.map(query => ({
      label: this.isAnomalous(query) ? 1 : 0,
      features: this.extractFeatures(query)
    }));
    
    this.model.train(trainingData);
    this.isTrained = true;
  },
  
  // Анализ запроса
  analyze: function(query, context) {
    if (!this.isTrained) {
      return null;
    }
    
    const features = this.extractFeatures(query);
    const prediction = this.model.predict(features);
    const probability = this.model.predictProbability(features);
    
    if (prediction === 1 && probability > 0.8) {
      return {
        type: 'ANOMALOUS_QUERY',
        severity: 'medium',
        confidence: probability,
        message: 'Query pattern appears anomalous compared to historical data',
        recommendation: 'Review query for potential security or performance issues',
        metadata: {
          features,
          probability,
          anomalyScore: this.calculateAnomalyScore(features)
        }
      };
    }
    
    return null;
  },
  
  // Извлечение признаков
  extractFeatures: function(query) {
    return [
      query.sql.length,
      this.countTables(query.ast),
      this.countJoins(query.ast),
      this.calculateWhereComplexity(query.ast),
      this.calculateSubqueryDepth(query.ast)
    ];
  },
  
  // Дополнительные методы
  countTables: function(ast) { /* реализация */ },
  countJoins: function(ast) { /* реализация */ },
  calculateWhereComplexity: function(ast) { /* реализация */ },
  calculateSubqueryDepth: function(ast) { /* реализация */ },
  calculateAnomalyScore: function(features) { /* реализация */ }
};
```

### Управление кастомными правилами

#### Регистрация правил
```javascript
// rules-loader.js
const path = require('path');
const fs = require('fs');

class CustomRulesLoader {
  constructor(rulesPath) {
    this.rulesPath = rulesPath;
    this.rules = new Map();
  }
  
  loadRules() {
    const ruleFiles = fs.readdirSync(this.rulesPath)
      .filter(file => file.endsWith('.js'));
    
    ruleFiles.forEach(file => {
      const rulePath = path.join(this.rulesPath, file);
      const rule = require(rulePath);
      
      // Валидация правила
      if (this.validateRule(rule)) {
        this.rules.set(rule.id, rule);
        console.log(`Loaded custom rule: ${rule.id}`);
      } else {
        console.warn(`Invalid rule: ${file}`);
      }
    });
    
    return Array.from(this.rules.values());
  }
  
  validateRule(rule) {
    const required = ['id', 'name', 'description', 'severity', 'category'];
    return required.every(field => rule.hasOwnProperty(field));
  }
}

module.exports = CustomRulesLoader;
```

## Интеграция с CI/CD

### GitHub Actions продвинутый

```yaml
# .github/workflows/advanced-security.yml
name: Advanced Security Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1' # Еженедельный анализ

env:
  SQLGUARD_CACHE_DIR: ~/.sqlguard-cache
  SQLGUARD_CONFIG_PATH: ./.sqlguard.json

jobs:
  security-scan:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        database: [mysql, postgresql, mssql]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Полная история для анализа изменений
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install SQLGuard Pro
        run: |
          npm install -g sqlguard-pro
          sqlguard --version
      
      - name: Cache SQLGuard rules
        uses: actions/cache@v3
        with:
          path: ${{ env.SQLGUARD_CACHE_DIR }}
          key: sqlguard-${{ matrix.database }}-${{ hashFiles('**/*.sql') }}
          restore-keys: |
            sqlguard-${{ matrix.database }}-
            sqlguard-
      
      - name: Configure SQLGuard
        run: |
          cat > .sqlguard.json << EOF
          {
            "scanner": {
              "databaseType": "${{ matrix.database }}",
              "securityLevel": "strict",
              "enableGPTAnalysis": true
            },
            "reporting": {
              "defaultFormat": "sarif",
              "includeStatistics": true
            },
            "security": {
              "offlineMode": true,
              "auditLogging": true
            }
          }
          EOF
      
      - name: Analyze changed files
        id: analyze
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            # Анализ только измененных файлов для PR
            git diff --name-only origin/${{ github.base_ref }}..HEAD | grep '\.sql$' > changed_files.txt
            sqlguard analyze --files-from-changed-files changed_files.txt --output results.sarif
          else
            # Полный анализ для push
            sqlguard analyze --directory . --output results.sarif
          fi
          
          # Сохранение метрик
          echo "::set-output name=vulnerability_count::$(jq '.run.invocations[0].toolExecutionNotifications | length' results.sarif)"
          echo "::set-output name=critical_count::$(jq '.run.invocations[0].toolExecutionNotifications[] | select(.level=="error") | length' results.sarif)"
      
      - name: Generate summary report
        run: |
          sqlguard report --input results.sarif --format html --output security-summary.html
          sqlguard report --input results.sarif --format markdown --output security-summary.md
      
      - name: Upload SARIF results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
      
      - name: Upload HTML report
        uses: actions/upload-artifact@v3
        with:
          name: security-report-${{ matrix.database }}
          path: |
            results.sarif
            security-summary.html
            security-summary.md
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('security-summary.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🔍 Security Analysis Results\n\n${summary}`
            });
      
      - name: Check security gates
        run: |
          CRITICAL_COUNT=${{ steps.analyze.outputs.critical_count }}
          if [ $CRITICAL_COUNT -gt 0 ]; then
            echo "::error::Critical vulnerabilities found: $CRITICAL_COUNT"
            exit 1
          fi
          
          VULNERABILITY_COUNT=${{ steps.analyze.outputs.vulnerability_count }}
          if [ $VULNERABILITY_COUNT -gt 10 ]; then
            echo "::warning::High vulnerability count: $VULNERABILITY_COUNT"
          fi
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - security
  - report

variables:
  SQLGUARD_VERSION: "1.0.0"
  SQLGUARD_CACHE: "$CI_PROJECT_DIR/.sqlguard-cache"

security_scan:
  stage: security
  image: node:18-alpine
  cache:
    key: sqlguard-$CI_COMMIT_REF_SLUG
    paths:
      - $SQLGUARD_CACHE
  before_script:
    - npm install -g sqlguard-pro
    - sqlguard --version
  script:
    - |
      # Конфигурация для GitLab
      cat > .sqlguard.json << EOF
      {
        "scanner": {
          "databaseType": "postgresql",
          "securityLevel": "strict"
        },
        "reporting": {
          "defaultFormat": "json"
        },
        "security": {
          "offlineMode": true
        }
      }
      EOF
      
      # Анализ проекта
      sqlguard analyze --directory . --output security-results.json
      
      # Генерация отчетов
      sqlguard report --input security-results.json --format html --output security-report.html
      sqlguard report --input security-results.json --format junit --output security-junit.xml
  artifacts:
    reports:
      junit: security-junit.xml
    paths:
      - security-results.json
      - security-report.html
    expire_in: 1 week
  only:
    - merge_requests
    - main
    - develop

security_report:
  stage: report
  image: alpine:latest
  dependencies:
    - security_scan
  script:
    - |
      # Отправка отчета в Slack (опционально)
      if [ -n "$SLACK_WEBHOOK" ]; then
        VULN_COUNT=$(jq '.vulnerabilities | length' security-results.json)
        CRITICAL_COUNT=$(jq '.vulnerabilities[] | select(.severity=="critical") | length' security-results.json)
        
        curl -X POST -H 'Content-type: application/json' \
          --data "{\"text\":\"🔍 Security Scan Results\\nVulnerabilities: $VULN_COUNT\\nCritical: $CRITICAL_COUNT\\nBranch: $CI_COMMIT_REF_NAME\"}" \
          $SLACK_WEBHOOK
      fi
  only:
    - main
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        SQLGUARD_HOME = "${WORKSPACE}/.sqlguard"
        SQLGUARD_CONFIG = "${WORKSPACE}/.sqlguard.json"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'npm install -g sqlguard-pro'
                sh 'sqlguard --version'
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    // Создание конфигурации
                    def config = [
                        scanner: [
                            databaseType: 'mysql',
                            securityLevel: 'strict',
                            enableGPTAnalysis: true
                        ],
                        reporting: [
                            defaultFormat: 'sarif',
                            includeStatistics: true
                        ]
                    ]
                    
                    writeFile file: SQLGUARD_CONFIG, text: groovy.json.JsonOutput.toJson(config)
                    
                    // Запуск анализа
                    sh "sqlguard analyze --directory . --output security-results.sarif"
                    
                    // Парсинг результатов
                    def sarif = readJSON file: 'security-results.sarif'
                    def vulnerabilityCount = sarif.runs[0].results.size()
                    def criticalCount = sarif.runs[0].results.count { it.level == 'error' }
                    
                    // Сохранение метрик
                    env.VULNERABILITY_COUNT = vulnerabilityCount.toString()
                    env.CRITICAL_COUNT = criticalCount.toString()
                    
                    echo "Found ${vulnerabilityCount} vulnerabilities (${criticalCount} critical)"
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    def criticalCount = env.CRITICAL_COUNT as Integer
                    
                    if (criticalCount > 0) {
                        error("Build failed: ${criticalCount} critical vulnerabilities found")
                    }
                    
                    def vulnerabilityCount = env.VULNERABILITY_COUNT as Integer
                    
                    if (vulnerabilityCount > 20) {
                        unstable("Build unstable: ${vulnerabilityCount} vulnerabilities found")
                    }
                }
            }
        }
        
        stage('Report') {
            steps {
                sh 'sqlguard report --input security-results.sarif --format html --output security-report.html'
                
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'security-report.html',
                    reportName: 'Security Report'
                ])
                
                archiveArtifacts artifacts: 'security-results.sarif,security-report.html', fingerprint: true
            }
        }
    }
    
    post {
        always {
            // Очистка
            sh 'rm -rf ${SQLGUARD_HOME}'
        }
        
        failure {
            emailext(
                subject: "Security Scan Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Security scan found critical vulnerabilities. Check the build report for details.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

## Оптимизация производительности

### Параллельная обработка

```javascript
// performance-optimizer.js
const os = require('os');
const cluster = require('cluster');

class PerformanceOptimizer {
  constructor(options = {}) {
    this.maxConcurrentFiles = options.maxConcurrentFiles || this.getOptimalConcurrency();
    this.chunkSize = options.chunkSize || 10;
    this.cache = new Map();
  }
  
  getOptimalConcurrency() {
    const cpuCount = os.cpus().length;
    const memoryGB = os.totalmem() / (1024 * 1024 * 1024);
    
    // Оптимальное количество на основе CPU и памяти
    return Math.min(cpuCount, Math.floor(memoryGB / 2));
  }
  
  async processFiles(files) {
    const chunks = this.chunkArray(files, this.chunkSize);
    const results = [];
    
    // Создание воркеров для параллельной обработки
    const workers = [];
    const workerCount = Math.min(chunks.length, this.maxConcurrentFiles);
    
    for (let i = 0; i < workerCount; i++) {
      const worker = cluster.fork();
      workers.push(worker);
    }
    
    // Распределение задач между воркерами
    const promises = workers.map((worker, index) => {
      return new Promise((resolve, reject) => {
        const chunkIndex = index % chunks.length;
        const chunk = chunks[chunkIndex];
        
        worker.send({ type: 'ANALYZE', files: chunk });
        
        worker.on('message', (result) => {
          resolve(result);
        });
        
        worker.on('error', reject);
        worker.on('exit', (code) => {
          if (code !== 0) {
            reject(new Error(`Worker exited with code ${code}`));
          }
        });
      });
    });
    
    try {
      const workerResults = await Promise.all(promises);
      results.push(...workerResults.flat());
    } finally {
      // Очистка воркеров
      workers.forEach(worker => worker.kill());
    }
    
    return results;
  }
  
  chunkArray(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}

module.exports = PerformanceOptimizer;
```

### Интеллектуальное кэширование

```javascript
// smart-cache.js
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

class SmartCache {
  constructor(options = {}) {
    this.cacheDir = options.cacheDir || path.join(os.tmpdir(), 'sqlguard-cache');
    this.maxSize = options.maxSize || 100 * 1024 * 1024; // 100MB
    this.ttl = options.ttl || 3600; // 1 час
    this.compressionEnabled = options.compression !== false;
    
    this.initializeCache();
  }
  
  async initializeCache() {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true });
      await this.cleanupExpired();
    } catch (error) {
      console.warn('Cache initialization failed:', error.message);
    }
  }
  
  generateKey(content, metadata) {
    const hash = crypto.createHash('sha256');
    hash.update(content);
    
    if (metadata) {
      hash.update(JSON.stringify(metadata));
    }
    
    return hash.digest('hex');
  }
  
  async get(key) {
    const cachePath = path.join(this.cacheDir, `${key}.cache`);
    
    try {
      const data = await fs.readFile(cachePath);
      const cacheEntry = JSON.parse(data.toString());
      
      // Проверка TTL
      if (Date.now() > cacheEntry.expiresAt) {
        await fs.unlink(cachePath);
        return null;
      }
      
      // Декомпрессия если нужно
      let content = cacheEntry.content;
      if (cacheEntry.compressed) {
        content = await this.decompress(content);
      }
      
      return {
        ...cacheEntry,
        content,
        hit: true
      };
    } catch (error) {
      return null;
    }
  }
  
  async set(key, content, metadata = {}) {
    const cacheEntry = {
      content,
      metadata,
      createdAt: Date.now(),
      expiresAt: Date.now() + (this.ttl * 1000),
      compressed: false,
      size: JSON.stringify(content).length
    };
    
    // Компрессия если включена
    if (this.compressionEnabled && cacheEntry.size > 1024) {
      cacheEntry.content = await this.compress(content);
      cacheEntry.compressed = true;
      cacheEntry.size = cacheEntry.content.length;
    }
    
    // Проверка размера кэша
    await this.ensureCapacity(cacheEntry.size);
    
    // Сохранение
    const cachePath = path.join(this.cacheDir, `${key}.cache`);
    await fs.writeFile(cachePath, JSON.stringify(cacheEntry));
  }
  
  async ensureCapacity(newEntrySize) {
    const currentSize = await this.getCurrentCacheSize();
    
    if (currentSize + newEntrySize > this.maxSize) {
      await this.evictLRU(currentSize + newEntrySize - this.maxSize);
    }
  }
  
  async evictLRU(bytesToEvict) {
    const files = await fs.readdir(this.cacheDir);
    const entries = [];
    
    for (const file of files) {
      if (file.endsWith('.cache')) {
        const filePath = path.join(this.cacheDir, file);
        const stats = await fs.stat(filePath);
        const data = await fs.readFile(filePath);
        const entry = JSON.parse(data.toString());
        
        entries.push({
          file,
          path: filePath,
          lastAccessed: entry.lastAccessed || entry.createdAt,
          size: stats.size
        });
      }
    }
    
    // Сортировка по времени последнего доступа
    entries.sort((a, b) => a.lastAccessed - b.lastAccessed);
    
    let evicted = 0;
    for (const entry of entries) {
      if (evicted >= bytesToEvict) break;
      
      await fs.unlink(entry.path);
      evicted += entry.size;
    }
  }
  
  async cleanupExpired() {
    const files = await fs.readdir(this.cacheDir);
    const now = Date.now();
    
    for (const file of files) {
      if (file.endsWith('.cache')) {
        const filePath = path.join(this.cacheDir, file);
        const data = await fs.readFile(filePath);
        const entry = JSON.parse(data.toString());
        
        if (now > entry.expiresAt) {
          await fs.unlink(filePath);
        }
      }
    }
  }
  
  async compress(data) {
    const zlib = require('zlib');
    return zlib.deflateSync(JSON.stringify(data));
  }
  
  async decompress(data) {
    const zlib = require('zlib');
    return JSON.parse(zlib.inflateSync(data).toString());
  }
}

module.exports = SmartCache;
```

## API программирования

### Расширение функциональности

```javascript
// plugin-system.js
const EventEmitter = require('events');

class PluginSystem extends EventEmitter {
  constructor() {
    super();
    this.plugins = new Map();
    this.hooks = new Map();
  }
  
  // Регистрация плагина
  registerPlugin(plugin) {
    if (!this.validatePlugin(plugin)) {
      throw new Error(`Invalid plugin: ${plugin.name}`);
    }
    
    this.plugins.set(plugin.name, plugin);
    
    // Регистрация хуков плагина
    if (plugin.hooks) {
      Object.entries(plugin.hooks).forEach(([hookName, handler]) => {
        this.registerHook(hookName, handler);
      });
    }
    
    // Инициализация плагина
    if (plugin.initialize) {
      plugin.initialize(this.createPluginContext(plugin));
    }
    
    this.emit('pluginRegistered', plugin);
  }
  
  // Регистрация хука
  registerHook(hookName, handler) {
    if (!this.hooks.has(hookName)) {
      this.hooks.set(hookName, []);
    }
    
    this.hooks.get(hookName).push(handler);
  }
  
  // Выполнение хука
  async executeHook(hookName, data) {
    const handlers = this.hooks.get(hookName) || [];
    let result = data;
    
    for (const handler of handlers) {
      try {
        result = await handler(result);
      } catch (error) {
        console.error(`Hook ${hookName} failed:`, error);
      }
    }
    
    return result;
  }
  
  // Создание контекста для плагина
  createPluginContext(plugin) {
    return {
      // API для работы с SQLGuard
      scanner: this.getScannerAPI(),
      reporter: this.getReporterAPI(),
      config: this.getConfigAPI(),
      
      // Утилиты
      utils: {
        hash: this.hash,
        logger: this.createLogger(plugin.name),
        storage: this.getStorageAPI(plugin.name)
      },
      
      // События
      events: {
        on: this.on.bind(this),
        emit: this.emit.bind(this)
      }
    };
  }
  
  // Валидация плагина
  validatePlugin(plugin) {
    const required = ['name', 'version', 'description'];
    return required.every(field => plugin.hasOwnProperty(field));
  }
  
  // API методы
  getScannerAPI() {
    return {
      analyzeFile: (file, content) => this.emit('analyzeFile', { file, content }),
      analyzeQuery: (query, type) => this.emit('analyzeQuery', { query, type })
    };
  }
  
  getReporterAPI() {
    return {
      addVulnerability: (vuln) => this.emit('vulnerabilityFound', vuln),
      addMetric: (metric) => this.emit('metricAdded', metric),
      generateReport: (format) => this.emit('reportGenerated', { format })
    };
  }
  
  getConfigAPI() {
    return {
      get: (key) => this.emit('configGet', key),
      set: (key, value) => this.emit('configSet', { key, value }),
      watch: (key, callback) => this.on('configChanged', ({ key: changedKey, value }) => {
        if (changedKey === key) callback(value);
      })
    };
  }
  
  createLogger(pluginName) {
    return {
      debug: (message) => console.debug(`[${pluginName}] ${message}`),
      info: (message) => console.info(`[${pluginName}] ${message}`),
      warn: (message) => console.warn(`[${pluginName}] ${message}`),
      error: (message) => console.error(`[${pluginName}] ${message}`)
    };
  }
}

module.exports = PluginSystem;
```

### Пример плагина

```javascript
// plugins/slack-notifier.js
const fetch = require('node-fetch');

module.exports = {
  name: 'slack-notifier',
  version: '1.0.0',
  description: 'Sends security notifications to Slack',
  
  // Конфигурация плагина
  config: {
    webhookUrl: {
      type: 'string',
      required: true,
      description: 'Slack webhook URL'
    },
    channel: {
      type: 'string',
      default: '#security',
      description: 'Slack channel for notifications'
    },
    notifyOn: {
      type: 'array',
      default: ['critical', 'high'],
      description: 'Severity levels to notify about'
    }
  },
  
  // Хуки
  hooks: {
    'analysisComplete': async function(result) {
      const criticalVulns = result.vulnerabilities.filter(v => 
        this.config.notifyOn.includes(v.severity.toLowerCase())
      );
      
      if (criticalVulns.length > 0) {
        await this.sendSlackNotification(result, criticalVulns);
      }
    },
    
    'vulnerabilityFound': async function(vulnerability) {
      if (this.config.notifyOn.includes(vulnerability.severity.toLowerCase())) {
        await this.sendImmediateNotification(vulnerability);
      }
    }
  },
  
  // Инициализация
  initialize(context) {
    this.context = context;
    this.logger = context.utils.logger;
    this.config = context.config.get('slack-notifier') || {};
    
    this.logger.info('Slack notifier plugin initialized');
  },
  
  // Методы плагина
  async sendSlackNotification(result, vulnerabilities) {
    const message = {
      channel: this.config.channel,
      username: 'SQLGuard Bot',
      icon_emoji: ':shield:',
      text: `🚨 Security Alert: ${vulnerabilities.length} vulnerabilities found`,
      attachments: [{
        color: 'danger',
        fields: [
          {
            title: 'File',
            value: result.filePath,
            short: true
          },
          {
            title: 'Critical',
            value: vulnerabilities.filter(v => v.severity === 'critical').length,
            short: true
          },
          {
            title: 'High',
            value: vulnerabilities.filter(v => v.severity === 'high').length,
            short: true
          }
        ]
      }]
    };
    
    try {
      const response = await fetch(this.config.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message)
      });
      
      if (!response.ok) {
        throw new Error(`Slack API error: ${response.status}`);
      }
      
      this.logger.info('Slack notification sent successfully');
    } catch (error) {
      this.logger.error('Failed to send Slack notification:', error.message);
    }
  },
  
  async sendImmediateNotification(vulnerability) {
    const message = {
      channel: this.config.channel,
      username: 'SQLGuard Bot',
      icon_emoji: ':warning:',
      text: `⚠️ ${vulnerability.severity.toUpperCase()} vulnerability detected`,
      attachments: [{
        color: this.getColorBySeverity(vulnerability.severity),
        fields: [
          {
            title: 'Type',
            value: vulnerability.type,
            short: true
          },
          {
            title: 'Line',
            value: vulnerability.line,
            short: true
          },
          {
            title: 'Description',
            value: vulnerability.description.substring(0, 200),
            short: false
          }
        ]
      }]
    };
    
    // Отправка немедленного уведомления
    // ... реализация аналогична sendSlackNotification
  },
  
  getColorBySeverity(severity) {
    const colors = {
      critical: 'danger',
      high: 'warning',
      medium: 'good',
      low: '#cccccc'
    };
    return colors[severity] || 'good';
  }
};
```

## Мониторинг и логирование

### Продвинутый аудит

```javascript
// advanced-audit-logger.js
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class AdvancedAuditLogger {
  constructor(options = {}) {
    this.logDir = options.logDir || './logs';
    this.encryptionKey = options.encryptionKey || this.generateKey();
    this.rotationInterval = options.rotationInterval || 'daily';
    this.maxLogSize = options.maxLogSize || 100 * 1024 * 1024; // 100MB
    this.compressionEnabled = options.compression !== false;
    
    this.initializeLogger();
  }
  
  async initializeLogger() {
    await fs.mkdir(this.logDir, { recursive: true });
    await this.setupLogRotation();
  }
  
  async logSecurityEvent(event, metadata = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'SECURITY_EVENT',
      event,
      metadata: this.sanitizeMetadata(metadata),
      sessionId: this.getSessionId(),
      userId: this.getCurrentUserId(),
      ipAddress: this.getClientIP()
    };
    
    await this.writeLog(logEntry);
    
    // Критические события - немедленная отправка
    if (this.isCriticalEvent(event)) {
      await this.sendImmediateAlert(logEntry);
    }
  }
  
  async logAnalysisResult(result) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'ANALYSIS_RESULT',
      filePath: result.filePath,
      vulnerabilityCount: result.vulnerabilities.length,
      criticalCount: result.vulnerabilities.filter(v => v.severity === 'critical').length,
      analysisTime: result.duration,
      rulesVersion: result.metadata.rulesVersion,
      scannerVersion: result.metadata.scannerVersion
    };
    
    await this.writeLog(logEntry);
  }
  
  async writeLog(logEntry) {
    const logLine = JSON.stringify(logEntry) + '\n';
    const encrypted = this.encrypt(logLine);
    
    const logFile = this.getCurrentLogFile();
    await fs.appendFile(logFile, encrypted);
    
    // Проверка размера и ротация
    await this.checkAndRotateLog(logFile);
  }
  
  encrypt(data) {
    const cipher = crypto.createCipher('aes-256-gcm', this.encryptionKey);
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    return authTag.toString('hex') + ':' + encrypted;
  }
  
  decrypt(encryptedData) {
    const parts = encryptedData.split(':');
    const authTag = Buffer.from(parts[0], 'hex');
    const encrypted = parts[1];
    
    const decipher = crypto.createDecipher('aes-256-gcm', this.encryptionKey);
    decipher.setAuthTag(authTag);
    
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }
  
  sanitizeMetadata(metadata) {
    const sanitized = { ...metadata };
    
    // Удаление чувствительных данных
    const sensitiveKeys = ['password', 'token', 'secret', 'key'];
    sensitiveKeys.forEach(key => {
      if (sanitized[key]) {
        sanitized[key] = '[REDACTED]';
      }
    });
    
    return sanitized;
  }
  
  isCriticalEvent(event) {
    const criticalEvents = [
      'CRITICAL_VULNERABILITY_FOUND',
      'UNAUTHORIZED_ACCESS_ATTEMPT',
      'DATA_BREACH_DETECTED',
      'SYSTEM_COMPROMISE'
    ];
    
    return criticalEvents.includes(event);
  }
  
  async sendImmediateAlert(logEntry) {
    // Отправка алертов в различные системы
    await Promise.all([
      this.sendEmailAlert(logEntry),
      this.sendSlackAlert(logEntry),
      this.sendWebhookAlert(logEntry)
    ]);
  }
  
  async generateSecurityReport(timeRange) {
    const logs = await this.getLogsInRange(timeRange);
    const report = this.analyzeLogs(logs);
    
    return {
      timeRange,
      generatedAt: new Date().toISOString(),
      summary: {
        totalEvents: report.totalEvents,
        criticalEvents: report.criticalEvents,
        uniqueUsers: report.uniqueUsers.size,
        topVulnerabilities: report.topVulnerabilities
      },
      details: report.detailedAnalysis
    };
  }
  
  analyzeLogs(logs) {
    const analysis = {
      totalEvents: logs.length,
      criticalEvents: 0,
      uniqueUsers: new Set(),
      topVulnerabilities: new Map(),
      detailedAnalysis: []
    };
    
    logs.forEach(log => {
      if (log.type === 'SECURITY_EVENT') {
        if (this.isCriticalEvent(log.event)) {
          analysis.criticalEvents++;
        }
        
        if (log.userId) {
          analysis.uniqueUsers.add(log.userId);
        }
      }
      
      if (log.type === 'ANALYSIS_RESULT') {
        log.vulnerabilities?.forEach(vuln => {
          const count = analysis.topVulnerabilities.get(vuln.type) || 0;
          analysis.topVulnerabilities.set(vuln.type, count + 1);
        });
      }
    });
    
    return analysis;
  }
}

module.exports = AdvancedAuditLogger;
```

## Решение сложных проблем

### Обработка сложных SQL конструкций

```javascript
// complex-query-analyzer.js
class ComplexQueryAnalyzer {
  constructor() {
    this.complexityMetrics = [
      'cyclomaticComplexity',
      'nestedSubqueries',
      'joinComplexity',
      'conditionalComplexity',
      'aggregationComplexity'
    ];
  }
  
  analyzeComplexQuery(query) {
    const ast = this.parseQuery(query);
    const complexity = this.calculateComplexity(ast);
    const issues = [];
    
    // Анализ сложных CTE
    if (this.hasComplexCTE(ast)) {
      issues.push(this.analyzeCTE(ast));
    }
    
    // Анализ рекурсивных запросов
    if (this.hasRecursiveQueries(ast)) {
      issues.push(this.analyzeRecursiveQuery(ast));
    }
    
    // Анализ оконных функций
    if (this.hasWindowFunctions(ast)) {
      issues.push(this.analyzeWindowFunctions(ast));
    }
    
    // Анализ сложных JOIN
    if (this.hasComplexJoins(ast)) {
      issues.push(this.analyzeComplexJoins(ast));
    }
    
    return {
      complexity,
      issues,
      recommendations: this.generateRecommendations(complexity, issues)
    };
  }
  
  calculateComplexity(ast) {
    let complexity = 1; // Базовая сложность
    
    // Цикломатическая сложность
    complexity += this.countConditionalStatements(ast);
    
    // Вложенные подзапросы
    complexity += this.countNestedSubqueries(ast) * 2;
    
    // Сложность JOIN
    complexity += this.calculateJoinComplexity(ast);
    
    // Агрегатные функции
    complexity += this.countAggregations(ast);
    
    return {
      score: complexity,
      level: this.getComplexityLevel(complexity),
      metrics: {
        conditionalStatements: this.countConditionalStatements(ast),
        nestedSubqueries: this.countNestedSubqueries(ast),
        joinCount: this.countJoins(ast),
        aggregationCount: this.countAggregations(ast)
      }
    };
  }
  
  analyzeRecursiveQuery(ast) {
    const recursiveCTE = this.findRecursiveCTE(ast);
    
    if (!recursiveCTE) return null;
    
    return {
      type: 'RECURSIVE_QUERY',
      severity: 'medium',
      title: 'Complex Recursive Query Detected',
      description: 'Recursive queries can be performance-intensive and hard to maintain',
      line: recursiveCTE.line,
      column: recursiveCTE.column,
      metadata: {
        recursionDepth: this.estimateRecursionDepth(recursiveCTE),
        terminationCondition: this.hasTerminationCondition(recursiveCTE)
      },
      recommendation: 'Consider optimizing recursive logic or using alternative approaches'
    };
  }
  
  analyzeWindowFunctions(ast) {
    const windowFunctions = this.findWindowFunctions(ast);
    const issues = [];
    
    windowFunctions.forEach(wf => {
      // Проверка на отсутствие PARTITION BY
      if (!wf.partitionBy && this.shouldHavePartitionBy(wf)) {
        issues.push({
          type: 'MISSING_PARTITION_BY',
          severity: 'medium',
          title: 'Window Function Missing PARTITION BY',
          description: 'Window function without PARTITION BY may cause performance issues',
          line: wf.line,
          column: wf.column,
          recommendation: 'Add appropriate PARTITION BY clause'
        });
      }
      
      // Проверка на неэффективные рамки
      if (this.hasInefficientFrame(wf)) {
        issues.push({
          type: 'INEFFICIENT_WINDOW_FRAME',
          severity: 'low',
          title: 'Inefficient Window Frame',
          description: 'Window frame may cause performance degradation',
          line: wf.line,
          column: wf.column,
          recommendation: 'Optimize window frame or consider alternative approach'
        });
      }
    });
    
    return issues;
  }
  
  generateRecommendations(complexity, issues) {
    const recommendations = [];
    
    if (complexity.score > 20) {
      recommendations.push({
        priority: 'high',
        type: 'COMPLEXITY_REDUCTION',
        message: 'Consider breaking down complex query into simpler components',
        action: 'split_query'
      });
    }
    
    if (issues.some(i => i.type === 'RECURSIVE_QUERY')) {
      recommendations.push({
        priority: 'medium',
        type: 'RECURSION_OPTIMIZATION',
        message: 'Optimize recursive query or consider materialized views',
        action: 'optimize_recursion'
      });
    }
    
    if (issues.some(i => i.type.includes('JOIN'))) {
      recommendations.push({
        priority: 'medium',
        type: 'JOIN_OPTIMIZATION',
        message: 'Review join order and consider appropriate indexing',
        action: 'optimize_joins'
      });
    }
    
    return recommendations;
  }
}

module.exports = ComplexQueryAnalyzer;
```

---

**Поздравляем!** Вы освоили продвинутые возможности SQLGuard Pro.

*Продолжайте обучение в [руководстве для экспертов](./expert-guide.md)*
