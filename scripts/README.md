# 📁 Scripts Directory

This directory contains utility scripts and test files for the RSecure project.

## 🚀 Main Scripts

### Installation and Setup
- **`install_rsecure.py`** - Automated installation script for RSecure
- **`uninstall_rsecure.sh`** - Cleanup script for removing RSecure

### Running Modes
- **`maximal_rsecure.py`** - Full-featured RSecure with all modules enabled
- **`minimal_rsecure.py`** - Lightweight RSecure with essential features only
- **`ollama_rsecure.py`** - RSecure with Ollama LLM integration
- **`rsecure_enhanced.py`** - Enhanced version with additional features
- **`simple_rsecure_runner.py`** - Simple runner for basic usage

### Dashboard and Interface
- **`run_rsecure_with_dashboard.py`** - Main dashboard launcher (moved to root)
- **`simple_dashboard.py`** - Lightweight dashboard (moved to root)

## 🧪 Test Scripts

### System Tests
- **`test_rsecure.py`** - Basic system functionality tests
- **`test_runner.py`** - Comprehensive test runner
- **`test_wifi_antipositioning.py`** - WiFi anti-positioning tests
- **`test_neural_encryptor.py`** - Neural encryption tests (moved from examples)

## 📋 Usage

### Installation
```bash
# Run installation script
python scripts/install_rsecure.py

# Uninstall if needed
bash scripts/uninstall_rsecure.sh
```

### Running RSecure
```bash
# Full featured mode
python scripts/maximal_rsecure.py

# Minimal mode
python scripts/minimal_rsecure.py

# With Ollama integration
python scripts/ollama_rsecure.py

# Enhanced mode
python scripts/rsecure_enhanced.py

# Simple runner
python scripts/simple_rsecure_runner.py
```

### Testing
```bash
# Run basic tests
python scripts/test_rsecure.py

# Run comprehensive tests
python scripts/test_runner.py

# Test specific features
python scripts/test_wifi_antipositioning.py
python scripts/test_neural_encryptor.py
```

## 📝 Notes

- All scripts are designed to be run from the project root directory
- Most scripts will automatically detect and use the virtual environment
- Test scripts may require additional dependencies to be installed
- Some scripts may need elevated privileges for certain operations

## 🔧 Configuration

Most scripts can be configured through:
- Command line arguments
- Environment variables
- Configuration files in `config/` directory
- Default settings within each script

For detailed usage instructions, run each script with `--help` flag.
