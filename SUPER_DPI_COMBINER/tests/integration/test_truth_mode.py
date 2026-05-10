#!/usr/bin/env python3
"""
Truth Mode Integration Test
Проверяет DNS fail, timeout, refused connection
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

def test_truth_mode():
    """Integration test для Truth Mode"""
    print("🔍 Truth Mode Integration Test")
    
    pipeline = HTTPFragmentation()
    
    # Test 1: DNS failure
    request = Request(host="nonexistent-domain.invalid", port=80, method="GET")
    response = pipeline.execute(request)
    
    assert not response.success, "DNS failure should return success=False"
    assert response.error is not None, "DNS failure should have error message"
    assert response.status_code == 0, "DNS failure should return status_code=0"
    
    # Test 2: Connection refused
    request = Request(host="127.0.0.1", port=9999, method="GET")
    response = pipeline.execute(request)
    
    assert not response.success, "Connection refused should return success=False"
    assert response.error is not None, "Connection refused should have error message"
    assert response.status_code == 0, "Connection refused should return status_code=0"
    
    # Test 3: Timeout
    request = Request(host="httpbin.org", port=80, method="GET", timeout=0.001)
    response = pipeline.execute(request)
    
    assert not response.success, "Timeout should return success=False"
    assert response.error is not None, "Timeout should have error message"
    assert response.status_code == 0, "Timeout should return status_code=0"
    
    print("✅ Truth Mode integration test passed")

if __name__ == "__main__":
    test_truth_mode()
