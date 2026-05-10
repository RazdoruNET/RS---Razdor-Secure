"""
SpoofDPI пайплайны - техники обхода через манипуляцию пакетами
"""

from super_dpi_combiner.pipelines.spoof_dpi.packet_shaper import PacketShaperPipeline
from super_dpi_combiner.pipelines.spoof_dpi.tls_fingerprint import TLSFingerprintPipeline
from super_dpi_combiner.pipelines.spoof_dpi.http_fragmentation import HTTPFragmentationPipeline

__all__ = [
    'PacketShaperPipeline',
    'TLSFingerprintPipeline', 
    'HTTPFragmentationPipeline'
]
