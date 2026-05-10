"""
Domain Fronting пайплайны - техники CDN маскировки
"""

from pipelines.domain_fronting.cdn_bypass import CDNBypassPipeline
from pipelines.domain_fronting.host_header import HostHeaderPipeline

__all__ = [
    'CDNBypassPipeline',
    'HostHeaderPipeline'
]
