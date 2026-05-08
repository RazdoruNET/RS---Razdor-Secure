"""
Normalization Stress Layer (NSL)

Tests WAF and UTF-8 normalization resilience by injecting
malformed, overlong, and ambiguous token streams.
"""

import asyncio
import random
import structlog
from typing import Dict, Any, List
from urllib.parse import quote, unquote

from ...core.models import TestRequest, SemanticDriftEvent

logger = structlog.get_logger(__name__)


class NormalizationStressLayer:
    """
    Tests the resilience of WAF and UTF-8 normalization layers.
    
    This layer injects various types of malformed data to test:
    - UTF-8 overlong sequences
    - Unicode normalization inconsistencies
    - URL encoding ambiguities
    - Character set conversion issues
    """
    
    def __init__(self):
        self.malformed_payloads = self._generate_malformed_payloads()
        self.ambiguous_tokens = self._generate_ambiguous_tokens()
        self.overlong_sequences = self._generate_overlong_sequences()
        
        logger.info("Normalization Stress Layer initialized")
    
    async def process_request(self, request: TestRequest) -> None:
        """
        Process a request through normalization stress testing.
        
        Args:
            request: The test request to process
        """
        # Randomly apply normalization stress techniques
        stress_type = random.choice([
            "utf8_overlong", "unicode_normalization", 
            "url_encoding", "character_set", "control_characters"
        ])
        
        if stress_type == "utf8_overlong":
            await self._inject_utf8_overlong(request)
        elif stress_type == "unicode_normalization":
            await self._inject_unicode_normalization_issues(request)
        elif stress_type == "url_encoding":
            await self._inject_url_encoding_ambiguity(request)
        elif stress_type == "character_set":
            await self._inject_character_set_issues(request)
        elif stress_type == "control_characters":
            await self._inject_control_characters(request)
        
        # Add anomaly flag to track stress testing
        request.anomaly_flags.append(f"nsl_{stress_type}")
        
        logger.debug("Applied normalization stress", 
                    request_id=request.id, 
                    stress_type=stress_type)
    
    async def _inject_utf8_overlong(self, request: TestRequest) -> None:
        """Inject UTF-8 overlong sequences"""
        # Overlong encoding of '/' (0x2F) as 0xC0 0xAF
        overlong_slash = b'\xc0\xaf'
        
        # Overlong encoding of '.' (0x2E) as 0xC0 0xAE  
        overlong_dot = b'\xc0\xae'
        
        # Inject into payload
        if "username" in request.payload:
            username = request.payload["username"]
            # Replace normal characters with overlong sequences
            modified_username = username.replace("/", overlong_slash.decode('latin1'))
            modified_username = modified_username.replace(".", overlong_dot.decode('latin1'))
            request.payload["username"] = modified_username
        
        # Add to query parameters if present
        if "query" in request.payload:
            query = request.payload["query"]
            modified_query = query.replace("path=", "path=" + overlong_slash.decode('latin1'))
            request.payload["query"] = modified_query
    
    async def _inject_unicode_normalization_issues(self, request: TestRequest) -> None:
        """Inject Unicode normalization inconsistencies"""
        # Use characters with different normalization forms
        normalization_pairs = [
            ('é', 'é'),  # 'e' + combining acute vs precomposed
            ('𝔞', 'a'),   # Fraktur 'a' vs normal 'a'
            ('㎜', 'mm'),  # Square mm vs normal mm
            ('①', '1'),   # Circled number vs normal
            ('Ａ', 'A'),   # Fullwidth vs normal
        ]
        
        if "username" in request.payload:
            username = request.payload["username"]
            # Randomly replace characters with normalization variants
            for original, variant in random.sample(normalization_pairs, min(2, len(normalization_pairs))):
                if random.random() < 0.3:  # 30% chance for each pair
                    username = username.replace(original, variant) or variant + username
            request.payload["username"] = username
        
        # Add normalization test string
        request.payload["normalization_test"] = "".join([pair[0] for pair in normalization_pairs])
    
    async def _inject_url_encoding_ambiguity(self, request: TestRequest) -> None:
        """Inject URL encoding ambiguities"""
        # Double-encoded values
        double_encoded = quote(quote("test/admin"))
        
        # Mixed encoding
        mixed_encoding = "test%2Fadmin%u002fuser"
        
        # Partial encoding
        partial_encoding = "test%/admin"
        
        if "path" in request.payload:
            request.payload["path"] = random.choice([double_encoded, mixed_encoding, partial_encoding])
        
        # Add ambiguous query parameters
        if "query" in request.payload:
            query = request.payload["query"]
            query += f"&param={double_encoded}&mixed={mixed_encoding}"
            request.payload["query"] = query
    
    async def _inject_character_set_issues(self, request: TestRequest) -> None:
        """Inject character set conversion issues"""
        # Characters that cause issues in different encodings
        problematic_chars = [
            '\u20ac',  # Euro sign
            '\u201c',  # Left double quotation mark
            '\u201d',  # Right double quotation mark
            '\u2013',  # En dash
            '\u2014',  # Em dash
            '\u2026',  # Horizontal ellipsis
            '\xa0',    # Non-breaking space
            '\xad',    # Soft hyphen
        ]
        
        if "data" in request.payload:
            data = request.payload["data"]
            # Inject problematic characters
            for char in random.sample(problematic_chars, min(3, len(problematic_chars))):
                if random.random() < 0.4:  # 40% chance
                    data = char + data + char
            request.payload["data"] = data
        
        # Add character set test field
        request.payload["charset_test"] = "".join(random.sample(problematic_chars, 5))
    
    async def _inject_control_characters(self, request: TestRequest) -> None:
        """Inject control characters that may be filtered"""
        control_chars = [
            '\x00',  # Null
            '\x01',  # Start of heading
            '\x08',  # Backspace
            '\x0b',  # Vertical tab
            '\x0c',  # Form feed
            '\x0e',  # Shift out
            '\x0f',  # Shift in
            '\x1b',  # Escape
        ]
        
        # Inject into string fields
        for field in ["username", "data", "query"]:
            if field in request.payload and random.random() < 0.3:
                value = request.payload[field]
                # Add control characters at random positions
                for char in random.sample(control_chars, min(2, len(control_chars))):
                    if len(value) > 0:
                        pos = random.randint(0, len(value))
                        value = value[:pos] + char + value[pos:]
                request.payload[field] = value
    
    def _generate_malformed_payloads(self) -> List[Dict[str, Any]]:
        """Generate predefined malformed payloads for testing"""
        return [
            {
                "username": "admin\x00",
                "password": "pass",
                "type": "null_byte_injection"
            },
            {
                "username": "test\xc0\xafadmin",  # Overlong slash
                "password": "pass",
                "type": "utf8_overlong"
            },
            {
                "username": "test%2fadmin%u002fuser",  # Mixed encoding
                "password": "pass",
                "type": "mixed_encoding"
            },
            {
                "username": "𝔞dmin",  # Fraktur characters
                "password": "pass",
                "type": "unicode_variant"
            },
            {
                "username": "test\x1b[31minject",  # ANSI escape sequence
                "password": "pass",
                "type": "control_injection"
            }
        ]
    
    def _generate_ambiguous_tokens(self) -> List[str]:
        """Generate tokens with ambiguous interpretations"""
        return [
            "admin//",           # Double slash
            "admin/./",          # Directory traversal
            "admin/../",         # Parent directory
            "admin/%2e%2e/",     # URL encoded traversal
            "admin\\..\\",       # Windows path traversal
            "admin\u0000admin",  # Null byte injection
            "admin\u202eadmin",  # Left-to-right override
            "admin\ufffeadmin",  # Invalid Unicode
        ]
    
    def _generate_overlong_sequences(self) -> Dict[str, bytes]:
        """Generate UTF-8 overlong sequences for common characters"""
        return {
            "slash": b'\xc0\xaf',      # Overlong /
            "dot": b'\xc0\xae',        # Overlong .
            "null": b'\xc0\x80',       # Overlong \0
            "space": b'\xc0\xa0',      # Overlong space
            "question": b'\xc0\x3f',   # Overlong ?
        }
    
    def analyze_normalization_loss(self, original: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze semantic loss during normalization.
        
        Args:
            original: Original payload before normalization
            normalized: Payload after normalization
            
        Returns:
            Analysis of normalization loss
        """
        loss_analysis = {
            "fields_changed": [],
            "characters_lost": 0,
            "semantic_drift": 0.0,
            "encoding_issues": []
        }
        
        for key, original_value in original.items():
            if key in normalized:
                normalized_value = normalized[key]
                
                if isinstance(original_value, str) and isinstance(normalized_value, str):
                    if original_value != normalized_value:
                        loss_analysis["fields_changed"].append(key)
                        
                        # Calculate character loss
                        char_diff = len(original_value) - len(normalized_value)
                        if char_diff > 0:
                            loss_analysis["characters_lost"] += char_diff
                        
                        # Simple semantic drift calculation
                        if len(original_value) > 0:
                            drift = 1.0 - (len(set(original_value) & set(normalized_value)) / len(set(original_value)))
                            loss_analysis["semantic_drift"] = max(loss_analysis["semantic_drift"], drift)
                        
                        # Check for encoding issues
                        if any(ord(c) > 127 for c in original_value):
                            if not any(ord(c) > 127 for c in normalized_value):
                                loss_analysis["encoding_issues"].append(f"unicode_loss_in_{key}")
        
        return loss_analysis
    
    def get_normalization_test_cases(self) -> List[Dict[str, Any]]:
        """
        Get predefined test cases for normalization testing.
        
        Returns:
            List of test cases with expected behaviors
        """
        return [
            {
                "name": "UTF-8 Overlong Slash",
                "input": {"path": "admin\xc0\xafsecret"},
                "expected_behavior": "should_be_blocked_or_normalized",
                "risk_level": "high"
            },
            {
                "name": "Unicode Normalization",
                "input": {"username": "ádmín"},  # Combining accents
                "expected_behavior": "should_normalize_consistently",
                "risk_level": "medium"
            },
            {
                "name": "Mixed URL Encoding",
                "input": {"query": "user=admin%2Fsecret%u002fdata"},
                "expected_behavior": "should_decode_consistently",
                "risk_level": "high"
            },
            {
                "name": "Control Character Injection",
                "input": {"data": "test\x00admin\x1b[31m"},
                "expected_behavior": "should_strip_control_chars",
                "risk_level": "medium"
            },
            {
                "name": "Character Set Issues",
                "input": {"content": "test€\u201c\u2013"},
                "expected_behavior": "handle_charset_conversion",
                "risk_level": "low"
            }
        ]
