#!/usr/bin/env python3
"""
Simple HTTP Server for testing DPI bypass functionality
"""

import asyncio
from aiohttp import web
import json
import time

async def handle_request(request):
    """Handle HTTP requests"""
    client_ip = request.remote
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    response_data = {
        'timestamp': time.time(),
        'client_ip': client_ip,
        'user_agent': user_agent,
        'method': request.method,
        'path': request.path,
        'headers': dict(request.headers),
        'message': 'Hello from local HTTP server!'
    }
    
    return web.Response(
        text=json.dumps(response_data, indent=2),
        content_type='application/json',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

async def handle_options(request):
    """Handle CORS preflight requests"""
    return web.Response(
        text='',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

async def main():
    """Main server function"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', handle_request)
    app.router.add_get('/test', handle_request)
    app.router.add_get('/ip', handle_request)
    app.router.add_options('/', handle_options)
    app.router.add_options('/test', handle_options)
    app.router.add_options('/ip', handle_options)
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8081)
    await site.start()
    
    print("🚀 Local HTTP Server started on http://0.0.0.0:8081")
    print("📊 Available endpoints:")
    print("   - GET  http://localhost:8081/")
    print("   - GET  http://localhost:8081/test")
    print("   - GET  http://localhost:8081/ip")
    print("🔗 Use with SOCKS5: curl --socks5-hostname 127.0.0.1:1080 http://localhost:8081/test")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
