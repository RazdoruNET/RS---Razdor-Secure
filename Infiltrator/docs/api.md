# 🔌 API Справочник INFILTRATOR v2.0

<div align="center">

**Программный интерфейс и интеграция**

[![API](https://img.shields.io/badge/api-stable-green.svg)](https://github.com/razdor/RS---Razdor-Secure)
[![Complexity](https://img.shields.io/badge/complexity-⭐⭐⭐-orange.svg)](docs/README.md)

</div>

## 📋 Содержание

- [Обзор API](#обзор-api)
- [Основные классы](#основные-классы)
- [Конфигурация](#конфигурация)
- [Методы анализа](#методы-анализа)
- [Обработка результатов](#обработка-результатов)
- [Расширенное API](#расширенное-api)
- [Примеры интеграции](#примеры-интеграции)

---

## 🎯 Обзор API

### Основные компоненты

```python
# Основные импорты
from infiltrator_v2 import (
    InfiltratorV2,           # Основной класс
    InfiltratorConfig,       # Конфигурация
    ReactEndpointExtractor,  # Извлечение эндпоинтов
    ObfuscationResistance,   # Противодействие обфускации
    SSAVariable,            # SSA переменная
    SSAInstruction,         # SSA инструкция
    SSABlock,               # SSA блок
    SSAFunction             # SSA функция
)
```

### Базовый паттерн использования

```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# 1. Конфигурация
config = InfiltratorConfig(
    enable_stealth=True,
    max_bundle_size=50*1024*1024
)

# 2. Создание экземпляра
infiltrator = InfiltratorV2(config)

# 3. Анализ
results = infiltrator.analyze_bundle("bundle.js")

# 4. Обработка результатов
endpoints = results['endpoints']
risk_level = results['risk_assessment']['level']
```

---

## 🏗️ Основные классы

### InfiltratorV2

Основной класс системы анализа.

#### Конструктор

```python
def __init__(self, config: InfiltratorConfig = None):
    """
    Инициализация INFILTRATOR v2.0
    
    Args:
        config: Конфигурация анализа. Если None, используется конфигурация по умолчанию
    """
```

#### Основные методы

##### analyze_bundle()
```python
def analyze_bundle(self, bundle_path: str) -> Dict[str, Any]:
    """
    Анализ JavaScript бандла
    
    Args:
        bundle_path: Путь к JavaScript файлу для анализа
        
    Returns:
        Dict[str, Any]: Результаты анализа
        
    Raises:
        FileNotFoundError: Файл не найден
        BundleTooLargeError: Файл превышает лимит размера
        ParseError: Ошибка парсинга JavaScript
        AnalysisTimeoutError: Превышен таймаут анализа
        
    Example:
        >>> infiltrator = InfiltratorV2()
        >>> results = infiltrator.analyze_bundle("app.js")
        >>> print(f"Found {len(results['endpoints'])} endpoints")
    """
```

##### save_results()
```python
def save_results(self, results: Dict[str, Any], output_path: str):
    """
    Сохранение результатов анализа в файл
    
    Args:
        results: Результаты анализа
        output_path: Путь к выходному файлу
        
    Example:
        >>> infiltrator.save_results(results, "analysis.json")
    """
```

#### Пример использования

```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

# Создание с конфигурацией по умолчанию
infiltrator = InfiltratorV2()

# Анализ файла
try:
    results = infiltrator.analyze_bundle("bundle.js")
    print(f"Analysis complete: {results['risk_assessment']['level']} risk")
    
    # Сохранение результатов
    infiltrator.save_results(results, "results.json")
    
except Exception as e:
    print(f"Analysis failed: {e}")
```

### InfiltratorConfig

Класс конфигурации системы.

#### Параметры

```python
@dataclass
class InfiltratorConfig:
    max_bundle_size: int = 50 * 1024 * 1024          # Макс. размер бандла (50MB)
    enable_stealth: bool = True                       # Стелс-режим
    encryption_key: Optional[bytes] = None           # Ключ шифрования
    output_format: str = "json"                       # Формат вывода
    parallel_analysis: bool = True                    # Параллельный анализ
    max_workers: int = 4                              # Макс. потоков
    timeout_seconds: int = 300                        # Таймаут (сек)
    enable_source_map_recovery: bool = True           # Восстановление source maps
    enable_runtime_instrumentation: bool = True       # Инструментация runtime
```

#### Примеры конфигурации

```python
# Конфигурация для больших файлов
config = InfiltratorConfig(
    max_bundle_size=200*1024*1024,  # 200MB
    parallel_analysis=False,        # Отключить параллелизм
    timeout_seconds=1200             # Увеличить таймаут
)

# Конфигурация для максимальной безопасности
config = InfiltratorConfig(
    enable_stealth=True,
    encryption_key=b"your-secret-key-32-bytes-long",
    enable_source_map_recovery=True
)

# Конфигурация для быстрого анализа
config = InfiltratorConfig(
    enable_stealth=False,
    parallel_analysis=True,
    max_workers=8,
    timeout_seconds=60
)
```

### ReactEndpointExtractor

Специализированный извлекатель эндпоинтов.

#### Методы

##### extract_endpoints()
```python
def extract_endpoints(self, js_code: str) -> List[Dict[str, Any]]:
    """
    Извлечение API эндпоинтов из JavaScript кода
    
    Args:
        js_code: JavaScript код для анализа
        
    Returns:
        List[Dict[str, Any]]: Список найденных эндпоинтов
    """
```

##### Пример использования

```python
from infiltrator_v2 import ReactEndpointExtractor, InfiltratorConfig

config = InfiltratorConfig()
extractor = ReactEndpointExtractor(config)

# Прямой анализ кода
js_code = """
const api = axios.create({
    baseURL: process.env.API_URL
});

api.get('/users');
"""

endpoints = extractor.extract_endpoints(js_code)
for endpoint in endpoints:
    print(f"Found: {endpoint['url']} (risk: {endpoint['risk_level']})")
```

### ObfuscationResistance

Модуль противодействия обфускации.

#### Методы

##### decode_obfuscated_strings()
```python
def decode_obfuscated_strings(self, js_code: str) -> str:
    """
    Декодирование обфусцированных строк
    
    Args:
        js_code: Обфусцированный JavaScript код
        
    Returns:
        str: Декодированный код
    """
```

##### extract_string_arrays()
```python
def extract_string_arrays(self, js_code: str) -> Dict[str, List[str]]:
    """
    Извлечение обфусцированных строковых массивов
    
    Args:
        js_code: JavaScript код
        
    Returns:
        Dict[str, List[str]]: Словарь строковых массивов
    """
```

#### Пример использования

```python
from infiltrator_v2 import ObfuscationResistance, InfiltratorConfig

config = InfiltratorConfig()
resistance = ObfuscationResistance(config)

# Декодирование обфусцированного кода
obfuscated_code = 'var _0x2a4b = ["\\x68\\x74\\x74\\x70\\x73://api.example.com"];'
decoded_code = resistance.decode_obfuscated_strings(obfuscated_code)

# Извлечение строковых массивов
arrays = resistance.extract_string_arrays(obfuscated_code)
print(f"Found {len(arrays)} string arrays")
```

---

## 🔧 SSA Компоненты

### SSAVariable

Представление переменной в SSA форме.

```python
@dataclass(frozen=True)
class SSAVariable:
    name: str
    version: int = 0
    scope: str = "global"
    
    def __str__(self) -> str:
        return f"{self.name}_{self.version}@{self.scope}"
    
    def next_version(self) -> 'SSAVariable':
        """Создание следующей версии переменной"""
        return SSAVariable(self.name, self.version + 1, self.scope)
```

#### Пример использования

```python
from infiltrator_v2 import SSAVariable

# Создание переменной
var = SSAVariable("api_url", 0, "global")
print(str(var))  # "api_url_0@global"

# Следующая версия
next_var = var.next_version()
print(str(next_var))  # "api_url_1@global"
```

### SSAInstruction

Инструкция в SSA форме.

```python
@dataclass
class SSAInstruction:
    opcode: str                    # CALL, ASSIGN, LOAD, STORE, PHI
    operands: List[Union[str, SSAVariable]]
    result: Optional[SSAVariable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.result:
            return f"{self.result} = {self.opcode}({', '.join(map(str, self.operands))})"
        return f"{self.opcode}({', '.join(map(str, self.operands))})"
```

#### Пример использования

```python
from infiltrator_v2 import SSAInstruction, SSAVariable

# Создание инструкции присваивания
result_var = SSAVariable("base_url", 0, "local")
assign_instr = SSAInstruction(
    opcode="ASSIGN",
    operands=["https://api.example.com"],
    result=result_var,
    metadata={'type': 'literal'}
)

print(str(assign_instr))  # "base_url_0@local = ASSIGN(https://api.example.com)"
```

### SSABlock

Базовый блок в SSA.

```python
@dataclass
class SSABlock:
    label: str
    instructions: List[SSAInstruction] = field(default_factory=list)
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    phi_nodes: List[SSAInstruction] = field(default_factory=list)
    
    def add_instruction(self, instr: SSAInstruction):
        """Добавление инструкции в блок"""
        self.instructions.append(instr)
    
    def add_phi_node(self, phi: SSAInstruction):
        """Добавление PHI-узла"""
        self.phi_nodes.append(phi)
```

### SSAFunction

Функция в SSA форме.

```python
@dataclass
class SSAFunction:
    name: str
    blocks: Dict[str, SSABlock] = field(default_factory=dict)
    entry_block: str = "entry"
    exit_block: str = "exit"
    parameters: List[SSAVariable] = field(default_factory=list)
    returns: List[SSAVariable] = field(default_factory=list)
    
    def add_block(self, block: SSABlock):
        """Добавление блока в функцию"""
        self.blocks[block.label] = block
    
    def get_block(self, label: str) -> Optional[SSABlock]:
        """Получение блока по метке"""
        return self.blocks.get(label)
```

---

## 📊 Методы анализа

### Анализ одного файла

```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

def analyze_single_file(file_path: str) -> Dict[str, Any]:
    """Анализ одного JavaScript файла"""
    config = InfiltratorConfig(enable_stealth=True)
    infiltrator = InfiltratorV2(config)
    
    try:
        results = infiltrator.analyze_bundle(file_path)
        return results
    except Exception as e:
        return {'error': str(e)}
```

### Анализ директории

```python
import os
from pathlib import Path
from typing import List, Dict

def analyze_directory(directory: str, pattern: str = "*.js") -> List[Dict[str, Any]]:
    """Анализ всех JavaScript файлов в директории"""
    config = InfiltratorConfig(enable_stealth=True)
    infiltrator = InfiltratorV2(config)
    
    results = []
    
    for js_file in Path(directory).rglob(pattern):
        try:
            result = infiltrator.analyze_bundle(str(js_file))
            results.append(result)
            print(f"Analyzed: {js_file}")
        except Exception as e:
            print(f"Failed to analyze {js_file}: {e}")
    
    return results
```

### Параллельный анализ

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

def analyze_parallel(file_paths: List[str], max_workers: int = 4) -> List[Dict[str, Any]]:
    """Параллельный анализ нескольких файлов"""
    config = InfiltratorConfig(
        parallel_analysis=True,
        max_workers=max_workers
    )
    infiltrator = InfiltratorV2(config)
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(infiltrator.analyze_bundle, path): path
            for path in file_paths
        }
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed: {file_path}")
            except Exception as e:
                print(f"Failed: {file_path} - {e}")
    
    return results
```

---

## 📈 Обработка результатов

### Структура результатов

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
```

### Фильтрация результатов

```python
def filter_high_risk_endpoints(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Фильтрация высокорисковых эндпоинтов"""
    high_risk = []
    for endpoint in results['endpoints']:
        if endpoint['risk_level'] in ['HIGH', 'CRITICAL']:
            high_risk.append(endpoint)
    return high_risk

def filter_by_domain(results: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
    """Фильтрация эндпоинтов по домену"""
    filtered = []
    for endpoint in results['endpoints']:
        url = endpoint.get('url', '')
        if domain in url:
            filtered.append(endpoint)
    return filtered

def get_obfuscated_endpoints(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Получение обфусцированных эндпоинтов"""
    return [ep for ep in results['endpoints'] if ep.get('obfuscated', False)]
```

### Агрегация результатов

```python
from typing import List, Dict
import json

def aggregate_results(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Агрегация результатов из нескольких файлов"""
    aggregated = {
        'total_files': len(results_list),
        'total_endpoints': 0,
        'high_risk_count': 0,
        'critical_risk_count': 0,
        'process_env_vars': set(),
        'domains': set(),
        'files': results_list
    }
    
    for result in results_list:
        if 'error' in result:
            continue
            
        aggregated['total_endpoints'] += len(result['endpoints'])
        aggregated['process_env_vars'].update(result['process_env_vars'])
        
        for endpoint in result['endpoints']:
            if endpoint['risk_level'] == 'HIGH':
                aggregated['high_risk_count'] += 1
            elif endpoint['risk_level'] == 'CRITICAL':
                aggregated['critical_risk_count'] += 1
                
            url = endpoint.get('url', '')
            if url and '://' in url:
                domain = url.split('://')[1].split('/')[0]
                aggregated['domains'].add(domain)
    
    aggregated['process_env_vars'] = list(aggregated['process_env_vars'])
    aggregated['domains'] = list(aggregated['domains'])
    
    return aggregated
```

### Генерация отчетов

```python
def generate_security_report(results: Dict[str, Any]) -> str:
    """Генерация текстового отчета о безопасности"""
    report = []
    report.append("=== SECURITY ANALYSIS REPORT ===\n")
    
    # Общая информация
    report.append(f"Bundle: {results['bundle_path']}")
    report.append(f"Size: {results['bundle_size']:,} bytes")
    report.append(f"Analysis Date: {results['analysis_timestamp']}")
    report.append("")
    
    # Оценка рисков
    risk = results['risk_assessment']
    report.append("=== RISK ASSESSMENT ===")
    report.append(f"Overall Risk Level: {risk['level']}")
    report.append(f"Risk Score: {risk['score']}")
    report.append(f"Total Endpoints: {risk['total_endpoints']}")
    report.append(f"High Risk Endpoints: {risk['high_risk_endpoints']}")
    report.append("")
    
    # Переменные окружения
    if results['process_env_vars']:
        report.append("=== ENVIRONMENT VARIABLES ===")
        for var in results['process_env_vars']:
            report.append(f"- {var}")
        report.append("")
    
    # Эндпоинты
    report.append("=== API ENDPOINTS ===")
    for i, endpoint in enumerate(results['endpoints'], 1):
        report.append(f"{i}. {endpoint.get('url', 'Unknown URL')}")
        report.append(f"   Risk Level: {endpoint['risk_level']}")
        report.append(f"   Call Target: {endpoint['call_target']}")
        if endpoint.get('obfuscated'):
            report.append(f"   ⚠️  OBFUSCATED")
        report.append("")
    
    return "\n".join(report)

def generate_json_report(results: Dict[str, Any], output_path: str):
    """Генерация JSON отчета"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
```

---

## 🔌 Расширенное API

### Кастомные анализаторы

```python
from infiltrator_v2 import ReactEndpointExtractor, InfiltratorConfig

class CustomEndpointExtractor(ReactEndpointExtractor):
    """Кастомный извлекатель эндпоинтов"""
    
    def extract_endpoints(self, js_code: str) -> List[Dict[str, Any]]:
        # Вызов базового метода
        endpoints = super().extract_endpoints(js_code)
        
        # Добавление кастомной логики
        custom_endpoints = self._extract_custom_patterns(js_code)
        endpoints.extend(custom_endpoints)
        
        return endpoints
    
    def _extract_custom_patterns(self, js_code: str) -> List[Dict[str, Any]]:
        """Извлечение кастомных паттернов"""
        custom_endpoints = []
        
        # Пример: поиск GraphQL эндпоинтов
        graphql_pattern = r'graphql\s*\(\s*["\']([^"\']+)["\']'
        matches = re.findall(graphql_pattern, js_code)
        
        for match in matches:
            endpoint_info = {
                'call_target': 'GRAPHQL',
                'url': match,
                'risk_level': 'MEDIUM',
                'custom': True
            }
            custom_endpoints.append(endpoint_info)
        
        return custom_endpoints
```

### Обработчики событий

```python
from typing import Callable

class InfiltratorWithCallbacks(InfiltratorV2):
    """Infiltrator с поддержкой колбэков"""
    
    def __init__(self, config: InfiltratorConfig = None):
        super().__init__(config)
        self.callbacks = {
            'on_start': [],
            'on_progress': [],
            'on_endpoint_found': [],
            'on_complete': [],
            'on_error': []
        }
    
    def add_callback(self, event: str, callback: Callable):
        """Добавление колбэка"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Вызов колбэков"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def analyze_bundle(self, bundle_path: str) -> Dict[str, Any]:
        """Анализ с колбэками"""
        self._trigger_callbacks('on_start', bundle_path)
        
        try:
            results = super().analyze_bundle(bundle_path)
            
            # Колбэк для каждого найденного эндпоинта
            for endpoint in results['endpoints']:
                self._trigger_callbacks('on_endpoint_found', endpoint)
            
            self._trigger_callbacks('on_complete', results)
            return results
            
        except Exception as e:
            self._trigger_callbacks('on_error', e)
            raise

# Пример использования
def on_endpoint_found(endpoint):
    print(f"Found endpoint: {endpoint.get('url')}")

def on_analysis_complete(results):
    print(f"Analysis complete. Risk level: {results['risk_assessment']['level']}")

infiltrator = InfiltratorWithCallbacks()
infiltrator.add_callback('on_endpoint_found', on_endpoint_found)
infiltrator.add_callback('on_complete', on_analysis_complete)
```

### Валидаторы результатов

```python
from abc import ABC, abstractmethod

class ResultValidator(ABC):
    """Базовый класс валидатора"""
    
    @abstractmethod
    def validate(self, results: Dict[str, Any]) -> List[str]:
        """Валидация результатов"""
        pass

class SecurityValidator(ResultValidator):
    """Валидатор безопасности"""
    
    def validate(self, results: Dict[str, Any]) -> List[str]:
        issues = []
        
        # Проверка критических рисков
        if results['risk_assessment']['level'] == 'CRITICAL':
            issues.append("CRITICAL risk level detected")
        
        # Проверка обфусцированных эндпоинтов
        obfuscated_count = sum(1 for ep in results['endpoints'] if ep.get('obfuscated'))
        if obfuscated_count > 0:
            issues.append(f"Found {obfuscated_count} obfuscated endpoints")
        
        # Проверка переменных окружения
        if len(results['process_env_vars']) > 5:
            issues.append("High number of environment variables")
        
        return issues

class PerformanceValidator(ResultValidator):
    """Валидатор производительности"""
    
    def validate(self, results: Dict[str, Any]) -> List[str]:
        issues = []
        
        # Проверка размера бандла
        if results['bundle_size'] > 10 * 1024 * 1024:  # 10MB
            issues.append("Large bundle size may affect performance")
        
        # Проверка количества эндпоинтов
        if len(results['endpoints']) > 50:
            issues.append("High number of API endpoints")
        
        return issues

def validate_results(results: Dict[str, Any], validators: List[ResultValidator]) -> List[str]:
    """Валидация результатов с несколькими валидаторами"""
    all_issues = []
    
    for validator in validators:
        issues = validator.validate(results)
        all_issues.extend(issues)
    
    return all_issues
```

---

## 🔄 Примеры интеграции

### Интеграция с Flask

```python
from flask import Flask, request, jsonify
import tempfile
import os
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_javascript():
    """API endpoint для анализа JavaScript"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Сохранение временного файла
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.js', delete=False) as tmp_file:
        file.save(tmp_file.name)
        tmp_path = tmp_file.name
    
    try:
        # Анализ
        config = InfiltratorConfig(enable_stealth=True)
        infiltrator = InfiltratorV2(config)
        results = infiltrator.analyze_bundle(tmp_path)
        
        # Очистка
        os.unlink(tmp_path)
        
        return jsonify(results)
        
    except Exception as e:
        # Очистка при ошибке
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Интеграция с Django

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import tempfile
import os
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

@csrf_exempt
@require_http_methods(["POST"])
def analyze_javascript(request):
    """Django view для анализа JavaScript"""
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    # Проверка типа файла
    if not file.name.endswith('.js'):
        return JsonResponse({'error': 'Invalid file type'}, status=400)
    
    # Сохранение временного файла
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.js', delete=False) as tmp_file:
        for chunk in file.chunks():
            tmp_file.write(chunk)
        tmp_path = tmp_file.name
    
    try:
        # Анализ
        config = InfiltratorConfig(enable_stealth=True)
        infiltrator = InfiltratorV2(config)
        results = infiltrator.analyze_bundle(tmp_path)
        
        return JsonResponse(results)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    finally:
        # Очистка
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
```

### Интеграция с CI/CD

```python
#!/usr/bin/env python3
"""
CI/CD скрипт для анализа JavaScript файлов
"""

import os
import sys
import json
import argparse
from pathlib import Path
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

def main():
    parser = argparse.ArgumentParser(description='CI/CD JavaScript Analysis')
    parser.add_argument('--directory', required=True, help='Directory to analyze')
    parser.add_argument('--output', default='security_report.json', help='Output file')
    parser.add_argument('--fail-on-critical', action='store_true', help='Fail on critical issues')
    parser.add_argument('--max-risk-score', type=int, default=50, help='Maximum allowed risk score')
    
    args = parser.parse_args()
    
    # Конфигурация
    config = InfiltratorConfig(
        enable_stealth=True,
        parallel_analysis=True,
        max_workers=4
    )
    
    infiltrator = InfiltratorV2(config)
    
    # Анализ всех JS файлов
    results = []
    critical_issues = 0
    total_risk_score = 0
    
    for js_file in Path(args.directory).rglob("*.js"):
        try:
            result = infiltrator.analyze_bundle(str(js_file))
            results.append(result)
            
            # Проверка критических проблем
            if result['risk_assessment']['level'] == 'CRITICAL':
                critical_issues += 1
            
            total_risk_score += result['risk_assessment']['score']
            
            print(f"✓ Analyzed: {js_file} (Risk: {result['risk_assessment']['level']})")
            
        except Exception as e:
            print(f"✗ Failed: {js_file} - {e}")
    
    # Сохранение результатов
    report = {
        'summary': {
            'total_files': len(results),
            'critical_issues': critical_issues,
            'total_risk_score': total_risk_score
        },
        'results': results
    }
    
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nAnalysis complete. Report saved to: {args.output}")
    print(f"Critical issues: {critical_issues}")
    print(f"Total risk score: {total_risk_score}")
    
    # Проверка условий для выхода с ошибкой
    if args.fail_on_critical and critical_issues > 0:
        print("❌ Critical issues found. Failing build.")
        sys.exit(1)
    
    if total_risk_score > args.max_risk_score:
        print(f"❌ Risk score {total_risk_score} exceeds maximum {args.max_risk_score}. Failing build.")
        sys.exit(1)
    
    print("✅ Security check passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Интеграция с pytest

```python
import pytest
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig
import tempfile
import os

@pytest.fixture
def infiltrator():
    """Фикстура для Infiltrator"""
    config = InfiltratorConfig(enable_stealth=True)
    return InfiltratorV2(config)

@pytest.fixture
def sample_js_file():
    """Фикстура для тестового JavaScript файла"""
    js_content = """
    const api = axios.create({
        baseURL: process.env.API_URL,
        timeout: process.env.API_TIMEOUT
    });
    
    api.get('/users');
    api.post('/orders', data);
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_content)
        f.flush()
        yield f.name
    
    os.unlink(f.name)

def test_basic_analysis(infiltrator, sample_js_file):
    """Тест базового анализа"""
    results = infiltrator.analyze_bundle(sample_js_file)
    
    assert 'endpoints' in results
    assert 'process_env_vars' in results
    assert 'risk_assessment' in results
    assert len(results['endpoints']) == 2
    assert 'API_URL' in results['process_env_vars']
    assert 'API_TIMEOUT' in results['process_env_vars']

def test_risk_assessment(infiltrator, sample_js_file):
    """Тест оценки рисков"""
    results = infiltrator.analyze_bundle(sample_js_file)
    
    risk = results['risk_assessment']
    assert 'level' in risk
    assert 'score' in risk
    assert risk['level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    assert isinstance(risk['score'], int)

def test_obfuscated_code(infiltrator):
    """Тест анализа обфусцированного кода"""
    obfuscated_js = """
    var _0x2a4b = ['\\x68\\x74\\x74\\x70\\x73://api.example.com'];
    var _0x1f2c = function() { return axios.get(_0x2a4b[0]); };
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(obfuscated_js)
        f.flush()
        
        results = infiltrator.analyze_bundle(f.name)
        
        assert len(results['endpoints']) > 0
        assert any(ep.get('obfuscated', False) for ep in results['endpoints'])
    
    os.unlink(f.name)
```

---

## 🚨 Обработка ошибок

### Исключения

```python
class InfiltratorError(Exception):
    """Базовое исключение INFILTRATOR"""
    pass

class ParseError(InfiltratorError):
    """Ошибка парсинга JavaScript"""
    pass

class BundleTooLargeError(InfiltratorError):
    """Превышен размер бандла"""
    pass

class AnalysisTimeoutError(InfiltratorError):
    """Превышен таймаут анализа"""
    pass

class ConfigurationError(InfiltratorError):
    """Ошибка конфигурации"""
    pass
```

### Обработка ошибок

```python
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig, InfiltratorError

def safe_analyze(bundle_path: str) -> Dict[str, Any]:
    """Безопасный анализ с обработкой ошибок"""
    config = InfiltratorConfig(timeout_seconds=60)
    infiltrator = InfiltratorV2(config)
    
    try:
        return infiltrator.analyze_bundle(bundle_path)
    except FileNotFoundError:
        return {'error': 'File not found', 'code': 'FILE_NOT_FOUND'}
    except BundleTooLargeError:
        return {'error': 'Bundle too large', 'code': 'BUNDLE_TOO_LARGE'}
    except ParseError:
        return {'error': 'JavaScript parse error', 'code': 'PARSE_ERROR'}
    except AnalysisTimeoutError:
        return {'error': 'Analysis timeout', 'code': 'TIMEOUT'}
    except InfiltratorError as e:
        return {'error': str(e), 'code': 'INFILTRATOR_ERROR'}
    except Exception as e:
        return {'error': f'Unexpected error: {e}', 'code': 'UNKNOWN_ERROR'}
```

---

**[← Назад к навигации](README.md) • [Примеры использования →](examples.md)**
