# 📁 Bin Directory

This directory contains executable scripts and binaries for the RSecure project.

## 🚀 Executable Scripts

### Main Launcher
- **`start_rsecure.sh`** - Shell script for launching RSecure with proper environment setup

## 📋 Usage

### Quick Start
```bash
# Make script executable (if not already)
chmod +x bin/start_rsecure.sh

# Run RSecure
./bin/start_rsecure.sh
```

### Available Options
```bash
# Run with default settings
./bin/start_rsecure.sh

# Run with dashboard
./bin/start_rsecure.sh --dashboard

# Run in debug mode
./bin/start_rsecure.sh --debug

# Run with specific config
./bin/start_rsecure.sh --config custom_config.json
```

## 🔧 Script Details

### start_rsecure.sh
- **Purpose:** Main launcher script for RSecure
- **Features:**
  - Automatic virtual environment activation
  - Dependency checking
  - Configuration validation
  - Error handling and logging
  - Support for multiple run modes

### Script Arguments
- `--dashboard` - Launch with web dashboard
- `--debug` - Enable debug logging
- `--config <file>` - Use specific configuration file
- `--help` - Show help message

## 📝 Notes

- All scripts are designed to be run from the project root directory
- Scripts will automatically detect and use the appropriate Python environment
- Error messages are logged for troubleshooting
- Some operations may require elevated privileges

## 🔒 Security

- Scripts validate inputs before execution
- Environment variables are sanitized
- Temporary files are cleaned up automatically
- Logging respects privacy settings

## 🐛 Troubleshooting

### Permission Issues
```bash
# Make scripts executable
chmod +x bin/*.sh
```

### Environment Issues
```bash
# Check Python environment
./bin/start_rsecure.sh --check-env
```

### Configuration Issues
```bash
# Validate configuration
./bin/start_rsecure.sh --validate-config
```

## 📚 Related Documentation

- [Installation Guide](../INSTALLATION.md) - Complete installation instructions
- [User Guide](../USER_GUIDE.md) - User documentation
- [Scripts Directory](../scripts/) - Additional utility scripts
