#!/bin/bash

# Simplified entrypoint for testing without TPROXY
# Focus on proxy daemon functionality first

set -e

# Configuration from environment variables
CHUNK_SIZE=${CHUNK_SIZE:-30}
CHUNK_DELAY=${CHUNK_DELAY:-0.005}
LISTEN_PORT=${LISTEN_PORT:-1080}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "[Docker] Запуск DPI-Evading Proxy Daemon в режиме прямого прослушивания..."
echo "[Docker] Конфигурация: port=${LISTEN_PORT}, chunk_size=${CHUNK_SIZE}, chunk_delay=${CHUNK_DELAY}"

# Запускаем прокси демон напрямую без TPROXY маршрутизации
exec python3 /app/proxy_daemon_working.py
