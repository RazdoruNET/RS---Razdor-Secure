# 🛡️ Основы безопасности

## 📋 Введение в безопасность веб-приложений

Безопасность веб-приложений - это критически важный аспект современной разработки. Prophecy Sentinel помогает выявлять уязвимости на ранних этапах разработки.

---

## 🚨 Основные типы уязвимостей

### SQL Injection
**Что это:** Внедрение вредоносного SQL-кода в запросы к базе данных.

**Пример:**
```sql
-- Уязвимый запрос
SELECT * FROM users WHERE username = 'admin' AND password = 'password' OR '1'='1'

-- Безопасный запрос с параметризацией
SELECT * FROM users WHERE username = ? AND password = ?
```

**Защита:**
- Используйте параметризованные запросы
- Применяйте ORM с защитой от SQLi
- Валидируйте входные данные

### Cross-Site Scripting (XSS)
**Что это:** Внедрение вредоносного JavaScript-кода в веб-страницы.

**Типы XSS:**
- **Reflected XSS:** Атака через URL параметры
- **Stored XSS:** Атака через сохраненные данные
- **DOM-based XSS:** Атака через манипуляцию DOM

**Пример защиты:**
```javascript
// Небезопасно
element.innerHTML = userInput;

// Безопасно
element.textContent = userInput;
// или с санитизацией
element.innerHTML = DOMPurify.sanitize(userInput);
```

### Directory Traversal
**Что это:** Доступ к файлам вне разрешенной директории.

**Пример атаки:**
```
../../../etc/passwd
..%2F..%2F..%2Fetc%2Fpasswd
```

**Защита:**
- Валидация путей файлов
- Использование whitelist разрешенных директорий
- Ограничение прав доступа

---

## 🔒 Принципы безопасной разработки

### 1. Минимизация привилегий
- Давайте только необходимые права
- Используйте разные учетные записи для разных операций
- Регулярно пересматривайте права доступа

### 2. Глубокая защита (Defense in Depth)
- Используйте несколько уровней защиты
- Не полагайтесь на один механизм безопасности
- Комбинируйте различные подходы

### 3. Валидация входных данных
```javascript
// Пример валидации
function validateInput(input, type) {
  const patterns = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    username: /^[a-zA-Z0-9_]{3,20}$/,
    id: /^\d+$/
  };
  
  return patterns[type] ? patterns[type].test(input) : false;
}
```

### 4. Принцип наименьшего удивления
- Предсказуемое поведение системы
- Явные сообщения об ошибках
- Не раскрывайте внутреннюю структуру

---

## 🛠️ Практические советы

### Аутентификация и авторизация
```javascript
// Безопасная проверка пароля
async function verifyPassword(password, hash) {
  const isValid = await bcrypt.compare(password, hash);
  if (!isValid) {
    // Используйте универсальное сообщение
    throw new Error('Invalid credentials');
  }
  return isValid;
}
```

### Защита сессий
```javascript
// Безопасные настройки сессии
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,    // Только HTTPS
    httpOnly: true,  // Защита от XSS
    maxAge: 3600000  // 1 час
  }
}));
```

### Защита от CSRF
```html
<!-- CSRF токен в форме -->
<input type="hidden" name="csrf_token" value="{{csrfToken}}">
```

```javascript
// Проверка CSRF токена
app.post('/api/data', (req, res) => {
  if (req.body.csrf_token !== req.session.csrfToken) {
    return res.status(403).json({ error: 'CSRF token invalid' });
  }
  // Обработка запроса
});
```

---

## 📊 Метрики безопасности

### Критические показатели
- **CVSS Score:** Оценка серьезности уязвимости (0-10)
- **OWASP Top 10:** Соответствие основным угрозам
- **Time to Detection:** Время обнаружения уязвимости
- **Time to Remediation:** Время исправления

### Пример отчета
```json
{
  "scan_date": "2026-05-09T15:20:00Z",
  "total_vulnerabilities": 5,
  "critical": 1,
  "high": 2,
  "medium": 2,
  "low": 0,
  "cvss_average": 6.8
}
```

---

## 🚀 Использование Prophecy Sentinel

### Базовое сканирование
```bash
# Сканирование одного файла
node ProphecySentinel.js --file app.js

# Сканирование директории
node ProphecySentinel.js --directory ./src

# Сканирование с выводом в JSON
node ProphecySentinel.js --directory ./src --format json --output report.json
```

### Интерпретация результатов
```javascript
// Пример результата сканирования
{
  "vulnerabilities": [
    {
      "type": "SQL Injection",
      "severity": "Critical",
      "file": "database.js",
      "line": 45,
      "description": "Potential SQL injection in query construction",
      "recommendation": "Use parameterized queries"
    }
  ]
}
```

---

## 📚 Дополнительные ресурсы

### Документация
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Dictionary](https://cwe.mitre.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Инструменты
- **Burp Suite:** Тестирование веб-приложений
- **OWASP ZAP:** Бесплатный сканер безопасности
- **Nmap:** Сканирование сети и портов

### Курсы и обучение
- [OWASP Security Shepherd](https://github.com/OWASP/SecurityShepherd)
- [Web Security Academy](https://portswigger.net/web-security)
- [Hack The Box](https://www.hackthebox.com/)

---

## ⚠️ Частые ошибки

### 1. Недостаточная валидация
```javascript
// Плохо
app.get('/user/:id', (req, res) => {
  const userId = req.params.id;
  // Прямое использование без валидации
});

// Хорошо
app.get('/user/:id', (req, res) => {
  const userId = parseInt(req.params.id);
  if (isNaN(userId) || userId <= 0) {
    return res.status(400).json({ error: 'Invalid user ID' });
  }
});
```

### 2. Излишняя информация в ошибках
```javascript
// Плохо - раскрывает структуру БД
catch (error) {
  res.status(500).json({ 
    error: 'Database error',
    details: error.message 
  });
}

// Хорошо - универсальное сообщение
catch (error) {
  console.error('Database error:', error);
  res.status(500).json({ 
    error: 'Internal server error' 
  });
}
```

---

## 🎯 Заключение

Безопасность - это непрерывный процесс, а не разовое действие. Prophecy Sentinel помогает автоматизировать обнаружение уязвимостей, но важна также культура безопасности в команде разработки.

**Ключевые принципы:**
- Регулярное сканирование
- Обучение команды
- Code review с фокусом на безопасность
- Быстрое реагирование на уязвимости

Начните с базовых принципов и постепенно усложняйте подходы к безопасности. Prophecy Sentinel будет вашим надежным помощником в этом пути.

---

*Последнее обновление: 9 мая 2026*
