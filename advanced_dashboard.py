#!/usr/bin/env python3
"""
Advanced RSecure Dashboard with Combat Control
Extended dashboard with human approval and turbo mode capabilities
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

# Advanced HTML template with combat control
ADVANCED_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSecure Combat Dashboard</title>
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
    </style>
</head>
<body>
    <div class="mode-indicator" id="modeIndicator">
        <div id="modeText">🛡️ HUMAN MODE</div>
        <div id="modeStatus">Manual approval required</div>
    </div>

    <div class="container">
        <div class="header">
            <h1>🔪 RSECURE COMBAT DASHBOARD</h1>
            <p>Advanced Threat Response & Retaliation Control</p>
        </div>

        <div class="grid grid-3">
            <div class="card card-danger">
                <h3>🎯 THREAT STATUS</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-value" id="activeThreats">0</div>
                        <div class="status-label">Active Threats</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="pendingAttacks">0</div>
                        <div class="status-label">Pending Attacks</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="executingAttacks">0</div>
                        <div class="status-label">Executing</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="completedAttacks">0</div>
                        <div class="status-label">Completed</div>
                    </div>
                </div>
            </div>

            <div class="card card-warning">
                <h3>⚡ COMBAT MODE</h3>
                <div class="controls controls-center">
                    <button class="btn btn-success" onclick="setHumanMode()">🛡️ Human Mode</button>
                    <button class="btn btn-turbo" onclick="setTurboMode()">🚀 Turbo Mode</button>
                    <button class="btn btn-warning" onclick="emergencyStop()">🛑 EMERGENCY STOP</button>
                </div>
                <div style="margin-top: 15px; text-align: center;">
                    <div id="currentMode" style="font-size: 1.2em; font-weight: bold;">Current: HUMAN MODE</div>
                    <div id="modeDescription" style="color: #888; margin-top: 5px;">Manual approval required for all attacks</div>
                </div>
            </div>

            <div class="card card-success">
                <h3>📊 SYSTEM STATUS</h3>
                <div class="metric">
                    <span class="metric-label">Ollama Status:</span>
                    <span class="metric-value metric-success">Online</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Retaliation System:</span>
                    <span class="metric-value metric-success">Active</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Auto-Retaliation:</span>
                    <span class="metric-value" id="autoRetaliation">Disabled</span>
                </div>
                <div class="metric">
                    <span class="metric-label">System Uptime:</span>
                    <span class="metric-value" id="systemUptime">00:00:00</span>
                </div>
            </div>
        </div>

        <div id="alertBanner" class="alert-banner" style="display: none;">
            🚨 CRITICAL THREAT DETECTED - IMMEDIATE ACTION REQUIRED 🚨
        </div>

        <div class="grid grid-2">
            <div class="card card-danger">
                <h3>🎯 ACTIVE THREATS</h3>
                <div class="threat-list" id="threatList">
                    <div style="text-align: center; color: #888; padding: 40px;">
                        No active threats detected
                    </div>
                </div>
            </div>

            <div class="card card-warning">
                <h3>⚔️ ATTACK QUEUE</h3>
                <div class="attack-queue" id="attackQueue">
                    <div style="text-align: center; color: #888; padding: 40px;">
                        No attacks in queue
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🎮 COMBAT CONTROLS</h3>
            <div class="controls">
                <button class="btn" onclick="refreshThreats()">🔄 Refresh Threats</button>
                <button class="btn btn-success" onclick="approveAllAttacks()">✅ Approve All</button>
                <button class="btn btn-danger" onclick="rejectAllAttacks()">❌ Reject All</button>
                <button class="btn btn-warning" onclick="clearCompleted()">🧹 Clear Completed</button>
                <button class="btn" onclick="showAttackHistory()">📜 Attack History</button>
            </div>
        </div>

        <div class="card">
            <h3>📋 COMBAT LOGS</h3>
            <div class="logs" id="combatLogs">
                <div class="log-entry">
                    <span class="log-time">00:00:00</span>
                    <span class="log-level-INFO">[INFO]</span>
                    RSecure Combat Dashboard initialized
                </div>
            </div>
        </div>
    </div>

    <!-- Attack Approval Modal -->
    <div id="attackModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">⚔️ ATTACK APPROVAL REQUIRED</div>
            <div class="modal-body" id="modalBody">
                <!-- Attack details will be populated here -->
            </div>
            <div class="modal-footer">
                <button class="btn btn-success" onclick="approveAttack()">✅ APPROVE ATTACK</button>
                <button class="btn btn-danger" onclick="rejectAttack()">❌ REJECT ATTACK</button>
                <button class="btn" onclick="closeModal()">🚫 CANCEL</button>
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
            addLog('INFO', '🛡️ Switched to HUMAN MODE - Manual approval required');
        }

        function setTurboMode() {
            if (confirm('⚠️ WARNING: Turbo mode enables automatic retaliation without human approval.\\n\\nThis can lead to system self-destruction.\\n\\nContinue?')) {
                currentMode = 'turbo';
                updateModeDisplay();
                fetch('/api/set_mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: 'turbo' })
                });
                addLog('CRITICAL', '🚀 TURBO MODE ACTIVATED - Automatic retaliation enabled');
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
                modeText.textContent = '🚀 TURBO MODE';
                modeStatus.textContent = 'Automatic retaliation active';
                currentModeDiv.textContent = 'Current: TURBO MODE';
                currentModeDiv.style.color = '#ff0000';
                modeDescription.textContent = 'Automatic retaliation without human approval';
                autoRetaliation.textContent = 'ENABLED';
                autoRetaliation.className = 'metric-value metric-critical';
            } else {
                indicator.className = 'mode-indicator mode-human';
                modeText.textContent = '🛡️ HUMAN MODE';
                modeStatus.textContent = 'Manual approval required';
                currentModeDiv.textContent = 'Current: HUMAN MODE';
                currentModeDiv.style.color = '#00ff44';
                modeDescription.textContent = 'Manual approval required for all attacks';
                autoRetaliation.textContent = 'DISABLED';
                autoRetaliation.className = 'metric-value metric-warning';
            }
        }

        function emergencyStop() {
            if (confirm('🛑 EMERGENCY STOP - This will halt all retaliation activities.\\n\\nContinue?')) {
                fetch('/api/emergency_stop', { method: 'POST' });
                addLog('CRITICAL', '🛑 EMERGENCY STOP ACTIVATED - All retaliation halted');
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
                            addLog('CRITICAL', `🚨 ${criticalThreats.length} CRITICAL threats detected`);
                        }
                    }
                })
                .catch(error => {
                    addLog('ERROR', 'Failed to refresh threats: ' + error.message);
                });
        }

        function updateThreatDisplay() {
            const threatList = document.getElementById('threatList');
            
            if (threats.length === 0) {
                threatList.innerHTML = '<div style="text-align: center; color: #888; padding: 40px;">No active threats detected</div>';
                return;
            }
            
            threatList.innerHTML = threats.map(threat => `
                <div class="threat-item">
                    <div class="threat-header">
                        <span class="threat-ip">${threat.ip}</span>
                        <span class="threat-severity severity-${threat.severity}">${threat.severity.toUpperCase()}</span>
                    </div>
                    <div class="threat-details">Type: ${threat.type} | Confidence: ${(threat.confidence * 100).toFixed(1)}%</div>
                    <div class="threat-details">Vulnerability: ${threat.vulnerability}</div>
                    <div class="threat-actions">
                        <button class="btn btn-success" onclick="approveAttackForThreat('${threat.ip}')">✅ Approve</button>
                        <button class="btn btn-danger" onclick="rejectAttackForThreat('${threat.ip}')">❌ Reject</button>
                        <button class="btn" onclick="showThreatDetails('${threat.ip}')">📋 Details</button>
                    </div>
                </div>
            `).join('');
        }

        function updateAttackDisplay() {
            const attackQueue = document.getElementById('attackQueue');
            
            if (attacks.length === 0) {
                attackQueue.innerHTML = '<div style="text-align: center; color: #888; padding: 40px;">No attacks in queue</div>';
                return;
            }
            
            attackQueue.innerHTML = attacks.map(attack => `
                <div class="attack-item">
                    <div class="attack-header">
                        <span class="attack-type">${attack.type.toUpperCase()}</span>
                        <span class="attack-target">${attack.target_ip}</span>
                        <span class="attack-status status-${attack.status}">${attack.status.toUpperCase()}</span>
                    </div>
                    <div class="threat-details">Attack: ${attack.attack_type} | Severity: ${attack.severity}</div>
                    <div class="threat-details">Queued: ${new Date(attack.timestamp).toLocaleString()}</div>
                    ${attack.status === 'pending' ? `
                        <div class="threat-actions">
                            <button class="btn btn-success" onclick="approveAttackById('${attack.id}')">✅ Approve</button>
                            <button class="btn btn-danger" onclick="rejectAttackById('${attack.id}')">❌ Reject</button>
                        </div>
                    ` : ''}
                </div>
            `).join('');
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
                    addLog('INFO', `✅ Approved retaliation for ${ip}`);
                    refreshThreats();
                } else {
                    addLog('ERROR', 'Failed to approve attack: ' + data.error);
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
                    addLog('INFO', `❌ Rejected retaliation for ${ip}`);
                    refreshThreats();
                } else {
                    addLog('ERROR', 'Failed to reject attack: ' + data.error);
                }
            });
        }

        function approveAllAttacks() {
            if (confirm('⚠️ Approve ALL pending attacks? This cannot be undone.')) {
                fetch('/api/approve_all_attacks', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addLog('WARNING', `✅ Approved ${data.count} attacks`);
                            refreshThreats();
                        } else {
                            addLog('ERROR', 'Failed to approve all attacks: ' + data.error);
                        }
                    });
            }
        }

        function rejectAllAttacks() {
            if (confirm('⚠️ Reject ALL pending attacks?')) {
                fetch('/api/reject_all_attacks', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addLog('INFO', `❌ Rejected ${data.count} attacks`);
                            refreshThreats();
                        } else {
                            addLog('ERROR', 'Failed to reject all attacks: ' + data.error);
                        }
                    });
            }
        }

        function clearCompleted() {
            fetch('/api/clear_completed', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('INFO', `🧹 Cleared ${data.count} completed attacks`);
                        refreshThreats();
                    } else {
                        addLog('ERROR', 'Failed to clear completed attacks: ' + data.error);
                    }
                });
        }

        function showThreatDetails(ip) {
            const threat = threats.find(t => t.ip === ip);
            if (threat) {
                alert(`🎯 THREAT DETAILS\\n\\nIP: ${threat.ip}\\nType: ${threat.type}\\nSeverity: ${threat.severity}\\nConfidence: ${(threat.confidence * 100).toFixed(1)}%\\nVulnerability: ${threat.vulnerability}\\nAttack Vector: ${threat.attack_vector}\\n\\nMetadata: ${JSON.stringify(threat.metadata, null, 2)}`);
            }
        }

        function showAttackHistory() {
            fetch('/api/attack_history')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.history.length > 0) {
                        const history = data.history.map(h => 
                            `${new Date(h.timestamp).toLocaleString()} - ${h.type} against ${h.target_ip} - ${h.status}`
                        ).join('\\n');
                        alert('📜 ATTACK HISTORY\\n\\n' + history);
                    } else {
                        alert('📜 No attack history available');
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
                        addLog('INFO', `✅ Approved attack ${currentAttackId}`);
                        refreshThreats();
                        closeModal();
                    } else {
                        addLog('ERROR', 'Failed to approve attack: ' + data.error);
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
                        addLog('INFO', `❌ Rejected attack ${currentAttackId}`);
                        refreshThreats();
                        closeModal();
                    } else {
                        addLog('ERROR', 'Failed to reject attack: ' + data.error);
                    }
                });
            }
        }

        function approveAttackById(attackId) {
            currentAttackId = attackId;
            const attack = attacks.find(a => a.id === attackId);
            if (attack) {
                document.getElementById('modalBody').innerHTML = `
                    <h4>⚔️ Attack Details</h4>
                    <p><strong>Type:</strong> ${attack.type}</p>
                    <p><strong>Target:</strong> ${attack.target_ip}</p>
                    <p><strong>Attack:</strong> ${attack.attack_type}</p>
                    <p><strong>Severity:</strong> ${attack.severity}</p>
                    <p><strong>Confidence:</strong> ${(attack.confidence * 100).toFixed(1)}%</p>
                    <p><strong>Queued:</strong> ${new Date(attack.timestamp).toLocaleString()}</p>
                    <hr>
                    <p><strong>⚠️ This action will initiate retaliation against the target.</strong></p>
                    <p><strong>⚠️ This may have legal and ethical implications.</strong></p>
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
                    addLog('INFO', `❌ Rejected attack ${attackId}`);
                    refreshThreats();
                } else {
                    addLog('ERROR', 'Failed to reject attack: ' + data.error);
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
        addLog('INFO', '🔪 RSecure Combat Dashboard initialized');
        addLog('INFO', '🛡️ Human mode active - Manual approval required');
        refreshThreats();
        updateMetrics();
    </script>
</body>
</html>
"""

class AdvancedRSecureDashboard:
    """Advanced RSecure Dashboard with Combat Control"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'rsecure_combat_dashboard_2024'
        
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
        self.logger = logging.getLogger('rsecure_combat_dashboard')
        
        # Combat-specific log handler
        combat_handler = logging.FileHandler(log_dir / 'combat_operations.log')
        combat_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(combat_handler)
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return ADVANCED_DASHBOARD_HTML
        
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
            # Simulate threat detection
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
                    return jsonify({'success': False, 'error': 'Invalid mode'})
                
                self.current_mode = mode
                
                # Update retaliation system configuration
                if self.retaliation_system:
                    if mode == 'turbo':
                        # Enable auto-retaliation
                        self.retaliation_system.config['auto_retaliation'] = True
                        self.retaliation_system.config['require_confirmation'] = False
                        self.logger.critical("🚀 TURBO MODE ACTIVATED - Auto-retaliation enabled")
                    else:
                        # Disable auto-retaliation
                        self.retaliation_system.config['auto_retaliation'] = False
                        self.retaliation_system.config['require_confirmation'] = True
                        self.logger.info("🛡️ HUMAN MODE ACTIVATED - Manual approval required")
                
                return jsonify({'success': True})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/emergency_stop', methods=['POST'])
        def emergency_stop():
            try:
                self.logger.critical("🛑 EMERGENCY STOP ACTIVATED")
                
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
                        self.logger.info(f"✅ Approved attack {attack_id} against {target_ip}")
                elif target_ip:
                    # Approve all attacks for target
                    target_attacks = [a for a in self.pending_attacks if a.get('target_ip') == target_ip]
                    for attack in target_attacks:
                        self.pending_attacks.remove(attack)
                        self.approved_attacks.append(attack)
                        self._execute_attack(attack)
                    self.logger.info(f"✅ Approved {len(target_attacks)} attacks against {target_ip}")
                
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
                        self.logger.info(f"❌ Rejected attack {attack_id}")
                elif target_ip:
                    # Reject all attacks for target
                    target_attacks = [a for a in self.pending_attacks if a.get('target_ip') == target_ip]
                    for attack in target_attacks:
                        self.pending_attacks.remove(attack)
                        self.rejected_attacks.append(attack)
                    self.logger.info(f"❌ Rejected {len(target_attacks)} attacks against {target_ip}")
                
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
                
                self.logger.warning(f"✅ Approved ALL {count} pending attacks")
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
                self.logger.info(f"❌ Rejected ALL {count} pending attacks")
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
                self.logger.info(f"🧹 Cleared {count} completed attacks to history")
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
            
            self.logger.info("🔪 Retaliation system initialized with human approval")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize retaliation system: {e}")
    
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
                    self.logger.info(f"⚔️ Executing attack: {attack.get('type')} against {attack.get('target_ip')}")
                    
                    # Simulate attack completion
                    threading.Timer(30.0, self._complete_attack, args=[attack]).start()
                else:
                    self.logger.error(f"❌ Failed to execute attack against {attack.get('target_ip')}")
                    self._fail_attack(attack)
            
        except Exception as e:
            self.logger.error(f"Error executing attack: {e}")
            self._fail_attack(attack)
    
    def _complete_attack(self, attack):
        """Mark attack as completed"""
        try:
            if attack in self.executing_attacks:
                self.executing_attacks.remove(attack)
            
            attack['status'] = 'completed'
            attack['completed_time'] = datetime.now().isoformat()
            self.completed_attacks.append(attack)
            
            self.logger.info(f"✅ Attack completed: {attack.get('type')} against {attack.get('target_ip')}")
            
        except Exception as e:
            self.logger.error(f"Error completing attack: {e}")
    
    def _fail_attack(self, attack):
        """Mark attack as failed"""
        try:
            if attack in self.executing_attacks:
                self.executing_attacks.remove(attack)
            
            attack['status'] = 'failed'
            attack['failed_time'] = datetime.now().isoformat()
            self.completed_attacks.append(attack)
            
            self.logger.error(f"❌ Attack failed: {attack.get('type')} against {attack.get('target_ip')}")
            
        except Exception as e:
            self.logger.error(f"Error failing attack: {e}")
    
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
                    
                    self.logger.warning(f"🎯 New threat detected: {threat['severity']} {threat['type']} from {threat['ip']}")
                    
                    # Auto-approve in turbo mode
                    if self.current_mode == 'turbo':
                        self._execute_attack(attack_proposal)
                        self.logger.critical(f"🚀 TURBO MODE: Auto-approved attack against {threat['ip']}")
                
                # Clean up old threats
                if len(self.threats_detected) > 10:
                    self.threats_detected = self.threats_detected[-10:]
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in threat simulation: {e}")
                time.sleep(10)
    
    def run(self, host='0.0.0.0', port=5002, debug=False):
        """Run the advanced dashboard"""
        self.logger.info(f"🔪 Starting Advanced RSecure Combat Dashboard on http://{host}:{port}")
        self.logger.info("🛡️ Human mode active - Manual approval required")
        self.logger.info("🔪 Retaliation system integrated")
        
        # Start threat simulation in background
        threat_thread = threading.Thread(target=self.simulate_threats, daemon=True)
        threat_thread.start()
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Main function"""
    print("🔪 RSECURE ADVANCED COMBAT DASHBOARD")
    print("=" * 60)
    print("⚔️ Extended threat response & retaliation control")
    print("🛡️ Human approval system to prevent self-destruction")
    print("🚀 Turbo mode for automatic retaliation")
    print("🎯 Real-time combat monitoring and decision making")
    print("=" * 60)
    print("⚠️  FOR EDUCATIONAL AND LEGITIMATE SECURITY PURPOSES ONLY")
    print("=" * 60)
    
    dashboard = AdvancedRSecureDashboard()
    
    try:
        dashboard.run(host='0.0.0.0', port=5002)
    except KeyboardInterrupt:
        print("\n🛑 Stopping advanced dashboard...")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
