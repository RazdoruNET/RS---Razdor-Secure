"""
Test Planner

Autonomous test planning agent that creates comprehensive
test scenarios based on system analysis and requirements.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import yaml


class TestType(Enum):
    """Types of tests to plan."""
    AUTHENTICATION_STRESS = "authentication_stress"
    RATE_LIMITING_TEST = "rate_limiting_test"
    SESSION_MANAGEMENT = "session_management"
    INPUT_NORMALIZATION = "input_normalization"
    SQL_PARSER_ANALYSIS = "sql_parser_analysis"
    HEADER_POLYMORPHISM = "header_polymorphism"
    CIRCUIT_BREAKER_TEST = "circuit_breaker_test"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    RESILIENCE_TEST = "resilience_test"


class TestPriority(Enum):
    """Test priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestScenario:
    """Individual test scenario definition."""
    name: str
    test_type: TestType
    priority: TestPriority
    description: str
    target_endpoint: str
    request_count: int
    concurrency: int
    duration_seconds: int
    parameters: Dict[str, Any]
    expected_outcomes: List[str]
    success_criteria: Dict[str, Any]
    safety_limits: Dict[str, Any]


@dataclass
class TestPlan:
    """Comprehensive test plan."""
    name: str
    description: str
    created_at: float
    scenarios: List[TestScenario]
    global_parameters: Dict[str, Any]
    safety_config: Dict[str, Any]
    estimated_duration: int
    resource_requirements: Dict[str, Any]


class TestPlanner:
    """
    Autonomous test planning agent for creating comprehensive test scenarios.
    """
    
    def __init__(self, target_system: str, config_path: Optional[str] = None):
        """
        Initialize test planner.
        
        Args:
            target_system: Target system URL or identifier
            config_path: Optional configuration file path
        """
        self.target_system = target_system
        self.config = self._load_config(config_path) if config_path else {}
        
        # Test templates
        self.test_templates = self._initialize_templates()
        
        # Planning state
        self.current_plan: Optional[TestPlan] = None
        self.planning_history: List[TestPlan] = []
        
        # System analysis results
        self.system_analysis: Dict[str, Any] = {}
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception:
            return {}
    
    def _initialize_templates(self) -> Dict[TestType, Dict[str, Any]]:
        """Initialize test templates for different test types."""
        templates = {
            TestType.AUTHENTICATION_STRESS: {
                "request_count": 1000,
                "concurrency": 50,
                "duration_seconds": 300,
                "parameters": {
                    "auth_methods": ["basic", "bearer", "session"],
                    "credential_variations": 10,
                    "failure_injection": True
                },
                "success_criteria": {
                    "min_success_rate": 0.95,
                    "max_response_time_p95": 2.0,
                    "error_rate_threshold": 0.05
                },
                "safety_limits": {
                    "max_error_rate": 0.3,
                    "circuit_breaker_threshold": 0.2,
                    "max_response_time": 10.0
                }
            },
            
            TestType.RATE_LIMITING_TEST: {
                "request_count": 5000,
                "concurrency": 100,
                "duration_seconds": 600,
                "parameters": {
                    "burst_patterns": ["constant", "spike", "gradual"],
                    "rate_limit_thresholds": [10, 50, 100, 500],
                    "bypass_attempts": False
                },
                "success_criteria": {
                    "rate_limit_effectiveness": 0.9,
                    "response_consistency": 0.95,
                    "no_cascade_failures": True
                },
                "safety_limits": {
                    "max_4xx_rate": 0.5,
                    "max_5xx_rate": 0.1,
                    "system_stability": True
                }
            },
            
            TestType.SESSION_MANAGEMENT: {
                "request_count": 2000,
                "concurrency": 25,
                "duration_seconds": 400,
                "parameters": {
                    "session_types": ["cookie", "token", "jwt"],
                    "concurrent_sessions": 100,
                    "session_lifecycle": ["create", "validate", "expire", "renew"]
                },
                "success_criteria": {
                    "session_creation_success": 0.98,
                    "session_validation_accuracy": 0.99,
                    "session_cleanup_efficiency": 0.95
                },
                "safety_limits": {
                    "max_session_creation_time": 5.0,
                    "max_memory_usage": "500MB",
                    "session_leak_threshold": 0.05
                }
            },
            
            TestType.INPUT_NORMALIZATION: {
                "request_count": 1500,
                "concurrency": 30,
                "duration_seconds": 300,
                "parameters": {
                    "input_variations": ["case", "whitespace", "encoding", "charset"],
                    "test_vectors": 100,
                    "edge_cases": True
                },
                "success_criteria": {
                    "normalization_consistency": 0.95,
                    "parser_robustness": 0.9,
                    "no_security_bypass": True
                },
                "safety_limits": {
                    "max_parser_errors": 0.1,
                    "max_response_time": 3.0,
                    "no_data_corruption": True
                }
            },
            
            TestType.SQL_PARSER_ANALYSIS: {
                "request_count": 800,
                "concurrency": 20,
                "duration_seconds": 200,
                "parameters": {
                    "query_variations": ["syntax", "encoding", "comments", "case"],
                    "safe_queries_only": True,
                    "response_analysis": True
                },
                "success_criteria": {
                    "parser_consistency": 0.9,
                    "no_data_exposure": True,
                    "error_handling_robustness": 0.95
                },
                "safety_limits": {
                    "no_sql_injection": True,
                    "max_error_rate": 0.15,
                    "response_time_consistency": 0.8
                }
            },
            
            TestType.HEADER_POLYMORPHISM: {
                "request_count": 3000,
                "concurrency": 75,
                "duration_seconds": 500,
                "parameters": {
                    "header_variations": ["order", "case", "duplicates", "whitespace"],
                    "user_agent_variants": 50,
                    "accept_language_variants": 20
                },
                "success_criteria": {
                    "header_processing_consistency": 0.9,
                    "no_header_injection": True,
                    "middleware_robustness": 0.95
                },
                "safety_limits": {
                    "max_header_processing_time": 2.0,
                    "no_request_rejection": 0.1,
                    "memory_usage_stable": True
                }
            },
            
            TestType.CIRCUIT_BREAKER_TEST: {
                "request_count": 2000,
                "concurrency": 40,
                "duration_seconds": 300,
                "parameters": {
                    "failure_injection": True,
                    "recovery_testing": True,
                    "cascade_prevention": True
                },
                "success_criteria": {
                    "circuit_breaker_effectiveness": 0.9,
                    "recovery_time_acceptable": True,
                    "no_system_wide_failure": True
                },
                "safety_limits": {
                    "max_system_downtime": 30.0,
                    "graceful_degradation": True,
                    "auto_recovery": True
                }
            },
            
            TestType.PERFORMANCE_BENCHMARK: {
                "request_count": 5000,
                "concurrency": 100,
                "duration_seconds": 600,
                "parameters": {
                    "load_patterns": ["ramp_up", "sustained", "spike"],
                    "resource_monitoring": True,
                    "baseline_comparison": True
                },
                "success_criteria": {
                    "response_time_p95": 1.0,
                    "throughput_target": 1000,
                    "resource_efficiency": 0.8
                },
                "safety_limits": {
                    "max_cpu_usage": 80.0,
                    "max_memory_usage": 85.0,
                    "no_system_crash": True
                }
            },
            
            TestType.RESILIENCE_TEST: {
                "request_count": 4000,
                "concurrency": 60,
                "duration_seconds": 800,
                "parameters": {
                    "failure_scenarios": ["network", "service", "resource"],
                    "recovery_testing": True,
                    "chaos_engineering": True
                },
                "success_criteria": {
                    "system_availability": 0.99,
                    "graceful_degradation": True,
                    "auto_recovery": True
                },
                "safety_limits": {
                    "max_downtime": 60.0,
                    "data_integrity": True,
                    "security_maintained": True
                }
            }
        }
        
        return templates
    
    async def analyze_target_system(self) -> Dict[str, Any]:
        """
        Analyze target system to inform test planning.
        
        Returns:
            System analysis results
        """
        analysis = {
            "target": self.target_system,
            "analysis_timestamp": time.time(),
            "discovered_endpoints": [],
            "authentication_methods": [],
            "identified_risks": [],
            "recommended_tests": [],
            "system_characteristics": {}
        }
        
        # Basic system characterization
        analysis["system_characteristics"] = {
            "target_type": "web_application",
            "protocol": "https",
            "expected_auth_endpoints": ["/login", "/auth", "/api/auth"],
            "common_protected_endpoints": ["/api/", "/admin/", "/dashboard"],
            "rate_limiting_indicators": ["429", "rate limit", "too many requests"],
            "session_indicators": ["session", "cookie", "token", "jwt"]
        }
        
        # Recommended tests based on system type
        analysis["recommended_tests"] = [
            TestType.AUTHENTICATION_STRESS,
            TestType.RATE_LIMITING_TEST,
            TestType.SESSION_MANAGEMENT,
            TestType.INPUT_NORMALIZATION,
            TestType.HEADER_POLYMORPHISM,
            TestType.CIRCUIT_BREAKER_TEST,
            TestType.RESILIENCE_TEST
        ]
        
        # Identified risks
        analysis["identified_risks"] = [
            "authentication_bypass",
            "rate_limit_evasion",
            "session_hijacking",
            "parser_inconsistency",
            "cascade_failure",
            "resource_exhaustion"
        ]
        
        self.system_analysis = analysis
        return analysis
    
    async def create_test_plan(self, test_types: Optional[List[TestType]] = None,
                             priority_filter: Optional[TestPriority] = None,
                             custom_parameters: Optional[Dict[str, Any]] = None) -> TestPlan:
        """
        Create comprehensive test plan.
        
        Args:
            test_types: Specific test types to include (None for all recommended)
            priority_filter: Filter by priority level
            custom_parameters: Custom parameters to override defaults
            
        Returns:
            Created test plan
        """
        # Analyze system if not already done
        if not self.system_analysis:
            await self.analyze_target_system()
        
        # Determine test types
        if test_types is None:
            test_types = self.system_analysis.get("recommended_tests", list(TestType))
        
        # Create scenarios
        scenarios = []
        total_duration = 0
        
        for test_type in test_types:
            scenario = await self._create_scenario(test_type, priority_filter, custom_parameters)
            if scenario:
                scenarios.append(scenario)
                total_duration += scenario.duration_seconds
        
        # Sort scenarios by priority
        priority_order = {TestPriority.CRITICAL: 0, TestPriority.HIGH: 1, 
                         TestPriority.MEDIUM: 2, TestPriority.LOW: 3}
        scenarios.sort(key=lambda s: priority_order[s.priority])
        
        # Create test plan
        plan = TestPlan(
            name=f"Test Plan for {self.target_system}",
            description=f"Comprehensive resilience test plan generated at {time.ctime()}",
            created_at=time.time(),
            scenarios=scenarios,
            global_parameters=custom_parameters or {},
            safety_config=self._create_safety_config(),
            estimated_duration=total_duration,
            resource_requirements=self._estimate_resources(scenarios)
        )
        
        self.current_plan = plan
        self.planning_history.append(plan)
        
        return plan
    
    async def _create_scenario(self, test_type: TestType, 
                            priority_filter: Optional[TestPriority],
                            custom_parameters: Optional[Dict[str, Any]]) -> Optional[TestScenario]:
        """Create individual test scenario."""
        template = self.test_templates.get(test_type)
        if not template:
            return None
        
        # Determine priority
        priority = self._determine_priority(test_type)
        if priority_filter and priority != priority_filter:
            return None
        
        # Merge parameters
        parameters = template["parameters"].copy()
        if custom_parameters:
            parameters.update(custom_parameters.get(test_type.value, {}))
        
        # Create scenario
        scenario = TestScenario(
            name=f"{test_type.value.replace('_', ' ').title()} Test",
            test_type=test_type,
            priority=priority,
            description=self._generate_scenario_description(test_type),
            target_endpoint=self.target_system,
            request_count=custom_parameters.get("request_count", template["request_count"]),
            concurrency=custom_parameters.get("concurrency", template["concurrency"]),
            duration_seconds=custom_parameters.get("duration_seconds", template["duration_seconds"]),
            parameters=parameters,
            expected_outcomes=self._generate_expected_outcomes(test_type),
            success_criteria=template["success_criteria"],
            safety_limits=template["safety_limits"]
        )
        
        return scenario
    
    def _determine_priority(self, test_type: TestType) -> TestPriority:
        """Determine priority for test type."""
        high_priority_tests = {
            TestType.AUTHENTICATION_STRESS,
            TestType.RATE_LIMITING_TEST,
            TestType.SESSION_MANAGEMENT,
            TestType.CIRCUIT_BREAKER_TEST
        }
        
        medium_priority_tests = {
            TestType.INPUT_NORMALIZATION,
            TestType.SQL_PARSER_ANALYSIS,
            TestType.HEADER_POLYMORPHISM
        }
        
        if test_type in high_priority_tests:
            return TestPriority.HIGH
        elif test_type in medium_priority_tests:
            return TestPriority.MEDIUM
        else:
            return TestPriority.LOW
    
    def _generate_scenario_description(self, test_type: TestType) -> str:
        """Generate description for test scenario."""
        descriptions = {
            TestType.AUTHENTICATION_STRESS: "Stress test authentication endpoints with various credential combinations and load patterns",
            TestType.RATE_LIMITING_TEST: "Test rate limiting effectiveness and bypass attempts under different load conditions",
            TestType.SESSION_MANAGEMENT: "Validate session creation, management, and cleanup under concurrent load",
            TestType.INPUT_NORMALIZATION: "Test input normalization consistency across different encoding and format variations",
            TestType.SQL_PARSER_ANALYSIS: "Analyze SQL parser behavior and response consistency with safe query variations",
            TestType.HEADER_POLYMORPHISM: "Test header processing robustness with various header formats and orders",
            TestType.CIRCUIT_BREAKER_TEST: "Validate circuit breaker functionality and recovery mechanisms",
            TestType.PERFORMANCE_BENCHMARK: "Establish performance baselines and measure system under load",
            TestType.RESILIENCE_TEST: "Test system resilience under failure conditions and recovery scenarios"
        }
        
        return descriptions.get(test_type, "Test scenario for system validation")
    
    def _generate_expected_outcomes(self, test_type: TestType) -> List[str]:
        """Generate expected outcomes for test scenario."""
        outcomes = {
            TestType.AUTHENTICATION_STRESS: [
                "System maintains authentication availability under stress",
                "No authentication bypass vulnerabilities discovered",
                "Response times remain within acceptable limits",
                "Session management remains stable"
            ],
            TestType.RATE_LIMITING_TEST: [
                "Rate limiting effectively prevents abuse",
                "Legitimate requests are not overly restricted",
                "No rate limit bypass methods found",
                "System remains stable during rate limit activation"
            ],
            TestType.SESSION_MANAGEMENT: [
                "Sessions are created and managed correctly",
                "Session cleanup prevents resource leaks",
                "Concurrent session handling works properly",
                "Session security is maintained"
            ],
            TestType.INPUT_NORMALIZATION: [
                "Input normalization is consistent across variations",
                "No parser inconsistencies discovered",
                "Security is not compromised by input variations",
                "System handles edge cases gracefully"
            ],
            TestType.SQL_PARSER_ANALYSIS: [
                "SQL parser behaves consistently",
                "No data exposure through parser variations",
                "Error handling is robust and consistent",
                "Response times remain stable"
            ],
            TestType.HEADER_POLYMORPHISM: [
                "Header processing is consistent and robust",
                "No security issues from header variations",
                "Middleware handles variations correctly",
                "No request rejection due to header format"
            ],
            TestType.CIRCUIT_BREAKER_TEST: [
                "Circuit breaker activates appropriately",
                "System recovers gracefully after failures",
                "No cascade failures occur",
                "Auto-recovery mechanisms work correctly"
            ],
            TestType.PERFORMANCE_BENCHMARK: [
                "Performance meets defined benchmarks",
                "System scales appropriately under load",
                "Resource usage remains within limits",
                "Response times are consistent"
            ],
            TestType.RESILIENCE_TEST: [
                "System maintains availability during failures",
                "Graceful degradation occurs when needed",
                "Recovery mechanisms function correctly",
                "Data integrity is maintained"
            ]
        }
        
        return outcomes.get(test_type, ["System behaves as expected under test conditions"])
    
    def _create_safety_config(self) -> Dict[str, Any]:
        """Create safety configuration for test plan."""
        return {
            "max_error_rate": 0.3,
            "circuit_breaker_threshold": 0.2,
            "max_response_time": 10.0,
            "max_memory_usage": "2GB",
            "max_cpu_usage": 90.0,
            "emergency_stop": True,
            "auto_recovery": True,
            "monitoring_interval": 5.0
        }
    
    def _estimate_resources(self, scenarios: List[TestScenario]) -> Dict[str, Any]:
        """Estimate resource requirements for test plan."""
        total_requests = sum(s.request_count for s in scenarios)
        max_concurrency = max(s.concurrency for s in scenarios)
        total_duration = sum(s.duration_seconds for s in scenarios)
        
        return {
            "estimated_requests": total_requests,
            "max_concurrent_requests": max_concurrency,
            "total_duration_seconds": total_duration,
            "estimated_memory_usage": f"{max(512, max_concurrency * 10)}MB",
            "estimated_cpu_usage": f"{min(80, max_concurrency * 0.5)}%",
            "network_bandwidth": f"{max(10, total_requests * 0.001)}Mbps"
        }
    
    def get_current_plan(self) -> Optional[TestPlan]:
        """Get current test plan."""
        return self.current_plan
    
    def get_planning_history(self) -> List[TestPlan]:
        """Get planning history."""
        return self.planning_history.copy()
    
    def export_plan(self, filename: str, format: str = "yaml"):
        """
        Export current test plan to file.
        
        Args:
            filename: Output filename
            format: Export format ("yaml" or "json")
        """
        if not self.current_plan:
            raise ValueError("No current test plan to export")
        
        plan_dict = asdict(self.current_plan)
        
        # Convert enums to strings
        for scenario in plan_dict["scenarios"]:
            scenario["test_type"] = scenario["test_type"].value
            scenario["priority"] = scenario["priority"].value
        
        if format.lower() == "yaml":
            with open(filename, 'w') as f:
                yaml.dump(plan_dict, f, default_flow_style=False)
        
        elif format.lower() == "json":
            with open(filename, 'w') as f:
                json.dump(plan_dict, f, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_plan(self, filename: str, format: str = "yaml") -> TestPlan:
        """
        Import test plan from file.
        
        Args:
            filename: Input filename
            format: Import format ("yaml" or "json")
            
        Returns:
            Imported test plan
        """
        if format.lower() == "yaml":
            with open(filename, 'r') as f:
                plan_dict = yaml.safe_load(f)
        
        elif format.lower() == "json":
            with open(filename, 'r') as f:
                plan_dict = json.load(f)
        
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        # Convert strings back to enums
        for scenario in plan_dict["scenarios"]:
            scenario["test_type"] = TestType(scenario["test_type"])
            scenario["priority"] = TestPriority(scenario["priority"])
        
        self.current_plan = TestPlan(**plan_dict)
        self.planning_history.append(self.current_plan)
        
        return self.current_plan
    
    async def optimize_plan(self, constraints: Dict[str, Any]) -> TestPlan:
        """
        Optimize current plan based on constraints.
        
        Args:
            constraints: Resource or time constraints
            
        Returns:
            Optimized test plan
        """
        if not self.current_plan:
            raise ValueError("No current test plan to optimize")
        
        optimized_scenarios = []
        
        for scenario in self.current_plan.scenarios:
            optimized_scenario = scenario
            
            # Apply constraints
            if "max_duration" in constraints:
                if scenario.duration_seconds > constraints["max_duration"]:
                    # Reduce duration while maintaining test effectiveness
                    scale_factor = constraints["max_duration"] / scenario.duration_seconds
                    optimized_scenario.duration_seconds = constraints["max_duration"]
                    optimized_scenario.request_count = int(scenario.request_count * scale_factor)
            
            if "max_concurrency" in constraints:
                if scenario.concurrency > constraints["max_concurrency"]:
                    optimized_scenario.concurrency = constraints["max_concurrency"]
                    # Increase duration to maintain total requests
                    scale_factor = scenario.concurrency / constraints["max_concurrency"]
                    optimized_scenario.duration_seconds = int(scenario.duration_seconds * scale_factor)
            
            if "max_requests" in constraints:
                if scenario.request_count > constraints["max_requests"]:
                    optimized_scenario.request_count = constraints["max_requests"]
                    # Adjust duration based on concurrency
                    optimized_scenario.duration_seconds = int(scenario.request_count / scenario.concurrency) + 60
            
            optimized_scenarios.append(optimized_scenario)
        
        # Create optimized plan
        optimized_plan = TestPlan(
            name=f"Optimized {self.current_plan.name}",
            description=f"Optimized version of {self.current_plan.description}",
            created_at=time.time(),
            scenarios=optimized_scenarios,
            global_parameters=self.current_plan.global_parameters,
            safety_config=self.current_plan.safety_config,
            estimated_duration=sum(s.duration_seconds for s in optimized_scenarios),
            resource_requirements=self._estimate_resources(optimized_scenarios)
        )
        
        self.current_plan = optimized_plan
        return optimized_plan
