"""
Darknet пайплайны - продвинутые даркнет техники
"""

from super_dpi_combiner.pipelines.darknet.i2p_garlic import I2PGarlicPipeline
from super_dpi_combiner.pipelines.darknet.freenet_p2p import FreenetP2PPipeline
from super_dpi_combiner.pipelines.darknet.yggdrasil_mesh import YggdrasilMeshPipeline
from super_dpi_combiner.pipelines.darknet.zeronet_bitcoin import ZeroNetBitcoinPipeline

__all__ = [
    'I2PGarlicPipeline',
    'FreenetP2PPipeline',
    'YggdrasilMeshPipeline',
    'ZeroNetBitcoinPipeline'
]
