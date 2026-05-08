"""
Rate Limit Pressure Module (RLPM)

Tests rate limiting resilience by simulating burst traffic,
distributed IP spoofing patterns, and adaptive throttling evasion.
"""

import asyncio
import random
import time
import uuid
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field
import structlog

from core.models import TestRequest, FailureEvent

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitState:
    """Represents the rate limit state for an IP/user"""
    identifier: str  # IP address, user ID, etc.
    request_count: int = 0
    window_start: float = field(default_factory=time.time)
    blocked_until: float = 0.0
    violation_count: int = 0
    last_request_time: float = field(default_factory=time.time)


@dataclass
class BurstPattern:
    """Defines a burst traffic pattern"""
    name: str
    requests_per_second: int
    duration_seconds: int
    source_distribution: Dict[str, float]  # IP -> probability
    payload_variation: float  # 0.0 to 1.0


class RateLimitPressureModule:
    """
    Tests rate limiting resilience through various attack patterns.
    
    This module simulates:
    - Burst traffic patterns
    - Distributed IP spoofing (logical simulation)
    - Adaptive throttling evasion techniques
    - Rate limit bypass attempts
    """
    
    def __init__(self):
        self.rate_limits: Dict[str, RateLimitState] = {}
        self.global_limits: Dict[str, RateLimitState] = {}
        
        # Rate limit configurations
        self.ip_limit = 100  # requests per minute per IP
        self.user_limit = 50  # requests per minute per user
        self.global_limit = 10000  # requests per minute globally
        
        # Attack patterns
        self.burst_patterns = self._generate_burst_patterns()
        self.spoofing_ranges = self._generate_spoofing_ranges()
        self.evasion_techniques = self._generate_evasion_techniques()
        
        # Statistics
        self.blocked_requests = 0
        self.allowed_requests = 0
        self.bypass_attempts = 0
        self.successful_bypasses = 0
        
        logger.info("Rate Limit Pressure Module initialized")
    
    async def process_request(self, request: TestRequest) -> None:
        """
        Process a request through rate limit pressure testing.
        
        Args:
            request: The test request to process
        """
        # Randomly apply rate limit stress techniques
        stress_type = random.choice([
            "burst_traffic", "distributed_spoof", "evasion_attempt",
            "slowloris", "header_rotation", "timing_attack"
        ])
        
        if stress_type == "burst_traffic":
            await self._simulate_burst_traffic(request)
        elif stress_type == "distributed_spoof":
            await self._simulate_distributed_spoofing(request)
        elif stress_type == "evasion_attempt":
            await self._simulate_evasion_attempt(request)
        elif stress_type == "slowloris":
            await self._simulate_slowloris_attack(request)
        elif stress_type == "header_rotation":
            await self._simulate_header_rotation(request)
        elif stress_type == "timing_attack":
            await self._simulate_timing_attack(request)
        
        # Add anomaly flag
        request.anomaly_flags.append(f"rlpm_{stress_type}")
        
        logger.debug("Applied rate limit stress", 
                    request_id=request.id, 
                    stress_type=stress_type)
    
    async def _simulate_burst_traffic(self, request: TestRequest) -> None:
        """Simulate burst traffic patterns"""
        pattern = random.choice(self.burst_patterns)
        
        # Generate burst requests
        burst_size = pattern.requests_per_second * pattern.duration_seconds
        
        for i in range(min(burst_size, 100)):  # Limit to prevent overload
            burst_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i / pattern.requests_per_second),
                source_ip=self._select_source_ip(pattern.source_distribution),
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload=request.payload.copy(),
                expected_result="rate_limited" if i > self.ip_limit else "success"
            )
            
            # Check rate limits
            await self._check_rate_limits(burst_request)
    
    async def _simulate_distributed_spoofing(self, request: TestRequest) -> None:
        """Simulate distributed IP spoofing patterns"""
        spoof_count = random.randint(10, 50)
        
        for i in range(spoof_count):
            # Generate spoofed IP from different ranges
            spoofed_ip = self._generate_spoofed_ip()
            
            spoofed_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 0.01),
                source_ip=spoofed_ip,
                user_agent=self._rotate_user_agent(i),
                auth_token=f"spoofed_token_{i}",
                session_id=None,  # No session for spoofed requests
                payload={"spoofed": True, "attempt": i},
                expected_result="blocked"
            )
            
            # Check if spoofing is detected
            await self._check_spoofing_detection(spoofed_request)
    
    async def _simulate_evasion_attempt(self, request: TestRequest) -> None:
        """Simulate rate limit evasion attempts"""
        technique = random.choice(self.evasion_techniques)
        
        if technique["type"] == "header_rotation":
            await self._rotate_headers_evasion(request)
        elif technique["type"] == "ip_rotation":
            await self._rotate_ip_evasion(request)
        elif technique["type"] == "user_agent_rotation":
            await self._rotate_user_agent_evasion(request)
        elif technique["type"] == "payload_variation":
            await self._payload_variation_evasion(request)
        elif technique["type"] == "timing_manipulation":
            await self._timing_manipulation_evasion(request)
    
    async def _rotate_headers_evasion(self, request: TestRequest) -> None:
        """Rotate headers to evade rate limiting"""
        headers = [
            {"X-Forwarded-For": f"192.168.1.{random.randint(1, 254)}"},
            {"X-Real-IP": f"10.0.0.{random.randint(1, 254)}"},
            {"X-Original-IP": f"172.16.0.{random.randint(1, 254)}"},
            {"X-Client-IP": f"203.0.113.{random.randint(1, 254)}"},
        ]
        
        for i, header_set in enumerate(headers):
            evasion_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 0.1),
                source_ip=request.source_ip,
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload={**request.payload, **header_set},
                expected_result="success"  # Hoping to bypass limits
            )
            
            await self._check_rate_limits(evasion_request)
            self.bypass_attempts += 1
    
    async def _rotate_ip_evasion(self, request: TestRequest) -> None:
        """Rotate IP addresses to evade rate limiting"""
        ip_ranges = ["192.168.1.", "10.0.0.", "172.16.0.", "203.0.113."]
        
        for i, ip_range in enumerate(ip_ranges):
            new_ip = f"{ip_range}{random.randint(1, 254)}"
            
            evasion_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 0.05),
                source_ip=new_ip,
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload=request.payload.copy(),
                expected_result="success"
            )
            
            await self._check_rate_limits(evasion_request)
            self.bypass_attempts += 1
    
    async def _rotate_user_agent_evasion(self, request: TestRequest) -> None:
        """Rotate user agents to evade rate limiting"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "curl/7.68.0",
            "Python-requests/2.25.1",
        ]
        
        for i, ua in enumerate(user_agents):
            evasion_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 0.02),
                source_ip=request.source_ip,
                user_agent=ua,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload=request.payload.copy(),
                expected_result="success"
            )
            
            await self._check_rate_limits(evasion_request)
            self.bypass_attempts += 1
    
    async def _payload_variation_evasion(self, request: TestRequest) -> None:
        """Vary payload to evade rate limiting"""
        variations = [
            {"username": "admin", "password": "pass"},
            {"username": "admin", "password": "pass", "extra": "data"},
            {"user": "admin", "pwd": "pass"},
            {"login": "admin", "passwd": "pass"},
            {"username": "admin", "password": "pass", "timestamp": time.time()},
        ]
        
        for i, variation in enumerate(variations):
            evasion_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 0.03),
                source_ip=request.source_ip,
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload=variation,
                expected_result="success"
            )
            
            await self._check_rate_limits(evasion_request)
            self.bypass_attempts += 1
    
    async def _timing_manipulation_evasion(self, request: TestRequest) -> None:
        """Manipulate timing to evade rate limiting"""
        # Send requests with carefully calculated intervals
        base_time = time.time()
        intervals = [0.1, 0.5, 1.0, 2.0, 0.1, 0.5]  # Irregular pattern
        
        for i, interval in enumerate(intervals):
            evasion_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=base_time + sum(intervals[:i+1]),
                source_ip=request.source_ip,
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload=request.payload.copy(),
                expected_result="success"
            )
            
            await self._check_rate_limits(evasion_request)
            self.bypass_attempts += 1
    
    async def _simulate_slowloris_attack(self, request: TestRequest) -> None:
        """Simulate Slowloris-style attacks"""
        # Send incomplete headers slowly
        for i in range(10):
            slow_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 5),  # Very slow
                source_ip=request.source_ip,
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload={"incomplete": f"partial_{i}"},
                expected_result="timeout"
            )
            
            await self._check_rate_limits(slow_request)
    
    async def _simulate_header_rotation(self, request: TestRequest) -> None:
        """Simulate header rotation attacks"""
        header_combinations = [
            {"X-Custom-Header": "value1"},
            {"X-Another-Header": "value2"},
            {"X-Forwarded-Proto": "https"},
            {"X-Forwarded-Host": "evil.com"},
        ]
        
        for i, headers in enumerate(header_combinations):
            rotation_request = TestRequest(
                id=str(uuid.uuid4()),
                timestamp=time.time() + (i * 0.1),
                source_ip=request.source_ip,
                user_agent=request.user_agent,
                auth_token=request.auth_token,
                session_id=request.session_id,
                payload={**request.payload, **headers},
                expected_result="success"
            )
            
            await self._check_rate_limits(rotation_request)
    
    async def _simulate_timing_attack(self, request: TestRequest) -> None:
        """Simulate timing-based attacks"""
        # Send requests at specific intervals to exploit timing windows
        timing_patterns = [
            [0.01, 0.01, 0.01],  # Rapid burst
            [0.5, 0.5, 0.5],    # Regular intervals
            [0.1, 1.0, 0.1],    # Irregular pattern
        ]
        
        for pattern in timing_patterns:
            base_time = time.time()
            for i, interval in enumerate(pattern):
                timing_request = TestRequest(
                    id=str(uuid.uuid4()),
                    timestamp=base_time + sum(pattern[:i+1]),
                    source_ip=request.source_ip,
                    user_agent=request.user_agent,
                    auth_token=request.auth_token,
                    session_id=request.session_id,
                    payload=request.payload.copy(),
                    expected_result="success"
                )
                
                await self._check_rate_limits(timing_request)
    
    async def _check_rate_limits(self, request: TestRequest) -> None:
        """Check if request violates rate limits"""
        current_time = time.time()
        
        # Check IP-based limits
        ip_key = f"ip:{request.source_ip}"
        if ip_key not in self.rate_limits:
            self.rate_limits[ip_key] = RateLimitState(identifier=request.source_ip)
        
        ip_state = self.rate_limits[ip_key]
        
        # Reset window if needed
        if current_time - ip_state.window_start > 60:  # 1 minute window
            ip_state.request_count = 0
            ip_state.window_start = current_time
        
        # Check if blocked
        if current_time < ip_state.blocked_until:
            self.blocked_requests += 1
            return
        
        # Check limit
        if ip_state.request_count >= self.ip_limit:
            ip_state.blocked_until = current_time + 300  # Block for 5 minutes
            ip_state.violation_count += 1
            self.blocked_requests += 1
            return
        
        # Update state
        ip_state.request_count += 1
        ip_state.last_request_time = current_time
        self.allowed_requests += 1
    
    async def _check_spoofing_detection(self, request: TestRequest) -> None:
        """Check if IP spoofing is detected"""
        # Simple spoofing detection based on IP patterns
        ip_parts = request.source_ip.split('.')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            all(part == "0" for part in ip_parts),  # 0.0.0.0
            all(part == "255" for part in ip_parts),  # 255.255.255.255
            ip_parts[0] == "127",  # localhost
            ip_parts[0] in ["169", "224", "240"],  # Reserved ranges
        ]
        
        if any(suspicious_patterns):
            self.blocked_requests += 1
            logger.debug("Spoofing detected", ip=request.source_ip)
        else:
            self.allowed_requests += 1
    
    def _select_source_ip(self, distribution: Dict[str, float]) -> str:
        """Select source IP based on distribution"""
        rand = random.random()
        cumulative = 0.0
        
        for ip, probability in distribution.items():
            cumulative += probability
            if rand <= cumulative:
                return ip
        
        # Fallback to first IP
        return list(distribution.keys())[0]
    
    def _generate_spoofed_ip(self) -> str:
        """Generate a spoofed IP address"""
        ip_range = random.choice(self.spoofing_ranges)
        return f"{ip_range}.{random.randint(1, 254)}"
    
    def _rotate_user_agent(self, index: int) -> str:
        """Rotate user agent based on index"""
        user_agents = [
            f"Mozilla/5.0 (compatible; Bot/{index})",
            f"curl/7.{68 + index}.{0 + index}",
            f"Python-requests/2.{25 + index}.{1 + index}",
        ]
        return user_agents[index % len(user_agents)]
    
    def _generate_burst_patterns(self) -> List[BurstPattern]:
        """Generate predefined burst traffic patterns"""
        return [
            BurstPattern(
                name="short_burst",
                requests_per_second=50,
                duration_seconds=5,
                source_distribution={"192.168.1.100": 1.0},
                payload_variation=0.1
            ),
            BurstPattern(
                name="distributed_burst",
                requests_per_second=100,
                duration_seconds=10,
                source_distribution={
                    "192.168.1.100": 0.3,
                    "192.168.1.101": 0.3,
                    "192.168.1.102": 0.4
                },
                payload_variation=0.5
            ),
            BurstPattern(
                name="sustained_load",
                requests_per_second=20,
                duration_seconds=60,
                source_distribution={
                    f"192.168.1.{100+i}": 0.1 for i in range(10)
                },
                payload_variation=0.8
            ),
        ]
    
    def _generate_spoofing_ranges(self) -> List[str]:
        """Generate IP ranges for spoofing simulation"""
        return [
            "192.168.1",
            "10.0.0",
            "172.16.0",
            "203.0.113",
            "198.51.100",
        ]
    
    def _generate_evasion_techniques(self) -> List[Dict[str, Any]]:
        """Generate rate limit evasion techniques"""
        return [
            {"type": "header_rotation", "success_rate": 0.3},
            {"type": "ip_rotation", "success_rate": 0.6},
            {"type": "user_agent_rotation", "success_rate": 0.2},
            {"type": "payload_variation", "success_rate": 0.4},
            {"type": "timing_manipulation", "success_rate": 0.5},
        ]
    
    def get_rate_limit_metrics(self) -> Dict[str, Any]:
        """Get rate limiting performance metrics"""
        total_requests = self.allowed_requests + self.blocked_requests
        
        return {
            "total_requests": total_requests,
            "allowed_requests": self.allowed_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": self.blocked_requests / max(total_requests, 1),
            "bypass_attempts": self.bypass_attempts,
            "successful_bypasses": self.successful_bypasses,
            "bypass_success_rate": self.successful_bypasses / max(self.bypass_attempts, 1),
            "active_rate_limits": len(self.rate_limits),
            "most_blocked_ips": self._get_most_blocked_ips(),
            "violation_distribution": self._get_violation_distribution(),
        }
    
    def _get_most_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get IPs with most violations"""
        ip_violations = [
            {"ip": state.identifier, "violations": state.violation_count}
            for state in self.rate_limits.values()
            if state.violation_count > 0
        ]
        
        return sorted(ip_violations, key=lambda x: x["violations"], reverse=True)[:10]
    
    def _get_violation_distribution(self) -> Dict[str, int]:
        """Get distribution of violations by count"""
        distribution = {}
        for state in self.rate_limits.values():
            if state.violation_count > 0:
                key = f"{state.violation_count}_violations"
                distribution[key] = distribution.get(key, 0) + 1
        
        return distribution
