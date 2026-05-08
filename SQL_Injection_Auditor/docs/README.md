# SQL Injection Auditor - Документация

## 🎯 Обзор

**SQL Injection Auditor** - это профессиональный инструмент для автоматизированного поиска уязвимостей SQL injection в веб-приложениях. Система включает enterprise-grade security controls, продвинутые техники evasion и comprehensive reporting capabilities.

## 📚 Навигация по Документации

### 🚀 Для Начинающих
- **[Руководство для Начинающих](BEGINNER_GUIDE_RU.md)** - Быстрый старт, базовая установка и первые шаги
  - Установка и настройка
  - Базовые команды сканирования
  - Понимание результатов
  - Этическое использование

### 🔧 Для Продвинутых Пользователей
- **[Руководство для Продвинутых](ADVANCED_GUIDE_RU.md)** - Расширенные возможности и конфигурация
  - Enterprise Security Mode
  - Custom payloads и техники WAF bypass
  - Продвинутая конфигурация
  - Оптимизация производительности

### 🏗️ Для Инженеров и Разработчиков
- **[Техническая Документация](ENGINEER_DOCUMENTATION_RU.md)** - Внутреннее устройство и архитектура
  - Системная архитектура
  - Модульная структура
  - API интеграция
  - Разработка расширений

### 🔐 Для Специалистов по Безопасности
- **[Архитектура Безопасности](SECURITY_ARCHITECTURE_RU.md)** - Enterprise security controls
  - PDP/PEP архитектура
  - Cryptographic audit chain
  - Execution isolation
  - Risk management

### 📖 Справочные Материалы
- **[API Reference](API_REFERENCE_RU.md)** - Полное описание API
  - Основные классы и методы
  - Примеры использования
  - Конфигурационные опции
  - Callback функции

- **[Техники SQL Injection](TECHNIQUES_TRAINING_RU.md)** - Обучающий материал по SQLi
  - Error-based injection
  - Boolean-based injection
  - Time-based injection
  - Union-based injection
  - Advanced techniques

## 🎯 Быстрый Старт

### 1. Базовая Установка
```bash
git clone <repository-url>
cd sql_injection_auditor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Первый Скан
```bash
# Пассивный режим (безопасный)
python main.py -u https://example.com --mode passive

# Активный режим (полный скан)
python main.py -u https://example.com --mode active
```

### 3. Просмотр Результатов
- JSON отчеты: `reports/scan_report_<timestamp>.json`
- PDF отчеты: `reports/scan_report_<timestamp>.pdf`

## 🔍 Основные Возможности

### 🛡️ Enterprise Security
- **Policy Decision Point (PDP)** - централизованное принятие решений
- **Policy Enforcement Point (PEP)** - enforcement security политик
- **Cryptographic Audit Chain** - tamper-evident логирование
- **Execution Isolation** - container-level изоляция

### 🎯 Детекция Уязвимостей
- **Error-Based SQLi** - анализ ошибок базы данных
- **Boolean-Based SQLi** - true/false response анализ
- **Time-Based SQLi** - temporal response анализ
- **Union-Based SQLi** - UNION query техники

### 🚀 Advanced Features
- **WAF Bypass** - обход Web Application Firewalls
- **Custom Payloads** - настраиваемые векторы атак
- **Parallel Processing** - многопоточный скан
- **Smart Crawling** - интеллектуальный краулинг

## 📊 Уровни Документации

| Уровень | Документация | Аудитория | Цель |
|--------|--------------|-----------|------|
| 🟢 **Beginner** | BEGINNER_GUIDE_RU.md | Новички | Быстрый старт |
| 🟡 **Advanced** | ADVANCED_GUIDE_RU.md | Опытные пользователи | Расширенные функции |
| 🟠 **Engineer** | ENGINEER_DOCUMENTATION_RU.md | Разработчики | Внутреннее устройство |
| 🔴 **Security** | SECURITY_ARCHITECTURE_RU.md | Security специалисты | Enterprise security |
| 📚 **Reference** | API_REFERENCE_RU.md | Все пользователи | API справочник |
| 🎓 **Training** | TECHNIQUES_TRAINING_RU.md | Обучение | SQLi техники |

## 🛠️ Конфигурация

### Базовый Config
```json
{
  "crawl_delay": 2.0,
  "crawl_depth": 2,
  "timeout": 30,
  "database_types": ["mysql", "postgresql"],
  "verify_vulnerabilities": true
}
```

### Enterprise Config
```json
{
  "enterprise_mode": true,
  "pdp_config": "pdp_config.json",
  "audit_chain_file": "audit_chain.db",
  "isolation_type": "container",
  "risk_thresholds": {
    "low": 3.0,
    "medium": 6.0,
    "high": 8.0
  }
}
```

## ⚠️ Важные Предупреждения

### ✅ Этическое Использование
- Сканируйте только сайты, которыми вы владеете
- Используйте только для образовательных целей
- Сообщайте о найденных уязвимостях владельцам

### ❌ Запрещено
- Использование для незаконных действий
- Сканирование сайтов без разрешения
- Использование найденных уязвимостей во вред

## 🆘 Поддержка и Помощь

### 📋 Поиск Решений
1. **Новички** - начните с [BEGINNER_GUIDE_RU.md](BEGINNER_GUIDE_RU.md)
2. **Проблемы с конфигурацией** - см. [ADVANCED_GUIDE_RU.md](ADVANCED_GUIDE_RU.md)
3. **Технические вопросы** - см. [ENGINEER_DOCUMENTATION_RU.md](ENGINEER_DOCUMENTATION_RU.md)
4. **Security проблемы** - см. [SECURITY_ARCHITECTURE_RU.md](SECURITY_ARCHITECTURE_RU.md)

### 🐛 Troubleshooting
- Проверьте логи в консоли
- Изучите отчеты в папке `reports/`
- Проверьте конфигурационные файлы
- Увеличьте timeout при проблемах с сетью

## 🎓 Путь Обучения

### Шаг 1: Основы
1. Прочтите **BEGINNER_GUIDE_RU.md**
2. Выполните базовую установку
3. Проведите первый скан на тестовом сайте

### Шаг 2: Продвинутые Техники
1. Изучите **ADVANCED_GUIDE_RU.md**
2. Настройте custom payloads
3. Освойте WAF bypass техники

### Шаг 3: Enterprise Level
1. Прочтите **SECURITY_ARCHITECTURE_RU.md**
2. Настройте PDP/PEP
3. Внедрите audit chain

### Шаг 4: Эксплуатация
1. Изучите **API_REFERENCE_RU.md**
2. Интегрируйте с CI/CD
3. Создайте custom модули

## 📈 Развитие Проекта

### 🔄 Версионирование
- **v1.0** - Базовый функционал
- **v2.0** - Enterprise security
- **v3.0** - Advanced evasion techniques

### 🚀 Будущие Возможности
- ML-based detection
- Real-time monitoring
- Cloud integration
- Advanced reporting

---

**Важно:** Этот инструмент создан для образовательных целей и легального тестирования безопасности. Используйте его ответственно )) и в соответствии с законодательством )))))).

*Последнее обновление: Май 2026*
