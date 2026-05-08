# EVENT HORIZON - Руководство по устранению проблем

## 🚨 Общие проблемы

### Проблема: Docker контейнеры не запускаются

**Симптомы:**
```bash
docker-compose -f docker-compose-isolated.yml up
# Ошибка: Cannot start service ...
```

**Возможные причины:**
1. Порты уже заняты
2. Docker не запущен
3. Недостаточно памяти
4. Сеть Docker недоступна

**Решения:**

#### 1. Проверка занятых портов
```bash
# Проверка портов
lsof -i :8000
lsof -i :9000
lsof -i :3000
lsof -i :9090

# Если порты заняты, остановите процессы или измените порты в docker-compose.yml
```

#### 2. Проверка Docker
```bash
# Проверка статуса Docker
docker ps
docker-compose --version

# Перезапуск Docker
sudo systemctl restart docker  # Linux
# Или перезапустите Docker Desktop (Mac/Windows)
```

#### 3. Проверка памяти
```bash
# Проверка доступной памяти
free -h  # Linux
# Или проверьте через Docker Desktop

# Очистка неиспользуемых ресурсов
docker system prune -a
```

#### 4. Проверка сети Docker
```bash
# Проверка сетей Docker
docker network ls

# Пересоздание сети по умолчанию
docker network prune
```

---

### Проблема: Python зависимости не устанавливаются

**Симптомы:**
```bash
pip install -r requirements.txt
# Ошибка: Could not find a version that satisfies the requirement ...
```

**Возможные причины:**
1. Неправильная версия Python
2. Проблемы с pip
3. Сетевые проблемы
4. Конфликт зависимостей

**Решения:**

#### 1. Проверка версии Python
```bash
python --version  # Должен быть 3.11+

# Если версия неправильная, установите Python 3.11
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install python3.11

# Mac:
brew install python@3.11
```

#### 2. Обновление pip
```bash
python -m pip install --upgrade pip
```

#### 3. Использование виртуального окружения
```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

#### 4. Использование зеркал
```bash
# Если проблемы с сетью, используйте зеркало
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### Проблема: Тесты не выполняются

**Симптомы:**
```bash
python -m src.main --target http://mock-target:9000
# Ошибка: Target validation failed
```

**Возможные причины:**
1. Цель не изолирована
2. Mock-target недоступен
3. Проблемы с сетью
4. Неверная конфигурация

**Решения:**

#### 1. Проверка изоляции цели
```bash
# Валидация изолированной цели
python -m src.main --validate-isolation --target http://mock-target:9000

# Если не изолирована, используйте только изолированные цели:
# - localhost
# - 127.0.0.1
# - mock-target
# - event-horizon-mock
```

#### 2. Проверка доступности mock-target
```bash
# Проверка доступности
curl http://mock-target:9000/health

# Если недоступен, запустите контейнеры
docker-compose -f docker-compose-isolated.yml up -d
```

#### 3. Проверка сети
```bash
# Проверка сетевого соединения
docker network inspect isolated-lab-net

# Проверка DNS
docker exec event-horizon nslookup mock-target
```

#### 4. Проверка конфигурации
```bash
# Проверка конфигурационных файлов
cat config/event_horizon.yaml

# Проверка переменных окружения
env | grep EVENT_HORIZON
```

---

## 🔐 Проблемы с авторизацией

### Проблема: Авторизация не проходит валидацию

**Симптомы:**
```bash
python -m src.main --validate-authorization --target https://example.com
# Ошибка: Authorization validation failed
```

**Возможные причины:**
1. Отсутствуют документы авторизации
2. Документы неправильно заполнены
3. Цель не в authorised_targets.txt
4. Временное окно истекло

**Решения:**

#### 1. Проверка документов авторизации
```bash
# Проверка наличия документов
ls -la authorization/

# Должны быть:
# - authorization_letter.pdf
# - scope_of_engagement.pdf
# - authorized_targets.txt
# - contact_info.txt
# - authorization.json
```

#### 2. Проверка заполнения authorization.json
```bash
# Проверка формата JSON
cat authorization/authorization.json | jq .

# Проверка полей:
# - authorization_id
# - target_url (должен соответствовать цели)
# - status (должен быть "verified")
# - time_window (текущее время должно быть в окне)
```

#### 3. Проверка authorised_targets.txt
```bash
# Проверка списка авторизованных целей
cat authorization/authorized_targets.txt

# Убедитесь, что ваша цель в списке
echo "https://example.com" >> authorization/authorized_targets.txt
```

#### 4. Проверка временного окна
```bash
# Проверка текущего времени
date +%s

# Сравните с time_window в authorization.json
# Если окно истекло, обновите время
```

---

## 💾 Проблемы с производительностью

### Проблема: Медленное выполнение тестов

**Симптомы:**
- Тесты выполняются очень медленно
- Высокое использование CPU
- Большое время отклика

**Возможные причины:**
1. Недостаточно ресурсов
2. Слишком высокая нагрузка
3. Проблемы с сетью
4. Неоптимальная конфигурация

**Решения:**

#### 1. Проверка ресурсов
```bash
# Проверка использования ресурсов
docker stats

# Проверка логов
docker-compose -f docker-compose-isolated.yml logs event-horizon
```

#### 2. Уменьшение нагрузки
```yaml
# В конфигурационном файле:
execution:
  max_concurrent_requests: 50  # Уменьшите с 100
  rate_limit: 5.0              # Уменьшите с 10.0
```

#### 3. Оптимизация сети
```bash
# Проверка сетевой задержки
docker exec event-horizon ping mock-target

# Используйте локальную сеть вместо внешней
```

#### 4. Кэширование
```python
# Включите кэширование в конфигурации
observability:
  cache_enabled: true
  cache_ttl: 3600
```

---

### Проблема: Memory exhaustion

**Симптомы:**
- OOM Killer останавливает контейнеры
- Высокое использование памяти
- Система становится медленной

**Возможные причины:**
1. Слишком много запросов
2. Утечки памяти
3. Недостаточно памяти в системе
4. Неограниченный рост данных

**Решения:**

#### 1. Ограничение памяти
```yaml
# В docker-compose.yml:
services:
  event-horizon:
    mem_limit: 2g
    mem_reservation: 1g
```

#### 2. Уменьшение количества запросов
```yaml
# В конфигурационном файле:
execution:
  max_concurrent_requests: 25  # Уменьшите
  batch_size: 100               # Уменьшите
```

#### 3. Очистка данных
```bash
# Очистка старых логов
find logs/ -name "*.log" -mtime +7 -delete

# Очистка старых данных
find data/ -name "*.json" -mtime +30 -delete
```

#### 4. Мониторинг памяти
```python
# В коде добавьте мониторинг
import psutil

def check_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
        logger.warning("High memory usage detected")
```

---

## 📊 Проблемы с мониторингом

### Проблема: Grafana не показывает данные

**Симптомы:**
- Grafana пустой
- Нет метрик
- Дашборды не загружаются

**Возможные причины:**
1. Prometheus не работает
2. Неверная конфигурация источника данных
3. Проблемы с сетью
4. Неверные запросы

**Решения:**

#### 1. Проверка Prometheus
```bash
# Проверка доступности Prometheus
curl http://localhost:9090/api/v1/targets

# Проверка метрик
curl http://localhost:8080/metrics
```

#### 2. Проверка конфигурации Grafana
1. Откройте Grafana: http://localhost:3000
2. Перейдите в Configuration > Data Sources
3. Проверьте конфигурацию Prometheus
4. URL должен быть: http://prometheus:9090

#### 3. Проверка сети
```bash
# Проверка соединения между Grafana и Prometheus
docker exec grafana ping prometheus
```

#### 4. Перезагрузка сервисов
```bash
docker-compose -f docker-compose-isolated.yml restart prometheus grafana
```

---

### Проблема: Логи не записываются

**Симптомы:**
- Лог файлы пустые
- Нет новых записей
- Логи не вращаются

**Возможные причины:**
1. Нет прав на запись
2. Диск заполнен
3. Неверная конфигурация логирования
4. Проблемы с файловой системой

**Решения:**

#### 1. Проверка прав доступа
```bash
# Проверка прав на директорию логов
ls -la logs/

# Если нужно, измените права
chmod 755 logs/
```

#### 2. Проверка дискового пространства
```bash
# Проверка свободного места
df -h

# Очистка диска при необходимости
docker system prune -a
```

#### 3. Проверка конфигурации логирования
```yaml
# В конфигурационном файле:
observability:
  log_level: "INFO"
  log_file: "logs/event_horizon.log"
  log_rotation: true
  log_max_size: "100MB"
  log_max_files: 10
```

#### 4. Проверка файловой системы
```bash
# Проверка монтирования
df -h

# Проверка ошибок файловой системы
dmesg | grep -i error
```

---

## 🔧 Проблемы с конфигурацией

### Проблема: Конфигурация не загружается

**Симптомы:**
- Ошибка при загрузке конфигурации
- Используются значения по умолчанию
- Неверные настройки

**Возможные причины:**
1. Неверный формат YAML
2. Неверный путь к конфигурации
3. Синтаксические ошибки
4. Отсутствующие поля

**Решения:**

#### 1. Проверка формата YAML
```bash
# Валидация YAML
python -c "import yaml; yaml.safe_load(open('config/event_horizon.yaml'))"

# Или используйте yamllint
yamllint config/event_horizon.yaml
```

#### 2. Проверка пути к конфигурации
```bash
# Проверка существования файла
ls -la config/event_horizon.yaml

# Проверка переменной окружения
echo $EVENT_HORIZON_CONFIG
```

#### 3. Проверка синтаксиса
```yaml
# Убедитесь, что:
# - Отступы правильные (2 пробела)
# - Нет табов
# - Кавычки согласованы
# - Нет лишних пробелов
```

#### 4. Проверка обязательных полей
```yaml
# Проверьте наличие обязательных полей:
system:
  mode: "isolated"  # Обязательно

execution:
  max_concurrent_requests: 100  # Обязательно
  max_request_timeout: 30.0     # Обязательно
```

---

## 🚀 Проблемы с деплоем

### Проблема: Контейнеры не обновляются

**Симптомы:**
- Старая версия кода
- Изменения не применяются
- Кэширование образов

**Возможные причины:**
1. Docker кэширует образы
2. Неправильная команда сборки
3. Проблемы с volumes
4. Неправильная команда запуска

**Решения:**

#### 1. Пересборка без кэша
```bash
# Пересборка без кэша
docker-compose build --no-cache

# Пересборка конкретного сервиса
docker-compose build --no-cache event-horizon
```

#### 2. Пересоздание контейнеров
```bash
# Остановка и удаление контейнеров
docker-compose down

# Пересоздание volumes
docker-compose down -v

# Запуск с нуля
docker-compose up -d
```

#### 3. Проверка volumes
```bash
# Проверка volumes
docker volume ls

# Удаление старых volumes
docker volume rm windsurf-project_redis_data_isolated
```

#### 4. Принудительное обновление
```bash
# Принудительное обновление образов
docker-compose pull
docker-compose up -d --force-recreate
```

---

## 📞 Где получить дополнительную помощь

### Логи и отладка

```bash
# Просмотр всех логов
docker-compose -f docker-compose-isolated.yml logs

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose-isolated.yml logs event-horizon

# Просмотр логов в реальном времени
docker-compose -f docker-compose-isolated.yml logs -f

# Подключение к контейнеру
docker exec -it event-horizon bash
```

### Диагностика системы

```bash
# Проверка состояния системы
python -m src.main --validate-isolation --target http://mock-target:9000

# Проверка авторизации
python -m src.main --validate-authorization --target https://example.com

# Экспорт состояния системы
python -c "from architecture.formal_state_model import FormalStateModel; ..."
```

### Ресурсы

- **Документация**: `docs/`
- **Примеры**: `scenarios/`
- **GitHub Issues**: для баг-репортов
- **Email**: support@eventhorizon.example.com

---

## 🎯 Профилактика проблем

### Регулярное обслуживание

```bash
# Еженедельное обслуживание
docker system prune -f
docker volume prune -f
find logs/ -name "*.log" -mtime +7 -delete
find data/ -name "*.json" -mtime +30 -delete
```

### Мониторинг

```bash
# Регулярная проверка состояния
docker ps
docker stats
docker-compose -f docker-compose-isolated.yml ps
```

### Резервное копирование

```bash
# Резервное копирование конфигурации
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# Резервное копирование данных
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/
```

---

## 📋 Чек-лист диагностики

При возникновении проблем:

1. [ ] Проверьте логи
2. [ ] Проверьте состояние контейнеров
3. [ ] Проверьте использование ресурсов
4. [ ] Проверьте сетевое соединение
5. [ ] Проверьте конфигурацию
6. [ ] Проверьте права доступа
7. [ ] Проверьте дисковое пространство
8. [ ] Перезапустите сервисы
9. [ ] Пересоберите образы
10. [ ] Обратитесь за помощью
