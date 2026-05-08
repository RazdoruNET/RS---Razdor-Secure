"""
Observation Plane - Pure read-side layer

Responsible for:
- Causal graph building
- System pressure monitoring
- Root cause analysis
- NO influence on Control Plane (architectural constraint)
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import networkx as nx
from collections import defaultdict, deque

from .core_constraints import (
    PlaneType, ExecutionCycleManager, ArchitecturalViolationError,
    ObservationControlSeparation
)


class EventType(Enum):
    """Types of system events."""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    ERROR_OCCURRED = "error_occurred"
    BACKPRESSURE_CHANGE = "backpressure_change"
    CIRCUIT_BREAK = "circuit_break"
    RESOURCE_PRESSURE = "resource_pressure"
    SYSTEM_METRIC = "system_metric"
    PLANE_INTERACTION = "plane_interaction"


@dataclass(frozen=True)
class CausalEvent:
    """Immutable causal event with relationship tracking."""
    event_id: str
    timestamp: float
    event_type: EventType
    plane: PlaneType
    causation_id: Optional[str]  # Parent event
    correlation_id: str
    system_state: Dict[str, Any]
    data: Dict[str, Any]
    
    def causal_chain(self) -> List[str]:
        """Get full causal chain."""
        chain = []
        current = self.causation_id
        while current:
            chain.append(current)
            current = self._get_parent_event(current)
        return chain
    
    def _get_parent_event(self, event_id: str) -> Optional[str]:
        """Get parent event ID (implementation specific)."""
        # This would be implemented by the specific storage
        return None


@dataclass
class CausalRelationship:
    """Relationship between two events."""
    cause_event_id: str
    effect_event_id: str
    relationship_type: str
    confidence: float
    timestamp: float


class CausalGraphBuilder:
    """
    Builds and maintains causal graphs of system events.
    
    CRITICAL: This is READ-ONLY - cannot influence Control Plane.
    """
    
    def __init__(self, cycle_manager: ExecutionCycleManager):
        self.cycle_manager = cycle_manager
        self.events: Dict[str, CausalEvent] = {}
        self.causal_graph = nx.DiGraph()
        self.relationships: List[CausalRelationship] = []
        
        # Performance optimization
        self.event_index = defaultdict(set)  # event_type -> event_ids
        self.correlation_index = defaultdict(set)  # correlation_id -> event_ids
        self.time_index = deque(maxlen=10000)  # recent events by time
    
    async def add_event(self, event: CausalEvent) -> bool:
        """
        Add event to causal graph.
        
        Returns True if event was added, False if architectural constraint violated.
        """
        
        # Start observation cycle
        cycle_id = str(uuid.uuid4())
        self.cycle_manager.start_cycle(cycle_id)
        
        try:
            # Validate interaction: Observation -> Observation (internal)
            self.cycle_manager.record_interaction(
                source_plane=PlaneType.OBSERVATION,
                target_plane=PlaneType.OBSERVATION,
                interaction_type="event_addition",
                data={"event_id": event.event_id, "event_type": event.event_type.value}
            )
            
            # Store event
            self.events[event.event_id] = event
            self.causal_graph.add_node(event.event_id, **asdict(event))
            
            # Add causal edge if parent exists
            if event.causation_id:
                self.causal_graph.add_edge(
                    event.causation_id, 
                    event.event_id,
                    relationship_type="causation",
                    timestamp=event.timestamp
                )
                
                # Track relationship
                relationship = CausalRelationship(
                    cause_event_id=event.causation_id,
                    effect_event_id=event.event_id,
                    relationship_type="causation",
                    confidence=1.0,
                    timestamp=event.timestamp
                )
                self.relationships.append(relationship)
            
            # Update indexes
            self.event_index[event.event_type.value].add(event.event_id)
            self.correlation_index[event.correlation_id].add(event.event_id)
            self.time_index.append((event.timestamp, event.event_id))
            
            return True
            
        except ArchitecturalViolationError:
            # This should not happen in Observation -> Observation
            return False
        finally:
            self.cycle_manager.end_cycle()
    
    async def find_root_cause(self, symptom_event_id: str) -> Optional[CausalEvent]:
        """
        Find root cause of a symptom event.
        
        Pure analysis - no influence on system.
        """
        if symptom_event_id not in self.events:
            return None
        
        symptom_event = self.events[symptom_event_id]
        
        # Traverse up causal chain
        current_event = symptom_event
        while current_event.causation_id:
            parent_event = self.events.get(current_event.causation_id)
            if not parent_event:
                break
            current_event = parent_event
        
        return current_event
    
    async def find_causal_paths(self, 
                               from_event_id: str, 
                               to_event_id: str) -> List[List[str]]:
        """
        Find all causal paths between events.
        
        Pure analysis - no system influence.
        """
        try:
            paths = list(nx.all_simple_paths(
                self.causal_graph, 
                from_event_id, 
                to_event_id
            ))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    async def analyze_event_patterns(self, 
                                 time_window: float = 300.0) -> Dict[str, Any]:
        """
        Analyze patterns in recent events.
        
        Pure observation - no system influence.
        """
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        # Get recent events
        recent_events = [
            event for event in self.events.values()
            if event.timestamp >= cutoff_time
        ]
        
        # Pattern analysis
        patterns = {
            "event_frequency": defaultdict(int),
            "causal_patterns": defaultdict(int),
            "correlation_patterns": defaultdict(int),
            "temporal_patterns": []
        }
        
        # Event frequency
        for event in recent_events:
            patterns["event_frequency"][event.event_type.value] += 1
        
        # Causal patterns (A -> B)
        for relationship in self.relationships:
            if relationship.timestamp >= cutoff_time:
                cause_event = self.events.get(relationship.cause_event_id)
                effect_event = self.events.get(relationship.effect_event_id)
                
                if cause_event and effect_event:
                    pattern = f"{cause_event.event_type.value} -> {effect_event.event_type.value}"
                    patterns["causal_patterns"][pattern] += 1
        
        # Correlation patterns (same correlation_id)
        correlation_groups = defaultdict(list)
        for event in recent_events:
            correlation_groups[event.correlation_id].append(event)
        
        for corr_id, events in correlation_groups.items():
            if len(events) > 1:
                event_types = [e.event_type.value for e in events]
                pattern = f"corr:{'+'.join(sorted(event_types))}"
                patterns["correlation_patterns"][pattern] += 1
        
        # Temporal patterns (time-based)
        time_sorted_events = sorted(recent_events, key=lambda e: e.timestamp)
        for i in range(len(time_sorted_events) - 1):
            current = time_sorted_events[i]
            next_event = time_sorted_events[i + 1]
            
            time_diff = next_event.timestamp - current.timestamp
            if time_diff < 1.0:  # Within 1 second
                pattern = f"{current.event_type.value} -> {next_event.event_type.value} ({time_diff:.2f}s)"
                patterns["temporal_patterns"].append(pattern)
        
        return patterns
    
    async def detect_anomalies(self, 
                              baseline_window: float = 3600.0) -> List[Dict[str, Any]]:
        """
        Detect anomalies in event patterns.
        
        Pure analysis - no system influence.
        """
        current_time = time.time()
        baseline_cutoff = current_time - baseline_window
        recent_cutoff = current_time - 300.0  # Last 5 minutes
        
        # Baseline events
        baseline_events = [
            event for event in self.events.values()
            if event.timestamp >= baseline_cutoff and event.timestamp < recent_cutoff
        ]
        
        # Recent events
        recent_events = [
            event for event in self.events.values()
            if event.timestamp >= recent_cutoff
        ]
        
        anomalies = []
        
        # Frequency anomalies
        baseline_freq = defaultdict(int)
        recent_freq = defaultdict(int)
        
        for event in baseline_events:
            baseline_freq[event.event_type.value] += 1
        
        for event in recent_events:
            recent_freq[event.event_type.value] += 1
        
        for event_type in baseline_freq:
            baseline_rate = baseline_freq[event_type] / (baseline_window - 300.0)
            recent_rate = recent_freq[event_type] / 300.0
            
            if recent_rate > baseline_rate * 3.0:  # 3x increase
                anomalies.append({
                    "type": "frequency_spike",
                    "event_type": event_type,
                    "baseline_rate": baseline_rate,
                    "recent_rate": recent_rate,
                    "severity": "high"
                })
        
        # Causal chain anomalies
        for event in recent_events:
            if event.causation_id:
                chain_length = len(event.causal_chain())
                if chain_length > 10:  # Unusually long causal chain
                    anomalies.append({
                        "type": "long_causal_chain",
                        "event_id": event.event_id,
                        "chain_length": chain_length,
                        "severity": "medium"
                    })
        
        return anomalies
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the causal graph."""
        return {
            "total_events": len(self.events),
            "total_relationships": len(self.relationships),
            "graph_density": nx.density(self.causal_graph),
            "average_path_length": nx.average_shortest_path_length(self.causal_graph) 
                               if nx.is_connected(self.causal_graph) else 0.0,
            "strongly_connected_components": nx.number_strongly_connected_components(self.causal_graph),
            "event_types": list(self.event_index.keys()),
            "correlation_groups": len(self.correlation_index)
        }
    
    def export_subgraph(self, 
                       event_ids: List[str], 
                       max_depth: int = 5) -> nx.DiGraph:
        """
        Export subgraph around specific events.
        
        Pure data export - no system influence.
        """
        subgraph = nx.DiGraph()
        
        for event_id in event_ids:
            if event_id in self.events:
                event = self.events[event_id]
                subgraph.add_node(event_id, **asdict(event))
                
                # Add causal relationships within depth
                self._add_causal_subgraph(subgraph, event_id, max_depth, 0)
        
        return subgraph
    
    def _add_causal_subgraph(self, 
                           graph: nx.DiGraph, 
                           event_id: str, 
                           max_depth: int, 
                           current_depth: int):
        """Recursively add causal subgraph."""
        if current_depth >= max_depth:
            return
        
        event = self.events.get(event_id)
        if not event or not event.causation_id:
            return
        
        # Add parent edge
        if event.causation_id not in graph:
            parent_event = self.events.get(event.causation_id)
            if parent_event:
                graph.add_node(event.causation_id, **asdict(parent_event))
                graph.add_edge(event.causation_id, event_id)
                
                # Recurse up
                self._add_causal_subgraph(
                    graph, event.causation_id, max_depth, current_depth + 1
                )


class SystemPressureMonitor:
    """
    Monitors system pressure without influencing control decisions.
    
    CRITICAL: Read-only monitoring - no control plane interaction.
    """
    
    def __init__(self, cycle_manager: ExecutionCycleManager):
        self.cycle_manager = cycle_manager
        self.pressure_history = deque(maxlen=1000)
        self.current_pressure = {
            "cpu_saturation": 0.0,
            "memory_pressure": 0.0,
            "event_loop_latency": 0.0,
            "connection_pool_pressure": 0.0,
            "downstream_response_time": 0.0,
            "overall_pressure": 0.0
        }
    
    async def record_pressure_reading(self, 
                                  pressure_data: Dict[str, float]) -> bool:
        """
        Record system pressure reading.
        
        Returns True if recorded, False if architectural constraint violated.
        """
        
        # Start observation cycle
        cycle_id = str(uuid.uuid4())
        self.cycle_manager.start_cycle(cycle_id)
        
        try:
            # Validate interaction: Observation -> Observation (internal)
            self.cycle_manager.record_interaction(
                source_plane=PlaneType.OBSERVATION,
                target_plane=PlaneType.OBSERVATION,
                interaction_type="pressure_recording",
                data={"pressure_data": pressure_data}
            )
            
            # Update current pressure
            self.current_pressure.update(pressure_data)
            self.current_pressure["overall_pressure"] = max(
                pressure_data.get("cpu_saturation", 0.0),
                pressure_data.get("memory_pressure", 0.0),
                pressure_data.get("event_loop_latency", 0.0) / 0.1,  # 100ms baseline
                pressure_data.get("connection_pool_pressure", 0.0),
                pressure_data.get("downstream_response_time", 0.0) / 5.0  # 5s baseline
            )
            
            # Add to history
            self.pressure_history.append({
                "timestamp": time.time(),
                "pressure": self.current_pressure.copy()
            })
            
            return True
            
        except ArchitecturalViolationError:
            return False
        finally:
            self.cycle_manager.end_cycle()
    
    def get_current_pressure(self) -> Dict[str, float]:
        """Get current system pressure (read-only)."""
        return self.current_pressure.copy()
    
    def get_pressure_trends(self, 
                           window_minutes: int = 30) -> Dict[str, Any]:
        """
        Analyze pressure trends over time window.
        
        Pure analysis - no system influence.
        """
        cutoff_time = time.time() - (window_minutes * 60)
        
        recent_readings = [
            reading for reading in self.pressure_history
            if reading["timestamp"] >= cutoff_time
        ]
        
        if not recent_readings:
            return {}
        
        # Calculate trends
        trends = {}
        for metric in ["cpu_saturation", "memory_pressure", "overall_pressure"]:
            values = [reading["pressure"][metric] for reading in recent_readings]
            
            if len(values) > 1:
                # Simple linear regression for trend
                n = len(values)
                x = list(range(n))
                y = values
                
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i] * y[i] for i in range(n))
                sum_x2 = sum(x[i] ** 2 for i in range(n))
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
                
                trends[metric] = {
                    "slope": slope,
                    "direction": "increasing" if slope > 0.001 else "decreasing" if slope < -0.001 else "stable",
                    "current_value": values[-1],
                    "average_value": sum_y / n
                }
        
        return trends
