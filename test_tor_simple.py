#!/usr/bin/env python3
"""
Simple Tor bypass test
"""
import sys
import os
sys.path.append('.')
sys.path.append('./rsecure')

try:
    from rsecure.modules.defense.dpi_bypass import DPIBypassEngine, BypassConfig, BypassMethod
    print("✅ Import successful")
    
    # Create engine
    engine = DPIBypassEngine()
    print("✅ Engine created")
    
    # Test Tor wrapper
    config = BypassConfig(
        method=BypassMethod.PROTOCOL_MIMICKING,
        target_host="www.youtube.com",
        target_port=443
    )
    
    print("🌐 Testing Tor wrapper bypass...")
    result = engine._tor_wrapper_bypass(config)
    print(f"Result: {result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
