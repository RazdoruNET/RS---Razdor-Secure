# 💡 Частые ошибки

## 📋 Обзор

Наиболее частые ошибки в разработке SQL-кода и способы их предотвращения с помощью SQLGuard Pro.

---

## 🚨 Критические ошибки

### 1. Прямая конкатенация SQL

**❌ Плохо:**
```javascript
const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
```

**✅ Хорошо:**
```javascript
const query = 'SELECT * FROM users WHERE username = ? AND password = ?';
const result = await db.query(query, [username, password]);
```

**Обнаружение SQLGuard Pro:**
```bash
# SQLGuard Pro обнаружит эту уязвимость
sqlguard analyze file.js

# Результат:
{
  "type": "SQL Injection",
  "severity": "Critical",
  "line": 15,
  "description": "Direct string concatenation in SQL query",
  "recommendation": "Use parameterized queries"
}
```

### 2. Динамическое формирование SQL

**❌ Плохо:**
```javascript
let query = 'SELECT * FROM products';
if (category) {
  query += ` WHERE category = '${category}'`;
}
if (minPrice) {
  query += ` AND price >= ${minPrice}`;
}
```

**✅ Хорошо:**
```javascript
let query = 'SELECT * FROM products WHERE 1=1';
const params = [];
if (category) {
  query += ' AND category = ?';
  params.push(category);
}
if (minPrice) {
  query += ' AND price >= ?';
  params.push(minPrice);
}
```

### 3. Использование eval для SQL

**❌ Плохо:**
```javascript
const sqlFunction = `SELECT ${columns} FROM ${table} WHERE ${condition}`;
const result = await db.query(sqlFunction);
```

**✅ Хорошо:**
```javascript
const allowedColumns = ['id', 'name', 'price'];
const allowedTables = ['products', 'users'];

if (!allowedColumns.includes(columns) || !allowedTables.includes(table)) {
  throw new Error('Invalid columns or table');
}

const query = `SELECT ${columns} FROM ${table} WHERE ${condition}`;
```

---

## ⚠️ Серьезные ошибки

### 4. Hardcoded учетные данные

**❌ Плохо:**
```javascript
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password123',
  database: 'myapp'
});
```

**✅ Хорошо:**
```javascript
const connection = mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME
});
```

**Обнаружение SQLGuard Pro:**
```json
{
  "type": "Hardcoded Credentials",
  "severity": "High",
  "line": 25,
  "description": "Database credentials hardcoded in source code",
  "recommendation": "Use environment variables"
}
```

### 5. Отсутствие валидации входных данных

**❌ Плохо:**
```javascript
app.get('/users/:id', (req, res) => {
  const query = `SELECT * FROM users WHERE id = ${req.params.id}`;
  db.query(query, (err, results) => {
    res.json(results);
  });
});
```

**✅ Хорошо:**
```javascript
app.get('/users/:id', (req, res) => {
  const id = parseInt(req.params.id);
  if (isNaN(id) || id <= 0) {
    return res.status(400).json({ error: 'Invalid user ID' });
  }
  
  const query = 'SELECT * FROM users WHERE id = ?';
  db.query(query, [id], (err, results) => {
    res.json(results);
  });
});
```

### 6. Небезопасные хранимые процедуры

**❌ Плохо:**
```javascript
const query = `CALL GetUserProfile('${userId}', '${userRole}')`;
```

**✅ Хорошо:**
```javascript
const query = 'CALL GetUserProfile(?, ?)';
db.query(query, [userId, userRole], callback);
```

---

## 📡 Ошибки среднего уровня

### 7. Неэффективные запросы

**❌ Плохо:**
```javascript
// N+1 проблема
const users = await db.query('SELECT * FROM users');
for (const user of users) {
  const orders = await db.query(`SELECT * FROM orders WHERE user_id = ${user.id}`);
  user.orders = orders;
}
```

**✅ Хорошо:**
```javascript
// Один запрос с JOIN
const query = `
  SELECT u.*, o.* 
  FROM users u 
  LEFT JOIN orders o ON u.id = o.user_id
`;
const results = await db.query(query);
```

**Обнаружение SQLGuard Pro:**
```json
{
  "type": "Performance Issue",
  "severity": "Medium",
  "line": 45,
  "description": "Potential N+1 query problem",
  "recommendation": "Use JOIN or batch queries"
}
```

### 8. Отсутствие индексов

**❌ Плохо:**
```sql
-- Запрос без индекса
SELECT * FROM orders WHERE customer_id = 12345 AND status = 'pending';
```

**✅ Хорошо:**
```sql
-- С индексом
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
```

### 9. Использование SELECT *

**❌ Плохо:**
```javascript
const query = 'SELECT * FROM users WHERE id = ?';
```

**✅ Хорошо:**
```javascript
const query = 'SELECT id, name, email FROM users WHERE id = ?';
```

---

## 🟢 Мелкие ошибки

### 10. Отсутствие LIMIT

**❌ Плохо:**
```javascript
const query = 'SELECT * FROM logs WHERE created_at > ?';
```

**✅ Хорошо:**
```javascript
const query = 'SELECT * FROM logs WHERE created_at > ? LIMIT 1000';
```

### 11. Отсутствие обработки ошибок

**❌ Плохо:**
```javascript
const result = await db.query(sql);
return result;
```

**✅ Хорошо:**
```javascript
try {
  const result = await db.query(sql);
  return result;
} catch (error) {
  console.error('Database error:', error);
  throw new Error('Database operation failed');
}
```

---

## 🔧 Как SQLGuard Pro помогает

### Автоматическое обнаружение

```bash
# Запуск сканирования
sqlguard analyze --directory ./src --verbose

# SQLGuard Pro автоматически обнаружит:
# - SQL инъекции
# - Hardcoded credentials
# - Performance проблемы
# - Нарушения лучших практик
```

### Подробные рекомендации

```javascript
// SQLGuard Pro предоставит конкретные рекомендации:
{
  "vulnerability": {
    "type": "SQL Injection",
    "line": 23,
    "code": "const query = `SELECT * FROM users WHERE name = '${name}'`;",
    "recommendation": {
      "title": "Use parameterized queries",
      "description": "Replace string concatenation with parameter binding",
      "example": {
        "before": "const query = `SELECT * FROM users WHERE name = '${name}'`;",
        "after": "const query = 'SELECT * FROM users WHERE name = ?';\nconst result = await db.query(query, [name]);"
      }
    }
  }
}
```

### Интеграция с IDE

```javascript
// VS Code extension покажет подсветку:
function getUser(id) {
  // 🚨 SQL Injection Risk: String concatenation detected
  const query = `SELECT * FROM users WHERE id = ${id}`;
  return db.query(query);
}

function getUserSafe(id) {
  // ✅ Safe: Parameterized query
  const query = 'SELECT * FROM users WHERE id = ?';
  return db.query(query, [id]);
}
```

---

## 📚 Проверочный лист

### Перед коммитом кода

```bash
# Запуск полной проверки
sqlguard analyze --directory . --format json --output pre-commit-report.json

# Проверка конкретных файлов
sqlguard analyze --file models/user.js --file models/order.js

# Проверка с высокими стандартами
sqlguard analyze --directory . --security-level strict
```

### Code Review чеклист

- [ ] Все SQL запросы используют параметризацию
- [ ] Отсутствуют hardcoded учетные данные
- [ ] Входные данные валидируются
- [ ] Запросы оптимизированы (нет N+1 проблем)
- [ ] Используются индексы для частых запросов
- [ ] Обрабатываются ошибки базы данных
- [ ] Не используется SELECT * без необходимости
- [ ] Применяются LIMIT для больших выборок

---

## 🛠️ Инструменты предотвращения

### ORM с защитой

```javascript
// Sequelize
const user = await User.findOne({
  where: {
    id: userId
  }
});

// TypeORM
const user = await userRepository.findOne({
  where: { id: userId }
});

// Prisma
const user = await prisma.user.findUnique({
  where: { id: userId }
});
```

### Query Builders

```javascript
// Knex.js
const query = knex('users')
  .where('id', userId)
  .select('id', 'name', 'email');

// Query Builder для Node.js
const query = qb.select('id', 'name', 'email')
  .from('users')
  .where('id', userId);
```

### Валидация данных

```javascript
// Joi
const schema = Joi.object({
  id: Joi.number().integer().positive().required(),
  name: Joi.string().min(1).max(100).required()
});

const { error, value } = schema.validate(req.body);
if (error) {
  return res.status(400).json({ error: error.details[0].message });
}

// Zod
const userSchema = z.object({
  id: z.number().int().positive(),
  name: z.string().min(1).max(100)
});

try {
  const validated = userSchema.parse(req.body);
  // Используем validated данные
} catch (error) {
  return res.status(400).json({ error: error.message });
}
```

---

## 🎯 Лучшие практики

### 1. Принцип наименьших привилегий

```javascript
// Разные пользователи для разных операций
const readUser = await db.authenticate('app_readonly', 'readonly_password');
const writeUser = await db.authenticate('app_writer', 'writer_password');
const adminUser = await db.authenticate('app_admin', 'admin_password');
```

### 2. Валидация на всех уровнях

```javascript
// Валидация в middleware
app.use((req, res, next) => {
  if (req.query.id && !/^\d+$/.test(req.query.id)) {
    return res.status(400).json({ error: 'Invalid ID format' });
  }
  next();
});

// Валидация в бизнес-логике
function getUserById(id) {
  if (!Number.isInteger(id) || id <= 0) {
    throw new Error('Invalid user ID');
  }
  // ...
}

// Валидация в базе данных
const query = 'SELECT * FROM users WHERE id = ? AND id > 0';
```

### 3. Логирование безопасности

```javascript
function logSecurityEvent(event, details) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    event: event,
    details: details,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  };
  
  // Запись в отдельный лог безопасности
  securityLogger.warn(JSON.stringify(logEntry));
}

// Использование
if (sqlInjectionDetected) {
  logSecurityEvent('SQL_INJECTION_ATTEMPT', {
    query: maliciousQuery,
    parameters: req.body
  });
}
```

---

## 📚 Дополнительные ресурсы

### Документация
- [OWASP SQL Injection Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [SQLGuard Pro Documentation](https://docs.sqlguard-pro.com)

### Инструменты
- [SQLMap](https://sqlmap.org/) - Тестирование на SQL инъекции
- [Burp Suite](https://portswigger.net/burp) - Тестирование веб-приложений
- [OWASP ZAP](https://www.zaproxy.org/) - Бесплатный сканер безопасности

### Обучение
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [Hack The Box SQL Injection Track](https://www.hackthebox.com/learn/modules/sql-injection)
- [SQLGuard Pro Training](https://training.sqlguard-pro.com)

---

## 🔄 Непрерывное улучшение

### Регулярное сканирование

```bash
# Добавить в package.json
{
  "scripts": {
    "security-scan": "sqlguard analyze --directory . --format html --output security-report.html",
    "security-check": "sqlguard analyze --directory . --security-level strict"
  }
}

# Запуск перед коммитом
npm run security-check

# Генерация отчета для команды
npm run security-scan
```

### Интеграция с Git hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running SQLGuard Pro security scan..."
npm run security-check

if [ $? -ne 0 ]; then
  echo "❌ Security issues found. Please fix before committing."
  exit 1
fi

echo "✅ Security scan passed."
```

### Мониторинг в CI/CD

```yaml
# GitHub Actions
name: Security Check
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run SQLGuard Pro
        run: |
          npm install -g sqlguard-pro
          sqlguard analyze --directory . --format sarif --output security-results.sarif
      - name: Upload Results
        uses: github/codeql-action/upload-sarif@v1
        with:
          sarif_file: security-results.sarif
```

---

## 🎯 Заключение

Избегание этих частых ошибок значительно повысит безопасность вашего приложения:

1. **Всегда используйте параметризованные запросы**
2. **Никогда не доверяйте пользовательскому вводу**
3. **Валидируйте данные на всех уровнях**
4. **Используйте ORM или query builders**
5. **Регулярно сканируйте код с SQLGuard Pro**
6. **Следуйте принципу наименьших привилегий**
7. **Логируйте события безопасности**

SQLGuard Pro поможет вам обнаружить эти ошибки на ранних стадиях и предоставить конкретные рекомендации по их исправлению.

---

*Последнее обновление: 9 мая 2026*
