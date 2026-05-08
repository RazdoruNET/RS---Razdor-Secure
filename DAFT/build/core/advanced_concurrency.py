"""
EVENT_HORIZON Advanced Concurrency Model

Implements proper concurrency control with backpressure,
circuit breakers, and graceful degradation handling.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import structlog
from collections import deque, defaultdict

logger = structlog.get_logger(__name__)


class SystemState(Enum):
    """System operational states"""
    HEALTHY = "healthy"
    DEGRADING = "degrading"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"
    RECOVERING = "recovering"


class BackpressureStrategy(Enum):
    """Backpressure handling strategies"""
    DROP_NEWEST = "drop_newest"
    DROP_OLDEST = "drop_oldest"
    QUEUE_FULL_REJECT = "queue_full_reject"
    ADAPTIVE_THROTTLING = "adaptive_throttling"


@dataclass
class ConcurrencyMetrics:
    """Metrics for concurrency monitoring"""
    active_tasks: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    rejected_tasks: int = 0
    average_wait_time: float = 0.0
    peak_concurrency: int = 0
    circuit_breaker_trips: int = 0
    backpressure_activations: int = 0


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds before trying recovery
    expected_exception: type = Exception
    success_threshold: int = 3  # Successes before closing


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = SystemState.HEALTHY
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == SystemState.CIRCUIT_OPEN:
            if time.time() - self.last_failure_time < self.config.recovery_timeout:
                raise Exception("Circuit breaker is OPEN")
            else:
                self.state = SystemState.RECOVERING
                logger.info("Circuit breaker entering recovery state")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.success_count += 1
        if self.state == SystemState.RECOVERING:
            if self.success_count >= self.config.success_threshold:
                self.state = SystemState.HEALTHY
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker recovered")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = SystemState.CIRCUIT_OPEN
            logger.warning("Circuit breaker opened", failure_count=self.failure_count)


class AdaptiveQueue:
    """Adaptive queue with backpressure handling"""
    
    def __init__(self, max_size: int = 1000, strategy: BackpressureStrategy = BackpressureStrategy.DROP_NEWEST):
        self.max_size = max_size
        self.strategy = strategy
        self.queue = deque()
        self.drop_count = 0
        self.reject_count = 0
        self.current_size = 0
    
    async def put(self, item: Any) -> bool:
        """Add item to queue with backpressure handling"""
        if self.current_size >= self.max_size:
            return await self._handle_backpressure(item)
        
        self.queue.append(item)
        self.current_size += 1
        return True
    
    async def get(self) -> Optional[Any]:
        """Get item from queue"""
        if not self.queue:
            return None
        
        item = self.queue.popleft()
        self.current_size -= 1
        return item
    
    async def _handle_backpressure(self, item: Any) -> bool:
        """Handle backpressure based on strategy"""
        if self.strategy == BackpressureStrategy.DROP_NEWEST:
            self.drop_count += 1
            logger.debug("Dropping newest item due to backpressure")
            return False
        
        elif self.strategy == BackpressureStrategy.DROP_OLDEST:
            if self.queue:
                self.queue.popleft()
                self.queue.append(item)
                self.drop_count += 1
                logger.debug("Dropping oldest item due to backpressure")
                return True
            return False
        
        elif self.strategy == BackpressureStrategy.QUEUE_FULL_REJECT:
            self.reject_count += 1
            logger.debug("Rejecting item due to full queue")
            return False
        
        elif self.strategy == BackpressureStrategy.ADAPTIVE_THROTTLING:
            # Implement adaptive throttling
            return await self._adaptive_throttle(item)
        
        return False
    
    async def _adaptive_throttle(self, item: Any) -> bool:
        """Adaptive throttling implementation"""
        # Simplified adaptive throttling
        if self.drop_count > 10:  # High drop rate
            await asyncio.sleep(0.1)  # Add delay
            return True
        return False


class AdvancedConcurrencyManager:
    """Advanced concurrency manager with backpressure and circuit breakers"""
    
    def __init__(self, 
                 max_concurrent_tasks: int = 100,
                 queue_size: int = 1000,
                 backpressure_strategy: BackpressureStrategy = BackpressureStrategy.DROP_NEWEST,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.queue = AdaptiveQueue(queue_size, backpressure_strategy)
        
        # Circuit breakers for different failure types
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        if circuit_breaker_config:
            self.circuit_breakers["default"] = CircuitBreaker(circuit_breaker_config)
        
        # Metrics
        self.metrics = ConcurrencyMetrics()
        self.system_state = SystemState.HEALTHY
        
        # Performance tracking
        self.wait_times = deque(maxlen=1000)
        self.task_start_times: Dict[str, float] = {}
        
        logger.info("Advanced concurrency manager initialized", 
                   max_concurrent=max_concurrent_tasks,
                   queue_size=queue_size)
    
    async def submit_task(self, 
                        task_id: str, 
                        coro, 
                        circuit_breaker_key: str = "default") -> Any:
        """Submit task with advanced concurrency control"""
        start_time = time.time()
        
        # Check system state
        if self.system_state == SystemState.CIRCUIT_OPEN:
            raise Exception("System is in circuit breaker state")
        
        # Check circuit breaker
        if circuit_breaker_key in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[circuit_breaker_key]
            
            async def protected_coro():
                return await circuit_breaker.call(coro)
            
            coro = protected_coro()
        
        # Try to queue the task
        queued = await self.queue.put(task_id)
        if not queued:
            self.metrics.rejected_tasks += 1
            self._update_system_state()
            raise Exception("Task rejected due to backpressure")
        
        self.metrics.queued_tasks += 1
        
        # Wait for semaphore and execute task
        try:
            await self.semaphore.acquire()
            self.metrics.active_tasks += 1
            self.metrics.peak_concurrency = max(self.metrics.peak_concurrency, self.metrics.active_tasks)
            
            # Track wait time
            wait_time = time.time() - start_time
            self.wait_times.append(wait_time)
            self.task_start_times[task_id] = time.time()
            
            # Get task from queue
            queued_task_id = await self.queue.get()
            if queued_task_id != task_id:
                logger.warning("Task ID mismatch", expected=task_id, got=queued_task_id)
            
            # Execute the task
            try:
                result = await coro
                self.metrics.completed_tasks += 1
                return result
            except Exception as e:
                self.metrics.failed_tasks += 1
                self._handle_task_failure(task_id, e)
                raise e
            finally:
                self.task_start_times.pop(task_id, None)
                self.metrics.active_tasks -= 1
                self.semaphore.release()
                self._update_system_state()
        
        except asyncio.TimeoutError:
            self.metrics.failed_tasks += 1
            self.metrics.active_tasks -= 1
            self.semaphore.release()
            self._update_system_state()
            raise Exception("Task timed out")
    
    def _handle_task_failure(self, task_id: str, error: Exception):
        """Handle task failure and update circuit breakers"""
        logger.error("Task failed", task_id=task_id, error=str(error))
        
        # Update circuit breakers
        for circuit_breaker in self.circuit_breakers.values():
            if isinstance(error, circuit_breaker.config.expected_exception):
                circuit_breaker._on_failure()
    
    def _update_system_state(self):
        """Update system state based on metrics"""
        failure_rate = self.metrics.failed_tasks / max(1, self.metrics.completed_tasks + self.metrics.failed_tasks)
        
        if failure_rate > 0.5:  # 50% failure rate
            if self.system_state != SystemState.CIRCUIT_OPEN:
                self.system_state = SystemState.CIRCUIT_OPEN
                logger.warning("System state changed to CIRCUIT_OPEN", failure_rate=failure_rate)
        
        elif failure_rate > 0.2:  # 20% failure rate
            if self.system_state == SystemState.HEALTHY:
                self.system_state = SystemState.DEGRADING
                logger.warning("System state changed to DEGRADING", failure_rate=failure_rate)
        
        elif failure_rate < 0.1:  # 10% failure rate
            if self.system_state in [SystemState.DEGRADING, SystemState.DEGRADED]:
                self.system_state = SystemState.HEALTHY
                logger.info("System state recovered to HEALTHY", failure_rate=failure_rate)
    
    def get_metrics(self) -> ConcurrencyMetrics:
        """Get current concurrency metrics"""
        # Update average wait time
        if self.wait_times:
            self.metrics.average_wait_time = sum(self.wait_times) / len(self.wait_times)
        
        # Update queue size
        self.metrics.queued_tasks = self.queue.current_size
        
        return self.metrics
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        metrics = self.get_metrics()
        
        return {
            "system_state": self.system_state.value,
            "active_tasks": metrics.active_tasks,
            "queued_tasks": metrics.queued_tasks,
            "completed_tasks": metrics.completed_tasks,
            "failed_tasks": metrics.failed_tasks,
            "rejected_tasks": metrics.rejected_tasks,
            "failure_rate": metrics.failed_tasks / max(1, metrics.completed_tasks + metrics.failed_tasks),
            "average_wait_time": metrics.average_wait_time,
            "peak_concurrency": metrics.peak_concurrency,
            "queue_utilization": metrics.queued_tasks / self.queue.max_size,
            "concurrency_utilization": metrics.active_tasks / self.max_concurrent_tasks,
            "circuit_breaker_states": {
                key: cb.state.value for key, cb in self.circuit_breakers.items()
            },
            "backpressure_drops": self.queue.drop_count,
            "backpressure_rejects": self.queue.reject_count
        }
    
    def add_circuit_breaker(self, key: str, config: CircuitBreakerConfig):
        """Add circuit breaker for specific failure type"""
        self.circuit_breakers[key] = CircuitBreaker(config)
        logger.info("Circuit breaker added", key=key)
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = ConcurrencyMetrics()
        self.wait_times.clear()
        self.task_start_times.clear()
        logger.info("Concurrency metrics reset")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down concurrency manager")
        
        # Wait for active tasks to complete (with timeout)
        timeout = 30.0
        start_time = time.time()
        
        while self.metrics.active_tasks > 0 and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        
        if self.metrics.active_tasks > 0:
            logger.warning("Shutdown timeout with active tasks", active_tasks=self.metrics.active_tasks)
        else:
            logger.info("Graceful shutdown completed")
