#!/usr/bin/env python3
"""
Test script for stabilized SOCKS5 proxy in passthrough mode
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

from socks5_daemon_rfc1928 import SOCKS5Daemon

async def test_proxy_stability():
    """Test basic SOCKS5 proxy functionality"""
    print("🔧 Testing SOCKS5 proxy stability...")
    
    # Create daemon with minimal configuration
    daemon = SOCKS5Daemon(listen_port=1081)
    
    # Start the server
    server = await daemon.start_server()
    print("✅ SOCKS5 proxy started on port 1081")
    
    # Wait a moment for server to be ready
    await asyncio.sleep(1)
    
    # Test cases
    test_cases = [
        {
            "name": "HTTP GET to example.com",
            "command": [
                "curl", "--socks5", "localhost:1081", 
                "--max-time", "10", "--verbose",
                "http://example.com"
            ]
        },
        {
            "name": "HTTPS GET to example.com", 
            "command": [
                "curl", "--socks5", "localhost:1081",
                "--max-time", "10", "--verbose",
                "https://example.com"
            ]
        },
        {
            "name": "HTTPS GET to google.com",
            "command": [
                "curl", "--socks5", "localhost:1081",
                "--max-time", "10", "--verbose",
                "https://www.google.com"
            ]
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        try:
            start_time = time.time()
            result = subprocess.run(
                test_case['command'],
                capture_output=True,
                text=True,
                timeout=15
            )
            end_time = time.time()
            
            if result.returncode == 0:
                print(f"✅ SUCCESS ({end_time - start_time:.2f}s)")
                print(f"   Response length: {len(result.stdout)} chars")
                results.append(True)
            else:
                print(f"❌ FAILED ({end_time - start_time:.2f}s)")
                print(f"   Return code: {result.returncode}")
                print(f"   Error: {result.stderr[:200]}...")
                results.append(False)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT (15s)")
            results.append(False)
        except Exception as e:
            print(f"💥 ERROR: {e}")
            results.append(False)
    
    # Cleanup
    server.close()
    await server.wait_closed()
    print("\n🧹 SOCKS5 proxy stopped")
    
    # Summary
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Test Summary:")
    print(f"   Passed: {sum(results)}/{len(results)}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Proxy stability test PASSED")
        return True
    else:
        print("🚨 Proxy stability test FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_proxy_stability())
    sys.exit(0 if success else 1)
