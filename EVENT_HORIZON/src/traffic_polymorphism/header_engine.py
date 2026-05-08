"""
Header Variability Engine

Generates diverse HTTP header combinations to test middleware robustness
and identify parser inconsistencies without offensive intent.
"""

import random
import string
from typing import Dict, List, Optional
from dataclasses import dataclass
from faker import Faker


@dataclass
class HeaderProfile:
    """Profile for generating specific header patterns."""
    user_agents: List[str]
    accept_languages: List[str]
    custom_headers: Dict[str, List[str]]


class HeaderVariabilityEngine:
    """Generates varied HTTP headers for defensive testing."""
    
    def __init__(self, profile: Optional[HeaderProfile] = None):
        self.fake = Faker()
        self.profile = profile or self._default_profile()
        
    def _default_profile(self) -> HeaderProfile:
        """Default header profiles for testing."""
        return HeaderProfile(
            user_agents=[
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
                "curl/8.5.0",
                "Python-requests/2.31.0",
                "PostmanRuntime/7.34.0",
                "Apache-HttpClient/4.5.14 (Java/17.0.8)",
                "Go-http-client/2.0"
            ],
            accept_languages=[
                "en-US,en;q=0.9",
                "en-GB,en;q=0.8",
                "ru-RU,ru;q=0.9,en;q=0.8",
                "de-DE,de;q=0.9,en;q=0.8",
                "fr-FR,fr;q=0.9,en;q=0.8",
                "es-ES,es;q=0.9,en;q=0.8",
                "ja-JP,ja;q=0.9,en;q=0.8",
                "zh-CN,zh;q=0.9,en;q=0.8",
                "en-US,en;q=0.8,fr;q=0.6",
                "de, en-US;q=0.9, en;q=0.8"
            ],
            custom_headers={
                "X-Request-ID": [str(random.randint(1000, 999999)) for _ in range(100)],
                "X-Forwarded-For": [self.fake.ipv4() for _ in range(50)],
                "X-Real-IP": [self.fake.ipv4() for _ in range(50)],
                "X-Forwarded-Proto": ["http", "https"],
                "X-Forwarded-Host": [self.fake.domain_name() for _ in range(20)],
                "X-Client-ID": [f"client_{random.randint(1, 1000)}" for _ in range(50)],
                "X-Session-ID": [f"sess_{random.randint(100000, 999999)}" for _ in range(50)]
            }
        )
    
    def generate_headers(self, variation_level: str = "medium") -> Dict[str, str]:
        """
        Generate HTTP headers with specified variation level.
        
        Args:
            variation_level: "low", "medium", or "high" variation intensity
            
        Returns:
            Dictionary of HTTP headers
        """
        headers = {}
        
        # Basic headers
        headers["User-Agent"] = random.choice(self.profile.user_agents)
        headers["Accept-Language"] = random.choice(self.profile.accept_languages)
        
        # Add variation based on level
        if variation_level == "low":
            headers.update(self._generate_low_variation())
        elif variation_level == "medium":
            headers.update(self._generate_medium_variation())
        elif variation_level == "high":
            headers.update(self._generate_high_variation())
        
        # Randomize header order for testing parser robustness
        return self._randomize_header_order(headers)
    
    def _generate_low_variation(self) -> Dict[str, str]:
        """Generate headers with low variation."""
        headers = {}
        
        # Add a few standard headers
        if random.random() > 0.3:
            headers["X-Request-ID"] = random.choice(self.profile.custom_headers["X-Request-ID"])
        
        if random.random() > 0.5:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        
        return headers
    
    def _generate_medium_variation(self) -> Dict[str, str]:
        """Generate headers with medium variation."""
        headers = {}
        
        # Add custom headers with moderate probability
        custom_headers = ["X-Request-ID", "X-Forwarded-For", "X-Client-ID", "X-Session-ID"]
        for header in custom_headers:
            if random.random() > 0.4:
                headers[header] = random.choice(self.profile.custom_headers[header])
        
        # Add standard headers
        if random.random() > 0.3:
            headers["Accept"] = random.choice([
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "application/json",
                "text/plain",
                "*/*"
            ])
        
        if random.random() > 0.5:
            headers["Accept-Encoding"] = random.choice([
                "gzip, deflate",
                "gzip, deflate, br",
                "identity"
            ])
        
        return headers
    
    def _generate_high_variation(self) -> Dict[str, str]:
        """Generate headers with high variation for robustness testing."""
        headers = {}
        
        # Add all custom headers with high probability
        for header_name, values in self.profile.custom_headers.items():
            if random.random() > 0.2:
                headers[header_name] = random.choice(values)
        
        # Add edge case headers for parser testing
        if random.random() > 0.3:
            headers["Accept"] = self._generate_complex_accept_header()
        
        if random.random() > 0.4:
            headers["Accept-Encoding"] = self._generate_complex_encoding_header()
        
        # Add whitespace variations for parser testing
        if random.random() > 0.7:
            headers = self._add_whitespace_variations(headers)
        
        # Add duplicate headers for testing header merging
        if random.random() > 0.8:
            headers = self._add_duplicate_headers(headers)
        
        return headers
    
    def _generate_complex_accept_header(self) -> str:
        """Generate complex Accept header for parser testing."""
        media_types = [
            "text/html", "application/xhtml+xml", "application/xml", "text/plain",
            "application/json", "application/javascript", "text/css", "image/*"
        ]
        
        selected = random.sample(media_types, random.randint(2, 5))
        parts = []
        
        for i, media_type in enumerate(selected):
            q_value = round(random.uniform(0.1, 1.0), 1)
            parts.append(f"{media_type};q={q_value}")
        
        return ", ".join(parts)
    
    def _generate_complex_encoding_header(self) -> str:
        """Generate complex Accept-Encoding header."""
        encodings = ["gzip", "deflate", "br", "identity", "compress"]
        selected = random.sample(encodings, random.randint(1, 3))
        
        # Add quality values randomly
        parts = []
        for encoding in selected:
            if random.random() > 0.5:
                q_value = round(random.uniform(0.5, 1.0), 1)
                parts.append(f"{encoding};q={q_value}")
            else:
                parts.append(encoding)
        
        return ", ".join(parts)
    
    def _add_whitespace_variations(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add whitespace variations to test parser robustness."""
        varied_headers = {}
        
        for key, value in headers.items():
            if random.random() > 0.5:
                # Add leading/trailing whitespace
                if random.random() > 0.5:
                    value = " " + value
                if random.random() > 0.5:
                    value = value + " "
            
            varied_headers[key] = value
        
        return varied_headers
    
    def _add_duplicate_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add headers that might be duplicated by middleware."""
        # Note: This simulates what might happen when multiple layers add the same header
        if "X-Forwarded-For" in headers and random.random() > 0.5:
            # Simulate multiple proxy IPs
            original_ip = headers["X-Forwarded-For"]
            additional_ip = self.fake.ipv4()
            headers["X-Forwarded-For"] = f"{original_ip}, {additional_ip}"
        
        return headers
    
    def _randomize_header_order(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Randomize header order to test parsing consistency."""
        items = list(headers.items())
        random.shuffle(items)
        return dict(items)
    
    def generate_header_batch(self, count: int, variation_levels: List[str] = None) -> List[Dict[str, str]]:
        """
        Generate a batch of headers with mixed variation levels.
        
        Args:
            count: Number of header sets to generate
            variation_levels: List of variation levels to use (default: all levels)
            
        Returns:
            List of header dictionaries
        """
        if variation_levels is None:
            variation_levels = ["low", "medium", "high"]
        
        batch = []
        for _ in range(count):
            level = random.choice(variation_levels)
            batch.append(self.generate_headers(level))
        
        return batch
    
    def analyze_header_consistency(self, responses: List[Dict]) -> Dict[str, any]:
        """
        Analyze response patterns to identify header parsing inconsistencies.
        
        Args:
            responses: List of response data including headers and status
            
        Returns:
            Analysis results with identified patterns
        """
        analysis = {
            "total_requests": len(responses),
            "status_distribution": {},
            "header_response_patterns": {},
            "potential_inconsistencies": []
        }
        
        # Analyze status code distribution
        for response in responses:
            status = response.get("status", "unknown")
            analysis["status_distribution"][status] = analysis["status_distribution"].get(status, 0) + 1
        
        # Look for patterns in responses based on header variations
        # This is a simplified analysis - in practice, you'd want more sophisticated pattern detection
        
        return analysis
