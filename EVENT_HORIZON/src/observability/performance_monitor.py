"""
Performance Monitor

Real-time performance monitoring including CPU, memory, network,
and application-specific metrics collection.
"""

import asyncio
import psutil
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import deque
import statistics


class MetricCategory(Enum):
    """Performance metric categories."""
    SYSTEM = "system"
    PROCESS = "process"
    NETWORK = "network"
    MEMORY = "memory"
    DISK = "disk"
    APPLICATION = "application"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    category: MetricCategory
    value: float
    unit: str
    timestamp: float
    labels: Dict[str, str]
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    active_connections: int
    custom_metrics: Dict[str, float]


class PerformanceMonitor:
    """
    Real-time performance monitoring system.
    """
    
    def __init__(self, collection_interval: float = 1.0, 
                 history_size: int = 3600):
        """
        Initialize performance monitor.
        
        Args:
            collection_interval: Collection interval in seconds
            history_size: Maximum number of data points to keep
        """
        self.collection_interval = collection_interval
        self.history_size = history_size
        
        # Metric storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.custom_metrics: Dict[str, float] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.metric_callbacks: List[Callable[[PerformanceMetric], None]] = []
        self.alert_callbacks: List[Callable[[str, float, float], None]] = []
        
        # Thresholds for alerts
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "network_error_rate": 5.0
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Initial network stats
        self._last_network_stats = psutil.net_io_counters()
    
    def add_metric_callback(self, callback: Callable[[PerformanceMetric], None]):
        """Add callback for metric collection."""
        self.metric_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[str, float, float], None]):
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def set_threshold(self, metric_name: str, threshold: float):
        """Set alert threshold for a metric."""
        self.thresholds[metric_name] = threshold
    
    async def start_monitoring(self):
        """Start performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                print(f"Performance monitoring error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_metrics(self):
        """Collect all performance metrics."""
        timestamp = time.time()
        
        # System metrics
        await self._collect_system_metrics(timestamp)
        
        # Process metrics
        await self._collect_process_metrics(timestamp)
        
        # Memory metrics
        await self._collect_memory_metrics(timestamp)
        
        # Disk metrics
        await self._collect_disk_metrics(timestamp)
        
        # Network metrics
        await self._collect_network_metrics(timestamp)
        
        # Custom metrics
        await self._collect_custom_metrics(timestamp)
    
    async def _collect_system_metrics(self, timestamp: float):
        """Collect system-level metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        await self._record_metric("cpu_percent", cpu_percent, "%", 
                                 MetricCategory.SYSTEM, timestamp)
        
        # CPU count
        cpu_count = psutil.cpu_count()
        await self._record_metric("cpu_count", cpu_count, "count", 
                                 MetricCategory.SYSTEM, timestamp)
        
        # Load average (Unix systems)
        try:
            load_avg = psutil.getloadavg()
            await self._record_metric("load_avg_1min", load_avg[0], "processes", 
                                     MetricCategory.SYSTEM, timestamp)
            await self._record_metric("load_avg_5min", load_avg[1], "processes", 
                                     MetricCategory.SYSTEM, timestamp)
            await self._record_metric("load_avg_15min", load_avg[2], "processes", 
                                     MetricCategory.SYSTEM, timestamp)
        except AttributeError:
            # Not available on Windows
            pass
    
    async def _collect_process_metrics(self, timestamp: float):
        """Collect process-level metrics."""
        try:
            process = psutil.Process()
            
            # Process CPU usage
            process_cpu = process.cpu_percent()
            await self._record_metric("process_cpu_percent", process_cpu, "%", 
                                     MetricCategory.PROCESS, timestamp)
            
            # Process memory
            process_memory = process.memory_info()
            await self._record_metric("process_memory_rss", process_memory.rss, "bytes", 
                                     MetricCategory.PROCESS, timestamp)
            await self._record_metric("process_memory_vms", process_memory.vms, "bytes", 
                                     MetricCategory.PROCESS, timestamp)
            
            # Process threads
            process_threads = process.num_threads()
            await self._record_metric("process_threads", process_threads, "count", 
                                     MetricCategory.PROCESS, timestamp)
            
            # Process file descriptors
            try:
                process_fds = process.num_fds()
                await self._record_metric("process_fds", process_fds, "count", 
                                         MetricCategory.PROCESS, timestamp)
            except (AttributeError, psutil.AccessDenied):
                pass
            
        except psutil.NoSuchProcess:
            pass
    
    async def _collect_memory_metrics(self, timestamp: float):
        """Collect memory metrics."""
        # Virtual memory
        memory = psutil.virtual_memory()
        await self._record_metric("memory_total", memory.total, "bytes", 
                                 MetricCategory.MEMORY, timestamp)
        await self._record_metric("memory_available", memory.available, "bytes", 
                                 MetricCategory.MEMORY, timestamp)
        await self._record_metric("memory_used", memory.used, "bytes", 
                                 MetricCategory.MEMORY, timestamp)
        await self._record_metric("memory_percent", memory.percent, "%", 
                                 MetricCategory.MEMORY, timestamp)
        
        # Swap memory
        swap = psutil.swap_memory()
        await self._record_metric("swap_total", swap.total, "bytes", 
                                 MetricCategory.MEMORY, timestamp)
        await self._record_metric("swap_used", swap.used, "bytes", 
                                 MetricCategory.MEMORY, timestamp)
        await self._record_metric("swap_percent", swap.percent, "%", 
                                 MetricCategory.MEMORY, timestamp)
    
    async def _collect_disk_metrics(self, timestamp: float):
        """Collect disk metrics."""
        # Disk usage for root partition
        try:
            disk = psutil.disk_usage('/')
            await self._record_metric("disk_total", disk.total, "bytes", 
                                     MetricCategory.DISK, timestamp)
            await self._record_metric("disk_used", disk.used, "bytes", 
                                     MetricCategory.DISK, timestamp)
            await self._record_metric("disk_free", disk.free, "bytes", 
                                     MetricCategory.DISK, timestamp)
            await self._record_metric("disk_percent", disk.percent, "%", 
                                     MetricCategory.DISK, timestamp)
        except (psutil.AccessDenied, FileNotFoundError):
            pass
        
        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                await self._record_metric("disk_read_count", disk_io.read_count, "count", 
                                         MetricCategory.DISK, timestamp)
                await self._record_metric("disk_write_count", disk_io.write_count, "count", 
                                         MetricCategory.DISK, timestamp)
                await self._record_metric("disk_read_bytes", disk_io.read_bytes, "bytes", 
                                         MetricCategory.DISK, timestamp)
                await self._record_metric("disk_write_bytes", disk_io.write_bytes, "bytes", 
                                         MetricCategory.DISK, timestamp)
        except (psutil.AccessDenied, AttributeError):
            pass
    
    async def _collect_network_metrics(self, timestamp: float):
        """Collect network metrics."""
        try:
            network = psutil.net_io_counters()
            
            if network and self._last_network_stats:
                # Calculate rates
                time_diff = timestamp - (self.metrics_history.get("network_timestamp", [timestamp])[-1] if self.metrics_history.get("network_timestamp") else timestamp)
                
                if time_diff > 0:
                    bytes_sent_rate = (network.bytes_sent - self._last_network_stats.bytes_sent) / time_diff
                    bytes_recv_rate = (network.bytes_recv - self._last_network_stats.bytes_recv) / time_diff
                    
                    await self._record_metric("network_bytes_sent_rate", bytes_sent_rate, "bytes/sec", 
                                             MetricCategory.NETWORK, timestamp)
                    await self._record_metric("network_bytes_recv_rate", bytes_recv_rate, "bytes/sec", 
                                             MetricCategory.NETWORK, timestamp)
            
            # Absolute values
            if network:
                await self._record_metric("network_bytes_sent", network.bytes_sent, "bytes", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_bytes_recv", network.bytes_recv, "bytes", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_packets_sent", network.packets_sent, "count", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_packets_recv", network.packets_recv, "count", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_errin", network.errin, "count", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_errout", network.errout, "count", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_dropin", network.dropin, "count", 
                                         MetricCategory.NETWORK, timestamp)
                await self._record_metric("network_dropout", network.dropout, "count", 
                                         MetricCategory.NETWORK, timestamp)
            
            self._last_network_stats = network
            
            # Network connections
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            await self._record_metric("active_connections", active_connections, "count", 
                                     MetricCategory.NETWORK, timestamp)
            
        except (psutil.AccessDenied, AttributeError):
            pass
    
    async def _collect_custom_metrics(self, timestamp: float):
        """Collect custom application metrics."""
        for name, value in self.custom_metrics.items():
            await self._record_metric(name, value, "custom", 
                                     MetricCategory.APPLICATION, timestamp)
    
    async def _record_metric(self, name: str, value: float, unit: str, 
                           category: MetricCategory, timestamp: float,
                           labels: Optional[Dict[str, str]] = None):
        """Record a performance metric."""
        if labels is None:
            labels = {}
        
        metric = PerformanceMetric(
            name=name,
            category=category,
            value=value,
            unit=unit,
            timestamp=timestamp,
            labels=labels
        )
        
        # Store in history
        with self.lock:
            self.metrics_history[name].append(metric)
        
        # Check thresholds and trigger alerts
        threshold = self.thresholds.get(name)
        if threshold and value > threshold:
            for callback in self.alert_callbacks:
                try:
                    callback(name, value, threshold)
                except Exception:
                    pass
        
        # Trigger callbacks
        for callback in self.metric_callbacks:
            try:
                callback(metric)
            except Exception:
                pass
    
    def set_custom_metric(self, name: str, value: float):
        """Set a custom metric value."""
        with self.lock:
            self.custom_metrics[name] = value
    
    def increment_custom_metric(self, name: str, increment: float = 1.0):
        """Increment a custom metric."""
        with self.lock:
            current = self.custom_metrics.get(name, 0.0)
            self.custom_metrics[name] = current + increment
    
    def get_metric_history(self, name: str, 
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[PerformanceMetric]:
        """
        Get history for a specific metric.
        
        Args:
            name: Metric name
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of metrics
        """
        with self.lock:
            history = list(self.metrics_history.get(name, []))
        
        # Apply time filters
        if start_time or end_time:
            filtered = []
            for metric in history:
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                filtered.append(metric)
            return filtered
        
        return history
    
    def get_current_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot."""
        timestamp = time.time()
        
        # Get most recent values
        cpu_percent = self._get_latest_value("cpu_percent")
        memory_percent = self._get_latest_value("memory_percent")
        memory_used_mb = self._get_latest_value("memory_used") / (1024 * 1024)
        disk_usage_percent = self._get_latest_value("disk_percent")
        network_bytes_sent = self._get_latest_value("network_bytes_sent")
        network_bytes_recv = self._get_latest_value("network_bytes_recv")
        process_count = len(psutil.pids())
        active_connections = int(self._get_latest_value("active_connections"))
        
        return PerformanceSnapshot(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            process_count=process_count,
            active_connections=active_connections,
            custom_metrics=self.custom_metrics.copy()
        )
    
    def _get_latest_value(self, metric_name: str) -> float:
        """Get latest value for a metric."""
        with self.lock:
            history = self.metrics_history.get(metric_name)
            if history and len(history) > 0:
                return history[-1].value
        return 0.0
    
    def get_metric_statistics(self, name: str, 
                            minutes: int = 5) -> Dict[str, float]:
        """
        Get statistics for a metric over a time period.
        
        Args:
            name: Metric name
            minutes: Time period in minutes
            
        Returns:
            Statistics dictionary
        """
        cutoff_time = time.time() - (minutes * 60)
        history = self.get_metric_history(name, start_time=cutoff_time)
        
        if not history:
            return {}
        
        values = [m.value for m in history]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "p50": statistics.median(values),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        snapshot = self.get_current_snapshot()
        
        # Get recent statistics
        cpu_stats = self.get_metric_statistics("cpu_percent", 5)
        memory_stats = self.get_metric_statistics("memory_percent", 5)
        network_stats = self.get_metric_statistics("network_bytes_sent_rate", 5)
        
        return {
            "timestamp": snapshot.timestamp,
            "current": {
                "cpu_percent": snapshot.cpu_percent,
                "memory_percent": snapshot.memory_percent,
                "memory_used_mb": snapshot.memory_used_mb,
                "disk_usage_percent": snapshot.disk_usage_percent,
                "active_connections": snapshot.active_connections,
                "process_count": snapshot.process_count
            },
            "recent_5min": {
                "cpu": cpu_stats,
                "memory": memory_stats,
                "network": network_stats
            },
            "custom_metrics": snapshot.custom_metrics,
            "monitoring_active": self.monitoring_active
        }
    
    def export_metrics(self, filename: str, format: str = "json",
                      minutes: int = 60):
        """
        Export metrics to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "csv")
            minutes: Time window in minutes
        """
        cutoff_time = time.time() - (minutes * 60)
        
        # Get all metrics in time window
        all_metrics = []
        metric_names = list(self.metrics_history.keys())
        
        for name in metric_names:
            history = self.get_metric_history(name, start_time=cutoff_time)
            all_metrics.extend(history)
        
        # Sort by timestamp
        all_metrics.sort(key=lambda x: x.timestamp)
        
        if format.lower() == "json":
            import json
            
            export_data = {
                "export_timestamp": time.time(),
                "time_window_minutes": minutes,
                "metrics": [
                    {
                        "name": m.name,
                        "category": m.category.value,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp,
                        "labels": m.labels
                    }
                    for m in all_metrics
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            if all_metrics:
                fieldnames = ["timestamp", "name", "category", "value", "unit"]
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for metric in all_metrics:
                        row = {
                            "timestamp": metric.timestamp,
                            "name": metric.name,
                            "category": metric.category.value,
                            "value": metric.value,
                            "unit": metric.unit
                        }
                        writer.writerow(row)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def reset_metrics(self):
        """Reset all metrics and history."""
        with self.lock:
            self.metrics_history.clear()
            self.custom_metrics.clear()


# Import defaultdict for metrics_history
from collections import defaultdict
