"""
Structured Logger

Structured logging with JSON formatting and correlation IDs
for distributed tracing and debugging.
"""

import json
import logging
import time
import uuid
import threading
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from contextvars import ContextVar
import structlog


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEvent:
    """Structured log event."""
    timestamp: float
    level: LogLevel
    message: str
    logger_name: str
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


# Context variables for correlation
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class StructuredLogger:
    """
    Structured logger with JSON formatting and correlation support.
    """
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Log level
        """
        self.name = name
        self.level = level
        
        # Setup structlog processor
        self.structlog_logger = structlog.get_logger(name)
        
        # Configure standard logging for fallback
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value.upper()))
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Event buffer for recent events
        self.event_buffer = []
        self.max_buffer_size = 1000
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current context."""
        correlation_id_var.set(correlation_id)
    
    def set_request_id(self, request_id: str):
        """Set request ID for current context."""
        request_id_var.set(request_id)
    
    def set_user_id(self, user_id: str):
        """Set user ID for current context."""
        user_id_var.set(user_id)
    
    def set_session_id(self, session_id: str):
        """Set session ID for current context."""
        session_id_var.set(session_id)
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message."""
        if error:
            kwargs["error"] = str(error)
            kwargs["stack_trace"] = self._get_stack_trace(error)
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        if error:
            kwargs["error"] = str(error)
            kwargs["stack_trace"] = self._get_stack_trace(error)
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def log_http_request(self, method: str, url: str, status_code: int,
                        duration_ms: float, user_agent: str = "", **kwargs):
        """Log HTTP request."""
        self.info(
            "HTTP request completed",
            component="http",
            operation="request",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration_ms,
            user_agent=user_agent,
            **kwargs
        )
    
    def log_auth_attempt(self, method: str, result: str, duration_ms: float,
                        user_id: Optional[str] = None, **kwargs):
        """Log authentication attempt."""
        if user_id:
            self.set_user_id(user_id)
        
        self.info(
            "Authentication attempt",
            component="auth",
            operation="authenticate",
            auth_method=method,
            auth_result=result,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_database_operation(self, operation: str, table: str, duration_ms: float,
                              affected_rows: Optional[int] = None, **kwargs):
        """Log database operation."""
        self.info(
            "Database operation completed",
            component="database",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            affected_rows=affected_rows,
            **kwargs
        )
    
    def log_circuit_breaker_event(self, circuit_name: str, event_type: str,
                                 reason: str = "", **kwargs):
        """Log circuit breaker event."""
        level = LogLevel.WARNING if event_type in ["opened", "failure"] else LogLevel.INFO
        
        self._log(
            level,
            f"Circuit breaker {event_type}",
            component="circuit_breaker",
            operation=event_type,
            circuit_name=circuit_name,
            reason=reason,
            **kwargs
        )
    
    def log_error_monitoring_event(self, error_type: str, severity: str,
                                  message: str, **kwargs):
        """Log error monitoring event."""
        level = LogLevel.CRITICAL if severity == "critical" else LogLevel.WARNING
        
        self._log(
            level,
            f"Error monitoring: {message}",
            component="error_monitor",
            operation="error_detected",
            error_type=error_type,
            severity=severity,
            **kwargs
        )
    
    def log_performance_metric(self, metric_name: str, value: float,
                              unit: str = "", **kwargs):
        """Log performance metric."""
        self.info(
            f"Performance metric: {metric_name}",
            component="performance",
            operation="metric",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs
        )
    
    def log_security_event(self, event_type: str, severity: str,
                           description: str, **kwargs):
        """Log security event."""
        level = LogLevel.CRITICAL if severity == "critical" else LogLevel.WARNING
        
        self._log(
            level,
            f"Security event: {description}",
            component="security",
            operation=event_type,
            security_event_type=event_type,
            security_severity=severity,
            security_description=description,
            **kwargs
        )
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Internal logging method."""
        # Check log level
        if not self._should_log(level):
            return
        
        # Create log event
        event = LogEvent(
            timestamp=time.time(),
            level=level,
            message=message,
            logger_name=self.name,
            correlation_id=correlation_id_var.get(),
            request_id=request_id_var.get(),
            user_id=user_id_var.get(),
            session_id=session_id_var.get(),
            metadata=kwargs
        )
        
        # Extract common fields from metadata
        if "component" in kwargs:
            event.component = kwargs.pop("component")
        if "operation" in kwargs:
            event.operation = kwargs.pop("operation")
        if "duration_ms" in kwargs:
            event.duration_ms = kwargs.pop("duration_ms")
        if "error" in kwargs:
            event.error = kwargs.pop("error")
        if "stack_trace" in kwargs:
            event.stack_trace = kwargs.pop("stack_trace")
        
        event.metadata = kwargs
        
        # Add to buffer
        with self.lock:
            self.event_buffer.append(event)
            if len(self.event_buffer) > self.max_buffer_size:
                self.event_buffer = self.event_buffer[-self.max_buffer_size:]
        
        # Log to structlog
        log_dict = asdict(event)
        self.structlog_logger.log(level.value.upper(), message, **log_dict)
        
        # Also log to standard logger as fallback
        log_level = getattr(logging, level.value.upper())
        self.logger.log(log_level, self._format_log_message(event))
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level."""
        level_hierarchy = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        return level_hierarchy[level] >= level_hierarchy[self.level]
    
    def _format_log_message(self, event: LogEvent) -> str:
        """Format log message for standard logger."""
        parts = [f"[{event.level.value.upper()}]", f"{event.logger_name}"]
        
        if event.correlation_id:
            parts.append(f"corr:{event.correlation_id}")
        if event.request_id:
            parts.append(f"req:{event.request_id}")
        if event.component:
            parts.append(f"comp:{event.component}")
        if event.operation:
            parts.append(f"op:{event.operation}")
        
        parts.append(event.message)
        
        return " ".join(parts)
    
    def _get_stack_trace(self, error: Exception) -> str:
        """Get stack trace from exception."""
        import traceback
        return "".join(traceback.format_exception(type(error), error, error.__traceback__))
    
    def get_recent_events(self, count: int = 100, 
                         level: Optional[LogLevel] = None,
                         component: Optional[str] = None) -> list:
        """
        Get recent log events.
        
        Args:
            count: Maximum number of events to return
            level: Filter by log level
            component: Filter by component
            
        Returns:
            List of log events
        """
        with self.lock:
            events = self.event_buffer.copy()
        
        # Apply filters
        if level:
            events = [e for e in events if e.level == level]
        
        if component:
            events = [e for e in events if e.component == component]
        
        # Return most recent events
        return events[-count:] if events else []
    
    def get_error_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """
        Get summary of recent errors.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Error summary
        """
        cutoff_time = time.time() - (minutes * 60)
        
        with self.lock:
            recent_events = [e for e in self.event_buffer if e.timestamp >= cutoff_time]
        
        error_events = [e for e in recent_events if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        # Group by component
        errors_by_component = {}
        for event in error_events:
            component = event.component or "unknown"
            if component not in errors_by_component:
                errors_by_component[component] = []
            errors_by_component[component].append(event)
        
        # Group by error type
        errors_by_type = {}
        for event in error_events:
            error_type = event.metadata.get("error_type", "unknown")
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(event)
        
        return {
            "total_errors": len(error_events),
            "time_window_minutes": minutes,
            "errors_by_component": {k: len(v) for k, v in errors_by_component.items()},
            "errors_by_type": {k: len(v) for k, v in errors_by_type.items()},
            "most_recent_error": error_events[-1].message if error_events else None,
            "error_rate": len(error_events) / len(recent_events) if recent_events else 0.0
        }
    
    def export_logs(self, filename: str, format: str = "json",
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None):
        """
        Export logs to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "csv")
            start_time: Start time filter
            end_time: End time filter
        """
        with self.lock:
            events = self.event_buffer.copy()
        
        # Apply time filters
        if start_time or end_time:
            filtered_events = []
            for event in events:
                if start_time and event.timestamp < start_time:
                    continue
                if end_time and event.timestamp > end_time:
                    continue
                filtered_events.append(event)
            events = filtered_events
        
        if format.lower() == "json":
            with open(filename, 'w') as f:
                json.dump([asdict(event) for event in events], f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            if events:
                fieldnames = ["timestamp", "level", "message", "logger_name", 
                            "correlation_id", "request_id", "component", "operation"]
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for event in events:
                        row = {
                            "timestamp": event.timestamp,
                            "level": event.level.value,
                            "message": event.message,
                            "logger_name": event.logger_name,
                            "correlation_id": event.correlation_id,
                            "request_id": event.request_id,
                            "component": event.component,
                            "operation": event.operation
                        }
                        writer.writerow(row)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def set_level(self, level: LogLevel):
        """Set log level."""
        self.level = level
        self.logger.setLevel(getattr(logging, level.value.upper()))
    
    def clear_buffer(self):
        """Clear event buffer."""
        with self.lock:
            self.event_buffer.clear()


class LoggerManager:
    """
    Manager for multiple structured loggers.
    """
    
    def __init__(self):
        self.loggers: Dict[str, StructuredLogger] = {}
        self.default_level = LogLevel.INFO
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def get_logger(self, name: str, level: Optional[LogLevel] = None) -> StructuredLogger:
        """
        Get or create a logger.
        
        Args:
            name: Logger name
            level: Log level (uses default if None)
            
        Returns:
            Structured logger instance
        """
        if name not in self.loggers:
            log_level = level or self.default_level
            self.loggers[name] = StructuredLogger(name, log_level)
        
        return self.loggers[name]
    
    def set_default_level(self, level: LogLevel):
        """Set default log level for new loggers."""
        self.default_level = level
    
    def get_all_loggers(self) -> Dict[str, StructuredLogger]:
        """Get all loggers."""
        return self.loggers.copy()
    
    def get_error_summary_all(self, minutes: int = 60) -> Dict[str, Any]:
        """Get error summary from all loggers."""
        all_summaries = {}
        
        for name, logger in self.loggers.items():
            all_summaries[name] = logger.get_error_summary(minutes)
        
        # Calculate totals
        total_errors = sum(summary["total_errors"] for summary in all_summaries.values())
        
        return {
            "total_errors": total_errors,
            "time_window_minutes": minutes,
            "loggers": all_summaries
        }
    
    def export_all_logs(self, filename: str, format: str = "json"):
        """Export logs from all loggers."""
        import os
        
        if format.lower() == "json":
            all_events = []
            
            for logger in self.loggers.values():
                with logger.lock:
                    all_events.extend([asdict(event) for event in logger.event_buffer])
            
            # Sort by timestamp
            all_events.sort(key=lambda x: x["timestamp"])
            
            with open(filename, 'w') as f:
                json.dump(all_events, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            # Create directory if needed
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            for name, logger in self.loggers.items():
                logger_filename = filename.replace('.csv', f'_{name}.csv')
                logger.export_logs(logger_filename, 'csv')
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
