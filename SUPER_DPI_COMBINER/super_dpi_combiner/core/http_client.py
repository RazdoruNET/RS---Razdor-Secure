#!/usr/bin/env python3
"""
HTTP Client - Стабилизированный клиент с реальными сетевыми операциями
Только asyncio, без внешних зависимостей
"""

import asyncio
import ssl
import socket
from typing import Optional
from .contracts import Request, Response

class HTTPClient:
    """Минимальный HTTP клиент с реальными сетевыми операциями"""
    
    def __init__(self):
        self.reader = None
        self.writer = None
        self.ssl_context = ssl.create_default_context()
        
    async def connect(
        self,
        host: str,
        port: int,
        ssl_enabled: bool = False,
        timeout: float = 10.0
    ) -> bool:
        """Подключиться к серверу"""
        try:
            target = (host, port)
            
            if ssl_enabled:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(target, ssl=self.ssl_context),
                    timeout=timeout
                )
            else:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(target),
                    timeout=timeout
                )
                
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
