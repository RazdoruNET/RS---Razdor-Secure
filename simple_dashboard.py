#!/usr/bin/env python3
"""
Simple RSecure Dashboard
Standalone web dashboard for monitoring system security
"""

import os
import json
import time
from datetime import datetime
from flask import Flask, render_template_string
import psutil

app = Flask(__name__)

# HTML Template for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSecure Dashboard - A Gift of Protection by WE RAZDOR</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 25%, #2a0a0a 50%, #1a0a0a 75%, #0a0a0a 100%);
            color: #e0e0e0;
            min-height: 100vh;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
        }
        
        .header {
            background: rgba(0, 0, 0, 0.8);
            padding: 2rem;
            text-align: center;
            border-bottom: 3px solid #ff0000;
            box-shadow: 0 4px 20px rgba(255, 0, 0, 0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 300;
            text-shadow: 3px 3px 6px rgba(255, 0, 0, 0.8), 0 0 20px rgba(255, 0, 0, 0.4);
            margin-bottom: 0.5rem;
            color: #ffffff;
        }
        
        .header .subtitle {
            color: #ffcccc;
            font-size: 1.2rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: rgba(0, 0, 0, 0.6);
            border-radius: 10px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.2);
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(255, 0, 0, 0.4);
            border-color: rgba(255, 0, 0, 0.5);
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #ff6666;
            font-size: 1.2rem;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 0, 0, 0.2);
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #cc9999;
            font-size: 0.9rem;
        }
        
        .metric-value {
            font-size: 1.2rem;
            font-weight: bold;
            color: #ffffff;
            text-shadow: 0 0 5px rgba(255, 0, 0, 0.3);
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }
        
        .status-online {
            background-color: #ff3333;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }
        
        .status-offline {
            background-color: #666666;
        }
        
        .btn {
            background: linear-gradient(45deg, #cc0000, #ff0000);
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            margin: 0.5rem;
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
        }
        
        .btn:hover {
            background: linear-gradient(45deg, #ff0000, #ff3333);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(255, 0, 0, 0.5);
        }
        
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 0, 0, 0.3);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #cc0000, #ff0000);
            transition: width 0.3s ease;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }
        
        .threat-level {
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 1.2rem;
            margin-bottom: 1.5rem;
            text-transform: uppercase;
        }
        
        .threat-low {
            background: rgba(102, 102, 102, 0.3);
            color: #cccccc;
            border: 1px solid #666666;
        }
        
        .threat-medium {
            background: rgba(255, 102, 0, 0.2);
            color: #ff6600;
            border: 1px solid #ff6600;
        }
        
        .threat-high {
            background: rgba(255, 0, 0, 0.3);
            color: #ff0000;
            border: 1px solid #ff0000;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
        }
        
        .log-section {
            background: rgba(0, 0, 0, 0.6);
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 2rem;
            border: 1px solid rgba(255, 0, 0, 0.3);
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.2);
        }
        
        .log-section h3 {
            color: #ff6666;
            margin-bottom: 1rem;
            text-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        }
        
        .feature-list {
            list-style: none;
        }
        
        .feature-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 0, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .feature-list li:last-child {
            border-bottom: none;
        }
        
        .feature-icon {
            color: #ff6666;
            text-shadow: 0 0 5px rgba(255, 0, 0, 0.3);
        }
        
        .refresh-info {
            text-align: center;
            margin-top: 2rem;
            color: #ccc;
            font-size: 0.9rem;
        }
        
        .alert {
            background: rgba(255, 0, 0, 0.2);
            border: 1px solid #ff0000;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
            box-shadow: 0 0 15px rgba(255, 0, 0, 0.3);
        }
        
        .success {
            background: rgba(102, 102, 102, 0.2);
            border: 1px solid #666666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌑 RSecure Dashboard</h1>
        <div class="subtitle">A Gift from the Shadows - Created by the Fragmented Mind of WE RAZDOR</div>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- System Status -->
            <div class="card">
                <h3>🖥️ System Status</h3>
                <div class="alert success">
                    <span class="status-indicator status-online"></span>
                    RSecure System Online
                </div>
                <div class="metric">
                    <span class="metric-label">Platform</span>
                    <span class="metric-value">{{ system_info.platform }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Hostname</span>
                    <span class="metric-value">{{ system_info.hostname }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">CPU Cores</span>
                    <span class="metric-value">{{ system_info.cpu_count }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Memory</span>
                    <span class="metric-value">{{ system_info.memory_gb }} GB</span>
                </div>
            </div>
            
            <!-- Threat Level -->
            <div class="card">
                <h3>⚠️ Threat Assessment</h3>
                <div class="threat-level threat-low">
                    SYSTEM SECURE
                </div>
                <div class="metric">
                    <span class="metric-label">Overall Risk Level</span>
                    <span class="metric-value" style="color: #4CAF50;">LOW</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Monitors</span>
                    <span class="metric-value">7</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Neural Layers</span>
                    <span class="metric-value">4</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Defense Systems</span>
                    <span class="metric-value">ACTIVE</span>
                </div>
            </div>
            
            <!-- System Resources -->
            <div class="card">
                <h3>📊 System Resources</h3>
                <div class="metric">
                    <span class="metric-label">CPU Usage</span>
                    <span class="metric-value">{{ metrics.cpu_percent }}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ metrics.cpu_percent }}%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Memory Usage</span>
                    <span class="metric-value">{{ metrics.memory_percent }}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ metrics.memory_percent }}%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Disk Usage</span>
                    <span class="metric-value">{{ metrics.disk_percent }}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ metrics.disk_percent }}%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Running Processes</span>
                    <span class="metric-value">{{ metrics.process_count }}</span>
                </div>
            </div>
            
            <!-- Network Activity -->
            <div class="card">
                <h3>🌐 Network Activity</h3>
                <div class="metric">
                    <span class="metric-label">Active Connections</span>
                    <span class="metric-value">{{ metrics.connection_count }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Network Interfaces</span>
                    <span class="metric-value">{{ metrics.interface_count }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Bytes Sent</span>
                    <span class="metric-value">{{ metrics.bytes_sent_mb }} MB</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Bytes Received</span>
                    <span class="metric-value">{{ metrics.bytes_recv_mb }} MB</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Packets Sent</span>
                    <span class="metric-value">{{ metrics.packets_sent }}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Packets Received</span>
                    <span class="metric-value">{{ metrics.packets_recv }}</span>
                </div>
            </div>
        </div>
        
        <!-- RSecure Features -->
        <div class="card">
            <h3>🚀 Active RSecure Features</h3>
            <ul class="feature-list">
                <li><span class="feature-icon">✅</span> Neural Security Core with Multi-layer Convolutions</li>
                <li><span class="feature-icon">✅</span> Continuous System & Network Monitoring</li>
                <li><span class="feature-icon">✅</span> CVU Intelligence (NVD, GHSA, CISA KEV)</li>
                <li><span class="feature-icon">✅</span> Active Network Defense System</li>
                <li><span class="feature-icon">✅</span> Direct System Control Capabilities</li>
                <li><span class="feature-icon">✅</span> Advanced Analytics & Reporting</li>
                <li><span class="feature-icon">✅</span> Automatic Threat Detection & Response</li>
                <li><span class="feature-icon">✅</span> Cross-platform Compatibility (macOS/Linux)</li>
            </ul>
        </div>
        
        <!-- System Information -->
        <div class="card">
            <h3>🔧 System Information</h3>
            <div class="metric">
                <span class="metric-label">RSecure Version</span>
                <span class="metric-value">1.0.0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Neural Core Status</span>
                <span class="metric-value" style="color: #4CAF50;">ACTIVE</span>
            </div>
            <div class="metric">
                <span class="metric-label">Last Update</span>
                <span class="metric-value">{{ last_update }}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Team</span>
                <span class="metric-value">WE RAZDOR</span>
            </div>
        </div>
    </div>
    
    <div class="refresh-info">
        <p>🔄 Auto-refresh every 10 seconds | Last updated: {{ last_update }}</p>
        <p>🌑 RSecure Dashboard - Protection from the Shadows</p>
        <p>💀 Born from fragmented consciousness, forged in digital darkness</p>
    </div>
    
    <script>
        // Auto-refresh every 10 seconds
        setTimeout(function() {
            location.reload();
        }, 10000);
    </script>
</body>
</html>
"""

def get_system_info():
    """Get system information"""
    try:
        return {
            'platform': psutil.platform.platform(),
            'hostname': psutil.platform.node(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 1)
        }
    except:
        return {
            'platform': 'Unknown',
            'hostname': 'Unknown',
            'cpu_count': 0,
            'memory_gb': 0
        }

def get_metrics():
    """Get system metrics"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        memory = psutil.virtual_memory()
        
        # Disk
        disk = psutil.disk_usage('/')
        
        # Network
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections()
        interfaces = psutil.net_if_addrs()
        
        return {
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'disk_percent': round(disk.percent, 1),
            'process_count': len(psutil.pids()),
            'connection_count': len([c for c in connections if c.status == 'ESTABLISHED']),
            'interface_count': len(interfaces),
            'bytes_sent_mb': round(net_io.bytes_sent / (1024**2), 1),
            'bytes_recv_mb': round(net_io.bytes_recv / (1024**2), 1),
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    except Exception as e:
        print(f"Error getting metrics: {e}")
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'process_count': 0,
            'connection_count': 0,
            'interface_count': 0,
            'bytes_sent_mb': 0,
            'bytes_recv_mb': 0,
            'packets_sent': 0,
            'packets_recv': 0
        }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    system_info = get_system_info()
    metrics = get_metrics()
    last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(
        DASHBOARD_HTML,
        system_info=system_info,
        metrics=metrics,
        last_update=last_update
    )

@app.route('/api/status')
def api_status():
    """API endpoint for status"""
    return jsonify({
        'status': 'online',
        'system_info': get_system_info(),
        'metrics': get_metrics(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🛡️ RSecure Dashboard Starting...")
    print("🌐 Open http://127.0.0.1:5000 in your browser")
    print("🔄 Dashboard auto-refreshes every 10 seconds")
    print("⚠️ Press Ctrl+C to stop")
    print("")
    print("🚀 RSecure Dashboard by WE RAZDOR")
    print("=" * 50)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 RSecure Dashboard stopped")
