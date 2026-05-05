# Unit Tests

This directory contains unit tests for individual components of the RS Razdor Secure system.

## Test Categories

### Core Component Tests
- `test_neural_encryptor.py` - Neural encryption module tests
- `test_rsecure.py` - Core RSecure functionality tests
- `test_runner.py` - Test runner utilities
- `test_wifi_antipositioning.py` - WiFi anti-positioning tests

## Usage

Run unit tests with:
```bash
python -m pytest tests/unit/
```

Unit tests focus on individual components and can be run independently without requiring the full system setup.
