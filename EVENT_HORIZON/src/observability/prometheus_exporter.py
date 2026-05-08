"""
Prometheus Exporter

Exports metrics in Prometheus format and provides HTTP endpoint
for Prometheus scraping.
"""

import asyncio
import aiohttp
from aiohttp import web
from typing import Dict, Optional, Any
from .metrics_collector import MetricsCollector


class PrometheusExporter:
    """
    Prometheus metrics exporter with HTTP endpoint.
    """
    
    def __init__(self, metrics_collector: MetricsCollector, 
                 port: int = 8000, host: str = "0.0.0.0"):
        """
        Initialize Prometheus exporter.
        
        Args:
            metrics_collector: Metrics collector instance
            port: HTTP port for exporter
            host: HTTP host for exporter
        """
        self.metrics_collector = metrics_collector
        self.port = port
        self.host = host
        
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get('/metrics', self.metrics_handler)
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/', self.index_handler)
    
    async def metrics_handler(self, request: web.Request) -> web.Response:
        """Handle metrics endpoint."""
        try:
            metrics_data = self.metrics_collector.export_prometheus_format()
            return web.Response(
                text=metrics_data,
                content_type='text/plain; version=0.0.4; charset=utf-8'
            )
        except Exception as e:
            return web.Response(
                text=f"Error generating metrics: {str(e)}",
                status=500,
                content_type='text/plain'
            )
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """Handle health check endpoint."""
        health_data = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "metrics_count": len(self.metrics_collector.get_all_metrics())
        }
        return web.json_response(health_data)
    
    async def index_handler(self, request: web.Request) -> web.Response:
        """Handle index endpoint."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>EVENT_HORIZON Metrics</title>
        </head>
        <body>
            <h1>EVENT_HORIZON Metrics Exporter</h1>
            <p><a href="/metrics">Metrics</a></p>
            <p><a href="/health">Health Check</a></p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def start(self):
        """Start the HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        print(f"Prometheus exporter started on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the HTTP server."""
        if self.runner:
            await self.runner.cleanup()
            print("Prometheus exporter stopped")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
