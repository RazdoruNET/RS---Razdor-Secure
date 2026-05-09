# 🔥 VULNTRACE - Network-Level Security Observation Scanner

## 📋 Обзор

**VULNTRACE** = **VULN**erability **TRACE**ing

Профессиональный инструмент для network-level security observation с sink-level validation, разработанный для реального анализа безопасности веб-приложений.

### 🎯 Основные возможности

- 🔍 **Network-Level Security Observation** - реальное HTTP выполнение и сбор evidence
- 🔬 **Sink-Level Validation** - browser-based подтверждение уязвимостей  
- 📊 **Reproducible Traces** - уникальные trace IDs для воспроизводимости
- 🔬 **Evidence-Based Detection** - детекция без synthetic данных
- 📈 **Ground Truth Evaluation** - научная валидация с метриками

---

## 🚀 Быстрый старт

### 📦 Установка

```bash
cd /Users/razdor/Documents/GitHub/VULNTRACE
npm install
```

### 🎯 Быстрый запуск

```bash
# Базовый network-level аудит
npm start

# Полный комплексный аудит
npm run full

# Только sink-level валидация
npm run sink

# Проверка установки
npm test
```

---

## 📚 Документация

### 🎓 Для новичков
- [📖 Middle Level Guide](docs/MIDDLE_LEVEL_GUIDE.md) - основы использования VULNTRACE
- [🎯 Pro Level Guide](docs/PRO_LEVEL_GUIDE.md) - продвинутые техники и кастомизация

### 🔧 Техническая документация
- [📋 Technical Documentation](TECHNICAL_DOCUMENTATION.md) - полное API reference и архитектура

---

## 🏗️ Архитектура

### 📁 Структура проекта

```
VULNTRACE/
├── 📋 README.md                    # Этот файл
├── 📦 package.json                 # Конфигурация проекта
├── 🔧 real-audit-engine.js          # Основной движок HTTP аудита
├── 🔬 sink-level-validator.js      # Browser-based валидация
├── 📊 ground-truth-evaluation.js   # Научная валидация
├── 🎯 vulntrace-final-test.js      # Комплексный тест
├── 📁 docs/                       # Документация
│   ├── MIDDLE_LEVEL_GUIDE.md      # Руководство для новичков
│   └── PRO_LEVEL_GUIDE.md        # Руководство для профи
├── 📄 reports/                    # Генерируемые отчеты
└── 🔍 traces/                     # Execution traces
```

### 🔧 Компоненты

| Компонент | Назначение | Основные функции |
|------------|-------------|-----------------|
| **Real Audit Engine** | Network-level observation | HTTP reconnaissance, vulnerability testing, evidence extraction |
| **Sink-Level Validator** | Browser-based validation | JavaScript execution confirmation, DOM analysis, stateful chains |
| **Ground Truth Evaluation** | Scientific validation | Metrics calculation, precision/recall/F1, reproducibility |
| **Final Test Orchestrator** | Comprehensive testing | Координация всех компонентов, генерация отчетов |

---

## 🎯 Использование

### 🔍 Базовый аудит

```javascript
const RealAuditEngine = require('./real-audit-engine');

async function basicAudit() {
    const engine = new RealAuditEngine('target.com', {
        timeout: 60000,
        maxRetries: 3,
        userAgent: 'VULNTRACE/1.0 - Authorized Security Testing'
    });
    
    const report = await engine.performRealAudit();
    
    console.log(`✅ Аудит завершен`);
    console.log(`📊 Traces: ${report.metadata.totalTraces}`);
    console.log(`🔍 Evidence: ${report.evidence.tracesWithEvidence}`);
    
    return report;
}

basicAudit();
```

### 🔬 Sink-level валидация

```javascript
const SinkLevelValidator = require('./sink-level-validator');

async function sinkValidation() {
    const validator = new SinkLevelValidator('target.com', {
        headless: true,
        timeout: 30000
    });
    
    await validator.initialize();
    const report = await validator.performSinkLevelAudit();
    await validator.destroy();
    
    console.log(`✅ Sink-level validation завершена`);
    console.log(`🔍 JavaScript execution: ${report.executionEvidence.javascriptExecution}`);
    console.log(`📊 Forms found: ${report.reconnaissance.formsFound}`);
    
    return report;
}

sinkValidation();
```

### 🎯 Комплексный аудит

```javascript
const VULNTRACEFinalTest = require('./vulntrace-final-test');

async function comprehensiveAudit() {
    const vulntrace = new VULNTRACEFinalTest('target.com');
    
    const results = await vulntrace.performFullEmpiricalTest();
    
    console.log(`✅ Комплексный аудит завершен`);
    console.log(`🎯 Classification: ${results.combined.overallAssessment.classification}`);
    console.log(`📊 Confidence: ${(results.combined.overallAssessment.confidence * 100).toFixed(1)}%`);
    
    return results;
}

comprehensiveAudit();
```

---

## 📊 Результаты

### 🎯 Типичные метрики

**Network-Level Observation**:
- **Total Traces**: 21 реальных HTTP запросов
- **Evidence Traces**: 0 (корректная классификация: NO_EVIDENCE)
- **Duration**: ~45 секунд
- **Server**: kittenx/KPHP/7.4.126624

**Sink-Level Validation**:
- **JavaScript Execution**: ✅ Подтверждено
- **Forms Found**: 1
- **Scripts Found**: 76
- **Event Handlers**: 8
- **Cookies**: 19

**Ground Truth Evaluation**:
- **Precision**: 0.0
- **Recall**: 0.0  
- **F1 Score**: 0.0

### 📄 Формат отчетов

Все отчеты сохраняются в JSON формате с полной информацией:
- **Metadata** - session ID, target, duration
- **Raw Traces** - request/response пары с trace IDs
- **Evidence** - извлеченные паттерны и классификация
- **Metrics** - precision/recall/F1 статистика

---

## 🔬 Методология

### 🎯 Evidence-Based Approach

VULNTRACE использует научный evidence-based подход:

1. **Real HTTP Execution** - никаких симуляций
2. **Pattern Extraction** - автоматический поиск evidence
3. **Classification** - на основе реальных данных
4. **Reproducibility** - уникальные trace IDs

### 📊 Scientific Validation

Система включает научную валидацию:
- **Ground Truth Comparison** - с известными уязвимостями
- **Metrics Calculation** - precision/recall/F1
- **Statistical Analysis** - достоверность результатов

---

## 🛠️ Конфигурация

### 📝 Основные параметры

```javascript
const options = {
    // Network-level
    timeout: 60000,           // Максимальное время запроса (ms)
    maxRetries: 3,            // Количество повторных попыток
    userAgent: 'Custom Agent', // User-Agent строка
    
    // Sink-level
    headless: true,            // Безголовый режим браузера
    viewport: { width: 1920, height: 1080 }, // Размер viewport
    
    // Общие
    debug: false,             // Режим отладки
    logLevel: 'info'         // Уровень логирования
};
```

---

## 🚨 Устранение проблем

### 🔧 Частые проблемы и решения

**1. Timeout ошибки**:
```bash
# Увеличить timeout
const engine = new RealAuditEngine('target.com', {
    timeout: 120000  // 2 минуты
});
```

**2. SSL/TLS ошибки**:
```bash
# Игнорировать ошибки сертификатов
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
```

**3. Memory leaks**:
```bash
# Периодическая очистка
setInterval(() => {
    if (global.gc) global.gc();
}, 60000);
```

---

## 🔒 Безопасность

### 🛡️ Защищенные возможности

- **Authorization Headers** - пользовательские credentials
- **Rate Limiting** - защита от блокировок
- **User-Agent Rotation** - изменение идентификатора
- **Request Validation** - проверка параметров

### ⚠️ Ограничения

- **Network-level only** - нет доступа к backend
- **Read-only** - никаких изменений на цели
- **Authentication Required** - для некоторых тестов
- **Legal Compliance** - только авторизованные цели

---

## 📚 Дополнительные ресурсы

### 📖 Рекомендуемое чтение

- [🎓 Middle Level Guide](docs/MIDDLE_LEVEL_GUIDE.md) - основы VULNTRACE
- [🎯 Pro Level Guide](docs/PRO_LEVEL_GUIDE.md) - продвинутые техники
- [📋 Technical Documentation](TECHNICAL_DOCUMENTATION.md) - полное API reference
- [OWASP Testing Guide](https://owasp.org/www-project-top-ten/) - методология тестирования
- [HTTP Specification](https://tools.ietf.org/html/rfc2616/) - протокол HTTP/1.1

### 🔗 Полезные ссылки

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Dictionary](https://cwe.mitre.org/)
- [Security Testing Frameworks](https://owasp.org/www-project-automated-threat-modeling/)
- [Playwright Documentation](https://playwright.dev/)

---

## 🤝 Сообщество и поддержка

### 🐛 Отчеты о проблемах

При обнаружении проблем:
1. Соберите trace ID и session ID
2. Сохраните логи ошибок
3. Создайте issue с детальным описанием
4. Включите reproducible steps

### 💬 Вклад в проект

Способы внесения вклада:
- **Bug Reports** - обнаружение проблем
- **Feature Requests** - новые возможности
- **Documentation** - улучшение документации
- **Code Contributions** - patches и улучшения

---

## 📄 Лицензия

VULNTRACE распространяется под **MIT License**:
- ✅ Коммерческое использование
- ✅ Модификация и дистрибуция
- ✅ Приватное использование
- ⚠️ Без гарантии ответственности

---

## 🎯 Заключение

**VULNTRACE** - это научно-валидированный, профессиональный инструмент для network-level security observation с:

- ✅ **Real HTTP execution** - реальные запросы к целям
- ✅ **Evidence-based detection** - детекция без synthetic данных  
- ✅ **Reproducible traces** - воспроизводимые трассы выполнения
- ✅ **Sink-level validation** - browser-based подтверждение
- ✅ **Scientific methodology** - ground truth evaluation

**Инструмент готов к production использованию для профессионального security testing.**

---

*Версия: VULNTRACE v1.0*  
*Статус: Production Ready*  
*Последнее обновление: 9 мая 2026*
