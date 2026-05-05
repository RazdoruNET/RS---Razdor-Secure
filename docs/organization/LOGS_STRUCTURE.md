# Logs Structure Documentation

This document describes the organized log file structure for the RS Razdor Secure system.

## Directory Structure

```
logs/
├── application/          # Application-level logs
│   ├── dashboard.log
│   ├── rsecure_*.log
│   └── ollama_rsecure.log
├── security/            # Security-related logs
│   ├── cvu_intelligence.log
│   ├── llm_defense.log
│   ├── phishing_detector.log
│   ├── network_defense.log
│   ├── combat_operations*.log
│   ├── counter_attacks.log
│   ├── equipment_*.log
│   ├── escalation*.log
│   ├── retaliation.log
│   ├── stealth_operations.log
│   ├── total_*.log
│   ├── turbo_*.log
│   ├── wifi_antipositioning.log
│   └── security_analysis.log
├── dpi_bypass/          # DPI bypass operation logs
│   ├── dpi_bypass*.log
│   ├── dpi_bypass_daemon.log
│   ├── dpi_bypass_v2*.log
│   └── timestamped_bypass_logs/
├── system/              # System-level logs
│   └── system_control.log
└── monitoring/          # Monitoring logs
    ├── audio_video_monitor.log
    └── macos_notifications.log
```

## Log Categories

### Application Logs
- **dashboard.log** - Dashboard application events and errors
- **rsecure_*.log** - Main RSecure application logs
- **ollama_rsecure.log** - Ollama AI integration logs

### Security Logs
- **cvu_intelligence.log** - CVU intelligence operations
- **llm_defense.log** - LLM-based defense mechanisms
- **phishing_detector.log** - Phishing detection activities
- **network_defense.log** - Network defense operations
- **combat_operations*.log** - Combat operation logs
- **counter_attacks.log** - Counter-attack activities
- **equipment_*.log** - Equipment control and status
- **escalation*.log** - Escalation procedure logs
- **retaliation.log** - Retaliation mechanism logs
- **stealth_operations.log** - Stealth operation logs
- **total_*.log** - Total system operation logs
- **turbo_*.log** - Turbo mode operation logs
- **wifi_antipositioning.log** - WiFi anti-positioning logs
- **security_analysis.log** - Security analysis results

### DPI Bypass Logs
- **dpi_bypass*.log** - General DPI bypass operations
- **dpi_bypass_daemon.log** - DPI bypass daemon logs
- **dpi_bypass_v2*.log** - DPI bypass v2 implementation logs
- **Timestamped logs** - Individual bypass session logs

### System Logs
- **system_control.log** - System control operations

### Monitoring Logs
- **audio_video_monitor.log** - Audio/video monitoring activities
- **macos_notifications.log** - macOS notification system logs

## Usage Guidelines

### For Debugging
1. Check `application/` logs for application errors
2. Review `security/` logs for security-related issues
3. Use `dpi_bypass/` logs for DPI bypass troubleshooting
4. Monitor `system/` logs for system-level problems

### For Monitoring
1. Regular monitoring of `security/` logs for threats
2. Watch `monitoring/` logs for system health
3. Track `dpi_bypass/` logs for bypass effectiveness

### Log Analysis
- Use grep and filtering tools to search specific events
- Correlate timestamps across different log categories
- Monitor log file sizes for disk space management

## Log Management

### Rotation
- Implement log rotation for long-running systems
- Archive old logs periodically
- Compress archived logs to save space

### Security
- Logs contain sensitive security information
- Ensure proper access controls
- Consider encryption for highly sensitive logs

### Retention
- Define retention policies based on compliance requirements
- Regular cleanup of old log files
- Backup critical logs before deletion
