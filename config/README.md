# ⚙️ Config Directory

This directory contains configuration files and templates for the RSecure project.

## 📁 Configuration Files

### Main Configuration
- **`rsecure_config.json`** - Main RSecure configuration (should be in project root)
- **`rsecure_config.template.json`** - Configuration template
- **`development.json`** - Development environment settings
- **`production.json`** - Production environment settings
- **`testing.json`** - Testing environment settings

### Module Configurations
- **`dpi_bypass.json`** - DPI bypass module configuration
- **`vpn_proxy.json`** - VPN and proxy settings
- **`traffic_obfuscation.json`** - Traffic obfuscation settings
- **`tor_integration.json`** - Tor integration configuration
- **`neural_core.json`** - Neural network settings
- **`ollama.json`** - Ollama LLM integration settings

### Security Configurations
- **`security_policies.json`** - Security policies and rules
- **`threat_levels.json`** - Threat level definitions
- **`logging.json`** - Logging configuration
- **`alerts.json`** - Alert and notification settings

## 📋 Configuration Structure

### Main Configuration Template
```json
{
  "system_detection": {
    "enabled": true,
    "scan_interval": 30
  },
  "monitoring": {
    "enabled": true,
    "log_interval": 1,
    "network_scan_interval": 30
  },
  "neural_core": {
    "enabled": true,
    "threat_threshold": 0.7,
    "model_path": "models/neural_security.pt"
  },
  "network_defense": {
    "enabled": true,
    "monitored_ports": [22, 80, 443],
    "auto_block": true
  },
  "dpi_bypass": {
    "enabled": false,
    "default_method": "adaptive",
    "tor_enabled": true,
    "vpn_enabled": false
  },
  "traffic_obfuscation": {
    "enabled": false,
    "default_method": "aes",
    "encryption_key": "auto_generated"
  },
  "ollama": {
    "enabled": true,
    "host": "localhost",
    "port": 11434,
    "models": ["qwen2.5-coder:1.5b", "gemma2:2b"]
  },
  "notifications": {
    "enabled": true,
    "methods": ["desktop", "email"],
    "threshold": 0.8,
    "cooldown": 300
  }
}
```

### DPI Bypass Configuration
```json
{
  "methods": {
    "fragmentation": {
      "enabled": true,
      "fragment_size": 512,
      "delay_ms": 50
    },
    "tor_routing": {
      "enabled": true,
      "socks_port": 9050,
      "circuit_timeout": 60
    },
    "vpn_tunneling": {
      "enabled": false,
      "auto_connect": false
    }
  },
  "adaptive_selection": {
    "enabled": true,
    "success_threshold": 0.8,
    "performance_weight": 0.6
  }
}
```

## 🔧 Configuration Management

### Loading Configuration
```python
import json
from pathlib import Path

def load_config(config_name="rsecure_config.json"):
    config_path = Path(config_name)
    if not config_path.exists():
        config_path = Path("config") / config_name
    
    with open(config_path, 'r') as f:
        return json.load(f)

# Usage
config = load_config()
```

### Environment-Specific Configuration
```python
import os

def get_environment():
    return os.getenv('RSECURE_ENV', 'development')

def load_env_config():
    env = get_environment()
    return load_config(f"{env}.json")

# Usage
config = load_env_config()
```

### Configuration Validation
```python
def validate_config(config):
    required_sections = ['system_detection', 'monitoring', 'neural_core']
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section: {section}")
    
    return True

# Usage
if validate_config(config):
    print("Configuration is valid")
```

## 🌍 Environment Variables

### Configuration Override
```bash
# Override configuration file
export RSECURE_CONFIG=/path/to/custom_config.json

# Environment
export RSECURE_ENV=production

# Debug mode
export RSECURE_DEBUG=1

# Log level
export RSECURE_LOG_LEVEL=DEBUG
```

### Security Settings
```bash
# Encryption key
export RSECURE_ENCRYPTION_KEY=your_key_here

# Database password
export RSECURE_DB_PASSWORD=your_db_password

# API keys
export RSECURE_API_KEY=your_api_key
```

## 📝 Configuration Templates

### Development Configuration
```json
{
  "debug": true,
  "log_level": "DEBUG",
  "monitoring": {
    "enabled": true,
    "log_interval": 1
  },
  "neural_core": {
    "enabled": true,
    "threat_threshold": 0.5
  }
}
```

### Production Configuration
```json
{
  "debug": false,
  "log_level": "INFO",
  "monitoring": {
    "enabled": true,
    "log_interval": 60
  },
  "neural_core": {
    "enabled": true,
    "threat_threshold": 0.8
  }
}
```

## 🔒 Security Considerations

### Sensitive Data
- Store encryption keys separately from configuration
- Use environment variables for sensitive values
- Restrict file permissions on configuration files
- Regularly rotate encryption keys and passwords

### File Permissions
```bash
# Set appropriate permissions
chmod 600 config/*.json
chmod 700 config/
```

### Configuration Backup
```bash
# Backup configuration
cp config/*.json backups/config_$(date +%Y%m%d_%H%M%S)/
```

## 📚 Best Practices

1. **Use Templates**: Start with templates and customize as needed
2. **Environment Separation**: Use different configs for dev/staging/prod
3. **Validation**: Always validate configuration before use
4. **Security**: Keep sensitive data out of version control
5. **Documentation**: Document custom configuration options
6. **Backup**: Regular backup of configuration files
7. **Version Control**: Use version control for non-sensitive configs

## 🚀 Getting Started

### Create Initial Configuration
```bash
# Copy template
cp config/rsecure_config.template.json rsecure_config.json

# Edit for your environment
nano rsecure_config.json
```

### Validate Configuration
```bash
# Use RSecure config validator
python -c "
from rsecure.config.validator import validate_config
validate_config('rsecure_config.json')
"
```

### Test Configuration
```bash
# Test with specific config
RSECURE_CONFIG=test_config.json python rsecure/rsecure_main.py
```

## 📖 Related Documentation

- [Installation Guide](../INSTALLATION.md) - Setup and configuration
- [User Guide](../USER_GUIDE.md) - Configuration usage
- [Security Guide](../docs/security/) - Security best practices
- [Development Guide](../docs/development/) - Development configuration
