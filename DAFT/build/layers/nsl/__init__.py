"""
Normalization Stress Layer (NSL)

Tests WAF and UTF-8 normalization resilience by injecting
malformed, overlong, and ambiguous token streams.
"""

from .normalization_stress import NormalizationStressLayer

__all__ = ["NormalizationStressLayer"]
