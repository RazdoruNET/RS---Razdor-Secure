#!/usr/bin/env python3
"""
Test script to verify Ollama timeout fix
"""

import sys
import json
import requests
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_ollama_connection():
    """Test Ollama connection with new timeout settings"""
    print("🔧 Testing Ollama timeout fix...")
    
    # Test basic connection
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

def test_ollama_analysis():
    """Test Ollama analysis with new timeout settings"""
    print("🧠 Testing Ollama analysis...")
    
    try:
        from ollama_rsecure import OllamaRSecure
        
        # Create instance
        rsecure = OllamaRSecure()
        
        # Test event
        test_event = {
            'type': 'network_intrusion',
            'source_ip': '192.168.1.100',
            'target_port': 22,
            'attack_pattern': 'brute_force',
            'attempts': 5,
            'timestamp': '2026-05-05T04:30:00'
        }
        
        # Test analysis
        result = rsecure.analyze_with_ollama(test_event, "security")
        
        if result:
            print("✅ Analysis completed successfully")
            print(f"📊 Result keys: {list(result.keys())}")
            if 'threat_level' in result:
                print(f"🚨 Threat level: {result['threat_level']}")
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
    print("🛡️  Testing Ollama RSecure Timeout Fix")
    print("=" * 50)
    
    # Test connection
    if test_ollama_connection():
        print("\n🔄 Testing analysis with new timeout settings...")
        if test_ollama_analysis():
            print("\n✅ All tests passed! Timeout fix is working.")
        else:
            print("\n❌ Analysis test failed.")
    else:
        print("\n❌ Cannot connect to Ollama. Please ensure Ollama is running.")
    
    print("=" * 50)
