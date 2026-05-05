#!/bin/bash

# Скрипт для тестирования всех модулей обхода DPI
# Проверка доступности youtube.com через каждый инструмент

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Настройки
PROJECT_ROOT="/Users/razdor/Documents/GitHub/RS---Razdor-Secure"
RESULTS_DIR="$PROJECT_ROOT/dpi_test_results"
TEST_URL="https://www.youtube.com"
TIMEOUT=30

# Создание папки для результатов
mkdir -p "$RESULTS_DIR"

# Функция логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Функция проверки доступности сайта
check_youtube() {
    local test_name="$1"
    local proxy_port="$2"
    local log_file="$RESULTS_DIR/${test_name}_$(date +%Y%m%d_%H%M%S).log"
    
    log "🧪 Тестирование: $test_name (порт: $proxy_port)"
    
    # Проверяем, что прокси запущен
    if ! lsof -i :$proxy_port >/dev/null 2>&1; then
        echo -e "${RED}❌ $test_name: Прокси не запущен на порту $proxy_port${NC}" | tee "$log_file"
        return 1
    fi
    
    # Тестирование с curl через прокси
    local start_time=$(date +%s)
    
    if curl -x socks5://127.0.0.1:$proxy_port \
           --connect-timeout $TIMEOUT \
           --max-time $TIMEOUT \
           -s -o /dev/null \
           -w "%{http_code}\n" \
           "$TEST_URL" 2>/dev/null | grep -q "200\|301\|302"; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${GREEN}✅ $test_name: YouTube доступен (${duration}s)${NC}" | tee "$log_file"
        echo "Время ответа: ${duration} секунд" >> "$log_file"
        echo "HTTP код: 200/301/302" >> "$log_file"
        return 0
    else
        echo -e "${RED}❌ $test_name: YouTube недоступен${NC}" | tee "$log_file"
        echo "Ошибка подключения" >> "$log_file"
        return 1
    fi
}

# Функция HTTP прокси проверки
check_youtube_http() {
    local test_name="$1"
    local proxy_port="$2"
    local log_file="$RESULTS_DIR/${test_name}_$(date +%Y%m%d_%H%M%S).log"
    
    log "🧪 Тестирование: $test_name (HTTP порт: $proxy_port)"
    
    if ! lsof -i :$proxy_port >/dev/null 2>&1; then
        echo -e "${RED}❌ $test_name: Прокси не запущен на порту $proxy_port${NC}" | tee "$log_file"
        return 1
    fi
    
    local start_time=$(date +%s)
    
    if curl -x http://127.0.0.1:$proxy_port \
           --connect-timeout $TIMEOUT \
           --max-time $TIMEOUT \
           -s -o /dev/null \
           -w "%{http_code}\n" \
           "$TEST_URL" 2>/dev/null | grep -q "200\|301\|302"; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${GREEN}✅ $test_name: YouTube доступен (${duration}s)${NC}" | tee "$log_file"
        echo "Время ответа: ${duration} секунд" >> "$log_file"
        echo "HTTP код: 200/301/302" >> "$log_file"
        return 0
    else
        echo -e "${RED}❌ $test_name: YouTube недоступен${NC}" | tee "$log_file"
        echo "Ошибка подключения" >> "$log_file"
        return 1
    fi
}

# Функция запуска и тестирования модуля
test_module() {
    local script_path="$1"
    local module_name="$2"
    local proxy_port="$3"
    local proxy_type="$4"  # socks5 или http
    
    log "🚀 Запуск модуля: $module_name"
    
    # Переходим в директорию скрипта
    cd "$(dirname "$script_path")"
    
    # Запуск модуля в фоновом режиме
    python3 "$(basename "$script_path")" > /dev/null 2>&1 &
    local module_pid=$!
    
    # Ожидание запуска прокси
    sleep 5
    
    # Проверяем, что процесс запущен
    if ! kill -0 $module_pid 2>/dev/null; then
        echo -e "${RED}❌ $module_name: Не удалось запустить модуль${NC}"
        return 1
    fi
    
    # Тестирование
    if [ "$proxy_type" = "socks5" ]; then
        check_youtube "$module_name" "$proxy_port"
    else
        check_youtube_http "$module_name" "$proxy_port"
    fi
    
    local test_result=$?
    
    # Остановка модуля
    log "🛑 Остановка модуля: $module_name"
    kill $module_pid 2>/dev/null || true
    wait $module_pid 2>/dev/null || true
    
    return $test_result
}

# Основная функция
main() {
    log "🎯 Начало тестирования модулей обхода DPI"
    log "📍 Корень проекта: $PROJECT_ROOT"
    log "📁 Папка результатов: $RESULTS_DIR"
    log "🌐 Тестовый URL: $TEST_URL"
    echo
    
    # Проверка доступности YouTube без прокси (контроль)
    log "🔍 Проверка доступности YouTube без прокси..."
    if curl -s --connect-timeout $TIMEOUT --max-time $TIMEOUT -o /dev/null -w "%{http_code}\n" "$TEST_URL" 2>/dev/null | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✅ Контроль: YouTube доступен без прокси${NC}"
    else
        echo -e "${YELLOW}⚠️ Контроль: YouTube недоступен без прокси (ожидаемо)${NC}"
    fi
    echo
    
    # Список модулей для тестирования (кроме VPN)
    # Используем простые массивы для совместимости с macOS bash
    MODULE_NAMES=(
        "white_ghost_proxy"
        "enhanced_fin_storm_proxy"
        "fin_storm_proxy"
        "robust_proxy"
        "ultimate_proxy"
        "simple_working_proxy"
        "white_ghost_proxy_fixed"
    )
    
    MODULE_INFOS=(
        "White Ghost SOCKS5 Proxy:1080:socks5"
        "Enhanced Fin Storm Proxy:8080:http"
        "Fin Storm Proxy:8081:http"
        "Robust Proxy:8082:http"
        "Ultimate Proxy:8083:http"
        "Simple Working Proxy:8084:http"
        "White Ghost Fixed:1081:socks5"
    )
    
    local success_count=0
    local total_count=${#MODULE_NAMES[@]}
    
    # Тестирование каждого модуля
    for i in "${!MODULE_NAMES[@]}"; do
        local module_script="${MODULE_NAMES[$i]}"
        local module_info="${MODULE_INFOS[$i]}"
        local module_name=$(echo "$module_info" | cut -d':' -f1)
        local proxy_port=$(echo "$module_info" | cut -d':' -f2)
        local proxy_type=$(echo "$module_info" | cut -d':' -f3)
        
        local script_path="$PROJECT_ROOT/scripts/proxy_tools/${module_script}.py"
        
        if [ -f "$script_path" ]; then
            if test_module "$script_path" "$module_name" "$proxy_port" "$proxy_type"; then
                ((success_count++))
            fi
        else
            echo -e "${YELLOW}⚠️ Скрипт не найден: $script_path${NC}"
        fi
        
        # Пауза между тестами
        sleep 3
        echo
    done
    
    # Итоговые результаты
    log "📊 Итоги тестирования:"
    echo -e "${GREEN}✅ Успешных модулей: $success_count/$total_count${NC}"
    echo -e "${RED}❌ Неуспешных модулей: $((total_count - success_count))/$total_count${NC}"
    echo
    
    # Создание сводного отчета
    local summary_file="$RESULTS_DIR/test_summary_$(date +%Y%m%d_%H%M%S).txt"
    echo "=== Сводный отчет тестирования модулей DPI ===" > "$summary_file"
    echo "Дата: $(date)" >> "$summary_file"
    echo "Тестовый URL: $TEST_URL" >> "$summary_file"
    echo "Успешных модулей: $success_count/$total_count" >> "$summary_file"
    echo "" >> "$summary_file"
    echo "Подробные логи в файлах:" >> "$summary_file"
    ls -la "$RESULTS_DIR"/*.log >> "$summary_file" 2>/dev/null || true
    
    log "📋 Сводный отчет сохранен: $summary_file"
    
    # Вывод лучших модулей
    if [ $success_count -gt 0 ]; then
        echo -e "${GREEN}🏆 Лучшие модули (успешно прошли тест):${NC}"
        for log_file in "$RESULTS_DIR"/*.log; do
            if grep -q "✅" "$log_file" 2>/dev/null; then
                local module_name=$(basename "$log_file" | sed 's/_.*//')
                echo -e "${GREEN}  - $module_name${NC}"
            fi
        done
    fi
}

# Проверка зависимостей
check_dependencies() {
    log "🔧 Проверка зависимостей..."
    
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${RED}❌ curl не найден. Установите: brew install curl${NC}"
        exit 1
    fi
    
    if ! command -v lsof >/dev/null 2>&1; then
        echo -e "${RED}❌ lsof не найден. Установите: brew install lsof${NC}"
        exit 1
    fi
    
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}❌ python3 не найден${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Все зависимости найдены${NC}"
}

# Запуск
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Использование: $0 [опции]"
    echo "Опции:"
    echo "  --help, -h     Показать эту справку"
    echo "  --clean         Очистить папку результатов"
    echo ""
    echo "Скрипт тестирует все модули обхода DPI на доступность YouTube"
    exit 0
fi

if [ "$1" = "--clean" ]; then
    log "🧹 Очистка папки результатов..."
    rm -rf "$RESULTS_DIR"
    echo -e "${GREEN}✅ Папка результатов очищена${NC}"
    exit 0
fi

check_dependencies
main
