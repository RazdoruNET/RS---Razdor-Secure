# ⚙️ Техническая документация INFILTRATOR v2.0

<div align="center">

**Архитектура, алгоритмы и внутреннее устройство системы**

[![Technical](https://img.shields.io/badge/technical-advanced-purple.svg)](https://github.com/razdor/RS---Razdor-Secure)
[![Complexity](https://img.shields.io/badge/complexity-⭐⭐⭐⭐-red.svg)](docs/README.md)

</div>

## 📋 Содержание

- [Архитектура системы](#архитектура-системы)
- [SSA IR Implementation](#ssa-ir-implementation)
- [Алгоритмы анализа](#алгоритмы-анализа)
- [Противодействие обфускации](#противодействие-обфускации)
- [Data Flow Analysis](#data-flow-analysis)
- [Оптимизация производительности](#оптимизация-производительности)
- [Внутренние форматы данных](#внутренние-форматы-данных)

---

## 🏗️ Архитектура системы

### Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    INFILTRATOR v2.0                        │
├─────────────────────────────────────────────────────────────┤
│  Command Line Interface                                    │
├─────────────────────────────────────────────────────────────┤
│  InfiltratorV2 (Main Controller)                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Endpoint     │ │ Obfuscation     │ │ Risk            │   │
│  │ Extractor    │ │ Resistance      │ │ Assessment      │   │
│  └─────────────┘ └─────────────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  RealWorldBridge (JavaScript → SSA IR)                     │
├─────────────────────────────────────────────────────────────┤
│  SSA IR Engine                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ SSAVariable │ │ SSAInstr    │ │ SSABlock    │         │
│  │ SSAFunction │ │ SSAPhi      │ │ CFG         │         │
│  └─────────────┘ └─────────────┘ └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  JavaScript Parser (Regex-based)                           │
└─────────────────────────────────────────────────────────────┘
```

### Ключевые компоненты

#### 1. InfiltratorV2 (Основной контроллер)
```python
class InfiltratorV2:
    def __init__(self, config: InfiltratorConfig):
        self.config = config
        self.endpoint_extractor = ReactEndpointExtractor(config)
        self.obfuscation_resistance = ObfuscationResistance(config)
        self.encryption_key = self._setup_encryption()
    
    def analyze_bundle(self, bundle_path: str) -> Dict[str, Any]:
        # Основной метод анализа
```

#### 2. RealWorldBridge (Мост JavaScript → SSA)
```python
class RealWorldBridge:
    def parse_bundle(self, js_code: str) -> SSAFunction:
        # Конвертация JavaScript в SSA IR
        return self._parse_with_regex(js_code)
```

#### 3. ReactEndpointExtractor (Извлечение эндпоинтов)
```python
class ReactEndpointExtractor:
    def extract_endpoints(self, js_code: str) -> List[Dict[str, Any]]:
        # Извлечение API эндпоинтов из SSA IR
```

---

## 🔧 SSA IR Implementation

### Static Single Assignment (SSA) в INFILTRATOR

SSA - это форма промежуточного представления (IR), где каждая переменная присваивается только один раз.

#### Core SSA Components

##### SSAVariable
```python
@dataclass(frozen=True)
class SSAVariable:
    name: str
    version: int = 0
    scope: str = "global"
    
    def __str__(self):
        return f"{self.name}_{self.version}@{self.scope}"
    
    def next_version(self):
        return SSAVariable(self.name, self.version + 1, self.scope)
```

**Пример использования:**
```python
# Создание переменной
var1 = SSAVariable("api_url", 0, "global")  # api_url_0@global

# Следующая версия
var2 = var1.next_version()  # api_url_1@global
```

##### SSAInstruction
```python
@dataclass
class SSAInstruction:
    opcode: str  # CALL, ASSIGN, LOAD, STORE, PHI
    operands: List[Union[str, SSAVariable]]
    result: Optional[SSAVariable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Типы инструкций:**
```python
# Присваивание
assign = SSAInstruction(
    opcode="ASSIGN",
    operands=["https://api.example.com"],
    result=SSAVariable("base_url", 0, "local")
)

# Вызов функции
call = SSAInstruction(
    opcode="CALL",
    operands=["axios.get", base_url],
    result=SSAVariable("response", 0, "local")
)

# Загрузка свойства
load = SSAInstruction(
    opcode="LOAD",
    operands=["process.env.API_KEY"],
    result=SSAVariable("api_key", 0, "local")
)
```

##### SSABlock
```python
@dataclass
class SSABlock:
    label: str
    instructions: List[SSAInstruction] = field(default_factory=list)
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    phi_nodes: List[SSAInstruction] = field(default_factory=list)
```

##### SSAFunction
```python
@dataclass
class SSAFunction:
    name: str
    blocks: Dict[str, SSABlock] = field(default_factory=dict)
    entry_block: str = "entry"
    exit_block: str = "exit"
    parameters: List[SSAVariable] = field(default_factory=list)
    returns: List[SSAVariable] = field(default_factory=list)
```

### Пример конвертации JavaScript → SSA

#### Исходный JavaScript:
```javascript
const baseUrl = process.env.API_BASE_URL;
const response = axios.get(baseUrl + '/users');
```

#### SSA представление:
```python
# Блок entry
entry_block = SSABlock("entry")

# Инструкция 1: LOAD process.env.API_BASE_URL
api_key_var = SSAVariable("api_key", 0, "local")
load_instr = SSAInstruction(
    opcode="LOAD",
    operands=["process.env.API_BASE_URL"],
    result=api_key_var
)

# Инструкция 2: ASSIGN baseUrl
base_url_var = SSAVariable("base_url", 0, "local")
assign_instr = SSAInstruction(
    opcode="ASSIGN",
    operands=[api_key_var],
    result=base_url_var
)

# Инструкция 3: CALL axios.get
response_var = SSAVariable("response", 0, "local")
call_instr = SSAInstruction(
    opcode="CALL",
    operands=["axios.get", base_url_var, "/users"],
    result=response_var
)
```

---

## 🧠 Алгоритмы анализа

### 1. Парсинг JavaScript

#### Regex-based подход
```python
def _parse_with_regex(self, js_code: str) -> SSAFunction:
    function = SSAFunction("main")
    entry_block = SSABlock("entry")
    function.add_block(entry_block)
    
    # Извлечение process.env переменных
    process_env_pattern = r'process\.env\.([A-Z_]+)'
    matches = list(re.finditer(process_env_pattern, js_code))
    
    for match in matches:
        var_name = match.group(1)
        env_var = SSAVariable(var_name, 0, "process.env")
        
        assign_instr = SSAInstruction(
            opcode="ASSIGN",
            operands=[f"process.env.{var_name}"],
            result=env_var,
            metadata={'type': 'process_env', 'var': var_name}
        )
        entry_block.add_instruction(assign_instr)
    
    return function
```

#### Извлечение API вызовов
```python
api_patterns = [
    r'axios\.[a-zA-Z]+\s*\(\s*["\']([^"\']+)["\']',
    r'fetch\s*\(\s*["\']([^"\']+)["\']',
    r'\.get\s*\(\s*["\']([^"\']+)["\']',
    r'\.post\s*\(\s*["\']([^"\']+)["\']'
]

for pattern in api_patterns:
    for match in re.finditer(pattern, js_code):
        url = match.group(1)
        result_var = self._create_ssa_variable("api_call")
        
        call_instr = SSAInstruction(
            opcode="CALL",
            operands=[f"API_CALL({url})"],
            result=result_var,
            metadata={'url': url, 'type': 'api_call'}
        )
```

### 2. Taint Analysis

#### Инициализация зараженных источников
```python
def _initialize_tainted_sources(self, function: SSAFunction):
    for block_name, block in function.blocks.items():
        for instr in block.instructions:
            if instr.opcode == "LOAD":
                operands = instr.operands
                if operands and "process.env" in str(operands[0]):
                    if instr.result:
                        self.tainted_vars.add(instr.result)
```

#### Распространение заражения
```python
def _analyze_dataflow(self, function: SSAFunction):
    worklist = deque(self.tainted_vars)
    
    while worklist:
        current_var = worklist.popleft()
        
        for block_name, block in function.blocks.items():
            for instr in block.instructions:
                if self._uses_variable(instr, current_var):
                    new_tainted = self._process_instruction(instr, current_var)
                    for new_var in new_tainted:
                        if new_var not in self.tainted_vars:
                            self.tainted_vars.add(new_var)
                            worklist.append(new_var)
```

### 3. Risk Assessment

#### Алгоритм оценки рисков
```python
def _assess_risk(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not endpoints:
        return {'level': 'LOW', 'score': 0}
    
    high_risk_count = sum(1 for ep in endpoints if ep.get('risk_level') == 'HIGH')
    medium_risk_count = sum(1 for ep in endpoints if ep.get('risk_level') == 'MEDIUM')
    
    total_score = high_risk_count * 10 + medium_risk_count * 5
    
    if total_score >= 50:
        level = 'CRITICAL'
    elif total_score >= 20:
        level = 'HIGH'
    elif total_score >= 10:
        level = 'MEDIUM'
    else:
        level = 'LOW'
    
    return {
        'level': level,
        'score': total_score,
        'high_risk_endpoints': high_risk_count,
        'medium_risk_endpoints': medium_risk_count,
        'total_endpoints': len(endpoints)
    }
```

---

## 🛡️ Противодействие обфускации

### ObfuscationResistance Module

#### 1. Декодирование hex строк
```python
def decode_obfuscated_strings(self, js_code: str) -> str:
    decoded_code = js_code
    
    # Pattern 1: Hex string concatenation
    hex_pattern = r'\\x([0-9a-fA-F]{2})'
    decoded_code = re.sub(hex_pattern, lambda m: chr(int(m.group(1), 16)), decoded_code)
    
    return decoded_code
```

**Пример:**
```javascript
// Обфусцированный
'\x68\x74\x74\x70\x73\x3a\x2f\x2f\x61\x70\x69\x2e\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d'

// Декодированный
'https://api.example.com'
```

#### 2. Unicode escape sequences
```python
unicode_pattern = r'\\u([0-9a-fA-F]{4})'
decoded_code = re.sub(unicode_pattern, lambda m: chr(int(m.group(1), 16)), decoded_code)
```

#### 3. String.fromCharCode chains
```python
def _decode_fromcharcode(self, match):
    try:
        codes = [int(x.strip()) for x in match.group(1).split(',')]
        return '"' + ''.join(chr(code) for code in codes) + '"'
    except:
        return match.group(0)
```

#### 4. Base64 декодирование
```python
b64_pattern = r'atob\(["\']([^"\']+)["\']\)'
decoded_code = re.sub(b64_pattern, lambda m: base64.b64decode(m.group(1)).decode(), decoded_code)
```

### Извлечение строковых массивов

#### Обнаружение обфусцированных массивов
```python
def extract_string_arrays(self, js_code: str) -> Dict[str, List[str]]:
    string_arrays = {}
    
    # Pattern: var _0xabc = ["string1", "string2", ...]
    array_pattern = r'(?:var|let|const)\s+([a-zA-Z_$][0-9a-zA-Z_$]*)\s*=\s*\[([^\]]+)\]'
    
    for match in re.finditer(array_pattern, js_code):
        array_name = match.group(1)
        array_content = match.group(2)
        
        strings = []
        string_pattern = r'["\']([^"\']+)["\']'
        for str_match in re.finditer(string_pattern, array_content):
            strings.append(str_match.group(1))
        
        if strings:
            string_arrays[array_name] = strings
    
    return string_arrays
```

**Пример:**
```javascript
// Обфусцированный
var _0x2a4b = [
    '\x68\x74\x74\x70\x73\x3a\x2f\x2f\x61\x70\x69\x2e\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d',
    '\x2f\x61\x70\x69\x2f\x76\x31\x2f\x75\x73\x65\x72\x73'
];

// Результат extraction
{
    "_0x2a4b": [
        "https://api.example.com",
        "/api/v1/users"
    ]
}
```

---

## 🔄 Data Flow Analysis

### Worklist Algorithm

#### Основной алгоритм
```python
def analyze_dataflow(self, function: SSAFunction):
    worklist = deque()
    
    # Инициализация
    for var in self.tainted_vars:
        worklist.append(var)
    
    # Основной цикл
    while worklist:
        current_var = worklist.popleft()
        
        # Поиск инструкций, использующих переменную
        for block_name, block in function.blocks.items():
            for instr in block.instructions:
                if self._uses_variable(instr, current_var):
                    new_tainted = self._process_instruction(instr, current_var)
                    
                    # Добавление новых зараженных переменных
                    for new_var in new_tainted:
                        if new_var not in self.tainted_vars:
                            self.tainted_vars.add(new_var)
                            worklist.append(new_var)
```

#### Обработка инструкций
```python
def _process_instruction(self, instr: SSAInstruction, tainted_var: SSAVariable) -> List[SSAVariable]:
    newly_tainted = []
    
    if instr.opcode == "CALL":
        if self._is_api_call(str(instr.operands[0])):
            if instr.result:
                newly_tainted.append(instr.result)
                self._record_api_call(instr, tainted_var)
    
    elif instr.opcode == "ASSIGN" and instr.result:
        newly_tainted.append(instr.result)
    
    elif instr.opcode == "LOAD" and instr.result:
        newly_tainted.append(instr.result)
    
    return newly_tainted
```

### Control Flow Graph (CFG)

#### Построение CFG
```python
def _process_if_statement(self, node: dict, function: SSAFunction, block: SSABlock):
    # Создание условных блоков
    then_block = SSABlock(f"then_{self.block_counter}")
    else_block = SSABlock(f"else_{self.block_counter}")
    merge_block = SSABlock(f"merge_{self.block_counter}")
    
    self.block_counter += 1
    
    # Добавление блоков в функцию
    function.add_block(then_block)
    function.add_block(else_block)
    function.add_block(merge_block)
    
    # Установка ребер CFG
    block.successors.add(then_block.label)
    block.successors.add(else_block.label)
    then_block.predecessors.add(block.label)
    else_block.predecessors.add(block.label)
```

---

## ⚡ Оптимизация производительности

### 1. Параллельная обработка

#### Конфигурация
```python
@dataclass
class InfiltratorConfig:
    parallel_analysis: bool = True
    max_workers: int = 4
    timeout_seconds: int = 300
```

#### Реализация
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def analyze_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
    if not self.config.parallel_analysis:
        return [self.analyze_bundle(path) for path in file_paths]
    
    results = []
    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
        future_to_file = {
            executor.submit(self.analyze_bundle, path): path 
            for path in file_paths
        }
        
        for future in as_completed(future_to_file):
            try:
                result = future.result(timeout=self.config.timeout_seconds)
                results.append(result)
            except Exception as e:
                print(f"Analysis failed: {e}")
    
    return results
```

### 2. Оптимизация памяти

#### Ленивая загрузка
```python
def analyze_bundle_lazy(self, bundle_path: str) -> Iterator[Dict[str, Any]]:
    """Постепенный анализ для больших файлов"""
    with open(bundle_path, 'r', encoding='utf-8') as f:
        for chunk in self._read_chunks(f):
            yield self._analyze_chunk(chunk)

def _read_chunks(self, file, chunk_size=1024*1024):  # 1MB chunks
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk
```

#### Кэширование результатов
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _cached_regex_search(self, pattern: str, text: str) -> List[str]:
    return re.findall(pattern, text)
```

### 3. Профилирование производительности

#### Метрики производительности
```python
import time
import psutil
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    analysis_time: float
    memory_usage: float
    cpu_usage: float
    file_size: int

def analyze_with_metrics(self, bundle_path: str) -> Tuple[Dict[str, Any], PerformanceMetrics]:
    start_time = time.time()
    process = psutil.Process()
    
    # Анализ
    results = self.analyze_bundle(bundle_path)
    
    # Метрики
    metrics = PerformanceMetrics(
        analysis_time=time.time() - start_time,
        memory_usage=process.memory_info().rss / 1024 / 1024,  # MB
        cpu_usage=process.cpu_percent(),
        file_size=os.path.getsize(bundle_path)
    )
    
    return results, metrics
```

---

## 📊 Внутренние форматы данных

### 1. Структура результатов анализа

```python
@dataclass
class AnalysisResult:
    bundle_path: str
    bundle_size: int
    endpoints: List[EndpointInfo]
    process_env_vars: List[str]
    analysis_timestamp: str
    infiltrator_version: str
    risk_assessment: RiskAssessment
    encrypted: Optional[str] = None

@dataclass
class EndpointInfo:
    call_target: str
    tainted_source: str
    arguments: List[str]
    url: Optional[str]
    location: Optional[Dict[str, int]]
    instruction: str
    risk_level: str
    obfuscated: bool = False

@dataclass
class RiskAssessment:
    level: str
    score: int
    high_risk_endpoints: int
    medium_risk_endpoints: int
    total_endpoints: int
```

### 2. Формат конфигурации

```python
@dataclass
class InfiltratorConfig:
    max_bundle_size: int = 50 * 1024 * 1024  # 50MB
    enable_stealth: bool = True
    encryption_key: Optional[bytes] = None
    output_format: str = "json"
    parallel_analysis: bool = True
    max_workers: int = 4
    timeout_seconds: int = 300
    enable_source_map_recovery: bool = True
    enable_runtime_instrumentation: bool = True
```

### 3. Сериализация данных

#### JSON сериализация
```python
def serialize_results(self, results: AnalysisResult) -> str:
    return json.dumps(asdict(results), indent=2, default=str)

def deserialize_results(self, data: str) -> AnalysisResult:
    return AnalysisResult(**json.loads(data))
```

#### Шифрование результатов
```python
def _encrypt_results(self, results: Dict[str, Any]) -> str:
    data = json.dumps(results).encode()
    key = self.encryption_key
    
    # XOR encryption
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    return base64.b64encode(encrypted).decode()
```

---

## 🔍 Алгоритмы обнаружения паттернов

### 1. Process.env паттерны

```python
PROCESS_ENV_PATTERNS = [
    r'process\.env\.([A-Z_]+)',                    # Прямой доступ
    r'process\.env\["([^"]+)"\]',                  # Квадратные скобки
    r'process\.env\[\'([^\']+)\'\]',               # Одинарные кавычки
    r'env\.([A-Z_]+)',                             # Короткая форма
]
```

### 2. API вызовы

```python
API_PATTERNS = {
    'axios': [
        r'axios\.get\s*\(\s*["\']([^"\']+)["\']',
        r'axios\.post\s*\(\s*["\']([^"\']+)["\']',
        r'axios\.put\s*\(\s*["\']([^"\']+)["\']',
        r'axios\.delete\s*\(\s*["\']([^"\']+)["\']',
    ],
    'fetch': [
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'fetch\s*\(\s*([^,\s]+)',
    ],
    'xhr': [
        r'\.open\s*\(\s*["\']([^"\']+)["\']',
        r'XMLHttpRequest',
    ]
}
```

### 3. Обфускационные паттерны

```python
OBFUSCATION_PATTERNS = [
    r'_0x[a-f0-9]+\s*=\s*\[([^\]]+)\]',           # Hex массивы
    r'\\x([0-9a-fA-F]{2})',                       # Hex символы
    r'\\u([0-9a-fA-F]{4})',                       # Unicode
    r'String\.fromCharCode\(([^)]+)\)',           # fromCharCode
    r'atob\(["\']([^"\']+)["\']\)',               # Base64
]
```

---

## 🧪 Тестирование и валидация

### 1. Unit тесты

```python
import unittest
from unittest.mock import patch, MagicMock

class TestInfiltrator(unittest.TestCase):
    def setUp(self):
        self.config = InfiltratorConfig()
        self.infiltrator = InfiltratorV2(self.config)
    
    def test_process_env_extraction(self):
        js_code = 'const api = process.env.API_URL;'
        result = self.infiltrator.analyze_bundle(js_code)
        self.assertIn('API_URL', result['process_env_vars'])
    
    def test_api_endpoint_detection(self):
        js_code = 'axios.get("https://api.example.com/users");'
        result = self.infiltrator.analyze_bundle(js_code)
        self.assertEqual(len(result['endpoints']), 1)
        self.assertEqual(result['endpoints'][0]['url'], 'https://api.example.com/users')
```

### 2. Интеграционные тесты

```python
class TestIntegration(unittest.TestCase):
    def test_full_analysis_pipeline(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(TEST_BUNDLE_CODE)
            f.flush()
            
            result = self.infiltrator.analyze_bundle(f.name)
            
            self.assertIn('endpoints', result)
            self.assertIn('risk_assessment', result)
            self.assertGreater(len(result['endpoints']), 0)
```

### 3. Бенчмарки производительности

```python
def benchmark_analysis():
    test_files = generate_test_files(sizes=[1, 10, 50, 100])  # MB
    
    for file_path, size in test_files:
        start_time = time.time()
        result = infiltrator.analyze_bundle(file_path)
        analysis_time = time.time() - start_time
        
        print(f"Size: {size}MB, Time: {analysis_time:.2f}s, Endpoints: {len(result['endpoints'])}")
```

---

## 🔄 Взаимодействие компонентов

### Sequence Diagram

```
User → CLI → InfiltratorV2 → RealWorldBridge → SSA IR
                ↓
                ↓
         ObfuscationResistance
                ↓
                ↓
         ReactEndpointExtractor
                ↓
                ↓
         RiskAssessment
                ↓
                ↓
         Results (JSON)
```

### Data Flow

```
JavaScript Code → Regex Parser → SSA Instructions → Taint Analysis → Endpoint Detection → Risk Assessment
```

---

## 📈 Метрики и мониторинг

### 1. Метрики анализа

```python
@dataclass
class AnalysisMetrics:
    total_files_analyzed: int
    total_endpoints_found: int
    high_risk_endpoints: int
    average_analysis_time: float
    memory_usage_peak: float
    false_positive_rate: float
```

### 2. Мониторинг производительности

```python
def monitor_performance():
    metrics = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'analysis_time': time.time() - start_time,
    }
    return metrics
```

---

## 🚨 Обработка ошибок

### 1. Типы ошибок

```python
class InfiltratorError(Exception):
    """Base exception for INFILTRATOR"""
    pass

class ParseError(InfiltratorError):
    """JavaScript parsing failed"""
    pass

class BundleTooLargeError(InfiltratorError):
    """Bundle exceeds size limit"""
    pass

class AnalysisTimeoutError(InfiltratorError):
    """Analysis took too long"""
    pass
```

### 2. Стратегии восстановления

```python
def analyze_with_fallback(self, bundle_path: str):
    try:
        return self.analyze_bundle(bundle_path)
    except ParseError:
        # Попытка с стелс-режимом
        config = InfiltratorConfig(enable_stealth=True)
        stealth_infiltrator = InfiltratorV2(config)
        return stealth_infiltrator.analyze_bundle(bundle_path)
    except BundleTooLargeError:
        # Попытка с увеличенным лимитом
        config = InfiltratorConfig(max_bundle_size=200*1024*1024)
        large_infiltrator = InfiltratorV2(config)
        return large_infiltrator.analyze_bundle(bundle_path)
```

---

## 🔮 Будущие улучшения

### 1. Алгоритмические улучшения

- **Machine Learning** для обнаружения паттернов
- **Symbolic Execution** для глубокого анализа
- **Type Inference** для улучшения точности
- **Cross-file Analysis** для межмодульного анализа

### 2. Архитектурные улучшения

- **Microservices Architecture** для масштабируемости
- **Stream Processing** для реального времени
- **Distributed Analysis** для кластерных вычислений
- **GPU Acceleration** для параллельной обработки

---

**[← Назад к навигации](README.md) • [API справочник →](api.md)**
