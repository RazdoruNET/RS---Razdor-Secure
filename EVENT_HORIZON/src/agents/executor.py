"""
Test Executor

Autonomous test execution agent that runs test scenarios
with proper safety controls and real-time monitoring.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json

from ..async_engine import AsyncRequestEngine, RequestMethod, RequestConfig
from ..safety_layer import StabilityController, StabilityConfig
from ..observability import MetricsCollector, StructuredLogger
from ..traffic_polymorphism import HeaderVariabilityEngine, TrafficMutator
from .planner import TestScenario, TestPlan


class ExecutionStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class ExecutionResult:
    """Result of test execution."""
    scenario_name: str
    status: ExecutionStatus
    start_time: float
    end_time: float
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time: float
    p95_response_time: float
    throughput: float
    errors: List[str]
    metrics: Dict[str, Any]
    safety_events: List[str]


@dataclass
class ExecutionContext:
    """Context for test execution."""
    scenario: TestScenario
    request_engine: AsyncRequestEngine
    stability_controller: StabilityController
    metrics_collector: MetricsCollector
    logger: StructuredLogger
    progress_callback: Optional[Callable[[float], None]] = None


class TestExecutor:
    """
    Autonomous test execution agent with safety controls and monitoring.
    """
    
    def __init__(self, target_system: str, safety_config: Optional[StabilityConfig] = None):
        """
        Initialize test executor.
        
        Args:
            target_system: Target system URL
            safety_config: Safety configuration
        """
        self.target_system = target_system
        self.safety_config = safety_config or StabilityConfig()
        
        # Components
        self.request_engine: Optional[AsyncRequestEngine] = None
        self.stability_controller = StabilityController(self.safety_config)
        self.metrics_collector = MetricsCollector()
        self.logger = StructuredLogger("test_executor")
        
        # Traffic generation components
        self.header_engine = HeaderVariabilityEngine()
        self.traffic_mutator = TrafficMutator()
        
        # Execution state
        self.current_execution: Optional[ExecutionContext] = None
        self.execution_results: List[ExecutionResult] = []
        self.execution_active = False
        self.execution_paused = False
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup component callbacks."""
        # Stability controller callbacks
        self.stability_controller.add_stability_callback(self._on_stability_change)
        self.stability_controller.add_emergency_callback(self._on_emergency)
        
        # Metrics collector callbacks
        self.metrics_collector.record_http_request = self._record_http_metric
    
    async def initialize(self):
        """Initialize executor components."""
        # Initialize request engine
        self.request_engine = AsyncRequestEngine(
            max_concurrent_requests=self.safety_config.max_concurrent_requests,
            rate_limit=100.0,  # Will be adjusted per scenario
            timeout=30.0
        )
        
        await self.request_engine.start()
        
        # Start stability monitoring
        await self.stability_controller.start_monitoring()
        
        self.logger.info("Test executor initialized", component="executor")
    
    async def execute_scenario(self, scenario: TestPlan, 
                            progress_callback: Optional[Callable[[float], None]] = None) -> ExecutionResult:
        """
        Execute a single test scenario.
        
        Args:
            scenario: Test scenario to execute
            progress_callback: Progress callback function
            
        Returns:
            Execution result
        """
        if not self.request_engine:
            await self.initialize()
        
        # Create execution context
        context = ExecutionContext(
            scenario=scenario,
            request_engine=self.request_engine,
            stability_controller=self.stability_controller,
            metrics_collector=self.metrics_collector,
            logger=self.logger,
            progress_callback=progress_callback
        )
        
        self.current_execution = context
        self.execution_active = True
        self.execution_paused = False
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting scenario: {scenario.name}", 
                           component="executor", operation="execute_start",
                           scenario_name=scenario.name, test_type=scenario.test_type.value)
            
            # Execute the scenario
            result = await self._execute_scenario_internal(context)
            
            self.logger.info(f"Scenario completed: {scenario.name}", 
                           component="executor", operation="execute_complete",
                           scenario_name=scenario.name, status=result.status.value)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Scenario execution failed: {scenario.name}", 
                            component="executor", operation="execute_failed",
                            scenario_name=scenario.name, error=str(e))
            
            # Create failure result
            return ExecutionResult(
                scenario_name=scenario.name,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration_seconds=time.time() - start_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                error_rate=1.0,
                avg_response_time=0.0,
                p95_response_time=0.0,
                throughput=0.0,
                errors=[str(e)],
                metrics={},
                safety_events=[]
            )
        
        finally:
            self.execution_active = False
            self.current_execution = None
    
    async def _execute_scenario_internal(self, context: ExecutionContext) -> ExecutionResult:
        """Internal scenario execution logic."""
        scenario = context.scenario
        start_time = time.time()
        
        # Configure request engine for scenario
        context.request_engine.rate_limit = scenario.request_count / scenario.duration_seconds
        
        # Generate test requests
        requests = await self._generate_test_requests(context)
        
        # Execute requests with safety controls
        results = await self._execute_with_safety(context, requests)
        
        # Calculate metrics
        execution_metrics = self._calculate_execution_metrics(results, start_time)
        
        # Create result
        result = ExecutionResult(
            scenario_name=scenario.name,
            status=ExecutionStatus.COMPLETED,
            start_time=start_time,
            end_time=time.time(),
            duration_seconds=time.time() - start_time,
            total_requests=len(results),
            successful_requests=sum(1 for r in results if r.error is None),
            failed_requests=sum(1 for r in results if r.error is not None),
            error_rate=sum(1 for r in results if r.error is not None) / len(results) if results else 0.0,
            avg_response_time=sum(r.response_time for r in results) / len(results) if results else 0.0,
            p95_response_time=self._calculate_percentile([r.response_time for r in results], 0.95),
            throughput=len(results) / (time.time() - start_time) if results else 0.0,
            errors=[r.error for r in results if r.error],
            metrics=execution_metrics,
            safety_events=self._collect_safety_events(context)
        )
        
        self.execution_results.append(result)
        return result
    
    async def _generate_test_requests(self, context: ExecutionContext) -> List[RequestConfig]:
        """Generate test requests based on scenario type."""
        scenario = context.scenario
        requests = []
        
        # Generate base requests
        for i in range(scenario.request_count):
            request = await self._create_request_for_scenario(scenario, i)
            requests.append(request)
        
        return requests
    
    async def _create_request_for_scenario(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create a request for specific scenario."""
        base_url = scenario.target_endpoint
        
        if scenario.test_type.value == "authentication_stress":
            return await self._create_auth_request(scenario, index)
        elif scenario.test_type.value == "rate_limiting_test":
            return await self._create_rate_limit_request(scenario, index)
        elif scenario.test_type.value == "session_management":
            return await self._create_session_request(scenario, index)
        elif scenario.test_type.value == "input_normalization":
            return await self._create_normalization_request(scenario, index)
        elif scenario.test_type.value == "sql_parser_analysis":
            return await self._create_sql_request(scenario, index)
        elif scenario.test_type.value == "header_polymorphism":
            return await self._create_header_request(scenario, index)
        else:
            # Default request
            return RequestConfig(
                method=RequestMethod.GET,
                url=base_url,
                headers=self.header_engine.generate_headers("medium")
            )
    
    async def _create_auth_request(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create authentication test request."""
        auth_methods = scenario.parameters.get("auth_methods", ["basic"])
        method = auth_methods[index % len(auth_methods)]
        
        if method == "basic":
            credentials = f"test{index}:pass{index}"
            headers = {
                "Authorization": f"Basic {credentials.encode().hex()}",
                **self.header_engine.generate_headers("medium")
            }
        elif method == "bearer":
            token = f"token_{index}"
            headers = {
                "Authorization": f"Bearer {token}",
                **self.header_engine.generate_headers("medium")
            }
        else:  # session
            headers = {
                "Cookie": f"session_id=session_{index}",
                **self.header_engine.generate_headers("medium")
            }
        
        return RequestConfig(
            method=RequestMethod.POST,
            url=f"{scenario.target_endpoint}/login",
            headers=headers,
            data=f"username=test{index}&password=pass{index}"
        )
    
    async def _create_rate_limit_request(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create rate limiting test request."""
        headers = self.header_engine.generate_headers("high")
        
        # Add variations to test rate limit bypass
        if index % 10 == 0:
            headers["X-Forwarded-For"] = f"192.168.{index % 255}.{index % 255}"
        
        return RequestConfig(
            method=RequestMethod.GET,
            url=f"{scenario.target_endpoint}/api/data",
            headers=headers
        )
    
    async def _create_session_request(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create session management test request."""
        session_operations = scenario.parameters.get("session_lifecycle", ["create"])
        operation = session_operations[index % len(session_operations)]
        
        if operation == "create":
            return RequestConfig(
                method=RequestMethod.POST,
                url=f"{scenario.target_endpoint}/session/create",
                headers=self.header_engine.generate_headers("medium"),
                data=f"user_id={index}"
            )
        elif operation == "validate":
            return RequestConfig(
                method=RequestMethod.GET,
                url=f"{scenario.target_endpoint}/session/validate",
                headers={
                    "Cookie": f"session_id=session_{index}",
                    **self.header_engine.generate_headers("medium")
                }
            )
        else:  # expire
            return RequestConfig(
                method=RequestMethod.DELETE,
                url=f"{scenario.target_endpoint}/session/{index}",
                headers=self.header_engine.generate_headers("medium")
            )
    
    async def _create_normalization_request(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create input normalization test request."""
        # Create variations in input
        base_params = f"input=test{index}"
        
        # Apply mutations
        mutated_params = self.traffic_mutator.mutate_url(
            f"{scenario.target_endpoint}/api/normalize?{base_params}",
            "medium"
        )
        
        return RequestConfig(
            method=RequestMethod.GET,
            url=mutated_params,
            headers=self.header_engine.generate_headers("medium")
        )
    
    async def _create_sql_request(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create SQL parser analysis test request."""
        # Safe SQL variations only
        safe_queries = [
            "SELECT 1",
            "SELECT 'test'",
            "SELECT 1 FROM dual",
            "SELECT (1)"
        ]
        
        query = safe_queries[index % len(safe_queries)]
        
        return RequestConfig(
            method=RequestMethod.POST,
            url=f"{scenario.target_endpoint}/api/query",
            headers=self.header_engine.generate_headers("low"),
            data=f"query={query}"
        )
    
    async def _create_header_request(self, scenario: TestScenario, index: int) -> RequestConfig:
        """Create header polymorphism test request."""
        # Generate varied headers
        variation_level = ["low", "medium", "high"][index % 3]
        headers = self.header_engine.generate_headers(variation_level)
        
        return RequestConfig(
            method=RequestMethod.GET,
            url=f"{scenario.target_endpoint}/api/endpoint",
            headers=headers
        )
    
    async def _execute_with_safety(self, context: ExecutionContext, 
                                  requests: List[RequestConfig]) -> List[Any]:
        """Execute requests with safety controls."""
        results = []
        batch_size = 100  # Process in batches for better control
        
        for i in range(0, len(requests), batch_size):
            if not self.execution_active:
                break
            
            # Check if execution is paused
            while self.execution_paused and self.execution_active:
                await asyncio.sleep(0.1)
            
            if not self.execution_active:
                break
            
            batch = requests[i:i + batch_size]
            
            # Execute batch with stability protection
            try:
                batch_results = await self.stability_controller.execute_with_protection(
                    context.request_engine.execute_requests,
                    batch,
                    progress_callback=self._create_progress_callback(context, i, len(requests))
                )
                results.extend(batch_results)
                
                # Update progress
                if context.progress_callback:
                    progress = (i + len(batch)) / len(requests)
                    context.progress_callback(progress)
                
            except Exception as e:
                context.logger.error(f"Batch execution failed: {str(e)}", 
                                   component="executor", operation="batch_failed")
                break
        
        return results
    
    def _create_progress_callback(self, context: ExecutionContext, 
                                batch_start: int, total_requests: int) -> Callable[[int, int], None]:
        """Create progress callback for batch execution."""
        def callback(completed: int, total: int):
            if context.progress_callback:
                overall_progress = (batch_start + completed) / total_requests
                context.progress_callback(overall_progress)
        
        return callback
    
    def _calculate_execution_metrics(self, results: List[Any], start_time: float) -> Dict[str, Any]:
        """Calculate execution metrics."""
        if not results:
            return {}
        
        response_times = [r.response_time for r in results if r.error is None]
        status_codes = [r.status_code for r in results]
        
        return {
            "request_count": len(results),
            "success_count": len(response_times),
            "response_time_stats": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "mean": sum(response_times) / len(response_times) if response_times else 0,
                "p50": self._calculate_percentile(response_times, 0.5),
                "p95": self._calculate_percentile(response_times, 0.95),
                "p99": self._calculate_percentile(response_times, 0.99)
            },
            "status_code_distribution": {
                str(code): status_codes.count(code) for code in set(status_codes)
            },
            "execution_duration": time.time() - start_time
        }
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _collect_safety_events(self, context: ExecutionContext) -> List[str]:
        """Collect safety events from execution."""
        events = []
        
        # Get stability controller events
        health_status = context.stability_controller.get_health_status()
        if health_status["status"] != "healthy":
            events.append(f"Stability issue: {health_status['status']}")
        
        # Get error monitor events
        error_metrics = context.stability_controller.error_monitor.get_metrics()
        if error_metrics.total_errors > 0:
            events.append(f"Errors detected: {error_metrics.total_errors}")
        
        # Get circuit breaker events
        if context.stability_controller.circuit_breaker.get_state().value == "open":
            events.append("Circuit breaker opened")
        
        return events
    
    def _record_http_metric(self, method: str, endpoint: str, status_code: int,
                           duration: float, response_size: int):
        """Record HTTP metric in metrics collector."""
        self.metrics_collector.record_http_request(
            method, endpoint, status_code, duration, response_size
        )
    
    def _on_stability_change(self, old_level, new_level):
        """Handle stability level changes."""
        self.logger.warning(f"Stability level changed: {old_level.value} -> {new_level.value}",
                           component="executor", operation="stability_change")
    
    def _on_emergency(self):
        """Handle emergency conditions."""
        self.logger.critical("Emergency condition detected - stopping execution",
                           component="executor", operation="emergency")
        self.stop_execution()
    
    async def execute_plan(self, plan: TestPlan, 
                         progress_callback: Optional[Callable[[str, float], None]] = None) -> List[ExecutionResult]:
        """
        Execute complete test plan.
        
        Args:
            plan: Test plan to execute
            progress_callback: Progress callback (scenario_name, progress)
            
        Returns:
            List of execution results
        """
        results = []
        
        for i, scenario in enumerate(plan.scenarios):
            if not self.execution_active:
                break
            
            scenario_progress_callback = None
            if progress_callback:
                def scenario_progress(p):
                    progress_callback(scenario.name, (i + p) / len(plan.scenarios))
                scenario_progress_callback = scenario_progress
            
            result = await self.execute_scenario(scenario, scenario_progress_callback)
            results.append(result)
            
            # Check if we should continue based on safety
            if result.status == ExecutionStatus.FAILED:
                if result.error_rate > self.safety_config.error_rate_threshold:
                    self.logger.warning("Stopping plan execution due to high error rate",
                                       component="executor", operation="plan_stop")
                    break
        
        return results
    
    def pause_execution(self):
        """Pause current execution."""
        self.execution_paused = True
        self.logger.info("Execution paused", component="executor")
    
    def resume_execution(self):
        """Resume paused execution."""
        self.execution_paused = False
        self.logger.info("Execution resumed", component="executor")
    
    def stop_execution(self):
        """Stop current execution."""
        self.execution_active = False
        self.execution_paused = False
        self.logger.info("Execution stopped", component="executor")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        return {
            "execution_active": self.execution_active,
            "execution_paused": self.execution_paused,
            "current_scenario": self.current_execution.scenario.name if self.current_execution else None,
            "completed_scenarios": len(self.execution_results),
            "stability_level": self.stability_controller.get_stability_level().value,
            "health_status": self.stability_controller.get_health_status()
        }
    
    def get_execution_results(self) -> List[ExecutionResult]:
        """Get all execution results."""
        return self.execution_results.copy()
    
    async def cleanup(self):
        """Cleanup executor resources."""
        if self.request_engine:
            await self.request_engine.close()
        
        await self.stability_controller.stop_monitoring()
        
        self.logger.info("Test executor cleaned up", component="executor")
