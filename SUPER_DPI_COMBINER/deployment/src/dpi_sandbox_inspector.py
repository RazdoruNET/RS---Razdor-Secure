#!/usr/bin/env python3
"""
DPI Sandbox Inspector - Анализ TLS-пакетов для классификации сбросов соединений
"""

import os
import asyncio
import json
from datetime import datetime
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
    
    def __init__(self, logger=None, export_path: str = "/app/logs/matrix_report.json"):
        self.logger = logger or __import__('logging').getLogger(self.__class__.__name__)
        self.export_path = os.getenv("MATRIX_EXPORT_PATH", export_path)
        
        # Инициализируем базовые счетчики дропов ядра
        self.drop_stats = {
            "unknown": 0,
            "DPI Request Drop": 0,
            "DPI Deep Inspect Drop": 0,
            "Server Error": 0,
            "Clean": 0
        }
        
        # Конфигурация из переменных окружения
        self.enabled = os.environ.get('DPI_SANDBOX_INSPECTION', 'true').lower() == 'true'
        
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
    
    def _normalize_domain(self, domain: str) -> str:
        if not domain:
            return "unknown_init"
        return str(domain).strip().lower()

    async def export_matrix_report(self, orchestrator):
        """
        orchestrator: Активный инстанс SmartFailoverOrchestrator из Event Loop
        """
        try:
            if not orchestrator:
                self.logger.error("[INSPECTOR ERROR] Передан пустой объект оркестратора.")
                return

            # Извлекаем честный thread-safe снимок памяти оркестратора
            snapshot = await orchestrator.get_snapshot()
            domains_memory = snapshot.get("domains", {})

            # Формируем структуру отчета
            report_data = {
                "export_timestamp": datetime.utcnow().timestamp(),
                "total_domains": len(domains_memory),
                "drop_statistics": self.drop_stats.copy(),
                "domains": {}
            }

            total_connections_tracked = 0

            # Перенос данных без потерь и фильтрации
            for domain_key, strategy_info in domains_memory.items():
                norm_key = self._normalize_domain(domain_key)
                
                # Обновляем внутреннюю статистику дропов инспектора на основе причин сбоев
                last_reason = strategy_info.get("last_drop_reason", "N/A")
                if last_reason == "Connection timeout":
                    self.drop_stats["DPI Request Drop"] += 1
                elif last_reason == "DPI Request Drop":
                    self.drop_stats["DPI Deep Inspect Drop"] += 1
                else:
                    self.drop_stats["unknown"] += 1

                # Сборка кадра домена
                report_data["domains"][norm_key] = {
                    "status": strategy_info.get("status", "MUTATING"),
                    "successful_pipeline": strategy_info.get("successful_pipeline", []),
                    "failures_count": strategy_info.get("failures_count", 0),
                    "last_drop_reason": last_reason,
                    # Гарантируем экспорт накопленного массива истории мутаций
                    "history_of_failures": strategy_info.get("history_of_failures", []),
                    "total_connections": 1 + strategy_info.get("failures_count", 0),
                    "successful_connections": 0,
                    "failed_connections": strategy_info.get("failures_count", 0),
                    "bytes_from_server": 0,
                    "tls_version": None,
                    "last_analysis": 0
                }
                
                total_connections_tracked += report_data["domains"][norm_key]["total_connections"]

            report_data["drop_statistics"] = self.drop_stats.copy()
            
            # Директория выгрузки
            dir_name = os.path.dirname(self.export_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            # Потокобезопасная неблокирующая запись на диск
            def sync_write():
                with open(self.export_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)

            await asyncio.to_thread(sync_write)
            
            self.logger.info(f"[INSPECTOR] Matrix report successfully exported to {self.export_path}")
            self.logger.info(f"[INSPECTOR] Exported {len(report_data['domains'])} domains, total connections: {total_connections_tracked}")

        except Exception as e:
            self.logger.error(f"[INSPECTOR CRITICAL ERROR] Сбой экспорта матрицы на диск: {e}")
    
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
