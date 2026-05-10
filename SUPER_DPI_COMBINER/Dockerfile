#!/usr/bin/env python3
# Dockerfile for Super DPI Combiner
# Real DPI bypass system with network functionality

FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies for TPROXY
RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    net-tools \
    curl \
    netcat-openbsd \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpcap-dev \
    tcpdump \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Copy stage 3 components
COPY proxy_daemon_working.py /app/
COPY destination_extractor_final.py /app/
COPY verification/ /app/verification/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config

# Set permissions
RUN chmod +x /app/proxy_daemon_working.py

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV CHUNK_SIZE=30
ENV CHUNK_DELAY=0.005
ENV LISTEN_PORT=1080
ENV LOG_LEVEL=INFO

# Expose proxy port
EXPOSE 1080

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
