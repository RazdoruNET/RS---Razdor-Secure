"""
EVENT_HORIZON Architectural Corrections Layer

Addresses critical architectural issues identified in security review:
- Immutable event sourcing for request lineage
- Exception classification as first-class events  
- Contextual evaluation model
- Service decomposition boundaries
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Union, Callable
from enum import Enum
import structlog
from collections import defaultdict, deque

from .models import TestRequest, TestResponse, FailureEvent
from .trust_boundaries import DataContract, TrustZone, TrustBoundaryEnforcer

logger = structlog.get_logger(__name__)


class ExceptionClassification(Enum):
    """Classification of exceptions for proper handling"""
    EXPECTED_FAILURE = "expected_failure"      # Normal failure mode
    SYSTEM_DEGRADATION = "system_degradation"  # Performance degradation
    CIRCUIT_BREAKER = "circuit_breaker"      # Circuit breaker triggered
    BACKPRESSURE = "backpressure"              # Queue/backpressure issue
    TIMEOUT = "timeout"                        # Operation timeout
    VALIDATION_ERROR = "validation_error"        # Input validation failed
    INFRASTRUCTURE_ERROR = "infrastructure_error" # External system failure
    UNKNOWN_ERROR = "unknown_error"              # Unclassified error


@dataclass
class EventSnapshot:
    """Immutable snapshot of system state at a point in time"""
    snapshot_id: str
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    parent_snapshot_id: Optional[str] = None
    version: int = 1
    checksum: str = field(init=False)
    
    def __post_init__(self):
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification"""
        import hashlib
        content = f"{self.snapshot_id}:{self.timestamp}:{self.version}:{str(sorted(self.data.items()))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def verify_integrity(self) -> bool:
        """Verify snapshot integrity"""
        return self.checksum == self._calculate_checksum()


@dataclass
class ExceptionEvent:
    """First-class exception event for telemetry"""
    exception_id: str
    timestamp: float
    classification: ExceptionClassification
    severity: float  # 0.0 to 1.0
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_action: Optional[str] = None
    isolated_component: Optional[str] = None
    cascade_depth: int = 0


class ServiceDecompositionBoundary:
    """Boundary between different service responsibilities"""
    
    def __init__(self, boundary_name: str):
        self.boundary_name = boundary_name
        self.input_contracts: Dict[str, DataContract] = {}
        self.output_contracts: Dict[str, DataContract] = {}
        self.telemetry_events: List[Dict[str, Any]] = []
        self.boundary_metrics: Dict[str, Any] = defaultdict(float)
    
    def create_input_contract(self, request_id: str, data: Dict[str, Any]) -> DataContract:
        """Create immutable input contract"""
        contract = DataContract(
            data=data,
            trust_zone=TrustZone.SYNTHETIC_INPUT,
            contract_id=f"input_{self.boundary_name}_{request_id}"
        )
        self.input_contracts[request_id] = contract
        return contract
    
    def create_output_contract(self, request_id: str, data: Dict[str, Any], 
                           input_contract: DataContract) -> DataContract:
        """Create immutable output contract with lineage"""
        output_contract = DataContract(
            data=data,
            trust_zone=TrustZone.TRUSTED_TRANSFORM,
            contract_id=f"output_{self.boundary_name}_{request_id}"
        )
        
        # Add lineage metadata
        output_contract.data['_input_contract_id'] = input_contract.contract_id
        output_contract.data['_boundary_name'] = self.boundary_name
        output_contract.data['_lineage_timestamp'] = time.time()
        
        self.output_contracts[request_id] = output_contract
        return output_contract
    
    def record_telemetry_event(self, event_type: str, data: Dict[str, Any]):
        """Record telemetry event without mutating contracts"""
        telemetry_event = {
            'event_id': str(uuid.uuid4()),
            'boundary_name': self.boundary_name,
            'event_type': event_type,
            'timestamp': time.time(),
            'data': data.copy()  # Immutable copy
        }
        self.telemetry_events.append(telemetry_event)
        self.boundary_metrics[f"{event_type}_count"] += 1


class ContextualEvaluationModel:
    """Context-aware evaluation model instead of deterministic verification"""
    
    def __init__(self):
        self.evaluation_context = {
            'system_mode': 'simulation',  # simulation, testing, production
            'strictness_level': 0.7,    # 0.0 (lenient) to 1.0 (strict)
            'environmental_factors': {},
            'adaptation_history': deque(maxlen=100)
        }
        self.oracle_snapshots: List[EventSnapshot] = []
    
    def set_evaluation_context(self, **kwargs):
        """Update evaluation context"""
        for key, value in kwargs.items():
            if key in self.evaluation_context:
                self.evaluation_context[key] = value
        
        logger.info("Evaluation context updated", context=self.evaluation_context)
    
    def evaluate_result(self, result: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Context-aware result evaluation"""
        strictness = self.evaluation_context['strictness_level']
        system_mode = self.evaluation_context['system_mode']
        
        # Adapt evaluation based on context
        if system_mode == 'simulation':
            # More lenient evaluation for simulations
            adjusted_strictness = strictness * 0.7
        elif system_mode == 'testing':
            # Moderate strictness for testing
            adjusted_strictness = strictness * 0.85
        else:  # production
            # Full strictness for production
            adjusted_strictness = strictness
        
        # Create evaluation snapshot
        snapshot = EventSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="result_evaluation",
            data={
                'result': result,
                'context': context,
                'strictness_used': adjusted_strictness,
                'system_mode': system_mode
            }
        )
        self.oracle_snapshots.append(snapshot)
        
        return {
            'evaluation_result': result,
            'confidence': self._calculate_confidence(result, context, adjusted_strictness),
            'context_adjustments': {
                'strictness_adjusted': adjusted_strictness,
                'system_mode': system_mode
            },
            'recommendations': self._generate_contextual_recommendations(result, context, adjusted_strictness)
        }
    
    def _calculate_confidence(self, result: Any, context: Dict[str, Any], 
                            strictness: float) -> float:
        """Calculate confidence based on context and strictness"""
        base_confidence = 0.8
        
        # Adjust based on result characteristics
        if isinstance(result, dict) and 'error_rate' in result:
            error_rate = result['error_rate']
            if error_rate < 0.05:
                base_confidence = 0.95
            elif error_rate < 0.1:
                base_confidence = 0.85
            elif error_rate < 0.2:
                base_confidence = 0.7
            else:
                base_confidence = 0.5
        
        # Apply strictness adjustment
        adjusted_confidence = base_confidence * (1.0 - strictness * 0.3)
        
        return max(0.1, min(1.0, adjusted_confidence))
    
    def _generate_contextual_recommendations(self, result: Any, context: Dict[str, Any], 
                                       strictness: float) -> List[str]:
        """Generate context-aware recommendations"""
        recommendations = []
        
        if strictness > 0.8:
            recommendations.append("Consider reducing strictness for simulation mode")
        
        if isinstance(result, dict):
            if result.get('error_rate', 0) > 0.15:
                recommendations.append("High error rate detected - review system configuration")
            
            if result.get('semantic_drift_detected', False):
                recommendations.append("Semantic drift detected - review data transformation logic")
        
        return recommendations
    
    def create_evaluation_snapshot(self, snapshot_data: Dict[str, Any]) -> EventSnapshot:
        """Create immutable evaluation snapshot"""
        snapshot = EventSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="evaluation_snapshot",
            data=snapshot_data
        )
        self.oracle_snapshots.append(snapshot)
        return snapshot


class ArchitecturalCorrectionLayer:
    """Main correction layer addressing all identified architectural issues"""
    
    def __init__(self):
        self.trust_enforcer = TrustBoundaryEnforcer()
        self.evaluation_model = ContextualEvaluationModel()
        self.service_boundaries: Dict[str, ServiceDecompositionBoundary] = {}
        self.event_snapshots: List[EventSnapshot] = []
        self.exception_events: List[ExceptionEvent] = []
        self.lineage_tracker: Dict[str, List[str]] = defaultdict(list)
        
        # Configure evaluation context
        self.evaluation_model.set_evaluation_context(
            system_mode='simulation',
            strictness_level=0.7
        )
        
        logger.info("Architectural correction layer initialized")
    
    def create_service_boundary(self, boundary_name: str) -> ServiceDecompositionBoundary:
        """Create service decomposition boundary"""
        boundary = ServiceDecompositionBoundary(boundary_name)
        self.service_boundaries[boundary_name] = boundary
        return boundary
    
    def process_request_with_corrections(self, 
                                    request_id: str,
                                    boundary_name: str,
                                    request_data: Dict[str, Any],
                                    processing_func: Callable) -> Dict[str, Any]:
        """Process request with all architectural corrections applied"""
        
        # Get service boundary
        boundary = self.service_boundaries.get(boundary_name)
        if not boundary:
            boundary = self.create_service_boundary(boundary_name)
        
        # Create immutable input contract
        input_contract = boundary.create_input_contract(request_id, request_data)
        
        # Track lineage
        self.lineage_tracker[request_id].append(input_contract.contract_id)
        
        # Process with exception classification
        try:
            start_time = time.time()
            result = processing_func(input_contract.get_immutable_copy())
            processing_time = time.time() - start_time
            
            # Create output contract
            output_contract = boundary.create_output_contract(
                request_id, result, input_contract
            )
            
            # Record telemetry
            boundary.record_telemetry_event("processing_success", {
                'request_id': request_id,
                'processing_time': processing_time,
                'input_contract': input_contract.contract_id,
                'output_contract': output_contract.contract_id
            })
            
            # Create evaluation snapshot
            evaluation_result = self.evaluation_model.evaluate_result(result, {
                'request_id': request_id,
                'boundary_name': boundary_name,
                'processing_time': processing_time
            })
            
            return {
                'success': True,
                'result': result,
                'input_contract': input_contract,
                'output_contract': output_contract,
                'evaluation': evaluation_result,
                'lineage': self.lineage_tracker[request_id].copy()
            }
            
        except Exception as e:
            # Classify exception
            classification = self._classify_exception(e, boundary_name)
            
            # Create exception event
            exception_event = ExceptionEvent(
                exception_id=str(uuid.uuid4()),
                timestamp=time.time(),
                classification=classification,
                severity=self._calculate_exception_severity(e, classification),
                context={
                    'request_id': request_id,
                    'boundary_name': boundary_name,
                    'input_contract': input_contract.contract_id
                },
                stack_trace=str(e),
                isolated_component=boundary_name
            )
            
            self.exception_events.append(exception_event)
            
            # Record failure telemetry
            boundary.record_telemetry_event("processing_failure", {
                'request_id': request_id,
                'exception_id': exception_event.exception_id,
                'classification': classification.value,
                'severity': exception_event.severity
            })
            
            return {
                'success': False,
                'exception_event': exception_event,
                'input_contract': input_contract,
                'lineage': self.lineage_tracker[request_id].copy()
            }
    
    def _classify_exception(self, exception: Exception, boundary_name: str) -> ExceptionClassification:
        """Classify exception for proper handling"""
        exception_type = type(exception).__name__
        
        # Classification rules
        if exception_type in ['TimeoutError', 'asyncio.TimeoutError']:
            return ExceptionClassification.TIMEOUT
        elif exception_type in ['ConnectionError', 'ConnectionRefusedError']:
            return ExceptionClassification.INFRASTRUCTURE_ERROR
        elif 'validation' in str(exception).lower():
            return ExceptionClassification.VALIDATION_ERROR
        elif 'circuit' in str(exception).lower():
            return ExceptionClassification.CIRCUIT_BREAKER
        elif 'backpressure' in str(exception).lower() or 'queue' in str(exception).lower():
            return ExceptionClassification.BACKPRESSURE
        elif 'degradation' in str(exception).lower():
            return ExceptionClassification.SYSTEM_DEGRADATION
        else:
            return ExceptionClassification.UNKNOWN_ERROR
    
    def _calculate_exception_severity(self, exception: Exception, 
                                   classification: ExceptionClassification) -> float:
        """Calculate exception severity"""
        base_severity = {
            ExceptionClassification.TIMEOUT: 0.6,
            ExceptionClassification.INFRASTRUCTURE_ERROR: 0.8,
            ExceptionClassification.VALIDATION_ERROR: 0.4,
            ExceptionClassification.CIRCUIT_BREAKER: 0.7,
            ExceptionClassification.BACKPRESSURE: 0.5,
            ExceptionClassification.SYSTEM_DEGRADATION: 0.6,
            ExceptionClassification.EXPECTED_FAILURE: 0.3,
            ExceptionClassification.UNKNOWN_ERROR: 0.9
        }
        
        severity = base_severity.get(classification, 0.7)
        
        # Adjust based on exception properties
        if hasattr(exception, 'severity_override'):
            severity = exception.severity_override
        
        return max(0.0, min(1.0, severity))
    
    def create_lineage_snapshot(self, request_id: str) -> EventSnapshot:
        """Create snapshot of request lineage"""
        lineage = self.lineage_tracker.get(request_id, [])
        
        snapshot = EventSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="lineage_snapshot",
            data={
                'request_id': request_id,
                'lineage': lineage,
                'lineage_depth': len(lineage)
            }
        )
        
        self.event_snapshots.append(snapshot)
        return snapshot
    
    def get_architectural_metrics(self) -> Dict[str, Any]:
        """Get comprehensive architectural metrics"""
        return {
            'trust_boundary_violations': len(self.trust_enforcer.violations),
            'exception_classifications': {
                classification.value: len([e for e in self.exception_events 
                                       if e.classification == classification])
                for classification in ExceptionClassification
            },
            'service_boundary_metrics': {
                boundary_name: {
                    'input_contracts': len(boundary.input_contracts),
                    'output_contracts': len(boundary.output_contracts),
                    'telemetry_events': len(boundary.telemetry_events),
                    'boundary_metrics': dict(boundary.boundary_metrics)
                }
                for boundary_name, boundary in self.service_boundaries.items()
            },
            'lineage_metrics': {
                'total_lineage_entries': sum(len(lineage) for lineage in self.lineage_tracker.values()),
                'max_lineage_depth': max(len(lineage) for lineage in self.lineage_tracker.values()),
                'requests_with_lineage': len(self.lineage_tracker)
            },
            'evaluation_context': self.evaluation_model.evaluation_context,
            'snapshot_count': len(self.event_snapshots),
            'oracle_snapshots': len(self.evaluation_model.oracle_snapshots)
        }
    
    def export_audit_trail(self) -> Dict[str, Any]:
        """Export complete audit trail for external validation"""
        return {
            'event_snapshots': [
                {
                    'snapshot_id': s.snapshot_id,
                    'timestamp': s.timestamp,
                    'event_type': s.event_type,
                    'data': s.data,
                    'checksum': s.checksum,
                    'integrity_verified': s.verify_integrity()
                }
                for s in self.event_snapshots
            ],
            'exception_events': [
                {
                    'exception_id': e.exception_id,
                    'timestamp': e.timestamp,
                    'classification': e.classification.value,
                    'severity': e.severity,
                    'context': e.context,
                    'isolated_component': e.isolated_component,
                    'cascade_depth': e.cascade_depth
                }
                for e in self.exception_events
            ],
            'trust_boundary_audit': self.trust_enforcer.get_audit_trail(),
            'service_boundary_audit': {
                boundary_name: {
                    'input_contracts': {
                        contract_id: {
                            'trust_zone': contract.trust_zone.value,
                            'created_at': contract.created_at,
                            'integrity': contract.verify_integrity()
                        }
                        for contract_id, contract in boundary.input_contracts.items()
                    },
                    'output_contracts': {
                        contract_id: {
                            'trust_zone': contract.trust_zone.value,
                            'created_at': contract.created_at,
                            'integrity': contract.verify_integrity()
                        }
                        for contract_id, contract in boundary.output_contracts.items()
                    },
                    'telemetry_events': boundary.telemetry_events
                }
                for boundary_name, boundary in self.service_boundaries.items()
            },
            'lineage_tracking': dict(self.lineage_tracker),
            'evaluation_context': self.evaluation_model.evaluation_context,
            'architectural_metrics': self.get_architectural_metrics()
        }
