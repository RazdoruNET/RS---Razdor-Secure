"""
EVENT_HORIZON Reporting System

Generates comprehensive reports from assessment results including
resilience scores, failure topology graphs, and detailed analytics.
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import networkx as nx
from datetime import datetime

from .models import AssessmentResults, ResilienceScore

logger = structlog.get_logger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports from assessment results.
    
    Reports include:
    - Executive summary with key metrics
    - Detailed component analysis
    - Failure topology visualization
    - Resilience score breakdowns
    - Recommendations for improvement
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configure matplotlib for non-interactive use
        plt.switch_backend('Agg')
        sns.set_style("whitegrid")
        
        logger.info("Report Generator initialized", output_dir=str(self.output_dir))
    
    def generate_all_reports(self, results: AssessmentResults, scores: List[ResilienceScore]) -> Dict[str, str]:
        """
        Generate all available reports.
        
        Args:
            results: Assessment results from the engine
            scores: Resilience scores from the scorer
            
        Returns:
            Dictionary mapping report names to file paths
        """
        report_files = {}
        
        try:
            # Generate executive summary
            summary_file = self.generate_executive_summary(results, scores)
            report_files["executive_summary"] = summary_file
            
            # Generate detailed component report
            component_file = self.generate_component_report(results, scores)
            report_files["component_analysis"] = component_file
            
            # Generate failure topology report
            topology_file = self.generate_topology_report(results)
            report_files["failure_topology"] = topology_file
            
            # Generate visualizations
            viz_files = self.generate_visualizations(results, scores)
            report_files.update(viz_files)
            
            # Generate JSON data export
            json_file = self.generate_json_export(results, scores)
            report_files["json_export"] = json_file
            
            logger.info("All reports generated successfully", report_count=len(report_files))
            
        except Exception as e:
            logger.error("Report generation failed", error=str(e))
            raise
        
        return report_files
    
    def generate_executive_summary(self, results: AssessmentResults, scores: List[ResilienceScore]) -> str:
        """Generate executive summary report"""
        # Get system-wide score
        system_score = next((s for s in scores if s.component_id is None), None)
        
        if not system_score:
            raise ValueError("No system-wide resilience score found")
        
        summary = {
            "assessment_metadata": {
                "test_id": results.test_id,
                "scenario_id": results.scenario_id,
                "start_time": datetime.fromtimestamp(results.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(results.end_time).isoformat(),
                "duration_seconds": results.end_time - results.start_time,
                "components_tested": len(results.component_metrics)
            },
            "overall_resilience": {
                "score": system_score.score,
                "confidence": system_score.confidence,
                "assessment_level": self._get_assessment_level(system_score.score),
                "score_breakdown": system_score.breakdown
            },
            "key_metrics": {
                "total_requests": results.system_metrics.total_requests,
                "success_rate": (results.system_metrics.total_requests - results.system_metrics.failed_requests) / max(results.system_metrics.total_requests, 1),
                "average_response_time": results.system_metrics.avg_response_time,
                "throughput": results.system_metrics.throughput,
                "failure_events": len(results.system_metrics.failure_events),
                "semantic_drift_events": len(results.semantic_drift_events)
            },
            "critical_findings": self._extract_critical_findings(results, scores),
            "top_recommendations": self._get_top_recommendations(system_score, results)
        }
        
        # Generate HTML report
        html_content = self._generate_html_summary(summary)
        
        # Save report
        filename = f"executive_summary_{results.test_id}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("Executive summary generated", filepath=str(filepath))
        return str(filepath)
    
    def generate_component_report(self, results: AssessmentResults, scores: List[ResilienceScore]) -> str:
        """Generate detailed component analysis report"""
        component_scores = {s.component_id: s for s in scores if s.component_id is not None}
        
        component_analysis = []
        
        for component_id, metrics in results.component_metrics.items():
            score = component_scores.get(component_id)
            
            analysis = {
                "component_id": component_id,
                "resilience_score": score.score if score else 0.0,
                "confidence": score.confidence if score else 0.0,
                "assessment_level": self._get_assessment_level(score.score if score else 0.0),
                "performance_metrics": {
                    "total_requests": metrics.total_requests,
                    "success_rate": (metrics.total_requests - metrics.failed_requests) / max(metrics.total_requests, 1),
                    "average_response_time": metrics.avg_response_time,
                    "max_response_time": metrics.max_response_time,
                    "min_response_time": metrics.min_response_time,
                    "throughput": metrics.throughput,
                    "error_rate": metrics.error_rate
                },
                "issues_detected": [],
                "semantic_drift_events": len(metrics.semantic_drift_events),
                "failure_events": len(metrics.failure_events),
                "recommendations": []
            }
            
            # Add issues detected
            if metrics.error_rate > 0.1:
                analysis["issues_detected"].append(f"High error rate: {metrics.error_rate:.2%}")
            
            if metrics.avg_response_time > 0.5:
                analysis["issues_detected"].append(f"Slow response time: {metrics.avg_response_time:.3f}s")
            
            if len(metrics.semantic_drift_events) > 0:
                avg_drift = sum(e.drift_magnitude for e in metrics.semantic_drift_events) / len(metrics.semantic_drift_events)
                analysis["issues_detected"].append(f"Semantic drift detected: {avg_drift:.3f}")
            
            # Add recommendations
            if score:
                analysis["recommendations"] = self._get_component_recommendations(score, metrics)
            
            component_analysis.append(analysis)
        
        # Sort components by resilience score (lowest first)
        component_analysis.sort(key=lambda x: x["resilience_score"])
        
        # Generate HTML report
        html_content = self._generate_html_component_report(component_analysis)
        
        # Save report
        filename = f"component_analysis_{results.test_id}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("Component report generated", filepath=str(filepath))
        return str(filepath)
    
    def generate_topology_report(self, results: AssessmentResults) -> str:
        """Generate failure topology analysis report"""
        topology = results.failure_topology
        
        # Create NetworkX graph for analysis
        G = nx.DiGraph()
        
        # Add nodes
        for node in topology.get("nodes", []):
            G.add_node(node["id"], 
                      name=node["name"], 
                      type=node["type"],
                      failures=0)
        
        # Add edges
        for edge in topology.get("edges", []):
            G.add_edge(edge["source"], edge["target"])
        
        # Add failure information
        for failure in topology.get("failures", []):
            if failure["component"] in G.nodes:
                G.nodes[failure["component"]]["failures"] += 1
                G.nodes[failure["component"]]["severity"] = failure["severity"]
                G.nodes[failure["component"]]["failure_type"] = failure["type"]
        
        # Calculate topology metrics
        topology_analysis = {
            "graph_metrics": {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "is_connected": nx.is_weakly_connected(G),
                "density": nx.density(G),
                "average_clustering": nx.average_clustering(G.to_undirected())
            },
            "failure_analysis": {
                "failed_nodes": [n for n, d in G.nodes(data=True) if d.get("failures", 0) > 0],
                "failure_propagation_paths": self._find_failure_paths(G),
                "critical_nodes": self._find_critical_nodes(G),
                "isolated_components": self._find_isolated_components(G)
            },
            "resilience_implications": self._analyze_resilience_implications(G)
        }
        
        # Generate topology visualization
        self._generate_topology_visualization(G, results.test_id)
        
        # Generate HTML report
        html_content = self._generate_html_topology_report(topology_analysis, topology)
        
        # Save report
        filename = f"topology_analysis_{results.test_id}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("Topology report generated", filepath=str(filepath))
        return str(filepath)
    
    def generate_visualizations(self, results: AssessmentResults, scores: List[ResilienceScore]) -> Dict[str, str]:
        """Generate visualization files"""
        viz_files = {}
        
        try:
            # Resilience score breakdown chart
            score_chart = self._generate_score_chart(scores, results.test_id)
            viz_files["score_breakdown"] = score_chart
            
            # Component performance comparison
            performance_chart = self._generate_performance_chart(results, results.test_id)
            viz_files["performance_comparison"] = performance_chart
            
            # Failure timeline
            timeline_chart = self._generate_failure_timeline(results, results.test_id)
            viz_files["failure_timeline"] = timeline_chart
            
            # Semantic drift heatmap
            drift_heatmap = self._generate_drift_heatmap(results, results.test_id)
            viz_files["drift_heatmap"] = drift_heatmap
            
        except Exception as e:
            logger.error("Visualization generation failed", error=str(e))
        
        return viz_files
    
    def generate_json_export(self, results: AssessmentResults, scores: List[ResilienceScore]) -> str:
        """Generate complete JSON export of results"""
        export_data = {
            "metadata": {
                "test_id": results.test_id,
                "scenario_id": results.scenario_id,
                "export_timestamp": time.time(),
                "event_horizon_version": "1.0.0"
            },
            "assessment_results": {
                "test_id": results.test_id,
                "scenario_id": results.scenario_id,
                "start_time": results.start_time,
                "end_time": results.end_time,
                "duration": results.end_time - results.start_time,
                "component_metrics": {
                    comp_id: {
                        "component_id": metrics.component_id,
                        "total_requests": metrics.total_requests,
                        "successful_requests": metrics.successful_requests,
                        "failed_requests": metrics.failed_requests,
                        "avg_response_time": metrics.avg_response_time,
                        "max_response_time": metrics.max_response_time,
                        "min_response_time": metrics.min_response_time,
                        "error_rate": metrics.error_rate,
                        "throughput": metrics.throughput,
                        "semantic_drift_events_count": len(metrics.semantic_drift_events),
                        "failure_events_count": len(metrics.failure_events)
                    }
                    for comp_id, metrics in results.component_metrics.items()
                },
                "system_metrics": {
                    "component_id": results.system_metrics.component_id,
                    "total_requests": results.system_metrics.total_requests,
                    "successful_requests": results.system_metrics.successful_requests,
                    "failed_requests": results.system_metrics.failed_requests,
                    "avg_response_time": results.system_metrics.avg_response_time,
                    "max_response_time": results.system_metrics.max_response_time,
                    "min_response_time": results.system_metrics.min_response_time,
                    "error_rate": results.system_metrics.error_rate,
                    "throughput": results.system_metrics.throughput
                },
                "resilience_scores": [
                    {
                        "component_id": score.component_id,
                        "score": score.score,
                        "confidence": score.confidence,
                        "breakdown": score.breakdown,
                        "timestamp": score.timestamp
                    }
                    for score in scores
                ],
                "failure_topology": results.failure_topology,
                "auth_pipeline_breakpoints": results.auth_pipeline_breakpoints,
                "normalization_loss_report": results.normalization_loss_report,
                "session_integrity_heatmap": results.session_integrity_heatmap
            }
        }
        
        # Save JSON export
        filename = f"assessment_export_{results.test_id}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info("JSON export generated", filepath=str(filepath))
        return str(filepath)
    
    def _get_assessment_level(self, score: float) -> str:
        """Get assessment level based on score"""
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
    
    def _extract_critical_findings(self, results: AssessmentResults, scores: List[ResilienceScore]) -> List[str]:
        """Extract critical findings from results"""
        findings = []
        
        # Check for high error rates
        if results.system_metrics.error_rate > 0.1:
            findings.append(f"High system error rate: {results.system_metrics.error_rate:.2%}")
        
        # Check for slow response times
        if results.system_metrics.avg_response_time > 0.5:
            findings.append(f"Slow average response time: {results.system_metrics.avg_response_time:.3f}s")
        
        # Check for semantic drift
        if len(results.semantic_drift_events) > 0:
            avg_drift = sum(e.drift_magnitude for e in results.semantic_drift_events) / len(results.semantic_drift_events)
            findings.append(f"Semantic drift detected: {avg_drift:.3f} average magnitude")
        
        # Check for critical components
        critical_components = [
            comp_id for comp_id, score in [(s.component_id, s) for s in scores if s.component_id]
            if score.score < 0.6
        ]
        
        if critical_components:
            findings.append(f"Critical components with low resilience: {', '.join(critical_components)}")
        
        return findings
    
    def _get_top_recommendations(self, system_score: ResilienceScore, results: AssessmentResults) -> List[str]:
        """Get top recommendations based on system score"""
        recommendations = []
        
        breakdown = system_score.breakdown
        
        # Prioritize based on lowest scoring dimensions
        sorted_dimensions = sorted(breakdown.items(), key=lambda x: x[1])
        
        for dimension, score in sorted_dimensions[:3]:  # Top 3 issues
            if dimension == "availability" and score < 0.8:
                recommendations.append("Implement better error handling and failover mechanisms")
            elif dimension == "performance" and score < 0.8:
                recommendations.append("Optimize database queries and implement caching")
            elif dimension == "consistency" and score < 0.8:
                recommendations.append("Review data normalization and consistency checks")
            elif dimension == "security" and score < 0.8:
                recommendations.append("Strengthen input validation and rate limiting")
            elif dimension == "recovery" and score < 0.8:
                recommendations.append("Implement automated failure detection and recovery")
        
        return recommendations
    
    def _get_component_recommendations(self, score: ResilienceScore, metrics) -> List[str]:
        """Get recommendations for a specific component"""
        recommendations = []
        
        if score.score < 0.7:
            recommendations.append("Component requires immediate attention")
        
        if metrics.error_rate > 0.05:
            recommendations.append("Reduce error rate through better error handling")
        
        if metrics.avg_response_time > 0.2:
            recommendations.append("Optimize component performance")
        
        if len(metrics.semantic_drift_events) > 0:
            recommendations.append("Address semantic drift issues")
        
        return recommendations
    
    def _find_failure_paths(self, G) -> List[List[str]]:
        """Find failure propagation paths in the graph"""
        failed_nodes = [n for n, d in G.nodes(data=True) if d.get("failures", 0) > 0]
        paths = []
        
        for failed_node in failed_nodes:
            # Find paths from failed nodes to other nodes
            for target_node in G.nodes():
                if target_node != failed_node and nx.has_path(G, failed_node, target_node):
                    try:
                        path = nx.shortest_path(G, failed_node, target_node)
                        if len(path) > 1:
                            paths.append(path)
                    except nx.NetworkXNoPath:
                        continue
        
        return paths[:10]  # Limit to top 10 paths
    
    def _find_critical_nodes(self, G) -> List[str]:
        """Find critical nodes based on centrality measures"""
        centrality = nx.betweenness_centrality(G)
        return sorted(centrality.keys(), key=centrality.get, reverse=True)[:5]
    
    def _find_isolated_components(self, G) -> List[str]:
        """Find isolated components in the graph"""
        components = list(nx.weakly_connected_components(G))
        return [list(comp) for comp in components if len(comp) == 1]
    
    def _analyze_resilience_implications(self, G) -> Dict[str, Any]:
        """Analyze resilience implications of the topology"""
        return {
            "single_points_of_failure": len([n for n, d in G.degree() if d == 1]),
            "redundancy_level": "high" if nx.is_weakly_connected(G) and G.number_of_edges() > G.number_of_nodes() else "low",
            "cascade_risk": "high" if nx.is_weakly_connected(G) and G.number_of_edges() > G.number_of_nodes() * 2 else "low"
        }
    
    def _generate_html_summary(self, summary: Dict[str, Any]) -> str:
        """Generate HTML executive summary"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EVENT_HORIZON Executive Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .metric {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background-color: #ecf0f1; }}
                .critical {{ border-left-color: #e74c3c; }}
                .good {{ border-left-color: #27ae60; }}
                .score {{ font-size: 48px; font-weight: bold; color: #2c3e50; }}
                .assessment {{ font-size: 24px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>EVENT_HORIZON Resilience Assessment</h1>
                <p>Test ID: {summary['assessment_metadata']['test_id']}</p>
                <p>Duration: {summary['assessment_metadata']['duration_seconds']:.2f} seconds</p>
            </div>
            
            <div class="metric">
                <div class="score">{summary['overall_resilience']['score']:.3f}</div>
                <div class="assessment">Assessment: {summary['overall_resilience']['assessment_level']}</div>
                <p>Confidence: {summary['overall_resilience']['confidence']:.3f}</p>
            </div>
            
            <h2>Key Metrics</h2>
            <div class="metric">
                <p>Total Requests: {summary['key_metrics']['total_requests']:,}</p>
                <p>Success Rate: {summary['key_metrics']['success_rate']:.2%}</p>
                <p>Average Response Time: {summary['key_metrics']['average_response_time']:.3f}s</p>
                <p>Throughput: {summary['key_metrics']['throughput']:.2f} req/s</p>
            </div>
            
            <h2>Critical Findings</h2>
        """
        
        for finding in summary['critical_findings']:
            html += f'<div class="metric critical">{finding}</div>'
        
        html += """
            <h2>Top Recommendations</h2>
        """
        
        for rec in summary['top_recommendations']:
            html += f'<div class="metric good">{rec}</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_html_component_report(self, component_analysis: List[Dict[str, Any]]) -> str:
        """Generate HTML component analysis report"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>EVENT_HORIZON Component Analysis</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
                .component { margin: 20px 0; padding: 15px; border: 1px solid #bdc3c7; border-radius: 5px; }
                .critical { border-color: #e74c3c; background-color: #fadbd8; }
                .warning { border-color: #f39c12; background-color: #fef5e7; }
                .good { border-color: #27ae60; background-color: #d5f4e6; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Component Resilience Analysis</h1>
            </div>
        """
        
        for component in component_analysis:
            css_class = "critical" if component["resilience_score"] < 0.6 else "warning" if component["resilience_score"] < 0.8 else "good"
            
            html += f"""
            <div class="component {css_class}">
                <h3>{component['component_id']}</h3>
                <p><strong>Resilience Score:</strong> {component['resilience_score']:.3f} ({component['assessment_level']})</p>
                <p><strong>Confidence:</strong> {component['confidence']:.3f}</p>
                
                <h4>Performance Metrics</h4>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Requests</td><td>{component['performance_metrics']['total_requests']:,}</td></tr>
                    <tr><td>Success Rate</td><td>{component['performance_metrics']['success_rate']:.2%}</td></tr>
                    <tr><td>Average Response Time</td><td>{component['performance_metrics']['average_response_time']:.3f}s</td></tr>
                    <tr><td>Throughput</td><td>{component['performance_metrics']['throughput']:.2f} req/s</td></tr>
                    <tr><td>Error Rate</td><td>{component['performance_metrics']['error_rate']:.2%}</td></tr>
                </table>
            """
            
            if component['issues_detected']:
                html += "<h4>Issues Detected</h4><ul>"
                for issue in component['issues_detected']:
                    html += f"<li>{issue}</li>"
                html += "</ul>"
            
            if component['recommendations']:
                html += "<h4>Recommendations</h4><ul>"
                for rec in component['recommendations']:
                    html += f"<li>{rec}</li>"
                html += "</ul>"
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_html_topology_report(self, topology_analysis: Dict[str, Any], topology: Dict[str, Any]) -> str:
        """Generate HTML topology analysis report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EVENT_HORIZON Topology Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #bdc3c7; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Failure Topology Analysis</h1>
            </div>
            
            <div class="section">
                <h2>Graph Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Nodes</td><td>{topology_analysis['graph_metrics']['total_nodes']}</td></tr>
                    <tr><td>Total Edges</td><td>{topology_analysis['graph_metrics']['total_edges']}</td></tr>
                    <tr><td>Is Connected</td><td>{topology_analysis['graph_metrics']['is_connected']}</td></tr>
                    <tr><td>Density</td><td>{topology_analysis['graph_metrics']['density']:.3f}</td></tr>
                    <tr><td>Average Clustering</td><td>{topology_analysis['graph_metrics']['average_clustering']:.3f}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Failure Analysis</h2>
                <p><strong>Failed Nodes:</strong> {', '.join(topology_analysis['failure_analysis']['failed_nodes'])}</p>
                <p><strong>Critical Nodes:</strong> {', '.join(topology_analysis['failure_analysis']['critical_nodes'])}</p>
                <p><strong>Isolated Components:</strong> {len(topology_analysis['failure_analysis']['isolated_components'])}</p>
            </div>
            
            <div class="section">
                <h2>Resilience Implications</h2>
                <p><strong>Single Points of Failure:</strong> {topology_analysis['resilience_implications']['single_points_of_failure']}</p>
                <p><strong>Redundancy Level:</strong> {topology_analysis['resilience_implications']['redundancy_level']}</p>
                <p><strong>Cascade Risk:</strong> {topology_analysis['resilience_implications']['cascade_risk']}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_score_chart(self, scores: List[ResilienceScore], test_id: str) -> str:
        """Generate resilience score breakdown chart"""
        system_score = next((s for s in scores if s.component_id is None), None)
        
        if not system_score:
            return ""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        dimensions = list(system_score.breakdown.keys())
        values = list(system_score.breakdown.values())
        
        bars = ax.bar(dimensions, values, color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'])
        
        ax.set_title('Resilience Score Breakdown')
        ax.set_ylabel('Score')
        ax.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{value:.3f}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        filename = f"score_breakdown_{test_id}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def _generate_performance_chart(self, results: AssessmentResults, test_id: str) -> str:
        """Generate component performance comparison chart"""
        if not results.component_metrics:
            return ""
        
        components = list(results.component_metrics.keys())
        response_times = [results.component_metrics[comp].avg_response_time for comp in components]
        error_rates = [results.component_metrics[comp].error_rate for comp in components]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Response time chart
        ax1.bar(components, response_times, color='#3498db')
        ax1.set_title('Average Response Time by Component')
        ax1.set_ylabel('Response Time (s)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Error rate chart
        ax2.bar(components, error_rates, color='#e74c3c')
        ax2.set_title('Error Rate by Component')
        ax2.set_ylabel('Error Rate')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        filename = f"performance_comparison_{test_id}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def _generate_failure_timeline(self, results: AssessmentResults, test_id: str) -> str:
        """Generate failure timeline chart"""
        if not results.system_metrics.failure_events:
            return ""
        
        failure_times = [event.timestamp for event in results.system_metrics.failure_events]
        failure_severities = [event.severity for event in results.system_metrics.failure_events]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        scatter = ax.scatter(failure_times, failure_severities, 
                           c=failure_severities, cmap='Reds', s=50, alpha=0.7)
        
        ax.set_title('Failure Timeline')
        ax.set_xlabel('Time')
        ax.set_ylabel('Severity')
        ax.set_ylim(0, 1)
        
        plt.colorbar(scatter, label='Severity')
        plt.tight_layout()
        
        filename = f"failure_timeline_{test_id}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def _generate_drift_heatmap(self, results: AssessmentResults, test_id: str) -> str:
        """Generate semantic drift heatmap"""
        if not results.semantic_drift_events:
            return ""
        
        # Create drift matrix
        components = list(set(event.target_component for event in results.semantic_drift_events))
        sources = list(set(event.source_component for event in results.semantic_drift_events))
        
        drift_matrix = [[0.0] * len(components) for _ in range(len(sources))]
        
        for event in results.semantic_drift_events:
            if event.target_component in components and event.source_component in sources:
                i = sources.index(event.source_component)
                j = components.index(event.target_component)
                drift_matrix[i][j] = max(drift_matrix[i][j], event.drift_magnitude)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(drift_matrix, cmap='Reds', aspect='auto', vmin=0, vmax=1)
        
        ax.set_xticks(range(len(components)))
        ax.set_yticks(range(len(sources)))
        ax.set_xticklabels(components, rotation=45)
        ax.set_yticklabels(sources)
        
        ax.set_xlabel('Target Component')
        ax.set_ylabel('Source Component')
        ax.set_title('Semantic Drift Heatmap')
        
        plt.colorbar(im, label='Drift Magnitude')
        plt.tight_layout()
        
        filename = f"drift_heatmap_{test_id}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def _generate_topology_visualization(self, G, test_id: str) -> str:
        """Generate network topology visualization"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Draw nodes
        failed_nodes = [n for n, d in G.nodes(data=True) if d.get("failures", 0) > 0]
        normal_nodes = [n for n in G.nodes() if n not in failed_nodes]
        
        nx.draw_networkx_nodes(G, pos, nodelist=normal_nodes, 
                              node_color='#3498db', node_size=500, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=failed_nodes, 
                              node_color='#e74c3c', node_size=700, ax=ax)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='#7f8c8d', width=1, ax=ax)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)
        
        ax.set_title('Failure Topology Graph')
        ax.axis('off')
        
        filename = f"topology_graph_{test_id}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
