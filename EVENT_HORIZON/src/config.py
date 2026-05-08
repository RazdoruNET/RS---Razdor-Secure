"""
Configuration management for EVENT_HORIZON framework.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
import yaml


@dataclass
class TrafficConfig:
    """Traffic generation configuration."""
    max_concurrent_requests: int = 100
    request_rate_limit: float = 50.0  # requests per second
    user_agents: List[str] = None
    accept_languages: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "curl/8.0.0",
                "Python-requests/2.28.0",
                "PostmanRuntime/7.29.0"
            ]
        if self.accept_languages is None:
            self.accept_languages = [
                "en-US,en;q=0.9",
                "en-GB,en;q=0.8",
                "ru-RU,ru;q=0.9,en;q=0.8",
                "de-DE,de;q=0.9,en;q=0.8",
                "fr-FR,fr;q=0.9,en;q=0.8"
            ]


@dataclass
class SafetyConfig:
    """Safety and stability configuration."""
    max_error_rate: float = 0.2  # 20% error rate threshold
    circuit_breaker_threshold: int = 5
    backoff_cooldown: int = 5  # seconds
    max_503_errors: int = 10
    latency_threshold: float = 5.0  # seconds


@dataclass
class ObservabilityConfig:
    """Observability and metrics configuration."""
    metrics_port: int = 8000
    log_level: str = "INFO"
    enable_prometheus: bool = True
    enable_structured_logging: bool = True


@dataclass
class EventHorizonConfig:
    """Main configuration for EVENT_HORIZON framework."""
    traffic: TrafficConfig = None
    safety: SafetyConfig = None
    observability: ObservabilityConfig = None
    target_url: str = "http://localhost:8080"
    
    def __post_init__(self):
        if self.traffic is None:
            self.traffic = TrafficConfig()
        if self.safety is None:
            self.safety = SafetyConfig()
        if self.observability is None:
            self.observability = ObservabilityConfig()
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "EventHorizonConfig":
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(
            traffic=TrafficConfig(**config_data.get('traffic', {})),
            safety=SafetyConfig(**config_data.get('safety', {})),
            observability=ObservabilityConfig(**config_data.get('observability', {})),
            target_url=config_data.get('target_url', 'http://localhost:8080')
        )
    
    def to_yaml(self, config_path: str):
        """Save configuration to YAML file."""
        config_dict = {
            'traffic': {
                'max_concurrent_requests': self.traffic.max_concurrent_requests,
                'request_rate_limit': self.traffic.request_rate_limit,
                'user_agents': self.traffic.user_agents,
                'accept_languages': self.traffic.accept_languages
            },
            'safety': {
                'max_error_rate': self.safety.max_error_rate,
                'circuit_breaker_threshold': self.safety.circuit_breaker_threshold,
                'backoff_cooldown': self.safety.backoff_cooldown,
                'max_503_errors': self.safety.max_503_errors,
                'latency_threshold': self.safety.latency_threshold
            },
            'observability': {
                'metrics_port': self.observability.metrics_port,
                'log_level': self.observability.log_level,
                'enable_prometheus': self.observability.enable_prometheus,
                'enable_structured_logging': self.observability.enable_structured_logging
            },
            'target_url': self.target_url
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
