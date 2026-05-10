#!/usr/bin/env python3
"""
Real HTTP Client for DPI bypass operations
"""

import asyncio
import ssl
import socket
import time
import random
from typing import Dict, Any, Optional, Tuple
import aiohttp
import certifi
from urllib.parse import urlparse

class HTTPClient:
    """Real HTTP client with advanced features for DPI bypass"""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.session = None
        self.connector = None
        
    async def initialize(self):
        """Initialize aiohttp session with custom settings"""
        # Custom SSL context for certificate pinning bypass
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Custom connector with socket options
        self.connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            family=socket.AF_INET,
            enable_cleanup_closed=True
        )
        
        # Session with custom headers and timeout
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=timeout,
            headers={
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
    def _get_random_user_agent(self) -> str:
        """Get random user agent for fingerprint rotation"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return random.choice(user_agents)
    
    async def make_request(self, 
                          method: str, 
                          url: str, 
                          headers: Optional[Dict[str, str]] = None,
                          data: Optional[bytes] = None,
                          params: Optional[Dict[str, str]] = None,
                          allow_redirects: bool = True) -> Tuple[bool, int, Dict[str, str], bytes, float]:
        """
        Make HTTP request with real network operations
        
        Returns:
            Tuple[success, status_code, response_headers, response_data, response_time]
        """
        if not self.session:
            await self.initialize()
            
        start_time = time.time()
        
        try:
            # Merge custom headers with default ones
            request_headers = {}
            if headers:
                request_headers.update(headers)
            
            async with self.session.request(
                method=method,
                url=url,
                headers=request_headers if request_headers else None,
                data=data,
                params=params,
                allow_redirects=allow_redirects,
                ssl=False  # Bypass SSL verification for DPI testing
            ) as response:
                response_data = await response.read()
                response_time = time.time() - start_time
                
                # Convert headers to dict
                response_headers = dict(response.headers)
                
                return True, response.status, response_headers, response_data, response_time
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return False, 408, {}, b"Request timeout", response_time
            
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            return False, 500, {}, f"Client error: {str(e)}".encode(), response_time
            
        except Exception as e:
            response_time = time.time() - start_time
            return False, 500, {}, f"Unexpected error: {str(e)}".encode(), response_time
    
    async def head_request(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, int, Dict[str, str], float]:
        """Make HEAD request for connectivity testing"""
        success, status_code, response_headers, _, response_time = await self.make_request(
            'HEAD', url, headers=headers
        )
        return success, status_code, response_headers, response_time
    
    async def get_request(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, int, Dict[str, str], bytes, float]:
        """Make GET request"""
        return await self.make_request('GET', url, headers=headers)
    
    async def post_request(self, url: str, data: bytes, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, int, Dict[str, str], bytes, float]:
        """Make POST request"""
        return await self.make_request('POST', url, headers=headers, data=data)
    
    async def test_connectivity(self, host: str, port: int = 443) -> bool:
        """Test basic connectivity to host"""
        try:
            # Basic socket connection test
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        if self.connector:
            await self.connector.close()

class TCPClient:
    """Raw TCP client for low-level operations"""
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
    
    async def create_connection(self, host: str, port: int) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Create TCP connection with custom settings"""
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=self.timeout
        )
        
        # Set socket options for DPI bypass
        sock = writer.get_extra_info('socket')
        if sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Set TTL if needed for DPI bypass
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 64)
        
        return reader, writer
    
    async def send_data(self, writer: asyncio.StreamWriter, data: bytes):
        """Send data with error handling"""
        try:
            writer.write(data)
            await writer.drain()
            return True
        except:
            return False
    
    async def receive_data(self, reader: asyncio.StreamReader, max_size: int = 8192) -> bytes:
        """Receive data with timeout"""
        try:
            data = await asyncio.wait_for(
                reader.read(max_size),
                timeout=self.timeout
            )
            return data
        except asyncio.TimeoutError:
            return b""
        except:
            return b""
    
    async def close_connection(self, writer: asyncio.StreamWriter):
        """Close connection properly"""
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
