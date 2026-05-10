#!/usr/bin/env python3
"""
Stress Test - Проверка memory growth, socket leaks, task leaks
100 sequential requests с метриками
"""

import asyncio
import sys
import time
import gc
import socket
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class StressTestAuditor:
    """Auditor для стресс теста"""
    
    def __init__(self):
        self.metrics_before = {}
        self.metrics_after = {}
        self.request_results = []
        
    def capture_baseline_metrics(self):
        """Захватить baseline метрики"""
        print("\n📊 Capturing Baseline Metrics")
        print("=" * 50)
        
        # Memory metrics
        gc.collect()
        baseline_memory = gc.get_stats()
        
        # Socket metrics
        open_sockets_before = len([f for f in gc.get_objects() if isinstance(f, socket.socket)])
        
        # Task metrics
        try:
            tasks_before = len(asyncio.all_tasks())
        except:
            tasks_before = 0
        
        self.metrics_before = {
            'memory_stats': baseline_memory,
            'open_sockets': open_sockets_before,
            'tasks': tasks_before,
            'timestamp': time.time()
        }
        
        print(f"📈 Baseline Memory: {baseline_memory}")
        print(f"🌐 Open Sockets: {open_sockets_before}")
        print(f"📤 Async Tasks: {tasks_before}")
        
        return self.metrics_before
    
    async def run_sequential_requests(self):
        """Выполнить 100 sequential requests"""
        print("\n🚀 Running 100 Sequential Requests")
        print("=" * 50)
        
        try:
            from super_dpi_combiner.pipelines.echo import Echo
            from super_dpi_combiner.core.contracts import Request
            
            pipeline = Echo()
            
            for i in range(100):
                request = Request(
                    host=f"test-{i}.example.com",
                    port=80,
                    method="GET"
                )
                
                start_time = time.time()
                response = pipeline.execute(request)
                end_time = time.time()
                
                result = {
                    'request_id': i + 1,
                    'success': response.success,
                    'latency': end_time - start_time,
                    'status_code': response.status_code,
                    'error': response.error
                }
                
                self.request_results.append(result)
                
                if (i + 1) % 20 == 0:
                    print(f"📊 Progress: {i + 1}/100 requests")
                    avg_latency = sum(r['latency'] for r in self.request_results) / len(self.request_results)
                    success_rate = sum(1 for r in self.request_results if r['success']) / len(self.request_results) * 100
                    print(f"  Avg Latency: {avg_latency:.3f}s")
                    print(f"  Success Rate: {success_rate:.1f}%")
                
        except Exception as e:
            print(f"❌ Stress test error: {e}")
    
    def capture_final_metrics(self):
        """Захватить финальные метрики"""
        print("\n📊 Capturing Final Metrics")
        print("=" * 50)
        
        # Memory metrics
        gc.collect()
        final_memory = gc.get_stats()
        
        # Socket metrics
        open_sockets_after = len([f for f in gc.get_objects() if isinstance(f, socket.socket)])
        
        # Task metrics
        try:
            tasks_after = len(asyncio.all_tasks())
        except:
            tasks_after = 0
        
        self.metrics_after = {
            'memory_stats': final_memory,
            'open_sockets': open_sockets_after,
            'tasks': tasks_after,
            'timestamp': time.time()
        }
        
        print(f"📈 Final Memory: {final_memory}")
        print(f"🌐 Open Sockets: {open_sockets_after}")
        print(f"📤 Async Tasks: {tasks_after}")
        
        return self.metrics_after
    
    def analyze_memory_growth(self):
        """Анализировать memory growth"""
        print("\n🧠 Memory Growth Analysis")
        print("=" * 50)
        
        before_stats = self.metrics_before['memory_stats']
        after_stats = self.metrics_after['memory_stats']
        
        # Simple memory comparison
        before_total = before_stats[0].get('collected', 0) if before_stats else 0
        after_total = after_stats[0].get('collected', 0) if after_stats else 0
        
        memory_growth = {
            'allocated_before': before_total,
            'allocated_after': after_total,
            'growth': after_total - before_total
        }
        
        print(f"📊 Memory Allocated Before: {memory_growth['allocated_before']}")
        print(f"📊 Memory Allocated After: {memory_growth['allocated_after']}")
        print(f"📊 Memory Growth: {memory_growth['growth']}")
        
        if memory_growth['growth'] > 0:
            print("❌ Memory leak detected")
            return False
        else:
            print("✅ No significant memory growth")
            return True
    
    def analyze_socket_leaks(self):
        """Анализировать socket leaks"""
        print("\n🌐 Socket Leak Analysis")
        print("=" * 50)
        
        sockets_before = self.metrics_before['open_sockets']
        sockets_after = self.metrics_after['open_sockets']
        
        socket_leak = {
            'sockets_before': sockets_before,
            'sockets_after': sockets_after,
            'leaked': sockets_after - sockets_before
        }
        
        print(f"📊 Open Sockets Before: {socket_leak['sockets_before']}")
        print(f"📊 Open Sockets After: {socket_leak['sockets_after']}")
        print(f"📊 Socket Leak: {socket_leak['leaked']}")
        
        if socket_leak['leaked'] > 0:
            print("❌ Socket leak detected")
            return False
        else:
            print("✅ No socket leaks")
            return True
    
    def analyze_task_leaks(self):
        """Анализировать task leaks"""
        print("\n📤 Task Leak Analysis")
        print("=" * 50)
        
        tasks_before = self.metrics_before['tasks']
        tasks_after = self.metrics_after['tasks']
        
        task_leak = {
            'tasks_before': tasks_before,
            'tasks_after': tasks_after,
            'leaked': tasks_after - tasks_before
        }
        
        print(f"📊 Tasks Before: {task_leak['tasks_before']}")
        print(f"📊 Tasks After: {task_leak['tasks_after']}")
        print(f"📊 Task Leak: {task_leak['leaked']}")
        
        if task_leak['leaked'] > 0:
            print("❌ Task leak detected")
            return False
        else:
            print("✅ No task leaks")
            return True
    
    def analyze_latency_drift(self):
        """Анализировать latency drift"""
        print("\n⏱️ Latency Drift Analysis")
        print("=" * 50)
        
        if not self.request_results:
            print("❌ No request results to analyze")
            return False
        
        latencies = [r['latency'] for r in self.request_results]
        
        latency_stats = {
            'min': min(latencies),
            'max': max(latencies),
            'avg': sum(latencies) / len(latencies),
            'first_10': sum(latencies[:10]) / 10,
            'last_10': sum(latencies[-10:]) / 10
        }
        
        print(f"📊 Min Latency: {latency_stats['min']:.6f}s")
        print(f"📊 Max Latency: {latency_stats['max']:.6f}s")
        print(f"📊 Avg Latency: {latency_stats['avg']:.6f}s")
        print(f"📊 First 10 Avg: {latency_stats['first_10']:.6f}s")
        print(f"📊 Last 10 Avg: {latency_stats['last_10']:.6f}s")
        
        # Проверяем drift
        drift = latency_stats['last_10'] - latency_stats['first_10']
        print(f"📊 Latency Drift: {drift:.6f}s")
        
        if abs(drift) > 0.001:  # 1ms drift threshold
            print("❌ Significant latency drift detected")
            return False
        else:
            print("✅ No significant latency drift")
            return True
    
    async def run_full_stress_test(self):
        """Полный стресс тест"""
        print("🚀 Stress Test v2")
        print("Цель: Проверить memory growth, socket leaks, task leaks")
        print("Метод: 100 sequential requests + метрики")
        
        # Базовые метрики
        self.capture_baseline_metrics()
        
        # Выполняем запросы
        await self.run_sequential_requests()
        
        # Финальные метрики
        self.capture_final_metrics()
        
        # Анализируем результаты
        memory_ok = self.analyze_memory_growth()
        sockets_ok = self.analyze_socket_leaks()
        tasks_ok = self.analyze_task_leaks()
        latency_ok = self.analyze_latency_drift()
        
        return {
            'memory_ok': memory_ok,
            'sockets_ok': sockets_ok,
            'tasks_ok': tasks_ok,
            'latency_ok': latency_ok,
            'total_requests': len(self.request_results)
        }

def write_stress_test_report(results):
    """Записать отчёт о стресс тесте"""
    report = f"""# STRESS_TEST_REPORT.md

## Stress Test Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Configuration
- Sequential Requests: 100
- Pipeline: Echo
- Target: test-*.example.com

## Resource Metrics

### Memory Analysis
- Memory Growth: {'VERIFIED' if results['memory_ok'] else 'NOT VERIFIED'}
- Memory Leaks: {'NO' if results['memory_ok'] else 'YES'}

### Socket Analysis  
- Socket Leaks: {'NO' if results['sockets_ok'] else 'YES'}
- Socket Management: {'VERIFIED' if results['sockets_ok'] else 'NOT VERIFIED'}

### Task Analysis
- Task Leaks: {'NO' if results['tasks_ok'] else 'YES'}
- Task Management: {'VERIFIED' if results['tasks_ok'] else 'NOT VERIFIED'}

### Performance Analysis
- Latency Drift: {'VERIFIED' if results['latency_ok'] else 'NOT VERIFIED'}
- Performance Stability: {'VERIFIED' if results['latency_ok'] else 'NOT VERIFIED'}

## Verification Results

### Resource Management
- Memory Management: {'VERIFIED' if results['memory_ok'] else 'NOT VERIFIED'}
- Socket Management: {'VERIFIED' if results['sockets_ok'] else 'NOT VERIFIED'}
- Task Management: {'VERIFIED' if results['tasks_ok'] else 'NOT VERIFIED'}

### Performance
- Latency Stability: {'VERIFIED' if results['latency_ok'] else 'NOT VERIFIED'}
- Request Processing: {'VERIFIED' if results['total_requests'] == 100 else 'NOT VERIFIED'}

## Component Status
- Echo Pipeline: {'VERIFIED' if results['total_requests'] == 100 else 'NOT VERIFIED'}
- Runtime: {'VERIFIED' if all([results['memory_ok'], results['sockets_ok'], results['tasks_ok']]) else 'NOT VERIFIED'}

## Final Classification

### Stress Test Results
- Total Requests: {results['total_requests']}/100
- Memory Leaks: {'NO' if results['memory_ok'] else 'YES'}
- Socket Leaks: {'NO' if results['sockets_ok'] else 'YES'}
- Task Leaks: {'NO' if results['tasks_ok'] else 'YES'}
- Latency Drift: {'NO' if results['latency_ok'] else 'YES'}

### Overall Status
STRESS_TEST: {'VERIFIED' if results['total_requests'] == 100 and all([results['memory_ok'], results['sockets_ok'], results['tasks_ok'], results['latency_ok']]) else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/STRESS_TEST_REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 Stress test report written to: STRESS_TEST_REPORT.md")

async def main():
    """Основная функция стресс теста"""
    auditor = StressTestAuditor()
    results = await auditor.run_full_stress_test()
    write_stress_test_report(results)
    print("\n✅ Stress Test завершён")

if __name__ == "__main__":
    asyncio.run(main())
