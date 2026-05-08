#!/usr/bin/env python3
"""
Analysis Engine
Detects SQL injection vulnerabilities through response analysis
"""

import re
import time
import requests
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import difflib
import logging
from urllib.parse import urlparse, parse_qs

class InjectionType(Enum):
    ERROR_BASED = "error_based"
    BOOLEAN_BASED = "boolean_based"
    TIME_BASED = "time_based"
    UNION_BASED = "union_based"

class DatabaseType(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    ORACLE = "oracle"
    SQLITE = "sqlite"

@dataclass
class Vulnerability:
    """Represents a discovered vulnerability"""
    url: str
    parameter: str
    injection_type: InjectionType
    database_type: DatabaseType
    payload: str
    evidence: str
    confidence: float
    response_time: float
    status_code: int
    error_message: Optional[str] = None
    database_info: Optional[Dict[str, str]] = None

class ErrorPatternMatcher:
    """Matches SQL error patterns in responses"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_patterns = self._load_error_patterns()
    
    def _load_error_patterns(self) -> Dict[DatabaseType, List[str]]:
        """Load SQL error patterns for different databases"""
        return {
            DatabaseType.MYSQL: [
                r"you have an error in your sql syntax",
                r"mysql_fetch_array\(\)",
                r"mysql_fetch_assoc\(\)",
                r"mysql_num_rows\(\)",
                r"mysql_query\(\)",
                r"Unknown column '[^']*'",
                r"Table '[^']*' doesn't exist",
                r"Column '[^']*' not found",
                r"SQL syntax.*MySQL",
                r"Warning.*mysql_.*",
                r"valid MySQL result",
                r"MySqlClient\.",
                r"com\.mysql\.jdbc",
                r"org\.ggj\.mysql",
                r"at .*mysql.*",
                r"Syntax error or access violation",
                r"Query failed",
                r"SQLSTATE\[42000\]",
                r"SQLSTATE\[23000\]",
                r"SQLSTATE\[42S02\]",
                r"SQLSTATE\[42S22\]",
                r"SQLSTATE\[42S12\]",
                r"SQLSTATE\[HY000\]"
            ],
            DatabaseType.POSTGRESQL: [
                r"pg_query\(\)",
                r"pg_fetch_array\(\)",
                r"pg_fetch_assoc\(\)",
                r"pg_num_rows\(\)",
                r"PostgreSQL query failed",
                r"pg_exec\(\)",
                r"valid PostgreSQL result",
                r"Npgsql\.",
                r"PG::SyntaxError",
                r"org\.postgresql\.util\.PSQLException",
                r"ERROR.*syntax error at or near",
                r"ERROR.*column .* does not exist",
                r"ERROR.*relation .* does not exist",
                r"ERROR.*operator does not exist",
                r"ERROR.*invalid input syntax for",
                r"ERROR.*could not determine data type",
                r"SQLSTATE\[42601\]",
                r"SQLSTATE\[42703\]",
                r"SQLSTATE\[42P01\]",
                r"SQLSTATE\[42883\]"
            ],
            DatabaseType.MSSQL: [
                r"Microsoft OLE DB Provider for ODBC Drivers error",
                r"Microsoft OLE DB Provider for SQL Server error",
                r"ODBC SQL Server Driver",
                r"SQLServer JDBC Driver",
                r"com\.microsoft\.sqlserver\.jdbc",
                r"System\.Data\.SqlClient\.SqlException",
                r"Unclosed quotation mark before the character string",
                r"Syntax error converting the nvarchar value",
                r"Invalid column name",
                r"Invalid object name",
                r"The column prefix .* does not match with a table name",
                r"Conversion failed when converting",
                r"Must declare the scalar variable",
                r"SQLSTATE\[42000\]",
                r"SQLSTATE\[42S22\]",
                r"SQLSTATE\[42S02\]"
            ],
            DatabaseType.ORACLE: [
                r"ORA-\d{5}",
                r"Oracle error",
                r"Oracle driver",
                r"Warning.*oci_.*",
                r"Warning.*ora_.*",
                r"java\.sql\.SQLException: ORA-",
                r"oracle\.jdbc\.driver",
                r"quoted string not properly terminated",
                r"invalid identifier",
                r"invalid number",
                r"missing comma",
                r"missing right parenthesis",
                r"SQL command not properly ended"
            ],
            DatabaseType.SQLITE: [
                r"SQLite/JDBCDriver",
                r"SQLite\.Exception",
                r"Warning.*sqlite_.*",
                r"Warning.*SQLite3::",
                r"SQLSTATE\[HY000\]: General error: \d+ no such table",
                r"SQLSTATE\[HY000\]: General error: \d+ no such column",
                r"SQLSTATE\[HY000\]: General error: \d+ near",
                r"SQLSTATE\[23000\]: Integrity constraint violation"
            ]
        }
    
    def detect_database_type(self, response_text: str) -> Optional[DatabaseType]:
        """Detect database type from error messages"""
        response_lower = response_text.lower()
        
        for db_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    return db_type
        
        return None
    
    def find_sql_errors(self, response_text: str, db_type: Optional[DatabaseType] = None) -> List[str]:
        """Find SQL error messages in response"""
        errors = []
        
        if db_type:
            patterns = self.error_patterns.get(db_type, [])
        else:
            # Check all database patterns
            patterns = []
            for db_patterns in self.error_patterns.values():
                patterns.extend(db_patterns)
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                errors.extend(matches)
        
        return list(set(errors))  # Remove duplicates
    
    def extract_database_info(self, response_text: str, db_type: DatabaseType) -> Dict[str, str]:
        """Extract database information from error messages"""
        info = {}
        
        if db_type == DatabaseType.MYSQL:
            # Extract version
            version_match = re.search(r'(\d+\.\d+\.\d+[^,\s]*)', response_text)
            if version_match:
                info['version'] = version_match.group(1)
            
            # Extract database name
            db_match = re.search(r"database '([^']+)'", response_text, re.IGNORECASE)
            if db_match:
                info['database'] = db_match.group(1)
            
            # Extract table name
            table_match = re.search(r"table ['`]?([^'`]+)['`]?", response_text, re.IGNORECASE)
            if table_match:
                info['table'] = table_match.group(1)
            
            # Extract column name
            column_match = re.search(r"column ['`]?([^'`]+)['`]?", response_text, re.IGNORECASE)
            if column_match:
                info['column'] = column_match.group(1)
        
        elif db_type == DatabaseType.POSTGRESQL:
            # Extract version
            version_match = re.search(r'PostgreSQL (\d+\.\d+)', response_text)
            if version_match:
                info['version'] = version_match.group(1)
            
            # Extract database name
            db_match = re.search(r'database "([^"]+)"', response_text)
            if db_match:
                info['database'] = db_match.group(1)
        
        elif db_type == DatabaseType.MSSQL:
            # Extract version
            version_match = re.search(r'SQL Server (\d{4})', response_text)
            if version_match:
                info['version'] = version_match.group(1)
            
            # Extract database name
            db_match = re.search(r"database '([^']+)'", response_text, re.IGNORECASE)
            if db_match:
                info['database'] = db_match.group(1)
        
        return info

class ResponseAnalyzer:
    """Analyzes HTTP responses for SQL injection indicators"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_matcher = ErrorPatternMatcher()
    
    def analyze_response(self, response: requests.Response, payload: str, 
                        baseline_response: Optional[requests.Response] = None) -> Dict[str, Any]:
        """Analyze response for SQL injection indicators"""
        analysis = {
            'status_code': response.status_code,
            'response_time': getattr(response, 'elapsed', None),
            'content_length': len(response.content),
            'response_text': response.text,
            'headers': dict(response.headers),
            'sql_errors': [],
            'database_type': None,
            'database_info': {},
            'content_diff': None,
            'time_delay': False,
            'boolean_difference': False
        }
        
        # Check for SQL errors
        analysis['sql_errors'] = self.error_matcher.find_sql_errors(response.text)
        
        # Detect database type
        if analysis['sql_errors']:
            analysis['database_type'] = self.error_matcher.detect_database_type(response.text)
            if analysis['database_type']:
                analysis['database_info'] = self.error_matcher.extract_database_info(
                    response.text, analysis['database_type']
                )
        
        # Compare with baseline if available
        if baseline_response:
            analysis['content_diff'] = self._compare_content(
                baseline_response.text, response.text
            )
            analysis['boolean_difference'] = self._detect_boolean_difference(
                baseline_response.text, response.text
            )
            
            # Check for time-based delays
            if hasattr(response, 'elapsed') and hasattr(baseline_response, 'elapsed'):
                baseline_time = baseline_response.elapsed.total_seconds()
                current_time = response.elapsed.total_seconds()
                analysis['time_delay'] = (current_time - baseline_time) > 3.0
        
        return analysis
    
    def _compare_content(self, baseline: str, current: str) -> Dict[str, Any]:
        """Compare content between baseline and current response"""
        baseline_lines = baseline.splitlines()
        current_lines = current.splitlines()
        
        diff = list(difflib.unified_diff(
            baseline_lines, current_lines, 
            fromfile='baseline', tofile='current', lineterm=''
        ))
        
        similarity = difflib.SequenceMatcher(None, baseline, current).ratio()
        
        return {
            'diff': diff,
            'similarity_ratio': similarity,
            'significant_difference': similarity < 0.8
        }
    
    def _detect_boolean_difference(self, baseline: str, current: str) -> bool:
        """Detect boolean-based injection differences"""
        # Simple heuristic: significant content difference without SQL errors
        baseline_words = set(baseline.lower().split())
        current_words = set(current.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(baseline_words.intersection(current_words))
        union = len(baseline_words.union(current_words))
        
        if union == 0:
            return False
        
        similarity = intersection / union
        
        # Consider it a boolean difference if similarity is between 0.3 and 0.8
        return 0.3 < similarity < 0.8

class VulnerabilityScanner:
    """Main vulnerability scanning engine"""
    
    def __init__(self, session: requests.Session, timeout: int = 30):
        self.session = session
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.analyzer = ResponseAnalyzer()
        self.vulnerabilities: List[Vulnerability] = []
    
    def scan_parameter(self, url: str, parameter: str, payloads: List[str], 
                      injection_type: InjectionType, db_type: DatabaseType) -> List[Vulnerability]:
        """Scan a specific parameter for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        # Get baseline response
        baseline_response = self._get_baseline_response(url, parameter)
        if not baseline_response:
            return vulnerabilities
        
        for payload in payloads:
            try:
                # Prepare request with payload
                test_response = self._send_payload(url, parameter, payload)
                
                if not test_response:
                    continue
                
                # Analyze response
                analysis = self.analyzer.analyze_response(test_response, payload, baseline_response)
                
                # Check for vulnerability indicators
                vulnerability = self._check_vulnerability(
                    url, parameter, payload, injection_type, db_type, analysis
                )
                
                if vulnerability:
                    vulnerabilities.append(vulnerability)
                    self.logger.info(f"Vulnerability found: {vulnerability}")
                    break  # Stop after finding first vulnerability for this parameter
                    
            except Exception as e:
                self.logger.error(f"Error scanning {url} with payload {payload}: {e}")
                continue
        
        return vulnerabilities
    
    def _get_baseline_response(self, url: str, parameter: str) -> Optional[requests.Response]:
        """Get baseline response for comparison"""
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Use a safe value for baseline
            if parameter in params:
                original_value = params[parameter][0]
                params[parameter] = ['1']  # Safe numeric value
            else:
                params[parameter] = ['1']
            
            # Reconstruct URL with modified parameters
            query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
            baseline_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            
            response = self.session.get(baseline_url, timeout=self.timeout)
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting baseline response: {e}")
            return None
    
    def _send_payload(self, url: str, parameter: str, payload: str, 
                      security_manager=None, auth_token=None) -> Optional[requests.Response]:
        """Send payload and return response with security validation"""
        try:
            # Security check before execution
            if security_manager:
                authorized, auth_msg = security_manager.authorize_operation(
                    url, 'execute_requests', payload, auth_token
                )
                if not authorized:
                    self.logger.warning(f"Security denied payload execution: {auth_msg}")
                    return None
                
                # Log payload execution
                import hashlib
                payload_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
                security_manager.log_operation(
                    "payload_execution", url, f"test_{parameter}",
                    payload_hash=payload_hash
                )
            
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Replace parameter value with payload
            params[parameter] = [payload]
            
            # Reconstruct URL with payload
            query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            
            start_time = time.time()
            response = self.session.get(test_url, timeout=self.timeout)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response
            if security_manager:
                security_manager.log_operation(
                    "payload_response", url, f"response_{parameter}",
                    payload_hash=payload_hash,
                    response_code=response.status_code,
                    duration_ms=duration_ms
                )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error sending payload: {e}")
            if security_manager:
                security_manager.log_operation(
                    "payload_error", url, f"error_{parameter}",
                    metadata={"error": str(e)}
                )
            return None
    
    def _check_vulnerability(self, url: str, parameter: str, payload: str,
                           injection_type: InjectionType, db_type: DatabaseType,
                           analysis: Dict[str, Any]) -> Optional[Vulnerability]:
        """Check if response indicates a vulnerability"""
        
        if injection_type == InjectionType.ERROR_BASED:
            if analysis['sql_errors']:
                return Vulnerability(
                    url=url,
                    parameter=parameter,
                    injection_type=injection_type,
                    database_type=analysis['database_type'] or db_type,
                    payload=payload,
                    evidence=str(analysis['sql_errors']),
                    confidence=0.9,
                    response_time=analysis['response_time'].total_seconds() if analysis['response_time'] else 0,
                    status_code=analysis['status_code'],
                    error_message=', '.join(analysis['sql_errors']),
                    database_info=analysis['database_info']
                )
        
        elif injection_type == InjectionType.BOOLEAN_BASED:
            if analysis['boolean_difference']:
                return Vulnerability(
                    url=url,
                    parameter=parameter,
                    injection_type=injection_type,
                    database_type=db_type,
                    payload=payload,
                    evidence="Boolean-based response difference detected",
                    confidence=0.7,
                    response_time=analysis['response_time'].total_seconds() if analysis['response_time'] else 0,
                    status_code=analysis['status_code']
                )
        
        elif injection_type == InjectionType.TIME_BASED:
            if analysis['time_delay']:
                return Vulnerability(
                    url=url,
                    parameter=parameter,
                    injection_type=injection_type,
                    database_type=db_type,
                    payload=payload,
                    evidence="Time-based delay detected",
                    confidence=0.8,
                    response_time=analysis['response_time'].total_seconds() if analysis['response_time'] else 0,
                    status_code=analysis['status_code']
                )
        
        elif injection_type == InjectionType.UNION_BASED:
            if analysis['content_diff'] and analysis['content_diff']['significant_difference']:
                return Vulnerability(
                    url=url,
                    parameter=parameter,
                    injection_type=injection_type,
                    database_type=db_type,
                    payload=payload,
                    evidence="UNION-based response modification detected",
                    confidence=0.8,
                    response_time=analysis['response_time'].total_seconds() if analysis['response_time'] else 0,
                    status_code=analysis['status_code']
                )
        
        return None
    
    def get_vulnerabilities(self) -> List[Vulnerability]:
        """Return all discovered vulnerabilities"""
        return self.vulnerabilities
    
    def clear_vulnerabilities(self) -> None:
        """Clear all stored vulnerabilities"""
        self.vulnerabilities.clear()
