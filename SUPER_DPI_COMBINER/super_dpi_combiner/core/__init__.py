"""
Core module - Стабилизированные essential компоненты
"""

from .contracts import BasePipeline, Request, Response, PipelineStatus
from .runner import Runner
from .http_client import HTTPClient
from .logging import get_logger
from .shutdown import get_shutdown_manager

__all__ = [
    'BasePipeline',
    'Request', 
    'Response',
    'PipelineStatus',
    'Runner',
    'HTTPClient',
    'get_logger',
    'get_shutdown_manager'
]
