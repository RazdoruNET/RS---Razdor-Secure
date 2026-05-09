# 🟡 Обучающие материалы для среднего уровня

Продвинутые техники пентестинга и валидации с Prophecy Sentinel

---

## 📚 Содержание

### 🔍 Продвинутые техники обнаружения
- [Глубокий анализ SQL Injection](./advanced-sql-injection.md)
- [Blind SQL Injection](./blind-sql-injection.md)
- [Продвинутые XSS атаки](./advanced-xss.md)
- [Server-Side Template Injection](./ssti.md)

### 🎭 Техники валидации
- [Многостадийная валидация](./multi-stage-validation.md)
- [Playwright подтверждение](./playwright-validation.md)
- [Replay атаки](./replay-attacks.md)
- [Sink подтверждение](./sink-validation.md)

### 📊 Анализ и метрики
- [Анализ результатов](./results-analysis.md)
- [Метрики качества](./metrics-analysis.md)
- [False Negative тестирование](./false-negative-testing.md)
- [Регрессионное тестирование](./regression-testing.md)

### 🏗️ Бенчмаркинг
- [OWASP Benchmark](./owasp-benchmark.md)
- [DVWA валидация](./dvwa-validation.md)
- [Juice Shop тестирование](./juice-shop-testing.md)
- [Создание собственных бенчмарков](./custom-benchmarks.md)

---

## 🎯 Цели этого уровня

### 🔍 Продвинутые навыки обнаружения
- **Blind атаки** - обнаружение уязвимостей без прямых ответов
- **Time-based атаки** - использование временных задержек
- **Boolean-based атаки** - анализ истинности/ложности условий
- **Error-based атаки** - анализ сообщений об ошибках

### 🎭 Техники валидации
- **Эмпирическое подтверждение** - реальное выполнение эксплойтов
- **Многостадийная проверка** - комплексная валидация
- **Browser-based подтверждение** - использование Playwright
- **Sink анализ** - проверка достижения опасных точек

### 📊 Аналитические навыки
- **Метрики качества** - оценка эффективности обнаружения
- **False Negative анализ** - поиск пропущенных уязвимостей
- **Регрессионное тестирование** - отслеживание качества во времени
- **Статистический анализ** - оценка надежности результатов

---

## 🚀 Путь обучения

### Шаг 1: Продвинутые техники 🔍
1. [Изучите Blind SQL Injection](./blind-sql-injection.md)
2. [Освойте продвинутые XSS](./advanced-xss.md)
3. [Исследуйте SSTI](./ssti.md)

### Шаг 2: Валидация 🎭
1. [Настройте многостадийную валидацию](./multi-stage-validation.md)
2. [Используйте Playwright](./playwright-validation.md)
3. [Освойте sink подтверждение](./sink-validation.md)

### Шаг 3: Анализ 📊
1. [Анализируйте результаты](./results-analysis.md)
2. [Работайте с метриками](./metrics-analysis.md)
3. [Проводите регрессионное тестирование](./regression-testing.md)

---

## 🔍 Продвинутые техники обнаружения

### 🕵️ Blind SQL Injection

#### Time-based атаки
```sql
-- PostgreSQL
SELECT pg_sleep(5) WHERE condition;

-- MySQL
SELECT SLEEP(5) WHERE condition;

-- SQL Server
WAITFOR DELAY '00:00:05';
```

#### Boolean-based атаки
```sql
-- Условная инъекция
SELECT * FROM users WHERE id = 1 AND (SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a';

-- Использование CASE
SELECT CASE WHEN condition THEN 'true' ELSE 'false' END;
```

### 🎭 Продвинутые XSS

#### DOM-based XSS
```javascript
// Поиск DOM XSS
const sources = ['URL', 'location.hash', 'document.referrer'];
const sinks = ['innerHTML', 'outerHTML', 'document.write'];

// Анализ потока данных
sources.forEach(source => {
  sinks.forEach(sink => {
    // Проверка возможности data flow
  });
});
```

#### Self-XSS
```javascript
// Эксплуатация self-XSS
const payload = `<img src=x onerror=alert(document.domain)>`;
// Сохранение и последующее выполнение
```

---

## 📊 Метрики и KPI

### 🎯 Ключевые метрики
- **True Positive Rate** - процент правильных обнаружений
- **False Positive Rate** - процент ложных срабатываний
- **False Negative Rate** - процент пропущенных уязвимостей
- **Precision** - точность обнаружения
- **Recall** - полнота обнаружения

### 📈 Расчет метрик
```javascript
// Расчет метрик качества
function calculateMetrics(tp, fp, fn, tn) {
  const precision = tp / (tp + fp);
  const recall = tp / (tp + fn);
  const f1Score = 2 * (precision * recall) / (precision + recall);
  const accuracy = (tp + tn) / (tp + fp + fn + tn);
  
  return { precision, recall, f1Score, accuracy };
}
```

---

## 🎭 Практические примеры

### 🔍 Обнаружение Blind SQL Injection
```javascript
// Реализация time-based атаки
async function testTimeBasedSQL(url, parameter) {
  const payloads = [
    "1' AND SLEEP(5)--",
    "1' AND pg_sleep(5)--",
    "1' WAITFOR DELAY '00:00:05'--"
  ];

  for (const payload of payloads) {
    const startTime = Date.now();
    await makeRequest(url, 'POST', `${parameter}=${payload}`);
    const endTime = Date.now();
    
    if (endTime - startTime > 4000) {
      console.log(`🚨 Time-based SQL Injection detected: ${payload}`);
      return true;
    }
  }
  return false;
}
```

### 🎭 Playwright валидация XSS
```javascript
// Подтверждение XSS с помощью Playwright
async function confirmXSSWithPlaywright(url, payload) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Перехват alert
  let alertDetected = false;
  page.on('dialog', async dialog => {
    if (dialog.type() === 'alert') {
      alertDetected = true;
      await dialog.accept();
    }
  });
  
  await page.goto(url);
  await page.evaluate(`window.location.search = '?q=${payload}'`);
  
  await browser.close();
  return alertDetected;
}
```

---

## 📊 Бенчмаркинг

### 🧪 OWASP Benchmark
```javascript
// Запуск OWASP Benchmark тестов
async function runOWASPBenchmark() {
  const benchmark = require('../benchmark/OWASPBenchmarkRunner');
  const results = await benchmark.runValidation();
  
  console.log(`📊 OWASP Benchmark Results:`);
  console.log(`True Positive Rate: ${results.truePositiveRate}`);
  console.log(`False Positive Rate: ${results.falsePositiveRate}`);
  console.log(`Score: ${results.score}/100`);
}
```

### 🏗️ DVWA валидация
```javascript
// Валидация на DVWA
async function runDVWAValidation() {
  const dvwa = require('../benchmark/DVWAValidationRunner');
  const results = await dvwa.runValidation();
  
  console.log(`🎯 DVWA Validation Results:`);
  console.log(`Vulnerabilities Found: ${results.vulnerabilitiesFound}`);
  console.log(`Expected: ${results.expectedVulnerabilities}`);
  console.log(`Accuracy: ${results.accuracy}%`);
}
```

---

## 🛠️ Расширенная конфигурация

### ⚙️ Продвинутые настройки
```javascript
// Продвинутая конфигурация сканера
const sentinel = new ProphecySentinel();

// Настройки для продвинутого тестирования
sentinel.advancedConfig = {
  enableBlindAttacks: true,
  enableTimeBasedAttacks: true,
  enableBooleanBasedAttacks: true,
  maxPayloadLength: 1000,
  customPayloads: [
    // Custom payloads for specific environments
  ]
};

// Настройки валидации
sentinel.validationConfig = {
  enablePlaywrightValidation: true,
  enableReplayValidation: true,
  enableSinkValidation: true,
  validationThreshold: 0.8
};
```

### 🎭 Конфигурация Playwright
```javascript
// Расширенная конфигурация Playwright
const playwrightConfig = {
  headless: false, // Для отладки
  slowMo: 100,    // Замедление для наблюдения
  viewport: { width: 1920, height: 1080 },
  userAgent: 'ProphecySentinel/1.0 Advanced Scanner',
  ignoreHTTPSErrors: true
};
```

---

## 📈 Анализ результатов

### 📊 Визуализация метрик
```javascript
// Создание графика метрик
function visualizeMetrics(metrics) {
  const data = [
    { metric: 'Precision', value: metrics.precision },
    { metric: 'Recall', value: metrics.recall },
    { metric: 'F1 Score', value: metrics.f1Score }
  ];
  
  console.log('📊 Метрики качества:');
  data.forEach(item => {
    const bar = '█'.repeat(Math.round(item.value * 10));
    console.log(`${item.metric}: ${bar} ${(item.value * 100).toFixed(1)}%`);
  });
}
```

### 📈 Трендовый анализ
```javascript
// Анализ трендов качества
function analyzeTrends(results) {
  const trend = calculateTrend(results);
  const trendDescription = getTrendDescription(trend);
  
  console.log(`📈 Тренд качества: ${trendDescription}`);
  console.log(`Изменение: ${trend > 0 ? '+' : ''}${trend.toFixed(2)}%`);
}
```

---

## 💡 Советы для среднего уровня

### 🔍 Оптимизация обнаружения
- Используйте кастомные payloads для специфических технологий
- Комбинируйте различные техники атаки
- Анализируйте контекст для повышения точности
- Используйте timing атаки для blind уязвимостей

### 🎭 Улучшение валидации
- Настраивайте Playwright для специфических сценариев
- Используйте replay тесты для проверки стабильности
- Внедряйте sink анализ для подтверждения эксплойтов
- Создавайте собственные метрики валидации

### 📊 Работа с метриками
- Ведите историю всех сканирований
- Сравнивайте результаты с бенчмарками
- Используйте статистический анализ для оценки надежности
- Создавайте дашборды для визуализации

---

## 🎯 Следующие шаги

После освоения среднего уровня:

1. 🚀 Изучите [продвинутые техники](../advanced/README.md)
2. 📊 Практикуйтесь с [бенчмаркингом](./owasp-benchmark.md)
3. 🎭 Освойте [эксплуатацию](../advanced/exploitation.md)

---

## 🤝 Сообщество

### 💬 Обсуждение продвинутых техник
- **GitHub Discussions**: [Advanced Techniques](https://github.com/prophecy-sentinel/prophecy-sentinel/discussions/categories/advanced)
- **Research Papers**: [Security Research](https://github.com/prophecy-sentinel/prophecy-sentinel/wiki/research)
- **Case Studies**: [Real-world Examples](https://github.com/prophecy-sentinel/prophecy-sentinel/wiki/case-studies)

---

## ⚠️ Важное напоминание

**Продвинутые техники требуют ответственности!**

- ✅ Используйте только на авторизованных целях
- ✅ Тестируйте в изолированных средах
- ✅ Документируйте все находки
- ❌ Не используйте для вредоносных целей

---

## 🎯 Готовы к продвинутому уровню?

Если вы освоили все техники среднего уровня:

- ✅ Понимаете blind атаки
- ✅ Используете многостадийную валидацию
- ✅ Работаете с метриками качества
- ✅ Проводите бенчмаркинг

**Переходите к [продвинутому уровню](../advanced/README.md)!** 🚀

---

*Продвинутый уровень требует глубокого понимания безопасности и ответственности. Используйте знания мудро!*
