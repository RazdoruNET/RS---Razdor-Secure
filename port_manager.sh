#!/bin/bash

# Утилита для управления портами DPI модулей

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Порты модулей (простые массивы для macOS)
MODULE_NAMES=(
    "white_ghost_proxy"
    "enhanced_fin_storm_proxy"
    "fin_storm_proxy"
    "robust_proxy"
    "ultimate_proxy"
    "simple_working_proxy"
    "white_ghost_proxy_fixed"
)

MODULE_PORTS=(
    "1080"
    "8080"
    "8081"
    "8082"
    "8083"
    "8084"
    "1081"
)

# Функции логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
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

# Проверка занятости портов
check_ports() {
    log "🔍 Проверка занятости портов..."
    echo
    
    local busy_ports=()
    
    for i in "${!MODULE_NAMES[@]}"; do
        local module="${MODULE_NAMES[$i]}"
        local port="${MODULE_PORTS[$i]}"
            
        if lsof -i :$port >/dev/null 2>&1; then
            local pid=$(lsof -ti:$port 2>/dev/null | head -1)
            local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                
            echo -e "${RED}🔴 Порт $port занят${NC}"
            echo -e "   Модуль: $module"
            echo -e "   PID: $pid"
            echo -e "   Процесс: $process"
            echo -e "   Команда освобождения: sudo kill -9 $pid"
        else
            echo -e "${GREEN}🟢 Порт $port свободен${NC}"
            echo -e "   Модуль: $module"
        fi
    done
    
    if [ ${#busy_ports[@]} -gt 0 ]; then
        log_warning "Занятые порты: ${busy_ports[*]}"
        return 1
    else
        log_success "Все порты свободны"
        return 0
    fi
}

# Освобождение портов
free_ports() {
    log "🔓 Освобождение портов..."
    
    local freed_count=0
    
    for i in "${!MODULE_NAMES[@]}"; do
        local module="${MODULE_NAMES[$i]}"
        local port="${MODULE_PORTS[$i]}"
        
        # Находим PID процесса на порту
        local pids=$(lsof -ti:$port 2>/dev/null)
        
        if [ -n "$pids" ]; then
            echo -e "${YELLOW}🔓 Освобождаем порт $port (${module})${NC}"
            
            for pid in $pids; do
                if kill -0 $pid 2>/dev/null; then
                    echo -e "   Завершаем процесс $pid"
                    kill -TERM $pid 2>/dev/null || true
                    
                    # Ждем завершения
                    sleep 2
                    
                    # Принудительно убиваем если не завершился
                    if kill -0 $pid 2>/dev/null; then
                        echo -e "   Принудительно убиваем процесс $pid"
                        kill -KILL $pid 2>/dev/null || true
                    fi
                    
                    ((freed_count++))
                fi
            done
            
            echo -e "${GREEN}   Порт $port освобожден${NC}"
            echo
        else
            echo -e "${GREEN}🟢 Порт $port уже свободен${NC}"
        fi
    done
    
    log_success "Освобождено портов: $freed_count"
}

# Проверка конкретного порта
check_port() {
    local port=$1
    
    if [ -z "$port" ]; then
        log_error "Укажите порт: $0 check <порт>"
        return 1
    fi
    
    if lsof -i :$port >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port 2>/dev/null | head -1)
        local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        
        echo -e "${RED}🔴 Порт $port занят${NC}"
        echo -e "   PID: $pid"
        echo -e "   Процесс: $process"
        echo -e "   Команда освобождения: sudo kill -9 $pid"
        return 1
    else
        echo -e "${GREEN}🟢 Порт $port свободен${NC}"
        return 0
    fi
}

# Мониторинг портов в реальном времени
monitor_ports() {
    log "👁️ Мониторинг портов (Ctrl+C для остановки)..."
    echo
    
    while true; do
        clear
        echo "=== Мониторинг портов DPI модулей ==="
        echo "Время: $(date)"
        echo
        
        for module in "${!MODULE_PORTS[@]}"; do
            local port=${MODULE_PORTS[$module]}
            
            if lsof -i :$port >/dev/null 2>&1; then
                local pid=$(lsof -ti:$port 2>/dev/null | head -1)
                local process=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                
                echo -e "${RED}🔴 $port - $process ($pid)${NC}"
            else
                echo -e "${GREEN}🟢 $port - свободен${NC}"
            fi
        done
        
        echo
        echo "Нажмите Ctrl+C для выхода..."
        sleep 3
    done
}

# Автоматическое освобождение и проверка
auto_fix() {
    log "🔧 Автоматическое исправление проблем с портами..."
    
    # Сначала освобождаем все занятые порты
    free_ports
    
    # Ждем освобождения
    sleep 2
    
    # Проверяем результат
    if check_ports; then
        log_success "Проблемы с портами исправлены"
        return 0
    else
        log_error "Не удалось исправить проблемы с портами"
        return 1
    fi
}

# Показать справку
show_help() {
    echo "Управление портами DPI модулей"
    echo ""
    echo "Использование: $0 [команда] [опции]"
    echo ""
    echo "Команды:"
    echo "  check              Проверить все порты"
    echo "  check <порт>       Проверить конкретный порт"
    echo "  free               Освободить все порты"
    echo "  monitor             Мониторить порты в реальном времени"
    echo "  auto-fix           Автоматически исправить проблемы"
    echo "  help               Показать эту справку"
    echo ""
    echo "Порты модулей:"
    for i in "${!MODULE_NAMES[@]}"; do
        echo "  ${MODULE_NAMES[$i]}: ${MODULE_PORTS[$i]}"
    done
}

# Основная логика
case "$1" in
    check)
        check_ports
        ;;
    check-port)
        check_port "$2"
        ;;
    free)
        free_ports
        ;;
    monitor)
        monitor_ports
        ;;
    auto-fix)
        auto_fix
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        log_error "Укажите команду. Используйте '$0 help' для справки"
        exit 1
        ;;
    *)
        log_error "Неизвестная команда: $1"
        echo "Используйте '$0 help' для справки"
        exit 1
        ;;
esac
