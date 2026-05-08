"""
EVENT_HORIZON — Defensive Authentication Resilience Framework (DARF)

A modular framework for analyzing and stress-testing authentication pipeline 
resilience in distributed enterprise systems.
"""

__version__ = "1.0.0"
__author__ = "EVENT_HORIZON Team"

from .core.engine import EventHorizonEngine
from .core.scoring import ResilienceScorer
from .core.reporting import ReportGenerator

__all__ = [
    "EventHorizonEngine",
    "ResilienceScorer", 
    "ReportGenerator"
]
