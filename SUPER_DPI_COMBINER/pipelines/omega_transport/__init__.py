"""
Omega Transport пайплайны - транспортные мосты и прокси
"""

from .bridge_manager import BridgeManagerPipeline
from .proxy_chains import ProxyChainsPipeline

__all__ = [
    'BridgeManagerPipeline',
    'ProxyChainsPipeline'
]
