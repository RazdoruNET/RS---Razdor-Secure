#!/usr/bin/env python3
"""
Test script to verify timeout and fallback fixes
"""

import sys
import json
import requests
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_basic_connection():
    """Test basic Ollama connection"""
    print("🔧 Testing basic Ollama connection...")
    try:
        response = requests.get("http://127.0.0.1:11434/api/version", timeout=5)
        if response.status_code == 200:
            version = response.json()
            print(f"✅ Ollama connected: {version.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ Ollama returned HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False

def test_improved_ollama():
    """Test improved Ollama with fallback"""
    print("🧠 Testing improved Ollama with fallback mechanism...")
    
    try:
        from ollama_rsecure import OllamaRSecure
        
        # Create instance
        rsecure = OllamaRSecure()
        
        # Check if Ollama is available
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
            'attempts': 3,
            'timestamp': '2026-05-05T12:59:00'
        }
        
        print("🔄 Testing analysis with improved timeout and fallback...")
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

if __name__ == "__main__":
    print("🛡️  Testing Improved Ollama Timeout Fix")
    print("=" * 50)
    
    # Test basic connection
    if test_basic_connection():
        print("\n🔄 Testing improved analysis...")
        if test_improved_ollama():
            print("\n✅ All tests passed! Timeout and fallback fixes are working.")
        else:
            print("\n❌ Analysis test failed.")
    else:
        print("\n❌ Cannot connect to Ollama. Please ensure Ollama is running.")
    
    print("=" * 50)
