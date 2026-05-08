"""
Stability Controller

Coordinates safety mechanisms including error monitoring, circuit breaking,
and adaptive backoff to maintain system stability during testing.
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .error_monitor import ErrorMonitor, ErrorType, AlertLevel
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from .adaptive_backoff import AdaptiveBackoff, BackoffConfig, BackoffStrategy


class StabilityLevel(Enum):
    """System stability levels."""
    STABLE = "stable"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNSTABLE = "unstable"


@dataclass
class StabilityConfig:
    """Configuration for stability controller."""
    error_rate_threshold: float = 0.1      # 10% error rate threshold
    latency_threshold: float = 5.0          # 5 second latency threshold
    circuit_breaker_threshold: int = 5      # Circuit breaker failure threshold
    recovery_timeout: float = 60.0           # Circuit breaker recovery timeout
    max_concurrent_requests: int = 100      # Max concurrent requests
    adaptive_backoff_enabled: bool = True    # Enable adaptive backoff
    auto_recovery_enabled: bool = True       # Enable automatic recovery


@dataclass
class StabilityMetrics:
    """Metrics for stability controller."""
    current_level: StabilityLevel = StabilityLevel.STABLE
    overall_health_score: float = 1.0        # 0.0 to 1.0
    error_rate: float = 0.0
    avg_latency: float = 0.0
    active_circuits: int = 0
    recovery_attempts: int = 0
    last_stability_check: float = 0.0
    level_transitions: Dict[StabilityLevel, int] = None
    
    def __post_init__(self):
        if self.level_transitions is None:
            self.level_transitions = {level: 0 for level in StabilityLevel}


class StabilityController:
    """
    Coordinates safety mechanisms to maintain system stability.
    """
    
    def __init__(self, config: Optional[StabilityConfig] = None):
        """
        Initialize stability controller.
        
        Args:
            config: Stability configuration
        """
        self.config = config or StabilityConfig()
        self.metrics = StabilityMetrics()
        
        # Initialize components
        self.error_monitor = ErrorMonitor()
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=self.config.circuit_breaker_threshold,
                recovery_timeout=self.config.recovery_timeout
            ),
            name="main_circuit"
        )
        self.adaptive_backoff = AdaptiveBackoff(
            BackoffConfig(
                strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
                max_retries=3
            ) if self.config.adaptive_backoff_enabled else None
        )
        
        # State management
        self.current_level = StabilityLevel.STABLE
        self.last_level_change = time.time()
        self.stability_history: List[Dict[str, Any]] = []
        
        # Callbacks
        self.stability_callbacks: List[Callable[[StabilityLevel, StabilityLevel], None]] = []
        self.emergency_callbacks: List[Callable[[], None]] = []
        
        # Setup component interactions
        self._setup_component_callbacks()
        
        # Background monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_active = False
    
    def _setup_component_callbacks(self):
        """Setup callbacks between components."""
        # Error monitor callbacks
        self.error_monitor.add_alert_callback(self._on_error_alert)
        
        # Circuit breaker callbacks
        self.circuit_breaker.add_state_change_callback(self._on_circuit_state_change)
        self.circuit_breaker.add_failure_callback(self._on_circuit_failure)
    
    def add_stability_callback(self, callback: Callable[[StabilityLevel, StabilityLevel], None]):
        """Add callback for stability level changes."""
        self.stability_callbacks.append(callback)
    
    def add_emergency_callback(self, callback: Callable[[], None]):
        """Add callback for emergency conditions."""
        self.emergency_callbacks.append(callback)
    
    async def start_monitoring(self, interval: float = 5.0):
        """
        Start background stability monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
    
    async def stop_monitoring(self):
        """Stop background stability monitoring."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _monitoring_loop(self, interval: float):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                await self._check_stability()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception:
                # Don't let monitoring errors break the loop
                await asyncio.sleep(interval)
    
    async def execute_with_protection(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with full stability protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        start_time = time.time()
        
        try:
            # Check if we should execute based on stability level
            if not self._should_allow_execution():
                raise StabilityControllerError(f"Execution blocked at stability level: {self.current_level}")
            
            # Execute with circuit breaker
            if self.adaptive_backoff:
                result = await self.circuit_breaker.call(
                    self.adaptive_backoff.execute_with_backoff,
                    func, *args, **kwargs
                )
            else:
                result = await self.circuit_breaker.call(func, *args, **kwargs)
            
            # Record success
            execution_time = time.time() - start_time
            self._record_execution_success(execution_time)
            
            return result
        
        except Exception as e:
            # Record failure
            execution_time = time.time() - start_time
            self._record_execution_failure(e, execution_time)
            raise
    
    def _should_allow_execution(self) -> bool:
        """Check if execution should be allowed based on stability level."""
        if self.current_level == StabilityLevel.CRITICAL:
            return False
        elif self.current_level == StabilityLevel.UNSTABLE:
            # Allow limited execution in unstable state
            return self.circuit_breaker.get_state() != CircuitState.OPEN
        else:
            return True
    
    def _record_execution_success(self, execution_time: float):
        """Record successful execution."""
        self.error_monitor.record_request(True, execution_time)
        
        # Check for high latency
        if execution_time > self.config.latency_threshold:
            self.error_monitor.record_high_latency(
                "unknown",
                execution_time,
                self.config.latency_threshold
            )
    
    def _record_execution_failure(self, exception: Exception, execution_time: float):
        """Record failed execution."""
        self.error_monitor.record_request(False, execution_time)
        
        # Classify and record error
        if "timeout" in str(exception).lower():
            self.error_monitor.record_timeout("unknown", execution_time)
        elif "connection" in str(exception).lower():
            self.error_monitor.record_connection_error("unknown", str(exception))
        else:
            self.error_monitor.record_error(
                ErrorType.HTTP_5XX,
                f"Execution failed: {str(exception)}",
                AlertLevel.WARNING
            )
    
    async def _check_stability(self):
        """Check overall system stability."""
        current_time = time.time()
        
        # Get metrics from components
        error_metrics = self.error_monitor.get_metrics()
        circuit_metrics = self.circuit_breaker.get_metrics()
        health_status = self.error_monitor.get_health_status()
        
        # Calculate stability metrics
        self.metrics.error_rate = error_metrics.error_rate
        self.metrics.avg_latency = self._calculate_avg_latency()
        self.metrics.active_circuits = 1 if self.circuit_breaker.get_state() == CircuitState.OPEN else 0
        self.metrics.last_stability_check = current_time
        
        # Determine stability level
        new_level = self._determine_stability_level(health_status, circuit_metrics)
        
        # Update level if changed
        if new_level != self.current_level:
            await self._change_stability_level(new_level)
        
        # Update health score
        self.metrics.overall_health_score = self._calculate_health_score()
        
        # Record stability check
        self._record_stability_check()
        
        # Trigger recovery if needed
        if self.config.auto_recovery_enabled and self.current_level in [StabilityLevel.CRITICAL, StabilityLevel.UNSTABLE]:
            await self._attempt_recovery()
    
    def _determine_stability_level(self, health_status: Dict[str, Any], 
                                 circuit_metrics: Any) -> StabilityLevel:
        """Determine current stability level."""
        error_rate = health_status.get("error_rate", 0.0)
        active_alerts = health_status.get("active_alerts", 0)
        
        # Critical conditions
        if (error_rate > 0.5 or 
            active_alerts > 5 or
            self.circuit_breaker.get_state() == CircuitState.OPEN):
            return StabilityLevel.CRITICAL
        
        # Unstable conditions
        elif (error_rate > 0.3 or 
              active_alerts > 3 or
              circuit_metrics.current_failures > self.config.circuit_breaker_threshold):
            return StabilityLevel.UNSTABLE
        
        # Degraded conditions
        elif (error_rate > self.config.error_rate_threshold or 
              active_alerts > 1):
            return StabilityLevel.DEGRADED
        
        # Warning conditions
        elif error_rate > self.config.error_rate_threshold * 0.5:
            return StabilityLevel.WARNING
        
        # Stable
        else:
            return StabilityLevel.STABLE
    
    async def _change_stability_level(self, new_level: StabilityLevel):
        """Change stability level and trigger callbacks."""
        old_level = self.current_level
        self.current_level = new_level
        self.last_level_change = time.time()
        
        # Update metrics
        self.metrics.level_transitions[new_level] += 1
        self.metrics.current_level = new_level
        
        # Trigger callbacks
        for callback in self.stability_callbacks:
            try:
                callback(old_level, new_level)
            except Exception:
                pass
        
        # Trigger emergency callbacks for critical conditions
        if new_level == StabilityLevel.CRITICAL:
            for callback in self.emergency_callbacks:
                try:
                    callback()
                except Exception:
                    pass
    
    def _calculate_health_score(self) -> float:
        """Calculate overall health score (0.0 to 1.0)."""
        # Base score starts at 1.0
        score = 1.0
        
        # Reduce based on error rate
        score -= self.metrics.error_rate * 0.5
        
        # Reduce based on active circuits
        score -= self.metrics.active_circuits * 0.3
        
        # Reduce based on stability level
        level_penalties = {
            StabilityLevel.STABLE: 0.0,
            StabilityLevel.WARNING: 0.1,
            StabilityLevel.DEGRADED: 0.3,
            StabilityLevel.UNSTABLE: 0.6,
            StabilityLevel.CRITICAL: 0.9
        }
        score -= level_penalties[self.current_level]
        
        return max(0.0, min(1.0, score))
    
    def _calculate_avg_latency(self) -> float:
        """Calculate average latency from recent requests."""
        # This is a simplified calculation
        # In practice, you'd track latency more comprehensively
        return self.error_monitor.get_metrics().avg_error_frequency
    
    def _record_stability_check(self):
        """Record stability check in history."""
        check_record = {
            "timestamp": time.time(),
            "level": self.current_level.value,
            "health_score": self.metrics.overall_health_score,
            "error_rate": self.metrics.error_rate,
            "avg_latency": self.metrics.avg_latency,
            "active_circuits": self.metrics.active_circuits
        }
        
        self.stability_history.append(check_record)
        
        # Keep only recent history (last 1000 checks)
        if len(self.stability_history) > 1000:
            self.stability_history = self.stability_history[-1000:]
    
    async def _attempt_recovery(self):
        """Attempt automatic recovery."""
        self.metrics.recovery_attempts += 1
        
        # Force circuit breaker to half-open if it's open
        if self.circuit_breaker.get_state() == CircuitState.OPEN:
            self.circuit_breaker._change_state(CircuitState.HALF_OPEN)
        
        # Reduce system load
        if self.adaptive_backoff:
            self.adaptive_backoff.update_system_load(0.5)  # Reduce load by 50%
        
        # Wait a bit before allowing normal operations
        await asyncio.sleep(5.0)
    
    def _on_error_alert(self, alert_event):
        """Handle error alerts from monitor."""
        # Update adaptive backoff based on error rate
        if self.adaptive_backoff:
            error_rate = self.error_monitor.get_error_rate(60)  # Last minute
            self.adaptive_backoff.update_error_rate(error_rate)
    
    def _on_circuit_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """Handle circuit breaker state changes."""
        if new_state == CircuitState.OPEN:
            self.error_monitor.record_error(
                ErrorType.CIRCUIT_BREAK,
                "Circuit breaker opened due to failures",
                AlertLevel.CRITICAL
            )
    
    def _on_circuit_failure(self, exception: Exception, context: Dict[str, Any]):
        """Handle circuit breaker failures."""
        self.error_monitor.record_error(
            ErrorType.HTTP_5XX,
            f"Circuit breaker failure: {str(exception)}",
            AlertLevel.WARNING,
            context
        )
    
    def get_stability_level(self) -> StabilityLevel:
        """Get current stability level."""
        return self.current_level
    
    def get_metrics(self) -> StabilityMetrics:
        """Get stability metrics."""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "stability_level": self.current_level.value,
            "health_score": self.metrics.overall_health_score,
            "error_rate": self.metrics.error_rate,
            "avg_latency": self.metrics.avg_latency,
            "active_circuits": self.metrics.active_circuits,
            "circuit_breaker_state": self.circuit_breaker.get_state().value,
            "recovery_attempts": self.metrics.recovery_attempts,
            "last_check": self.metrics.last_stability_check,
            "uptime": time.time() - (self.stability_history[0]["timestamp"] if self.stability_history else time.time())
        }
    
    def force_stability_level(self, level: StabilityLevel):
        """Force a specific stability level (for testing)."""
        asyncio.create_task(self._change_stability_level(level))
    
    def reset(self):
        """Reset stability controller to initial state."""
        self.current_level = StabilityLevel.STABLE
        self.metrics = StabilityMetrics()
        self.stability_history.clear()
        self.last_level_change = time.time()
        
        # Reset components
        self.error_monitor.reset()
        self.circuit_breaker.reset()
        if self.adaptive_backoff:
            self.adaptive_backoff.reset_metrics()
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external monitoring."""
        return {
            "stability_controller": {
                "health_status": self.get_health_status(),
                "error_monitor": self.error_monitor.export_metrics(),
                "circuit_breaker": self.circuit_breaker.export_metrics(),
                "adaptive_backoff": self.adaptive_backoff.export_metrics() if self.adaptive_backoff else None,
                "stability_history": self.stability_history[-10:],  # Last 10 checks
                "timestamp": time.time()
            }
        }


class StabilityControllerError(Exception):
    """Exception raised by stability controller."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
