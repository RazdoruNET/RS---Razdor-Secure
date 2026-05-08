# SQL Injection Auditor - API Reference

## 📚 Обзор API

Этот документ содержит полное описание API всех модулей SQL Injection Auditor.

## 🔧 Основной API

### SQLInjectionAuditor Class

```python
class SQLInjectionAuditor:
    """Основной класс SQL Injection Auditor"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация аудитора
        
        Args:
            config: Словарь конфигурации
        """
        
    def audit_target(self, target_url: str, scan_mode: str = 'active') -> Dict[str, Any]:
        """
        Выполнение полного SQL injection аудита
        
        Args:
            target_url: Целевой URL для аудита
            scan_mode: Режим сканирования ('active' или 'passive')
            
        Returns:
            Dict с результатами аудита:
            {
                'target': str,
                'status': str,
                'duration': float,
                'vulnerabilities_found': int,
                'vulnerabilities': List[Vulnerability]
            }
        """
```

### Пример Использования

```python
from main import SQLInjectionAuditor

# Инициализация
config = {
    'crawl_delay': 2.0,
    'crawl_depth': 2,
    'timeout': 30,
    'database_types': ['mysql', 'postgresql']
}

auditor = SQLInjectionAuditor(config)

# Выполнение аудита
results = auditor.audit_target('https://example.com', scan_mode='active')

# Обработка результатов
if results['status'] == 'completed':
    print(f"Найдено уязвимостей: {results['vulnerabilities_found']}")
    for vuln in results['vulnerabilities']:
        print(f"URL: {vuln.url}")
        print(f"Параметр: {vuln.parameter}")
        print(f"Тип: {vuln.injection_type}")
        print(f"БД: {vuln.database_type}")
        print(f"Уверенность: {vuln.confidence}")
```

## 🕷️ Crawler Module API

### WebCrawler Class

```python
class WebCrawler:
    """Краулер для обнаружения input vectors"""
    
    def __init__(self, delay: float = 1.0, user_agent: str = None, 
                 respect_robots: bool = True):
        """
        Инициализация краулера
        
        Args:
            delay: Задержка между запросами в секундах
            user_agent: User Agent string
            respect_robots: Учитывать robots.txt
        """
        
    def crawl_domain(self, base_url: str, max_depth: int = 3) -> List[InputVector]:
        """
        Краулинг домена с заданной глубиной
        
        Args:
            base_url: Базовый URL для краулинга
            max_depth: Максимальная глубина краулинга
            
        Returns:
            List[InputVector]: Список найденных input vectors
        """
        
    def extract_forms(self, soup) -> List[Dict[str, Any]]:
        """
        Извлечение HTML форм из страницы
        
        Args:
            soup: BeautifulSoup объект страницы
            
        Returns:
            List[Dict]: Список форм с полями
        """
        
    def extract_links(self, soup, base_url: str) -> List[str]:
        """
        Извлечение ссылок со страницы
        
        Args:
            soup: BeautifulSoup объект страницы
            base_url: Базовый URL для разрешения относительных ссылок
            
        Returns:
            List[str]: Список абсолютных URL
        """
```

### InputVector Class

```python
@dataclass
class InputVector:
    """Представление input point для тестирования"""
    
    url: str
    method: str  # 'GET', 'POST', etc.
    params: Dict[str, List[str]]
    headers: Dict[str, str]
    cookies: Dict[str, str]
    data: Dict[str, Any]
    form_data: Dict[str, Any]
```

### VectorAnalyzer Class

```python
class VectorAnalyzer:
    """Анализатор и приоритизатор input vectors"""
    
    def analyze_vectors(self, input_vectors: List[InputVector]) -> Dict[str, Any]:
        """
        Анализ и приоритизация input vectors
        
        Args:
            input_vectors: Список input vectors для анализа
            
        Returns:
            Dict с категоризацией:
            {
                'high_risk': List[InputVector],
                'medium_risk': List[InputVector],
                'low_risk': List[InputVector],
                'total_count': int
            }
        """
        
    def calculate_risk_score(self, vector: InputVector) -> float:
        """
        Расчет риска для input vector
        
        Args:
            vector: InputVector для оценки
            
        Returns:
            float: Оценка риска (0.0 - 10.0)
        """
```

### Пример Использования Crawler

```python
from modules.crawler import WebCrawler, VectorAnalyzer

# Инициализация краулера
crawler = WebCrawler(delay=2.0, respect_robots=True)

# Краулинг домена
input_vectors = crawler.crawl_domain('https://example.com', max_depth=3)

# Анализ vectors
analyzer = VectorAnalyzer()
analysis = analyzer.analyze_vectors(input_vectors)

print(f"High risk: {len(analysis['high_risk'])}")
print(f"Medium risk: {len(analysis['medium_risk'])}")
print(f"Low risk: {len(analysis['low_risk'])}")
```

## 💣 Payload Engine API

### PayloadGenerator Class

```python
class PayloadGenerator:
    """Генератор SQL injection payloads"""
    
    def __init__(self):
        """Инициализация генератора"""
        
    def generate_all_payloads(self, db_type: DatabaseType) -> Dict[str, List[str]]:
        """
        Генерация всех типов payloads для указанной БД
        
        Args:
            db_type: Тип базы данных
            
        Returns:
            Dict с payloads по типам инъекций:
            {
                'error_based': List[str],
                'boolean_based': List[str],
                'time_based': List[str],
                'union_based': List[str]
            }
        """
        
    def generate_error_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """
        Генерация error-based payloads
        
        Args:
            db_type: Тип базы данных
            
        Returns:
            List[str]: Список error-based payloads
        """
        
    def generate_boolean_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """
        Генерация boolean-based payloads
        
        Args:
            db_type: Тип базы данных
            
        Returns:
            List[str]: Список boolean-based payloads
        """
        
    def generate_time_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """
        Генерация time-based payloads
        
        Args:
            db_type: Тип базы данных
            
        Returns:
            List[str]: Список time-based payloads
        """
        
    def generate_union_based_payloads(self, db_type: DatabaseType) -> List[str]:
        """
        Генерация union-based payloads
        
        Args:
            db_type: Тип базы данных
            
        Returns:
            List[str]: Список union-based payloads
        """
```

### PayloadOptimizer Class

```python
class PayloadOptimizer:
    """Оптимизатор порядка payloads"""
    
    def optimize_payload_order(self, payloads: List[str], 
                               strategy: str = 'effectiveness') -> List[str]:
        """
        Оптимизация порядка payloads
        
        Args:
            payloads: Список payloads для оптимизации
            strategy: Стратегия оптимизации ('effectiveness', 'length', 'random')
            
        Returns:
            List[str]: Оптимизированный список payloads
        """
        
    def calculate_effectiveness_score(self, payload: str) -> float:
        """
        Расчет effectiveness score для payload
        
        Args:
            payload: Payload для оценки
            
        Returns:
            float: Effectiveness score (0.0 - 1.0)
        """
```

### DatabaseType Enum

```python
class DatabaseType(Enum):
    """Поддерживаемые типы баз данных"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    SQLITE = "sqlite"
```

### InjectionType Enum

```python
class InjectionType(Enum):
    """Типы SQL injection"""
    ERROR_BASED = "error_based"
    BOOLEAN_BASED = "boolean_based"
    TIME_BASED = "time_based"
    UNION_BASED = "union_based"
    STACKED_QUERIES = "stacked_queries"
    SECOND_ORDER = "second_order"
```

### Пример Использования Payload Engine

```python
from modules.payload_engine import PayloadGenerator, PayloadOptimizer, DatabaseType

# Инициализация
generator = PayloadGenerator()
optimizer = PayloadOptimizer()

# Генерация payloads
payloads = generator.generate_all_payloads(DatabaseType.MYSQL)

# Оптимизация
optimized = optimizer.optimize_payload_order(payloads, strategy='effectiveness')

# Использование
for payload in optimized[:10]:  # Первые 10 самых эффективных
    print(payload)
```

## 🔍 Analysis Engine API

### VulnerabilityScanner Class

```python
class VulnerabilityScanner:
    """Сканер уязвимостей SQL injection"""
    
    def __init__(self, session: requests.Session, timeout: int = 30,
                 security_manager=None):
        """
        Инициализация сканера
        
        Args:
            session: HTTP session для запросов
            timeout: Timeout для запросов
            security_manager: Security manager для контроля доступа
        """
        
    def scan_parameter(self, url: str, parameter: str, payloads: List[str],
                      injection_type: InjectionType, db_type: DatabaseType) -> List[Vulnerability]:
        """
        Сканирование параметра на уязвимости
        
        Args:
            url: URL для тестирования
            parameter: Имя параметра для инъекции
            payloads: Список payloads для тестирования
            injection_type: Тип инъекции
            db_type: Тип базы данных
            
        Returns:
            List[Vulnerability]: Список найденных уязвимостей
        """
        
    def _send_payload(self, url: str, parameter: str, payload: str,
                     security_manager=None, auth_token=None) -> Optional[requests.Response]:
        """
        Отправка payload и возврат ответа
        
        Args:
            url: URL для тестирования
            parameter: Имя параметра
            payload: Payload для инъекции
            security_manager: Security manager
            auth_token: Авторизационный токен
            
        Returns:
            Optional[requests.Response]: HTTP ответ или None
        """
```

### Vulnerability Dataclass

```python
@dataclass
class Vulnerability:
    """Представление найденной уязвимости"""
    
    url: str
    parameter: str
    injection_type: str
    database_type: str
    payload: str
    evidence: str
    confidence: float
    response_time: float
    status_code: int
    error_message: Optional[str] = None
    database_info: Optional[Dict[str, Any]] = None
```

### ErrorPatternMatcher Class

```python
class ErrorPatternMatcher:
    """Сопоставитель паттернов ошибок SQL"""
    
    def __init__(self):
        """Инициализация с паттернами ошибок"""
        
    def match_error_patterns(self, response_text: str, 
                            db_type: DatabaseType) -> Optional[str]:
        """
        Поиск паттернов SQL ошибок в ответе
        
        Args:
            response_text: Текст HTTP ответа
            db_type: Тип базы данных для паттернов
            
        Returns:
            Optional[str]: Найденный паттерн или None
        """
        
    def extract_database_info(self, response_text: str) -> Optional[Dict[str, str]]:
        """
        Извлечение информации о базе данных из ответа
        
        Args:
            response_text: Текст HTTP ответа
            
        Returns:
            Optional[Dict]: Информация о БД или None
        """
```

### Пример Использования Analysis Engine

```python
from modules.analysis_engine import VulnerabilityScanner, InjectionType, DatabaseType
import requests

# Инициализация
session = requests.Session()
scanner = VulnerabilityScanner(session, timeout=30)

# Сканирование
vulnerabilities = scanner.scan_parameter(
    url='https://example.com/search.php',
    parameter='q',
    payloads=["' OR 1=1 -- ", "' UNION SELECT NULL -- "],
    injection_type=InjectionType.ERROR_BASED,
    db_type=DatabaseType.MYSQL
)

# Обработка результатов
for vuln in vulnerabilities:
    print(f"Уязвимость найдена на {vuln.url}")
    print(f"Параметр: {vuln.parameter}")
    print(f"Payload: {vuln.payload}")
    print(f"Уверенность: {vuln.confidence}")
```

## ✅ Verification Module API

### VulnerabilityVerifier Class

```python
class VulnerabilityVerifier:
    """Верификатор уязвимостей для снижения false positives"""
    
    def __init__(self, session: requests.Session, timeout: int = 30):
        """
        Инициализация верификатора
        
        Args:
            session: HTTP session
            timeout: Timeout для запросов
        """
        
    def verify_vulnerability(self, vulnerability: Vulnerability) -> VerificationResult:
        """
        Верификация уязвимости
        
        Args:
            vulnerability: Уязвимость для верификации
            
        Returns:
            VerificationResult: Результат верификации
        """
        
    def verify_batch(self, vulnerabilities: List[Vulnerability]) -> List[VerificationResult]:
        """
        Пакетная верификация уязвимостей
        
        Args:
            vulnerabilities: Список уязвимостей
            
        Returns:
            List[VerificationResult]: Список результатов верификации
        """
```

### VerificationResult Dataclass

```python
@dataclass
class VerificationResult:
    """Результат верификации уязвимости"""
    
    vulnerability: Vulnerability
    status: VerificationStatus
    confidence: float
    verification_details: Dict[str, Any]
    timestamp: datetime
```

### VerificationStatus Enum

```python
class VerificationStatus(Enum):
    """Статус верификации"""
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    UNLIKELY = "unlikely"
    FALSE_POSITIVE = "false_positive"
    INCONCLUSIVE = "inconclusive"
```

### Пример Использования Verification

```python
from modules.verification import VulnerabilityVerifier
import requests

# Инициализация
session = requests.Session()
verifier = VulnerabilityVerifier(session, timeout=30)

# Верификация уязвимости
result = verifier.verify_vulnerability(vulnerability)

print(f"Статус: {result.status.value}")
print(f"Уверенность: {result.confidence}")
print(f"Детали: {result.verification_details}")
```

## 🛡️ WAF Bypass Module API

### WAFBypassEngine Class

```python
class WAFBypassEngine:
    """Движок обхода WAF"""
    
    def __init__(self):
        """Инициализация движка"""
        
    def generate_bypass_payloads(self, url: str, parameter: str,
                                injection_type: InjectionType,
                                db_type: DatabaseType) -> List[str]:
        """
        Генерация WAF bypass payloads
        
        Args:
            url: Целевой URL
            parameter: Имя параметра
            injection_type: Тип инъекции
            db_type: Тип базы данных
            
        Returns:
            List[str]: Список bypass payloads
        """
        
    def analyze_waf_response(self, headers: Dict[str, str], 
                           response_text: str) -> Dict[str, Any]:
        """
        Анализ ответа для детекции WAF
        
        Args:
            headers: HTTP заголовки ответа
            response_text: Текст ответа
            
        Returns:
            Dict с информацией о WAF:
            {
                'waf_detected': bool,
                'waf_type': Optional[str],
                'confidence': float
            }
        """
        
    def bypass_payload(self, original_payload: str, headers: Dict[str, str],
                      response_text: str, waf_type: str) -> List[str]:
        """
        Генерация bypass variant для payload
        
        Args:
            original_payload: Оригинальный payload
            headers: HTTP заголовки
            response_text: Текст ответа
            waf_type: Тип WAF
            
        Returns:
            List[str]: Список bypass variants
        """
```

### WAFFingerprint Class

```python
class WAFFingerprint:
    """Фингерпринтинг WAF/IDS"""
    
    def __init__(self):
        """Инициализация с сигнатурами WAF"""
        
    def identify_waf(self, headers: Dict[str, str], 
                    response_text: str) -> Optional[str]:
        """
        Идентификация типа WAF
        
        Args:
            headers: HTTP заголовки
            response_text: Текст ответа
            
        Returns:
            Optional[str]: Тип WAF или None
        """
```

### Пример Использования WAF Bypass

```python
from modules.waf_bypass import WAFBypassEngine

# Инициализация
waf_bypass = WAFBypassEngine()

# Анализ на наличие WAF
waf_analysis = waf_bypass.analyze_waf_response(
    headers=response.headers,
    response_text=response.text
)

if waf_analysis['waf_detected']:
    print(f"WAF detected: {waf_analysis['waf_type']}")
    
    # Генерация bypass payloads
    bypass_payloads = waf_bypass.generate_bypass_payloads(
        url='https://example.com/search.php',
        parameter='q',
        injection_type=InjectionType.ERROR_BASED,
        db_type=DatabaseType.MYSQL
    )
    
    # Тестирование bypass payloads
    for bypass_payload in bypass_payloads:
        # Тестирование...
        pass
```

## 🔒 Enterprise Security API

### EnterpriseSecurityManager Class

```python
class EnterpriseSecurityManager:
    """Enterprise security manager с PDP/PEP архитектурой"""
    
    def __init__(self, config_file: str = "pdp_config.json"):
        """
        Инициализация enterprise security manager
        
        Args:
            config_file: Путь к файлу конфигурации PDP
        """
        
    def authorize_and_enforce(self, request_context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Авторизация и enforcement в одном вызове
        
        Args:
            request_context: Контекст запроса:
                {
                    'target': str,
                    'operation': str,
                    'payload': Optional[str],
                    'user_context': Dict
                }
            
        Returns:
            Tuple[bool, str]: (allowed, message)
        """
        
    def create_isolated_execution(self, request_context: Dict) -> ExecutionContext:
        """
        Создание изолированного контекста выполнения
        
        Args:
            request_context: Контекст запроса
            
        Returns:
            ExecutionContext: Изолированный контекст
        """
        
    def generate_auth_token(self, scope: List[str], security_level: SecurityLevel,
                          capabilities: List[str], expires_hours: int = 24) -> str:
        """
        Генерация авторизационного токена
        
        Args:
            scope: Список разрешенных scope
            security_level: Уровень безопасности
            capabilities: Список разрешенных capabilities
            expires_hours: Время жизни токена в часах
            
        Returns:
            str: Сериализованный токен
        """
```

### CentralPolicyDecisionPoint Class

```python
class CentralPolicyDecisionPoint:
    """Централизованный Policy Decision Point (PDP)"""
    
    def __init__(self, config_file: str = "pdp_config.json"):
        """
        Инициализация PDP
        
        Args:
            config_file: Путь к файлу конфигурации
        """
        
    def evaluate_request(self, request_context: Dict[str, Any]) -> PolicyDecision:
        """
        Централизованная оценка запроса
        
        Args:
            request_context: Контекст запроса
            
        Returns:
            PolicyDecision: Решение политики
        """
        
    def _evaluate_scope(self, target: str) -> Tuple[bool, str, float]:
        """Оценка scope policies"""
        
    def _evaluate_capability(self, operation: str, user_context: Dict,
                           payload: str) -> Tuple[bool, str, float]:
        """Оценка capability policies"""
        
    def _evaluate_context(self, request_context: Dict) -> Tuple[bool, str, float]:
        """Оценка контекстных факторов"""
```

### PolicyDecision Dataclass

```python
@dataclass
class PolicyDecision:
    """Решение политики от PDP"""
    
    decision_id: str
    allowed: bool
    reason: str
    risk_score: float
    expires_at: datetime
    context: Dict[str, Any]
    signature: str
```

### PolicyEnforcementPoint Class

```python
class PolicyEnforcementPoint:
    """Централизованный Policy Enforcement Point (PEP)"""
    
    def __init__(self, pdp: CentralPolicyDecisionPoint):
        """
        Инициализация PEP
        
        Args:
            pdp: Экземпляр PDP
        """
        
    def enforce_policy(self, request_context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Enforcement политики
        
        Args:
            request_context: Контекст запроса
            
        Returns:
            Tuple[bool, str]: (allowed, message)
        """
```

### CryptographicAuditChain Class

```python
class CryptographicAuditChain:
    """Tamper-evident audit chain с Merkle tree"""
    
    def __init__(self, chain_file: str = "audit_chain.db"):
        """
        Инициализация audit chain
        
        Args:
            chain_file: Путь к файлу базы данных
        """
        
    def log_decision(self, decision: PolicyDecision, request_context: Dict):
        """
        Логирование решения в audit chain
        
        Args:
            decision: Решение политики
            request_context: Контекст запроса
        """
        
    def log_isolation(self, exec_context: ExecutionContext, decision_id: str):
        """
        Логирование изоляции
        
        Args:
            exec_context: Контекст выполнения
            decision_id: ID решения политики
        """
        
    def verify_chain_integrity(self) -> bool:
        """
        Проверка целостности audit chain
        
        Returns:
            bool: True если цепь целостна, False если скомпрометирована
        """
        
    def get_audit_entries(self, limit: int = 100) -> List[AuditChain]:
        """
        Получение audit entries
        
        Args:
            limit: Максимальное количество entries
            
        Returns:
            List[AuditChain]: Список audit entries
        """
```

### IsolatedExecutionManager Class

```python
class IsolatedExecutionManager:
    """Менеджер изолированного выполнения"""
    
    def __init__(self):
        """Инициализация менеджера"""
        
    def create_isolated_context(self, request_context: Dict,
                               decision: PolicyDecision) -> ExecutionContext:
        """
        Создание изолированного контекста
        
        Args:
            request_context: Контекст запроса
            decision: Решение политики
            
        Returns:
            ExecutionContext: Изолированный контекст
        """
        
    def cleanup_isolation(self, execution_id: str):
        """
        Очистка изолированного контекста
        
        Args:
            execution_id: ID выполнения
        """
```

### ExecutionContext Dataclass

```python
@dataclass
class ExecutionContext:
    """Изолированный контекст выполнения"""
    
    execution_id: str
    container_id: str
    sandbox_path: str
    network_policy: Dict[str, Any]
    resource_limits: Dict[str, Any]
    isolation_type: str
```

### Пример Использования Enterprise Security

```python
from modules.enterprise_security import EnterpriseSecurityManager

# Инициализация
esm = EnterpriseSecurityManager('pdp_config.json')

# Авторизация и enforcement
request_context = {
    'target': 'https://example.com',
    'operation': 'execute_requests',
    'user_context': {
        'auth_token': 'token123',
        'user_id': 'user456'
    },
    'payload': "' OR 1=1 -- "
}

allowed, message = esm.authorize_and_enforce(request_context)

if allowed:
    print("✅ Авторизация успешна")
    
    # Создание изолированного выполнения
    exec_context = esm.create_isolated_execution(request_context)
    print(f"Isolation ID: {exec_context.execution_id}")
    print(f"Container ID: {exec_context.container_id}")
else:
    print(f"❌ Авторизация отклонена: {message}")
```

## 📊 Reporting Module API

### ReportGenerator Class

```python
class ReportGenerator:
    """Генератор отчетов"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Инициализация генератора отчетов
        
        Args:
            output_dir: Директория для сохранения отчетов
        """
        
    def generate_report(self, scan_summary: ScanSummary, 
                       format: str = "json") -> str:
        """
        Генерация отчета
        
        Args:
            scan_summary: Сводка сканирования
            format: Формат отчета ('json' или 'pdf')
            
        Returns:
            str: Путь к созданному отчету
        """
        
    def generate_json_report(self, scan_summary: ScanSummary) -> str:
        """
        Генерация JSON отчета
        
        Args:
            scan_summary: Сводка сканирования
            
        Returns:
            str: Путь к JSON отчету
        """
        
    def generate_pdf_report(self, scan_summary: ScanSummary) -> str:
        """
        Генерация PDF отчета
        
        Args:
            scan_summary: Сводка сканирования
            
        Returns:
            str: Путь к PDF отчету
        """
```

### ScanSummary Dataclass

```python
@dataclass
class ScanSummary:
    """Сводка результатов сканирования"""
    
    target_url: str
    scan_start: datetime
    scan_end: datetime
    total_duration: float
    vectors_tested: int
    vulnerabilities_found: int
    vulnerabilities: List[Vulnerability]
    verification_results: List[VerificationResult]
    security_events: List[Dict[str, Any]]
```

### Пример Использования Reporting

```python
from modules.reporting import ReportGenerator, ScanSummary

# Инициализация
report_generator = ReportGenerator(output_dir='reports')

# Создание сводки
scan_summary = ScanSummary(
    target_url='https://example.com',
    scan_start=datetime.now(),
    scan_end=datetime.now(),
    total_duration=123.45,
    vectors_tested=50,
    vulnerabilities_found=5,
    vulnerabilities=vulnerabilities,
    verification_results=verification_results,
    security_events=[]
)

# Генерация отчетов
json_report = report_generator.generate_json_report(scan_summary)
pdf_report = report_generator.generate_pdf_report(scan_summary)

print(f"JSON отчет: {json_report}")
print(f"PDF отчет: {pdf_report}")
```

## 🔧 Utility Classes

### SecurityLevel Enum

```python
class SecurityLevel(Enum):
    """Уровни безопасности"""
    BASIC = "basic"
    STANDARD = "standard"
    ANALYSIS = "analysis"
    AUDIT = "audit"
    ENTERPRISE = "enterprise"
```

### SecurityException

```python
class SecurityException(Exception):
    """Исключение безопасности"""
    pass
```

## 📝 Константы и Конфигурация

### Default Configuration

```python
DEFAULT_CONFIG = {
    'crawl_delay': 2.0,
    'crawl_depth': 2,
    'timeout': 30,
    'user_agent': 'SQLiAuditor/2.0',
    'respect_robots': True,
    'database_types': ['mysql', 'postgresql'],
    'verify_vulnerabilities': True,
    'enable_waf_bypass': False
}
```

### Error Patterns

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

## 🚀 Async API

### Async Vulnerability Scanner

```python
class AsyncVulnerabilityScanner:
    """Асинхронный сканер уязвимостей"""
    
    async def scan_parameter_async(self, url: str, parameter: str,
                                   payloads: List[str]) -> List[Vulnerability]:
        """
        Асинхронное сканирование параметра
        
        Args:
            url: URL для тестирования
            parameter: Имя параметра
            payloads: Список payloads
            
        Returns:
            List[Vulnerability]: Список уязвимостей
        """
        
    async def _send_payload_async(self, url: str, parameter: str,
                                  payload: str) -> Optional[aiohttp.ClientResponse]:
        """
        Асинхронная отправка payload
        
        Args:
            url: URL для тестирования
            parameter: Имя параметра
            payload: Payload
            
        Returns:
            Optional[ClientResponse]: HTTP ответ
        """
```

### Пример Использования Async API

```python
import asyncio
from modules.analysis_engine import AsyncVulnerabilityScanner

async def main():
    scanner = AsyncVulnerabilityScanner()
    
    vulnerabilities = await scanner.scan_parameter_async(
        url='https://example.com/search.php',
        parameter='q',
        payloads=["' OR 1=1 -- "]
    )
    
    for vuln in vulnerabilities:
        print(vuln)

asyncio.run(main())
```

---

**Дополнительная документация:**
- Security Architecture Documentation
- Integration Guide
- Troubleshooting Guide
