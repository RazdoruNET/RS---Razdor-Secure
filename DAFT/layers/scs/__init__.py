"""
Session Collapse Simulator (SCS)

Tests session management resilience by creating massive
session creation/termination scenarios and checking
consistency between stateless and stateful nodes.
"""

from .session_collapse import SessionCollapseSimulator

__all__ = ["SessionCollapseSimulator"]
