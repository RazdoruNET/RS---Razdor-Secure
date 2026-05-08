"""
SQL Inference Engine

Defensive module for analyzing SQL parser behavior and identifying
potential anomalies without offensive data extraction or credential access.
"""

from .sql_analyzer import SQLInferenceEngine
from .response_analyzer import ResponseAnalyzer

__all__ = ['SQLInferenceEngine', 'ResponseAnalyzer']
