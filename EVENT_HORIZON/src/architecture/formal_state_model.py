"""
Formal System State Model with Immutable Boundaries

Implements the core architectural fix for mixed trust domains
by creating a formal, immutable state model with strict domain separation.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from abc import ABC, abstractmethod

from .core_constraints import (
    PlaneType, ExecutionCycleManager, ArchitecturalViolationError
)


class DomainType(Enum):
    """System domains with strict separation."""
    GENERATION = "generation"      # Input mutation and traffic generation
    EXECUTION = "execution"        # Request execution only
    OBSERVATION = "observation"      # Read-only monitoring
    PLANNING = "planning"          # Deterministic planning
    VALIDATION = "validation"        # External oracle validation


class StateTransition(Enum):
    """Types of state transitions."""
    GENERATE = "generate"
    EXECUTE = "execute"
    OBSERVE = "observe"
    PLAN = "plan"
    VALIDATE = "validate"


@dataclass(frozen=True)
class ResourceCost:
    """Cost model for resource consumption."""
    cpu_cycles: int
    memory_bytes: int
    network_bytes: int
    time_units: float
    io_operations: int
    
    def __add__(self, other: 'ResourceCost') -> 'ResourceCost':
        return ResourceCost(
            cpu_cycles=self.cpu_cycles + other.cpu_cycles,
            memory_bytes=self.memory_bytes + other.memory_bytes,
            network_bytes=self.network_bytes + other.network_bytes,
            time_units=self.time_units + other.time_units,
            io_operations=self.io_operations + other.io_operations
        )
    
    def within_budget(self, budget: 'ResourceBudget') -> bool:
        """Check if cost is within budget."""
        return (self.cpu_cycles <= budget.max_cpu_cycles and
                self.memory_bytes <= budget.max_memory_bytes and
                self.network_bytes <= budget.max_network_bytes and
                self.time_units <= budget.max_time_units and
                self.io_operations <= budget.max_io_operations)


@dataclass(frozen=True)
class ResourceBudget:
    """Immutable resource budget."""
    budget_id: str
    max_cpu_cycles: int
    max_memory_bytes: int
    max_network_bytes: int
    max_time_units: float
    max_io_operations: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'budget_id': self.budget_id,
            'max_cpu_cycles': self.max_cpu_cycles,
            'max_memory_bytes': self.max_memory_bytes,
            'max_network_bytes': self.max_network_bytes,
            'max_time_units': self.max_time_units,
            'max_io_operations': self.max_io_operations
        }


@dataclass(frozen=True)
class SystemInvariant:
    """Formal system invariant."""
    invariant_id: str
    description: str
    domain: DomainType
    validator: Callable[['SystemState'], bool]
    violation_severity: str
    created_at: float = field(default_factory=time.time)
    
    def validate(self, state: 'SystemState') -> bool:
        """Validate invariant against system state."""
        try:
            return self.validator(state)
        except Exception:
            return False


@dataclass(frozen=True)
class StateTransition:
    """Immutable state transition record."""
    transition_id: str
    from_state_hash: str
    to_state_hash: str
    transition_type: StateTransition
    domain: DomainType
    timestamp: float
    resource_cost: ResourceCost
    actor_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    signature: str = field(init=False)
    
    def __post_init__(self):
        if not self.signature:
            content = json.dumps({
                'transition_id': self.transition_id,
                'from_state_hash': self.from_state_hash,
                'to_state_hash': self.to_state_hash,
                'transition_type': self.transition_type.value,
                'domain': self.domain.value,
                'timestamp': self.timestamp,
                'resource_cost': self.resource_cost.__dict__,
                'actor_id': self.actor_id,
                'data': self.data
            }, sort_keys=True)
            object.__setattr__(self, 'signature', hashlib.sha256(content.encode()).hexdigest())


@dataclass(frozen=True)
class SystemState:
    """Immutable system state snapshot."""
    state_hash: str
    timestamp: float
    domain_states: Dict[DomainType, Dict[str, Any]]
    resource_usage: ResourceCost
    active_transitions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    
    def get_domain_state(self, domain: DomainType) -> Dict[str, Any]:
        """Get state for specific domain."""
        return self.domain_states.get(domain, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'state_hash': self.state_hash,
            'timestamp': self.timestamp,
            'domain_states': {k.value: v for k, v in self.domain_states.items()},
            'resource_usage': self.resource_usage.__dict__,
            'active_transitions': self.active_transitions,
            'invariants': self.invariants
        }


class FormalStateModel:
    """
    Formal state model with immutable boundaries and strict domain separation.
    
    This is the core architectural fix for mixed trust domains.
    """
    
    def __init__(self, cycle_manager: ExecutionCycleManager):
        self.cycle_manager = cycle_manager
        
        # Immutable state storage
        self.states: Dict[str, SystemState] = {}
        self.transitions: Dict[str, StateTransition] = {}
        self.invariants: Dict[str, SystemInvariant] = {}
        
        # Domain isolation
        self.domain_boundaries: Dict[DomainType, DomainBoundary] = {}
        self._initialize_domain_boundaries()
        
        # Resource budgets
        self.resource_budgets: Dict[str, ResourceBudget] = {}
        self._initialize_resource_budgets()
        
        # State history
        self.state_history: List[SystemState] = []
        
        # Current state
        self.current_state: Optional[SystemState] = None
    
    def _initialize_domain_boundaries(self):
        """Initialize strict domain boundaries."""
        self.domain_boundaries[DomainType.GENERATION] = DomainBoundary(
            allowed_operations=[StateTransition.GENERATE],
            allowed_data_types=['input_data', 'mutation_config'],
            max_data_size=1024 * 1024,  # 1MB
            read_only=False
        )
        
        self.domain_boundaries[DomainType.EXECUTION] = DomainBoundary(
            allowed_operations=[StateTransition.EXECUTE],
            allowed_data_types=['request_config', 'execution_result'],
            max_data_size=512 * 1024,  # 512KB
            read_only=False
        )
        
        self.domain_boundaries[DomainType.OBSERVATION] = DomainBoundary(
            allowed_operations=[StateTransition.OBSERVE],
            allowed_data_types=['metrics', 'events', 'traces'],
            max_data_size=2 * 1024 * 1024,  # 2MB
            read_only=True
        )
        
        self.domain_boundaries[DomainType.PLANNING] = DomainBoundary(
            allowed_operations=[StateTransition.PLAN],
            allowed_data_types=['plan_config', 'constraints', 'contracts'],
            max_data_size=256 * 1024,  # 256KB
            read_only=False
        )
        
        self.domain_boundaries[DomainType.VALIDATION] = DomainBoundary(
            allowed_operations=[StateTransition.VALIDATE],
            allowed_data_types=['oracle_response', 'validation_result'],
            max_data_size=128 * 1024,  # 128KB
            read_only=True
        )
    
    def _initialize_resource_budgets(self):
        """Initialize resource budgets."""
        self.resource_budgets['default'] = ResourceBudget(
            budget_id="default",
            max_cpu_cycles=1000000,    # 1M cycles
            max_memory_bytes=100 * 1024 * 1024,  # 100MB
            max_network_bytes=10 * 1024 * 1024,  # 10MB
            max_time_units=60.0,  # 60 time units
            max_io_operations=1000
        )
        
        self.resource_budgets['generation'] = ResourceBudget(
            budget_id="generation",
            max_cpu_cycles=500000,     # 500K cycles
            max_memory_bytes=50 * 1024 * 1024,   # 50MB
            max_network_bytes=1 * 1024 * 1024,   # 1MB
            max_time_units=30.0,  # 30 time units
            max_io_operations=100
        )
        
        self.resource_budgets['execution'] = ResourceBudget(
            budget_id="execution",
            max_cpu_cycles=2000000,    # 2M cycles
            max_memory_bytes=200 * 1024 * 1024,  # 200MB
            max_network_bytes=50 * 1024 * 1024,  # 50MB
            max_time_units=120.0,  # 120 time units
            max_io_operations=5000
        )
    
    def add_invariant(self, invariant: SystemInvariant) -> str:
        """Add system invariant."""
        self.invariants[invariant.invariant_id] = invariant
        return invariant.invariant_id
    
    def validate_transition(self, 
                         transition_type: StateTransition,
                         domain: DomainType,
                         from_state: SystemState,
                         to_state: SystemState,
                         data: Dict[str, Any],
                         actor_id: str,
                         resource_cost: ResourceCost) -> bool:
        """
        Validate state transition against all constraints.
        """
        
        # Start validation cycle
        cycle_id = str(time.time())
        self.cycle_manager.start_cycle(cycle_id)
        
        try:
            # Validate domain boundary
            boundary = self.domain_boundaries.get(domain)
            if not boundary:
                raise ArchitecturalViolationError(f"No boundary for domain: {domain.value}")
            
            if transition_type not in boundary.allowed_operations:
                raise ArchitecturalViolationError(
                    f"Operation {transition_type.value} not allowed in domain {domain.value}"
                )
            
            # Validate data size
            data_size = len(json.dumps(data, default=str).encode())
            if data_size > boundary.max_data_size:
                raise ArchitecturalViolationError(
                    f"Data size {data_size} exceeds limit {boundary.max_data_size}"
                )
            
            # Validate read-only constraint
            if boundary.read_only and transition_type != StateTransition.OBSERVE:
                raise ArchitecturalViolationError(
                    f"Write operation {transition_type.value} not allowed in read-only domain {domain.value}"
                )
            
            # Validate invariants
            for invariant in self.invariants.values():
                if invariant.domain == domain or invariant.domain == DomainType.GENERATION:
                    if not invariant.validate(to_state):
                        raise ArchitecturalViolationError(
                            f"Invariant {invariant.invariant_id} violated: {invariant.description}"
                        )
            
            # Validate resource budget
            budget = self.resource_budgets.get('default', self.resource_budgets['default'])
            if not resource_cost.within_budget(budget):
                raise ArchitecturalViolationError(
                    f"Resource cost exceeds budget: {resource_cost} > {budget}"
                )
            
            return True
            
        finally:
            self.cycle_manager.end_cycle()
    
    def create_state(self, 
                   domain_states: Dict[DomainType, Dict[str, Any]],
                   resource_usage: ResourceCost) -> SystemState:
        """Create new immutable system state."""
        
        # Generate state hash
        state_content = json.dumps({
            'domain_states': {k.value: v for k, v in domain_states.items()},
            'resource_usage': resource_usage.__dict__,
            'timestamp': time.time()
        }, sort_keys=True)
        
        state_hash = hashlib.sha256(state_content.encode()).hexdigest()
        
        # Create state
        state = SystemState(
            state_hash=state_hash,
            timestamp=time.time(),
            domain_states=domain_states,
            resource_usage=resource_usage,
            active_transitions=[],
            invariants=list(self.invariants.keys())
        )
        
        # Store state
        self.states[state_hash] = state
        self.state_history.append(state)
        
        # Update current state
        self.current_state = state
        
        return state
    
    def transition_state(self, 
                      transition_type: StateTransition,
                      domain: DomainType,
                      data: Dict[str, Any],
                      actor_id: str,
                      resource_cost: ResourceCost) -> SystemState:
        """
        Execute state transition with full validation.
        """
        
        if not self.current_state:
            raise ArchitecturalViolationError("No current state to transition from")
        
        # Create new state
        new_domain_states = self.current_state.domain_states.copy()
        new_resource_usage = self.current_state.resource_usage + resource_cost
        
        # Update domain state
        if domain not in new_domain_states:
            new_domain_states[domain] = {}
        
        new_domain_states[domain].update({
            'last_transition': transition_type.value,
            'last_actor': actor_id,
            'last_data': data,
            'last_timestamp': time.time()
        })
        
        # Create new state
        new_state = self.create_state(new_domain_states, new_resource_usage)
        
        # Validate transition
        if self.validate_transition(
            transition_type, domain, self.current_state, new_state, data, actor_id, resource_cost
        ):
            # Record transition
            transition = StateTransition(
                transition_id=str(time.time()),
                from_state_hash=self.current_state.state_hash,
                to_state_hash=new_state.state_hash,
                transition_type=transition_type,
                domain=domain,
                timestamp=time.time(),
                resource_cost=resource_cost,
                actor_id=actor_id,
                data=data
            )
            
            self.transitions[transition.transition_id] = transition
            
            # Update active transitions
            new_state.active_transitions.append(transition.transition_id)
            
            return new_state
        
        raise ArchitecturalViolationError("Transition validation failed")
    
    def get_state_history(self, 
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None,
                         domain: Optional[DomainType] = None) -> List[SystemState]:
        """Get state history with filters."""
        
        history = self.state_history.copy()
        
        # Time filter
        if start_time is not None:
            history = [s for s in history if s.timestamp >= start_time]
        if end_time is not None:
            history = [s for s in history if s.timestamp <= end_time]
        
        # Domain filter
        if domain is not None:
            history = [s for s in history if domain in s.domain_states]
        
        return history
    
    def verify_state_integrity(self) -> Dict[str, Any]:
        """Verify integrity of entire state history."""
        
        integrity_report = {
            'total_states': len(self.states),
            'total_transitions': len(self.transitions),
            'state_chain_valid': True,
            'invariant_violations': [],
            'signature_violations': [],
            'resource_budget_violations': []
        }
        
        # Verify state chain
        for transition in self.transitions.values():
            from_state = self.states.get(transition.from_state_hash)
            to_state = self.states.get(transition.to_state_hash)
            
            if not from_state or not to_state:
                integrity_report['state_chain_valid'] = False
                break
        
        # Verify invariants
        for state in self.states.values():
            for invariant in self.invariants.values():
                if not invariant.validate(state):
                    integrity_report['invariant_violations'].append({
                        'state_hash': state.state_hash,
                        'invariant_id': invariant.invariant_id,
                        'description': invariant.description
                    })
        
        # Verify signatures
        for transition in self.transitions.values():
            expected_signature = transition.signature
            # Recalculate signature
            content = json.dumps({
                'transition_id': transition.transition_id,
                'from_state_hash': transition.from_state_hash,
                'to_state_hash': transition.to_state_hash,
                'transition_type': transition.transition_type.value,
                'domain': transition.domain.value,
                'timestamp': transition.timestamp,
                'resource_cost': transition.resource_cost.__dict__,
                'actor_id': transition.actor_id,
                'data': transition.data
            }, sort_keys=True)
            calculated_signature = hashlib.sha256(content.encode()).hexdigest()
            
            if transition.signature != calculated_signature:
                integrity_report['signature_violations'].append({
                    'transition_id': transition.transition_id,
                    'expected': expected_signature,
                    'calculated': calculated_signature
                })
        
        return integrity_report
    
    def get_domain_status(self, domain: DomainType) -> Dict[str, Any]:
        """Get status of specific domain."""
        if not self.current_state:
            return {'status': 'no_current_state'}
        
        domain_state = self.current_state.get_domain_state(domain)
        boundary = self.domain_boundaries.get(domain)
        
        return {
            'domain': domain.value,
            'state': domain_state,
            'boundary': {
                'allowed_operations': [op.value for op in boundary.allowed_operations],
                'max_data_size': boundary.max_data_size,
                'read_only': boundary.read_only
            },
            'last_transition': domain_state.get('last_transition'),
            'last_actor': domain_state.get('last_actor'),
            'resource_usage': self.current_state.resource_usage.__dict__
        }
    
    def export_state_model(self, filename: str):
        """Export entire state model to file."""
        export_data = {
            'export_timestamp': time.time(),
            'states': {hash_val: state.to_dict() for hash_val, state in self.states.items()},
            'transitions': {tid: {
                'transition_id': t.transition_id,
                'from_state_hash': t.from_state_hash,
                'to_state_hash': t.to_state_hash,
                'transition_type': t.transition_type.value,
                'domain': t.domain.value,
                'timestamp': t.timestamp,
                'resource_cost': t.resource_cost.__dict__,
                'actor_id': t.actor_id,
                'data': t.data,
                'signature': t.signature
            } for tid, t in self.transitions.items()},
            'invariants': {
                inv_id: {
                    'description': inv.description,
                    'domain': inv.domain.value,
                    'violation_severity': inv.violation_severity
                } for inv_id, inv in self.invariants.items()
            },
            'domain_boundaries': {
                domain.value: {
                    'allowed_operations': [op.value for op in boundary.allowed_operations],
                    'allowed_data_types': boundary.allowed_data_types,
                    'max_data_size': boundary.max_data_size,
                    'read_only': boundary.read_only
                } for domain, boundary in self.domain_boundaries.items()
            },
            'resource_budgets': {
                budget_id: budget.to_dict() for budget_id, budget in self.resource_budgets.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)


@dataclass(frozen=True)
class DomainBoundary:
    """Immutable domain boundary definition."""
    allowed_operations: List[StateTransition]
    allowed_data_types: List[str]
    max_data_size: int
    read_only: bool
