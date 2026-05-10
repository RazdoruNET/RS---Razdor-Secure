"""
Darknet пайплайны - продвинутые даркнет техники
"""

from pipelines.darknet.i2p_garlic import I2PGarlicPipeline
from pipelines.darknet.freenet_p2p import FreenetP2PPipeline
from pipelines.darknet.yggdrasil_mesh import YggdrasilMeshPipeline
from pipelines.darknet.gnunet_cadet import GNUnetCADETPipeline
from pipelines.darknet.zeronet_bitcoin import ZeroNetBitcoinPipeline
from pipelines.darknet.lokinet_llarp import LokinetLLARPPipeline
from pipelines.darknet.hyphanet_wot import HyphanetWoTPipeline

__all__ = [
    'I2PGarlicPipeline',
    'FreenetP2PPipeline',
    'YggdrasilMeshPipeline',
    'GNUnetCADETPipeline',
    'ZeroNetBitcoinPipeline',
    'LokinetLLARPPipeline',
    'HyphanetWoTPipeline'
]
