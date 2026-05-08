"""
Telemetry Collector

Autonomous telemetry collection agent that gathers real-time
metrics and performance data during test execution.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

from ..observability import MetricsCollector, PerformanceMonitor, StructuredLogger
from .executor import ExecutionResult


class TelemetryType(Enum):
    """Types of telemetry data."""
    SYSTEM_METRICS = "system_metrics"
    APPLICATION_METRICS = "application_metrics"
    NETWORK_METRICS = "network_metrics"
    ERROR_METRICS = "error_metrics"
    PERFORMANCE_METRICS = "performance_metrics"
    CUSTOM_METRICS = "custom_metrics"


@dataclass
class TelemetryPoint:
    """Individual telemetry data point."""
    timestamp: float
    telemetry_type: TelemetryType
    source: str
    data: Dict[str, Any]
    labels: Dict[str, str]
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class TelemetrySnapshot:
    """Snapshot of telemetry data at a point in time."""
    timestamp: float
    system_metrics: Dict[str, Any]
    application_metrics: Dict[str, Any]
    network_metrics: Dict[str, Any]
    error_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    custom_metrics: Dict[str, Any]


class TelemetryCollector:
    """
    Autonomous telemetry collection agent for real-time monitoring.
    """
    
    def __init__(self, collection_interval: float = 1.0, 
                 buffer_size: int = 10000):
        """
        Initialize telemetry collector.
        
        Args:
            collection_interval: Collection interval in seconds
            buffer_size: Maximum number of data points to buffer
        """
        self.collection_interval = collection_interval
        self.buffer_size = buffer_size
        
        # Components
        self.metrics_collector = MetricsCollector()
        self.performance_monitor = PerformanceMonitor(collection_interval)
        self.logger = StructuredLogger("telemetry_collector")
        
        # Telemetry storage
        self.telemetry_buffer: List[TelemetryPoint] = []
        self.snapshots: List[TelemetrySnapshot] = []
        
        # Collection state
        self.collection_active = False
        self.collection_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.telemetry_callbacks: List[Callable[[TelemetryPoint], None]] = []
        self.snapshot_callbacks: List[Callable[[TelemetrySnapshot], None]] = []
        
        # Custom metric collectors
        self.custom_collectors: Dict[str, Callable[[], Dict[str, Any]]] = {}
    
    def add_telemetry_callback(self, callback: Callable[[TelemetryPoint], None]):
        """Add callback for telemetry data points."""
        self.telemetry_callbacks.append(callback)
    
    def add_snapshot_callback(self, callback: Callable[[TelemetrySnapshot], None]):
        """Add callback for telemetry snapshots."""
        self.snapshot_callbacks.append(callback)
    
    def add_custom_collector(self, name: str, collector: Callable[[], Dict[str, Any]]):
        """Add custom metric collector."""
        self.custom_collectors[name] = collector
    
    async def start_collection(self):
        """Start telemetry collection."""
        if self.collection_active:
            return
        
        self.collection_active = True
        
        # Start performance monitoring
        await self.performance_monitor.start_monitoring()
        
        # Start collection loop
        self.collection_task = asyncio.create_task(self._collection_loop())
        
        self.logger.info("Telemetry collection started", component="telemetry")
    
    async def stop_collection(self):
        """Stop telemetry collection."""
        self.collection_active = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
            self.collection_task = None
        
        await self.performance_monitor.stop_monitoring()
        
        self.logger.info("Telemetry collection stopped", component="telemetry")
    
    async def _collection_loop(self):
        """Main telemetry collection loop."""
        while self.collection_active:
            try:
                # Collect all telemetry types
                await self._collect_all_telemetry()
                
                # Create snapshot
                snapshot = await self._create_snapshot()
                self.snapshots.append(snapshot)
                
                # Trigger snapshot callbacks
                for callback in self.snapshot_callbacks:
                    try:
                        callback(snapshot)
                    except Exception:
                        pass
                
                # Maintain buffer size
                if len(self.snapshots) > self.buffer_size:
                    self.snapshots = self.snapshots[-self.buffer_size:]
                
                await asyncio.sleep(self.collection_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Telemetry collection error: {str(e)}", 
                                 component="telemetry", error=e)
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_all_telemetry(self):
        """Collect all types of telemetry data."""
        timestamp = time.time()
        
        # System metrics
        system_metrics = await self._collect_system_metrics(timestamp)
        
        # Application metrics
        application_metrics = await self._collect_application_metrics(timestamp)
        
        # Network metrics
        network_metrics = await self._collect_network_metrics(timestamp)
        
        # Error metrics
        error_metrics = await self._collect_error_metrics(timestamp)
        
        # Performance metrics
        performance_metrics = await self._collect_performance_metrics(timestamp)
        
        # Custom metrics
        custom_metrics = await self._collect_custom_metrics(timestamp)
    
    async def _collect_system_metrics(self, timestamp: float):
        """Collect system-level metrics."""
        try:
            snapshot = self.performance_monitor.get_current_snapshot()
            
            data = {
                "cpu_percent": snapshot.cpu_percent,
                "memory_percent": snapshot.memory_percent,
                "memory_used_mb": snapshot.memory_used_mb,
                "disk_usage_percent": snapshot.disk_usage_percent,
                "process_count": snapshot.process_count
            }
            
            point = TelemetryPoint(
                timestamp=timestamp,
                telemetry_type=TelemetryType.SYSTEM_METRICS,
                source="performance_monitor",
                data=data,
                labels={"component": "system"}
            )
            
            self._add_telemetry_point(point)
            
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {str(e)}", 
                             component="telemetry", error=e)
    
    async def _collect_application_metrics(self, timestamp: float):
        """Collect application-level metrics."""
        try:
            # Get metrics from metrics collector
            all_metrics = self.metrics_collector.get_all_metrics()
            
            # Focus on key application metrics
            data = {
                "http_requests_total": all_metrics.get("counters", {}).get("http_requests_total", 0),
                "active_connections": all_metrics.get("gauges", {}).get("active_connections", 0),
                "queue_sizes": all_metrics.get("gauges", {}),
                "auth_attempts_total": all_metrics.get("counters", {}).get("auth_attempts_total", 0),
                "active_sessions": all_metrics.get("gauges", {}).get("active_sessions", 0)
            }
            
            point = TelemetryPoint(
                timestamp=timestamp,
                telemetry_type=TelemetryType.APPLICATION_METRICS,
                source="metrics_collector",
                data=data,
                labels={"component": "application"}
            )
            
            self._add_telemetry_point(point)
            
        except Exception as e:
            self.logger.error(f"Application metrics collection failed: {str(e)}", 
                             component="telemetry", error=e)
    
    async def _collect_network_metrics(self, timestamp: float):
        """Collect network-level metrics."""
        try:
            snapshot = self.performance_monitor.get_current_snapshot()
            
            data = {
                "active_connections": snapshot.active_connections,
                "network_bytes_sent": snapshot.network_bytes_sent,
                "network_bytes_recv": snapshot.network_bytes_recv
            }
            
            # Get network statistics
            network_stats = self.performance_monitor.get_metric_statistics("network_bytes_sent_rate", 1)
            if network_stats:
                data["network_send_rate"] = network_stats.get("mean", 0)
            
            point = TelemetryPoint(
                timestamp=timestamp,
                telemetry_type=TelemetryType.NETWORK_METRICS,
                source="performance_monitor",
                data=data,
                labels={"component": "network"}
            )
            
            self._add_telemetry_point(point)
            
        except Exception as e:
            self.logger.error(f"Network metrics collection failed: {str(e)}", 
                             component="telemetry", error=e)
    
    async def _collect_error_metrics(self, timestamp: float):
        """Collect error-related metrics."""
        try:
            # Get error metrics from metrics collector
            all_metrics = self.metrics_collector.get_all_metrics()
            
            # Calculate error rates
            total_requests = all_metrics.get("counters", {}).get("http_requests_total", 0)
            error_requests = sum(count for key, count in all_metrics.get("counters", {}).items() 
                               if "error" in key.lower())
            
            error_rate = error_requests / total_requests if total_requests > 0 else 0.0
            
            data = {
                "total_errors": error_requests,
                "error_rate": error_rate,
                "http_5xx_errors": all_metrics.get("counters", {}).get("http_5xx_total", 0),
                "http_4xx_errors": all_metrics.get("counters", {}).get("http_4xx_total", 0),
                "timeout_errors": all_metrics.get("counters", {}).get("timeout_errors", 0)
            }
            
            point = TelemetryPoint(
                timestamp=timestamp,
                telemetry_type=TelemetryType.ERROR_METRICS,
                source="metrics_collector",
                data=data,
                labels={"component": "errors"}
            )
            
            self._add_telemetry_point(point)
            
        except Exception as e:
            self.logger.error(f"Error metrics collection failed: {str(e)}", 
                             component="telemetry", error=e)
    
    async def _collect_performance_metrics(self, timestamp: float):
        """Collect performance-related metrics."""
        try:
            # Get HTTP request duration statistics
            duration_stats = self.metrics_collector.get_histogram_stats("http_request_duration_seconds")
            
            data = {
                "avg_response_time": duration_stats.get("mean", 0),
                "p95_response_time": duration_stats.get("p95", 0),
                "p99_response_time": duration_stats.get("p99", 0),
                "total_requests": duration_stats.get("count", 0),
                "throughput": duration_stats.get("count", 0) / self.collection_interval if self.collection_interval > 0 else 0
            }
            
            point = TelemetryPoint(
                timestamp=timestamp,
                telemetry_type=TelemetryType.PERFORMANCE_METRICS,
                source="metrics_collector",
                data=data,
                labels={"component": "performance"}
            )
            
            self._add_telemetry_point(point)
            
        except Exception as e:
            self.logger.error(f"Performance metrics collection failed: {str(e)}", 
                             component="telemetry", error=e)
    
    async def _collect_custom_metrics(self, timestamp: float):
        """Collect custom metrics from registered collectors."""
        for name, collector in self.custom_collectors.items():
            try:
                data = collector()
                
                point = TelemetryPoint(
                    timestamp=timestamp,
                    telemetry_type=TelemetryType.CUSTOM_METRICS,
                    source=name,
                    data=data,
                    labels={"component": "custom", "collector": name}
                )
                
                self._add_telemetry_point(point)
                
            except Exception as e:
                self.logger.error(f"Custom collector '{name}' failed: {str(e)}", 
                                 component="telemetry", error=e)
    
    def _add_telemetry_point(self, point: TelemetryPoint):
        """Add telemetry point to buffer."""
        self.telemetry_buffer.append(point)
        
        # Maintain buffer size
        if len(self.telemetry_buffer) > self.buffer_size:
            self.telemetry_buffer = self.telemetry_buffer[-self.buffer_size:]
        
        # Trigger callbacks
        for callback in self.telemetry_callbacks:
            try:
                callback(point)
            except Exception:
                pass
    
    async def _create_snapshot(self) -> TelemetrySnapshot:
        """Create telemetry snapshot from current data."""
        timestamp = time.time()
        
        # Get latest data for each type
        system_metrics = {}
        application_metrics = {}
        network_metrics = {}
        error_metrics = {}
        performance_metrics = {}
        custom_metrics = {}
        
        # Extract latest data from buffer
        for point in reversed(self.telemetry_buffer):
            if point.timestamp > timestamp - self.collection_interval * 2:
                if point.telemetry_type == TelemetryType.SYSTEM_METRICS:
                    system_metrics.update(point.data)
                elif point.telemetry_type == TelemetryType.APPLICATION_METRICS:
                    application_metrics.update(point.data)
                elif point.telemetry_type == TelemetryType.NETWORK_METRICS:
                    network_metrics.update(point.data)
                elif point.telemetry_type == TelemetryType.ERROR_METRICS:
                    error_metrics.update(point.data)
                elif point.telemetry_type == TelemetryType.PERFORMANCE_METRICS:
                    performance_metrics.update(point.data)
                elif point.telemetry_type == TelemetryType.CUSTOM_METRICS:
                    custom_metrics[point.source] = point.data
        
        return TelemetrySnapshot(
            timestamp=timestamp,
            system_metrics=system_metrics,
            application_metrics=application_metrics,
            network_metrics=network_metrics,
            error_metrics=error_metrics,
            performance_metrics=performance_metrics,
            custom_metrics=custom_metrics
        )
    
    def get_recent_telemetry(self, minutes: int = 5, 
                           telemetry_type: Optional[TelemetryType] = None) -> List[TelemetryPoint]:
        """
        Get recent telemetry data.
        
        Args:
            minutes: Time window in minutes
            telemetry_type: Filter by telemetry type
            
        Returns:
            List of telemetry points
        """
        cutoff_time = time.time() - (minutes * 60)
        
        filtered_points = []
        for point in self.telemetry_buffer:
            if point.timestamp < cutoff_time:
                continue
            if telemetry_type and point.telemetry_type != telemetry_type:
                continue
            filtered_points.append(point)
        
        return filtered_points
    
    def get_telemetry_statistics(self, minutes: int = 5) -> Dict[str, Any]:
        """
        Get telemetry statistics for time window.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Telemetry statistics
        """
        recent_points = self.get_recent_telemetry(minutes)
        
        # Group by type
        by_type = {}
        for point in recent_points:
            type_name = point.telemetry_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(point)
        
        # Calculate statistics for each type
        statistics = {
            "time_window_minutes": minutes,
            "total_points": len(recent_points),
            "points_by_type": {k: len(v) for k, v in by_type.items()},
            "type_statistics": {}
        }
        
        for type_name, points in by_type.items():
            type_stats = {
                "point_count": len(points),
                "sources": list(set(p.source for p in points)),
                "data_fields": set()
            }
            
            # Collect all data fields
            for point in points:
                type_stats["data_fields"].update(point.data.keys())
            
            type_stats["data_fields"] = list(type_stats["data_fields"])
            statistics["type_statistics"][type_name] = type_stats
        
        return statistics
    
    def correlate_with_execution(self, execution_result: ExecutionResult) -> Dict[str, Any]:
        """
        Correlate telemetry data with execution results.
        
        Args:
            execution_result: Execution result to correlate with
            
        Returns:
            Correlation analysis
        """
        # Get telemetry data for execution period
        start_time = execution_result.start_time
        end_time = execution_result.end_time
        
        relevant_points = []
        for point in self.telemetry_buffer:
            if start_time <= point.timestamp <= end_time:
                relevant_points.append(point)
        
        # Group by type and calculate correlations
        correlations = {
            "execution_period": {
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            },
            "telemetry_points_analyzed": len(relevant_points),
            "correlations": {}
        }
        
        # System metrics correlation
        system_points = [p for p in relevant_points if p.telemetry_type == TelemetryType.SYSTEM_METRICS]
        if system_points:
            cpu_values = [p.data.get("cpu_percent", 0) for p in system_points]
            memory_values = [p.data.get("memory_percent", 0) for p in system_points]
            
            correlations["correlations"]["system"] = {
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max_cpu_percent": max(cpu_values) if cpu_values else 0,
                "avg_memory_percent": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max_memory_percent": max(memory_values) if memory_values else 0
            }
        
        # Performance metrics correlation
        perf_points = [p for p in relevant_points if p.telemetry_type == TelemetryType.PERFORMANCE_METRICS]
        if perf_points:
            response_times = [p.data.get("avg_response_time", 0) for p in perf_points]
            throughputs = [p.data.get("throughput", 0) for p in perf_points]
            
            correlations["correlations"]["performance"] = {
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "avg_throughput": sum(throughputs) / len(throughputs) if throughputs else 0,
                "max_throughput": max(throughputs) if throughputs else 0
            }
        
        # Error metrics correlation
        error_points = [p for p in relevant_points if p.telemetry_type == TelemetryType.ERROR_METRICS]
        if error_points:
            error_rates = [p.data.get("error_rate", 0) for p in error_points]
            
            correlations["correlations"]["errors"] = {
                "avg_error_rate": sum(error_rates) / len(error_rates) if error_rates else 0,
                "max_error_rate": max(error_rates) if error_rates else 0,
                "total_errors": sum(p.data.get("total_errors", 0) for p in error_points)
            }
        
        return correlations
    
    def export_telemetry(self, filename: str, format: str = "json",
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None):
        """
        Export telemetry data to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "csv")
            start_time: Start time filter
            end_time: End time filter
        """
        # Filter data by time
        if start_time or end_time:
            filtered_points = []
            for point in self.telemetry_buffer:
                if start_time and point.timestamp < start_time:
                    continue
                if end_time and point.timestamp > end_time:
                    continue
                filtered_points.append(point)
        else:
            filtered_points = self.telemetry_buffer
        
        if format.lower() == "json":
            export_data = {
                "export_timestamp": time.time(),
                "total_points": len(filtered_points),
                "time_range": {
                    "start": start_time or (filtered_points[0].timestamp if filtered_points else time.time()),
                    "end": end_time or (filtered_points[-1].timestamp if filtered_points else time.time())
                },
                "telemetry_points": [asdict(point) for point in filtered_points]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            if filtered_points:
                fieldnames = ["timestamp", "telemetry_type", "source", "data"]
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for point in filtered_points:
                        row = {
                            "timestamp": point.timestamp,
                            "telemetry_type": point.telemetry_type.value,
                            "source": point.source,
                            "data": json.dumps(point.data)
                        }
                        writer.writerow(row)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get data for real-time dashboard."""
        if not self.snapshots:
            return {}
        
        latest_snapshot = self.snapshots[-1]
        
        return {
            "timestamp": latest_snapshot.timestamp,
            "system_health": {
                "cpu_percent": latest_snapshot.system_metrics.get("cpu_percent", 0),
                "memory_percent": latest_snapshot.system_metrics.get("memory_percent", 0),
                "disk_percent": latest_snapshot.system_metrics.get("disk_usage_percent", 0)
            },
            "application_status": {
                "active_connections": latest_snapshot.application_metrics.get("active_connections", 0),
                "total_requests": latest_snapshot.application_metrics.get("http_requests_total", 0),
                "active_sessions": latest_snapshot.application_metrics.get("active_sessions", 0)
            },
            "performance": {
                "avg_response_time": latest_snapshot.performance_metrics.get("avg_response_time", 0),
                "p95_response_time": latest_snapshot.performance_metrics.get("p95_response_time", 0),
                "throughput": latest_snapshot.performance_metrics.get("throughput", 0)
            },
            "errors": {
                "error_rate": latest_snapshot.error_metrics.get("error_rate", 0),
                "total_errors": latest_snapshot.error_metrics.get("total_errors", 0),
                "http_5xx_errors": latest_snapshot.error_metrics.get("http_5xx_errors", 0)
            },
            "network": {
                "active_connections": latest_snapshot.network_metrics.get("active_connections", 0),
                "bytes_sent": latest_snapshot.network_metrics.get("network_bytes_sent", 0),
                "bytes_recv": latest_snapshot.network_metrics.get("network_bytes_recv", 0)
            }
        }
    
    def reset_telemetry(self):
        """Reset all telemetry data."""
        self.telemetry_buffer.clear()
        self.snapshots.clear()
        self.metrics_collector.reset_all_metrics()
        self.performance_monitor.reset_metrics()
        
        self.logger.info("Telemetry data reset", component="telemetry")
