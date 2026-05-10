#!/usr/bin/env python3
"""
Internet Targets - Список публичных endpoints для реального интернет тестирования
"""

# Публичные endpoints для реального интернет тестирования
# Запрещено: localhost, 127.0.0.1, mock servers

TARGETS = [
    # Basic HTTP endpoints
    ("example.com", 80),
    ("httpbin.org", 80),
    ("neverssl.com", 80),
    
    # HTTPS endpoints (для fallback тестов)
    ("example.org", 443),
    ("httpbingo.org", 443),
    
    # CDN endpoints
    ("cloudflare.com", 80),
    ("fastly.com", 80),
    
    # DNS testing endpoints
    ("dns.google", 53),
    ("8.8.8.8", 53),
    ("1.1.1.1", 53),
]

# Test paths для HTTP endpoints
TEST_PATHS = [
    "/get",
    "/ip",
    "/user-agent",
    "/headers",
    "/status/200",
    "/status/404",
]

# Fragmentation test scenarios
FRAGMENTATION_SCENARIOS = [
    {
        "name": "normal_request",
        "chunk_size": 1000,  # Без фрагментации
        "description": "Normal HTTP request without fragmentation"
    },
    {
        "name": "fragmented_request", 
        "chunk_size": 50,   # С фрагментацией
        "description": "Fragmented HTTP request with small chunks"
    },
    {
        "name": "minimal_fragmentation",
        "chunk_size": 10,   # Минимальная фрагментация
        "description": "Minimal chunk size for maximum fragmentation"
    }
]

def get_target_for_test(index: int = 0):
    """Получить target для теста"""
    if 0 <= index < len(TARGETS):
        return TARGETS[index]
    else:
        return TARGETS[0]

def get_path_for_test(index: int = 0):
    """Получить path для теста"""
    if 0 <= index < len(TEST_PATHS):
        return TEST_PATHS[index]
    else:
        return TEST_PATHS[0]

def get_scenario_for_test(index: int = 0):
    """Получить сценарий для теста"""
    if 0 <= index < len(FRAGMENTATION_SCENARIOS):
        return FRAGMENTATION_SCENARIOS[index]
    else:
        return FRAGMENTATION_SCENARIOS[0]

def validate_targets():
    """Валидировать targets"""
    print("🔍 Validating Internet Targets")
    
    valid_targets = []
    invalid_targets = []
    
    for host, port in TARGETS:
        # Проверяем что это не localhost
        if host in ["localhost", "127.0.0.1", "0.0.0.0"]:
            invalid_targets.append((host, port, "localhost_not_allowed"))
            continue
        
        # Проверяем что это не private IP
        if host.startswith(("192.168.", "10.", "172.16.", "169.254.")):
            invalid_targets.append((host, port, "private_ip_not_allowed"))
            continue
        
        valid_targets.append((host, port))
    
    print(f"📊 Target Validation Results:")
    print(f"  Total targets: {len(TARGETS)}")
    print(f"  Valid targets: {len(valid_targets)}")
    print(f"  Invalid targets: {len(invalid_targets)}")
    
    if invalid_targets:
        print(f"\n❌ Invalid Targets:")
        for host, port, reason in invalid_targets:
            print(f"  {host}:{port} - {reason}")
    
    if valid_targets:
        print(f"\n✅ Valid Targets:")
        for host, port in valid_targets:
            print(f"  {host}:{port}")
    
    return {
        "total_targets": len(TARGETS),
        "valid_targets": len(valid_targets),
        "invalid_targets": len(invalid_targets),
        "valid_target_list": valid_targets,
        "invalid_target_list": invalid_targets
    }

def main():
    """Основная функция"""
    print("🚀 Internet Targets Validation")
    print("Цель: Проверить список публичных endpoints")
    print("Запрещено: localhost, private IPs, mock servers")
    print("=" * 60)
    
    results = validate_targets()
    
    # Сохраняем результаты
    import json
    with open("INTERNET_TARGETS_VALIDATION.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: INTERNET_TARGETS_VALIDATION.json")
    
    return results["invalid_targets"] == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
