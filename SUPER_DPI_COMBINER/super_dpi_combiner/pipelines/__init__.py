"""
Pipelines module - Минимальный набор рабочих пайплайнов
"""

from .http_fragmentation import HTTPFragmentation
from .echo import Echo

__all__ = [
    'HTTPFragmentation',
    'Echo'
]
