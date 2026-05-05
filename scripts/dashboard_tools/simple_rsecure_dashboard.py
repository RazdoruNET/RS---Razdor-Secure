#!/usr/bin/env python3
"""
Simple RSecure Dashboard with Ollama Integration
Lightweight web dashboard connected to Docker Ollama
"""

import os
import sys
import json
import time
import threading
import requests
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
import logging

# Simple HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSecure Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #00ff88; font-size: 2.5em; text-shadow: 0 0 10px rgba(0,255,136,0.3); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(0,255,136,0.3); border-radius: 10px; padding: 20px; }
        .card h3 { color: #00ff88; margin-bottom: 15px; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-label { color: #888; }
        .metric-value { color: #fff; font-weight: bold; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-online { background: #00ff88; }
        .status-offline { background: #ff4444; }
        .status-warning { background: #ffaa00; }
        .controls { background: rgba(255,255,255,0.05); border: 1px solid rgba(0,255,136,0.3); border-radius: 10px; padding: 20px; margin-bottom: 30px; }
        .btn { background: #00ff88; color: #000; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; font-weight: bold; }
        .btn:hover { background: #00cc66; }
        .btn-danger { background: #ff4444; color: #fff; }
        .btn-danger:hover { background: #cc0000; }
        .logs { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; max-height: 400px; overflow-y: auto; }
        .log-entry { margin: 5px 0; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 5px; font-family: monospace; font-size: 12px; }
        .log-time { color: #888; margin-right: 10px; }
        .log-level-INFO { color: #00ff88; }
        .log-level-WARNING { color: #ffaa00; }
        .log-level-ERROR { color: #ff4444; }
        .models-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; }
        .model-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(0,255,136,0.3); border-radius: 8px; padding: 15px; }
        .model-name { color: #00ff88; font-weight: bold; margin-bottom: 5px; }
        .model-size { color: #888; font-size: 12px; }
        .test-section { background: rgba(255,255,255,0.05); border: 1px solid rgba(0,255,136,0.3); border-radius: 10px; padding: 20px; margin: 20px 0; }
        .test-input { width: 100%; padding: 10px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); border-radius: 5px; color: #fff; margin: 10px 0; }
        .test-result { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); border-radius: 5px; padding: 15px; margin: 10px 0; font-family: monospace; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ RSECURE DASHBOARD</h1>
            <p style="color: #888;">Интеграция с Docker Ollama - Система безопасности</p>
        </div>

        <div class="status-grid">
            <div class="card">
                <h3>🤖 Ollama Статус</h3>
                <div class="metric">
                    <span class="metric-label">Сервис:</span>
                    <span class="metric-value"><span class="status-indicator status-online"></span>Активен</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Модели:</span>
                    <span class="metric-value" id="model-count">5 моделей</span>
                </div>
                <div class="metric">
                    <span class="metric-label">API:</span>
                    <span class="metric-value">localhost:11434</span>
                </div>
            </div>

            <div class="card">
                <h3>🔐 Безопасность</h3>
                <div class="metric">
                    <span class="metric-label">Событий обработано:</span>
                    <span class="metric-value" id="events-count">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Угроз обнаружено:</span>
                    <span class="metric-value" id="threats-count">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Уровень защиты:</span>
                    <span class="metric-value" id="protection-level">Активна</span>
                </div>
            </div>

            <div class="card">
                <h3>📊 Система</h3>
                <div class="metric">
                    <span class="metric-label">Время работы:</span>
                    <span class="metric-value" id="uptime">0:00:00</span>
                </div>
                <div class="metric">
                    <span class="metric-label">CPU:</span>
                    <span class="metric-value" id="cpu-usage">0%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Память:</span>
                    <span class="metric-value" id="memory-usage">0%</span>
                </div>
            </div>
        </div>

        <div class="controls">
            <h3>🎮 Управление</h3>
            <button class="btn" onclick="refreshStatus()">🔄 Обновить статус</button>
            <button class="btn" onclick="showModels()">📦 Показать модели</button>
            <button class="btn" onclick="testSecurity()">🧪 Тест безопасности</button>
            <button class="btn btn-danger" onclick="testDPI()">🔓 Тест DPI обхода</button>
        </div>

        <div class="test-section" id="test-section" style="display: none;">
            <h3>🧪 Тестирование</h3>
            <textarea class="test-input" id="test-input" placeholder="Введите описание события безопасности...">Обнаружена подозрительная сетевая активность с неизвестного IP адреса</textarea>
            <button class="btn" onclick="runTest()">🔍 Анализировать</button>
            <div class="test-result" id="test-result"></div>
        </div>

        <div class="models-grid" id="models-grid" style="display: none;">
            <h3>📦 Доступные модели</h3>
            <div id="models-container"></div>
        </div>

        <div class="logs">
            <h3>📋 Логи событий</h3>
            <div id="logs-container"></div>
        </div>
    </div>

    <script>
        let startTime = Date.now();
        let eventCount = 0;
        let threatCount = 0;

        function updateMetrics() {
            const uptime = Date.now() - startTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // Simulate system metrics
            document.getElementById('cpu-usage').textContent = Math.floor(Math.random() * 30 + 10) + '%';
            document.getElementById('memory-usage').textContent = Math.floor(Math.random() * 40 + 20) + '%';
            
            document.getElementById('events-count').textContent = eventCount;
            document.getElementById('threats-count').textContent = threatCount;
        }

        function addLog(level, message) {
            const logsContainer = document.getElementById('logs-container');
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            
            const time = new Date().toLocaleTimeString();
            logEntry.innerHTML = `<span class="log-time">${time}</span><span class="log-level-${level}">[${level}]</span> ${message}`;
            
            logsContainer.insertBefore(logEntry, logsContainer.firstChild);
            
            // Keep only last 20 logs
            while (logsContainer.children.length > 20) {
                logsContainer.removeChild(logsContainer.lastChild);
            }
        }

        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                if (data.success) {
                    addLog('INFO', 'Статус обновлен успешно');
                    eventCount++;
                } else {
                    addLog('ERROR', 'Ошибка обновления статуса: ' + data.error);
                }
            } catch (error) {
                addLog('ERROR', 'Ошибка подключения: ' + error.message);
            }
            
            updateMetrics();
        }

        async function showModels() {
            const modelsSection = document.getElementById('models-grid');
            const testSection = document.getElementById('test-section');
            
            modelsSection.style.display = modelsSection.style.display === 'none' ? 'block' : 'none';
            testSection.style.display = 'none';

            if (modelsSection.style.display === 'block') {
                try {
                    const response = await fetch('/api/models');
                    const data = await response.json();
                    
                    const container = document.getElementById('models-container');
                    container.innerHTML = '';
                    
                    if (data.success) {
                        data.models.forEach(model => {
                            const modelCard = document.createElement('div');
                            modelCard.className = 'model-card';
                            modelCard.innerHTML = `
                                <div class="model-name">${model.name}</div>
                                <div class="model-size">${model.size}</div>
                            `;
                            container.appendChild(modelCard);
                        });
                        
                        addLog('INFO', 'Загружено ' + data.models.length + ' моделей');
                    }
                } catch (error) {
                    addLog('ERROR', 'Ошибка загрузки моделей: ' + error.message);
                }
            }
        }

        function testSecurity() {
            const testSection = document.getElementById('test-section');
            const modelsSection = document.getElementById('models-grid');
            
            testSection.style.display = testSection.style.display === 'none' ? 'block' : 'none';
            modelsSection.style.display = 'none';
            
            document.getElementById('test-input').value = 'Обнаружена подозрительная сетевая активность с неизвестного IP адреса';
        }

        function testDPI() {
            const testSection = document.getElementById('test-section');
            const modelsSection = document.getElementById('models-grid');
            
            testSection.style.display = testSection.style.display === 'none' ? 'block' : 'none';
            modelsSection.style.display = 'none';
            
            document.getElementById('test-input').value = 'Обнаружена попытка обхода DPI через TLS SNI splitting';
        }

        async function runTest() {
            const input = document.getElementById('test-input').value;
            const resultDiv = document.getElementById('test-result');
            
            if (!input.trim()) {
                addLog('WARNING', 'Пустой запрос для анализа');
                return;
            }
            
            resultDiv.textContent = 'Анализ...';
            addLog('INFO', 'Запуск анализа безопасности');
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: input })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.textContent = JSON.stringify(data.result, null, 2);
                    addLog('INFO', 'Анализ завершен успешно');
                    
                    if (data.result.threat_level && data.result.threat_level !== 'low') {
                        threatCount++;
                        addLog('WARNING', 'Обнаружена угроза: ' + data.result.threat_level);
                    }
                } else {
                    resultDiv.textContent = 'Ошибка: ' + data.error;
                    addLog('ERROR', 'Ошибка анализа: ' + data.error);
                }
            } catch (error) {
                resultDiv.textContent = 'Ошибка подключения: ' + error.message;
                addLog('ERROR', 'Ошибка подключения: ' + error.message);
            }
            
            updateMetrics();
        }

        // Auto-update metrics
        setInterval(updateMetrics, 1000);
        
        // Initial setup
        addLog('INFO', 'RSecure Dashboard запущен');
        addLog('INFO', 'Подключение к Docker Ollama: localhost:11434');
        updateMetrics();
    </script>
</body>
</html>
"""

class SimpleRSecureDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.setup_logging()
        
        # Metrics
        self.start_time = datetime.now()
        self.events_processed = 0
        self.threats_detected = 0
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return DASHBOARD_HTML
        
        @self.app.route('/api/status')
        def get_status():
            try:
                # Check Ollama status
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                ollama_status = response.status_code == 200
                
                return jsonify({
                    'success': True,
                    'data': {
                        'ollama_status': 'online' if ollama_status else 'offline',
                        'uptime': str(datetime.now() - self.start_time),
                        'events_processed': self.events_processed,
                        'threats_detected': self.threats_detected,
                        'timestamp': datetime.now().isoformat()
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/models')
        def get_models():
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get('models', []):
                        size_gb = model.get('size', 0) / (1024**3)
                        models.append({
                            'name': model['name'],
                            'size': f'{size_gb:.1f} GB'
                        })
                    
                    return jsonify({
                        'success': True,
                        'models': models
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Ollama returned HTTP {response.status_code}'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/analyze', methods=['POST'])
        def analyze_security():
            try:
                data = request.get_json()
                prompt = data.get('prompt', '')
                
                if not prompt:
                    return jsonify({
                        'success': False,
                        'error': 'Empty prompt'
                    })
                
                # Use rsecure-security model
                payload = {
                    "model": "rsecure-security",
                    "prompt": f"Analyze this security event: {prompt}",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                }
                
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis_text = result.get('response', '')
                    
                    # Try to parse JSON response
                    try:
                        start_idx = analysis_text.find('{')
                        end_idx = analysis_text.rfind('}') + 1
                        if start_idx != -1 and end_idx != -1:
                            json_str = analysis_text[start_idx:end_idx]
                            analysis = json.loads(json_str)
                        else:
                            analysis = {"raw_analysis": analysis_text}
                    except json.JSONDecodeError:
                        analysis = {"raw_analysis": analysis_text}
                    
                    self.events_processed += 1
                    
                    # Check for threats
                    threat_level = analysis.get('threat_level', 'low').lower()
                    if threat_level in ['medium', 'high', 'critical']:
                        self.threats_detected += 1
                    
                    return jsonify({
                        'success': True,
                        'result': analysis
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Ollama request failed: HTTP {response.status_code}'
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the dashboard"""
        self.logger.info(f"🌐 Starting RSecure Dashboard on http://{host}:{port}")
        self.logger.info("🤖 Connected to Docker Ollama at localhost:11434")
        self.logger.info("🛡️ RSecure Security System Active")
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Main function"""
    print("🛡️ RSECURE DASHBOARD")
    print("=" * 50)
    print("🌐 Веб-интерфейс системы безопасности")
    print("🤖 Интеграция с Docker Ollama")
    print("🔐 Анализ угроз в реальном времени")
    print("=" * 50)
    
    dashboard = SimpleRSecureDashboard()
    
    try:
        dashboard.run(host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n🛑 Остановка дашборда...")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
