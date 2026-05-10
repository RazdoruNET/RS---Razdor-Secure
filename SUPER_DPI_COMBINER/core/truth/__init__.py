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

__all__ = [
    'IOMonitor',
    'get_io_monitor', 
    'enable_instrumentation',
    'disable_instrumentation',
    'require_real_io',
    'async_require_real_io',
    'IOOperationType',
    'IOOperationRecord',
    'SystemCallRecord'
]
