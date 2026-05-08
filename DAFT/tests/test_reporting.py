"""
Tests for EVENT_HORIZON Reporting System
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from event_horizon.core.reporting import ReportGenerator
from event_horizon.core.models import (
    AssessmentResults, ComponentMetrics, FailureEvent, 
    SemanticDriftEvent, FailureType, ResilienceScore
)


class TestReportGenerator:
    """Test cases for ReportGenerator"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def reporter(self, temp_dir):
        """Create a test reporter instance"""
        return ReportGenerator(output_dir=temp_dir)
    
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
                semantic_drift_events=[
                    SemanticDriftEvent(
                        request_id="req1",
                        source_component="input",
                        target_component="waf_01",
                        input_data={"test": "data"},
                        output_data={"test": "normalized_data"},
                        drift_magnitude=0.3,
                        drift_type="normalization_loss"
                    )
                ],
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
                failure_events=[
                    FailureEvent(
                        id="fail1",
                        component_id="db_01",
                        failure_type=FailureType.CONNECTION_EXHAUSTION,
                        severity=0.6,
                        description="Connection pool exhausted",
                        affected_requests=["req1", "req2"],
                        recovery_time=1234567890
                    )
                ]
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
            semantic_drift_events=[
                SemanticDriftEvent(
                    request_id="req1",
                    source_component="input",
                    target_component="waf_01",
                    input_data={"test": "data"},
                    output_data={"test": "normalized_data"},
                    drift_magnitude=0.3,
                    drift_type="normalization_loss"
                )
            ],
            failure_events=[
                FailureEvent(
                    id="fail1",
                    component_id="db_01",
                    failure_type=FailureType.CONNECTION_EXHAUSTION,
                    severity=0.6,
                    description="Connection pool exhausted",
                    affected_requests=["req1", "req2"],
                    recovery_time=1234567890
                )
            ]
        )
        
        return AssessmentResults(
            test_id="test_123",
            scenario_id="test_scenario",
            start_time=1234567800,
            end_time=1234567900,
            component_metrics=component_metrics,
            system_metrics=system_metrics,
            resilience_scores=[],
            failure_topology={
                "nodes": [
                    {"id": "waf_01", "name": "Web Application Firewall", "type": "waf"},
                    {"id": "db_01", "name": "Database", "type": "database"}
                ],
                "edges": [
                    {"source": "waf_01", "target": "db_01"}
                ],
                "failures": [
                    {"component": "db_01", "severity": 0.6, "type": "connection_exhaustion"}
                ]
            },
            auth_pipeline_breakpoints=["db_01: High error rate (10.00%)"],
            normalization_loss_report={
                "total_events": 1,
                "average_drift": 0.3,
                "affected_components": ["waf_01"],
                "drift_distribution": {"low": 1, "medium": 0, "high": 0}
            },
            session_integrity_heatmap={
                "session_failures": 0,
                "failure_density": 0.0,
                "hotspots": []
            }
        )
    
    @pytest.fixture
    def sample_scores(self):
        """Create sample resilience scores"""
        return [
            ResilienceScore(
                component_id=None,
                score=0.75,
                confidence=0.85,
                breakdown={
                    "availability": 0.8,
                    "performance": 0.9,
                    "consistency": 0.7,
                    "security": 0.8,
                    "recovery": 0.6
                }
            ),
            ResilienceScore(
                component_id="waf_01",
                score=0.85,
                confidence=0.9,
                breakdown={
                    "availability": 0.9,
                    "performance": 0.95,
                    "consistency": 0.7,
                    "security": 0.9,
                    "recovery": 0.8
                }
            ),
            ResilienceScore(
                component_id="db_01",
                score=0.65,
                confidence=0.8,
                breakdown={
                    "availability": 0.7,
                    "performance": 0.8,
                    "consistency": 0.6,
                    "security": 0.7,
                    "recovery": 0.5
                }
            )
        ]
    
    def test_reporter_initialization(self, reporter, temp_dir):
        """Test reporter initialization"""
        assert reporter.output_dir == Path(temp_dir)
        assert reporter.output_dir.exists()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_executive_summary_generation(self, mock_close, mock_savefig, reporter, sample_results, sample_scores):
        """Test executive summary report generation"""
        summary_file = reporter.generate_executive_summary(sample_results, sample_scores)
        
        assert Path(summary_file).exists()
        assert summary_file.endswith('.html')
        
        # Check file content
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "EVENT_HORIZON Resilience Assessment" in content
            assert "0.750" in content  # Score should be in content
            assert "GOOD" in content  # Assessment level should be in content
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_component_report_generation(self, mock_close, mock_savefig, reporter, sample_results, sample_scores):
        """Test component analysis report generation"""
        component_file = reporter.generate_component_report(sample_results, sample_scores)
        
        assert Path(component_file).exists()
        assert component_file.endswith('.html')
        
        # Check file content
        with open(component_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Component Resilience Analysis" in content
            assert "waf_01" in content
            assert "db_01" in content
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('networkx.spring_layout')
    def test_topology_report_generation(self, mock_layout, mock_close, mock_savefig, reporter, sample_results):
        """Test topology analysis report generation"""
        mock_layout.return_value = {"waf_01": [0, 0], "db_01": [1, 1]}
        
        topology_file = reporter.generate_topology_report(sample_results)
        
        assert Path(topology_file).exists()
        assert topology_file.endswith('.html')
        
        # Check file content
        with open(topology_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Failure Topology Analysis" in content
            assert "Graph Metrics" in content
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_visualizations_generation(self, mock_close, mock_savefig, reporter, sample_results, sample_scores):
        """Test visualization generation"""
        viz_files = reporter.generate_visualizations(sample_results, sample_scores)
        
        # Should generate multiple visualization files
        assert len(viz_files) > 0
        
        for viz_type, viz_file in viz_files.items():
            assert Path(viz_file).exists()
            assert viz_file.endswith('.png')
    
    def test_json_export_generation(self, reporter, sample_results, sample_scores):
        """Test JSON export generation"""
        json_file = reporter.generate_json_export(sample_results, sample_scores)
        
        assert Path(json_file).exists()
        assert json_file.endswith('.json')
        
        # Check file content
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            assert "metadata" in content
            assert "assessment_results" in content
            assert content["metadata"]["test_id"] == sample_results.test_id
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_all_reports_generation(self, mock_close, mock_savefig, reporter, sample_results, sample_scores):
        """Test complete report generation"""
        report_files = reporter.generate_all_reports(sample_results, sample_scores)
        
        # Should generate all report types
        assert "executive_summary" in report_files
        assert "component_analysis" in report_files
        assert "failure_topology" in report_files
        assert "json_export" in report_files
        
        # All files should exist
        for report_type, file_path in report_files.items():
            assert Path(file_path).exists()
    
    def test_assessment_level_determination(self, reporter):
        """Test assessment level determination"""
        assert reporter._get_assessment_level(0.95) == "EXCELLENT"
        assert reporter._get_assessment_level(0.85) == "GOOD"
        assert reporter._get_assessment_level(0.75) == "ACCEPTABLE"
        assert reporter._get_assessment_level(0.65) == "NEEDS_IMPROVEMENT"
        assert reporter._get_assessment_level(0.5) == "POOR"
        assert reporter._get_assessment_level(0.3) == "CRITICAL"
    
    def test_critical_findings_extraction(self, reporter, sample_results):
        """Test critical findings extraction"""
        findings = reporter._extract_critical_findings(sample_results, [])
        
        assert len(findings) > 0
        assert any("error rate" in finding.lower() for finding in findings)
        assert any("semantic drift" in finding.lower() for finding in findings)
    
    def test_top_recommendations_generation(self, reporter, sample_results):
        """Test top recommendations generation"""
        system_score = ResilienceScore(
            component_id=None,
            score=0.6,  # Lower score to trigger recommendations
            confidence=0.8,
            breakdown={
                "availability": 0.7,
                "performance": 0.5,  # Lowest - should trigger performance recommendation
                "consistency": 0.6,
                "security": 0.8,
                "recovery": 0.4  # Second lowest - should trigger recovery recommendation
            }
        )
        
        recommendations = reporter._get_top_recommendations(system_score, sample_results)
        
        assert len(recommendations) > 0
        assert any("performance" in rec.lower() for rec in recommendations)
        assert any("recovery" in rec.lower() for rec in recommendations)
    
    def test_component_recommendations(self, reporter, sample_results):
        """Test component-specific recommendations"""
        component_score = ResilienceScore(
            component_id="db_01",
            score=0.5,  # Poor score
            confidence=0.8,
            breakdown={
                "availability": 0.6,
                "performance": 0.4,
                "consistency": 0.5,
                "security": 0.7,
                "recovery": 0.3
            }
        )
        
        # Create metrics with issues
        metrics = ComponentMetrics(
            component_id="db_01",
            total_requests=1000,
            successful_requests=800,
            failed_requests=200,
            avg_response_time=0.3,  # Slow
            max_response_time=1.0,
            min_response_time=0.1,
            error_rate=0.2,  # High error rate
            throughput=50,
            semantic_drift_events=[
                SemanticDriftEvent(
                    request_id="req1",
                    source_component="input",
                    target_component="db_01",
                    input_data={"test": "data"},
                    output_data={"test": "modified_data"},
                    drift_magnitude=0.4,
                    drift_type="data_transformation"
                )
            ],
            failure_events=[]
        )
        
        recommendations = reporter._get_component_recommendations(component_score, metrics)
        
        assert len(recommendations) > 0
        assert any("attention" in rec.lower() for rec in recommendations)
        assert any("error" in rec.lower() for rec in recommendations)
        assert any("performance" in rec.lower() for rec in recommendations)
    
    @patch('networkx.spring_layout')
    def test_topology_analysis(self, mock_layout, reporter, sample_results):
        """Test topology analysis methods"""
        mock_layout.return_value = {"waf_01": [0, 0], "db_01": [1, 1]}
        
        topology = sample_results.failure_topology
        
        # Test failure path finding
        paths = reporter._find_failure_paths(topology)
        assert isinstance(paths, list)
        
        # Test critical node finding
        critical_nodes = reporter._find_critical_nodes(topology)
        assert isinstance(critical_nodes, list)
        
        # Test isolated component finding
        isolated = reporter._find_isolated_components(topology)
        assert isinstance(isolated, list)
        
        # Test resilience implications
        implications = reporter._analyze_resilience_implications(topology)
        assert "single_points_of_failure" in implications
        assert "redundancy_level" in implications
        assert "cascade_risk" in implications
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_score_chart_generation(self, mock_close, mock_savefig, reporter, sample_scores):
        """Test score breakdown chart generation"""
        system_score = next((s for s in sample_scores if s.component_id is None), None)
        
        chart_file = reporter._generate_score_chart(sample_scores, "test_123")
        
        assert chart_file.endswith('.png')
        mock_savefig.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_performance_chart_generation(self, mock_close, mock_savefig, reporter, sample_results):
        """Test performance comparison chart generation"""
        chart_file = reporter._generate_performance_chart(sample_results, "test_123")
        
        assert chart_file.endswith('.png')
        mock_savefig.assert_called()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_failure_timeline_generation(self, mock_close, mock_savefig, reporter, sample_results):
        """Test failure timeline chart generation"""
        chart_file = reporter._generate_failure_timeline(sample_results, "test_123")
        
        assert chart_file.endswith('.png')
        mock_savefig.assert_called()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_drift_heatmap_generation(self, mock_close, mock_savefig, reporter, sample_results):
        """Test semantic drift heatmap generation"""
        chart_file = reporter._generate_drift_heatmap(sample_results, "test_123")
        
        assert chart_file.endswith('.png')
        mock_savefig.assert_called()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    @patch('networkx.spring_layout')
    def test_topology_visualization(self, mock_layout, mock_close, mock_savefig, reporter, sample_results):
        """Test topology visualization generation"""
        mock_layout.return_value = {"waf_01": [0, 0], "db_01": [1, 1]}
        
        viz_file = reporter._generate_topology_visualization(None, "test_123")
        
        assert viz_file.endswith('.png')
        mock_savefig.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
