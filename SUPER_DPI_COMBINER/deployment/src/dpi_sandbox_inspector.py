#!/usr/bin/env python3
"""
DPI Sandbox Inspector - Анализ TLS-пакетов для классификации сбросов соединений
"""

import os
import asyncio
import logging
import json
from typing import Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict

class ConnectionDropReason(Enum):
    """Причина сброса соединения"""
    UNKNOWN = "unknown"
    DPI_REQUEST_DROP = "DPI Request Drop"
    DPI_DEEP_INSPECT_DROP = "DPI Deep Inspect Drop"
    SERVER_ERROR = "Server Error"
    CLEAN = "Clean"

@dataclass
class ConnectionAnalysis:
    """Результат анализа соединения"""
    domain: str
    server_hello_received: bool
    drop_reason: ConnectionDropReason
    bytes_from_server: int
    tls_version: Optional[str] = None
    timestamp: float = 0.0

class DpiSandboxInspector:
    """Инспектор для анализа DPI-поведения и классификации сбросов"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Конфигурация из переменных окружения
        self.enabled = os.environ.get('DPI_SANDBOX_INSPECTION', 'true').lower() == 'true'
        self.matrix_export_path = os.environ.get('MATRIX_EXPORT_PATH', '/app/logs/matrix_report.json')
        
        # Анализ соединений
        self.active_connections: Dict[str, ConnectionAnalysis] = {}
        self.completed_connections: Dict[str, ConnectionAnalysis] = {}
        
        # TLS Record типы
        self.TLS_RECORD_TYPES = {
            0x14: "change_cipher_spec",
            0x15: "alert", 
            0x16: "handshake",
            0x17: "application_data",
            0x18: "heartbeat"
        }
        
        # TLS версии
        self.TLS_VERSIONS = {
            0x0301: "TLS 1.0",
            0x0302: "TLS 1.1", 
            0x0303: "TLS 1.2",
            0x0304: "TLS 1.3"
        }
        
        self.logger.info(f"DpiSandboxInspector initialized: enabled={self.enabled}")
    
    def start_connection_analysis(self, domain: str) -> str:
        """
        Начать анализ нового соединения
        
        Args:
            domain: Целевой домен
            
        Returns:
            ID соединения
        """
        if not self.enabled:
            return f"{domain}_disabled"
        
        import time
        connection_id = f"{domain}_{int(time.time() * 1000)}"
        
        analysis = ConnectionAnalysis(
            domain=domain,
            server_hello_received=False,
            drop_reason=ConnectionDropReason.UNKNOWN,
            bytes_from_server=0,
            timestamp=time.time()
        )
        
        self.active_connections[connection_id] = analysis
        self.logger.info(f"[INSPECTOR] Started analysis for {domain} (ID: {connection_id})")
        
        return connection_id
    
    def analyze_server_response(self, connection_id: str, data: bytes) -> bool:
        """
        Анализ ответа от сервера
        
        Args:
            connection_id: ID соединения
            data: Байты от сервера
            
        Returns:
            True если это TLS Server Hello
        """
        if not self.enabled or connection_id not in self.active_connections:
            return False
        
        analysis = self.active_connections[connection_id]
        analysis.bytes_from_server += len(data)
        
        # Проверяем TLS Record заголовок (первые 5 байт)
        if len(data) >= 5:
            record_type = data[0]
            version_bytes = data[1:3]
            version_int = int.from_bytes(version_bytes, byteorder='big')
            
            # Проверяем, это ли TLS Handshake record
            if record_type == 0x16 and version_int in self.TLS_VERSIONS:
                analysis.server_hello_received = True
                analysis.tls_version = self.TLS_VERSIONS[version_int]
                
                self.logger.info(f"[INSPECTOR] Server Hello signature verified for {analysis.domain}. "
                               f"TLS {analysis.tls_version}, Connection status: Clean")
                return True
        
        return False
    
    def finalize_connection_analysis(self, connection_id: str, error_type: Optional[str] = None) -> ConnectionAnalysis:
        """
        Завершить анализ соединения и классифицировать сброс
        
        Args:
            connection_id: ID соединения
            error_type: Тип ошибки если есть
            
        Returns:
            Результат анализа
        """
        if not self.enabled or connection_id not in self.active_connections:
            # Возвращаем заглушку если инспектор отключен
            return ConnectionAnalysis(
                domain="unknown",
                server_hello_received=True,
                drop_reason=ConnectionDropReason.CLEAN,
                bytes_from_server=0
            )
        
        analysis = self.active_connections[connection_id]
        
        # Классификация причины сброса
        if error_type:
            if not analysis.server_hello_received:
                analysis.drop_reason = ConnectionDropReason.DPI_REQUEST_DROP
                self.logger.info(f"[INSPECTOR] {analysis.domain}: DPI Request Drop detected "
                               f"(no Server Hello, error: {error_type})")
            else:
                if "timeout" in error_type.lower() or "connection" in error_type.lower():
                    analysis.drop_reason = ConnectionDropReason.DPI_DEEP_INSPECT_DROP
                    self.logger.info(f"[INSPECTOR] {analysis.domain}: DPI Deep Inspect Drop detected "
                                   f"(Server Hello received, then error: {error_type})")
                else:
                    analysis.drop_reason = ConnectionDropReason.SERVER_ERROR
                    self.logger.info(f"[INSPECTOR] {analysis.domain}: Server Error detected "
                                   f"(Server Hello received, error: {error_type})")
        else:
            # Соединение завершилось успешно
            analysis.drop_reason = ConnectionDropReason.CLEAN
            self.logger.info(f"[INSPECTOR] {analysis.domain}: Clean connection completed")
        
        # Перемещаем в завершенные соединения
        self.completed_connections[connection_id] = analysis
        del self.active_connections[connection_id]
        
        return analysis
    
    def get_drop_statistics(self) -> Dict[str, int]:
        """
        Получить статистику по причинам сбросов
        
        Returns:
            Словарь со статистикой
        """
        stats = {reason.value: 0 for reason in ConnectionDropReason}
        
        for analysis in self.completed_connections.values():
            stats[analysis.drop_reason.value] += 1
        
        return stats
    
    async def export_matrix_report(self, orchestrator=None) -> bool:
        """
        Экспорт матрицы стратегий в JSON файл
        
        Args:
            orchestrator: Опциональная ссылка на оркестратор для получения mutation_history
        
        Returns:
            True если экспорт успешен
        """
        if not self.enabled:
            return True
        
        try:
            # Группируем по доменам
            domain_data: Dict[str, Dict[str, Any]] = {}
            
            # Получаем snapshot из оркестратора для mutation_history
            orchestrator_snapshot = None
            if orchestrator:
                orchestrator_snapshot = await orchestrator.get_snapshot()
            
            # Сначала добавляем домены из оркестратора (даже если соединение не завершено)
            if orchestrator_snapshot and "domains" in orchestrator_snapshot:
                for domain, domain_info in orchestrator_snapshot["domains"].items():
                    domain_data[domain] = {
                        "status": domain_info.get("status", "UNKNOWN"),
                        "successful_pipeline": domain_info.get("active_pipeline", []),
                        "failures_count": domain_info.get("failures", 0),
                        "last_drop_reason": domain_info.get("last_drop_reason", "unknown"),
                        "history_of_failures": domain_info.get("mutation_history", []),
                        "total_connections": 0,
                        "successful_connections": 0,
                        "failed_connections": 0,
                        "bytes_from_server": 0,
                        "tls_version": None,
                        "last_analysis": 0
                    }
            
            # Затем обновляем данными из завершенных соединений
            for analysis in self.completed_connections.values():
                domain = analysis.domain
                
                if domain not in domain_data:
                    domain_data[domain] = {
                        "status": "UNKNOWN",
                        "server_hello_received": False,
                        "drop_reason": "unknown",
                        "total_connections": 0,
                        "successful_connections": 0,
                        "failed_connections": 0,
                        "bytes_from_server": 0,
                        "tls_version": None,
                        "last_analysis": analysis.timestamp,
                        "history_of_failures": []
                    }
                
                domain_entry = domain_data[domain]
                domain_entry["total_connections"] += 1
                domain_entry["bytes_from_server"] += analysis.bytes_from_server
                domain_entry["server_hello_received"] = domain_entry["server_hello_received"] or analysis.server_hello_received
                
                if analysis.tls_version:
                    domain_entry["tls_version"] = analysis.tls_version
                
                # Определяем статус домена
                if analysis.drop_reason == ConnectionDropReason.CLEAN:
                    domain_entry["successful_connections"] += 1
                    domain_entry["status"] = "STABLE"
                else:
                    domain_entry["failed_connections"] += 1
                    if domain_entry["status"] == "STABLE":
                        domain_entry["status"] = "UNSTABLE"
                
                # Сохраняем последнюю причину сброса
                if analysis.drop_reason != ConnectionDropReason.CLEAN:
                    domain_entry["drop_reason"] = analysis.drop_reason.value
                    domain_entry["last_analysis"] = analysis.timestamp
            
            # Добавляем общую статистику
            matrix_report = {
                "export_timestamp": analysis.timestamp if self.completed_connections else 0,
                "total_domains": len(domain_data),
                "drop_statistics": self.get_drop_statistics(),
                "domains": domain_data
            }
            
            # Асинхронная запись в файл через asyncio.to_thread
            def write_json_file():
                with open(self.matrix_export_path, 'w') as f:
                    json.dump(matrix_report, f, indent=2, default=str)
            
            await asyncio.to_thread(write_json_file)
            
            self.logger.info(f"[INSPECTOR] Matrix report exported to {self.matrix_export_path}")
            self.logger.info(f"[INSPECTOR] Exported {len(domain_data)} domains, "
                           f"total connections: {sum(d['total_connections'] for d in domain_data.values())}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[INSPECTOR] Failed to export matrix report: {e}")
            return False
    
    def is_server_hello(self, data: bytes) -> bool:
        """
        Быстрая проверка, является ли пакет TLS Server Hello
        
        Args:
            data: Байты для проверки
            
        Returns:
            True если это TLS Server Hello
        """
        if len(data) < 5:
            return False
        
        # TLS Record: Type (1) + Version (2) + Length (2)
        record_type = data[0]
        version_bytes = data[1:3]
        version_int = int.from_bytes(version_bytes, byteorder='big')
        
        return (record_type == 0x16 and 
                version_int in self.TLS_VERSIONS and
                len(data) >= 6)  # Минимальный размер для Handshake message
    
    def extract_sni_from_client_hello(self, data: bytes) -> Optional[str]:
        """
        Извлечение SNI из Client Hello (для будущего использования)
        
        Args:
            data: Client Hello байты
            
        Returns:
            SNI домен или None
        """
        # Упрощенная реализация - ищем SNI в расширениях
        # В реальной реализации нужен полный парсинг TLS Handshake
        try:
            data_str = data.decode('utf-8', errors='ignore')
            
            # Ищем тип расширения SNI (0x0000)
            if b'\x00\x00' in data:
                # Находим начало расширений
                handshake_end = data.find(b'\x00\x00')
                if handshake_end > 0:
                    # Упрощенный поиск домена в расширениях
                    remaining = data[handshake_end:]
                    # Ищем строку похожую на домен
                    for i in range(len(remaining) - 3):
                        if remaining[i:i+2] == b'\x00' and remaining[i+3] in range(ord('a'), ord('z')):
                            # Потенциальное начало имени домена
                            domain_end = remaining.find(b'\x00', i + 3)
                            if domain_end > i + 3:
                                domain_bytes = remaining[i + 3:domain_end]
                                try:
                                    return domain_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    continue
        except Exception:
            pass
        
        return None
