"""
Adaptive пайплайны - адаптивные техники обхода
"""

from pipelines.adaptive.auto_switch import AutoSwitchPipeline
from pipelines.adaptive.ml_detection import MLDetectionPipeline

__all__ = [
    'AutoSwitchPipeline',
    'MLDetectionPipeline'
]
