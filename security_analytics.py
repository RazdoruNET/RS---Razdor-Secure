#!/usr/bin/env python3
"""
RSecure Analytics and Reporting System
Provides comprehensive analysis, visualization, and reporting of security events
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from collections import defaultdict, deque
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: str
    event_type: str
    severity: str
    source: str
    description: str
    threat_score: float
    confidence: float
    details: Dict
    resolved: bool = False
    response_actions: List[str] = None

@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    indicator: str
    indicator_type: str
    threat_type: str
    confidence: float
    first_seen: str
    last_seen: str
    sources: List[str]
    tags: List[str]

class RSecureAnalytics:
    def __init__(self, db_path: str = "./security_analytics.db", config: Dict = None):
        self.db_path = db_path
        self.config = config or self._get_default_config()
        
        # Initialize database
        self._init_database()
        
        # Data structures
        self.events_buffer = deque(maxlen=10000)
        self.threat_intel = {}
        self.trends_data = defaultdict(list)
        self.metrics_cache = {}
        
        # Setup logging
        self.logger = logging.getLogger('rsecure_analytics')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('./analytics.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Analysis thread
        self.analysis_thread = None
        self.running = False
        
        # Report templates
        self._init_report_templates()
    
    def _get_default_config(self) -> Dict:
        return {
            'analysis_interval': 60,  # seconds
            'trend_window': 24,  # hours
            'alert_threshold': 0.7,
            'report_retention_days': 90,
            'auto_correlation': True,
            'ml_enabled': True,
            'export_formats': ['json', 'html', 'pdf']
        }
    
    def _init_database(self):
        """Initialize SQLite database for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT NOT NULL,
                threat_score REAL NOT NULL,
                confidence REAL NOT NULL,
                details TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                response_actions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Threat intelligence table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threat_intelligence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT NOT NULL,
                indicator_type TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                sources TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(indicator, indicator_type)
            )
        ''')
        
        # Trends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                context TEXT
            )
        ''')
        
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                format TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                period_start TEXT,
                period_end TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_report_templates(self):
        """Initialize report templates"""
        self.html_template = Template('''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { background: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .section { margin: 20px 0; }
        .critical { color: #d32f2f; }
        .high { color: #f57c00; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .chart { margin: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Generated: {{ generated_at }}</p>
        <p>Period: {{ period_start }} to {{ period_end }}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{{ summary }}</p>
        <ul>
            <li>Total Events: {{ total_events }}</li>
            <li>Critical Events: {{ critical_events }}</li>
            <li>High Severity Events: {{ high_events }}</li>
            <li>Average Threat Score: {{ avg_threat_score }}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Top Security Events</h2>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Threat Score</th>
            </tr>
            {% for event in top_events %}
            <tr>
                <td>{{ event.timestamp }}</td>
                <td>{{ event.event_type }}</td>
                <td class="{{ event.severity }}">{{ event.severity }}</td>
                <td>{{ event.description }}</td>
                <td>{{ "%.3f"|format(event.threat_score) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="section">
        <h2>Threat Trends</h2>
        <div class="chart">
            <img src="{{ trends_chart }}" alt="Threat Trends" />
        </div>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {% for recommendation in recommendations %}
            <li>{{ recommendation }}</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
        ''')
    
    def start_analysis(self):
        """Start continuous analysis"""
        if self.running:
            return
        
        self.running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        self.logger.info("RSecure analytics started")
    
    def stop_analysis(self):
        """Stop analysis"""
        self.running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=10)
        self.logger.info("RSecure analytics stopped")
    
    def _analysis_loop(self):
        """Main analysis loop"""
        while self.running:
            try:
                # Process events from buffer
                self._process_events()
                
                # Update trends
                self._update_trends()
                
                # Correlate events
                if self.config['auto_correlation']:
                    self._correlate_events()
                
                # Update metrics cache
                self._update_metrics_cache()
                
                # Generate periodic reports
                if self._should_generate_report():
                    self._generate_periodic_report()
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
            
            time.sleep(self.config['analysis_interval'])
    
    def add_security_event(self, event: SecurityEvent):
        """Add security event for analysis"""
        self.events_buffer.append(event)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events 
            (timestamp, event_type, severity, source, description, threat_score, confidence, details, resolved, response_actions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.timestamp,
            event.event_type,
            event.severity,
            event.source,
            event.description,
            event.threat_score,
            event.confidence,
            json.dumps(event.details),
            int(event.resolved),
            json.dumps(event.response_actions or [])
        ))
        
        conn.commit()
        conn.close()
        
        # Trigger immediate analysis for high-threat events
        if event.threat_score > self.config['alert_threshold']:
            self._trigger_immediate_analysis(event)
    
    def _process_events(self):
        """Process events in buffer"""
        if not self.events_buffer:
            return
        
        # Get recent events
        recent_events = list(self.events_buffer)[-100:]  # Last 100 events
        
        # Analyze patterns
        event_patterns = self._analyze_event_patterns(recent_events)
        
        # Store trends
        for pattern_name, pattern_value in event_patterns.items():
            self._store_trend(pattern_name, pattern_value)
    
    def _analyze_event_patterns(self, events: List[SecurityEvent]) -> Dict:
        """Analyze patterns in security events"""
        patterns = {}
        
        if not events:
            return patterns
        
        # Event type distribution
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        source_counts = defaultdict(int)
        
        for event in events:
            type_counts[event.event_type] += 1
            severity_counts[event.severity] += 1
            source_counts[event.source] += 1
        
        # Calculate rates
        time_window = 3600  # 1 hour
        current_time = datetime.now()
        recent_events = [e for e in events if 
                        (current_time - datetime.fromisoformat(e.timestamp)).total_seconds() < time_window]
        
        patterns['events_per_hour'] = len(recent_events)
        patterns['unique_sources'] = len(source_counts)
        patterns['critical_events_per_hour'] = len([e for e in recent_events if e.severity == 'critical'])
        
        # Calculate average threat score
        if recent_events:
            patterns['avg_threat_score'] = np.mean([e.threat_score for e in recent_events])
            patterns['max_threat_score'] = np.max([e.threat_score for e in recent_events])
        else:
            patterns['avg_threat_score'] = 0.0
            patterns['max_threat_score'] = 0.0
        
        # Detect anomalies
        patterns['anomaly_detected'] = self._detect_anomalies(recent_events)
        
        return patterns
    
    def _detect_anomalies(self, events: List[SecurityEvent]) -> bool:
        """Detect anomalies in events"""
        if len(events) < 10:
            return False
        
        # Check for unusual patterns
        threat_scores = [e.threat_score for e in events]
        
        # Statistical anomaly detection
        mean_score = np.mean(threat_scores)
        std_score = np.std(threat_scores)
        
        # Check if any event is significantly above mean
        for score in threat_scores:
            if score > mean_score + 3 * std_score:
                return True
        
        # Check for burst of events
        if len(events) > 50:  # More than 50 events in recent window
            return True
        
        # Check for multiple critical events
        critical_count = len([e for e in events if e.severity == 'critical'])
        if critical_count > 3:
            return True
        
        return False
    
    def _correlate_events(self):
        """Correlate related security events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent events
        cursor.execute('''
            SELECT * FROM security_events 
            WHERE datetime(timestamp) > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''')
        
        events = cursor.fetchall()
        
        # Simple correlation logic
        correlations = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                if self._events_correlated(event1, event2):
                    correlations.append((event1, event2))
        
        # Store correlations (simplified)
        if correlations:
            self.logger.info(f"Found {len(correlations)} event correlations")
        
        conn.close()
    
    def _events_correlated(self, event1: Tuple, event2: Tuple) -> bool:
        """Check if two events are correlated"""
        # Extract event data
        e1_type, e1_source = event1[2], event1[4]
        e2_type, e2_source = event2[2], event2[4]
        
        # Same source and similar time
        if e1_source == e2_source and e1_type == e2_type:
            return True
        
        # Network and process events from same source
        if (('network' in e1_type and 'process' in e2_type) or 
            ('process' in e1_type and 'network' in e2_type)) and e1_source == e2_source:
            return True
        
        return False
    
    def _update_trends(self):
        """Update trend data"""
        current_time = datetime.now()
        
        # Calculate various metrics
        metrics = self._calculate_metrics()
        
        for metric_name, metric_value in metrics.items():
            self._store_trend(metric_name, metric_value)
            self.trends_data[metric_name].append((current_time, metric_value))
    
    def _calculate_metrics(self) -> Dict:
        """Calculate security metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metrics = {}
        
        # Event counts by severity
        cursor.execute('''
            SELECT severity, COUNT(*) FROM security_events 
            WHERE datetime(timestamp) > datetime('now', '-24 hours')
            GROUP BY severity
        ''')
        
        severity_counts = dict(cursor.fetchall())
        metrics['critical_events_24h'] = severity_counts.get('critical', 0)
        metrics['high_events_24h'] = severity_counts.get('high', 0)
        metrics['medium_events_24h'] = severity_counts.get('medium', 0)
        metrics['low_events_24h'] = severity_counts.get('low', 0)
        
        # Average threat scores
        cursor.execute('''
            SELECT AVG(threat_score), MAX(threat_score) FROM security_events 
            WHERE datetime(timestamp) > datetime('now', '-24 hours')
        ''')
        
        avg_score, max_score = cursor.fetchone()
        metrics['avg_threat_score_24h'] = avg_score or 0.0
        metrics['max_threat_score_24h'] = max_score or 0.0
        
        # Top event types
        cursor.execute('''
            SELECT event_type, COUNT(*) FROM security_events 
            WHERE datetime(timestamp) > datetime('now', '-24 hours')
            GROUP BY event_type ORDER BY COUNT(*) DESC LIMIT 5
        ''')
        
        top_events = dict(cursor.fetchall())
        metrics['top_event_type'] = list(top_events.keys())[0] if top_events else 'none'
        
        conn.close()
        
        return metrics
    
    def _store_trend(self, metric_name: str, metric_value: float):
        """Store trend data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_trends (timestamp, metric_name, metric_value, context)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), metric_name, metric_value, json.dumps({})))
        
        conn.commit()
        conn.close()
    
    def _update_metrics_cache(self):
        """Update metrics cache for quick access"""
        self.metrics_cache = self._calculate_metrics()
    
    def _should_generate_report(self) -> bool:
        """Check if periodic report should be generated"""
        # Generate report every 6 hours
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(generated_at) FROM security_reports 
            WHERE report_type = 'periodic'
        ''')
        
        last_report = cursor.fetchone()[0]
        conn.close()
        
        if not last_report:
            return True
        
        last_time = datetime.fromisoformat(last_report)
        return (datetime.now() - last_time).total_seconds() > 6 * 3600
    
    def _generate_periodic_report(self):
        """Generate periodic security report"""
        report_data = self._generate_report_data('24h')
        
        # Generate HTML report
        html_report = self._generate_html_report(report_data)
        
        # Store report
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_reports 
            (report_type, title, content, format, generated_at, period_start, period_end)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'periodic',
            f"Security Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            html_report,
            'html',
            datetime.now().isoformat(),
            report_data['period_start'],
            report_data['period_end']
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info("Generated periodic RSecure report")
    
    def _generate_report_data(self, period: str) -> Dict:
        """Generate data for security report"""
        # Parse period (e.g., '24h', '7d', '30d')
        if period.endswith('h'):
            hours = int(period[:-1])
            period_start = datetime.now() - timedelta(hours=hours)
        elif period.endswith('d'):
            days = int(period[:-1])
            period_start = datetime.now() - timedelta(days=days)
        else:
            period_start = datetime.now() - timedelta(hours=24)
        
        period_end = datetime.now()
        
        # Get events in period
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM security_events 
            WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
            ORDER BY threat_score DESC
        ''', (period_start.isoformat(), period_end.isoformat()))
        
        events = cursor.fetchall()
        
        # Process events
        total_events = len(events)
        critical_events = len([e for e in events if e[3] == 'critical'])
        high_events = len([e for e in events if e[3] == 'high'])
        avg_threat_score = np.mean([e[6] for e in events]) if events else 0.0
        
        # Top events
        top_events = []
        for event in events[:10]:
            top_events.append({
                'timestamp': event[1],
                'event_type': event[2],
                'severity': event[3],
                'description': event[5],
                'threat_score': event[6]
            })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(events)
        
        conn.close()
        
        return {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_events': total_events,
            'critical_events': critical_events,
            'high_events': high_events,
            'avg_threat_score': avg_threat_score,
            'top_events': top_events,
            'recommendations': recommendations,
            'summary': f"Security monitoring period showed {total_events} events with {critical_events} critical incidents."
        }
    
    def _generate_recommendations(self, events: List) -> List[str]:
        """Generate security recommendations based on events"""
        recommendations = []
        
        if not events:
            return ["No security events detected in the period. System appears secure."]
        
        # Analyze event patterns
        event_types = [e[2] for e in events]
        severities = [e[3] for e in events]
        
        # High-level recommendations
        if 'critical' in severities:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Critical security events detected. Investigate and respond immediately.")
        
        if 'network' in event_types:
            recommendations.append("Review network security configurations and monitor for unusual traffic patterns.")
        
        if 'process' in event_types:
            recommendations.append("Monitor process execution patterns and investigate suspicious activities.")
        
        if 'file' in event_types:
            recommendations.append("Review file integrity monitoring results and investigate unauthorized modifications.")
        
        # Specific recommendations based on event counts
        if len(events) > 100:
            recommendations.append("High volume of security events detected. Consider tuning detection thresholds to reduce noise.")
        
        if len(set(event_types)) > 5:
            recommendations.append("Multiple types of security events detected. Conduct comprehensive security assessment.")
        
        return recommendations
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML security report"""
        return self.html_template.render(
            title="RSecure Analytics Report",
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            period_start=report_data['period_start'],
            period_end=report_data['period_end'],
            summary=report_data['summary'],
            total_events=report_data['total_events'],
            critical_events=report_data['critical_events'],
            high_events=report_data['high_events'],
            avg_threat_score=f"{report_data['avg_threat_score']:.3f}",
            top_events=report_data['top_events'],
            trends_chart="trends.png",  # Placeholder
            recommendations=report_data['recommendations']
        )
    
    def _trigger_immediate_analysis(self, event: SecurityEvent):
        """Trigger immediate analysis for high-threat events"""
        self.logger.warning(f"Immediate analysis triggered for high-threat event: {event.event_type}")
        
        # Perform correlation analysis
        self._correlate_events()
        
        # Check for related threat intelligence
        self._check_threat_intelligence(event)
    
    def _check_threat_intelligence(self, event: SecurityEvent):
        """Check event against threat intelligence"""
        # Extract indicators from event
        indicators = self._extract_indicators(event)
        
        for indicator in indicators:
            if indicator in self.threat_intel:
                intel = self.threat_intel[indicator]
                self.logger.info(f"Event matches threat intelligence: {intel}")
    
    def _extract_indicators(self, event: SecurityEvent) -> List[str]:
        """Extract IoC indicators from event"""
        indicators = []
        
        # Extract IPs, domains, file hashes from event details
        details = event.details
        
        if 'remote_address' in details:
            indicators.append(details['remote_address'])
        
        if 'file_hash' in details:
            indicators.append(details['file_hash'])
        
        if 'domain' in details:
            indicators.append(details['domain'])
        
        return indicators
    
    def get_dashboard_data(self) -> Dict:
        """Get data for security dashboard"""
        return {
            'current_metrics': self.metrics_cache,
            'recent_events': list(self.events_buffer)[-20:],
            'threat_level': self._calculate_overall_threat_level(),
            'trends': dict(list(self.trends_data.items())[:10])
        }
    
    def _calculate_overall_threat_level(self) -> str:
        """Calculate overall system threat level"""
        if not self.metrics_cache:
            return 'low'
        
        critical = self.metrics_cache.get('critical_events_24h', 0)
        high = self.metrics_cache.get('high_events_24h', 0)
        avg_score = self.metrics_cache.get('avg_threat_score_24h', 0)
        
        if critical > 0:
            return 'critical'
        elif high > 5 or avg_score > 0.8:
            return 'high'
        elif high > 0 or avg_score > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def export_report(self, report_id: int, format_type: str = 'json') -> str:
        """Export security report in specified format"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM security_reports WHERE id = ?', (report_id,))
        report = cursor.fetchone()
        
        conn.close()
        
        if not report:
            return None
        
        if format_type == 'json':
            return json.dumps({
                'id': report[0],
                'report_type': report[1],
                'title': report[2],
                'content': report[3],
                'format': report[4],
                'generated_at': report[5],
                'period_start': report[6],
                'period_end': report[7]
            }, indent=2)
        else:
            return report[3]  # Return content as-is for HTML/PDF

if __name__ == "__main__":
    # Example usage
    analytics = RSecureAnalytics()
    analytics.start_analysis()
    
    # Example event
    event = SecurityEvent(
        timestamp=datetime.now().isoformat(),
        event_type="network_intrusion",
        severity="high",
        source="neural_core",
        description="Suspicious network connection detected",
        threat_score=0.85,
        confidence=0.92,
        details={"remote_address": "192.168.1.100:4444", "process": "unknown"}
    )
    
    analytics.add_security_event(event)
    
    try:
        while True:
            dashboard = analytics.get_dashboard_data()
            print(f"Threat Level: {dashboard['threat_level']}")
            time.sleep(30)
    except KeyboardInterrupt:
        analytics.stop_analysis()
