#!/bin/bash

# Расширенный скрипт для тестирования DPI обхода
# Проверка множественных сайтов и детальный анализ

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Настройки
PROJECT_ROOT="/Users/razdor/Documents/GitHub/RS---Razdor-Secure"
RESULTS_DIR="$PROJECT_ROOT/dpi_test_results"
DETAILED_DIR="$RESULTS_DIR/detailed_$(date +%Y%m%d_%H%M%S)"

# Список сайтов для тестирования
TEST_SITES=(
    "https://www.youtube.com"
    "https://m.youtube.com"
    "https://youtu.be"
    "https://www.google.com"
    "https://www.github.com"
    "https://www.reddit.com"
    "https://www.twitter.com"
    "https://www.instagram.com"
    "https://www.facebook.com"
    "https://www.wikipedia.org"
)

TIMEOUT=15
RETRIES=3

# Создание папок
mkdir -p "$DETAILED_DIR"

# Функции логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Функция детальной проверки сайта
test_site() {
    local site="$1"
    local proxy_type="$2"
    local proxy_port="$3"
    local module_name="$4"
    
    local site_name=$(echo "$site" | sed 's|https://www\.||' | sed 's|https://||' | sed 's|/||')
    local result_file="$DETAILED_DIR/${module_name}_${site_name}.txt"
    
    echo "=== Тестирование $site_name через $module_name ===" > "$result_file"
    echo "Время: $(date)" >> "$result_file"
    echo "Прокси: $proxy_type://127.0.0.1:$proxy_port" >> "$result_file"
    echo "" >> "$result_file"
    
    local success_count=0
    local total_time=0
    
    for ((i=1; i<=RETRIES; i++)); do
        echo "Попытка $i/$RETRIES..." >> "$result_file"
        
        local start_time=$(date +%s.%N)
        
        if [ "$proxy_type" = "socks5" ]; then
            local response=$(curl -x socks5://127.0.0.1:$proxy_port \
                               --connect-timeout $TIMEOUT \
                               --max-time $TIMEOUT \
                               -s -o /dev/null \
                               -w "%{http_code}|%{time_total}|%{size_download}" \
                               "$site" 2>/dev/null || echo "FAILED|0|0")
        else
            local response=$(curl -x http://127.0.0.1:$proxy_port \
                               --connect-timeout $TIMEOUT \
                               --max-time $TIMEOUT \
                               -s -o /dev/null \
                               -w "%{http_code}|%{time_total}|%{size_download}" \
                               "$site" 2>/dev/null || echo "FAILED|0|0")
        fi
        
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        
        IFS='|' read -r http_code time_total size_download <<< "$response"
        
        echo "  HTTP код: $http_code" >> "$result_file"
        echo "  Время: ${time_total}s" >> "$result_file"
        echo "  Размер: ${size_download} байт" >> "$result_file"
        
        if [[ "$http_code" =~ ^(200|301|302)$ ]]; then
            ((success_count++))
            echo "  Статус: УСПЕХ" >> "$result_file"
        else
            echo "  Статус: ОШИБКА" >> "$result_file"
        fi
        
        total_time=$(echo "$total_time + $time_total" | bc -l 2>/dev/null || echo "$total_time")
        
        sleep 1
    done
    
    local avg_time=$(echo "scale=2; $total_time / $RETRIES" | bc -l 2>/dev/null || echo "0")
    local success_rate=$((success_count * 100 / RETRIES))
    
    echo "" >> "$result_file"
    echo "Итоги:" >> "$result_file"
    echo "  Успешных попыток: $success_count/$RETRIES" >> "$result_file"
    echo "  Успешность: ${success_rate}%" >> "$result_file"
    echo "  Среднее время: ${avg_time}s" >> "$result_file"
    
    if [ $success_rate -ge 67 ]; then
        echo "  Общий статус: УСПЕХ" >> "$result_file"
        log_success "$module_name → $site_name: ${success_rate}% (${avg_time}s)"
        return 0
    else
        echo "  Общий статус: НЕУСПЕХ" >> "$result_file"
        log_error "$module_name → $site_name: ${success_rate}% (${avg_time}s)"
        return 1
    fi
}

# Функция тестирования модуля
test_module_advanced() {
    local script_path="$1"
    local module_name="$2"
    local proxy_port="$3"
    local proxy_type="$4"
    
    log_info "🧪 Расширенное тестирование: $module_name"
    
    cd "$(dirname "$script_path")"
    
    # Запуск модуля
    python3 "$(basename "$script_path")" > /dev/null 2>&1 &
    local module_pid=$!
    sleep 5
    
    if ! kill -0 $module_pid 2>/dev/null; then
        log_error "$module_name: Не удалось запустить"
        return 1
    fi
    
    local module_success=0
    local total_sites=${#TEST_SITES[@]}
    
    # Тестирование каждого сайта
    for site in "${TEST_SITES[@]}"; do
        if test_site "$site" "$proxy_type" "$proxy_port" "$module_name"; then
            ((module_success++))
        fi
        sleep 1
    done
    
    local module_success_rate=$((module_success * 100 / total_sites))
    
    # Остановка модуля
    kill $module_pid 2>/dev/null || true
    wait $module_pid 2>/dev/null || true
    
    log_info "$module_name: $module_success/$total_sites сайтов (${module_success_rate}%)"
    
    return 0
}

# Функция создания сводного отчета
create_summary_report() {
    local summary_file="$RESULTS_DIR/advanced_summary_$(date +%Y%m%d_%H%M%S).html"
    
    cat > "$summary_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Тестирование DPI обхода - Отчет</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .module { background: white; margin: 10px 0; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .success { border-left: 5px solid #27ae60; }
        .partial { border-left: 5px solid #f39c12; }
        .failure { border-left: 5px solid #e74c3c; }
        .stats { display: flex; justify-content: space-between; margin: 10px 0; }
        .stat { text-align: center; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Отчет тестирования модулей обхода DPI</h1>
        <p>Дата: $(date)</p>
    </div>
EOF
    
    # Добавление результатов по модулям
    for result_file in "$DETAILED_DIR"/*.txt; do
        if [ -f "$result_file" ]; then
            local filename=$(basename "$result_file")
            local module_name=$(echo "$filename" | sed 's/_[^.]*\.txt//')
            
            echo "<div class='module'>" >> "$summary_file"
            echo "<h3>$module_name</h3>" >> "$summary_file"
            echo "<pre>$(cat "$result_file")</pre>" >> "$summary_file"
            echo "</div>" >> "$summary_file"
        fi
    done
    
    echo "</body></html>" >> "$summary_file"
    
    log_success "HTML отчет создан: $summary_file"
}

# Основная функция
main() {
    log "🚀 Расширенное тестирование модулей DPI обхода"
    log "📁 Папка результатов: $DETAILED_DIR"
    log "🌐 Сайтов для тестирования: ${#TEST_SITES[@]}"
    log "🔄 Повторов: $RETRIES"
    echo
    
    # Контрольная проверка без прокси
    log_info "🔍 Контрольная проверка без прокси..."
    local control_success=0
    for site in "${TEST_SITES[@]}"; do
        if curl -s --connect-timeout $TIMEOUT --max-time $TIMEOUT -o /dev/null -w "%{http_code}\n" "$site" 2>/dev/null | grep -q "200\|301\|302"; then
            ((control_success++))
        fi
    done
    
    log_info "Контроль: $control_success/${#TEST_SITES[@]} сайтов доступны без прокси"
    echo
    
    # Модули для тестирования
    # Используем простые массивы для совместимости с macOS bash
    MODULE_NAMES=(
        "white_ghost_proxy"
        "enhanced_fin_storm_proxy"
        "fin_storm_proxy"
        "robust_proxy"
        "ultimate_proxy"
        "simple_working_proxy"
    )
    
    MODULE_INFOS=(
        "White Ghost SOCKS5:1080:socks5"
        "Enhanced Fin Storm:8080:http"
        "Fin Storm:8081:http"
        "Robust:8082:http"
        "Ultimate:8083:http"
        "Simple Working:8084:http"
    )
    
    # Тестирование каждого модуля
    for i in "${!MODULE_NAMES[@]}"; do
        local module_script="${MODULE_NAMES[$i]}"
        local module_info="${MODULE_INFOS[$i]}"
        local module_name=$(echo "$module_info" | cut -d':' -f1)
        local proxy_port=$(echo "$module_info" | cut -d':' -f2)
        local proxy_type=$(echo "$module_info" | cut -d':' -f3)
        
        local script_path="$PROJECT_ROOT/scripts/proxy_tools/${module_script}.py"
        
        if [ -f "$script_path" ]; then
            test_module_advanced "$script_path" "$module_name" "$proxy_port" "$proxy_type"
        else
            log_warning "Скрипт не найден: $script_path"
        fi
        
        sleep 3
        echo
    done
    
    # Создание отчетов
    log_info "📊 Создание сводных отчетов..."
    create_summary_report
    
    log_success "🎉 Тестирование завершено!"
    log_info "📁 Результаты сохранены в: $DETAILED_DIR"
    log_info "📋 HTML отчет: $RESULTS_DIR/advanced_summary_*.html"
}

# Проверка зависимостей
check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if ! command -v lsof >/dev/null 2>&1; then
        missing_deps+=("lsof")
    fi
    
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi
    
    if ! command -v bc >/dev/null 2>&1; then
        missing_deps+=("bc")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Отсутствуют зависимости: ${missing_deps[*]}"
        log_info "Установите: brew install ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "Все зависимости найдены"
}

# Обработка аргументов
case "$1" in
    --help|-h)
        echo "Использование: $0 [опции]"
        echo "Опции:"
        echo "  --help, -h     Показать справку"
        echo "  --clean         Очистить старые результаты"
        echo "  --quick         Быстрое тестирование (только YouTube)"
        echo ""
        echo "Скрипт выполняет расширенное тестирование всех модулей DPI обхода"
        exit 0
        ;;
    --clean)
        log_info "🧹 Очистка старых результатов..."
        rm -rf "$RESULTS_DIR"
        log_success "Очистка завершена"
        exit 0
        ;;
    --quick)
        log_info "⚡ Быстрое тестирование (только YouTube)..."
        exec "$PROJECT_ROOT/test_dpi_modules.sh"
        ;;
esac

check_dependencies
main
