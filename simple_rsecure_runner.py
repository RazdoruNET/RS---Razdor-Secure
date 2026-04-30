#!/usr/bin/env python3
"""
Simple RSecure Runner
Minimal version to test basic functionality
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('rsecure.log')
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'numpy', 'pandas', 'scipy', 'sklearn', 
        'scapy', 'psutil', 'matplotlib', 'requests', 'flask'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Missing modules: {missing}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies OK!")
    return True

def check_ollama():
    """Check if Ollama is running"""
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            models = response.json().get('models', [])
            if models:
                print(f"📦 Available models: {[m['name'] for m in models]}")
            return True
        else:
            print("❌ Ollama server returned error")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running: brew services start ollama")
        return False

def create_basic_config():
    """Create basic configuration"""
    return {
        'system_detector': {
            'enabled': True,
            'scan_interval': 30
        },
        'neural_core': {
            'enabled': True,
            'model_path': './models'
        },
        'ollama': {
            'enabled': True,
            'server_url': 'http://localhost:11434',
            'models': ['qwen2.5-coder:1.5b']
        },
        'notifications': {
            'enabled': True,
            'level': 'INFO'
        },
        'logging': {
            'level': 'INFO',
            'file': 'rsecure.log',
            'console': True
        }
    }

def main():
    """Main runner function"""
    print("🛡️  RSecure Security System")
    print("=" * 40)
    
    logger = setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Ollama
    if not check_ollama():
        print("⚠️  Ollama not available - some features will be limited")
    
    try:
        # Import RSecure components
        print("\n📦 Loading RSecure components...")
        
        # Try to import main components
        try:
            from rsecure_main import RSecureMain
            print("✅ RSecureMain loaded")
            
            # Create and start RSecure
            config = create_basic_config()
            rsecure = RSecureMain(config)
            
            print("\n🚀 Starting RSecure...")
            rsecure.start()
            
            print("✅ RSecure is running!")
            print("Press Ctrl+C to stop\n")
            
            # Keep running
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
                    
        except ImportError as e:
            print(f"❌ Cannot import RSecureMain: {e}")
            print("Running in basic mode...")
            
            # Basic mode - just show system info
            import psutil
            import platform
            
            print(f"\n📊 System Information:")
            print(f"Platform: {platform.system()} {platform.release()}")
            print(f"CPU: {psutil.cpu_percent()}%")
            print(f"Memory: {psutil.virtual_memory().percent}%")
            print(f"Disk: {psutil.disk_usage('/').percent}%")
            
            print("\n⏳ Monitoring system... (Press Ctrl+C to stop)")
            while True:
                try:
                    time.sleep(5)
                    cpu = psutil.cpu_percent()
                    mem = psutil.virtual_memory().percent
                    print(f"\rCPU: {cpu:5.1f}% | Memory: {mem:5.1f}%", end="", flush=True)
                except KeyboardInterrupt:
                    break
                    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping RSecure...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("✅ Done")

if __name__ == "__main__":
    main()
