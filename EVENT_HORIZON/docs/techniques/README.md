# EVENT HORIZON - Учебник по техникам безопасности

## 🎯 Для кого этот учебник

Этот учебник предназначен для:
- **Мидл разработчиков**, которые хотят понять внутренние механизмы безопасности
- **Security исследователей**, интересующихся методами тестирования
- **Скрипт киди**, которые хотят перейти на профессиональный уровень

## 📚 Структура учебника

### Часть 1: Базовые техники
- Traffic Polymorphism (Морфизм трафика)
- SQL Inference (Вывод SQL)
- Input Normalization (Нормализация ввода)
- Async Request Patterns (Асинхронные паттерны)

### Часть 2: Продвинутые техники
- Header Injection Detection (Обнаружение инъекций заголовков)
- Timing Side Channels (Тайминг side channels)
- Race Condition Testing (Тестирование race conditions)
- Memory Leak Detection (Обнаружение утечек памяти)

### Часть 3: Супер техники
- Causal Graph Analysis (Анализ причинно-следственных графов)
- Formal Invariant Verification (Формальная верификация инвариантов)
- Distributed Consensus Testing (Тестирование распределённого консенсуса)
- Machine Learning Security (Безопасность машинного обучения)

---

# ЧАСТЬ 1: БАЗОВЫЕ ТЕХНИКИ

## 🌊 Техника 1: Traffic Polymorphism (Морфизм трафика)

### Что это такое?

Traffic Polymorphism - это техника генерации разнообразных вариантов HTTP запросов для тестирования устойчивости систем к разным типам трафика.

### Зачем это нужно?

Системы часто обрабатывают одинаковые данные по-разному в зависимости от:
- Порядка заголовков
- Регистра символов
- Кодировки
- Пробелов
- Дубликатов

### Как это работает в EVENT HORIZON?

```python
from traffic_polymorphism.header_engine import HeaderVariabilityEngine

# Создаём движок генерации заголовков
engine = HeaderVariabilityEngine()

# Генерируем 100 разных вариантов заголовков
for i in range(100):
    headers = engine.generate_headers(complexity="high")
    
    # Каждый вариант уникален
    print(f"Вариант {i}: {headers}")
```

### Практический пример

**Сценариё:** Тестируем, как сайт обрабатывает User-Agent

```python
# Базовый запрос
headers1 = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html'
}

# Морфизм - меняем порядок
headers2 = {
    'Accept': 'text/html',
    'User-Agent': 'Mozilla/5.0'
}

# Морфизм - меняем регистр
headers3 = {
    'user-agent': 'Mozilla/5.0',
    'accept': 'text/html'
}

# Морфизм - добавляем пробелы
headers4 = {
    'User-Agent': ' Mozilla/5.0 ',
    'Accept': 'text/html'
}

# Тестируем все варианты
for headers in [headers1, headers2, headers3, headers4]:
    response = requests.get('https://example.com', headers=headers)
    print(f"Status: {response.status_code}")
```

### Что искать в результатах?

**Нормальное поведение:**
- Все запросы возвращают одинаковый статус
- Время ответа примерно одинаковое
- Контент идентичный

**Проблемы:**
- Разные статусы для разных вариантов
- Значительные различия во времени ответа
- Разный контент

### Самостоятельная практика

**Задание 1:** Создайте 50 вариантов заголовков и протестируйте сайт
```python
# Ваш код здесь
engine = HeaderVariabilityEngine()
# ... генерация и тестирование
```

**Задание 2:** Найдите сайт, который по-разному обрабатывает порядок заголовков

---

## 🔍 Техника 2: SQL Inference (Вывод SQL)

### Что это такое?

SQL Inference - это техника анализа поведения системы при выполнении SQL запросов для выявления уязвимостей без прямого доступа к базе данных.

### Зачем это нужно?

Найти уязвимости SQL injection, не атакуя напрямую, а анализируя:
- Время ответа
- Статусы ответов
- Содержимое ошибок
- Хэши контента

### Как это работает в EVENT HORIZON?

```python
from sql_inference.sql_analyzer import SQLInferenceEngine

# Создаём движок анализа SQL
engine = SQLInferenceEngine()

# Генерируем безопасные варианты запросов
queries = engine.generate_safe_variants("SELECT * FROM users WHERE id = 1")

# Анализируем ответы
for query in queries:
    response = execute_query(query)
    analysis = engine.analyze_response(response)
    
    print(f"Запрос: {query}")
    print(f"Анализ: {analysis}")
```

### Практический пример

**Сценариё:** Тестируем API с параметром id

```python
# Базовый запрос
query1 = "SELECT * FROM users WHERE id = 1"

# Вариант с кавычками
query2 = "SELECT * FROM users WHERE id = '1'"

# Вариант с пробелами
query3 = "SELECT * FROM users WHERE id =  1"

# Вариант с комментариями
query4 = "SELECT * FROM users WHERE id = 1 -- comment"

# Тестируем все варианты
for query in [query1, query2, query3, query4]:
    response = execute_query(query)
    
    # Анализируем
    if response.time > 1.0:
        print(f"Медленный ответ на: {query}")
    
    if "error" in response.content.lower():
        print(f"Ошибка в ответе на: {query}")
```

### Timing Side Channel (Тайминг side channel)

Это продвинутая техника SQL inference:

```python
import time

def timing_attack(query):
    """Анализ времени выполнения запроса"""
    times = []
    
    for i in range(10):
        start = time.time()
        response = execute_query(query)
        end = time.time()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    std_dev = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5
    
    print(f"Среднее время: {avg_time:.3f}s")
    print(f"Стандартное отклонение: {std_dev:.3f}s")
    
    # Если стандартное отклонение высокое - возможно уязвимость
    if std_dev > 0.1:
        print("⚠️ Возможная уязвимость timing side channel")
```

### Что искать в результатах?

**Нормальное поведение:**
- Все запросы выполняются за похожее время
- Одинаковые статусы
- Одинаковые ошибки (если есть)

**Проблемы:**
- Значительные различия во времени выполнения
- Разные статусы для похожих запросов
- Разное содержимое ошибок

### Самостоятельная практика

**Задание 1:** Создайте 10 безопасных вариантов SQL запроса
```python
# Ваш код здесь
engine = SQLInferenceEngine()
# ... генерация и анализ
```

**Задание 2:** Реализуйте timing attack анализ

---

## 🧪 Техника 3: Input Normalization (Нормализация ввода)

### Что это такое?

Input Normalization - это техника тестирования того, как система нормализирует и обрабатывает различные варианты одного и того же ввода.

### Зачем это нужно?

Найти несоответствия в обработке ввода между:
- WAF (Web Application Firewall)
- Прокси
- Приложением
- Базой данных

### Как это работает в EVENT HORIZON?

```python
from input_normalization.normalization_tester import InputNormalizationTester

# Создаём тестер нормализации
tester = InputNormalizationTester()

# Генерируем тестовые варианты
test_cases = tester.generate_case_variations("admin")

# Тестируем все варианты
for test_case in test_cases:
    response = tester.test_variant(test_case)
    print(f"Вариант: {test_case.input}")
    print(f"Результат: {response.normalized}")
```

### Практический пример

**Сценариё:** Тестируем поле username

```python
# Базовый ввод
input1 = "admin"

# Вариант с заглавными буквами
input2 = "ADMIN"

# Вариант с пробелами
input3 = " admin "

# Вариант с Unicode
input4 = "аdmin"  # кириллица вместо латиницы

# Вариант с кодированием
input5 = "%61dmin"  # URL encoding

# Тестируем все варианты
for input_var in [input1, input2, input3, input4, input5]:
    response = test_login(input_var)
    
    print(f"Ввод: {input_var}")
    print(f"Статус: {response.status}")
    print(f"Нормализовано: {response.normalized_input}")
```

### Charset Testing (Тестирование кодировок)

```python
from input_normalization.charset_handler import CharsetHandler

handler = CharsetHandler()

# Тестируем разные кодировки
inputs = ["admin", "admin", "admin"]
charsets = ["utf-8", "latin-1", "windows-1252"]

for input_var, charset in zip(inputs, charsets):
    encoded = handler.encode(input_var, charset)
    response = test_input(encoded)
    
    print(f"Кодировка: {charset}")
    print(f"Результат: {response}")
```

### Что искать в результатах?

**Нормальное поведение:**
- Все варианты нормализуются одинаково
- Одинаковый результат для эквивалентных вводов
- Корректная обработка всех кодировок

**Проблемы:**
- Разные результаты для эквивалентных вводов
- Некорректная обработка кодировок
- Пропуск через WAF но блокировка приложением

### Самостоятельная практика

**Задание 1:** Создайте 20 вариантов ввода "password"
```python
# Ваш код здесь
tester = InputNormalizationTester()
# ... генерация и тестирование
```

**Задание 2:** Найдите сайт с несоответствием нормализации

---

## ⚡ Техника 4: Async Request Patterns (Асинхронные паттерны)

### Что это такое?

Async Request Patterns - это техника выполнения множества параллельных запросов для тестирования производительности и устойчивости системы.

### Зачем это нужно?

Проверить, как система справляется с:
- Параллельными запросами
- Высокими нагрузками
- Race conditions
- Deadlocks

### Как это работает в EVENT HORIZON?

```python
from async_engine.request_engine import AsyncRequestEngine
import asyncio

# Создаём асинхронный движок
engine = AsyncRequestEngine()

# Создаём 100 параллельных запросов
requests = [
    RequestConfig(url='https://example.com', method='GET')
    for _ in range(100)
]

# Выполняем параллельно
results = await engine.execute_requests(requests)

# Анализируем результаты
successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]

print(f"Успешно: {len(successful)}")
print(f"Неудачно: {len(failed)}")
```

### Rate Limiting Testing (Тестирование rate limiting)

```python
import asyncio
import time

async def test_rate_limit():
    """Тестируем rate limiting"""
    results = []
    
    # Отправляем 20 запросов за 1 секунду
    start = time.time()
    for i in range(20):
        response = await send_request()
        results.append(response)
        
        # Очень маленькая задержка
        await asyncio.sleep(0.01)
    
    end = time.time()
    
    # Анализируем
    rate_limited = sum(1 for r in results if r.status == 429)
    print(f"Rate limited запросов: {rate_limited}")
    print(f"Время выполнения: {end - start:.2f}s")

asyncio.run(test_rate_limit())
```

### Race Condition Testing (Тестирование race conditions)

```python
async def test_race_condition():
    """Тестируем race conditions"""
    
    # Создаём 10 параллельных запросов на один ресурс
    tasks = []
    for i in range(10):
        task = asyncio.create_task(
            send_request(f'/api/resource/{i}')
        )
        tasks.append(task)
    
    # Выполняем параллельно
    results = await asyncio.gather(*tasks)
    
    # Проверяем на конфликты
    conflicts = [r for r in results if 'conflict' in r.content.lower()]
    print(f"Конфликтов: {len(conflicts)}")

asyncio.run(test_race_condition())
```

### Что искать в результатах?

**Нормальное поведение:**
- Система справляется с нагрузкой
- Rate limiting работает корректно
- Нет race conditions

**Проблемы:**
- Система падает под нагрузкой
- Rate limiting не работает или слишком агрессивен
- Race conditions приводят к ошибкам

### Самостоятельная практика

**Задание 1:** Создайте нагрузочный тест с 50 параллельными запросами
```python
# Ваш код здесь
engine = AsyncRequestEngine()
# ... создание и выполнение запросов
```

**Задание 2:** Найдите порог rate limiting системы

---

# ЧАСТЬ 2: ПРОДВИНУТЫЕ ТЕХНИКИ

## 🎭 Техника 5: Header Injection Detection (Обнаружение инъекций заголовков)

### Что это такое?

Header Injection - это техника обнаружения уязвимостей, связанных с инъекцией данных через HTTP заголовки.

### Зачем это нужно?

Найти уязвимости типа:
- CRLF Injection
- HTTP Request Splitting
- Header Spoofing
- Cache Poisoning

### Практический пример

```python
def test_header_injection():
    """Тестируем инъекции заголовков"""
    
    # CRLF Injection
    malicious_headers = {
        'User-Agent': 'Mozilla/5.0\r\nX-Injected: true',
        'Accept': 'text/html\r\nX-Another: value'
    }
    
    response = send_request('https://example.com', headers=malicious_headers)
    
    # Проверяем, инъекция прошла
    if 'X-Injected' in response.headers:
        print("⚠️ Обнаружена CRLF инъекция!")
    
    # HTTP Request Splitting
    split_headers = {
        'User-Agent': 'Mozilla/5.0\r\n\r\nGET /admin HTTP/1.1\r\nHost: evil.com'
    }
    
    response = send_request('https://example.com', headers=split_headers)
    
    # Проверяем на request splitting
    if response.status == 400 or response.status == 418:
        print("⚠️ Возможна HTTP Request Splitting")
```

### Cache Poisoning (Отравление кэша)

```python
def test_cache_poisoning():
    """Тестируем cache poisoning"""
    
    # Отправляем запрос с вредоносным заголовком
    malicious_headers = {
        'X-Forwarded-Host': 'evil.com',
        'Host': 'example.com'
    }
    
    response1 = send_request('/page', headers=malicious_headers)
    
    # Отправляем нормальный запрос
    response2 = send_request('/page')
    
    # Если кэш отравлен, второй запрос вернёт вредоносный контент
    if 'evil.com' in response2.content:
        print("⚠️ Обнаружено Cache Poisoning!")
```

### Самостоятельная практика

**Задание 1:** Реализуйте детектор CRLF инъекций

---

## ⏱️ Техника 6: Timing Side Channels (Тайминг side channels)

### Что это такое?

Timing Side Channels - это техника анализа времени выполнения операций для получения информации о внутреннем состоянии системы.

### Зачем это нужно?

Найти уязвимости через:
- Анализ времени ответов
- Статистический анализ
- Pattern recognition

### Практический пример

```python
import time
import statistics

def timing_analysis(target_function, inputs):
    """Анализ времени выполнения"""
    
    times = []
    for input_var in inputs:
        start = time.time()
        result = target_function(input_var)
        end = time.time()
        times.append(end - start)
    
    # Статистический анализ
    mean = statistics.mean(times)
    median = statistics.median(times)
    stdev = statistics.stdev(times)
    
    print(f"Среднее: {mean:.4f}s")
    print(f"Медиана: {median:.4f}s")
    print(f StdDev: {stdev:.4f}s")
    
    # Анализ аномалий
    for i, t in enumerate(times):
        if abs(t - mean) > 2 * stdev:
            print(f"⚠️ Аномалия в запросе {i}: {t:.4f}s")
            print(f"   Ввод: {inputs[i]}")
```

### Blind SQL Injection через Timing

```python
async def blind_sql_timing(query):
    """Blind SQL через timing"""
    
    # Базовый запрос
    base_query = f"SELECT * FROM users WHERE id = 1 AND {query}"
    
    times = []
    for _ in range(10):
        start = time.time()
        response = await execute_query(base_query)
        end = time.time()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    
    # Если условие истинно, запрос будет медленнее
    if avg_time > 1.0:
        print(f"Условие '{query}' вероятно истинно")
    else:
        print(f"Условие '{query}' вероятно ложно")
```

### Самостоятельная практика

**Задание 1:** Реализуйте детектор timing аномалий

---

## 🏁 Техника 7: Race Condition Testing (Тестирование race conditions)

### Что это такое?

Race Condition Testing - это техника поиска уязвимостей, возникающих при одновременном доступе к общим ресурсам.

### Зачем это нужно?

Найти уязвимости типа:
- TOCTOU (Time-of-check to time-of-use)
- Double-spend
- Privilege escalation
- Data corruption

### Практический пример

```python
import asyncio
import random

async def test_toctou():
    """Тестируем TOCTOU уязвимость"""
    
    # Шаг 1: Проверка доступа
    has_access = await check_access('/file')
    
    # Шаг 2: Изменение состояния между проверкой и использованием
    if has_access:
        # Имитация задержки
        await asyncio.sleep(0.1)
        
        # Шаг 3: Использование
        result = await read_file('/file')
        
        # Если состояние изменилось, возможна уязвимость
        if not result.success:
            print("⚠️ Возможна TOCTOU уязвимость")

async def test_double_spend():
    """Тестируем double spend"""
    
    # Два параллельных запроса на трату одного ресурса
    tasks = []
    for i in range(2):
        task = asyncio.create_task(spend_resource('user123', 100))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # Если оба запроса успешны - double spend
    if all(r.success for r in results):
        print("⚠️ Обнаружена Double Spend уязвимость!")
```

### Самостоятельная практика

**Задание 1:** Реализуйте детектор race conditions

---

## 💾 Техника 8: Memory Leak Detection (Обнаружение утечек памяти)

### Что это такое?

Memory Leak Detection - это техника выявления утечек памяти в долгоживущих процессах.

### Зачем это нужно?

Найти проблемы:
- Утечки памяти
- Неэффективное использование памяти
- Memory bloat

### Практический пример

```python
import psutil
import time

def monitor_memory(process_name):
    """Мониторинг памяти процесса"""
    
    process = None
    for proc in psutil.process_iter(['name', 'pid']):
        if process_name in proc.info['name']:
            process = proc
            break
    
    if not process:
        print("Процесс не найден")
        return
    
    memory_samples = []
    
    for i in range(60):  # Мониторим 60 секунд
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_samples.append(memory_mb)
        
        print(f"Память: {memory_mb:.2f} MB")
        time.sleep(1)
    
    # Анализ тренда
    if memory_samples[-1] > memory_samples[0] * 1.5:
        print("⚠️ Обнаружена утечка памяти!")
        print(f"   Начало: {memory_samples[0]:.2f} MB")
        print(f"   Конец: {memory_samples[-1]:.2f} MB")
```

### Самостоятельная практика

**Задание 1:** Реализуйте детектор утечек памяти

---

# ЧАСТЬ 3: СУПЕР ТЕХНИКИ

## 🧠 Техника 9: Causal Graph Analysis (Анализ причинно-следственных графов)

### Что это такое?

Causal Graph Analysis - это продвинутая техника анализа причинно-следственных связей между событиями в системе.

### Зачем это нужно?

Понять:
- Корневые причины проблем
- Цепочки событий
- Скрытые зависимости
- Emergent behavior

### Практический пример

```python
from observation_plane import CausalGraphBuilder, CausalEvent

# Создаём граф причинно-следственных связей
graph = CausalGraphBuilder()

# Добавляем события
event1 = CausalEvent(
    event_id="e1",
    timestamp=time.time(),
    event_type="request_start",
    causation_id=None,
    data={"url": "/api/users"}
)

event2 = CausalEvent(
    event_id="e2",
    timestamp=time.time() + 0.1,
    event_type="db_query",
    causation_id="e1",  # e2 вызвано e1
    data={"query": "SELECT * FROM users"}
)

event3 = CausalEvent(
    event_id="e3",
    timestamp=time.time() + 0.2,
    event_type="response",
    causation_id="e2",  # e3 вызвано e2
    data={"status": 200}
)

# Добавляем в граф
await graph.add_event(event1)
await graph.add_event(event2)
await graph.add_event(event3)

# Находим корневую причину
root_cause = await graph.find_root_cause("e3")
print(f"Корневая причина: {root_cause.event_id}")

# Анализируем паттерны
patterns = await graph.analyze_event_patterns()
print(f"Обнаруженные паттерны: {patterns}")
```

### Root Cause Analysis (Анализ корневых причин)

```python
async def analyze_incident(error_event_id):
    """Анализ инцидента"""
    
    # Получаем цепочку событий
    causal_chain = []
    current_event_id = error_event_id
    
    while current_event_id:
        event = graph.get_event(current_event_id)
        causal_chain.append(event)
        current_event_id = event.causation_id
    
    # Анализируем цепочку
    print("Цепочка событий:")
    for i, event in enumerate(reversed(causal_chain)):
        print(f"{i}. {event.event_type}: {event.data}")
    
    # Находим корневую причину
    root_cause = causal_chain[-1]
    print(f"\nКорневая причина: {root_cause.event_type}")
    print(f"Данные: {root_cause.data}")
```

### Самостоятельная практика

**Задание 1:** Реализуйте анализ причинно-следственных связей

---

## 🔐 Техника 10: Formal Invariant Verification (Формальная верификация инвариантов)

### Что это такое?

Formal Invariant Verification - это математический подход к проверке соблюдения правил безопасности в системе.

### Зачем это нужно?

Гарантировать:
- Безопасность системы
- Корректность поведения
- Отсутствие emergent behavior

### Практический пример

```python
from architecture.formal_state_model import SystemInvariant

# Определяем инвариант
def no_self_modification_invariant(state):
    """Система не должна модифицировать саму себя"""
    control_state = state.get_domain_state(DomainType.CONTROL)
    return not control_state.get('self_modified', False)

# Создаём инвариант
invariant = SystemInvariant(
    invariant_id="no_self_modification",
    description="Система не должна модифицировать саму себя",
    domain=DomainType.CONTROL,
    validator=no_self_modification_invariant,
    violation_severity="critical"
)

# Добавляем в модель состояния
state_model.add_invariant(invariant)

# Проверяем при каждом переходе
def check_invariants(state):
    """Проверяем все инварианты"""
    for invariant in state_model.invariants.values():
        if not invariant.validate(state):
            print(f"⚠️ Нарушен инвариант: {invariant.invariant_id}")
            print(f"   Описание: {invariant.description}")
            return False
    return True
```

### Temporal Logic (Темпоральная логика)

```python
class TemporalInvariant:
    """Темопральный инвариант"""
    
    def __init__(self, formula):
        self.formula = formula
        self.history = []
    
    def check(self, event):
        """Проверяем темпоральную формулу"""
        self.history.append(event)
        
        # Пример: ◇(request_processed) - запрос будет обработан
        if "request" in event.type and "processed" in event.type:
            return True
        
        # Пример: □(no_self_modification) - никогда не модифицирует саму себя
        if "self_modification" in event.type:
            return False
        
        return True
```

### Самостоятельная практика

**Задание 1:** Реализуйте формальную верификацию инвариантов

---

## 🌐 Техника 11: Distributed Consensus Testing (Тестирование распределённого консенсуса)

### Что это такое?

Distributed Consensus Testing - это техника проверки корректности алгоритмов консенсуса в распределённых системах.

### Зачем это нужно?

Проверить:
- Корректность консенсуса
- Fault tolerance
- Network partition handling
- Leader election

### Практический пример

```python
class ConsensusTester:
    """Тестер консенсуса"""
    
    def __init__(self, nodes):
        self.nodes = nodes
        self.values = {}
    
    async def test_consensus(self, value):
        """Тестируем достижение консенсуса"""
        
        # Отправляем значение всем узлам
        tasks = []
        for node in self.nodes:
            task = asyncio.create_task(node.propose(value))
            tasks.append(task)
        
        # Ждём завершения
        results = await asyncio.gather(*tasks)
        
        # Проверяем консенсус
        unique_values = set(results)
        
        if len(unique_values) == 1:
            print("✅ Консенсус достигнут")
            return True
        else:
            print(f"⚠️ Консенсус не достигнут: {unique_values}")
            return False
    
    async def test_partition(self):
        """Тестируем сетевой partition"""
        
        # Симулируем partition
        partition1 = self.nodes[:len(self.nodes)//2]
        partition2 = self.nodes[len(self.nodes)//2:]
        
        # Отправляем разные значения
        await self.propose_to_partition(partition1, "value1")
        await self.propose_to_partition(partition2, "value2")
        
        # Восстанавливаем соединение
        await self.restore_connection()
        
        # Проверяем консенсус после восстановления
        result = await self.test_consensus("value3")
        
        return result
```

### Самостоятельная практика

**Задание 1:** Реализуйте тестер консенсуса

---

## 🤖 Техника 12: Machine Learning Security (Безопасность машинного обучения)

### Что это такое?

Machine Learning Security - это техника защиты и тестирования ML систем от adversarial attacks.

### Зачем это нужно?

Защитить от:
- Adversarial examples
- Model inversion
- Data poisoning
- Model extraction

### Практический пример

```python
class AdversarialExampleTester:
    """Тестер adversarial examples"""
    
    def __init__(self, model):
        self.model = model
    
    def generate_adversarial(self, input_data, epsilon=0.01):
        """Генерируем adversarial example"""
        
        # Вычисляем градиент
        gradient = self.compute_gradient(input_data)
        
        # Добавляем perturbation
        adversarial = input_data + epsilon * gradient.sign()
        
        return adversarial
    
    def test_robustness(self, input_data, epsilons):
        """Тестируем устойчивость"""
        
        results = []
        for epsilon in epsilons:
            adversarial = self.generate_adversarial(input_data, epsilon)
            
            # Классифицируем
            original_pred = self.model.predict(input_data)
            adversarial_pred = self.model.predict(adversarial)
            
            # Если предсказания изменились - уязвимость
            if original_pred != adversarial_pred:
                print(f"⚠️ Уязвимость при epsilon={epsilon}")
                results.append(False)
            else:
                results.append(True)
        
        return results
```

### Model Inversion Attack (Атака инверсии модели)

```python
async def model_inversion_attack(model, target_output):
    """Атака инверсии модели"""
    
    # Пытаемся восстановить вход по выходу
    reconstructed_input = None
    best_similarity = 0
    
    for _ in range(1000):
        # Генерируем случайный вход
        random_input = generate_random_input()
        
        # Получаем предсказание
        prediction = model.predict(random_input)
        
        # Сравниваем с целевым выходом
        similarity = compare_outputs(prediction, target_output)
        
        if similarity > best_similarity:
            best_similarity = similarity
            reconstructed_input = random_input
    
    if best_similarity > 0.9:
        print("⚠️ Обнаружена уязвимость Model Inversion")
        return reconstructed_input
    
    return None
```

### Самостоятельная практика

**Задание 1:** Реализуйте детектор adversarial examples

---

# 🎓 ЗАКЛЮЧЕНИЕ

## Что вы узнали

В этом учебнике мы рассмотрели:

### Базовые техники:
- Traffic Polymorphism - генерация разнообразного трафика
- SQL Inference - анализ поведения SQL запросов
- Input Normalization - тестирование обработки ввода
- Async Request Patterns - параллельное выполнение запросов

### Продвинутые техники:
- Header Injection Detection - обнаружение инъекций заголовков
- Timing Side Channels - анализ времени выполнения
- Race Condition Testing - тестирование конкурентных условий
- Memory Leak Detection - обнаружение утечек памяти

### Супер техники:
- Causal Graph Analysis - анализ причинно-следственных связей
- Formal Invariant Verification - формальная верификация
- Distributed Consensus Testing - тестирование консенсуса
- Machine Learning Security - безопасность ML

## Следующие шаги

1. Практикуйтесь с каждой техникой
2. Создайте собственные сценарии тестирования
3. Изучайте EVENT HORIZON исходный код
4. Экспериментируйте в изолированной среде

## Важные напоминания

- Всегда тестируйте в изолированной среде
- Не используйте для атак на реальные системы
- Соблюдайте этические принципы
- Получайте разрешение для внешнего тестирования

## Дополнительные ресурсы

- [Документация EVENT HORIZON](../README.md)
- [API Reference](../api/README.md)
- [Troubleshooting Guide](../troubleshooting/README.md)

**Удачи в изучении техник безопасности!** 🚀
