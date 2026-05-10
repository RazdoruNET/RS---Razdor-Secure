#!/usr/bin/env python3
"""
Simple Test: Truth-Based Metrics Engine - TASK 8.7
Тест без внешних сетевых соединений
"""

import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth import (
    get_truth_metrics_engine,
    get_io_monitor,
    ValidationLevel
)
from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse, BypassTechnique
from core.execution_trace import ExecutionTrace

class MockSimulationPipeline(BasePipeline):
    """Мок пайплайн с симуляцией (без реальных I/O)"""
    
    def __init__(self):
        super().__init__(
            name="DNS_Tunnel_Simulation",
            technique=BypassTechnique.DOMAIN_FRONTING,
            priority=2
        )
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение без реальных I/O (симуляция)"""
        # Имитируем работу без реальных сетевых операций
        await asyncio.sleep(0.1)  # Имитация задержки
        
        # Возвращаем фейковый успешный ответ
        return BypassResponse(
            success=True,
            latency=0.1,
            status_code=200,
            data=b'{"simulated": true, "response": "fake data"}'
        )
    
    def initialize(self, config):
        self._initialized = True
        return True
    
    def cleanup(self):
        return True

class MockFailedPipeline(BasePipeline):
    """Мок пайплайн который всегда падает"""
    
    def __init__(self):
        super().__init__(
            name="Failed_Pipeline",
            technique=BypassTechnique.SPOOF_DPI,
            priority=3
        )
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Всегда падает"""
        await asyncio.sleep(0.05)
        raise RuntimeError("Simulated pipeline failure")
    
    def initialize(self, config):
        self._initialized = True
        return True
    
    def cleanup(self):
        return True

async def test_truth_metrics_simple():
    """Простой тест truth-based metrics без внешних соединений"""
    print("🧬 Simple Truth-Based Metrics Test")
    print("=" * 50)
    
    # Получаем движок метрик
    metrics_engine = get_truth_metrics_engine()
    print("✅ Truth metrics engine initialized")
    
    # Создаем мок пайплайны
    simulation_pipeline = MockSimulationPipeline()
    failed_pipeline = MockFailedPipeline()
    
    # Инициализируем пайплайны
    simulation_pipeline.initialize({})
    failed_pipeline.initialize({})
    
    print("\n🚀 Starting pipeline tests...")
    
    # Создаем тестовый запрос
    test_request = BypassRequest(
        host="example.com",
        port=80,
        method="GET",
        data=b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    )
    
    # Тестируем симуляцию
    print("\n--- Testing Simulation Pipeline ---")
    for i in range(3):
        try:
            response = await simulation_pipeline.execute(test_request)
            print(f"✅ Simulation {i+1}: {response.success} ({response.latency:.3f}s)")
            
            # Создаем execution trace для симуляции
            trace = ExecutionTrace(f"simulation_test_{i}")
            trace.start_execution()
            trace.end_execution(response.success, "completed")
            
            # Записываем в metrics engine
            await metrics_engine.record_pipeline_run(
                pipeline_name="DNS_Tunnel_Simulation",
                execution_trace=trace,
                response_success=response.success
            )
            
        except Exception as e:
            print(f"❌ Simulation {i+1}: Failed - {str(e)}")
        
        await asyncio.sleep(0.05)
    
    # Тестируем падения
    print("\n--- Testing Failed Pipeline ---")
    for i in range(2):
        try:
            response = await failed_pipeline.execute(test_request)
            print(f"✅ Failed {i+1}: {response.success}")
        except Exception as e:
            print(f"❌ Failed {i+1}: Failed - {str(e)}")
            
            # Создаем execution trace для падения
            trace = ExecutionTrace(f"failed_test_{i}")
            trace.start_execution()
            trace.end_execution(False, "failed")
            
            # Записываем в metrics engine
            await metrics_engine.record_pipeline_run(
                pipeline_name="Failed_Pipeline",
                execution_trace=trace,
                response_success=False
            )
        
        await asyncio.sleep(0.05)
    
    # Получаем финальные метрики
    print("\n📊 Final Metrics:")
    print("-" * 30)
    
    system_metrics = metrics_engine.get_system_metrics()
    print(f"Total Runs: {system_metrics.total_runs}")
    print(f"Network Verified: {system_metrics.network_verified_runs}")
    print(f"Simulation Detected: {system_metrics.simulated_runs}")
    print(f"Failed: {system_metrics.failed_runs}")
    print(f"REALITY_SCORE: {system_metrics.reality_score:.1f}%")
    print(f"SIMULATION_RATIO: {system_metrics.simulation_ratio:.3f}")
    
    # Метрики по пайплайнам
    print("\n📈 Pipeline Breakdown:")
    print("-" * 30)
    
    pipeline_metrics = metrics_engine.get_all_pipeline_metrics()
    for name, stats in pipeline_metrics.items():
        if stats['total_runs'] > 0:
            print(f"{name}:")
            print(f"  Executed: {stats['total_runs']}")
            print(f"  Network Verified: {stats['network_verified']}")
            print(f"  Simulation Detected: {stats['simulation_detected']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Reality Score: {stats['reality_score']:.1f}%")
            print(f"  Simulation Ratio: {stats['simulation_ratio']:.3f}")
            print()
    
    # Генерируем SYSTEM_TRUTH_REPORT.md
    print("📝 Generating SYSTEM_TRUTH_REPORT.md...")
    try:
        report_path = metrics_engine.generate_truth_report()
        print(f"✅ Report generated: {report_path}")
        
        # Показываем краткое содержимое отчета
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        print("\n📄 Report Preview:")
        print("=" * 50)
        lines = report_content.split('\n')
        for line in lines[:20]:  # Показываем первые 20 строк
            print(line)
        if len(lines) > 20:
            print("...")
            print(f"(Total {len(lines)} lines in report)")
        
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")
    
    # Показываем последние запуски
    print("\n🕐 Recent Runs:")
    print("-" * 30)
    
    recent_runs = metrics_engine.get_recent_runs(5)
    for run in reversed(recent_runs):
        status_emoji = {
            "network_verified": "✅",
            "simulation_detected": "🎭", 
            "failed": "❌",
            "unknown": "❓"
        }.get(run.status.value, "❓")
        
        print(f"{status_emoji} {run.pipeline_name} - {run.status.value} ({run.execution_time:.3f}s)")
        if run.simulation_result and run.simulation_result.reason:
            print(f"    Reason: {run.simulation_result.reason}")
    
    print("\n🎉 Simple test completed!")
    print("\nKey Results:")
    print(f"- REALITY_SCORE: {system_metrics.reality_score:.1f}%")
    print(f"- SIMULATION_RATIO: {system_metrics.simulation_ratio:.3f}")
    print(f"- SYSTEM_TRUTH_REPORT.md generated")
    
    # Проверяем формулы
    print("\n🧮 Formula Verification:")
    print("-" * 30)
    if system_metrics.total_runs > 0:
        expected_reality_score = (system_metrics.network_verified_runs / system_metrics.total_runs) * 100
        expected_simulation_ratio = system_metrics.simulated_runs / system_metrics.total_runs
        
        print(f"Expected REALITY_SCORE: {expected_reality_score:.1f}%")
        print(f"Actual REALITY_SCORE: {system_metrics.reality_score:.1f}%")
        print(f"Expected SIMULATION_RATIO: {expected_simulation_ratio:.3f}")
        print(f"Actual SIMULATION_RATIO: {system_metrics.simulation_ratio:.3f}")
        
        if abs(expected_reality_score - system_metrics.reality_score) < 0.01:
            print("✅ REALITY_SCORE formula correct")
        else:
            print("❌ REALITY_SCORE formula mismatch")
            
        if abs(expected_simulation_ratio - system_metrics.simulation_ratio) < 0.001:
            print("✅ SIMULATION_RATIO formula correct")
        else:
            print("❌ SIMULATION_RATIO formula mismatch")
    else:
        print("No runs to verify formulas")

if __name__ == "__main__":
    asyncio.run(test_truth_metrics_simple())
