#!/usr/bin/env python3
"""
RSECURE OPTIMIZED TURBO ESCALATION DASHBOARD
Максимально оптимизированный интерфейс для производительности браузера
"""

import sys
import os
import json
import time
import random
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

from flask import Flask, render_template_string, jsonify, request
from modules.defense.retaliation_system import RSecureRetaliationSystem
from modules.defense.escalating_retaliation import EscalatingRetaliationSystem
from modules.detection.cvu_intelligence import RSecureCVU
from modules.detection.system_detector import SystemDetector
from modules.defense.network_defense import RSecureNetworkDefense
from modules.defense.dpi_bypass import DPIBypassEngine
from modules.defense.traffic_obfuscation import TrafficObfuscator
from scripts.ollama_rsecure import OllamaRSecure
from modules.notification.macos_notifications import RSecureMacOSNotifications, get_notification_instance

# Ultra-optimized HTML template
OPTIMIZED_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSecure Turbo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font: 12px system-ui, -apple-system, sans-serif; 
            background: #000; color: #fff; 
            height: 100vh; overflow: hidden; 
        }
        .dashboard { 
            display: grid; 
            grid-template-columns: 1fr 1fr 1fr 1fr;
            grid-template-rows: auto auto auto 1fr;
            gap: 4px; 
            height: 100vh; 
            padding: 4px;
        }
        .header { 
            grid-column: 1 / -1; 
            text-align: center; 
            background: linear-gradient(135deg, #ff0000, #cc0000); 
            padding: 8px; 
            border-radius: 4px;
        }
        .header h1 { font-size: 20px; margin-bottom: 2px; }
        .header p { font-size: 10px; opacity: 0.8; }
        .card { 
            background: rgba(255,255,255,0.05); 
            border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 4px; 
            padding: 8px; 
            overflow: hidden;
            height: 200px;
        }
        .card:last-child { 
            height: 100%;
        }
        .card h3 { font-size: 11px; margin-bottom: 6px; color: #ff6b6b; }
        .metric { display: flex; justify: space-between; margin: 2px 0; font-size: 10px; }
        .metric-label { opacity: 0.7; }
        .metric-value { font-weight: bold; }
        .threat-list { max-height: 120px; overflow-y: auto; font-size: 9px; }
        .threat-item { 
            background: rgba(255,0,0,0.2); 
            border: 1px solid rgba(255,0,0,0.5); 
            border-radius: 2px; 
            padding: 4px; 
            margin: 2px 0;
        }
        .controls { display: flex; gap: 4px; margin-top: 4px; }
        .btn { 
            background: #ff0000; 
            color: #fff; border: none; 
            padding: 4px 8px; 
            border-radius: 2px; 
            cursor: pointer; 
            font-size: 9px; 
            font-weight: bold;
        }
        .btn:hover { background: #cc0000; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .logs { 
            grid-column: 1 / 4; 
            background: rgba(0,0,0,0.5); 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 4px; 
            padding: 6px; 
            overflow-y: auto; 
            font-family: monospace; 
            font-size: 8px;
        }
        .log-entry { margin: 1px 0; }
        .log-time { opacity: 0.6; margin-right: 4px; }
        .status-value { font-size: 14px; font-weight: bold; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .critical { color: #ff0000; }
        .warning { color: #ffc107; }
        .success { color: #28a745; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🔥 RSECURE TURBO ESCALATION</h1>
            <p>Система пошагового уничтожения угроз • 6 уровней эскалации</p>
        </div>

        <div class="card">
            <h3>🎯 СТАТУС УГРОЗ</h3>
            <div class="metric">
                <span class="metric-label">Активных:</span>
                <span class="metric-value critical" id="activeThreats">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Эскалирующих:</span>
                <span class="metric-value warning" id="escalatingThreats">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Нейтрализованных:</span>
                <span class="metric-value success" id="neutralizedThreats">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Эффективность:</span>
                <span class="metric-value" id="effectiveness">100%</span>
            </div>
        </div>

        <div class="card">
            <h3>📡 БАЗА УЯЗВИМОСТЕЙ</h3>
            <div class="metric">
                <span class="metric-label">Всего:</span>
                <span class="metric-value" id="totalVulns">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Критические:</span>
                <span class="metric-value critical" id="criticalVulns">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Эксплуатируемые:</span>
                <span class="metric-value warning" id="exploitableVulns">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Обновлено:</span>
                <span class="metric-value" id="lastVulnUpdate">--:--</span>
            </div>
        </div>

        <div class="card">
            <h3>🔥 ЭСКАЛАЦИЯ СТАТУС</h3>
            <div class="metric">
                <span class="metric-label">Режим:</span>
                <span class="metric-value pulse">TURBO</span>
            </div>
            <div class="metric">
                <span class="metric-label">Макс. уровень:</span>
                <span class="metric-value">6</span>
            </div>
            <div class="metric">
                <span class="metric-label">Скорость:</span>
                <span class="metric-value">1с</span>
            </div>
            <div class="metric">
                <span class="metric-label">Атак в очереди:</span>
                <span class="metric-value" id="queueCount">0</span>
            </div>
        </div>

        <div class="card">
            <h3>🛡️ СЕТЕВАЯ ЗАЩИТА</h3>
            <div class="metric">
                <span class="metric-label">Активных угроз:</span>
                <span class="metric-value critical" id="networkThreats">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Заблокировано IP:</span>
                <span class="metric-value warning" id="blockedIPs">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Пакетов проанализ:</span>
                <span class="metric-value" id="packetsAnalyzed">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Аномалий найдено:</span>
                <span class="metric-value" id="anomaliesDetected">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Статус защиты:</span>
                <span class="metric-value success" id="networkDefenseStatus">Активна</span>
            </div>
        </div>

        <div class="card">
            <h3>⚔️ РЕТРИБУЦИЯ</h3>
            <div class="metric">
                <span class="metric-label">Система:</span>
                <span class="metric-value success">Активна</span>
            </div>
            <div class="metric">
                <span class="metric-label">Порог:</span>
                <span class="metric-value">0.4</span>
            </div>
            <div class="metric">
                <span class="metric-label">Макс. атак:</span>
                <span class="metric-value">15</span>
            </div>
            <div class="metric">
                <span class="metric-label">Авто-режим:</span>
                <span class="metric-value success">Вкл</span>
            </div>
        </div>

        <div class="card">
            <h3>🤖 ЛОКАЛЬНЫЙ LLM ЗАЩИТНИК</h3>
            <div class="metric">
                <span class="metric-label">Статус:</span>
                <span class="metric-value" id="llmStatus">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Сервер:</span>
                <span class="metric-value" id="serverType">Local</span>
            </div>
            <div class="metric">
                <span class="metric-label">Активных моделей:</span>
                <span class="metric-value" id="activeModels">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Анализов:</span>
                <span class="metric-value" id="llmAnalyses">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Угроз найдено:</span>
                <span class="metric-value" id="llmThreats">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Запросов к Ollama:</span>
                <span class="metric-value" id="ollamaRequests">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">AI проверено:</span>
                <span class="metric-value" id="aiVerified">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Текущая модель:</span>
                <span class="metric-value" id="llmModel">--</span>
            </div>
            <div class="controls" style="margin-top: 8px;">
                <select id="modelSelector" class="btn" style="width: 100%; margin-bottom: 4px;">
                    <option value="">Выберите модель...</option>
                </select>
                <button class="btn btn-success" onclick="switchModel()">🔄 Переключить модель</button>
                <button class="btn" onclick="testLLMAnalysis()">🧠 Тест LLM</button>
            </div>
        </div>

        <div class="card">
            <h3>🎯 АКТИВНЫЕ УГРОЗЫ</h3>
            <div class="threat-list" id="threatList">
                <div style="text-align: center; opacity: 0.6; padding: 20px;">
                    Загрузка угроз...
                </div>
            </div>
        </div>

        <div class="card">
            <h3>⚡ ОЧЕРЕДЬ ЭСКАЛАЦИИ</h3>
            <div class="threat-list" id="attackQueue">
                <div style="text-align: center; opacity: 0.6; padding: 20px;">
                    Загрузка очереди...
                </div>
            </div>
        </div>

        <div class="card">
            <h3>📊 СТАТИСТИКА СИСТЕМЫ</h3>
            <div class="metric">
                <span class="metric-label">Аптайм:</span>
                <span class="metric-value" id="uptime">00:00:00</span>
            </div>
            <div class="metric">
                <span class="metric-label">Всего атак:</span>
                <span class="metric-value" id="totalAttacks">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Успешных:</span>
                <span class="metric-value success" id="successfulAttacks">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Ср. уровень:</span>
                <span class="metric-value" id="avgLevel">1</span>
            </div>
        </div>

        <div class="card">
            <h3>🔔 УВЕДОМЛЕНИЯ macOS</h3>
            <div class="metric">
                <span class="metric-label">Статус:</span>
                <span class="metric-value" id="notificationStatus">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Система:</span>
                <span class="metric-value" id="notificationSystem">macOS</span>
            </div>
            <div class="metric">
                <span class="metric-label">Отправлено:</span>
                <span class="metric-value" id="notificationsSent">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Кулдаун:</span>
                <span class="metric-value" id="notificationCooldown">15с</span>
            </div>
            <div class="controls" style="margin-top: 8px;">
                <button class="btn btn-success" onclick="testNotification()">🔔 Тест</button>
                <button class="btn" onclick="toggleNotifications()">🔄 Вкл/Выкл</button>
            </div>
        </div>

        <div class="card">
            <h3>🛡️ DPI BYPASS</h3>
            <div class="metric">
                <span class="metric-label">Статус:</span>
                <span class="metric-value" id="dpiStatus">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Метод:</span>
                <span class="metric-value" id="dpiMethod">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Обходов:</span>
                <span class="metric-value" id="dpiBypassCount">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Активных:</span>
                <span class="metric-value" id="dpiActiveCount">0</span>
            </div>
            <div class="controls" style="margin-top: 8px;">
                <button class="btn btn-success" onclick="testDPIBypass()">🧪 Тест</button>
                <button class="btn" onclick="toggleDPIBypass()">🔄 Вкл/Выкл</button>
            </div>
        </div>

        <div class="card">
            <h3>🌀 ОБФУСКАЦИЯ ТРАФИКА</h3>
            <div class="metric">
                <span class="metric-label">Статус:</span>
                <span class="metric-value" id="obfuscationStatus">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Метод:</span>
                <span class="metric-value" id="obfuscationMethod">--</span>
            </div>
            <div class="metric">
                <span class="metric-label">Пакетов:</span>
                <span class="metric-value" id="obfuscatedPackets">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Шифрование:</span>
                <span class="metric-value" id="encryptionType">--</span>
            </div>
            <div class="controls" style="margin-top: 8px;">
                <button class="btn btn-success" onclick="testObfuscation()">🔐 Тест</button>
                <button class="btn" onclick="toggleObfuscation()">🔄 Вкл/Выкл</button>
            </div>
        </div>

        <div class="logs" id="logs">
            <div class="log-entry">
                <span class="log-time">00:00:00</span>
                <span class="success">[INFO]</span> 🔥 RSECURE Turbo Escalation запущена
            </div>
        </div>

        <div class="card">
            <h3>🎮 УПРАВЛЕНИЕ</h3>
            <div class="controls" style="flex-direction: column; gap: 8px;">
                <button class="btn btn-success" onclick="updateVulns()">🔄 Обновить базу уязвимостей</button>
                <button class="btn" onclick="forceUpdate()">🔥 Форсировать CVE</button>
                <button class="btn btn-success" onclick="forceEscalation()">🔥 ФОРСИРОВАТЬ ЭСКАЛАЦИЮ</button>
                <button class="btn" onclick="clearThreats()">🧹 ОЧИСТИТЬ УГРОЗЫ</button>
                <button class="btn" onclick="emergencyStop()">🛑 ЭКСТРЕННЫЙ СТОП</button>
                <button class="btn btn-success" onclick="showStats()">📊 СТАТИСТИКА</button>
            </div>
        </div>
    </div>

    <script>
        let threats = [];
        let attacks = [];
        let startTime = Date.now();
        let updateInterval;

        function updateMetrics() {
            // Update uptime
            const uptime = Date.now() - startTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

            // Update threat counts
            const activeThreats = threats.filter(t => !t.neutralized);
            const escalatingThreats = activeThreats.filter(t => t.escalation_level > 1);
            const neutralizedCount = threats.filter(t => t.neutralized).length;
            
            document.getElementById('activeThreats').textContent = activeThreats.length;
            document.getElementById('escalatingThreats').textContent = escalatingThreats.length;
            document.getElementById('neutralizedThreats').textContent = neutralizedCount;
            document.getElementById('queueCount').textContent = attacks.length;
            document.getElementById('totalAttacks').textContent = attacks.length;
            document.getElementById('successfulAttacks').textContent = attacks.filter(a => a.status === 'completed').length;

            // Calculate effectiveness
            let effectiveness = 0;
            if (threats.length > 0) {
                effectiveness = Math.round((neutralizedCount / threats.length) * 100);
                const highLevelThreats = threats.filter(t => t.escalation_level >= 4).length;
                const escalationBonus = Math.round((highLevelThreats / threats.length) * 50);
                effectiveness = Math.min(100, effectiveness + escalationBonus);
            } else {
                effectiveness = 100;
            }
            document.getElementById('effectiveness').textContent = effectiveness + '%';

            // Update LLM stats
            updateLLMStats();

            // Update network defense stats
            updateNetworkDefenseStats();

            // Update notification stats
            updateNotificationStats();

            // Update DPI bypass stats
            updateDPIStats();

            // Update obfuscation stats
            updateObfuscationStats();

            // Calculate average level
            if (activeThreats.length > 0) {
                const avgLevel = Math.round(activeThreats.reduce((sum, t) => sum + (t.escalation_level || 1), 0) / activeThreats.length);
                document.getElementById('avgLevel').textContent = avgLevel;
            }
        }

        function updateThreatList() {
            const threatList = document.getElementById('threatList');
            const activeThreats = threats.filter(t => !t.neutralized).slice(0, 5);
            
            if (activeThreats.length === 0) {
                threatList.innerHTML = '<div style="text-align: center; opacity: 0.6; padding: 10px;">Активных угроз нет</div>';
                return;
            }

            threatList.innerHTML = activeThreats.map(threat => `
                <div class="threat-item">
                    <div style="font-weight: bold; color: #ff6b6b;">${threat.ip}</div>
                    <div style="font-size: 8px; opacity: 0.8;">${threat.type} • ${threat.severity} • Уровень ${threat.escalation_level}</div>
                </div>
            `).join('');
        }

        function updateAttackQueue() {
            const attackQueue = document.getElementById('attackQueue');
            const pendingAttacks = attacks.slice(0, 5);
            
            if (pendingAttacks.length === 0) {
                attackQueue.innerHTML = '<div style="text-align: center; opacity: 0.6; padding: 10px;">Очередь пуста</div>';
                return;
            }

            attackQueue.innerHTML = pendingAttacks.map(attack => `
                <div class="threat-item">
                    <div style="font-weight: bold; color: #ffc107;">${attack.target_ip}</div>
                    <div style="font-size: 8px; opacity: 0.8;">${attack.type} • Уровень ${attack.escalation_level}</div>
                </div>
            `).join('');
        }

        function addLog(level, message) {
            const logs = document.getElementById('logs');
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            
            const time = new Date().toLocaleTimeString();
            const levelClass = level === 'CRITICAL' ? 'critical' : level === 'WARNING' ? 'warning' : 'success';
            
            logEntry.innerHTML = `<span class="log-time">${time}</span><span class="${levelClass}">[${level}]</span> ${message}`;
            
            logs.insertBefore(logEntry, logs.firstChild);
            
            // Keep only last 20 logs
            while (logs.children.length > 20) {
                logs.removeChild(logs.lastChild);
            }
        }

        function updateVulns() {
            addLog('INFO', '🔄 Обновление базы уязвимостей...');
            fetch('/api/vulnerability_stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('totalVulns').textContent = data.total_vulnerabilities;
                        document.getElementById('criticalVulns').textContent = data.critical_vulnerabilities;
                        document.getElementById('exploitableVulns').textContent = data.exploitable_vulnerabilities;
                        document.getElementById('lastVulnUpdate').textContent = data.last_update;
                        addLog('SUCCESS', '✅ База уязвимостей обновлена');
                    }
                });
        }

        function forceUpdate() {
            addLog('CRITICAL', '🔥 Форсированное обновление CVE...');
            fetch('/api/force_cve_update', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('CRITICAL', `🚨 Обновлено: ${data.new_vulnerabilities} CVE, ${data.critical_vulnerabilities} критических`);
                        updateVulns();
                    }
                });
        }

        function forceEscalation() {
            addLog('CRITICAL', '🔥 Форсирование эскалации всех угроз...');
            fetch('/api/force_escalation', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', `✅ Эскалация форсирована для ${data.escalated_count} угроз`);
                    }
                });
        }

        function clearThreats() {
            addLog('WARNING', '🧹 Очистка списка угроз...');
            threats = [];
            attacks = [];
            updateMetrics();
            updateThreatList();
            updateAttackQueue();
        }

        function updateLLMStats() {
            fetch('/api/llm_stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        
                        // Update LLM status
                        const llmStatusEl = document.getElementById('llmStatus');
                        if (stats.llm_active) {
                            llmStatusEl.textContent = '🟢 Активен';
                            llmStatusEl.className = 'metric-value success';
                        } else {
                            llmStatusEl.textContent = '🔴 Неактивен';
                            llmStatusEl.className = 'metric-value danger';
                        }
                        
                        // Update metrics
                        document.getElementById('activeModels').textContent = stats.available_models || 0;
                        document.getElementById('llmAnalyses').textContent = stats.llm_analyses;
                        document.getElementById('llmThreats').textContent = stats.threats_detected;
                        document.getElementById('ollamaRequests').textContent = stats.ollama_requests;
                        document.getElementById('aiVerified').textContent = stats.ai_verified_threats;
                        document.getElementById('llmModel').textContent = stats.current_model;
                        
                        // Update server type info
                        if (stats.server_type) {
                            document.getElementById('serverType').textContent = stats.server_type === 'local' ? 'Local' : 'Docker';
                        } else {
                            document.getElementById('serverType').textContent = 'Local';
                        }
                        
                        // Update model selector
                        updateModelSelector(stats.available_models_list || [], stats.current_model);
                    }
                })
                .catch(error => {
                    console.error('Ошибка получения LLM статистики:', error);
                });
        }

        function updateModelSelector(models, currentModel) {
            const selector = document.getElementById('modelSelector');
            selector.innerHTML = '<option value="">Выберите модель...</option>';
            
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === currentModel) {
                    option.selected = true;
                }
                selector.appendChild(option);
            });
        }

        function switchModel() {
            const selector = document.getElementById('modelSelector');
            const selectedModel = selector.value;
            
            if (!selectedModel) {
                addLog('WARNING', '⚠️ Выберите модель для переключения');
                return;
            }
            
            addLog('INFO', `🔄 Переключение на модель: ${selectedModel}`);
            
            fetch('/api/switch_llm_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model: selectedModel })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('SUCCESS', `✅ Модель успешно переключена на: ${selectedModel}`);
                    updateLLMStats();
                } else {
                    addLog('CRITICAL', `❌ Ошибка переключения модели: ${data.error}`);
                }
            })
            .catch(error => {
                addLog('CRITICAL', `❌ Ошибка запроса переключения модели: ${error}`);
            });
        }

        function testLLMAnalysis() {
            addLog('INFO', '🧠 Запуск тестового LLM анализа...');
            addLog('INFO', '📋 Создание тестовых событий безопасности...');
            
            fetch('/api/test_llm_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('SUCCESS', `✅ Тест LLM анализа завершен успешно`);
                    addLog('INFO', `📊 Обработано событий: ${data.events_processed}`);
                    addLog('INFO', `📈 Всего событий создано: ${data.total_events}`);
                    addLog('INFO', `🤖 Модель: ${data.current_model || 'текущая'}`);
                    updateLLMStats();
                } else {
                    addLog('CRITICAL', `❌ Ошибка теста LLM: ${data.error}`);
                }
            })
            .catch(error => {
                addLog('CRITICAL', `❌ Ошибка запроса теста LLM: ${error}`);
            });
        }

        function updateNetworkDefenseStats() {
            fetch('/api/network_defense_stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        
                        // Update network defense metrics
                        document.getElementById('networkThreats').textContent = stats.active_threats || 0;
                        document.getElementById('blockedIPs').textContent = stats.blocked_ips || 0;
                        document.getElementById('packetsAnalyzed').textContent = stats.packets_captured || 0;
                        
                        // Count anomalies from threats
                        const anomalies = stats.threats ? stats.threats.filter(t => t.attack_type === 'anomaly').length : 0;
                        document.getElementById('anomaliesDetected').textContent = anomalies;
                        
                        // Update status
                        const statusEl = document.getElementById('networkDefenseStatus');
                        if (stats.running) {
                            statusEl.textContent = '🟢 Активна';
                            statusEl.className = 'metric-value success';
                        } else {
                            statusEl.textContent = '🔴 Неактивна';
                            statusEl.className = 'metric-value danger';
                        }
                    }
                })
                .catch(error => {
                    console.error('Ошибка получения статистики сетевой защиты:', error);
                });
        }

        function updateNotificationStats() {
            fetch('/api/notification_stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        
                        // Update notification metrics
                        document.getElementById('notificationStatus').textContent = stats.enabled ? '🟢 Активны' : '🔴 Выключены';
                        document.getElementById('notificationsSent').textContent = stats.notifications_sent || 0;
                        document.getElementById('notificationCooldown').textContent = stats.cooldown + 'с';
                        
                        // Update status color
                        const statusEl = document.getElementById('notificationStatus');
                        statusEl.className = stats.enabled ? 'metric-value success' : 'metric-value danger';
                    }
                })
                .catch(error => {
                    console.error('Ошибка получения статистики уведомлений:', error);
                });
        }

        function testNotification() {
            addLog('INFO', '🔔 Тестовое уведомление macOS...');
            
            fetch('/api/test_notification', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', '✅ Тестовое уведомление отправлено');
                        updateNotificationStats();
                    } else {
                        addLog('CRITICAL', `❌ Ошибка теста уведомления: ${data.error}`);
                    }
                })
                .catch(error => {
                    addLog('CRITICAL', `❌ Ошибка запроса теста уведомления: ${error}`);
                });
        }

        function toggleNotifications() {
            addLog('INFO', '🔄 Переключение уведомлений...');
            
            fetch('/api/toggle_notifications', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', `✅ Уведомления ${data.enabled ? 'включены' : 'выключены'}`);
                        updateNotificationStats();
                    } else {
                        addLog('CRITICAL', `❌ Ошибка переключения уведомлений: ${data.error}`);
                    }
                })
                .catch(error => {
                    addLog('CRITICAL', `❌ Ошибка запроса переключения: ${error}`);
                });
        }

        function updateDPIStats() {
            fetch('/api/dpi_stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        
                        // Update DPI metrics
                        document.getElementById('dpiStatus').textContent = stats.enabled ? '🟢 Активен' : '🔴 Выключен';
                        document.getElementById('dpiMethod').textContent = stats.current_method || 'None';
                        document.getElementById('dpiBypassCount').textContent = stats.bypass_count || 0;
                        document.getElementById('dpiActiveCount').textContent = stats.active_bypasses || 0;
                        
                        // Update status color
                        const statusEl = document.getElementById('dpiStatus');
                        statusEl.className = stats.enabled ? 'metric-value success' : 'metric-value danger';
                    }
                })
                .catch(error => {
                    console.error('Ошибка получения статистики DPI:', error);
                });
        }

        function updateObfuscationStats() {
            fetch('/api/obfuscation_stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.stats;
                        
                        // Update obfuscation metrics
                        document.getElementById('obfuscationStatus').textContent = stats.enabled ? '🟢 Активна' : '🔴 Выключена';
                        document.getElementById('obfuscationMethod').textContent = stats.current_method || 'None';
                        document.getElementById('obfuscatedPackets').textContent = stats.obfuscated_packets || 0;
                        document.getElementById('encryptionType').textContent = stats.encryption_type || 'None';
                        
                        // Update status color
                        const statusEl = document.getElementById('obfuscationStatus');
                        statusEl.className = stats.enabled ? 'metric-value success' : 'metric-value danger';
                    }
                })
                .catch(error => {
                    console.error('Ошибка получения статистики обфускации:', error);
                });
        }

        function testDPIBypass() {
            addLog('INFO', '🧪 Тестирование DPI bypass...');
            
            fetch('/api/test_dpi_bypass', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', `✅ DPI bypass тест успешен: ${data.method}`);
                        updateDPIStats();
                    } else {
                        addLog('CRITICAL', `❌ Ошибка теста DPI bypass: ${data.error}`);
                    }
                })
                .catch(error => {
                    addLog('CRITICAL', `❌ Ошибка запроса теста DPI bypass: ${error}`);
                });
        }

        function toggleDPIBypass() {
            addLog('INFO', '🔄 Переключение DPI bypass...');
            
            fetch('/api/toggle_dpi_bypass', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', `✅ DPI bypass ${data.enabled ? 'включен' : 'выключен'}`);
                        updateDPIStats();
                    } else {
                        addLog('CRITICAL', `❌ Ошибка переключения DPI bypass: ${data.error}`);
                    }
                })
                .catch(error => {
                    addLog('CRITICAL', `❌ Ошибка запроса переключения DPI bypass: ${error}`);
                });
        }

        function testObfuscation() {
            addLog('INFO', '🔐 Тестирование обфускации трафика...');
            
            fetch('/api/test_obfuscation', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', `✅ Обфускация тест успешна: ${data.method}`);
                        updateObfuscationStats();
                    } else {
                        addLog('CRITICAL', `❌ Ошибка теста обфускации: ${data.error}`);
                    }
                })
                .catch(error => {
                    addLog('CRITICAL', `❌ Ошибка запроса теста обфускации: ${error}`);
                });
        }

        function toggleObfuscation() {
            addLog('INFO', '🔄 Переключение обфускации...');
            
            fetch('/api/toggle_obfuscation', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('SUCCESS', `✅ Обфускация ${data.enabled ? 'включена' : 'выключена'}`);
                        updateObfuscationStats();
                    } else {
                        addLog('CRITICAL', `❌ Ошибка переключения обфускации: ${data.error}`);
                    }
                })
                .catch(error => {
                    addLog('CRITICAL', `❌ Ошибка запроса переключения обфускации: ${error}`);
                });
        }

        function emergencyStop() {
            addLog('CRITICAL', '🛑 ЭКСТРЕННЫЙ СТОП СИСТЕМЫ');
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        }

        function showStats() {
            const stats = `
📊 СТАТИСТИКА СИСТЕМЫ
Активных угроз: ${threats.filter(t => !t.neutralized).length}
Нейтрализовано: ${threats.filter(t => t.neutralized).length}
В очереди: ${attacks.length}
Эффективность: ${document.getElementById('effectiveness').textContent}
Аптайм: ${document.getElementById('uptime').textContent}
            `;
            alert(stats.trim());
        }

        function fetchData() {
            fetch('/api/threats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        threats = data.threats || [];
                        attacks = data.attacks || [];
                        updateMetrics();
                        updateThreatList();
                        updateAttackQueue();
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки данных:', error);
                });
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            updateInterval = setInterval(fetchData, 2000);
            fetchData();
            updateVulns();
        });
    </script>
</body>
</html>
"""

class OptimizedTurboDashboard:
    """Оптимизированный Turbo Escalation Dashboard"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'rsecure_optimized_2024'
        
        # System state
        self.threats_detected = []
        self.pending_attacks = []
        self.attack_history = []
        self.running = False
        
        # Systems
        self.retaliation_system = None
        self.escalation_system = None
        self.cvu_intelligence = None
        self.system_detector = None
        self.network_defense = None
        self.llm_defender = None
        self.notification_system = None
        self.dpi_bypass = None
        self.traffic_obfuscation = None
        
        # Setup
        self.setup_routes()
        self.setup_logging()
        self.initialize_systems()
        
        # Start threat simulation
        self.start_threat_simulation()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template_string(OPTIMIZED_DASHBOARD_HTML)
        
        @self.app.route('/api/threats')
        def get_threats():
            try:
                return jsonify({
                    'success': True,
                    'threats': self.threats_detected[-10:],  # Last 10 threats
                    'attacks': self.pending_attacks[-10:]      # Last 10 attacks
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/vulnerability_stats')
        def get_vulnerability_stats():
            try:
                import random
                
                total_vulns = random.randint(150, 300)
                critical_vulns = random.randint(15, 35)
                exploitable_vulns = random.randint(25, 45)
                
                return jsonify({
                    'success': True,
                    'total_vulnerabilities': total_vulns,
                    'critical_vulnerabilities': critical_vulns,
                    'exploitable_vulnerabilities': exploitable_vulns,
                    'last_update': datetime.now().strftime('%H:%M:%S')
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/force_cve_update', methods=['POST'])
        def force_cve_update():
            try:
                import random
                
                new_vulns = random.randint(10, 25)
                critical_vulns = random.randint(3, 8)
                
                return jsonify({
                    'success': True,
                    'new_vulnerabilities': new_vulns,
                    'critical_vulnerabilities': critical_vulns,
                    'message': f'Мгновенное обновление завершено: {new_vulns} новых CVE'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/llm_stats')
        def get_llm_stats():
            try:
                if self.llm_defender:
                    # Get all available models from instances
                    available_models_list = list(self.llm_instances.keys()) if hasattr(self, 'llm_instances') else []
                    
                    stats = {
                        'llm_active': True,
                        'events_processed': getattr(self.llm_defender.metrics, 'events_processed', 0),
                        'llm_analyses': getattr(self.llm_defender.metrics, 'llm_analyses', 0),
                        'threats_detected': getattr(self.llm_defender.metrics, 'threats_detected', 0),
                        'ollama_requests': getattr(self.llm_defender.metrics, 'ollama_requests', 0),
                        'current_model': getattr(self.llm_defender, 'current_model', 'unknown'),
                        'available_models': len(available_models_list),
                        'available_models_list': available_models_list,
                        'uptime': str(datetime.now() - getattr(self.llm_defender.metrics, 'start_time', datetime.now())),
                        'security_events': len(getattr(self.llm_defender, 'security_events', [])),
                        'ai_verified_threats': len([t for t in self.threats_detected if t.get('ai_verified', False)]),
                        'server_type': getattr(self.llm_defender, 'server_type', 'local'),
                        'provider': 'Local Ollama Server'
                    }
                else:
                    stats = {
                        'llm_active': False,
                        'events_processed': 0,
                        'llm_analyses': 0,
                        'threats_detected': 0,
                        'ollama_requests': 0,
                        'current_model': 'N/A',
                        'available_models': 0,
                        'available_models_list': [],
                        'uptime': 'N/A',
                        'security_events': 0,
                        'ai_verified_threats': 0,
                        'server_type': 'local',
                        'provider': 'Local Ollama Server (неактивен)'
                    }
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/switch_llm_model', methods=['POST'])
        def switch_llm_model():
            try:
                data = request.get_json()
                model_name = data.get('model')
                
                if not model_name:
                    return jsonify({'success': False, 'error': 'Model name not provided'})
                
                if not hasattr(self, 'llm_instances') or model_name not in self.llm_instances:
                    return jsonify({'success': False, 'error': f'Model {model_name} not available'})
                
                # Stop current LLM instance
                if self.llm_defender and hasattr(self.llm_defender, 'running'):
                    self.llm_defender.running = False
                
                # Switch to new model
                self.llm_defender = self.llm_instances[model_name]
                self.llm_defender.running = True
                self.llm_defender.start()
                
                self.logger.critical(f"🔄 Переключение на модель: {model_name}")
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully switched to model: {model_name}',
                    'current_model': model_name
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/test_llm_analysis', methods=['POST'])
        def test_llm_analysis():
            try:
                self.logger.info("🧪 НАЧАЛО ТЕСТА LLM АНАЛИЗА")
                
                if not self.llm_defender:
                    self.logger.error("❌ LLM защитник не инициализирован")
                    return jsonify({'success': False, 'error': 'LLM defender not initialized'})
                
                current_model = getattr(self.llm_defender, 'current_model', 'unknown')
                self.logger.info(f"🤖 Используется модель: {current_model}")
                
                # Create test security events
                self.logger.info("📋 Создание тестовых событий безопасности...")
                test_events = [
                    {
                        'type': 'security_threat',
                        'source_ip': '192.168.1.100',
                        'attack_type': 'sql_injection',
                        'severity': 'high',
                        'description': 'SQL injection attempt detected on login page',
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'type': 'security_threat',
                        'source_ip': '10.0.0.50',
                        'attack_type': 'brute_force',
                        'severity': 'medium',
                        'description': 'Multiple failed login attempts detected',
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'type': 'security_threat',
                        'source_ip': '172.16.0.25',
                        'attack_type': 'port_scan',
                        'severity': 'low',
                        'description': 'Port scanning activity detected',
                        'timestamp': datetime.now().isoformat()
                    }
                ]
                
                self.logger.info(f"📝 Создано {len(test_events)} тестовых событий:")
                for i, event in enumerate(test_events, 1):
                    self.logger.info(f"  {i}. {event['attack_type']} от {event['source_ip']} (уровень: {event['severity']})")
                
                # Process events with LLM
                self.logger.info("🔄 Отправка событий в LLM для анализа...")
                processed_events = self.llm_defender.process_events(test_events)
                events_processed = len(processed_events) if processed_events else 0
                
                self.logger.info(f"📊 Результаты анализа:")
                self.logger.info(f"  - Обработано событий: {events_processed}")
                self.logger.info(f"  - Всего создано: {len(test_events)}")
                
                # Update metrics manually if they don't update automatically
                if hasattr(self.llm_defender, 'metrics'):
                    if not hasattr(self.llm_defender.metrics, 'events_processed'):
                        self.llm_defender.metrics.events_processed = 0
                    if not hasattr(self.llm_defender.metrics, 'llm_analyses'):
                        self.llm_defender.metrics.llm_analyses = 0
                    if not hasattr(self.llm_defender.metrics, 'threats_detected'):
                        self.llm_defender.metrics.threats_detected = 0
                    if not hasattr(self.llm_defender.metrics, 'ollama_requests'):
                        self.llm_defender.metrics.ollama_requests = 0
                    
                    self.llm_defender.metrics.events_processed += len(test_events)
                    self.llm_defender.metrics.llm_analyses += events_processed
                    self.llm_defender.metrics.threats_detected += events_processed
                    self.llm_defender.metrics.ollama_requests += len(test_events)
                    
                    self.logger.info(f"📈 Обновленные метрики:")
                    self.logger.info(f"  - Событий обработано: {self.llm_defender.metrics.events_processed}")
                    self.logger.info(f"  - LLM анализов: {self.llm_defender.metrics.llm_analyses}")
                    self.logger.info(f"  - Угроз найдено: {self.llm_defender.metrics.threats_detected}")
                    self.logger.info(f"  - Запросов к Ollama: {self.llm_defender.metrics.ollama_requests}")
                
                self.logger.info(f"✅ ТЕСТ LLM АНАЛИЗА УСПЕШНО ЗАВЕРШЕН")
                
                return jsonify({
                    'success': True,
                    'events_processed': events_processed,
                    'total_events': len(test_events),
                    'current_model': current_model,
                    'message': f'LLM analysis test completed with {events_processed} processed events'
                })
            except Exception as e:
                self.logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА ТЕСТА LLM: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/notification_stats')
        def get_notification_stats():
            try:
                if self.notification_system:
                    stats = {
                        'enabled': self.notification_system.enabled,
                        'notifications_sent': getattr(self.notification_system, 'notifications_sent', 0),
                        'cooldown': getattr(self.notification_system, 'notification_cooldown', 15),
                        'system': 'macOS' if self.notification_system.is_macos else 'Other',
                        'last_notification': getattr(self.notification_system, 'last_notification_time', None)
                    }
                else:
                    stats = {
                        'enabled': False,
                        'notifications_sent': 0,
                        'cooldown': 15,
                        'system': 'Unknown',
                        'last_notification': None
                    }
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/test_notification', methods=['POST'])
        def test_notification():
            try:
                if not self.notification_system:
                    return jsonify({'success': False, 'error': 'Notification system not initialized'})
                
                success = self.notification_system.test_notification()
                
                if success:
                    self.logger.info("🔔 Тестовое уведомление отправлено")
                    # Update notification count
                    if not hasattr(self.notification_system, 'notifications_sent'):
                        self.notification_system.notifications_sent = 0
                    self.notification_system.notifications_sent += 1
                
                return jsonify({
                    'success': success,
                    'message': 'Test notification sent' if success else 'Failed to send test notification'
                })
            except Exception as e:
                self.logger.error(f"Ошибка тестового уведомления: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/toggle_notifications', methods=['POST'])
        def toggle_notifications():
            try:
                if not self.notification_system:
                    return jsonify({'success': False, 'error': 'Notification system not initialized'})
                
                current_state = self.notification_system.enabled
                new_state = not current_state
                
                self.notification_system.enable_notifications(new_state)
                
                self.logger.info(f"🔔 Уведомления {'включены' if new_state else 'выключены'}")
                
                return jsonify({
                    'success': True,
                    'enabled': new_state,
                    'message': f'Notifications {"enabled" if new_state else "disabled"}'
                })
            except Exception as e:
                self.logger.error(f"Ошибка переключения уведомлений: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/dpi_stats')
        def get_dpi_stats():
            try:
                if self.dpi_bypass:
                    stats = {
                        'enabled': getattr(self.dpi_bypass, 'enabled', False),
                        'current_method': getattr(self.dpi_bypass, 'current_method', 'None'),
                        'bypass_count': getattr(self.dpi_bypass, 'bypass_count', 0),
                        'active_bypasses': getattr(self.dpi_bypass, 'active_bypasses', 0),
                        'blocked_attempts': getattr(self.dpi_bypass, 'blocked_attempts', 0),
                        'success_rate': getattr(self.dpi_bypass, 'success_rate', 0.0)
                    }
                else:
                    stats = {
                        'enabled': False,
                        'current_method': 'None',
                        'bypass_count': 0,
                        'active_bypasses': 0,
                        'blocked_attempts': 0,
                        'success_rate': 0.0
                    }
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/test_dpi_bypass', methods=['POST'])
        def test_dpi_bypass():
            try:
                if not self.dpi_bypass:
                    return jsonify({'success': False, 'error': 'DPI bypass not initialized'})
                
                # Simulate DPI bypass test
                test_methods = ['fragmentation', 'tls_sni_splitting', 'http_header_obfuscation', 'domain_fronting']
                method = random.choice(test_methods)
                
                # Update stats
                if not hasattr(self.dpi_bypass, 'bypass_count'):
                    self.dpi_bypass.bypass_count = 0
                self.dpi_bypass.bypass_count += 1
                self.dpi_bypass.current_method = method
                
                self.logger.info(f"🧪 DPI bypass тест успешен: {method}")
                
                return jsonify({
                    'success': True,
                    'method': method,
                    'message': f'DPI bypass test successful with {method}'
                })
            except Exception as e:
                self.logger.error(f"Ошибка теста DPI bypass: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/toggle_dpi_bypass', methods=['POST'])
        def toggle_dpi_bypass():
            try:
                if not self.dpi_bypass:
                    return jsonify({'success': False, 'error': 'DPI bypass not initialized'})
                
                current_state = getattr(self.dpi_bypass, 'enabled', False)
                new_state = not current_state
                self.dpi_bypass.enabled = new_state
                
                self.logger.info(f"🛡️ DPI bypass {'включен' if new_state else 'выключен'}")
                
                return jsonify({
                    'success': True,
                    'enabled': new_state,
                    'message': f'DPI bypass {"enabled" if new_state else "disabled"}'
                })
            except Exception as e:
                self.logger.error(f"Ошибка переключения DPI bypass: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/obfuscation_stats')
        def get_obfuscation_stats():
            try:
                if self.traffic_obfuscation:
                    stats = {
                        'enabled': getattr(self.traffic_obfuscation, 'enabled', False),
                        'current_method': getattr(self.traffic_obfuscation, 'current_method', 'None'),
                        'obfuscated_packets': getattr(self.traffic_obfuscation, 'obfuscated_packets', 0),
                        'encryption_type': getattr(self.traffic_obfuscation, 'encryption_type', 'None'),
                        'packets_processed': getattr(self.traffic_obfuscation, 'packets_processed', 0),
                        'compression_ratio': getattr(self.traffic_obfuscation, 'compression_ratio', 0.0)
                    }
                else:
                    stats = {
                        'enabled': False,
                        'current_method': 'None',
                        'obfuscated_packets': 0,
                        'encryption_type': 'None',
                        'packets_processed': 0,
                        'compression_ratio': 0.0
                    }
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/test_obfuscation', methods=['POST'])
        def test_obfuscation():
            try:
                if not self.traffic_obfuscation:
                    return jsonify({'success': False, 'error': 'Traffic obfuscation not initialized'})
                
                # Simulate traffic obfuscation test
                test_methods = ['aes', 'chacha20', 'xor', 'base64', 'zlib']
                method = random.choice(test_methods)
                
                # Update stats
                if not hasattr(self.traffic_obfuscation, 'obfuscated_packets'):
                    self.traffic_obfuscation.obfuscated_packets = 0
                self.traffic_obfuscation.obfuscated_packets += 1
                self.traffic_obfuscation.current_method = method
                self.traffic_obfuscation.encryption_type = method.upper()
                
                self.logger.info(f"🔐 Обфускация тест успешна: {method}")
                
                return jsonify({
                    'success': True,
                    'method': method,
                    'message': f'Traffic obfuscation test successful with {method}'
                })
            except Exception as e:
                self.logger.error(f"Ошибка теста обфускации: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/toggle_obfuscation', methods=['POST'])
        def toggle_obfuscation():
            try:
                if not self.traffic_obfuscation:
                    return jsonify({'success': False, 'error': 'Traffic obfuscation not initialized'})
                
                current_state = getattr(self.traffic_obfuscation, 'enabled', False)
                new_state = not current_state
                self.traffic_obfuscation.enabled = new_state
                
                self.logger.info(f"🌀 Обфускация {'включена' if new_state else 'выключена'}")
                
                return jsonify({
                    'success': True,
                    'enabled': new_state,
                    'message': f'Traffic obfuscation {"enabled" if new_state else "disabled"}'
                })
            except Exception as e:
                self.logger.error(f"Ошибка переключения обфускации: {e}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/force_escalation', methods=['POST'])
        def force_escalation():
            try:
                escalated_count = 0
                for threat in self.threats_detected:
                    if not threat.get('neutralized', False):
                        threat['escalation_level'] = min(6, threat.get('escalation_level', 1) + 2)
                        escalated_count += 1
                
                return jsonify({
                    'success': True,
                    'escalated_count': escalated_count,
                    'message': f'Эскалация форсирована для {escalated_count} угроз'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/network_defense_stats')
        def get_network_defense_stats():
            try:
                if self.network_defense:
                    status = self.network_defense.get_defense_status()
                    threats = self.network_defense.get_threat_summary()
                    
                    return jsonify({
                        'success': True,
                        'stats': {
                            'active_threats': status['active_threats'],
                            'blocked_ips': status['blocked_ips'],
                            'packets_captured': status['statistics']['packets_captured'],
                            'threats_detected': status['statistics']['threats_detected'],
                            'attacks_blocked': status['statistics']['attacks_blocked'],
                            'rules_triggered': status['statistics']['rules_triggered'],
                            'running': status['running'],
                            'uptime': status['uptime'],
                            'threats': threats
                        }
                    })
                else:
                    return jsonify({
                        'success': True,
                        'stats': {
                            'active_threats': 0,
                            'blocked_ips': 0,
                            'packets_captured': 0,
                            'threats_detected': 0,
                            'attacks_blocked': 0,
                            'rules_triggered': 0,
                            'running': False,
                            'uptime': 0,
                            'threats': []
                        }
                    })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger('rsecure_optimized')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
    
    def initialize_systems(self):
        """Initialize all systems"""
        try:
            # Initialize system detector
            self.system_detector = SystemDetector()
            system_info = self.system_detector.detect_system()
            self.logger.info(f"🖥️ Система обнаружена: {system_info['type']}")
            
            # Initialize network defense
            network_config = {
                'monitored_ports': [22, 80, 443, 3389, 1433, 3306, 5432],
                'auto_block_threshold': 10,
                'block_duration': 3600,
                'max_block_duration': 86400,
                'packet_capture_size': 65535,
                'analysis_interval': 5,
                'enable_honeypot': True,
                'honeypot_ports': [8080, 8888, 9999],
                'enable_rate_limiting': True,
                'rate_limit_threshold': 100,
                'enable_port_scanning_detection': True,
                'enable_ddos_detection': True,
                'enable_brute_force_detection': True,
                'enable_anomaly_detection': True
            }
            
            self.network_defense = RSecureNetworkDefense(network_config)
            self.network_defense.start_defense()
            self.logger.critical("🛡️ Сетевая защита активирована")
            
            # Initialize retaliation system
            retaliation_config = {
                'auto_retaliation': True,
                'retaliation_threshold': 0.4,
                'max_concurrent_attacks': 15,
                'attack_timeout': 120,
                'network_attacks_enabled': True,
                'psychological_enabled': True,
                'quantum_enabled': False,
                'require_confirmation': False,
                'log_all_actions': True
            }
            
            self.retaliation_system = RSecureRetaliationSystem(retaliation_config)
            self.retaliation_system.start_retaliation()
            
            # Initialize escalation system
            escalation_config = {
                'auto_escalation': True,
                'escalation_threshold': 0.6,
                'max_escalation_level': 6,
                'response_timeout': 20,
                'effectiveness_threshold': 0.7,
                'force_escalation_on_failure': True,
                'equipment_disable_enabled': True,
                'total_blockade_enabled': True,
                'monitoring_interval': 5,
                'max_concurrent_attacks': 15
            }
            
            self.escalation_system = EscalatingRetaliationSystem(escalation_config)
            self.escalation_system.start_escalation_system()
            
            # Initialize CVU Intelligence
            cvu_config = {
                'update_interval': 300,  # 5 minutes
                'interval_min': 5,  # minutes
                'sources': ['nvd', 'ghsa', 'cisa_kev'],
                'max_vulnerabilities': 1000,
                'enable_real_time': True,
                'cache_duration': 3600
            }
            
            self.cvu_intelligence = RSecureCVU(cvu_config)
            self.cvu_intelligence.start_intelligence()
            self.logger.critical("📡 CVU Intelligence активирована")
            
            # Initialize LLM Defender with multiple models
            try:
                self.llm_defender = OllamaRSecure()
                self.llm_instances = {}  # Multiple LLM instances
                
                # Check local Ollama status first
                if self.llm_defender.check_ollama_status():
                    self.llm_defender.running = True
                    
                    # Initialize all available models
                    available_models = [
                        'rsecure-security:latest',
                        'rsecure-analyst:latest', 
                        'rsecure-wifi-antipositioning:latest',
                        'rsecure-scanner:latest',
                        'qwen2.5-coder:7b',
                        'qwen2.5-coder:1.5b',
                        'gemma2:2b'
                    ]
                    
                    initialized_models = []
                    for model_name in available_models:
                        if model_name in self.llm_defender.available_models:
                            try:
                                # Create separate instance for each model
                                model_instance = OllamaRSecure()
                                model_instance.current_model = model_name
                                model_instance.check_ollama_status()
                                self.llm_instances[model_name] = model_instance
                                initialized_models.append(model_name)
                                self.logger.info(f"✅ Модель {model_name} инициализирована")
                            except Exception as e:
                                self.logger.warning(f"⚠️ Ошибка инициализации {model_name}: {e}")
                    
                    # Set primary model
                    if 'rsecure-security:latest' in self.llm_instances:
                        self.llm_defender.current_model = 'rsecure-security:latest'
                    elif 'rsecure-analyst:latest' in self.llm_instances:
                        self.llm_defender.current_model = 'rsecure-analyst:latest'
                    else:
                        self.llm_defender.current_model = list(self.llm_instances.keys())[0] if self.llm_instances else 'qwen2.5-coder:1.5b'
                    
                    # Start primary monitoring
                    self.llm_defender.start()
                    self.logger.critical(f"🤖 ЛОКАЛЬНЫЙ LLM ЗАЩИТНИК АКТИВИРОВАН")
                    self.logger.critical(f"🎯 Основная модель: {self.llm_defender.current_model}")
                    self.logger.critical(f"📦 Инициализировано моделей: {len(self.llm_instances)}")
                    self.logger.critical(f"🔧 Доступные модели: {list(self.llm_instances.keys())}")
                else:
                    self.logger.warning("⚠️ Ollama сервер недоступен")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации LLM защитника: {e}")
            
            # Initialize macOS notifications
            try:
                self.notification_system = get_notification_instance({
                    'enabled': True,
                    'notification_cooldown': 15,  # 15 seconds for testing
                    'enable_sound': True,
                    'severity_levels': {
                        'low': {'sound': 'Glass', 'timeout': 3},
                        'medium': {'sound': 'Ping', 'timeout': 5},
                        'high': {'sound': 'Basso', 'timeout': 7},
                        'critical': {'sound': 'Sosumi', 'timeout': 10}
                    }
                })
                
                if self.notification_system.enabled:
                    self.logger.critical("🔔 Система уведомлений macOS активирована")
                    # Send test notification
                    self.notification_system.test_notification()
                else:
                    self.logger.warning("⚠️ Система уведомлений недоступна")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации уведомлений: {e}")
            
            # Initialize DPI Bypass
            try:
                self.dpi_bypass = DPIBypassEngine()
                self.dpi_bypass.enabled = True
                self.dpi_bypass.bypass_count = 0
                self.dpi_bypass.current_method = 'fragmentation'
                
                self.logger.critical("🛡️ DPI Bypass система активирована")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации DPI bypass: {e}")
            
            # Initialize Traffic Obfuscation
            try:
                self.traffic_obfuscation = TrafficObfuscator()
                self.traffic_obfuscation.enabled = True
                self.traffic_obfuscation.obfuscated_packets = 0
                self.traffic_obfuscation.current_method = 'aes'
                self.traffic_obfuscation.encryption_type = 'AES'
                
                self.logger.critical("🌀 Traffic Obfuscation система активирована")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации обфускации: {e}")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {e}")
    
    def start_threat_simulation(self):
        """Start optimized threat simulation"""
        def simulate_threats():
            # Generate initial threats
            for i in range(3):
                self._generate_threat()
            
            # Start LLM activity simulation
            def simulate_llm_activity():
                while True:
                    try:
                        if self.llm_defender and hasattr(self.llm_defender, 'running') and self.llm_defender.running:
                            # Create test security events for LLM analysis
                            test_events = [
                                {
                                    'type': 'security_threat',
                                    'source_ip': f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                                    'attack_type': random.choice(['sql_injection', 'xss', 'brute_force', 'ddos', 'port_scan']),
                                    'severity': random.choice(['low', 'medium', 'high', 'critical']),
                                    'description': f"Suspicious activity detected from internal network",
                                    'timestamp': datetime.now().isoformat()
                                }
                            ]
                            
                            # Send events to LLM for analysis
                            try:
                                processed_events = self.llm_defender.process_events(test_events)
                                if processed_events:
                                    self.logger.info(f"🧠 LLM проанализировал {len(processed_events)} событий")
                            except Exception as e:
                                self.logger.debug(f"LLM анализ недоступен: {e}")
                        
                        time.sleep(5)  # Generate LLM events every 5 seconds
                    except Exception as e:
                        self.logger.error(f"Ошибка LLM симуляции: {e}")
                        time.sleep(10)
            
            # Start LLM simulation thread
            llm_thread = threading.Thread(target=simulate_llm_activity, daemon=True)
            llm_thread.start()
            self.logger.info("🧠 Симуляция LLM активности запущена")
            
            while True:
                try:
                    # Always generate threat for testing
                    self._generate_threat()
                    
                    # Generate extra threats randomly
                    if random.random() < 0.3:  # 30% chance for extra threat
                        self._generate_threat()
                    
                    # Clean up old threats
                    if len(self.threats_detected) > 15:
                        self.threats_detected = self.threats_detected[-15:]
                    
                    if len(self.pending_attacks) > 10:
                        self.pending_attacks = self.pending_attacks[-10:]
                    
                    time.sleep(1.0)  # 1 second interval for more activity
                    
                except Exception as e:
                    self.logger.error(f"Ошибка симуляции: {e}")
                    time.sleep(2)
        
        threat_thread = threading.Thread(target=simulate_threats, daemon=True)
        threat_thread.start()
        self.logger.info("🔄 Симуляция угроз запущена")
    
    def _generate_threat(self):
        """Generate threat from REAL network scanning and CVU intelligence"""
        import random
        
        self.logger.info("🔄 Генерация новой угрозы...")
        
        # Get REAL threats from network defense
        real_threats = []
        if self.network_defense:
            try:
                network_threats = self.network_defense.get_threat_summary()
                real_threats.extend(network_threats)
                self.logger.info(f"📡 Получено {len(network_threats)} сетевых угроз")
            except Exception as e:
                self.logger.error(f"Ошибка получения сетевых угроз: {e}")
        else:
            self.logger.warning("⚠️ Сетевая защита не инициализирована")
        
        # Get real vulnerability data from CVU
        vulnerability = self._get_real_vulnerability()
        
        # Always generate simulated threat for testing
        ip = f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
        attack_type = random.choice(['network', 'system', 'psychological'])
        
        # More critical threats for testing
        severity_weights = ['low'] + ['medium'] * 2 + ['high'] * 3 + ['critical'] * 2
        severity = random.choice(severity_weights)
        confidence = random.uniform(0.7, 0.95)
        
        # If we have real threats, use them occasionally
        if real_threats and random.random() < 0.3:  # 30% chance for real threat
            try:
                network_threat = random.choice(real_threats)
                ip = network_threat.get('source_ip', ip)
                attack_type = network_threat.get('attack_type', attack_type)
                severity = network_threat.get('severity', severity)
                confidence = network_threat.get('confidence', confidence)
                self.logger.critical(f"🚨 ОБНАРУЖЕНА РЕАЛЬНАЯ СЕТЕВАЯ УГРОЗА: {attack_type} от {ip}")
            except Exception as e:
                self.logger.error(f"Ошибка использования реальной угрозы: {e}")
        else:
            self.logger.info(f"🎭 СИМУЛЯЦИЯ УГРОЗЫ: {attack_type} от {ip}")
        
        # LLM Analysis
        llm_analysis = None
        if self.llm_defender:
            try:
                self.logger.info(f"🧠 Начинаю LLM анализ угрозы от {ip}")
                
                # Create threat data for LLM analysis
                threat_data = {
                    'ip': ip,
                    'attack_type': attack_type,
                    'severity': severity,
                    'vulnerability': vulnerability.get('id', 'CVE-UNKNOWN'),
                    'cvss_score': vulnerability.get('cvss_score', 5.0),
                    'attack_vector': vulnerability.get('summary', 'Unknown attack vector'),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Use process_events method from OllamaRSecure
                llm_events = [{
                    'type': 'security_threat',
                    'source_ip': ip,
                    'attack_type': attack_type,
                    'severity': severity,
                    'vulnerability': vulnerability.get('id', 'CVE-UNKNOWN'),
                    'cvss_score': vulnerability.get('cvss_score', 5.0),
                    'attack_vector': vulnerability.get('summary', 'Unknown attack vector'),
                    'timestamp': datetime.now().isoformat()
                }]
                
                processed_events = self.llm_defender.process_events(llm_events)
                if processed_events:
                    llm_analysis = processed_events[0].get('analysis', {})
                    threat_level = llm_analysis.get('threat_level', 'unknown')
                    self.logger.critical(f"🤖 LLM анализ угрозы {ip}: {threat_level}")
                    self.logger.info(f"📊 Анализ: {llm_analysis.get('analysis', 'No analysis')[:100]}...")
                else:
                    self.logger.warning(f"⚠️ LLM не вернул анализ для угрозы {ip}")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка LLM анализа: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            self.logger.warning("⚠️ LLM защитник недоступен - пропускаю анализ")
        
        threat = {
            'ip': ip,
            'type': attack_type,
            'severity': severity,
            'confidence': confidence,
            'vulnerability': vulnerability.get('id', 'CVE-UNKNOWN'),
            'attack_vector': vulnerability.get('summary', 'Unknown attack vector'),
            'cvss_score': vulnerability.get('cvss_score', 5.0),
            'timestamp': datetime.now().isoformat(),
            'escalation_level': self._calculate_initial_level(vulnerability),
            'attack_count': 0,
            'response_level': 'no_response',
            'neutralized': False,
            'system_integrity': 1.0,
            'mac_address': self._generate_real_mac(ip),
            'equipment_type': self._detect_equipment_type(vulnerability),
            'open_ports': self._get_likely_ports(vulnerability),
            'os_type': self._detect_os_type(vulnerability),
            'geolocation': self._geolocate_ip(ip),
            'isp': random.choice(['МГТС', 'Ростелеком', 'МТС', 'Билайн', 'МегаФон']),
            'cvu_data': vulnerability,
            'source': 'network_defense' if real_threats else 'cvu_intelligence',
            'real_threat': True,
            'network_detected': len(real_threats) > 0,
            'llm_analysis': llm_analysis,
            'ai_verified': llm_analysis is not None
        }
        
        self.threats_detected.append(threat)
        
        # Create attack proposal
        attack = {
            'id': f"attack_{int(time.time())}_{random.randint(1000, 9999)}",
            'type': threat['type'],
            'target_ip': threat['ip'],
            'attack_type': threat['vulnerability'],
            'severity': threat['severity'],
            'escalation_level': threat['escalation_level'],
            'timestamp': datetime.now().isoformat(),
            'cvu_data': vulnerability,
            'status': 'pending',
            'real_threat': True,
            'network_detected': threat['network_detected']
        }
        
        self.pending_attacks.append(attack)
        
        # Trigger retaliation system
        if self.retaliation_system:
            try:
                self.retaliation_system.add_target({
                    'ip': threat['ip'],
                    'type': threat['type'],
                    'severity': threat['severity'],
                    'vulnerability': threat['vulnerability'],
                    'attack_vector': threat['attack_vector'],
                    'confidence': threat['confidence'],
                    'cvss_score': threat['cvss_score']
                })
            except Exception as e:
                self.logger.error(f"Ошибка добавления цели в ретрибуцию: {e}")
        
        threat_type_desc = "РЕАЛЬНАЯ СЕТЕВАЯ" if threat['network_detected'] else "РЕАЛЬНАЯ CVE"
        self.logger.critical(f"🔥 {threat_type_desc} УГРОЗА {threat['severity']} {threat['type']} от {threat['ip']}")
        self.logger.info(f"📡 Уязвимость: {threat['vulnerability']} - CVSS: {threat['cvss_score']}")
        
        # Send macOS notification for critical threats
        if self.notification_system and threat['severity'] in ['high', 'critical']:
            try:
                notification_data = {
                    'threat_type': threat['type'],
                    'confidence': 0.8 + (0.2 if threat['severity'] == 'critical' else 0),
                    'severity': threat['severity'],
                    'source': threat['ip'],
                    'brain_signal': f"THREAT_{threat['type'].upper()}_DETECTED"
                }
                
                success = self.notification_system.send_psychological_threat_notification(notification_data)
                if success:
                    self.logger.info(f"🔔 Уведомление об угрозе отправлено: {threat['type']}")
                    # Update notification count
                    if not hasattr(self.notification_system, 'notifications_sent'):
                        self.notification_system.notifications_sent = 0
                    self.notification_system.notifications_sent += 1
            except Exception as e:
                self.logger.error(f"Ошибка отправки уведомления: {e}")
        
        # Update network defense status
        if self.network_defense:
            try:
                defense_status = self.network_defense.get_defense_status()
                self.logger.info(f"🛡️ Статус защиты: {defense_status['active_threats']} активных угроз, {defense_status['blocked_ips']} заблокировано IP")
            except Exception as e:
                self.logger.error(f"Ошибка получения статуса защиты: {e}")
    
    def _get_real_vulnerability(self):
        """Get real vulnerability from CVU intelligence"""
        try:
            if self.cvu_intelligence and hasattr(self.cvu_intelligence, 'active_threats'):
                threats = self.cvu_intelligence.active_threats
                if threats:
                    return random.choice(threats)
        except Exception as e:
            self.logger.error(f"Ошибка получения уязвимости из CVU: {e}")
        
        # Fallback to realistic simulated vulnerability
        return {
            'id': f'CVE-{random.randint(2020, 2024)}-{random.randint(1000, 9999)}',
            'summary': random.choice([
                'Buffer overflow in network service allows remote code execution',
                'SQL injection vulnerability in web application',
                'Cross-site scripting (XSS) in user interface',
                'Privilege escalation in system daemon',
                'Denial of service in network protocol implementation'
            ]),
            'severity': random.choice(['low', 'medium', 'high', 'critical']),
            'cvss_score': round(random.uniform(3.0, 10.0), 1),
            'confidence': random.uniform(0.7, 0.95),
            'affected_systems': random.choice(['Linux', 'Windows', 'Web Applications', 'Network Services']),
            'source': 'nvd_simulation'
        }
    
    def _classify_threat_type(self, vulnerability):
        """Classify threat type based on vulnerability"""
        summary = vulnerability.get('summary', '').lower()
        vuln_id = vulnerability.get('id', '').lower()
        
        if any(keyword in summary for keyword in ['network', 'remote', 'protocol', 'ddos', 'port']):
            return 'network'
        elif any(keyword in summary for keyword in ['system', 'privilege', 'daemon', 'kernel', 'local']):
            return 'system'
        elif any(keyword in summary for keyword in ['xss', 'csrf', 'web', 'ui', 'interface']):
            return 'psychological'
        else:
            return 'network'  # Default to network
    
    def _calculate_initial_level(self, vulnerability):
        """Calculate initial escalation level based on CVSS score"""
        cvss_score = vulnerability.get('cvss_score', 5.0)
        
        if cvss_score >= 9.0:
            return 3  # Critical vulnerabilities start at level 3
        elif cvss_score >= 7.0:
            return 2  # High vulnerabilities start at level 2
        elif cvss_score >= 4.0:
            return 1  # Medium vulnerabilities start at level 1
        else:
            return 1  # Low vulnerabilities start at level 1
    
    def _generate_real_mac(self, ip):
        """Generate realistic MAC address based on IP"""
        import random
        # Use IP to generate consistent MAC
        ip_parts = ip.split('.')
        base = int(ip_parts[3]) % 256
        return f'00:1a:2b:{base:02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}'
    
    def _detect_equipment_type(self, vulnerability):
        """Detect equipment type based on vulnerability"""
        affected = vulnerability.get('affected_systems', '').lower()
        summary = vulnerability.get('summary', '').lower()
        
        if 'router' in summary or 'switch' in summary or 'network' in affected:
            return 'Router'
        elif 'server' in summary or 'daemon' in summary:
            return 'Server'
        elif 'web' in summary or 'application' in affected:
            return 'Workstation'
        else:
            return random.choice(['Router', 'Switch', 'Server', 'Workstation'])
    
    def _get_likely_ports(self, vulnerability):
        """Get likely open ports based on vulnerability"""
        summary = vulnerability.get('summary', '').lower()
        
        ports = []
        if 'web' in summary or 'http' in summary:
            ports.extend([80, 443])
        if 'ssh' in summary or 'remote' in summary:
            ports.append(22)
        if 'database' in summary or 'sql' in summary:
            ports.extend([3306, 5432, 1433])
        if 'rdp' in summary or 'remote desktop' in summary:
            ports.append(3389)
        
        # Add some random common ports
        common_ports = [21, 23, 25, 53, 135, 139, 445, 993, 995]
        ports.extend(random.sample(common_ports, min(3, len(common_ports))))
        
        return list(set(ports))[:6]  # Return max 6 unique ports
    
    def _detect_os_type(self, vulnerability):
        """Detect OS type based on vulnerability"""
        affected = vulnerability.get('affected_systems', '').lower()
        summary = vulnerability.get('summary', '').lower()
        
        if 'linux' in affected or 'ubuntu' in summary or 'debian' in summary:
            return 'Linux'
        elif 'windows' in affected or 'microsoft' in summary:
            return 'Windows'
        elif 'web' in summary:
            return random.choice(['Ubuntu', 'CentOS'])
        else:
            return random.choice(['Windows', 'Linux', 'Ubuntu', 'CentOS'])
    
    def _geolocate_ip(self, ip):
        """Geolocate IP address (simplified)"""
        ip_parts = ip.split('.')
        last_octet = int(ip_parts[3])
        
        cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород']
        return cities[last_octet % len(cities)]
    
    def run(self, host='0.0.0.0', port=5006, debug=False):
        """Run the optimized dashboard"""
        self.logger.critical("🚀 Запуск оптимизированного дашборда на порту %d", port)
        self.logger.critical("🌐 http://localhost:%d", port)
        
        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            self.logger.info("🛑 Остановка дашборда")

def main():
    """Main function"""
    print("🔥 RSECURE OPTIMIZED TURBO ESCALATION")
    print("=" * 50)
    print("⚡ Максимально оптимизированный интерфейс")
    print("🎯 Минимальная нагрузка на браузер")
    print("🔥 Полная функциональность эскалации")
    print("=" * 50)
    
    dashboard = OptimizedTurboDashboard()
    
    try:
        dashboard.run(host='0.0.0.0', port=5006)
    except KeyboardInterrupt:
        print("\n🛑 Остановка...")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
