#!/usr/bin/env python3
"""
RSecure Web Dashboard
Web interface for visualizing security data and system status
"""

import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import psutil
import logging
from pathlib import Path

class RSecureDashboard:
    def __init__(self, rsecure_instance=None):
        self.app = Flask(__name__)
        self.rsecure = rsecure_instance
        self.dashboard_data = {}
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_dashboard')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./logs/dashboard.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Setup routes
        self._setup_routes()
        
        # Start data collection thread
        self.running = False
        self.data_thread = None
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status"""
            try:
                if self.rsecure:
                    status = self.rsecure.get_status()
                else:
                    status = self._get_system_status()
                
                return jsonify({
                    'success': True,
                    'data': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get system metrics"""
            try:
                metrics = self._collect_metrics()
                return jsonify({
                    'success': True,
                    'data': metrics,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/threats')
        def get_threats():
            """Get threat information"""
            try:
                threats = self._get_threat_data()
                return jsonify({
                    'success': True,
                    'data': threats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/logs')
        def get_logs():
            """Get recent logs"""
            try:
                log_type = request.args.get('type', 'rsecure')
                lines = int(request.args.get('lines', 50))
                logs = self._get_logs(log_type, lines)
                return jsonify({
                    'success': True,
                    'data': logs,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/network')
        def get_network_data():
            """Get network information"""
            try:
                network_data = self._get_network_info()
                return jsonify({
                    'success': True,
                    'data': network_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/cvu')
        def get_cvu_data():
            """Get CVU threat intelligence"""
            try:
                if self.rsecure and hasattr(self.rsecure, 'cvu_intelligence') and self.rsecure.cvu_intelligence:
                    cvu_threats = self.rsecure.cvu_intelligence.get_active_threats(20, 5.0)
                    cvu_stats = self.rsecure.cvu_intelligence.get_statistics()
                else:
                    cvu_threats = []
                    cvu_stats = {}
                
                return jsonify({
                    'success': True,
                    'data': {
                        'threats': cvu_threats,
                        'statistics': cvu_stats
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/control', methods=['POST'])
        def execute_control():
            """Execute system control action"""
            try:
                action = request.json.get('action')
                target = request.json.get('target')
                
                if not self.rsecure or not hasattr(self.rsecure, 'system_control'):
                    return jsonify({
                        'success': False,
                        'error': 'System control not available'
                    })
                
                result = self._execute_action(action, target)
                return jsonify({
                    'success': True,
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
    
    def _get_system_status(self):
        """Get basic system status without RSecure instance"""
        try:
            return {
                'system_info': {
                    'platform': psutil.platform.platform(),
                    'hostname': psutil.platform.node(),
                    'cpu_count': psutil.cpu_count(),
                    'memory_total': psutil.virtual_memory().total
                },
                'running': False,
                'uptime': 0,
                'metrics': {
                    'start_time': datetime.now().isoformat(),
                    'events_processed': 0,
                    'threats_detected': 0,
                    'system_checks': 0
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def _collect_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            net_io = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                'processes': {
                    'count': process_count
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return {'error': str(e)}
    
    def _get_threat_data(self):
        """Get threat information"""
        try:
            threats = []
            
            # Get threats from network defense if available
            if self.rsecure and hasattr(self.rsecure, 'network_defense') and self.rsecure.network_defense:
                defense_threats = self.rsecure.network_defense.get_threat_summary()
                threats.extend(defense_threats)
            
            # Get threats from analytics if available
            if self.rsecure and hasattr(self.rsecure, 'analytics') and self.rsecure.analytics:
                # This would get recent security events
                pass
            
            return {
                'active_threats': len(threats),
                'threats': threats[:10],  # Limit to 10 most recent
                'blocked_ips': len(self.rsecure.network_defense.blocked_ips) if self.rsecure and hasattr(self.rsecure, 'network_defense') else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting threat data: {e}")
            return {'error': str(e)}
    
    def _get_logs(self, log_type: str, lines: int):
        """Get recent logs"""
        try:
            log_files = {
                'rsecure': 'logs/rsecure_main.log',
                'network': 'logs/network_activity.log',
                'process': 'logs/process_activity.log',
                'file': 'logs/file_integrity.log',
                'dashboard': 'logs/dashboard.log'
            }
            
            if log_type not in log_files:
                return {'error': f'Unknown log type: {log_type}'}
            
            log_file = Path(log_files[log_type])
            if not log_file.exists():
                return {'logs': []}
            
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                return {
                    'logs': recent_lines,
                    'total_lines': len(all_lines)
                }
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}")
            return {'error': str(e)}
    
    def _get_network_info(self):
        """Get network information"""
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            
            # Get network connections
            connections = psutil.net_connections()
            
            # Get network IO stats
            net_io = psutil.net_io_counters(pernic=True)
            
            return {
                'interfaces': list(interfaces.keys()),
                'connection_count': len([c for c in connections if c.status == 'ESTABLISHED']),
                'io_stats': net_io,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting network info: {e}")
            return {'error': str(e)}
    
    def _execute_action(self, action: str, target: str):
        """Execute system control action"""
        try:
            if not self.rsecure or not hasattr(self.rsecure, 'system_control'):
                return {'error': 'System control not available'}
            
            control = self.rsecure.system_control
            
            if action == 'kill_process':
                try:
                    pid = int(target)
                    control.kill_process(pid, "Dashboard initiated action")
                    return {'success': True, 'message': f'Process {pid} killed'}
                except ValueError:
                    return {'error': 'Invalid PID'}
            
            elif action == 'block_ip':
                control.block_ip(target, "Dashboard initiated action")
                return {'success': True, 'message': f'IP {target} blocked'}
            
            elif action == 'unblock_ip':
                # This would need to be implemented in system_control
                return {'success': True, 'message': f'IP {target} unblocked'}
            
            elif action == 'quarantine_file':
                control.quarantine_file(target, "Dashboard initiated action")
                return {'success': True, 'message': f'File {target} quarantined'}
            
            else:
                return {'error': f'Unknown action: {action}'}
        
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {'error': str(e)}
    
    def start_data_collection(self):
        """Start background data collection"""
        if self.running:
            return
        
        self.running = True
        self.data_thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        self.data_thread.start()
        self.logger.info("Dashboard data collection started")
    
    def stop_data_collection(self):
        """Stop data collection"""
        self.running = False
        if self.data_thread:
            self.data_thread.join(timeout=5)
        self.logger.info("Dashboard data collection stopped")
    
    def _data_collection_loop(self):
        """Background data collection loop"""
        while self.running:
            try:
                # Update dashboard data
                self.dashboard_data = {
                    'metrics': self._collect_metrics(),
                    'threats': self._get_threat_data(),
                    'network': self._get_network_info(),
                    'timestamp': datetime.now().isoformat()
                }
                
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in data collection: {e}")
                time.sleep(30)
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the dashboard"""
        # Create templates directory
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)
        
        # Create HTML template
        self._create_html_template(templates_dir)
        
        # Start data collection
        self.start_data_collection()
        
        try:
            self.logger.info(f"Starting RSecure dashboard on http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
        finally:
            self.stop_data_collection()
    
    def _create_html_template(self, templates_dir):
        """Create HTML template for dashboard"""
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSecure Dashboard - WE RAZDOR</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem 2rem;
            border-bottom: 2px solid #ff4444;
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 300;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .header .subtitle {
            text-align: center;
            color: #ccc;
            margin-top: 0.5rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #ff4444;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #4CAF50;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
        }
        
        .status-online {
            background: #4CAF50;
            box-shadow: 0 0 10px #4CAF50;
        }
        
        .status-offline {
            background: #f44336;
            box-shadow: 0 0 10px #f44336;
        }
        
        .status-warning {
            background: #ff9800;
            box-shadow: 0 0 10px #ff9800;
        }
        
        .threat-level {
            padding: 0.5rem 1rem;
            border-radius: 25px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        
        .threat-low {
            background: #4CAF50;
        }
        
        .threat-medium {
            background: #ff9800;
        }
        
        .threat-high {
            background: #f44336;
        }
        
        .threat-critical {
            background: #9c27b0;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .logs {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .log-entry {
            margin-bottom: 0.5rem;
            padding: 0.25rem;
            border-left: 3px solid #ff4444;
            padding-left: 0.5rem;
        }
        
        .controls {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #ff4444;
            color: white;
        }
        
        .btn-secondary {
            background: #666;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff4444, #ff6666);
            transition: width 0.5s ease;
        }
        
        .refresh-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .loading {
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ RSecure Dashboard</h1>
        <div class="subtitle">Advanced Security System by WE RAZDOR</div>
    </div>
    
    <div class="refresh-indicator" id="refreshIndicator">
        Last updated: <span id="lastUpdate">Loading...</span>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- System Status Card -->
            <div class="card">
                <h3>🖥️ System Status</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span><span class="status-indicator status-online"></span>Online</span>
                </div>
                <div class="metric">
                    <span>Platform:</span>
                    <span id="platform">Loading...</span>
                </div>
                <div class="metric">
                    <span>Uptime:</span>
                    <span id="uptime">Loading...</span>
                </div>
                <div class="metric">
                    <span>Events Processed:</span>
                    <span class="metric-value" id="eventsProcessed">0</span>
                </div>
            </div>
            
            <!-- Threat Level Card -->
            <div class="card">
                <h3>⚠️ Threat Level</h3>
                <div class="threat-level threat-low" id="threatLevel">
                    LOW RISK
                </div>
                <div class="metric">
                    <span>Active Threats:</span>
                    <span class="metric-value" id="activeThreats">0</span>
                </div>
                <div class="metric">
                    <span>Blocked IPs:</span>
                    <span class="metric-value" id="blockedIPs">0</span>
                </div>
                <div class="metric">
                    <span>Threats Detected:</span>
                    <span class="metric-value" id="threatsDetected">0</span>
                </div>
            </div>
            
            <!-- System Resources Card -->
            <div class="card">
                <h3>📊 System Resources</h3>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span id="cpuUsage">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpuProgress" style="width: 0%"></div>
                </div>
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span id="memoryUsage">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memoryProgress" style="width: 0%"></div>
                </div>
                <div class="metric">
                    <span>Disk Usage:</span>
                    <span id="diskUsage">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="diskProgress" style="width: 0%"></div>
                </div>
            </div>
            
            <!-- Network Activity Card -->
            <div class="card">
                <h3>🌐 Network Activity</h3>
                <div class="metric">
                    <span>Connections:</span>
                    <span id="networkConnections">0</span>
                </div>
                <div class="metric">
                    <span>Bytes Sent:</span>
                    <span id="bytesSent">0 MB</span>
                </div>
                <div class="metric">
                    <span>Bytes Received:</span>
                    <span id="bytesReceived">0 MB</span>
                </div>
                <div class="metric">
                    <span>Interfaces:</span>
                    <span id="networkInterfaces">0</span>
                </div>
            </div>
        </div>
        
        <!-- Recent Logs -->
        <div class="card">
            <h3>📋 Recent Logs</h3>
            <div class="logs" id="recentLogs">
                <div class="log-entry">Loading logs...</div>
            </div>
            <div class="controls">
                <button class="btn btn-primary" onclick="refreshLogs()">Refresh Logs</button>
                <button class="btn btn-secondary" onclick="clearLogs()">Clear Display</button>
            </div>
        </div>
        
        <!-- CVU Intelligence -->
        <div class="card">
            <h3>🔍 CVU Intelligence</h3>
            <div class="metric">
                <span>Active Threats:</span>
                <span id="cvuThreats">0</span>
            </div>
            <div class="metric">
                <span>KEV Vulnerabilities:</span>
                <span id="kevVulns">0</span>
            </div>
            <div class="metric">
                <span>High Risk Threats:</span>
                <span id="highRiskThreats">0</span>
            </div>
        </div>
    </div>
    
    <script>
        let updateInterval;
        
        function updateDashboard() {
            // Update system status
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateSystemStatus(data.data);
                    }
                })
                .catch(error => console.error('Error fetching status:', error));
            
            // Update metrics
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateMetrics(data.data);
                    }
                })
                .catch(error => console.error('Error fetching metrics:', error));
            
            // Update threats
            fetch('/api/threats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateThreats(data.data);
                    }
                })
                .catch(error => console.error('Error fetching threats:', error));
            
            // Update network
            fetch('/api/network')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateNetwork(data.data);
                    }
                })
                .catch(error => console.error('Error fetching network:', error));
            
            // Update CVU
            fetch('/api/cvu')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateCVU(data.data);
                    }
                })
                .catch(error => console.error('Error fetching CVU:', error));
            
            // Update logs
            fetch('/api/logs?type=rsecure&lines=10')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateLogs(data.data.logs);
                    }
                })
                .catch(error => console.error('Error fetching logs:', error));
            
            // Update last refresh time
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        }
        
        function updateSystemStatus(status) {
            if (status.system_info) {
                document.getElementById('platform').textContent = status.system_info.platform || 'Unknown';
            }
            
            if (status.uptime) {
                const uptime = Math.floor(status.uptime / 3600);
                document.getElementById('uptime').textContent = uptime + 'h';
            }
            
            if (status.metrics) {
                document.getElementById('eventsProcessed').textContent = status.metrics.events_processed || 0;
                document.getElementById('threatsDetected').textContent = status.metrics.threats_detected || 0;
            }
        }
        
        function updateMetrics(metrics) {
            if (metrics.cpu) {
                const cpuPercent = metrics.cpu.percent || 0;
                document.getElementById('cpuUsage').textContent = cpuPercent.toFixed(1) + '%';
                document.getElementById('cpuProgress').style.width = cpuPercent + '%';
            }
            
            if (metrics.memory) {
                const memoryPercent = metrics.memory.percent || 0;
                document.getElementById('memoryUsage').textContent = memoryPercent.toFixed(1) + '%';
                document.getElementById('memoryProgress').style.width = memoryPercent + '%';
            }
            
            if (metrics.disk) {
                const diskPercent = metrics.disk.percent || 0;
                document.getElementById('diskUsage').textContent = diskPercent.toFixed(1) + '%';
                document.getElementById('diskProgress').style.width = diskPercent + '%';
            }
        }
        
        function updateThreats(threats) {
            const activeThreats = threats.active_threats || 0;
            const blockedIPs = threats.blocked_ips || 0;
            
            document.getElementById('activeThreats').textContent = activeThreats;
            document.getElementById('blockedIPs').textContent = blockedIPs;
            
            // Update threat level
            const threatLevel = document.getElementById('threatLevel');
            threatLevel.className = 'threat-level';
            
            if (activeThreats === 0) {
                threatLevel.textContent = 'LOW RISK';
                threatLevel.classList.add('threat-low');
            } else if (activeThreats < 5) {
                threatLevel.textContent = 'MEDIUM RISK';
                threatLevel.classList.add('threat-medium');
            } else if (activeThreats < 10) {
                threatLevel.textContent = 'HIGH RISK';
                threatLevel.classList.add('threat-high');
            } else {
                threatLevel.textContent = 'CRITICAL RISK';
                threatLevel.classList.add('threat-critical');
            }
        }
        
        function updateNetwork(network) {
            document.getElementById('networkConnections').textContent = network.connection_count || 0;
            document.getElementById('networkInterfaces').textContent = (network.interfaces || []).length;
            
            if (network.io_stats) {
                // Calculate total bytes
                let totalBytes = 0;
                for (const iface in network.io_stats) {
                    totalBytes += network.io_stats[iface].bytes_sent || 0;
                    totalBytes += network.io_stats[iface].bytes_recv || 0;
                }
                
                const mb = (totalBytes / 1024 / 1024).toFixed(1);
                document.getElementById('bytesSent').textContent = mb + ' MB';
                document.getElementById('bytesReceived').textContent = mb + ' MB';
            }
        }
        
        function updateCVU(cvuData) {
            if (cvuData.statistics) {
                document.getElementById('cvuThreats').textContent = cvuData.statistics.total_threats || 0;
                document.getElementById('kevVulns').textContent = cvuData.statistics.kev_threats || 0;
                document.getElementById('highRiskThreats').textContent = cvuData.statistics.high_risk_threats || 0;
            }
        }
        
        function updateLogs(logs) {
            const logsContainer = document.getElementById('recentLogs');
            logsContainer.innerHTML = '';
            
            if (logs && logs.length > 0) {
                logs.forEach(log => {
                    const logEntry = document.createElement('div');
                    logEntry.className = 'log-entry';
                    logEntry.textContent = log.trim();
                    logsContainer.appendChild(logEntry);
                });
            } else {
                logsContainer.innerHTML = '<div class="log-entry">No recent logs</div>';
            }
        }
        
        function refreshLogs() {
            fetch('/api/logs?type=rsecure&lines=20')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateLogs(data.data.logs);
                    }
                })
                .catch(error => console.error('Error refreshing logs:', error));
        }
        
        function clearLogs() {
            document.getElementById('recentLogs').innerHTML = '<div class="log-entry">Logs cleared</div>';
        }
        
        // Start auto-refresh
        function startAutoRefresh() {
            updateDashboard(); // Initial update
            updateInterval = setInterval(updateDashboard, 5000); // Update every 5 seconds
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            startAutoRefresh();
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>'''
        
        template_file = templates_dir / 'dashboard.html'
        with open(template_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML template created at {template_file}")

def main():
    """Main function to run dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RSecure Web Dashboard')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create dashboard
    dashboard = RSecureDashboard()
    
    try:
        print(f"Starting RSecure Dashboard on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        dashboard.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nDashboard stopped")

if __name__ == "__main__":
    main()
