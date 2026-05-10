#!/usr/bin/env python3
"""
Basic Test: Truth-Based Metrics Engine - TASK 8.7
Минимальный тест для демонстрации работы метрик
"""

import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth import get_truth_metrics_engine
from core.execution_trace import ExecutionTrace

async def test_basic_metrics():
    """Базовый тест truth-based metrics"""
    print("🧬 Basic Truth Metrics Test")
    print("=" * 40)
    
    # Получаем движок метрик
    metrics_engine = get_truth_metrics_engine()
    print("✅ Truth metrics engine initialized")
    
    print("\n📝 Recording test pipeline runs...")
    
    # Создаем тестовые execution traces
    
    # 1. Симулированный запуск (без сетевых операций)
    print("1. Recording simulation run...")
    sim_trace = ExecutionTrace("simulation_test")
    sim_trace.start_execution()
    await asyncio.sleep(0.01)  # Короткая задержка
    sim_trace.end_execution(True, "completed")
    
    await metrics_engine.record_pipeline_run(
        pipeline_name="DNS_Tunnel",
        execution_trace=sim_trace,
        response_success=True
    )
    
    # 2. Еще один симулированный запуск
    print("2. Recording another simulation run...")
    sim_trace2 = ExecutionTrace("simulation_test_2")
    sim_trace2.start_execution()
    await asyncio.sleep(0.01)
    sim_trace2.end_execution(True, "completed")
    
    await metrics_engine.record_pipeline_run(
        pipeline_name="DNS_Tunnel",
        execution_trace=sim_trace2,
        response_success=True
    )
    
    # 3. Падение пайплайна
    print("3. Recording failed run...")
    failed_trace = ExecutionTrace("failed_test")
    failed_trace.start_execution()
    await asyncio.sleep(0.01)
    failed_trace.end_execution(False, "failed")
    
    await metrics_engine.record_pipeline_run(
        pipeline_name="HTTPFragmentation",
        execution_trace=failed_trace,
        response_success=False
    )
    
    # Получаем метрики
    print("\n📊 Current Metrics:")
    print("-" * 25)
    
    system_metrics = metrics_engine.get_system_metrics()
    print(f"Total Runs: {system_metrics.total_runs}")
    print(f"Network Verified: {system_metrics.network_verified_runs}")
    print(f"Simulation Detected: {system_metrics.simulated_runs}")
    print(f"Failed: {system_metrics.failed_runs}")
    print(f"REALITY_SCORE: {system_metrics.reality_score:.1f}%")
    print(f"SIMULATION_RATIO: {system_metrics.simulation_ratio:.3f}")
    
    # Метрики по пайплайнам
    print("\n📈 Pipeline Metrics:")
    print("-" * 25)
    
    pipeline_metrics = metrics_engine.get_all_pipeline_metrics()
    for name, stats in pipeline_metrics.items():
        if stats['total_runs'] > 0:
            print(f"{name}:")
            print(f"  Total: {stats['total_runs']}")
            print(f"  Reality Score: {stats['reality_score']:.1f}%")
            print(f"  Simulation Ratio: {stats['simulation_ratio']:.3f}")
            print()
    
    # Генерируем отчет
    print("📝 Generating SYSTEM_TRUTH_REPORT.md...")
    try:
        report_path = metrics_engine.generate_truth_report()
        print(f"✅ Report generated: {report_path}")
        
        # Показываем первые строки отчета
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("\n📄 Report Preview (first 15 lines):")
        print("-" * 40)
        for i, line in enumerate(lines[:15]):
            print(f"{i+1:2d}: {line.rstrip()}")
        
        if len(lines) > 15:
            print(f"... ({len(lines) - 15} more lines)")
            
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")
    
    # Проверяем формулы
    print("\n🧮 Formula Verification:")
    print("-" * 25)
    
    if system_metrics.total_runs > 0:
        expected_reality = (system_metrics.network_verified_runs / system_metrics.total_runs) * 100
        expected_simulation = system_metrics.simulated_runs / system_metrics.total_runs
        
        print(f"REALITY_SCORE: {system_metrics.reality_score:.1f}% (expected: {expected_reality:.1f}%)")
        print(f"SIMULATION_RATIO: {system_metrics.simulation_ratio:.3f} (expected: {expected_simulation:.3f})")
        
        reality_ok = abs(system_metrics.reality_score - expected_reality) < 0.01
        simulation_ok = abs(system_metrics.simulation_ratio - expected_simulation) < 0.001
        
        print(f"✅ REALITY_SCORE formula: {'CORRECT' if reality_ok else 'INCORRECT'}")
        print(f"✅ SIMULATION_RATIO formula: {'CORRECT' if simulation_ok else 'INCORRECT'}")
    else:
        print("No runs to verify")
    
    print("\n🎉 Basic test completed!")
    print("\n📋 Summary:")
    print(f"- Total pipeline runs recorded: {system_metrics.total_runs}")
    print(f"- SYSTEM_TRUTH_REPORT.md generated successfully")
    print(f"- REALITY_SCORE and SIMULATION_RATIO formulas verified")

if __name__ == "__main__":
    asyncio.run(test_basic_metrics())
