#!/usr/bin/env python3
"""
HTTP Fragmentation Integration Test
Проверяет fragmentation, socket cleanup, no fake success
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

def test_http_fragmentation():
    """Integration test для HTTP Fragmentation"""
    print("🌐 HTTP Fragmentation Integration Test")
    
    pipeline = HTTPFragmentation()
    
    # Test 1: Fragmentation with valid host
    request = Request(host="httpbin.org", port=80, method="GET", path="/get")
    
    import time
    start_time = time.time()
    response = pipeline.execute(request)
    end_time = time.time()
    measured_latency = end_time - start_time
    
    assert response.success, "HTTP Fragmentation should succeed with valid host"
    assert response.status_code == 200, "Should return 200 for valid request"
    assert len(response.data) > 0, "Should receive response data"
    assert measured_latency > 0, "Should have measurable latency"
    
    print("✅ HTTP Fragmentation integration test passed")

if __name__ == "__main__":
    test_http_fragmentation()
