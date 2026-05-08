"""
Tests for EVENT_HORIZON Resilience Scoring System
"""

import pytest
import time

from event_horizon.core.scoring import ResilienceScorer, ScoringWeights
from event_horizon.core.models import (
    AssessmentResults, ComponentMetrics, FailureEvent, 
    SemanticDriftEvent, FailureType, ResilienceScore
)


class TestResilienceScorer:
    """Test cases for ResilienceScorer"""
    
    @pytest.fixture
    def scorer(self):
        """Create a test scorer instance"""
        weights = ScoringWeights(
            availability=0.3,
            performance=0.25,
            consistency=0.2,
            security=0.15,
            recovery=0.1
        )
        return ResilienceScorer(weights)
    
    @pytest.fixture
    def sample_results(self):
        """Create sample assessment results"""
        # Create component metrics
        component_metrics = {
            "waf_01": ComponentMetrics(
                component_id="waf_01",
                total_requests=1000,
                successful_requests=950,
                failed_requests=50,
                avg_response_time=0.05,
                max_response_time=0.2,
                min_response_time=0.01,
                error_rate=0.05,
                throughput=100,
                semantic_drift_events=[],
                failure_events=[]
            ),
            "db_01": ComponentMetrics(
                component_id="db_01",
                total_requests=800,
                successful_requests=720,
                failed_requests=80,
                avg_response_time=0.15,
                max_response_time=0.5,
                min_response_time=0.02,
                error_rate=0.1,
                throughput=80,
                semantic_drift_events=[],
                failure_events=[]
            )
        }
        
        # Create system metrics
        system_metrics = ComponentMetrics(
            component_id="system",
            total_requests=1800,
            successful_requests=1670,
            failed_requests=130,
            avg_response_time=0.08,
            max_response_time=0.5,
            min_response_time=0.01,
            error_rate=0.072,
            throughput=180,
            semantic_drift_events=[],
            failure_events=[]
        )
        
        # Create semantic drift events
        drift_events = [
            SemanticDriftEvent(
                request_id="req1",
                source_component="input",
                target_component="waf_01",
                input_data={"test": "data"},
                output_data={"test": "normalized_data"},
                drift_magnitude=0.3,
                drift_type="normalization_loss"
            )
        ]
        
        # Create failure events
        failure_events = [
            FailureEvent(
                id="fail1",
                component_id="db_01",
                failure_type=FailureType.CONNECTION_EXHAUSTION,
                severity=0.6,
                description="Connection pool exhausted",
                affected_requests=["req1", "req2"],
                recovery_time=time.time() + 10
            )
        ]
        
        system_metrics.failure_events = failure_events
        system_metrics.semantic_drift_events = drift_events
        
        return AssessmentResults(
            test_id="test_123",
            scenario_id="test_scenario",
            start_time=time.time() - 100,
            end_time=time.time(),
            component_metrics=component_metrics,
            system_metrics=system_metrics,
            resilience_scores=[],
            failure_topology={},
            auth_pipeline_breakpoints=[],
            normalization_loss_report={},
            session_integrity_heatmap={}
        )
    
    def test_scorer_initialization(self, scorer):
        """Test scorer initialization"""
        assert scorer.weights.availability == 0.3
        assert scorer.weights.performance == 0.25
        assert scorer.weights.consistency == 0.2
        assert scorer.weights.security == 0.15
        assert scorer.weights.recovery == 0.1
        assert len(scorer.scoring_history) == 0
    
    def test_system_score_calculation(self, scorer, sample_results):
        """Test system-wide resilience score calculation"""
        scores = scorer.calculate_resilience_scores(sample_results)
        
        # Should have system score and component scores
        assert len(scores) == 3  # 1 system + 2 components
        
        # Find system score
        system_score = next((s for s in scores if s.component_id is None), None)
        assert system_score is not None
        assert 0.0 <= system_score.score <= 1.0
        assert 0.0 <= system_score.confidence <= 1.0
        assert "availability" in system_score.breakdown
        assert "performance" in system_score.breakdown
        assert "consistency" in system_score.breakdown
        assert "security" in system_score.breakdown
        assert "recovery" in system_score.breakdown
    
    def test_component_score_calculation(self, scorer, sample_results):
        """Test component-level resilience score calculation"""
        scores = scorer.calculate_resilience_scores(sample_results)
        
        # Find component scores
        component_scores = [s for s in scores if s.component_id is not None]
        assert len(component_scores) == 2
        
        # Check WAF score (should be higher due to better performance)
        waf_score = next((s for s in component_scores if s.component_id == "waf_01"), None)
        assert waf_score is not None
        assert waf_score.score > 0.7  # Should be good
        
        # Check DB score (should be lower due to higher error rate)
        db_score = next((s for s in component_scores if s.component_id == "db_01"), None)
        assert db_score is not None
        assert db_score.score < waf_score.score  # Should be worse than WAF
    
    def test_availability_score_calculation(self, scorer):
        """Test availability score calculation"""
        # Perfect availability
        perfect_metrics = ComponentMetrics(
            component_id="test",
            total_requests=1000,
            successful_requests=1000,
            failed_requests=0,
            avg_response_time=0.1,
            max_response_time=0.2,
            min_response_time=0.01,
            error_rate=0.0,
            throughput=100,
            semantic_drift_events=[],
            failure_events=[]
        )
        
        score = scorer._calculate_availability_score(perfect_metrics)
        assert score == 1.0
        
        # Poor availability
        poor_metrics = ComponentMetrics(
            component_id="test",
            total_requests=1000,
            successful_requests=800,
            failed_requests=200,
            avg_response_time=0.1,
            max_response_time=0.2,
            min_response_time=0.01,
            error_rate=0.2,
            throughput=100,
            semantic_drift_events=[],
            failure_events=[]
        )
        
        score = scorer._calculate_availability_score(poor_metrics)
        assert score < 0.8
    
    def test_performance_score_calculation(self, scorer):
        """Test performance score calculation"""
        # Good performance
        good_metrics = ComponentMetrics(
            component_id="test",
            total_requests=1000,
            successful_requests=1000,
            failed_requests=0,
            avg_response_time=0.05,  # 50ms - good
            max_response_time=0.1,
            min_response_time=0.01,
            error_rate=0.0,
            throughput=150,  # High throughput
            semantic_drift_events=[],
            failure_events=[]
        )
        
        score = scorer._calculate_performance_score(good_metrics)
        assert score > 0.8
        
        # Poor performance
        poor_metrics = ComponentMetrics(
            component_id="test",
            total_requests=1000,
            successful_requests=1000,
            failed_requests=0,
            avg_response_time=0.5,  # 500ms - poor
            max_response_time=1.0,
            min_response_time=0.1,
            error_rate=0.0,
            throughput=50,  # Low throughput
            semantic_drift_events=[],
            failure_events=[]
        )
        
        score = scorer._calculate_performance_score(poor_metrics)
        assert score < 0.6
    
    def test_consistency_score_calculation(self, scorer, sample_results):
        """Test consistency score calculation"""
        score = scorer._calculate_consistency_score(sample_results)
        
        assert 0.0 <= score <= 1.0
        # Should be less than perfect due to drift events
        assert score < 1.0
    
    def test_security_score_calculation(self, scorer, sample_results):
        """Test security score calculation"""
        score = scorer._calculate_security_score(sample_results)
        
        assert 0.0 <= score <= 1.0
        # Should be less than perfect due to failure events
        assert score < 1.0
    
    def test_recovery_score_calculation(self, scorer, sample_results):
        """Test recovery score calculation"""
        score = scorer._calculate_recovery_score(sample_results)
        
        assert 0.0 <= score <= 1.0
        # Should be good since we have recovery times
        assert score > 0.5
    
    def test_confidence_calculation(self, scorer):
        """Test confidence score calculation"""
        # High sample size
        high_confidence = scorer._calculate_confidence(1000)
        assert high_confidence == 1.0
        
        # Medium sample size
        medium_confidence = scorer._calculate_confidence(500)
        assert 0.7 <= medium_confidence < 1.0
        
        # Low sample size
        low_confidence = scorer._calculate_confidence(50)
        assert 0.4 <= low_confidence < 0.7
        
        # Very low sample size
        very_low_confidence = scorer._calculate_confidence(5)
        assert very_low_confidence < 0.4
    
    def test_assessment_level_determination(self, scorer):
        """Test assessment level determination"""
        assert scorer._get_overall_assessment(0.95) == "EXCELLENT"
        assert scorer._get_overall_assessment(0.85) == "GOOD"
        assert scorer._get_overall_assessment(0.75) == "ACCEPTABLE"
        assert scorer._get_overall_assessment(0.65) == "NEEDS_IMPROVEMENT"
        assert scorer._get_overall_assessment(0.5) == "POOR"
        assert scorer._get_overall_assessment(0.3) == "CRITICAL"
    
    def test_scoring_history_tracking(self, scorer, sample_results):
        """Test scoring history tracking"""
        # Calculate scores
        scorer.calculate_resilience_scores(sample_results)
        
        # Check history
        assert len(scorer.scoring_history) == 1
        
        history_entry = scorer.scoring_history[0]
        assert "timestamp" in history_entry
        assert "test_id" in history_entry
        assert "system_score" in history_entry
        assert "overall_assessment" in history_entry
        assert history_entry["test_id"] == sample_results.test_id
    
    def test_scoring_summary(self, scorer, sample_results):
        """Test scoring summary generation"""
        # Calculate scores multiple times
        scorer.calculate_resilience_scores(sample_results)
        scorer.calculate_resilience_scores(sample_results)
        
        summary = scorer.get_scoring_summary()
        
        assert "latest_assessment" in summary
        assert "latest_score" in summary
        assert "score_trend" in summary
        assert "trend_direction" in summary
        assert "total_assessments" in summary
        assert "average_score" in summary
        assert "best_score" in summary
        assert "worst_score" in summary
        
        assert summary["total_assessments"] == 2
    
    def test_recommendations_generation(self, scorer):
        """Test recommendations generation"""
        # Poor score
        poor_score = ResilienceScore(
            component_id="test",
            score=0.4,
            confidence=0.8,
            breakdown={
                "availability": 0.5,
                "performance": 0.3,
                "consistency": 0.4,
                "security": 0.6,
                "recovery": 0.2
            }
        )
        
        recommendations = scorer.get_recommendations(poor_score)
        
        assert len(recommendations) > 0
        assert any("performance" in rec.lower() for rec in recommendations)
        assert any("recovery" in rec.lower() for rec in recommendations)
        
        # Good score
        good_score = ResilienceScore(
            component_id="test",
            score=0.9,
            confidence=0.9,
            breakdown={
                "availability": 0.95,
                "performance": 0.9,
                "consistency": 0.85,
                "security": 0.92,
                "recovery": 0.88
            }
        )
        
        recommendations = scorer.get_recommendations(good_score)
        assert any("performing well" in rec.lower() for rec in recommendations)
    
    def test_component_specific_scoring(self, scorer, sample_results):
        """Test component-specific scoring methods"""
        # Test component consistency scoring
        consistency_score = scorer._calculate_component_consistency_score("waf_01", sample_results)
        assert 0.0 <= consistency_score <= 1.0
        
        # Test component security scoring
        security_score = scorer._calculate_component_security_score("db_01", sample_results)
        assert 0.0 <= security_score <= 1.0
        
        # Test component recovery scoring
        recovery_score = scorer._calculate_component_recovery_score("waf_01", sample_results)
        assert 0.0 <= recovery_score <= 1.0


class TestScoringWeights:
    """Test cases for ScoringWeights"""
    
    def test_default_weights(self):
        """Test default scoring weights"""
        weights = ScoringWeights()
        
        assert weights.availability == 0.25
        assert weights.performance == 0.20
        assert weights.consistency == 0.20
        assert weights.security == 0.15
        assert weights.recovery == 0.20
    
    def test_custom_weights(self):
        """Test custom scoring weights"""
        weights = ScoringWeights(
            availability=0.3,
            performance=0.3,
            consistency=0.2,
            security=0.1,
            recovery=0.1
        )
        
        assert weights.availability == 0.3
        assert weights.performance == 0.3
        assert weights.consistency == 0.2
        assert weights.security == 0.1
        assert weights.recovery == 0.1
    
    def test_weight_sum_validation(self):
        """Test that weights sum to reasonable values"""
        weights = ScoringWeights()
        total = (weights.availability + weights.performance + 
                weights.consistency + weights.security + weights.recovery)
        
        # Should sum to 1.0
        assert abs(total - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])
