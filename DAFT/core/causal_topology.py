"""
EVENT_HORIZON Causal Failure Topology

Implements causal inference and temporal ordering for failure analysis
instead of simple structural dependency graphs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
import time
import networkx as nx
from collections import defaultdict

from .models import FailureEvent, TestPhase


class CausalRelation(Enum):
    """Types of causal relationships between failures"""
    DIRECT_CAUSE = "direct_cause"           # A directly caused B
    INDIRECT_CAUSE = "indirect_cause"       # A contributed to B
    CORRELATION = "correlation"             # A and B correlated
    CASCADE_TRIGGER = "cascade_trigger"       # A triggered cascade to B
    RECOVERY_DEPENDENCY = "recovery_dep"    # B recovery depends on A


@dataclass
class TemporalFailureEvent:
    """Failure event with temporal and causal context"""
    base_event: FailureEvent
    temporal_order: int
    causal_predecessors: List[str] = field(default_factory=list)
    causal_successors: List[str] = field(default_factory=list)
    propagation_delay: Optional[float] = None
    root_cause_distance: int = 0
    cascade_depth: int = 0
    
    def __post_init__(self):
        if self.base_event.timestamp:
            self.temporal_order = int(self.base_event.timestamp)


@dataclass
class CausalEdge:
    """Edge representing causal relationship between failures"""
    source_event_id: str
    target_event_id: str
    relation_type: CausalRelation
    confidence: float  # 0.0 to 1.0
    temporal_delta: float  # Time difference in seconds
    evidence: List[str] = field(default_factory=list)
    
    def __str__(self):
        return f"{self.source_event_id} -> {self.target_event_id} ({self.relation_type.value}, conf: {self.confidence:.2f})"


@dataclass
class CausalGraph:
    """Directed acyclic graph representing causal relationships"""
    nodes: Dict[str, TemporalFailureEvent] = field(default_factory=dict)
    edges: List[CausalEdge] = field(default_factory=list)
    root_causes: Set[str] = field(default_factory=set)
    cascade_chains: List[List[str]] = field(default_factory=list)
    
    def add_node(self, event: TemporalFailureEvent):
        """Add node to causal graph"""
        self.nodes[event.base_event.id] = event
    
    def add_edge(self, edge: CausalEdge):
        """Add causal edge to graph"""
        self.edges.append(edge)
        
        # Update node relationships
        if edge.source_event_id in self.nodes:
            self.nodes[edge.source_event_id].causal_successors.append(edge.target_event_id)
        if edge.target_event_id in self.nodes:
            self.nodes[edge.target_event_id].causal_predecessors.append(edge.source_event_id)
    
    def find_root_causes(self) -> Set[str]:
        """Find events with no predecessors (root causes)"""
        self.root_causes = {
            event_id for event_id, event in self.nodes.items()
            if not event.causal_predecessors
        }
        return self.root_causes
    
    def calculate_cascade_depths(self):
        """Calculate cascade depth for all nodes"""
        for event_id, event in self.nodes.items():
            if not event.causal_predecessors:
                event.cascade_depth = 0
            else:
                max_pred_depth = max(
                    self.nodes[pred].cascade_depth 
                    for pred in event.causal_predecessors
                    if pred in self.nodes
                )
                event.cascade_depth = max_pred_depth + 1
    
    def find_cascade_chains(self):
        """Find all cascade chains in the graph"""
        self.cascade_chains = []
        
        for root_id in self.root_causes:
            if root_id not in self.nodes:
                continue
                
            chain = self._trace_cascade_chain(root_id)
            if len(chain) > 1:
                self.cascade_chains.append(chain)
    
    def _trace_cascade_chain(self, start_id: str) -> List[str]:
        """Trace cascade chain from starting event"""
        chain = [start_id]
        current = start_id
        
        while current in self.nodes:
            successors = self.nodes[current].causal_successors
            if not successors:
                break
            
            # Follow the most likely successor (highest confidence)
            next_event = max(
                [(edge, edge.confidence) for edge in self.edges 
                 if edge.source_event_id == current],
                key=lambda x: x[1]
            )[0][0]
            
            chain.append(next_event.target_event_id)
            current = next_event.target_event_id
        
        return chain


class CausalInferenceEngine:
    """Engine for inferring causal relationships from failure events"""
    
    def __init__(self):
        self.temporal_window = 30.0  # 30 seconds for causal inference
        self.confidence_threshold = 0.6
        self.propagation_delay_threshold = 5.0  # 5 seconds max propagation delay
    
    def infer_causal_relationships(self, 
                                 failure_events: List[FailureEvent]) -> CausalGraph:
        """Infer causal relationships from failure events"""
        
        # Create temporal events
        temporal_events = self._create_temporal_events(failure_events)
        
        # Sort by temporal order
        temporal_events.sort(key=lambda x: x.temporal_order)
        
        # Build causal graph
        causal_graph = CausalGraph()
        
        # Add all nodes
        for event in temporal_events:
            causal_graph.add_node(event)
        
        # Infer causal edges
        for i, event_i in enumerate(temporal_events):
            for event_j in temporal_events[i+1:]:
                edge = self._infer_causal_edge(event_i, event_j)
                if edge and edge.confidence >= self.confidence_threshold:
                    causal_graph.add_edge(edge)
        
        # Calculate graph properties
        causal_graph.find_root_causes()
        causal_graph.calculate_cascade_depths()
        causal_graph.find_cascade_chains()
        
        return causal_graph
    
    def _create_temporal_events(self, 
                               failure_events: List[FailureEvent]) -> List[TemporalFailureEvent]:
        """Create temporal events from failure events"""
        temporal_events = []
        
        for event in failure_events:
            temporal_event = TemporalFailureEvent(
                base_event=event,
                temporal_order=int(event.timestamp) if event.timestamp else 0
            )
            temporal_events.append(temporal_event)
        
        return temporal_events
    
    def _infer_causal_edge(self, 
                          source: TemporalFailureEvent, 
                          target: TemporalFailureEvent) -> Optional[CausalEdge]:
        """Infer causal relationship between two events"""
        
        # Check temporal ordering
        if source.temporal_order >= target.temporal_order:
            return None
        
        temporal_delta = target.temporal_order - source.temporal_order
        
        # Check if within temporal window
        if temporal_delta > self.temporal_window:
            return None
        
        # Determine causal relation type
        relation_type, confidence, evidence = self._determine_causal_relation(
            source, target, temporal_delta
        )
        
        if confidence < self.confidence_threshold:
            return None
        
        return CausalEdge(
            source_event_id=source.base_event.id,
            target_event_id=target.base_event.id,
            relation_type=relation_type,
            confidence=confidence,
            temporal_delta=temporal_delta,
            evidence=evidence
        )
    
    def _determine_causal_relation(self, 
                                 source: TemporalFailureEvent,
                                 target: TemporalFailureEvent,
                                 temporal_delta: float) -> Tuple[CausalRelation, float, List[str]]:
        """Determine type and confidence of causal relation"""
        
        evidence = []
        confidence = 0.0
        relation_type = CausalRelation.CORRELATION
        
        # Component dependency analysis
        if self._are_components_dependent(source.base_event.component_id, 
                                       target.base_event.component_id):
            confidence += 0.4
            evidence.append("component_dependency")
            
            if temporal_delta < self.propagation_delay_threshold:
                relation_type = CausalRelation.DIRECT_CAUSE
                confidence += 0.3
                evidence.append("fast_propagation")
            else:
                relation_type = CausalRelation.INDIRECT_CAUSE
                confidence += 0.2
                evidence.append("delayed_propagation")
        
        # Failure type analysis
        if self._are_failure_types_related(source.base_event.failure_type,
                                       target.base_event.failure_type):
            confidence += 0.2
            evidence.append("related_failure_types")
        
        # Severity correlation
        severity_correlation = self._calculate_severity_correlation(
            source.base_event.severity, target.base_event.severity
        )
        confidence += severity_correlation * 0.2
        if severity_correlation > 0.7:
            evidence.append("severity_correlation")
        
        # Temporal proximity bonus
        if temporal_delta < 5.0:
            confidence += 0.2
            evidence.append("temporal_proximity")
        elif temporal_delta < 15.0:
            confidence += 0.1
            evidence.append("moderate_temporal_proximity")
        
        # Component type analysis
        if self._is_critical_component(source.base_event.component_id):
            confidence += 0.1
            evidence.append("critical_component_source")
        
        if self._is_critical_component(target.base_event.component_id):
            confidence += 0.1
            evidence.append("critical_component_target")
        
        # Cascade detection
        if confidence > 0.8 and temporal_delta < 10.0:
            relation_type = CausalRelation.CASCADE_TRIGGER
            evidence.append("cascade_pattern")
        
        return relation_type, min(confidence, 1.0), evidence
    
    def _are_components_dependent(self, source_comp: str, target_comp: str) -> bool:
        """Check if components have dependency relationship"""
        # This would use actual component dependency graph
        # Simplified implementation for demonstration
        dependency_map = {
            "waf": ["rate_limiter", "session_manager"],
            "rate_limiter": ["load_balancer"],
            "load_balancer": ["session_manager", "database"],
            "session_manager": ["database"],
            "database": ["identity_federation"]
        }
        
        return target_comp in dependency_map.get(source_comp, [])
    
    def _are_failure_types_related(self, 
                                 source_type, target_type) -> bool:
        """Check if failure types are causally related"""
        related_types = {
            "connection_exhaustion": ["timeout", "service_unavailable"],
            "normalization_loss": ["semantic_drift", "authentication_failure"],
            "rate_limit_bypass": ["authentication_failure", "resource_exhaustion"],
            "session_desync": ["authentication_failure", "authorization_failure"],
            "token_mismatch": ["authentication_failure", "session_invalid"],
            "proxy_mutation": ["semantic_drift", "authentication_failure"]
        }
        
        return target_type.value in related_types.get(source_type.value, [])
    
    def _calculate_severity_correlation(self, source_severity: float, 
                                     target_severity: float) -> float:
        """Calculate correlation between severities"""
        # Higher correlation if target severity is similar or higher
        if target_severity >= source_severity:
            return 1.0 - abs(target_severity - source_severity)
        else:
            return max(0.0, 0.5 - abs(target_severity - source_severity))
    
    def _is_critical_component(self, component_id: str) -> bool:
        """Check if component is critical for system operation"""
        critical_components = {"database", "session_manager", "identity_federation"}
        return component_id in critical_components
    
    def analyze_causal_patterns(self, causal_graph: CausalGraph) -> Dict[str, Any]:
        """Analyze patterns in causal graph"""
        
        return {
            "root_cause_analysis": self._analyze_root_causes(causal_graph),
            "cascade_analysis": self._analyze_cascades(causal_graph),
            "propagation_analysis": self._analyze_propagation_patterns(causal_graph),
            "critical_path_analysis": self._analyze_critical_paths(causal_graph),
            "temporal_patterns": self._analyze_temporal_patterns(causal_graph)
        }
    
    def _analyze_root_causes(self, causal_graph: CausalGraph) -> Dict[str, Any]:
        """Analyze root cause patterns"""
        root_causes = []
        
        for root_id in causal_graph.root_causes:
            if root_id not in causal_graph.nodes:
                continue
                
            root_event = causal_graph.nodes[root_id]
            root_causes.append({
                "event_id": root_id,
                "component_id": root_event.base_event.component_id,
                "failure_type": root_event.base_event.failure_type.value,
                "severity": root_event.base_event.severity,
                "timestamp": root_event.base_event.timestamp,
                "impact_scope": len(root_event.causal_successors)
            })
        
        # Group by component
        component_root_causes = defaultdict(list)
        for cause in root_causes:
            component_root_causes[cause["component_id"]].append(cause)
        
        return {
            "total_root_causes": len(root_causes),
            "root_causes_by_component": dict(component_root_causes),
            "most_problematic_components": sorted(
                component_root_causes.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]
        }
    
    def _analyze_cascades(self, causal_graph: CausalGraph) -> Dict[str, Any]:
        """Analyze cascade patterns"""
        cascade_analysis = []
        
        for chain in causal_graph.cascade_chains:
            cascade_analysis.append({
                "chain_length": len(chain),
                "cascade_depth": max(
                    causal_graph.nodes[node_id].cascade_depth 
                    for node_id in chain if node_id in causal_graph.nodes
                ),
                "propagation_time": self._calculate_cascade_propagation_time(chain, causal_graph),
                "components_involved": [
                    causal_graph.nodes[node_id].base_event.component_id 
                    for node_id in chain if node_id in causal_graph.nodes
                ],
                "max_severity": max(
                    causal_graph.nodes[node_id].base_event.severity 
                    for node_id in chain if node_id in causal_graph.nodes
                )
            })
        
        return {
            "total_cascades": len(cascade_analysis),
            "average_cascade_length": sum(c["chain_length"] for c in cascade_analysis) / len(cascade_analysis) if cascade_analysis else 0,
            "longest_cascade": max(cascade_analysis, key=lambda x: x["chain_length"]) if cascade_analysis else None,
            "fastest_propagation": min(cascade_analysis, key=lambda x: x["propagation_time"]) if cascade_analysis else None,
            "cascades_by_depth": defaultdict(list)
        }
    
    def _analyze_propagation_patterns(self, causal_graph: CausalGraph) -> Dict[str, Any]:
        """Analyze failure propagation patterns"""
        propagation_delays = []
        propagation_paths = []
        
        for edge in causal_graph.edges:
            propagation_delays.append(edge.temporal_delta)
            
            if edge.relation_type in [CausalRelation.DIRECT_CAUSE, CausalRelation.CASCADE_TRIGGER]:
                propagation_paths.append({
                    "source": edge.source_event_id,
                    "target": edge.target_event_id,
                    "delay": edge.temporal_delta,
                    "confidence": edge.confidence,
                    "relation": edge.relation_type.value
                })
        
        return {
            "average_propagation_delay": sum(propagation_delays) / len(propagation_delays) if propagation_delays else 0,
            "max_propagation_delay": max(propagation_delays) if propagation_delays else 0,
            "propagation_paths": propagation_paths,
            "fast_propagations": [p for p in propagation_paths if p["delay"] < 5.0],
            "slow_propagations": [p for p in propagation_paths if p["delay"] > 20.0]
        }
    
    def _analyze_critical_paths(self, causal_graph: CausalGraph) -> Dict[str, Any]:
        """Analyze critical failure paths"""
        critical_paths = []
        
        for root_id in causal_graph.root_causes:
            if root_id not in causal_graph.nodes:
                continue
                
            # Find longest path from this root
            path = self._find_longest_path(root_id, causal_graph)
            if len(path) > 2:  # Only consider paths with multiple hops
                critical_paths.append({
                    "root_cause": root_id,
                    "path_length": len(path),
                    "path": path,
                    "total_impact": len(path),
                    "max_severity": max(
                        causal_graph.nodes[node_id].base_event.severity 
                        for node_id in path if node_id in causal_graph.nodes
                    )
                })
        
        return {
            "critical_paths": critical_paths,
            "longest_critical_path": max(critical_paths, key=lambda x: x["path_length"]) if critical_paths else None,
            "highest_impact_path": max(critical_paths, key=lambda x: x["total_impact"]) if critical_paths else None
        }
    
    def _analyze_temporal_patterns(self, causal_graph: CausalGraph) -> Dict[str, Any]:
        """Analyze temporal patterns in failures"""
        temporal_events = list(causal_graph.nodes.values())
        temporal_events.sort(key=lambda x: x.temporal_order)
        
        if not temporal_events:
            return {}
        
        # Time-based clustering
        time_clusters = self._cluster_by_time(temporal_events, window=60)  # 1-minute windows
        
        # Phase-based analysis
        phase_distribution = defaultdict(int)
        for event in temporal_events:
            # This would need phase information from the test context
            # Simplified for demonstration
            phase = "unknown"
            phase_distribution[phase] += 1
        
        return {
            "time_clusters": time_clusters,
            "phase_distribution": dict(phase_distribution),
            "failure_rate_over_time": self._calculate_failure_rate_timeline(temporal_events),
            "burst_detection": self._detect_failure_bursts(temporal_events)
        }
    
    def _calculate_cascade_propagation_time(self, 
                                         chain: List[str], 
                                         causal_graph: CausalGraph) -> float:
        """Calculate total propagation time for cascade chain"""
        if len(chain) < 2:
            return 0.0
        
        start_time = causal_graph.nodes[chain[0]].temporal_order
        end_time = causal_graph.nodes[chain[-1]].temporal_order
        
        return end_time - start_time
    
    def _find_longest_path(self, start_id: str, causal_graph: CausalGraph) -> List[str]:
        """Find longest path from starting node using DFS"""
        visited = set()
        path = []
        
        def dfs(current_id: str, current_path: List[str]):
            if current_id in visited:
                return current_path
            
            visited.add(current_id)
            current_path.append(current_id)
            
            max_path = current_path.copy()
            for successor in causal_graph.nodes[current_id].causal_successors:
                if successor in causal_graph.nodes:
                    successor_path = dfs(successor, current_path.copy())
                    if len(successor_path) > len(max_path):
                        max_path = successor_path
            
            return max_path
        
        return dfs(start_id, path)
    
    def _cluster_by_time(self, events: List[TemporalFailureEvent], window: int) -> List[Dict[str, Any]]:
        """Cluster events by time windows"""
        if not events:
            return []
        
        clusters = []
        current_cluster = [events[0]]
        current_time = events[0].temporal_order
        
        for event in events[1:]:
            if event.temporal_order - current_time <= window:
                current_cluster.append(event)
            else:
                clusters.append({
                    "start_time": current_cluster[0].temporal_order,
                    "end_time": current_cluster[-1].temporal_order,
                    "event_count": len(current_cluster),
                    "events": current_cluster
                })
                current_cluster = [event]
                current_time = event.temporal_order
        
        # Add last cluster
        if current_cluster:
            clusters.append({
                "start_time": current_cluster[0].temporal_order,
                "end_time": current_cluster[-1].temporal_order,
                "event_count": len(current_cluster),
                "events": current_cluster
            })
        
        return clusters
    
    def _calculate_failure_rate_timeline(self, 
                                     events: List[TemporalFailureEvent]) -> List[Dict[str, Any]]:
        """Calculate failure rate over time"""
        if not events:
            return []
        
        timeline = []
        window_size = 60  # 1-minute windows
        
        start_time = events[0].temporal_order
        end_time = events[-1].temporal_order
        
        current_time = start_time
        while current_time <= end_time:
            window_events = [
                e for e in events 
                if current_time <= e.temporal_order < current_time + window_size
            ]
            
            timeline.append({
                "timestamp": current_time,
                "failure_count": len(window_events),
                "failure_rate": len(window_events) / window_size
            })
            
            current_time += window_size
        
        return timeline
    
    def _detect_failure_bursts(self, 
                               events: List[TemporalFailureEvent]) -> List[Dict[str, Any]]:
        """Detect failure bursts using statistical analysis"""
        if len(events) < 10:
            return []
        
        # Calculate moving average
        window_size = min(10, len(events) // 3)
        moving_averages = []
        
        for i in range(window_size, len(events)):
            window_events = events[i-window_size:i]
            avg_rate = len(window_events) / (events[i].temporal_order - events[i-window_size].temporal_order)
            moving_averages.append(avg_rate)
        
        # Detect bursts (rate > 2x moving average)
        bursts = []
        threshold = sum(moving_averages) / len(moving_averages) * 2
        
        for i, avg_rate in enumerate(moving_averages):
            if avg_rate > threshold:
                bursts.append({
                    "timestamp": events[i + window_size].temporal_order,
                    "burst_rate": avg_rate,
                    "threshold": threshold,
                    "severity": "high" if avg_rate > threshold * 3 else "medium"
                })
        
        return bursts
