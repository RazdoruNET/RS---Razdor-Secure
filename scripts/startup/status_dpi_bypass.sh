#!/bin/bash
# DPI-Bypass Status Script
# Проверка статуса работы DPI-Bypass

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 DPI-Bypass Status${NC}"
echo -e "${BLUE}🔍 Проверка статуса системы обхода DPI${NC}"
echo "=================================================="

# Проверка PID файла
PROXY_PID=""
if [[ -f ".dpi_bypass.pid" ]]; then
    PROXY_PID=$(cat .dpi_bypass.pid)
    echo -e "${YELLOW}📁 Файл PID найден: $PROXY_PID${NC}"
else
    echo -e "${YELLOW}⚠️ Файл .dpi_bypass.pid не найден${NC}"
fi

# Проверка процесса
if [[ -n "$PROXY_PID" ]]; then
    if kill -0 $PROXY_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Процесс DPI-Bypass запущен (PID: $PROXY_PID)${NC}"
        
        # Получаем дополнительную информацию о процессе
        if command -v ps >/dev/null; then
            echo -e "${BLUE}📋 Детали процесса:${NC}"
            ps -p $PROXY_PID -o pid,ppid,etime,pcpu,pmem,command 2>/dev/null || true
        fi
    else
        echo -e "${RED}❌ Процесс $PROXY_PID не запущен${NC}"
        PROXY_PID=""
    fi
fi

# Поиск других процессов
echo -e "${YELLOW}🔍 Поиск других процессов DPI-Bypass...${NC}"
PYTHON_PIDS=$(pgrep -f "launch_dpi_bypass_proxy.py" || true)

if [[ -n "$PYTHON_PIDS" ]]; then
    echo -e "${YELLOW}🎯 Найдены процессы:${NC}"
    for pid in $PYTHON_PIDS; do
        if [[ "$pid" != "$PROXY_PID" ]]; then
            echo -e "${YELLOW}   - PID $pid (дополнительный)${NC}"
        fi
    done
else
    if [[ -z "$PROXY_PID" ]]; then
        echo -e "${RED}❌ Нет запущенных процессов DPI-Bypass${NC}"
    fi
fi

# Проверка порта
echo -e "${YELLOW}🔍 Проверка порта 8080...${NC}"

if command -v lsof >/dev/null; then
    PORT_INFO=$(lsof -i :8080 2>/dev/null || echo "")
    if [[ -n "$PORT_INFO" ]]; then
        echo -e "${GREEN}✅ Порт 8080 занят:${NC}"
        echo "$PORT_INFO" | while read line; do
            echo -e "${BLUE}   $line${NC}"
        done
    else
        echo -e "${RED}❌ Порт 8080 свободен${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Не удалось проверить порт (lsof недоступен)${NC}"
fi

# Проверка системного прокси
echo -e "${YELLOW}🔍 Проверка системного прокси...${NC}"

if command -v networksetup >/dev/null; then
    echo -e "${BLUE}📋 Настройки прокси Wi-Fi:${NC}"
    
    # HTTP прокси
    HTTP_STATE=$(networksetup -getwebproxystate Wi-Fi 2>/dev/null || echo "Error")
    if [[ "$HTTP_STATE" == "Enabled" ]]; then
        HTTP_SETTINGS=$(networksetup -getwebproxy Wi-Fi 2>/dev/null || echo "Error")
        echo -e "${GREEN}✅ HTTP прокси: Включен${NC}"
        echo "$HTTP_SETTINGS" | grep -E "(Server|Port)" | while read line; do
            echo -e "${BLUE}   $line${NC}"
        done
    else
        echo -e "${RED}❌ HTTP прокси: Выключен${NC}"
    fi
    
    # HTTPS прокси
    HTTPS_STATE=$(networksetup -getsecurewebproxystate Wi-Fi 2>/dev/null || echo "Error")
    if [[ "$HTTPS_STATE" == "Enabled" ]]; then
        HTTPS_SETTINGS=$(networksetup -getsecurewebproxy Wi-Fi 2>/dev/null || echo "Error")
        echo -e "${GREEN}✅ HTTPS прокси: Включен${NC}"
        echo "$HTTPS_SETTINGS" | grep -E "(Server|Port)" | while read line; do
            echo -e "${BLUE}   $line${NC}"
        done
    else
        echo -e "${RED}❌ HTTPS прокси: Выключен${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Не удалось проверить системный прокси${NC}"
fi

# Проверка доступности прокси
echo -e "${YELLOW}🔍 Проверка доступности прокси...${NC}"

if command -v curl >/dev/null; then
    if curl -s --connect-timeout 3 --proxy http://127.0.0.1:8080 http://httpbin.org/ip >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Прокси отвечает на запросы${NC}"
        
        # Тестовый запрос
        echo -e "${BLUE}🌐 Тестовый запрос через прокси:${NC}"
        TEST_RESPONSE=$(curl -s --connect-timeout 5 --proxy http://127.0.0.1:8080 http://httpbin.org/ip 2>/dev/null || echo "Error")
        if [[ "$TEST_RESPONSE" != "Error" && -n "$TEST_RESPONSE" ]]; then
            echo -e "${GREEN}   $TEST_RESPONSE${NC}"
        fi
    else
        echo -e "${RED}❌ Прокси не отвечает${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ curl недоступен для проверки${NC}"
fi

# Проверка лог-файлов
echo -e "${YELLOW}📋 Проверка лог-файлов...${NC}"

if [[ -d "logs" ]]; then
    LOG_COUNT=$(find logs -name "*.log" 2>/dev/null | wc -l)
    if [[ "$LOG_COUNT" -gt 0 ]]; then
        echo -e "${GREEN}✅ Найдено лог-файлов: $LOG_COUNT${NC}"
        
        # Показываем последний лог-файл
        LATEST_LOG=$(find logs -name "*.log" -type f -exec ls -t {} + | head -1 2>/dev/null)
        if [[ -n "$LATEST_LOG" ]]; then
            echo -e "${BLUE}📄 Последний лог: $LATEST_LOG${NC}"
            echo -e "${BLUE}📊 Размер: $(du -h "$LATEST_LOG" | cut -f1)${NC}"
            
            # Показываем последние строки
            echo -e "${BLUE}📝 Последние строки:${NC}"
            tail -5 "$LATEST_LOG" 2>/dev/null | while read line; do
                echo -e "${YELLOW}   $line${NC}"
            done
        fi
    else
        echo -e "${YELLOW}⚠️ Лог-файлы не найдены${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Директория logs не найдена${NC}"
fi

# Итоговый статус
echo ""
echo -e "${BLUE}📊 Итоговый статус:${NC}"

if [[ -n "$PROXY_PID" ]] && kill -0 $PROXY_PID 2>/dev/null; then
    echo -e "${GREEN}✅ DPI-Bypass работает корректно${NC}"
    echo -e "${GREEN}🌐 Прокси доступен по адресу: 127.0.0.1:8080${NC}"
    echo -e "${GREEN}📊 Статистика: http://127.0.0.1:8080/stats${NC}"
else
    echo -e "${RED}❌ DPI-Bypass не запущен${NC}"
    echo -e "${YELLOW}🔄 Для запуска: ./start_dpi_bypass.sh${NC}"
fi

echo ""
echo -e "${BLUE}🛑 Остановка: ./stop_dpi_bypass.sh${NC}"
echo -e "${BLUE}🔄 Перезапуск: ./stop_dpi_bypass.sh && ./start_dpi_bypass.sh${NC}"
