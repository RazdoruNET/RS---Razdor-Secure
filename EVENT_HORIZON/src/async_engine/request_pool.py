"""
Request Pool

Connection and request pool management for optimal
resource utilization during high-load testing.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time


class PoolState(Enum):
    """Pool state enumeration."""
    IDLE = "idle"
    ACTIVE = "active"
    DRAINING = "draining"
    CLOSED = "closed"


@dataclass
class PoolStatistics:
    """Statistics for the request pool."""
    total_requests: int = 0
    active_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    avg_concurrent_requests: float = 0.0
    peak_concurrent_requests: int = 0
    total_wait_time: float = 0.0
    avg_wait_time: float = 0.0


class RequestPool:
    """
    Connection and request pool manager for optimal resource utilization.
    """
    
    def __init__(self, max_concurrent: int = 100):
        """
        Initialize the request pool.
        
        Args:
            max_concurrent: Maximum number of concurrent requests
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        self.state = PoolState.IDLE
        self.statistics = PoolStatistics()
        
        # Track active requests
        self.active_requests: Dict[str, float] = {}
        self.request_history: List[float] = []
        
        # Timing statistics
        self.start_time = time.time()
        self.last_activity = time.time()
    
    async def acquire(self, request_id: Optional[str] = None) -> bool:
        """
        Acquire a slot from the pool.
        
        Args:
            request_id: Optional request identifier
            
        Returns:
            True if slot acquired, False if pool is closed
        """
        if self.state == PoolState.CLOSED:
            return False
        
        wait_start = time.time()
        
        # Acquire semaphore slot
        await self.semaphore.acquire()
        
        wait_time = time.time() - wait_start
        self.statistics.total_wait_time += wait_time
        
        # Track active request
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000000)}"
        
        self.active_requests[request_id] = time.time()
        self.statistics.total_requests += 1
        self.statistics.active_requests = len(self.active_requests)
        
        # Update peak concurrent requests
        if self.statistics.active_requests > self.statistics.peak_concurrent_requests:
            self.statistics.peak_concurrent_requests = self.statistics.active_requests
        
        # Update average concurrent requests
        elapsed = time.time() - self.start_time
        self.statistics.avg_concurrent_requests = (
            self.statistics.total_requests / elapsed
        ) if elapsed > 0 else 0
        
        self.last_activity = time.time()
        
        return True
    
    def release(self, request_id: Optional[str] = None):
        """
        Release a slot back to the pool.
        
        Args:
            request_id: Request identifier to release
        """
        if request_id and request_id in self.active_requests:
            del self.active_requests[request_id]
        
        self.semaphore.release()
        self.statistics.active_requests = len(self.active_requests)
        
        # Update average wait time
        if self.statistics.total_requests > 0:
            self.statistics.avg_wait_time = (
                self.statistics.total_wait_time / self.statistics.total_requests
            )
        
        self.last_activity = time.time()
    
    async def execute_with_pool(self, coro, request_id: Optional[str] = None):
        """
        Execute a coroutine within the pool constraints.
        
        Args:
            coro: Coroutine to execute
            request_id: Optional request identifier
            
        Returns:
            Result of the coroutine
        """
        if not await self.acquire(request_id):
            raise RuntimeError("Pool is closed")
        
        try:
            result = await coro
            self.statistics.completed_requests += 1
            return result
        except Exception:
            self.statistics.failed_requests += 1
            raise
        finally:
            self.release(request_id)
    
    def get_available_slots(self) -> int:
        """Get number of available slots in the pool."""
        return self.semaphore._value
    
    def get_utilization(self) -> float:
        """Get current pool utilization (0.0 to 1.0)."""
        used = self.max_concurrent - self.get_available_slots()
        return used / self.max_concurrent
    
    def get_statistics(self) -> PoolStatistics:
        """Get current pool statistics."""
        stats = PoolStatistics(
            total_requests=self.statistics.total_requests,
            active_requests=self.statistics.active_requests,
            completed_requests=self.statistics.completed_requests,
            failed_requests=self.statistics.failed_requests,
            avg_concurrent_requests=self.statistics.avg_concurrent_requests,
            peak_concurrent_requests=self.statistics.peak_concurrent_requests,
            total_wait_time=self.statistics.total_wait_time,
            avg_wait_time=self.statistics.avg_wait_time
        )
        
        # Calculate success rate
        if stats.total_requests > 0:
            stats.success_rate = stats.completed_requests / stats.total_requests
        else:
            stats.success_rate = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset pool statistics."""
        self.statistics = PoolStatistics()
        self.start_time = time.time()
        self.request_history.clear()
    
    def set_state(self, state: PoolState):
        """Set pool state."""
        self.state = state
    
    def close(self):
        """Close the pool and reject new requests."""
        self.set_state(PoolState.CLOSED)
    
    def is_closed(self) -> bool:
        """Check if pool is closed."""
        return self.state == PoolState.CLOSED
    
    async def wait_for_completion(self, timeout: Optional[float] = None):
        """
        Wait for all active requests to complete.
        
        Args:
            timeout: Optional timeout in seconds
        """
        if self.state == PoolState.IDLE:
            return
        
        self.set_state(PoolState.DRAINING)
        
        start_time = time.time()
        
        while self.active_requests and (timeout is None or time.time() - start_time < timeout):
            await asyncio.sleep(0.1)
        
        # Force close if timeout exceeded
        if self.active_requests and timeout and time.time() - start_time >= timeout:
            self.active_requests.clear()
            self.statistics.failed_requests += len(self.active_requests)
        
        self.set_state(PoolState.IDLE)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.set_state(PoolState.ACTIVE)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.wait_for_completion()
        self.close()
    
    def __len__(self) -> int:
        """Return number of active requests."""
        return len(self.active_requests)
    
    def __repr__(self) -> str:
        """String representation of pool state."""
        return (f"RequestPool(state={self.state.value}, "
                f"active={len(self.active_requests)}/{self.max_concurrent}, "
                f"utilization={self.get_utilization():.2%})")
