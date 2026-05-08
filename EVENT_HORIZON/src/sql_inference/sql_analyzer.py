"""
SQL Inference Engine

Defensive module for analyzing SQL parser behavior and identifying
potential anomalies without offensive data extraction or credential access.
"""

import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio


class AnomalyType(Enum):
    """Types of SQL parser anomalies to detect."""
    PARSER_INCONSISTENCY = "parser_inconsistency"
    QUERY_PATH_VARIATION = "query_path_variation"
    RESPONSE_BEHAVIOR_DIFFERENCE = "response_behavior_difference"
    NORMALIZATION_ISSUE = "normalization_issue"
    TIMEOUT_VARIATION = "timeout_variation"


@dataclass
class QueryVariant:
    """Represents a SQL query variant for testing."""
    query: str
    description: str
    category: str
    safe: bool = True  # All variants are safe by design


@dataclass
class ResponseMetrics:
    """Metrics collected from SQL query responses."""
    status_code: int
    response_time: float
    content_length: int
    headers: Dict[str, str]
    body_hash: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class AnomalyDetection:
    """Represents a detected anomaly."""
    anomaly_type: AnomalyType
    severity: str  # "low", "medium", "high"
    description: str
    affected_queries: List[str]
    metrics_difference: Dict[str, Any]
    confidence: float


class SQLInferenceEngine:
    """
    Defensive SQL analysis engine for identifying parser anomalies
    and response behavior differences without offensive operations.
    """
    
    def __init__(self):
        self.safe_variants = self._generate_safe_variants()
        self.baseline_metrics: Dict[str, ResponseMetrics] = {}
        self.anomaly_threshold = 0.2  # 20% difference threshold
        
    def _generate_safe_variants(self) -> List[QueryVariant]:
        """Generate safe SQL query variants for testing."""
        variants = [
            # Basic structure variations
            QueryVariant(
                query="SELECT 1",
                description="Basic SELECT with literal",
                category="basic_select"
            ),
            QueryVariant(
                query="SELECT 1 FROM dual",
                description="SELECT with FROM clause",
                category="basic_select"
            ),
            QueryVariant(
                query="SELECT   1",
                description="SELECT with extra whitespace",
                category="whitespace"
            ),
            QueryVariant(
                query="SELECT\t1",
                description="SELECT with tab whitespace",
                category="whitespace"
            ),
            QueryVariant(
                query="SELECT\n1",
                description="SELECT with newline whitespace",
                category="whitespace"
            ),
            
            # Case variations
            QueryVariant(
                query="select 1",
                description="Lowercase SELECT",
                category="case_variation"
            ),
            QueryVariant(
                query="Select 1",
                description="Mixed case SELECT",
                category="case_variation"
            ),
            QueryVariant(
                query="SELECT 1",
                description="Uppercase SELECT",
                category="case_variation"
            ),
            
            # Comment variations
            QueryVariant(
                query="SELECT 1-- comment",
                description="SELECT with line comment",
                category="comment"
            ),
            QueryVariant(
                query="SELECT 1 /* comment */",
                description="SELECT with block comment",
                category="comment"
            ),
            QueryVariant(
                query="SELECT 1 # comment",
                description="SELECT with MySQL-style comment",
                category="comment"
            ),
            
            # Parentheses and grouping
            QueryVariant(
                query="(SELECT 1)",
                description="SELECT wrapped in parentheses",
                category="grouping"
            ),
            QueryVariant(
                query="SELECT (1)",
                description="SELECT with parentheses around literal",
                category="grouping"
            ),
            QueryVariant(
                query="SELECT ((1))",
                description="SELECT with nested parentheses",
                category="grouping"
            ),
            
            # String literal variations
            QueryVariant(
                query="SELECT '1'",
                description="SELECT with string literal",
                category="string_literal"
            ),
            QueryVariant(
                query="SELECT \"1\"",
                description="SELECT with double-quoted string",
                category="string_literal"
            ),
            QueryVariant(
                query="SELECT '1' ",
                description="SELECT with trailing space in string",
                category="string_literal"
            ),
            
            # Numeric variations
            QueryVariant(
                query="SELECT 1.0",
                description="SELECT with float",
                category="numeric"
            ),
            QueryVariant(
                query="SELECT +1",
                description="SELECT with unary plus",
                category="numeric"
            ),
            QueryVariant(
                query="SELECT -1",
                description="SELECT with unary minus",
                category="numeric"
            ),
            
            # Function variations
            QueryVariant(
                query="SELECT ABS(1)",
                description="SELECT with function",
                category="function"
            ),
            QueryVariant(
                query="SELECT ABS ( 1 )",
                description="SELECT with function spacing",
                category="function"
            ),
            QueryVariant(
                query="SELECT ABS((1))",
                description="SELECT with nested function",
                category="function"
            ),
            
            # Operator variations
            QueryVariant(
                query="SELECT 1+0",
                description="SELECT with addition",
                category="operator"
            ),
            QueryVariant(
                query="SELECT 1 * 1",
                description="SELECT with multiplication",
                category="operator"
            ),
            QueryVariant(
                query="SELECT 1||1",
                description="SELECT with concatenation",
                category="operator"
            ),
            
            # NULL variations
            QueryVariant(
                query="SELECT NULL",
                description="SELECT NULL literal",
                category="null"
            ),
            QueryVariant(
                query="SELECT ISNULL(NULL)",
                description="SELECT with ISNULL function",
                category="null"
            ),
            QueryVariant(
                query="SELECT COALESCE(NULL, 1)",
                description="SELECT with COALESCE",
                category="null"
            ),
            
            # Boolean variations
            QueryVariant(
                query="SELECT TRUE",
                description="SELECT TRUE literal",
                category="boolean"
            ),
            QueryVariant(
                query="SELECT FALSE",
                description="SELECT FALSE literal",
                category="boolean"
            ),
            QueryVariant(
                query="SELECT 1=1",
                description="SELECT with boolean expression",
                category="boolean"
            ),
            
            # Type casting variations
            QueryVariant(
                query="SELECT CAST(1 AS INT)",
                description="SELECT with explicit CAST",
                category="casting"
            ),
            QueryVariant(
                query="SELECT CONVERT(INT, 1)",
                description="SELECT with CONVERT function",
                category="casting"
            ),
            QueryVariant(
                query="SELECT 1::INT",
                description="SELECT with PostgreSQL cast",
                category="casting"
            ),
        ]
        
        return variants
    
    async def analyze_query_response(self, query: str, response_data: Dict) -> ResponseMetrics:
        """
        Analyze response metrics for a SQL query.
        
        Args:
            query: SQL query that was executed
            response_data: Response data from the query
            
        Returns:
            ResponseMetrics object with analysis results
        """
        start_time = time.time()
        
        # Extract basic metrics
        status_code = response_data.get("status_code", 200)
        content_length = len(response_data.get("body", ""))
        headers = response_data.get("headers", {})
        
        # Calculate response time if not provided
        response_time = response_data.get("response_time", time.time() - start_time)
        
        # Generate body hash for comparison
        body = response_data.get("body", "")
        body_hash = hashlib.md5(body.encode()).hexdigest() if body else None
        
        # Extract error message if present
        error_message = self._extract_error_message(body)
        
        return ResponseMetrics(
            status_code=status_code,
            response_time=response_time,
            content_length=content_length,
            headers=headers,
            body_hash=body_hash,
            error_message=error_message
        )
    
    def _extract_error_message(self, body: str) -> Optional[str]:
        """Extract error message from response body."""
        error_patterns = [
            r'error:\s*(.+?)(?:\n|$)',
            r'Error:\s*(.+?)(?:\n|$)',
            r'ERROR:\s*(.+?)(?:\n|$)',
            r'exception:\s*(.+?)(?:\n|$)',
            r'Exception:\s*(.+?)(?:\n|$)',
            r'syntax error.*?:(.+?)(?:\n|$)',
            r'SQLSTATE\[\d+\]:\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def detect_anomalies(self, query_variants: List[QueryVariant], 
                             responses: List[ResponseMetrics]) -> List[AnomalyDetection]:
        """
        Detect anomalies in SQL query responses.
        
        Args:
            query_variants: List of query variants tested
            responses: Corresponding response metrics
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        if len(query_variants) != len(responses):
            raise ValueError("Query variants and responses must have same length")
        
        # Group responses by category
        categories = {}
        for i, variant in enumerate(query_variants):
            category = variant.category
            if category not in categories:
                categories[category] = []
            categories[category].append((variant, responses[i]))
        
        # Analyze each category for anomalies
        for category, items in categories.items():
            category_anomalies = await self._analyze_category_anomalies(category, items)
            anomalies.extend(category_anomalies)
        
        # Cross-category analysis
        cross_anomalies = await self._analyze_cross_category_anomalies(categories)
        anomalies.extend(cross_anomalies)
        
        return anomalies
    
    async def _analyze_category_anomalies(self, category: str, 
                                        items: List[Tuple[QueryVariant, ResponseMetrics]]) -> List[AnomalyDetection]:
        """Analyze anomalies within a specific category."""
        anomalies = []
        
        if len(items) < 2:
            return anomalies
        
        # Extract metrics for comparison
        status_codes = [r.status_code for _, r in items]
        response_times = [r.response_time for _, r in items]
        content_lengths = [r.content_length for _, r in items]
        body_hashes = [r.body_hash for _, r in items]
        
        # Check for status code inconsistencies
        unique_statuses = set(status_codes)
        if len(unique_statuses) > 1:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.PARSER_INCONSISTENCY,
                severity="medium",
                description=f"Different status codes in {category}: {unique_statuses}",
                affected_queries=[q.query for q, _ in items],
                metrics_difference={"status_codes": status_codes},
                confidence=0.8
            ))
        
        # Check for response time variations
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        if max_time > 0 and (max_time - min_time) / avg_time > self.anomaly_threshold:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.TIMEOUT_VARIATION,
                severity="low",
                description=f"Response time variation in {category}: {min_time:.3f}s - {max_time:.3f}s",
                affected_queries=[q.query for q, _ in items],
                metrics_difference={"response_times": response_times},
                confidence=0.6
            ))
        
        # Check for content length variations
        unique_lengths = set(content_lengths)
        if len(unique_lengths) > 1:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.RESPONSE_BEHAVIOR_DIFFERENCE,
                severity="low",
                description=f"Different content lengths in {category}: {unique_lengths}",
                affected_queries=[q.query for q, _ in items],
                metrics_difference={"content_lengths": content_lengths},
                confidence=0.5
            ))
        
        # Check for body hash differences (indicating different responses)
        unique_hashes = set(filter(None, body_hashes))
        if len(unique_hashes) > 1:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.RESPONSE_BEHAVIOR_DIFFERENCE,
                severity="medium",
                description=f"Different response bodies in {category}",
                affected_queries=[q.query for q, _ in items],
                metrics_difference={"body_hashes": list(unique_hashes)},
                confidence=0.7
            ))
        
        return anomalies
    
    async def _analyze_cross_category_anomalies(self, categories: Dict[str, List]) -> List[AnomalyDetection]:
        """Analyze anomalies across different categories."""
        anomalies = []
        
        # Compare basic queries with modified versions
        basic_category = categories.get("basic_select", [])
        whitespace_category = categories.get("whitespace", [])
        
        if basic_category and whitespace_category:
            basic_response = basic_category[0][1]
            
            for variant, response in whitespace_category:
                # Check if whitespace changes cause different behavior
                if basic_response.status_code != response.status_code:
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.NORMALIZATION_ISSUE,
                        severity="medium",
                        description=f"Whitespace normalization affects query behavior",
                        affected_queries=[variant.query],
                        metrics_difference={
                            "basic_status": basic_response.status_code,
                            "whitespace_status": response.status_code
                        },
                        confidence=0.8
                    ))
        
        return anomalies
    
    def generate_test_scenarios(self, focus_areas: List[str] = None) -> List[QueryVariant]:
        """
        Generate test scenarios based on focus areas.
        
        Args:
            focus_areas: List of categories to focus on (None for all)
            
        Returns:
            List of query variants for testing
        """
        if focus_areas is None:
            return self.safe_variants
        
        return [variant for variant in self.safe_variants 
                if variant.category in focus_areas]
    
    def create_baseline(self, baseline_responses: Dict[str, ResponseMetrics]):
        """Create baseline metrics for comparison."""
        self.baseline_metrics = baseline_responses
    
    def compare_with_baseline(self, current_responses: Dict[str, ResponseMetrics]) -> List[AnomalyDetection]:
        """Compare current responses with baseline metrics."""
        anomalies = []
        
        for query, current in current_responses.items():
            if query in self.baseline_metrics:
                baseline = self.baseline_metrics[query]
                
                # Compare key metrics
                if baseline.status_code != current.status_code:
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.PARSER_INCONSISTENCY,
                        severity="high",
                        description=f"Status code changed from baseline for query: {query}",
                        affected_queries=[query],
                        metrics_difference={
                            "baseline_status": baseline.status_code,
                            "current_status": current.status_code
                        },
                        confidence=0.9
                    ))
                
                # Check response time degradation
                time_increase = current.response_time - baseline.response_time
                if baseline.response_time > 0 and time_increase / baseline.response_time > self.anomaly_threshold:
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.TIMEOUT_VARIATION,
                        severity="medium",
                        description=f"Response time increased by {time_increase:.3f}s from baseline",
                        affected_queries=[query],
                        metrics_difference={
                            "baseline_time": baseline.response_time,
                            "current_time": current.response_time,
                            "increase": time_increase
                        },
                        confidence=0.7
                    ))
        
        return anomalies
    
    def get_analysis_summary(self, anomalies: List[AnomalyDetection]) -> Dict[str, Any]:
        """Generate summary of anomaly analysis."""
        summary = {
            "total_anomalies": len(anomalies),
            "severity_distribution": {"low": 0, "medium": 0, "high": 0},
            "type_distribution": {},
            "high_confidence_anomalies": [],
            "affected_queries": set()
        }
        
        for anomaly in anomalies:
            # Count by severity
            summary["severity_distribution"][anomaly.severity] += 1
            
            # Count by type
            anomaly_type = anomaly.anomaly_type.value
            summary["type_distribution"][anomaly_type] = summary["type_distribution"].get(anomaly_type, 0) + 1
            
            # Track high confidence anomalies
            if anomaly.confidence > 0.8:
                summary["high_confidence_anomalies"].append(anomaly)
            
            # Track affected queries
            summary["affected_queries"].update(anomaly.affected_queries)
        
        summary["affected_queries"] = list(summary["affected_queries"])
        
        return summary
