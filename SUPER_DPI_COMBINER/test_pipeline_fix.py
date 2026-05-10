#!/usr/bin/env python3
"""
Test script to verify that pipelines can be created and executed without exceptions
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from core.base_pipeline import SafePipeline, BypassRequest
from pipelines.domain_fronting.host_header import HostHeaderPipeline
from pipelines.spoof_dpi.tls_fingerprint import TLSFingerprintPipeline

async def test_pipeline_creation():
    """Test that pipelines can be created without exceptions"""
    print("🧪 Testing Pipeline Creation...")
    
    try:
        # Test SafePipeline
        safe_pipeline = SafePipeline("TestSafe")
        print(f"✅ SafePipeline created: {safe_pipeline}")
        
        # Test HostHeaderPipeline
        host_pipeline = HostHeaderPipeline()
        print(f"✅ HostHeaderPipeline created: {host_pipeline}")
        
        # Test TLSFingerprintPipeline
        tls_pipeline = TLSFingerprintPipeline()
        print(f"✅ TLSFingerprintPipeline created: {tls_pipeline}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline creation failed: {e}")
        return False

async def test_pipeline_initialization():
    """Test that pipelines can be initialized without exceptions"""
    print("\n🔧 Testing Pipeline Initialization...")
    
    try:
        # Test SafePipeline
        safe_pipeline = SafePipeline("TestSafe")
        result = safe_pipeline.initialize({})
        print(f"✅ SafePipeline initialized: {result}")
        
        # Test HostHeaderPipeline
        host_pipeline = HostHeaderPipeline()
        result = host_pipeline.initialize({'host_overrides': ['example.com']})
        print(f"✅ HostHeaderPipeline initialized: {result}")
        
        # Test TLSFingerprintPipeline
        tls_pipeline = TLSFingerprintPipeline()
        result = tls_pipeline.initialize({'tls_version': '1.2'})
        print(f"✅ TLSFingerprintPipeline initialized: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return False

async def test_pipeline_execution():
    """Test that pipelines can be executed without exceptions"""
    print("\n🚀 Testing Pipeline Execution...")
    
    try:
        # Create test request
        test_request = BypassRequest(
            host="example.com",
            port=443,
            method="GET",
            timeout=5.0
        )
        
        # Test SafePipeline
        safe_pipeline = SafePipeline("TestSafe")
        safe_pipeline.initialize({})
        response = await safe_pipeline.execute(test_request)
        print(f"✅ SafePipeline executed: success={response.success}, latency={response.latency:.4f}s")
        
        # Test HostHeaderPipeline
        host_pipeline = HostHeaderPipeline()
        host_pipeline.initialize({'host_overrides': ['example.com']})
        response = await host_pipeline.execute(test_request)
        print(f"✅ HostHeaderPipeline executed: success={response.success}, latency={response.latency:.4f}s")
        
        # Test TLSFingerprintPipeline
        tls_pipeline = TLSFingerprintPipeline()
        tls_pipeline.initialize({'tls_version': '1.2'})
        response = await tls_pipeline.execute(test_request)
        print(f"✅ TLSFingerprintPipeline executed: success={response.success}, latency={response.latency:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🎯 Testing Pipeline Fix - ТЗ-2 MAKE BASEPIPELINE EXECUTABLE")
    print("=" * 60)
    
    # Run all tests
    creation_ok = await test_pipeline_creation()
    init_ok = await test_pipeline_initialization()
    execution_ok = await test_pipeline_execution()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   Creation:    {'✅ PASS' if creation_ok else '❌ FAIL'}")
    print(f"   Initialization: {'✅ PASS' if init_ok else '❌ FAIL'}")
    print(f"   Execution:   {'✅ PASS' if execution_ok else '❌ FAIL'}")
    
    if creation_ok and init_ok and execution_ok:
        print("\n🎉 ALL TESTS PASSED! BasePipeline is now executable.")
        print("✅ Критерий приёмки выполнен: хотя бы 1 pipeline можно создать и выполнить без exception")
    else:
        print("\n💥 SOME TESTS FAILED! BasePipeline still has issues.")
    
    return creation_ok and init_ok and execution_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
