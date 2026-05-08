"""
EVENT_HORIZON Core Data Models

Defines the data structures used throughout the framework for
modeling authentication pipeline components, test scenarios,
and assessment results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time
import uuid


class AuthComponentType(Enum):
    """Types of authentication pipeline components"""
    RATE_LIMITER = "rate_limiter"
    SESSION_MANAGER = "session_manager"
    REVERSE_PROXY = "reverse_proxy"
    WAF = "waf"
    LOAD_BALANCER = "load_balancer"
    DATABASE = "database"
    IDENTITY_FEDERATION = "identity_federation"


class FailureType(Enum):
    """Types of failures that can occur in auth pipeline"""
    SEMANTIC_DRIFT = "semantic_drift"
    SESSION_DESYNC = "session_desync"
    NORMALIZATION_LOSS = "normalization_loss"
    RATE_LIMIT_BYPASS = "rate_limit_bypass"
    CONNECTION_EXHAUSTION = "connection_exhaustion"
    TOKEN_MISMATCH = "token_mismatch"
    PROXY_MUTATION = "proxy_mutation"


class TestPhase(Enum):
    """Phases of resilience testing"""
    BASELINE = "baseline"
    STRESS = "stress"
    DEGRADATION = "degradation"
    RECOVERY = "recovery"


@dataclass
class AuthComponent:
    """Represents an authentication pipeline component"""
    id: str
    name: str
    type: AuthComponentType
    endpoint: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class TestRequest:
    """Represents a synthetic authentication request"""
    id: str
    timestamp: float
    source_ip: str
    user_agent: str
    auth_token: Optional[str]
    session_id: Optional[str]
    payload: Dict[str, Any]
    expected_result: str
    anomaly_flags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class TestResponse:
    """Represents the response from an auth component"""
    request_id: str
    component_id: str
    timestamp: float
    status_code: int
    response_time: float
    payload: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class SemanticDriftEvent:
    """Records semantic drift between pipeline layers"""
    request_id: str
    source_component: str
    target_component: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    drift_magnitude: float
    drift_type: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class FailureEvent:
    """Records a failure event in the auth pipeline"""
    id: str
    component_id: str
    failure_type: FailureType
    severity: float  # 0.0 to 1.0
    description: str
    affected_requests: List[str]
    timestamp: float = field(default_factory=time.time)
    recovery_time: Optional[float] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class ComponentMetrics:
    """Metrics collected for each component during testing"""
    component_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    error_rate: float
    throughput: float  # requests per second
    semantic_drift_events: List[SemanticDriftEvent]
    failure_events: List[FailureEvent]


@dataclass
class TestScenario:
    """Defines a test scenario for resilience assessment"""
    id: str
    name: str
    description: str
    target_components: List[str]
    load_pattern: Dict[str, Any]
    anomaly_injection: List[Dict[str, Any]]
    duration_seconds: int
    expected_behaviors: List[str]
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class ResilienceScore:
    """Represents the resilience score for a component or system"""
    component_id: Optional[str]  # None for system-wide score
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    breakdown: Dict[str, float]  # sub-scores by category
    timestamp: float = field(default_factory=time.time)


@dataclass
class AssessmentResults:
    """Complete results from a resilience assessment"""
    test_id: str
    scenario_id: str
    start_time: float
    end_time: float
    component_metrics: Dict[str, ComponentMetrics]
    system_metrics: ComponentMetrics
    resilience_scores: List[ResilienceScore]
    failure_topology: Dict[str, Any]
    auth_pipeline_breakpoints: List[str]
    normalization_loss_report: Dict[str, Any]
    session_integrity_heatmap: Dict[str, Any]
    
    @property
    def overall_resilience_score(self) -> float:
        """Get the overall system resilience score"""
        system_scores = [s for s in self.resilience_scores if s.component_id is None]
        return system_scores[0].score if system_scores else 0.0
    
    def __post_init__(self):
        if not self.test_id:
            self.test_id = str(uuid.uuid4())
