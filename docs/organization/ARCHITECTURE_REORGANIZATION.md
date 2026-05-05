# RS Razdor Secure - Architecture Reorganization

This document describes the reorganized project structure for better maintainability and clarity.

## New Directory Structure

```
RS---Razdor-Secure/
├── models/                          # AI/ML Models (gitignored for security)
│   └── ai_models/                   # Ollama model files
│       ├── rsecure-analyst.modelfile
│       ├── rsecure-scanner.modelfile
│       ├── rsecure-security.modelfile
│       └── rsecure-wifi-antipositioning.modelfile
├── scripts/                         # All utility and execution scripts
│   ├── startup/                     # Application startup and setup scripts
│   │   ├── README.md
│   │   ├── run_rsecure.py
│   │   ├── run_rsecure_with_dashboard.py
│   │   ├── run_dpi_bypass_daemon.py
│   │   ├── start_fixed_proxy.py
│   │   ├── start_full_system_proxy.py
│   │   ├── start_white_ghost.py
│   │   ├── launch_dpi_bypass_proxy.py
│   │   ├── setup_http_proxy.py
│   │   ├── setup_system_proxy.py
│   │   ├── start_dpi_bypass.sh
│   │   ├── start_rsecure.sh
│   │   ├── status_dpi_bypass.sh
│   │   └── stop_dpi_bypass.sh
│   ├── proxy_tools/                 # Proxy implementation scripts
│   │   ├── README.md
│   │   ├── fin_storm_proxy.py
│   │   ├── enhanced_fin_storm_proxy.py
│   │   ├── final_proxy.py
│   │   ├── robust_proxy.py
│   │   ├── simple_proxy.py
│   │   ├── simple_working_proxy.py
│   │   ├── ultimate_proxy.py
│   │   ├── http_tunnel_proxy.py
│   │   ├── ngrok_proxy.py
│   │   ├── system_proxy.py
│   │   ├── system_proxy_manager.py
│   │   ├── white_ghost_proxy.py
│   │   ├── white_ghost_proxy_fixed.py
│   │   └── working_ngrok_proxy.py
│   ├── dashboard_tools/             # Dashboard and monitoring interfaces
│   │   ├── README.md
│   │   ├── advanced_dashboard.py
│   │   ├── optimized_dashboard.py
│   │   ├── russian_dashboard.py
│   │   ├── simple_dashboard.py
│   │   ├── simple_rsecure_dashboard.py
│   │   ├── turbo_escalation_dashboard.py
│   │   └── turbo_russian_dashboard.py
│   ├── install_rsecure.py           # Installation script
│   ├── advanced_pipelines.py        # Advanced pipeline utilities
│   ├── uninstall_rsecure.sh         # Uninstallation script
│   └── [existing scripts...]        # Other existing scripts
├── tests/                           # All test files organized by type
│   ├── integration/                 # Integration tests
│   │   ├── README.md
│   │   ├── test_dpi_bypass_complete.py
│   │   ├── test_dpi_bypass_combiner_standalone.py
│   │   ├── test_dpi_bypass_combiner_v2.py
│   │   ├── test_dpi_bypass_simple.py
│   │   ├── test_dpi_bypass_standalone.py
│   │   ├── test_10min_timeout.py
│   │   ├── test_dns_fix.py
│   │   ├── test_ollama_fix.py
│   │   ├── test_omega_complete.py
│   │   ├── test_real_accessibility.py
│   │   ├── test_retaliation.py
│   │   ├── test_timeout_fix.py
│   │   ├── test_tor_core_integration.py
│   │   ├── test_tor_simple.py
│   │   └── test_white_ghost_pipelines.py
│   ├── unit/                        # Unit tests
│   │   ├── README.md
│   │   ├── test_neural_encryptor.py
│   │   ├── test_rsecure.py
│   │   ├── test_runner.py
│   │   └── test_wifi_antipositioning.py
│   ├── performance/                 # Performance tests
│   │   └── README.md
│   └── [existing tests...]          # Other existing test files
├── logs/                            # System logs organized by category (gitignored)
│   ├── application/                  # Application-level logs
│   ├── security/                    # Security-related logs
│   ├── dpi_bypass/                  # DPI bypass operation logs
│   ├── system/                      # System-level logs
│   └── monitoring/                  # Monitoring logs
├── test_results/                    # Test results and reports (gitignored)
│   ├── dpi_bypass/                  # DPI bypass test results
│   └── summaries/                   # Executive summaries
├── rsecure/                         # Core application code
├── src/                             # Source code
├── docs/                            # Documentation
├── config/                          # Configuration files
├── examples/                        # Example code
├── tools/                           # Development tools
├── assets/                          # Static assets
├── templates/                       # Template files
├── bin/                             # Binary executables
└── [other directories...]           # Other existing directories
```

## Reorganization Summary

### Before Reorganization
- Model files scattered in `rsecure_models/`
- Test files mixed in root, `scripts/`, and `tests/`
- Startup scripts scattered throughout root directory
- Proxy scripts mixed with other utilities
- Dashboard scripts not organized together

### After Reorganization
- **Models**: Centralized in `models/ai_models/` (4 .modelfile files)
- **Tests**: Organized by type in `tests/` subdirectories
  - Integration tests: 15 files
  - Unit tests: 4 files
  - Performance tests: dedicated directory
- **Startup Scripts**: All in `scripts/startup/` (13 files)
- **Proxy Tools**: All in `scripts/proxy_tools/` (14 files)
- **Dashboard Tools**: All in `scripts/dashboard_tools/` (7 files)
- **Logs**: Organized by category in `logs/` subdirectories
  - Application logs: 4 files
  - Security logs: 15+ files
  - DPI bypass logs: 8+ files
  - System logs: 1 file
  - Monitoring logs: 2 files
- **Test Results**: Organized by type in `test_results/` subdirectories
  - DPI bypass results: 3 JSON files
  - Executive summaries: 3 TXT files

## Benefits

1. **Better Organization**: Related files are grouped together
2. **Easier Maintenance**: Clear separation of concerns
3. **Improved Navigation**: Logical directory structure
4. **Scalability**: Easy to add new files in appropriate categories
5. **Documentation**: Each category has its own README

## Migration Notes

- All model files moved to `models/ai_models/`
- Test files categorized by type (integration/unit/performance)
- Shell scripts moved to appropriate script categories
- Import statements may need updating to reflect new paths
- Configuration files remain in place to avoid breaking existing setups

## Usage

### Running Tests
```bash
# All tests
python -m pytest tests/

# Integration tests only
python -m pytest tests/integration/

# Unit tests only
python -m pytest tests/unit/

# Performance tests only
python -m pytest tests/performance/
```

### Starting the System
```bash
# Main application
python scripts/startup/run_rsecure.py

# With dashboard
python scripts/startup/run_rsecure_with_dashboard.py

# DPI bypass daemon
python scripts/startup/run_dpi_bypass_daemon.py
```

### Using Proxy Tools
```bash
# Fin Storm proxy
python scripts/proxy_tools/fin_storm_proxy.py

# White Ghost proxy
python scripts/proxy_tools/white_ghost_proxy.py
```

### Dashboard Interfaces
```bash
# Advanced dashboard
python scripts/dashboard_tools/advanced_dashboard.py

# Simple dashboard
python scripts/dashboard_tools/simple_dashboard.py
```

### Log Analysis
```bash
# View security logs
tail -f logs/security/cvu_intelligence.log

# Monitor DPI bypass logs
tail -f logs/dpi_bypass/dpi_bypass.log

# Check application logs
tail -f logs/application/dashboard.log
```

### Test Results Analysis
```bash
# View latest DPI bypass test results
cat test_results/dpi_bypass/dpi_bypass_combiner_test_*.json

# Check test summaries
cat test_results/summaries/dpi_bypass_combiner_test_*_summary.txt
```

This reorganization maintains backward compatibility while providing a cleaner, more maintainable project structure. All logs and test results are now properly categorized for easier analysis and debugging.
