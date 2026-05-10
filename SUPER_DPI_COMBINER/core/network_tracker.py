#!/usr/bin/env python3
"""
Network Tracker - Helper class for tracking network events in pipelines
Provides easy integration with ExecutionTrace for network operations
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple, Callable
from .execution_trace import ExecutionTrace, EventType

class NetworkTracker:
    """
    Network operation tracker that integrates with ExecutionTrace
    Provides automatic tracking of connection attempts, retries, timeouts, and data transfer
    """
    
    def __init__(self, execution_trace: ExecutionTrace):
        self.trace = execution_trace
        self._connection_contexts: Dict[str, Dict[str, Any]] = {}
    
    async def tracked_connection(self, 
                               host: str, 
                               port: int, 
                               connection_func: Callable,
                               method: str = "TCP",
                               max_retries: int = 3,
                               retry_delay: float = 1.0,
                               timeout: float = 30.0,
                               **kwargs) -> Tuple[Any, bool]:
        """
        Track a connection attempt with automatic retry and timeout tracking
        
        Args:
            host: Target host
            port: Target port
            connection_func: Async function that performs the connection
            method: Connection method (TCP, TLS, etc.)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries
            timeout: Connection timeout
            **kwargs: Additional arguments for connection_func
            
        Returns:
            Tuple[connection_result, success_flag]
        """
        connection_key = f"{host}:{port}"
        attempt = 0
        last_error = None
        
        while attempt <= max_retries:
            attempt += 1
            
            # Track connection attempt
            self.trace.add_connection_attempt(host, port, method, {
                'attempt': attempt,
                'max_retries': max_retries,
                'timeout': timeout
            })
            
            try:
                # Attempt connection with timeout
                connection_result = await asyncio.wait_for(
                    connection_func(**kwargs), 
                    timeout=timeout
                )
                
                # Track successful connection
                self.trace.add_connection_success(host, port, {
                    'attempt': attempt,
                    'connection_type': method
                })
                
                return connection_result, True
                
            except asyncio.TimeoutError:
                last_error = f"Connection timeout after {timeout}s"
                self.trace.add_timeout("connection_attempt", timeout, {
                    'host': host,
                    'port': port,
                    'method': method,
                    'attempt': attempt
                })
                
                if attempt <= max_retries:
                    self.trace.add_retry_attempt("connection", attempt, max_retries, 
                                                f"Timeout after {timeout}s")
                    await asyncio.sleep(retry_delay)
                
            except Exception as e:
                last_error = str(e)
                self.trace.add_connection_failure(host, port, last_error, {
                    'attempt': attempt,
                    'method': method
                })
                
                if attempt <= max_retries:
                    self.trace.add_retry_attempt("connection", attempt, max_retries, 
                                                f"Connection failed: {last_error}")
                    await asyncio.sleep(retry_delay)
        
        # All attempts failed
        self.trace.add_error("CONNECTION_EXHAUSTED", 
                           f"All {max_retries + 1} connection attempts failed for {host}:{port}",
                           {'last_error': last_error, 'total_attempts': attempt})
        
        return None, False
    
    async def tracked_send(self, 
                          host: str, 
                          port: int, 
                          data: bytes, 
                          send_func: Callable,
                          **kwargs) -> bool:
        """
        Track data sending operation
        
        Args:
            host: Target host
            port: Target port
            data: Data to send
            send_func: Async function that sends data
            **kwargs: Additional arguments for send_func
            
        Returns:
            bool: Success flag
        """
        try:
            # Track send attempt
            self.trace.add_network_send(host, port, len(data), {
                'data_type': type(data).__name__,
                'send_function': send_func.__name__
            })
            
            # Perform send
            await send_func(data, **kwargs)
            
            return True
            
        except Exception as e:
            self.trace.add_error("SEND_ERROR", f"Failed to send data to {host}:{port}: {str(e)}", {
                'data_size': len(data),
                'error_type': type(e).__name__
            })
            return False
    
    async def tracked_receive(self, 
                             host: str, 
                             port: int, 
                             receive_func: Callable,
                             max_size: Optional[int] = None,
                             timeout: float = 30.0,
                             **kwargs) -> Tuple[bytes, bool]:
        """
        Track data receiving operation
        
        Args:
            host: Source host
            port: Source port
            receive_func: Async function that receives data
            max_size: Maximum expected size
            timeout: Receive timeout
            **kwargs: Additional arguments for receive_func
            
        Returns:
            Tuple[received_data, success_flag]
        """
        try:
            # Perform receive with timeout
            data = await asyncio.wait_for(receive_func(**kwargs), timeout=timeout)
            
            # Track receive
            self.trace.add_network_receive(host, port, len(data), {
                'data_type': type(data).__name__,
                'receive_function': receive_func.__name__,
                'max_size': max_size,
                'timeout': timeout
            })
            
            return data, True
            
        except asyncio.TimeoutError:
            self.trace.add_timeout("data_receive", timeout, {
                'host': host,
                'port': port,
                'max_size': max_size
            })
            return b"", False
            
        except Exception as e:
            self.trace.add_error("RECEIVE_ERROR", f"Failed to receive data from {host}:{port}: {str(e)}", {
                'error_type': type(e).__name__,
                'max_size': max_size
            })
            return b"", False
    
    def start_operation(self, operation_name: str, details: Dict[str, Any] = None):
        """Start tracking a custom operation"""
        self.trace.add_event(EventType.PIPELINE_START, {
            'operation': operation_name,
            **(details or {})
        })
    
    def end_operation(self, operation_name: str, success: bool, details: Dict[str, Any] = None):
        """End tracking a custom operation"""
        self.trace.add_event(EventType.PIPELINE_END, {
            'operation': operation_name,
            'success': success,
            **(details or {})
        })
    
    def track_custom_event(self, event_type: EventType, details: Dict[str, Any] = None):
        """Track a custom event"""
        self.trace.add_event(event_type, details)
    
    def track_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Track a custom error"""
        self.trace.add_error(error_type, error_message, context)


class TrackedTCPClient:
    """
    Wrapper for TCP client with automatic execution trace integration
    """
    
    def __init__(self, tcp_client, execution_trace: ExecutionTrace):
        self.tcp_client = tcp_client
        self.tracker = NetworkTracker(execution_trace)
    
    async def create_connection(self, host: str, port: int, **kwargs) -> Tuple[Any, bool]:
        """Tracked TCP connection"""
        return await self.tracker.tracked_connection(
            host, port,
            self.tcp_client.create_connection,
            method="TCP",
            **kwargs
        )
    
    async def create_tls_connection(self, host: str, port: int, **kwargs) -> Tuple[Any, bool]:
        """Tracked TLS connection"""
        return await self.tracker.tracked_connection(
            host, port,
            self.tcp_client.create_tls_connection,
            method="TLS",
            **kwargs
        )
    
    async def send_data(self, writer, data: bytes, **kwargs) -> bool:
        """Tracked data send"""
        # Extract host/port from writer if possible
        host = "unknown"
        port = 0
        try:
            transport = writer.get_extra_info('peername')
            if transport:
                host, port = transport
        except:
            pass
        
        return await self.tracker.tracked_send(
            host, port, data,
            self.tcp_client.send_data,
            writer=writer,
            **kwargs
        )
    
    async def close_connection(self, writer, **kwargs):
        """Close connection"""
        try:
            await self.tcp_client.close_connection(writer, **kwargs)
        except Exception as e:
            self.tracker.track_error("CLOSE_ERROR", f"Failed to close connection: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.tcp_client.cleanup()
        except Exception as e:
            self.tracker.track_error("CLEANUP_ERROR", f"Failed to cleanup: {str(e)}")
