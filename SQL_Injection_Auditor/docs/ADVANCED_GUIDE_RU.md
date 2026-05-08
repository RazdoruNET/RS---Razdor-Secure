# SQL Injection Auditor - Руководство для Продвинутых Пользователей

## 🎯 Расширенные Возможности

Это руководство предназначено для пользователей, которые уже освоили базовое использование и хотят использовать все возможности инструмента.

## 🔧 Продвинутая Конфигурация

### Полная Конфигурация config.json

```json
{
  "crawl_delay": 2.0,
  "crawl_depth": 3,
  "timeout": 30,
  "user_agent": "SQLiAuditor/2.0",
  "respect_robots": true,
  "database_types": ["mysql", "postgresql", "mssql"],
  "payload_strategy": "effectiveness",
  "verify_vulnerabilities": true,
  "enable_waf_bypass": true,
  "output_dir": "reports",
  "report_formats": ["json", "pdf"],
  "generate_pdf": true,
  "proxies": {
    "http": "http://proxy.example.com:8080",
    "https": "https://proxy.example.com:8080"
  }
}
```

### Enterprise Security Конфигурация

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
  },
  "policy_settings": {
    "default_deny": true,
    "require_auth": false,
    "audit_all": true,
    "contextual_capabilities": true,
    "risk_adaptive": true
  },
  "execution_settings": {
    "max_concurrent_operations": 5,
    "isolation_timeout": 300,
    "resource_limits": {
      "cpu": "50%",
      "memory": "512MB",
      "network": "1MB/s"
    }
  }
}
```

### PDP Policy Конфигурация

```json
{
  "version": "2.0",
  "phase": "phase_3_central_enforcement",
  "global_rules": {
    "default_deny": true,
    "require_auth": true,
    "audit_all": true
  },
  "scope_policies": {
    "allow_patterns": [
      {
        "pattern": "https://.*\\.example\\.com",
        "risk": 2.0
      },
      {
        "pattern": "https://.*\\.test\\.com",
        "risk": 3.0
      }
    ],
    "deny_patterns": [
      {
        "pattern": ".*\\.internal",
        "reason": "internal_network"
      },
      {
        "pattern": "localhost|127\\.0\\.0\\.1",
        "reason": "loopback"
      }
    ]
  },
  "capability_policies": {
    "contextual_capabilities": true,
    "risk_adaptive": true,
    "time_bound": true,
    "capabilities": {
      "execute_requests": {
        "base_risk": 6.0,
        "requires_auth": true,
        "max_concurrent": 5,
        "isolation_required": true
      }
    }
  }
}
```

## 🚀 Продвинутые Команды

### Скан с Custom Payloads

```bash
# Использование custom payload файла
python main.py -u https://example.com --custom-payloads my_payloads.txt

# Специфическая база данных
python main.py -u https://example.com --db-type mysql

# Специфический тип инъекции
python main.py -u https://example.com --injection-type error_based
```

### Скан с WAF Bypass

```bash
# Включение WAF bypass
python main.py -u https://example.com --enable-waf-bypass

# Агрессивный WAF bypass
python main.py -u https://example.com --enable-waf-bypass --aggressive-bypass
```

### Enterprise Security Скан

```bash
# Enterprise режим
python main.py -u https://example.com --config enterprise_config.json

# С авторизационным токеном
python main.py -u https://example.com --config enterprise_config.json --auth-token TOKEN

# С изоляцией выполнения
python main.py -u https://example.com --config enterprise_config.json --isolation container
```

## 🎛️ Payload Engine Configuration

### Custom Payload Patterns

Создайте файл `custom_payloads.json`:

```json
{
  "custom_payloads": {
    "mysql": {
      "error_based": [
        "' OR 1=1 -- ",
        "' OR '1'='1",
        "admin' --",
        "' UNION SELECT NULL,NULL,NULL -- "
      ],
      "time_based": [
        "' AND SLEEP(5) -- ",
        "' AND BENCHMARK(5000000,MD5(1)) -- "
      ]
    }
  }
}
```

### Payload Optimization Strategies

```json
{
  "payload_strategy": "effectiveness",
  "optimization_options": {
    "sort_by_confidence": true,
    "remove_duplicates": true,
    "minimize_length": true,
    "max_payloads_per_test": 50
  }
}
```

## 🔍 Advanced Crawler Options

### Custom Crawler Configuration

```json
{
  "crawl_delay": 2.0,
  "crawl_depth": 3,
  "max_pages": 100,
  "follow_redirects": true,
  "respect_robots": true,
  "user_agent": "Mozilla/5.0 (compatible; SQLiAuditor/2.0)",
  "headers": {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.5"
  },
  "cookies": {
    "session_id": "your_session_id"
  },
  "exclude_patterns": [
    "\\.jpg$",
    "\\.png$",
    "\\.css$",
    "\\.js$"
  ],
  "include_patterns": [
    "\\.php$",
    "\\.asp$",
    "\\.jsp$"
  ]
}
```

### Targeted Crawler

```bash
# Краулинг только определенных путей
python main.py -u https://example.com --crawl-paths "/search,/login,/admin"

# Исключение определенных путей
python main.py -u https://example.com --exclude-paths "/static,/images,/assets"

# Краулинг с custom headers
python main.py -u https://example.com --headers "Authorization: Bearer TOKEN"
```

## 🛡️ Enterprise Security Features

### Central Policy Decision Point (PDP)

PDP - централизованный механизм принятия решений о безопасности.

**Принципы работы:**
1. **Scope Evaluation** - проверка целевого URL против allow/deny patterns
2. **Capability Evaluation** - проверка прав на выполнение операции
3. **Context Evaluation** - учет контекстных факторов (время, concurrent ops)
4. **Risk Aggregation** - агрегация рисков для финального решения

### Policy Enforcement Point (PEP)

PEP - единая точка enforcement для всех security решений.

**Функции:**
- Автоматическое enforcement PDP решений
- Создание изоляции для high-risk операций
- Логирование в cryptographic audit chain
- Кэширование решений для оптимизации

### Cryptographic Audit Chain

Tamper-evident audit trail с Merkle tree integrity.

**Особенности:**
- Hash chaining - каждый entry связан с предыдущим
- Merkle tree - целостность всего audit log
- Automatic verification - детекция любых модификаций
- Immutable storage - невозможность изменения истории

### Execution Isolation

True isolation на container level.

**Уровни изоляции:**
- **Container** - Docker/Kubernetes containers
- **Chroot** - файловая система изоляция
- **Namespace** - Linux namespace isolation
- **Network** - network policy enforcement

## 🎨 Custom Reporting

### Custom Report Templates

Создайте файл `custom_report_template.json`:

```json
{
  "report_template": {
    "include_scan_metadata": true,
    "include_vulnerability_details": true,
    "include_payloads_used": true,
    "include_response_analysis": true,
    "include_recommendations": true,
    "custom_fields": {
      "company": "Your Company",
      "project": "Security Audit",
      "classification": "Confidential"
    }
  }
}
```

### Report Filtering

```bash
# Фильтрация по уровню уязвимости
python main.py -u https://example.com --filter-severity high,medium

# Фильтрация по типу инъекции
python main.py -u https://example.com --filter-injection error_based,boolean_based

# Фильтрация по базе данных
python main.py -u https://example.com --filter-database mysql,postgresql
```

## 🔬 Advanced Analysis

### False Positive Detection

Инструмент включает автоматическую детекцию ложных срабатываний:

```json
{
  "false_positive_detection": {
    "enabled": true,
    "min_confidence_threshold": 0.7,
    "check_patterns": [
      "generic error message",
      "application error",
      "validation error"
    ]
  }
}
```

### Vulnerability Verification

Многоуровневая верификация найденных уязвимостей:

```json
{
  "verification": {
    "enabled": true,
    "strategies": [
      "payload_variation",
      "consistency_check",
      "response_analysis"
    ],
    "min_verification_score": 0.8
  }
}
```

## 🌐 Advanced Network Options

### Proxy Configuration

```json
{
  "proxies": {
    "http": "http://proxy.example.com:8080",
    "https": "https://proxy.example.com:8080",
    "socks5": "socks5://proxy.example.com:1080"
  }
}
```

### Rate Limiting

```json
{
  "rate_limiting": {
    "enabled": true,
    "requests_per_second": 2,
    "burst_size": 10,
    "adaptive_rate_limiting": true
  }
}
```

### Custom Headers and Cookies

```bash
# Custom headers
python main.py -u https://example.com --header "Authorization: Bearer TOKEN"

# Custom cookies
python main.py -u https://example.com --cookie "session_id=abc123; user_token=xyz789"

# Load from file
python main.py -u https://example.com --headers-file headers.txt --cookies-file cookies.txt
```

## 🎯 Target-Specific Scenarios

### E-commerce Sites

```json
{
  "target_type": "ecommerce",
  "focus_areas": [
    "search",
    "product_filters",
    "category_navigation",
    "user_profiles"
  ],
  "sensitive_parameters": [
    "user_id",
    "product_id",
    "order_id",
    "payment_id"
  ]
}
```

### CMS Platforms

```json
{
  "target_type": "cms",
  "platform": "wordpress",
  "focus_areas": [
    "admin_panel",
    "plugin_endpoints",
    "theme_files",
    "api_endpoints"
  ]
}
```

### API Endpoints

```json
{
  "target_type": "api",
  "api_format": "rest",
  "test_methods": ["GET", "POST", "PUT", "DELETE"],
  "content_types": ["application/json", "application/xml"],
  "authentication": "bearer_token"
}
```

## 📊 Performance Optimization

### Parallel Processing

```json
{
  "parallel_processing": {
    "enabled": true,
    "max_workers": 5,
    "chunk_size": 10
  }
}
```

### Caching

```json
{
  "caching": {
    "enabled": true,
    "cache_responses": true,
    "cache_duration": 3600,
    "max_cache_size": 1000
  }
}
```

### Memory Management

```json
{
  "memory_management": {
    "max_memory_usage": "2GB",
    "gc_interval": 100,
    "cleanup_temp_files": true
  }
}
```

## 🔒 Advanced Security Features

### Authorization Tokens

Генерация и использование авторизационных токенов:

```python
from modules.security import SecurityManager, SecurityLevel

# Создание security manager
security_manager = SecurityManager('security_config.json')

# Генерация токена
token = security_manager.generate_auth_token(
    scope=['https://example.com'],
    security_level=SecurityLevel.ANALYSIS,
    capabilities=['execute_requests', 'analyze_responses'],
    expires_hours=24
)

print(f"Authorization Token: {token}")
```

### Audit Chain Verification

```python
from modules.enterprise_security import CryptographicAuditChain

# Проверка целостности audit chain
audit_chain = CryptographicAuditChain('audit_chain.db')
integrity_ok = audit_chain.verify_chain_integrity()

if integrity_ok:
    print("✅ Audit chain integrity verified")
else:
    print("❌ Audit chain compromised!")
```

### Isolation Management

```python
from modules.enterprise_security import EnterpriseSecurityManager

# Создание enterprise manager
esm = EnterpriseSecurityManager('pdp_config.json')

# Создание изолированного контекста
request_context = {
    'target': 'https://example.com',
    'operation': 'execute_requests',
    'payload': "' OR 1=1 -- "
}

exec_context = esm.create_isolated_execution(request_context)
print(f"Isolation ID: {exec_context.execution_id}")
print(f"Container ID: {exec_context.container_id}")
```

## 🎓 Integration Examples

### Integration with CI/CD

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run SQL Injection Audit
        run: |
          python main.py -u ${{ secrets.TARGET_URL }} --config enterprise_config.json
```

### Integration with Security Tools

```python
# Integration with OWASP ZAP
import zapv2 as zap

zap_proxy = zap.ZAPv2(proxies={'http': 'http://localhost:8080', 'https': 'http://localhost:8080'})

# Запуск ZAP passive scan
zap_proxy.pscan.enable_scanner('10021')  # SQL Injection scanner
zap_proxy.pscan.scan('https://example.com')

# Запуск нашего SQLi Auditor
from main import SQLInjectionAuditor
auditor = SQLInjectionAuditor(config)
results = auditor.audit_target('https://example.com')
```

## 🐛 Troubleshooting Advanced Issues

### Memory Leaks

```bash
# Мониторинг памяти
python -m memory_profiler main.py -u https://example.com

# Очистка кэша
python main.py -u https://example.com --clear-cache
```

### Network Timeouts

```json
{
  "network_settings": {
    "connection_timeout": 10,
    "read_timeout": 30,
    "max_retries": 3,
    "retry_delay": 5
  }
}
```

### Audit Chain Corruption

```bash
# Резервное копирование audit chain
cp audit_chain.db audit_chain.db.backup

# Пересоздание audit chain
rm audit_chain.db
python main.py -u https://example.com --rebuild-audit-chain
```

## 📚 Дополнительные Ресурсы

- **Technical Documentation** - для инженеров
- **API Reference** - полное описание API
- **Security Architecture** - архитектура безопасности
- **Integration Guide** - руководство по интеграции

---

**Следующий уровень:** Техническая документация для инженеров и разработчиков.
