"""
Tor Integration пайплайны - интеграция с Tor сетью
"""

from pipelines.tor_integration.tor_bridges import TorBridgesPipeline
from pipelines.tor_integration.darknet_access import DarknetAccessPipeline

__all__ = [
    'TorBridgesPipeline',
    'DarknetAccessPipeline'
]
