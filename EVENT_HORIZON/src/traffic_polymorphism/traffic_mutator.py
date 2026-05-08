"""
Traffic Mutator

Applies various transformations to HTTP traffic for testing middleware robustness.
Focuses on defensive testing to identify parser inconsistencies and normalization issues.
"""

import random
import string
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote, unquote


@dataclass
class MutationProfile:
    """Profile defining mutation strategies."""
    enable_whitespace_variations: bool = True
    enable_encoding_variations: bool = True
    enable_case_variations: bool = True
    enable_duplicate_parameters: bool = True
    enable_empty_parameters: bool = True
    max_mutation_depth: int = 3


class TrafficMutator:
    """Mutates HTTP traffic components for defensive testing."""
    
    def __init__(self, profile: Optional[MutationProfile] = None):
        self.profile = profile or MutationProfile()
    
    def mutate_url(self, base_url: str, mutation_level: str = "medium") -> str:
        """
        Apply mutations to URL for testing parser robustness.
        
        Args:
            base_url: Base URL to mutate
            mutation_level: "low", "medium", or "high"
            
        Returns:
            Mutated URL
        """
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        
        # Apply mutations based on level
        if mutation_level == "low":
            query_params = self._mutate_params_low(query_params)
        elif mutation_level == "medium":
            query_params = self._mutate_params_medium(query_params)
        elif mutation_level == "high":
            query_params = self._mutate_params_high(query_params)
        
        # Reconstruct URL
        new_query = urlencode(query_params, doseq=True)
        mutated_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        return mutated_url
    
    def _mutate_params_low(self, params: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Apply low-level parameter mutations."""
        mutated = {}
        
        for key, values in params.items():
            # Case variation
            if self.profile.enable_case_variations and random.random() > 0.7:
                key = self._randomize_case(key)
            
            # Value variations
            mutated_values = []
            for value in values:
                if random.random() > 0.8:
                    # Simple whitespace variation
                    value = self._add_whitespace(value)
                mutated_values.append(value)
            
            mutated[key] = mutated_values
        
        return mutated
    
    def _mutate_params_medium(self, params: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Apply medium-level parameter mutations."""
        mutated = {}
        
        for key, values in params.items():
            # Case variation
            if self.profile.enable_case_variations:
                key = self._randomize_case(key)
            
            # Value variations
            mutated_values = []
            for value in values:
                # Multiple mutation types
                if self.profile.enable_whitespace_variations and random.random() > 0.5:
                    value = self._add_whitespace(value)
                
                if self.profile.enable_encoding_variations and random.random() > 0.6:
                    value = self._apply_encoding_variation(value)
                
                mutated_values.append(value)
            
            mutated[key] = mutated_values
        
        # Add empty parameters
        if self.profile.enable_empty_parameters and random.random() > 0.7:
            empty_key = f"empty_{random.randint(1, 100)}"
            mutated[empty_key] = [""]
        
        return mutated
    
    def _mutate_params_high(self, params: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Apply high-level parameter mutations for robustness testing."""
        mutated = {}
        
        for key, values in params:
            # Aggressive case variations
            if self.profile.enable_case_variations:
                key = self._randomize_case(key, aggressive=True)
            
            # Complex value mutations
            mutated_values = []
            for value in values:
                # Apply multiple mutations
                if self.profile.enable_whitespace_variations:
                    value = self._add_whitespace(value, aggressive=True)
                
                if self.profile.enable_encoding_variations:
                    value = self._apply_encoding_variation(value, aggressive=True)
                
                mutated_values.append(value)
            
            mutated[key] = mutated_values
        
        # Add duplicate parameters
        if self.profile.enable_duplicate_parameters and random.random() > 0.5:
            if params:  # Only if there are existing parameters
                orig_key = list(params.keys())[0]
                dup_key = self._randomize_case(orig_key)
                mutated[dup_key] = mutated.get(orig_key, [""])
        
        # Add empty parameters
        if self.profile.enable_empty_parameters:
            for _ in range(random.randint(1, 3)):
                empty_key = f"empty_{random.randint(1, 1000)}"
                mutated[empty_key] = [""]
        
        # Add parameters with special characters for parser testing
        if random.random() > 0.6:
            special_key = f"special_{random.randint(1, 100)}"
            special_value = self._generate_special_chars()
            mutated[special_key] = [special_value]
        
        return mutated
    
    def _randomize_case(self, text: str, aggressive: bool = False) -> str:
        """Randomize case of text."""
        if aggressive:
            # More aggressive case randomization
            return ''.join(
                random.choice([c.upper(), c.lower()]) if c.isalpha() else c
                for c in text
            )
        else:
            # Simple case randomization
            if random.random() > 0.5:
                return text.upper()
            elif random.random() > 0.5:
                return text.lower()
            return text
    
    def _add_whitespace(self, text: str, aggressive: bool = False) -> str:
        """Add whitespace variations to text."""
        if aggressive:
            # Multiple whitespace types
            whitespace_chars = [' ', '\t', '\n', '\r']
            result = text
            
            # Add leading whitespace
            if random.random() > 0.5:
                leading = ''.join(random.choice(whitespace_chars) for _ in range(random.randint(1, 3)))
                result = leading + result
            
            # Add trailing whitespace
            if random.random() > 0.5:
                trailing = ''.join(random.choice(whitespace_chars) for _ in range(random.randint(1, 3)))
                result = result + trailing
            
            # Add internal whitespace
            if random.random() > 0.7 and len(result) > 2:
                pos = random.randint(1, len(result) - 1)
                internal = random.choice(whitespace_chars)
                result = result[:pos] + internal + result[pos:]
            
            return result
        else:
            # Simple whitespace
            if random.random() > 0.5:
                return " " + text
            if random.random() > 0.5:
                return text + " "
            return text
    
    def _apply_encoding_variation(self, text: str, aggressive: bool = False) -> str:
        """Apply encoding variations for testing normalization."""
        if aggressive:
            # Multiple encoding rounds
            operations = [
                lambda x: quote(x),
                lambda x: quote(x, safe=''),
                lambda x: quote_plus(x),
                lambda x: unquote(x),
                lambda x: x.replace(' ', '+'),
                lambda x: x.replace('+', ' ')
            ]
            
            # Apply random operations
            result = text
            for _ in range(random.randint(1, 3)):
                op = random.choice(operations)
                try:
                    result = op(result)
                except:
                    pass  # Ignore encoding errors
            
            return result
        else:
            # Simple encoding
            if random.random() > 0.5:
                try:
                    return quote(text)
                except:
                    return text
            return text
    
    def _generate_special_chars(self) -> str:
        """Generate string with special characters for parser testing."""
        # Safe special characters that should be handled properly
        safe_specials = "!#$%&'()*+,-./:;<=>?@[]^_`{|}~"
        numbers = string.digits
        letters = string.ascii_letters
        
        # Mix of characters
        all_chars = safe_specials + numbers + letters
        
        # Generate random string
        length = random.randint(5, 20)
        return ''.join(random.choice(all_chars) for _ in range(length))
    
    def mutate_body(self, body: str, content_type: str = "application/json", mutation_level: str = "medium") -> str:
        """
        Mutate request body for testing parser robustness.
        
        Args:
            body: Original request body
            content_type: Content type of the body
            mutation_level: Mutation intensity level
            
        Returns:
            Mutated body
        """
        if mutation_level == "low":
            return self._mutate_body_low(body, content_type)
        elif mutation_level == "medium":
            return self._mutate_body_medium(body, content_type)
        elif mutation_level == "high":
            return self._mutate_body_high(body, content_type)
        
        return body
    
    def _mutate_body_low(self, body: str, content_type: str) -> str:
        """Low-level body mutations."""
        # Simple whitespace variations
        if self.profile.enable_whitespace_variations:
            body = self._add_whitespace(body)
        
        return body
    
    def _mutate_body_medium(self, body: str, content_type: str) -> str:
        """Medium-level body mutations."""
        # Combine multiple mutations
        if self.profile.enable_whitespace_variations:
            body = self._add_whitespace(body)
        
        if content_type == "application/x-www-form-urlencoded":
            # Mutate form parameters
            from urllib.parse import parse_qs, urlencode
            params = parse_qs(body, keep_blank_values=True)
            mutated_params = self._mutate_params_medium(params)
            body = urlencode(mutated_params, doseq=True)
        
        return body
    
    def _mutate_body_high(self, body: str, content_type: str) -> str:
        """High-level body mutations."""
        # Aggressive mutations
        if self.profile.enable_whitespace_variations:
            body = self._add_whitespace(body, aggressive=True)
        
        if content_type == "application/x-www-form-urlencoded":
            from urllib.parse import parse_qs, urlencode
            params = parse_qs(body, keep_blank_values=True)
            mutated_params = self._mutate_params_high(params)
            body = urlencode(mutated_params, doseq=True)
        
        return body
    
    def generate_traffic_variants(self, base_request: Dict, count: int, mutation_levels: List[str] = None) -> List[Dict]:
        """
        Generate multiple traffic variants from a base request.
        
        Args:
            base_request: Base request dictionary with url, headers, body, etc.
            count: Number of variants to generate
            mutation_levels: List of mutation levels to use
            
        Returns:
            List of mutated request dictionaries
        """
        if mutation_levels is None:
            mutation_levels = ["low", "medium", "high"]
        
        variants = []
        for i in range(count):
            variant = base_request.copy()
            
            # Mutate URL
            level = random.choice(mutation_levels)
            variant["url"] = self.mutate_url(base_request.get("url", ""), level)
            
            # Mutate body if present
            if "body" in variant:
                content_type = variant.get("headers", {}).get("Content-Type", "application/json")
                variant["body"] = self.mutate_body(variant["body"], content_type, level)
            
            variants.append(variant)
        
        return variants
