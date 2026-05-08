# SQL Injection Auditor - Техническая Документация для Инженеров

## 🏗️ Системная Архитектура

### Обзор Архитектуры

SQL Injection Auditor построен на модульной архитектуре с enterprise-grade security controls. Система разделена на три основных уровня:

1. **Application Layer** - основная логика аудита
2. **Security Layer** - enterprise security controls (PDP/PEP)
3. **Infrastructure Layer** - изоляция выполнения и audit chain

### Компоненты Системы

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  main.py │ Crawler │ Payload Engine │ Analysis │ Verification │
├─────────────────────────────────────────────────────────────┤
│                     Security Layer                          │
├─────────────────────────────────────────────────────────────┤
│  PDP │ PEP │ Audit Chain │ Isolation Manager │ Risk Model    │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Container Isolation │ Network Policy │ Resource Limits      │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Модульная Структура

### Основные Модули

#### 1. Crawler Module (`modules/crawler.py`)

**Назначение:** Обнаружение input vectors через краулинг веб-приложений.

**Классы:**
- `InputVector` - представление найденного input point
- `WebCrawler` - основной краулер с поддержкой robots.txt
- `VectorAnalyzer` - анализ и приоритизация input vectors

**Ключевые методы:**
```python
class WebCrawler:
    def crawl_domain(self, base_url: str, max_depth: int) -> List[InputVector]:
        """Краулинг домена с заданной глубиной"""
        
    def extract_forms(self, soup) -> List[Dict]:
        """Извлечение HTML форм"""
        
    def extract_links(self, soup, base_url) -> List[str]:
        """Извлечение ссылок"""
```

**Алгоритм краулинга:**
1. BFS traversal с depth limit
2. Учет robots.txt
3. Rate limiting через crawl_delay
4. Извлечение форм, ссылок, API endpoints
5. Фильтрация по exclude/include patterns

#### 2. Payload Engine (`modules/payload_engine.py`)

**Назначение:** Генерация SQL injection payloads для разных типов БД.

**Классы:**
- `PayloadGenerator` - основной генератор payloads
- `PayloadOptimizer` - оптимизация порядка payloads
- `DatabaseType` - enum поддерживаемых БД
- `InjectionType` - enum типов инъекций

**Алгоритм генерации:**
```python
def generate_error_based_payloads(self, db_type: DatabaseType) -> List[str]:
    """Генерация error-based payloads"""
    
    if db_type == DatabaseType.MYSQL:
        return [
            "' OR 1=1 -- ",
            "' OR '1'='1",
            "' UNION SELECT NULL,NULL -- ",
            # ... MySQL-specific payloads
        ]
    elif db_type == DatabaseType.POSTGRESQL:
        return [
            "' OR 1=1 -- ",
            "' UNION SELECT NULL,NULL -- ",
            # ... PostgreSQL-specific payloads
        ]
```

**Оптимизация payloads:**
- Сортировка по effectiveness score
- Удаление дубликатов
- Минимизация длины
- Кластеризация по паттернам

#### 3. Analysis Engine (`modules/analysis_engine.py`)

**Назначение:** Детекция SQL injection vulnerabilities через анализ HTTP ответов.

**Классы:**
- `VulnerabilityScanner` - основной сканер
- `ErrorPatternMatcher` - сопоставление паттернов ошибок
- `ResponseAnalyzer` - анализ HTTP ответов
- `Vulnerability` - dataclass для найденных уязвимостей

**Алгоритм детекции:**
```python
def _send_payload(self, url: str, parameter: str, payload: str) -> Response:
    """Отправка payload и анализ ответа"""
    
    response = self._make_request(url, parameter, payload)
    
    # Error-based detection
    if self._detect_sql_errors(response.text):
        return Vulnerability(
            injection_type=InjectionType.ERROR_BASED,
            confidence=0.9
        )
    
    # Boolean-based detection
    if self._detect_boolean_differences(response):
        return Vulnerability(
            injection_type=InjectionType.BOOLEAN_BASED,
            confidence=0.7
        )
    
    # Time-based detection
    if self._detect_time_delays(response):
        return Vulnerability(
            injection_type=InjectionType.TIME_BASED,
            confidence=0.8
        )
```

**Паттерны ошибок:**
```python
ERROR_PATTERNS = {
    'mysql': [
        r"SQL syntax.*MySQL",
        r"mysql_fetch",
        r"You have an error in your SQL syntax"
    ],
    'postgresql': [
        r"PostgreSQL.*ERROR",
        r"pg_query",
        r"ERROR: syntax error"
    ],
    'mssql': [
        r"Microsoft OLE DB Provider for SQL Server",
        r"Unclosed quotation mark",
        r"Incorrect syntax near"
    ]
}
```

#### 4. Verification Module (`modules/verification.py`)

**Назначение:** Верификация найденных уязвимостей для снижения false positives.

**Классы:**
- `VulnerabilityVerifier` - основной верификатор
- `FalsePositiveDetector` - детектор ложных срабатываний
- `PayloadVariator` - вариация payloads
- `ConsistencyChecker` - проверка консистентности

**Алгоритм верификации:**
```python
def verify_vulnerability(self, vulnerability: Vulnerability) -> VerificationResult:
    """Многоуровневая верификация"""
    
    # Step 1: Payload variation
    variant_results = self._test_payload_variants(vulnerability)
    
    # Step 2: Consistency check
    consistency_score = self._check_consistency(variant_results)
    
    # Step 3: False positive detection
    fp_score = self._detect_false_positives(vulnerability)
    
    # Aggregate confidence
    final_confidence = self._calculate_confidence(
        variant_results, consistency_score, fp_score
    )
    
    return VerificationResult(
        confidence=final_confidence,
        status=self._determine_status(final_confidence)
    )
```

#### 5. WAF Bypass Module (`modules/waf_bypass.py`)

**Назначение:** Обход Web Application Firewalls через obfuscation techniques.

**Классы:**
- `WAFBypassEngine` - основной bypass engine
- `WAFFingerprint` - детекция типа WAF
- `PayloadObfuscator` - obfuscation payloads

**Techniques:**
```python
BYPASS_TECHNIQUES = {
    'case_variation': "' OR 1=1 -- " -> "' oR 1=1 -- ",
    'encoding': "' OR 1=1 -- " -> "'%20OR%201=1%20--%20",
    'comment_obfuscation': "' OR 1=1 -- " -> "'/**/OR/**/1=1/**/--",
    'newline_obfuscation': "' OR 1=1 -- " -> "'\nOR\n1=1\n--\n",
    'unicode_obfuscation': "' OR 1=1 -- " -> "'\u004fR 1=1 -- "
}
```

## 🔒 Enterprise Security Architecture

### Phase 3: Centralized Enforcement

#### Central Policy Decision Point (PDP)

**Назначение:** Централизованная оценка security policies.

**Архитектура:**
```
Request Context → Scope Evaluation → Capability Evaluation → Context Evaluation
     ↓                      ↓                      ↓                      ↓
   Target URL          Operation Type         User Context         Risk Factors
     ↓                      ↓                      ↓                      ↓
   Pattern Match      Capability Check      Time/Concurrent      Risk Score
     ↓                      ↓                      ↓                      ↓
  Allow/Deny          Allow/Deny            Allow/Deny           Final Risk
     ↓                      ↓                      ↓                      ↓
         └────────────────────── Policy Decision ────────────────────────┘
```

**Реализация:**
```python
class CentralPolicyDecisionPoint:
    def evaluate_request(self, request_context: Dict) -> PolicyDecision:
        """Централизованная оценка политики"""
        
        # Step 1: Scope evaluation
        scope_allowed, scope_reason, scope_risk = self._evaluate_scope(
            request_context['target']
        )
        
        # Step 2: Capability evaluation
        cap_allowed, cap_reason, cap_risk = self._evaluate_capability(
            request_context['operation'],
            request_context['user_context'],
            request_context.get('payload')
        )
        
        # Step 3: Context evaluation
        context_allowed, context_reason, context_risk = self._evaluate_context(
            request_context
        )
        
        # Step 4: Risk aggregation
        total_risk = scope_risk + cap_risk + context_risk
        
        # Step 5: Final decision
        allowed = scope_allowed and cap_allowed and context_allowed
        
        return PolicyDecision(
            decision_id=self._generate_decision_id(),
            allowed=allowed,
            reason=self._generate_reason(scope_reason, cap_reason, context_reason),
            risk_score=total_risk,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            context=request_context,
            signature=self._sign_decision(decision_data)
        )
```

**Scope Evaluation:**
```python
def _evaluate_scope(self, target: str) -> Tuple[bool, str, float]:
    """Оценка target URL против scope policies"""
    
    # Check deny patterns
    for deny_rule in self.policy_rules['scope_policies']['deny_patterns']:
        if re.match(deny_rule['pattern'], target):
            return False, deny_rule['reason'], 9.0
    
    # Check allow patterns
    for allow_rule in self.policy_rules['scope_policies']['allow_patterns']:
        if re.match(allow_rule['pattern'], target):
            return True, "Pattern matched", allow_rule['risk']
    
    # Default deny
    return False, "Default deny - no matching allow pattern", 8.0
```

**Capability Evaluation:**
```python
def _evaluate_capability(self, operation: str, user_context: Dict, 
                        payload: str) -> Tuple[bool, str, float]:
    """Оценка capability requirements"""
    
    caps = self.policy_rules['capability_policies']['capabilities']
    
    if operation not in caps:
        return False, f"Unknown capability: {operation}", 10.0
    
    cap_config = caps[operation]
    
    # Check authentication
    if cap_config.get('requires_auth') and not user_context.get('auth_token'):
        return False, "Authentication required", 7.0
    
    # Check payload risk
    if payload:
        payload_risk = self.risk_model.assess_payload_risk(payload)
        cap_config['base_risk'] += payload_risk
    
    return True, "Capability allowed", cap_config['base_risk']
```

**Context Evaluation:**
```python
def _evaluate_context(self, request_context: Dict) -> Tuple[bool, str, float]:
    """Оценка контекстных факторов"""
    
    context_risk = 0.0
    
    # Time-based risk
    current_hour = datetime.now().hour
    if 22 <= current_hour or current_hour <= 6:
        context_risk += 1.0  # Higher risk during off-hours
    
    # User risk
    user_context = request_context.get('user_context', {})
    if user_context.get('risk_level') == 'high':
        context_risk += 2.0
    
    # Concurrent operations
    if self.context_engine.get_concurrent_operations() > 5:
        context_risk += 1.5
    
    return True, "Context evaluated", context_risk
```

#### Policy Enforcement Point (PEP)

**Назначение:** Единая точка enforcement для всех security решений.

**Реализация:**
```python
class PolicyEnforcementPoint:
    def enforce_policy(self, request_context: Dict) -> Tuple[bool, str]:
        """Единая точка enforcement"""
        
        # Step 1: Get policy decision
        decision = self.pdp.evaluate_request(request_context)
        
        # Step 2: Cache decision
        self.active_decisions[decision.decision_id] = decision
        
        # Step 3: Log to audit chain
        self.audit_chain.log_decision(decision, request_context)
        
        # Step 4: Enforce decision
        if not decision.allowed:
            return False, decision.reason
        
        # Step 5: Automatic isolation for high-risk
        if decision.risk_score > 7.0:
            return self._enforce_isolated_execution(request_context, decision)
        
        return True, "Policy enforced"
```

**Isolated Execution:**
```python
def _enforce_isolated_execution(self, request_context: Dict, 
                                decision: PolicyDecision) -> Tuple[bool, str]:
    """Enforce execution in isolation"""
    
    exec_context = self.execution_manager.create_isolated_context(
        request_context, decision
    )
    
    self.audit_chain.log_isolation(exec_context, decision.decision_id)
    
    return True, f"Isolated execution ready: {exec_context.execution_id}"
```

#### Cryptographic Audit Chain

**Назначение:** Tamper-evident audit trail с Merkle tree integrity.

**Структура Audit Chain Entry:**
```python
@dataclass
class AuditChain:
    sequence_number: int           # Порядковый номер
    entry_hash: str               # Hash текущего entry
    previous_hash: str            # Hash предыдущего entry
    merkle_root: str              # Merkle root на момент создания
    timestamp: datetime           # Timestamp создания
    event_data: Dict[str, Any]    # Данные события
    signature: str                # Криптографическая подпись
```

**Hash Chaining Algorithm:**
```python
def _create_chain_entry(self, event_data: Dict) -> AuditChain:
    """Создание cryptographically chained entry"""
    
    # Serialize event data
    event_json = json.dumps(event_data, sort_keys=True)
    
    # Get previous hash
    previous_hash = self._get_previous_hash()
    
    # Create entry hash with chaining
    entry_data = f"{self.current_sequence}{event_json}{previous_hash}"
    entry_hash = hashlib.sha256(entry_data.encode()).hexdigest()
    
    # Update Merkle tree
    self.merkle_tree.add_leaf(entry_hash)
    merkle_root = self.merkle_tree.get_root()
    
    return AuditChain(
        sequence_number=self.current_sequence,
        entry_hash=entry_hash,
        previous_hash=previous_hash,
        merkle_root=merkle_root,
        timestamp=datetime.now(timezone.utc),
        event_data=event_data,
        signature=self._sign_entry(entry_hash, merkle_root)
    )
```

**Merkle Tree Implementation:**
```python
class MerkleTree:
    def __init__(self):
        self.leaves = []
        self.tree = []
    
    def add_leaf(self, data: str):
        """Добавление leaf в Merkle tree"""
        leaf_hash = hashlib.sha256(data.encode()).hexdigest()
        self.leaves.append(leaf_hash)
        self._build_tree()
    
    def _build_tree(self):
        """Построение Merkle tree"""
        if not self.leaves:
            return
        
        self.tree = self.leaves.copy()
        current_level = self.leaves
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]
                
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            
            current_level = next_level
            self.tree.extend(current_level)
    
    def get_root(self) -> str:
        """Получение Merkle root"""
        if not self.tree:
            return "0" * 64
        return self.tree[-1]
```

**Integrity Verification:**
```python
def verify_chain_integrity(self) -> bool:
    """Проверка целостности audit chain"""
    
    conn = sqlite3.connect(self.chain_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM audit_chain ORDER BY sequence_number")
    entries = cursor.fetchall()
    conn.close()
    
    previous_hash = "0" * 64
    
    for entry in entries:
        seq, entry_hash, prev_hash, merkle_root, timestamp, event_data, signature = entry
        
        # Verify hash chain
        if prev_hash != previous_hash:
            self.logger.error(f"Chain break at sequence {seq}")
            return False
        
        # Verify entry hash
        expected_hash = hashlib.sha256(
            f"{seq}{event_data}{prev_hash}".encode()
        ).hexdigest()
        
        if entry_hash != expected_hash:
            self.logger.error(f"Hash mismatch at sequence {seq}")
            return False
        
        previous_hash = entry_hash
    
    return True
```

#### Execution Isolation Manager

**Назначение:** True isolation на container level для high-risk операций.

**Isolation Levels:**
```python
class IsolationType(Enum):
    CONTAINER = "container"       # Docker/Kubernetes containers
    CHROOT = "chroot"            # Chroot filesystem isolation
    NAMESPACE = "namespace"      # Linux namespace isolation
    NETWORK = "network"          # Network policy isolation only
```

**Container Isolation Setup:**
```python
def _setup_container_isolation(self, context: ExecutionContext):
    """Настройка container-level isolation"""
    
    # Step 1: Create container network namespace
    self._create_network_namespace(context.container_id)
    
    # Step 2: Apply network policy
    self._apply_network_policy(context.network_policy)
    
    # Step 3: Set resource limits
    self._set_resource_limits(context.resource_limits)
    
    # Step 4: Setup seccomp profile
    self._setup_seccomp_profile(context.container_id)
    
    # Step 5: Mount filesystem read-only
    self._mount_readonly_filesystem(context.sandbox_path)
    
    # Step 6: Create isolated directory structure
    self._create_sandbox_structure(context.sandbox_path)
```

**Network Policy Enforcement:**
```python
def _apply_network_policy(self, network_policy: Dict):
    """Применение network policy"""
    
    allowed_ports = network_policy.get('allowed_ports', [80, 443])
    blocked_ips = network_policy.get('blocked_ips', ['127.0.0.1', '169.254.0.0/16'])
    max_bandwidth = network_policy.get('max_bandwidth', '1MB/s')
    
    # Apply iptables rules
    for port in allowed_ports:
        self._add_iptables_rule(f"ACCEPT --dport {port}")
    
    for ip in blocked_ips:
        self._add_iptables_rule(f"DROP --destination {ip}")
    
    # Apply traffic shaping
    self._apply_traffic_shaping(max_bandwidth)
```

**Resource Limits:**
```python
def _set_resource_limits(self, resource_limits: Dict):
    """Установка resource limits"""
    
    cpu_limit = resource_limits.get('cpu_limit', '50%')
    memory_limit = resource_limits.get('memory_limit', '512MB')
    disk_limit = resource_limits.get('disk_limit', '100MB')
    
    # CPU limits via cgroups
    self._set_cpu_limit(cpu_limit)
    
    # Memory limits via cgroups
    self._set_memory_limit(memory_limit)
    
    # Disk limits via quotas
    self._set_disk_limit(disk_limit)
```

## 🔌 API Reference

### Main API Interface

```python
from main import SQLInjectionAuditor

# Initialize auditor
auditor = SQLInjectionAuditor(config)

# Perform audit
results = auditor.audit_target(
    target_url='https://example.com',
    scan_mode='active'
)

# Results structure
{
    'target': 'https://example.com',
    'status': 'completed',
    'duration': 123.45,
    'vulnerabilities_found': 5,
    'vulnerabilities': [...]
}
```

### Enterprise Security API

```python
from modules.enterprise_security import EnterpriseSecurityManager

# Initialize enterprise manager
esm = EnterpriseSecurityManager('pdp_config.json')

# Authorization and enforcement
request_context = {
    'target': 'https://example.com',
    'operation': 'execute_requests',
    'user_context': {'auth_token': 'token123'}
}

allowed, message = esm.authorize_and_enforce(request_context)

# Create isolated execution
exec_context = esm.create_isolated_execution(request_context)
```

### Crawler API

```python
from modules.crawler import WebCrawler

crawler = WebCrawler(delay=2.0, user_agent='CustomAgent')

# Crawl domain
input_vectors = crawler.crawl_domain('https://example.com', max_depth=3)

# Analyze vectors
from modules.crawler import VectorAnalyzer
analyzer = VectorAnalyzer()
analysis = analyzer.analyze_vectors(input_vectors)
```

### Payload Engine API

```python
from modules.payload_engine import PayloadGenerator, PayloadOptimizer

generator = PayloadGenerator()
optimizer = PayloadOptimizer()

# Generate payloads
payloads = generator.generate_all_payloads(DatabaseType.MYSQL)

# Optimize payloads
optimized = optimizer.optimize_payload_order(
    payloads, 
    strategy='effectiveness'
)
```

### Analysis Engine API

```python
from modules.analysis_engine import VulnerabilityScanner

scanner = VulnerabilityScanner(session, timeout=30)

# Scan parameter
vulnerabilities = scanner.scan_parameter(
    url='https://example.com/search.php',
    parameter='q',
    payloads=["' OR 1=1 -- "],
    injection_type=InjectionType.ERROR_BASED,
    db_type=DatabaseType.MYSQL
)
```

## 🗄️ Database Schema

### Audit Chain Database

```sql
CREATE TABLE audit_chain (
    sequence_number INTEGER PRIMARY KEY,
    entry_hash TEXT NOT NULL,
    previous_hash TEXT,
    merkle_root TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_data TEXT NOT NULL,
    signature TEXT NOT NULL
);

CREATE INDEX idx_sequence ON audit_chain(sequence_number);
CREATE INDEX idx_timestamp ON audit_chain(timestamp);
```

### Security Configuration Database

```sql
CREATE TABLE security_config (
    config_key TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE authorization_tokens (
    token_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    security_level TEXT NOT NULL,
    capabilities TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE
);
```

## 🚀 Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Application Server (Gunicorn)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              SQL Injection Auditor Instance                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Enterprise Security Manager                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │   PDP    │  │   PEP    │  │  Audit Chain     │  │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │      Isolation Manager (Docker/K8s)           │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Container Registry (Docker Hub)                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Docker/Kubernetes Cluster                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Container 1 │  │  Container 2 │  │  Container N │      │
│  │  (Isolation) │  │  (Isolation) │  │  (Isolation) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Target Application (Scanned)                    │
└─────────────────────────────────────────────────────────────┘
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sqli-auditor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sqli-auditor
  template:
    metadata:
      labels:
        app: sqli-auditor
    spec:
      containers:
      - name: auditor
        image: sqli-auditor:latest
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        env:
        - name: ENTERPRISE_MODE
          value: "true"
        - name: AUDIT_CHAIN_FILE
          value: "/data/audit_chain.db"
        volumeMounts:
        - name: audit-data
          mountPath: /data
      volumes:
      - name: audit-data
        persistentVolumeClaim:
          claimName: audit-chain-pvc
```

## 🔍 Monitoring and Logging

### Logging Architecture

```python
# Structured logging with JSON format
import structlog

logger = structlog.get_logger()
logger.info(
    "audit_started",
    target="https://example.com",
    mode="active",
    user_id="user123",
    request_id="req456"
)

# Security event logging
logger.warning(
    "security_violation",
    decision_id="dec789",
    reason="Scope policy violation",
    risk_score=8.5,
    user_id="user123"
)
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram

# Define metrics
vulnerabilities_found = Counter('vulnerabilities_found_total', 'Total vulnerabilities found')
scan_duration = Histogram('scan_duration_seconds', 'Scan duration')
policy_decisions = Counter('policy_decisions_total', 'Total policy decisions', ['allowed'])

# Use metrics
vulnerabilities_found.inc()
scan_duration.observe(scan_time)
policy_decisions.labels(allowed='true').inc()
```

## 🧪 Testing Strategy

### Unit Tests

```python
import pytest
from modules.payload_engine import PayloadGenerator, DatabaseType

def test_mysql_payload_generation():
    generator = PayloadGenerator()
    payloads = generator.generate_error_based_payloads(DatabaseType.MYSQL)
    
    assert len(payloads) > 0
    assert "' OR 1=1 -- " in payloads
    assert "' UNION SELECT NULL -- " in payloads

def test_payload_optimization():
    generator = PayloadGenerator()
    optimizer = PayloadOptimizer()
    
    payloads = generator.generate_all_payloads(DatabaseType.MYSQL)
    optimized = optimizer.optimize_payload_order(payloads, strategy='effectiveness')
    
    assert len(optimized) <= len(payloads)
```

### Integration Tests

```python
def test_end_to_end_audit():
    auditor = SQLInjectionAuditor(test_config)
    results = auditor.audit_target('https://test-site.com', scan_mode='passive')
    
    assert results['status'] == 'completed'
    assert 'vulnerabilities' in results
    assert 'duration' in results
```

### Security Tests

```python
def test_pdp_denies_internal_network():
    pdp = CentralPolicyDecisionPoint(test_config)
    decision = pdp.evaluate_request({
        'target': 'http://192.168.1.1/admin',
        'operation': 'execute_requests'
    })
    
    assert decision.allowed == False
    assert 'internal_network' in decision.reason

def test_audit_chain_integrity():
    audit_chain = CryptographicAuditChain('test_chain.db')
    
    # Add entry
    audit_chain.log_decision(test_decision, test_context)
    
    # Verify integrity
    assert audit_chain.verify_chain_integrity() == True
    
    # Tamper with chain
    tampered_entry = audit_chain._get_entry(1)
    tampered_entry.entry_hash = "0" * 64
    audit_chain._store_entry(tampered_entry)
    
    # Verify tamper detection
    assert audit_chain.verify_chain_integrity() == False
```

## 📊 Performance Considerations

### Optimization Strategies

1. **Parallel Processing**
   - Multi-threaded payload testing
   - Async I/O for HTTP requests
   - Concurrent crawling

2. **Caching**
   - Response caching
   - Decision caching
   - Pattern matching cache

3. **Resource Management**
   - Memory pooling
   - Connection pooling
   - Garbage collection tuning

### Scalability

```
Single Instance: 10-50 concurrent scans
Cluster (3 nodes): 30-150 concurrent scans
Cluster (10 nodes): 100-500 concurrent scans
```

## 🔧 Troubleshooting Guide

### Common Issues

**Issue:** Memory leak during long scans
**Solution:** Enable garbage collection, increase memory limits

**Issue:** Audit chain corruption
**Solution:** Restore from backup, verify integrity before writes

**Issue:** Container isolation failures
**Solution:** Check Docker/Kubernetes health, verify resource limits

**Issue:** PDP performance degradation
**Solution:** Enable decision caching, optimize pattern matching

---

**Следующий уровень:** API Reference и Security Architecture Documentation.
