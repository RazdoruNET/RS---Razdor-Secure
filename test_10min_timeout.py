#!/usr/bin/env python3
"""
Test script to verify 10-minute timeout settings
"""

import sys
import json
import requests
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_timeout_settings():
    """Test the new 10-minute timeout settings"""
    print("🕐 Testing 10-minute timeout settings...")
    
    try:
        from ollama_rsecure import OllamaRSecure
        
        # Create instance
        rsecure = OllamaRSecure()
        
        # Check Ollama connection
        if not rsecure.check_ollama_status():
            print("❌ Ollama not available")
            return False
            
        print(f"📦 Available models: {len(rsecure.available_models)}")
        print(f"🔄 Fallback models: {rsecure.fallback_models}")
        
        # Test event
        test_event = {
            'type': 'network_intrusion',
            'source_ip': '192.168.1.100',
            'target_port': 22,
            'attack_pattern': 'brute_force',
            'attempts': 5,
            'timestamp': '2026-05-05T13:07:00'
        }
        
        print("🔄 Testing analysis with 10-minute timeout...")
        print("⏱️  Note: This test may take up to 10 minutes if Ollama is slow...")
        
        result = rsecure.analyze_with_ollama(test_event, "security")
        
        if result:
            print("✅ Analysis completed successfully")
            print(f"📊 Result keys: {list(result.keys())}")
            if 'threat_level' in result:
                print(f"🚨 Threat level: {result['threat_level']}")
            if 'analysis' in result:
                print(f"📝 Analysis: {result['analysis'][:100]}...")
            return True
        else:
            print("❌ Analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_timeout_config():
    """Check timeout configuration in the code"""
    print("🔧 Checking timeout configuration...")
    
    try:
        with open('scripts/ollama_rsecure.py', 'r') as f:
            content = f.read()
            
        if 'timeout=600' in content:
            print("✅ Timeout set to 600 seconds (10 minutes)")
        else:
            print("❌ Timeout not set to 600 seconds")
            
        if 'max_retries = 1' in content:
            print("✅ Max retries set to 1")
        else:
            print("❌ Max retries not set to 1")
            
        if 'retry_delay = 30' in content:
            print("✅ Retry delay set to 30 seconds")
        else:
            print("❌ Retry delay not set to 30 seconds")
            
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")

if __name__ == "__main__":
    print("🛡️  Testing 10-Minute Timeout Settings")
    print("=" * 50)
    
    # Check configuration
    check_timeout_config()
    
    print("\n" + "=" * 50)
    
    # Test with actual Ollama
    test_timeout_settings()
    
    print("=" * 50)
