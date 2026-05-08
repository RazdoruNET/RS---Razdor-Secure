"""
Metrics Collector

Comprehensive metrics collection for the EVENT_HORIZON framework
including HTTP metrics, infrastructure metrics, and custom application metrics.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Represents a metric value with timestamp."""
    value: float
    timestamp: float
    labels: Dict[str, str]
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution metrics."""
    upper_bound: float
    count: int


@dataclass
class MetricDefinition:
    """Definition of a metric."""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None  # For histograms


class MetricsCollector:
    """
    Comprehensive metrics collection system.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of data points to keep per metric
        """
        self.max_history = max_history
        
        # Metric storage
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.summaries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # Metric definitions
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        
        # Time series data
        self.time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Built-in metric definitions
        self._register_builtin_metrics()
    
    def _register_builtin_metrics(self):
        """Register built-in metrics."""
        # HTTP metrics
        self.register_metric(
            "http_requests_total",
            MetricType.COUNTER,
            "Total number of HTTP requests",
            ["method", "status", "endpoint"]
        )
        
        self.register_metric(
            "http_request_duration_seconds",
            MetricType.HISTOGRAM,
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.register_metric(
            "http_response_size_bytes",
            MetricType.HISTOGRAM,
            "HTTP response size in bytes",
            ["method", "endpoint"],
            buckets=[100, 1000, 10000, 100000, 1000000]
        )
        
        # Authentication metrics
        self.register_metric(
            "auth_attempts_total",
            MetricType.COUNTER,
            "Total authentication attempts",
            ["method", "result"]
        )
        
        self.register_metric(
            "auth_duration_seconds",
            MetricType.HISTOGRAM,
            "Authentication duration in seconds",
            ["method"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5]
        )
        
        self.register_metric(
            "active_sessions",
            MetricType.GAUGE,
            "Number of active sessions",
            []
        )
        
        # System metrics
        self.register_metric(
            "system_cpu_usage",
            MetricType.GAUGE,
            "System CPU usage percentage",
            []
        )
        
        self.register_metric(
            "system_memory_usage",
            MetricType.GAUGE,
            "System memory usage percentage",
            []
        )
        
        self.register_metric(
            "system_disk_usage",
            MetricType.GAUGE,
            "System disk usage percentage",
            []
        )
        
        # Application metrics
        self.register_metric(
            "active_connections",
            MetricType.GAUGE,
            "Number of active connections",
            []
        )
        
        self.register_metric(
            "queue_size",
            MetricType.GAUGE,
            "Current queue size",
            ["queue_name"]
        )
        
        self.register_metric(
            "processing_duration_seconds",
            MetricType.HISTOGRAM,
            "Processing duration in seconds",
            ["operation"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
    
    def register_metric(self, name: str, metric_type: MetricType, 
                        description: str, labels: List[str],
                        buckets: Optional[List[float]] = None):
        """
        Register a new metric definition.
        
        Args:
            name: Metric name
            metric_type: Type of metric
            description: Metric description
            labels: List of label names
            buckets: Histogram buckets (for histogram metrics)
        """
        with self.lock:
            definition = MetricDefinition(
                name=name,
                metric_type=metric_type,
                description=description,
                labels=labels,
                buckets=buckets
            )
            self.metric_definitions[name] = definition
    
    def increment_counter(self, name: str, value: float = 1.0, 
                         labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Metric labels
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            
            # Record time series data
            self.time_series[key].append(MetricValue(
                value=self.counters[key],
                timestamp=time.time(),
                labels=labels or {}
            ))
    
    def set_gauge(self, name: str, value: float, 
                 labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Value to set
            labels: Metric labels
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            
            # Record time series data
            self.time_series[key].append(MetricValue(
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            ))
    
    def observe_histogram(self, name: str, value: float, 
                         labels: Optional[Dict[str, str]] = None):
        """
        Observe a histogram metric value.
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Metric labels
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            
            # Keep only recent values
            if len(self.histograms[key]) > self.max_history:
                self.histograms[key] = self.histograms[key][-self.max_history:]
            
            # Record time series data
            self.time_series[key].append(MetricValue(
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            ))
    
    def observe_summary(self, name: str, value: float, 
                       labels: Optional[Dict[str, str]] = None):
        """
        Observe a summary metric value.
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Metric labels
        """
        with self.lock:
            key = self._make_key(name, labels)
            self.summaries[key].append(value)
            
            # Record time series data
            self.time_series[key].append(MetricValue(
                value=value,
                timestamp=time.time(),
                labels=labels or {}
            ))
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter metric value."""
        with self.lock:
            key = self._make_key(name, labels)
            return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge metric value."""
        with self.lock:
            key = self._make_key(name, labels)
            return self.gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        with self.lock:
            key = self._make_key(name, labels)
            values = self.histograms.get(key, [])
            
            if not values:
                return {}
            
            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p50": statistics.median(values),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99)
            }
    
    def get_summary_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get summary statistics."""
        with self.lock:
            key = self._make_key(name, labels)
            values = list(self.summaries.get(key, []))
            
            if not values:
                return {}
            
            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p50": statistics.median(values),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99)
            }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_time_series(self, name: str, labels: Optional[Dict[str, str]] = None,
                       start_time: Optional[float] = None,
                       end_time: Optional[float] = None) -> List[MetricValue]:
        """
        Get time series data for a metric.
        
        Args:
            name: Metric name
            labels: Metric labels
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of metric values
        """
        with self.lock:
            key = self._make_key(name, labels)
            series = list(self.time_series.get(key, []))
            
            if start_time or end_time:
                filtered_series = []
                for value in series:
                    if start_time and value.timestamp < start_time:
                        continue
                    if end_time and value.timestamp > end_time:
                        continue
                    filtered_series.append(value)
                return filtered_series
            
            return series
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values."""
        with self.lock:
            metrics = {}
            
            # Counters
            metrics["counters"] = dict(self.counters)
            
            # Gauges
            metrics["gauges"] = dict(self.gauges)
            
            # Histogram stats
            metrics["histograms"] = {}
            for key in self.histograms:
                metrics["histograms"][key] = self.get_histogram_stats(key.split('[')[0])
            
            # Summary stats
            metrics["summaries"] = {}
            for key in self.summaries:
                metrics["summaries"][key] = self.get_summary_stats(key.split('[')[0])
            
            return metrics
    
    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Get all metric definitions."""
        with self.lock:
            return self.metric_definitions.copy()
    
    def reset_metric(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Reset a specific metric."""
        with self.lock:
            key = self._make_key(name, labels)
            
            # Remove from all metric stores
            self.counters.pop(key, None)
            self.gauges.pop(key, None)
            self.histograms.pop(key, None)
            self.summaries.pop(key, None)
            self.time_series.pop(key, None)
    
    def reset_all_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.summaries.clear()
            self.time_series.clear()
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        with self.lock:
            output = []
            
            # Export metric definitions
            for name, definition in self.metric_definitions.items():
                output.append(f"# HELP {name} {definition.description}")
                output.append(f"# TYPE {name} {definition.metric_type.value}")
            
            # Export counters
            for key, value in self.counters.items():
                name = key.split('[')[0]
                labels = self._extract_labels_from_key(key)
                label_str = self._format_labels(labels)
                output.append(f"{name}{label_str} {value}")
            
            # Export gauges
            for key, value in self.gauges.items():
                name = key.split('[')[0]
                labels = self._extract_labels_from_key(key)
                label_str = self._format_labels(labels)
                output.append(f"{name}{label_str} {value}")
            
            # Export histograms
            for key, values in self.histograms.items():
                if not values:
                    continue
                
                name = key.split('[')[0]
                labels = self._extract_labels_from_key(key)
                
                # Get bucket definitions
                definition = self.metric_definitions.get(name)
                buckets = definition.buckets if definition else []
                
                # Calculate bucket counts
                for bucket in buckets:
                    count = sum(1 for v in values if v <= bucket)
                    bucket_labels = labels.copy()
                    bucket_labels["le"] = str(bucket)
                    label_str = self._format_labels(bucket_labels)
                    output.append(f"{name}_bucket{label_str} {count}")
                
                # Add +Inf bucket
                count = len(values)
                bucket_labels = labels.copy()
                bucket_labels["le"] = "+Inf"
                label_str = self._format_labels(bucket_labels)
                output.append(f"{name}_bucket{label_str} {count}")
                
                # Add count and sum
                label_str = self._format_labels(labels)
                output.append(f"{name}_count{label_str} {len(values)}")
                output.append(f"{name}_sum{label_str} {sum(values)}")
            
            return "\n".join(output)
    
    def _extract_labels_from_key(self, key: str) -> Dict[str, str]:
        """Extract labels from metric key."""
        if '[' not in key:
            return {}
        
        label_part = key.split('[')[1].rstrip(']')
        labels = {}
        
        for pair in label_part.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                labels[k] = v
        
        return labels
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output."""
        if not labels:
            return ""
        
        label_pairs = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(label_pairs) + "}"
    
    def record_http_request(self, method: str, endpoint: str, status_code: int,
                           duration: float, response_size: int):
        """
        Record HTTP request metrics.
        
        Args:
            method: HTTP method
            endpoint: Request endpoint
            status_code: Response status code
            duration: Request duration in seconds
            response_size: Response size in bytes
        """
        labels = {"method": method, "endpoint": endpoint, "status": str(status_code)}
        
        self.increment_counter("http_requests_total", labels=labels)
        self.observe_histogram("http_request_duration_seconds", duration, 
                             labels={"method": method, "endpoint": endpoint})
        self.observe_histogram("http_response_size_bytes", response_size,
                             labels={"method": method, "endpoint": endpoint})
    
    def record_auth_attempt(self, method: str, result: str, duration: float):
        """
        Record authentication attempt metrics.
        
        Args:
            method: Authentication method
            result: Authentication result (success/failure)
            duration: Authentication duration in seconds
        """
        self.increment_counter("auth_attempts_total", 
                             labels={"method": method, "result": result})
        self.observe_histogram("auth_duration_seconds", duration,
                             labels={"method": method})
    
    def update_system_metrics(self, cpu_usage: float, memory_usage: float, 
                            disk_usage: float):
        """
        Update system metrics.
        
        Args:
            cpu_usage: CPU usage percentage (0-100)
            memory_usage: Memory usage percentage (0-100)
            disk_usage: Disk usage percentage (0-100)
        """
        self.set_gauge("system_cpu_usage", cpu_usage)
        self.set_gauge("system_memory_usage", memory_usage)
        self.set_gauge("system_disk_usage", disk_usage)
    
    def update_application_metrics(self, active_connections: int, 
                                 queue_sizes: Dict[str, int]):
        """
        Update application metrics.
        
        Args:
            active_connections: Number of active connections
            queue_sizes: Dictionary of queue sizes
        """
        self.set_gauge("active_connections", active_connections)
        
        for queue_name, size in queue_sizes.items():
            self.set_gauge("queue_size", size, labels={"queue_name": queue_name})
    
    def record_processing_duration(self, operation: str, duration: float):
        """
        Record processing duration for an operation.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        self.observe_histogram("processing_duration_seconds", duration,
                             labels={"operation": operation})
