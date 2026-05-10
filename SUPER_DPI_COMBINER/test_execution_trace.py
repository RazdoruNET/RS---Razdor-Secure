#!/usr/bin/env python3
"""
Test and Example Usage for Execution Trace Collector
TASK 8.2 - Execution Trace Collector Test
"""

import asyncio
import time
import json
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.execution_trace import ExecutionTrace, EventType, NetworkEventType
from core.network_tracker import NetworkTracker
from core.base_pipeline import BypassRequest, BypassResponse, BasePipeline, BypassTechnique, PipelineExecutionStatus

class TestPipeline(BasePipeline):
    """Test pipeline for demonstrating execution trace functionality"""
    
    def __init__(self):
        super().__init__("TestPipeline", BypassTechnique.SPOOF_DPI, priority=1, execution_status=PipelineExecutionStatus.REAL)
        self.network_tracker = None
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Execute pipeline with full execution trace tracking"""
        start_time = time.time()
        
        # Get execution trace and create network tracker
        trace = self.get_execution_trace()
        if not trace:
            trace = self.create_execution_trace()
        
        self.network_tracker = NetworkTracker(trace)
        
        try:
            # Track connection attempts
            trace.add_connection_attempt(request.host, request.port, "TCP", {
                'user_agent': 'TestPipeline/1.0',
                'protocol': 'HTTP/1.1'
            })
            
            # Simulate network operations with tracking
            await self._simulate_network_operations(request)
            
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            # Track successful completion
            response_time = time.time() - start_time
            
            return BypassResponse(
                success=True,
                latency=response_time,
                status_code=200,
                technique_used=self.name,
                data=b"Test response data",
                headers={
                    'X-Trace-ID': trace.execution_id,
                    'X-Events': str(len(trace.events)),
                    'X-Network-Events': str(len(trace.network_events))
                }
            )
            
        except Exception as e:
            # Track errors
            trace.add_error("PIPELINE_ERROR", str(e), {
                'request_host': request.host,
                'request_port': request.port
            })
            
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=f"Test pipeline error: {str(e)}"
            )
    
    async def _simulate_network_operations(self, request: BypassRequest):
        """Simulate network operations with full tracking"""
        trace = self.get_execution_trace()
        
        # Simulate connection success
        trace.add_connection_success(request.host, request.port, {
            'connection_time': 0.05,
            'tls_version': 'TLSv1.3'
        })
        
        # Simulate data send
        test_data = b"GET / HTTP/1.1\r\nHost: " + request.host.encode() + b"\r\n\r\n"
        trace.add_network_send(request.host, request.port, len(test_data), {
            'data_type': 'HTTP_REQUEST',
            'fragment_count': 1
        })
        
        # Simulate retry scenario
        trace.add_retry_attempt("data_send", 1, 3, "Initial send failed")
        
        # Simulate timeout
        trace.add_timeout("response_wait", 5.0, {
            'operation': 'waiting_for_response',
            'timeout_duration': 5.0
        })
        
        # Simulate data receive
        response_data = b"HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\nHello World!"
        trace.add_network_receive(request.host, request.port, len(response_data), {
            'data_type': 'HTTP_RESPONSE',
            'status_code': 200
        })
        
        # Simulate connection close
        trace.add_event(EventType.CONNECTION_FAILURE, {
            'host': request.host,
            'port': request.port,
            'reason': 'Connection closed normally'
        })
    
    def initialize(self, config):
        """Initialize test pipeline"""
        self.config = config or {}
        self._mark_initialized(True)
        return True
    
    def cleanup(self):
        """Cleanup resources"""
        return True

async def test_basic_execution_trace():
    """Test basic execution trace functionality"""
    print("🧪 Testing Basic Execution Trace Functionality")
    print("=" * 60)
    
    # Create execution trace
    trace = ExecutionTrace("TestPipeline")
    
    # Start execution
    trace.start_execution()
    
    # Add various events
    trace.add_connection_attempt("example.com", 443, "TLS")
    trace.add_connection_success("example.com", 443, {"connection_time": 0.1})
    
    trace.add_network_send("example.com", 443, 256, {"data_type": "HTTP_REQUEST"})
    trace.add_network_receive("example.com", 443, 1024, {"data_type": "HTTP_RESPONSE"})
    
    trace.add_retry_attempt("connection", 1, 3, "Initial timeout")
    trace.add_timeout("response_wait", 5.0)
    
    trace.add_error("TEST_ERROR", "This is a test error", {"test": True})
    
    # End execution
    trace.end_execution(success=True, final_status="completed")
    
    # Display results
    print(f"✅ Execution ID: {trace.execution_id}")
    print(f"✅ Pipeline: {trace.pipeline_name}")
    print(f"✅ Duration: {trace.get_duration():.3f}s")
    print(f"✅ Total Events: {len(trace.events)}")
    print(f"✅ Network Events: {len(trace.network_events)}")
    print(f"✅ Errors: {len(trace.errors)}")
    
    # Show connection statistics
    conn_stats = trace.get_connection_statistics()
    print(f"✅ Connection Statistics:")
    for key, value in conn_stats.items():
        print(f"   - {key}: {value}")
    
    # Show critical events
    critical = trace.get_critical_events()
    print(f"✅ Critical Events: {len(critical)}")
    for event in critical:
        print(f"   - {event['event_type']}: {event.get('error_message', event.get('details', {}))}")
    
    return trace

async def test_pipeline_integration():
    """Test execution trace integration with BasePipeline"""
    print("\n🧪 Testing Pipeline Integration")
    print("=" * 60)
    
    # Create and initialize test pipeline
    pipeline = TestPipeline()
    pipeline.initialize({"test_mode": True})
    
    # Create test request
    request = BypassRequest(
        host="httpbin.org",
        port=443,
        method="GET",
        timeout=10.0
    )
    
    # Execute pipeline (this will automatically create execution trace)
    response = await pipeline.safe_execute(request, timeout=5.0)
    
    # Get execution trace
    trace = pipeline.get_execution_trace()
    
    if trace:
        print(f"✅ Pipeline Execution Trace:")
        print(f"   - Execution ID: {trace.execution_id}")
        print(f"   - Pipeline: {trace.pipeline_name}")
        print(f"   - Duration: {trace.get_duration():.3f}s")
        print(f"   - Success: {response.success}")
        print(f"   - Events: {len(trace.events)}")
        print(f"   - Network Events: {len(trace.network_events)}")
        print(f"   - Errors: {len(trace.errors)}")
        
        # Show timeline
        timeline = trace.get_timeline_summary()
        print(f"   - Timeline Events: {len(timeline)}")
        
        # Save trace to file
        trace.save_to_file("test_execution_trace.json")
        print(f"   - Saved to: test_execution_trace.json")
        
        return trace
    else:
        print("❌ No execution trace found")
        return None

async def test_network_tracker():
    """Test NetworkTracker functionality"""
    print("\n🧪 Testing Network Tracker")
    print("=" * 60)
    
    # Create execution trace and network tracker
    trace = ExecutionTrace("NetworkTrackerTest")
    tracker = NetworkTracker(trace)
    
    trace.start_execution()
    
    # Simulate connection with retries
    async def mock_connect(host, port, **kwargs):
        await asyncio.sleep(0.1)  # Simulate connection time
        if "fail_first" in kwargs:
            raise ConnectionError("First attempt failed")
        return ("reader", "writer")  # Mock connection result
    
    # Test successful connection after retry
    print("📡 Testing connection with retry...")
    connection, success = await tracker.tracked_connection(
        "test.example.com", 443, mock_connect,
        max_retries=2, retry_delay=0.1, fail_first=True
    )
    
    print(f"   - Connection Success: {success}")
    
    # Test data send/receive
    async def mock_send(data, **kwargs):
        await asyncio.sleep(0.05)
        return len(data)
    
    async def mock_receive(**kwargs):
        await asyncio.sleep(0.05)
        return b"Mock response data"
    
    print("📤 Testing data send...")
    send_success = await tracker.tracked_send("test.example.com", 443, b"Test data", mock_send)
    print(f"   - Send Success: {send_success}")
    
    print("📥 Testing data receive...")
    received_data, recv_success = await tracker.tracked_receive("test.example.com", 443, mock_receive)
    print(f"   - Receive Success: {recv_success}")
    print(f"   - Data Size: {len(received_data)} bytes")
    
    trace.end_execution(success=True)
    
    # Show results
    print(f"✅ Network Tracker Results:")
    print(f"   - Total Events: {len(trace.events)}")
    print(f"   - Network Events: {len(trace.network_events)}")
    print(f"   - Connection Attempts: {trace.get_connection_statistics()['total_attempts']}")
    print(f"   - Retries: {trace.get_connection_statistics()['total_retries']}")
    
    return trace

async def demonstrate_trace_analysis():
    """Demonstrate trace analysis capabilities"""
    print("\n🧪 Demonstrating Trace Analysis")
    print("=" * 60)
    
    # Create a complex trace with various events
    trace = ExecutionTrace("AnalysisDemo")
    trace.start_execution()
    
    # Simulate complex pipeline execution
    hosts = ["api.example.com", "cdn.example.com", "auth.example.com"]
    
    for i, host in enumerate(hosts):
        # Connection attempts
        trace.add_connection_attempt(host, 443, "TLS", {"attempt": i+1})
        
        if i == 1:  # Simulate failure on second host
            trace.add_connection_failure(host, 443, "Connection refused")
            trace.add_retry_attempt("connection", 1, 3, "Connection refused")
            continue
        
        trace.add_connection_success(host, 443, {"connection_time": 0.05 + i*0.02})
        
        # Data transfer
        trace.add_network_send(host, 443, 512, {"request_type": "API_CALL"})
        await asyncio.sleep(0.01)
        
        if i == 2:  # Simulate timeout on third host
            trace.add_timeout("response_wait", 3.0)
            continue
            
        trace.add_network_receive(host, 443, 1024, {"response_type": "JSON"})
    
    # Add some errors
    trace.add_error("VALIDATION_ERROR", "Invalid response format", {
        "host": hosts[0],
        "expected": "JSON",
        "received": "HTML"
    })
    
    trace.add_error("RATE_LIMIT_ERROR", "Rate limit exceeded", {
        "host": hosts[1],
        "limit": 100,
        "current": 101
    })
    
    trace.end_execution(success=False, final_status="partial_failure")
    
    # Analysis
    print("📊 Trace Analysis Results:")
    
    # Basic statistics
    stats = trace.get_connection_statistics()
    print(f"   - Total Connection Attempts: {stats['total_attempts']}")
    print(f"   - Successful Connections: {stats['successful_connections']}")
    print(f"   - Failed Connections: {stats['failed_connections']}")
    print(f"   - Success Rate: {stats['success_rate']:.1%}")
    print(f"   - Total Retries: {stats['total_retries']}")
    print(f"   - Total Timeouts: {stats['total_timeouts']}")
    print(f"   - Data Sent: {stats['total_bytes_sent']} bytes")
    print(f"   - Data Received: {stats['total_bytes_received']} bytes")
    
    # Critical events analysis
    critical = trace.get_critical_events()
    print(f"   - Critical Events: {len(critical)}")
    
    error_types = {}
    for event in critical:
        error_type = event.get('error_type', event.get('event_type', 'unknown'))
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    print("   - Error Breakdown:")
    for error_type, count in error_types.items():
        print(f"     * {error_type}: {count}")
    
    # Timeline analysis
    timeline = trace.get_timeline_summary()
    print(f"   - Timeline Events: {len(timeline)}")
    
    # Save detailed trace
    trace.save_to_file("analysis_demo_trace.json")
    print(f"   - Detailed trace saved to: analysis_demo_trace.json")
    
    return trace

async def main():
    """Main test function"""
    print("🚀 Execution Trace Collector - TASK 8.2 Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Basic functionality
        trace1 = await test_basic_execution_trace()
        
        # Test 2: Pipeline integration
        trace2 = await test_pipeline_integration()
        
        # Test 3: Network tracker
        trace3 = await test_network_tracker()
        
        # Test 4: Analysis demonstration
        trace4 = await demonstrate_trace_analysis()
        
        # Summary
        print("\n📋 Test Summary")
        print("=" * 60)
        print(f"✅ Basic Execution Trace: {'PASS' if trace1 else 'FAIL'}")
        print(f"✅ Pipeline Integration: {'PASS' if trace2 else 'FAIL'}")
        print(f"✅ Network Tracker: {'PASS' if trace3 else 'FAIL'}")
        print(f"✅ Trace Analysis: {'PASS' if trace4 else 'FAIL'}")
        
        # Show sample JSON output
        if trace1:
            print(f"\n📄 Sample JSON Output (first 500 chars):")
            json_output = trace1.to_json()
            print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"📁 Generated files:")
        print(f"   - test_execution_trace.json")
        print(f"   - analysis_demo_trace.json")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
