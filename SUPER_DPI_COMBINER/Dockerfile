#!/usr/bin/env python3
# Dockerfile for Super DPI Combiner
# Real DPI bypass system with network functionality

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpcap-dev \
    tcpdump \
    netcat-openbsd \
    curl \
    wget \
    dnsutils \
    iproute2 \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dpi && \
    chown -R dpi:dpi /app
USER dpi

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config

# Expose ports for different services
EXPOSE 8080 8443 3128 1080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "main.py", "--config", "config/settings.json", "--mode", "production"]
