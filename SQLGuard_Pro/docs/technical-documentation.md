# Техническая документация SQLGuard Pro

## Содержание

1. [Архитектура системы](#архитектура-системы)
2. [Компоненты](#компоненты)
3. [Алгоритмы анализа](#алгоритмы-анализа)
4. [Интеграция с IDE](#интеграция-с-ide)
5. [Безопасность](#безопасность)
6. [Производительность](#производительность)
7. [API](#api)
8. [Конфигурация](#конфигурация)

## Архитектура системы

### Обзор архитектуры

SQLGuard Pro построен на микроядерной архитектуре с событийно-ориентированным дизайном:

```
┌─────────────────────────────────────────────────────────────┐
│                    SQLGuard Pro                        │
├─────────────────────────────────────────────────────────────┤
│  Cascade Integration Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   UI/IDE    │  │  Commands   │  │  Events     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  Core Analysis Engine                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Parser   │  │  Analyzer   │  │  Detector   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  Security & Monitoring                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Network   │  │   Audit     │  │  Ethics     │    │
│  │  Monitor    │  │   Logger    │  │  Manager    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  External Services                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  GPT AI     │  │   Reports   │  │  Storage    │    │
│  │  Analyzer    │  │ Generator   │  │  Manager    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Принципы проектирования

1. **Модульность** - каждый компонент независим и может быть заменен
2. **Событийность** - все взаимодействия через события
3. **Безопасность** - многоуровневая защита данных
4. **Расширяемость** - плагинная архитектура
5. **Производительность** - асинхронная обработка

## Компоненты

### 1. Cascade Integration Layer

#### CascadeIntegration.ts
Основной класс интеграции с Cascade SWE-1.5

```typescript
export class CascadeIntegration implements IDEIntegration {
  private scanner: SQLVulnerabilityScanner;
  private decorations: Map<string, any[]>;
  private tooltipProvider: any;
  private commandProvider: any;
  private statusBarItem: any;

  // IDE Integration methods
  highlightVulnerabilities(vulnerabilities: Vulnerability[]): void;
  showTooltip(vulnerability: Vulnerability): void;
  openFile(filePath: string, line: number, column: number): void;
  showReport(result: AnalysisResult): void;
  ignoreVulnerability(vulnerabilityId: string): void;
}
```

**Ключевые возможности:**
- Реальная подсветка уязвимостей в редакторе
- Интерактивные подсказки с рекомендациями
- Команды анализа файлов и рабочего пространства
- Генерация отчетов в различных форматах

### 2. Core Analysis Engine

#### SQLVulnerabilityScanner.ts
Основной движок сканирования

```typescript
export class SQLVulnerabilityScanner {
  private parser: SQLParser;
  private analyzer: StaticAnalyzer;
  private gptAnalyzer: GPTAnalyzer;
  private detector: VulnerabilityDetector;

  async analyzeFile(filePath: string, content: string): Promise<AnalysisResult>;
  async analyzeMultipleFiles(filePaths: string[]): Promise<AnalysisResult[]>;
  private async processQuery(query: SQLQuery): Promise<Vulnerability[]>;
}
```

**Процесс анализа:**
1. Парсинг SQL в AST (Abstract Syntax Tree)
2. Статический анализ по правилам
3. GPT анализ для сложных случаев
4. Агрегация результатов
5. Генерация рекомендаций

#### SQLParser.ts
Парсер SQL с поддержкой множества диалектов

```typescript
export class SQLParser {
  private adapters: Map<DatabaseType, DatabaseAdapter>;

  parse(sql: string, databaseType: DatabaseType): ParseResult;
  validateAST(ast: SQLAST): ValidationResult;
  normalizeQuery(query: string): string;
}
```

**Поддерживаемые базы данных:**
- MySQL 5.7+ (полная поддержка)
- PostgreSQL 10+ (включая CTE)
- MSSQL 2016+ (T-SQL особенности)
- Oracle 12c+ (PL/SQL конструкции)
- SQLite 3.x (мобильные приложения)

### 3. Security & Monitoring

#### NetworkMonitor.ts
Мониторинг сетевой активности

```typescript
export class NetworkMonitor extends EventEmitter {
  private blockedRequests: NetworkRequest[];
  private offlineMode: boolean;

  enableOfflineMode(): void;
  disableOfflineMode(): void;
  wrapHttpRequest(originalRequest: typeof http.request): typeof http.request;
  wrapHttpsRequest(originalRequest: typeof https.request): typeof https.request;
  wrapFetch(originalFetch: typeof global.fetch): typeof global.fetch;
}
```

**Функции безопасности:**
- Блокировка всех внешних запросов
- Логирование попыток соединений
- Автоматическое переключение в offline режим
- Защита от утечек данных

#### EthicalUsageManager.ts
Управление этическим использованием

```typescript
export class EthicalUsageManager {
  private acceptedTerms: boolean = false;
  private auditLogger: AuditLogger;

  async validateUsage(): Promise<boolean>;
  async showEthicalWarning(): Promise<boolean>;
  logUsage(action: string, metadata: any): void;
}
```

## Алгоритмы анализа

### 1. Статический анализ

#### Алгоритм обнаружения SQL Injection

```typescript
class SQLInjectionDetector {
  detect(query: SQLQuery): Vulnerability[] {
    const vulnerabilities: Vulnerability[] = [];
    
    // 1. Поиск конкатенации строк
    const concatenations = this.findStringConcatenations(query.ast);
    
    // 2. Анализ параметризации
    const unparameterized = this.findUnparameterizedQueries(query.ast);
    
    // 3. Проверка валидации входных данных
    const missingValidation = this.findMissingInputValidation(query.ast);
    
    // 4. Анализ динамического SQL
    const dynamicSQL = this.findDynamicSQL(query.ast);
    
    // 5. Генерация уязвимостей
    vulnerabilities.push(...this.generateVulnerabilities(
      concatenations, unparameterized, missingValidation, dynamicSQL
    ));
    
    return vulnerabilities;
  }
}
```

#### Алгоритм анализа производительности

```typescript
class PerformanceAnalyzer {
  analyze(query: SQLQuery): PerformanceIssue[] {
    const issues: PerformanceIssue[] = [];
    
    // 1. Анализ SELECT *
    const selectAll = this.findSelectAll(query.ast);
    
    // 2. Поиск отсутствия индексов
    const missingIndexes = this.findMissingIndexes(query.ast);
    
    // 3. Анализ JOIN операций
    const inefficientJoins = this.findInefficientJoins(query.ast);
    
    // 4. Проверка N+1 проблемы
    const nPlusOne = this.findNPlusOneProblem(query.ast);
    
    return issues;
  }
}
```

### 2. GPT анализ

#### Алгоритм контекстуального анализа

```typescript
class GPTAnalyzer {
  private openai: OpenAIApi;
  private promptTemplates: Map<string, string>;

  async analyzeWithContext(query: SQLQuery, context: AnalysisContext): Promise<GPTAnalysisResult> {
    // 1. Формирование контекста
    const contextData = this.buildContext(query, context);
    
    // 2. Выбор шаблона промпта
    const template = this.selectTemplate(query.type);
    
    // 3. Генерация промпта
    const prompt = this.generatePrompt(template, contextData);
    
    // 4. Запрос к GPT
    const response = await this.openai.chat.completions.create({
      model: "gpt-4",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.1
    });
    
    // 5. Парсинг ответа
    return this.parseGPTResponse(response.choices[0].message.content);
  }
}
```

## Интеграция с IDE

### Cascade SWE-1.5 Integration

#### Регистрация команд

```typescript
class CommandRegistry {
  registerCommands(): void {
    const commands = [
      {
        id: 'sqlScanner.analyzeCurrentFile',
        title: 'Analyze Current File',
        handler: () => this.analyzeCurrentFile()
      },
      {
        id: 'sqlScanner.analyzeWorkspace',
        title: 'Analyze Workspace',
        handler: () => this.analyzeWorkspace()
      },
      {
        id: 'sqlScanner.generateReport',
        title: 'Generate Report',
        handler: () => this.generateReport()
      }
    ];

    commands.forEach(cmd => this.registerCommand(cmd));
  }
}
```

#### Подсветка уязвимостей

```typescript
class VulnerabilityHighlighter {
  highlightVulnerabilities(vulnerabilities: Vulnerability[]): void {
    vulnerabilities.forEach(vuln => {
      const decoration = {
        range: new vscode.Range(
          new vscode.Position(vuln.line - 1, vuln.column - 1),
          new vscode.Position(vuln.line - 1, vuln.column - 1 + vuln.length)
        ),
        hoverMessage: this.createHoverMessage(vuln),
        color: this.getSeverityColor(vuln.severity)
      };

      this.editor.setDecorations(decoration.type, [decoration]);
    });
  }
}
```

## Безопасность

### Многоуровневая защита

#### 1. Network Layer
```typescript
class NetworkSecurityLayer {
  private monitor: NetworkMonitor;
  
  constructor() {
    this.monitor = new NetworkMonitor();
    this.monitor.enableOfflineMode(); // Force offline by default
  }
  
  validateRequest(url: string): boolean {
    // Block all external requests
    return false;
  }
}
```

#### 2. Data Layer
```typescript
class DataSecurityLayer {
  sanitizeInput(input: string): string {
    // Remove sensitive data patterns
    return input
      .replace(/password/i, '[REDACTED]')
      .replace(/secret/i, '[REDACTED]')
      .replace(/token/i, '[REDACTED]');
  }
  
  encryptLogData(data: any): string {
    // Encrypt sensitive log entries
    return this.encrypt(JSON.stringify(data));
  }
}
```

#### 3. Application Layer
```typescript
class ApplicationSecurityLayer {
  private ethicalManager: EthicalUsageManager;
  
  async validateAccess(): Promise<boolean> {
    // Check ethical usage agreement
    return await this.ethicalManager.validateUsage();
  }
  
  auditAction(action: string, metadata: any): void {
    // Log all actions for audit trail
    this.auditLogger.log(action, metadata);
  }
}
```

## Производительность

### Оптимизации

#### 1. Параллельная обработка
```typescript
class ParallelProcessor {
  async processFiles(files: string[]): Promise<AnalysisResult[]> {
    const chunks = this.chunkArray(files, this.getOptimalChunkSize());
    const results = await Promise.all(
      chunks.map(chunk => this.processChunk(chunk))
    );
    return results.flat();
  }
  
  private getOptimalChunkSize(): number {
    return Math.max(1, Math.floor(os.cpus().length / 2));
  }
}
```

#### 2. Кэширование результатов
```typescript
class ResultCache {
  private cache: Map<string, CachedResult>;
  
  async get(key: string): Promise<CachedResult | null> {
    const result = this.cache.get(key);
    if (result && !this.isExpired(result)) {
      return result;
    }
    return null;
  }
  
  async set(key: string, result: AnalysisResult): Promise<void> {
    this.cache.set(key, {
      result,
      timestamp: Date.now(),
      ttl: this.getTTL(result)
    });
  }
}
```

#### 3. Ленивая загрузка
```typescript
class LazyLoader {
  private loadedModules: Set<string>;
  
  async loadModule(moduleName: string): Promise<any> {
    if (!this.loadedModules.has(moduleName)) {
      const module = await import(moduleName);
      this.loadedModules.add(moduleName);
      return module;
    }
    return this.getLoadedModule(moduleName);
  }
}
```

## API

### Core API

#### SQLVulnerabilityScanner

```typescript
interface ISQLVulnerabilityScanner {
  // Основные методы
  analyzeFile(filePath: string, content: string): Promise<AnalysisResult>;
  analyzeMultipleFiles(filePaths: string[]): Promise<AnalysisResult[]>;
  generateReport(results: AnalysisResult[], format: ReportFormat): Promise<string>;
  
  // Конфигурация
  updateConfig(config: Partial<ScannerConfig>): void;
  getConfig(): ScannerConfig;
  
  // События
  on(event: 'analysisStart', callback: (file: string) => void): void;
  on(event: 'analysisComplete', callback: (result: AnalysisResult) => void): void;
  on(event: 'vulnerabilityFound', callback: (vulnerability: Vulnerability) => void): void;
}
```

#### AnalysisResult

```typescript
interface AnalysisResult {
  // Метаданные
  filePath: string;
  analysisType: AnalysisType;
  duration: number;
  timestamp: Date;
  
  // Результаты
  vulnerabilities: Vulnerability[];
  queries: SQLQuery[];
  statistics: AnalysisStatistics;
  
  // Дополнительная информация
  metadata: {
    databaseType: DatabaseType;
    scannerVersion: string;
    rulesVersion: string;
  };
}
```

#### Vulnerability

```typescript
interface Vulnerability {
  // Идентификация
  id: string;
  type: VulnerabilityType;
  severity: Severity;
  category: VulnerabilityCategory;
  
  // Описание
  title: string;
  description: string;
  recommendation: string;
  
  // Позиция
  filePath: string;
  line: number;
  column: number;
  length: number;
  
  // Контекст
  sqlQuery: string;
  context: string;
  confidence: number;
  
  // Стандарты
  cwe?: string;
  owasp?: string;
  references?: string[];
}
```

## Конфигурация

### ScannerConfig

```typescript
interface ScannerConfig {
  // Основные настройки
  databaseType: DatabaseType;
  securityLevel: 'strict' | 'moderate' | 'lenient';
  enableGPTAnalysis: boolean;
  enablePerformanceAnalysis: boolean;
  
  // Правила анализа
  enabledRules: string[];
  disabledRules: string[];
  customRules: CustomRule[];
  
  // Отчетность
  reportFormat: ReportFormat;
  includeStatistics: boolean;
  includeRecommendations: boolean;
  
  // Производительность
  maxConcurrentFiles: number;
  cacheEnabled: boolean;
  cacheTTL: number;
  
  // Безопасность
  offlineMode: boolean;
  auditLogging: boolean;
  dataRetention: number;
}
```

### CustomRule

```typescript
interface CustomRule {
  id: string;
  name: string;
  description: string;
  severity: Severity;
  category: VulnerabilityCategory;
  
  // Правило
  pattern: string | RegExp;
  databaseTypes: DatabaseType[];
  queryTypes: QueryType[];
  
  // Действие
  action: 'warn' | 'error' | 'info';
  recommendation: string;
  
  // Валидация
  validate: (query: SQLQuery) => boolean;
}
```

---

*Техническая документация SQLGuard Pro v1.0.0*
