# 🚀 Установка и настройка Prophecy Sentinel

Полное руководство по установке и первоначальной настройке системы

---

## 📋 Системные требования

### 🔧 Минимальные требования
- **Node.js**: 18.0.0 или выше
- **npm**: 8.0.0 или выше
- **Оперативная память**: 4GB RAM
- **Диск**: 2GB свободного места
- **ОС**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 💡 Рекомендуемые требования
- **Node.js**: 20.0.0 или выше
- **npm**: 10.0.0 или выше
- **Оперативная память**: 8GB RAM
- **Диск**: 5GB свободного места
- **Процессор**: 4+ ядра

---

## 📥 Шаг 1: Клонирование репозитория

### 🌐 Через Git
```bash
git clone https://github.com/prophecy-sentinel/prophecy-sentinel.git
cd prophecy-sentinel
```

### 📦 Через ZIP
1. Скачайте [ZIP архив](https://github.com/prophecy-sentinel/prophecy-sentinel/archive/refs/heads/main.zip)
2. Распакуйте архив
3. Переименуйте папку в `prophecy-sentinel`
4. Откройте терминал в этой папке

---

## 🔧 Шаг 2: Установка зависимостей

### 📦 Базовая установка
```bash
npm install
```

### 🎭 Установка Playwright
```bash
npx playwright install
```

### ✅ Проверка установки
```bash
npm test
```

---

## 🛡️ Шаг 3: Настройка безопасности

### 🔐 Создание конфигурации
Создайте файл `.env` в корневой директории:

```env
# Базовые настройки
NODE_ENV=development
LOG_LEVEL=info

# Настройки безопасности
ALLOWED_DOMAINS=localhost,127.0.0.1
REQUIRE_AUTHORIZATION=true
ENABLE_AUDIT_LOG=true

# Настройки сканера
DEFAULT_CONFIDENCE_THRESHOLD=0.5
MAX_CONCURRENT_REQUESTS=5
RATE_LIMIT_DELAY=1000
```

### 🔒 Права доступа
```bash
# Установка прав на Linux/macOS
chmod +x ProphecySentinel.js

# Создание директории для логов
mkdir logs
chmod 700 logs
```

---

## 🧪 Шаг 4: Тестовая установка

### 🏗️ Запуск тестовых целей
```bash
# DVWA (Damn Vulnerable Web Application)
docker-compose -f docker-compose.dvwa.yml up -d

# OWASP Juice Shop
docker-compose -f docker-compose.juiceshop.yml up -d
```

### 🧪 Первое сканирование
```bash
# Тестовое сканирование DVWA
node ProphecySentinel.js localhost:8080

# Тестовое сканирование Juice Shop
node ProphecySentinel.js localhost:3000
```

---

## 🔧 Шаг 5: Конфигурация сканера

### ⚙️ Базовые настройки
```javascript
// Создайте файл config.js
const ProphecySentinel = require('./ProphecySentinel');

const sentinel = new ProphecySentinel();

// Настройки производительности
sentinel.concurrencyLimit = 5;
sentinel.rateLimitDelay = 1000;
sentinel.requestTimeout = 10000;
sentinel.maxRetries = 3;

// Пороги уверенности
sentinel.confidenceThreshold = 0.5;

// Настройки безопасности
sentinel.userAgent = 'ProphecySentinel/1.0 Security Assessment';
```

### 🎭 Настройка Playwright
```javascript
// config-playwright.js
const { PlaywrightXSSConfirmation } = require('./src/confirmation/PlaywrightXSSConfirmation');

const xssConfirm = new PlaywrightXSSConfirmation();

// Настройки браузера
await xssConfirm.initialize({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});
```

---

## 🐛 Устранение проблем

### ❌ Частые проблемы

#### Ошибка: "Cannot find module 'playwright'"
```bash
# Решение
npm install playwright
npx playwright install
```

#### Ошибка: "Permission denied"
```bash
# Решение (Linux/macOS)
sudo chown -R $USER:$USER /path/to/prophecy-sentinel
chmod +x ProphecySentinel.js
```

#### Ошибка: "Port already in use"
```bash
# Решение
lsof -i :8080
kill -9 <PID>
```

#### Ошибка: "Docker not found"
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 🔍 Диагностика

#### Проверка Node.js
```bash
node --version
npm --version
```

#### Проверка зависимостей
```bash
npm list
npm audit
```

#### Проверка Playwright
```bash
npx playwright --version
npx playwright install --dry-run
```

---

## 📚 Дополнительная настройка

### 🔔 Настройка уведомлений
```javascript
// notifications.js
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransporter({
  service: 'gmail',
  auth: {
    user: 'your-email@gmail.com',
    pass: 'your-password'
  }
});

// Функция отправки уведомлений
function sendVulnerabilityAlert(vulnerability) {
  const mailOptions = {
    from: 'your-email@gmail.com',
    to: 'security-team@company.com',
    subject: 'Vulnerability Detected',
    text: `New vulnerability found: ${JSON.stringify(vulnerability, null, 2)}`
  };

  transporter.sendMail(mailOptions);
}
```

### 📊 Интеграция с SIEM
```javascript
// siem-integration.js
const axios = require('axios');

async function sendToSIEM(vulnerability) {
  try {
    await axios.post('https://your-siem.com/api/events', {
      timestamp: new Date().toISOString(),
      source: 'prophecy-sentinel',
      event_type: 'vulnerability_detected',
      data: vulnerability
    });
  } catch (error) {
    console.error('Failed to send to SIEM:', error.message);
  }
}
```

---

## ✅ Проверка работоспособности

### 🧪 Запуск тестов
```bash
# Все тесты
npm test

# Конкретный тест
npm run test:unit
npm run test:integration
```

### 🎯 Тестовое сканирование
```bash
# Сканирование тестовой цели
node ProphecySentinel.js testphp.vulnwebapp.com

# Проверка результатов
ls -la scan_results/
```

---

## 🔄 Обновление

### 📦 Обновление зависимостей
```bash
npm update
npm audit fix
```

### 🔄 Обновление Playwright
```bash
npx playwright install
```

### 🌐 Обновление репозитория
```bash
git pull origin main
npm install
```

---

## 📝 Следующие шаги

После успешной установки:

1. 📖 Прочитайте [основы безопасности](./security-basics.md)
2. 🚀 Проведите [первое сканирование](./first-scan.md)
3. 🧪 Практикуйтесь на [тестовых целях](./safe-environment.md)

---

## 💡 Советы по установке

### ✨ Лучшие практики
- Используйте последнюю версию Node.js
- Регулярно обновляйте зависимости
- Создавайте резервные копии конфигурации
- Используйте изолированные среды для тестов

### 🛡️ Безопасность
- Ограничьте права доступа к файлам
- Используйте VPN для публичного тестирования
- Ведите логи всех сканирований
- Храните результаты в зашифрованном виде

---

## 🆘 Поддержка

Если у вас возникли проблемы:

- 📖 [Документация](../technical/README.md)
- 💬 [GitHub Discussions](https://github.com/prophecy-sentinel/prophecy-sentinel/discussions)
- 🐛 [GitHub Issues](https://github.com/prophecy-sentinel/prophecy-sentinel/issues)

---

**Готовы начать? Перейдите к [первому сканированию](./first-scan.md)!** 🚀
