#!/usr/bin/env python3
"""
Truth Module - слой правды о реальных I/O операциях
"""

from .instrumentation import (
    IOMonitor,
    get_io_monitor,
    enable_instrumentation,
    disable_instrumentation,
    require_real_io,
    async_require_real_io,
    IOOperationType,
    IOOperationRecord,
    SystemCallRecord
)

from .pipeline_wrapper import (
    PipelineExecutionTrace,
    ExecutionStatus,
    ValidationLevel,
    PipelineValidator,
    execute_with_truth,
    TruthWrapperRegistry,
    get_truth_registry,
    wrap_pipeline,
    IOValidationResult
)

from .metrics_engine import (
    TruthMetricsEngine,
    get_truth_metrics_engine,
    PipelineRunMetrics,
    SystemTruthMetrics,
    RunStatus
)

__all__ = [
    'IOMonitor',
    'get_io_monitor', 
    'enable_instrumentation',
    'disable_instrumentation',
    'require_real_io',
    'async_require_real_io',
    'IOOperationType',
    'IOOperationRecord',
    'SystemCallRecord',
    'PipelineExecutionTrace',
    'ExecutionStatus',
    'ValidationLevel',
    'PipelineValidator',
    'execute_with_truth',
    'TruthWrapperRegistry',
    'get_truth_registry',
    'wrap_pipeline',
    'IOValidationResult',
    'TruthMetricsEngine',
    'get_truth_metrics_engine',
    'PipelineRunMetrics',
    'SystemTruthMetrics',
    'RunStatus'
]
