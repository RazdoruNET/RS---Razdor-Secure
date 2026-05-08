"""
Input Normalization Lab

Tests how WAF/proxy/app normalize input and checks consistency
across the parsing chain without offensive tamper automation.
"""

from .normalization_tester import InputNormalizationTester
from .charset_handler import CharsetHandler
from .encoding_analyzer import EncodingAnalyzer

__all__ = ['InputNormalizationTester', 'CharsetHandler', 'EncodingAnalyzer']
