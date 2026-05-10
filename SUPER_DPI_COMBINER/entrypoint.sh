#!/bin/bash

# Entrypoint script for DPI-Evading Transparent Proxy
# Automatically configures TPROXY routing and starts daemon

set -e

# Configuration from environment variables
CHUNK_SIZE=${CHUNK_SIZE:-30}
CHUNK_DELAY=${CHUNK_DELAY:-0.005}
LISTEN_PORT=${LISTEN_PORT:-1080}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# Cleanup function
cleanup() {
    echo "🔄 Cleaning up network rules..."
    
    # Remove iptables rules
    iptables -t mangle -D OUTPUT -p tcp --dport 80 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1 2>/dev/null || true
    iptables -t mangle -D OUTPUT -p tcp --dport 443 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1 2>/dev/null || true
    iptables -t mangle -D OUTPUT -p udp --dport 443 -j DROP 2>/dev/null || true
    
    # Remove ip rules and routes
    ip rule del fwmark 1 lookup 100 2>/dev/null || true
    ip route del local default dev lo table 100 2>/dev/null || true
    
    echo "✅ Network cleanup completed"
}

# Signal handlers
trap cleanup SIGINT SIGTERM

echo "🚀 Starting DPI-Evading Transparent Proxy Container"
echo "📋 Configuration:"
echo "   CHUNK_SIZE: ${CHUNK_SIZE}"
echo "   CHUNK_DELAY: ${CHUNK_DELAY}"
echo "   LISTEN_PORT: ${LISTEN_PORT}"
echo "   LOG_LEVEL: ${LOG_LEVEL}"

# Setup TPROXY routing
echo "🔧 Setting up TPROXY routing..."

# Create routing table for local packets
ip rule add fwmark 1 lookup 100
ip route add local default dev lo table 100

# Add iptables rules for TCP traffic redirection
iptables -t mangle -A OUTPUT -p tcp --dport 80 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1
iptables -t mangle -A OUTPUT -p tcp --dport 443 -j TPROXY --on-port ${LISTEN_PORT} --tproxy-mark 1/1

# Block UDP/443 to force TCP stack
iptables -t mangle -A OUTPUT -p udp --dport 443 -j DROP

echo "✅ TPROXY routing configured"
echo "🌐 Redirecting TCP ports 80 and 443 to local port ${LISTEN_PORT}"
echo "🚫 Blocking UDP/443 (QUIC) to force TCP stack"

# Show current rules
echo "📋 Current iptables rules:"
iptables -t mangle -L OUTPUT -n -v

echo "📋 Current routing rules:"
ip rule list

echo "🚀 Starting proxy daemon..."

# Start the proxy daemon
exec python3 /app/proxy_daemon_working.py \
    --port ${LISTEN_PORT} \
    --chunk-size ${CHUNK_SIZE} \
    --chunk-delay ${CHUNK_DELAY} \
    --log-level ${LOG_LEVEL}
