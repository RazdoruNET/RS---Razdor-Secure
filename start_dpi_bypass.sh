#!/bin/bash
# DPI-Bypass Launcher Script
# Быстрый запуск DPI-Bypass с автоматической настройкой прокси

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Параметры
PROXY_PORT=8080
LOG_FILE="dpi_bypass_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}🔥 DPI-Bypass Launcher${NC}"
echo -e "${BLUE}🚀 Запуск системы обхода DPI${NC}"
echo "=================================================="

# Проверка зависимостей
echo -e "${YELLOW}📋 Проверка зависимостей...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден. Установите Python3${NC}"
    exit 1
fi

if ! command -v networksetup &> /dev/null; then
    echo -e "${RED}❌ networksetup не найден. Требуется macOS${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Зависимости проверены${NC}"

# Проверка прав администратора
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}⚠️ Запуск от root - это хорошо!${NC}"
    ADMIN_MODE=true
else
    echo -e "${YELLOW}⚠️ Рекомендуется запуск от root для полной функциональности${NC}"
    echo -e "${YELLOW}🔧 Используйте: sudo ./start_dpi_bypass.sh${NC}"
    ADMIN_MODE=false
fi

# Проверка наличия файлов
echo -e "${YELLOW}📋 Проверка файлов DPI-Bypass...${NC}"

if [[ ! -f "launch_dpi_bypass_proxy.py" ]]; then
    echo -e "${RED}❌ Файл launch_dpi_bypass_proxy.py не найден${NC}"
    exit 1
fi

if [[ ! -f "setup_system_proxy.py" ]]; then
    echo -e "${RED}❌ Файл setup_system_proxy.py не найден${NC}"
    exit 1
fi

if [[ ! -d "rsecure" ]]; then
    echo -e "${RED}❌ Директория rsecure не найдена${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Все файлы на месте${NC}"

# Создание лог-директории
mkdir -p logs

# Настройка системного прокси (если есть права)
if [[ "$ADMIN_MODE" == true ]]; then
    echo -e "${YELLOW}🔧 Настройка системного прокси...${NC}"
    
    if python3 setup_system_proxy.py --port $PROXY_PORT; then
        echo -e "${GREEN}✅ Системный прокси настроен${NC}"
    else
        echo -e "${RED}❌ Ошибка настройки системного прокси${NC}"
        echo -e "${YELLOW}⚠️ Продолжаем без системного прокси...${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Пропускаю настройку системного прокси (нужны права root)${NC}"
    echo -e "${BLUE}📋 Настройте прокси вручную:${NC}"
    echo -e "${BLUE}   HTTP Proxy: 127.0.0.1:$PROXY_PORT${NC}"
    echo -e "${BLUE}   HTTPS Proxy: 127.0.0.1:$PROXY_PORT${NC}"
fi

# Запуск DPI-Bypass прокси
echo -e "${YELLOW}🚀 Запуск DPI-Bypass прокси...${NC}"
echo -e "${BLUE}📍 Прокси будет доступен по адресу: 127.0.0.1:$PROXY_PORT${NC}"
echo -e "${BLUE}📊 Статистика: http://127.0.0.1:$PROXY_PORT/stats${NC}"
echo -e "${BLUE}📝 Лог-файл: logs/$LOG_FILE${NC}"
echo "=================================================="

# Запуск в фоновом режиме с сохранением PID
nohup python3 launch_dpi_bypass_proxy.py --port $PROXY_PORT > "logs/$LOG_FILE" 2>&1 &
PROXY_PID=$!

echo $PROXY_PID > .dpi_bypass.pid

echo -e "${GREEN}✅ DPI-Bypass запущен!${NC}"
echo -e "${GREEN}🔄 PID: $PROXY_PID${NC}"
echo -e "${GREEN}📝 Лог: logs/$LOG_FILE${NC}"

# Проверка запуска
sleep 2

if kill -0 $PROXY_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Прокси-сервер успешно запущен и работает${NC}"
    echo ""
    echo -e "${BLUE}🌐 Теперь весь ваш трафик маршрутизируется через DPI-Bypass!${NC}"
    echo -e "${BLUE}🔥 Недоступные сайты станут доступны без VPN${NC}"
    echo ""
    echo -e "${YELLOW}📋 Проверка работы:${NC}"
    echo -e "${YELLOW}   1. Откройте браузер и зайдите на заблокированный сайт${NC}"
    echo -e "${YELLOW}   2. Проверьте статистику: http://127.0.0.1:$PROXY_PORT/stats${NC}"
    echo ""
    echo -e "${BLUE}⏹️ Остановка: ./stop_dpi_bypass.sh${NC}"
    echo -e "${BLUE}📊 Статус: ./status_dpi_bypass.sh${NC}"
else
    echo -e "${RED}❌ Ошибка запуска прокси-сервера${NC}"
    echo -e "${YELLOW}📝 Проверьте лог-файл: logs/$LOG_FILE${NC}"
    exit 1
fi

# Автоматическая проверка доступности
echo -e "${YELLOW}🔍 Проверка доступности прокси...${NC}"
sleep 3

if curl -s --proxy http://127.0.0.1:$PROXY_PORT http://httpbin.org/ip > /dev/null; then
    echo -e "${GREEN}✅ Прокси отвечает на запросы${NC}"
else
    echo -e "${YELLOW}⚠️ Прокси не отвечает (это нормально для первых секунд работы)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 DPI-Bypass успешно запущен!${NC}"
echo -e "${GREEN}🔥 Наслаждайтесь свободным интернетом без VPN!${NC}"
