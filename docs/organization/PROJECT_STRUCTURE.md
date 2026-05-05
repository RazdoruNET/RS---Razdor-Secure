# 📁 RSecure Project Structure

This document describes the complete directory structure of the RSecure project after reorganization for release.

## 🌳 Directory Tree

```
rsecure/
├── 📋 README.md                       # Main project documentation
├── 📚 USER_GUIDE.md                  # Complete user guide
├── ⚙️ INSTALLATION.md                # Installation instructions
├── 📁 PROJECT_STRUCTURE.md            # This file - project structure
├── 📁 LICENSE                        # License file
├── 📁 .gitignore                     # Git ignore rules
├── 📁 requirements.txt                # Python dependencies
├── 📁 rsecure_modules_integration_guide.md # Module integration guide
├── 
├── 📁 bin/                           # Executable scripts
│   ├── 🚀 rsecure                     # Main executable launcher
│   ├── 🚀 start_rsecure.sh             # Shell launcher script
│   └── 📋 README.md                   # Bin directory documentation
│
├── 📁 scripts/                       # Utility and test scripts
│   ├── 🚀 install_rsecure.py           # Installation script
│   ├── 🚀 maximal_rsecure.py            # Full-featured launcher
│   ├── 🚀 minimal_rsecure.py            # Minimal launcher
│   ├── 🚀 ollama_rsecure.py             # Ollama integration launcher
│   ├── 🚀 rsecure_enhanced.py          # Enhanced launcher
│   ├── 🚀 simple_rsecure_runner.py      # Simple runner
│   ├── 🧪 test_rsecure.py              # Basic tests
│   ├── 🧪 test_runner.py               # Test runner
│   ├── 🧪 test_wifi_antipositioning.py # WiFi tests
│   └── 📋 README.md                   # Scripts documentation
│
├── 📁 tools/                         # Development and maintenance tools
│   └── 📋 README.md                   # Tools documentation
│
├── 📁 config/                        # Configuration files
│   ├── 📋 README.md                   # Config documentation
│   └── 📁 templates/                  # Configuration templates
│       └── 📄 rsecure_config.template.json # Main config template
│
├── 📁 examples/                      # Example scripts and demos
│   ├── 🔓 neural_encryptor_examples.py  # Neural encryption examples
│   └── 📋 README.md                   # Examples documentation
│
├── 📁 rsecure/                       # Main RSecure package
│   ├── 🎯 rsecure_main.py              # Main application entry point
│   ├── 📁 __init__.py                  # Package initialization
│   ├── 📁 core/                        # Core modules
│   │   ├── 🧬 neural_security_core.py  # Neural security core
│   │   ├── 🎮 reinforcement_learning.py # RL algorithms
│   │   ├── 🤖 ollama_integration.py     # LLM integration
│   │   └── 📁 __init__.py               # Core package init
│   ├── 📁 modules/                      # Security modules
│   │   ├── 📁 __init__.py               # Modules package init
│   │   ├── 📁 detection/                # Threat detection modules
│   │   │   ├── 🎣 phishing_detector.py  # Phishing detection
│   │   │   ├── 💻 system_detector.py    # System threat detection
│   │   │   ├── 🛡️ cvu_intelligence.py   # CVU intelligence
│   │   │   └── 📁 __init__.py           # Detection package init
│   │   ├── 📁 defense/                  # Defense modules
│   │   │   ├── 🌐 network_defense.py    # Network defense
│   │   │   ├── 🤖 llm_defense.py         # LLM defense
│   │   │   ├── 🔓 dpi_bypass.py          # DPI bypass (10+ methods)
│   │   │   ├── 🔐 traffic_obfuscation.py  # Traffic obfuscation
│   │   │   ├── 🌐 tor_integration.py       # Tor integration
│   │   │   ├── 🛡️ vpn_proxy.py             # VPN and proxy
│   │   │   ├── 🎮 system_control.py       # System control
│   │   │   └── 📁 __init__.py           # Defense package init
│   │   ├── 📁 monitoring/                # Monitoring modules
│   │   │   ├── 🎵 audio_stream_monitor.py # Audio monitoring
│   │   │   ├── 📹 audio_video_monitor.py # Video monitoring
│   │   │   └── 📁 __init__.py           # Monitoring package init
│   │   ├── 📁 protection/                # Protection modules
│   │   │   ├── 🛡️ psychological_protection.py # Psychological protection
│   │   │   └── 📁 __init__.py           # Protection package init
│   │   ├── 📁 analysis/                  # Analysis modules
│   │   │   ├── 📊 security_analytics.py  # Security analytics
│   │   │   └── 📁 __init__.py           # Analysis package init
│   │   └── 📁 notification/             # Notification modules
│   │       ├── 🍎 macos_notifications.py # macOS notifications
│   │       └── 📁 __init__.py           # Notification package init
│   ├── 📁 utils/                        # Utility modules
│   │   ├── 📊 dashboard.py             # Web dashboard
│   │   ├── 📝 monitoring_logger.py     # Logging utilities
│   │   └── 📁 __init__.py               # Utils package init
│   ├── 📁 config/                       # Configuration data
│   │   └── 🛡️ offline_threats.json      # Offline threat database
│   └── 📁 tests/                        # Internal tests
│       └── 🧪 rsecure_test.py           # Internal test suite
│
├── 📁 tests/                         # Test suites
│   ├── 📁 __init__.py                  # Tests package init
│   ├── 🔍 test_dpi_bypass.py          # DPI bypass tests
│   ├── 🛡️ test_vpn_proxy.py            # VPN/proxy tests
│   ├── 🔐 test_traffic_obfuscation.py # Traffic obfuscation tests
│   ├── 🌐 test_tor_integration.py     # Tor integration tests
│   ├── 📊 test_behavioral_analysis.py # Behavioral analysis tests
│   ├── 🌊 test_spectral_analysis.py   # Spectral analysis tests
│   ├── 🧠 test_neural_architectures.py # Neural architecture tests
│   └── ⚙️ conftest.py                  # Pytest configuration
│
├── 📁 docs/                          # Documentation
│   ├── 📖 README.md                   # Documentation index
│   ├── 📁 architecture/                # Architecture documentation
│   │   └── 📋 overview.md               # System architecture overview
│   ├── 📁 core-modules/                # Core module documentation
│   │   ├── 🧬 neural-security-core.md  # Neural core docs
│   │   ├── 🤖 ollama-integration.md   # Ollama integration docs
│   │   └── 🎮 reinforcement-learning.md # RL documentation
│   ├── 📁 defense/                     # Defense module documentation
│   │   ├── 🔓 dpi-bypass-guide.md      # DPI bypass guide
│   │   ├── 🛡️ vpn-proxy-guide.md       # VPN/proxy guide
│   │   ├── 🔐 traffic-obfuscation-guide.md # Obfuscation guide
│   │   ├── 🌐 tor-integration-guide.md  # Tor integration guide
│   │   ├── 🧠 neural-wave-protection.md # Neural wave protection
│   │   ├── 🛡️ wifi-antipositioning-defense.md # WiFi defense
│   │   ├── 🎭 psychological-protection.md # Psychological protection
│   │   ├── 🌐 network-defense.md       # Network defense
│   │   ├── 🤖 llm-defense.md           # LLM defense
│   │   └── 🎥 visual-security.md       # Visual security
│   ├── 📁 detection/                  # Detection module documentation
│   │   ├── 🎣 phishing-detector.md     # Phishing detector docs
│   │   └── 💻 system-detector.md       # System detector docs
│   ├── 📁 monitoring/                  # Monitoring module documentation
│   │   ├── 📹 audio-video-monitor.md   # Audio/video monitoring
│   │   └── 📊 system-monitoring.md     # System monitoring
│   ├── 📁 algorithms/                  # Algorithm documentation
│   │   ├── 📈 behavioral-analysis.md   # Behavioral analysis
│   │   └── 🌊 spectral-analysis.md     # Spectral analysis
│   ├── 📁 research/                    # Research documentation
│   │   ├── 🔬 scientific-foundations.md # Scientific foundations
│   │   └── 🧠 neural-wave-scientific-foundations.md # Neural wave research
│   └── 📁 api/                         # API documentation
│       ├── 🐍 python-api.md             # Python API docs
│       └── 🌐 rest-api.md               # REST API docs
│
├── 📁 assets/                        # Static assets
│   └── 🖼️ we_razdor_logo.png          # Project logo
│
├── 📁 templates/                     # Web templates
│   └── 🌐 dashboard.html              # Dashboard HTML template
│
├── 📁 mock_libs/                     # Mock libraries for testing
│   ├── 📁 __init__.py                  # Mock libs package init
│   └── 🧬 tensorflow.py               # TensorFlow mock
│
├── 📁 rsecure_models/                # RSecure model files
│   ├── 🔍 rsecure-scanner.modelfile  # Scanner model
│   ├── 🤖 rsecure-analyst.modelfile  # Analyst model
│   └── 🛡️ rsecure-security.modelfile # Security model
│
├── 📁 logs/                          # Log files directory
├── 📁 data/                          # Data directory
├── 📁 backups/                       # Backup directory
├── 📁 quarantine/                    # Quarantine directory
├── 📁 models/                        # Model storage
│
├── 📁 rsecure_env/                   # Python virtual environment
├── 📁 tf_env/                       # TensorFlow environment
│
├── 🚀 run_rsecure.py                 # Simple runner script
├── 🚀 run_rsecure_with_dashboard.py # Dashboard launcher
├── 🚀 simple_dashboard.py            # Simple dashboard
└── 🗑️ uninstall_rsecure.sh            # Uninstallation script
```

## 📁 Directory Purposes

### 🚀 Root Level Files
- **Documentation**: Main project documentation (README, USER_GUIDE, INSTALLATION)
- **Launchers**: Entry points for running RSecure
- **Configuration**: Project-level configuration and templates
- **Dependencies**: Python requirements and virtual environments

### 📁 bin/ - Executables
- **Main executable**: `rsecure` - primary launcher script
- **Shell scripts**: `start_rsecure.sh` - shell-based launcher
- **Purpose**: Provide easy access to RSecure functionality

### 📁 scripts/ - Utility Scripts
- **Installation**: `install_rsecure.py` - automated setup
- **Launchers**: Various RSecure launchers for different modes
- **Testing**: Test scripts and test runners
- **Purpose**: Development, testing, and utility functions

### 📁 tools/ - Development Tools
- **Build tools**: Project building and packaging
- **Deployment**: Deployment automation
- **Maintenance**: Cleanup, backup, update utilities
- **Purpose**: Development workflow and project maintenance

### 📁 config/ - Configuration
- **Templates**: Configuration file templates
- **Environment-specific**: Development, production, testing configs
- **Module configs**: Individual module configuration files
- **Purpose**: Centralized configuration management

### 📁 examples/ - Examples and Demos
- **Usage examples**: Demonstrations of RSecure functionality
- **Integration examples**: How to integrate with other systems
- **Purpose**: Learning and reference implementations

### 📁 rsecure/ - Main Package
- **Core**: Neural security core, RL, LLM integration
- **Modules**: Detection, defense, monitoring, protection modules
- **Utils**: Dashboard, logging, utilities
- **Purpose**: Main application code

### 📁 tests/ - Test Suites
- **Unit tests**: Individual module tests
- **Integration tests**: Cross-module functionality tests
- **Performance tests**: Load and stress testing
- **Purpose**: Quality assurance and validation

### 📁 docs/ - Documentation
- **Architecture**: System design and architecture
- **Modules**: Detailed module documentation
- **APIs**: Python and REST API documentation
- **Purpose**: Comprehensive project documentation

## 🔄 File Organization Principles

### 1. **Separation of Concerns**
- **Code vs. Configuration**: Code in `rsecure/`, configs in `config/`
- **Executables vs. Libraries**: Executables in `bin/`, libraries in `rsecure/`
- **Development vs. Production**: Dev tools in `tools/`, production in `rsecure/`

### 2. **Logical Grouping**
- **Functionality**: Related modules grouped together
- **Purpose**: Scripts grouped by purpose (install, test, run)
- **Hierarchy**: Clear parent-child relationships

### 3. **Accessibility**
- **Common tasks**: Easy access through `bin/` and root-level scripts
- **Development**: Development tools in `tools/`
- **Documentation**: Comprehensive docs in `docs/`

### 4. **Maintainability**
- **Clear structure**: Intuitive directory organization
- **Documentation**: README files in each directory
- **Consistency**: Consistent naming and structure

## 🚀 Usage Patterns

### For Users
```bash
# Quick start
./bin/rsecure

# With dashboard
./bin/rsecure dashboard

# With specific config
./bin/rsecure --config custom.json
```

### For Developers
```bash
# Run tests
python -m pytest tests/

# Development mode
python scripts/rsecure_enhanced.py

# Build project
python tools/build.py
```

### For System Administrators
```bash
# Install
python scripts/install_rsecure.py

# Deploy
python tools/deploy.py --env production

# Monitor
python tools/monitor.py --realtime
```

## 📝 Maintenance Guidelines

### Adding New Modules
1. Create module in appropriate `rsecure/modules/` subdirectory
2. Add tests in `tests/`
3. Add documentation in `docs/`
4. Update configuration templates if needed

### Adding New Scripts
1. Place utility scripts in `scripts/`
2. Place development tools in `tools/`
3. Add executables to `bin/`
4. Update relevant README files

### Configuration Management
1. Use templates in `config/templates/`
2. Environment-specific configs in `config/`
3. Validate configurations before use
4. Document all configuration options

This structure ensures a clean, maintainable, and user-friendly project organization suitable for release.
