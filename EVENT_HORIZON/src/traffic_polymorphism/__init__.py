"""
Traffic Polymorphism Module

Tests robustness of middleware by generating varied HTTP traffic patterns
to identify parser inconsistencies and normalization pipeline issues.
"""

from .header_engine import HeaderVariabilityEngine
from .traffic_mutator import TrafficMutator

__all__ = ['HeaderVariabilityEngine', 'TrafficMutator']
