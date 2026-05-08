# DARF — Руководство по развертыванию

**Defensive Authentication Resilience Framework**

## 🚀 Требования к системе

### Минимальные требования

- **CPU:** 2 ядра
- **RAM:** 4 GB
- **Disk:** 10 GB свободного места
- **Python:** 3.8+
- **Docker:** 20.10+ (опционально)

### Рекомендуемые требования

- **CPU:** 4+ ядра
- **RAM:** 8+ GB
- **Disk:** 20+ GB SSD
- **Python:** 3.11+
- **Docker:** 24.0+

## 📦 Установка

### Вариант 1: Установка с pip

```bash
# Клонируйте репозиторий
git clone https://github.com/your-repo/event_horizon_darf.git
cd event_horizon_darf

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Установите пакет
pip install -e .
```

### Вариант 2: Установка с Docker

```bash
# Клонируйте репозиторий
git clone https://github.com/your-repo/event_horizon_darf.git
cd event_horizon_darf

# Соберите Docker образ
docker-compose build

# Запустите контейнеры
docker-compose up -d
```

### Вариант 3: Установка из исходников

```bash
# Клонируйте репозиторий
git clone https://github.com/your-repo/event_horizon_darf.git
cd event_horizon_darf

# Установите зависимости
pip install -r requirements.txt

# Установите пакет
python setup.py install
```

## ⚙️ Конфигурация

### Создание конфигурации

```bash
# Создайте пример конфигурации
python main.py create-config
```

Это создаст файлы:
- `config/default.yaml` — Основная конфигурация
- `config/components.yaml` — Конфигурация компонентов

### Редактирование конфигурации

#### Основная конфигурация (`config/default.yaml`)

```yaml
# Основные настройки
max_concurrent_requests: 100
test_timeout_seconds: 300
log_level: "INFO"
output_directory: "reports"
enable_visualizations: true

# Конфигурация NSL
nsl_config:
  enable_utf8_tests: true
  enable_unicode_tests: true
  malformed_payload_ratio: 0.3

# Конфигурация SCS
scs_config:
  max_sessions: 10000
  session_ttl: 3600
  cleanup_interval: 300

# Конфигурация RLPM
rlpm_config:
  ip_limit: 100
  user_limit: 50
  global_limit: 10000

# Конфигурация DB-SIL
dbsil_config:
  max_connections: 100
  query_timeout: 30
  connection_pool_size: 100

# Веса оценки
scoring_weights:
  availability: 0.25
  performance: 0.20
  consistency: 0.20
  security: 0.15
  recovery: 0.20
```

#### Конфигурация компонентов (`config/components.yaml`)

```yaml
components:
  - component_id: "waf"
    name: "Web Application Firewall"
    type: "waf"
    endpoint: "/waf"
    dependencies: []
    
  - component_id: "auth_service"
    name: "Authentication Service"
    type: "authentication"
    endpoint: "/auth"
    dependencies: ["waf"]
    
  - component_id: "session_manager"
    name: "Session Manager"
    type: "session"
    endpoint: "/session"
    dependencies: ["auth_service"]
```

### Конфигурация для security audit

Создайте файл `config/security_audit_config.yaml`:

```yaml
# Целевая система
target:
  domain: "example.com"
  protocol: "https"
  port: 443
  timeout: 30

# Область аудита
audit_scope:
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/login"
      method: "POST"
    - path: "/api"
      method: "GET"
  
  components:
    - waf
    - rate_limiter
    - session_manager
    - database
    - authentication

# Сценарии тестирования
test_scenarios:
  baseline:
    name: "Baseline performance"
    requests: 100
    rate: 10
    duration: 10
  
  stress:
    name: "Stress testing"
    requests: 1000
    rate: 100
    duration: 30

# Ограничения безопасности
security_constraints:
  max_requests_per_minute: 1000
  respect_robots_txt: true
  user_agent: "DARF-Security-Audit/1.0"
```

## 🐳 Развертывание в Docker

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f event-horizon

# Остановка сервисов
docker-compose down
```

### Отдельный контейнер

```bash
# Сборка образа
docker build -t darf:latest .

# Запуск контейнера
docker run -d \
  --name darf \
  -p 8080:8080 \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/config:/app/config \
  darf:latest

# Просмотр логов
docker logs -f darf

# Остановка контейнера
docker stop darf
docker rm darf
```

### Docker с мониторингом

```bash
# Запуск с Prometheus и Grafana
docker-compose up -d

# Доступ к сервисам
# Grafana: http://localhost:3000 (admin/event_horizon_secure)
# Prometheus: http://localhost:9090
# DARF: http://localhost:8080
```

## 🌐 Развертывание в Kubernetes

### Создание deployment

```yaml
# darf-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: darf
spec:
  replicas: 3
  selector:
    matchLabels:
      app: darf
  template:
    metadata:
      labels:
        app: darf
    spec:
      containers:
      - name: darf
        image: darf:latest
        ports:
        - containerPort: 8080
        env:
        - name: MAX_CONCURRENT_REQUESTS
          value: "100"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: results
          mountPath: /app/results
      volumes:
      - name: config
        configMap:
          name: darf-config
      - name: results
        persistentVolumeClaim:
          claimName: darf-results
```

### Создание service

```yaml
# darf-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: darf
spec:
  selector:
    app: darf
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Развертывание

```bash
# Применение конфигураций
kubectl apply -f darf-deployment.yaml
kubectl apply -f darf-service.yaml

# Проверка статуса
kubectl get pods
kubectl get services
```

## 🔧 Развертывание в продакшн

### Системные требования для продакшн

- **CPU:** 8+ ядер
- **RAM:** 16+ GB
- **Disk:** 50+ GB SSD
- **Network:** 1+ Gbps
- **High Availability:** Load balancer + multiple instances

### Настройка базы данных

```bash
# PostgreSQL для хранения результатов
docker run -d \
  --name darf-db \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=darf_results \
  -v darf-db-data:/var/lib/postgresql/data \
  postgres:15
```

### Настройка Redis для кэширования

```bash
# Redis для кэширования
docker run -d \
  --name darf-redis \
  -v darf-redis-data:/data \
  redis:7-alpine
```

### Настройка Nginx

```nginx
# nginx.conf
upstream darf_backend {
    server darf-1:8080;
    server darf-2:8080;
    server darf-3:8080;
}

server {
    listen 80;
    server_name darf.example.com;

    location / {
        proxy_pass http://darf_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

## 🔒 Безопасность развертывания

### SSL/TLS конфигурация

```bash
# Генерация SSL сертификатов
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/darf.key \
  -out /etc/ssl/certs/darf.crt
```

### Firewall настройки

```bash
# Разрешить только необходимые порты
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### Аутентификация

```yaml
# config/security.yaml
authentication:
  enabled: true
  method: "jwt"
  secret_key: "your-secret-key"
  token_expiry: 3600

authorization:
  enabled: true
  roles:
    - admin
    - operator
    - viewer
```

## 📊 Мониторинг

### Prometheus конфигурация

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'darf'
    static_configs:
      - targets: ['localhost:8080']
```

### Grafana дашборды

Импортируйте дашборды из `monitoring/grafana/dashboards/`:
- DARF Overview
- Performance Metrics
- Failure Analysis
- Component Health

### Логирование

```yaml
# config/logging.yaml
logging:
  level: "INFO"
  format: "json"
  outputs:
    - type: "console"
    - type: "file"
      path: "/var/log/darf/app.log"
    - type: "syslog"
      facility: "local0"
```

## 🚨 Резервное копирование

### Резервное копирование результатов

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/darf"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание бэкапа результатов
tar -czf $BACKUP_DIR/results_$DATE.tar.gz /app/results/

# Создание бэкапа конфигурации
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /app/config/

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Восстановление

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

# Восстановление результатов
tar -xzf $BACKUP_FILE -C /
```

## 🔧 Обслуживание

### Обновление

```bash
# Остановка сервисов
docker-compose down

# Обновление кода
git pull origin main

# Пересборка образов
docker-compose build

# Запуск сервисов
docker-compose up -d
```

### Масштабирование

```bash
# Масштабирование до 5 экземпляров
docker-compose up -d --scale event-horizon=5
```

### Очистка

```bash
# Очистка старых результатов
find results/ -type f -mtime +7 -delete

# Очистка Docker
docker system prune -a
```

## 🐛 Устранение проблем

### Проблема: Недостаточно памяти

**Решение:**
```bash
# Увеличение лимита памяти
export DARF_MEMORY_LIMIT=8g
docker-compose up -d
```

### Проблема: Медленная производительность

**Решение:**
```yaml
# Уменьшение конкурентности
max_concurrent_requests: 50
```

### Проблема: Connection timeout

**Решение:**
```yaml
# Увеличение timeout
test_timeout_seconds: 600
```

### Проблема: Docker контейнер не запускается

**Решение:**
```bash
# Проверка логов
docker logs event_horizon_audit

# Проверка статуса
docker-compose ps

# Пересборка образа
docker-compose build --no-cache
docker-compose up -d
```

## 📈 Оптимизация производительности

### Оптимизация базы данных

```sql
-- Создание индексов
CREATE INDEX idx_results_timestamp ON assessment_results(timestamp);
CREATE INDEX idx_results_component ON assessment_results(component_id);
```

### Оптимизация кэширования

```python
# config/cache.yaml
cache:
  enabled: true
  backend: "redis"
  ttl: 3600
  max_size: 10000
```

### Оптимизация сети

```bash
# Увеличение буферов
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
```

## 🧪 Тестирование развертывания

### Проверка работоспособности

```bash
# Запуск базового теста
python main.py run --scenarios baseline_performance

# Проверка результатов
ls -la results/
```

### Нагрузочное тестирование

```bash
# Запуск стресс-теста
python main.py run --scenarios high_load_stress
```

### Интеграционное тестирование

```bash
# Запуск интеграционных тестов
pytest tests/test_integration.py
```

## 📋 Чек-лист развертывания

### Перед развертыванием

- [ ] Проверены системные требования
- [ ] Установлены все зависимости
- [ ] Создана конфигурация
- [ ] Настроены права доступа
- [ ] Настроен firewall
- [ ] Настроен SSL/TLS
- [ ] Настроено резервное копирование
- [ ] Настроен мониторинг

### После развертывания

- [ ] Проверен статус сервисов
- [ ] Проверены логи
- [ ] Запущен базовый тест
- [ ] Проверена производительность
- [ ] Настроены алерты
- [ ] Документированы изменения
- [ ] Обучён персонал

## 🆘 Поддержка

### Логи

```bash
# Логи приложения
docker logs event_horizon_audit -f

# Логи системы
journalctl -u darf -f
```

### Диагностика

```bash
# Проверка здоровья
python main.py health-check

# Проверка конфигурации
python main.py validate-config
```

### Контакт

- GitHub Issues: https://github.com/your-repo/event_horizon_darf/issues
- Email: support@example.com
- Documentation: https://docs.example.com

---

**Удачного развертывания!** 🚀
