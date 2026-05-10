"""
Protocol Obfuscation пайплайны - обфускация протоколов
"""

from pipelines.protocol_obfuscation.http_fragmentation import HTTPFragmentationPipeline
from pipelines.protocol_obfuscation.custom_headers import CustomHeadersPipeline

__all__ = [
    'HTTPFragmentationPipeline',
    'CustomHeadersPipeline'
]
