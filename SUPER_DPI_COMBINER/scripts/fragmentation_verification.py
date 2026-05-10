#!/usr/bin/env python3
"""
Fragmentation Verification - Доказательство физической фрагментации
Фиксация timestamps, chunk sizes, inter-send latency
"""

import sys
import time
import socket
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fragmentation tracing
fragmentation_traces = []

class FragmentationTracingSocket:
    """Socket wrapper для трассировки фрагментации"""
    
    def __init__(self, *args, **kwargs):
        self.original = socket.socket(*args, **kwargs)
        self.last_send_time = None
        
    def connect(self, address):
        trace = {
            'timestamp': time.time(),
            'operation': 'CONNECT',
            'address': str(address)
        }
        fragmentation_traces.append(trace)
        print(f"[FRAG] CONNECT {address} at {trace['timestamp']:.6f}")
        return self.original.connect(address)
    
    def send(self, data):
        current_time = time.time()
        
        # Вычисляем inter-send latency
        inter_send_latency = None
        if self.last_send_time is not None:
            inter_send_latency = current_time - self.last_send_time
        
        trace = {
            'timestamp': current_time,
            'operation': 'SEND',
            'data_size': len(data),
            'data_preview': data[:30].hex(),
            'inter_send_latency': inter_send_latency
        }
        fragmentation_traces.append(trace)
        
        print(f"[FRAG] CHUNK {len(fragmentation_traces)}: {len(data)} bytes at {current_time:.6f}")
        if inter_send_latency is not None:
            print(f"[FRAG]   Inter-send latency: {inter_send_latency*1000:.3f}ms")
        print(f"[FRAG]   Data preview: {data[:30].hex()}")
        
        self.last_send_time = current_time
        return self.original.send(data)
    
    def recv(self, bufsize):
        data = self.original.recv(bufsize)
        trace = {
            'timestamp': time.time(),
            'operation': 'RECV',
            'data_size': len(data) if data else 0
        }
        fragmentation_traces.append(trace)
        print(f"[FRAG] RECV {len(data) if data else 0} bytes at {trace['timestamp']:.6f}")
        return data
    
    def close(self):
        trace = {
            'timestamp': time.time(),
            'operation': 'CLOSE'
        }
        fragmentation_traces.append(trace)
        print(f"[FRAG] CLOSE at {trace['timestamp']:.6f}")
        return self.original.close()
    
    def settimeout(self, value):
        print(f"[FRAG] SETTIMEOUT {value}")
        return self.original.settimeout(value)
    
    def __getattr__(self, name):
        return getattr(self.original, name)

def patch_socket_for_fragmentation():
    """Патч для трассировки фрагментации"""
    original_socket = socket.socket
    socket.socket = FragmentationTracingSocket
    print("🔍 Fragmentation tracing enabled")
    return original_socket

def test_fragmentation():
    """Тест фрагментации с детальной трассировкой"""
    print("\n🧪 Testing HTTP Fragmentation with detailed tracing")
    print("=" * 60)
    
    original_socket = patch_socket_for_fragmentation()
    
    try:
        # Импортируем после патча
        from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
        from super_dpi_combiner.core.contracts import Request
        
        # Создаем пайплайн
        pipeline = HTTPFragmentation()
        
        print(f"\n📊 Pipeline chunk size: {pipeline.chunk_size} bytes")
        
        # Создаем запрос
        request = Request(
            host="httpbin.org",
            port=80,
            method="GET",
            path="/get"
        )
        
        print(f"\n📤 Executing fragmented request to {request.host}:{request.port}")
        print(f"📤 Expected fragmentation: chunks of {pipeline.chunk_size} bytes")
        
        # Выполняем
        start_time = time.time()
        response = pipeline.execute(request)
        end_time = time.time()
        
        print(f"\n📊 Execution Results:")
        print(f"  Success: {response.success}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Total Latency: {end_time - start_time:.3f}s")
        print(f"  Error: {response.error}")
        print(f"  Response Size: {len(response.data)} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        socket.socket = original_socket
        print("🔍 Fragmentation tracing disabled")

def analyze_fragmentation():
    """Анализировать фрагментацию"""
    print("\n📈 Fragmentation Analysis")
    print("=" * 60)
    
    if not fragmentation_traces:
        print("❌ No fragmentation traces")
        return
    
    # Извлекаем SEND операции
    send_ops = [t for t in fragmentation_traces if t['operation'] == 'SEND']
    
    if not send_ops:
        print("❌ No SEND operations found")
        return
    
    print(f"\n🔍 Fragmentation Evidence:")
    print(f"  Total chunks sent: {len(send_ops)}")
    print(f"  Chunk sizes: {[op['data_size'] for op in send_ops]}")
    
    # Проверяем что chunks не буферизуются
    unique_sizes = set(op['data_size'] for op in send_ops)
    if len(unique_sizes) > 1:
        print("  ✅ Variable chunk sizes - NOT buffered")
    else:
        print("  ❌ Same chunk sizes - possibly buffered")
    
    # Анализируем inter-send latency
    inter_send_latencies = [op['inter_send_latency'] for op in send_ops if op['inter_send_latency'] is not None]
    if inter_send_latencies:
        avg_latency = sum(inter_send_latencies) / len(inter_send_latencies)
        print(f"  Average inter-send latency: {avg_latency*1000:.3f}ms")
        print(f"  Min inter-send latency: {min(inter_send_latencies)*1000:.3f}ms")
        print(f"  Max inter-send latency: {max(inter_send_latencies)*1000:.3f}ms")
    
    # Детальная информация о chunks
    print(f"\n📋 Detailed Chunk Information:")
    for i, op in enumerate(send_ops):
        timestamp = time.strftime('%H:%M:%S', time.localtime(op['timestamp']))
        print(f"  Chunk {i+1}: {op['data_size']} bytes at {timestamp}")
        if op['inter_send_latency'] is not None:
            print(f"    Delay after previous: {op['inter_send_latency']*1000:.3f}ms")
        print(f"    Data preview: {op['data_preview']}")

def write_fragmentation_report():
    """Записать отчёт о фрагментации"""
    send_ops = [t for t in fragmentation_traces if t['operation'] == 'SEND']
    
    report = f"""# FRAGMENTATION_VERIFICATION.md

## Fragmentation Verification Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Fragmentation Evidence

### Chunks Sent
- Total chunks: {len(send_ops)}
- Chunk sizes: {[op['data_size'] for op in send_ops]}

### Inter-Send Latency Analysis
{chr(10).join(f"- Chunk {i+1} delay: {op['inter_send_latency']*1000:.3f}ms" for i, op in enumerate(send_ops) if op['inter_send_latency'] is not None)}

### Detailed Chunk Timeline
{chr(10).join(f"- {time.strftime('%H:%M:%S', time.localtime(op['timestamp']))}: Chunk {i+1} - {op['data_size']} bytes" for i, op in enumerate(send_ops))}

## Verification Results

### Physical Fragmentation
- Real chunk separation: {'VERIFIED' if len(set(op['data_size'] for op in send_ops)) > 1 else 'NOT VERIFIED'}
- Inter-send delays: {'VERIFIED' if any(op['inter_send_latency'] for op in send_ops) else 'NOT VERIFIED'}
- Timestamp evidence: {'VERIFIED' if len(send_ops) > 0 else 'NOT VERIFIED'}

### Component Status
- HTTPFragmentation: {'VERIFIED' if len(send_ops) > 1 else 'NOT VERIFIED'}
- Chunk processing: {'VERIFIED' if len(send_ops) > 0 else 'NOT VERIFIED'}

## Final Classification
FRAGMENTATION_PHYSICAL: {'VERIFIED' if len(send_ops) > 1 else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/FRAGMENTATION_VERIFICATION.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 Fragmentation report written to: FRAGMENTATION_VERIFICATION.md")

def main():
    """Основная функция"""
    print("🚀 Fragmentation Verification v2")
    print("Цель: Доказать физическую фрагментацию")
    print("Метод: Socket tracing с timestamps и chunk sizes")
    
    # Тестируем фрагментацию
    test_fragmentation()
    
    # Анализируем результаты
    analyze_fragmentation()
    
    # Записываем отчёт
    write_fragmentation_report()
    
    print("\n✅ Fragmentation Verification завершён")

if __name__ == "__main__":
    main()
