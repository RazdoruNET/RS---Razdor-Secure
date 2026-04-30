#!/usr/bin/env python3
"""
Simple RSecure Test
Tests basic functionality without heavy dependencies
"""

import os
import sys
import json
import time
from pathlib import Path

def test_project_structure():
    """Test that project structure is organized correctly"""
    print("🌑 Testing RSecure Project Structure...")
    
    # Check main directories
    required_dirs = [
        'rsecure',
        'rsecure/core',
        'rsecure/modules',
        'rsecure/modules/detection',
        'rsecure/modules/defense',
        'rsecure/modules/protection',
        'rsecure/modules/monitoring',
        'rsecure/modules/notification',
        'rsecure/modules/analysis',
        'rsecure/utils',
        'rsecure/config',
        'rsecure/tests',
        'assets',
        'data',
        'logs'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path}")
    
    # Check key files
    required_files = [
        'rsecure/__init__.py',
        'rsecure/rsecure_main.py',
        'rsecure/config/rsecure_config.json',
        'rsecure/config/offline_threats.json',
        'assets/we_razdor_logo.png',
        'README.md',
        'requirements.txt'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")

def test_offline_knowledge_base():
    """Test offline knowledge base loading"""
    print("\n🧠 Testing Offline Knowledge Base...")
    
    try:
        offline_file = Path('rsecure/config/offline_threats.json')
        if offline_file.exists():
            with open(offline_file, 'r', encoding='utf-8') as f:
                threats = []
                for line in f:
                    line = line.strip()
                    if line:
                        threat = json.loads(line)
                        threats.append(threat)
                
                print(f"✅ Loaded {len(threats)} offline threats")
                
                # Show sample threat
                if threats:
                    sample = threats[0]
                    print(f"📋 Sample: {sample.get('id')} - Score: {sample.get('final_risk', 0)}")
                
                return True
        else:
            print("❌ Offline knowledge base file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading offline knowledge base: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n⚙️ Testing Configuration Loading...")
    
    try:
        config_file = Path('rsecure/config/rsecure_config.json')
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"✅ Configuration loaded with {len(config)} sections")
                return True
        else:
            print("❌ Configuration file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def test_basic_imports():
    """Test basic imports without heavy dependencies"""
    print("\n📦 Testing Basic Imports...")
    
    try:
        # Test basic Python imports
        import json
        import os
        import time
        import threading
        from pathlib import Path
        print("✅ Basic Python modules")
        
        # Test if we can import our modules (without heavy dependencies)
        sys.path.insert(0, './rsecure')
        
        # Try to import modules that don't require TensorFlow/Flask
        try:
            from modules.detection.system_detector import SystemDetector
            print("✅ SystemDetector imported")
        except ImportError as e:
            print(f"⚠️ SystemDetector import issue: {e}")
        
        try:
            from modules.detection.cvu_intelligence import RSecureCVU
            print("✅ CVU Intelligence imported")
        except ImportError as e:
            print(f"⚠️ CVU Intelligence import issue: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main test function"""
    print("🌑 RSecure System Test")
    print("=" * 50)
    
    # Run all tests
    tests = [
        test_project_structure,
        test_offline_knowledge_base,
        test_config_loading,
        test_basic_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RSecure system is ready.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
    
    print("\n🚀 To run full system:")
    print("   pip install -r requirements.txt")
    print("   python3 rsecure/rsecure_main.py")
    print("\n🎨 To run dashboard:")
    print("   pip install flask psutil")
    print("   python3 simple_dashboard.py")

if __name__ == "__main__":
    main()
