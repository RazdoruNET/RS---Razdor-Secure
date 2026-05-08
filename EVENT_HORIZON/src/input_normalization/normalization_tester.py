"""
Input Normalization Tester

Tests how WAF/proxy/app normalize input and checks consistency
across the parsing chain without offensive tamper automation.
"""

import re
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import unicodedata


class NormalizationType(Enum):
    """Types of input normalization to test."""
    CASE_NORMALIZATION = "case_normalization"
    WHITESPACE_NORMALIZATION = "whitespace_normalization"
    UTF8_NORMALIZATION = "utf8_normalization"
    URL_ENCODING_NORMALIZATION = "url_encoding_normalization"
    DUPLICATE_HEADER_NORMALIZATION = "duplicate_header_normalization"
    CHARACTER_SET_NORMALIZATION = "character_set_normalization"


@dataclass
class NormalizationTest:
    """Represents a single normalization test."""
    test_name: str
    input_data: str
    expected_normalizations: List[str]
    test_type: NormalizationType
    safe_variants: List[str]


@dataclass
class NormalizationResult:
    """Result of a normalization test."""
    test_name: str
    input_data: str
    normalized_output: str
    expected_outputs: List[str]
    is_consistent: bool
    inconsistency_details: Optional[str]
    test_type: NormalizationType


class InputNormalizationTester:
    """
    Tests input normalization across different layers (WAF, proxy, application)
    to identify inconsistencies and parsing chain issues.
    """
    
    def __init__(self):
        self.test_cases = self._generate_test_cases()
        self.results: List[NormalizationResult] = []
        
    def _generate_test_cases(self) -> List[NormalizationTest]:
        """Generate safe test cases for normalization testing."""
        test_cases = []
        
        # Case normalization tests
        test_cases.extend([
            NormalizationTest(
                test_name="mixed_case_username",
                input_data="Admin",
                expected_normalizations=["admin", "Admin", "ADMIN"],
                test_type=NormalizationType.CASE_NORMALIZATION,
                safe_variants=["admin", "Admin", "ADMIN", "aDmIn"]
            ),
            NormalizationTest(
                test_name="mixed_case_email",
                input_data="Test@Example.COM",
                expected_normalizations=["test@example.com", "Test@example.com", "test@example.COM"],
                test_type=NormalizationType.CASE_NORMALIZATION,
                safe_variants=["test@example.com", "Test@Example.COM", "TEST@EXAMPLE.COM"]
            ),
            NormalizationTest(
                test_name="mixed_case_parameter",
                input_data="Action=Login",
                expected_normalizations=["action=login", "Action=Login", "action=Login"],
                test_type=NormalizationType.CASE_NORMALIZATION,
                safe_variants=["action=login", "Action=Login", "ACTION=login"]
            )
        ])
        
        # Whitespace normalization tests
        test_cases.extend([
            NormalizationTest(
                test_name="leading_whitespace",
                input_data="  username",
                expected_normalizations=["username", " username"],
                test_type=NormalizationType.WHITESPACE_NORMALIZATION,
                safe_variants=["username", " username", "  username", "\tusername"]
            ),
            NormalizationTest(
                test_name="trailing_whitespace",
                input_data="username  ",
                expected_normalizations=["username", "username "],
                test_type=NormalizationType.WHITESPACE_NORMALIZATION,
                safe_variants=["username", "username ", "username\t", "username  "]
            ),
            NormalizationTest(
                test_name="multiple_spaces",
                input_data="user  name",
                expected_normalizations=["user name", "user  name"],
                test_type=NormalizationType.WHITESPACE_NORMALIZATION,
                safe_variants=["user name", "user  name", "user\tname", "user   name"]
            ),
            NormalizationTest(
                test_name="tab_whitespace",
                input_data="user\tname",
                expected_normalizations=["user name", "user\tname"],
                test_type=NormalizationType.WHITESPACE_NORMALIZATION,
                safe_variants=["user name", "user\tname", "user\t\tname"]
            ),
            NormalizationTest(
                test_name="newline_whitespace",
                input_data="user\nname",
                expected_normalizations=["user name", "user\nname"],
                test_type=NormalizationType.WHITESPACE_NORMALIZATION,
                safe_variants=["user name", "user\nname", "user\r\nname"]
            )
        ])
        
        # UTF-8 normalization tests
        test_cases.extend([
            NormalizationTest(
                test_name="accented_characters",
                input_data="café",
                expected_normalizations=["café", "cafe", "café"],
                test_type=NormalizationType.UTF8_NORMALIZATION,
                safe_variants=["café", "cafe", "café"]
            ),
            NormalizationTest(
                test_name="unicode_normalization",
                input_data="𝔘𝔫𝔦𝔠𝔬𝔡𝔢",
                expected_normalizations=["Unicode", "𝔘𝔫𝔦𝔠𝔬𝔡𝔢"],
                test_type=NormalizationType.UTF8_NORMALIZATION,
                safe_variants=["Unicode", "𝔘𝔫𝔦𝔠𝔬𝔡𝔢", "unicode"]
            ),
            NormalizationTest(
                test_name="zero_width_characters",
                input_data="user\u200bname",
                expected_normalizations=["username", "user\u200bname"],
                test_type=NormalizationType.UTF8_NORMALIZATION,
                safe_variants=["username", "user\u200bname", "user\u200cname"]
            )
        ])
        
        # URL encoding normalization tests
        test_cases.extend([
            NormalizationTest(
                test_name="basic_url_encoding",
                input_data="user%20name",
                expected_normalizations=["user name", "user%20name"],
                test_type=NormalizationType.URL_ENCODING_NORMALIZATION,
                safe_variants=["user name", "user%20name", "user+name"]
            ),
            NormalizationTest(
                test_name="double_encoding",
                input_data="user%2520name",
                expected_normalizations=["user%20name", "user name"],
                test_type=NormalizationType.URL_ENCODING_NORMALIZATION,
                safe_variants=["user%20name", "user name", "user%2520name"]
            ),
            NormalizationTest(
                test_name="mixed_case_encoding",
                input_data="User%20Name",
                expected_normalizations=["User Name", "User%20Name"],
                test_type=NormalizationType.URL_ENCODING_NORMALIZATION,
                safe_variants=["User Name", "User%20Name", "user%20name"]
            ),
            NormalizationTest(
                test_name="special_characters_encoding",
                input_data="test%40example.com",
                expected_normalizations=["test@example.com", "test%40example.com"],
                test_type=NormalizationType.URL_ENCODING_NORMALIZATION,
                safe_variants=["test@example.com", "test%40example.com", "test%2540example.com"]
            )
        ])
        
        # Duplicate header tests
        test_cases.extend([
            NormalizationTest(
                test_name="duplicate_content_type",
                input_data="application/json",
                expected_normalizations=["application/json"],
                test_type=NormalizationType.DUPLICATE_HEADER_NORMALIZATION,
                safe_variants=["application/json", "text/html", "application/xml"]
            ),
            NormalizationTest(
                test_name="duplicate_authorization",
                input_data="Bearer token123",
                expected_normalizations=["Bearer token123"],
                test_type=NormalizationType.DUPLICATE_HEADER_NORMALIZATION,
                safe_variants=["Bearer token123", "Basic token123"]
            )
        ])
        
        # Character set normalization tests
        test_cases.extend([
            NormalizationTest(
                test_name="cyrillic_characters",
                input_data="пользователь",
                expected_normalizations=["пользователь"],
                test_type=NormalizationType.CHARACTER_SET_NORMALIZATION,
                safe_variants=["пользователь", "polzovatel"]
            ),
            NormalizationTest(
                test_name="chinese_characters",
                input_data="用户",
                expected_normalizations=["用户"],
                test_type=NormalizationType.CHARACTER_SET_NORMALIZATION,
                safe_variants=["用户", "user"]
            ),
            NormalizationTest(
                test_name="emoji_characters",
                input_data="user🔒name",
                expected_normalizations=["user🔒name", "username"],
                test_type=NormalizationType.CHARACTER_SET_NORMALIZATION,
                safe_variants=["user🔒name", "username", "userlockname"]
            )
        ])
        
        return test_cases
    
    def normalize_payload(self, payload: str, normalization_type: NormalizationType) -> str:
        """
        Apply specific normalization to payload.
        
        Args:
            payload: Input payload to normalize
            normalization_type: Type of normalization to apply
            
        Returns:
            Normalized payload
        """
        if normalization_type == NormalizationType.CASE_NORMALIZATION:
            return self._normalize_case(payload)
        elif normalization_type == NormalizationType.WHITESPACE_NORMALIZATION:
            return self._normalize_whitespace(payload)
        elif normalization_type == NormalizationType.UTF8_NORMALIZATION:
            return self._normalize_utf8(payload)
        elif normalization_type == NormalizationType.URL_ENCODING_NORMALIZATION:
            return self._normalize_url_encoding(payload)
        elif normalization_type == NormalizationType.DUPLICATE_HEADER_NORMALIZATION:
            return self._normalize_duplicate_headers(payload)
        elif normalization_type == NormalizationType.CHARACTER_SET_NORMALIZATION:
            return self._normalize_character_set(payload)
        
        return payload
    
    def _normalize_case(self, payload: str) -> str:
        """Apply case normalization."""
        # Try different case normalization strategies
        strategies = [
            str.lower,
            str.upper,
            str.capitalize,
            lambda x: x  # No change
        ]
        
        # For testing, return lowercase as most common normalization
        return payload.lower()
    
    def _normalize_whitespace(self, payload: str) -> str:
        """Apply whitespace normalization."""
        # Strip leading/trailing whitespace
        normalized = payload.strip()
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Replace tabs with spaces
        normalized = normalized.replace('\t', ' ')
        
        # Replace newlines with spaces
        normalized = normalized.replace('\n', ' ').replace('\r', ' ')
        
        return normalized
    
    def _normalize_utf8(self, payload: str) -> str:
        """Apply UTF-8 normalization."""
        # Apply Unicode normalization (NFC - canonical composition)
        normalized = unicodedata.normalize('NFC', payload)
        
        # Remove zero-width characters
        normalized = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff]', '', normalized)
        
        return normalized
    
    def _normalize_url_encoding(self, payload: str) -> str:
        """Apply URL encoding normalization."""
        try:
            # Decode URL encoding
            decoded = urllib.parse.unquote(payload)
            
            # Re-encode to ensure consistent format
            re_encoded = urllib.parse.quote(decoded, safe=' ')
            
            # Replace %20 with + for spaces (common in query parameters)
            re_encoded = re_encoded.replace('%20', '+')
            
            return re_encoded
        except Exception:
            return payload
    
    def _normalize_duplicate_headers(self, payload: str) -> str:
        """Handle duplicate header normalization."""
        # For simple payload testing, return as-is
        # In practice, this would handle HTTP header merging
        return payload
    
    def _normalize_character_set(self, payload: str) -> str:
        """Apply character set normalization."""
        try:
            # Convert to UTF-8 and back to ensure consistent encoding
            encoded = payload.encode('utf-8', errors='ignore')
            decoded = encoded.decode('utf-8', errors='ignore')
            return decoded
        except Exception:
            return payload
    
    async def run_normalization_test(self, test_case: NormalizationTest, 
                                   response_data: Dict) -> NormalizationResult:
        """
        Run a single normalization test.
        
        Args:
            test_case: Test case to run
            response_data: Response data from the system
            
        Returns:
            Normalization result
        """
        # Extract normalized output from response
        normalized_output = self._extract_normalized_value(response_data)
        
        # Check if output is consistent with expected normalizations
        is_consistent = normalized_output in test_case.expected_normalizations
        
        # Determine inconsistency details
        inconsistency_details = None
        if not is_consistent:
            inconsistency_details = f"Expected one of {test_case.expected_normalizations}, got '{normalized_output}'"
        
        result = NormalizationResult(
            test_name=test_case.test_name,
            input_data=test_case.input_data,
            normalized_output=normalized_output,
            expected_outputs=test_case.expected_normalizations,
            is_consistent=is_consistent,
            inconsistency_details=inconsistency_details,
            test_type=test_case.test_type
        )
        
        self.results.append(result)
        return result
    
    def _extract_normalized_value(self, response_data: Dict) -> str:
        """Extract normalized value from response data."""
        # Try different extraction methods
        body = response_data.get("body", "")
        
        # Look for JSON responses
        if response_data.get("headers", {}).get("content-type", "").startswith("application/json"):
            try:
                import json
                json_data = json.loads(body)
                # Look for common fields that might contain normalized data
                for field in ["normalized", "result", "output", "value", "data"]:
                    if field in json_data:
                        return str(json_data[field])
            except:
                pass
        
        # Look for form responses
        if "form" in body.lower():
            # Extract form values
            form_matches = re.findall(r'name="([^"]+)"\s*value="([^"]*)"', body)
            if form_matches:
                return form_matches[0][1]  # Return first form value
        
        # Return body as fallback
        return body.strip()
    
    async def run_all_tests(self, response_generator) -> List[NormalizationResult]:
        """
        Run all normalization tests.
        
        Args:
            response_generator: Function that generates responses for test inputs
            
        Returns:
            List of all test results
        """
        results = []
        
        for test_case in self.test_cases:
            # Generate response for test input
            response_data = await response_generator(test_case.input_data)
            
            # Run the test
            result = await self.run_normalization_test(test_case, response_data)
            results.append(result)
        
        return results
    
    def analyze_consistency(self, results: List[NormalizationResult] = None) -> Dict[str, Any]:
        """
        Analyze consistency across normalization tests.
        
        Args:
            results: List of test results (uses self.results if None)
            
        Returns:
            Consistency analysis
        """
        if results is None:
            results = self.results
        
        analysis = {
            "total_tests": len(results),
            "consistent_tests": sum(1 for r in results if r.is_consistent),
            "inconsistent_tests": sum(1 for r in results if not r.is_consistent),
            "consistency_rate": 0.0,
            "inconsistencies_by_type": {},
            "detailed_inconsistencies": []
        }
        
        if analysis["total_tests"] > 0:
            analysis["consistency_rate"] = analysis["consistent_tests"] / analysis["total_tests"]
        
        # Group inconsistencies by type
        for result in results:
            if not result.is_consistent:
                test_type = result.test_type.value
                if test_type not in analysis["inconsistencies_by_type"]:
                    analysis["inconsistencies_by_type"][test_type] = 0
                analysis["inconsistencies_by_type"][test_type] += 1
                
                analysis["detailed_inconsistencies"].append({
                    "test_name": result.test_name,
                    "input": result.input_data,
                    "output": result.normalized_output,
                    "expected": result.expected_outputs,
                    "details": result.inconsistency_details
                })
        
        return analysis
    
    def generate_test_variants(self, base_input: str, test_type: NormalizationType, 
                             count: int = 5) -> List[str]:
        """
        Generate test variants for a specific input and test type.
        
        Args:
            base_input: Base input to generate variants from
            test_type: Type of normalization test
            count: Number of variants to generate
            
        Returns:
            List of input variants
        """
        variants = []
        
        if test_type == NormalizationType.CASE_NORMALIZATION:
            variants.extend([
                base_input.lower(),
                base_input.upper(),
                base_input.capitalize(),
                base_input.swapcase(),
                base_input  # Original
            ])
        
        elif test_type == NormalizationType.WHITESPACE_NORMALIZATION:
            variants.extend([
                f"  {base_input}",
                f"{base_input}  ",
                f" {base_input} ",
                f"{base_input}\t{base_input}",
                f"{base_input}\n{base_input}",
                base_input
            ])
        
        elif test_type == NormalizationType.UTF8_NORMALIZATION:
            variants.extend([
                base_input,
                unicodedata.normalize('NFC', base_input),
                unicodedata.normalize('NFD', base_input),
                unicodedata.normalize('NFKC', base_input),
                unicodedata.normalize('NFKD', base_input)
            ])
        
        elif test_type == NormalizationType.URL_ENCODING_NORMALIZATION:
            variants.extend([
                urllib.parse.quote(base_input),
                urllib.parse.quote_plus(base_input),
                urllib.parse.quote(base_input, safe=''),
                urllib.parse.unquote(base_input),
                base_input
            ])
        
        # Return requested number of variants
        return variants[:count]
    
    def create_comprehensive_report(self) -> Dict[str, Any]:
        """Create a comprehensive report of all normalization tests."""
        analysis = self.analyze_consistency()
        
        report = {
            "summary": analysis,
            "test_coverage": {
                "case_normalization_tests": len([t for t in self.test_cases if t.test_type == NormalizationType.CASE_NORMALIZATION]),
                "whitespace_normalization_tests": len([t for t in self.test_cases if t.test_type == NormalizationType.WHITESPACE_NORMALIZATION]),
                "utf8_normalization_tests": len([t for t in self.test_cases if t.test_type == NormalizationType.UTF8_NORMALIZATION]),
                "url_encoding_normalization_tests": len([t for t in self.test_cases if t.test_type == NormalizationType.URL_ENCODING_NORMALIZATION]),
                "duplicate_header_tests": len([t for t in self.test_cases if t.test_type == NormalizationType.DUPLICATE_HEADER_NORMALIZATION]),
                "character_set_tests": len([t for t in self.test_cases if t.test_type == NormalizationType.CHARACTER_SET_NORMALIZATION])
            },
            "recommendations": self._generate_recommendations(analysis),
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "test_type": r.test_type.value,
                    "input": r.input_data,
                    "output": r.normalized_output,
                    "consistent": r.is_consistent,
                    "expected": r.expected_outputs
                }
                for r in self.results
            ]
        }
        
        return report
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        if analysis["consistency_rate"] < 0.8:
            recommendations.append("Low consistency rate detected. Review normalization pipeline.")
        
        # Check for specific inconsistency patterns
        inconsistencies = analysis["inconsistencies_by_type"]
        
        if "case_normalization" in inconsistencies and inconsistencies["case_normalization"] > 0:
            recommendations.append("Case normalization inconsistencies found. Ensure consistent case handling across all components.")
        
        if "whitespace_normalization" in inconsistencies and inconsistencies["whitespace_normalization"] > 0:
            recommendations.append("Whitespace normalization inconsistencies found. Implement consistent whitespace handling.")
        
        if "utf8_normalization" in inconsistencies and inconsistencies["utf8_normalization"] > 0:
            recommendations.append("UTF-8 normalization inconsistencies found. Ensure proper Unicode normalization.")
        
        if "url_encoding_normalization" in inconsistencies and inconsistencies["url_encoding_normalization"] > 0:
            recommendations.append("URL encoding inconsistencies found. Standardize URL encoding/decoding across components.")
        
        if analysis["inconsistent_tests"] == 0:
            recommendations.append("All normalization tests passed. System shows consistent normalization behavior.")
        
        return recommendations
