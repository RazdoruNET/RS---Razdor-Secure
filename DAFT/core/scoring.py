"""
EVENT_HORIZON Resilience Scoring System

Calculates resilience scores for components and the overall system
based on test results, failure patterns, and performance metrics.
"""

import math
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import structlog

from .models import (
    ComponentMetrics, FailureEvent, SemanticDriftEvent,
    ResilienceScore, AssessmentResults, FailureType
)

logger = structlog.get_logger(__name__)


@dataclass
class ScoringWeights:
    """Weights for different scoring factors"""
    availability: float = 0.25      # Service availability and uptime
    performance: float = 0.20      # Response times and throughput
    consistency: float = 0.20      # Data consistency across components
    security: float = 0.15         # Resistance to attacks and bypasses
    recovery: float = 0.20         # Ability to recover from failures


class ResilienceScorer:
    """
    Calculates resilience scores based on assessment results.
    
    The scoring system considers multiple dimensions:
    - Availability: Service uptime and error rates
    - Performance: Response times and throughput
    - Consistency: Data consistency and semantic drift
    - Security: Resistance to various attack patterns
    - Recovery: Ability to recover from failures
    """
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        self.scoring_history: List[Dict[str, Any]] = []
        
        logger.info("Resilience Scorer initialized", weights=self.weights.__dict__)
    
    def calculate_resilience_scores(self, results: AssessmentResults) -> List[ResilienceScore]:
        """
        Calculate resilience scores for all components and the system.
        
        Args:
            results: Assessment results from the engine
            
        Returns:
            List of resilience scores
        """
        scores = []
        
        # Calculate system-wide score
        system_score = self._calculate_system_score(results)
        scores.append(system_score)
        
        # Calculate component scores
        for component_id, metrics in results.component_metrics.items():
            component_score = self._calculate_component_score(component_id, metrics, results)
            scores.append(component_score)
        
        # Store scoring history
        self.scoring_history.append({
            "timestamp": time.time(),
            "test_id": results.test_id,
            "system_score": system_score.score,
            "component_count": len(results.component_metrics),
            "overall_assessment": self._get_overall_assessment(system_score.score)
        })
        
        return scores
    
    def _calculate_system_score(self, results: AssessmentResults) -> ResilienceScore:
        """Calculate overall system resilience score"""
        system_metrics = results.system_metrics
        
        # Calculate individual dimension scores
        availability_score = self._calculate_availability_score(system_metrics)
        performance_score = self._calculate_performance_score(system_metrics)
        consistency_score = self._calculate_consistency_score(results)
        security_score = self._calculate_security_score(results)
        recovery_score = self._calculate_recovery_score(results)
        
        # Calculate weighted overall score
        overall_score = (
            availability_score * self.weights.availability +
            performance_score * self.weights.performance +
            consistency_score * self.weights.consistency +
            security_score * self.weights.security +
            recovery_score * self.weights.recovery
        )
        
        # Calculate confidence based on data volume
        confidence = self._calculate_confidence(system_metrics.total_requests)
        
        # Create score breakdown
        breakdown = {
            "availability": availability_score,
            "performance": performance_score,
            "consistency": consistency_score,
            "security": security_score,
            "recovery": recovery_score
        }
        
        return ResilienceScore(
            component_id=None,  # System-wide score
            score=overall_score,
            confidence=confidence,
            breakdown=breakdown
        )
    
    def _calculate_component_score(self, component_id: str, metrics: ComponentMetrics, 
                                 results: AssessmentResults) -> ResilienceScore:
        """Calculate resilience score for a specific component"""
        # Calculate individual dimension scores for component
        availability_score = self._calculate_availability_score(metrics)
        performance_score = self._calculate_performance_score(metrics)
        consistency_score = self._calculate_component_consistency_score(component_id, results)
        security_score = self._calculate_component_security_score(component_id, results)
        recovery_score = self._calculate_component_recovery_score(component_id, results)
        
        # Calculate weighted overall score
        overall_score = (
            availability_score * self.weights.availability +
            performance_score * self.weights.performance +
            consistency_score * self.weights.consistency +
            security_score * self.weights.security +
            recovery_score * self.weights.recovery
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(metrics.total_requests)
        
        # Create score breakdown
        breakdown = {
            "availability": availability_score,
            "performance": performance_score,
            "consistency": consistency_score,
            "security": security_score,
            "recovery": recovery_score
        }
        
        return ResilienceScore(
            component_id=component_id,
            score=overall_score,
            confidence=confidence,
            breakdown=breakdown
        )
    
    def _calculate_availability_score(self, metrics: ComponentMetrics) -> float:
        """Calculate availability score based on error rates"""
        if metrics.total_requests == 0:
            return 0.0
        
        # Base score from success rate
        success_rate = (metrics.total_requests - metrics.failed_requests) / metrics.total_requests
        
        # Apply logarithmic scaling for better sensitivity
        if success_rate >= 0.99:  # 99%+ success rate
            base_score = 1.0
        elif success_rate >= 0.95:  # 95-99% success rate
            base_score = 0.8 + 0.2 * (success_rate - 0.95) / 0.04
        elif success_rate >= 0.90:  # 90-95% success rate
            base_score = 0.6 + 0.2 * (success_rate - 0.90) / 0.05
        else:  # Below 90% success rate
            base_score = max(0.0, success_rate / 0.90 * 0.6)
        
        # Penalize high error rates more severely
        if metrics.error_rate > 0.1:  # More than 10% error rate
            base_score *= 0.5
        
        return min(1.0, base_score)
    
    def _calculate_performance_score(self, metrics: ComponentMetrics) -> float:
        """Calculate performance score based on response times and throughput"""
        if metrics.total_requests == 0:
            return 0.0
        
        # Score based on average response time (lower is better)
        # Assume acceptable response time is 100ms
        acceptable_response_time = 0.1  # 100ms
        
        if metrics.avg_response_time <= acceptable_response_time:
            response_time_score = 1.0
        elif metrics.avg_response_time <= acceptable_response_time * 2:
            # Linear penalty up to 2x acceptable time
            response_time_score = 1.0 - (metrics.avg_response_time - acceptable_response_time) / acceptable_response_time * 0.5
        elif metrics.avg_response_time <= acceptable_response_time * 5:
            # Exponential penalty beyond 2x
            excess_ratio = (metrics.avg_response_time - acceptable_response_time * 2) / (acceptable_response_time * 3)
            response_time_score = 0.5 * math.exp(-excess_ratio * 2)
        else:
            response_time_score = 0.1  # Very poor performance
        
        # Score based on throughput (higher is better)
        # Assume acceptable throughput is 100 requests/second
        acceptable_throughput = 100.0
        
        if metrics.throughput >= acceptable_throughput:
            throughput_score = 1.0
        elif metrics.throughput >= acceptable_throughput * 0.5:
            throughput_score = 0.5 + 0.5 * (metrics.throughput - acceptable_throughput * 0.5) / (acceptable_throughput * 0.5)
        else:
            throughput_score = metrics.throughput / (acceptable_throughput * 0.5) * 0.5
        
        # Combine scores (70% response time, 30% throughput)
        performance_score = response_time_score * 0.7 + throughput_score * 0.3
        
        return min(1.0, performance_score)
    
    def _calculate_consistency_score(self, results: AssessmentResults) -> float:
        """Calculate consistency score based on semantic drift and data integrity"""
        total_drift_events = len(results.semantic_drift_events)
        
        if total_drift_events == 0:
            return 1.0
        
        # Calculate average drift magnitude
        avg_drift = sum(event.drift_magnitude for event in results.semantic_drift_events) / total_drift_events
        
        # Penalize high drift magnitudes
        if avg_drift <= 0.1:  # Very low drift
            drift_score = 1.0
        elif avg_drift <= 0.3:  # Low drift
            drift_score = 0.8
        elif avg_drift <= 0.5:  # Medium drift
            drift_score = 0.6
        elif avg_drift <= 0.7:  # High drift
            drift_score = 0.4
        else:  # Very high drift
            drift_score = 0.2
        
        # Consider number of affected components
        affected_components = len(set(event.target_component for event in results.semantic_drift_events))
        total_components = len(results.component_metrics)
        
        if total_components > 0:
            component_impact = affected_components / total_components
            component_penalty = min(0.3, component_impact * 0.5)
        else:
            component_penalty = 0.0
        
        consistency_score = drift_score - component_penalty
        
        return max(0.0, min(1.0, consistency_score))
    
    def _calculate_security_score(self, results: AssessmentResults) -> float:
        """Calculate security score based on failure types and bypass attempts"""
        # Analyze failure events for security-related issues
        security_failures = [
            event for event in results.system_metrics.failure_events
            if any(security_term in event.failure_type.value.lower() 
                  for security_term in ["bypass", "injection", "spoof", "normalization"])
        ]
        
        total_failures = len(results.system_metrics.failure_events)
        
        if total_failures == 0:
            return 1.0
        
        # Calculate security failure ratio
        security_failure_ratio = len(security_failures) / total_failures
        
        # Base security score
        base_security_score = 1.0 - security_failure_ratio
        
        # Consider severity of security failures
        if security_failures:
            avg_severity = sum(event.severity for event in security_failures) / len(security_failures)
            severity_penalty = avg_severity * 0.3
        else:
            severity_penalty = 0.0
        
        # Consider normalization loss
        normalization_report = results.normalization_loss_report
        if normalization_report:
            normalization_impact = normalization_report.get("average_drift", 0.0)
            normalization_penalty = min(0.2, normalization_impact * 0.4)
        else:
            normalization_penalty = 0.0
        
        security_score = base_security_score - severity_penalty - normalization_penalty
        
        return max(0.0, min(1.0, security_score))
    
    def _calculate_recovery_score(self, results: AssessmentResults) -> float:
        """Calculate recovery score based on system ability to recover from failures"""
        failure_events = results.system_metrics.failure_events
        
        if not failure_events:
            return 1.0  # No failures to recover from
        
        # Calculate recovery metrics
        recovered_failures = [f for f in failure_events if f.recovery_time is not None]
        
        if not recovered_failures:
            return 0.0  # No recoveries
        
        # Calculate average recovery time
        recovery_times = [f.recovery_time - f.timestamp for f in recovered_failures]
        avg_recovery_time = sum(recovery_times) / len(recovery_times)
        
        # Score based on recovery time (lower is better)
        # Assume acceptable recovery time is 30 seconds
        acceptable_recovery_time = 30.0
        
        if avg_recovery_time <= acceptable_recovery_time:
            recovery_time_score = 1.0
        elif avg_recovery_time <= acceptable_recovery_time * 2:
            recovery_time_score = 0.7
        elif avg_recovery_time <= acceptable_recovery_time * 5:
            recovery_time_score = 0.4
        else:
            recovery_time_score = 0.1
        
        # Consider recovery rate
        recovery_rate = len(recovered_failures) / len(failure_events)
        
        # Combine scores
        recovery_score = recovery_time_score * 0.6 + recovery_rate * 0.4
        
        return min(1.0, recovery_score)
    
    def _calculate_component_consistency_score(self, component_id: str, results: AssessmentResults) -> float:
        """Calculate consistency score for a specific component"""
        # Get semantic drift events for this component
        component_drifts = [
            event for event in results.semantic_drift_events
            if event.target_component == component_id
        ]
        
        if not component_drifts:
            return 1.0
        
        # Calculate average drift magnitude for this component
        avg_drift = sum(event.drift_magnitude for event in component_drifts) / len(component_drifts)
        
        # Convert drift magnitude to consistency score
        consistency_score = max(0.0, 1.0 - avg_drift)
        
        return consistency_score
    
    def _calculate_component_security_score(self, component_id: str, results: AssessmentResults) -> float:
        """Calculate security score for a specific component"""
        # Get failure events for this component
        component_failures = [
            event for event in results.system_metrics.failure_events
            if event.component_id == component_id
        ]
        
        if not component_failures:
            return 1.0
        
        # Count security-related failures
        security_failures = [
            event for event in component_failures
            if any(security_term in event.failure_type.value.lower() 
                  for security_term in ["bypass", "injection", "spoof", "normalization"])
        ]
        
        security_failure_ratio = len(security_failures) / len(component_failures)
        security_score = 1.0 - security_failure_ratio
        
        return max(0.0, min(1.0, security_score))
    
    def _calculate_component_recovery_score(self, component_id: str, results: AssessmentResults) -> float:
        """Calculate recovery score for a specific component"""
        # Get failure events for this component
        component_failures = [
            event for event in results.system_metrics.failure_events
            if event.component_id == component_id
        ]
        
        if not component_failures:
            return 1.0
        
        # Calculate recovery rate
        recovered_failures = [f for f in component_failures if f.recovery_time is not None]
        recovery_rate = len(recovered_failures) / len(component_failures)
        
        return recovery_rate
    
    def _calculate_confidence(self, sample_size: int) -> float:
        """Calculate confidence score based on sample size"""
        # Minimum sample size for reasonable confidence
        min_sample_size = 100
        optimal_sample_size = 1000
        
        if sample_size >= optimal_sample_size:
            return 1.0
        elif sample_size >= min_sample_size:
            # Linear scaling between min and optimal
            return 0.7 + 0.3 * (sample_size - min_sample_size) / (optimal_sample_size - min_sample_size)
        elif sample_size >= 10:
            return 0.4 + 0.3 * (sample_size - 10) / (min_sample_size - 10)
        else:
            return max(0.1, sample_size / 10 * 0.4)
    
    def _get_overall_assessment(self, score: float) -> str:
        """Get overall assessment based on score"""
        if score >= 0.9:
            return "EXCELLENT"
        elif score >= 0.8:
            return "GOOD"
        elif score >= 0.7:
            return "ACCEPTABLE"
        elif score >= 0.6:
            return "NEEDS_IMPROVEMENT"
        elif score >= 0.4:
            return "POOR"
        else:
            return "CRITICAL"
    
    def get_scoring_summary(self) -> Dict[str, Any]:
        """Get summary of scoring history"""
        if not self.scoring_history:
            return {"message": "No scoring history available"}
        
        latest = self.scoring_history[-1]
        
        # Calculate trends
        if len(self.scoring_history) >= 2:
            previous = self.scoring_history[-2]
            score_trend = latest["system_score"] - previous["system_score"]
            trend_direction = "improving" if score_trend > 0.01 else "declining" if score_trend < -0.01 else "stable"
        else:
            score_trend = 0.0
            trend_direction = "insufficient_data"
        
        return {
            "latest_assessment": latest["overall_assessment"],
            "latest_score": latest["system_score"],
            "score_trend": score_trend,
            "trend_direction": trend_direction,
            "total_assessments": len(self.scoring_history),
            "average_score": sum(h["system_score"] for h in self.scoring_history) / len(self.scoring_history),
            "best_score": max(h["system_score"] for h in self.scoring_history),
            "worst_score": min(h["system_score"] for h in self.scoring_history)
        }
    
    def get_recommendations(self, score: ResilienceScore) -> List[str]:
        """Get recommendations based on score breakdown"""
        recommendations = []
        
        breakdown = score.breakdown
        
        if breakdown.get("availability", 1.0) < 0.8:
            recommendations.append("Improve error handling and increase service availability")
        
        if breakdown.get("performance", 1.0) < 0.8:
            recommendations.append("Optimize response times and increase throughput")
        
        if breakdown.get("consistency", 1.0) < 0.8:
            recommendations.append("Address semantic drift and improve data consistency")
        
        if breakdown.get("security", 1.0) < 0.8:
            recommendations.append("Strengthen security measures against bypass attempts")
        
        if breakdown.get("recovery", 1.0) < 0.8:
            recommendations.append("Improve failure detection and recovery mechanisms")
        
        if not recommendations:
            recommendations.append("System is performing well across all dimensions")
        
        return recommendations
