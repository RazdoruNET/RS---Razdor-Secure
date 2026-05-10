#!/bin/bash

# Fixed TPROXY entrypoint with proper routing
# Uses correct TPROXY configuration for transparent proxy

set -e

# Configuration from environment variables
CHUNK_SIZE=${CHUNK_SIZE:-30}
CHUNK_DELAY=${CHUNK_DELAY:-0.005}
LISTEN_PORT=${LISTEN_PORT:-1080}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Function to cleanup network stack
cleanup() {
    echo "[Docker] Остановка системы. Очистка iptables и маршрутов..."
    
    # Remove TPROXY rules from PREROUTING
    iptables -t mangle -D PREROUTING -p tcp --dport 80 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1 2>/dev/null || true
    iptables -t mangle -D PREROUTING -p tcp --dport 443 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1 2>/dev/null || true
    
    # Remove UDP block
    iptables -t mangle -D OUTPUT -p udp --dport 443 -j DROP 2>/dev/null || true
    
    # Remove routing rules
    ip rule del fwmark 1 lookup 100 2>/dev/null || true
    ip route del local default dev lo table 100 2>/dev/null || true
    
    exit 0
}

# Перехватываем сигналы завершения (Ctrl+C / docker stop)
trap cleanup SIGINT SIGTERM

echo "[Docker] Очистка существующих правил перед запуском..."
# Remove existing rules without calling cleanup (to avoid exit)
ip rule del fwmark 1 lookup 100 2>/dev/null || true
ip route del local default dev lo table 100 2>/dev/null || true
iptables -t mangle -D PREROUTING -p tcp --dport 80 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1 2>/dev/null || true
iptables -t mangle -D PREROUTING -p tcp --dport 443 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1 2>/dev/null || true
iptables -t mangle -D OUTPUT -p udp --dport 443 -j DROP 2>/dev/null || true

echo "[Docker] Настройка TPROXY и маршрутизации на хосте..."

# Add routing table first
ip rule add fwmark 1 lookup 100
ip route add local default dev lo table 100

# Add TPROXY rules to PREROUTING chain (not OUTPUT)
iptables -t mangle -A PREROUTING -p tcp --dport 80 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1
iptables -t mangle -A PREROUTING -p tcp --dport 443 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1

# Block UDP/443 to force TCP stack
iptables -t mangle -A OUTPUT -p udp --dport 443 -j DROP

echo "[Docker] Запуск DPI-Evading Proxy Daemon..."
exec python3 /app/proxy_daemon_working.py
