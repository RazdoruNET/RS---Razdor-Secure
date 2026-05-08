"""
EVENT_HORIZON Core Engine

The main engine that orchestrates synthetic load generation,
manages test scenarios, and coordinates all testing layers.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
import structlog
from dataclasses import asdict

from .models import (
    AuthComponent, TestRequest, TestResponse, TestScenario,
    AssessmentResults, ComponentMetrics, FailureEvent,
    SemanticDriftEvent, TestPhase
)
from ..layers.nsl.normalization_stress import NormalizationStressLayer
from ..layers.scs.session_collapse import SessionCollapseSimulator
from ..layers.rlpm.rate_limit_pressure import RateLimitPressureModule
from ..layers.dbsil.db_stress import DBStressInterfaceLayer


logger = structlog.get_logger(__name__)


class EventHorizonEngine:
    """
    Core engine for synthetic load generation and test orchestration.
    
    Manages the execution of resilience assessment scenarios across
    multiple authentication pipeline components.
    """
    
    def __init__(self):
        self.test_id = str(uuid.uuid4())
        self.components: Dict[str, AuthComponent] = {}
        self.active_scenarios: List[TestScenario] = []
        self.test_results: List[TestResponse] = []
        self.failure_events: List[FailureEvent] = []
        self.semantic_drift_events: List[SemanticDriftEvent] = []
        
        # Initialize testing layers
        self.nsl = NormalizationStressLayer()
        self.scs = SessionCollapseSimulator()
        self.rlpm = RateLimitPressureModule()
        self.dbsil = DBStressInterfaceLayer()
        
        # Test state
        self.current_phase = TestPhase.BASELINE
        self.test_start_time: Optional[float] = None
        self.test_end_time: Optional[float] = None
        
        logger.info("EventHorizon engine initialized", test_id=self.test_id)
    
    def register_component(self, component: AuthComponent) -> None:
        """Register an authentication component for testing"""
        self.components[component.id] = component
        logger.info("Component registered", component_id=component.id, component_type=component.type.value)
    
    def add_scenario(self, scenario: TestScenario) -> None:
        """Add a test scenario to the execution queue"""
        self.active_scenarios.append(scenario)
        logger.info("Scenario added", scenario_id=scenario.id, scenario_name=scenario.name)
    
    async def run_assessment(self) -> AssessmentResults:
        """
        Execute the complete resilience assessment.
        
        Returns:
            AssessmentResults: Complete results from the assessment
        """
        logger.info("Starting resilience assessment", test_id=self.test_id)
        
        self.test_start_time = time.time()
        
        try:
            # Phase 1: Baseline measurement
            await self._run_baseline_phase()
            
            # Phase 2: Stress testing
            await self._run_stress_phase()
            
            # Phase 3: Degradation scenarios
            await self._run_degradation_phase()
            
            # Phase 4: Recovery testing
            await self._run_recovery_phase()
            
        except Exception as e:
            logger.error("Assessment failed", error=str(e))
            raise
        finally:
            self.test_end_time = time.time()
        
        # Generate results
        results = self._generate_assessment_results()
        
        logger.info("Assessment completed", 
                   test_id=self.test_id,
                   duration=self.test_end_time - self.test_start_time,
                   overall_score=results.overall_resilience_score)
        
        return results
    
    async def _run_baseline_phase(self) -> None:
        """Run baseline measurements without stress"""
        logger.info("Starting baseline phase")
        self.current_phase = TestPhase.BASELINE
        
        # Generate normal traffic patterns
        baseline_requests = self._generate_baseline_requests()
        
        # Execute requests against all components
        await self._execute_requests(baseline_requests)
        
        logger.info("Baseline phase completed")
    
    async def _run_stress_phase(self) -> None:
        """Run stress testing with high load"""
        logger.info("Starting stress phase")
        self.current_phase = TestPhase.STRESS
        
        # Generate high-volume traffic
        stress_requests = self._generate_stress_requests()
        
        # Execute with parallel processing
        await self._execute_requests_parallel(stress_requests, max_concurrency=50)
        
        logger.info("Stress phase completed")
    
    async def _run_degradation_phase(self) -> None:
        """Run degradation scenarios with anomaly injection"""
        logger.info("Starting degradation phase")
        self.current_phase = TestPhase.DEGRADATION
        
        for scenario in self.active_scenarios:
            logger.info("Executing degradation scenario", scenario_id=scenario.id)
            
            # Generate scenario-specific requests
            scenario_requests = self._generate_scenario_requests(scenario)
            
            # Inject anomalies based on scenario configuration
            await self._inject_anomalies(scenario.anomaly_injection)
            
            # Execute scenario
            await self._execute_requests_parallel(scenario_requests, max_concurrency=25)
        
        logger.info("Degradation phase completed")
    
    async def _run_recovery_phase(self) -> None:
        """Test recovery capabilities after stress"""
        logger.info("Starting recovery phase")
        self.current_phase = TestPhase.RECOVERY
        
        # Generate recovery traffic (normal load)
        recovery_requests = self._generate_baseline_requests()
        
        # Execute and measure recovery
        await self._execute_requests(recovery_requests)
        
        logger.info("Recovery phase completed")
    
    def _generate_baseline_requests(self) -> List[TestRequest]:
        """Generate normal authentication requests for baseline"""
        requests = []
        base_time = time.time()
        
        for i in range(100):  # 100 baseline requests
            request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=base_time + (i * 0.1),  # 10 requests per second
                source_ip=f"192.168.1.{100 + (i % 155)}",
                user_agent="Mozilla/5.0 (compatible; EVENT_HORIZON/1.0)",
                auth_token=f"baseline_token_{i}",
                session_id=f"session_{i % 20}",
                payload={"username": f"user_{i}", "password": "test_pass"},
                expected_result="success"
            )
            requests.append(request)
        
        return requests
    
    def _generate_stress_requests(self) -> List[TestRequest]:
        """Generate high-volume stress requests"""
        requests = []
        base_time = time.time()
        
        # Generate burst traffic pattern
        for burst in range(5):  # 5 bursts
            burst_start = base_time + (burst * 2)
            for i in range(200):  # 200 requests per burst
                request = TestRequest(
                    id=str(uuid.uuid4()),
                    timestamp=burst_start + (i * 0.01),  # 100 requests per second
                    source_ip=f"10.0.0.{1 + (i % 254)}",
                    user_agent="Mozilla/5.0 (compatible; EVENT_HORIZON-Stress/1.0)",
                    auth_token=f"stress_token_{burst}_{i}",
                    session_id=f"stress_session_{burst}_{i % 50}",
                    payload={"username": f"stress_user_{burst}_{i}", "password": "stress_pass"},
                    expected_result="success"
                )
                requests.append(request)
        
        return requests
    
    def _generate_scenario_requests(self, scenario: TestScenario) -> List[TestRequest]:
        """Generate requests specific to a test scenario"""
        requests = []
        base_time = time.time()
        
        # Generate requests based on scenario load pattern
        pattern = scenario.load_pattern
        request_count = pattern.get("request_count", 50)
        rate = pattern.get("requests_per_second", 10)
        
        for i in range(request_count):
            request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=base_time + (i / rate),
                source_ip=pattern.get("source_ip_pattern", f"172.16.0.{1 + (i % 254)}"),
                user_agent=pattern.get("user_agent", "Mozilla/5.0 (compatible; EVENT_HORIZON-Scenario/1.0)"),
                auth_token=f"scenario_token_{scenario.id}_{i}",
                session_id=f"scenario_session_{scenario.id}_{i % 30}",
                payload=pattern.get("payload_template", {"test": "data"}),
                expected_result=pattern.get("expected_result", "success")
            )
            requests.append(request)
        
        return requests
    
    async def _execute_requests(self, requests: List[TestRequest]) -> None:
        """Execute requests sequentially"""
        for request in requests:
            await self._process_request(request)
    
    async def _execute_requests_parallel(self, requests: List[TestRequest], max_concurrency: int = 10) -> None:
        """Execute requests in parallel with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def process_with_semaphore(request: TestRequest):
            async with semaphore:
                return await self._process_request(request)
        
        tasks = [process_with_semaphore(request) for request in requests]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_request(self, request: TestRequest) -> None:
        """Process a single request through the auth pipeline"""
        try:
            # Process through each component in dependency order
            for component_id in self._get_component_execution_order():
                component = self.components[component_id]
                
                # Simulate component processing
                response = await self._simulate_component_processing(component, request)
                self.test_results.append(response)
                
                # Check for semantic drift
                drift_event = self._detect_semantic_drift(request, response, component)
                if drift_event:
                    self.semantic_drift_events.append(drift_event)
                
                # Update request with component response data
                request.payload.update(response.payload)
                
                # Stop processing on failure
                if response.status_code >= 400:
                    break
        
        except Exception as e:
            logger.error("Request processing failed", request_id=request.id, error=str(e))
            
            # Record failure event
            failure = FailureEvent(
                id=str(uuid.uuid4()),
                component_id="unknown",
                failure_type="processing_error",
                severity=1.0,
                description=f"Request processing failed: {str(e)}",
                affected_requests=[request.id]
            )
            self.failure_events.append(failure)
    
    async def _simulate_component_processing(self, component: AuthComponent, request: TestRequest) -> TestResponse:
        """Simulate processing of a request by a component"""
        start_time = time.time()
        
        # Apply component-specific stress testing
        if component.type.value == "waf":
            await self.nsl.process_request(request)
        elif component.type.value == "session_manager":
            await self.scs.process_request(request)
        elif component.type.value == "rate_limiter":
            await self.rlpm.process_request(request)
        elif component.type.value == "database":
            await self.dbsil.process_request(request)
        
        # Simulate response time based on component load
        processing_time = 0.01 + (len(self.test_results) * 0.0001)  # Gradual degradation
        
        # Simulate occasional failures
        status_code = 200
        if len(self.test_results) % 100 == 0 and self.current_phase == TestPhase.STRESS:
            status_code = 503  # Service unavailable under stress
        
        await asyncio.sleep(processing_time)
        
        return TestResponse(
            request_id=request.id,
            component_id=component.id,
            timestamp=time.time(),
            status_code=status_code,
            response_time=processing_time,
            payload={"processed_by": component.name, "timestamp": time.time()}
        )
    
    def _get_component_execution_order(self) -> List[str]:
        """Get components in dependency order"""
        # Simple topological sort for component dependencies
        ordered = []
        remaining = list(self.components.values())
        
        while remaining:
            for component in remaining[:]:
                # Check if all dependencies are already ordered
                if all(dep in ordered for dep in component.dependencies):
                    ordered.append(component.id)
                    remaining.remove(component)
                    break
            else:
                # Circular dependency - break arbitrarily
                ordered.append(remaining[0].id)
                remaining.remove(remaining[0])
        
        return ordered
    
    def _detect_semantic_drift(self, request: TestRequest, response: TestResponse, component: AuthComponent) -> Optional[SemanticDriftEvent]:
        """Detect semantic drift between request and response"""
        # Simple drift detection based on payload changes
        if request.payload.get("preserve_semantics") and "normalized" in response.payload:
            return SemanticDriftEvent(
                request_id=request.id,
                source_component="input",
                target_component=component.id,
                input_data=request.payload.copy(),
                output_data=response.payload.copy(),
                drift_magnitude=0.3,
                drift_type="normalization_loss"
            )
        return None
    
    async def _inject_anomalies(self, anomaly_configs: List[Dict[str, Any]]) -> None:
        """Inject anomalies based on configuration"""
        for anomaly in anomaly_configs:
            anomaly_type = anomaly.get("type")
            
            if anomaly_type == "network_latency":
                await self._inject_network_latency(anomaly.get("duration_ms", 100))
            elif anomaly_type == "packet_loss":
                await self._inject_packet_loss(anomaly.get("loss_rate", 0.1))
            elif anomaly_type == "component_failure":
                await self._inject_component_failure(anomaly.get("component_id"), anomaly.get("duration_ms", 1000))
    
    async def _inject_network_latency(self, duration_ms: int) -> None:
        """Inject network latency"""
        logger.info("Injecting network latency", duration_ms=duration_ms)
        await asyncio.sleep(duration_ms / 1000.0)
    
    async def _inject_packet_loss(self, loss_rate: float) -> None:
        """Simulate packet loss"""
        logger.info("Simulating packet loss", loss_rate=loss_rate)
        # Implementation would depend on network simulation capabilities
    
    async def _inject_component_failure(self, component_id: str, duration_ms: int) -> None:
        """Simulate component failure"""
        logger.info("Simulating component failure", component_id=component_id, duration_ms=duration_ms)
        # Mark component as failed for duration
        if component_id in self.components:
            # Simulate failure by adding delay
            await asyncio.sleep(duration_ms / 1000.0)
    
    def _generate_assessment_results(self) -> AssessmentResults:
        """Generate comprehensive assessment results"""
        # Calculate component metrics
        component_metrics = {}
        for component_id, component in self.components.items():
            component_results = [r for r in self.test_results if r.component_id == component_id]
            
            if component_results:
                metrics = ComponentMetrics(
                    component_id=component_id,
                    total_requests=len(component_results),
                    successful_requests=len([r for r in component_results if r.status_code < 400]),
                    failed_requests=len([r for r in component_results if r.status_code >= 400]),
                    avg_response_time=sum(r.response_time for r in component_results) / len(component_results),
                    max_response_time=max(r.response_time for r in component_results),
                    min_response_time=min(r.response_time for r in component_results),
                    error_rate=len([r for r in component_results if r.status_code >= 400]) / len(component_results),
                    throughput=len(component_results) / (self.test_end_time - self.test_start_time) if self.test_end_time else 0,
                    semantic_drift_events=[e for e in self.semantic_drift_events if e.target_component == component_id],
                    failure_events=[e for e in self.failure_events if e.component_id == component_id]
                )
                component_metrics[component_id] = metrics
        
        # Generate system-wide metrics
        system_metrics = ComponentMetrics(
            component_id="system",
            total_requests=len(self.test_results),
            successful_requests=len([r for r in self.test_results if r.status_code < 400]),
            failed_requests=len([r for r in self.test_results if r.status_code >= 400]),
            avg_response_time=sum(r.response_time for r in self.test_results) / len(self.test_results) if self.test_results else 0,
            max_response_time=max(r.response_time for r in self.test_results) if self.test_results else 0,
            min_response_time=min(r.response_time for r in self.test_results) if self.test_results else 0,
            error_rate=len([r for r in self.test_results if r.status_code >= 400]) / len(self.test_results) if self.test_results else 0,
            throughput=len(self.test_results) / (self.test_end_time - self.test_start_time) if self.test_end_time and self.test_start_time else 0,
            semantic_drift_events=self.semantic_drift_events,
            failure_events=self.failure_events
        )
        
        return AssessmentResults(
            test_id=self.test_id,
            scenario_id="combined_scenarios",
            start_time=self.test_start_time or 0,
            end_time=self.test_end_time or 0,
            component_metrics=component_metrics,
            system_metrics=system_metrics,
            resilience_scores=[],  # Will be populated by scoring module
            failure_topology=self._generate_failure_topology(),
            auth_pipeline_breakpoints=self._identify_breakpoints(),
            normalization_loss_report=self._generate_normalization_report(),
            session_integrity_heatmap=self._generate_session_heatmap()
        )
    
    def _generate_failure_topology(self) -> Dict[str, Any]:
        """Generate failure topology graph data"""
        return {
            "nodes": [
                {"id": comp_id, "name": comp.name, "type": comp.type.value}
                for comp_id, comp in self.components.items()
            ],
            "edges": [
                {"source": dep, "target": comp_id}
                for comp_id, comp in self.components.items()
                for dep in comp.dependencies
            ],
            "failures": [
                {"component": event.component_id, "severity": event.severity, "type": event.failure_type.value}
                for event in self.failure_events
            ]
        }
    
    def _identify_breakpoints(self) -> List[str]:
        """Identify authentication pipeline breakpoints"""
        breakpoints = []
        
        # Components with high error rates
        for component_id, metrics in self.component_metrics.items():
            if metrics.error_rate > 0.1:  # 10% error rate threshold
                breakpoints.append(f"{component_id}: High error rate ({metrics.error_rate:.2%})")
        
        # Components with semantic drift
        for event in self.semantic_drift_events:
            if event.drift_magnitude > 0.5:
                breakpoints.append(f"{event.target_component}: Semantic drift detected")
        
        return breakpoints
    
    def _generate_normalization_report(self) -> Dict[str, Any]:
        """Generate normalization loss report"""
        normalization_events = [e for e in self.semantic_drift_events if e.drift_type == "normalization_loss"]
        
        return {
            "total_events": len(normalization_events),
            "average_drift": sum(e.drift_magnitude for e in normalization_events) / len(normalization_events) if normalization_events else 0,
            "affected_components": list(set(e.target_component for e in normalization_events)),
            "drift_distribution": {
                "low": len([e for e in normalization_events if e.drift_magnitude < 0.3]),
                "medium": len([e for e in normalization_events if 0.3 <= e.drift_magnitude < 0.7]),
                "high": len([e for e in normalization_events if e.drift_magnitude >= 0.7])
            }
        }
    
    def _generate_session_heatmap(self) -> Dict[str, Any]:
        """Generate session integrity heatmap data"""
        session_events = [e for e in self.failure_events if "session" in e.description.lower()]
        
        return {
            "session_failures": len(session_events),
            "failure_density": len(session_events) / len(self.components) if self.components else 0,
            "hotspots": [
                {"component": event.component_id, "intensity": event.severity}
                for event in session_events
            ]
        }
