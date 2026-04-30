#!/usr/bin/env python3
"""
Test script for WiFi anti-positioning system
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure'))

try:
    from rsecure.modules.defense.wifi_antipositioning import WiFiAntiPositioningSystem
    from rsecure.rsecure_main import RSecureMain
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure the rsecure module is properly installed")
    sys.exit(1)

def setup_logging():
    """Setup logging for test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_wifi_antipositioning_standalone():
    """Test WiFi anti-positioning system standalone"""
    print("=== Testing WiFi Anti-Positioning System (Standalone) ===")
    
    try:
        # Create system with test configuration
        config = {
            'csi_monitoring': {
                'interface': 'wlan0',
                'sampling_rate': 10,  # Lower for testing
                'buffer_size': 100,
                'analysis_window': 20
            },
            'signal_obfuscation': {
                'enabled': True,
                'phase_randomization': True,
                'amplitude_modulation': True,
                'obfuscation_strength': 0.5
            },
            'multipath_noise': {
                'enabled': True,
                'noise_level_db': -30,
                'synthetic_reflections': 3
            },
            'pattern_disruption': {
                'enabled': True,
                'disruption_interval_ms': 500,
                'randomization_depth': 'moderate'
            },
            'detection': {
                'threat_threshold': 0.5,  # Lower for testing
                'confidence_threshold': 0.6
            }
        }
        
        system = WiFiAntiPositioningSystem(config)
        
        # Start protection
        system.start_protection()
        print("✓ WiFi anti-positioning protection started")
        
        # Monitor for a few seconds
        print("Monitoring for 10 seconds...")
        time.sleep(10)
        
        # Get status
        status = system.get_protection_status()
        print(f"✓ Protection status: {status}")
        
        # Get threat report
        threat_report = system.get_threat_report()
        print(f"✓ Threat report: {threat_report}")
        
        # Stop protection
        system.stop_protection()
        print("✓ WiFi anti-positioning protection stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in standalone test: {e}")
        return False

def test_rsecure_integration():
    """Test WiFi anti-positioning integration with RSecure"""
    print("\n=== Testing WiFi Anti-Positioning Integration ===")
    
    try:
        # Create RSecure configuration
        config = {
            'wifi_antipositioning': {
                'enabled': True,
                'interface': 'wlan0',
                'sampling_rate': 10,  # Lower for testing
                'threat_threshold': 0.5,
                'confidence_threshold': 0.6,
                'auto_activate': True,
                'protection_level': 'medium',
                'signal_obfuscation': True,
                'multipath_noise': True,
                'pattern_disruption': True
            },
            'system_detection': {'enabled': False},
            'monitoring': {'enabled': False},
            'neural_core': {'enabled': False},
            'analytics': {'enabled': False},
            'system_control': {'enabled': False},
            'cvu_intelligence': {'enabled': False},
            'reinforcement_learning': {'enabled': False},
            'network_defense': {'enabled': False},
            'phishing_detection': {'enabled': False},
            'llm_defense': {'enabled': False},
            'audio_video_monitoring': {'enabled': False},
            'psychological_protection': {'enabled': False},
            'integration': {'enable_ml_decisions': False, 'enable_auto_response': False}
        }
        
        # Create temporary config file
        import json
        config_path = './test_rsecure_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create RSecure main system
        rsecure = RSecureMain(config_path)
        
        # Start system
        rsecure.start()
        print("✓ RSecure system started with WiFi anti-positioning")
        
        # Monitor for a few seconds
        print("Monitoring for 10 seconds...")
        time.sleep(10)
        
        # Check if WiFi anti-positioning is active
        if hasattr(rsecure, 'wifi_antipositioning') and rsecure.wifi_antipositioning:
            wifi_status = rsecure.wifi_antipositioning.get_protection_status()
            print(f"✓ WiFi anti-positioning status: {wifi_status}")
        else:
            print("✗ WiFi anti-positioning not initialized")
            return False
        
        # Stop system
        rsecure.stop()
        print("✓ RSecure system stopped")
        
        # Clean up config file
        os.remove(config_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Error in integration test: {e}")
        return False

def test_ollama_integration():
    """Test WiFi anti-positioning with Ollama integration"""
    print("\n=== Testing WiFi Anti-Positioning with Ollama ===")
    
    try:
        from rsecure.core.ollama_integration import OllamaSecurityAnalyzer
        
        # Create Ollama analyzer
        analyzer = OllamaSecurityAnalyzer()
        
        # Test WiFi positioning threat event
        wifi_threat_event = {
            "timestamp": "2024-01-01T12:00:00Z",
            "event_type": "wifi_positioning_attack",
            "attack_vector": "wifi_reflection_positioning",
            "source_interface": "wlan0",
            "csi_patterns": "anomalous_multipath",
            "positioning_accuracy": "high",
            "attack_indicators": ["csi_probing", "coordinated_scanning"],
            "threat_level": "high",
            "confidence": 0.85
        }
        
        # Analyze with Ollama
        result = analyzer.analyze_security_event(wifi_threat_event)
        print(f"✓ Ollama analysis result: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in Ollama integration test: {e}")
        return False

def main():
    """Main test function"""
    print("WiFi Anti-Positioning System Test Suite")
    print("=" * 50)
    
    setup_logging()
    
    tests = [
        ("Standalone System", test_wifi_antipositioning_standalone),
        ("RSecure Integration", test_rsecure_integration),
        ("Ollama Integration", test_ollama_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"{test_name}: FAIL - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! WiFi anti-positioning system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()
