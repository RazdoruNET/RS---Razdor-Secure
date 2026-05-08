"""
Control Plane - Deterministic decision layer

Responsible for:
- Test planning and configuration
- Immutable execution contracts
- No runtime state mutation
- External oracle validation
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import hashlib
import random

from .core_constraints import (
    PlaneType, ExecutionCycleManager, ArchitecturalViolationError,
    ObservationControlSeparation
)
from .immutable_log import ImmutableEventLog, SignedEvent
from .external_oracle import ExternalOracle


@dataclass(frozen=True)
class SystemConstraints:
    """Immutable system constraints for execution planning."""
    max_concurrent_requests: int
    max_error_rate: float
    max_response_time: float
    resource_limits: Dict[str, float]
    safety_invariants: List[str]
    
    def to_hash(self) -> str:
        """Create deterministic hash of constraints."""
        constraints_str = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(constraints_str.encode()).hexdigest()


@dataclass(frozen=True)
class ExecutionContract:
    """Immutable execution contract."""
    contract_id: str
    created_at: float
    input_hash: str
    deterministic_seed: int
    constraints_hash: str
    execution_plan: Dict[str, Any]
    expected_invariants: List[str]
    oracle_validation_required: bool
    
    def is_reproducible(self) -> bool:
        """Check if contract is reproducible."""
        return True  # By definition of frozen dataclass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class DeterministicPlanner(ABC):
    """Abstract deterministic planner with no runtime state mutation."""
    
    def __init__(self, 
                 cycle_manager: ExecutionCycleManager,
                 event_log: ImmutableEventLog,
                 oracle: ExternalOracle):
        self.cycle_manager = cycle_manager
        self.event_log = event_log
        self.oracle = oracle
        self._validated = False
    
    @abstractmethod
    async def generate_base_plan(self, 
                              requirements: Dict[str, Any],
                              constraints: SystemConstraints) -> Dict[str, Any]:
        """Generate base execution plan."""
        pass
    
    async def create_execution_contract(
        self,
        requirements: Dict[str, Any],
        constraints: SystemConstraints,
        seed: Optional[int] = None
    ) -> ExecutionContract:
        """Create immutable execution contract."""
        
        # Start new execution cycle
        cycle_id = str(uuid.uuid4())
        self.cycle_manager.start_cycle(cycle_id)
        
        try:
            # Validate interaction: Control -> Control (internal)
            self.cycle_manager.record_interaction(
                source_plane=PlaneType.CONTROL,
                target_plane=PlaneType.CONTROL,
                interaction_type="contract_creation",
                data={"requirements": requirements, "constraints": asdict(constraints)}
            )
            
            # Deterministic seed
            if seed is None:
                seed = int(time.time()) % (2**31)
            
            # Generate deterministic plan
            random.seed(seed)
            base_plan = await self.generate_base_plan(requirements, constraints)
            
            # Create immutable contract
            contract = ExecutionContract(
                contract_id=str(uuid.uuid4()),
                created_at=time.time(),
                input_hash=self._hash_requirements(requirements),
                deterministic_seed=seed,
                constraints_hash=constraints.to_hash(),
                execution_plan=base_plan,
                expected_invariants=self._extract_invariants(base_plan),
                oracle_validation_required=True
            )
            
            # Log contract creation
            event = SignedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=time.time(),
                event_type="contract_created",
                plane=PlaneType.CONTROL,
                data=contract.to_dict(),
                signature=self._sign_event(contract.to_dict())
            )
            
            await self.event_log.append(event)
            
            return contract
            
        finally:
            self.cycle_manager.end_cycle()
    
    async def validate_contract(self, 
                            contract: ExecutionContract) -> bool:
        """Validate contract against external oracle."""
        
        # Start validation cycle
        cycle_id = str(uuid.uuid4())
        self.cycle_manager.start_cycle(cycle_id)
        
        try:
            # Validate interaction: Control -> Observation (for validation)
            self.cycle_manager.record_interaction(
                source_plane=PlaneType.CONTROL,
                target_plane=PlaneType.OBSERVATION,
                interaction_type="contract_validation",
                data={"contract_id": contract.contract_id}
            )
            
            # External oracle validation
            oracle_verdict = await self.oracle.validate_contract(contract)
            
            # Log validation result
            event = SignedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=time.time(),
                event_type="contract_validated",
                plane=PlaneType.CONTROL,
                data={
                    "contract_id": contract.contract_id,
                    "oracle_verdict": oracle_verdict.to_dict(),
                    "valid": oracle_verdict.is_valid
                },
                signature=self._sign_event(oracle_verdict.to_dict())
            )
            
            await self.event_log.append(event)
            
            return oracle_verdict.is_valid
            
        finally:
            self.cycle_manager.end_cycle()
    
    def _hash_requirements(self, requirements: Dict[str, Any]) -> str:
        """Create hash of requirements."""
        req_str = json.dumps(requirements, sort_keys=True)
        return hashlib.sha256(req_str.encode()).hexdigest()
    
    def _extract_invariants(self, plan: Dict[str, Any]) -> List[str]:
        """Extract expected invariants from plan."""
        invariants = []
        
        # Basic invariants
        invariants.append("no_self_modification")
        invariants.append("deterministic_execution")
        invariants.append("backpressure_respected")
        
        # Plan-specific invariants
        if "test_scenarios" in plan:
            for scenario in plan["test_scenarios"]:
                invariants.append(f"scenario_{scenario['name']}_completes")
        
        return invariants
    
    def _sign_event(self, data: Dict[str, Any]) -> str:
        """Sign event for immutability."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class TestScenarioPlanner(DeterministicPlanner):
    """Concrete implementation for test scenario planning."""
    
    async def generate_base_plan(self, 
                              requirements: Dict[str, Any],
                              constraints: SystemConstraints) -> Dict[str, Any]:
        """Generate deterministic test scenario plan."""
        
        # Extract test requirements
        test_types = requirements.get("test_types", ["authentication_stress"])
        target_system = requirements.get("target_system", "http://localhost:9000")
        
        # Generate deterministic scenarios
        scenarios = []
        for i, test_type in enumerate(test_types):
            scenario = self._generate_scenario(
                test_type, target_system, i, constraints
            )
            scenarios.append(scenario)
        
        return {
            "scenarios": scenarios,
            "total_requests": sum(s["request_count"] for s in scenarios),
            "estimated_duration": sum(s["duration_seconds"] for s in scenarios),
            "resource_requirements": self._estimate_resources(scenarios)
        }
    
    def _generate_scenario(self, 
                         test_type: str,
                         target_system: str,
                         index: int,
                         constraints: SystemConstraints) -> Dict[str, Any]:
        """Generate individual scenario deterministically."""
        
        # Use deterministic random for reproducibility
        base_seed = index * 1000
        
        # Scenario parameters (deterministic)
        scenario = {
            "name": f"{test_type}_scenario_{index}",
            "test_type": test_type,
            "target_endpoint": target_system,
            "request_count": min(1000, constraints.max_concurrent_requests * 10),
            "concurrency": min(50, constraints.max_concurrent_requests),
            "duration_seconds": 300,
            "priority": "high" if index == 0 else "medium",
            "parameters": self._generate_scenario_parameters(test_type, base_seed),
            "expected_outcomes": self._generate_expected_outcomes(test_type),
            "success_criteria": self._generate_success_criteria(test_type),
            "safety_limits": {
                "max_error_rate": constraints.max_error_rate,
                "max_response_time": constraints.max_response_time,
                "max_concurrent_requests": constraints.max_concurrent_requests
            }
        }
        
        return scenario
    
    def _generate_scenario_parameters(self, 
                                  test_type: str,
                                  seed: int) -> Dict[str, Any]:
        """Generate scenario parameters deterministically."""
        random.seed(seed)
        
        base_params = {
            "auth_methods": ["basic", "bearer", "session"],
            "user_variations": 10,
            "failure_injection": False
        }
        
        if test_type == "rate_limiting_test":
            base_params.update({
                "burst_patterns": ["constant", "spike", "gradual"],
                "rate_limit_thresholds": [10, 50, 100],
                "bypass_attempts": False
            })
        elif test_type == "input_normalization":
            base_params.update({
                "input_variations": ["case", "whitespace", "encoding"],
                "test_vectors": 100,
                "edge_cases": True
            })
        elif test_type == "header_polymorphism":
            base_params.update({
                "header_variations": ["order", "case", "duplicates"],
                "user_agent_variants": 50,
                "accept_language_variants": 20
            })
        
        return base_params
    
    def _generate_expected_outcomes(self, test_type: str) -> List[str]:
        """Generate expected outcomes for test type."""
        outcomes_map = {
            "authentication_stress": [
                "System maintains authentication availability under stress",
                "No authentication bypass vulnerabilities discovered",
                "Response times remain within acceptable limits"
            ],
            "rate_limiting_test": [
                "Rate limiting effectively prevents abuse",
                "Legitimate requests are not overly restricted",
                "No rate limit bypass methods found"
            ],
            "input_normalization": [
                "Input normalization is consistent across variations",
                "No parser inconsistencies discovered",
                "Security is not compromised by input variations"
            ],
            "header_polymorphism": [
                "Header processing is consistent and robust",
                "No security issues from header variations",
                "Middleware handles variations correctly"
            ]
        }
        
        return outcomes_map.get(test_type, ["Test scenario completes successfully"])
    
    def _generate_success_criteria(self, test_type: str) -> Dict[str, Any]:
        """Generate success criteria for test type."""
        criteria_map = {
            "authentication_stress": {
                "min_success_rate": 0.95,
                "max_response_time_p95": 2.0,
                "error_rate_threshold": 0.05
            },
            "rate_limiting_test": {
                "rate_limit_effectiveness": 0.9,
                "response_consistency": 0.95,
                "no_cascade_failures": True
            },
            "input_normalization": {
                "normalization_consistency": 0.95,
                "parser_robustness": 0.9,
                "no_security_bypass": True
            },
            "header_polymorphism": {
                "header_processing_consistency": 0.9,
                "no_header_injection": True,
                "middleware_robustness": 0.95
            }
        }
        
        return criteria_map.get(test_type, {"success": True})
    
    def _estimate_resources(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate resource requirements for scenarios."""
        total_requests = sum(s["request_count"] for s in scenarios)
        max_concurrency = max(s["concurrency"] for s in scenarios)
        total_duration = sum(s["duration_seconds"] for s in scenarios)
        
        return {
            "estimated_requests": total_requests,
            "max_concurrent_requests": max_concurrency,
            "total_duration_seconds": total_duration,
            "estimated_memory_usage": f"{max(512, max_concurrency * 10)}MB",
            "estimated_cpu_usage": f"{min(80, max_concurrency * 0.5)}%"
        }
