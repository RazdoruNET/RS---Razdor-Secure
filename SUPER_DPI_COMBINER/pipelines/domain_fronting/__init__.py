"""
Domain Fronting пайплайны - техники CDN маскировки
"""

from .cdn_bypass import CDNBypassPipeline
from .host_header import HostHeaderPipeline

__all__ = [
    'CDNBypassPipeline',
    'HostHeaderPipeline'
]
