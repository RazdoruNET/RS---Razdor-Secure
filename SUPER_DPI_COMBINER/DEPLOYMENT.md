# Super DPI Combiner - Deployment Guide

## Overview

Super DPI Combiner is a real DPI bypass system with network functionality, replacing simulation with actual network operations.

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB
- **Network**: Stable internet connection

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+
- **Network**: High-speed connection with low latency

## Quick Start with Docker

### 1. Clone Repository
```bash
git clone <repository-url>
cd SUPER_DPI_COMBINER
```

### 2. Basic Deployment
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f super-dpi-combiner
```

### 3. Access Services
- **Main API**: http://localhost:8080
- **HTTPS API**: https://localhost:8443
- **Proxy**: localhost:3128
- **SOCKS Proxy**: localhost:1080
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

## Advanced Deployment

### Custom Configuration
```bash
# Copy and modify configuration
cp config/production.json config/custom.json

# Edit configuration
nano config/custom.json

# Deploy with custom config
docker-compose -f docker-compose.yml -f docker-compose.custom.yml up -d
```

### Environment Variables
```bash
# Create .env file
cat > .env << EOF
LOG_LEVEL=INFO
DPI_MODE=production
MAX_WORKERS=50
REDIS_HOST=redis
ELASTICSEARCH_HOST=elasticsearch
EOF
```

## Service Configuration

### Main Service (super-dpi-combiner)
- **Ports**: 8080, 8443, 3128, 1080
- **Environment**: PYTHONPATH, LOG_LEVEL, DPI_MODE
- **Volumes**: config/, logs/, data/

### Redis Cache
- **Port**: 6379
- **Memory Limit**: 256MB
- **Persistence**: Enabled

### Nginx Reverse Proxy
- **Ports**: 80, 443
- **SSL**: Self-signed certificates (replace with production certs)
- **Load Balancing**: Round-robin

### Monitoring Stack
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Visualization (port 3000)
- **Elasticsearch**: Log storage (port 9200)
- **Kibana**: Log analysis (port 5601)

## Configuration Files

### Main Configuration (config/production.json)
```json
{
  "system": {
    "mode": "production",
    "max_workers": 50,
    "timeout": 30.0
  },
  "pipelines": {
    "enabled": [
      "spoof_dpi/packet_shaper",
      "domain_fronting/cdn_bypass",
      "protocol_obfuscation/http_fragmentation"
    ]
  },
  "network": {
    "dns_servers": ["8.8.8.8", "1.1.1.1"],
    "user_agents": [...]
  }
}
```

### Nginx Configuration (nginx/nginx.conf)
- Load balancing setup
- SSL termination
- Rate limiting
- Security headers

## Security Considerations

### Production Deployment
1. **Replace Default Credentials**
   ```bash
   # Grafana admin password
   docker-compose exec grafana grafana-cli admin reset-admin-password
   
   # Redis password
   # Edit redis configuration in docker-compose.yml
   ```

2. **SSL Certificates**
   ```bash
   # Generate production SSL certificates
   mkdir -p nginx/ssl
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem \
     -out nginx/ssl/cert.pem
   ```

3. **Network Security**
   ```bash
   # Firewall configuration
   ufw allow 80
   ufw allow 443
   ufw allow 22
   ufw enable
   ```

### Access Control
- **IP Whitelisting**: Configure in security section
- **Rate Limiting**: Built-in rate limiting
- **Authentication**: API key authentication

## Performance Tuning

### System Optimization
```bash
# Increase file limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Network optimization
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

### Docker Optimization
```yaml
# In docker-compose.yml
services:
  super-dpi-combiner:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Monitoring and Logging

### Metrics Collection
- **Request Rate**: RPS per pipeline
- **Success Rate**: Percentage of successful bypasses
- **Response Time**: Average response times
- **Error Rate**: Failed requests percentage

### Log Analysis
```bash
# View real-time logs
docker-compose logs -f super-dpi-combiner

# Search logs
docker-compose logs super-dpi-combiner | grep ERROR

# Export logs
docker-compose logs --no-color super-dpi-combiner > logs.txt
```

### Grafana Dashboards
1. **System Overview**: CPU, Memory, Network
2. **DPI Bypass Metrics**: Success rates, response times
3. **Pipeline Performance**: Individual pipeline metrics
4. **Error Analysis**: Error types and frequencies

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs super-dpi-combiner

# Check configuration
docker-compose config

# Restart services
docker-compose restart
```

#### Network Connectivity Issues
```bash
# Test DNS resolution
docker-compose exec super-dpi-combiner nslookup google.com

# Test external connectivity
docker-compose exec super-dpi-combiner curl -I https://httpbin.org/ip

# Check firewall rules
iptables -L -n
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor system resources
htop
iotop
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up -d

# Run with single worker for debugging
export MAX_WORKERS=1
docker-compose up -d
```

## Scaling

### Horizontal Scaling
```yaml
# In docker-compose.yml
services:
  super-dpi-combiner:
    deploy:
      replicas: 3
```

### Load Balancing
- **Nginx**: Built-in load balancing
- **HAProxy**: Alternative load balancer
- **Kubernetes**: Container orchestration

## Backup and Recovery

### Data Backup
```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz config/ data/

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp dpi-redis:/data/dump.rdb ./redis-backup.rdb
```

### Recovery
```bash
# Restore configuration
tar -xzf backup-YYYYMMDD.tar.gz

# Restore Redis data
docker cp ./redis-backup.rdb dpi-redis:/data/dump.rdb
docker-compose restart redis
```

## Updates and Maintenance

### Updating Services
```bash
# Pull latest images
docker-compose pull

# Recreate services
docker-compose up -d --force-recreate

# Clean up old images
docker image prune -f
```

### Maintenance Tasks
```bash
# Log rotation
docker-compose exec super-dpi-combiner find /app/logs -name "*.log" -mtime +7 -delete

# Cache cleanup
docker-compose exec redis redis-cli FLUSHDB

# System cleanup
docker system prune -f
```

## Support

### Getting Help
- **Documentation**: Check this guide and inline documentation
- **Logs**: Review application logs for error messages
- **Metrics**: Use Grafana dashboards for performance analysis
- **Community**: GitHub issues and discussions

### Contributing
1. Fork the repository
2. Create feature branch
3. Submit pull request
4. Follow code review process

## License

This project is licensed under the MIT License. See LICENSE file for details.
