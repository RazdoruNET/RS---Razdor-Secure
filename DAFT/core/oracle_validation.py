"""
EVENT_HORIZON External Oracle Validation

Prevents self-referential evaluation loops by providing
external validation of system behavior and results.
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import structlog

from .models import TestRequest, TestResponse, AssessmentResults
from .trust_boundaries import DataContract, TrustZone

logger = structlog.get_logger(__name__)


class ValidationType(Enum):
    """Types of external validation"""
    SEMANTIC_CONSISTENCY = "semantic_consistency"
    CONTRACT_INTEGRITY = "contract_integrity"
    CAUSAL_VALIDITY = "causal_validity"
    PERFORMANCE_BOUNDS = "performance_bounds"
    SECURITY_INVARIANTS = "security_invariants"


class OracleResponse(Enum):
    """Oracle validation responses"""
    VALID = "valid"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"
    ERROR = "oracle_error"


@dataclass
class ValidationRule:
    """External validation rule"""
    rule_id: str
    validation_type: ValidationType
    description: str
    validator_func: callable
    confidence_threshold: float = 0.8
    enabled: bool = True


@dataclass
class OracleResult:
    """Result of oracle validation"""
    rule_id: str
    validation_type: ValidationType
    response: OracleResponse
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    explanation: str = ""


class ExternalOracle:
    """External validation system for preventing self-referential loops"""
    
    def __init__(self):
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.validation_history: List[OracleResult] = []
        self.known_good_patterns: Dict[str, Any] = {}
        self.known_bad_patterns: Dict[str, Any] = {}
        self.semantic_baseline: Optional[Dict[str, Any]] = None
        
        # Initialize validation rules
        self._initialize_validation_rules()
        
        logger.info("External Oracle initialized", rules_count=len(self.validation_rules))
    
    def _initialize_validation_rules(self):
        """Initialize external validation rules"""
        
        # Rule 1: Semantic consistency validation
        self.add_validation_rule(ValidationRule(
            rule_id="semantic_consistency_001",
            validation_type=ValidationType.SEMANTIC_CONSISTENCY,
            description="Validate semantic consistency across pipeline stages",
            validator_func=self._validate_semantic_consistency,
            confidence_threshold=0.7
        ))
        
        # Rule 2: Contract integrity validation
        self.add_validation_rule(ValidationRule(
            rule_id="contract_integrity_001",
            validation_type=ValidationType.CONTRACT_INTEGRITY,
            description="Validate data contract integrity",
            validator_func=self._validate_contract_integrity,
            confidence_threshold=0.9
        ))
        
        # Rule 3: Causal validity validation
        self.add_validation_rule(ValidationRule(
            rule_id="causal_validity_001",
            validation_type=ValidationType.CAUSAL_VALIDITY,
            description="Validate causal relationships in failures",
            validator_func=self._validate_causal_validity,
            confidence_threshold=0.6
        ))
        
        # Rule 4: Performance bounds validation
        self.add_validation_rule(ValidationRule(
            rule_id="performance_bounds_001",
            validation_type=ValidationType.PERFORMANCE_BOUNDS,
            description="Validate performance within expected bounds",
            validator_func=self._validate_performance_bounds,
            confidence_threshold=0.8
        ))
        
        # Rule 5: Security invariants validation
        self.add_validation_rule(ValidationRule(
            rule_id="security_invariants_001",
            validation_type=ValidationType.SECURITY_INVARIANTS,
            description="Validate security invariants are maintained",
            validator_func=self._validate_security_invariants,
            confidence_threshold=0.9
        ))
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a validation rule to the oracle"""
        self.validation_rules[rule.rule_id] = rule
        logger.debug("Validation rule added", rule_id=rule.rule_id)
    
    def validate_assessment_results(self, 
                                  results: AssessmentResults,
                                  original_requests: List[TestRequest],
                                  final_contracts: List[DataContract]) -> Dict[str, Any]:
        """Validate complete assessment results externally"""
        
        validation_results = []
        
        for rule_id, rule in self.validation_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Call validation function
                validation_context = {
                    'assessment_results': results,
                    'original_requests': original_requests,
                    'final_contracts': final_contracts,
                    'semantic_baseline': self.semantic_baseline
                }
                
                validation_result = rule.validator_func(validation_context)
                
                # Create oracle result
                oracle_result = OracleResult(
                    rule_id=rule_id,
                    validation_type=rule.validation_type,
                    response=validation_result['response'],
                    confidence=validation_result['confidence'],
                    evidence=validation_result.get('evidence', {}),
                    explanation=validation_result.get('explanation', '')
                )
                
                validation_results.append(oracle_result)
                self.validation_history.append(oracle_result)
                
            except Exception as e:
                logger.error("Validation rule failed", rule_id=rule_id, error=str(e))
                
                oracle_result = OracleResult(
                    rule_id=rule_id,
                    validation_type=rule.validation_type,
                    response=OracleResponse.ERROR,
                    confidence=0.0,
                    evidence={'error': str(e)},
                    explanation=f"Validation rule execution failed: {str(e)}"
                )
                validation_results.append(oracle_result)
        
        # Calculate overall validation score
        overall_score = self._calculate_overall_validation_score(validation_results)
        
        return {
            'validation_results': validation_results,
            'overall_score': overall_score,
            'is_valid': overall_score >= 0.7,
            'critical_issues': [r for r in validation_results 
                              if r.response == OracleResponse.INVALID and r.confidence > 0.8],
            'recommendations': self._generate_validation_recommendations(validation_results)
        }
    
    def _validate_semantic_consistency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate semantic consistency across pipeline stages"""
        final_contracts = context.get('final_contracts', [])
        
        if not final_contracts:
            return {
                'response': OracleResponse.UNCERTAIN,
                'confidence': 0.0,
                'explanation': 'No final contracts available for validation'
            }
        
        # Check for semantic drift between stages
        drift_detected = False
        total_drift = 0.0
        drift_count = 0
        
        for contract in final_contracts:
            if contract.trust_zone == TrustZone.DERIVED_TELEMETRY:
                telemetry_data = contract.data
                
                # Check for semantic drift indicators
                if 'drift_events' in telemetry_data:
                    drift_count += telemetry_data['drift_events']
                    total_drift += sum(
                        event.get('drift_magnitude', 0.0) 
                        for event in telemetry_data.get('drift_events', [])
                    )
                    drift_detected = True
        
        # Calculate confidence based on drift
        if drift_detected:
            avg_drift = total_drift / max(1, drift_count)
            confidence = max(0.0, 1.0 - avg_drift)
            
            return {
                'response': OracleResponse.INVALID if avg_drift > 0.3 else OracleResponse.VALID,
                'confidence': confidence,
                'evidence': {
                    'drift_count': drift_count,
                    'average_drift': avg_drift,
                    'total_drift': total_drift
                },
                'explanation': f'Semantic drift detected: {drift_count} events with average magnitude {avg_drift:.3f}'
            }
        else:
            return {
                'response': OracleResponse.VALID,
                'confidence': 0.9,
                'evidence': {'drift_detected': False},
                'explanation': 'No semantic drift detected'
            }
    
    def _validate_contract_integrity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data contract integrity"""
        final_contracts = context.get('final_contracts', [])
        
        if not final_contracts:
            return {
                'response': OracleResponse.UNCERTAIN,
                'confidence': 0.0,
                'explanation': 'No contracts available for integrity validation'
            }
        
        integrity_violations = []
        total_contracts = len(final_contracts)
        valid_contracts = 0
        
        for contract in final_contracts:
            # Verify contract integrity
            is_valid = contract.verify_integrity()
            
            if is_valid:
                valid_contracts += 1
            else:
                integrity_violations.append({
                    'contract_id': contract.contract_id,
                    'trust_zone': contract.trust_zone.value,
                    'violation': 'Integrity check failed'
                })
        
        confidence = valid_contracts / total_contracts if total_contracts > 0 else 0.0
        
        return {
            'response': OracleResponse.VALID if len(integrity_violations) == 0 else OracleResponse.INVALID,
            'confidence': confidence,
            'evidence': {
                'total_contracts': total_contracts,
                'valid_contracts': valid_contracts,
                'violations': integrity_violations
            },
            'explanation': f'Contract integrity: {valid_contracts}/{total_contracts} contracts valid'
        }
    
    def _validate_causal_validity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate causal relationships in failures"""
        results = context.get('assessment_results')
        
        if not results or not results.failure_topology:
            return {
                'response': OracleResponse.UNCERTAIN,
                'confidence': 0.0,
                'explanation': 'No failure topology available for causal validation'
            }
        
        topology = results.failure_topology
        failures = topology.get('failures', [])
        
        # Check for circular causality
        circular_causality_detected = False
        causal_violations = []
        
        # Simple circular causality detection
        for failure in failures:
            # Check if failure is both cause and effect of same type
            if failure.get('circular_reference', False):
                circular_causality_detected = True
                causal_violations.append({
                    'component': failure['component'],
                    'violation': 'Circular causality detected'
                })
        
        # Check temporal consistency
        temporal_violations = []
        for failure in failures:
            if 'timestamp' in failure and 'cause_timestamp' in failure:
                if failure['timestamp'] < failure['cause_timestamp']:
                    temporal_violations.append({
                        'component': failure['component'],
                        'violation': 'Effect precedes cause'
                    })
        
        total_violations = len(causal_violations) + len(temporal_violations)
        confidence = 1.0 - (total_violations / max(1, len(failures)))
        
        return {
            'response': OracleResponse.INVALID if total_violations > 0 else OracleResponse.VALID,
            'confidence': confidence,
            'evidence': {
                'circular_causality': circular_causality_detected,
                'causal_violations': causal_violations,
                'temporal_violations': temporal_violations,
                'total_violations': total_violations
            },
            'explanation': f'Causal validity: {total_violations} violations detected'
        }
    
    def _validate_performance_bounds(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance within expected bounds"""
        results = context.get('assessment_results')
        
        if not results or not results.system_metrics:
            return {
                'response': OracleResponse.UNCERTAIN,
                'confidence': 0.0,
                'explanation': 'No system metrics available for performance validation'
            }
        
        metrics = results.system_metrics
        
        # Define performance bounds
        bounds = {
            'max_response_time': 1.0,  # 1 second
            'max_error_rate': 0.1,   # 10%
            'min_throughput': 10.0,   # 10 req/s
            'max_memory_usage': 0.8     # 80% of available
        }
        
        violations = []
        
        # Check response time
        if metrics.avg_response_time > bounds['max_response_time']:
            violations.append({
                'metric': 'avg_response_time',
                'value': metrics.avg_response_time,
                'bound': bounds['max_response_time'],
                'violation': 'Response time exceeds maximum'
            })
        
        # Check error rate
        if metrics.error_rate > bounds['max_error_rate']:
            violations.append({
                'metric': 'error_rate',
                'value': metrics.error_rate,
                'bound': bounds['max_error_rate'],
                'violation': 'Error rate exceeds maximum'
            })
        
        # Check throughput
        if metrics.throughput < bounds['min_throughput']:
            violations.append({
                'metric': 'throughput',
                'value': metrics.throughput,
                'bound': bounds['min_throughput'],
                'violation': 'Throughput below minimum'
            })
        
        confidence = 1.0 - (len(violations) / len(bounds))
        
        return {
            'response': OracleResponse.INVALID if len(violations) > 0 else OracleResponse.VALID,
            'confidence': confidence,
            'evidence': {
                'performance_bounds': bounds,
                'violations': violations,
                'metrics': {
                    'avg_response_time': metrics.avg_response_time,
                    'error_rate': metrics.error_rate,
                    'throughput': metrics.throughput
                }
            },
            'explanation': f'Performance bounds: {len(violations)} violations detected'
        }
    
    def _validate_security_invariants(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security invariants are maintained"""
        final_contracts = context.get('final_contracts', [])
        original_requests = context.get('original_requests', [])
        
        if not final_contracts or not original_requests:
            return {
                'response': OracleResponse.UNCERTAIN,
                'confidence': 0.0,
                'explanation': 'Insufficient data for security validation'
            }
        
        security_violations = []
        
        # Check for data leakage
        telemetry_contracts = [
            contract for contract in final_contracts
            if contract.trust_zone == TrustZone.DERIVED_TELEMETRY
        ]
        
        for contract in telemetry_contracts:
            telemetry_data = contract.data
            
            # Check for sensitive data in telemetry
            sensitive_patterns = ['password', 'token', 'secret', 'key', 'credential']
            
            for pattern in sensitive_patterns:
                if pattern in str(telemetry_data).lower():
                    security_violations.append({
                        'contract_id': contract.contract_id,
                        'violation': f'Sensitive data pattern detected: {pattern}',
                        'severity': 'high'
                    })
        
        # Check for privilege escalation
        original_privileges = set()
        for request in original_requests:
            if 'privilege_level' in request.payload:
                original_privileges.add(request.payload['privilege_level'])
        
        final_privileges = set()
        for contract in final_contracts:
            if 'privilege_level' in contract.data:
                final_privileges.add(contract.data['privilege_level'])
        
        if final_privileges - original_privileges:
            security_violations.append({
                'violation': 'Privilege escalation detected',
                'original_privileges': list(original_privileges),
                'final_privileges': list(final_privileges),
                'severity': 'critical'
            })
        
        confidence = 1.0 - (len(security_violations) / 10.0)  # Arbitrary baseline
        
        return {
            'response': OracleResponse.INVALID if len(security_violations) > 0 else OracleResponse.VALID,
            'confidence': confidence,
            'evidence': {
                'security_violations': security_violations,
                'sensitive_data_detected': len([v for v in security_violations if 'sensitive' in v['violation']]) > 0,
                'privilege_escalation': len([v for v in security_violations if 'privilege' in v['violation']]) > 0
            },
            'explanation': f'Security invariants: {len(security_violations)} violations detected'
        }
    
    def _calculate_overall_validation_score(self, validation_results: List[OracleResult]) -> float:
        """Calculate overall validation score from all results"""
        if not validation_results:
            return 0.0
        
        # Weight different validation types
        weights = {
            ValidationType.SEMANTIC_CONSISTENCY: 0.3,
            ValidationType.CONTRACT_INTEGRITY: 0.25,
            ValidationType.CAUSAL_VALIDITY: 0.2,
            ValidationType.PERFORMANCE_BOUNDS: 0.15,
            ValidationType.SECURITY_INVARIANTS: 0.1
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for result in validation_results:
            weight = weights.get(result.validation_type, 0.1)
            
            # Convert response to numeric score
            if result.response == OracleResponse.VALID:
                score = 1.0
            elif result.response == OracleResponse.INVALID:
                score = 0.0
            elif result.response == OracleResponse.UNCERTAIN:
                score = 0.5
            else:  # ERROR
                score = 0.0
            
            weighted_score += weight * score * result.confidence
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_validation_recommendations(self, validation_results: List[OracleResult]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for result in validation_results:
            if result.response == OracleResponse.INVALID:
                if result.validation_type == ValidationType.SEMANTIC_CONSISTENCY:
                    recommendations.append("Review semantic drift detection algorithms and thresholds")
                elif result.validation_type == ValidationType.CONTRACT_INTEGRITY:
                    recommendations.append("Implement stronger data contract validation and immutability")
                elif result.validation_type == ValidationType.CAUSAL_VALIDITY:
                    recommendations.append("Review causal inference logic and temporal ordering")
                elif result.validation_type == ValidationType.PERFORMANCE_BOUNDS:
                    recommendations.append("Optimize performance or adjust performance bounds")
                elif result.validation_type == ValidationType.SECURITY_INVARIANTS:
                    recommendations.append("Review security invariants and data handling procedures")
        
        return list(set(recommendations))  # Remove duplicates
    
    def set_semantic_baseline(self, baseline: Dict[str, Any]):
        """Set semantic baseline for comparison"""
        self.semantic_baseline = baseline
        logger.info("Semantic baseline set", baseline_keys=list(baseline.keys()))
    
    def add_known_pattern(self, pattern_type: str, pattern: Dict[str, Any], is_good: bool):
        """Add known good or bad pattern for validation"""
        if is_good:
            self.known_good_patterns[pattern_type] = pattern
        else:
            self.known_bad_patterns[pattern_type] = pattern
        
        logger.debug("Pattern added", pattern_type=pattern_type, is_good=is_good)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation history"""
        if not self.validation_history:
            return {'message': 'No validation history available'}
        
        recent_validations = self.validation_history[-100:]  # Last 100 validations
        
        return {
            'total_validations': len(self.validation_history),
            'recent_validations': len(recent_validations),
            'overall_validity_rate': sum(
                1 for v in recent_validations 
                if v.response == OracleResponse.VALID
            ) / len(recent_validations),
            'average_confidence': sum(v.confidence for v in recent_validations) / len(recent_validations),
            'common_issues': self._get_common_validation_issues(recent_validations),
            'validation_types_distribution': self._get_validation_type_distribution(recent_validations)
        }
    
    def _get_common_validation_issues(self, validations: List[OracleResult]) -> List[str]:
        """Get most common validation issues"""
        issue_counts = {}
        
        for validation in validations:
            if validation.response == OracleResponse.INVALID:
                issue_counts[validation.explanation] = issue_counts.get(validation.explanation, 0) + 1
        
        return sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _get_validation_type_distribution(self, validations: List[OracleResult]) -> Dict[str, int]:
        """Get distribution of validation types"""
        type_counts = {}
        
        for validation in validations:
            type_name = validation.validation_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return type_counts
