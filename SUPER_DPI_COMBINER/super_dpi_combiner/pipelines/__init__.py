"""
Pipelines module - Изолированные пайплайны без зависимостей
"""

from .http_fragmentation import HTTPFragmentation
from .echo import Echo

__all__ = [
    'HTTPFragmentation',
    'Echo'
]
