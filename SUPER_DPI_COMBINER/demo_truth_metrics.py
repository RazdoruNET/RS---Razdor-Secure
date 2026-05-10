#!/usr/bin/env python3
"""
Demo: Truth-Based Metrics Engine - TASK 8.7
Демонстрация работы REALITY_SCORE и SIMULATION_RATIO
"""

import asyncio
import sys
import os
import time
import random

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth import (
    enable_instrumentation,
    get_truth_metrics_engine,
    get_io_monitor,
    execute_with_truth,
    ValidationLevel
)
from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse, BypassTechnique
from core.execution_trace import ExecutionTrace

class MockRealPipeline(BasePipeline):
    """Мок пайплайн с реальными сетевыми операциями"""
    
    def __init__(self):
        super().__init__(
            name="HTTPFragmentation",
            technique=BypassTechnique.PROTOCOL_OBFUSCATION,
            priority=1
        )
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальными I/O операциями"""
        import socket
        
        try:
            # Создаем реальный сокет и подключаемся
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(("httpbin.org", 80))
            
            # Отправляем реальный HTTP запрос
            http_request = f"GET /get HTTP/1.1\r\nHost: httpbin.org\r\n\r\n"
            bytes_sent = sock.send(http_request.encode())
            
            # Получаем ответ
            response_data = sock.recv(4096)
            sock.close()
            
            return BypassResponse(
                success=True,
                latency=0.5,
                status_code=200,
                data=response_data
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                latency=0.1,
                error=str(e)
            )
    
    def initialize(self, config):
        self._initialized = True
        return True
    
    def cleanup(self):
        return True

class MockSimulationPipeline(BasePipeline):
    """Мок пайплайн с симуляцией (без реальных I/O)"""
    
    def __init__(self):
        super().__init__(
            name="DNS_Tunnel",
            technique=BypassTechnique.DOMAIN_FRONTING,
            priority=2
        )
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение без реальных I/O (симуляция)"""
        # Имитируем работу без реальных сетевых операций
        await asyncio.sleep(0.2)  # Имитация задержки
        
        # Возвращаем фейковый успешный ответ
        return BypassResponse(
            success=True,
            latency=0.2,
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
        await asyncio.sleep(0.1)
        raise RuntimeError("Simulated pipeline failure")
    
    def initialize(self, config):
        self._initialized = True
        return True
    
    def cleanup(self):
        return True

async def demo_truth_metrics():
    """Демонстрация truth-based metrics"""
    print("🧬 Truth-Based Metrics Engine Demo")
    print("=" * 50)
    
    # Включаем инструментирование
    enable_instrumentation()
    print("✅ Instrumentation enabled")
    
    # Получаем движок метрик
    metrics_engine = get_truth_metrics_engine()
    print("✅ Truth metrics engine initialized")
    
    # Создаем мок пайплайны
    real_pipeline = MockRealPipeline()
    simulation_pipeline = MockSimulationPipeline()
    failed_pipeline = MockFailedPipeline()
    
    # Инициализируем пайплайны
    real_pipeline.initialize({})
    simulation_pipeline.initialize({})
    failed_pipeline.initialize({})
    
    print("\n🚀 Starting pipeline executions...")
    
    # Создаем тестовый запрос
    test_request = BypassRequest(
        host="example.com",
        port=80,
        method="GET",
        data=b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    )
    
    # Запускаем пайплайны в разном порядке для создания реальной статистики
    pipelines = [
        ("HTTPFragmentation", real_pipeline),
        ("DNS_Tunnel", simulation_pipeline), 
        ("Failed_Pipeline", failed_pipeline)
    ]
    
    # Выполняем каждый пайплайн несколько раз
    for i in range(5):
        print(f"\n--- Round {i+1} ---")
        
        # Перемешиваем порядок выполнения
        random.shuffle(pipelines)
        
        for name, pipeline in pipelines:
            print(f"🔄 Executing {name}...")
            
            try:
                response, trace = await execute_with_truth(
                    pipeline, 
                    test_request, 
                    validation_level=ValidationLevel.STRICT
                )
                
                print(f"   ✅ {name}: {response.success} ({trace.total_duration:.3f}s)")
                
            except Exception as e:
                print(f"   ❌ {name}: Failed - {str(e)}")
            
            # Небольшая задержка между выполнениями
            await asyncio.sleep(0.1)
    
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
        
        # Показываем содержимое отчета
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        print("\n📄 Report Content:")
        print("=" * 50)
        print(report_content[:1000] + "..." if len(report_content) > 1000 else report_content)
        
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
    
    print("\n🎉 Demo completed!")
    print("\nKey Results:")
    print(f"- REALITY_SCORE: {system_metrics.reality_score:.1f}%")
    print(f"- SIMULATION_RATIO: {system_metrics.simulation_ratio:.3f}")
    print(f"- SYSTEM_TRUTH_REPORT.md generated")

if __name__ == "__main__":
    asyncio.run(demo_truth_metrics())
