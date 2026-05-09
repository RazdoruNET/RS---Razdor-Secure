# 🔌 Разработка плагинов

## 📋 Обзор

SQLGuard Pro поддерживает плагинную архитектуру, позволяя разработчикам создавать собственные правила анализа и интеграции.

---

## 🏗️ Архитектура плагинов

### Базовая структура плагина

```javascript
const BasePlugin = require('sqlguard-pro/core/BasePlugin');

class CustomSecurityPlugin extends BasePlugin {
  constructor(config) {
    super(config);
    this.name = 'custom-security';
    this.version = '1.0.0';
    this.description = 'Custom security analysis plugin';
    this.author = 'Your Name';
    
    // Метаданные плагина
    this.metadata = {
      category: 'security',
      supportedDatabases: ['mysql', 'postgresql', 'mssql'],
      minVersion: '1.0.0',
      maxVersion: '2.0.0'
    };
  }
  
  async initialize() {
    await super.initialize();
    this.setupRules();
    this.loadPatterns();
  }
  
  async analyze(sql, context) {
    const results = [];
    
    // Основная логика анализа
    const vulnerabilities = await this.detectVulnerabilities(sql, context);
    results.push(...vulnerabilities);
    
    return results;
  }
  
  async cleanup() {
    await super.cleanup();
    this.cleanupResources();
  }
}

module.exports = CustomSecurityPlugin;
```

---

## 🔧 Создание правил анализа

### Правило для SQL Injection

```javascript
class SQLInjectionRule extends BaseRule {
  constructor() {
    super({
      name: 'custom-sql-injection',
      severity: 'high',
      category: 'sql-injection',
      description: 'Custom SQL injection detection rule'
    });
    
    // Паттерны для обнаружения
    this.patterns = [
      // String concatenation
      {
        pattern: /['"]\s*\+\s*['"]|['"]\s*\+\s*\w+\s*\+\s*['"]/gi,
        type: 'string-concatenation',
        message: 'String concatenation in SQL query'
      },
      
      // Dynamic query execution
      {
        pattern: /execute\s*\(\s*['"]\s*.*\s*\+\s*/gi,
        type: 'dynamic-execution',
        message: 'Dynamic SQL execution detected'
      },
      
      // Eval-like functions
      {
        pattern: /eval\s*\(|exec\s*\(|sp_executesql/gi,
        type: 'eval-function',
        message: 'Potentially dangerous SQL function'
      }
    ];
  }
  
  async analyze(sql, context) {
    const vulnerabilities = [];
    
    for (const pattern of this.patterns) {
      const matches = sql.match(pattern.pattern);
      
      if (matches) {
        vulnerabilities.push({
          id: this.generateId(),
          rule: this.name,
          type: pattern.type,
          severity: this.severity,
          line: this.findLineNumber(sql, matches[0]),
          column: this.findColumnNumber(sql, matches[0]),
          match: matches[0],
          message: pattern.message,
          recommendation: this.getRecommendation(pattern.type),
          context: this.extractContext(sql, matches[0])
        });
      }
    }
    
    return vulnerabilities;
  }
  
  getRecommendation(type) {
    const recommendations = {
      'string-concatenation': 'Use parameterized queries or prepared statements',
      'dynamic-execution': 'Avoid dynamic SQL execution. Use stored procedures or parameterized queries',
      'eval-function': 'Replace eval/exec functions with safe alternatives'
    };
    
    return recommendations[type] || 'Review SQL query for security issues';
  }
}
```

### Правило для анализа производительности

```javascript
class PerformanceRule extends BaseRule {
  constructor() {
    super({
      name: 'performance-analysis',
      severity: 'medium',
      category: 'performance',
      description: 'SQL performance analysis rule'
    });
    
    this.performancePatterns = [
      {
        pattern: /SELECT\s+\*\s+FROM/i,
        type: 'select-star',
        message: 'SELECT * detected - may impact performance'
      },
      
      {
        pattern: /ORDER\s+BY\s+RAND\s*\(/i,
        type: 'order-by-rand',
        message: 'ORDER BY RAND() - very expensive operation'
      },
      
      {
        pattern: /LIKE\s+['"]%.*%['"]/i,
        type: 'leading-wildcard',
        message: 'Leading wildcard in LIKE - prevents index usage'
      }
    ];
  }
  
  async analyze(sql, context) {
    const issues = [];
    
    // Анализ SELECT *
    if (this.performancePatterns[0].pattern.test(sql)) {
      const table = this.extractTableFromSelect(sql);
      issues.push({
        id: this.generateId(),
        type: 'select-star',
        severity: 'medium',
        message: 'SELECT * instead of specific columns',
        recommendation: `Specify only needed columns: SELECT id, name, email FROM ${table}`,
        impact: 'High - transfers unnecessary data',
        table: table
      });
    }
    
    // Анализ ORDER BY RAND()
    if (this.performancePatterns[1].pattern.test(sql)) {
      issues.push({
        id: this.generateId(),
        type: 'order-by-rand',
        severity: 'high',
        message: 'ORDER BY RAND() detected',
        recommendation: 'Use application-level randomization or indexed random selection',
        impact: 'Very High - full table scan required'
      });
    }
    
    // Анализ LIKE с ведущим wildcard
    if (this.performancePatterns[2].pattern.test(sql)) {
      issues.push({
        id: this.generateId(),
        type: 'leading-wildcard',
        severity: 'medium',
        message: 'LIKE with leading wildcard',
        recommendation: 'Use full-text search or remove leading wildcard',
        impact: 'Medium - prevents index usage'
      });
    }
    
    return issues;
  }
}
```

---

## 🔗 Интеграция с внешними сервисами

### Плагин для интеграции с CVE Database

```javascript
class CVEIntegrationPlugin extends BasePlugin {
  constructor(config) {
    super(config);
    this.name = 'cve-integration';
    this.cveApiUrl = 'https://services.nvd.nist.gov/rest/json/cves/1.0';
    this.cache = new Map();
  }
  
  async analyze(sql, context) {
    const vulnerabilities = [];
    
    // Извлечение версий БД из SQL
    const dbVersion = this.extractDatabaseVersion(sql);
    if (dbVersion) {
      const cves = await this.getCVEsForDatabase(dbVersion.type, dbVersion.version);
      
      for (const cve of cves) {
        if (this.isRelevantCVE(cve, sql)) {
          vulnerabilities.push({
            id: this.generateId(),
            type: 'cve-vulnerability',
            severity: this.mapCVESeverity(cve.severity),
            cveId: cve.id,
            description: cve.description,
            affectedVersion: dbVersion.version,
            recommendation: `Upgrade to version ${cve.fixedVersion} or later`,
            references: cve.references
          });
        }
      }
    }
    
    return vulnerabilities;
  }
  
  async getCVEsForDatabase(dbType, version) {
    const cacheKey = `${dbType}-${version}`;
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }
    
    try {
      const response = await fetch(`${this.cveApiUrl}?keyword=${dbType}`);
      const data = await response.json();
      
      const relevantCVEs = data.result.CVE_Items.filter(cve => 
        this.isVersionAffected(version, cve)
      );
      
      // Кеширование на 1 час
      this.cache.set(cacheKey, relevantCVEs);
      setTimeout(() => this.cache.delete(cacheKey), 3600000);
      
      return relevantCVEs;
    } catch (error) {
      this.error('Failed to fetch CVEs:', error);
      return [];
    }
  }
  
  isVersionAffected(version, cve) {
    // Логика проверки версии
    const versionParts = version.split('.').map(Number);
    
    for (const config of cve.configurations || []) {
      if (config.cpe_match) {
        for (const match of config.cpe_match) {
          if (match.versionStartIncluding && match.versionEndIncluding) {
            return this.isVersionInRange(version, 
              match.versionStartIncluding, 
              match.versionEndIncluding);
          }
        }
      }
    }
    
    return false;
  }
}
```

---

## 🧪 Тестирование плагинов

### Unit тесты

```javascript
const CustomSecurityPlugin = require('../src/plugins/CustomSecurityPlugin');
const assert = require('assert');

describe('CustomSecurityPlugin', () => {
  let plugin;
  
  beforeEach(() => {
    plugin = new CustomSecurityPlugin({
      enabled: true,
      severity: 'high'
    });
  });
  
  afterEach(async () => {
    await plugin.cleanup();
  });
  
  describe('SQL Injection Detection', () => {
    it('should detect string concatenation', async () => {
      const sql = "SELECT * FROM users WHERE name = '" + userName + "'";
      const context = { language: 'javascript' };
      
      const results = await plugin.analyze(sql, context);
      
      assert.ok(results.length > 0);
      assert.equal(results[0].type, 'string-concatenation');
      assert.equal(results[0].severity, 'high');
    });
    
    it('should not detect parameterized queries', async () => {
      const sql = 'SELECT * FROM users WHERE name = ?';
      const context = { language: 'javascript' };
      
      const results = await plugin.analyze(sql, context);
      
      assert.equal(results.length, 0);
    });
  });
  
  describe('Performance Analysis', () => {
    it('should detect SELECT *', async () => {
      const sql = 'SELECT * FROM users';
      const context = { language: 'sql' };
      
      const results = await plugin.analyze(sql, context);
      
      assert.ok(results.length > 0);
      assert.equal(results[0].type, 'select-star');
    });
    
    it('should suggest specific columns', async () => {
      const sql = 'SELECT * FROM users';
      const context = { language: 'sql' };
      
      const results = await plugin.analyze(sql, context);
      
      assert.ok(results[0].recommendation.includes('id, name, email'));
    });
  });
});
```

### Интеграционные тесты

```javascript
describe('Plugin Integration', () => {
  let sqlguard;
  let plugin;
  
  before(async () => {
    sqlguard = new SQLGuardPro();
    plugin = new CustomSecurityPlugin({
      enabled: true,
      apiKeys: {
        cve: process.env.CVE_API_KEY
      }
    });
    
    await sqlguard.registerPlugin(plugin);
    await sqlguard.initialize();
  });
  
  after(async () => {
    await sqlguard.cleanup();
  });
  
  it('should integrate with SQLGuard Pro', async () => {
    const testSQL = `
      SELECT * FROM users 
      WHERE name = '${userName}' 
      ORDER BY RAND()
    `;
    
    const results = await sqlguard.analyze(testSQL);
    
    // Проверка результатов от плагина
    const pluginResults = results.filter(r => r.plugin === 'custom-security');
    assert.ok(pluginResults.length > 0);
    
    // Проверка типов уязвимостей
    const types = pluginResults.map(r => r.type);
    assert.ok(types.includes('string-concatenation'));
    assert.ok(types.includes('select-star'));
    assert.ok(types.includes('order-by-rand'));
  });
});
```

---

## 📦 Публикация плагинов

### Структура пакета

```json
// package.json
{
  "name": "@sqlguard-pro/custom-security-plugin",
  "version": "1.0.0",
  "description": "Custom security analysis plugin for SQLGuard Pro",
  "main": "index.js",
  "keywords": [
    "sqlguard-pro",
    "plugin",
    "security",
    "sql",
    "vulnerability"
  ],
  "author": "Your Name <your.email@example.com>",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/custom-security-plugin.git"
  },
  "sqlguard-pro": {
    "pluginType": "analysis",
    "category": "security",
    "supportedVersions": "^1.0.0",
    "dependencies": [],
    "permissions": ["network", "filesystem"]
  }
}
```

### Манифест плагина

```json
// plugin.json
{
  "name": "custom-security",
  "version": "1.0.0",
  "description": "Custom security analysis plugin",
  "author": "Your Name",
  "license": "MIT",
  "entry": "index.js",
  "category": "security",
  "type": "analysis",
  "supportedDatabases": ["mysql", "postgresql", "mssql", "oracle", "sqlite"],
  "permissions": {
    "network": true,
    "filesystem": {
      "read": true,
      "write": false
    },
    "environment": ["API_KEYS"]
  },
  "configuration": {
    "schema": "./config/schema.json",
    "default": "./config/default.json"
  },
  "hooks": {
    "beforeAnalysis": "beforeAnalysisHook",
    "afterAnalysis": "afterAnalysisHook",
    "onVulnerabilityFound": "onVulnerabilityHook"
  }
}
```

### Регистрация плагина

```javascript
// index.js
const CustomSecurityPlugin = require('./src/CustomSecurityPlugin');

module.exports = {
  plugin: CustomSecurityPlugin,
  manifest: require('./plugin.json'),
  hooks: {
    beforeAnalysis: async (context) => {
      console.log('Starting analysis with custom plugin');
      return context;
    },
    
    afterAnalysis: async (results) => {
      console.log(`Analysis completed. Found ${results.length} issues`);
      return results;
    },
    
    onVulnerabilityFound: async (vulnerability) => {
      // Отправка в внешнюю систему
      await this.sendToSlack(vulnerability);
      return vulnerability;
    }
  }
};
```

---

## 🔧 Конфигурация плагинов

### Schema конфигурации

```json
// config/schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": true,
      "description": "Enable or disable the plugin"
    },
    "severity": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"],
      "default": "medium",
      "description": "Default severity for findings"
    },
    "apiKeys": {
      "type": "object",
      "properties": {
        "cve": {
          "type": "string",
          "description": "CVE Database API key"
        }
      }
    },
    "thresholds": {
      "type": "object",
      "properties": {
        "minConfidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "default": 0.7
        }
      }
    }
  },
  "required": ["enabled"]
}
```

### Конфигурация по умолчанию

```json
// config/default.json
{
  "enabled": true,
  "severity": "medium",
  "apiKeys": {
    "cve": ""
  },
  "thresholds": {
    "minConfidence": 0.7,
    "maxResults": 100
  },
  "performance": {
    "cacheEnabled": true,
    "cacheTTL": 3600,
    "timeout": 30000
  },
  "reporting": {
    "includeCVE": true,
    "includeRecommendations": true,
    "customFields": []
  }
}
```

---

## 🔄 Обновление плагинов

### Автоматические обновления

```javascript
class PluginUpdater {
  constructor(plugin) {
    this.plugin = plugin;
    this.updateUrl = `https://plugins.sqlguard-pro.com/${plugin.name}/updates`;
  }
  
  async checkForUpdates() {
    try {
      const response = await fetch(`${this.updateUrl}/latest.json`);
      const updateInfo = await response.json();
      
      if (this.isNewerVersion(updateInfo.version, this.plugin.version)) {
        return {
          available: true,
          version: updateInfo.version,
          downloadUrl: updateInfo.downloadUrl,
          changelog: updateInfo.changelog,
          critical: updateInfo.critical || false
        };
      }
      
      return { available: false };
    } catch (error) {
      this.error('Update check failed:', error);
      return { available: false, error: error.message };
    }
  }
  
  async installUpdate(updateInfo) {
    try {
      // Скачивание обновления
      const response = await fetch(updateInfo.downloadUrl);
      const pluginData = await response.buffer();
      
      // Проверка цифровой подписи
      if (!await this.verifySignature(pluginData, updateInfo.signature)) {
        throw new Error('Invalid plugin signature');
      }
      
      // Установка обновления
      await this.extractAndInstall(pluginData);
      
      // Перезагрузка плагина
      await this.reloadPlugin();
      
      return { success: true };
    } catch (error) {
      this.error('Update installation failed:', error);
      return { success: false, error: error.message };
    }
  }
}
```

---

## 📚 Примеры плагинов

### Плагин для анализа ORM запросов

```javascript
class ORMAnalysisPlugin extends BasePlugin {
  constructor(config) {
    super(config);
    this.name = 'orm-analysis';
    this.supportedORMs = ['sequelize', 'typeorm', 'prisma'];
  }
  
  async analyze(code, context) {
    const vulnerabilities = [];
    
    // Анализ Sequelize запросов
    if (context.framework === 'sequelize') {
      const sequelizeVulns = await this.analyzeSequelize(code);
      vulnerabilities.push(...sequelizeVulns);
    }
    
    // Анализ TypeORM запросов
    if (context.framework === 'typeorm') {
      const typeormVulns = await this.analyzeTypeORM(code);
      vulnerabilities.push(...typeormVulns);
    }
    
    // Анализ Prisma запросов
    if (context.framework === 'prisma') {
      const prismaVulns = await this.analyzePrisma(code);
      vulnerabilities.push(...prismaVulns);
    }
    
    return vulnerabilities;
  }
  
  async analyzeSequelize(code) {
    const vulnerabilities = [];
    
    // Поиск небезопасных Sequelize запросов
    const unsafePatterns = [
      {
        pattern: /sequelize\.query\s*\(\s*['"`]([^'"`]*[^?]*)['"`]/gi,
        type: 'raw-query',
        message: 'Raw SQL query in Sequelize'
      },
      {
        pattern: /\.literal\s*\(/gi,
        type: 'literal-usage',
        message: 'Sequelize literal usage - potential SQL injection'
      }
    ];
    
    for (const pattern of unsafePatterns) {
      const matches = code.match(pattern.pattern);
      if (matches) {
        vulnerabilities.push({
          id: this.generateId(),
          type: pattern.type,
          severity: 'high',
          message: pattern.message,
          recommendation: 'Use parameterized Sequelize methods instead of raw queries'
        });
      }
    }
    
    return vulnerabilities;
  }
}
```

### Плагин для интеграции с SIEM

```javascript
class SIEMIntegrationPlugin extends BasePlugin {
  constructor(config) {
    super(config);
    this.name = 'siem-integration';
    this.siemConfig = config.siem;
  }
  
  async analyze(sql, context) {
    const vulnerabilities = await super.analyze(sql, context);
    
    // Отправка критических уязвимостей в SIEM
    const criticalVulns = vulnerabilities.filter(v => v.severity === 'critical');
    
    for (const vuln of criticalVulns) {
      await this.sendToSIEM(vuln, context);
    }
    
    return vulnerabilities;
  }
  
  async sendToSIEM(vulnerability, context) {
    const siemEvent = {
      timestamp: new Date().toISOString(),
      event_type: 'security_vulnerability',
      severity: this.mapSeverityToSIEM(vulnerability.severity),
      source: 'sqlguard-pro',
      details: {
        vulnerability: vulnerability,
        file: context.file,
        line: vulnerability.line,
        project: context.project
      }
    };
    
    try {
      await this.sendSIEMEvent(siemEvent);
    } catch (error) {
      this.error('Failed to send SIEM event:', error);
    }
  }
  
  async sendSIEMEvent(event) {
    const response = await fetch(this.siemConfig.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.siemConfig.apiKey}`
      },
      body: JSON.stringify(event)
    });
    
    if (!response.ok) {
      throw new Error(`SIEM API error: ${response.status}`);
    }
    
    return response.json();
  }
}
```

---

## 🛠️ Отладка плагинов

### Логирование

```javascript
class CustomPlugin extends BasePlugin {
  constructor(config) {
    super(config);
    this.logger = this.createLogger();
  }
  
  createLogger() {
    return {
      debug: (message, ...args) => {
        if (this.config.debug) {
          console.log(`[${this.name}] DEBUG:`, message, ...args);
        }
      },
      info: (message, ...args) => {
        console.log(`[${this.name}] INFO:`, message, ...args);
      },
      warn: (message, ...args) => {
        console.warn(`[${this.name}] WARN:`, message, ...args);
      },
      error: (message, ...args) => {
        console.error(`[${this.name}] ERROR:`, message, ...args);
      }
    };
  }
  
  async analyze(sql, context) {
    this.logger.debug('Starting analysis', { sqlLength: sql.length });
    
    try {
      const results = await this.performAnalysis(sql, context);
      this.logger.info(`Analysis completed. Found ${results.length} issues`);
      return results;
    } catch (error) {
      this.logger.error('Analysis failed:', error);
      throw error;
    }
  }
}
```

### Метрики плагина

```javascript
class PluginMetrics {
  constructor(pluginName) {
    this.pluginName = pluginName;
    this.metrics = {
      analyses: 0,
      vulnerabilities: 0,
      executionTime: 0,
      errors: 0
    };
  }
  
  recordAnalysis(duration, vulnerabilityCount) {
    this.metrics.analyses++;
    this.metrics.vulnerabilities += vulnerabilityCount;
    this.metrics.executionTime += duration;
  }
  
  recordError() {
    this.metrics.errors++;
  }
  
  getMetrics() {
    return {
      plugin: this.pluginName,
      ...this.metrics,
      averageExecutionTime: this.metrics.executionTime / this.metrics.analyses,
      vulnerabilityRate: this.metrics.vulnerabilities / this.metrics.analyses,
      errorRate: this.metrics.errors / this.metrics.analyses
    };
  }
}
```

---

## 📚 Ресурсы для разработчиков

### Документация
- [SQLGuard Pro Plugin API](https://docs.sqlguard-pro.com/plugin-api)
- [Plugin Development Guide](https://docs.sqlguard-pro.com/plugin-development)
- [Security Guidelines](https://docs.sqlguard-pro.com/security-guidelines)

### Инструменты
- [Plugin Generator](https://github.com/sqlguard-pro/plugin-generator)
- [Testing Framework](https://github.com/sqlguard-pro/plugin-test-utils)
- [Validation Tools](https://github.com/sqlguard-pro/plugin-validator)

### Сообщество
- [Discord Plugin Development](https://discord.gg/sqlguard-plugins)
- [GitHub Discussions](https://github.com/sqlguard-pro/discussions/categories/plugins)
- [Plugin Registry](https://plugins.sqlguard-pro.com)

---

## 🎯 Лучшие практики

### 1. Безопасность плагинов
- Валидируйте все входные данные
- Используйте параметризованные запросы
- Не храните чувствительные данные в коде
- Применяйте принцип наименьших привилегий

### 2. Производительность
- Кешируйте результаты внешних запросов
- Используйте асинхронные операции
- Ограничивайте использование памяти
- Обрабатывайте ошибки gracefully

### 3. Совместимость
- Следуйте семантическому версионированию
- Тестируйте с разными версиями SQLGuard Pro
- Предоставляйте обратную совместимость
- Документируйте breaking changes

### 4. Тестирование
- Пишите unit тесты для всех функций
- Используйте интеграционные тесты
- Тестируйте пограничные случаи
- Автоматизируйте тестирование

---

*Последнее обновление: 9 мая 2026*
