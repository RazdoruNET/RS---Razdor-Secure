"""
Response Analyzer

Analyzes HTTP responses to identify patterns and anomalies in SQL query behavior.
Focuses on defensive analysis without data extraction.
"""

import re
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json


class ResponsePattern(Enum):
    """Types of response patterns to analyze."""
    ERROR_PATTERN = "error_pattern"
    SUCCESS_PATTERN = "success_pattern"
    TIMEOUT_PATTERN = "timeout_pattern"
    REDIRECT_PATTERN = "redirect_pattern"
    SIZE_VARIATION = "size_variation"
    CONTENT_VARIATION = "content_variation"


@dataclass
class ResponseSignature:
    """Unique signature of a response for comparison."""
    status_code: int
    content_length: int
    body_hash: str
    key_headers: Dict[str, str]
    response_time: float


@dataclass
class PatternMatch:
    """Represents a matched pattern in response analysis."""
    pattern_type: ResponsePattern
    confidence: float
    description: str
    affected_queries: List[str]
    signature_differences: Dict[str, Any]


class ResponseAnalyzer:
    """
    Analyzes HTTP responses to identify patterns and anomalies
    in SQL query behavior for defensive purposes.
    """
    
    def __init__(self):
        self.error_patterns = self._compile_error_patterns()
        self.success_patterns = self._compile_success_patterns()
        self.response_signatures: Dict[str, ResponseSignature] = {}
        
    def _compile_error_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for detecting SQL errors."""
        patterns = [
            # SQL syntax errors
            re.compile(r'syntax error.*?near\s+[\'"]?([^\'"\s]+)', re.IGNORECASE),
            re.compile(r'you have an error in your sql syntax', re.IGNORECASE),
            re.compile(r'sqlstate\[42000\]', re.IGNORECASE),
            re.compile(r'ora-\d+:.*?near\s+[\'"]?([^\'"\s]+)', re.IGNORECASE),
            
            # Parser errors
            re.compile(r'parser error', re.IGNORECASE),
            re.compile(r'parse error.*?near\s+[\'"]?([^\'"\s]+)', re.IGNORECASE),
            
            # Type errors
            re.compile(r'type mismatch', re.IGNORECASE),
            re.compile(r'invalid data type', re.IGNORECASE),
            re.compile(r'cannot convert', re.IGNORECASE),
            
            # Function errors
            re.compile(r'function.*?does not exist', re.IGNORECASE),
            re.compile(r'invalid function', re.IGNORECASE),
            re.compile(r'unknown function', re.IGNORECASE),
            
            # Table/column errors (safe to detect)
            re.compile(r'table.*?doesn\'t exist', re.IGNORECASE),
            re.compile(r'column.*?doesn\'t exist', re.IGNORECASE),
            re.compile(r'no such table', re.IGNORECASE),
            re.compile(r'unknown column', re.IGNORECASE),
            
            # Constraint errors
            re.compile(r'constraint violation', re.IGNORECASE),
            re.compile(r'unique constraint', re.IGNORECASE),
            re.compile(r'foreign key constraint', re.IGNORECASE),
            
            # Connection/timeout errors
            re.compile(r'connection.*?timeout', re.IGNORECASE),
            re.compile(r'query.*?timeout', re.IGNORECASE),
            re.compile(r'deadlock', re.IGNORECASE),
            re.compile(r'lock wait timeout', re.IGNORECASE),
        ]
        
        return patterns
    
    def _compile_success_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for detecting successful responses."""
        patterns = [
            # Common success indicators
            re.compile(r'query executed successfully', re.IGNORECASE),
            re.compile(r'command completed', re.IGNORECASE),
            re.compile(r'success', re.IGNORECASE),
            re.compile(r'ok', re.IGNORECASE),
            
            # JSON success responses
            re.compile(r'"status":\s*["\']?success["\']?', re.IGNORECASE),
            re.compile(r'"result":\s*["\']?ok["\']?', re.IGNORECASE),
            re.compile(r'"success":\s*true', re.IGNORECASE),
            
            # HTML success indicators
            re.compile(r'<title>.*?success.*?</title>', re.IGNORECASE),
            re.compile(r'class=["\']success["\']', re.IGNORECASE),
        ]
        
        return patterns
    
    def analyze_response(self, query: str, response_data: Dict) -> ResponseSignature:
        """
        Analyze a single response and create its signature.
        
        Args:
            query: SQL query that generated the response
            response_data: HTTP response data
            
        Returns:
            ResponseSignature for the response
        """
        # Extract basic metrics
        status_code = response_data.get("status_code", 200)
        content_length = len(response_data.get("body", ""))
        headers = response_data.get("headers", {})
        response_time = response_data.get("response_time", 0.0)
        
        # Generate body hash
        body = response_data.get("body", "")
        body_hash = hashlib.md5(body.encode()).hexdigest()
        
        # Extract key headers for comparison
        key_headers = self._extract_key_headers(headers)
        
        signature = ResponseSignature(
            status_code=status_code,
            content_length=content_length,
            body_hash=body_hash,
            key_headers=key_headers,
            response_time=response_time
        )
        
        # Store signature for comparison
        self.response_signatures[query] = signature
        
        return signature
    
    def _extract_key_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Extract important headers for response comparison."""
        key_header_names = [
            "content-type",
            "content-length",
            "server",
            "x-powered-by",
            "cache-control",
            "pragma",
            "expires",
            "set-cookie",
            "location",
            "x-error-message"
        ]
        
        key_headers = {}
        for name in key_header_names:
            if name in headers:
                key_headers[name] = headers[name]
        
        return key_headers
    
    def detect_patterns(self, query: str, response_data: Dict) -> List[PatternMatch]:
        """
        Detect patterns in a response.
        
        Args:
            query: SQL query that generated the response
            response_data: HTTP response data
            
        Returns:
            List of detected patterns
        """
        patterns = []
        body = response_data.get("body", "")
        status_code = response_data.get("status_code", 200)
        
        # Detect error patterns
        error_patterns = self._detect_error_patterns(query, body, status_code)
        patterns.extend(error_patterns)
        
        # Detect success patterns
        success_patterns = self._detect_success_patterns(query, body, status_code)
        patterns.extend(success_patterns)
        
        # Detect timeout patterns
        timeout_patterns = self._detect_timeout_patterns(query, response_data)
        patterns.extend(timeout_patterns)
        
        # Detect redirect patterns
        redirect_patterns = self._detect_redirect_patterns(query, response_data)
        patterns.extend(redirect_patterns)
        
        return patterns
    
    def _detect_error_patterns(self, query: str, body: str, status_code: int) -> List[PatternMatch]:
        """Detect error patterns in response."""
        patterns = []
        
        # Check HTTP error status codes
        if status_code >= 400:
            for pattern in self.error_patterns:
                matches = pattern.findall(body)
                if matches:
                    patterns.append(PatternMatch(
                        pattern_type=ResponsePattern.ERROR_PATTERN,
                        confidence=0.8,
                        description=f"SQL error detected: {matches[0]}",
                        affected_queries=[query],
                        signature_differences={"error_matches": matches}
                    ))
        
        return patterns
    
    def _detect_success_patterns(self, query: str, body: str, status_code: int) -> List[PatternMatch]:
        """Detect success patterns in response."""
        patterns = []
        
        # Check HTTP success status codes
        if status_code < 400:
            for pattern in self.success_patterns:
                if pattern.search(body):
                    patterns.append(PatternMatch(
                        pattern_type=ResponsePattern.SUCCESS_PATTERN,
                        confidence=0.7,
                        description="Success pattern detected in response",
                        affected_queries=[query],
                        signature_differences={"success_indicators": True}
                    ))
        
        return patterns
    
    def _detect_timeout_patterns(self, query: str, response_data: Dict) -> List[PatternMatch]:
        """Detect timeout patterns in response."""
        patterns = []
        
        response_time = response_data.get("response_time", 0.0)
        body = response_data.get("body", "")
        status_code = response_data.get("status_code", 200)
        
        # Check for long response times
        if response_time > 5.0:  # 5 second threshold
            patterns.append(PatternMatch(
                pattern_type=ResponsePattern.TIMEOUT_PATTERN,
                confidence=0.6,
                description=f"Long response time detected: {response_time:.3f}s",
                affected_queries=[query],
                signature_differences={"response_time": response_time}
            ))
        
        # Check for timeout error messages
        timeout_indicators = [
            "timeout", "timed out", "connection timeout", 
            "query timeout", "request timeout"
        ]
        
        for indicator in timeout_indicators:
            if indicator.lower() in body.lower():
                patterns.append(PatternMatch(
                    pattern_type=ResponsePattern.TIMEOUT_PATTERN,
                    confidence=0.8,
                    description=f"Timeout indicator found: {indicator}",
                    affected_queries=[query],
                    signature_differences={"timeout_indicator": indicator}
                ))
        
        return patterns
    
    def _detect_redirect_patterns(self, query: str, response_data: Dict) -> List[PatternMatch]:
        """Detect redirect patterns in response."""
        patterns = []
        
        status_code = response_data.get("status_code", 200)
        headers = response_data.get("headers", {})
        
        # Check for redirect status codes
        if 300 <= status_code < 400:
            location = headers.get("location", "")
            patterns.append(PatternMatch(
                pattern_type=ResponsePattern.REDIRECT_PATTERN,
                confidence=0.9,
                description=f"Redirect detected: {status_code} -> {location}",
                affected_queries=[query],
                signature_differences={"redirect_status": status_code, "location": location}
            ))
        
        return patterns
    
    def compare_responses(self, query1: str, query2: str) -> Dict[str, Any]:
        """
        Compare two query responses for differences.
        
        Args:
            query1: First query
            query2: Second query
            
        Returns:
            Comparison results
        """
        if query1 not in self.response_signatures or query2 not in self.response_signatures:
            return {"error": "One or both queries not found in signatures"}
        
        sig1 = self.response_signatures[query1]
        sig2 = self.response_signatures[query2]
        
        differences = {}
        
        # Compare status codes
        if sig1.status_code != sig2.status_code:
            differences["status_code"] = {
                "query1": sig1.status_code,
                "query2": sig2.status_code
            }
        
        # Compare content lengths
        if sig1.content_length != sig2.content_length:
            differences["content_length"] = {
                "query1": sig1.content_length,
                "query2": sig2.content_length
            }
        
        # Compare body hashes
        if sig1.body_hash != sig2.body_hash:
            differences["body_content"] = "different"
        
        # Compare key headers
        header_diffs = {}
        all_header_keys = set(sig1.key_headers.keys()) | set(sig2.key_headers.keys())
        
        for key in all_header_keys:
            val1 = sig1.key_headers.get(key, "")
            val2 = sig2.key_headers.get(key, "")
            if val1 != val2:
                header_diffs[key] = {"query1": val1, "query2": val2}
        
        if header_diffs:
            differences["headers"] = header_diffs
        
        # Compare response times
        time_diff = abs(sig1.response_time - sig2.response_time)
        if time_diff > 0.1:  # 100ms threshold
            differences["response_time"] = {
                "query1": sig1.response_time,
                "query2": sig2.response_time,
                "difference": time_diff
            }
        
        return {
            "queries": [query1, query2],
            "differences": differences,
            "significant_differences": len(differences) > 0
        }
    
    def analyze_response_variations(self, queries: List[str], responses: List[Dict]) -> Dict[str, Any]:
        """
        Analyze variations across multiple query responses.
        
        Args:
            queries: List of SQL queries
            responses: Corresponding response data
            
        Returns:
            Analysis of response variations
        """
        if len(queries) != len(responses):
            raise ValueError("Queries and responses must have same length")
        
        # Generate signatures for all responses
        signatures = []
        for query, response in zip(queries, responses):
            signature = self.analyze_response(query, response)
            signatures.append(signature)
        
        # Analyze variations
        variations = {
            "status_code_variations": {},
            "content_length_variations": {},
            "response_time_variations": {},
            "body_hash_variations": {},
            "header_variations": {},
            "summary": {}
        }
        
        # Status code variations
        status_codes = [sig.status_code for sig in signatures]
        unique_statuses = set(status_codes)
        if len(unique_statuses) > 1:
            variations["status_code_variations"] = {
                "unique_codes": list(unique_statuses),
                "distribution": {code: status_codes.count(code) for code in unique_statuses}
            }
        
        # Content length variations
        content_lengths = [sig.content_length for sig in signatures]
        unique_lengths = set(content_lengths)
        if len(unique_lengths) > 1:
            variations["content_length_variations"] = {
                "unique_lengths": list(unique_lengths),
                "min_length": min(content_lengths),
                "max_length": max(content_lengths),
                "avg_length": sum(content_lengths) / len(content_lengths)
            }
        
        # Response time variations
        response_times = [sig.response_time for sig in signatures]
        if max(response_times) - min(response_times) > 0.1:
            variations["response_time_variations"] = {
                "min_time": min(response_times),
                "max_time": max(response_times),
                "avg_time": sum(response_times) / len(response_times),
                "std_dev": self._calculate_std_dev(response_times)
            }
        
        # Body hash variations
        body_hashes = [sig.body_hash for sig in signatures]
        unique_hashes = set(body_hashes)
        if len(unique_hashes) > 1:
            variations["body_hash_variations"] = {
                "unique_hashes": len(unique_hashes),
                "hash_distribution": {hash_val: body_hashes.count(hash_val) for hash_val in unique_hashes}
            }
        
        # Header variations
        all_headers = {}
        for sig in signatures:
            for key, value in sig.key_headers.items():
                if key not in all_headers:
                    all_headers[key] = set()
                all_headers[key].add(value)
        
        header_variations = {k: list(v) for k, v in all_headers.items() if len(v) > 1}
        if header_variations:
            variations["header_variations"] = header_variations
        
        # Summary
        variations["summary"] = {
            "total_queries": len(queries),
            "has_status_variations": len(variations["status_code_variations"]) > 0,
            "has_content_variations": len(variations["content_length_variations"]) > 0,
            "has_time_variations": len(variations["response_time_variations"]) > 0,
            "has_body_variations": len(variations["body_hash_variations"]) > 0,
            "has_header_variations": len(variations["header_variations"]) > 0,
            "overall_consistency": self._calculate_overall_consistency(variations)
        }
        
        return variations
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_overall_consistency(self, variations: Dict[str, Any]) -> float:
        """Calculate overall consistency score (0.0 = very inconsistent, 1.0 = very consistent)."""
        consistency_factors = []
        
        # Each type of variation reduces consistency
        if variations["status_code_variations"]:
            consistency_factors.append(0.5)  # Status variations are significant
        else:
            consistency_factors.append(1.0)
        
        if variations["content_length_variations"]:
            consistency_factors.append(0.7)  # Content variations are moderately significant
        else:
            consistency_factors.append(1.0)
        
        if variations["response_time_variations"]:
            time_var = variations["response_time_variations"]
            # Large time variations are more significant
            if time_var["std_dev"] > 1.0:
                consistency_factors.append(0.6)
            else:
                consistency_factors.append(0.8)
        else:
            consistency_factors.append(1.0)
        
        if variations["body_hash_variations"]:
            consistency_factors.append(0.4)  # Body variations are very significant
        else:
            consistency_factors.append(1.0)
        
        if variations["header_variations"]:
            consistency_factors.append(0.8)  # Header variations are less significant
        else:
            consistency_factors.append(1.0)
        
        return sum(consistency_factors) / len(consistency_factors)
    
    def export_analysis(self, output_file: str):
        """Export analysis results to JSON file."""
        export_data = {
            "response_signatures": {
                query: {
                    "status_code": sig.status_code,
                    "content_length": sig.content_length,
                    "body_hash": sig.body_hash,
                    "key_headers": sig.key_headers,
                    "response_time": sig.response_time
                }
                for query, sig in self.response_signatures.items()
            },
            "export_timestamp": time.time()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
