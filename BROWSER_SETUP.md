# 🌐 Настройка браузера для White-Ghost Proxy

## 🚀 Быстрый запуск (Автоматический)

### 1. Запуск с автоматической настройкой:
```bash
cd /Users/razdor/Documents/GitHub/RS---Razdor-Secure
python3 start_white_ghost.py
```

Это автоматически:
- ✅ Запустит White-Ghost Proxy на 127.0.0.1:1080
- ✅ Настроит системный прокси macOS
- ✅ Откроет YouTube в браузере

### 2. Запуск без системных настроек:
```bash
python3 start_white_ghost.py --no-system
```
(тогда нужно настроить прокси в браузере вручную)

---

## 🔧 Ручная настройка браузера

### 🦊 Firefox
1. Меню → Настройки → Общие → Параметры сети
2. Нажать "Настройки..."
3. Выбрать "Ручная настройка прокси"
4. Ввести:
   - **SOCKS-хост**: `127.0.0.1`
   - **Порт**: `1080`
   - ✅ **SOCKS v5**
5. Нажать "ОК"

### 🌐 Chrome/Edge (системные настройки)
1. Системные настройки → Сеть → Прокси
2. Выбрать "Веб-прокси (HTTP)"
3. Включить прокси:
   - **Адрес сервера**: `127.0.0.1`
   - **Порт**: `1080`
4. То же для "Безопасный веб-прокси (HTTPS)"
5. Нажать "ОК"

### 🍎 Safari
Использует системные настройки macOS (см. Chrome/Edge)

---

## 📱 Проверка работы

### 1. Проверка прокси:
```bash
python3 start_white_ghost.py --status
```

### 2. Проверка YouTube:
Откройте в браузере:
- https://www.youtube.com
- https://m.youtube.com
- https://youtu.be

### 3. Проверка доменов:
White-Ghost обходит:
- ✅ youtube.com
- ✅ www.youtube.com  
- ✅ m.youtube.com
- ✅ youtu.be
- ✅ ytimg.com
- ✅ googlevideo.com
- ✅ googleapis.com
- ✅ gstatic.com
- ✅ ggpht.com

---

## 🛠️ Управление прокси

### Запуск в фоне:
```bash
cd /Users/razdor/Documents/GitHub/RS---Razdor-Secure
nohup python3 start_white_ghost.py --no-browser > proxy.log 2>&1 &
```

### Проверка статуса:
```bash
python3 start_white_ghost.py --status
```

### Остановка:
```bash
python3 start_white_ghost.py --stop
```

### Просмотр логов:
```bash
tail -f proxy.log
```

---

## 🔥 Продвинутые опции

### Изменение порта:
```bash
python3 start_white_ghost.py --port 1081
```

### Только запуск прокси (без браузера):
```bash
python3 start_white_ghost.py --no-browser
```

### Только прокси (без системных настроек):
```bash
python3 start_white_ghost.py --no-system --no-browser
```

---

## ⚠️ Устранение проблем

### Прокси не работает:
1. Проверьте запущен ли процесс:
   ```bash
   ps aux | grep white_ghost
   ```
2. Проверьте порт:
   ```bash
   lsof -i :1080
   ```
3. Перезапустите:
   ```bash
   python3 start_white_ghost.py --stop
   python3 start_white_ghost.py
   ```

### YouTube не открывается:
1. Очистите кэш браузера
2. Отключите VPN
3. Перезапустите браузер
4. Проверьте настройки прокси

### Медленная скорость:
1. Прокси использует White-Ghost цепочки
2. Попробуйте другой порт:
   ```bash
   python3 start_white_ghost.py --port 1081
   ```

---

## 📊 Статистика

При остановке прокси покажет:
- 🔗 Всего соединений
- 👻 White-Ghost использован
- 🌐 Прямых соединений  
- ❌ Ошибок

---

## 🎯 Готово к использованию!

После настройки:
1. 🚀 Запустите прокси
2. 🌐 Откройте YouTube
3. 🎺 Наслаждайтесь видео!

White-Ghost Proxy автоматически определет YouTube трафик и применит нужную цепочку обхода.
