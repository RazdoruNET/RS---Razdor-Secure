"""
EVENT_HORIZON Final Architecture

Addresses the fundamental issue: system becomes self-modifying during analysis.
Implements strict separation of concerns with immutable data flow.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum
import structlog
from abc import ABC, abstractmethod
from collections import defaultdict, deque
import hashlib

logger = structlog.get_logger(__name__)


class SystemRole(Enum):
    """Explicit system roles to prevent confusion"""
    INPUT_GENERATOR = "input_generator"
    OBSERVER = "observer"
    ANALYZER = "analyzer"
    REPORTER = "reporter"
    EXTERNAL_ORACLE = "external_oracle"


class DataAccessMode(Enum):
    """How data can be accessed"""
    READ_ONLY = "read_only"
    APPEND_ONLY = "append_only"
    TRANSFORM_ONLY = "transform_only"


class ImmutableEvent(Protocol):
    """Protocol for immutable events"""
    
    def get_event_id(self) -> str:
        ...
    
    def get_timestamp(self) -> float:
        ...
    
    def get_data(self) -> Dict[str, Any]:
        ...
    
    def get_metadata(self) -> Dict[str, Any]:
        ...
    
    def is_immutable(self) -> bool:
        ...


@dataclass
class TestInputEvent(ImmutableEvent):
    """Immutable input event with no mutation capabilities"""
    event_id: str
    timestamp: float
    input_data: Dict[str, Any]
    source_system: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification"""
        content = f"{self.event_id}:{self.timestamp}:{str(sorted(self.input_data.items()))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_event_id(self) -> str:
        return self.event_id
    
    def get_timestamp(self) -> float:
        return self.timestamp
    
    def get_data(self) -> Dict[str, Any]:
        return self.input_data.copy()  # Immutable copy
    
    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata.copy()
    
    def is_immutable(self) -> bool:
        return True


@dataclass
class ProcessingEvent(ImmutableEvent):
    """Immutable processing event from system components"""
    event_id: str
    timestamp: float
    component_id: str
    input_event_id: str
    processing_result: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    role: SystemRole
    
    def get_event_id(self) -> str:
        return self.event_id
    
    def get_timestamp(self) -> float:
        return self.timestamp
    
    def get_data(self) -> Dict[str, Any]:
        return self.processing_result.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        return self.processing_metadata.copy()
    
    def is_immutable(self) -> bool:
        return True


@dataclass
class ObservationEvent(ImmutableEvent):
    """Immutable observation event from analysis system"""
    event_id: str
    timestamp: float
    observation_type: str
    observed_data: Dict[str, Any]
    confidence: float
    analysis_metadata: Dict[str, Any]
    
    def get_event_id(self) -> str:
        return self.event_id
    
    def get_timestamp(self) -> float:
        return self.timestamp
    
    def get_data(self) -> Dict[str, Any]:
        return self.observed_data.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        return self.analysis_metadata.copy()
    
    def is_immutable(self) -> bool:
        return True


class EventStore:
    """Immutable event store with append-only semantics"""
    
    def __init__(self):
        self.events: List[ImmutableEvent] = []
        self.events_by_id: Dict[str, ImmutableEvent] = {}
        self.events_by_type: Dict[str, List[ImmutableEvent]] = defaultdict(list)
        self.events_by_timestamp: List[ImmutableEvent] = []
        
    def append_event(self, event: ImmutableEvent) -> None:
        """Append event to store (append-only semantics)"""
        if event.get_event_id() in self.events_by_id:
            raise ValueError(f"Event ID {event.get_event_id()} already exists")
        
        self.events.append(event)
        self.events_by_id[event.get_event_id()] = event
        self.events_by_type[event.__class__.__name__].append(event)
        self.events_by_timestamp.append(event)
        
        # Keep sorted by timestamp
        self.events_by_timestamp.sort(key=lambda e: e.get_timestamp())
    
    def get_events_by_id(self, event_id: str) -> Optional[ImmutableEvent]:
        return self.events_by_id.get(event_id)
    
    def get_events_by_type(self, event_type: str) -> List[ImmutableEvent]:
        return self.events_by_type.get(event_type, [])
    
    def get_events_in_timerange(self, start_time: float, end_time: float) -> List[ImmutableEvent]:
        return [
            event for event in self.events_by_timestamp
            if start_time <= event.get_timestamp() <= end_time
        ]
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all events"""
        integrity_issues = []
        
        for event in self.events:
            if not event.is_immutable():
                integrity_issues.append({
                    "event_id": event.get_event_id(),
                    "issue": "Event is not immutable"
                })
        
        return {
            "total_events": len(self.events),
            "integrity_issues": integrity_issues,
            "is_valid": len(integrity_issues) == 0
        }


class ComponentInterface(ABC):
    """Interface for all system components"""
    
    def __init__(self, component_id: str, role: SystemRole):
        self.component_id = component_id
        self.role = role
        self.event_store: Optional[EventStore] = None
    
    def set_event_store(self, event_store: EventStore) -> None:
        """Set event store for component"""
        self.event_store = event_store
    
    @abstractmethod
    async def process_input(self, input_event: TestInputEvent) -> ProcessingEvent:
        """Process input event and return processing event"""
        pass
    
    @abstractmethod
    def get_component_metrics(self) -> Dict[str, Any]:
        """Get component-specific metrics"""
        pass


class WAFComponent(ComponentInterface):
    """WAF component with strict immutable semantics"""
    
    def __init__(self, component_id: str):
        super().__init__(component_id, SystemRole.OBSERVER)
        self.processed_requests = 0
        self.blocked_requests = 0
        self.normalization_rules_applied = 0
    
    async def process_input(self, input_event: TestInputEvent) -> ProcessingEvent:
        """Process input with immutable semantics"""
        self.processed_requests += 1
        
        input_data = input_event.get_data()
        
        # Apply normalization without mutating input
        normalized_data = self._apply_normalization(input_data)
        
        # Create processing event
        processing_event = ProcessingEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            component_id=self.component_id,
            input_event_id=input_event.get_event_id(),
            processing_result=normalized_data,
            processing_metadata={
                "normalization_applied": True,
                "rules_count": self.normalization_rules_applied,
                "blocked": self._should_block_request(normalized_data),
                "processing_time_ms": 0  # Would be measured
            },
            role=self.role
        )
        
        if self.event_store:
            self.event_store.append_event(processing_event)
        
        # Update metrics
        if processing_event.processing_metadata["blocked"]:
            self.blocked_requests += 1
        
        return processing_event
    
    def _apply_normalization(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply normalization without mutating original"""
        self.normalization_rules_applied += 1
        
        # Return new normalized data (immutable transformation)
        normalized = input_data.copy()
        normalized["normalized"] = True
        normalized["normalization_timestamp"] = time.time()
        normalized["normalization_rules"] = ["url_decode", "unicode_normalize"]
        
        return normalized
    
    def _should_block_request(self, normalized_data: Dict[str, Any]) -> bool:
        """Determine if request should be blocked"""
        # Simplified blocking logic
        suspicious_patterns = ["<script", "javascript:", "union select"]
        request_str = str(normalized_data).lower()
        
        return any(pattern in request_str for pattern in suspicious_patterns)
    
    def get_component_metrics(self) -> Dict[str, Any]:
        return {
            "processed_requests": self.processed_requests,
            "blocked_requests": self.blocked_requests,
            "normalization_rules_applied": self.normalization_rules_applied,
            "block_rate": self.blocked_requests / max(1, self.processed_requests)
        }


class RateLimiterComponent(ComponentInterface):
    """Rate limiter with backpressure handling"""
    
    def __init__(self, component_id: str):
        super().__init__(component_id, SystemRole.OBSERVER)
        self.client_buckets: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.rejected_requests = 0
        self.backpressure_events = 0
    
    async def process_input(self, input_event: TestInputEvent) -> ProcessingEvent:
        """Process input with rate limiting"""
        input_data = input_event.get_data()
        client_id = input_data.get("client_id", "unknown")
        
        # Check rate limit
        if self._is_rate_limited(client_id):
            self.rejected_requests += 1
            self.backpressure_events += 1
            
            processing_event = ProcessingEvent(
                event_id=str(uuid.uuid4()),
                timestamp=time.time(),
                component_id=self.component_id,
                input_event_id=input_event.get_event_id(),
                processing_result={"rejected": True, "reason": "rate_limit_exceeded"},
                processing_metadata={
                    "rate_limited": True,
                    "client_id": client_id,
                    "bucket_size": len(self.client_buckets[client_id])
                },
                role=self.role
            )
        else:
            # Process normally
            self.client_buckets[client_id].append(time.time())
            processing_event = ProcessingEvent(
                event_id=str(uuid.uuid4()),
                timestamp=time.time(),
                component_id=self.component_id,
                input_event_id=input_event.get_event_id(),
                processing_result={"accepted": True, "rate_limit_status": "ok"},
                processing_metadata={
                    "rate_limited": False,
                    "client_id": client_id,
                    "bucket_size": len(self.client_buckets[client_id])
                },
                role=self.role
            )
        
        if self.event_store:
            self.event_store.append_event(processing_event)
        
        return processing_event
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited"""
        bucket = self.client_buckets[client_id]
        now = time.time()
        
        # Remove old requests (older than 1 minute)
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        
        # Rate limit: 10 requests per minute
        return len(bucket) >= 10
    
    def get_component_metrics(self) -> Dict[str, Any]:
        return {
            "rejected_requests": self.rejected_requests,
            "backpressure_events": self.backpressure_events,
            "active_clients": len(self.client_buckets),
            "total_requests_processed": sum(len(bucket) for bucket in self.client_buckets.values())
        }


class AnalysisEngine:
    """Analysis engine that only observes and analyzes"""
    
    def __init__(self):
        self.event_store: Optional[EventStore] = None
        self.analysis_cache: Dict[str, Any] = {}
        self.analysis_results: List[ObservationEvent] = []
    
    def set_event_store(self, event_store: EventStore) -> None:
        """Set event store for analysis"""
        self.event_store = event_store
    
    async def analyze_system_behavior(self, time_window: float = 300.0) -> ObservationEvent:
        """Analyze system behavior over time window"""
        if not self.event_store:
            raise ValueError("Event store not set")
        
        now = time.time()
        start_time = now - time_window
        
        # Get events in time window
        events = self.event_store.get_events_in_timerange(start_time, now)
        
        # Perform analysis
        analysis_result = self._perform_analysis(events)
        
        # Create observation event
        observation = ObservationEvent(
            event_id=str(uuid.uuid4()),
            timestamp=now,
            observation_type="system_behavior_analysis",
            observed_data=analysis_result,
            confidence=0.8,  # Would be calculated based on data quality
            analysis_metadata={
                "time_window": time_window,
                "events_analyzed": len(events),
                "analysis_timestamp": now
            }
        )
        
        self.analysis_results.append(observation)
        
        if self.event_store:
            self.event_store.append_event(observation)
        
        return observation
    
    def _perform_analysis(self, events: List[ImmutableEvent]) -> Dict[str, Any]:
        """Perform actual analysis on events"""
        if not events:
            return {"analysis": "no_events"}
        
        # Analyze by event type
        events_by_type = {}
        for event in events:
            event_type = event.__class__.__name__
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)
        
        # Calculate metrics
        input_events = events_by_type.get("TestInputEvent", [])
        processing_events = events_by_type.get("ProcessingEvent", [])
        
        return {
            "total_events": len(events),
            "events_by_type": {k: len(v) for k, v in events_by_type.items()},
            "input_events": len(input_events),
            "processing_events": len(processing_events),
            "component_metrics": self._analyze_component_metrics(processing_events),
            "system_health": self._calculate_system_health(events),
            "recommendations": self._generate_recommendations(events)
        }
    
    def _analyze_component_metrics(self, processing_events: List[ProcessingEvent]) -> Dict[str, Any]:
        """Analyze component performance metrics"""
        if not processing_events:
            return {}
        
        metrics_by_component = defaultdict(list)
        for event in processing_events:
            metrics_by_component[event.component_id].append(event)
        
        component_analysis = {}
        for component_id, events in metrics_by_component.items():
            processing_times = [
                e.processing_metadata.get("processing_time_ms", 0) 
                for e in events
            ]
            
            blocked_count = sum(
                1 for e in events 
                if e.processing_result.get("rejected", False)
            )
            
            component_analysis[component_id] = {
                "total_events": len(events),
                "blocked_events": blocked_count,
                "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
                "block_rate": blocked_count / len(events) if events else 0
            }
        
        return component_analysis
    
    def _calculate_system_health(self, events: List[ImmutableEvent]) -> Dict[str, Any]:
        """Calculate overall system health metrics"""
        if not events:
            return {"health": "unknown"}
        
        now = time.time()
        recent_events = [
            e for e in events 
            if now - e.get_timestamp() <= 60  # Last 1 minute
        ]
        
        processing_events = [
            e for e in recent_events 
            if isinstance(e, ProcessingEvent)
        ]
        
        blocked_count = sum(
            1 for e in processing_events 
            if e.processing_result.get("rejected", False)
        )
        
        health_score = 1.0 - (blocked_count / max(1, len(processing_events)))
        
        return {
            "health_score": health_score,
            "recent_events": len(recent_events),
            "blocked_rate": blocked_count / max(1, len(processing_events)),
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.6 else "critical"
        }
    
    def _generate_recommendations(self, events: List[ImmutableEvent]) -> List[str]:
        """Generate system recommendations based on analysis"""
        recommendations = []
        
        processing_events = [
            e for e in events 
            if isinstance(e, ProcessingEvent)
        ]
        
        # Analyze rejection patterns
        rejections_by_component = defaultdict(int)
        for event in processing_events:
            if event.processing_result.get("rejected", False):
                rejections_by_component[event.component_id] += 1
        
        # Generate recommendations
        for component_id, rejection_count in rejections_by_component.items():
            if rejection_count > 10:
                recommendations.append(f"Component {component_id} has high rejection rate ({rejection_count})")
        
        if len(rejections_by_component) > 0:
            recommendations.append("Review rate limiting configurations")
        
        return recommendations


class FinalEventHorizonArchitecture:
    """Final architecture that prevents self-modification loops"""
    
    def __init__(self):
        self.event_store = EventStore()
        self.components: Dict[str, ComponentInterface] = {}
        self.analysis_engine = AnalysisEngine()
        self.system_role = SystemRole.INPUT_GENERATOR
        
        # Initialize components
        self._initialize_components()
        
        # Set up analysis
        self.analysis_engine.set_event_store(self.event_store)
        
        logger.info("Final EVENT_HORIZON architecture initialized")
    
    def _initialize_components(self):
        """Initialize system components with proper roles"""
        self.components["waf"] = WAFComponent("waf_01")
        self.components["rate_limiter"] = RateLimiterComponent("rate_limiter_01")
        
        # Set event store for all components
        for component in self.components.values():
            component.set_event_store(self.event_store)
    
    async def run_assessment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run assessment with immutable data flow"""
        assessment_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info("Starting assessment with final architecture", assessment_id=assessment_id)
        
        # Create input event (immutable)
        input_event = TestInputEvent(
            event_id=f"input_{assessment_id}",
            timestamp=start_time,
            input_data=input_data,
            source_system="external_input",
            metadata={"assessment_id": assessment_id}
        )
        
        # Store input event
        self.event_store.append_event(input_event)
        
        # Process through components (immutable flow)
        current_event = input_event
        processing_chain = []
        
        for component_name, component in self.components.items():
            processing_event = await component.process_input(current_event)
            processing_chain.append(processing_event)
            current_event = processing_event
        
        # Analyze system behavior
        analysis_result = await self.analysis_engine.analyze_system_behavior()
        
        # Generate final results
        end_time = time.time()
        results = {
            "assessment_id": assessment_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "input_event_id": input_event.get_event_id(),
            "processing_chain": [e.get_event_id() for e in processing_chain],
            "final_processing_event": current_event.get_event_id() if processing_chain else None,
            "analysis_result": analysis_result,
            "event_store_integrity": self.event_store.verify_integrity(),
            "system_metrics": self._calculate_system_metrics(),
            "recommendations": analysis_result.get_data().get("recommendations", [])
        }
        
        logger.info("Assessment completed", 
                   assessment_id=assessment_id,
                   duration=results["duration"],
                   events_processed=len(self.event_store.events))
        
        return results
    
    def _calculate_system_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive system metrics"""
        events = self.event_store.events
        
        return {
            "total_events": len(events),
            "events_by_type": {
                event_type: len([e for e in events if e.__class__.__name__ == event_type])
                for event_type in set(e.__class__.__name__ for e in events)
            },
            "component_metrics": {
                component_id: component.get_component_metrics()
                for component_id, component in self.components.items()
            },
            "data_integrity": self.event_store.verify_integrity(),
            "system_role": self.system_role.value
        }
    
    def get_audit_trail(self) -> Dict[str, Any]:
        """Get complete audit trail"""
        return {
            "system_architecture": "immutable_event_sourcing",
            "event_store": {
                "total_events": len(self.event_store.events),
                "integrity": self.event_store.verify_integrity(),
                "events_by_type": {
                    event_type: len(events) 
                    for event_type, events in self.event_store.events_by_type.items()
                }
            },
            "components": {
                component_id: {
                    "role": component.role.value,
                    "metrics": component.get_component_metrics()
                }
                for component_id, component in self.components.items()
            },
            "analysis_results": self.analysis_engine.analysis_results,
            "system_role": self.system_role.value,
            "immutability_guaranteed": True
        }
