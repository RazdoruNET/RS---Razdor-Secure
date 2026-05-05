#!/usr/bin/env python3
"""
Russian RSecure Dashboard with Combat Control
Расширенный дашборд с управлением боевой частью на русском языке
"""

import os
import sys
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request, session
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Add rsecure to path
sys.path.insert(0, str(Path(__file__).parent / "rsecure"))

from modules.defense.retaliation_system import RSecureRetaliationSystem, RetaliationType, AttackSeverity

# Russian HTML template with combat control and tooltips
RUSSIAN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSecure Боевая Панель Управления</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #fff; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #ff4444; font-size: 3em; text-shadow: 0 0 20px rgba(255,68,68,0.5); }
        .header p { color: #888; font-size: 1.2em; }
        
        .mode-indicator { 
            position: fixed; top: 20px; right: 20px; 
            background: rgba(255,68,68,0.2); border: 2px solid #ff4444; 
            border-radius: 10px; padding: 15px; z-index: 1000;
        }
        .mode-turbo { background: rgba(255,0,0,0.3); border-color: #ff0000; animation: pulse 2s infinite; }
        .mode-human { background: rgba(0,255,68,0.2); border-color: #00ff44; }
        
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        
        .grid { display: grid; gap: 20px; }
        .grid-2 { grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); }
        .grid-3 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
        
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 15px; padding: 20px; }
        .card-danger { border-color: #ff4444; background: rgba(255,68,68,0.1); }
        .card-success { border-color: #00ff44; background: rgba(0,255,68,0.1); }
        .card-warning { border-color: #ffaa00; background: rgba(255,170,0,0.1); }
        
        .card h3 { margin-bottom: 15px; font-size: 1.3em; }
        .card-danger h3 { color: #ff4444; }
        .card-success h3 { color: #00ff44; }
        .card-warning h3 { color: #ffaa00; }
        
        .metric { display: flex; justify-content: space-between; align-items: center; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #888; }
        .metric-value { color: #fff; font-weight: bold; }
        .metric-critical { color: #ff4444; font-weight: bold; }
        .metric-warning { color: #ffaa00; font-weight: bold; }
        .metric-success { color: #00ff44; font-weight: bold; }
        
        .btn { 
            background: linear-gradient(135deg, #ff4444, #cc0000); 
            color: #fff; border: none; padding: 12px 24px; 
            border-radius: 8px; cursor: pointer; margin: 5px; 
            font-weight: bold; transition: all 0.3s;
            position: relative; display: inline-block;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255,68,68,0.3); }
        .btn-success { background: linear-gradient(135deg, #00ff44, #00cc33); }
        .btn-warning { background: linear-gradient(135deg, #ffaa00, #cc8800); }
        .btn-danger { background: linear-gradient(135deg, #ff4444, #cc0000); }
        .btn-turbo { 
            background: linear-gradient(135deg, #ff0000, #cc0000); 
            animation: pulse 2s infinite; font-size: 1.1em; padding: 15px 30px;
        }
        
        .controls { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }
        .controls-center { justify-content: center; }
        
        .threat-list { max-height: 300px; overflow-y: auto; }
        .threat-item { 
            background: rgba(255,68,68,0.1); border: 1px solid rgba(255,68,68,0.3); 
            border-radius: 8px; padding: 15px; margin: 10px 0;
        }
        .threat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .threat-ip { color: #ff4444; font-weight: bold; font-size: 1.1em; }
        .threat-severity { padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }
        .severity-critical { background: #ff4444; }
        .severity-high { background: #ff8800; }
        .severity-medium { background: #ffaa00; }
        .severity-low { background: #00ff44; color: #000; }
        
        .threat-actions { display: flex; gap: 10px; margin-top: 10px; }
        .threat-details { color: #ccc; font-size: 0.9em; margin: 5px 0; }
        
        .attack-queue { max-height: 400px; overflow-y: auto; }
        .attack-item { 
            background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 8px; padding: 15px; margin: 10px 0;
        }
        .attack-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .attack-type { color: #ffaa00; font-weight: bold; }
        .attack-target { color: #888; }
        .attack-status { padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }
        .status-pending { background: #ffaa00; color: #000; }
        .status-approved { background: #00ff44; color: #000; }
        .status-rejected { background: #ff4444; }
        .status-executing { background: #0088ff; }
        .status-completed { background: #00ff44; }
        
        .logs { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 20px; max-height: 400px; overflow-y: auto; }
        .log-entry { margin: 5px 0; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 5px; font-family: monospace; font-size: 12px; }
        .log-time { color: #888; margin-right: 10px; }
        .log-level-INFO { color: #00ff44; }
        .log-level-WARNING { color: #ffaa00; }
        .log-level-ERROR { color: #ff4444; }
        .log-level-CRITICAL { color: #ff0000; font-weight: bold; }
        
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .status-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; }
        .status-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .status-label { color: #888; }
        
        .alert-banner { 
            background: linear-gradient(135deg, #ff4444, #cc0000); 
            color: #fff; padding: 15px; border-radius: 10px; 
            margin: 20px 0; text-align: center; font-weight: bold;
            animation: pulse 2s infinite;
        }
        
        .modal { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); }
        .modal-content { 
            background: #1a1a1a; margin: 10% auto; padding: 30px; 
            border: 2px solid #ff4444; border-radius: 15px; width: 80%; max-width: 600px;
        }
        .modal-header { color: #ff4444; font-size: 1.5em; margin-bottom: 20px; }
        .modal-body { margin: 20px 0; }
        .modal-footer { display: flex; justify-content: flex-end; gap: 10px; }
        
        /* Tooltip styles */
        .tooltip {
            position: relative;
            cursor: help;
        }
        
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 300px;
            background-color: rgba(0, 0, 0, 0.9);
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 3000;
            bottom: 125%;
            left: 50%;
            margin-left: -150px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .tooltip .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: rgba(0, 0, 0, 0.9) transparent transparent transparent;
        }
        
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        
        .tooltip-icon {
            display: inline-block;
            width: 16px;
            height: 16px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            text-align: center;
            line-height: 16px;
            font-size: 10px;
            margin-left: 5px;
            cursor: help;
        }
        
        .help-section {
            background: rgba(0, 100, 200, 0.1);
            border: 1px solid rgba(0, 100, 200, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
        }
        
        .help-title {
            color: #00aaff;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .help-content {
            color: #ccc;
            font-size: 0.9em;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="mode-indicator" id="modeIndicator">
        <div id="modeText">🛡️ РЕЖИМ ЧЕЛОВЕК</div>
        <div id="modeStatus">Требуется ручное одобрение</div>
    </div>

    <div class="container">
        <div class="header">
            <h1>🔪 RSECURE БОЕВАЯ ПАНЕЛЬ</h1>
            <p>Расширенное управление угрозами и ответными ударами</p>
        </div>

        <div class="help-section">
            <div class="help-title">📖 Справка по интерфейсу</div>
            <div class="help-content">
                🔪 <strong>Боевая панель</strong> - центр управления системой ответного удара RSecure<br>
                🛡️ <strong>Режим Человек</strong> - все атаки требуют ручного одобрения<br>
                🚀 <strong>Турбо режим</strong> - автоматические ответные атаки без участия человека<br>
                ⚠️ <strong>Внимание:</strong> Турбо режим может привести к саморазрушению системы
            </div>
        </div>

        <div class="grid grid-3">
            <div class="card card-danger">
                <h3>🎯 СТАТУС УГРОЗ
                    <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>Активные угрозы:</strong> Текущее количество обнаруженных угроз<br>
                            <strong>Ожидающие атаки:</strong> Атаки, ожидающие одобрения<br>
                            <strong>Выполняются:</strong> Атаки в процессе выполнения<br>
                            <strong>Завершены:</strong> Успешно выполненные атаки
                        </span>
                    </span>
                </h3>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-value" id="activeThreats">0</div>
                        <div class="status-label">Активных угроз</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="pendingAttacks">0</div>
                        <div class="status-label">Ожидают атаки</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="executingAttacks">0</div>
                        <div class="status-label">Выполняются</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="completedAttacks">0</div>
                        <div class="status-label">Завершены</div>
                    </div>
                </div>
            </div>

            <div class="card card-warning">
                <h3>⚡ БОЕВОЙ РЕЖИМ
                    <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>Режим Человек:</strong> Безопасный режим с ручным контролем<br>
                            <strong>Турбо режим:</strong> Автоматический ответ без одобрения<br>
                            <strong>Экстренная остановка:</strong> Немедленная остановка всех атак
                        </span>
                    </span>
                </h3>
                <div class="controls controls-center">
                    <button class="btn btn-success tooltip" onclick="setHumanMode()">
                        🛡️ Режим Человек
                        <span class="tooltiptext">Включить безопасный режим с ручным одобрением атак</span>
                    </button>
                    <button class="btn btn-turbo tooltip" onclick="setTurboMode()">
                        🚀 Турбо Режим
                        <span class="tooltiptext">⚠️ ОПАСНО: Автоматические атаки без одобрения!</span>
                    </button>
                    <button class="btn btn-warning tooltip" onclick="emergencyStop()">
                        🛑 ЭКСТРЕННАЯ ОСТАНОВКА
                        <span class="tooltiptext">Немедленно остановить все ответные действия</span>
                    </button>
                </div>
                <div style="margin-top: 15px; text-align: center;">
                    <div id="currentMode" style="font-size: 1.2em; font-weight: bold;">Текущий: РЕЖИМ ЧЕЛОВЕК</div>
                    <div id="modeDescription" style="color: #888; margin-top: 5px;">Требуется ручное одобрение для всех атак</div>
                </div>
            </div>

            <div class="card card-success">
                <h3>📊 СТАТУС СИСТЕМЫ
                    <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>Ollama:</strong> Статус AI системы анализа<br>
                            <strong>Система ответного удара:</strong> Активность боевой системы<br>
                            <strong>Авто-ретрибуция:</strong> Статус автоматических ответов<br>
                            <strong>Время работы:</strong> Общее время работы системы
                        </span>
                    </span>
                </h3>
                <div class="metric">
                    <span class="metric-label">Ollama Статус:</span>
                    <span class="metric-value metric-success">Онлайн</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Система ответного удара:</span>
                    <span class="metric-value metric-success">Активна</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Авто-ретрибуция:</span>
                    <span class="metric-value" id="autoRetaliation">Отключена</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Время работы:</span>
                    <span class="metric-value" id="systemUptime">00:00:00</span>
                </div>
            </div>
        </div>

        <div id="alertBanner" class="alert-banner" style="display: none;">
            🚨 ОБНАРУЖЕНА КРИТИЧЕСКАЯ УГРОЗА - ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ДЕЙСТВИЕ 🚨
        </div>

        <div class="grid grid-2">
            <div class="card card-danger">
                <h3>🎯 АКТИВНЫЕ УГРОЗЫ
                    <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>IP адрес:</strong> Источник угрозы<br>
                            <strong>Тип:</strong> Категория угрозы (сетевая, системная, психологическая)<br>
                            <strong>Серьезность:</strong> Уровень опасности<br>
                            <strong>Действия:</strong> Одобрить или отклонить ответный удар
                        </span>
                    </span>
                </h3>
                <div class="threat-list" id="threatList">
                    <div style="text-align: center; color: #888; padding: 40px;">
                        Активные угрозы не обнаружены
                    </div>
                </div>
            </div>

            <div class="card card-warning">
                <h3>⚔️ ОЧЕРЕДЬ АТАК
                    <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>Тип атаки:</strong> Категория ответного действия<br>
                            <strong>Цель:</strong> IP адрес для ответного удара<br>
                            <strong>Статус:</strong> Ожидает, одобрена, выполняется, завершена<br>
                            <strong>Управление:</strong> Одобрение или отклонение конкретных атак
                        </span>
                    </span>
                </h3>
                <div class="attack-queue" id="attackQueue">
                    <div style="text-align: center; color: #888; padding: 40px;">
                        Атак в очереди нет
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🎮 БОЕВОЕ УПРАВЛЕНИЕ
                <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>Обновить угрозы:</strong> Проверить наличие новых угроз<br>
                            <strong>Одобрить все:</strong> Массовое одобрение всех ожидающих атак<br>
                            <strong>Отклонить все:</strong> Массовое отклонение всех ожидающих атак<br>
                            <strong>Очистить завершенные:</strong> Удалить завершенные атаки из очереди<br>
                            <strong>История атак:</strong> Просмотр истории выполненных атак
                        </span>
                    </span>
            </h3>
            <div class="controls">
                <button class="btn tooltip" onclick="refreshThreats()">
                    🔄 Обновить угрозы
                    <span class="tooltiptext">Проверить наличие новых угроз и атак</span>
                </button>
                <button class="btn btn-success tooltip" onclick="approveAllAttacks()">
                    ✅ Одобрить все
                    <span class="tooltiptext">Одобрить все ожидающие атаки (ОПАСНО)</span>
                </button>
                <button class="btn btn-danger tooltip" onclick="rejectAllAttacks()">
                    ❌ Отклонить все
                    <span class="tooltiptext">Отклонить все ожидающие атаки</span>
                </button>
                <button class="btn btn-warning tooltip" onclick="clearCompleted()">
                    🧹 Очистить завершенные
                    <span class="tooltiptext">Удалить завершенные атаки из очереди</span>
                </button>
                <button class="btn tooltip" onclick="showAttackHistory()">
                    📜 История атак
                    <span class="tooltiptext">Просмотреть историю выполненных атак</span>
                </button>
            </div>
        </div>

        <div class="card">
            <h3>📋 БОЕВОЙ ЖУРНАЛ
                <span class="tooltip">?
                        <span class="tooltiptext">
                            <strong>Журнал событий:</strong> Детальный лог всех боевых операций<br>
                            <strong>Уровни:</strong> INFO - информация, WARNING - предупреждение, ERROR - ошибка, CRITICAL - критическое<br>
                            <strong>Время:</strong> Временная метка каждого события
                        </span>
                    </span>
            </h3>
            <div class="logs" id="combatLogs">
                <div class="log-entry">
                    <span class="log-time">00:00:00</span>
                    <span class="log-level-INFO">[INFO]</span>
                    Боевая панель RSecure инициализирована
                </div>
            </div>
        </div>
    </div>

    <!-- Attack Approval Modal -->
    <div id="attackModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">⚔️ ТРЕБУЕТСЯ ОДОБРЕНИЕ АТАКИ</div>
            <div class="modal-body" id="modalBody">
                <!-- Attack details will be populated here -->
            </div>
            <div class="modal-footer">
                <button class="btn btn-success tooltip" onclick="approveAttack()">
                    ✅ ОДОБРИТЬ АТАКУ
                    <span class="tooltiptext">Запустить ответный удар против цели</span>
                </button>
                <button class="btn btn-danger tooltip" onclick="rejectAttack()">
                    ❌ ОТКЛОНИТЬ АТАКУ
                    <span class="tooltiptext">Отменить ответный удар</span>
                </button>
                <button class="btn tooltip" onclick="closeModal()">
                    🚫 ОТМЕНА
                    <span class="tooltiptext">Закрыть диалог без действий</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentMode = 'human';
        let currentAttackId = null;
        let threats = [];
        let attacks = [];
        let startTime = Date.now();

        function updateMetrics() {
            // Update system uptime
            const uptime = Date.now() - startTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            document.getElementById('systemUptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

            // Update threat counts
            document.getElementById('activeThreats').textContent = threats.length;
            document.getElementById('pendingAttacks').textContent = attacks.filter(a => a.status === 'pending').length;
            document.getElementById('executingAttacks').textContent = attacks.filter(a => a.status === 'executing').length;
            document.getElementById('completedAttacks').textContent = attacks.filter(a => a.status === 'completed').length;
        }

        function addLog(level, message) {
            const logsContainer = document.getElementById('combatLogs');
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            
            const time = new Date().toLocaleTimeString();
            logEntry.innerHTML = `<span class="log-time">${time}</span><span class="log-level-${level}">[${level}]</span> ${message}`;
            
            logsContainer.insertBefore(logEntry, logsContainer.firstChild);
            
            // Keep only last 50 logs
            while (logsContainer.children.length > 50) {
                logsContainer.removeChild(logsContainer.lastChild);
            }
        }

        function setHumanMode() {
            currentMode = 'human';
            updateModeDisplay();
            fetch('/api/set_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'human' })
            });
            addLog('INFO', '🛡️ Переключено на РЕЖИМ ЧЕЛОВЕК - Требуется ручное одобрение');
        }

        function setTurboMode() {
            if (confirm('⚠️ ПРЕДУПРЕЖДЕНИЕ: Турбо режим включает автоматическую ретрибуцию без человеческого одобрения.\\n\\nЭто может привести к саморазрушению системы.\\n\\nПродолжить?')) {
                currentMode = 'turbo';
                updateModeDisplay();
                fetch('/api/set_mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: 'turbo' })
                });
                addLog('CRITICAL', '🚀 ТУРБО РЕЖИМ АКТИВИРОВАН - Автоматическая ретрибуция включена');
            }
        }

        function updateModeDisplay() {
            const indicator = document.getElementById('modeIndicator');
            const modeText = document.getElementById('modeText');
            const modeStatus = document.getElementById('modeStatus');
            const currentModeDiv = document.getElementById('currentMode');
            const modeDescription = document.getElementById('modeDescription');
            const autoRetaliation = document.getElementById('autoRetaliation');

            if (currentMode === 'turbo') {
                indicator.className = 'mode-indicator mode-turbo';
                modeText.textContent = '🚀 ТУРБО РЕЖИМ';
                modeStatus.textContent = 'Автоматическая ретрибуция активна';
                currentModeDiv.textContent = 'Текущий: ТУРБО РЕЖИМ';
                currentModeDiv.style.color = '#ff0000';
                modeDescription.textContent = 'Автоматическая ретрибуция без одобрения человека';
                autoRetaliation.textContent = 'ВКЛЮЧЕНА';
                autoRetaliation.className = 'metric-value metric-critical';
            } else {
                indicator.className = 'mode-indicator mode-human';
                modeText.textContent = '🛡️ РЕЖИМ ЧЕЛОВЕК';
                modeStatus.textContent = 'Требуется ручное одобрение';
                currentModeDiv.textContent = 'Текущий: РЕЖИМ ЧЕЛОВЕК';
                currentModeDiv.style.color = '#00ff44';
                modeDescription.textContent = 'Требуется ручное одобрение для всех атак';
                autoRetaliation.textContent = 'ОТКЛЮЧЕНА';
                autoRetaliation.className = 'metric-value metric-warning';
            }
        }

        function emergencyStop() {
            if (confirm('🛑 ЭКСТРЕННАЯ ОСТАНОВКА - Это остановит все действия ретрибуции.\\n\\nПродолжить?')) {
                fetch('/api/emergency_stop', { method: 'POST' });
                addLog('CRITICAL', '🛑 ЭКСТРЕННАЯ ОСТАНОВКА АКТИВИРОВАНА - Все ретрибуции остановлены');
                setHumanMode();
            }
        }

        function refreshThreats() {
            fetch('/api/threats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        threats = data.threats;
                        attacks = data.attacks;
                        updateThreatDisplay();
                        updateAttackDisplay();
                        updateMetrics();
                        
                        // Show alert banner for critical threats
                        const criticalThreats = threats.filter(t => t.severity === 'critical');
                        const alertBanner = document.getElementById('alertBanner');
                        alertBanner.style.display = criticalThreats.length > 0 ? 'block' : 'none';
                        
                        if (criticalThreats.length > 0) {
                            addLog('CRITICAL', `🚨 Обнаружено ${criticalThreats.length} КРИТИЧЕСКИХ угроз`);
                        }
                    }
                })
                .catch(error => {
                    addLog('ERROR', 'Ошибка обновления угроз: ' + error.message);
                });
        }

        function updateThreatDisplay() {
            const threatList = document.getElementById('threatList');
            
            if (threats.length === 0) {
                threatList.innerHTML = '<div style="text-align: center; color: #888; padding: 40px;">Активные угрозы не обнаружены</div>';
                return;
            }
            
            threatList.innerHTML = threats.map(threat => `
                <div class="threat-item">
                    <div class="threat-header">
                        <span class="threat-ip">${threat.ip}</span>
                        <span class="threat-severity severity-${threat.severity}">${getSeverityText(threat.severity)}</span>
                    </div>
                    <div class="threat-details">Тип: ${getTypeText(threat.type)} | Уверенность: ${(threat.confidence * 100).toFixed(1)}%</div>
                    <div class="threat-details">Уязвимость: ${getVulnerabilityText(threat.vulnerability)}</div>
                    <div class="threat-actions">
                        <button class="btn btn-success tooltip" onclick="approveAttackForThreat('${threat.ip}')">
                            ✅ Одобрить
                            <span class="tooltiptext">Одобрить ответный удар для ${threat.ip}</span>
                        </button>
                        <button class="btn btn-danger tooltip" onclick="rejectAttackForThreat('${threat.ip}')">
                            ❌ Отклонить
                            <span class="tooltiptext">Отклонить ответный удар для ${threat.ip}</span>
                        </button>
                        <button class="btn tooltip" onclick="showThreatDetails('${threat.ip}')">
                            📋 Детали
                            <span class="tooltiptext">Показать подробную информацию об угрозе</span>
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function updateAttackDisplay() {
            const attackQueue = document.getElementById('attackQueue');
            
            if (attacks.length === 0) {
                attackQueue.innerHTML = '<div style="text-align: center; color: #888; padding: 40px;">Атак в очереди нет</div>';
                return;
            }
            
            attackQueue.innerHTML = attacks.map(attack => `
                <div class="attack-item">
                    <div class="attack-header">
                        <span class="attack-type">${getAttackTypeText(attack.type)}</span>
                        <span class="attack-target">${attack.target_ip}</span>
                        <span class="attack-status status-${attack.status}">${getStatusText(attack.status)}</span>
                    </div>
                    <div class="threat-details">Атака: ${getAttackText(attack.attack_type)} | Серьезность: ${getSeverityText(attack.severity)}</div>
                    <div class="threat-details">В очереди: ${new Date(attack.timestamp).toLocaleString()}</div>
                    ${attack.status === 'pending' ? `
                        <div class="threat-actions">
                            <button class="btn btn-success tooltip" onclick="approveAttackById('${attack.id}')">
                                ✅ Одобрить
                                <span class="tooltiptext">Одобрить эту атаку</span>
                            </button>
                            <button class="btn btn-danger tooltip" onclick="rejectAttackById('${attack.id}')">
                                ❌ Отклонить
                                <span class="tooltiptext">Отклонить эту атаку</span>
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }

        // Russian text translation functions
        function getSeverityText(severity) {
            const translations = {
                'critical': 'КРИТИЧЕСКАЯ',
                'high': 'ВЫСОКАЯ',
                'medium': 'СРЕДНЯЯ',
                'low': 'НИЗКАЯ'
            };
            return translations[severity] || severity.toUpperCase();
        }

        function getTypeText(type) {
            const translations = {
                'network': 'Сетевая',
                'system': 'Системная',
                'psychological': 'Психологическая'
            };
            return translations[type] || type;
        }

        function getVulnerabilityText(vulnerability) {
            const translations = {
                'ddos': 'DDoS атака',
                'exploit': 'Эксплойт',
                'phishing': 'Фишинг',
                'brute_force': 'Brute Force',
                'social_engineering': 'Социальная инженерия'
            };
            return translations[vulnerability] || vulnerability;
        }

        function getAttackTypeText(type) {
            const translations = {
                'network': 'СЕТЕВАЯ',
                'system': 'СИСТЕМНАЯ',
                'psychological': 'ПСИХОЛОГИЧЕСКАЯ'
            };
            return translations[type] || type.toUpperCase();
        }

        function getAttackText(attack) {
            const translations = {
                'ddos': 'DDoS',
                'exploit': 'Эксплойт',
                'phishing': 'Фишинг',
                'brute_force': 'Brute Force',
                'social_engineering': 'Социальная инженерия'
            };
            return translations[attack] || attack;
        }

        function getStatusText(status) {
            const translations = {
                'pending': 'ОЖИДАЕТ',
                'approved': 'ОДОБРЕНА',
                'rejected': 'ОТКЛОНЕНА',
                'executing': 'ВЫПОЛНЯЕТСЯ',
                'completed': 'ЗАВЕРШЕНА',
                'failed': 'ПРОВАЛЕНА'
            };
            return translations[status] || status.toUpperCase();
        }

        function approveAttackForThreat(ip) {
            fetch('/api/approve_attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_ip: ip })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('INFO', `✅ Одобрена ретрибуция для ${ip}`);
                    refreshThreats();
                } else {
                    addLog('ERROR', 'Ошибка одобрения атаки: ' + data.error);
                }
            });
        }

        function rejectAttackForThreat(ip) {
            fetch('/api/reject_attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_ip: ip })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('INFO', `❌ Отклонена ретрибуция для ${ip}`);
                    refreshThreats();
                } else {
                    addLog('ERROR', 'Ошибка отклонения атаки: ' + data.error);
                }
            });
        }

        function approveAllAttacks() {
            if (confirm('⚠️ Одобрить ВСЕ ожидающие атаки? Это действие нельзя отменить.')) {
                fetch('/api/approve_all_attacks', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addLog('WARNING', `✅ Одобрено ${data.count} атак`);
                            refreshThreats();
                        } else {
                            addLog('ERROR', 'Ошибка массового одобрения: ' + data.error);
                        }
                    });
            }
        }

        function rejectAllAttacks() {
            if (confirm('⚠️ Отклонить ВСЕ ожидающие атаки?')) {
                fetch('/api/reject_all_attacks', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addLog('INFO', `❌ Отклонено ${data.count} атак`);
                            refreshThreats();
                        } else {
                            addLog('ERROR', 'Ошибка массового отклонения: ' + data.error);
                        }
                    });
            }
        }

        function clearCompleted() {
            fetch('/api/clear_completed', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('INFO', `🧹 Очищено ${data.count} завершенных атак`);
                        refreshThreats();
                    } else {
                        addLog('ERROR', 'Ошибка очистки завершенных атак: ' + data.error);
                    }
                });
        }

        function showThreatDetails(ip) {
            const threat = threats.find(t => t.ip === ip);
            if (threat) {
                alert(`🎯 ДЕТАЛИ УГРОЗЫ\\n\\nIP: ${threat.ip}\\nТип: ${getTypeText(threat.type)}\\nСерьезность: ${getSeverityText(threat.severity)}\\nУверенность: ${(threat.confidence * 100).toFixed(1)}%\\nУязвимость: ${getVulnerabilityText(threat.vulnerability)}\\nВектор атаки: ${getAttackText(threat.attack_vector)}\\n\\nМетаданные: ${JSON.stringify(threat.metadata, null, 2)}`);
            }
        }

        function showAttackHistory() {
            fetch('/api/attack_history')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.history.length > 0) {
                        const history = data.history.map(h => 
                            `${new Date(h.timestamp).toLocaleString()} - ${getAttackTypeText(h.type)} против ${h.target_ip} - ${getStatusText(h.status)}`
                        ).join('\\n');
                        alert('📜 ИСТОРИЯ АТАК\\n\\n' + history);
                    } else {
                        alert('📜 История атак недоступна');
                    }
                });
        }

        function closeModal() {
            document.getElementById('attackModal').style.display = 'none';
            currentAttackId = null;
        }

        function approveAttack() {
            if (currentAttackId) {
                fetch('/api/approve_attack', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ attack_id: currentAttackId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('INFO', `✅ Одобрена атака ${currentAttackId}`);
                        refreshThreats();
                        closeModal();
                    } else {
                        addLog('ERROR', 'Ошибка одобрения атаки: ' + data.error);
                    }
                });
            }
        }

        function rejectAttack() {
            if (currentAttackId) {
                fetch('/api/reject_attack', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ attack_id: currentAttackId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('INFO', `❌ Отклонена атака ${currentAttackId}`);
                        refreshThreats();
                        closeModal();
                    } else {
                        addLog('ERROR', 'Ошибка отклонения атаки: ' + data.error);
                    }
                });
            }
        }

        function approveAttackById(attackId) {
            currentAttackId = attackId;
            const attack = attacks.find(a => a.id === attackId);
            if (attack) {
                document.getElementById('modalBody').innerHTML = `
                    <h4>⚔️ Детали атаки</h4>
                    <p><strong>Тип:</strong> ${getAttackTypeText(attack.type)}</p>
                    <p><strong>Цель:</strong> ${attack.target_ip}</p>
                    <p><strong>Атака:</strong> ${getAttackText(attack.attack_type)}</p>
                    <p><strong>Серьезность:</strong> ${getSeverityText(attack.severity)}</p>
                    <p><strong>Уверенность:</strong> ${(attack.confidence * 100).toFixed(1)}%</p>
                    <p><strong>В очереди:</strong> ${new Date(attack.timestamp).toLocaleString()}</p>
                    <hr>
                    <p><strong>⚠️ Это действие инициирует ответный удар против цели.</strong></p>
                    <p><strong>⚠️ Это может иметь юридические и этические последствия.</strong></p>
                `;
                document.getElementById('attackModal').style.display = 'block';
            }
        }

        function rejectAttackById(attackId) {
            fetch('/api/reject_attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ attack_id: attackId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog('INFO', `❌ Отклонена атака ${attackId}`);
                    refreshThreats();
                } else {
                    addLog('ERROR', 'Ошибка отклонения атаки: ' + data.error);
                }
            });
        }

        // Auto-refresh every 5 seconds
        setInterval(() => {
            refreshThreats();
            updateMetrics();
        }, 5000);

        // Initialize
        updateModeDisplay();
        addLog('INFO', '🔪 Боевая панель RSecure инициализирована');
        addLog('INFO', '🛡️ Активен режим человек - Требуется ручное одобрение');
        refreshThreats();
        updateMetrics();
    </script>
</body>
</html>
"""

class RussianRSecureDashboard:
    """Russian RSecure Dashboard with Combat Control"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'rsecure_combat_dashboard_russian_2024'
        
        # Combat control state
        self.current_mode = 'human'  # 'human' or 'turbo'
        self.retaliation_system = None
        self.pending_attacks = []
        self.approved_attacks = []
        self.rejected_attacks = []
        self.executing_attacks = []
        self.completed_attacks = []
        self.attack_history = []
        
        # Setup routes and logging
        self.setup_routes()
        self.setup_logging()
        
        # Initialize retaliation system
        self.initialize_retaliation_system()
        
        # Metrics
        self.start_time = datetime.now()
        self.threats_detected = []
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('rsecure_russian_dashboard')
        
        # Combat-specific log handler
        combat_handler = logging.FileHandler(log_dir / 'combat_operations_ru.log')
        combat_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(combat_handler)
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return RUSSIAN_DASHBOARD_HTML
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'success': True,
                'data': {
                    'mode': self.current_mode,
                    'uptime': str(datetime.now() - self.start_time),
                    'threats_count': len(self.threats_detected),
                    'pending_attacks': len(self.pending_attacks),
                    'executing_attacks': len(self.executing_attacks),
                    'completed_attacks': len(self.completed_attacks),
                    'retaliation_system_active': self.retaliation_system is not None,
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        @self.app.route('/api/threats')
        def get_threats():
            # Simulate threat detection with Russian descriptions
            simulated_threats = [
                {
                    'ip': '192.168.1.100',
                    'type': 'network',
                    'severity': 'critical',
                    'confidence': 0.95,
                    'vulnerability': 'ddos',
                    'attack_vector': 'syn_flood',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'source': 'network_monitor', 'packets_per_second': 1500}
                },
                {
                    'ip': '10.0.0.50',
                    'type': 'system',
                    'severity': 'high',
                    'confidence': 0.85,
                    'vulnerability': 'exploit',
                    'attack_vector': 'smb_exploit',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'source': 'system_monitor', 'process': 'suspicious'}
                },
                {
                    'ip': '172.16.0.25',
                    'type': 'psychological',
                    'severity': 'medium',
                    'confidence': 0.75,
                    'vulnerability': 'social_engineering',
                    'attack_vector': 'phishing',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'source': 'email_monitor', 'campaign': 'active'}
                }
            ]
            
            # Combine simulated and real threats
            all_threats = simulated_threats + self.threats_detected
            
            # Prepare attacks data
            all_attacks = []
            for attack in self.pending_attacks:
                all_attacks.append({
                    'id': attack.get('id', 'unknown'),
                    'type': attack.get('type', 'unknown'),
                    'target_ip': attack.get('target_ip', 'unknown'),
                    'attack_type': attack.get('attack_type', 'unknown'),
                    'severity': attack.get('severity', 'unknown'),
                    'status': 'pending',
                    'timestamp': attack.get('timestamp', datetime.now().isoformat())
                })
            
            for attack in self.approved_attacks:
                all_attacks.append({
                    'id': attack.get('id', 'unknown'),
                    'type': attack.get('type', 'unknown'),
                    'target_ip': attack.get('target_ip', 'unknown'),
                    'attack_type': attack.get('attack_type', 'unknown'),
                    'severity': attack.get('severity', 'unknown'),
                    'status': 'approved',
                    'timestamp': attack.get('timestamp', datetime.now().isoformat())
                })
            
            for attack in self.executing_attacks:
                all_attacks.append({
                    'id': attack.get('id', 'unknown'),
                    'type': attack.get('type', 'unknown'),
                    'target_ip': attack.get('target_ip', 'unknown'),
                    'attack_type': attack.get('attack_type', 'unknown'),
                    'severity': attack.get('severity', 'unknown'),
                    'status': 'executing',
                    'timestamp': attack.get('timestamp', datetime.now().isoformat())
                })
            
            for attack in self.completed_attacks:
                all_attacks.append({
                    'id': attack.get('id', 'unknown'),
                    'type': attack.get('type', 'unknown'),
                    'target_ip': attack.get('target_ip', 'unknown'),
                    'attack_type': attack.get('attack_type', 'unknown'),
                    'severity': attack.get('severity', 'unknown'),
                    'status': 'completed',
                    'timestamp': attack.get('timestamp', datetime.now().isoformat())
                })
            
            return jsonify({
                'success': True,
                'threats': all_threats,
                'attacks': all_attacks
            })
        
        @self.app.route('/api/set_mode', methods=['POST'])
        def set_mode():
            try:
                data = request.get_json()
                mode = data.get('mode', 'human')
                
                if mode not in ['human', 'turbo']:
                    return jsonify({'success': False, 'error': 'Неверный режим'})
                
                self.current_mode = mode
                
                # Update retaliation system configuration
                if self.retaliation_system:
                    if mode == 'turbo':
                        # Enable auto-retaliation
                        self.retaliation_system.config['auto_retaliation'] = True
                        self.retaliation_system.config['require_confirmation'] = False
                        self.logger.critical("🚀 ТУРБО РЕЖИМ АКТИВИРОВАН - Авто-ретрибуция включена")
                    else:
                        # Disable auto-retaliation
                        self.retaliation_system.config['auto_retaliation'] = False
                        self.retaliation_system.config['require_confirmation'] = True
                        self.logger.info("🛡️ РЕЖИМ ЧЕЛОВЕК АКТИВИРОВАН - Требуется ручное одобрение")
                
                return jsonify({'success': True})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/emergency_stop', methods=['POST'])
        def emergency_stop():
            try:
                self.logger.critical("🛑 ЭКСТРЕННАЯ ОСТАНОВКА АКТИВИРОВАНА")
                
                # Stop retaliation system
                if self.retaliation_system:
                    self.retaliation_system.stop_retaliation()
                
                # Clear all pending attacks
                self.pending_attacks.clear()
                self.approved_attacks.clear()
                
                # Switch to human mode
                self.current_mode = 'human'
                
                return jsonify({'success': True})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/approve_attack', methods=['POST'])
        def approve_attack():
            try:
                data = request.get_json()
                attack_id = data.get('attack_id')
                target_ip = data.get('target_ip')
                
                if attack_id:
                    # Approve specific attack
                    attack = self._find_attack_by_id(attack_id)
                    if attack and attack in self.pending_attacks:
                        self.pending_attacks.remove(attack)
                        self.approved_attacks.append(attack)
                        self._execute_attack(attack)
                        self.logger.info(f"✅ Одобрена атака {attack_id} против {target_ip}")
                elif target_ip:
                    # Approve all attacks for target
                    target_attacks = [a for a in self.pending_attacks if a.get('target_ip') == target_ip]
                    for attack in target_attacks:
                        self.pending_attacks.remove(attack)
                        self.approved_attacks.append(attack)
                        self._execute_attack(attack)
                    self.logger.info(f"✅ Одобрено {len(target_attacks)} атак против {target_ip}")
                
                return jsonify({'success': True})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/reject_attack', methods=['POST'])
        def reject_attack():
            try:
                data = request.get_json()
                attack_id = data.get('attack_id')
                target_ip = data.get('target_ip')
                
                if attack_id:
                    # Reject specific attack
                    attack = self._find_attack_by_id(attack_id)
                    if attack and attack in self.pending_attacks:
                        self.pending_attacks.remove(attack)
                        self.rejected_attacks.append(attack)
                        self.logger.info(f"❌ Отклонена атака {attack_id}")
                elif target_ip:
                    # Reject all attacks for target
                    target_attacks = [a for a in self.pending_attacks if a.get('target_ip') == target_ip]
                    for attack in target_attacks:
                        self.pending_attacks.remove(attack)
                        self.rejected_attacks.append(attack)
                    self.logger.info(f"❌ Отклонено {len(target_attacks)} атак против {target_ip}")
                
                return jsonify({'success': True})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/approve_all_attacks', methods=['POST'])
        def approve_all_attacks():
            try:
                count = len(self.pending_attacks)
                
                # Move all pending attacks to approved
                for attack in self.pending_attacks.copy():
                    self.pending_attacks.remove(attack)
                    self.approved_attacks.append(attack)
                    self._execute_attack(attack)
                
                self.logger.warning(f"✅ Одобрено ВСЕ {count} ожидающих атак")
                return jsonify({'success': True, 'count': count})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/reject_all_attacks', methods=['POST'])
        def reject_all_attacks():
            try:
                count = len(self.pending_attacks)
                
                # Move all pending attacks to rejected
                for attack in self.pending_attacks:
                    self.rejected_attacks.append(attack)
                
                self.pending_attacks.clear()
                self.logger.info(f"❌ Отклонено ВСЕ {count} ожидающих атак")
                return jsonify({'success': True, 'count': count})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/clear_completed', methods=['POST'])
        def clear_completed():
            try:
                count = len(self.completed_attacks)
                
                # Move completed attacks to history
                for attack in self.completed_attacks:
                    attack['completed_at'] = datetime.now().isoformat()
                    self.attack_history.append(attack)
                
                self.completed_attacks.clear()
                self.logger.info(f"🧹 Очищено {count} завершенных атак в историю")
                return jsonify({'success': True, 'count': count})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/attack_history')
        def get_attack_history():
            try:
                return jsonify({
                    'success': True,
                    'history': self.attack_history[-50:]  # Return last 50 attacks
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def initialize_retaliation_system(self):
        """Initialize retaliation system"""
        try:
            config = {
                'auto_retaliation': False,  # Start with manual approval
                'retaliation_threshold': 0.8,
                'max_concurrent_attacks': 5,
                'attack_timeout': 300,
                'network_attacks_enabled': True,
                'psychological_enabled': True,
                'quantum_enabled': False,
                'require_confirmation': True,
                'log_all_actions': True
            }
            
            self.retaliation_system = RSecureRetaliationSystem(config)
            self.retaliation_system.start_retaliation()
            
            self.logger.info("🔪 Система ответного удара инициализирована с человеческим одобрением")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации системы ответного удара: {e}")
    
    def _find_attack_by_id(self, attack_id):
        """Find attack by ID"""
        for attack in self.pending_attacks + self.approved_attacks + self.executing_attacks + self.completed_attacks:
            if attack.get('id') == attack_id:
                return attack
        return None
    
    def _execute_attack(self, attack):
        """Execute approved attack"""
        try:
            # Move to executing
            if attack in self.approved_attacks:
                self.approved_attacks.remove(attack)
            
            attack['status'] = 'executing'
            attack['execution_time'] = datetime.now().isoformat()
            self.executing_attacks.append(attack)
            
            # Execute with retaliation system
            if self.retaliation_system:
                target_info = {
                    'ip': attack.get('target_ip'),
                    'type': attack.get('type'),
                    'vulnerability': attack.get('attack_type'),
                    'attack_vector': attack.get('attack_vector', 'unknown'),
                    'confidence': attack.get('confidence', 0.8),
                    'metadata': attack.get('metadata', {})
                }
                
                success = self.retaliation_system.add_target(target_info)
                
                if success:
                    self.logger.info(f"⚔️ Выполнение атаки: {attack.get('type')} против {attack.get('target_ip')}")
                    
                    # Simulate attack completion
                    threading.Timer(30.0, self._complete_attack, args=[attack]).start()
                else:
                    self.logger.error(f"❌ Ошибка выполнения атаки против {attack.get('target_ip')}")
                    self._fail_attack(attack)
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения атаки: {e}")
            self._fail_attack(attack)
    
    def _complete_attack(self, attack):
        """Mark attack as completed"""
        try:
            if attack in self.executing_attacks:
                self.executing_attacks.remove(attack)
            
            attack['status'] = 'completed'
            attack['completed_time'] = datetime.now().isoformat()
            self.completed_attacks.append(attack)
            
            self.logger.info(f"✅ Атака завершена: {attack.get('type')} против {attack.get('target_ip')}")
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения атаки: {e}")
    
    def _fail_attack(self, attack):
        """Mark attack as failed"""
        try:
            if attack in self.executing_attacks:
                self.executing_attacks.remove(attack)
            
            attack['status'] = 'failed'
            attack['failed_time'] = datetime.now().isoformat()
            self.completed_attacks.append(attack)
            
            self.logger.error(f"❌ Атака провалена: {attack.get('type')} против {attack.get('target_ip')}")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки провала атаки: {e}")
    
    def simulate_threats(self):
        """Simulate threat detection for testing"""
        import random
        
        threat_types = ['network', 'system', 'psychological']
        severities = ['low', 'medium', 'high', 'critical']
        
        while True:
            try:
                if random.random() < 0.3:  # 30% chance of new threat
                    threat = {
                        'ip': f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                        'type': random.choice(threat_types),
                        'severity': random.choice(severities),
                        'confidence': random.uniform(0.6, 0.95),
                        'vulnerability': random.choice(['ddos', 'exploit', 'phishing', 'brute_force']),
                        'attack_vector': random.choice(['syn_flood', 'smb_exploit', 'fake_alerts', 'ssh_bruteforce']),
                        'timestamp': datetime.now().isoformat(),
                        'metadata': {'source': 'simulation', 'auto_generated': True}
                    }
                    
                    self.threats_detected.append(threat)
                    
                    # Create attack proposal
                    attack_proposal = {
                        'id': f"attack_{int(time.time())}_{random.randint(1000, 9999)}",
                        'type': threat['type'],
                        'target_ip': threat['ip'],
                        'attack_type': threat['vulnerability'],
                        'severity': threat['severity'],
                        'confidence': threat['confidence'],
                        'timestamp': datetime.now().isoformat(),
                        'metadata': threat['metadata']
                    }
                    
                    self.pending_attacks.append(attack_proposal)
                    
                    self.logger.warning(f"🎯 Обнаружена новая угроза: {threat['severity']} {threat['type']} от {threat['ip']}")
                    
                    # Auto-approve in turbo mode
                    if self.current_mode == 'turbo':
                        self._execute_attack(attack_proposal)
                        self.logger.critical(f"🚀 ТУРБО РЕЖИМ: Авто-одобрена атака против {threat['ip']}")
                
                # Clean up old threats
                if len(self.threats_detected) > 10:
                    self.threats_detected = self.threats_detected[-10:]
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Ошибка в симуляции угроз: {e}")
                time.sleep(10)
    
    def run(self, host='0.0.0.0', port=5003, debug=False):
        """Run the Russian dashboard"""
        self.logger.info(f"🔪 Запуск Русской Боевой Панели RSecure на http://{host}:{port}")
        self.logger.info("🛡️ Активен режим человек - Требуется ручное одобрение")
        self.logger.info("🔪 Система ответного удара интегрирована")
        
        # Start threat simulation in background
        threat_thread = threading.Thread(target=self.simulate_threats, daemon=True)
        threat_thread.start()
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Main function"""
    print("🔪 RSECURE РУССКАЯ БОЕВАЯ ПАНЕЛЬ")
    print("=" * 60)
    print("⚔️ Расширенное управление угрозами и ответными ударами")
    print("🛡️ Система одобрения человеком для предотвращения саморазрушения")
    print("🚀 Турбо режим для автоматической ретрибуции")
    print("🎯 Мониторинг боевых действий в реальном времени")
    print("📖 Полностью русифицированный интерфейс с подсказками")
    print("=" * 60)
    print("⚠️  ТОЛЬКО ДЛЯ ОБРАЗОВАТЕЛЬНЫХ И ЗАКОННЫХ ЦЕЛЕЙ БЕЗОПАСНОСТИ")
    print("=" * 60)
    
    dashboard = RussianRSecureDashboard()
    
    try:
        dashboard.run(host='0.0.0.0', port=5003)
    except KeyboardInterrupt:
        print("\n🛑 Остановка русской панели...")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
