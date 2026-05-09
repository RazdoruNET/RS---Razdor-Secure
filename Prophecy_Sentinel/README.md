# 🛡️ Prophecy Sentinel

Профессиональная система оценки безопасности с эмпирической валидацией и подтверждением эксплойтов

---

## 📋 Навигация по документации

### 🚀 Быстрый старт
- [Установка и базовое использование](./docs/beginner/installation.md)
- [Первое сканирование](./docs/beginner/first-scan.md)
- [Основы безопасности](./docs/beginner/security-basics.md)

### 📚 Обучающие материалы
- **🟢 Новичкам**: [Основы пентестинга](./docs/beginner/README.md)
- **🟡 Средний уровень**: [Продвинутые техники](./docs/intermediate/README.md)
- **🔴 Профессионалам**: [Эксплуатация и валидация](./docs/advanced/README.md)

### 🔧 Техническая документация
- [Архитектура системы](./docs/technical/architecture.md)
- [API Reference](./docs/technical/api-reference.md)
- [Конфигурация](./docs/technical/configuration.md)
- [Разработка модулей](./docs/technical/module-development.md)

---

## 🎯 Краткий обзор

Prophecy Sentinel - это продвинутая система оценки безопасности, которая трансформирует традиционный сканер уязвимостей в **валидационный движок** с эмпирическим подтверждением эксплойтов.

### 🎯 Ключевые возможности

- **Эмпирическая валидация** - тестирование на реальных уязвимых приложениях (DVWA, Juice Shop)
- **Подтверждение эксплойтов** - многостадийная проверка уязвимостей с помощью Playwright
- **Регрессионное тестирование** - отслеживание качества обнаружения во времени
- **Бенчмаркинг** - интеграция с OWASP Benchmark для метрик качества
- **Без эмуляций** - только реальная работа кода и реальные тесты

## 🚀 Быстрый старт

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/prophecy-sentinel/prophecy-sentinel.git
cd prophecy-sentinel

# Установка зависимостей
npm install

# Установка Playwright браузеров
npx playwright install
```

### Базовое использование

```bash
# Запуск сканирования
node ProphecySentinel.js vk.com

# Запуск с TypeScript
npm run dev vk.com
```

## 📊 Архитектура

```
Prophecy Sentinel/
├── ProphecySentinel.js          # Основной сканер
├── src/
│   ├── types/                   # TypeScript типы
│   ├── core/                    # Ядро системы
│   ├── benchmark/               # Бенчмаркинг
│   ├── confirmation/            # Подтверждение уязвимостей
│   └── testing/                 # Тестирование и регрессия
├── docker-compose.*.yml        # Docker конфигурации
└── package.json                # Зависимости
```

## 🔍 Модули обнаружения

### Встроенные детекторы

- **SQL Injection** - продвинутое обнаружение с тайминг-анализом
- **XSS** - отраженный, хранимый и DOM-based XSS
- **Directory Traversal** - безопасное тестирование путей
- **File Inclusion** - LFI/RFI с PHP обертками
- **Security Headers** - анализ заголовков безопасности

### Методы обнаружения

- **Response Diffing** - анализ различий ответов
- **Timing Analysis** - обнаружение по времени отклика
- **Content Analysis** - эвристики контента
- **Pattern Matching** - регулярные выражения
- **Behavioral Analysis** - анализ поведения приложения

## 🎭 Подтверждение уязвимостей

### Multi-Stage Confirmation

1. **Sink Confirmation** - проверка достижения опасных точек
2. **Replay Validation** - проверка воспроизводимости
3. **Playwright Execution** - браузерное подтверждение XSS

### Пример использования

```javascript
const { PlaywrightXSSConfirmation } = require('./src/confirmation/PlaywrightXSSConfirmation');

const xssConfirm = new PlaywrightXSSConfirmation();
await xssConfirm.initialize();

const result = await xssConfirm.confirmXSS(
  'https://target.com/search',
  '<script>alert(1)</script>',
  'query'
);

console.log(`XSS подтвержден: ${result.confirmed}`);
await xssConfirm.cleanup();
```

## 🧪 Бенчмаркинг

### DVWA (Damn Vulnerable Web Application)

```bash
# Запуск DVWA бенчмаркинга
npm run benchmark:dvwa
```

### Juice Shop

```bash
# Запуск Juice Shop бенчмаркинга
npm run benchmark:juiceshop
```

### OWASP Benchmark

```bash
# Запуск OWASP Benchmark
npm run benchmark:owasp
```

## 📈 Метрики качества

### False Negative Testing

```javascript
const { FalseNegativeTesting } = require('./src/testing/FalseNegativeTesting');

const fnTesting = new FalseNegativeTesting();
const metrics = await fnTesting.runFalseNegativeTests(scanner);

console.log(`False Negative Rate: ${metrics.falseNegativeRate * 100}%`);
```

### Regression Suite

```javascript
const { RegressionSuite } = require('./src/testing/RegressionSuite');

const regression = new RegressionSuite();
await regression.establishBaseline(scanner);
const results = await regression.runRegressionTests(scanner);
```

## 🔧 Конфигурация

### Настройки сканера

```javascript
const sentinel = new ProphecySentinel();

// Настройка параметров
sentinel.concurrencyLimit = 5;
sentinel.rateLimitDelay = 1000;
sentinel.requestTimeout = 10000;
sentinel.maxRetries = 3;
```

### Пороги уверенности

```javascript
// Консервативный порог для уменьшения ложных срабатываний
sentinel.confidenceThreshold = 0.5;
```

## 📊 Отчетность

### Форматы отчетов

- **JSON** - структурированные данные
- **HTML** - интерактивные отчеты
- **PDF** - готовые документы
- **JIRA** - интеграция с таск-трекером

### Метрики CVSS

```javascript
const cvssScores = sentinel.calculateCVSSScores();
console.log(`Overall Risk Score: ${cvssScores.overall}/10.0`);
```

## 🛡️ Безопасность

### Гарантии безопасности

- ✅ **Локальность выполнения** - весь анализ локально
- ✅ **Отсутствие телеметрии** - нет отправки данных
- ✅ **Режим только чтения** - автоматический запрет изменений
- ✅ **Изолированный контур** - SQL-код не покидает среду

### Контроль доступа

- ✅ **Ручной запуск** - анализ только по команде
- ✅ **Подтверждение действий** - требуется подтверждение
- ✅ **Белый список** - доверенные рабочие пространства
- ✅ **Блокировка фонового анализа** - запрещен авто-анализ

## 📝 Использование

### Разрешенные сценарии

- **Внутренний аудит** - проверка корпоративных проектов
- **Локальная отладка** - отладка в изолированной среде
- **Проверка своих модулей** - анализ собственного кода
- **Анализ репозиториев** - проверка внутри доверенного контура

### Запрещенные сценарии

- ❌ Анализ сторонних сайтов без разрешения
- ❌ Тестирование чужой инфраструктуры
- ❌ Сканирование публичных баз данных
- ❌ Несанкционированное тестирование

## 🤝 Contributing

1. Fork проекта
2. Создание feature branch
3. Commit изменений
4. Push в branch
5. Создание Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE

## 🆘 Поддержка

- **Issues**: [GitHub Issues](https://github.com/prophecy-sentinel/prophecy-sentinel/issues)
- **Documentation**: [Wiki](https://github.com/prophecy-sentinel/prophecy-sentinel/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/prophecy-sentinel/prophecy-sentinel/discussions)

---

**⚠️ Важно**: Используйте только на системах, которым вы владеете. Несанкционированное тестирование нарушает закон.
