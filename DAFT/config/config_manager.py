"""
EVENT_HORIZON Configuration Manager

Handles loading and managing configuration for the framework,
including component definitions, test parameters, and system settings.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import structlog

from core.models import AuthComponent, AuthComponentType

logger = structlog.get_logger(__name__)


@dataclass
class FrameworkConfig:
    """Main framework configuration"""
    max_concurrent_requests: int = 100
    test_timeout_seconds: int = 300
    log_level: str = "INFO"
    output_directory: str = "reports"
    enable_visualizations: bool = True
    
    # Layer configurations
    nsl_config: Dict[str, Any] = field(default_factory=dict)
    scs_config: Dict[str, Any] = field(default_factory=dict)
    rlpm_config: Dict[str, Any] = field(default_factory=dict)
    dbsil_config: Dict[str, Any] = field(default_factory=dict)
    
    # Scoring configuration
    scoring_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComponentConfig:
    """Configuration for an authentication component"""
    component_id: str
    name: str
    type: str
    endpoint: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True


class ConfigManager:
    """
    Manages configuration loading and validation for EVENT_HORIZON.
    
    Supports YAML and JSON configuration files with validation
    and default value handling.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.framework_config: Optional[FrameworkConfig] = None
        self.components: Dict[str, AuthComponent] = {}
        
        logger.info("Config Manager initialized", config_dir=str(self.config_dir))
    
    def load_config(self, config_file: str) -> FrameworkConfig:
        """
        Load framework configuration from file.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
            
        Returns:
            Loaded framework configuration
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            logger.warning("Config file not found, using defaults", config_file=config_file)
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
            # Validate and create configuration
            self.framework_config = self._create_framework_config(config_data)
            
            logger.info("Configuration loaded successfully", config_file=config_file)
            return self.framework_config
            
        except Exception as e:
            logger.error("Failed to load configuration", config_file=config_file, error=str(e))
            raise
    
    def load_components(self, components_file: str) -> Dict[str, AuthComponent]:
        """
        Load component configurations from file.
        
        Args:
            components_file: Path to components configuration file
            
        Returns:
            Dictionary of loaded components
        """
        components_path = self.config_dir / components_file
        
        if not components_path.exists():
            logger.warning("Components file not found, using defaults", components_file=components_file)
            return self._get_default_components()
        
        try:
            with open(components_path, 'r', encoding='utf-8') as f:
                if components_path.suffix.lower() in ['.yaml', '.yml']:
                    components_data = yaml.safe_load(f)
                elif components_path.suffix.lower() == '.json':
                    components_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {components_path.suffix}")
            
            # Load components
            self.components = {}
            
            for comp_data in components_data.get("components", []):
                component = self._create_component(comp_data)
                self.components[component.id] = component
            
            logger.info("Components loaded successfully", 
                        components_file=components_file, 
                        count=len(self.components))
            
            return self.components
            
        except Exception as e:
            logger.error("Failed to load components", components_file=components_file, error=str(e))
            raise
    
    def save_config(self, config: FrameworkConfig, config_file: str) -> None:
        """
        Save framework configuration to file.
        
        Args:
            config: Framework configuration to save
            config_file: Target configuration file
        """
        config_path = self.config_dir / config_file
        
        # Convert to dictionary
        config_dict = {
            "max_concurrent_requests": config.max_concurrent_requests,
            "test_timeout_seconds": config.test_timeout_seconds,
            "log_level": config.log_level,
            "output_directory": config.output_directory,
            "enable_visualizations": config.enable_visualizations,
            "nsl_config": config.nsl_config,
            "scs_config": config.scs_config,
            "rlpm_config": config.rlpm_config,
            "dbsil_config": config.dbsil_config,
            "scoring_weights": config.scoring_weights
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                elif config_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
            logger.info("Configuration saved successfully", config_file=config_file)
            
        except Exception as e:
            logger.error("Failed to save configuration", config_file=config_file, error=str(e))
            raise
    
    def save_components(self, components_file: str) -> None:
        """
        Save current components configuration to file.
        
        Args:
            components_file: Target components file
        """
        components_path = self.config_dir / components_file
        
        # Convert to dictionary
        components_dict = {
            "components": [
                {
                    "component_id": comp.id,
                    "name": comp.name,
                    "type": comp.type.value,
                    "endpoint": comp.endpoint,
                    "config": comp.config,
                    "dependencies": comp.dependencies,
                    "enabled": True
                }
                for comp in self.components.values()
            ]
        }
        
        try:
            with open(components_path, 'w', encoding='utf-8') as f:
                if components_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(components_dict, f, default_flow_style=False, indent=2)
                elif components_path.suffix.lower() == '.json':
                    json.dump(components_dict, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config format: {components_path.suffix}")
            
            logger.info("Components saved successfully", components_file=components_file)
            
        except Exception as e:
            logger.error("Failed to save components", components_file=components_file, error=str(e))
            raise
    
    def _create_framework_config(self, config_data: Dict[str, Any]) -> FrameworkConfig:
        """Create framework configuration from loaded data"""
        return FrameworkConfig(
            max_concurrent_requests=config_data.get("max_concurrent_requests", 100),
            test_timeout_seconds=config_data.get("test_timeout_seconds", 300),
            log_level=config_data.get("log_level", "INFO"),
            output_directory=config_data.get("output_directory", "reports"),
            enable_visualizations=config_data.get("enable_visualizations", True),
            nsl_config=config_data.get("nsl_config", {}),
            scs_config=config_data.get("scs_config", {}),
            rlpm_config=config_data.get("rlpm_config", {}),
            dbsil_config=config_data.get("dbsil_config", {}),
            scoring_weights=config_data.get("scoring_weights", {
                "availability": 0.25,
                "performance": 0.20,
                "consistency": 0.20,
                "security": 0.15,
                "recovery": 0.20
            })
        )
    
    def _create_component(self, comp_data: Dict[str, Any]) -> AuthComponent:
        """Create AuthComponent from configuration data"""
        try:
            component_type = AuthComponentType(comp_data["type"])
        except ValueError:
            raise ValueError(f"Unknown component type: {comp_data['type']}")
        
        return AuthComponent(
            id=comp_data["component_id"],
            name=comp_data["name"],
            type=component_type,
            endpoint=comp_data["endpoint"],
            config=comp_data.get("config", {}),
            dependencies=comp_data.get("dependencies", [])
        )
    
    def _get_default_config(self) -> FrameworkConfig:
        """Get default framework configuration"""
        return FrameworkConfig()
    
    def _get_default_components(self) -> Dict[str, AuthComponent]:
        """Get default component configuration"""
        components = {}
        
        # Create a basic authentication pipeline
        components["waf_01"] = AuthComponent(
            id="waf_01",
            name="Web Application Firewall",
            type=AuthComponentType.WAF,
            endpoint="https://auth.example.com/waf",
            config={"rules_file": "waf_rules.json"},
            dependencies=[]
        )
        
        components["rl_01"] = AuthComponent(
            id="rl_01",
            name="Rate Limiter",
            type=AuthComponentType.RATE_LIMITER,
            endpoint="https://auth.example.com/rate-limit",
            config={"requests_per_minute": 100, "burst_size": 200},
            dependencies=["waf_01"]
        )
        
        components["lb_01"] = AuthComponent(
            id="lb_01",
            name="Load Balancer",
            type=AuthComponentType.LOAD_BALANCER,
            endpoint="https://auth.example.com/lb",
            config={"algorithm": "round_robin", "health_check_interval": 30},
            dependencies=["rl_01"]
        )
        
        components["sm_01"] = AuthComponent(
            id="sm_01",
            name="Session Manager",
            type=AuthComponentType.SESSION_MANAGER,
            endpoint="https://auth.example.com/sessions",
            config={"session_timeout": 3600, "cookie_secure": True},
            dependencies=["lb_01"]
        )
        
        components["db_01"] = AuthComponent(
            id="db_01",
            name="Authentication Database",
            type=AuthComponentType.DATABASE,
            endpoint="https://auth.example.com/db",
            config={"connection_pool_size": 100, "query_timeout": 30},
            dependencies=["sm_01"]
        )
        
        components["idp_01"] = AuthComponent(
            id="idp_01",
            name="Identity Provider",
            type=AuthComponentType.IDENTITY_FEDERATION,
            endpoint="https://auth.example.com/idp",
            config={"sso_enabled": True, "oauth_flows": ["authorization_code"]},
            dependencies=["db_01"]
        )
        
        return components
    
    def validate_config(self, config: FrameworkConfig) -> List[str]:
        """
        Validate framework configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if config.max_concurrent_requests <= 0:
            errors.append("max_concurrent_requests must be positive")
        
        if config.test_timeout_seconds <= 0:
            errors.append("test_timeout_seconds must be positive")
        
        if config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("log_level must be a valid logging level")
        
        # Validate scoring weights sum to 1.0
        if config.scoring_weights:
            weight_sum = sum(config.scoring_weights.values())
            if abs(weight_sum - 1.0) > 0.01:
                errors.append(f"scoring_weights must sum to 1.0, got {weight_sum}")
        
        return errors
    
    def get_component_by_id(self, component_id: str) -> Optional[AuthComponent]:
        """Get component by ID"""
        return self.components.get(component_id)
    
    def get_components_by_type(self, component_type: AuthComponentType) -> List[AuthComponent]:
        """Get all components of a specific type"""
        return [comp for comp in self.components.values() if comp.type == component_type]
    
    def add_component(self, component: AuthComponent) -> None:
        """Add a component to the configuration"""
        self.components[component.id] = component
        logger.info("Component added", component_id=component.id)
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the configuration"""
        if component_id in self.components:
            del self.components[component_id]
            logger.info("Component removed", component_id=component_id)
            return True
        return False
    
    def get_dependency_order(self) -> List[str]:
        """Get components in dependency order (topological sort)"""
        # Simple topological sort implementation
        ordered = []
        remaining = list(self.components.values())
        
        while remaining:
            for component in remaining[:]:
                # Check if all dependencies are already ordered
                if all(dep in ordered for dep in component.dependencies):
                    ordered.append(component.id)
                    remaining.remove(component)
                    break
            else:
                # Circular dependency - break arbitrarily
                ordered.append(remaining[0].id)
                remaining.remove(remaining[0])
        
        return ordered
