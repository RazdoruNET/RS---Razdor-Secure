#!/bin/bash
# EVENT_HORIZON Docker Security Audit Script for dsmoto.ru
# Official Authorization: OFFICIAL_AUDIT_2024

set -e

echo "🔐 EVENT_HORIZON Security Audit - dsmoto.ru"
echo "📋 Authorization: OFFICIAL_AUDIT_2024"
echo ""

# Create necessary directories
mkdir -p results
mkdir -p logs
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring

# Create monitoring configuration
cat > monitoring/prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'event_horizon'
    static_configs:
      - targets: ['event-horizon:8080']
EOF

# Build Docker image
echo "🏗️  Building Docker image..."
docker-compose build

# Start services
echo "🚀 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "✅ EVENT_HORIZON Security Audit started successfully"
echo ""
echo "📋 Service URLs:"
echo "   - EVENT_HORIZON: http://localhost:8080"
echo "   - Grafana: http://localhost:3000 (admin/event_horizon_secure)"
echo "   - Prometheus: http://localhost:9090"
echo ""
echo "📁 Results will be saved to: ./results/"
echo "📁 Logs will be saved to: ./logs/"
echo ""
echo "🔍 Running security audit..."
docker-compose exec event-horizon python main.py run-assessment \
  --target dsmoto.ru \
  --mode security-audit \
  --config /app/config/dsmoto_audit_config.yaml

echo ""
echo "✅ Security audit completed"
echo "📊 Results available in ./results/ directory"
