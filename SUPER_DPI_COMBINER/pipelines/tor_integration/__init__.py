"""
Tor Integration пайплайны - интеграция с Tor сетью
"""

from .tor_bridges import TorBridgesPipeline
from .darknet_access import DarknetAccessPipeline

__all__ = [
    'TorBridgesPipeline',
    'DarknetAccessPipeline'
]
