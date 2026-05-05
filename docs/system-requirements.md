# 📋 СИСТЕМНЫЕ ТРЕБОВАНИЯ

## 💻 **МИНИМАЛЬНЫЕ ТРЕБОВАНИЯ**

### Операционная система
- **macOS**: 10.15+ (Catalina и новее)
- **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 8+
- **Windows**: 10+ (частичная поддержка)

### Программное обеспечение
- **Python**: 3.11+ (рекомендуется 3.11.5+)
- **Git**: 2.0+
- **Terminal**: Bash/Zsh (macOS/Linux), PowerShell/WSL (Windows)

### Аппаратное обеспечение
- **Процессор**: Intel Core i5 / AMD Ryzen 5 или эквивалент
- **Оперативная память**: 8GB RAM
- **Дисковое пространство**: 2GB свободного места
- **Сеть**: Стабильное интернет-соединение

## 🚀 **РЕКОМЕНДУЕМЫЕ ТРЕБОВАНИЯ**

### Операционная система
- **macOS**: 12.0+ (Monterey и новее)
- **Linux**: Ubuntu 20.04+, Debian 11+, CentOS 9+
- **Windows**: 11+ (полная поддержка)

### Программное обеспечение
- **Python**: 3.11.5+ или 3.12+
- **Docker**: 20.10+ (опционально)
- **VirtualBox**: 6.1+ (опционально)

### Аппаратное обеспечение
- **Процессор**: Intel Core i7 / AMD Ryzen 7 или эквивалент
- **Оперативная память**: 16GB+ RAM
- **Дисковое пространство**: 5GB+ SSD
- **Сеть**: Высокоскоростное интернет-соединение (100Mbps+)

## 📡 **ДОПОЛНИТЕЛЬНОЕ ОБОРУДОВАНИЕ**

### Для DPI обхода
- **SDR модули**:
  - HackRF One (рекомендуется)
  - RTL-SDR v3 (бюджетный вариант)
  - LimeSDR Mini (продвинутый)

### Для нейроволновой защиты
- **Нейроинтерфейсы**:
  - Muse S/Muse 2
  - Emotiv EPOC+
  - OpenBCI Cyton/Ganglion

### Для WiFi антипозиционирования
- **WiFi адаптеры**:
  - Alfa Network AWUS036ACH
  - TP-Link TL-WN722N v1/v2
  - Panda PAU09

## 🔧 **ПРОГРАММНЫЕ ЗАВИСИМОСТИ**

### Основные зависимости
```bash
# Python пакеты (requirements.txt)
tensorflow>=2.13.0
torch>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
requests>=2.31.0
flask>=2.3.0
fastapi>=0.100.0
uvicorn>=0.23.0
```

### Системные утилиты
```bash
# macOS
brew install git python3 tor ollama

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install git python3 python3-pip tor

# Linux (CentOS/RHEL)
sudo yum install git python3 python3-pip tor
```

### Виртуальные окружения
```bash
# Создание окружения
python3 -m venv rsecure_env

# Активация
source rsecure_env/bin/activate  # macOS/Linux
rsecure_env\Scripts\activate     # Windows
```

## 🤖 **AI/ML ТРЕБОВАНИЯ**

### Для Ollama интеграции
- **Ollama**: 0.1.0+
- **Модели**:
  - qwen2.5-coder:1.5b (2GB)
  - gemma2:2b (1.6GB)
  - llama3:8b (4.7GB)

### Для TensorFlow моделей
- **CUDA**: 11.8+ (для NVIDIA GPU)
- **cuDNN**: 8.6+ (для NVIDIA GPU)
- **ROCm**: 5.4+ (для AMD GPU)

### Для нейросетевого анализа
- **VRAM**: 4GB+ (GPU)
- **RAM**: 16GB+ (для больших моделей)
- **Storage**: 10GB+ (для моделей)

## 🌐 **СЕТЕВЫЕ ТРЕБОВАНИЯ**

### Для DPI обхода
- **Пропускная способность**: 10Mbps+
- **Latency**: <100ms
- **Протоколы**: HTTP/HTTPS, SOCKS5, Shadowsocks

### Для Tor интеграции
- **Tor**: 0.4.7+
- **Privoxy**: 3.0.26+ (опционально)
- **Obfs4proxy**: последняя версия

### Для прокси инструментов
- **OpenSSL**: 1.1.1+
- **Ngrok**: 3.0+ (опционально)
- **Cloudflared**: 1.0+ (опционально)

## 📊 **ПРОИЗВОДИТЕЛЬНОСТЬ**

### Базовая конфигурация
- **CPU**: 50-70% нагрузка
- **RAM**: 2-4GB использование
- **Network**: 1-5Mbps пропускная способность

### Продвинутая конфигурация
- **CPU**: 70-90% нагрузка
- **RAM**: 8-16GB использование
- **Network**: 10-50Mbps пропускная способность

### Максимальная конфигурация
- **CPU**: 90-100% нагрузка
- **RAM**: 16-32GB использование
- **Network**: 50-100Mbps+ пропускная способность

## 🔒 **БЕЗОПАСНОСТЬ**

### Требования к безопасности
- **Firewall**: Активный и настроенный
- **Antivirus**: Обновленный (для Windows)
- **File Permissions**: Правильные права доступа
- **Network Security**: Защищенное соединение

### Рекомендации по безопасности
- Использовать VPN для дополнительной анонимности
- Регулярно обновлять систему и зависимости
- Использовать двухфакторную аутентификацию
- Создавать отдельного пользователя для RSecure

## 🚨 **ПРЕДУПРЕЖДЕНИЯ**

### Ограничения
- **Windows**: Ограниченная поддержка некоторых модулей
- **ARM**: Ограниченная поддержка SDR устройств
- **Виртуализация**: Некоторые функции могут не работать в VM

### Известные проблемы
- **macOS**: Требуется отключение SIP для некоторых функций
- **Linux**: Требуются права sudo для сетевых операций
- **Windows**: Требуется запуск от администратора

---

## 📝 **ПРОВЕРКА СИСТЕМЫ**

### Скрипт проверки
```bash
#!/bin/bash
echo "Проверка системных требований..."

# Проверка Python
python3 --version

# Проверка Git
git --version

# Проверка RAM
free -h  # Linux
sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}'  # macOS

# Проверка диска
df -h

# Проверка сети
ping -c 4 google.com
```

### Рекомендуемая конфигурация тестирования
```bash
# Запуск тестов производительности
python scripts/minimal_rsecure.py --test-performance

# Проверка DPI обхода
python scripts/startup/run_dpi_bypass_daemon.py --test

# Проверка нейросетевых функций
python rsecure/rsecure_main.py --test-neural
```

---

**© 2026 WE RAZDOR. Все права защищены.**
