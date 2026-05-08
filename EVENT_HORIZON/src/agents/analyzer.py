"""
Test Analyzer

Autonomous test analysis agent that processes execution results,
identifies patterns, and generates comprehensive reports.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

from .executor import ExecutionResult
from .telemetry import TelemetryCollector
from ..observability import StructuredLogger


class AnalysisType(Enum):
    """Types of analysis to perform."""
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RESILIENCE_ANALYSIS = "resilience_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    TREND_ANALYSIS = "trend_analysis"
    CORRELATION_ANALYSIS = "correlation_analysis"


class SeverityLevel(Enum):
    """Severity levels for findings."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalysisFinding:
    """Individual analysis finding."""
    title: str
    description: str
    severity: SeverityLevel
    analysis_type: AnalysisType
    evidence: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    timestamp: float
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class AnalysisReport:
    """Comprehensive analysis report."""
    report_id: str
    generated_at: float
    execution_results: List[ExecutionResult]
    findings: List[AnalysisFinding]
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    recommendations: List[str]
    overall_score: float


class TestAnalyzer:
    """
    Autonomous test analysis agent for processing execution results.
    """
    
    def __init__(self, telemetry_collector: Optional[TelemetryCollector] = None):
        """
        Initialize test analyzer.
        
        Args:
            telemetry_collector: Optional telemetry collector for correlation
        """
        self.telemetry_collector = telemetry_collector
        self.logger = StructuredLogger("test_analyzer")
        
        # Analysis state
        self.analysis_results: List[AnalysisReport] = []
        self.analysis_history: List[Dict[str, Any]] = []
        
        # Analysis thresholds
        self.thresholds = {
            "error_rate_critical": 0.2,
            "error_rate_high": 0.1,
            "error_rate_medium": 0.05,
            "response_time_critical": 10.0,
            "response_time_high": 5.0,
            "response_time_medium": 2.0,
            "throughput_critical": 100,
            "throughput_high": 500,
            "throughput_medium": 1000,
            "availability_critical": 0.95,
            "availability_high": 0.98,
            "availability_medium": 0.99
        }
    
    async def analyze_execution_results(self, execution_results: List[ExecutionResult],
                                       analysis_types: Optional[List[AnalysisType]] = None) -> AnalysisReport:
        """
        Analyze execution results and generate comprehensive report.
        
        Args:
            execution_results: List of execution results to analyze
            analysis_types: Types of analysis to perform (None for all)
            
        Returns:
            Analysis report
        """
        if not execution_results:
            raise ValueError("No execution results to analyze")
        
        report_id = f"analysis_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"Starting analysis for {len(execution_results)} execution results",
                        component="analyzer", operation="analysis_start",
                        report_id=report_id)
        
        # Determine analysis types
        if analysis_types is None:
            analysis_types = list(AnalysisType)
        
        # Perform analyses
        findings = []
        
        for analysis_type in analysis_types:
            try:
                type_findings = await self._perform_analysis(analysis_type, execution_results)
                findings.extend(type_findings)
                
            except Exception as e:
                self.logger.error(f"Analysis failed for {analysis_type.value}: {str(e)}",
                                 component="analyzer", operation="analysis_failed",
                                 analysis_type=analysis_type.value, error=str(e))
        
        # Generate summary and metrics
        summary = self._generate_summary(execution_results, findings)
        metrics = self._calculate_metrics(execution_results)
        recommendations = self._generate_recommendations(findings)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(findings, metrics)
        
        # Create report
        report = AnalysisReport(
            report_id=report_id,
            generated_at=time.time(),
            execution_results=execution_results,
            findings=findings,
            summary=summary,
            metrics=metrics,
            recommendations=recommendations,
            overall_score=overall_score
        )
        
        self.analysis_results.append(report)
        
        self.logger.info(f"Analysis completed: {report_id}",
                        component="analyzer", operation="analysis_complete",
                        report_id=report_id, findings_count=len(findings),
                        overall_score=overall_score)
        
        return report
    
    async def _perform_analysis(self, analysis_type: AnalysisType, 
                              execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Perform specific type of analysis."""
        if analysis_type == AnalysisType.PERFORMANCE_ANALYSIS:
            return await self._analyze_performance(execution_results)
        elif analysis_type == AnalysisType.RESILIENCE_ANALYSIS:
            return await self._analyze_resilience(execution_results)
        elif analysis_type == AnalysisType.SECURITY_ANALYSIS:
            return await self._analyze_security(execution_results)
        elif analysis_type == AnalysisType.ANOMALY_DETECTION:
            return await self._detect_anomalies(execution_results)
        elif analysis_type == AnalysisType.TREND_ANALYSIS:
            return await self._analyze_trends(execution_results)
        elif analysis_type == AnalysisType.CORRELATION_ANALYSIS:
            return await self._analyze_correlations(execution_results)
        else:
            return []
    
    async def _analyze_performance(self, execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Analyze performance aspects of execution results."""
        findings = []
        
        for result in execution_results:
            # Response time analysis
            if result.avg_response_time > self.thresholds["response_time_critical"]:
                findings.append(AnalysisFinding(
                    title="Critical Response Time Degradation",
                    description=f"Average response time of {result.avg_response_time:.3f}s exceeds critical threshold",
                    severity=SeverityLevel.CRITICAL,
                    analysis_type=AnalysisType.PERFORMANCE_ANALYSIS,
                    evidence={
                        "avg_response_time": result.avg_response_time,
                        "p95_response_time": result.p95_response_time,
                        "threshold": self.thresholds["response_time_critical"],
                        "scenario": result.scenario_name
                    },
                    recommendations=[
                        "Optimize application code for better performance",
                        "Increase server resources or scaling",
                        "Implement caching mechanisms",
                        "Review database queries and indexing"
                    ],
                    confidence=0.9
                ))
            
            elif result.avg_response_time > self.thresholds["response_time_high"]:
                findings.append(AnalysisFinding(
                    title="High Response Time Detected",
                    description=f"Average response time of {result.avg_response_time:.3f}s exceeds high threshold",
                    severity=SeverityLevel.HIGH,
                    analysis_type=AnalysisType.PERFORMANCE_ANALYSIS,
                    evidence={
                        "avg_response_time": result.avg_response_time,
                        "p95_response_time": result.p95_response_time,
                        "threshold": self.thresholds["response_time_high"],
                        "scenario": result.scenario_name
                    },
                    recommendations=[
                        "Monitor performance trends",
                        "Consider performance optimization",
                        "Review resource utilization"
                    ],
                    confidence=0.8
                ))
            
            # Throughput analysis
            if result.throughput < self.thresholds["throughput_critical"]:
                findings.append(AnalysisFinding(
                    title="Critical Throughput Degradation",
                    description=f"Throughput of {result.throughput:.2f} req/s below critical threshold",
                    severity=SeverityLevel.CRITICAL,
                    analysis_type=AnalysisType.PERFORMANCE_ANALYSIS,
                    evidence={
                        "throughput": result.throughput,
                        "total_requests": result.total_requests,
                        "duration": result.duration_seconds,
                        "threshold": self.thresholds["throughput_critical"],
                        "scenario": result.scenario_name
                    },
                    recommendations=[
                        "Increase system capacity",
                        "Optimize request processing",
                        "Check for bottlenecks in the pipeline",
                        "Consider load balancing improvements"
                    ],
                    confidence=0.85
                ))
            
            # Error rate analysis
            if result.error_rate > self.thresholds["error_rate_critical"]:
                findings.append(AnalysisFinding(
                    title="Critical Error Rate",
                    description=f"Error rate of {result.error_rate:.2%} exceeds critical threshold",
                    severity=SeverityLevel.CRITICAL,
                    analysis_type=AnalysisType.PERFORMANCE_ANALYSIS,
                    evidence={
                        "error_rate": result.error_rate,
                        "failed_requests": result.failed_requests,
                        "total_requests": result.total_requests,
                        "threshold": self.thresholds["error_rate_critical"],
                        "scenario": result.scenario_name
                    },
                    recommendations=[
                        "Investigate root cause of errors",
                        "Implement better error handling",
                        "Review system logs for patterns",
                        "Consider circuit breaker patterns"
                    ],
                    confidence=0.95
                ))
        
        return findings
    
    async def _analyze_resilience(self, execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Analyze resilience aspects of execution results."""
        findings = []
        
        # Analyze system behavior under stress
        stress_scenarios = [r for r in execution_results if "stress" in r.scenario_name.lower() or 
                           "resilience" in r.scenario_name.lower()]
        
        for result in stress_scenarios:
            availability = 1.0 - result.error_rate
            
            if availability < self.thresholds["availability_critical"]:
                findings.append(AnalysisFinding(
                    title="Critical Availability Issue",
                    description=f"System availability of {availability:.2%} below critical threshold under stress",
                    severity=SeverityLevel.CRITICAL,
                    analysis_type=AnalysisType.RESILIENCE_ANALYSIS,
                    evidence={
                        "availability": availability,
                        "error_rate": result.error_rate,
                        "scenario": result.scenario_name,
                        "stress_level": "high"
                    },
                    recommendations=[
                        "Implement circuit breaker patterns",
                        "Add redundancy and failover mechanisms",
                        "Improve error recovery procedures",
                        "Consider auto-scaling under load"
                    ],
                    confidence=0.9
                ))
            
            # Check for graceful degradation
            if result.error_rate > 0.1 and result.avg_response_time < 5.0:
                findings.append(AnalysisFinding(
                    title="Graceful Degradation Observed",
                    description="System shows graceful degradation under stress with controlled response times",
                    severity=SeverityLevel.LOW,
                    analysis_type=AnalysisType.RESILIENCE_ANALYSIS,
                    evidence={
                        "error_rate": result.error_rate,
                        "avg_response_time": result.avg_response_time,
                        "scenario": result.scenario_name
                    },
                    recommendations=[
                        "Continue monitoring degradation patterns",
                        "Document degradation behavior",
                        "Consider improving partial functionality"
                    ],
                    confidence=0.7
                ))
        
        # Analyze recovery patterns
        recovery_scenarios = [r for r in execution_results if "recovery" in r.scenario_name.lower() or 
                            "circuit" in r.scenario_name.lower()]
        
        for result in recovery_scenarios:
            if result.error_rate < 0.05:
                findings.append(AnalysisFinding(
                    title="Good Recovery Performance",
                    description="System demonstrates good recovery capabilities",
                    severity=SeverityLevel.LOW,
                    analysis_type=AnalysisType.RESILIENCE_ANALYSIS,
                    evidence={
                        "error_rate": result.error_rate,
                        "scenario": result.scenario_name,
                        "recovery_time": result.duration_seconds
                    },
                    recommendations=[
                        "Maintain current recovery mechanisms",
                        "Document recovery procedures",
                        "Test recovery under different conditions"
                    ],
                    confidence=0.8
                ))
        
        return findings
    
    async def _analyze_security(self, execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Analyze security aspects of execution results."""
        findings = []
        
        # Analyze authentication scenarios
        auth_scenarios = [r for r in execution_results if "auth" in r.scenario_name.lower()]
        
        for result in auth_scenarios:
            # Check for authentication bypass indicators
            if result.error_rate < 0.01 and "stress" in result.scenario_name.lower():
                findings.append(AnalysisFinding(
                    title="Potential Authentication Bypass Risk",
                    description="Unusually low error rate in authentication stress test may indicate bypass vulnerabilities",
                    severity=SeverityLevel.HIGH,
                    analysis_type=AnalysisType.SECURITY_ANALYSIS,
                    evidence={
                        "error_rate": result.error_rate,
                        "scenario": result.scenario_name,
                        "total_requests": result.total_requests
                    },
                    recommendations=[
                        "Review authentication logic for bypass vulnerabilities",
                        "Implement proper authentication validation",
                        "Test with various attack vectors",
                        "Audit authentication mechanisms"
                    ],
                    confidence=0.7
                ))
            
            # Check for rate limiting effectiveness
            if "rate" in result.scenario_name.lower() and result.error_rate < 0.3:
                findings.append(AnalysisFinding(
                    title="Ineffective Rate Limiting",
                    description="Rate limiting may be ineffective based on test results",
                    severity=SeverityLevel.MEDIUM,
                    analysis_type=AnalysisType.SECURITY_ANALYSIS,
                    evidence={
                        "error_rate": result.error_rate,
                        "scenario": result.scenario_name,
                        "throughput": result.throughput
                    },
                    recommendations=[
                        "Review rate limiting configuration",
                        "Test rate limiting with different patterns",
                        "Implement more robust rate limiting",
                        "Monitor for rate limit bypass attempts"
                    ],
                    confidence=0.6
                ))
        
        # Analyze input normalization scenarios
        input_scenarios = [r for r in execution_results if "normalization" in r.scenario_name.lower() or 
                          "input" in r.scenario_name.lower()]
        
        for result in input_scenarios:
            # Check for parser inconsistencies
            if result.error_rate > 0.15:
                findings.append(AnalysisFinding(
                    title="Input Parser Inconsistencies",
                    description="High error rate in input normalization tests may indicate parser inconsistencies",
                    severity=SeverityLevel.MEDIUM,
                    analysis_type=AnalysisType.SECURITY_ANALYSIS,
                    evidence={
                        "error_rate": result.error_rate,
                        "scenario": result.scenario_name,
                        "errors": result.errors[:5]  # First 5 errors
                    },
                    recommendations=[
                        "Review input parsing logic",
                        "Implement consistent normalization",
                        "Test with various input formats",
                        "Add input validation layers"
                    ],
                    confidence=0.8
                ))
        
        return findings
    
    async def _detect_anomalies(self, execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Detect anomalies in execution results."""
        findings = []
        
        if len(execution_results) < 3:
            return findings  # Need minimum data for anomaly detection
        
        # Analyze response time anomalies
        response_times = [r.avg_response_time for r in execution_results]
        mean_rt = statistics.mean(response_times)
        stdev_rt = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        for result in execution_results:
            if stdev_rt > 0:
                z_score = abs(result.avg_response_time - mean_rt) / stdev_rt
                if z_score > 2.5:  # More than 2.5 standard deviations
                    findings.append(AnalysisFinding(
                        title="Response Time Anomaly",
                        description=f"Response time anomaly detected in {result.scenario_name}",
                        severity=SeverityLevel.MEDIUM,
                        analysis_type=AnalysisType.ANOMALY_DETECTION,
                        evidence={
                            "response_time": result.avg_response_time,
                            "mean_response_time": mean_rt,
                            "z_score": z_score,
                            "scenario": result.scenario_name
                        },
                        recommendations=[
                            "Investigate cause of response time anomaly",
                            "Check for resource contention",
                            "Review system logs for the time period",
                            "Monitor for recurring anomalies"
                        ],
                        confidence=0.7
                    ))
        
        # Analyze error rate anomalies
        error_rates = [r.error_rate for r in execution_results]
        mean_er = statistics.mean(error_rates)
        stdev_er = statistics.stdev(error_rates) if len(error_rates) > 1 else 0
        
        for result in execution_results:
            if stdev_er > 0:
                z_score = abs(result.error_rate - mean_er) / stdev_er
                if z_score > 2.0:
                    findings.append(AnalysisFinding(
                        title="Error Rate Anomaly",
                        description=f"Error rate anomaly detected in {result.scenario_name}",
                        severity=SeverityLevel.HIGH,
                        analysis_type=AnalysisType.ANOMALY_DETECTION,
                        evidence={
                            "error_rate": result.error_rate,
                            "mean_error_rate": mean_er,
                            "z_score": z_score,
                            "scenario": result.scenario_name
                        },
                        recommendations=[
                            "Investigate cause of error rate anomaly",
                            "Review error logs for patterns",
                            "Check for system issues during test",
                            "Analyze correlated system events"
                        ],
                        confidence=0.8
                    ))
        
        return findings
    
    async def _analyze_trends(self, execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Analyze trends in execution results."""
        findings = []
        
        if len(execution_results) < 2:
            return findings  # Need minimum data for trend analysis
        
        # Sort by start time
        sorted_results = sorted(execution_results, key=lambda x: x.start_time)
        
        # Analyze performance trends
        response_times = [r.avg_response_time for r in sorted_results]
        error_rates = [r.error_rate for r in sorted_results]
        
        # Calculate trend slopes (simplified linear regression)
        if len(response_times) >= 3:
            rt_slope = self._calculate_trend_slope(response_times)
            er_slope = self._calculate_trend_slope(error_rates)
            
            # Response time trend
            if rt_slope > 0.1:  # Increasing response times
                findings.append(AnalysisFinding(
                    title="Degrading Performance Trend",
                    description="Response times show increasing trend over test period",
                    severity=SeverityLevel.MEDIUM,
                    analysis_type=AnalysisType.TREND_ANALYSIS,
                    evidence={
                        "trend_slope": rt_slope,
                        "response_times": response_times,
                        "trend_direction": "increasing"
                    },
                    recommendations=[
                        "Investigate performance degradation causes",
                        "Monitor resource utilization trends",
                        "Consider performance optimization",
                        "Plan for capacity scaling"
                    ],
                    confidence=0.6
                ))
            
            # Error rate trend
            if er_slope > 0.05:  # Increasing error rates
                findings.append(AnalysisFinding(
                    title="Increasing Error Rate Trend",
                    description="Error rates show increasing trend over test period",
                    severity=SeverityLevel.HIGH,
                    analysis_type=AnalysisType.TREND_ANALYSIS,
                    evidence={
                        "trend_slope": er_slope,
                        "error_rates": error_rates,
                        "trend_direction": "increasing"
                    },
                    recommendations=[
                        "Investigate error rate increase causes",
                        "Review system stability over time",
                        "Check for resource exhaustion",
                        "Implement proactive monitoring"
                    ],
                    confidence=0.7
                ))
        
        return findings
    
    async def _analyze_correlations(self, execution_results: List[ExecutionResult]) -> List[AnalysisFinding]:
        """Analyze correlations between metrics."""
        findings = []
        
        if len(execution_results) < 3:
            return findings  # Need minimum data for correlation analysis
        
        # Extract metrics
        response_times = [r.avg_response_time for r in execution_results]
        error_rates = [r.error_rate for r in execution_results]
        throughputs = [r.throughput for r in execution_results]
        
        # Calculate correlations
        rt_er_correlation = self._calculate_correlation(response_times, error_rates)
        rt_tp_correlation = self._calculate_correlation(response_times, throughputs)
        er_tp_correlation = self._calculate_correlation(error_rates, throughputs)
        
        # Response time vs error rate correlation
        if abs(rt_er_correlation) > 0.7:
            correlation_type = "positive" if rt_er_correlation > 0 else "negative"
            findings.append(AnalysisFinding(
                title=f"Strong Response Time-Error Rate Correlation",
                description=f"Strong {correlation_type} correlation ({rt_er_correlation:.3f}) between response times and error rates",
                severity=SeverityLevel.MEDIUM,
                analysis_type=AnalysisType.CORRELATION_ANALYSIS,
                evidence={
                    "correlation_coefficient": rt_er_correlation,
                    "correlation_type": correlation_type,
                    "response_times": response_times,
                    "error_rates": error_rates
                },
                recommendations=[
                    "Investigate relationship between response time and errors",
                    "Consider performance tuning to reduce errors",
                    "Monitor for cascading failure patterns",
                    "Implement proactive error prevention"
                ],
                confidence=0.8
            ))
        
        # Response time vs throughput correlation
        if abs(rt_tp_correlation) > 0.7:
            correlation_type = "positive" if rt_tp_correlation > 0 else "negative"
            findings.append(AnalysisFinding(
                title=f"Strong Response Time-Throughput Correlation",
                description=f"Strong {correlation_type} correlation ({rt_tp_correlation:.3f}) between response times and throughput",
                severity=SeverityLevel.LOW,
                analysis_type=AnalysisType.CORRELATION_ANALYSIS,
                evidence={
                    "correlation_coefficient": rt_tp_correlation,
                    "correlation_type": correlation_type,
                    "response_times": response_times,
                    "throughputs": throughputs
                },
                recommendations=[
                    "Optimize system for better throughput-performance balance",
                    "Consider load balancing improvements",
                    "Monitor performance under different loads",
                    "Plan capacity scaling based on patterns"
                ],
                confidence=0.6
            ))
        
        return findings
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using simple linear regression."""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        x_variance = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_variance = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        denominator = (x_variance * y_variance) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _generate_summary(self, execution_results: List[ExecutionResult], 
                         findings: List[AnalysisFinding]) -> Dict[str, Any]:
        """Generate analysis summary."""
        total_requests = sum(r.total_requests for r in execution_results)
        total_errors = sum(r.failed_requests for r in execution_results)
        overall_error_rate = total_errors / total_requests if total_requests > 0 else 0.0
        avg_response_time = sum(r.avg_response_time for r in execution_results) / len(execution_results)
        
        # Findings summary
        findings_by_severity = {}
        for finding in findings:
            severity = finding.severity.value
            if severity not in findings_by_severity:
                findings_by_severity[severity] = 0
            findings_by_severity[severity] += 1
        
        return {
            "total_scenarios": len(execution_results),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_error_rate": overall_error_rate,
            "avg_response_time": avg_response_time,
            "total_findings": len(findings),
            "findings_by_severity": findings_by_severity,
            "analysis_duration": time.time() - execution_results[0].start_time if execution_results else 0
        }
    
    def _calculate_metrics(self, execution_results: List[ExecutionResult]) -> Dict[str, Any]:
        """Calculate comprehensive metrics."""
        metrics = {
            "performance": {
                "avg_response_time": sum(r.avg_response_time for r in execution_results) / len(execution_results),
                "p95_response_time": sum(r.p95_response_time for r in execution_results) / len(execution_results),
                "avg_throughput": sum(r.throughput for r in execution_results) / len(execution_results),
                "max_throughput": max(r.throughput for r in execution_results)
            },
            "reliability": {
                "overall_error_rate": sum(r.failed_requests for r in execution_results) / sum(r.total_requests for r in execution_results) if execution_results else 0,
                "availability": 1.0 - (sum(r.failed_requests for r in execution_results) / sum(r.total_requests for r in execution_results)) if execution_results else 1.0,
                "scenarios_with_errors": len([r for r in execution_results if r.failed_requests > 0]),
                "scenarios_completed": len([r for r in execution_results if r.status.value == "completed"])
            },
            "efficiency": {
                "requests_per_second": sum(r.throughput for r in execution_results),
                "avg_scenario_duration": sum(r.duration_seconds for r in execution_results) / len(execution_results),
                "total_execution_time": max(r.end_time for r in execution_results) - min(r.start_time for r in execution_results) if execution_results else 0
            }
        }
        
        return metrics
    
    def _generate_recommendations(self, findings: List[AnalysisFinding]) -> List[str]:
        """Generate high-level recommendations based on findings."""
        recommendations = []
        
        # Collect all unique recommendations
        all_recommendations = set()
        for finding in findings:
            all_recommendations.update(finding.recommendations)
        
        # Prioritize based on severity
        critical_findings = [f for f in findings if f.severity == SeverityLevel.CRITICAL]
        high_findings = [f for f in findings if f.severity == SeverityLevel.HIGH]
        
        if critical_findings:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Address critical findings before production deployment")
        
        if high_findings:
            recommendations.append("HIGH PRIORITY: Address high-severity findings in next iteration")
        
        # Add top recommendations
        recommendations.extend(list(all_recommendations)[:10])
        
        return recommendations
    
    def _calculate_overall_score(self, findings: List[AnalysisFinding], 
                                metrics: Dict[str, Any]) -> float:
        """Calculate overall system score (0.0 to 1.0)."""
        score = 1.0
        
        # Deduct points for findings based on severity
        severity_penalties = {
            SeverityLevel.CRITICAL: 0.3,
            SeverityLevel.HIGH: 0.15,
            SeverityLevel.MEDIUM: 0.05,
            SeverityLevel.LOW: 0.01,
            SeverityLevel.INFO: 0.0
        }
        
        for finding in findings:
            score -= severity_penalties.get(finding.severity, 0) * finding.confidence
        
        # Factor in performance metrics
        error_rate = metrics.get("reliability", {}).get("overall_error_rate", 0)
        score -= error_rate * 0.5
        
        avg_response_time = metrics.get("performance", {}).get("avg_response_time", 0)
        if avg_response_time > 5.0:
            score -= 0.1
        elif avg_response_time > 2.0:
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def get_analysis_report(self, report_id: str) -> Optional[AnalysisReport]:
        """Get analysis report by ID."""
        for report in self.analysis_results:
            if report.report_id == report_id:
                return report
        return None
    
    def get_all_reports(self) -> List[AnalysisReport]:
        """Get all analysis reports."""
        return self.analysis_results.copy()
    
    def export_report(self, report_id: str, filename: str, format: str = "json"):
        """Export analysis report to file."""
        report = self.get_analysis_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Convert to serializable format
        report_dict = asdict(report)
        
        # Convert enums to strings
        for finding in report_dict["findings"]:
            finding["severity"] = finding["severity"].value
            finding["analysis_type"] = finding["analysis_type"].value
        
        if format.lower() == "json":
            with open(filename, 'w') as f:
                json.dump(report_dict, f, indent=2)
        
        elif format.lower() == "html":
            html_content = self._generate_html_report(report_dict)
            with open(filename, 'w') as f:
                f.write(html_content)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _generate_html_report(self, report_dict: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EVENT_HORIZON Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .finding {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .critical {{ border-left-color: #d32f2f; }}
                .high {{ border-left-color: #f57c00; }}
                .medium {{ border-left-color: #fbc02d; }}
                .low {{ border-left-color: #388e3c; }}
                .info {{ border-left-color: #1976d2; }}
                .metrics {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                .metric {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; min-width: 200px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>EVENT_HORIZON Analysis Report</h1>
                <p>Report ID: {report_dict['report_id']}</p>
                <p>Generated: {time.ctime(report_dict['generated_at'])}</p>
                <p>Overall Score: {report_dict['overall_score']:.2%}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Scenarios: {report_dict['summary']['total_scenarios']}</p>
                <p>Total Requests: {report_dict['summary']['total_requests']}</p>
                <p>Overall Error Rate: {report_dict['summary']['overall_error_rate']:.2%}</p>
                <p>Total Findings: {report_dict['summary']['total_findings']}</p>
            </div>
            
            <div class="metrics">
                <h2>Metrics</h2>
                <div class="metric">
                    <h3>Performance</h3>
                    <p>Avg Response Time: {report_dict['metrics']['performance']['avg_response_time']:.3f}s</p>
                    <p>Avg Throughput: {report_dict['metrics']['performance']['avg_throughput']:.2f} req/s</p>
                </div>
                <div class="metric">
                    <h3>Reliability</h3>
                    <p>Availability: {report_dict['metrics']['reliability']['availability']:.2%}</p>
                    <p>Scenarios Completed: {report_dict['metrics']['reliability']['scenarios_completed']}</p>
                </div>
            </div>
            
            <div>
                <h2>Findings</h2>
        """
        
        for finding in report_dict["findings"]:
            html += f"""
                <div class="finding {finding['severity']}">
                    <h3>{finding['title']}</h3>
                    <p><strong>Severity:</strong> {finding['severity'].upper()}</p>
                    <p><strong>Type:</strong> {finding['analysis_type']}</p>
                    <p><strong>Description:</strong> {finding['description']}</p>
                    <p><strong>Confidence:</strong> {finding['confidence']:.1%}</p>
                    <p><strong>Recommendations:</strong></p>
                    <ul>
            """
            for rec in finding["recommendations"]:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
