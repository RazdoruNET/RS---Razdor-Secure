"""
Core Architectural Constraints for EVENT_HORIZON Framework

These constraints define the fundamental separation between planes
to prevent feedback loops and ensure system safety.
"""

from abc import ABC, abstractmethod
from typing import Protocol
from dataclasses import dataclass
from enum import Enum
import time


class PlaneType(Enum):
    """System plane types."""
    CONTROL = "control"
    DATA = "data"
    OBSERVATION = "observation"


@dataclass(frozen=True)
class ArchitecturalConstraint:
    """Immutable architectural constraint."""
    constraint_id: str
    description: str
    plane_type: PlaneType
    violation_severity: str
    validator: callable


class ObservationControlSeparation:
    """
    FUNDAMENTAL CONSTRAINT: Observation Plane CANNOT influence Control Plane
    in the same execution cycle.
    
    This prevents:
    - Real-time telemetry feedback loops
    - Observation-induced control bias
    - Indirect optimization through metrics
    """
    
    CONSTRAINT_ID = "OBS-CTRL-SEP-001"
    
    @staticmethod
    def validate_interaction(
        source_plane: PlaneType,
        target_plane: PlaneType,
        execution_cycle_id: str
    ) -> bool:
        """
        Validates that Observation Plane cannot influence Control Plane
        within the same execution cycle.
        """
        
        # CRITICAL: Observation -> Control in same cycle = FORBIDDEN
        if (source_plane == PlaneType.OBSERVATION and 
            target_plane == PlaneType.CONTROL and
            execution_cycle_id is not None):
            return False
        
        # Control -> Data (allowed)
        if (source_plane == PlaneType.CONTROL and 
            target_plane == PlaneType.DATA):
            return True
        
        # Data -> Observation (allowed)
        if (source_plane == PlaneType.DATA and 
            target_plane == PlaneType.OBSERVATION):
            return True
        
        # Control -> Observation (allowed - for contract validation)
        if (source_plane == PlaneType.CONTROL and 
            target_plane == PlaneType.OBSERVATION):
            return True
        
        return False


class ExecutionCycleManager:
    """
    Manages execution cycles to enforce architectural constraints.
    """
    
    def __init__(self):
        self.current_cycle = None
        self.cycle_history = []
        self.constraint_violations = []
    
    def start_cycle(self, cycle_id: str) -> str:
        """Start a new execution cycle."""
        self.current_cycle = {
            'cycle_id': cycle_id,
            'start_time': time.time(),
            'interactions': [],
            'constraints_applied': []
        }
        return cycle_id
    
    def record_interaction(
        self,
        source_plane: PlaneType,
        target_plane: PlaneType,
        interaction_type: str,
        data: dict = None
    ) -> bool:
        """Record and validate plane interaction."""
        
        if not self.current_cycle:
            raise RuntimeError("No active execution cycle")
        
        # Validate against core constraint
        is_valid = ObservationControlSeparation.validate_interaction(
            source_plane, target_plane, self.current_cycle['cycle_id']
        )
        
        interaction = {
            'timestamp': time.time(),
            'source_plane': source_plane,
            'target_plane': target_plane,
            'interaction_type': interaction_type,
            'data': data,
            'valid': is_valid
        }
        
        self.current_cycle['interactions'].append(interaction)
        
        if not is_valid:
            violation = {
                'cycle_id': self.current_cycle['cycle_id'],
                'timestamp': time.time(),
                'constraint_id': ObservationControlSeparation.CONSTRAINT_ID,
                'violation': f"{source_plane.value} -> {target_plane.value} in same cycle",
                'interaction': interaction
            }
            self.constraint_violations.append(violation)
            
            # CRITICAL: Immediately block the interaction
            raise ArchitecturalViolationError(
                f"CONSTRAINT VIOLATION: {violation['violation']}"
            )
        
        return is_valid
    
    def end_cycle(self) -> dict:
        """End current execution cycle and return summary."""
        if not self.current_cycle:
            raise RuntimeError("No active execution cycle")
        
        self.current_cycle['end_time'] = time.time()
        self.current_cycle['duration'] = (
            self.current_cycle['end_time'] - self.current_cycle['start_time']
        )
        
        cycle_summary = self.current_cycle.copy()
        self.cycle_history.append(cycle_summary)
        self.current_cycle = None
        
        return cycle_summary


class ArchitecturalViolationError(Exception):
    """Raised when architectural constraints are violated."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"ARCHITECTURAL VIOLATION: {message}")


class PlaneInterface(Protocol):
    """Protocol defining plane interface boundaries."""
    
    def get_plane_type(self) -> PlaneType:
        """Return the plane type."""
        ...
    
    def can_interact_with(self, target_plane: PlaneType) -> bool:
        """Check if interaction is allowed."""
        ...


# CORE ARCHITECTURAL INVARIANTS
CORE_INVARIANTS = [
    ArchitecturalConstraint(
        constraint_id="INV-001",
        description="Observation Plane cannot influence Control Plane in same execution cycle",
        plane_type=PlaneType.OBSERVATION,
        violation_severity="CRITICAL",
        validator=ObservationControlSeparation.validate_interaction
    ),
    
    ArchitecturalConstraint(
        constraint_id="INV-002",
        description="Control Plane decisions must be deterministic and reproducible",
        plane_type=PlaneType.CONTROL,
        violation_severity="HIGH",
        validator=lambda: True  # Implementation needed
    ),
    
    ArchitecturalConstraint(
        constraint_id="INV-003",
        description="Data Plane must be stateless or minimally stateful",
        plane_type=PlaneType.DATA,
        violation_severity="MEDIUM",
        validator=lambda: True  # Implementation needed
    ),
    
    ArchitecturalConstraint(
        constraint_id="INV-004",
        description="All plane interactions must be logged and validated",
        plane_type=None,  # Applies to all
        violation_severity="HIGH",
        validator=lambda: True  # Implementation needed
    )
]
