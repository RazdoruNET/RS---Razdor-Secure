"""
Tests for EVENT_HORIZON Core Engine
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from event_horizon.core.engine import EventHorizonEngine
from event_horizon.core.models import AuthComponent, AuthComponentType, TestScenario


class TestEventHorizonEngine:
    """Test cases for EventHorizonEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create a test engine instance"""
        return EventHorizonEngine()
    
    @pytest.fixture
    def sample_components(self):
        """Create sample authentication components"""
        components = [
            AuthComponent(
                id="waf_01",
                name="Web Application Firewall",
                type=AuthComponentType.WAF,
                endpoint="https://test.com/waf",
                dependencies=[]
            ),
            AuthComponent(
                id="rl_01", 
                name="Rate Limiter",
                type=AuthComponentType.RATE_LIMITER,
                endpoint="https://test.com/rate-limit",
                dependencies=["waf_01"]
            ),
            AuthComponent(
                id="db_01",
                name="Database",
                type=AuthComponentType.DATABASE,
                endpoint="https://test.com/db",
                dependencies=["rl_01"]
            )
        ]
        return components
    
    @pytest.fixture
    def sample_scenario(self):
        """Create a sample test scenario"""
        return TestScenario(
            id="test_scenario",
            name="Test Scenario",
            description="A test scenario for unit testing",
            target_components=["waf_01", "rl_01", "db_01"],
            load_pattern={
                "request_count": 10,
                "requests_per_second": 5,
                "source_ip_pattern": "192.168.1.100",
                "user_agent": "Test-Agent/1.0",
                "payload_template": {"test": "data"},
                "expected_result": "success"
            },
            anomaly_injection=[],
            duration_seconds=2,
            expected_behaviors=["success"]
        )
    
    def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert engine.test_id is not None
        assert len(engine.components) == 0
        assert len(engine.active_scenarios) == 0
        assert engine.current_phase.value == "baseline"
    
    def test_register_component(self, engine, sample_components):
        """Test component registration"""
        component = sample_components[0]
        engine.register_component(component)
        
        assert component.id in engine.components
        assert engine.components[component.id] == component
    
    def test_add_scenario(self, engine, sample_scenario):
        """Test scenario addition"""
        engine.add_scenario(sample_scenario)
        
        assert sample_scenario.id in [s.id for s in engine.active_scenarios]
        assert len(engine.active_scenarios) == 1
    
    def test_dependency_order(self, engine, sample_components):
        """Test component dependency ordering"""
        for component in sample_components:
            engine.register_component(component)
        
        order = engine._get_component_execution_order()
        
        # WAF should come first (no dependencies)
        assert order[0] == "waf_01"
        # Rate limiter should depend on WAF
        assert order.index("rl_01") > order.index("waf_01")
        # Database should depend on rate limiter
        assert order.index("db_01") > order.index("rl_01")
    
    @pytest.mark.asyncio
    async def test_baseline_requests_generation(self, engine):
        """Test baseline request generation"""
        requests = engine._generate_baseline_requests()
        
        assert len(requests) == 100
        assert all(hasattr(req, 'id') for req in requests)
        assert all(hasattr(req, 'timestamp') for req in requests)
        assert all(req.expected_result == "success" for req in requests)
    
    @pytest.mark.asyncio
    async def test_stress_requests_generation(self, engine):
        """Test stress request generation"""
        requests = engine._generate_stress_requests()
        
        assert len(requests) == 1000  # 5 bursts * 200 requests
        assert all(req.expected_result == "success" for req in requests)
    
    @pytest.mark.asyncio
    async def test_scenario_requests_generation(self, engine, sample_scenario):
        """Test scenario-specific request generation"""
        engine.add_scenario(sample_scenario)
        requests = engine._generate_scenario_requests(sample_scenario)
        
        assert len(requests) == 10
        assert all(req.expected_result == "success" for req in requests)
    
    @pytest.mark.asyncio
    async def test_request_processing(self, engine, sample_components):
        """Test individual request processing"""
        for component in sample_components:
            engine.register_component(component)
        
        from event_horizon.core.models import TestRequest
        request = TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"test": "data"},
            expected_result="success"
        )
        
        await engine._process_request(request)
        
        # Should have responses from all components
        assert len(engine.test_results) == 3
    
    @pytest.mark.asyncio
    async def test_semantic_drift_detection(self, engine, sample_components):
        """Test semantic drift detection"""
        for component in sample_components:
            engine.register_component(component)
        
        from event_horizon.core.models import TestRequest, TestResponse
        request = TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"preserve_semantics": True, "test": "data"},
            expected_result="success"
        )
        
        response = TestResponse(
            request_id=request.id,
            component_id="waf_01",
            timestamp=time.time(),
            status_code=200,
            response_time=0.01,
            payload={"processed_by": "waf_01", "normalized": True}
        )
        
        drift_event = engine._detect_semantic_drift(request, response, sample_components[0])
        
        assert drift_event is not None
        assert drift_event.request_id == request.id
        assert drift_event.target_component == "waf_01"
        assert drift_event.drift_type == "normalization_loss"
    
    @pytest.mark.asyncio
    async def test_anomaly_injection(self, engine):
        """Test anomaly injection"""
        anomalies = [
            {"type": "network_latency", "duration_ms": 100},
            {"type": "packet_loss", "loss_rate": 0.1},
            {"type": "component_failure", "component_id": "test_comp", "duration_ms": 1000}
        ]
        
        await engine._inject_anomalies(anomalies)
        
        # Should complete without errors
        assert True
    
    @pytest.mark.asyncio
    async def test_assessment_execution(self, engine, sample_components, sample_scenario):
        """Test full assessment execution"""
        # Setup
        for component in sample_components:
            engine.register_component(component)
        engine.add_scenario(sample_scenario)
        
        # Run assessment (with mocked time to speed up test)
        with patch('time.time', side_effect=[0, 1, 2, 3, 4, 5]):
            results = await engine.run_assessment()
        
        # Verify results
        assert results.test_id == engine.test_id
        assert results.start_time < results.end_time
        assert len(results.component_metrics) == 3
        assert results.system_metrics.total_requests > 0
    
    def test_failure_topology_generation(self, engine, sample_components):
        """Test failure topology generation"""
        for component in sample_components:
            engine.register_component(component)
        
        # Add some failure events
        from event_horizon.core.models import FailureEvent, FailureType
        failure = FailureEvent(
            id="test_failure",
            component_id="waf_01",
            failure_type=FailureType.NORMALIZATION_LOSS,
            severity=0.5,
            description="Test failure",
            affected_requests=["req1", "req2"]
        )
        engine.failure_events.append(failure)
        
        topology = engine._generate_failure_topology()
        
        assert "nodes" in topology
        assert "edges" in topology
        assert "failures" in topology
        assert len(topology["nodes"]) == 3
        assert len(topology["failures"]) == 1
    
    def test_breakpoint_identification(self, engine, sample_components):
        """Test breakpoint identification"""
        for component in sample_components:
            engine.register_component(component)
        
        # Add high error rate metrics
        from event_horizon.core.models import ComponentMetrics
        metrics = ComponentMetrics(
            component_id="waf_01",
            total_requests=100,
            successful_requests=80,
            failed_requests=20,
            avg_response_time=0.1,
            max_response_time=0.5,
            min_response_time=0.01,
            error_rate=0.2,
            throughput=10,
            semantic_drift_events=[],
            failure_events=[]
        )
        
        engine.component_metrics = {"waf_01": metrics}
        
        breakpoints = engine._identify_breakpoints()
        
        assert len(breakpoints) > 0
        assert any("waf_01" in bp for bp in breakpoints)
        assert any("High error rate" in bp for bp in breakpoints)


if __name__ == "__main__":
    pytest.main([__file__])
