#!/usr/bin/env python3
"""
Truth-Based Metrics Engine - TASK 8.7
Заменяет "фейковую готовность %" на реальную метрику

REALITY_SCORE = (network_verified_runs / total_runs) * 100
SIMULATION_RATIO = simulated_runs / total_runs
"""

import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, Counter

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import get_logger
from core.network_reality_verifier import NetworkRealityVerifier, VerificationResult
from core.simulation_detector import SimulationDetector, SimulationDetectionResult
from core.execution_trace import ExecutionTrace

logger = get_logger(__name__)

class RunStatus(Enum):
    """Статусы выполнения пайплайна"""
    NETWORK_VERIFIED = "network_verified"
    SIMULATION_DETECTED = "simulation_detected"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class PipelineRunMetrics:
    """Метрики выполнения пайплайна"""
    pipeline_name: str
    run_id: str
    timestamp: float
    status: RunStatus
    execution_time: float
    network_verified: bool = False
    simulation_detected: bool = False
    verification_result: Optional[VerificationResult] = None
    simulation_result: Optional[SimulationDetectionResult] = None
    execution_trace: Optional[ExecutionTrace] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemTruthMetrics:
    """Метрики правды системы"""
    total_runs: int = 0
    network_verified_runs: int = 0
    simulated_runs: int = 0
    failed_runs: int = 0
    reality_score: float = 0.0
    simulation_ratio: float = 0.0
    
    # Метрики по пайплайнам
    pipeline_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Временные метрики
    last_update: float = field(default_factory=time.time)
    update_interval: float = 5.0  # Обновлять каждые 5 секунд

class TruthMetricsEngine:
    """
    Движок метрик правды системы
    
    Отслеживает реальные выполнения против симуляций
    и вычисляет REALITY_SCORE и SIMULATION_RATIO
    """
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.run_history: List[PipelineRunMetrics] = []
        self.lock = threading.Lock()
        self.logger = logger
        
        # Верификатор и детектор
        self.network_verifier = NetworkRealityVerifier()
        self.simulation_detector = SimulationDetector()
        
        # Системные метрики
        self.system_metrics = SystemTruthMetrics()
        
        # Статистика по пайплайнам
        self.pipeline_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_runs': 0,
            'network_verified': 0,
            'simulation_detected': 0,
            'failed': 0,
            'reality_score': 0.0,
            'simulation_ratio': 0.0,
            'last_run': 0.0
        })
        
        self.logger.info("🧬 Truth Metrics Engine initialized")
    
    async def record_pipeline_run(
        self,
        pipeline_name: str,
        execution_trace: Optional[ExecutionTrace] = None,
        response_success: bool = False,
        **metadata
    ) -> str:
        """
        Записать запуск пайплайна и проанализировать его правдивость
        
        Args:
            pipeline_name: Имя пайплайна
            execution_trace: Trace выполнения
            response_success: Успешность ответа
            **metadata: Дополнительные метаданные
            
        Returns:
            str: ID запуска
        """
        run_id = f"{pipeline_name}_{int(time.time() * 1000000)}"
        start_time = time.time()
        
        try:
            self.logger.info(f"🔍 Анализ запуска пайплайна: {pipeline_name}")
            
            # 1. Детекция симуляции
            simulation_detected = False
            simulation_result = None
            if execution_trace:
                simulation_result = self.simulation_detector.analyze_pipeline_execution(
                    execution_trace, response_success, pipeline_name
                )
                simulation_detected = simulation_result.simulation_detected
                
            # 2. Верификация сети (если не симуляция)
            network_verified = False
            verification_result = None
            if not simulation_detected and execution_trace:
                # Проверяем наличие сетевых операций для верификации
                if self._has_network_operations(execution_trace):
                    verification_result = await self._verify_network_operations(execution_trace)
                    network_verified = verification_result.network_verified if verification_result else False
            
            # 3. Определение статуса
            if network_verified:
                status = RunStatus.NETWORK_VERIFIED
            elif simulation_detected:
                status = RunStatus.SIMULATION_DETECTED
            elif response_success is False:
                status = RunStatus.FAILED
            else:
                status = RunStatus.UNKNOWN
            
            # 4. Создание метрик запуска
            run_metrics = PipelineRunMetrics(
                pipeline_name=pipeline_name,
                run_id=run_id,
                timestamp=start_time,
                status=status,
                execution_time=time.time() - start_time,
                network_verified=network_verified,
                simulation_detected=simulation_detected,
                verification_result=verification_result,
                simulation_result=simulation_result,
                execution_trace=execution_trace,
                metadata=metadata
            )
            
            # 5. Сохранение в историю
            with self.lock:
                self.run_history.append(run_metrics)
                if len(self.run_history) > self.max_history:
                    self.run_history.pop(0)
                
                # Обновление статистики пайплайна
                self._update_pipeline_stats(pipeline_name, status)
                
                # Пересчет системных метрик
                self._recalculate_system_metrics()
            
            self.logger.info(f"✅ Запуск {run_id} записан: {status.value}")
            return run_id
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка записи запуска пайплайна: {e}")
            # Записываем как FAILED в случае ошибки
            failed_metrics = PipelineRunMetrics(
                pipeline_name=pipeline_name,
                run_id=run_id,
                timestamp=start_time,
                status=RunStatus.FAILED,
                execution_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
            
            with self.lock:
                self.run_history.append(failed_metrics)
                self._update_pipeline_stats(pipeline_name, RunStatus.FAILED)
                self._recalculate_system_metrics()
            
            return run_id
    
    async def _verify_network_operations(self, execution_trace: ExecutionTrace) -> Optional[VerificationResult]:
        """Верифицировать сетевые операции из execution trace"""
        try:
            # Ищем сетевые операции в trace
            network_events = execution_trace.network_events
            if not network_events:
                return None
            
            # Создаем тестовую операцию для верификации
            # Используем первую сетевую операцию как основу
            for event in network_events:
                # NetworkEvent имеет host и port атрибуты
                if hasattr(event, 'host') and hasattr(event, 'port'):
                    from core.network_reality_verifier import NetworkOperation
                    operation = NetworkOperation(
                        operation_type="connect",
                        claimed_success=True,
                        timestamp=event.timestamp,
                        target_host=event.host,
                        target_port=event.port
                    )
                    
                    result = await self.network_verifier.verify_network_operation(operation)
                    return result
            
            return None
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка верификации сети: {e}")
            return None
    
    def _has_network_operations(self, execution_trace: ExecutionTrace) -> bool:
        """Проверить наличие сетевых операций в execution trace"""
        return len(execution_trace.network_events) > 0
    
    def _update_pipeline_stats(self, pipeline_name: str, status: RunStatus):
        """Обновить статистику по пайплайну"""
        stats = self.pipeline_stats[pipeline_name]
        stats['total_runs'] += 1
        stats['last_run'] = time.time()
        
        if status == RunStatus.NETWORK_VERIFIED:
            stats['network_verified'] += 1
        elif status == RunStatus.SIMULATION_DETECTED:
            stats['simulation_detected'] += 1
        elif status == RunStatus.FAILED:
            stats['failed'] += 1
        
        # Пересчет метрик пайплайна
        if stats['total_runs'] > 0:
            stats['reality_score'] = (stats['network_verified'] / stats['total_runs']) * 100
            stats['simulation_ratio'] = stats['simulation_detected'] / stats['total_runs']
    
    def _recalculate_system_metrics(self):
        """Пересчитать системные метрики"""
        total = len(self.run_history)
        if total == 0:
            self.system_metrics = SystemTruthMetrics()
            return
        
        network_verified = sum(1 for r in self.run_history if r.status == RunStatus.NETWORK_VERIFIED)
        simulated = sum(1 for r in self.run_history if r.status == RunStatus.SIMULATION_DETECTED)
        failed = sum(1 for r in self.run_history if r.status == RunStatus.FAILED)
        
        self.system_metrics = SystemTruthMetrics(
            total_runs=total,
            network_verified_runs=network_verified,
            simulated_runs=simulated,
            failed_runs=failed,
            reality_score=(network_verified / total) * 100,
            simulation_ratio=simulated / total,
            pipeline_metrics=dict(self.pipeline_stats)
        )
    
    def get_system_metrics(self) -> SystemTruthMetrics:
        """Получить текущие системные метрики"""
        with self.lock:
            return self.system_metrics
    
    def get_pipeline_metrics(self, pipeline_name: str) -> Dict[str, Any]:
        """Получить метрики конкретного пайплайна"""
        with self.lock:
            return dict(self.pipeline_stats.get(pipeline_name, {
                'total_runs': 0,
                'network_verified': 0,
                'simulation_detected': 0,
                'failed': 0,
                'reality_score': 0.0,
                'simulation_ratio': 0.0,
                'last_run': 0.0
            }))
    
    def get_all_pipeline_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Получить метрики всех пайплайнов"""
        with self.lock:
            return dict(self.pipeline_stats)
    
    def get_recent_runs(self, count: int = 100) -> List[PipelineRunMetrics]:
        """Получить последние запуски"""
        with self.lock:
            return self.run_history[-count:]
    
    def generate_truth_report(self) -> str:
        """
        Сгенерировать SYSTEM_TRUTH_REPORT.md
        
        Returns:
            str: Путь к сгенерированному отчету
        """
        try:
            report_path = os.path.join(os.path.dirname(__file__), '..', '..', 'SYSTEM_TRUTH_REPORT.md')
            
            with self.lock:
                metrics = self.system_metrics
                pipeline_stats = dict(self.pipeline_stats)
            
            # Генерация содержимого отчета
            report_content = self._generate_report_content(metrics, pipeline_stats)
            
            # Запись в файл
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"📊 SYSTEM_TRUTH_REPORT.md сгенерирован: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации отчета: {e}")
            raise
    
    def _generate_report_content(self, metrics: SystemTruthMetrics, pipeline_stats: Dict[str, Dict[str, Any]]) -> str:
        """Сгенерировать содержимое отчета"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        
        content = f"""# System Truth Report

Generated: {timestamp}

## 🎯 System Overview

**REALITY_SCORE**: {metrics.reality_score:.1f}%
**SIMULATION_RATIO**: {metrics.simulation_ratio:.3f}

### Execution Statistics
- **Total Runs**: {metrics.total_runs}
- **Network Verified**: {metrics.network_verified_runs}
- **Simulation Detected**: {metrics.simulated_runs}
- **Failed**: {metrics.failed_runs}

### Success Rate Real
{(metrics.network_verified_runs / metrics.total_runs * 100) if metrics.total_runs > 0 else 0:.1f}%

---

"""
        
        # Добавляем статистику по пайплайнам
        if pipeline_stats:
            content += "## 📊 Pipeline Breakdown\n\n"
            
            # Сортируем пайплайны по общему количеству запусков
            sorted_pipelines = sorted(pipeline_stats.items(), key=lambda x: x[1]['total_runs'], reverse=True)
            
            for pipeline_name, stats in sorted_pipelines:
                if stats['total_runs'] > 0:
                    content += f"""### {pipeline_name}

**Executed**: {stats['total_runs']}
**Network Verified**: {stats['network_verified']}
**Simulation Detected**: {stats['simulation_detected']}
**Reality Score**: {stats['reality_score']:.1f}%
**Simulation Ratio**: {stats['simulation_ratio']:.3f}

"""
        
        # Добавляем последние запуски
        recent_runs = self.get_recent_runs(10)
        if recent_runs:
            content += "## 🕐 Recent Runs (Last 10)\n\n"
            
            for run in reversed(recent_runs):
                status_emoji = {
                    RunStatus.NETWORK_VERIFIED: "✅",
                    RunStatus.SIMULATION_DETECTED: "🎭",
                    RunStatus.FAILED: "❌",
                    RunStatus.UNKNOWN: "❓"
                }.get(run.status, "❓")
                
                content += f"{status_emoji} **{run.pipeline_name}** - {run.status.value} ({run.execution_time:.3f}s)\n"
                
                if run.simulation_result and run.simulation_result.reason:
                    content += f"   Reason: {run.simulation_result.reason}\n"
                
                content += "\n"
        
        content += """
---

## 🧬 Metrics Formula

```
REALITY_SCORE = (network_verified_runs / total_runs) * 100
SIMULATION_RATIO = simulated_runs / total_runs
```

## 📝 Notes

- **Network Verified**: Real network operations confirmed by OS-level verification
- **Simulation Detected**: Pipeline execution patterns indicate simulation/mock behavior  
- **Failed**: Pipeline execution failed or returned error
- **Reality Score**: Percentage of runs with verified real network operations
- **Simulation Ratio**: Ratio of simulated runs to total runs

*This report is generated automatically by the Truth-Based Metrics Engine*
"""
        
        return content
    
    def clear_history(self):
        """Очистить историю запусков"""
        with self.lock:
            self.run_history.clear()
            self.pipeline_stats.clear()
            self._recalculate_system_metrics()
        
        self.logger.info("🧹 История метрик очищена")

# Глобальный экземпляр движка метрик
_truth_metrics_engine = TruthMetricsEngine()

def get_truth_metrics_engine() -> TruthMetricsEngine:
    """Получить экземпляр движка метрик правды"""
    return _truth_metrics_engine
