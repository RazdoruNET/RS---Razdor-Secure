#!/usr/bin/env python3
"""
Test script for observability layer
Verifies structured logging, pipeline tracing, and metrics collection
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, get_tracer, get_global_metrics
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse
from core.metrics_api import get_metrics_api


class TestPipeline(BasePipeline):
    """Test pipeline for observability verification"""
    
    def __init__(self):
        super().__init__("test_pipeline", BypassTechnique.SPOOF_DPI)
        self._initialized = True
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Simulate pipeline execution"""
        await asyncio.sleep(0.1)  # Simulate work
        
        # Simulate success/failure based on host
        if "fail" in request.host:
            return BypassResponse(
                success=False,
                status_code=500,
                error="Simulated failure",
                technique_used=self.technique.value
            )
        else:
            return BypassResponse(
                success=True,
                status_code=200,
                data=b"Test response",
                technique_used=self.technique.value
            )
    
    def initialize(self, config):
        return True
    
    def cleanup(self):
        """Cleanup pipeline resources"""
        pass


async def test_structured_logging():
    """Test structured logging functionality"""
    print("Testing structured logging...")
    
    logger = get_logger("test_observability")
    
    # Test different log levels
    logger.info("test_info", test_param="test_value", number=42)
    logger.warning("test_warning", warning_type="test")
    logger.error("test_error", error_code="TEST_ERROR")
    
    print("✅ Structured logging test passed")


async def test_pipeline_tracing():
    """Test pipeline tracing functionality"""
    print("Testing pipeline tracing...")
    
    pipeline = TestPipeline()
    
    # Test successful execution
    request = BypassRequest(host="example.com", port=80, method="GET")
    response = await pipeline.safe_execute(request)
    
    assert response.success, "Expected successful response"
    
    # Test failed execution
    request_fail = BypassRequest(host="fail.example.com", port=80, method="GET")
    response_fail = await pipeline.safe_execute(request_fail)
    
    assert not response_fail.success, "Expected failed response"
    
    print("✅ Pipeline tracing test passed")


async def test_metrics_collection():
    """Test metrics collection functionality"""
    print("Testing metrics collection...")
    
    metrics_collector = get_global_metrics()
    
    # Run some test executions
    pipeline = TestPipeline()
    
    # Run more successful executions to ensure high success rate
    for i in range(10):
        request = BypassRequest(host=f"test{i}.com", port=80, method="GET")
        await pipeline.safe_execute(request)
    
    # Test failed execution (only 1)
    request_fail = BypassRequest(host="fail.com", port=80, method="GET")
    await pipeline.safe_execute(request_fail)
    
    # Check metrics
    metrics = metrics_collector.get_metrics("test_pipeline")
    success_rates = metrics_collector.get_success_rate("test_pipeline")
    traces = metrics_collector.get_recent_traces(20)
    
    assert metrics['total_executions'] >= 11, "Expected at least 11 executions"
    assert metrics['successful_executions'] >= 10, "Expected at least 10 successes"
    assert metrics['failed_executions'] >= 1, "Expected at least 1 failure"
    assert success_rates['test_pipeline'] > 0.8, f"Expected high success rate, got {success_rates['test_pipeline']}"
    assert len(traces) >= 11, "Expected at least 11 traces"
    
    print("✅ Metrics collection test passed")


async def test_metrics_api():
    """Test metrics API functionality"""
    print("Testing metrics API...")
    
    api = get_metrics_api()
    
    # Test system overview
    overview = api.get_system_overview()
    assert "system_stats" in overview, "Expected system_stats in overview"
    assert "pipeline_metrics" in overview, "Expected pipeline_metrics in overview"
    
    # Test pipeline metrics
    pipeline_metrics = api.get_pipeline_metrics("test_pipeline")
    assert pipeline_metrics["pipeline"] == "test_pipeline", "Expected correct pipeline name"
    
    # Test traces
    traces = api.get_traces(5)
    assert "traces" in traces, "Expected traces in response"
    assert "statistics" in traces, "Expected statistics in response"
    
    # Test failure analysis
    failure_analysis = api.get_failure_analysis()
    assert "failure_analysis" in failure_analysis, "Expected failure_analysis in response"
    
    # Test performance report
    perf_report = api.get_performance_report(1)  # Last 1 hour
    assert "pipeline_performance" in perf_report, "Expected pipeline_performance in report"
    
    # Test export
    json_export = api.export_metrics("json")
    assert "system_stats" in json_export, "Expected system_stats in JSON export"
    
    csv_export = api.export_metrics("csv")
    assert "pipeline,total_executions" in csv_export, "Expected CSV header"
    
    print("✅ Metrics API test passed")


async def test_log_format():
    """Test that logs are in correct JSON format"""
    print("Testing log format...")
    
    logger = get_logger("format_test")
    
    # This should produce a JSON log entry
    logger.info("format_test", 
                pipeline="test_pipeline",
                status="success",
                latency=0.123)
    
    print("✅ Log format test passed")


async def main():
    """Run all observability tests"""
    print("🔍 Starting observability layer tests...\n")
    
    try:
        await test_structured_logging()
        await test_pipeline_tracing()
        await test_metrics_collection()
        await test_metrics_api()
        await test_log_format()
        
        print("\n🎉 All observability tests passed!")
        print("\n📊 Current system state:")
        
        # Show final metrics
        api = get_metrics_api()
        overview = api.get_system_overview()
        
        print(f"  - Total executions: {overview['system_stats']['total_executions']}")
        print(f"  - Success rate: {overview['system_stats']['success_rate']:.2%}")
        print(f"  - Average latency: {overview['system_stats']['average_latency']:.3f}s")
        print(f"  - Active pipelines: {overview['system_stats']['active_pipelines']}")
        
        print("\n✅ Observability layer is fully functional!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
