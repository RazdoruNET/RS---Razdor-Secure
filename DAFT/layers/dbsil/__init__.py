"""
DB Stress Interface Layer (DB-SIL)

Tests database connection pool resilience, transaction starvation,
and query queue saturation under malformed auth payloads.
"""

from .db_stress import DBStressInterfaceLayer

__all__ = ["DBStressInterfaceLayer"]
