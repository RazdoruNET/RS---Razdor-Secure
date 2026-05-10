"""
Omega Transport пайплайны - транспортные мосты и прокси
"""

from pipelines.omega_transport.bridge_manager import BridgeManagerPipeline
from pipelines.omega_transport.proxy_chains import ProxyChainsPipeline

__all__ = [
    'BridgeManagerPipeline',
    'ProxyChainsPipeline'
]
