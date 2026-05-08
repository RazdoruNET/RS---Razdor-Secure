"""
EVENT_HORIZON Configuration Management

Provides configuration loading, scenario definitions, and
test parameter management for the framework.
"""

from .config_manager import ConfigManager
from .scenarios import ScenarioLibrary

__all__ = ["ConfigManager", "ScenarioLibrary"]
