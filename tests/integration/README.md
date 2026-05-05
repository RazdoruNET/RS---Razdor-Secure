# Integration Tests

This directory contains integration tests for the RS Razdor Secure system. These tests verify that different components work together correctly.

## Test Categories

### DPI Bypass Tests
- `test_dpi_bypass_complete.py` - Complete DPI bypass functionality
- `test_dpi_bypass_combiner_standalone.py` - Standalone DPI bypass combiner
- `test_dpi_bypass_combiner_v2.py` - DPI bypass combiner version 2
- `test_dpi_bypass_simple.py` - Simple DPI bypass test
- `test_dpi_bypass_standalone.py` - Standalone DPI bypass test

### System Integration Tests
- `test_10min_timeout.py` - 10-minute timeout test
- `test_dns_fix.py` - DNS resolution fix test
- `test_ollama_fix.py` - Ollama integration fix test
- `test_omega_complete.py` - Complete Omega system test
- `test_real_accessibility.py` - Real accessibility test
- `test_retaliation.py` - Retaliation mechanism test
- `test_timeout_fix.py` - Timeout fix verification
- `test_tor_core_integration.py` - Tor core integration test
- `test_tor_simple.py` - Simple Tor test
- `test_white_ghost_pipelines.py` - White Ghost pipeline test

## Usage

Run integration tests with:
```bash
python -m pytest tests/integration/
```

Integration tests require the full system to be properly configured and may require network access.
