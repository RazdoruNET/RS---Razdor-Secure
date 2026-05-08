# VK-COMPLIANCE-STRIKE

Комплексная система для автоматического анализа контента VK и подачи жалоб с целью защиты авторских прав и соблюдения правил сообщества.

## Архитектура

Система состоит из трех основных модулей:

### 1. LEGAL-MINING-VK
Модуль сканирования и анализа контента VK групп:
- **Поиск неоригинального контента**: Анализ хешей видео и фотографий для обнаружения дубликатов
- **Выявление нарушений ПДД/насилия**: Анализ текста на наличие опасных маневров и шокирующего контента
- **Обнаружение мошенничества**: Поиск продаж без официальных реквизитов

### 2. VK-REPORT-AUTOMATION
Модуль автоматической подачи жалоб:
- **API методы**: Использование `reports.report` для автоматической подачи жалоб
- **Браузерная автоматизация**: Selenium/Playwright для обхода фильтров
- **Ротация аккаунтов**: Сетка из 100+ VK-аккаунтов с имитацией активности
- **Приоритизация**: Основной упор на "Неоригинальный контент"

### 3. SUPPORT-PRESSURE
Модуль юридического давления:
- **DMCA претензии**: Автоматическая генерация и подача DMCA жалоб
- **Поддержка VK**: Автоматизация запросов в техподдержку
- **Брендовая защита**: Юридически обоснованные претензии от известных брендов

## Установка

### Требования
- Python 3.8+
- VK API токен
- Chrome/Chromium браузер (для Selenium)
- Список VK аккаунтов (для ротации)

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Установка Playwright
```bash
playwright install chromium
```

## Конфигурация

### 1. Основной конфигурационный файл
Скопируйте и настройте `config/vk_compliance_config.json`:

```json
{
  "vk": {
    "access_token": "your_vk_token_here",
    "group_id": "dsmotopro",
    "api_version": "5.199"
  },
  "analysis": {
    "max_posts_per_scan": 100,
    "hash_threshold": 0.95
  }
}
```

### 2. Настройка аккаунтов
Заполните `config/vk_accounts.json`:

```json
[
  {
    "login": "account1@gmail.com",
    "password": "password1",
    "user_id": "123456789",
    "is_active": true
  }
]
```

## Использование

### 1. Полный цикл Compliance
```bash
python main.py --mode full --posts 100
```

### 2. Только сканирование
```bash
python main.py --mode scan --posts 50
```

### 3. Только подача жалоб
```bash
python main.py --mode reports --violations-file violations.json
```

### 4. Расширенные опции
```bash
python main.py \
  --mode full \
  --posts 200 \
  --no-dmca \
  --no-tickets \
  --config custom_config.json
```

## API Использование

### Программное использование
```python
from main import VKComplianceStrike

# Инициализация
compliance = VKComplianceStrike("config/vk_compliance_config.json")

# Полный цикл
results = compliance.run_full_compliance_cycle(
    scan_posts=100,
    submit_reports=True,
    submit_dmca=True,
    submit_tickets=True
)

print(f"Найдено нарушений: {results['summary']['total_violations']}")
print(f"Подано жалоб: {results['summary']['reports_submitted']}")
```

### Отдельные модули
```python
from modules.legal_mining_vk import LegalMiningVK
from modules.vk_report_automation import VKReportAutomation
from modules.support_pressure import SupportPressure

# 1. Сканирование контента
miner = LegalMiningVK()
violations = miner.scan_group_wall()

# 2. Подача жалоб
automation = VKReportAutomation()
report_requests = automation.generate_report_requests(violations)
results = automation.submit_bulk_reports(report_requests)

# 3. DMCA претензии
pressure = SupportPressure()
claims = pressure.generate_brand_protection_claims(violations)
pressure.batch_submit_claims(claims)
```

## Структура результатов

### Результаты сканирования
```json
{
  "scan_timestamp": "2024-01-15T10:30:00",
  "total_violations": 15,
  "violations": [
    {
      "post_id": 123456,
      "post_url": "https://vk.com/wall-123456789_123456",
      "violation_type": "duplicate_content",
      "confidence": 0.95,
      "evidence": {"content_hash": "abc123..."}
    }
  ]
}
```

### Отчет о подаче жалоб
```json
{
  "total": 15,
  "successful": 12,
  "failed": 3,
  "errors": ["Rate limit exceeded"]
}
```

## Типы нарушений

### 1. Duplicate Content
- **Триггеры**: Совпадение хешей медиафайлов
- **Действие**: Жалоба "Неоригинальный контент"
- **Приоритет**: Высокий

### 2. Fraud/Scam
- **Триггеры**: Ключевые слова "продам", "цена", "договор"
- **Действие**: Жалоба "Спам/Мошенничество"
- **Приоритет**: Средний

### 3. Traffic Violence
- **Триггеры**: "ДТП", "авария", "нарушение ПДД"
- **Действие**: Жалоба "Насилие"
- **Приоритет**: Высокий

## Безопасность и анонимность

### Прокси ротация
```json
{
  "proxy": {
    "enabled": true,
    "rotation": true,
    "proxy_list": [
      "http://proxy1:8080",
      "socks5://proxy2:1080"
    ]
  }
}
```

### Имитация активности
- Автоматический просмотр поста перед жалобой
- Случайное время просмотра (5-15 секунд)
- Эмуляция скроллинга и мышиных движений

### Rate Limiting
- 5 минут между жалобами с одного аккаунта
- Ротация аккаунтов каждые 10 жалоб
- Случайные задержки между действиями

## Мониторинг и логирование

### Лог файлы
- `logs/legal_mining.log` - Сканирование контента
- `logs/vk_reports.log` - Подача жалоб
- `logs/support_pressure.log` - DMCA претензии
- `logs/vk_compliance_strike.log` - Общая статистика

### Метрики
- Успешность подачи жалоб (%)
- Количество найденных нарушений
- Активность аккаунтов
- Частота обнаружения дубликатов

## Устранение неполадок

### Частые проблемы

#### 1. "Invalid access token"
**Решение**: Проверьте VK токен в конфигурации

#### 2. "Rate limit exceeded"
**Решение**: Увеличьте `report_cooldown` в конфигурации

#### 3. "Account blocked"
**Решение**: Отключите аккаунт в `vk_accounts.json`

#### 4. Selenium не запускается
**Решение**: Установите ChromeDriver или используйте headless режим

### Отладка
```bash
# Включить debug логирование
export VK_COMPLIANCE_DEBUG=1

# Запуск с verbose выводом
python main.py --mode scan --posts 10 -v
```

## Юридические аспекты

### DMCA требования
- Полная идентификация правообладателя
- Точное указание нарушающего контента
- Контактная информация
- Заявление о добросовестности

### Соблюдение правил VK
- Максимальная имитация человеческого поведения
- Соблюдение rate limiting
- Использование легальных методов подачи жалоб

## Важные предупреждения

⚠️ **Используйте ответственно**
- Соблюдайте законодательство вашей страны
- Не используйте для незаконных целей
- Уважайте частную жизнь пользователей

⚠️ **Риски**
- Блокировка VK аккаунтов
- Юридические последствия
- Технические ограничения VK API

## Поддержка и развитие

### TODO
- [ ] Машинное обучение для анализа изображений
- [ ] Интеграция с Telegram для уведомлений
- [ ] Веб-интерфейс для мониторинга
- [ ] Расширенная аналитика и статистика

### Вклад
Для внесения изменений:
1. Fork репозиторий
2. Создайте feature branch
3. Отправьте pull request

### Лицензия
Этот проект предназначен исключительно для образовательных целей и исследовательского использования в рамках законодательства.

---

**Disclaimer**: Используйте данный модуль строго в соответствии с законодательством и правилами платформы VK. Разработчики не несут ответственности за неправомерное использование.
