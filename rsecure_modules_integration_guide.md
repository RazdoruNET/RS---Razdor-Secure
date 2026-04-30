# RSecure Модули Обхода DPI и Сетевой Безопасности

## Обзор

Я добавил comprehensive набор модулей для обхода DPI блокировок и обеспечения сетевой безопасности в ваш RSecure проект. Все модули включены в `rsecure/modules/defense/` и полностью протестированы.

## Созданные Модули

### 1. DPI Bypass (`dpi_bypass.py`)
**Функциональность:**
- **Фрагментация пакетов** - разделение данных на мелкие фрагменты
- **TLS SNI Splitting** - разделение TLS handshake для обхода SNI инспекции
- **Обфускация HTTP заголовков** - рандомизация и изменение заголовков
- **Domain Fronting** - использование CDN для маскировки трафика
- **Цепочка прокси** - маршрутизация через несколько прокси
- **Tor маршрутизация** - использование SOCKS5 для Tor
- **VPN туннелирование** - интеграция с VPN интерфейсами
- **Мимикрия протоколов** - имитация SSH, FTP, SMTP трафика
- **Кодирование payload** - Base64, URL, hex, zlib кодирование
- **Stealth порты** - использование нестандартных портов

**Использование:**
```python
from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod

engine = DPIBypassEngine()
config = BypassConfig(
    method=BypassMethod.FRAGMENTATION,
    target_host="example.com",
    target_port=80,
    fragment_size=256,
    delay_ms=50
)

success = engine.bypass_dpi(config)
```

### 2. VPN и Прокси (`vpn_proxy.py`)
**Функциональность:**
- **Прокси серверы** - HTTP, HTTPS, SOCKS4, SOCKS5, Shadowsocks
- **VPN менеджер** - OpenVPN, WireGuard, IKEv2, SSTP
- **Цепочки прокси** - многократная прокси маршрутизация
- **Плагируемые транспорты** - Obfs4, Meek, Snowflake
- **Автоматический выбор маршрута** - оптимальный путь обхода

**Использование:**
```python
from rsecure.modules.defense.vpn_proxy import NetworkBypassManager, ProxyConfig, ProxyType

manager = NetworkBypassManager()

# Запуск прокси сервера
proxy_config = ProxyConfig(proxy_type=ProxyType.HTTP, host="0.0.0.0", port=8080)
proxy_id = manager.start_proxy_server(proxy_config)

# Подключение VPN
from rsecure.modules.defense.vpn_proxy import VPNConfig, VPNType
vpn_config = VPNConfig(vpn_type=VPNType.OPENVPN, server_host="vpn.example.com", server_port=1194)
vpn_id = manager.connect_vpn(vpn_config)
```

### 3. Обфускация Трафика (`traffic_obfuscation.py`)
**Функциональность:**
- **Шифрование** - AES, ChaCha20, XOR
- **Кодирование** - Base64, ZLIB сжатие
- **Мимикрия протоколов** - HTTP, HTTPS, SSH, FTP, SMTP, DNS, ICMP, Tor
- **Стеганография** - скрытие данных в изображениях/аудио
- **Паддинг пакетов** - добавление случайных данных
- **Временная обфускация** - изменение таймингов
- **Многослойная обфускация** - комбинирование методов
- **Адаптивная обфускация** - выбор метода на основе условий сети

**Использование:**
```python
from rsecure.modules.defense.traffic_obfuscation import TrafficObfuscator, ObfuscationConfig, ObfuscationMethod

obfuscator = TrafficObfuscator()
config = ObfuscationConfig(
    method=ObfuscationMethod.AES,
    encryption_key=b"your_secret_key_32_bytes_long"
)

# Обфускация данных
obfuscated = obfuscator.obfuscate_data(b"secret data", config)
deobfuscated = obfuscator.deobfuscate_data(obfuscated, config)
```

### 4. Tor Интеграция (`tor_integration.py`)
**Функциональность:**
- **Tor контроллер** - управление Tor сетью
- **Создание circuits** - кастомные пути через Tor
- **Bridge менеджер** - работа с мостами Tor
- **Плагируемые транспорты** - Obfs4, Meek, Snowflake
- **Hidden сервисы** - создание .onion сервисов
- **Tor клиент** - анонимные запросы через Tor
- **Автоматический обход** - интеллектуальная маршрутизация

**Использование:**
```python
from rsecure.modules.defense.tor_integration import TorIntegrationManager, TorCircuitConfig, TorCircuitType

tor_manager = TorIntegrationManager()

# Запуск Tor
if tor_manager.start_tor():
    # Создание circuit
    circuit_config = TorCircuitConfig(
        circuit_type=TorCircuitType.STANDARD,
        exit_country="us"
    )
    circuit_id = tor_manager.controller.create_circuit(circuit_config)
    
    # Анонимный запрос
    status, response = tor_manager.client.http_request(
        "GET", "http://example.com", circuit_id=circuit_id
    )
```

## Тестирование

Все модули имеют comprehensive тесты в `tests/`:

- `test_dpi_bypass.py` - тесты DPI обхода
- `test_vpn_proxy.py` - тесты VPN и прокси
- `test_traffic_obfuscation.py` - тесты обфускации
- `test_tor_integration.py` - тесты Tor интеграции

**Запуск тестов:**
```bash
python -m pytest tests/test_dpi_bypass.py -v
python -m pytest tests/test_vpn_proxy.py -v
python -m pytest tests/test_traffic_obfuscation.py -v
python -m pytest tests/test_tor_integration.py -v
```

## Комплексное Использование

### Менеджер Обхода
```python
from rsecure.modules.defense.dpi_bypass import BypassManager
from rsecure.modules.defense.traffic_obfuscation import ObfuscationManager
from rsecure.modules.defense.tor_integration import TorIntegrationManager

# Инициализация всех менеджеров
bypass_manager = BypassManager()
obfuscation_manager = ObfuscationManager()
tor_manager = TorIntegrationManager()

# Комплексный обход
tor_manager.start_tor()
config = BypassConfig(method=BypassMethod.TOR_ROUTING, target_host="example.com", target_port=80)
bypass_id = bypass_manager.start_bypass(config)
```

### Адаптивная Обфускация
```python
from rsecure.modules.defense.traffic_obfuscation import AdvancedObfuscation, ObfuscationMethod

advanced = AdvancedObfuscation()

# Многослойная обфускация
data = b"sensitive information"
obfuscated = advanced.create_layered_obfuscation(
    data, 
    [ObfuscationMethod.ZLIB, ObfuscationMethod.BASE64, ObfuscationMethod.AES]
)

# Адаптивная обфускация
network_conditions = {"high_inspection": True}
adaptive_obfuscated = advanced.adaptive_obfuscation(data, network_conditions)
```

## Зависимости

Для полной функциональности установите зависимости:

```bash
pip install cryptography stem pysocks requests
```

## Безопасность и Законность

⚠️ **Важно:** Используйте эти модули ответственно и в соответствии с законодательством вашей страны. Модули предназначены для:
- Исследовательских целей
- Тестирования безопасности
- Обхода легитимных ограничений
- Защиты приватности

## Интеграция с RSecure

Все модули интегрированы с основной архитектурой RSecure:

```python
from rsecure.rsecure_main import RSecureCore
from rsecure.modules.defense.dpi_bypass import DPIBypassEngine

core = RSecureCore()
core.register_module("dpi_bypass", DPIBypassEngine())
```

Модули доступны через основной интерфейс RSecure и могут использоваться совместно с нейронными механизмами безопасности для enhanced защиты.
