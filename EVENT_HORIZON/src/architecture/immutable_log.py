"""
Immutable Event Log with External Oracle Integration

Provides append-only, replayable event log with external validation.
"""

import asyncio
import time
import json
import hashlib
import hmac
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
import os
from pathlib import Path


class EventType(Enum):
    """Types of events that can be logged."""
    CONTRACT_CREATED = "contract_created"
    CONTRACT_VALIDATED = "contract_validated"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    ERROR_OCCURRED = "error_occurred"
    BACKPRESSURE_CHANGED = "backpressure_changed"
    ORACLE_VALIDATION = "oracle_validation"
    PLANE_INTERACTION = "plane_interaction"
    SYSTEM_INVARIANT = "system_invariant"


@dataclass(frozen=True)
class SignedEvent:
    """Immutable signed event."""
    event_id: str
    timestamp: float
    event_type: EventType
    plane: str
    data: Dict[str, Any]
    signature: str
    previous_event_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def calculate_hash(self) -> str:
        """Calculate hash of event content."""
        content = json.dumps({
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'plane': self.plane,
            'data': self.data,
            'signature': self.signature
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class WALFile:
    """Write-Ahead Log file for durability."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_handle = None
    
    async def append(self, signed_event: SignedEvent) -> None:
        """Append signed event to WAL."""
        event_json = json.dumps(signed_event.to_dict())
        
        async with aiofiles.open(self.file_path, 'a') as f:
            await f.write(event_json + '\n')
            await f.fsync()  # Force write to disk
    
    async def read_all(self) -> List[Dict[str, Any]]:
        """Read all events from WAL."""
        if not self.file_path.exists():
            return []
        
        events = []
        async with aiofiles.open(self.file_path, 'r') as f:
            async for line in f:
                if line.strip():
                    try:
                        event_data = json.loads(line.strip())
                        events.append(event_data)
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
        
        return events
    
    async def close(self):
        """Close WAL file."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


class EventIndex:
    """Index for fast event lookup."""
    
    def __init__(self):
        self.by_id: Dict[str, SignedEvent] = {}
        self.by_type: Dict[EventType, List[str]] = {}
        self.by_plane: Dict[str, List[str]] = {}
        self.by_timestamp: List[tuple] = []  # (timestamp, event_id)
    
    def add_event(self, event: SignedEvent):
        """Add event to index."""
        self.by_id[event.event_id] = event
        
        if event.event_type not in self.by_type:
            self.by_type[event.event_type] = []
        self.by_type[event.event_type].append(event.event_id)
        
        if event.plane not in self.by_plane:
            self.by_plane[event.plane] = []
        self.by_plane[event.plane].append(event.event_id)
        
        # Insert into timestamp-sorted list
        self.by_timestamp.append((event.timestamp, event.event_id))
        self.by_timestamp.sort(key=lambda x: x[0])
    
    def get_events_by_type(self, event_type: EventType) -> List[SignedEvent]:
        """Get events by type."""
        event_ids = self.by_type.get(event_type, [])
        return [self.by_id[eid] for eid in event_ids]
    
    def get_events_by_plane(self, plane: str) -> List[SignedEvent]:
        """Get events by plane."""
        event_ids = self.by_plane.get(plane, [])
        return [self.by_id[eid] for eid in event_ids]
    
    def get_events_in_timerange(self, 
                               start_time: float, 
                               end_time: float) -> List[SignedEvent]:
        """Get events in time range."""
        event_ids = []
        for timestamp, event_id in self.by_timestamp:
            if start_time <= timestamp <= end_time:
                event_ids.append(event_id)
        
        return [self.by_id[eid] for eid in event_ids]


class ImmutableEventLog:
    """
    Immutable append-only event log with external oracle validation.
    
    Key properties:
    - Append-only (no modification)
    - Cryptographically signed events
    - External oracle validation
    - Replayable for analysis
    """
    
    def __init__(self, 
                 storage_path: str,
                 signing_key: Optional[str] = None):
        self.storage_path = storage_path
        self.signing_key = signing_key or hashlib.sha256(b"event-horizon-default").hexdigest()
        
        # Components
        self.wal = WALFile(f"{storage_path}/events.wal")
        self.index = EventIndex()
        self.oracle_validations: Dict[str, Dict[str, Any]] = {}
        
        # State
        self._initialized = False
    
    async def initialize(self):
        """Initialize the event log."""
        if self._initialized:
            return
        
        # Load existing events
        existing_events = await self.wal.read_all()
        
        for event_data in existing_events:
            try:
                # Validate signature
                event = self._validate_and_create_event(event_data)
                if event:
                    self.index.add_event(event)
            except Exception:
                continue  # Skip invalid events
        
        self._initialized = True
    
    async def append(self, 
                   event_type: EventType,
                   plane: str,
                   data: Dict[str, Any],
                   previous_event_hash: Optional[str] = None) -> SignedEvent:
        """
        Append new event to immutable log.
        
        Returns the signed event.
        """
        if not self._initialized:
            await self.initialize()
        
        # Create event
        event_id = hashlib.sha256(
            f"{time.time()}{plane}{event_type.value}{json.dumps(data, sort_keys=True)}"
            .encode()
        ).hexdigest()
        
        event = SignedEvent(
            event_id=event_id,
            timestamp=time.time(),
            event_type=event_type,
            plane=plane,
            data=data,
            signature=self._sign_event_data(event_id, plane, event_type, data),
            previous_event_hash=previous_event_hash
        )
        
        # Append to WAL
        await self.wal.append(event)
        
        # Update index
        self.index.add_event(event)
        
        return event
    
    async def append_with_oracle_validation(self,
                                        event_type: EventType,
                                        plane: str,
                                        data: Dict[str, Any],
                                        oracle_validation: Optional[Dict[str, Any]] = None) -> SignedEvent:
        """
        Append event with external oracle validation.
        """
        event = await self.append(event_type, plane, data)
        
        if oracle_validation:
            self.oracle_validations[event.event_id] = {
                'validation': oracle_validation,
                'timestamp': time.time(),
                'event_hash': event.calculate_hash()
            }
        
        return event
    
    async def replay(self, 
                    from_timestamp: float = 0.0,
                    to_timestamp: Optional[float] = None) -> 'EventStream':
        """
        Replay events from immutable log.
        
        Returns EventStream for iteration.
        """
        if not self._initialized:
            await self.initialize()
        
        events = self.index.get_events_in_timerange(
            from_timestamp, 
            to_timestamp or time.time()
        )
        
        return EventStream(events)
    
    async def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify cryptographic integrity of event chain.
        """
        if not self._initialized:
            await self.initialize()
        
        # Get all events sorted by timestamp
        all_events = sorted(
            self.index.by_id.values(),
            key=lambda e: e.timestamp
        )
        
        verification_results = {
            'total_events': len(all_events),
            'valid_signatures': 0,
            'invalid_signatures': 0,
            'chain_breaks': 0,
            'oracle_validations': 0,
            'details': []
        }
        
        previous_hash = None
        for event in all_events:
            # Verify signature
            expected_signature = self._sign_event_data(
                event.event_id, event.plane, event.event_type, event.data
            )
            
            if hmac.compare_digest(event.signature, expected_signature):
                verification_results['valid_signatures'] += 1
            else:
                verification_results['invalid_signatures'] += 1
                verification_results['details'].append({
                    'event_id': event.event_id,
                    'issue': 'invalid_signature'
                })
            
            # Verify chain integrity
            if previous_hash and event.previous_event_hash:
                if not hmac.compare_digest(previous_hash, event.previous_event_hash):
                    verification_results['chain_breaks'] += 1
                    verification_results['details'].append({
                        'event_id': event.event_id,
                        'issue': 'chain_break',
                        'expected': previous_hash,
                        'actual': event.previous_event_hash
                    })
            
            # Check oracle validation
            if event.event_id in self.oracle_validations:
                verification_results['oracle_validations'] += 1
            
            previous_hash = event.calculate_hash()
        
        return verification_results
    
    def _sign_event_data(self, 
                         event_id: str, 
                         plane: str, 
                         event_type: EventType, 
                         data: Dict[str, Any]) -> str:
        """Sign event data with HMAC."""
        content = json.dumps({
            'event_id': event_id,
            'plane': plane,
            'event_type': event_type.value,
            'data': data
        }, sort_keys=True)
        
        return hmac.new(
            self.signing_key.encode(),
            content.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _validate_and_create_event(self, event_data: Dict[str, Any]) -> Optional[SignedEvent]:
        """Validate and create event from data."""
        try:
            # Reconstruct event
            event = SignedEvent(
                event_id=event_data['event_id'],
                timestamp=event_data['timestamp'],
                event_type=EventType(event_data['event_type']),
                plane=event_data['plane'],
                data=event_data['data'],
                signature=event_data['signature'],
                previous_event_hash=event_data.get('previous_event_hash')
            )
            
            # Verify signature
            expected_signature = self._sign_event_data(
                event.event_id, event.plane, event.event_type, event.data
            )
            
            if not hmac.compare_digest(event.signature, expected_signature):
                return None
            
            return event
            
        except (KeyError, ValueError):
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get log statistics."""
        if not self._initialized:
            return {'initialized': False}
        
        return {
            'initialized': True,
            'total_events': len(self.index.by_id),
            'event_types': {et.value: len(eids) for et, eids in self.index.by_type.items()},
            'planes': {plane: len(eids) for plane, eids in self.index.by_plane.items()},
            'oracle_validations': len(self.oracle_validations),
            'time_range': {
                'earliest': self.index.by_timestamp[0][0] if self.index.by_timestamp else None,
                'latest': self.index.by_timestamp[-1][0] if self.index.by_timestamp else None
            }
        }


class EventStream:
    """Stream of events for replay."""
    
    def __init__(self, events: List[SignedEvent]):
        self.events = events
        self._position = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self) -> SignedEvent:
        if self._position >= len(self.events):
            raise StopAsyncIteration
        
        event = self.events[self._position]
        self._position += 1
        return event
    
    def reset(self):
        """Reset stream position."""
        self._position = 0
    
    def get_remaining_count(self) -> int:
        """Get count of remaining events."""
        return len(self.events) - self._position
