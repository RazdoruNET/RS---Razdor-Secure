"""
Charset Handler

Handles character set encoding and decoding for testing
charset handling consistency across different components.
"""

import codecs
import chardet
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class CharsetType(Enum):
    """Types of character sets to test."""
    UTF8 = "utf-8"
    UTF16 = "utf-16"
    ISO88591 = "iso-8859-1"
    WINDOWS1252 = "windows-1252"
    ASCII = "ascii"
    CP1251 = "cp1251"
    GB2312 = "gb2312"


@dataclass
class CharsetTest:
    """Represents a charset handling test."""
    test_name: str
    original_text: str
    source_charset: CharsetType
    target_charset: CharsetType
    expected_behavior: str


@dataclass
class CharsetResult:
    """Result of charset handling test."""
    test_name: str
    original_text: str
    encoded_text: Optional[bytes]
    decoded_text: Optional[str]
    conversion_successful: bool
    error_message: Optional[str]
    charset_detection: Optional[str]


class CharsetHandler:
    """
    Handles character set encoding/decoding for testing
    charset handling consistency.
    """
    
    def __init__(self):
        self.test_cases = self._generate_test_cases()
        self.results: List[CharsetResult] = []
    
    def _generate_test_cases(self) -> List[CharsetTest]:
        """Generate charset test cases."""
        test_cases = []
        
        # UTF-8 tests
        test_cases.extend([
            CharsetTest(
                test_name="utf8_basic_latin",
                original_text="Hello World",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.UTF8,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="utf8_accented_chars",
                original_text="café résumé naïve",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.UTF8,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="utf8_cyrillic",
                original_text="Привет мир",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.UTF8,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="utf8_chinese",
                original_text="你好世界",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.UTF8,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="utf8_emoji",
                original_text="Hello 🌍 World 🚀",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.UTF8,
                expected_behavior="perfect_roundtrip"
            )
        ])
        
        # ASCII tests
        test_cases.extend([
            CharsetTest(
                test_name="ascii_basic",
                original_text="Hello World",
                source_charset=CharsetType.ASCII,
                target_charset=CharsetType.ASCII,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="ascii_with_unicode",
                original_text="café",
                source_charset=CharsetType.ASCII,
                target_charset=CharsetType.ASCII,
                expected_behavior="encoding_error_or_replacement"
            )
        ])
        
        # ISO-8859-1 tests
        test_cases.extend([
            CharsetTest(
                test_name="iso88591_basic",
                original_text="Hello World",
                source_charset=CharsetType.ISO88591,
                target_charset=CharsetType.ISO88591,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="iso88591_western_european",
                original_text="café résumé",
                source_charset=CharsetType.ISO88591,
                target_charset=CharsetType.ISO88591,
                expected_behavior="perfect_roundtrip"
            )
        ])
        
        # Windows-1252 tests
        test_cases.extend([
            CharsetTest(
                test_name="windows1252_basic",
                original_text="Hello World",
                source_charset=CharsetType.WINDOWS1252,
                target_charset=CharsetType.WINDOWS1252,
                expected_behavior="perfect_roundtrip"
            ),
            CharsetTest(
                test_name="windows1252_extended",
                original_text="café résumé",
                source_charset=CharsetType.WINDOWS1252,
                target_charset=CharsetType.WINDOWS1252,
                expected_behavior="perfect_roundtrip"
            )
        ])
        
        # Cross-charset conversion tests
        test_cases.extend([
            CharsetTest(
                test_name="utf8_to_iso88591",
                original_text="café",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.ISO88591,
                expected_behavior="partial_conversion"
            ),
            CharsetTest(
                test_name="utf8_to_ascii",
                original_text="Hello World",
                source_charset=CharsetType.UTF8,
                target_charset=CharsetType.ASCII,
                expected_behavior="partial_conversion"
            ),
            CharsetTest(
                test_name="iso88591_to_utf8",
                original_text="café",
                source_charset=CharsetType.ISO88591,
                target_charset=CharsetType.UTF8,
                expected_behavior="perfect_roundtrip"
            )
        ])
        
        return test_cases
    
    def encode_text(self, text: str, charset: CharsetType) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Encode text using specified charset.
        
        Args:
            text: Text to encode
            charset: Target charset
            
        Returns:
            Tuple of (encoded_bytes, error_message)
        """
        try:
            encoded = text.encode(charset.value)
            return encoded, None
        except UnicodeEncodeError as e:
            return None, f"UnicodeEncodeError: {e}"
        except LookupError as e:
            return None, f"LookupError: {e}"
        except Exception as e:
            return None, f"Unexpected error: {e}"
    
    def decode_text(self, data: bytes, charset: CharsetType) -> Tuple[Optional[str], Optional[str]]:
        """
        Decode bytes using specified charset.
        
        Args:
            data: Bytes to decode
            charset: Source charset
            
        Returns:
            Tuple of (decoded_text, error_message)
        """
        try:
            decoded = data.decode(charset.value)
            return decoded, None
        except UnicodeDecodeError as e:
            return None, f"UnicodeDecodeError: {e}"
        except LookupError as e:
            return None, f"LookupError: {e}"
        except Exception as e:
            return None, f"Unexpected error: {e}"
    
    def detect_charset(self, data: bytes) -> Optional[str]:
        """
        Detect charset of byte data.
        
        Args:
            data: Byte data to analyze
            
        Returns:
            Detected charset name or None
        """
        try:
            result = chardet.detect(data)
            if result and result['confidence'] > 0.7:
                return result['encoding']
        except Exception:
            pass
        
        return None
    
    async def run_charset_test(self, test_case: CharsetTest) -> CharsetResult:
        """
        Run a single charset test.
        
        Args:
            test_case: Test case to run
            
        Returns:
            Charset test result
        """
        # Encode original text
        encoded_bytes, encode_error = self.encode_text(
            test_case.original_text, 
            test_case.source_charset
        )
        
        # Decode back if encoding was successful
        decoded_text = None
        decode_error = None
        conversion_successful = False
        
        if encoded_bytes is not None:
            decoded_text, decode_error = self.decode_text(
                encoded_bytes, 
                test_case.target_charset
            )
            conversion_successful = (decoded_text is not None and 
                                 decoded_text == test_case.original_text)
        
        # Detect charset if we have encoded data
        charset_detection = None
        if encoded_bytes is not None:
            charset_detection = self.detect_charset(encoded_bytes)
        
        # Combine error messages
        error_message = encode_error or decode_error
        
        result = CharsetResult(
            test_name=test_case.test_name,
            original_text=test_case.original_text,
            encoded_text=encoded_bytes,
            decoded_text=decoded_text,
            conversion_successful=conversion_successful,
            error_message=error_message,
            charset_detection=charset_detection
        )
        
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> List[CharsetResult]:
        """Run all charset tests."""
        results = []
        
        for test_case in self.test_cases:
            result = await self.run_charset_test(test_case)
            results.append(result)
        
        return results
    
    def analyze_charset_consistency(self, results: List[CharsetResult] = None) -> Dict[str, Any]:
        """
        Analyze charset handling consistency.
        
        Args:
            results: List of test results (uses self.results if None)
            
        Returns:
            Consistency analysis
        """
        if results is None:
            results = self.results
        
        analysis = {
            "total_tests": len(results),
            "successful_conversions": sum(1 for r in results if r.conversion_successful),
            "failed_conversions": sum(1 for r in results if not r.conversion_successful),
            "success_rate": 0.0,
            "charset_detection_accuracy": 0.0,
            "error_distribution": {},
            "charset_performance": {}
        }
        
        if analysis["total_tests"] > 0:
            analysis["success_rate"] = analysis["successful_conversions"] / analysis["total_tests"]
        
        # Analyze charset detection accuracy
        detection_tests = [r for r in results if r.charset_detection is not None]
        if detection_tests:
            # This is a simplified analysis - in practice you'd compare detected vs expected
            analysis["charset_detection_accuracy"] = len(detection_tests) / len(results)
        
        # Analyze error distribution
        for result in results:
            if result.error_message:
                error_type = result.error_message.split(':')[0]
                if error_type not in analysis["error_distribution"]:
                    analysis["error_distribution"][error_type] = 0
                analysis["error_distribution"][error_type] += 1
        
        # Analyze performance by charset
        charset_performance = {}
        for result in results:
            # Extract charset info from test name (simplified)
            if "utf8" in result.test_name:
                charset = "utf8"
            elif "ascii" in result.test_name:
                charset = "ascii"
            elif "iso" in result.test_name:
                charset = "iso88591"
            elif "windows" in result.test_name:
                charset = "windows1252"
            else:
                charset = "other"
            
            if charset not in charset_performance:
                charset_performance[charset] = {"success": 0, "total": 0}
            
            charset_performance[charset]["total"] += 1
            if result.conversion_successful:
                charset_performance[charset]["success"] += 1
        
        # Calculate success rates per charset
        for charset, stats in charset_performance.items():
            if stats["total"] > 0:
                stats["success_rate"] = stats["success"] / stats["total"]
            else:
                stats["success_rate"] = 0.0
        
        analysis["charset_performance"] = charset_performance
        
        return analysis
    
    def test_charset_roundtrip(self, text: str, charset: CharsetType) -> bool:
        """
        Test if text can be encoded and decoded successfully (roundtrip).
        
        Args:
            text: Text to test
            charset: Charset to use
            
        Returns:
            True if roundtrip is successful
        """
        encoded, encode_error = self.encode_text(text, charset)
        if encoded is None:
            return False
        
        decoded, decode_error = self.decode_text(encoded, charset)
        if decoded is None:
            return False
        
        return decoded == text
    
    def get_charset_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Get compatibility matrix between different charsets.
        
        Returns:
            Matrix showing compatibility rates between charsets
        """
        charsets = [c.value for c in CharsetType]
        matrix = {}
        
        test_text = "Hello World café résumé"
        
        for source in charsets:
            matrix[source] = {}
            for target in charsets:
                # Test compatibility
                source_charset = CharsetType(source)
                target_charset = CharsetType(target)
                
                encoded, _ = self.encode_text(test_text, source_charset)
                if encoded is not None:
                    decoded, _ = self.decode_text(encoded, target_charset)
                    if decoded is not None:
                        # Calculate compatibility score (simplified)
                        if decoded == test_text:
                            matrix[source][target] = 1.0
                        else:
                            # Partial compatibility based on character preservation
                            common_chars = sum(1 for c in test_text if c in decoded)
                            matrix[source][target] = common_chars / len(test_text)
                    else:
                        matrix[source][target] = 0.0
                else:
                    matrix[source][target] = 0.0
        
        return matrix
    
    def generate_charset_report(self) -> Dict[str, Any]:
        """Generate comprehensive charset handling report."""
        analysis = self.analyze_charset_consistency()
        
        report = {
            "summary": analysis,
            "compatibility_matrix": self.get_charset_compatibility_matrix(),
            "test_coverage": {
                "utf8_tests": len([t for t in self.test_cases if t.source_charset == CharsetType.UTF8]),
                "ascii_tests": len([t for t in self.test_cases if t.source_charset == CharsetType.ASCII]),
                "iso88591_tests": len([t for t in self.test_cases if t.source_charset == CharsetType.ISO88591]),
                "windows1252_tests": len([t for t in self.test_cases if t.source_charset == CharsetType.WINDOWS1252]),
                "cross_charset_tests": len([t for t in self.test_cases if t.source_charset != t.target_charset])
            },
            "recommendations": self._generate_charset_recommendations(analysis),
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "original": r.original_text,
                    "successful": r.conversion_successful,
                    "error": r.error_message,
                    "detected_charset": r.charset_detection
                }
                for r in self.results
            ]
        }
        
        return report
    
    def _generate_charset_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on charset analysis."""
        recommendations = []
        
        if analysis["success_rate"] < 0.9:
            recommendations.append("Low charset conversion success rate. Review charset handling implementation.")
        
        # Check specific charset performance
        charset_perf = analysis["charset_performance"]
        
        for charset, stats in charset_perf.items():
            if stats["success_rate"] < 0.8:
                recommendations.append(f"Poor performance with {charset}. Consider improving {charset} support.")
        
        if analysis["charset_detection_accuracy"] < 0.8:
            recommendations.append("Low charset detection accuracy. Implement better charset detection.")
        
        if len(analysis["error_distribution"]) > 0:
            most_common_error = max(analysis["error_distribution"].items(), key=lambda x: x[1])
            recommendations.append(f"Most common error: {most_common_error[0]}. Address this error type specifically.")
        
        if analysis["success_rate"] >= 0.95:
            recommendations.append("Excellent charset handling performance. System shows robust charset support.")
        
        return recommendations
