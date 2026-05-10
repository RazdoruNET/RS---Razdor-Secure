#!/usr/bin/env python3
"""
DPI-Evading Transparent Proxy Daemon - Интегрированная версия
Интегрирует WIRE_LEVEL_VERIFIED_FRAGMENTATION_RUNTIME с прозрачным прокси
"""

import sys
import asyncio
import socket
import struct
import logging
import signal
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import existing fragmentation runtime
from verification.tcp_segment_working import TCPSegmentAnalyzer

class IntegratedProxyDaemon:
    """Интегрированный прозрачный прокси с wire fragmentation"""
    
    def __init__(self, listen_port=1080, chunk_size=30, chunk_delay=0.005):
        self.listen_port = listen_port
        self.chunk_size = chunk_size
        self.chunk_delay = chunk_delay
        self.running = False
        self.connections = {}
        
        # Используем существующий fragment analyzer
        self.segment_analyzer = TCPSegmentAnalyzer()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('proxy_daemon.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Integrated proxy daemon initialized: port={listen_port}, chunk_size={chunk_size}, chunk_delay={chunk_delay}")
    
    async def handle_client(self, reader, writer):
        """Handle client connection with wire fragmentation"""
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"New client connection from {client_addr}")
        
        try:
            # Extract original destination using existing extractor
            from verification.destination_extractor_final import CrossPlatformDestinationExtractor
            
            extractor = CrossPlatformDestinationExtractor()
            original_dst = extractor.extract_original_destination(writer.get_extra_info().get('socket'))
            
            if not original_dst:
                self.logger.error("Failed to extract original destination")
                writer.close()
                return
            
            self.logger.info(f"Original destination: {original_dst}")
            
            # Connect to upstream server
            upstream_reader, upstream_writer = await self.connect_upstream(original_dst)
            
            if not upstream_reader or not upstream_writer:
                self.logger.error("Failed to connect to upstream")
                writer.close()
                return
            
            # Start bidirectional data forwarding
            await asyncio.gather(
                self.forward_client_to_upstream(reader, writer, upstream_writer),
                self.forward_upstream_to_client(upstream_reader, upstream_writer, writer),
            )
            
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            writer.close()
            self.logger.info(f"Client {client_addr} disconnected")
    
    async def connect_upstream(self, destination):
        """Connect to upstream server"""
        try:
            host, port = destination.split(':')
            port = int(port)
            
            self.logger.info(f"Connecting to upstream: {host}:{port}")
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=10.0
            )
            
            # Apply TCP_NODELAY to upstream connection
            upstream_socket = writer.get_extra_info().get('socket')
            if upstream_socket:
                upstream_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.logger.info("Applied TCP_NODELAY to upstream connection")
            
            self.logger.info(f"Connected to upstream: {host}:{port}")
            return reader, writer
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {destination}: {e}")
            return None, None
    
    async def forward_client_to_upstream(self, reader, writer, upstream_writer):
        """Forward data from client to upstream with wire fragmentation"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                
                self.logger.info(f"Client -> Upstream: {len(data)} bytes")
                
                # Apply wire fragmentation using existing analyzer
                await self.send_fragmented_data(upstream_writer, data)
                
        except Exception as e:
            self.logger.error(f"Error forwarding client to upstream: {e}")
    
    async def forward_upstream_to_client(self, upstream_reader, upstream_writer, writer):
        """Forward data from upstream to client (passthrough mode)"""
        try:
            while True:
                data = await upstream_reader.read(4096)
                if not data:
                    break
                
                self.logger.info(f"Upstream -> Client: {len(data)} bytes")
                
                # Send data back to client without fragmentation (passthrough)
                writer.write(data)
                await writer.drain()
                
        except Exception as e:
            self.logger.error(f"Error forwarding upstream to client: {e}")
    
    async def send_fragmented_data(self, writer, data):
        """Send data with wire-level fragmentation using existing analyzer"""
        total_sent = 0
        fragment_count = 0
        
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            
            # Send chunk with TCP_NODELAY
            writer.write(chunk)
            await writer.drain()
            
            fragment_count += 1
            total_sent += len(chunk)
            
            self.logger.info(f"Sent fragment {fragment_count}: {len(chunk)} bytes")
            
            # Force flush with configurable delay
            if self.chunk_delay > 0:
                await asyncio.sleep(self.chunk_delay)
        
        self.logger.info(f"Fragmentation complete: {fragment_count} fragments, {total_sent} bytes")
    
    async def start_server(self):
        """Start the transparent proxy server"""
        self.logger.info(f"Starting integrated transparent proxy on port {self.listen_port}")
        
        # Create server socket with required options
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.listen_port))
        server_socket.listen(100)
        server_socket.setblocking(False)
        
        # Store server socket for reference
        self.server_socket = server_socket
        
        self.logger.info(f"Integrated transparent proxy server listening on 0.0.0.0:{self.listen_port}")
        
        # Start serving clients
        server = await asyncio.start_server(
            self.handle_client,
            server_socket,
            limit_conns=1000
        )
        
        self.running = True
        self.logger.info("Integrated transparent proxy daemon started successfully")
        
        return server
    
    async def stop_server(self):
        """Stop the transparent proxy server"""
        self.running = False
        self.logger.info("Stopping integrated transparent proxy daemon")
        
        if hasattr(self, 'server') and self.server:
            self.server.close()
            self.logger.info("Integrated transparent proxy daemon stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop_server())

def main():
    """Main daemon entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DPI-Evading Integrated Transparent Proxy Daemon')
    parser.add_argument('--port', type=int, default=1080, help='Listen port (default: 1080)')
    parser.add_argument('--chunk-size', type=int, default=30, help='Fragment chunk size in bytes (default: 30)')
    parser.add_argument('--chunk-delay', type=float, default=0.005, help='Delay between chunks in seconds (default: 0.005)')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create and start integrated daemon
    daemon = IntegratedProxyDaemon(
        listen_port=args.port,
        chunk_size=args.chunk_size,
        chunk_delay=args.chunk_delay
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, daemon.signal_handler)
    signal.signal(signal.SIGINT, daemon.signal_handler)
    
    try:
        # Start the server
        server = asyncio.run(daemon.start_server())
    except KeyboardInterrupt:
        daemon.logger.info("Received interrupt, shutting down...")
    except Exception as e:
        daemon.logger.error(f"Daemon failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
