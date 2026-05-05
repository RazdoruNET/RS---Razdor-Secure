#!/bin/bash
# DPI-Bypass Stop Script
# Остановка DPI-Bypass и восстановление настроек

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⏹️ DPI-Bypass Stopper${NC}"
echo -e "${BLUE}🛑 Остановка системы обхода DPI${NC}"
echo "=================================================="

# Проверка PID файла
if [[ ! -f ".dpi_bypass.pid" ]]; then
    echo -e "${YELLOW}⚠️ Файл .dpi_bypass.pid не найден${NC}"
    echo -e "${YELLOW}🔍 Поиск процессов Python...${NC}"
    
    # Ищем процессы Python с нашим скриптом
    PYTHON_PIDS=$(pgrep -f "launch_dpi_bypass_proxy.py" || true)
    
    if [[ -n "$PYTHON_PIDS" ]]; then
        echo -e "${YELLOW}🎯 Найдены процессы: $PYTHON_PIDS${NC}"
        for pid in $PYTHON_PIDS; do
            echo -e "${YELLOW}🛑 Останавливаю процесс $pid...${NC}"
            kill $pid 2>/dev/null || true
        done
    else
        echo -e "${GREEN}✅ Нет запущенных процессов DPI-Bypass${NC}"
    fi
else
    # Читаем PID из файла
    PROXY_PID=$(cat .dpi_bypass.pid)
    echo -e "${YELLOW}🎯 Найден PID: $PROXY_PID${NC}"
    
    # Проверяем, что процесс существует
    if kill -0 $PROXY_PID 2>/dev/null; then
        echo -e "${YELLOW}🛑 Останавливаю процесс $PROXY_PID...${NC}"
        kill $PROXY_PID
        
        # Ждём завершения
        sleep 2
        
        # Проверяем, что процесс завершился
        if kill -0 $PROXY_PID 2>/dev/null; then
            echo -e "${YELLOW}⚠️ Процесс не завершился, принудительное завершение...${NC}"
            kill -9 $PROXY_PID 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ Процесс $PROXY_PID остановлен${NC}"
    else
        echo -e "${YELLOW}⚠️ Процесс $PROXY_PID уже не работает${NC}"
    fi
    
    # Удаляем PID файл
    rm -f .dpi_bypass.pid
fi

# Очистка оставшихся процессов
echo -e "${YELLOW}🧹 Очистка оставшихся процессов...${NC}"

REMAINING_PIDS=$(pgrep -f "launch_dpi_bypass_proxy.py" || true)
if [[ -n "$REMAINING_PIDS" ]]; then
    for pid in $REMAINING_PIDS; do
        echo -e "${YELLOW}🗑️ Удаляю процесс $pid${NC}"
        kill -9 $pid 2>/dev/null || true
    done
fi

# Отключение системного прокси (если есть права)
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}🔧 Отключение системного прокси...${NC}"
    
    if python3 setup_system_proxy.py --disable 2>/dev/null; then
        echo -e "${GREEN}✅ Системный прокси отключен${NC}"
    else
        echo -e "${YELLOW}⚠️ Не удалось отключить системный прокси${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Пропускаю отключение системного прокси (нужны права root)${NC}"
    echo -e "${YELLOW}🔧 Отключите прокси вручную в системных настройках${NC}"
fi

# Проверка порта
echo -e "${YELLOW}🔍 Проверка освобождения порта 8080...${NC}"

if lsof -i :8080 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Порт 8080 все еще занят${NC}"
    echo -e "${YELLOW}📋 Занятые процессы:${NC}"
    lsof -i :8080
else
    echo -e "${GREEN}✅ Порт 8080 свободен${NC}"
fi

echo ""
echo -e "${GREEN}✅ DPI-Bypass полностью остановлен${NC}"
echo -e "${GREEN}🔒 Системные настройки восстановлены${NC}"
echo ""
echo -e "${BLUE}📋 Лог-файлы сохранены в директории logs/${NC}"
echo -e "${BLUE}🔄 Для повторного запуска: ./start_dpi_bypass.sh${NC}"
