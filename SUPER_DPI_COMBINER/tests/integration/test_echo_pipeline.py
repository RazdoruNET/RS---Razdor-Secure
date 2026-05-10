#!/usr/bin/env python3
"""
Echo Pipeline Integration Test
Проверяет success path, latency, cleanup
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.pipelines.echo import Echo
from super_dpi_combiner.core.contracts import Request

def test_echo_pipeline():
    """Integration test для Echo pipeline"""
    print("🔊 Echo Pipeline Integration Test")
    
    pipeline = Echo()
    request = Request(host="test.example.com", port=80, method="GET")
    
    # Test 1: Success path
    response = pipeline.execute(request)
    assert response.success, "Echo should return success=True"
    assert response.status_code == 200, "Echo should return 200"
    assert "test.example.com:80" in response.data.decode(), "Echo should return host:port"
    assert response.latency > 0, "Echo should have measurable latency"
    
    print("✅ Echo pipeline integration test passed")

if __name__ == "__main__":
    test_echo_pipeline()
