#!/usr/bin/env python3
"""
Truth Storage Layer - SQLite backend for execution results
Хранение результатов выполнения с верификацией
"""

import sqlite3
import json
import time
import threading
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class ExecutionResult:
    """Результат выполнения"""
    execution_id: str
    pipeline: str
    success: bool
    network_verified: bool
    simulation_flag: bool
    timestamp: float
    metadata: Dict[str, Any] = None
    io_operations_count: int = 0
    execution_duration: float = 0.0
    error_message: Optional[str] = None

class TruthStorage:
    """Хранилище результатов выполнения с SQLite backend"""
    
    def __init__(self, db_path: str = "truth_storage.db"):
        self.db_path = Path(db_path)
        self.lock = threading.Lock()
        self.logger = logging.getLogger("truth_storage")
        
        # Создаем базу данных и таблицы
        self._initialize_database()
    
    def _initialize_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_results (
                    execution_id TEXT PRIMARY KEY,
                    pipeline TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    network_verified BOOLEAN NOT NULL,
                    simulation_flag BOOLEAN NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    io_operations_count INTEGER DEFAULT 0,
                    execution_duration REAL DEFAULT 0.0,
                    error_message TEXT
                )
            """)
            
            # Индексы для быстрых запросов
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pipeline ON execution_results(pipeline)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON execution_results(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_success ON execution_results(success)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_network_verified ON execution_results(network_verified)
            """)
            
            conn.commit()
    
    def store_execution(self, result: ExecutionResult) -> bool:
        """Сохранить результат выполнения"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO execution_results 
                        (execution_id, pipeline, success, network_verified, simulation_flag,
                         timestamp, metadata, io_operations_count, execution_duration, error_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.execution_id,
                        result.pipeline,
                        result.success,
                        result.network_verified,
                        result.simulation_flag,
                        result.timestamp,
                        json.dumps(result.metadata) if result.metadata else None,
                        result.io_operations_count,
                        result.execution_duration,
                        result.error_message
                    ))
                    conn.commit()
                    
            self.logger.info(f"Stored execution result: {result.execution_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store execution result: {e}")
            return False
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """Получить результат выполнения по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM execution_results WHERE execution_id = ?
                """, (execution_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_execution_result(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get execution result: {e}")
            return None
    
    def get_executions_by_pipeline(self, pipeline: str, limit: int = 100) -> List[ExecutionResult]:
        """Получить результаты выполнения для конкретного pipeline"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM execution_results 
                    WHERE pipeline = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (pipeline, limit))
                
                return [self._row_to_execution_result(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get executions by pipeline: {e}")
            return []
    
    def get_recent_executions(self, limit: int = 50) -> List[ExecutionResult]:
        """Получить последние результаты выполнения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM execution_results 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                return [self._row_to_execution_result(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get recent executions: {e}")
            return []
    
    def get_successful_executions(self, pipeline: Optional[str] = None, limit: int = 100) -> List[ExecutionResult]:
        """Получить успешные выполнения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if pipeline:
                    cursor = conn.execute("""
                        SELECT * FROM execution_results 
                        WHERE success = 1 AND pipeline = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (pipeline, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM execution_results 
                        WHERE success = 1 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                
                return [self._row_to_execution_result(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get successful executions: {e}")
            return []
    
    def get_network_verified_executions(self, limit: int = 100) -> List[ExecutionResult]:
        """Получить выполнения с верифицированной сетью"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM execution_results 
                    WHERE network_verified = 1 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                return [self._row_to_execution_result(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get network verified executions: {e}")
            return []
    
    def get_simulation_executions(self, limit: int = 100) -> List[ExecutionResult]:
        """Получить выполнения в режиме симуляции"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM execution_results 
                    WHERE simulation_flag = 1 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                return [self._row_to_execution_result(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get simulation executions: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по выполнениям"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Общая статистика
                total_cursor = conn.execute("SELECT COUNT(*) FROM execution_results")
                total_executions = total_cursor.fetchone()[0]
                
                success_cursor = conn.execute("SELECT COUNT(*) FROM execution_results WHERE success = 1")
                successful_executions = success_cursor.fetchone()[0]
                
                network_verified_cursor = conn.execute("SELECT COUNT(*) FROM execution_results WHERE network_verified = 1")
                network_verified_executions = network_verified_cursor.fetchone()[0]
                
                simulation_cursor = conn.execute("SELECT COUNT(*) FROM execution_results WHERE simulation_flag = 1")
                simulation_executions = simulation_cursor.fetchone()[0]
                
                # Статистика по pipeline
                pipeline_cursor = conn.execute("""
                    SELECT pipeline, COUNT(*) as count, 
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                           AVG(execution_duration) as avg_duration
                    FROM execution_results 
                    GROUP BY pipeline
                    ORDER BY count DESC
                """)
                
                pipeline_stats = []
                for row in pipeline_cursor.fetchall():
                    pipeline_stats.append({
                        'pipeline': row[0],
                        'total': row[1],
                        'successes': row[2],
                        'success_rate': row[2] / row[1] if row[1] > 0 else 0,
                        'avg_duration': row[3] or 0
                    })
                
                return {
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
                    'network_verified_executions': network_verified_executions,
                    'network_verification_rate': network_verified_executions / total_executions if total_executions > 0 else 0,
                    'simulation_executions': simulation_executions,
                    'simulation_rate': simulation_executions / total_executions if total_executions > 0 else 0,
                    'pipeline_statistics': pipeline_stats
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def delete_execution(self, execution_id: str) -> bool:
        """Удалить результат выполнения"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM execution_results WHERE execution_id = ?
                    """, (execution_id,))
                    conn.commit()
                    
            self.logger.info(f"Deleted execution result: {execution_id}")
            return cursor.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete execution result: {e}")
            return False
    
    def cleanup_old_executions(self, days_old: int = 30) -> int:
        """Очистка старых выполнений"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM execution_results WHERE timestamp < ?
                    """, (cutoff_time,))
                    conn.commit()
                    
            deleted_count = cursor.rowcount
            self.logger.info(f"Cleaned up {deleted_count} old executions (older than {days_old} days)")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old executions: {e}")
            return 0
    
    def _row_to_execution_result(self, row: sqlite3.Row) -> ExecutionResult:
        """Преобразовать строку базы данных в ExecutionResult"""
        metadata = None
        if row['metadata']:
            try:
                metadata = json.loads(row['metadata'])
            except json.JSONDecodeError:
                pass
        
        return ExecutionResult(
            execution_id=row['execution_id'],
            pipeline=row['pipeline'],
            success=bool(row['success']),
            network_verified=bool(row['network_verified']),
            simulation_flag=bool(row['simulation_flag']),
            timestamp=row['timestamp'],
            metadata=metadata,
            io_operations_count=row['io_operations_count'],
            execution_duration=row['execution_duration'],
            error_message=row['error_message']
        )
    
    def export_to_jsonl(self, output_path: str, pipeline: Optional[str] = None) -> bool:
        """Экспортировать данные в JSONL формат"""
        try:
            executions = []
            if pipeline:
                executions = self.get_executions_by_pipeline(pipeline, limit=10000)
            else:
                executions = self.get_recent_executions(limit=10000)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for execution in executions:
                    json_line = json.dumps(asdict(execution), ensure_ascii=False)
                    f.write(json_line + '\n')
            
            self.logger.info(f"Exported {len(executions)} executions to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to JSONL: {e}")
            return False

# Глобальный экземпляр хранилища
_truth_storage = None

def get_truth_storage(db_path: str = "truth_storage.db") -> TruthStorage:
    """Получить экземпляр хранилища"""
    global _truth_storage
    if _truth_storage is None:
        _truth_storage = TruthStorage(db_path)
    return _truth_storage

def create_execution_result(execution_id: str, 
                          pipeline: str, 
                          success: bool, 
                          network_verified: bool, 
                          simulation_flag: bool,
                          metadata: Dict[str, Any] = None,
                          io_operations_count: int = 0,
                          execution_duration: float = 0.0,
                          error_message: Optional[str] = None) -> ExecutionResult:
    """Создать объект ExecutionResult"""
    return ExecutionResult(
        execution_id=execution_id,
        pipeline=pipeline,
        success=success,
        network_verified=network_verified,
        simulation_flag=simulation_flag,
        timestamp=time.time(),
        metadata=metadata,
        io_operations_count=io_operations_count,
        execution_duration=execution_duration,
        error_message=error_message
    )
