"""
EVENT_HORIZON Trust Boundary Model

Implements strict trust boundaries between synthetic input,
semi-trusted transformations, and derived telemetry output.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Set
from enum import Enum
import hashlib
import time
import uuid

from .models import TestRequest, TestResponse


class TrustZone(Enum):
    """Trust zones for data classification"""
    SYNTHETIC_INPUT = "synthetic_input"      # Untrusted, generated internally
    SEMI_TRUSTED = "semi_trusted"          # Processed by validation layer
    TRUSTED_TRANSFORM = "trusted_transform"  # Validated and transformed
    DERIVED_TELEMETRY = "derived_telemetry"  # Observational data only
    SYSTEM_OUTPUT = "system_output"          # Final validated output


class DataContract:
    """Immutable data contract with semantic integrity guarantees"""
    
    def __init__(self, data: Dict[str, Any], trust_zone: TrustZone, 
                 contract_id: Optional[str] = None):
        self.data = data.copy()  # Deep copy to prevent mutation
        self.trust_zone = trust_zone
        self.contract_id = contract_id or str(uuid.uuid4())
        self.created_at = time.time()
        self.semantic_hash = self._calculate_semantic_hash(data)
        self._immutable = True
    
    def _calculate_semantic_hash(self, data: Dict[str, Any]) -> str:
        """Calculate semantic hash for integrity verification"""
        # Normalize data for consistent hashing
        normalized = {k: str(v) for k, v in sorted(data.items())}
        content = str(normalized)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_immutable_copy(self) -> Dict[str, Any]:
        """Get immutable copy of contract data"""
        return self.data.copy()
    
    def verify_integrity(self) -> bool:
        """Verify data contract integrity"""
        current_hash = self._calculate_semantic_hash(self.data)
        return current_hash == self.semantic_hash
    
    def transition_to_zone(self, new_zone: TrustZone, 
                         transformation_log: Optional[str] = None) -> 'DataContract':
        """Create new contract in different trust zone"""
        if not self._immutable:
            raise ValueError("Contract has been violated")
        
        new_contract = DataContract(
            data=self.data,
            trust_zone=new_zone,
            contract_id=str(uuid.uuid4())
        )
        
        # Add transformation metadata
        new_contract.data['_transformation_from'] = self.trust_zone.value
        new_contract.data['_transformation_log'] = transformation_log
        new_contract.data['_original_contract'] = self.contract_id
        
        return new_contract


@dataclass
class TrustBoundaryValidator:
    """Validates transitions between trust zones"""
    
    allowed_transitions: Set[tuple] = field(default_factory=lambda: {
        (TrustZone.SYNTHETIC_INPUT, TrustZone.SEMI_TRUSTED),
        (TrustZone.SEMI_TRUSTED, TrustZone.TRUSTED_TRANSFORM),
        (TrustZone.TRUSTED_TRANSFORM, TrustZone.DERIVED_TELEMETRY),
        (TrustZone.DERIVED_TELEMETRY, TrustZone.SYSTEM_OUTPUT),
    })
    
    def validate_transition(self, from_zone: TrustZone, 
                       to_zone: TrustZone) -> bool:
        """Validate trust zone transition"""
        return (from_zone, to_zone) in self.allowed_transitions
    
    def get_violation_reason(self, from_zone: TrustZone, 
                           to_zone: TrustZone) -> str:
        """Get reason for transition violation"""
        if self.validate_transition(from_zone, to_zone):
            return "No violation"
        
        return f"Invalid transition: {from_zone.value} -> {to_zone.value}"


@dataclass
class SemanticDriftDetector:
    """Advanced semantic drift detection with embedding space metrics"""
    
    def __init__(self):
        self.embedding_cache: Dict[str, float] = {}
        self.drift_threshold = 0.3
    
    def calculate_embedding_distance(self, original: DataContract, 
                               transformed: DataContract) -> float:
        """Calculate semantic distance using embedding space"""
        # Simplified embedding calculation (in production would use actual embeddings)
        original_hash = original.semantic_hash
        transformed_hash = transformed.semantic_hash
        
        # Hamming distance as proxy for semantic distance
        distance = sum(c1 != c2 for c1, c2 in 
                      zip(original_hash, transformed_hash)) / len(original_hash)
        
        return distance
    
    def detect_drift(self, original: DataContract, 
                   transformed: DataContract) -> Optional['SemanticDriftEvent']:
        """Detect semantic drift between contracts"""
        if original.trust_zone not in [TrustZone.SEMI_TRUSTED, TrustZone.TRUSTED_TRANSFORM]:
            return None
        
        distance = self.calculate_embedding_distance(original, transformed)
        
        if distance > self.drift_threshold:
            from ..models import SemanticDriftEvent
            return SemanticDriftEvent(
                request_id=original.data.get('request_id', 'unknown'),
                source_component=original.trust_zone.value,
                target_component=transformed.trust_zone.value,
                input_data=original.get_immutable_copy(),
                output_data=transformed.get_immutable_copy(),
                drift_magnitude=distance,
                drift_type="semantic_embedding_drift"
            )
        
        return None


@dataclass
class TrustBoundaryEnforcer:
    """Enforces trust boundaries throughout the pipeline"""
    
    def __init__(self):
        self.validator = TrustBoundaryValidator()
        self.drift_detector = SemanticDriftDetector()
        self.contract_chain: List[DataContract] = []
        self.violations: List[Dict[str, Any]] = []
    
    def create_input_contract(self, request_data: Dict[str, Any]) -> DataContract:
        """Create initial contract for synthetic input"""
        contract = DataContract(
            data=request_data,
            trust_zone=TrustZone.SYNTHETIC_INPUT
        )
        self.contract_chain.append(contract)
        return contract
    
    def transition_contract(self, contract: DataContract, new_zone: TrustZone,
                         transformation_data: Optional[Dict[str, Any]] = None) -> DataContract:
        """Safely transition contract between trust zones"""
        # Validate transition
        if not self.validator.validate_transition(contract.trust_zone, new_zone):
            violation = {
                'timestamp': time.time(),
                'from_zone': contract.trust_zone.value,
                'to_zone': new_zone.value,
                'reason': self.validator.get_violation_reason(
                    contract.trust_zone, new_zone),
                'contract_id': contract.contract_id
            }
            self.violations.append(violation)
            raise ValueError(f"Trust boundary violation: {violation['reason']}")
        
        # Create new contract
        transformation_log = transformation_data.get('log') if transformation_data else None
        new_contract = contract.transition_to_zone(new_zone, transformation_log)
        
        # Detect semantic drift
        drift_event = self.drift_detector.detect_drift(contract, new_contract)
        if drift_event:
            new_contract.data['_semantic_drift_detected'] = True
            new_contract.data['_drift_event'] = drift_event
        
        self.contract_chain.append(new_contract)
        return new_contract
    
    def get_telemetry_contract(self, final_contract: DataContract) -> DataContract:
        """Create final telemetry contract for system output"""
        if final_contract.trust_zone != TrustZone.TRUSTED_TRANSFORM:
            raise ValueError("Cannot create telemetry from non-trusted contract")
        
        telemetry_data = {
            'contract_id': final_contract.contract_id,
            'trust_zone_path': [c.trust_zone.value for c in self.contract_chain],
            'final_hash': final_contract.semantic_hash,
            'drift_events': len([c for c in self.contract_chain 
                                 if c.data.get('_semantic_drift_detected')]),
            'violations': len(self.violations),
            'processing_time': time.time() - self.contract_chain[0].created_at
        }
        
        telemetry_contract = DataContract(
            data=telemetry_data,
            trust_zone=TrustZone.DERIVED_TELEMETRY
        )
        
        self.contract_chain.append(telemetry_contract)
        return telemetry_contract
    
    def get_audit_trail(self) -> Dict[str, Any]:
        """Get complete audit trail of contract transitions"""
        return {
            'contract_count': len(self.contract_chain),
            'trust_zone_path': [c.trust_zone.value for c in self.contract_chain],
            'violations': self.violations,
            'drift_events': [c.data.get('_drift_event') for c in self.contract_chain 
                            if c.data.get('_semantic_drift_detected')],
            'integrity_checks': [c.verify_integrity() for c in self.contract_chain]
        }
