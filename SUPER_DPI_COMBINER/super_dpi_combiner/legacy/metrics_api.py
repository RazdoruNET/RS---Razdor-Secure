#!/usr/bin/env python3
"""
Metrics API - REST API for accessing pipeline metrics and traces
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_global_metrics, get_logger

logger = get_logger(__name__)


class MetricsAPI:
    """API for accessing pipeline metrics and traces"""
    
    def __init__(self):
        self.metrics_collector = get_global_metrics()
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview with key metrics"""
        try:
            all_metrics = self.metrics_collector.get_metrics()
            success_rates = self.metrics_collector.get_success_rate()
            recent_traces = self.metrics_collector.get_recent_traces(10)
            
            # Calculate system-wide stats
            total_executions = sum(m.get('total_executions', 0) for m in all_metrics.values())
            total_successful = sum(m.get('successful_executions', 0) for m in all_metrics.values())
            total_failed = sum(m.get('failed_executions', 0) for m in all_metrics.values())
            
            system_success_rate = total_successful / total_executions if total_executions > 0 else 0.0
            
            # Calculate average latency across all pipelines
            avg_latencies = [m.get('average_latency', 0) for m in all_metrics.values() if m.get('average_latency', 0) > 0]
            system_avg_latency = sum(avg_latencies) / len(avg_latencies) if avg_latencies else 0.0
            
            # Get recent activity
            recent_activity = len([t for t in recent_traces if t.get('end_time', 0) > time.time() - 300])  # Last 5 minutes
            
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "system_stats": {
                    "total_executions": total_executions,
                    "successful_executions": total_successful,
                    "failed_executions": total_failed,
                    "success_rate": system_success_rate,
                    "average_latency": system_avg_latency,
                    "active_pipelines": len(all_metrics),
                    "recent_activity_5min": recent_activity
                },
                "pipeline_metrics": all_metrics,
                "success_rates": success_rates,
                "recent_traces": recent_traces[-5:]  # Last 5 traces
            }
            
        except Exception as e:
            logger.error("metrics_overview_error", error=str(e))
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def get_pipeline_metrics(self, pipeline_name: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed metrics for specific pipeline or all pipelines"""
        try:
            if pipeline_name:
                metrics = self.metrics_collector.get_metrics(pipeline_name)
                success_rate = self.metrics_collector.get_success_rate(pipeline_name)
                recent_traces = self.metrics_collector.get_recent_traces(50)
                
                # Filter traces for this pipeline
                pipeline_traces = [t for t in recent_traces if t.get('pipeline') == pipeline_name]
                
                return {
                    "pipeline": pipeline_name,
                    "metrics": metrics,
                    "success_rate": success_rate.get(pipeline_name, 0.0),
                    "recent_traces": pipeline_traces[-10:],  # Last 10 traces
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                all_metrics = self.metrics_collector.get_metrics()
                success_rates = self.metrics_collector.get_success_rate()
                
                return {
                    "all_pipelines": all_metrics,
                    "success_rates": success_rates,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
        except Exception as e:
            logger.error("pipeline_metrics_error", pipeline=pipeline_name, error=str(e))
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def get_traces(self, count: int = 100, pipeline: Optional[str] = None) -> Dict[str, Any]:
        """Get recent execution traces"""
        try:
            traces = self.metrics_collector.get_recent_traces(count)
            
            if pipeline:
                traces = [t for t in traces if t.get('pipeline') == pipeline]
            
            # Calculate trace statistics
            total_traces = len(traces)
            successful_traces = len([t for t in traces if t.get('status') == 'success'])
            failed_traces = len([t for t in traces if t.get('status') == 'fail'])
            
            # Calculate average latency from traces
            latencies = [t.get('latency', 0) for t in traces if t.get('latency') is not None]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            
            return {
                "traces": traces,
                "statistics": {
                    "total_traces": total_traces,
                    "successful_traces": successful_traces,
                    "failed_traces": failed_traces,
                    "success_rate": successful_traces / total_traces if total_traces > 0 else 0.0,
                    "average_latency": avg_latency
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error("traces_error", error=str(e))
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def get_failure_analysis(self) -> Dict[str, Any]:
        """Get failure analysis and common error patterns"""
        try:
            all_metrics = self.metrics_collector.get_metrics()
            failure_analysis = {}
            
            for pipeline, metrics in all_metrics.items():
                failure_reasons = metrics.get('failure_reasons', {})
                total_failures = metrics.get('failed_executions', 0)
                
                if total_failures > 0:
                    failure_analysis[pipeline] = {
                        "total_failures": total_failures,
                        "failure_reasons": failure_reasons,
                        "most_common_error": max(failure_reasons.items(), key=lambda x: x[1])[0] if failure_reasons else None,
                        "failure_rate": total_failures / metrics.get('total_executions', 1)
                    }
            
            return {
                "failure_analysis": failure_analysis,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error("failure_analysis_error", error=str(e))
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance report for the last N hours"""
        try:
            # Get recent traces within the time window
            cutoff_time = time.time() - (hours * 3600)
            all_traces = self.metrics_collector.get_recent_traces(1000)
            
            recent_traces = [t for t in all_traces if t.get('end_time', 0) > cutoff_time]
            
            if not recent_traces:
                return {
                    "message": f"No traces found in the last {hours} hours",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # Group by pipeline
            pipeline_stats = {}
            
            for trace in recent_traces:
                pipeline = trace.get('pipeline', 'unknown')
                if pipeline not in pipeline_stats:
                    pipeline_stats[pipeline] = {
                        'executions': 0,
                        'successful': 0,
                        'failed': 0,
                        'latencies': [],
                        'errors': []
                    }
                
                stats = pipeline_stats[pipeline]
                stats['executions'] += 1
                
                if trace.get('status') == 'success':
                    stats['successful'] += 1
                elif trace.get('status') == 'fail':
                    stats['failed'] += 1
                    if trace.get('error'):
                        stats['errors'].append(trace.get('error'))
                
                latency = trace.get('latency')
                if latency is not None:
                    stats['latencies'].append(latency)
            
            # Calculate final metrics
            report = {
                "time_window_hours": hours,
                "total_executions": len(recent_traces),
                "pipeline_performance": {}
            }
            
            for pipeline, stats in pipeline_stats.items():
                latencies = stats['latencies']
                avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
                
                report["pipeline_performance"][pipeline] = {
                    "executions": stats['executions'],
                    "successful": stats['successful'],
                    "failed": stats['failed'],
                    "success_rate": stats['successful'] / stats['executions'] if stats['executions'] > 0 else 0.0,
                    "average_latency": avg_latency,
                    "min_latency": min(latencies) if latencies else 0.0,
                    "max_latency": max(latencies) if latencies else 0.0,
                    "common_errors": list(set(stats['errors']))[:5]  # Top 5 unique errors
                }
            
            report["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return report
            
        except Exception as e:
            logger.error("performance_report_error", error=str(e))
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat() + "Z"}
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        try:
            overview = self.get_system_overview()
            
            if format.lower() == "json":
                return json.dumps(overview, indent=2, ensure_ascii=False)
            elif format.lower() == "csv":
                # Simple CSV export
                lines = ["pipeline,total_executions,successful_executions,failed_executions,success_rate,average_latency"]
                
                for pipeline, metrics in overview.get("pipeline_metrics", {}).items():
                    lines.append(f"{pipeline},{metrics.get('total_executions', 0)},{metrics.get('successful_executions', 0)},{metrics.get('failed_executions', 0)},{metrics.get('success_rate', 0):.3f},{metrics.get('average_latency', 0):.3f}")
                
                return "\n".join(lines)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error("export_metrics_error", format=format, error=str(e))
            return f"Error: {str(e)}"


# Global instance
_metrics_api = MetricsAPI()


def get_metrics_api() -> MetricsAPI:
    """Get global metrics API instance"""
    return _metrics_api


# Import time for performance report
import time
