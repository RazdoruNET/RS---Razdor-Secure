# 🏗️ Архитектура Prophecy Sentinel

Техническая документация архитектуры системы

---

## 📋 Обзор архитектуры

Prophecy Sentinel построен на **микроядерной архитектуре** с событийно-ориентированным дизайном, обеспечивающим высокую модульность, масштабируемость и отказоустойчивость.

### 🎯 Ключевые принципы
- **Модульность** - независимые компоненты с четкими интерфейсами
- **Событийность** - асинхронная обработка событий
- **Масштабируемость** - горизонтальное масштабирование
- **Отказоустойчивость** - graceful degradation
- **Расширяемость** - плагинная архитектура

---

## 🏛️ Микроядерная архитектура

### 📦 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                 Prophecy Sentinel Core                │
├─────────────────────────────────────────────────────────────┤
│  🧠 Microkernel                                      │
│  ┌─────────────┬─────────────┬─────────────────────┐    │
│  │ Event Bus   │ Service Mgr  │ Dependency Inj.    │    │
│  └─────────────┴─────────────┴─────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  🔍 Detection Services                               │
│  ┌─────────────┬─────────────┬─────────────────────┐    │
│  │ SQL Injector│ XSS Scanner  │ File Analyzer     │    │
│  └─────────────┴─────────────┴─────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  🎭 Validation Services                             │
│  ┌─────────────┬─────────────┬─────────────────────┐    │
│  │ Playwright  │ Replay Val  │ Sink Confirmation │    │
│  └─────────────┴─────────────┴─────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  📊 Analysis & Reporting                            │
│  ┌─────────────┬─────────────┬─────────────────────┐    │
│  │ Metrics     │ Reporting   │ Benchmarking       │    │
│  └─────────────┴─────────────┴─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 Microkernel Details

#### Event Bus
```javascript
class EventBus {
  constructor() {
    this.events = new Map();
    this.middleware = [];
  }
  
  // Подписка на события
  on(event, handler, priority = 0) {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event).push({ handler, priority });
  }
  
  // Публикация события
  async emit(event, data) {
    const handlers = this.events.get(event) || [];
    
    // Применение middleware
    for (const middleware of this.middleware) {
      data = await middleware(event, data);
    }
    
    // Выполнение обработчиков по приоритету
    handlers.sort((a, b) => b.priority - a.priority);
    
    for (const { handler } of handlers) {
      try {
        await handler(data);
      } catch (error) {
        this.emit('error', { event, error, data });
      }
    }
  }
}
```

#### Service Manager
```javascript
class ServiceManager {
  constructor() {
    this.services = new Map();
    this.dependencies = new Map();
  }
  
  // Регистрация сервиса
  register(name, service, dependencies = []) {
    this.services.set(name, {
      instance: service,
      dependencies,
      initialized: false
    });
    
    this.dependencies.set(name, dependencies);
  }
  
  // Инициализация сервиса
  async initialize(name) {
    const service = this.services.get(name);
    
    if (service.initialized) {
      return service.instance;
    }
    
    // Инициализация зависимостей
    for (const dep of service.dependencies) {
      await this.initialize(dep);
    }
    
    // Инициализация сервиса
    if (typeof service.instance.initialize === 'function') {
      await service.instance.initialize();
    }
    
    service.initialized = true;
    return service.instance;
  }
}
```

---

## 🔍 Detection Layer

### 📊 Vulnerability Detectors

#### Base Detector Interface
```typescript
interface VulnerabilityDetector {
  name: string;
  version: string;
  supportedTypes: VulnerabilityType[];
  
  // Основные методы
  detect(target: Target): Promise<DetectionResult[]>;
  validate(finding: DetectionResult): Promise<ValidationResult>;
  
  // Конфигурация
  configure(options: DetectorOptions): void;
  getConfiguration(): DetectorOptions;
  
  // Метрики
  getMetrics(): DetectorMetrics;
}
```

#### SQL Injection Detector
```javascript
class SQLInjectionDetector implements VulnerabilityDetector {
  constructor() {
    this.name = 'SQL Injection Detector';
    this.version = '1.0.0';
    this.supportedTypes = ['SQL_INJECTION'];
    this.payloads = new SQLPayloadGenerator();
    this.analyzer = new SQLResponseAnalyzer();
  }
  
  async detect(target) {
    const results = [];
    
    // Генерация payloads
    const payloads = await this.payloads.generate(target);
    
    // Параллельное тестирование
    const promises = payloads.map(payload => 
      this.testPayload(target, payload)
    );
    
    const testResults = await Promise.all(promises);
    
    // Анализ результатов
    for (const result of testResults) {
      if (await this.analyzer.isVulnerable(result)) {
        results.push(await this.analyzer.createFinding(result));
      }
    }
    
    return results;
  }
  
  async testPayload(target, payload) {
    const startTime = Date.now();
    
    try {
      const response = await this.makeRequest(target, payload);
      const endTime = Date.now();
      
      return {
        target,
        payload,
        response,
        timing: endTime - startTime,
        success: true
      };
    } catch (error) {
      return {
        target,
        payload,
        error: error.message,
        success: false
      };
    }
  }
}
```

---

## 🎭 Validation Layer

### 🎭 Multi-Stage Validation

#### Validation Pipeline
```javascript
class ValidationPipeline {
  constructor() {
    this.stages = [
      new SinkConfirmationStage(),
      new ReplayValidationStage(),
      new PlaywrightValidationStage()
    ];
  }
  
  async validate(finding) {
    const context = new ValidationContext(finding);
    
    for (const stage of this.stages) {
      try {
        const result = await stage.validate(context);
        context.addResult(stage.name, result);
        
        // Early exit если required stage failed
        if (!result.passed && stage.required) {
          break;
        }
      } catch (error) {
        context.addError(stage.name, error);
      }
    }
    
    return context.getFinalResult();
  }
}
```

#### Sink Confirmation
```javascript
class SinkConfirmationStage {
  async validate(context) {
    const finding = context.finding;
    
    switch (finding.type) {
      case 'SQL_INJECTION':
        return await this.confirmSQLSink(finding);
      case 'XSS':
        return await this.confirmXSSSink(finding);
      case 'FILE_INCLUSION':
        return await this.confirmFileInclusionSink(finding);
      default:
        return { passed: false, reason: 'Unsupported vulnerability type' };
    }
  }
  
  async confirmSQLSink(finding) {
    // Проверка достижения SQL sink
    const indicators = [
      /sql|mysql|postgresql|sqlite/i,
      /error|warning|syntax/i,
      /ora-/i
    ];
    
    const response = finding.response;
    const content = response.text || '';
    
    for (const indicator of indicators) {
      if (indicator.test(content)) {
        return {
          passed: true,
          confidence: 0.8,
          evidence: `SQL sink indicator found: ${indicator.source}`
        };
      }
    }
    
    return { passed: false, confidence: 0.1 };
  }
}
```

---

## 📊 Analysis & Reporting

### 📈 Metrics Collection

#### Metrics Engine
```javascript
class MetricsEngine {
  constructor() {
    this.metrics = new Map();
    this.collectors = [
      new PerformanceMetricsCollector(),
      new VulnerabilityMetricsCollector(),
      new SystemMetricsCollector()
    ];
  }
  
  async collectMetrics(scanResult) {
    const metrics = {};
    
    for (const collector of this.collectors) {
      const collectorMetrics = await collector.collect(scanResult);
      Object.assign(metrics, collectorMetrics);
    }
    
    // Сохранение метрик
    await this.saveMetrics(metrics);
    
    return metrics;
  }
  
  async saveMetrics(metrics) {
    const timestamp = new Date().toISOString();
    const data = {
      timestamp,
      metrics,
      scanId: metrics.scanId
    };
    
    // Сохранение в базу данных
    await this.db.insert('metrics', data);
    
    // Отправка в мониторинг
    await this.sendToMonitoring(data);
  }
}
```

#### CVSS Calculator
```javascript
class CVSSCalculator {
  calculateScore(vulnerability) {
    const metrics = {
      attackVector: this.getAttackVector(vulnerability),
      attackComplexity: this.getAttackComplexity(vulnerability),
      privilegesRequired: this.getPrivilegesRequired(vulnerability),
      userInteraction: this.getUserInteraction(vulnerability),
      scope: this.getScope(vulnerability),
      confidentiality: this.getConfidentialityImpact(vulnerability),
      integrity: this.getIntegrityImpact(vulnerability),
      availability: this.getAvailabilityImpact(vulnerability)
    };
    
    return this.computeCVSSScore(metrics);
  }
  
  computeCVSSScore(metrics) {
    // Базовая метрика
    const impact = 1 - ((1 - metrics.confidentiality) * 
                          (1 - metrics.integrity) * 
                          (1 - metrics.availability));
    
    const exploitability = 8.22 * metrics.attackVector * 
                                   metrics.attackComplexity * 
                                   metrics.privilegesRequired * 
                                   metrics.userInteraction;
    
    const baseScore = Math.min(10, impact + exploitability);
    
    // Финальная метрика
    if (metrics.scope === 'CHANGED') {
      return Math.min(10, 1.08 * (impact + exploitability));
    } else {
      return baseScore;
    }
  }
}
```

---

## 🔄 Event Flow

### 📋 Scan Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                  Scan Initiation                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Target Validation                       │
│  • DNS Resolution                                   │
│  • Port Scanning                                   │
│  • Service Detection                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Parallel Detection                        │
│  • SQL Injection                                    │
│  • XSS                                             │
│  • Directory Traversal                               │
│  • File Inclusion                                  │
│  • Security Headers                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Evidence Correlation                      │
│  • Grouping Similar Findings                        │
│  • False Positive Suppression                        │
│  • Confidence Scoring                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│          Multi-Stage Validation                    │
│  • Sink Confirmation                                │
│  • Replay Validation                                │
│  • Playwright Execution                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Report Generation                        │
│  • CVSS Scoring                                   │
│  • Risk Assessment                                │
│  • Recommendations                                │
│  • Export (JSON, HTML, PDF)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security Architecture

### 🔐 Security Layers

#### Input Validation
```javascript
class InputValidator {
  static validateTarget(target) {
    const patterns = {
      // URL валидация
      url: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&=]*)$/,
      
      // Запрет приватных IP
      privateIP: /^(10\.|172\.(1[6-9]|2[0-9]|3[0-1])|192\.168\.)/,
      
      // Запрет localhost в production
      localhost: /^(localhost|127\.0\.0\.1)/
    };
    
    // Проверка паттернов
    if (patterns.privateIP.test(target) && process.env.NODE_ENV === 'production') {
      throw new Error('Private IP addresses not allowed in production');
    }
    
    if (patterns.localhost.test(target) && process.env.NODE_ENV === 'production') {
      throw new Error('Localhost not allowed in production');
    }
    
    return true;
  }
  
  static sanitizePayload(payload) {
    // Ограничение длины
    if (payload.length > 1000) {
      throw new Error('Payload too long');
    }
    
    // Фильтрация опасных символов для внутренних операций
    const dangerousChars = /[;&|`$(){}[\]]/;
    if (dangerousChars.test(payload)) {
      throw new Error('Dangerous characters detected');
    }
    
    return payload;
  }
}
```

#### Rate Limiting
```javascript
class RateLimiter {
  constructor() {
    this.requests = new Map();
    this.limits = {
      perSecond: 10,
      perMinute: 100,
      perHour: 1000
    };
  }
  
  async checkLimit(identifier) {
    const now = Date.now();
    const key = `${identifier}:${Math.floor(now / 1000)}`;
    
    if (!this.requests.has(key)) {
      this.requests.set(key, 0);
    }
    
    const current = this.requests.get(key);
    
    if (current >= this.limits.perSecond) {
      throw new Error('Rate limit exceeded');
    }
    
    this.requests.set(key, current + 1);
    
    // Очистка старых записей
    this.cleanup();
  }
  
  cleanup() {
    const cutoff = Date.now() - 3600000; // 1 час
    for (const [key] of this.requests) {
      const timestamp = parseInt(key.split(':')[1]) * 1000;
      if (timestamp < cutoff) {
        this.requests.delete(key);
      }
    }
  }
}
```

---

## 📊 Performance Architecture

### ⚡ Concurrency Control

#### Task Queue
```javascript
class TaskQueue {
  constructor(concurrency = 5) {
    this.concurrency = concurrency;
    this.running = 0;
    this.queue = [];
  }
  
  async add(task) {
    return new Promise((resolve, reject) => {
      this.queue.push({
        task,
        resolve,
        reject
      });
      
      this.process();
    });
  }
  
  async process() {
    if (this.running >= this.concurrency || this.queue.length === 0) {
      return;
    }
    
    this.running++;
    const { task, resolve, reject } = this.queue.shift();
    
    try {
      const result = await task();
      resolve(result);
    } catch (error) {
      reject(error);
    } finally {
      this.running--;
      this.process(); // Обработка следующей задачи
    }
  }
}
```

#### Resource Management
```javascript
class ResourceManager {
  constructor() {
    this.resources = {
      memory: { max: 1024 * 1024 * 1024, current: 0 }, // 1GB
      connections: { max: 100, current: 0 },
      processes: { max: 50, current: 0 }
    };
  }
  
  async allocate(type, amount) {
    if (this.resources[type].current + amount > this.resources[type].max) {
      throw new Error(`${type} resource limit exceeded`);
    }
    
    this.resources[type].current += amount;
    
    return {
      release: () => {
        this.resources[type].current -= amount;
      }
    };
  }
  
  getUsage() {
    const usage = {};
    for (const [type, resource] of Object.entries(this.resources)) {
      usage[type] = {
        current: resource.current,
        max: resource.max,
        percentage: (resource.current / resource.max * 100).toFixed(2)
      };
    }
    return usage;
  }
}
```

---

## 🔧 Configuration Architecture

### 📝 Configuration Management

#### Hierarchical Configuration
```javascript
class ConfigurationManager {
  constructor() {
    this.config = {
      // Default конфигурация
      default: require('./config/default.json'),
      
      // Environment-specific конфигурация
      environment: require(`./config/${process.env.NODE_ENV || 'development'}.json`),
      
      // User конфигурация
      user: this.loadUserConfig(),
      
      // Runtime конфигурация
      runtime: {}
    };
  }
  
  get(path) {
    // Поиск в иерархии конфигурации
    const keys = path.split('.');
    
    for (const level of ['runtime', 'user', 'environment', 'default']) {
      let value = this.config[level];
      
      for (const key of keys) {
        if (value && typeof value === 'object' && key in value) {
          value = value[key];
        } else {
          value = undefined;
          break;
        }
      }
      
      if (value !== undefined) {
        return value;
      }
    }
    
    throw new Error(`Configuration path not found: ${path}`);
  }
  
  set(path, value) {
    // Установка runtime конфигурации
    this.config.runtime[path] = value;
  }
  
  loadUserConfig() {
    try {
      const userConfigPath = path.join(os.homedir(), '.prophecy-sentinel', 'config.json');
      return require(userConfigPath);
    } catch (error) {
      return {};
    }
  }
}
```

---

## 📈 Monitoring & Observability

### 📊 Metrics Collection

#### Performance Metrics
```javascript
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      requests: {
        total: 0,
        successful: 0,
        failed: 0,
        averageTime: 0
      },
      vulnerabilities: {
        found: 0,
        confirmed: 0,
        falsePositives: 0
      },
      resources: {
        memoryUsage: 0,
        cpuUsage: 0,
        activeConnections: 0
      }
    };
  }
  
  recordRequest(duration, success) {
    this.metrics.requests.total++;
    
    if (success) {
      this.metrics.requests.successful++;
    } else {
      this.metrics.requests.failed++;
    }
    
    // Расчет среднего времени
    const total = this.metrics.requests.averageTime * (this.metrics.requests.total - 1);
    this.metrics.requests.averageTime = (total + duration) / this.metrics.requests.total;
  }
  
  recordVulnerability(found, confirmed) {
    if (found) {
      this.metrics.vulnerabilities.found++;
    }
    
    if (confirmed) {
      this.metrics.vulnerabilities.confirmed++;
    }
  }
}
```

---

## 🔄 Extensibility Architecture

### 🔌 Plugin System

#### Plugin Interface
```typescript
interface Plugin {
  name: string;
  version: string;
  description: string;
  author: string;
  
  // Lifecycle методы
  initialize(): Promise<void>;
  destroy(): Promise<void>;
  
  // Extension точки
  getDetectors(): VulnerabilityDetector[];
  getValidators(): ValidationStage[];
  getReporters(): ReportGenerator[];
  
  // Конфигурация
  getDefaultConfig(): PluginConfig;
  validateConfig(config: PluginConfig): boolean;
}
```

#### Plugin Manager
```javascript
class PluginManager {
  constructor() {
    this.plugins = new Map();
    this.hooks = new Map();
  }
  
  async loadPlugin(pluginPath) {
    try {
      const PluginClass = require(pluginPath);
      const plugin = new PluginClass();
      
      // Валидация плагина
      if (!this.validatePlugin(plugin)) {
        throw new Error(`Invalid plugin: ${plugin.name}`);
      }
      
      // Инициализация плагина
      await plugin.initialize();
      
      // Регистрация компонентов
      this.registerPluginComponents(plugin);
      
      this.plugins.set(plugin.name, plugin);
      
      console.log(`✅ Plugin loaded: ${plugin.name} v${plugin.version}`);
    } catch (error) {
      console.error(`❌ Failed to load plugin: ${error.message}`);
    }
  }
  
  registerHook(name, handler) {
    if (!this.hooks.has(name)) {
      this.hooks.set(name, []);
    }
    this.hooks.get(name).push(handler);
  }
  
  async executeHook(name, data) {
    const handlers = this.hooks.get(name) || [];
    
    for (const handler of handlers) {
      try {
        await handler(data);
      } catch (error) {
        console.error(`Hook execution error: ${error.message}`);
      }
    }
    
    return data;
  }
}
```

---

## 📋 Заключение

Архитектура Prophecy Sentinel обеспечивает:

### ✨ Преимущества
- **Модульность** - независимые компоненты с четкими интерфейсами
- **Масштабируемость** - горизонтальное масштабирование
- **Отказоустойчивость** - graceful degradation при ошибках
- **Расширяемость** - плагинная архитектура
- **Безопасность** - многоуровневая защита
- **Производительность** - эффективное управление ресурсами

### 🎯 Технические характеристики
- **Event-driven архитектура** для асинхронной обработки
- **Микроядерный дизайн** для высокой модульности
- **Multi-stage validation** для повышения точности
- **Comprehensive monitoring** для полной наблюдаемости
- **Plugin system** для расширения функциональности

Эта архитектура позволяет Prophecy Sentinel быть мощной, гибкой и надежной платформой для оценки безопасности.
