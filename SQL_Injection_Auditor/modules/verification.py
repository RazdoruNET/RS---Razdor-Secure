#!/usr/bin/env python3
"""
Verification Module
Reduces false positives through multi-stage verification
"""

import time
import requests
import random
import string
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
from urllib.parse import urlparse, parse_qs

from modules.analysis_engine import Vulnerability, InjectionType, DatabaseType

class VerificationStatus(Enum):
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    POSSIBLE = "possible"
    FALSE_POSITIVE = "false_positive"

@dataclass
class VerificationResult:
    """Result of vulnerability verification"""
    vulnerability: Vulnerability
    status: VerificationStatus
    confidence: float
    verification_tests: List[str]
    evidence: List[str]
    false_positive_indicators: List[str]

class FalsePositiveDetector:
    """Detects common false positive patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fp_patterns = self._load_fp_patterns()
    
    def _load_fp_patterns(self) -> Dict[str, List[str]]:
        """Load false positive patterns"""
        return {
            'generic_errors': [
                r"404 not found",
                r"500 internal server error",
                r"page not found",
                r"access denied",
                r"forbidden",
                r"service unavailable",
                r"bad request",
                r"request timeout"
            ],
            'framework_errors': [
                r"django\.debug",
                r"rails.*error",
                r"laravel.*error",
                r"wordpress.*error",
                r"drupal.*error",
                r"joomla.*error"
            ],
            'validation_errors': [
                r"invalid input",
                r"required field",
                r"missing parameter",
                r"validation failed",
                r"form validation",
                r"input validation"
            ],
            'application_errors': [
                r"application error",
                r"system error",
                r"unexpected error",
                r"error occurred",
                r"something went wrong"
            ]
        }
    
    def check_false_positive(self, response_text: str, payload: str) -> List[str]:
        """Check for false positive indicators"""
        indicators = []
        response_lower = response_text.lower()
        
        for category, patterns in self.fp_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_lower):
                    indicators.append(f"{category}: {pattern}")
        
        # Check for payload reflection (common in false positives)
        if payload.lower() in response_lower:
            indicators.append("payload_reflection")
        
        # Check for generic error pages
        if len(response_text) < 500 and any(keyword in response_lower for keyword in ['error', 'invalid', 'forbidden']):
            indicators.append("generic_error_page")
        
        return indicators

class PayloadVariator:
    """Generates payload variations for verification"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_variations(self, original_payload: str, db_type: DatabaseType) -> List[str]:
        """Generate variations of the original payload"""
        variations = []
        
        # Original payload
        variations.append(original_payload)
        
        # Case variations
        variations.append(original_payload.upper())
        variations.append(original_payload.lower())
        
        # Comment variations
        variations.append(original_payload.replace('--', '#'))
        variations.append(original_payload.replace('--', '/* */'))
        
        # Encoding variations
        variations.append(original_payload.replace(' ', '+'))
        variations.append(original_payload.replace(' ', '%20'))
        
        # Database-specific variations
        if db_type == DatabaseType.MYSQL:
            variations.extend([
                original_payload.replace("'", "\\'"),
                original_payload.replace("'", "\\\\'"),
                original_payload.replace('"', '\\"'),
                original_payload.replace('"', '\\\\"')
            ])
        elif db_type == DatabaseType.POSTGRESQL:
            variations.extend([
                original_payload.replace("'", "''"),
                original_payload.replace('"', '""')
            ])
        elif db_type == DatabaseType.MSSQL:
            variations.extend([
                original_payload.replace("'", "''"),
                original_payload.replace('"', '""')
            ])
        
        # Random string variations (for testing injection consistency)
        random_strings = ['test123', 'abc456', 'xyz789']
        for rand_str in random_strings:
            if "'" in original_payload:
                variations.append(original_payload.replace("'", f"'{rand_str}"))
            if '"' in original_payload:
                variations.append(original_payload.replace('"', f'"{rand_str}"'))
        
        return list(set(variations))  # Remove duplicates

class ConsistencyChecker:
    """Checks for consistent behavior across multiple requests"""
    
    def __init__(self, session: requests.Session, timeout: int = 30):
        self.session = session
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def check_consistency(self, url: str, parameter: str, payloads: List[str], 
                         expected_behavior: str) -> Tuple[bool, List[str]]:
        """Check if vulnerability behavior is consistent across payloads"""
        results = []
        consistent_count = 0
        
        for payload in payloads:
            try:
                response = self._send_payload(url, parameter, payload)
                if not response:
                    continue
                
                behavior = self._analyze_behavior(response, expected_behavior)
                results.append(behavior)
                
                if behavior['matches']:
                    consistent_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error in consistency check: {e}")
                continue
        
        # Consider consistent if at least 70% of payloads show expected behavior
        consistency_ratio = consistent_count / len(payloads) if payloads else 0
        is_consistent = consistency_ratio >= 0.7
        
        evidence = [f"Consistency ratio: {consistency_ratio:.2f}"]
        evidence.extend([r['evidence'] for r in results if r['evidence']])
        
        return is_consistent, evidence
    
    def _send_payload(self, url: str, parameter: str, payload: str) -> Optional[requests.Response]:
        """Send payload and return response"""
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Replace parameter value with payload
            params[parameter] = [payload]
            
            # Reconstruct URL with payload
            query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            
            response = self.session.get(test_url, timeout=self.timeout)
            return response
            
        except Exception as e:
            self.logger.error(f"Error sending payload: {e}")
            return None
    
    def _analyze_behavior(self, response: requests.Response, expected_behavior: str) -> Dict[str, Any]:
        """Analyze response behavior"""
        behavior = {
            'matches': False,
            'evidence': '',
            'response_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
            'status_code': response.status_code,
            'content_length': len(response.content)
        }
        
        response_text = response.text.lower()
        
        if expected_behavior == 'sql_error':
            # Check for SQL errors
            sql_error_patterns = [
                r"sql syntax",
                r"mysql_fetch",
                r"pg_query",
                r"microsoft ole db",
                r"ora-\d{5}",
                r"sqlite"
            ]
            
            for pattern in sql_error_patterns:
                if re.search(pattern, response_text):
                    behavior['matches'] = True
                    behavior['evidence'] = f"SQL error pattern found: {pattern}"
                    break
        
        elif expected_behavior == 'time_delay':
            # Check for time delay
            if behavior['response_time'] > 3.0:
                behavior['matches'] = True
                behavior['evidence'] = f"Time delay detected: {behavior['response_time']:.2f}s"
        
        elif expected_behavior == 'boolean_difference':
            # This would require baseline comparison
            # For simplicity, we'll check for significant content changes
            if len(response_text) > 100:  # Basic heuristic
                behavior['matches'] = True
                behavior['evidence'] = "Content modification detected"
        
        return behavior

class VulnerabilityVerifier:
    """Main verification engine"""
    
    def __init__(self, session: requests.Session, timeout: int = 30):
        self.session = session
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.fp_detector = FalsePositiveDetector()
        self.variator = PayloadVariator()
        self.consistency_checker = ConsistencyChecker(session, timeout)
    
    def verify_vulnerability(self, vulnerability: Vulnerability) -> VerificationResult:
        """Verify a vulnerability and reduce false positives"""
        self.logger.info(f"Verifying vulnerability: {vulnerability.url} - {vulnerability.parameter}")
        
        verification_tests = []
        evidence = []
        false_positive_indicators = []
        confidence = vulnerability.confidence
        
        # Test 1: False positive detection
        fp_indicators = self._test_false_positive(vulnerability)
        false_positive_indicators.extend(fp_indicators)
        verification_tests.append("False positive detection")
        
        # Test 2: Payload variation consistency
        consistency_result = self._test_payload_consistency(vulnerability)
        evidence.extend(consistency_result['evidence'])
        verification_tests.append("Payload variation consistency")
        
        # Test 3: Re-test with original payload
        retest_result = self._retest_original_payload(vulnerability)
        evidence.extend(retest_result['evidence'])
        verification_tests.append("Original payload retest")
        
        # Test 4: Different injection technique verification
        technique_result = self._test_different_techniques(vulnerability)
        evidence.extend(technique_result['evidence'])
        verification_tests.append("Different injection techniques")
        
        # Calculate final confidence and status
        final_confidence = self._calculate_confidence(
            confidence, fp_indicators, consistency_result, retest_result, technique_result
        )
        
        status = self._determine_status(final_confidence, false_positive_indicators)
        
        return VerificationResult(
            vulnerability=vulnerability,
            status=status,
            confidence=final_confidence,
            verification_tests=verification_tests,
            evidence=evidence,
            false_positive_indicators=false_positive_indicators
        )
    
    def _test_false_positive(self, vulnerability: Vulnerability) -> List[str]:
        """Test for false positive indicators"""
        indicators = []
        
        # Get response with original payload
        response = self._send_payload(vulnerability.url, vulnerability.parameter, vulnerability.payload)
        if response:
            indicators = self.fp_detector.check_false_positive(response.text, vulnerability.payload)
        
        return indicators
    
    def _test_payload_consistency(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """Test consistency across payload variations"""
        variations = self.variator.generate_variations(vulnerability.payload, vulnerability.database_type)
        
        # Determine expected behavior based on injection type
        expected_behavior = {
            InjectionType.ERROR_BASED: 'sql_error',
            InjectionType.TIME_BASED: 'time_delay',
            InjectionType.BOOLEAN_BASED: 'boolean_difference',
            InjectionType.UNION_BASED: 'boolean_difference'
        }.get(vulnerability.injection_type, 'sql_error')
        
        is_consistent, evidence = self.consistency_checker.check_consistency(
            vulnerability.url, vulnerability.parameter, variations, expected_behavior
        )
        
        return {
            'consistent': is_consistent,
            'evidence': evidence
        }
    
    def _retest_original_payload(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """Retest with original payload multiple times"""
        evidence = []
        success_count = 0
        total_tests = 3
        
        for i in range(total_tests):
            try:
                response = self._send_payload(vulnerability.url, vulnerability.parameter, vulnerability.payload)
                if response and self._confirm_vulnerability_in_response(response, vulnerability):
                    success_count += 1
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                self.logger.error(f"Error in retest {i+1}: {e}")
        
        success_rate = success_count / total_tests
        evidence.append(f"Retest success rate: {success_rate:.2f} ({success_count}/{total_tests})")
        
        return {
            'success_rate': success_rate,
            'evidence': evidence
        }
    
    def _test_different_techniques(self, vulnerability: Vulnerability) -> Dict[str, Any]:
        """Test with different injection techniques"""
        evidence = []
        alternative_payloads = []
        
        # Generate alternative payloads based on injection type
        if vulnerability.injection_type == InjectionType.ERROR_BASED:
            alternative_payloads = [
                "' OR 1=1 -- ",
                "' AND 1=1 -- ",
                "' AND 1=2 -- ",
                "' UNION SELECT 1,2,3 -- "
            ]
        elif vulnerability.injection_type == InjectionType.BOOLEAN_BASED:
            alternative_payloads = [
                "' AND 1=1 -- ",
                "' AND 1=2 -- ",
                "' AND (SELECT 1)=1 -- "
            ]
        elif vulnerability.injection_type == InjectionType.TIME_BASED:
            alternative_payloads = [
                "' AND SLEEP(3) -- ",
                "' AND (SELECT SLEEP(3)) -- ",
                "'; WAITFOR DELAY '00:00:03' -- "
            ]
        
        success_count = 0
        for payload in alternative_payloads:
            try:
                response = self._send_payload(vulnerability.url, vulnerability.parameter, payload)
                if response and self._confirm_vulnerability_in_response(response, vulnerability):
                    success_count += 1
                    evidence.append(f"Alternative payload successful: {payload}")
            except Exception as e:
                self.logger.error(f"Error testing alternative payload {payload}: {e}")
        
        evidence.append(f"Alternative technique success rate: {success_count}/{len(alternative_payloads)}")
        
        return {
            'success_count': success_count,
            'total_alternatives': len(alternative_payloads),
            'evidence': evidence
        }
    
    def _send_payload(self, url: str, parameter: str, payload: str) -> Optional[requests.Response]:
        """Send payload and return response"""
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Replace parameter value with payload
            params[parameter] = [payload]
            
            # Reconstruct URL with payload
            query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            
            response = self.session.get(test_url, timeout=self.timeout)
            return response
            
        except Exception as e:
            self.logger.error(f"Error sending payload: {e}")
            return None
    
    def _confirm_vulnerability_in_response(self, response: requests.Response, 
                                          vulnerability: Vulnerability) -> bool:
        """Confirm vulnerability in response"""
        response_text = response.text.lower()
        
        if vulnerability.injection_type == InjectionType.ERROR_BASED:
            # Check for SQL errors
            sql_error_patterns = [
                r"sql syntax",
                r"mysql_fetch",
                r"pg_query",
                r"microsoft ole db",
                r"ora-\d{5}"
            ]
            return any(re.search(pattern, response_text) for pattern in sql_error_patterns)
        
        elif vulnerability.injection_type == InjectionType.TIME_BASED:
            # Check for time delay
            if hasattr(response, 'elapsed'):
                return response.elapsed.total_seconds() > 3.0
        
        elif vulnerability.injection_type in [InjectionType.BOOLEAN_BASED, InjectionType.UNION_BASED]:
            # Check for content modification (basic heuristic)
            return len(response_text) > 100
        
        return False
    
    def _calculate_confidence(self, original_confidence: float, fp_indicators: List[str],
                            consistency_result: Dict, retest_result: Dict, 
                            technique_result: Dict) -> float:
        """Calculate final confidence score"""
        confidence = original_confidence
        
        # Reduce confidence based on false positive indicators
        confidence -= len(fp_indicators) * 0.1
        
        # Increase confidence based on consistency
        if consistency_result.get('consistent', False):
            confidence += 0.2
        
        # Increase confidence based on retest success
        retest_success = retest_result.get('success_rate', 0)
        confidence += retest_success * 0.1
        
        # Increase confidence based on alternative techniques
        technique_success = technique_result.get('success_count', 0) / max(technique_result.get('total_alternatives', 1), 1)
        confidence += technique_success * 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _determine_status(self, confidence: float, false_positive_indicators: List[str]) -> VerificationStatus:
        """Determine verification status based on confidence and indicators"""
        if confidence >= 0.8 and len(false_positive_indicators) == 0:
            return VerificationStatus.CONFIRMED
        elif confidence >= 0.6 and len(false_positive_indicators) <= 1:
            return VerificationStatus.LIKELY
        elif confidence >= 0.4:
            return VerificationStatus.POSSIBLE
        else:
            return VerificationStatus.FALSE_POSITIVE
