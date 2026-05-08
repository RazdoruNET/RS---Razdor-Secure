"""
Stability Agent

Autonomous stability management agent that monitors system health,
adjusts parameters, and ensures safe testing operations.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json

from ..safety_layer import StabilityController, StabilityConfig, StabilityLevel
from ..observability import StructuredLogger, MetricsCollector
from .executor import ExecutionContext, ExecutionStatus


class StabilityAction(Enum):
    """Types of stability actions."""
    ADJUST_RATE_LIMIT = "adjust_rate_limit"
    REDUCE_CONCURRENCY = "reduce_concurrency"
    INCREASE_TIMEOUTS = "increase_timeouts"
    ACTIVATE_CIRCUIT_BREAKER = "activate_circuit_breaker"
    PAUSE_EXECUTION = "pause_execution"
    STOP_EXECUTION = "stop_execution"
    SCALE_RESOURCES = "scale_resources"
    ADAPTIVE_THROTTLING = "adaptive_throttling"


@dataclass
class StabilityDecision:
    """Decision made by stability agent."""
    action: StabilityAction
    reason: str
    confidence: float
    parameters: Dict[str, Any]
    timestamp: float
    executed: bool = False
    execution_result: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class StabilityPolicy:
    """Policy for stability management."""
    name: str
    conditions: Dict[str, Any]
    actions: List[StabilityAction]
    priority: int
    enabled: bool = True


class StabilityAgent:
    """
    Autonomous stability management agent for safe testing operations.
    """
    
    def __init__(self, stability_controller: StabilityController,
                 metrics_collector: MetricsCollector):
        """
        Initialize stability agent.
        
        Args:
            stability_controller: Stability controller instance
            metrics_collector: Metrics collector instance
        """
        self.stability_controller = stability_controller
        self.metrics_collector = metrics_collector
        self.logger = StructuredLogger("stability_agent")
        
        # Agent state
        self.active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.decision_history: List[StabilityDecision] = []
        
        # Policies
        self.policies: List[StabilityPolicy] = []
        self._initialize_default_policies()
        
        # Action handlers
        self.action_handlers: Dict[StabilityAction, Callable] = {
            StabilityAction.ADJUST_RATE_LIMIT: self._handle_adjust_rate_limit,
            StabilityAction.REDUCE_CONCURRENCY: self._handle_reduce_concurrency,
            StabilityAction.INCREASE_TIMEOUTS: self._handle_increase_timeouts,
            StabilityAction.ACTIVATE_CIRCUIT_BREAKER: self._handle_activate_circuit_breaker,
            StabilityAction.PAUSE_EXECUTION: self._handle_pause_execution,
            StabilityAction.STOP_EXECUTION: self._handle_stop_execution,
            StabilityAction.SCALE_RESOURCES: self._handle_scale_resources,
            StabilityAction.ADAPTIVE_THROTTLING: self._handle_adaptive_throttling
        }
        
        # Current execution context
        self.current_context: Optional[ExecutionContext] = None
        
        # Callbacks
        self.decision_callbacks: List[Callable[[StabilityDecision], None]] = []
    
    def add_decision_callback(self, callback: Callable[[StabilityDecision], None]):
        """Add callback for stability decisions."""
        self.decision_callbacks.append(callback)
    
    def _initialize_default_policies(self):
        """Initialize default stability policies."""
        policies = [
            # Critical error rate policy
            StabilityPolicy(
                name="critical_error_rate",
                conditions={
                    "error_rate": {"operator": ">", "value": 0.2},
                    "duration": {"operator": ">", "value": 30}
                },
                actions=[StabilityAction.STOP_EXECUTION],
                priority=1
            ),
            
            # High error rate policy
            StabilityPolicy(
                name="high_error_rate",
                conditions={
                    "error_rate": {"operator": ">", "value": 0.1},
                    "duration": {"operator": ">", "value": 60}
                },
                actions=[StabilityAction.REDUCE_CONCURRENCY, StabilityAction.ADAPTIVE_THROTTLING],
                priority=2
            ),
            
            # High response time policy
            StabilityPolicy(
                name="high_response_time",
                conditions={
                    "avg_response_time": {"operator": ">", "value": 5.0},
                    "duration": {"operator": ">", "value": 45}
                },
                actions=[StabilityAction.ADJUST_RATE_LIMIT, StabilityAction.INCREASE_TIMEOUTS],
                priority=3
            ),
            
            # Circuit breaker policy
            StabilityPolicy(
                name="circuit_breaker_protection",
                conditions={
                    "circuit_breaker_open": {"operator": "==", "value": True}
                },
                actions=[StabilityAction.ADAPTIVE_THROTTLING, StabilityAction.PAUSE_EXECUTION],
                priority=2
            ),
            
            # Resource exhaustion policy
            StabilityPolicy(
                name="resource_exhaustion",
                conditions={
                    "cpu_usage": {"operator": ">", "value": 90},
                    "memory_usage": {"operator": ">", "value": 85}
                },
                actions=[StabilityAction.REDUCE_CONCURRENCY, StabilityAction.SCALE_RESOURCES],
                priority=2
            ),
            
            # System instability policy
            StabilityPolicy(
                name="system_instability",
                conditions={
                    "stability_level": {"operator": "in", "value": ["critical", "unstable"]}
                },
                actions=[StabilityAction.REDUCE_CONCURRENCY, StabilityAction.ADAPTIVE_THROTTLING],
                priority=1
            )
        ]
        
        self.policies = policies
    
    async def start_monitoring(self, context: Optional[ExecutionContext] = None):
        """Start stability monitoring."""
        if self.active:
            return
        
        self.current_context = context
        self.active = True
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Stability agent monitoring started",
                        component="stability_agent", operation="monitoring_start")
    
    async def stop_monitoring(self):
        """Stop stability monitoring."""
        self.active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        self.logger.info("Stability agent monitoring stopped",
                        component="stability_agent", operation="monitoring_stop")
    
    async def _monitoring_loop(self):
        """Main stability monitoring loop."""
        while self.active:
            try:
                # Evaluate policies
                decisions = await self._evaluate_policies()
                
                # Execute decisions
                for decision in decisions:
                    await self._execute_decision(decision)
                
                # Wait before next evaluation
                await asyncio.sleep(5.0)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Stability monitoring error: {str(e)}",
                                 component="stability_agent", error=e)
                await asyncio.sleep(5.0)
    
    async def _evaluate_policies(self) -> List[StabilityDecision]:
        """Evaluate all policies and return decisions."""
        decisions = []
        current_conditions = await self._get_current_conditions()
        
        # Sort policies by priority (lower number = higher priority)
        sorted_policies = sorted([p for p in self.policies if p.enabled], 
                               key=lambda p: p.priority)
        
        for policy in sorted_policies:
            if await self._evaluate_policy_conditions(policy, current_conditions):
                # Create decision for each action
                for action in policy.actions:
                    decision = StabilityDecision(
                        action=action,
                        reason=f"Policy '{policy.name}' triggered",
                        confidence=0.8,
                        parameters=policy.conditions.copy()
                    )
                    decisions.append(decision)
        
        return decisions
    
    async def _get_current_conditions(self) -> Dict[str, Any]:
        """Get current system conditions."""
        conditions = {}
        
        # Get stability controller metrics
        health_status = self.stability_controller.get_health_status()
        conditions.update(health_status)
        
        # Get metrics collector data
        all_metrics = self.metrics_collector.get_all_metrics()
        
        # Extract key metrics
        conditions["error_rate"] = health_status.get("error_rate", 0.0)
        conditions["avg_response_time"] = self._get_avg_response_time(all_metrics)
        conditions["circuit_breaker_open"] = health_status.get("circuit_breaker_state") == "open"
        conditions["stability_level"] = health_status.get("stability_level", "stable")
        
        # Get system metrics if available
        system_metrics = all_metrics.get("gauges", {})
        conditions["cpu_usage"] = system_metrics.get("system_cpu_usage", 0.0)
        conditions["memory_usage"] = system_metrics.get("system_memory_usage", 0.0)
        
        return conditions
    
    def _get_avg_response_time(self, all_metrics: Dict[str, Any]) -> float:
        """Get average response time from metrics."""
        histograms = all_metrics.get("histograms", {})
        http_duration = histograms.get("http_request_duration_seconds", {})
        return http_duration.get("mean", 0.0)
    
    async def _evaluate_policy_conditions(self, policy: StabilityPolicy, 
                                        conditions: Dict[str, Any]) -> bool:
        """Evaluate if policy conditions are met."""
        for condition_key, condition_spec in policy.conditions.items():
            if condition_key not in conditions:
                return False
            
            condition_value = conditions[condition_key]
            operator = condition_spec.get("operator")
            expected_value = condition_spec.get("value")
            
            if not self._evaluate_condition(condition_value, operator, expected_value):
                return False
        
        return True
    
    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate a single condition."""
        if operator == ">":
            return actual > expected
        elif operator == "<":
            return actual < expected
        elif operator == ">=":
            return actual >= expected
        elif operator == "<=":
            return actual <= expected
        elif operator == "==":
            return actual == expected
        elif operator == "!=":
            return actual != expected
        elif operator == "in":
            return actual in expected
        elif operator == "not_in":
            return actual not in expected
        else:
            return False
    
    async def _execute_decision(self, decision: StabilityDecision):
        """Execute a stability decision."""
        try:
            self.logger.info(f"Executing stability decision: {decision.action.value}",
                            component="stability_agent", operation="decision_execute",
                            action=decision.action.value, reason=decision.reason)
            
            # Get action handler
            handler = self.action_handlers.get(decision.action)
            if not handler:
                self.logger.warning(f"No handler for action: {decision.action.value}",
                                   component="stability_agent", action=decision.action.value)
                return
            
            # Execute action
            result = await handler(decision.parameters)
            decision.executed = True
            decision.execution_result = result
            
            # Add to history
            self.decision_history.append(decision)
            
            # Trigger callbacks
            for callback in self.decision_callbacks:
                try:
                    callback(decision)
                except Exception:
                    pass
            
            self.logger.info(f"Stability decision executed: {decision.action.value}",
                            component="stability_agent", operation="decision_complete",
                            action=decision.action.value, result=result)
        
        except Exception as e:
            decision.executed = True
            decision.execution_result = f"Error: {str(e)}"
            
            self.logger.error(f"Failed to execute decision {decision.action.value}: {str(e)}",
                             component="stability_agent", operation="decision_failed",
                             action=decision.action.value, error=e)
    
    async def _handle_adjust_rate_limit(self, parameters: Dict[str, Any]) -> str:
        """Handle rate limit adjustment."""
        current_conditions = await self._get_current_conditions()
        error_rate = current_conditions.get("error_rate", 0.0)
        
        # Calculate new rate limit based on error rate
        if error_rate > 0.2:
            reduction_factor = 0.5  # Reduce by 50%
        elif error_rate > 0.1:
            reduction_factor = 0.7  # Reduce by 30%
        else:
            reduction_factor = 0.9  # Reduce by 10%
        
        # Apply to current context if available
        if self.current_context and self.current_context.request_engine:
            current_rate = self.current_context.request_engine.rate_limit
            new_rate = current_rate * reduction_factor
            self.current_context.request_engine.rate_limit = new_rate
            
            return f"Rate limit adjusted from {current_rate:.1f} to {new_rate:.1f} req/s"
        
        return "Rate limit adjustment requested (no active context)"
    
    async def _handle_reduce_concurrency(self, parameters: Dict[str, Any]) -> str:
        """Handle concurrency reduction."""
        current_conditions = await self._get_current_conditions()
        cpu_usage = current_conditions.get("cpu_usage", 0.0)
        
        # Calculate reduction based on CPU usage
        if cpu_usage > 90:
            reduction_factor = 0.5  # Reduce by 50%
        elif cpu_usage > 80:
            reduction_factor = 0.7  # Reduce by 30%
        else:
            reduction_factor = 0.8  # Reduce by 20%
        
        # Apply to current context if available
        if self.current_context and self.current_context.request_engine:
            current_concurrency = self.current_context.request_engine.max_concurrent_requests
            new_concurrency = int(current_concurrency * reduction_factor)
            self.current_context.request_engine.max_concurrent_requests = new_concurrency
            
            return f"Concurrency reduced from {current_concurrency} to {new_concurrency}"
        
        return "Concurrency reduction requested (no active context)"
    
    async def _handle_increase_timeouts(self, parameters: Dict[str, Any]) -> str:
        """Handle timeout increase."""
        current_conditions = await self._get_current_conditions()
        avg_response_time = current_conditions.get("avg_response_time", 0.0)
        
        # Calculate new timeout based on response time
        new_timeout = max(10.0, avg_response_time * 3)
        
        # Apply to current context if available
        if self.current_context and self.current_context.request_engine:
            old_timeout = self.current_context.request_engine.timeout
            self.current_context.request_engine.timeout = new_timeout
            
            return f"Timeout increased from {old_timeout:.1f}s to {new_timeout:.1f}s"
        
        return "Timeout increase requested (no active context)"
    
    async def _handle_activate_circuit_breaker(self, parameters: Dict[str, Any]) -> str:
        """Handle circuit breaker activation."""
        self.stability_controller.circuit_breaker.force_open()
        return "Circuit breaker manually opened"
    
    async def _handle_pause_execution(self, parameters: Dict[str, Any]) -> str:
        """Handle execution pause."""
        if self.current_context:
            # This would need to be implemented in the executor
            return "Execution pause requested"
        return "Pause requested (no active context)"
    
    async def _handle_stop_execution(self, parameters: Dict[str, Any]) -> str:
        """Handle execution stop."""
        if self.current_context:
            # This would need to be implemented in the executor
            return "Execution stop requested"
        return "Stop requested (no active context)"
    
    async def _handle_scale_resources(self, parameters: Dict[str, Any]) -> str:
        """Handle resource scaling."""
        # This would integrate with container orchestration or cloud APIs
        self.logger.warning("Resource scaling requested but not implemented",
                           component="stability_agent", operation="scale_resources")
        return "Resource scaling requested (not implemented)"
    
    async def _handle_adaptive_throttling(self, parameters: Dict[str, Any]) -> str:
        """Handle adaptive throttling."""
        current_conditions = await self._get_current_conditions()
        error_rate = current_conditions.get("error_rate", 0.0)
        
        # Calculate throttle factor
        if error_rate > 0.2:
            throttle_factor = 0.3  # Heavy throttling
        elif error_rate > 0.1:
            throttle_factor = 0.6  # Moderate throttling
        else:
            throttle_factor = 0.8  # Light throttling
        
        # Apply to adaptive backoff if available
        if self.stability_controller.adaptive_backoff:
            self.stability_controller.adaptive_backoff.update_system_load(1.0 / throttle_factor)
            return f"Adaptive throttling applied with factor {throttle_factor}"
        
        return f"Adaptive throttling requested with factor {throttle_factor}"
    
    def add_policy(self, policy: StabilityPolicy):
        """Add a new stability policy."""
        self.policies.append(policy)
        self.logger.info(f"Added stability policy: {policy.name}",
                        component="stability_agent", operation="policy_add")
    
    def remove_policy(self, policy_name: str):
        """Remove a stability policy."""
        self.policies = [p for p in self.policies if p.name != policy_name]
        self.logger.info(f"Removed stability policy: {policy_name}",
                        component="stability_agent", operation="policy_remove")
    
    def enable_policy(self, policy_name: str):
        """Enable a stability policy."""
        for policy in self.policies:
            if policy.name == policy_name:
                policy.enabled = True
                self.logger.info(f"Enabled stability policy: {policy_name}",
                                component="stability_agent", operation="policy_enable")
                return
        
        self.logger.warning(f"Policy not found: {policy_name}",
                           component="stability_agent", operation="policy_enable_failed")
    
    def disable_policy(self, policy_name: str):
        """Disable a stability policy."""
        for policy in self.policies:
            if policy.name == policy_name:
                policy.enabled = False
                self.logger.info(f"Disabled stability policy: {policy_name}",
                                component="stability_agent", operation="policy_disable")
                return
        
        self.logger.warning(f"Policy not found: {policy_name}",
                           component="stability_agent", operation="policy_disable_failed")
    
    def get_decision_history(self, limit: int = 100) -> List[StabilityDecision]:
        """Get recent decision history."""
        return self.decision_history[-limit:] if self.decision_history else []
    
    def get_active_policies(self) -> List[StabilityPolicy]:
        """Get all active policies."""
        return [p for p in self.policies if p.enabled]
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "active": self.active,
            "current_context": self.current_context.scenario.name if self.current_context else None,
            "total_policies": len(self.policies),
            "active_policies": len(self.get_active_policies()),
            "decisions_made": len(self.decision_history),
            "recent_decisions": len([d for d in self.decision_history 
                                  if time.time() - d.timestamp < 300]),  # Last 5 minutes
            "stability_level": self.stability_controller.get_stability_level().value,
            "health_status": self.stability_controller.get_health_status()
        }
    
    def export_configuration(self, filename: str):
        """Export agent configuration to file."""
        config = {
            "policies": [
                {
                    "name": p.name,
                    "conditions": p.conditions,
                    "actions": [a.value for a in p.actions],
                    "priority": p.priority,
                    "enabled": p.enabled
                }
                for p in self.policies
            ],
            "export_timestamp": time.time()
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"Configuration exported to {filename}",
                        component="stability_agent", operation="config_export")
    
    def import_configuration(self, filename: str):
        """Import agent configuration from file."""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        # Clear existing policies
        self.policies.clear()
        
        # Import policies
        for policy_config in config.get("policies", []):
            policy = StabilityPolicy(
                name=policy_config["name"],
                conditions=policy_config["conditions"],
                actions=[StabilityAction(a) for a in policy_config["actions"]],
                priority=policy_config["priority"],
                enabled=policy_config.get("enabled", True)
            )
            self.policies.append(policy)
        
        self.logger.info(f"Configuration imported from {filename}",
                        component="stability_agent", operation="config_import")
    
    def reset_decision_history(self):
        """Reset decision history."""
        self.decision_history.clear()
        self.logger.info("Decision history reset",
                        component="stability_agent", operation="history_reset")
