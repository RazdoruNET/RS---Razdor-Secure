"""
Async Request Engine

High-performance asynchronous HTTP request engine for
stress-testing authentication systems with proper rate limiting
and safety controls.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import ssl
from urllib.parse import urljoin

from .rate_limiter import RateLimiter
from .request_pool import RequestPool


class RequestMethod(Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class RequestConfig:
    """Configuration for individual requests."""
    method: RequestMethod
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    data: Optional[str] = None
    json: Optional[Dict[str, Any]] = None
    timeout: float = 30.0
    allow_redirects: bool = True
    verify_ssl: bool = True
    proxy: Optional[str] = None


@dataclass
class RequestResult:
    """Result of an HTTP request."""
    request_id: str
    method: str
    url: str
    status_code: int
    headers: Dict[str, str]
    body: str
    response_time: float
    error: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class AsyncRequestEngine:
    """
    High-performance asynchronous HTTP request engine with
    built-in rate limiting, connection pooling, and safety controls.
    """
    
    def __init__(self, max_concurrent_requests: int = 100, 
                 rate_limit: float = 50.0,
                 timeout: float = 30.0,
                 verify_ssl: bool = True):
        """
        Initialize the async request engine.
        
        Args:
            max_concurrent_requests: Maximum concurrent requests
            rate_limit: Requests per second limit
            timeout: Default request timeout
            verify_ssl: Whether to verify SSL certificates
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self.rate_limiter = RateLimiter(rate_limit)
        self.request_pool = RequestPool(max_concurrent_requests)
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[RequestResult] = []
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "status_code_distribution": {}
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the request engine and create session."""
        if self.session is None:
            # Configure SSL context
            ssl_context = None
            if not self.verify_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create connector with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent_requests * 2,  # Connection pool limit
                limit_per_host=self.max_concurrent_requests,
                ssl=ssl_context,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            # Configure timeout
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            # Create session
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "EVENT_HORIZON/1.0 (Defensive Testing Framework)"
                }
            )
    
    async def close(self):
        """Close the request engine and cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def execute_request(self, config: RequestConfig, 
                            request_id: Optional[str] = None) -> RequestResult:
        """
        Execute a single HTTP request.
        
        Args:
            config: Request configuration
            request_id: Optional request ID for tracking
            
        Returns:
            Request result
        """
        if not self.session:
            await self.start()
        
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000000)}"
        
        start_time = time.time()
        
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()
            
            # Prepare request parameters
            kwargs = {
                "headers": config.headers or {},
                "allow_redirects": config.allow_redirects,
                "proxy": config.proxy
            }
            
            if config.params:
                kwargs["params"] = config.params
            
            if config.data:
                kwargs["data"] = config.data
            
            if config.json:
                kwargs["json"] = config.json
            
            # Execute request
            async with self.request_pool.semaphore:
                async with self.session.request(
                    config.method.value,
                    config.url,
                    **kwargs
                ) as response:
                    response_time = time.time() - start_time
                    
                    # Read response body
                    body = await response.text()
                    
                    # Extract headers
                    headers = dict(response.headers)
                    
                    result = RequestResult(
                        request_id=request_id,
                        method=config.method.value,
                        url=config.url,
                        status_code=response.status,
                        headers=headers,
                        body=body,
                        response_time=response_time,
                        timestamp=time.time()
                    )
                    
                    # Update statistics
                    self._update_stats(result)
                    self.results.append(result)
                    
                    return result
        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            result = RequestResult(
                request_id=request_id,
                method=config.method.value,
                url=config.url,
                status_code=0,
                headers={},
                body="",
                response_time=response_time,
                error="Request timeout",
                timestamp=time.time()
            )
            self._update_stats(result)
            self.results.append(result)
            return result
        
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            result = RequestResult(
                request_id=request_id,
                method=config.method.value,
                url=config.url,
                status_code=0,
                headers={},
                body="",
                response_time=response_time,
                error=f"Client error: {str(e)}",
                timestamp=time.time()
            )
            self._update_stats(result)
            self.results.append(result)
            return result
        
        except Exception as e:
            response_time = time.time() - start_time
            result = RequestResult(
                request_id=request_id,
                method=config.method.value,
                url=config.url,
                status_code=0,
                headers={},
                body="",
                response_time=response_time,
                error=f"Unexpected error: {str(e)}",
                timestamp=time.time()
            )
            self._update_stats(result)
            self.results.append(result)
            return result
    
    async def execute_requests(self, configs: List[RequestConfig],
                            progress_callback: Optional[Callable[[int, int], None]] = None) -> List[RequestResult]:
        """
        Execute multiple HTTP requests concurrently.
        
        Args:
            configs: List of request configurations
            progress_callback: Optional progress callback
            
        Returns:
            List of request results
        """
        if not configs:
            return []
        
        # Create tasks for all requests
        tasks = []
        for i, config in enumerate(configs):
            request_id = f"req_{i}_{int(time.time() * 1000000)}"
            task = asyncio.create_task(self.execute_request(config, request_id))
            tasks.append(task)
        
        # Execute all requests concurrently
        results = []
        completed = 0
        
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(configs))
            
            except Exception as e:
                # Create error result for failed task
                error_result = RequestResult(
                    request_id=f"failed_{completed}",
                    method="unknown",
                    url="unknown",
                    status_code=0,
                    headers={},
                    body="",
                    response_time=0.0,
                    error=f"Task execution error: {str(e)}",
                    timestamp=time.time()
                )
                results.append(error_result)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(configs))
        
        # Sort results by request ID to maintain order
        results.sort(key=lambda x: x.request_id)
        
        return results
    
    async def execute_request_batch(self, base_config: RequestConfig,
                                 variations: List[Dict[str, Any]],
                                 progress_callback: Optional[Callable[[int, int], None]] = None) -> List[RequestResult]:
        """
        Execute a batch of requests with variations.
        
        Args:
            base_config: Base request configuration
            variations: List of variations to apply
            progress_callback: Optional progress callback
            
        Returns:
            List of request results
        """
        configs = []
        
        for variation in variations:
            # Create a copy of base config
            config_dict = asdict(base_config)
            
            # Apply variation
            for key, value in variation.items():
                if key in config_dict:
                    config_dict[key] = value
            
            # Convert method back to enum
            if isinstance(config_dict["method"], str):
                config_dict["method"] = RequestMethod(config_dict["method"])
            
            config = RequestConfig(**config_dict)
            configs.append(config)
        
        return await self.execute_requests(configs, progress_callback)
    
    async def health_check(self, url: str, timeout: float = 5.0) -> bool:
        """
        Perform a health check on the target URL.
        
        Args:
            url: URL to check
            timeout: Health check timeout
            
        Returns:
            True if healthy, False otherwise
        """
        try:
            config = RequestConfig(
                method=RequestMethod.GET,
                url=url,
                timeout=timeout
            )
            
            result = await self.execute_request(config)
            return result.status_code == 200 and result.error is None
        
        except Exception:
            return False
    
    def _update_stats(self, result: RequestResult):
        """Update internal statistics."""
        self.stats["total_requests"] += 1
        
        if result.error is None:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        self.stats["total_response_time"] += result.response_time
        
        if self.stats["total_requests"] > 0:
            self.stats["avg_response_time"] = self.stats["total_response_time"] / self.stats["total_requests"]
        
        # Update status code distribution
        status = result.status_code
        if status not in self.stats["status_code_distribution"]:
            self.stats["status_code_distribution"][status] = 0
        self.stats["status_code_distribution"][status] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        stats = self.stats.copy()
        
        # Calculate additional metrics
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            stats["error_rate"] = stats["failed_requests"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["error_rate"] = 0.0
        
        # Calculate response time percentiles if we have results
        if self.results:
            response_times = [r.response_time for r in self.results if r.error is None]
            if response_times:
                response_times.sort()
                n = len(response_times)
                stats["p50_response_time"] = response_times[int(n * 0.5)]
                stats["p95_response_time"] = response_times[int(n * 0.95)]
                stats["p99_response_time"] = response_times[int(n * 0.99)]
        
        return stats
    
    def reset_statistics(self):
        """Reset all statistics."""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "status_code_distribution": {}
        }
        self.results.clear()
    
    def get_results_by_status(self, status_code: int) -> List[RequestResult]:
        """Get results filtered by status code."""
        return [r for r in self.results if r.status_code == status_code]
    
    def get_results_by_error(self) -> List[RequestResult]:
        """Get results that had errors."""
        return [r for r in self.results if r.error is not None]
    
    def export_results(self, filename: str, format: str = "json"):
        """
        Export results to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "csv")
        """
        if format.lower() == "json":
            with open(filename, 'w') as f:
                # Convert results to serializable format
                export_data = {
                    "statistics": self.get_statistics(),
                    "results": [asdict(r) for r in self.results]
                }
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            with open(filename, 'w', newline='') as f:
                if self.results:
                    fieldnames = ["request_id", "method", "url", "status_code", 
                                "response_time", "error", "timestamp"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for result in self.results:
                        row = {
                            "request_id": result.request_id,
                            "method": result.method,
                            "url": result.url,
                            "status_code": result.status_code,
                            "response_time": result.response_time,
                            "error": result.error or "",
                            "timestamp": result.timestamp
                        }
                        writer.writerow(row)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def __call__(self, config: RequestConfig) -> RequestResult:
        """Allow the engine to be called directly."""
        return await self.execute_request(config)
