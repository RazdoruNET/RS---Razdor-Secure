#!/usr/bin/env python3
"""
Web GUI Dashboard - Асинхронный веб-интерфейс реального времени
"""

import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import parse_qs

class WebGuiServer:
    """Асинхронный веб-сервер для дашборда"""
    
    def __init__(self, orchestrator, port: int = 8080):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.orchestrator = orchestrator
        self.port = port
        self.enabled = os.getenv('WEB_GUI_ENABLED', 'false').lower() in ('true', '1', 'yes')
        
        self.logger.info(f"WebGuiServer initialized: enabled={self.enabled}, port={self.port}")
    
    async def start(self):
        """Запуск веб-сервера"""
        if not self.enabled:
            self.logger.info("Web GUI disabled")
            return None
        
        self.server = await asyncio.start_server(
            self.handle_request,
            '0.0.0.0',
            self.port
        )
        
        self.logger.info(f"Web GUI server started on http://0.0.0.0:{self.port}")
        
        # Возвращаем сервер без блокировки - он будет работать в фоне
        return self.server
    
    async def handle_request(self, reader, writer):
        """Обработка HTTP запросов"""
        try:
            # Читаем запрос
            request_line = await reader.readline()
            if not request_line:
                return
            
            request = request_line.decode().strip()
            method, path, _ = request.split(' ')
            
            # Читаем заголовки
            headers = {}
            while True:
                line = await reader.readline()
                if line == b'\r\n':
                    break
                header_line = line.decode().strip()
                if ': ' in header_line:
                    key, value = header_line.split(': ', 1)
                    headers[key.lower()] = value
            
            # Читаем тело запроса если есть
            content_length = int(headers.get('content-length', 0))
            body = b''
            if content_length > 0:
                body = await reader.read(content_length)
            
            # Обрабатываем запрос
            self.logger.info(f"[WEB GUI] Request: {method} {path}")
            response = await self.route_request(method, path, headers, body)
            self.logger.info(f"[WEB GUI] Response length: {len(response)}")
            
            # Отправляем ответ
            writer.write(response.encode())
            await writer.drain()
            
        except Exception as e:
            self.logger.error(f"Web GUI request error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def route_request(self, method: str, path: str, headers: Dict[str, str], body: bytes) -> str:
        """Роутинг запросов"""
        if method == 'GET' and path == '/':
            return await self.serve_dashboard()
        elif method == 'GET' and path == '/api/status':
            return await self.serve_status_api()
        elif method == 'POST' and path == '/api/import':
            return await self.serve_import_api(headers, body)
        else:
            return self.make_response(404, 'Not Found')
    
    async def serve_dashboard(self) -> str:
        """Отдача HTML дашборда"""
        html = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DPI Proxy Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e4e4e7;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        
        .header h1 {
            color: white;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            color: rgba(255,255,255,0.9);
            font-size: 1.1em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: #1a1f3a;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #2d3748;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
        }
        
        .stat-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .stat-card .value {
            font-size: 2.2em;
            font-weight: bold;
            color: #4ade80;
            margin-bottom: 5px;
        }
        
        .stat-card .description {
            color: #9ca3af;
            font-size: 0.9em;
        }
        
        .domains-section {
            background: #1a1f3a;
            border-radius: 12px;
            padding: 25px;
            border: 1px solid #2d3748;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        
        .domains-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .domains-header h2 {
            color: #e4e4e7;
            font-size: 1.8em;
        }
        
        .import-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .import-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        .import-form {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #e4e4e7;
            font-weight: 500;
        }
        
        .form-group textarea {
            width: 100%;
            height: 150px;
            background: #1a1f3a;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 12px;
            color: #e4e4e7;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
            resize: vertical;
        }
        
        .form-buttons {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.95em;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-secondary {
            background: #6b7280;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .domains-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .domains-table th,
        .domains-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #2d3748;
        }
        
        .domains-table th {
            background: #0f172a;
            color: #667eea;
            font-weight: 600;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .domains-table tr:hover {
            background: #0f172a;
        }
        
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-stable {
            background: #10b981;
            color: white;
        }
        
        .status-unstable {
            background: #f59e0b;
            color: white;
        }
        
        .status-mutating {
            background: #8b5cf6;
            color: white;
        }
        
        .status-passthrough {
            background: #6b7280;
            color: white;
        }
        
        .pipeline-modules {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 5px;
        }
        
        .module-tag {
            background: #1e293b;
            color: #60a5fa;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 500;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #9ca3af;
            font-size: 1.1em;
        }
        
        .error {
            background: #dc2626;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .success {
            background: #10b981;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .updating {
            animation: pulse 2s infinite;
        }
        
        .history-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75em;
            transition: all 0.3s ease;
        }
        
        .history-btn:hover {
            background: #764ba2;
            transform: translateY(-1px);
        }
        
        .history-row {
            display: none;
            background: #0f172a;
        }
        
        .history-row.visible {
            display: table-row;
        }
        
        .history-table {
            width: 100%;
            margin: 10px 0;
            border-collapse: collapse;
            background: #1a1f3a;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .history-table th,
        .history-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #2d3748;
            font-size: 0.85em;
        }
        
        .history-table th {
            background: #0f172a;
            color: #667eea;
            font-weight: 600;
        }
        
        .history-table tr:last-child td {
            border-bottom: none;
        }
        
        .history-timestamp {
            color: #9ca3af;
            font-size: 0.8em;
        }
        
        .history-error {
            color: #f59e0b;
            font-weight: 500;
        }
        
        .history-solution {
            color: #10b981;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ SUPER DPI COMBINER</h1>
            <p>Мониторинг и управление стратегиями обхода в реальном времени</p>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <h3>🌐 Активные домены</h3>
                <div class="value" id="activeDomains">0</div>
                <div class="description">Всего доменов в кэше</div>
            </div>
            
            <div class="stat-card">
                <h3>🔄 Успешные сессии</h3>
                <div class="value" id="successfulSessions">0</div>
                <div class="description">Завершено успешно</div>
            </div>
            
            <div class="stat-card">
                <h3>⚠️ Сбросы соединений</h3>
                <div class="value" id="failedSessions">0</div>
                <div class="description">Обнаружено DPI</div>
            </div>
            
            <div class="stat-card">
                <h3>📊 Стабильные стратегии</h3>
                <div class="value" id="stableStrategies">0</div>
                <div class="description">Рабочие конфигурации</div>
            </div>
        </div>
        
        <div class="domains-section">
            <div class="domains-header">
                <h2>🗺️ Карта доменов</h2>
                <button class="import-btn" onclick="toggleImportForm()">📥 Импорт стратегий</button>
            </div>
            
            <div class="import-form" id="importForm">
                <div class="form-group">
                    <label for="strategyData">JSON с матрицей стратегий:</label>
                    <textarea id="strategyData" placeholder='{"youtube.com": {"status": "STABLE", "successful_pipeline": ["sni_modifier", "jitter_fragmentation"]}}'></textarea>
                </div>
                <div class="form-buttons">
                    <button class="btn btn-primary" onclick="importStrategies()">Импортировать</button>
                    <button class="btn btn-secondary" onclick="toggleImportForm()">Отмена</button>
                </div>
            </div>
            
            <div id="messageArea"></div>
            
            <table class="domains-table" id="domainsTable">
                <thead>
                    <tr>
                        <th>Домен</th>
                        <th>Статус</th>
                        <th>Активный пайплайн</th>
                        <th>Успешных сессий</th>
                        <th>Сбоев</th>
                        <th>Последний сброс</th>
                        <th>История</th>
                    </tr>
                </thead>
                <tbody id="domainsTableBody">
                    <tr>
                        <td colspan="7" class="loading">Загрузка данных...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let updateInterval;
        
        function toggleImportForm() {
            const form = document.getElementById('importForm');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }
        
        function showMessage(message, type = 'error') {
            const messageArea = document.getElementById('messageArea');
            messageArea.innerHTML = `<div class="${type}">${message}</div>`;
            setTimeout(() => {
                messageArea.innerHTML = '';
            }, 5000);
        }
        
        function toggleHistory(domain) {
            const historyRow = document.getElementById(`history-${domain}`);
            historyRow.classList.toggle('visible');
        }
        
        async function importStrategies() {
            const data = document.getElementById('strategyData').value;
            
            try {
                JSON.parse(data); // Валидация JSON
                
                const response = await fetch('/api/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: data
                });
                
                if (response.ok) {
                    showMessage('✅ Стратегии успешно импортированы!', 'success');
                    toggleImportForm();
                    document.getElementById('strategyData').value = '';
                    updateDashboard(); // Обновляем сразу
                } else {
                    showMessage('❌ Ошибка при импорте стратегий', 'error');
                }
            } catch (e) {
                showMessage('❌ Неверный формат JSON', 'error');
            }
        }
        
        async function updateDashboard() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Обновляем статистику
                document.getElementById('activeDomains').textContent = data.total_domains || 0;
                
                let successful = 0;
                let failed = 0;
                let stable = 0;
                
                Object.values(data.domains || {}).forEach(domain => {
                    successful += domain.successful_connections || 0;
                    failed += domain.failed_connections || 0;
                    if (domain.status === 'STABLE') stable++;
                });
                
                document.getElementById('successfulSessions').textContent = successful;
                document.getElementById('failedSessions').textContent = failed;
                document.getElementById('stableStrategies').textContent = stable;
                
                // Обновляем таблицу доменов
                const tbody = document.getElementById('domainsTableBody');
                tbody.innerHTML = '';
                
                Object.entries(data.domains || {}).forEach(([domain, info]) => {
                    const row = document.createElement('tr');
                    
                    const statusClass = `status-${(info.status || 'unknown').toLowerCase()}`;
                    const statusText = info.status || 'UNKNOWN';
                    
                    const modules = (info.pipeline_modules || []).map(module => 
                        `<span class="module-tag">${module}</span>`
                    ).join('');
                    
                    const history = info.mutation_history || [];
                    const hasHistory = history.length > 0;
                    
                    row.innerHTML = `
                        <td><strong>${domain}</strong></td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                        <td><div class="pipeline-modules">${modules}</div></td>
                        <td>${info.successful_connections || 0}</td>
                        <td>${info.failed_connections || 0}</td>
                        <td>${info.drop_reason || '-'}</td>
                        <td>
                            ${hasHistory ? `<button class="history-btn" onclick="toggleHistory('${domain}')">📜 История (${history.length})</button>` : '-'}
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                    
                    // Добавляем скрытую строку с историей мутаций
                    if (hasHistory) {
                        const historyRow = document.createElement('tr');
                        historyRow.id = `history-${domain}`;
                        historyRow.className = 'history-row';
                        
                        let historyHtml = '<table class="history-table"><thead><tr><th>Время</th><th>Упавший пайплайн</th><th>Ошибка</th><th>Решение</th></tr></thead><tbody>';
                        
                        history.forEach(event => {
                            const timestamp = new Date(event.timestamp).toLocaleString('ru-RU');
                            const failedPipeline = event.failed_pipeline ? event.failed_pipeline.join(', ') : '-';
                            const errorReason = event.error_reason || '-';
                            const mutatedTo = event.mutated_to_pipeline ? event.mutated_to_pipeline.join(', ') : '-';
                            
                            historyHtml += `
                                <tr>
                                    <td class="history-timestamp">${timestamp}</td>
                                    <td>${failedPipeline}</td>
                                    <td class="history-error">${errorReason}</td>
                                    <td class="history-solution">${mutatedTo}</td>
                                </tr>
                            `;
                        });
                        
                        historyHtml += '</tbody></table>';
                        historyRow.innerHTML = `<td colspan="7">${historyHtml}</td>`;
                        tbody.appendChild(historyRow);
                    }
                });
                
                if (Object.keys(data.domains || {}).length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #9ca3af;">Нет данных о доменах</td></tr>';
                }
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
                document.getElementById('domainsTableBody').innerHTML = 
                    '<tr><td colspan="7" style="text-align: center; color: #dc2626;">Ошибка загрузки данных</td></tr>';
            }
        }
        
        // Запускаем обновление каждые 2 секунды
        function startAutoUpdate() {
            updateDashboard();
            updateInterval = setInterval(updateDashboard, 2000);
        }
        
        // Останавливаем обновление при уходе со страницы
        window.addEventListener('beforeunload', () => {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
        
        // Запускаем при загрузке страницы
        document.addEventListener('DOMContentLoaded', startAutoUpdate);
    </script>
</body>
</html>
        """
        
        return self.make_response(200, html, 'text/html')
    
    async def serve_status_api(self) -> str:
        """API endpoint для получения статуса"""
        # Путь к файлу матрицы (должен совпадать с MATRIX_EXPORT_PATH из конфига)
        matrix_path = os.getenv('MATRIX_EXPORT_PATH', '/app/logs/matrix_report.json')
        
        matrix_json_body = "{}"
        try:
            # Если файл уже физически создан инспектором, асинхронно читаем его
            if os.path.exists(matrix_path):
                # Используем asyncio.to_thread для неблокирующего чтения файла с диска
                def read_file():
                    with open(matrix_path, 'r', encoding='utf-8') as f:
                        return f.read()
                
                file_content = await asyncio.to_thread(read_file)
                if file_content.strip():
                    matrix_json_body = file_content
            else:
                # Fallback если файл еще не создался (отдаем структуру на основе живой памяти)
                snapshot = await self.orchestrator.get_snapshot()
                matrix_json_body = json.dumps(snapshot, ensure_ascii=False)
                
        except Exception as read_err:
            self.logger.error(f"[WEB GUI API ERROR] Не удалось прочитать matrix_report.json: {read_err}")
            matrix_json_body = '{"error": "Failed to read matrix data"}'

        # Формируем валидный HTTP/1.1 ответ с честными данными о сбоях
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(matrix_json_body.encode('utf-8'))}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{matrix_json_body}"
        )
        return response
    
    async def serve_import_api(self, headers: Dict[str, str], body: bytes) -> str:
        """API endpoint для импорта стратегий"""
        try:
            if not body:
                return self.make_response(400, json.dumps({'error': 'Empty body'}), 'application/json')
            
            # Парсим JSON
            import_data = json.loads(body.decode())
            
            # Импортируем стратегии в оркестратор
            imported_count = 0
            for domain, strategy_data in import_data.items():
                try:
                    # Создаем стратегию из импортированных данных
                    if isinstance(strategy_data, dict) and 'pipeline_modules' in strategy_data:
                        # Преобразуем в формат оркестратора
                        modules = strategy_data.get('pipeline_modules', [])
                        configs = strategy_data.get('module_configs', {})
                        
                        strategy = self.orchestrator._config_to_strategy(domain, {
                            'pipeline_modules': modules,
                            'module_configs': configs
                        })
                        
                        # Устанавливаем статус
                        if strategy_data.get('status') == 'STABLE':
                            strategy.success_count = 1
                            strategy.failure_count = 0
                        
                        self.orchestrator.domain_strategies[domain] = strategy
                        imported_count += 1
                        
                        self.logger.info(f"[WEB_GUI] Imported strategy for {domain}: {modules}")
                
                except Exception as e:
                    self.logger.error(f"[WEB_GUI] Failed to import strategy for {domain}: {e}")
            
            # Экспортируем обновленную матрицу
            if self.orchestrator.inspector:
                await self.orchestrator.inspector.export_matrix_report()
            
            result = {
                'imported': imported_count,
                'message': f'Successfully imported {imported_count} strategies'
            }
            
            self.logger.info(f"[WEB_GUI] Strategy import completed: {imported_count} domains")
            return self.make_response(200, json.dumps(result), 'application/json')
            
        except json.JSONDecodeError as e:
            return self.make_response(400, json.dumps({'error': f'Invalid JSON: {str(e)}'}), 'application/json')
        except Exception as e:
            self.logger.error(f"Import API error: {e}")
            return self.make_response(500, json.dumps({'error': str(e)}), 'application/json')
    
    def make_response(self, status_code: int, body: str, content_type: str = 'text/plain') -> str:
        """Создание HTTP ответа"""
        status_text = {
            200: 'OK',
            400: 'Bad Request',
            404: 'Not Found',
            500: 'Internal Server Error'
        }.get(status_code, 'Unknown')
        
        headers = [
            f'HTTP/1.1 {status_code} {status_text}',
            f'Content-Type: {content_type}',
            f'Content-Length: {len(body.encode())}',
            'Connection: close',
            '\r\n'
        ]
        
        return '\r\n'.join(headers) + body
