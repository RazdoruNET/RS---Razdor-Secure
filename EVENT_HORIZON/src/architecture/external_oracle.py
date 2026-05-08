"""
External Oracle Interface

Provides external truth validation for system decisions.
Critical for preventing self-referential bias.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
import aiohttp


class OracleVerdict(Enum):
    """Oracle verdict types."""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class OracleValidationResult:
    """Result of oracle validation."""
    is_valid: bool
    verdict: OracleVerdict
    confidence: float
    reasoning: str
    external_data: Optional[Dict[str, Any]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ExternalOracle(ABC):
    """
    Abstract external oracle interface.
    
    Key requirements:
    - External to system (no internal state access)
    - Non-predictable from internal system state
    - Latency-tolerant
    - Provides ground truth validation
    """
    
    def __init__(self, oracle_config: Dict[str, Any]):
        self.config = oracle_config
        self.oracle_id = hashlib.sha256(
            json.dumps(oracle_config, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    @abstractmethod
    async def validate_contract(self, contract) -> OracleValidationResult:
        """
        Validate execution contract against external truth.
        
        Args:
            contract: ExecutionContract to validate
            
        Returns:
            OracleValidationResult with verdict
        """
        pass
    
    @abstractmethod
    async def validate_execution_state(self, 
                                   execution_id: str,
                                   system_state: Dict[str, Any]) -> OracleValidationResult:
        """
        Validate current system state against external truth.
        
        Args:
            execution_id: ID of execution
            system_state: Current system state
            
        Returns:
            OracleValidationResult with verdict
        """
        pass
    
    @abstractmethod
    async def get_ground_truth(self, 
                              metric_name: str,
                              time_range: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """
        Get ground truth value for a metric.
        
        Args:
            metric_name: Name of metric
            time_range: Optional time range for historical data
            
        Returns:
            Ground truth value or None if unavailable
        """
        pass
    
    def get_oracle_id(self) -> str:
        """Get unique oracle identifier."""
        return self.oracle_id


class ProductionMetricsOracle(ExternalOracle):
    """
    Oracle based on production metrics comparison.
    
    Compares test results against known production baselines.
    """
    
    def __init__(self, oracle_config: Dict[str, Any]):
        super().__init__(oracle_config)
        self.production_endpoint = oracle_config.get('production_endpoint')
        self.api_key = oracle_config.get('api_key')
        self.baselines = oracle_config.get('baselines', {})
        self.tolerance_threshold = oracle_config.get('tolerance_threshold', 0.1)
    
    async def validate_contract(self, contract) -> OracleValidationResult:
        """Validate contract against production baselines."""
        try:
            # Extract expected metrics from contract
            expected_metrics = self._extract_expected_metrics(contract)
            
            # Get production baselines
            production_metrics = await self._get_production_metrics(expected_metrics.keys())
            
            # Compare and validate
            violations = []
            total_comparisons = 0
            valid_comparisons = 0
            
            for metric_name, expected_value in expected_metrics.items():
                if metric_name in production_metrics:
                    production_value = production_metrics[metric_name]
                    
                    # Check if within tolerance
                    if self._is_within_tolerance(expected_value, production_value, metric_name):
                        valid_comparisons += 1
                    else:
                        violations.append({
                            'metric': metric_name,
                            'expected': expected_value,
                            'production': production_value,
                            'deviation': self._calculate_deviation(expected_value, production_value)
                        })
                    
                    total_comparisons += 1
            
            # Determine verdict
            if total_comparisons == 0:
                return OracleValidationResult(
                    is_valid=False,
                    verdict=OracleVerdict.UNKNOWN,
                    confidence=0.0,
                    reasoning="No comparable metrics found"
                )
            
            validity_rate = valid_comparisons / total_comparisons
            is_valid = validity_rate >= 0.8  # 80% of metrics within tolerance
            confidence = validity_rate
            
            return OracleValidationResult(
                is_valid=is_valid,
                verdict=OracleVerdict.VALID if is_valid else OracleVerdict.INVALID,
                confidence=confidence,
                reasoning=f"Contract validation: {valid_comparisons}/{total_comparisons} metrics within tolerance",
                external_data={
                    'violations': violations,
                    'validity_rate': validity_rate,
                    'total_comparisons': total_comparisons
                }
            )
            
        except Exception as e:
            return OracleValidationResult(
                is_valid=False,
                verdict=OracleVerdict.ERROR,
                confidence=0.0,
                reasoning=f"Oracle error: {str(e)}"
            )
    
    async def validate_execution_state(self, 
                                   execution_id: str,
                                   system_state: Dict[str, Any]) -> OracleValidationResult:
        """Validate current execution state against production."""
        try:
            # Get current production metrics
            production_state = await self._get_current_production_state()
            
            # Compare key indicators
            key_indicators = [
                'error_rate',
                'response_time_p95',
                'throughput',
                'availability'
            ]
            
            violations = []
            valid_indicators = 0
            
            for indicator in key_indicators:
                if indicator in system_state and indicator in production_state:
                    test_value = system_state[indicator]
                    prod_value = production_state[indicator]
                    
                    if self._is_within_tolerance(test_value, prod_value, indicator):
                        valid_indicators += 1
                    else:
                        violations.append({
                            'indicator': indicator,
                            'test_value': test_value,
                            'production_value': prod_value,
                            'deviation': self._calculate_deviation(test_value, prod_value)
                        })
            
            validity_rate = valid_indicators / len(key_indicators)
            is_valid = validity_rate >= 0.7  # 70% of indicators within tolerance
            
            return OracleValidationResult(
                is_valid=is_valid,
                verdict=OracleVerdict.VALID if is_valid else OracleVerdict.INVALID,
                confidence=validity_rate,
                reasoning=f"State validation: {valid_indicators}/{len(key_indicators)} indicators within tolerance",
                external_data={
                    'violations': violations,
                    'validity_rate': validity_rate,
                    'execution_id': execution_id
                }
            )
            
        except Exception as e:
            return OracleValidationResult(
                is_valid=False,
                verdict=OracleVerdict.ERROR,
                confidence=0.0,
                reasoning=f"Oracle error: {str(e)}"
            )
    
    async def get_ground_truth(self, 
                              metric_name: str,
                              time_range: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """Get ground truth value from production."""
        try:
            production_metrics = await self._get_production_metrics([metric_name])
            return production_metrics.get(metric_name)
        except Exception:
            return None
    
    def _extract_expected_metrics(self, contract) -> Dict[str, Any]:
        """Extract expected metrics from contract."""
        expected = {}
        
        # Extract from execution plan
        if hasattr(contract, 'execution_plan'):
            plan = contract.execution_plan
            
            # Resource requirements
            if 'resource_requirements' in plan:
                resources = plan['resource_requirements']
                expected['max_concurrent_requests'] = resources.get('max_concurrent_requests', 0)
                expected['estimated_memory_usage'] = self._parse_memory_usage(resources.get('estimated_memory_usage', '0MB'))
                expected['estimated_cpu_usage'] = self._parse_percentage(resources.get('estimated_cpu_usage', '0%'))
            
            # Performance expectations
            if 'scenarios' in plan:
                total_requests = sum(s.get('request_count', 0) for s in plan['scenarios'])
                expected['total_requests'] = total_requests
                
                # Extract success criteria
                success_rates = []
                for scenario in plan['scenarios']:
                    if 'success_criteria' in scenario:
                        criteria = scenario['success_criteria']
                        if 'min_success_rate' in criteria:
                            success_rates.append(criteria['min_success_rate'])
                        if 'max_response_time_p95' in criteria:
                            expected['max_response_time_p95'] = criteria['max_response_time_p95']
                
                if success_rates:
                    expected['min_success_rate'] = min(success_rates)
        
        return expected
    
    def _get_production_metrics(self, metric_names: List[str]) -> Dict[str, Any]:
        """Get metrics from production system."""
        # This would integrate with actual production monitoring
        # For now, return baselines from config
        production_metrics = {}
        
        for metric_name in metric_names:
            if metric_name in self.baselines:
                production_metrics[metric_name] = self.baselines[metric_name]
            elif metric_name in self._get_default_baselines():
                production_metrics[metric_name] = self._get_default_baselines()[metric_name]
        
        return production_metrics
    
    def _get_current_production_state(self) -> Dict[str, Any]:
        """Get current production state."""
        # This would query production monitoring systems
        # For now, return simulated production state
        return {
            'error_rate': 0.02,  # 2% error rate in production
            'response_time_p95': 1.2,  # 1.2s p95 response time
            'throughput': 1500,  # 1500 req/s
            'availability': 0.995  # 99.5% availability
        }
    
    def _get_default_baselines(self) -> Dict[str, Any]:
        """Get default production baselines."""
        return {
            'error_rate': 0.05,
            'response_time_p95': 2.0,
            'throughput': 1000,
            'availability': 0.99,
            'max_concurrent_requests': 200,
            'estimated_memory_usage': 2048,  # MB
            'estimated_cpu_usage': 70  # %
        }
    
    def _is_within_tolerance(self, 
                           test_value: float, 
                           production_value: float, 
                           metric_name: str) -> bool:
        """Check if test value is within tolerance of production."""
        if production_value == 0:
            return test_value == 0
        
        tolerance = self.tolerance_threshold
        
        # Adjust tolerance based on metric type
        if metric_name in ['error_rate']:
            tolerance *= 2.0  # Allow more tolerance for error rates
        elif metric_name in ['response_time_p95']:
            tolerance *= 1.5  # Less tolerance for response times
        elif metric_name in ['availability']:
            tolerance *= 0.5  # Less tolerance for availability
        
        deviation = abs(test_value - production_value) / production_value
        return deviation <= tolerance
    
    def _calculate_deviation(self, test_value: float, production_value: float) -> float:
        """Calculate percentage deviation."""
        if production_value == 0:
            return 0.0 if test_value == 0 else float('inf')
        
        return abs(test_value - production_value) / production_value
    
    def _parse_memory_usage(self, memory_str: str) -> float:
        """Parse memory usage string to MB."""
        memory_str = memory_str.upper().strip()
        if memory_str.endswith('GB'):
            return float(memory_str[:-2]) * 1024
        elif memory_str.endswith('MB'):
            return float(memory_str[:-2])
        elif memory_str.endswith('KB'):
            return float(memory_str[:-2]) / 1024
        else:
            return 0.0
    
    def _parse_percentage(self, percentage_str: str) -> float:
        """Parse percentage string."""
        percentage_str = percentage_str.strip()
        if percentage_str.endswith('%'):
            return float(percentage_str[:-1])
        else:
            return float(percentage_str)


class ManualVerificationOracle(ExternalOracle):
    """
    Oracle that requires manual verification.
    
    Used for critical security validations that require human judgment.
    """
    
    def __init__(self, oracle_config: Dict[str, Any]):
        super().__init__(oracle_config)
        self.verification_queue = asyncio.Queue()
        self.verification_results = {}
        self.notification_endpoint = oracle_config.get('notification_endpoint')
    
    async def validate_contract(self, contract) -> OracleValidationResult:
        """Queue contract for manual verification."""
        verification_id = hashlib.sha256(
            f"{contract.contract_id}{time.time()}".encode()
        ).hexdigest()[:16]
        
        # Queue for manual verification
        await self._queue_for_verification(verification_id, contract)
        
        # Return pending result
        return OracleValidationResult(
            is_valid=False,
            verdict=OracleVerdict.UNKNOWN,
            confidence=0.0,
            reasoning="Contract queued for manual verification",
            external_data={
                'verification_id': verification_id,
                'verification_type': 'manual',
                'notification_sent': await self._send_notification(verification_id, contract)
            }
        )
    
    async def validate_execution_state(self, 
                                   execution_id: str,
                                   system_state: Dict[str, Any]) -> OracleValidationResult:
        """Queue execution state for manual verification."""
        verification_id = hashlib.sha256(
            f"{execution_id}{time.time()}".encode()
        ).hexdigest()[:16]
        
        # Queue for manual verification
        await self._queue_for_verification(verification_id, {
            'execution_id': execution_id,
            'system_state': system_state,
            'type': 'execution_state'
        })
        
        return OracleValidationResult(
            is_valid=False,
            verdict=OracleVerdict.UNKNOWN,
            confidence=0.0,
            reasoning="Execution state queued for manual verification",
            external_data={
                'verification_id': verification_id,
                'verification_type': 'manual',
                'notification_sent': await self._send_notification(verification_id, system_state)
            }
        )
    
    async def get_ground_truth(self, 
                              metric_name: str,
                              time_range: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """Manual verification oracle doesn't provide ground truth."""
        return None
    
    async def _queue_for_verification(self, 
                                    verification_id: str, 
                                    data: Any):
        """Queue item for manual verification."""
        await self.verification_queue.put({
            'verification_id': verification_id,
            'data': data,
            'timestamp': time.time(),
            'status': 'pending'
        })
    
    async def _send_notification(self, verification_id: str, data: Any) -> bool:
        """Send notification for manual verification."""
        if not self.notification_endpoint:
            return False
        
        try:
            # This would send to notification system (email, Slack, etc.)
            # For now, just log the notification
            print(f"Manual verification required: {verification_id}")
            return True
        except Exception:
            return False
    
    async def submit_verification_result(self, 
                                     verification_id: str,
                                     is_valid: bool,
                                     reasoning: str,
                                     verifier: str):
        """Submit manual verification result."""
        self.verification_results[verification_id] = {
            'is_valid': is_valid,
            'reasoning': reasoning,
            'verifier': verifier,
            'timestamp': time.time()
        }


class OracleManager:
    """
    Manages multiple oracles and provides unified interface.
    """
    
    def __init__(self, oracle_configs: Dict[str, Dict[str, Any]]):
        self.oracles = {}
        self.primary_oracle = None
        
        # Initialize oracles
        for oracle_name, config in oracle_configs.items():
            oracle_type = config.get('type', 'production_metrics')
            
            if oracle_type == 'production_metrics':
                oracle = ProductionMetricsOracle(config)
            elif oracle_type == 'manual_verification':
                oracle = ManualVerificationOracle(config)
            else:
                continue
            
            self.oracles[oracle_name] = oracle
            
            # Set primary oracle
            if config.get('primary', False):
                self.primary_oracle = oracle
        
        # If no primary specified, use first oracle
        if not self.primary_oracle and self.oracles:
            self.primary_oracle = list(self.oracles.values())[0]
    
    async def validate_contract(self, contract) -> OracleValidationResult:
        """Validate contract using primary oracle."""
        if not self.primary_oracle:
            return OracleValidationResult(
                is_valid=False,
                verdict=OracleVerdict.ERROR,
                confidence=0.0,
                reasoning="No primary oracle configured"
            )
        
        return await self.primary_oracle.validate_contract(contract)
    
    async def validate_with_all_oracles(self, contract) -> Dict[str, OracleValidationResult]:
        """Validate contract with all configured oracles."""
        results = {}
        
        for oracle_name, oracle in self.oracles.items():
            try:
                result = await oracle.validate_contract(contract)
                results[oracle_name] = result
            except Exception as e:
                results[oracle_name] = OracleValidationResult(
                    is_valid=False,
                    verdict=OracleVerdict.ERROR,
                    confidence=0.0,
                    reasoning=f"Oracle error: {str(e)}"
                )
        
        return results
    
    def get_oracle_status(self) -> Dict[str, Any]:
        """Get status of all configured oracles."""
        status = {
            'total_oracles': len(self.oracles),
            'primary_oracle': self.primary_oracle.get_oracle_id() if self.primary_oracle else None,
            'oracles': {}
        }
        
        for name, oracle in self.oracles.items():
            status['oracles'][name] = {
                'oracle_id': oracle.get_oracle_id(),
                'type': oracle.__class__.__name__,
                'config': oracle.config
            }
        
        return status
