"""
Rate Limiter

Token bucket rate limiter for controlling request rates
and preventing system overload during testing.
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter for controlling request rates.
    """
    
    def __init__(self, rate: float, burst: Optional[int] = None):
        """
        Initialize rate limiter.
        
        Args:
            rate: Requests per second
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.burst = burst or int(rate)
        
        self.tokens = self.burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        async with self._lock:
            now = time.time()
            
            # Add new tokens based on elapsed time
            elapsed = now - self.last_update
            new_tokens = elapsed * self.rate
            
            self.tokens = min(self.burst, self.tokens + new_tokens)
            self.last_update = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_token(self, tokens: int = 1) -> None:
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens to wait for
        """
        while not await self.acquire(tokens):
            # Calculate wait time based on token deficit
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            await asyncio.sleep(wait_time)
    
    async def __aenter__(self):
        """Async context manager for automatic token acquisition."""
        await self.wait_for_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup."""
        pass
    
    def get_available_tokens(self) -> int:
        """Get current available tokens."""
        return int(self.tokens)
    
    def reset(self):
        """Reset the rate limiter."""
        self.tokens = self.burst
        self.last_update = time.time()
