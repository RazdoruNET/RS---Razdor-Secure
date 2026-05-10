#!/usr/bin/env python3
"""
Execution Trace Collector - Collector for complete pipeline execution traces
TASK 8.2 - Execution Trace Collector
"""

import time
import uuid
import asyncio
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import deque

class EventType(Enum):
    """Types of events that can be tracked"""
    CONNECTION_ATTEMPT = "connection_attempt"
    CONNECTION_SUCCESS = "connection_success"
    CONNECTION_FAILURE = "connection_failure"
    RETRY_ATTEMPT = "retry_attempt"
    TIMEOUT = "timeout"
    PIPELINE_START = "pipeline_start"
    PIPELINE_END = "pipeline_end"
    ERROR = "error"
    NETWORK_SEND = "network_send"
    NETWORK_RECEIVE = "network_receive"

class NetworkEventType(Enum):
    """Types of network events"""
    CONNECT_ATTEMPT = "connect_attempt"
    CONNECT_SUCCESS = "connect_success"
    CONNECT_FAILURE = "connect_failure"
    SEND_DATA = "send_data"
    RECEIVE_DATA = "receive_data"
    DISCONNECT = "disconnect"

@dataclass
class Event:
    """Single event in execution trace"""
    timestamp: float
    event_type: EventType
    details: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'details': self.details,
            'task_id': self.task_id
        }

@dataclass
class NetworkEvent:
    """Network event with connection details"""
    timestamp: float
    event_type: NetworkEventType
    host: str
    port: int
    details: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'host': self.host,
            'port': self.port,
            'details': self.details,
            'task_id': self.task_id
        }

@dataclass
class ErrorEvent:
    """Error event with full context"""
    timestamp: float
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'task_id': self.task_id
        }

class ExecutionTrace:
    """
    Complete execution trace collector for pipeline runs
    
    Tracks:
    - All connection attempts
    - Retry mechanisms
    - Timeouts
    - Network events
    - Errors
    - General pipeline events
    """
    
    def __init__(self, pipeline_name: str, execution_id: Optional[str] = None):
        self.execution_id = execution_id or str(uuid.uuid4())
        self.pipeline_name = pipeline_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Event storage (simplified - no locking needed for single-threaded async)
        self.events: List[Event] = []
        self.network_events: List[NetworkEvent] = []
        self.errors: List[ErrorEvent] = []
        
        # Connection tracking
        self._connection_attempts: Dict[str, List[float]] = {}
        self._retry_attempts: Dict[str, int] = {}
        self._timeout_events: List[Dict[str, Any]] = []
        
        # Performance metrics
        self._total_bytes_sent = 0
        self._total_bytes_received = 0
        self._connection_count = 0
        self._successful_connections = 0
        
    async def start_execution(self):
        """Mark the start of pipeline execution"""
        self.start_time = time.time()
        await self.add_event(EventType.PIPELINE_START, {
            'pipeline_name': self.pipeline_name,
            'execution_id': self.execution_id
        })
    
    async def end_execution(self, success: bool = True, final_status: str = "completed"):
        """Mark the end of pipeline execution"""
        self.end_time = time.time()
        await self.add_event(EventType.PIPELINE_END, {
            'pipeline_name': self.pipeline_name,
            'execution_id': self.execution_id,
            'success': success,
            'final_status': final_status,
            'duration': self.end_time - self.start_time if self.start_time else 0,
            'total_events': len(self.events),
            'total_network_events': len(self.network_events),
            'total_errors': len(self.errors),
            'connection_attempts': self._connection_count,
            'successful_connections': self._successful_connections,
            'total_bytes_sent': self._total_bytes_sent,
            'total_bytes_received': self._total_bytes_received
        })
    
    async def add_event(self, event_type: EventType, details: Dict[str, Any] = None):
        """Add a general event to the trace"""
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        event = Event(
            timestamp=time.time(),
            event_type=event_type,
            details=details or {},
            task_id=task_id
        )
        self.events.append(event)
    
    async def add_connection_attempt(self, host: str, port: int, method: str = "TCP", details: Dict[str, Any] = None):
        """Track connection attempt - MANDATORY tracking"""
        connection_key = f"{host}:{port}"
        timestamp = time.time()
        
        # Track connection attempts
        if connection_key not in self._connection_attempts:
            self._connection_attempts[connection_key] = []
        self._connection_attempts[connection_key].append(timestamp)
        self._connection_count += 1
        
        # Get task ID
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        # Add network event
        network_event = NetworkEvent(
            timestamp=timestamp,
            event_type=NetworkEventType.CONNECT_ATTEMPT,
            host=host,
            port=port,
            details={
                'method': method,
                'attempt_number': len(self._connection_attempts[connection_key]),
                **(details or {})
            },
            task_id=task_id
        )
        self.network_events.append(network_event)
        
        # Add general event
        await self.add_event(EventType.CONNECTION_ATTEMPT, {
            'host': host,
            'port': port,
            'method': method,
            'attempt_number': len(self._connection_attempts[connection_key]),
            **(details or {})
        })
    
    async def add_connection_success(self, host: str, port: int, details: Dict[str, Any] = None):
        """Track successful connection"""
        connection_key = f"{host}:{port}"
        timestamp = time.time()
        self._successful_connections += 1
        
        # Calculate connection time if we have attempts
        connection_time = 0
        if connection_key in self._connection_attempts and self._connection_attempts[connection_key]:
            last_attempt = self._connection_attempts[connection_key][-1]
            connection_time = timestamp - last_attempt
        
        # Get task ID
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        # Add network event
        network_event = NetworkEvent(
            timestamp=timestamp,
            event_type=NetworkEventType.CONNECT_SUCCESS,
            host=host,
            port=port,
            details={
                'connection_time': connection_time,
                **(details or {})
            },
            task_id=task_id
        )
        self.network_events.append(network_event)
        
        # Add general event
        await self.add_event(EventType.CONNECTION_SUCCESS, {
            'host': host,
            'port': port,
            'connection_time': connection_time,
            **(details or {})
        })
    
    async def add_connection_failure(self, host: str, port: int, error: str, details: Dict[str, Any] = None):
        """Track connection failure"""
        # Get task ID
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        # Add network event
        network_event = NetworkEvent(
            timestamp=time.time(),
            event_type=NetworkEventType.CONNECT_FAILURE,
            host=host,
            port=port,
            details={
                'error': error,
                **(details or {})
            },
            task_id=task_id
        )
        self.network_events.append(network_event)
        
        # Add general event
        await self.add_event(EventType.CONNECTION_FAILURE, {
            'host': host,
            'port': port,
            'error': error,
            **(details or {})
        })
        
        # Add error event
        await self.add_error("CONNECTION_FAILURE", f"Failed to connect to {host}:{port}: {error}", details)
    
    async def add_retry_attempt(self, operation: str, attempt_number: int, max_attempts: int, reason: str = "", details: Dict[str, Any] = None):
        """Track retry attempt - MANDATORY tracking"""
        operation_key = f"{operation}_{id(asyncio.current_task())}" if asyncio.current_task() else f"{operation}_{time.time()}"
        
        # Track retry attempts
        if operation_key not in self._retry_attempts:
            self._retry_attempts[operation_key] = 0
        self._retry_attempts[operation_key] += 1
        
        # Add event
        await self.add_event(EventType.RETRY_ATTEMPT, {
            'operation': operation,
            'attempt_number': attempt_number,
            'max_attempts': max_attempts,
            'reason': reason,
            'total_retries': self._retry_attempts[operation_key],
            **(details or {})
        })
    
    async def add_timeout(self, operation: str, timeout_duration: float, details: Dict[str, Any] = None):
        """Track timeout event - MANDATORY tracking"""
        timeout_info = {
            'timestamp': time.time(),
            'operation': operation,
            'timeout_duration': timeout_duration,
            **(details or {})
        }
        self._timeout_events.append(timeout_info)
        
        # Add event
        await self.add_event(EventType.TIMEOUT, timeout_info)
        
        # Add error event
        await self.add_error("TIMEOUT", f"Operation '{operation}' timed out after {timeout_duration}s", details)
    
    async def add_network_send(self, host: str, port: int, data_size: int, details: Dict[str, Any] = None):
        """Track network data send"""
        self._total_bytes_sent += data_size
        
        # Get task ID
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        network_event = NetworkEvent(
            timestamp=time.time(),
            event_type=NetworkEventType.SEND_DATA,
            host=host,
            port=port,
            details={
                'data_size': data_size,
                'total_bytes_sent': self._total_bytes_sent,
                **(details or {})
            },
            task_id=task_id
        )
        self.network_events.append(network_event)
        
        await self.add_event(EventType.NETWORK_SEND, {
            'host': host,
            'port': port,
            'data_size': data_size,
            **(details or {})
        })
    
    async def add_network_receive(self, host: str, port: int, data_size: int, details: Dict[str, Any] = None):
        """Track network data receive"""
        self._total_bytes_received += data_size
        
        # Get task ID
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        network_event = NetworkEvent(
            timestamp=time.time(),
            event_type=NetworkEventType.RECEIVE_DATA,
            host=host,
            port=port,
            details={
                'data_size': data_size,
                'total_bytes_received': self._total_bytes_received,
                **(details or {})
            },
            task_id=task_id
        )
        self.network_events.append(network_event)
        
        await self.add_event(EventType.NETWORK_RECEIVE, {
            'host': host,
            'port': port,
            'data_size': data_size,
            **(details or {})
        })
    
    async def add_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None, stack_trace: str = None):
        """Track error event"""
        # Get task ID
        try:
            task_id = id(asyncio.current_task())
        except:
            task_id = None
        
        error_event = ErrorEvent(
            timestamp=time.time(),
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context or {},
            task_id=task_id
        )
        self.errors.append(error_event)
        
        # Also add as general event
        await self.add_event(EventType.ERROR, {
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        })
    
    def get_duration(self) -> float:
        """Get total execution duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    async def get_connection_statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'total_attempts': self._connection_count,
            'successful_connections': self._successful_connections,
            'failed_connections': self._connection_count - self._successful_connections,
            'success_rate': (self._successful_connections / self._connection_count) if self._connection_count > 0 else 0,
            'unique_hosts': len(set(event.host for event in self.network_events)),
            'total_retries': sum(self._retry_attempts.values()),
            'total_timeouts': len(self._timeout_events),
            'total_bytes_sent': self._total_bytes_sent,
            'total_bytes_received': self._total_bytes_received
        }
    
    async def get_timeline_summary(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of all events"""
        all_events = []
        
        # Add all events with type markers
        for event in self.events:
            event_dict = event.to_dict()
            event_dict['event_category'] = 'general'
            all_events.append(event_dict)
        
        for network_event in self.network_events:
            event_dict = network_event.to_dict()
            event_dict['event_category'] = 'network'
            all_events.append(event_dict)
        
        for error_event in self.errors:
            event_dict = error_event.to_dict()
            event_dict['event_category'] = 'error'
            all_events.append(event_dict)
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x['timestamp'])
        
        return all_events
    
    async def to_dict(self) -> Dict[str, Any]:
        """Convert entire trace to dictionary for serialization"""
        return {
            'execution_id': self.execution_id,
            'pipeline_name': self.pipeline_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.get_duration(),
            'events': [event.to_dict() for event in self.events],
            'network_events': [event.to_dict() for event in self.network_events],
            'errors': [error.to_dict() for error in self.errors],
            'connection_statistics': await self.get_connection_statistics(),
            'connection_attempts': dict(self._connection_attempts),
            'retry_attempts': dict(self._retry_attempts),
            'timeout_events': self._timeout_events
        }
    
    async def to_json(self, indent: int = 2) -> str:
        """Convert trace to JSON string"""
        trace_dict = await self.to_dict()
        return json.dumps(trace_dict, indent=indent, default=str)
    
    async def save_to_file(self, filepath: str):
        """Save trace to file"""
        try:
            json_data = await self.to_json()
            with open(filepath, 'w') as f:
                f.write(json_data)
        except Exception as e:
            await self.add_error("FILE_SAVE_ERROR", f"Failed to save trace to {filepath}: {str(e)}")
    
    async def get_critical_events(self) -> List[Dict[str, Any]]:
        """Get only critical events (errors, timeouts, connection failures)"""
        critical = []
        
        # Add errors
        for error in self.errors:
            error_dict = error.to_dict()
            error_dict['severity'] = 'error'
            critical.append(error_dict)
        
        # Add timeouts
        for timeout in self._timeout_events:
            timeout_dict = timeout.copy()
            timeout_dict['severity'] = 'warning'
            timeout_dict['event_type'] = 'timeout'
            critical.append(timeout_dict)
        
        # Add connection failures
        for event in self.network_events:
            if event.event_type == NetworkEventType.CONNECT_FAILURE:
                failure_dict = event.to_dict()
                failure_dict['severity'] = 'warning'
                critical.append(failure_dict)
        
        return sorted(critical, key=lambda x: x['timestamp'])
    
    def __str__(self) -> str:
        return f"ExecutionTrace(id={self.execution_id[:8]}..., pipeline={self.pipeline_name}, events={len(self.events)})"
    
    def __repr__(self) -> str:
        return self.__str__()
