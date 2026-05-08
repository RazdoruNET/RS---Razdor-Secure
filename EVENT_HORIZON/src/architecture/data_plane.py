"""
Data Plane - Execution only layer

Responsible for:
- Pure request execution
- Global backpressure control
- Minimal state management
- No planning or decision logic
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import uuid

from .core_constraints import (
    PlaneType, ExecutionCycleManager, ArchitecturalViolationError,
    ObservationControlSeparation
)
from .system_pressure import SystemPressure, GlobalBackpressureController


class ExecutionState(Enum):
    """Request execution states."""
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    THROTTLED = "throttled"


@dataclass
class RequestContext:
    """Context for individual request execution."""
    request_id: str
    execution_contract_id: str
    timestamp: float
    backpressure_level: float
    priority: int = 1


@dataclass
class ExecutionResult:
    """Result of request execution."""
    request_id: str
    execution_state: ExecutionState
    start_time: float
    end_time: float
    duration: float
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    backpressure_applied: bool = False
    resource_usage: Optional[Dict[str, float]] = None


class PureExecutionEngine:
    """
    Pure execution engine with no decision logic.
    
    Only executes validated requests according to contracts.
    """
    
    def __init__(self, 
                 cycle_manager: ExecutionCycleManager,
                 backpressure_controller: GlobalBackpressureController):
        self.cycle_manager = cycle_manager
        self.backpressure_controller = backpressure_controller
        
        # Minimal state (only what's necessary for execution)
        self.active_requests: Dict[str, RequestContext] = {}
        self.execution_queue = asyncio.Queue()
        self.execution_semaphore = asyncio.Semaphore(100)  # Max concurrent
        
        # Metrics (read-only for other planes)
        self.execution_stats = {
            'total_executed': 0,
            'total_failed': 0,
            'total_throttled': 0,
            'avg_duration': 0.0,
            'current_backpressure': 0.0
        }
    
    async def execute_validated_request(self, 
                                   request_context: RequestContext,
                                   request_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a pre-validated request.
        
        This method ONLY executes - no decision logic.
        """
        
        # Start execution cycle
        cycle_id = str(uuid.uuid4())
        self.cycle_manager.start_cycle(cycle_id)
        
        try:
            # Validate interaction: Data -> Data (internal)
            self.cycle_manager.record_interaction(
                source_plane=PlaneType.DATA,
                target_plane=PlaneType.DATA,
                interaction_type="request_execution",
                data={"request_id": request_context.request_id}
            )
            
            # Check global backpressure
            throttle_decision = await self.backpressure_controller.should_throttle_execution()
            
            if throttle_decision.should_throttle:
                return await self._handle_throttled_request(
                    request_context, throttle_decision
                )
            
            # Execute request
            return await self._execute_request_internal(request_context, request_data)
            
        finally:
            self.cycle_manager.end_cycle()
    
    async def execute_batch(self, 
                          requests: List[tuple[RequestContext, Dict[str, Any]]]) -> List[ExecutionResult]:
        """Execute batch of requests with backpressure awareness."""
        
        # Check system pressure before batch
        system_pressure = await self.backpressure_controller.get_system_pressure()
        
        if system_pressure.overall_pressure() > 0.9:
            # Reject entire batch under extreme pressure
            return [
                ExecutionResult(
                    request_id=ctx.request_id,
                    execution_state=ExecutionState.FAILED,
                    start_time=time.time(),
                    end_time=time.time(),
                    duration=0.0,
                    error="System under extreme pressure - batch rejected"
                )
                for ctx, _ in requests
            ]
        
        # Execute with concurrency control
        results = []
        semaphore_limit = max(1, int(100 * (1.0 - system_pressure.overall_pressure())))
        
        async with asyncio.Semaphore(semaphore_limit):
            tasks = []
            for request_context, request_data in requests:
                task = asyncio.create_task(
                    self.execute_validated_request(request_context, request_data)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                ctx, _ = requests[i]
                processed_results.append(
                    ExecutionResult(
                        request_id=ctx.request_id,
                        execution_state=ExecutionState.FAILED,
                        start_time=time.time(),
                        end_time=time.time(),
                        duration=0.0,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_request_internal(self, 
                                     request_context: RequestContext,
                                     request_data: Dict[str, Any]) -> ExecutionResult:
        """Internal request execution with minimal logic."""
        
        start_time = time.time()
        
        # Track active request
        self.active_requests[request_context.request_id] = request_context
        
        try:
            async with self.execution_semaphore:
                # Record execution start
                self.execution_stats['total_executed'] += 1
                
                # Execute based on request type
                if request_data.get('type') == 'http_request':
                    result = await self._execute_http_request(request_context, request_data)
                elif request_data.get('type') == 'auth_request':
                    result = await self._execute_auth_request(request_context, request_data)
                else:
                    result = await self._execute_generic_request(request_context, request_data)
                
                # Update statistics
                duration = time.time() - start_time
                self._update_stats(duration, result.execution_state)
                
                return result
                
        except Exception as e:
            # Record failure
            self.execution_stats['total_failed'] += 1
            duration = time.time() - start_time
            self._update_stats(duration, ExecutionState.FAILED)
            
            return ExecutionResult(
                request_id=request_context.request_id,
                execution_state=ExecutionState.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration=duration,
                error=str(e)
            )
            
        finally:
            # Cleanup
            self.active_requests.pop(request_context.request_id, None)
    
    async def _execute_http_request(self, 
                                 request_context: RequestContext,
                                 request_data: Dict[str, Any]) -> ExecutionResult:
        """Execute HTTP request - pure execution only."""
        
        import aiohttp
        
        start_time = time.time()
        
        try:
            # Extract request parameters (no decision logic)
            method = request_data.get('method', 'GET')
            url = request_data.get('url')
            headers = request_data.get('headers', {})
            timeout = request_data.get('timeout', 30.0)
            
            # Execute request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_data = await response.text()
                    
                    return ExecutionResult(
                        request_id=request_context.request_id,
                        execution_state=ExecutionState.COMPLETED,
                        start_time=start_time,
                        end_time=time.time(),
                        duration=time.time() - start_time,
                        status_code=response.status,
                        response_data={"body": response_data, "headers": dict(response.headers)}
                    )
                    
        except asyncio.TimeoutError:
            return ExecutionResult(
                request_id=request_context.request_id,
                execution_state=ExecutionState.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration=time.time() - start_time,
                error="Request timeout"
            )
        except Exception as e:
            return ExecutionResult(
                request_id=request_context.request_id,
                execution_state=ExecutionState.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration=time.time() - start_time,
                error=str(e)
            )
    
    async def _execute_auth_request(self, 
                                 request_context: RequestContext,
                                 request_data: Dict[str, Any]) -> ExecutionResult:
        """Execute authentication request - pure execution only."""
        
        # Similar to HTTP request but with auth-specific handling
        return await self._execute_http_request(request_context, request_data)
    
    async def _execute_generic_request(self, 
                                   request_context: RequestContext,
                                   request_data: Dict[str, Any]) -> ExecutionResult:
        """Execute generic request - pure execution only."""
        
        # Placeholder for generic request execution
        start_time = time.time()
        
        await asyncio.sleep(0.1)  # Simulate work
        
        return ExecutionResult(
            request_id=request_context.request_id,
            execution_state=ExecutionState.COMPLETED,
            start_time=start_time,
            end_time=time.time(),
            duration=time.time() - start_time,
            status_code=200,
            response_data={"message": "Request executed successfully"}
        )
    
    async def _handle_throttled_request(self, 
                                     request_context: RequestContext,
                                     throttle_decision) -> ExecutionResult:
        """Handle throttled request due to backpressure."""
        
        self.execution_stats['total_throttled'] += 1
        
        return ExecutionResult(
            request_id=request_context.request_id,
            execution_state=ExecutionState.THROTTLED,
            start_time=time.time(),
            end_time=time.time(),
            duration=0.0,
            backpressure_applied=True,
            error=f"Request throttled: {throttle_decision.reason}"
        )
    
    def _update_stats(self, duration: float, execution_state: ExecutionState):
        """Update execution statistics."""
        # Update average duration
        total = self.execution_stats['total_executed']
        current_avg = self.execution_stats['avg_duration']
        self.execution_stats['avg_duration'] = (current_avg * (total - 1) + duration) / total
        
        # Update current backpressure
        self.execution_stats['current_backpressure'] = (
            self.backpressure_controller.get_current_pressure()
        )
    
    def get_current_backpressure(self) -> float:
        """Get current backpressure level."""
        return self.execution_stats['current_backpressure']
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get read-only execution statistics."""
        return self.execution_stats.copy()
    
    def get_active_requests_count(self) -> int:
        """Get count of currently active requests."""
        return len(self.active_requests)
    
    async def shutdown(self):
        """Graceful shutdown of execution engine."""
        # Wait for active requests to complete
        while self.active_requests:
            await asyncio.sleep(0.1)
        
        # Clear queue
        while not self.execution_queue.empty():
            try:
                self.execution_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
