"""
Circuit Breaker

Implements circuit breaker pattern for preventing cascade failures
and protecting systems during overload conditions.
"""

import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from collections import deque


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, blocking requests
    HALF_OPEN = "half_open"  # Testing if system has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 60.0     # Seconds to wait before trying recovery
    success_threshold: int = 3          # Successes in half-open to close circuit
    timeout: float = 30.0              # Request timeout
    expected_exception: type = Exception  # Exception type to catch


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    current_failures: int = 0
    state_changes: int = 0
    last_state_change: float = 0.0
    last_failure_time: float = 0.0


class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascade failures.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None,
                 name: str = "default"):
        """
        Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
            name: Circuit breaker name for identification
        """
        self.config = config or CircuitBreakerConfig()
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        
        # Request history for tracking
        self.request_history: deque = deque(maxlen=100)
        
        # State management
        self.last_state_change = time.time()
        self.half_open_successes = 0
        
        # Callbacks
        self.state_change_callbacks: List[Callable[[CircuitState, CircuitState], None]] = []
        self.failure_callbacks: List[Callable[[Exception, Dict[str, Any]], None]] = []
    
    def add_state_change_callback(self, callback: Callable[[CircuitState, CircuitState], None]):
        """Add callback for state change notifications."""
        self.state_change_callbacks.append(callback)
    
    def add_failure_callback(self, callback: Callable[[Exception, Dict[str, Any]], None]):
        """Add callback for failure notifications."""
        self.failure_callbacks.append(callback)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function call
        """
        if not self.allow_request():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
        
        start_time = time.time()
        
        try:
            # Execute the function with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: func(*args, **kwargs)
                )
            
            # Record success
            self.record_success()
            
            return result
        
        except asyncio.TimeoutError as e:
            # Record timeout as failure
            self.record_failure(e, {"timeout": self.config.timeout, "execution_time": time.time() - start_time})
            raise
        
        except Exception as e:
            # Record failure
            self.record_failure(e, {"execution_time": time.time() - start_time})
            raise
    
    def allow_request(self) -> bool:
        """
        Check if request should be allowed based on circuit state.
        
        Returns:
            True if request is allowed
        """
        current_time = time.time()
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.last_state_change >= self.config.recovery_timeout:
                self._change_state(CircuitState.HALF_OPEN)
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        else:  # CLOSED
            return True
    
    def record_success(self):
        """Record a successful request."""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        
        # Reset failure count on success
        if self.state == CircuitState.CLOSED:
            self.metrics.current_failures = 0
        
        elif self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            # Check if we should close the circuit
            if self.half_open_successes >= self.config.success_threshold:
                self._change_state(CircuitState.CLOSED)
                self.metrics.current_failures = 0
                self.half_open_successes = 0
        
        # Record request
        self.request_history.append({
            "timestamp": time.time(),
            "success": True,
            "state": self.state.value
        })
    
    def record_failure(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Record a failed request.
        
        Args:
            exception: The exception that occurred
            context: Additional context information
        """
        if context is None:
            context = {}
        
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.current_failures += 1
        self.metrics.last_failure_time = time.time()
        
        # Trigger failure callbacks
        for callback in self.failure_callbacks:
            try:
                callback(exception, context)
            except Exception:
                pass  # Don't let callback failures break circuit breaker
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED:
            if self.metrics.current_failures >= self.config.failure_threshold:
                self._change_state(CircuitState.OPEN)
        
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit again
            self._change_state(CircuitState.OPEN)
            self.half_open_successes = 0
        
        # Record request
        self.request_history.append({
            "timestamp": time.time(),
            "success": False,
            "state": self.state.value,
            "exception": str(exception),
            "context": context
        })
    
    def _change_state(self, new_state: CircuitState):
        """Change circuit breaker state."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = time.time()
        self.metrics.state_changes += 1
        
        # Trigger state change callbacks
        for callback in self.state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception:
                pass  # Don't let callback failures break circuit breaker
    
    def force_open(self):
        """Force the circuit breaker to open state."""
        self._change_state(CircuitState.OPEN)
    
    def force_close(self):
        """Force the circuit breaker to closed state."""
        self._change_state(CircuitState.CLOSED)
        self.metrics.current_failures = 0
        self.half_open_successes = 0
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get circuit breaker metrics."""
        return self.metrics
    
    def get_success_rate(self, window_seconds: Optional[int] = None) -> float:
        """
        Get success rate for requests.
        
        Args:
            window_seconds: Time window to calculate rate for (None for all time)
            
        Returns:
            Success rate as percentage (0.0 to 1.0)
        """
        if window_seconds is None:
            if self.metrics.total_requests == 0:
                return 1.0
            return self.metrics.successful_requests / self.metrics.total_requests
        
        # Calculate success rate for time window
        current_time = time.time()
        window_start = current_time - window_seconds
        
        window_requests = [r for r in self.request_history if r["timestamp"] >= window_start]
        
        if not window_requests:
            return 1.0
        
        successful = sum(1 for r in window_requests if r["success"])
        return successful / len(window_requests)
    
    def get_failure_rate(self, window_seconds: Optional[int] = None) -> float:
        """
        Get failure rate for requests.
        
        Args:
            window_seconds: Time window to calculate rate for (None for all time)
            
        Returns:
            Failure rate as percentage (0.0 to 1.0)
        """
        return 1.0 - self.get_success_rate(window_seconds)
    
    def time_until_next_attempt(self) -> float:
        """
        Get time until next request attempt will be allowed.
        
        Returns:
            Seconds until next attempt (0.0 if request is allowed now)
        """
        if self.state != CircuitState.OPEN:
            return 0.0
        
        time_since_open = time.time() - self.last_state_change
        time_until_recovery = self.config.recovery_timeout - time_since_open
        
        return max(0.0, time_until_recovery)
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.request_history.clear()
        self.last_state_change = time.time()
        self.half_open_successes = 0
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for external monitoring systems."""
        return {
            "circuit_breaker": {
                "name": self.name,
                "state": self.state.value,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "current_failures": self.metrics.current_failures,
                "success_rate": self.get_success_rate(),
                "failure_rate": self.get_failure_rate(),
                "state_changes": self.metrics.state_changes,
                "time_until_next_attempt": self.time_until_next_attempt(),
                "timestamp": time.time()
            }
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def create_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Create a new circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Circuit breaker configuration
            
        Returns:
            Created circuit breaker
        """
        if name in self.circuit_breakers:
            raise ValueError(f"Circuit breaker '{name}' already exists")
        
        breaker = CircuitBreaker(config, name)
        self.circuit_breakers[name] = breaker
        return breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.circuit_breakers.get(name)
    
    def remove_circuit_breaker(self, name: str):
        """Remove circuit breaker."""
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
    
    def get_all_circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers."""
        return self.circuit_breakers.copy()
    
    def get_open_circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers that are currently open."""
        return {name: breaker for name, breaker in self.circuit_breakers.items() 
                if breaker.get_state() == CircuitState.OPEN}
    
    def force_all_open(self):
        """Force all circuit breakers to open state."""
        for breaker in self.circuit_breakers.values():
            breaker.force_open()
    
    def force_all_closed(self):
        """Force all circuit breakers to closed state."""
        for breaker in self.circuit_breakers.values():
            breaker.force_close()
    
    def export_all_metrics(self) -> Dict[str, Any]:
        """Export metrics for all circuit breakers."""
        return {
            "circuit_breaker_manager": {
                "total_breakers": len(self.circuit_breakers),
                "open_breakers": len(self.get_open_circuit_breakers()),
                "breakers": {
                    name: breaker.export_metrics()["circuit_breaker"]
                    for name, breaker in self.circuit_breakers.items()
                },
                "timestamp": time.time()
            }
        }
