"""
Adaptive Backoff

Implements adaptive backoff strategies for handling system overload
and preventing cascading failures during testing operations.
"""

import asyncio
import random
import time
import math
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class BackoffStrategy(Enum):
    """Backoff strategy types."""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"
    FIBONACCI = "fibonacci"
    ADAPTIVE = "adaptive"


@dataclass
class BackoffConfig:
    """Configuration for backoff strategy."""
    strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_WITH_JITTER
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    max_retries: int = 10
    adaptive_threshold: float = 0.1  # Error rate threshold for adaptive backoff


@dataclass
class BackoffMetrics:
    """Metrics for backoff operations."""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_delay_time: float = 0.0
    avg_delay_time: float = 0.0
    max_delay_used: float = 0.0
    retry_distribution: Dict[int, int] = None
    
    def __post_init__(self):
        if self.retry_distribution is None:
            self.retry_distribution = {}


class AdaptiveBackoff:
    """
    Implements adaptive backoff strategies for handling system overload.
    """
    
    def __init__(self, config: Optional[BackoffConfig] = None):
        """
        Initialize adaptive backoff.
        
        Args:
            config: Backoff configuration
        """
        self.config = config or BackoffConfig()
        self.metrics = BackoffMetrics()
        
        # Adaptive parameters
        self.current_error_rate = 0.0
        self.system_load_factor = 1.0
        self.last_adjustment_time = time.time()
        
        # Fibonacci sequence for fibonacci backoff
        self.fibonacci_cache = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        
        # Callbacks
        self.backoff_callbacks: List[Callable[[int, float], None]] = []
        self.success_callbacks: List[Callable[[int, float], None]] = []
    
    def add_backoff_callback(self, callback: Callable[[int, float], None]):
        """Add callback for backoff events."""
        self.backoff_callbacks.append(callback)
    
    def add_success_callback(self, callback: Callable[[int, float], None]):
        """Add callback for success events."""
        self.success_callbacks.append(callback)
    
    def calculate_delay(self, attempt: int, error_rate: float = 0.0) -> float:
        """
        Calculate delay based on strategy and attempt number.
        
        Args:
            attempt: Current attempt number (0-based)
            error_rate: Current system error rate (0.0 to 1.0)
            
        Returns:
            Delay in seconds
        """
        self.current_error_rate = error_rate
        
        if self.config.strategy == BackoffStrategy.FIXED:
            delay = self.config.base_delay
        
        elif self.config.strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * (1 + attempt)
        
        elif self.config.strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.multiplier ** attempt)
        
        elif self.config.strategy == BackoffStrategy.EXPONENTIAL_WITH_JITTER:
            delay = self.config.base_delay * (self.config.multiplier ** attempt)
            if self.config.jitter:
                delay = self._add_jitter(delay)
        
        elif self.config.strategy == BackoffStrategy.FIBONACCI:
            delay = self.config.base_delay * self._get_fibonacci(attempt)
        
        elif self.config.strategy == BackoffStrategy.ADAPTIVE:
            delay = self._calculate_adaptive_delay(attempt, error_rate)
        
        else:
            delay = self.config.base_delay
        
        # Apply limits
        delay = min(delay, self.config.max_delay)
        delay = max(delay, 0.0)
        
        return delay
    
    def _add_jitter(self, delay: float) -> float:
        """Add jitter to delay to prevent thundering herd."""
        # Add up to 25% random jitter
        jitter_amount = delay * 0.25 * random.random()
        return delay + jitter_amount
    
    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number."""
        if n < len(self.fibonacci_cache):
            return self.fibonacci_cache[n]
        
        # Calculate additional Fibonacci numbers if needed
        while len(self.fibonacci_cache) <= n:
            next_fib = self.fibonacci_cache[-1] + self.fibonacci_cache[-2]
            self.fibonacci_cache.append(next_fib)
        
        return self.fibonacci_cache[n]
    
    def _calculate_adaptive_delay(self, attempt: int, error_rate: float) -> float:
        """Calculate adaptive delay based on system conditions."""
        # Base exponential delay
        base_delay = self.config.base_delay * (self.config.multiplier ** attempt)
        
        # Adjust based on error rate
        if error_rate > self.config.adaptive_threshold:
            # Increase delay proportionally to error rate
            error_factor = 1.0 + (error_rate - self.config.adaptive_threshold) * 5.0
            base_delay *= error_factor
        
        # Adjust based on system load factor
        base_delay *= self.system_load_factor
        
        # Add jitter
        if self.config.jitter:
            base_delay = self._add_jitter(base_delay)
        
        return base_delay
    
    async def execute_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with automatic backoff and retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(None, func, *args, **kwargs)
                
                # Record success
                execution_time = time.time() - start_time
                self._record_success(attempt, execution_time)
                
                # Trigger success callbacks
                for callback in self.success_callbacks:
                    try:
                        callback(attempt, execution_time)
                    except Exception:
                        pass
                
                return result
            
            except Exception as e:
                last_exception = e
                
                # Record failure
                self._record_failure(attempt)
                
                # Check if we should retry
                if attempt < self.config.max_retries:
                    # Calculate backoff delay
                    delay = self.calculate_delay(attempt, self.current_error_rate)
                    
                    # Trigger backoff callbacks
                    for callback in self.backoff_callbacks:
                        try:
                            callback(attempt, delay)
                        except Exception:
                            pass
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                
                else:
                    # All retries exhausted
                    break
        
        # Re-raise the last exception
        raise last_exception
    
    async def wait_adaptive(self, base_delay: float = 1.0) -> float:
        """
        Wait with adaptive delay based on current system conditions.
        
        Args:
            base_delay: Base delay in seconds
            
        Returns:
            Actual delay used
        """
        # Calculate adaptive delay
        adaptive_delay = base_delay * self.system_load_factor
        
        # Add jitter
        if self.config.jitter:
            adaptive_delay = self._add_jitter(adaptive_delay)
        
        # Apply limits
        adaptive_delay = min(adaptive_delay, self.config.max_delay)
        adaptive_delay = max(adaptive_delay, 0.0)
        
        # Wait
        await asyncio.sleep(adaptive_delay)
        
        return adaptive_delay
    
    def update_system_load(self, load_factor: float):
        """
        Update system load factor for adaptive calculations.
        
        Args:
            load_factor: System load factor (1.0 = normal, >1.0 = high load)
        """
        self.system_load_factor = max(0.1, load_factor)
        self.last_adjustment_time = time.time()
    
    def update_error_rate(self, error_rate: float):
        """
        Update current error rate for adaptive calculations.
        
        Args:
            error_rate: Current error rate (0.0 to 1.0)
        """
        self.current_error_rate = max(0.0, min(1.0, error_rate))
    
    def _record_success(self, attempt: int, execution_time: float):
        """Record successful attempt."""
        self.metrics.total_attempts += 1
        self.metrics.successful_attempts += 1
        
        # Update retry distribution
        if attempt not in self.metrics.retry_distribution:
            self.metrics.retry_distribution[attempt] = 0
        self.metrics.retry_distribution[attempt] += 1
    
    def _record_failure(self, attempt: int):
        """Record failed attempt."""
        self.metrics.total_attempts += 1
        self.metrics.failed_attempts += 1
    
    def get_metrics(self) -> BackoffMetrics:
        """Get current backoff metrics."""
        return self.metrics
    
    def get_success_rate(self) -> float:
        """Get success rate."""
        if self.metrics.total_attempts == 0:
            return 1.0
        return self.metrics.successful_attempts / self.metrics.total_attempts
    
    def get_avg_retries(self) -> float:
        """Get average number of retries per successful attempt."""
        if self.metrics.successful_attempts == 0:
            return 0.0
        
        total_retries = sum(attempt * count for attempt, count in self.metrics.retry_distribution.items())
        return total_retries / self.metrics.successful_attempts
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = BackoffMetrics()
    
    def estimate_recovery_time(self) -> float:
        """
        Estimate system recovery time based on current conditions.
        
        Returns:
            Estimated recovery time in seconds
        """
        if self.current_error_rate == 0.0:
            return 0.0
        
        # Base recovery time increases with error rate
        base_recovery = self.config.base_delay * 10
        
        # Scale by error rate
        recovery_time = base_recovery * (1.0 + self.current_error_rate * 5.0)
        
        # Scale by system load
        recovery_time *= self.system_load_factor
        
        return min(recovery_time, self.config.max_delay * 5)
    
    def should_throttle(self) -> bool:
        """
        Determine if operations should be throttled based on current conditions.
        
        Returns:
            True if throttling is recommended
        """
        return (self.current_error_rate > self.config.adaptive_threshold or 
                self.system_load_factor > 2.0)
    
    def get_throttle_factor(self) -> float:
        """
        Get recommended throttle factor.
        
        Returns:
            Throttle factor (1.0 = no throttling, 0.1 = heavy throttling)
        """
        if not self.should_throttle():
            return 1.0
        
        # Calculate throttle based on error rate and load
        error_throttle = max(0.1, 1.0 - self.current_error_rate)
        load_throttle = max(0.1, 1.0 / self.system_load_factor)
        
        return min(error_throttle, load_throttle)
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for external monitoring systems."""
        return {
            "adaptive_backoff": {
                "strategy": self.config.strategy.value,
                "total_attempts": self.metrics.total_attempts,
                "successful_attempts": self.metrics.successful_attempts,
                "failed_attempts": self.metrics.failed_attempts,
                "success_rate": self.get_success_rate(),
                "avg_retries": self.get_avg_retries(),
                "current_error_rate": self.current_error_rate,
                "system_load_factor": self.system_load_factor,
                "should_throttle": self.should_throttle(),
                "throttle_factor": self.get_throttle_factor(),
                "estimated_recovery_time": self.estimate_recovery_time(),
                "timestamp": time.time()
            }
        }


class BackoffManager:
    """
    Manager for multiple backoff strategies.
    """
    
    def __init__(self):
        self.backoff_strategies: Dict[str, AdaptiveBackoff] = {}
        self.global_error_rate = 0.0
        self.global_load_factor = 1.0
    
    def create_backoff(self, name: str, config: Optional[BackoffConfig] = None) -> AdaptiveBackoff:
        """
        Create a new backoff strategy.
        
        Args:
            name: Backoff strategy name
            config: Backoff configuration
            
        Returns:
            Created backoff strategy
        """
        if name in self.backoff_strategies:
            raise ValueError(f"Backoff strategy '{name}' already exists")
        
        backoff = AdaptiveBackoff(config)
        self.backoff_strategies[name] = backoff
        return backoff
    
    def get_backoff(self, name: str) -> Optional[AdaptiveBackoff]:
        """Get backoff strategy by name."""
        return self.backoff_strategies.get(name)
    
    def update_global_conditions(self, error_rate: float, load_factor: float):
        """
        Update global conditions for all backoff strategies.
        
        Args:
            error_rate: Global error rate
            load_factor: Global load factor
        """
        self.global_error_rate = error_rate
        self.global_load_factor = load_factor
        
        # Update all adaptive backoff strategies
        for backoff in self.backoff_strategies.values():
            backoff.update_error_rate(error_rate)
            backoff.update_system_load(load_factor)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all backoff strategies."""
        return {
            "backoff_manager": {
                "global_error_rate": self.global_error_rate,
                "global_load_factor": self.global_load_factor,
                "total_strategies": len(self.backoff_strategies),
                "strategies": {
                    name: backoff.export_metrics()["adaptive_backoff"]
                    for name, backoff in self.backoff_strategies.items()
                },
                "timestamp": time.time()
            }
        }
    
    def reset_all_metrics(self):
        """Reset metrics for all backoff strategies."""
        for backoff in self.backoff_strategies.values():
            backoff.reset_metrics()
