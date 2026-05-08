"""
EVENT_HORIZON Scenario Library

Provides predefined test scenarios for resilience assessment
including stress patterns, anomaly injection, and degradation scenarios.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import structlog

from core.models import TestScenario

logger = structlog.get_logger(__name__)


class ScenarioLibrary:
    """
    Library of predefined test scenarios for authentication pipeline testing.
    
    Scenarios cover various attack patterns, stress conditions, and
    degradation scenarios to comprehensively test system resilience.
    """
    
    def __init__(self):
        self.scenarios: Dict[str, TestScenario] = {}
        self._initialize_scenarios()
        
        logger.info("Scenario Library initialized", scenario_count=len(self.scenarios))
    
    def get_scenario(self, scenario_id: str) -> TestScenario:
        """Get a specific scenario by ID"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario not found: {scenario_id}")
        return self.scenarios[scenario_id]
    
    def list_scenarios(self) -> List[str]:
        """List all available scenario IDs"""
        return list(self.scenarios.keys())
    
    def get_scenarios_by_category(self, category: str) -> List[TestScenario]:
        """Get scenarios by category"""
        return [scenario for scenario in self.scenarios.values() 
                if scenario.name.lower().startswith(category.lower())]
    
    def add_scenario(self, scenario: TestScenario) -> None:
        """Add a custom scenario"""
        self.scenarios[scenario.id] = scenario
        logger.info("Custom scenario added", scenario_id=scenario.id)
    
    def _initialize_scenarios(self) -> None:
        """Initialize predefined scenarios"""
        
        # 1. Baseline Performance Scenario
        self.scenarios["baseline_performance"] = TestScenario(
            id="baseline_performance",
            name="Baseline Performance Test",
            description="Measures normal performance characteristics without stress",
            target_components=["all"],
            load_pattern={
                "request_count": 1000,
                "requests_per_second": 10,
                "source_ip_pattern": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Baseline/1.0)",
                "payload_template": {
                    "username": "test_user_{index}",
                    "password": "test_password",
                    "action": "authenticate"
                },
                "expected_result": "success"
            },
            anomaly_injection=[],
            duration_seconds=100,
            expected_behaviors=["high_success_rate", "low_latency", "no_errors"]
        )
        
        # 2. High Load Stress Scenario
        self.scenarios["high_load_stress"] = TestScenario(
            id="high_load_stress",
            name="High Load Stress Test",
            description="Tests system under sustained high load conditions",
            target_components=["all"],
            load_pattern={
                "request_count": 10000,
                "requests_per_second": 100,
                "source_ip_pattern": "10.0.0.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Stress/1.0)",
                "payload_template": {
                    "username": "stress_user_{index}",
                    "password": "stress_password",
                    "action": "authenticate"
                },
                "expected_result": "success"
            },
            anomaly_injection=[
                {
                    "type": "network_latency",
                    "duration_ms": 50,
                    "probability": 0.1
                }
            ],
            duration_seconds=100,
            expected_behaviors=["degraded_performance", "increased_latency", "some_errors"]
        )
        
        # 3. Burst Traffic Scenario
        self.scenarios["burst_traffic"] = TestScenario(
            id="burst_traffic",
            name="Burst Traffic Attack",
            description="Simulates sudden traffic bursts to test rate limiting",
            target_components=["rate_limiter", "load_balancer"],
            load_pattern={
                "request_count": 5000,
                "requests_per_second": 500,  # Very high burst
                "source_ip_pattern": "172.16.0.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Burst/1.0)",
                "payload_template": {
                    "username": "burst_user_{index}",
                    "password": "burst_password",
                    "action": "authenticate"
                },
                "expected_result": "rate_limited"
            },
            anomaly_injection=[
                {
                    "type": "rate_limit_bypass",
                    "technique": "header_rotation",
                    "probability": 0.3
                }
            ],
            duration_seconds=10,
            expected_behaviors=["rate_limiting_active", "some_requests_blocked"]
        )
        
        # 4. Session Flood Scenario
        self.scenarios["session_flood"] = TestScenario(
            id="session_flood",
            name="Session Flood Attack",
            description="Overwhelms session management with massive session creation",
            target_components=["session_manager", "database"],
            load_pattern={
                "request_count": 2000,
                "requests_per_second": 50,
                "source_ip_pattern": "192.168.2.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Session/1.0)",
                "payload_template": {
                    "username": "session_user_{index}",
                    "password": "session_password",
                    "action": "create_session"
                },
                "expected_result": "success"
            },
            anomaly_injection=[
                {
                    "type": "session_exhaustion",
                    "target_component": "session_manager",
                    "probability": 0.5
                }
            ],
            duration_seconds=40,
            expected_behaviors=["session_creation_delays", "memory_pressure"]
        )
        
        # 5. Normalization Attack Scenario
        self.scenarios["normalization_attack"] = TestScenario(
            id="normalization_attack",
            name="WAF Normalization Attack",
            description="Tests WAF resilience against normalization bypass techniques",
            target_components=["waf"],
            load_pattern={
                "request_count": 500,
                "requests_per_second": 20,
                "source_ip_pattern": "203.0.113.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-WAF/1.0)",
                "payload_template": {
                    "username": "waf_user_{index}",
                    "password": "waf_password",
                    "path": "/admin\xc0\xafsecret",  # Overlong slash
                    "action": "access_admin"
                },
                "expected_result": "blocked"
            },
            anomaly_injection=[
                {
                    "type": "utf8_overlong",
                    "target_component": "waf",
                    "probability": 0.8
                },
                {
                    "type": "unicode_normalization",
                    "target_component": "waf",
                    "probability": 0.6
                }
            ],
            duration_seconds=25,
            expected_behaviors=["malicious_requests_blocked", "normalization_consistent"]
        )
        
        # 6. Database Stress Scenario
        self.scenarios["database_stress"] = TestScenario(
            id="database_stress",
            name="Database Connection Pool Stress",
            description="Tests database resilience under connection pool exhaustion",
            target_components=["database"],
            load_pattern={
                "request_count": 1000,
                "requests_per_second": 50,
                "source_ip_pattern": "198.51.100.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-DB/1.0)",
                "payload_template": {
                    "username": "db_user_{index}",
                    "password": "db_password",
                    "query": "SELECT * FROM users WHERE id = {index}",
                    "action": "database_query"
                },
                "expected_result": "success"
            },
            anomaly_injection=[
                {
                    "type": "connection_exhaustion",
                    "target_component": "database",
                    "probability": 0.4
                },
                {
                    "type": "slow_query",
                    "target_component": "database",
                    "probability": 0.2
                }
            ],
            duration_seconds=20,
            expected_behaviors=["connection_pool_management", "query_queue_handling"]
        )
        
        # 7. Distributed Attack Scenario
        self.scenarios["distributed_attack"] = TestScenario(
            id="distributed_attack",
            name="Distributed Attack Simulation",
            description="Simulates coordinated attack from multiple sources",
            target_components=["rate_limiter", "waf", "session_manager"],
            load_pattern={
                "request_count": 3000,
                "requests_per_second": 150,
                "source_ip_pattern": "{random_ip}",  # Will be randomized
                "user_agent": "{random_agent}",  # Will be randomized
                "payload_template": {
                    "username": "attacker_{index}",
                    "password": "attack_password",
                    "action": "brute_force"
                },
                "expected_result": "blocked"
            },
            anomaly_injection=[
                {
                    "type": "distributed_spoofing",
                    "target_component": "rate_limiter",
                    "probability": 0.7
                },
                {
                    "type": "ip_rotation",
                    "target_component": "rate_limiter",
                    "probability": 0.8
                },
                {
                    "type": "user_agent_rotation",
                    "target_component": "waf",
                    "probability": 0.6
                }
            ],
            duration_seconds=20,
            expected_behaviors=["attack_detection", "ip_blocking", "rate_limiting"]
        )
        
        # 8. Cascade Failure Scenario
        self.scenarios["cascade_failure"] = TestScenario(
            id="cascade_failure",
            name="Cascade Failure Simulation",
            description="Tests system resilience to cascading failures",
            target_components=["all"],
            load_pattern={
                "request_count": 2000,
                "requests_per_second": 40,
                "source_ip_pattern": "192.168.100.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Cascade/1.0)",
                "payload_template": {
                    "username": "cascade_user_{index}",
                    "password": "cascade_password",
                    "action": "authenticate"
                },
                "expected_result": "service_degraded"
            },
            anomaly_injection=[
                {
                    "type": "component_failure",
                    "target_component": "database",
                    "duration_ms": 5000,
                    "probability": 0.3
                },
                {
                    "type": "network_partition",
                    "target_component": "session_manager",
                    "duration_ms": 3000,
                    "probability": 0.2
                }
            ],
            duration_seconds=50,
            expected_behaviors=["graceful_degradation", "circuit_breaker_activation", "recovery"]
        )
        
        # 9. Semantic Drift Scenario
        self.scenarios["semantic_drift"] = TestScenario(
            id="semantic_drift",
            name="Semantic Drift Detection",
            description="Tests detection of semantic drift between pipeline layers",
            target_components=["waf", "session_manager", "database"],
            load_pattern={
                "request_count": 800,
                "requests_per_second": 25,
                "source_ip_pattern": "10.10.10.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Drift/1.0)",
                "payload_template": {
                    "username": "drift_user_{index}",
                    "password": "drift_password",
                    "preserve_semantics": True,
                    "action": "authenticate"
                },
                "expected_result": "success"
            },
            anomaly_injection=[
                {
                    "type": "semantic_drift",
                    "target_component": "waf",
                    "drift_magnitude": 0.3,
                    "probability": 0.4
                },
                {
                    "type": "data_transformation",
                    "target_component": "session_manager",
                    "transformation_type": "normalization",
                    "probability": 0.5
                }
            ],
            duration_seconds=32,
            expected_behaviors=["drift_detection", "semantic_consistency_monitoring"]
        )
        
        # 10. Recovery Test Scenario
        self.scenarios["recovery_test"] = TestScenario(
            id="recovery_test",
            name="Recovery Capability Test",
            description="Tests system recovery after induced failures",
            target_components=["all"],
            load_pattern={
                "request_count": 1500,
                "requests_per_second": 30,
                "source_ip_pattern": "172.20.30.{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Recovery/1.0)",
                "payload_template": {
                    "username": "recovery_user_{index}",
                    "password": "recovery_password",
                    "action": "authenticate"
                },
                "expected_result": "success"
            },
            anomaly_injection=[
                {
                    "type": "temporary_failure",
                    "target_component": "database",
                    "duration_ms": 2000,
                    "probability": 0.2
                },
                {
                    "type": "service_restart",
                    "target_component": "session_manager",
                    "duration_ms": 1000,
                    "probability": 0.15
                }
            ],
            duration_seconds=50,
            expected_behaviors=["automatic_recovery", "service_restoration", "minimal_downtime"]
        )
        
        # 11. Mixed Attack Scenario
        self.scenarios["mixed_attack"] = TestScenario(
            id="mixed_attack",
            name="Mixed Attack Vectors",
            description="Combines multiple attack vectors simultaneously",
            target_components=["all"],
            load_pattern={
                "request_count": 4000,
                "requests_per_second": 80,
                "source_ip_pattern": "{mixed_ip}",
                "user_agent": "{mixed_agent}",
                "payload_template": {
                    "username": "mixed_user_{index}",
                    "password": "mixed_password",
                    "action": "mixed_attack"
                },
                "expected_result": "varied"
            },
            anomaly_injection=[
                {
                    "type": "rate_limit_pressure",
                    "target_component": "rate_limiter",
                    "probability": 0.6
                },
                {
                    "type": "session_collapse",
                    "target_component": "session_manager",
                    "probability": 0.4
                },
                {
                    "type": "normalization_stress",
                    "target_component": "waf",
                    "probability": 0.5
                },
                {
                    "type": "database_pressure",
                    "target_component": "database",
                    "probability": 0.3
                }
            ],
            duration_seconds=50,
            expected_behaviors=["comprehensive_defense", "attack_mitigation", "system_stability"]
        )
        
        # 12. Edge Case Scenario
        self.scenarios["edge_cases"] = TestScenario(
            id="edge_cases",
            name="Edge Case Testing",
            description="Tests system behavior with edge cases and boundary conditions",
            target_components=["all"],
            load_pattern={
                "request_count": 600,
                "requests_per_second": 15,
                "source_ip_pattern": "edge_case_{index}",
                "user_agent": "Mozilla/5.0 (compatible; EVENT_HORIZON-Edge/1.0)",
                "payload_template": {
                    "username": "edge_user_{index}",
                    "password": "edge_password",
                    "action": "edge_case_test"
                },
                "expected_result": "handled_gracefully"
            },
            anomaly_injection=[
                {
                    "type": "malformed_payload",
                    "target_component": "waf",
                    "probability": 0.7
                },
                {
                    "type": "extreme_values",
                    "target_component": "session_manager",
                    "probability": 0.5
                },
                {
                    "type": "boundary_conditions",
                    "target_component": "database",
                    "probability": 0.4
                }
            ],
            duration_seconds=40,
            expected_behaviors=["error_handling", "input_validation", "graceful_degradation"]
        )
    
    def get_comprehensive_suite(self) -> List[TestScenario]:
        """Get a comprehensive test suite covering all major scenarios"""
        return [
            self.scenarios["baseline_performance"],
            self.scenarios["high_load_stress"],
            self.scenarios["burst_traffic"],
            self.scenarios["session_flood"],
            self.scenarios["normalization_attack"],
            self.scenarios["database_stress"],
            self.scenarios["distributed_attack"],
            self.scenarios["cascade_failure"],
            self.scenarios["semantic_drift"],
            self.scenarios["recovery_test"]
        ]
    
    def get_security_focused_suite(self) -> List[TestScenario]:
        """Get security-focused test scenarios"""
        return [
            self.scenarios["normalization_attack"],
            self.scenarios["distributed_attack"],
            self.scenarios["mixed_attack"],
            self.scenarios["burst_traffic"],
            self.scenarios["edge_cases"]
        ]
    
    def get_performance_focused_suite(self) -> List[TestScenario]:
        """Get performance-focused test scenarios"""
        return [
            self.scenarios["baseline_performance"],
            self.scenarios["high_load_stress"],
            self.scenarios["database_stress"],
            self.scenarios["session_flood"],
            self.scenarios["recovery_test"]
        ]
    
    def get_resilience_focused_suite(self) -> List[TestScenario]:
        """Get resilience-focused test scenarios"""
        return [
            self.scenarios["cascade_failure"],
            self.scenarios["recovery_test"],
            self.scenarios["semantic_drift"],
            self.scenarios["mixed_attack"],
            self.scenarios["edge_cases"]
        ]
    
    def create_custom_scenario(self, 
                              scenario_id: str,
                              name: str,
                              description: str,
                              target_components: List[str],
                              load_pattern: Dict[str, Any],
                              anomaly_injection: List[Dict[str, Any]],
                              duration_seconds: int,
                              expected_behaviors: List[str]) -> TestScenario:
        """Create a custom scenario"""
        scenario = TestScenario(
            id=scenario_id,
            name=name,
            description=description,
            target_components=target_components,
            load_pattern=load_pattern,
            anomaly_injection=anomaly_injection,
            duration_seconds=duration_seconds,
            expected_behaviors=expected_behaviors
        )
        
        self.add_scenario(scenario)
        return scenario
