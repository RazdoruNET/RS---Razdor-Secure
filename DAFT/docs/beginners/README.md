# DARF — Руководство для начинающих

**Defensive Authentication Resilience Framework**

## 🎯 Что такое DARF?

DARF — это инструмент для тестирования устойчивости систем авторизации к атакам и перегрузкам. Проще говоря — это "стресс-тест для сайтов авторизации".

## 🚀 Быстрый старт

### Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/your-repo/event_horizon_darf.git
cd event_horizon_darf

# Установите зависимости
pip install -r requirements.txt
```

### Запуск базового теста

```bash
# Запустите базовое тестирование
python main.py run

# Посмотрите доступные сценарии
python main.py list-scenarios

# Посмотрите доступные компоненты
python main.py list-components
```

### Запуск в Docker

```bash
# Соберите Docker образ
docker-compose build

# Запустите контейнеры
docker-compose up -d

# Посмотрите логи
docker logs event_horizon_audit -f
```

## 📚 Основные команды

### Команда: `run` — Запуск тестирования

```bash
# Базовый запуск
python main.py run

# С конкретным конфигом
python main.py run --config my_config.yaml

# С конкретными сценариями
python main.py run --scenarios baseline_performance high_load_stress

# Укажите папку для результатов
python main.py run --output my_results
```

### Команда: `list-scenarios` — Список сценариев

```bash
# Посмотреть все доступные сценарии
python main.py list-scenarios
```

### Команда: `list-components` — Список компонентов

```bash
# Посмотреть все компоненты
python main.py list-components

# Из конкретного файла
python main.py list-components --file custom_components.yaml
```

### Команда: `create-config` — Создание конфигурации

```bash
# Создать пример конфигурации
python main.py create-config
```

## 🔍 Что тестирует DARF?

DARF тестирует 4 основных слоя защиты:

### 1. NSL — Normalization Stress Layer
**Тестирует:** WAF и нормализацию UTF-8
- Малоформатные данные
- Переполненные UTF-8 последовательности
- Амбигуитные токены

### 2. SCS — Session Collapse Simulator  
**Тестирует:** Управление сессиями
- Массовое создание/удаление сессий
- Консистентность между stateless и stateful узлами
- Утечки сессий

### 3. RLPM — Rate Limit Pressure Module
**Тестирует:** Ограничение скорости запросов
- Всплески трафика
- Подделка IP-адресов
- Обход ограничений

### 4. DB-SIL — DB Stress Interface Layer
**Тестирует:** Базу данных
- Перегрузка connection pool
- Голодание транзакций
- Насыщение очереди запросов

## 📊 Как читать результаты?

После завершения тестирования DARF создаст отчёт в папке `results/`:

```
results/
├── assessment_report.json      # Основной отчёт
├── failure_topology.json       # Граф отказов
├── component_metrics.json      # Метрики компонентов
└── visualizations/             # Графики и визуализации
```

### Основные метрики

- **Resilience Score** — Общая оценка устойчивости (0-100)
- **Availability** — Доступность системы
- **Performance** — Производительность
- **Consistency** — Консистентность данных
- **Security** — Безопасность
- **Recovery** — Способность к восстановлению

## 🛠️ Примеры использования

### Пример 1: Базовое тестирование

```bash
# Запустите базовое тестирование
python main.py run

# Результаты будут в папке results/
```

### Пример 2: Тестирование конкретного сценария

```bash
# Тест только высокой нагрузки
python main.py run --scenarios high_load_stress
```

### Пример 3: Кастомный конфиг

```bash
# Создайте свой конфиг
python main.py create-config

# Отредактируйте config/default.yaml
# Запустите с вашим конфигом
python main.py run --config config/default.yaml
```

### Пример 4: Docker тестирование

```bash
# Запустите в Docker
docker-compose up -d

# Следите за логами
docker logs event_horizon_audit -f

# Остановите когда закончите
docker-compose down
```

## ⚠️ Важные предупреждения

### Используйте только с разрешением!

DARF — это инструмент для тестирования безопасности. Используйте его только:
- На своих системах
- С официальным разрешением владельца системы
- В образовательных целях

### Не злоупотребляйте

- Не тестируйте системы без разрешения
- Не создавайте чрезмерную нагрузку
- Соблюдайте законы вашей страны

## 🐛 Частые проблемы

### Проблема: "ModuleNotFoundError"

**Решение:** Установите зависимости
```bash
pip install -r requirements.txt
```

### Проблема: "Config file not found"

**Решение:** Создайте конфигурацию
```bash
python main.py create-config
```

### Проблема: Docker не запускается

**Решение:** Проверьте Docker
```bash
docker --version
docker-compose --version
```

## 📚 Следующие шаги

1. **Изучите сценарии** — `python main.py list-scenarios`
2. **Создайте свой конфиг** — `python main.py create-config`
3. **Протестируйте свою систему** — `python main.py run`
4. **Проанализируйте результаты** — Проверьте `results/`
5. **Изучите документацию для инженеров** — `docs/engineers/`

## 💡 Советы

- Начните с базового тестирования
- Используйте Docker для изоляции
- Сохраняйте результаты для сравнения
- Следите за логами в реальном времени
- Не перегружайте систему без необходимости

## 🆘 Нужна помощь?

- Проверьте документацию в `docs/`
- Посмотрите примеры в `config/`
- Изучите логи для диагностики проблем
- Создайте issue на GitHub если нашли баг

---

**Удачи в тестировании!** 🚀
