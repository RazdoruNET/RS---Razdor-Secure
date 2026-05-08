"""
Session Collapse Simulator (SCS)

Tests session management resilience by creating massive
session creation/termination scenarios and checking
consistency between stateless and stateful nodes.
"""

import asyncio
import random
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import structlog

from ...core.models import TestRequest, FailureEvent

logger = structlog.get_logger(__name__)


@dataclass
class SessionState:
    """Represents the state of a session"""
    session_id: str
    user_id: str
    created_at: float
    last_accessed: float
    data: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    node_id: Optional[str] = None
    generation: int = 0  # For tracking session versions


@dataclass
class SessionConflict:
    """Represents a session consistency conflict"""
    session_id: str
    node_a: str
    node_b: str
    state_a: Dict[str, Any]
    state_b: Dict[str, Any]
    conflict_type: str
    timestamp: float = field(default_factory=time.time)


class SessionCollapseSimulator:
    """
    Simulates session collapse scenarios to test session management resilience.
    
    This layer creates massive session creation/termination scenarios and
    checks for consistency between stateless and stateful nodes.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionState] = {}
        self.session_history: List[SessionState] = []
        self.node_states: Dict[str, Dict[str, SessionState]] = {}
        self.conflicts: List[SessionConflict] = []
        
        # Simulation parameters
        self.max_sessions = 10000
        self.session_ttl = 3600  # 1 hour
        self.cleanup_interval = 300  # 5 minutes
        
        # Node simulation
        self.nodes = ["node-1", "node-2", "node-3", "node-4"]
        for node in self.nodes:
            self.node_states[node] = {}
        
        logger.info("Session Collapse Simulator initialized")
    
    async def process_request(self, request: TestRequest) -> None:
        """
        Process a request through session collapse testing.
        
        Args:
            request: The test request to process
        """
        # Randomly apply session stress techniques
        stress_type = random.choice([
            "session_flood", "race_condition", "ghost_session",
            "session_desync", "memory_leak", "invalidation_race"
        ])
        
        if stress_type == "session_flood":
            await self._simulate_session_flood(request)
        elif stress_type == "race_condition":
            await self._simulate_race_condition(request)
        elif stress_type == "ghost_session":
            await self._simulate_ghost_session(request)
        elif stress_type == "session_desync":
            await self._simulate_session_desync(request)
        elif stress_type == "memory_leak":
            await self._simulate_memory_leak(request)
        elif stress_type == "invalidation_race":
            await self._simulate_invalidation_race(request)
        
        # Add anomaly flag
        request.anomaly_flags.append(f"scs_{stress_type}")
        
        logger.debug("Applied session stress", 
                    request_id=request.id, 
                    stress_type=stress_type)
    
    async def _simulate_session_flood(self, request: TestRequest) -> None:
        """Simulate massive session creation to test limits"""
        flood_size = random.randint(100, 1000)
        
        for i in range(flood_size):
            session_id = str(uuid.uuid4())
            user_id = f"flood_user_{i}"
            
            session = SessionState(
                session_id=session_id,
                user_id=user_id,
                created_at=time.time(),
                last_accessed=time.time(),
                data={"flood_test": True, "request_id": request.id},
                node_id=random.choice(self.nodes)
            )
            
            self.active_sessions[session_id] = session
            self.node_states[session.node_id][session_id] = session
        
        # Simulate immediate cleanup to test recovery
        if len(self.active_sessions) > self.max_sessions:
            await self._emergency_cleanup()
    
    async def _simulate_race_condition(self, request: TestRequest) -> None:
        """Simulate concurrent session access race conditions"""
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create session if it doesn't exist
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = SessionState(
                session_id=session_id,
                user_id=request.payload.get("username", "unknown"),
                created_at=time.time(),
                last_accessed=time.time(),
                node_id=random.choice(self.nodes)
            )
        
        # Simulate concurrent access from multiple nodes
        concurrent_nodes = random.sample(self.nodes, min(3, len(self.nodes)))
        
        tasks = []
        for node in concurrent_nodes:
            task = self._concurrent_session_access(session_id, node, request)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for conflicts
        await self._detect_session_conflicts(session_id)
    
    async def _concurrent_session_access(self, session_id: str, node_id: str, request: TestRequest) -> None:
        """Simulate concurrent access to a session from a specific node"""
        await asyncio.sleep(random.uniform(0.001, 0.01))  # Simulate network delay
        
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        # Create local copy for this node
        local_session = SessionState(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            last_accessed=time.time(),
            data=session.data.copy(),
            node_id=node_id,
            generation=session.generation + 1
        )
        
        # Modify session data
        local_session.data[f"last_access_by_{node_id}"] = time.time()
        local_session.data["request_count"] = local_session.data.get("request_count", 0) + 1
        
        # Update node state
        self.node_states[node_id][session_id] = local_session
        
        # Randomly update global state (simulating synchronization)
        if random.random() < 0.3:  # 30% chance of sync
            self.active_sessions[session_id] = local_session
    
    async def _simulate_ghost_session(self, request: TestRequest) -> None:
        """Simulate ghost sessions that exist but shouldn't"""
        # Create session that should be invalid
        ghost_session_id = str(uuid.uuid4())
        
        # Create on some nodes but not others
        selected_nodes = random.sample(self.nodes, random.randint(1, len(self.nodes) - 1))
        
        for node in selected_nodes:
            ghost_session = SessionState(
                session_id=ghost_session_id,
                user_id="ghost_user",
                created_at=time.time() - 7200,  # 2 hours ago (expired)
                last_accessed=time.time() - 3600,  # 1 hour ago
                data={"ghost": True, "invalid": True},
                node_id=node,
                is_active=False
            )
            
            self.node_states[node][ghost_session_id] = ghost_session
        
        # Don't add to global active sessions (inconsistent state)
        logger.debug("Created ghost session", 
                    session_id=ghost_session_id, 
                    nodes=selected_nodes)
    
    async def _simulate_session_desync(self, request: TestRequest) -> None:
        """Simulate session desynchronization between nodes"""
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create different session states on different nodes
        for i, node in enumerate(self.nodes):
            node_session = SessionState(
                session_id=session_id,
                user_id=request.payload.get("username", f"user_{i}"),
                created_at=time.time() + i,  # Different creation times
                last_accessed=time.time() + i * 10,
                data={
                    "node_specific": f"data_{node}",
                    "version": i,
                    "desync_test": True
                },
                node_id=node,
                generation=i
            )
            
            self.node_states[node][session_id] = node_session
        
        # Add inconsistent global state
        if random.random() < 0.5:
            self.active_sessions[session_id] = self.node_states[self.nodes[0]][session_id]
    
    async def _simulate_memory_leak(self, request: TestRequest) -> None:
        """Simulate session memory leaks"""
        leak_size = random.randint(50, 200)
        
        for i in range(leak_size):
            session_id = str(uuid.uuid4())
            
            # Create sessions with large data
            large_data = {"x" * 1000: "y" * 1000}  # Large payload
            
            session = SessionState(
                session_id=session_id,
                user_id=f"leak_user_{i}",
                created_at=time.time(),
                last_accessed=time.time(),
                data=large_data,
                node_id=random.choice(self.nodes)
            )
            
            self.active_sessions[session_id] = session
            self.node_states[session.node_id][session_id] = session
        
        # Simulate failed cleanup
        if random.random() < 0.3:  # 30% chance of cleanup failure
            logger.warning("Session cleanup failed", leaked_sessions=leak_size)
    
    async def _simulate_invalidation_race(self, request: TestRequest) -> None:
        """Simulate session invalidation race conditions"""
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create session
        session = SessionState(
            session_id=session_id,
            user_id=request.payload.get("username", "test_user"),
            created_at=time.time(),
            last_accessed=time.time(),
            data={"active": True},
            node_id=random.choice(self.nodes)
        )
        
        self.active_sessions[session_id] = session
        self.node_states[session.node_id][session_id] = session
        
        # Simulate concurrent invalidation attempts
        invalidation_tasks = []
        for node in self.nodes:
            task = self._invalidate_session_from_node(session_id, node)
            invalidation_tasks.append(task)
        
        await asyncio.gather(*invalidation_tasks, return_exceptions=True)
    
    async def _invalidate_session_from_node(self, session_id: str, node_id: str) -> None:
        """Attempt to invalidate session from a specific node"""
        await asyncio.sleep(random.uniform(0.001, 0.005))
        
        if session_id in self.node_states[node_id]:
            session = self.node_states[node_id][session_id]
            session.is_active = False
            session.data["invalidated_by"] = node_id
            session.data["invalidated_at"] = time.time()
        
        # Randomly remove from global state
        if random.random() < 0.7:  # 70% chance
            self.active_sessions.pop(session_id, None)
    
    async def _detect_session_conflicts(self, session_id: str) -> None:
        """Detect conflicts between node states for a session"""
        node_sessions = {}
        for node, sessions in self.node_states.items():
            if session_id in sessions:
                node_sessions[node] = sessions[session_id]
        
        if len(node_sessions) < 2:
            return
        
        # Compare states between nodes
        nodes = list(node_sessions.keys())
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node_a, node_b = nodes[i], nodes[j]
                session_a, session_b = node_sessions[node_a], node_sessions[node_b]
                
                conflict = self._compare_session_states(session_a, session_b, node_a, node_b)
                if conflict:
                    self.conflicts.append(conflict)
    
    def _compare_session_states(self, session_a: SessionState, session_b: SessionState, 
                               node_a: str, node_b: str) -> Optional[SessionConflict]:
        """Compare two session states and identify conflicts"""
        conflicts = []
        
        # Check data differences
        if session_a.data != session_b.data:
            conflicts.append("data_mismatch")
        
        # Check generation differences
        if session_a.generation != session_b.generation:
            conflicts.append("generation_mismatch")
        
        # Check active status
        if session_a.is_active != session_b.is_active:
            conflicts.append("status_mismatch")
        
        # Check user ID
        if session_a.user_id != session_b.user_id:
            conflicts.append("user_mismatch")
        
        if conflicts:
            return SessionConflict(
                session_id=session_a.session_id,
                node_a=node_a,
                node_b=node_b,
                state_a=session_a.data,
                state_b=session_b.data,
                conflict_type=", ".join(conflicts)
            )
        
        return None
    
    async def _emergency_cleanup(self) -> None:
        """Perform emergency session cleanup"""
        cleanup_count = 0
        sessions_to_remove = []
        
        for session_id, session in self.active_sessions.items():
            if not session.is_active or (time.time() - session.last_accessed) > self.session_ttl:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.active_sessions.pop(session_id, None)
            for node in self.nodes:
                self.node_states[node].pop(session_id, None)
            cleanup_count += 1
        
        logger.info("Emergency cleanup completed", cleaned_sessions=cleanup_count)
    
    def get_session_integrity_metrics(self) -> Dict[str, Any]:
        """Get session integrity and consistency metrics"""
        total_sessions = len(self.active_sessions)
        total_conflicts = len(self.conflicts)
        
        # Calculate conflict rate
        conflict_rate = total_conflicts / max(total_sessions, 1)
        
        # Analyze conflict types
        conflict_types = {}
        for conflict in self.conflicts:
            for c_type in conflict.conflict_type.split(", "):
                conflict_types[c_type] = conflict_types.get(c_type, 0) + 1
        
        # Node consistency analysis
        node_consistency = {}
        for node in self.nodes:
            node_sessions = len(self.node_states[node])
            global_matches = sum(1 for session_id in self.node_states[node] 
                                if session_id in self.active_sessions)
            consistency_rate = global_matches / max(node_sessions, 1)
            node_consistency[node] = {
                "total_sessions": node_sessions,
                "global_matches": global_matches,
                "consistency_rate": consistency_rate
            }
        
        return {
            "total_sessions": total_sessions,
            "total_conflicts": total_conflicts,
            "conflict_rate": conflict_rate,
            "conflict_types": conflict_types,
            "node_consistency": node_consistency,
            "ghost_sessions": self._count_ghost_sessions(),
            "memory_usage_estimate": total_sessions * 1024  # Rough estimate
        }
    
    def _count_ghost_sessions(self) -> int:
        """Count ghost sessions (sessions that exist in nodes but not globally)"""
        ghost_count = 0
        all_node_sessions = set()
        
        for node in self.nodes:
            all_node_sessions.update(self.node_states[node].keys())
        
        ghost_sessions = all_node_sessions - set(self.active_sessions.keys())
        return len(ghost_sessions)
    
    def get_session_heatmap_data(self) -> Dict[str, Any]:
        """Generate session integrity heatmap data"""
        heatmap_data = {
            "nodes": [],
            "conflict_hotspots": [],
            "session_density": {},
            "risk_areas": []
        }
        
        # Node data
        for node in self.nodes:
            node_data = {
                "name": node,
                "session_count": len(self.node_states[node]),
                "conflict_count": len([c for c in self.conflicts 
                                     if node in [c.node_a, c.node_b]]),
                "risk_score": self._calculate_node_risk(node)
            }
            heatmap_data["nodes"].append(node_data)
        
        # Conflict hotspots
        for conflict in self.conflicts:
            hotspot = {
                "session_id": conflict.session_id,
                "nodes": [conflict.node_a, conflict.node_b],
                "conflict_type": conflict.conflict_type,
                "severity": len(conflict.conflict_type.split(", ")) / 4.0
            }
            heatmap_data["conflict_hotspots"].append(hotspot)
        
        return heatmap_data
    
    def _calculate_node_risk(self, node: str) -> float:
        """Calculate risk score for a node based on conflicts and inconsistencies"""
        node_conflicts = len([c for c in self.conflicts if node in [c.node_a, c.node_b]])
        node_sessions = len(self.node_states[node])
        
        # Risk factors
        conflict_risk = node_conflicts / max(node_sessions, 1) * 0.5
        volume_risk = min(node_sessions / 1000, 1.0) * 0.3
        isolation_risk = 0.2 if node_sessions == 0 else 0.0
        
        return min(conflict_risk + volume_risk + isolation_risk, 1.0)
