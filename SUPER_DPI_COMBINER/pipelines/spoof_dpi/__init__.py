"""
SpoofDPI пайплайны - техники обхода через манипуляцию пакетами
"""

from .packet_shaper import PacketShaperPipeline
from .tls_fingerprint import TLSFingerprintPipeline
from .http_fragmentation import HTTPFragmentationPipeline

__all__ = [
    'PacketShaperPipeline',
    'TLSFingerprintPipeline', 
    'HTTPFragmentationPipeline'
]
