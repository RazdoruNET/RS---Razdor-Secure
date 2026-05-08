"""
Encoding Analyzer

Analyzes different encoding schemes and their handling across
the parsing chain to identify inconsistencies.
"""

import base64
import binascii
import urllib.parse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json


class EncodingType(Enum):
    """Types of encoding to analyze."""
    BASE64 = "base64"
    URL_ENCODING = "url_encoding"
    HTML_ENCODING = "html_encoding"
    HEX_ENCODING = "hex_encoding"
    BINARY_ENCODING = "binary_encoding"
    UNICODE_ESCAPE = "unicode_escape"


@dataclass
class EncodingTest:
    """Represents an encoding test."""
    test_name: str
    original_data: str
    encoding_type: EncodingType
    expected_behavior: str
    safe_variants: List[str]


@dataclass
class EncodingResult:
    """Result of encoding analysis."""
    test_name: str
    original_data: str
    encoded_data: Optional[str]
    decoded_data: Optional[str]
    encoding_successful: bool
    decoding_successful: bool
    roundtrip_successful: bool
    error_message: Optional[str]
    encoding_type: EncodingType


class EncodingAnalyzer:
    """
    Analyzes different encoding schemes and their handling
    across the parsing chain.
    """
    
    def __init__(self):
        self.test_cases = self._generate_test_cases()
        self.results: List[EncodingResult] = []
    
    def _generate_test_cases(self) -> List[EncodingTest]:
        """Generate encoding test cases."""
        test_cases = []
        
        # Base64 tests
        test_cases.extend([
            EncodingTest(
                test_name="base64_basic_text",
                original_data="Hello World",
                encoding_type=EncodingType.BASE64,
                expected_behavior="perfect_roundtrip",
                safe_variants=["Hello World", "Test123", "API_KEY"]
            ),
            EncodingTest(
                test_name="base64_with_special_chars",
                original_data="user@domain.com",
                encoding_type=EncodingType.BASE64,
                expected_behavior="perfect_roundtrip",
                safe_variants=["user@domain.com", "test+tag@example.org", "user.name@company.co.uk"]
            ),
            EncodingTest(
                test_name="base64_unicode",
                original_data="café résumé",
                encoding_type=EncodingType.BASE64,
                expected_behavior="perfect_roundtrip",
                safe_variants=["café", "résumé", "naïve"]
            ),
            EncodingTest(
                test_name="base64_json_data",
                original_data='{"user": "admin", "role": "test"}',
                encoding_type=EncodingType.BASE64,
                expected_behavior="perfect_roundtrip",
                safe_variants=['{"status": "ok"}', '{"error": "none"}', '{"data": "test"}']
            )
        ])
        
        # URL encoding tests
        test_cases.extend([
            EncodingTest(
                test_name="url_basic_params",
                original_data="user=admin&pass=test",
                encoding_type=EncodingType.URL_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["user=admin", "id=123", "action=login"]
            ),
            EncodingTest(
                test_name="url_with_spaces",
                original_data="search query with spaces",
                encoding_type=EncodingType.URL_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["hello world", "test query", "search term"]
            ),
            EncodingTest(
                test_name="url_with_special_chars",
                original_data="email=test@domain.com",
                encoding_type=EncodingType.URL_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["email=user@site.org", "url=https://example.com", "path=/api/v1"]
            ),
            EncodingTest(
                test_name="url_unicode_chars",
                original_data="query=café",
                encoding_type=EncodingType.URL_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["query=résumé", "name=naïve", "title=café"]
            )
        ])
        
        # HTML encoding tests
        test_cases.extend([
            EncodingTest(
                test_name="html_basic_entities",
                original_data="<div>Hello</div>",
                encoding_type=EncodingType.HTML_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["<p>test</p>", "<span>data</span>", "<h1>title</h1>"]
            ),
            EncodingTest(
                test_name="html_special_chars",
                original_data="a & b > c < d",
                encoding_type=EncodingType.HTML_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["x & y", "a > b", "c < d"]
            ),
            EncodingTest(
                test_name="html_quotes",
                original_data='class="test" id=\'sample\'',
                encoding_type=EncodingType.HTML_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=['class="main"', 'id="test"', 'type="submit"']
            )
        ])
        
        # Hex encoding tests
        test_cases.extend([
            EncodingTest(
                test_name="hex_basic_text",
                original_data="Hello",
                encoding_type=EncodingType.HEX_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["Test", "Data", "User"]
            ),
            EncodingTest(
                test_name="hex_numeric_data",
                original_data="12345",
                encoding_type=EncodingType.HEX_ENCODING,
                expected_behavior="perfect_roundtrip",
                safe_variants=["67890", "123", "456"]
            )
        ])
        
        # Unicode escape tests
        test_cases.extend([
            EncodingTest(
                test_name="unicode_escape_basic",
                original_data="café",
                encoding_type=EncodingType.UNICODE_ESCAPE,
                expected_behavior="perfect_roundtrip",
                safe_variants=["résumé", "naïve", "señor"]
            ),
            EncodingTest(
                test_name="unicode_escape_special",
                original_data="Hello\tWorld\nTest",
                encoding_type=EncodingType.UNICODE_ESCAPE,
                expected_behavior="perfect_roundtrip",
                safe_variants=["Tab\tSeparated", "Line\nBreak", "Quote\"Test"]
            )
        ])
        
        return test_cases
    
    def encode_data(self, data: str, encoding_type: EncodingType) -> Tuple[Optional[str], Optional[str]]:
        """
        Encode data using specified encoding type.
        
        Args:
            data: Data to encode
            encoding_type: Type of encoding to use
            
        Returns:
            Tuple of (encoded_data, error_message)
        """
        try:
            if encoding_type == EncodingType.BASE64:
                encoded = base64.b64encode(data.encode('utf-8')).decode('ascii')
            
            elif encoding_type == EncodingType.URL_ENCODING:
                encoded = urllib.parse.quote(data)
            
            elif encoding_type == EncodingType.HTML_ENCODING:
                # Basic HTML encoding
                encoded = data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
            
            elif encoding_type == EncodingType.HEX_ENCODING:
                encoded = data.encode('utf-8').hex()
            
            elif encoding_type == EncodingType.UNICODE_ESCAPE:
                encoded = data.encode('unicode_escape').decode('ascii')
            
            elif encoding_type == EncodingType.BINARY_ENCODING:
                encoded = ' '.join(format(ord(c), '08b') for c in data)
            
            else:
                return None, f"Unsupported encoding type: {encoding_type}"
            
            return encoded, None
        
        except Exception as e:
            return None, f"Encoding error: {e}"
    
    def decode_data(self, data: str, encoding_type: EncodingType) -> Tuple[Optional[str], Optional[str]]:
        """
        Decode data using specified encoding type.
        
        Args:
            data: Data to decode
            encoding_type: Type of encoding to use
            
        Returns:
            Tuple of (decoded_data, error_message)
        """
        try:
            if encoding_type == EncodingType.BASE64:
                decoded = base64.b64decode(data.encode('ascii')).decode('utf-8')
            
            elif encoding_type == EncodingType.URL_ENCODING:
                decoded = urllib.parse.unquote(data)
            
            elif encoding_type == EncodingType.HTML_ENCODING:
                # Basic HTML decoding
                decoded = data.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#x27;', "'")
            
            elif encoding_type == EncodingType.HEX_ENCODING:
                decoded = bytes.fromhex(data).decode('utf-8')
            
            elif encoding_type == EncodingType.UNICODE_ESCAPE:
                decoded = data.encode('ascii').decode('unicode_escape')
            
            elif encoding_type == EncodingType.BINARY_ENCODING:
                # Convert binary string back to text
                binary_values = data.split()
                decoded = ''.join(chr(int(b, 2)) for b in binary_values)
            
            else:
                return None, f"Unsupported encoding type: {encoding_type}"
            
            return decoded, None
        
        except Exception as e:
            return None, f"Decoding error: {e}"
    
    async def run_encoding_test(self, test_case: EncodingTest) -> EncodingResult:
        """
        Run a single encoding test.
        
        Args:
            test_case: Test case to run
            
        Returns:
            Encoding test result
        """
        # Encode the data
        encoded_data, encode_error = self.encode_data(test_case.original_data, test_case.encoding_type)
        encoding_successful = encoded_data is not None
        
        # Decode the data if encoding was successful
        decoded_data = None
        decoding_successful = False
        roundtrip_successful = False
        error_message = encode_error
        
        if encoded_data is not None:
            decoded_data, decode_error = self.decode_data(encoded_data, test_case.encoding_type)
            decoding_successful = decoded_data is not None
            
            if decoded_data is not None:
                roundtrip_successful = decoded_data == test_case.original_data
            
            if decode_error:
                error_message = decode_error
        
        result = EncodingResult(
            test_name=test_case.test_name,
            original_data=test_case.original_data,
            encoded_data=encoded_data,
            decoded_data=decoded_data,
            encoding_successful=encoding_successful,
            decoding_successful=decoding_successful,
            roundtrip_successful=roundtrip_successful,
            error_message=error_message,
            encoding_type=test_case.encoding_type
        )
        
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> List[EncodingResult]:
        """Run all encoding tests."""
        results = []
        
        for test_case in self.test_cases:
            result = await self.run_encoding_test(test_case)
            results.append(result)
        
        return results
    
    def analyze_encoding_consistency(self, results: List[EncodingResult] = None) -> Dict[str, Any]:
        """
        Analyze encoding consistency across tests.
        
        Args:
            results: List of test results (uses self.results if None)
            
        Returns:
            Consistency analysis
        """
        if results is None:
            results = self.results
        
        analysis = {
            "total_tests": len(results),
            "successful_encodings": sum(1 for r in results if r.encoding_successful),
            "successful_decodings": sum(1 for r in results if r.decoding_successful),
            "successful_roundtrips": sum(1 for r in results if r.roundtrip_successful),
            "encoding_success_rate": 0.0,
            "decoding_success_rate": 0.0,
            "roundtrip_success_rate": 0.0,
            "encoding_type_performance": {},
            "error_distribution": {}
        }
        
        if analysis["total_tests"] > 0:
            analysis["encoding_success_rate"] = analysis["successful_encodings"] / analysis["total_tests"]
            analysis["decoding_success_rate"] = analysis["successful_decodings"] / analysis["total_tests"]
            analysis["roundtrip_success_rate"] = analysis["successful_roundtrips"] / analysis["total_tests"]
        
        # Analyze performance by encoding type
        type_performance = {}
        for result in results:
            encoding_type = result.encoding_type.value
            if encoding_type not in type_performance:
                type_performance[encoding_type] = {
                    "total": 0,
                    "encoding_success": 0,
                    "decoding_success": 0,
                    "roundtrip_success": 0
                }
            
            type_performance[encoding_type]["total"] += 1
            if result.encoding_successful:
                type_performance[encoding_type]["encoding_success"] += 1
            if result.decoding_successful:
                type_performance[encoding_type]["decoding_success"] += 1
            if result.roundtrip_successful:
                type_performance[encoding_type]["roundtrip_success"] += 1
        
        # Calculate success rates per encoding type
        for encoding_type, stats in type_performance.items():
            if stats["total"] > 0:
                stats["encoding_success_rate"] = stats["encoding_success"] / stats["total"]
                stats["decoding_success_rate"] = stats["decoding_success"] / stats["total"]
                stats["roundtrip_success_rate"] = stats["roundtrip_success"] / stats["total"]
        
        analysis["encoding_type_performance"] = type_performance
        
        # Analyze error distribution
        for result in results:
            if result.error_message:
                error_type = result.error_message.split(':')[0]
                if error_type not in analysis["error_distribution"]:
                    analysis["error_distribution"][error_type] = 0
                analysis["error_distribution"][error_type] += 1
        
        return analysis
    
    def test_encoding_variants(self, original_data: str, encoding_type: EncodingType) -> Dict[str, Any]:
        """
        Test multiple variants of encoding for the same data.
        
        Args:
            original_data: Original data to encode
            encoding_type: Type of encoding to test
            
        Returns:
            Test results for variants
        """
        variants = []
        
        # Test different encoding approaches
        if encoding_type == EncodingType.BASE64:
            # Standard base64
            encoded, error = self.encode_data(original_data, encoding_type)
            if encoded:
                variants.append({"method": "standard", "result": encoded, "error": None})
            
            # URL-safe base64
            try:
                url_safe = base64.urlsafe_b64encode(original_data.encode('utf-8')).decode('ascii')
                variants.append({"method": "url_safe", "result": url_safe, "error": None})
            except Exception as e:
                variants.append({"method": "url_safe", "result": None, "error": str(e)})
        
        elif encoding_type == EncodingType.URL_ENCODING:
            # Standard URL encoding
            encoded, error = self.encode_data(original_data, encoding_type)
            if encoded:
                variants.append({"method": "standard", "result": encoded, "error": None})
            
            # URL encoding with safe characters
            try:
                safe_encoded = urllib.parse.quote(original_data, safe='')
                variants.append({"method": "no_safe_chars", "result": safe_encoded, "error": None})
            except Exception as e:
                variants.append({"method": "no_safe_chars", "result": None, "error": str(e)})
        
        return {
            "original_data": original_data,
            "encoding_type": encoding_type.value,
            "variants": variants
        }
    
    def analyze_encoding_chain(self, data: str, encoding_chain: List[EncodingType]) -> Dict[str, Any]:
        """
        Analyze data through a chain of encodings.
        
        Args:
            data: Original data
            encoding_chain: List of encoding types to apply in sequence
            
        Returns:
            Analysis of encoding chain
        """
        current_data = data
        chain_results = []
        
        for i, encoding_type in enumerate(encoding_chain):
            # Encode
            encoded, encode_error = self.encode_data(current_data, encoding_type)
            
            # Decode (reverse the encoding)
            decoded = None
            decode_error = None
            if encoded is not None:
                decoded, decode_error = self.decode_data(encoded, encoding_type)
            
            chain_results.append({
                "step": i + 1,
                "encoding_type": encoding_type.value,
                "input": current_data,
                "encoded": encoded,
                "decoded": decoded,
                "encode_error": encode_error,
                "decode_error": decode_error,
                "roundtrip_success": decoded == current_data
            })
            
            # Move to next step with encoded data
            if encoded is not None:
                current_data = encoded
            else:
                break
        
        return {
            "original_data": data,
            "encoding_chain": [e.value for e in encoding_chain],
            "chain_results": chain_results,
            "final_success": all(r["roundtrip_success"] for r in chain_results)
        }
    
    def generate_encoding_report(self) -> Dict[str, Any]:
        """Generate comprehensive encoding analysis report."""
        analysis = self.analyze_encoding_consistency()
        
        report = {
            "summary": analysis,
            "test_coverage": {
                "base64_tests": len([t for t in self.test_cases if t.encoding_type == EncodingType.BASE64]),
                "url_encoding_tests": len([t for t in self.test_cases if t.encoding_type == EncodingType.URL_ENCODING]),
                "html_encoding_tests": len([t for t in self.test_cases if t.encoding_type == EncodingType.HTML_ENCODING]),
                "hex_encoding_tests": len([t for t in self.test_cases if t.encoding_type == EncodingType.HEX_ENCODING]),
                "unicode_escape_tests": len([t for t in self.test_cases if t.encoding_type == EncodingType.UNICODE_ESCAPE])
            },
            "recommendations": self._generate_encoding_recommendations(analysis),
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "encoding_type": r.encoding_type.value,
                    "original": r.original_data,
                    "encoded": r.encoded_data,
                    "decoded": r.decoded_data,
                    "roundtrip_success": r.roundtrip_successful,
                    "error": r.error_message
                }
                for r in self.results
            ]
        }
        
        return report
    
    def _generate_encoding_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on encoding analysis."""
        recommendations = []
        
        if analysis["roundtrip_success_rate"] < 0.9:
            recommendations.append("Low encoding roundtrip success rate. Review encoding/decoding implementation.")
        
        # Check specific encoding type performance
        type_perf = analysis["encoding_type_performance"]
        
        for encoding_type, stats in type_perf.items():
            if stats["roundtrip_success_rate"] < 0.8:
                recommendations.append(f"Poor performance with {encoding_type}. Consider improving {encoding_type} handling.")
        
        if len(analysis["error_distribution"]) > 0:
            most_common_error = max(analysis["error_distribution"].items(), key=lambda x: x[1])
            recommendations.append(f"Most common error: {most_common_error[0]}. Address this error type specifically.")
        
        if analysis["roundtrip_success_rate"] >= 0.95:
            recommendations.append("Excellent encoding handling performance. System shows robust encoding support.")
        
        return recommendations
