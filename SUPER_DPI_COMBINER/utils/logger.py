"""
Утилита логирования для Super DPI Combiner
Structured logging with pipeline tracing and metrics collection
"""

import logging
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import defaultdict, deque
from dataclasses import dataclass, asdict


@dataclass
class PipelineTrace:
    """Pipeline execution trace"""
    pipeline: str
    start_time: float
    end_time: Optional[float] = None
    status: Optional[str] = None
    latency: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics"""
    pipeline: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_latency: float = 0.0
    failure_reasons: Dict[str, int] = None
    
    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = defaultdict(int)


class StructuredLogger:
    """Structured logger with JSON output"""
    
    def __init__(self, name: str, log_file: Optional[str] = None, level: str = "INFO"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger(log_file, level)
    
    def _setup_logger(self, log_file: Optional[str], level: str):
        """Setup logger with structured JSON formatter"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # JSON formatter for structured logging
        formatter = logging.Formatter('%(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_structured(self, level: str, event: str, **kwargs):
        """Log structured event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "logger": self.name,
            **kwargs
        }
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(log_entry, ensure_ascii=False))
    
    def info(self, event: str, **kwargs):
        """Log info event"""
        self._log_structured("INFO", event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning event"""
        self._log_structured("WARNING", event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error event"""
        self._log_structured("ERROR", event, **kwargs)
    
    def debug(self, event: str, **kwargs):
        """Log debug event"""
        self._log_structured("DEBUG", event, **kwargs)


class GlobalMetricsCollector:
    """Global metrics collector for pipeline performance"""
    
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self.traces: deque = deque(maxlen=max_traces)
        self.metrics: Dict[str, PipelineMetrics] = {}
        self.lock = threading.Lock()
    
    def add_trace(self, trace: PipelineTrace):
        """Add pipeline execution trace"""
        with self.lock:
            self.traces.append(trace)
            
            # Update metrics
            if trace.pipeline not in self.metrics:
                self.metrics[trace.pipeline] = PipelineMetrics(pipeline=trace.pipeline)
            
            metric = self.metrics[trace.pipeline]
            metric.total_executions += 1
            
            if trace.status == "success":
                metric.successful_executions += 1
                if trace.latency is not None:
                    # Update average latency
                    total_latency = metric.average_latency * (metric.successful_executions - 1) + trace.latency
                    metric.average_latency = total_latency / metric.successful_executions
            elif trace.status == "fail":
                metric.failed_executions += 1
                if trace.error:
                    metric.failure_reasons[trace.error] += 1
    
    def get_metrics(self, pipeline: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific pipeline or all pipelines"""
        with self.lock:
            if pipeline:
                return asdict(self.metrics.get(pipeline, PipelineMetrics(pipeline=pipeline)))
            
            return {name: asdict(metric) for name, metric in self.metrics.items()}
    
    def get_recent_traces(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent execution traces"""
        with self.lock:
            return [asdict(trace) for trace in list(self.traces)[-count:]]
    
    def get_success_rate(self, pipeline: Optional[str] = None) -> Dict[str, float]:
        """Get success rate for pipelines"""
        with self.lock:
            if pipeline:
                metric = self.metrics.get(pipeline)
                if not metric or metric.total_executions == 0:
                    return {pipeline: 0.0}
                return {pipeline: metric.successful_executions / metric.total_executions}
            
            return {
                name: metric.successful_executions / metric.total_executions if metric.total_executions > 0 else 0.0
                for name, metric in self.metrics.items()
            }


class PipelineTracer:
    """Pipeline execution tracer"""
    
    def __init__(self, logger: StructuredLogger, metrics_collector: GlobalMetricsCollector):
        self.logger = logger
        self.metrics = metrics_collector
        self.active_traces: Dict[str, PipelineTrace] = {}
        self.lock = threading.Lock()
    
    def start_pipeline(self, pipeline: str, **metadata):
        """Start pipeline execution trace"""
        trace_id = f"{pipeline}_{time.time()}_{threading.get_ident()}"
        
        trace = PipelineTrace(
            pipeline=pipeline,
            start_time=time.time(),
            metadata=metadata
        )
        
        with self.lock:
            self.active_traces[trace_id] = trace
        
        self.logger.info("pipeline_start", pipeline=pipeline, trace_id=trace_id, **metadata)
        return trace_id
    
    def finish_pipeline(self, trace_id: str, status: str, error: Optional[str] = None, **metadata):
        """Finish pipeline execution trace"""
        with self.lock:
            trace = self.active_traces.pop(trace_id, None)
            if not trace:
                return
        
        trace.end_time = time.time()
        trace.status = status
        trace.latency = trace.end_time - trace.start_time
        trace.error = error
        
        if metadata:
            if trace.metadata:
                trace.metadata.update(metadata)
            else:
                trace.metadata = metadata
        
        # Add to metrics collector
        self.metrics.add_trace(trace)
        
        # Log completion
        log_data = {
            "pipeline": trace.pipeline,
            "trace_id": trace_id,
            "status": status,
            "latency": trace.latency
        }
        
        if error:
            log_data["error"] = error
        
        if trace.metadata:
            log_data.update(trace.metadata)
        
        if status == "success":
            self.logger.info("pipeline_success", **log_data)
        else:
            self.logger.error("pipeline_fail", **log_data)


# Global instances
_global_metrics = GlobalMetricsCollector()
_tracers: Dict[str, PipelineTracer] = {}


def get_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> StructuredLogger:
    """
    Создание и конфигурация структурированного логгера
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        level: Уровень логирования
        
    Returns:
        StructuredLogger: Сконфигурированный логгер
    """
    return StructuredLogger(name, log_file, level)


def get_tracer(name: str) -> PipelineTracer:
    """
    Получить tracer для логгера
    
    Args:
        name: Имя логгера
        
    Returns:
        PipelineTracer: Tracer для pipeline
    """
    if name not in _tracers:
        logger = get_logger(name)
        _tracers[name] = PipelineTracer(logger, _global_metrics)
    
    return _tracers[name]


def get_global_metrics() -> GlobalMetricsCollector:
    """
    Получить глобальный коллектор метрик
    
    Returns:
        GlobalMetricsCollector: Глобальный коллектор метрик
    """
    return _global_metrics


def log_pipeline_execution(pipeline_func):
    """
    Декоратор для автоматического логирования выполнения pipeline
    
    Args:
        pipeline_func: Функция pipeline
        
    Returns:
        Декорированная функция
    """
    def wrapper(*args, **kwargs):
        pipeline_name = pipeline_func.__name__
        tracer = get_tracer(pipeline_name)
        
        trace_id = tracer.start_pipeline(pipeline_name, args_count=len(args), kwargs_keys=list(kwargs.keys()))
        
        try:
            result = pipeline_func(*args, **kwargs)
            tracer.finish_pipeline(trace_id, "success")
            return result
        except Exception as e:
            tracer.finish_pipeline(trace_id, "fail", error=str(e))
            raise
    
    return wrapper


# Backward compatibility
def get_legacy_logger(name: str, log_file: Optional[str] = None, level: str = "INFO"):
    """
    Создание традиционного логгера для обратной совместимости
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        level: Уровень логирования
        
    Returns:
        logging.Logger: Сконфигурированный логгер
    """
    logger = logging.getLogger(name)
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
