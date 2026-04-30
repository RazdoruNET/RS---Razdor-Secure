# 📚 Examples Directory

This directory contains example scripts and demonstrations of RSecure functionality.

## 🔓 DPI Bypass Examples

### Basic Bypass Techniques
```python
# examples/dpi_bypass_basic.py
from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod

engine = DPIBypassEngine()
config = BypassConfig(
    method=BypassMethod.FRAGMENTATION,
    target_host="example.com",
    target_port=80
)

success = engine.bypass_dpi(config)
print(f"Bypass successful: {success}")
```

### Advanced Bypass with Obfuscation
```python
# examples/dpi_bypass_advanced.py
from rsecure.modules.defense.traffic_obfuscation import AdvancedObfuscation, ObfuscationMethod

obfuscator = AdvancedObfuscation()
data = b"sensitive_data"

# Multi-layer obfuscation
obfuscated = obfuscator.create_layered_obfuscation(
    data,
    [ObfuscationMethod.ZLIB, ObfuscationMethod.BASE64, ObfuscationMethod.AES]
)
```

## 🛡️ VPN/Proxy Examples

### VPN Connection Setup
```python
# examples/vpn_setup.py
from rsecure.modules.defense.vpn_proxy import VPNManager, VPNConfig, VPNType

vpn_manager = VPNManager()
config = VPNConfig(
    vpn_type=VPNType.OPENVPN,
    server_host="vpn.example.com",
    server_port=1194
)

connection_id = vpn_manager.connect_vpn(config)
```

### Proxy Chain Configuration
```python
# examples/proxy_chain.py
from rsecure.modules.defense.vpn_proxy import ProxyChain

chain = ProxyChain()
# Add multiple proxies for chained routing
chain.create_chain([proxy1, proxy2, proxy3])
```

## 🌐 Tor Integration Examples

### Hidden Service Creation
```python
# examples/tor_hidden_service.py
from rsecure.modules.defense.tor_integration import TorIntegrationManager

tor_manager = TorIntegrationManager()
onion_address = tor_manager.create_hidden_service(
    "my_service", 
    local_port=8080
)
print(f"Hidden service: {onion_address}")
```

### Anonymous Requests
```python
# examples/tor_anonymous.py
status_code, response = tor_manager.client.http_request(
    "GET", "http://httpbin.org/ip"
)
```

## 🔐 Traffic Obfuscation Examples

### Protocol Mimicry
```python
# examples/protocol_mimicry.py
from rsecure.modules.defense.traffic_obfuscation import TrafficObfuscator, ProtocolType

obfuscator = TrafficObfuscator()
# Mimic HTTP traffic
http_mimicked = obfuscator.mimic_protocol(data, ProtocolType.HTTP)
```

### Steganography
```python
# examples/steganography.py
# Hide data in images
hidden_data = obfuscator.hide_in_image(data, image_path)
# Extract hidden data
extracted_data = obfuscator.extract_from_image(hidden_image)
```

## 🧠 Neural Security Examples

### Threat Analysis
```python
# examples/neural_analysis.py
from rsecure.core.neural_security_core import NeuralSecurityCore

neural_core = NeuralSecurityCore()
threat_level = neural_core.analyze_threat(network_data)
```

### LLM Integration
```python
# examples/llm_integration.py
from rsecure.core.ollama_integration import OllamaSecurityAnalyzer

analyzer = OllamaSecurityAnalyzer()
analysis = analyzer.analyze_security_event(event_data)
```

## 📊 Monitoring Examples

### Real-time Monitoring
```python
# examples/realtime_monitoring.py
from rsecure.utils.monitoring_logger import SystemMonitor

monitor = SystemMonitor()
monitor.start_realtime_monitoring()
```

### Security Events
```python
# examples/security_events.py
# Handle security events
def handle_security_event(event):
    if event.severity > 0.8:
        send_alert(event)
```

## 🚀 Getting Started

### Running Examples

1. **Basic Examples:**
```bash
python examples/dpi_bypass_basic.py
python examples/vpn_setup.py
```

2. **Advanced Examples:**
```bash
python examples/dpi_bypass_advanced.py
python examples/tor_hidden_service.py
```

3. **Neural Examples:**
```bash
python examples/neural_analysis.py
python examples/llm_integration.py
```

### Prerequisites

- RSecure properly installed
- Virtual environment activated
- Required dependencies installed
- Configuration files set up

### Configuration

Most examples require configuration in `rsecure_config.json`:

```json
{
  "dpi_bypass": {"enabled": true},
  "vpn_proxy": {"enabled": true},
  "tor_integration": {"enabled": true},
  "neural_core": {"enabled": true}
}
```

## 📝 Notes

- Examples are for demonstration purposes
- Modify configurations for your specific use case
- Some examples may require additional setup
- Check individual example files for detailed comments

## 🔧 Customization

You can customize examples by:
- Modifying target hosts and ports
- Changing bypass methods
- Adjusting neural model parameters
- Adding custom logging and monitoring

## 📚 Learn More

- [User Guide](../USER_GUIDE.md) - Complete user documentation
- [API Documentation](../docs/api/) - API reference
- [Architecture](../docs/architecture/) - System architecture
- [Defense Modules](../docs/defense/) - Security modules documentation
