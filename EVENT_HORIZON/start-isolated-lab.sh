#!/bin/bash

# EVENT_HORIZON Isolated Laboratory Startup Script
# This script starts the complete isolated lab environment for defensive testing
# CRITICAL: This environment is completely isolated from production systems

set -e

echo "=========================================="
echo "EVENT_HORIZON Isolated Laboratory Startup"
echo "=========================================="
echo ""
echo "WARNING: This is an isolated laboratory environment"
echo "Do NOT modify targets to production systems"
echo "=========================================="
echo ""

# Validate environment
if [ -z "$EVENT_HORIZON_MODE" ]; then
    export EVENT_HORIZON_MODE=isolated_lab
    echo "Setting mode: isolated_lab"
fi

# Create necessary directories
mkdir -p data logs

# Validate Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

# Validate Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    exit 1
fi

# Stop any existing containers
echo "Stopping any existing containers..."
docker-compose -f docker-compose-isolated.yml down

# Start isolated lab environment
echo ""
echo "Starting isolated laboratory environment..."
docker-compose -f docker-compose-isolated.yml up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."
docker-compose -f docker-compose-isolated.yml ps

echo ""
echo "=========================================="
echo "Isolated Laboratory Environment Started"
echo "=========================================="
echo ""
echo "Available Services:"
echo "  - EVENT_HORIZON: http://localhost:8000"
echo "  - Mock Target: http://localhost:9000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/eventhorizon123)"
echo "  - Redis: localhost:6379"
echo ""
echo "To run tests:"
echo "  docker-compose -f docker-compose-isolated.yml exec event-horizon python -m src.main --target http://mock-target:9000"
echo ""
echo "To stop the environment:"
echo "  docker-compose -f docker-compose-isolated.yml down"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose-isolated.yml logs -f"
echo ""
echo "=========================================="
echo "CRITICAL: This is an isolated laboratory only"
echo "Never connect to production systems"
echo "=========================================="
