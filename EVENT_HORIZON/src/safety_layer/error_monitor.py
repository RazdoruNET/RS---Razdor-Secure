"""
Error Monitor

Monitors system health and detects various error conditions
including WAF overload, upstream saturation, and service degradation.
"""

import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict


class ErrorType(Enum):
    """Types of errors to monitor."""
    HTTP_503 = "http_503"
    HTTP_5XX = "http_5xx"
    HTTP_4XX = "http_4xx"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    RATE_LIMIT = "rate_limit"
    HIGH_LATENCY = "high_latency"
    CIRCUIT_BREAK = "circuit_break"


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Represents an error event."""
    error_type: ErrorType
    timestamp: float
    severity: AlertLevel
    message: str
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None


@dataclass
class ErrorMetrics:
    """Error metrics for monitoring."""
    total_errors: int = 0
    errors_by_type: Dict[ErrorType, int] = None
    errors_by_severity: Dict[AlertLevel, int] = None
    error_rate: float = 0.0
    avg_error_frequency: float = 0.0
    last_error_time: float = 0.0
    
    def __post_init__(self):
        if self.errors_by_type is None:
            self.errors_by_type = {}
        if self.errors_by_severity is None:
            self.errors_by_severity = {}


class ErrorMonitor:
    """
    Monitors system health and detects various error conditions.
    """
    
    def __init__(self, window_size: int = 300, max_events: int = 1000):
        """
        Initialize error monitor.
        
        Args:
            window_size: Time window in seconds for error rate calculation
            max_events: Maximum number of events to keep in memory
        """
        self.window_size = window_size
        self.max_events = max_events
        
        self.events: deque = deque(maxlen=max_events)
        self.active_alerts: Dict[str, ErrorEvent] = {}
        
        # Metrics tracking
        self.metrics = ErrorMetrics()
        self.error_history: deque = deque(maxlen=1000)
        
        # Thresholds
        self.thresholds = {
            "error_rate": 0.1,  # 10% error rate threshold
            "503_rate": 0.05,   # 5% 503 error rate threshold
            "5xx_rate": 0.15,   # 15% 5xx error rate threshold
            "latency_p95": 5.0, # 5 second P95 latency threshold
            "timeout_rate": 0.02 # 2% timeout rate threshold
        }
        
        # Callbacks
        self.alert_callbacks: List[Callable[[ErrorEvent], None]] = []
        
        # Statistics
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        
    def add_alert_callback(self, callback: Callable[[ErrorEvent], None]):
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[ErrorEvent], None]):
        """Remove alert callback."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def record_error(self, error_type: ErrorType, message: str, 
                    severity: AlertLevel = AlertLevel.WARNING,
                    context: Optional[Dict[str, Any]] = None):
        """
        Record an error event.
        
        Args:
            error_type: Type of error
            message: Error message
            severity: Error severity
            context: Additional context information
        """
        if context is None:
            context = {}
        
        event = ErrorEvent(
            error_type=error_type,
            timestamp=time.time(),
            severity=severity,
            message=message,
            context=context
        )
        
        self.events.append(event)
        self._update_metrics(event)
        self._check_thresholds(event)
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Don't let callback failures break monitoring
    
    def record_http_error(self, status_code: int, response_time: float,
                         url: str, context: Optional[Dict[str, Any]] = None):
        """
        Record HTTP error with automatic classification.
        
        Args:
            status_code: HTTP status code
            response_time: Response time in seconds
            url: Request URL
            context: Additional context
        """
        if context is None:
            context = {}
        
        context.update({
            "status_code": status_code,
            "response_time": response_time,
            "url": url
        })
        
        if status_code == 503:
            error_type = ErrorType.HTTP_503
            severity = AlertLevel.CRITICAL
            message = f"Service Unavailable (503) from {url}"
        elif 500 <= status_code < 600:
            error_type = ErrorType.HTTP_5XX
            severity = AlertLevel.CRITICAL
            message = f"Server Error ({status_code}) from {url}"
        elif 400 <= status_code < 500:
            error_type = ErrorType.HTTP_4XX
            severity = AlertLevel.WARNING
            message = f"Client Error ({status_code}) from {url}"
        else:
            return  # Not an error status code
        
        self.record_error(error_type, message, severity, context)
    
    def record_timeout(self, url: str, timeout_duration: float,
                       context: Optional[Dict[str, Any]] = None):
        """
        Record a timeout event.
        
        Args:
            url: Request URL
            timeout_duration: Timeout duration in seconds
            context: Additional context
        """
        if context is None:
            context = {}
        
        context.update({
            "url": url,
            "timeout_duration": timeout_duration
        })
        
        self.record_error(
            ErrorType.TIMEOUT,
            f"Request timeout after {timeout_duration}s for {url}",
            AlertLevel.WARNING,
            context
        )
    
    def record_connection_error(self, url: str, error_message: str,
                              context: Optional[Dict[str, Any]] = None):
        """
        Record a connection error.
        
        Args:
            url: Request URL
            error_message: Error message
            context: Additional context
        """
        if context is None:
            context = {}
        
        context.update({
            "url": url,
            "error_message": error_message
        })
        
        self.record_error(
            ErrorType.CONNECTION_ERROR,
            f"Connection error for {url}: {error_message}",
            AlertLevel.WARNING,
            context
        )
    
    def record_high_latency(self, url: str, latency: float, threshold: float,
                           context: Optional[Dict[str, Any]] = None):
        """
        Record high latency event.
        
        Args:
            url: Request URL
            latency: Actual latency in seconds
            threshold: Threshold that was exceeded
            context: Additional context
        """
        if context is None:
            context = {}
        
        context.update({
            "url": url,
            "latency": latency,
            "threshold": threshold
        })
        
        severity = AlertLevel.WARNING if latency < threshold * 2 else AlertLevel.CRITICAL
        
        self.record_error(
            ErrorType.HIGH_LATENCY,
            f"High latency {latency:.3f}s (threshold: {threshold:.3f}s) for {url}",
            severity,
            context
        )
    
    def record_request(self, success: bool, response_time: float = 0.0):
        """
        Record a request for statistics.
        
        Args:
            success: Whether request was successful
            response_time: Response time in seconds
        """
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        
        # Check for high latency
        if response_time > self.thresholds["latency_p95"]:
            self.record_high_latency(
                "unknown",
                response_time,
                self.thresholds["latency_p95"],
                {"response_time": response_time}
            )
    
    def _update_metrics(self, event: ErrorEvent):
        """Update internal metrics based on new event."""
        self.metrics.total_errors += 1
        self.metrics.last_error_time = event.timestamp
        
        # Update error type counts
        if event.error_type not in self.metrics.errors_by_type:
            self.metrics.errors_by_type[event.error_type] = 0
        self.metrics.errors_by_type[event.error_type] += 1
        
        # Update severity counts
        if event.severity not in self.metrics.errors_by_severity:
            self.metrics.errors_by_severity[event.severity] = 0
        self.metrics.errors_by_severity[event.severity] += 1
        
        # Calculate error rate
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Count errors in window
        errors_in_window = sum(1 for e in self.events if e.timestamp >= window_start)
        
        # Calculate requests in window (approximate)
        if self.total_requests > 0:
            time_fraction = self.window_size / (current_time - self.start_time)
            requests_in_window = self.total_requests * time_fraction
            self.metrics.error_rate = errors_in_window / requests_in_window if requests_in_window > 0 else 0
        else:
            self.metrics.error_rate = 0
        
        # Calculate average error frequency
        if len(self.events) > 1:
            time_span = self.events[-1].timestamp - self.events[0].timestamp
            self.metrics.avg_error_frequency = len(self.events) / time_span if time_span > 0 else 0
    
    def _check_thresholds(self, event: ErrorEvent):
        """Check if error thresholds are exceeded and create alerts."""
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Count specific error types in window
        events_in_window = [e for e in self.events if e.timestamp >= window_start]
        
        # Check 503 error rate
        if event.error_type == ErrorType.HTTP_503:
            total_503 = sum(1 for e in events_in_window if e.error_type == ErrorType.HTTP_503)
            if self.total_requests > 0:
                time_fraction = self.window_size / (current_time - self.start_time)
                requests_in_window = self.total_requests * time_fraction
                if requests_in_window > 0 and (total_503 / requests_in_window) > self.thresholds["503_rate"]:
                    self._create_alert(
                        "high_503_rate",
                        AlertLevel.CRITICAL,
                        f"High 503 error rate: {total_503}/{requests_in_window} ({total_503/requests_in_window:.2%})",
                        {"503_count": total_503, "total_requests": int(requests_in_window)}
                    )
        
        # Check 5xx error rate
        if event.error_type == ErrorType.HTTP_5XX:
            total_5xx = sum(1 for e in events_in_window if e.error_type == ErrorType.HTTP_5XX)
            if self.total_requests > 0:
                time_fraction = self.window_size / (current_time - self.start_time)
                requests_in_window = self.total_requests * time_fraction
                if requests_in_window > 0 and (total_5xx / requests_in_window) > self.thresholds["5xx_rate"]:
                    self._create_alert(
                        "high_5xx_rate",
                        AlertLevel.CRITICAL,
                        f"High 5xx error rate: {total_5xx}/{requests_in_window} ({total_5xx/requests_in_window:.2%})",
                        {"5xx_count": total_5xx, "total_requests": int(requests_in_window)}
                    )
        
        # Check overall error rate
        if self.metrics.error_rate > self.thresholds["error_rate"]:
            self._create_alert(
                "high_error_rate",
                AlertLevel.WARNING,
                f"High error rate: {self.metrics.error_rate:.2%}",
                {"error_rate": self.metrics.error_rate}
            )
    
    def _create_alert(self, alert_id: str, severity: AlertLevel, 
                      message: str, context: Dict[str, Any]):
        """Create or update an alert."""
        if alert_id in self.active_alerts:
            # Update existing alert
            alert = self.active_alerts[alert_id]
            alert.timestamp = time.time()
            alert.message = message
            alert.context.update(context)
        else:
            # Create new alert
            alert = ErrorEvent(
                error_type=ErrorType.CIRCUIT_BREAK,
                timestamp=time.time(),
                severity=severity,
                message=message,
                context=context
            )
            self.active_alerts[alert_id] = alert
    
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = time.time()
            del self.active_alerts[alert_id]
    
    def get_error_rate(self, window_seconds: Optional[int] = None) -> float:
        """
        Get error rate for specified time window.
        
        Args:
            window_seconds: Time window in seconds (uses default if None)
            
        Returns:
            Error rate as percentage (0.0 to 1.0)
        """
        if window_seconds is None:
            window_seconds = self.window_size
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        errors_in_window = sum(1 for e in self.events if e.timestamp >= window_start)
        
        if self.total_requests > 0:
            time_fraction = window_seconds / (current_time - self.start_time)
            requests_in_window = self.total_requests * time_fraction
            return errors_in_window / requests_in_window if requests_in_window > 0 else 0
        
        return 0.0
    
    def get_error_type_distribution(self, window_seconds: Optional[int] = None) -> Dict[str, int]:
        """
        Get distribution of error types in time window.
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            Dictionary of error type counts
        """
        if window_seconds is None:
            window_seconds = self.window_size
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        distribution = defaultdict(int)
        for event in self.events:
            if event.timestamp >= window_start:
                distribution[event.error_type.value] += 1
        
        return dict(distribution)
    
    def get_active_alerts(self) -> Dict[str, ErrorEvent]:
        """Get all active alerts."""
        return self.active_alerts.copy()
    
    def get_metrics(self) -> ErrorMetrics:
        """Get current error metrics."""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        current_time = time.time()
        
        # Calculate recent error rates
        recent_503_rate = self._get_specific_error_rate(ErrorType.HTTP_503, 60)  # Last minute
        recent_5xx_rate = self._get_specific_error_rate(ErrorType.HTTP_5XX, 60)
        recent_error_rate = self.get_error_rate(60)
        
        # Determine health status
        health_status = "healthy"
        if recent_503_rate > 0.05 or recent_5xx_rate > 0.15:
            health_status = "critical"
        elif recent_error_rate > 0.1 or len(self.active_alerts) > 0:
            health_status = "degraded"
        elif recent_error_rate > 0.05:
            health_status = "warning"
        
        return {
            "status": health_status,
            "error_rate": recent_error_rate,
            "503_rate": recent_503_rate,
            "5xx_rate": recent_5xx_rate,
            "active_alerts": len(self.active_alerts),
            "total_errors": self.metrics.total_errors,
            "uptime": current_time - self.start_time,
            "last_error": self.metrics.last_error_time
        }
    
    def _get_specific_error_rate(self, error_type: ErrorType, window_seconds: int) -> float:
        """Get error rate for specific error type."""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        errors_in_window = sum(1 for e in self.events 
                             if e.timestamp >= window_start and e.error_type == error_type)
        
        if self.total_requests > 0:
            time_fraction = window_seconds / (current_time - self.start_time)
            requests_in_window = self.total_requests * time_fraction
            return errors_in_window / requests_in_window if requests_in_window > 0 else 0
        
        return 0.0
    
    def reset(self):
        """Reset all monitoring state."""
        self.events.clear()
        self.active_alerts.clear()
        self.metrics = ErrorMetrics()
        self.error_history.clear()
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for external monitoring systems."""
        return {
            "error_monitor": {
                "total_errors": self.metrics.total_errors,
                "error_rate": self.metrics.error_rate,
                "avg_error_frequency": self.metrics.avg_error_frequency,
                "active_alerts": len(self.active_alerts),
                "health_status": self.get_health_status(),
                "error_type_distribution": self.get_error_type_distribution(),
                "timestamp": time.time()
            }
        }
