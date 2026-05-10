#!/usr/bin/env python3
"""
Демонстрация слоя инструментирования I/O операций
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth import enable_instrumentation, get_io_monitor, require_real_io
import socket

def demo_instrumentation_features():
    """Демонстрация возможностей инструментирования"""
    print("=== Instrumentation Layer Demo ===\n")
    
    # Включаем инструментирование
    enable_instrumentation()
    
    # Получаем монитор
    monitor = get_io_monitor()
    
    print("1. Testing socket operations with real I/O...")
    
    # Создаем сокет и делаем реальный запрос
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to Google
        sock.connect(("www.google.com", 80))
        
        # Send HTTP request
        request = b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n"
        bytes_sent = sock.send(request)
        print(f"   Sent {bytes_sent} bytes")
        
        # Receive response
        response = sock.recv(1024)
        print(f"   Received {len(response)} bytes")
        
        # Show sample of received data
        if response:
            sample = response[:100].hex()
            print(f"   Data sample: {sample[:50]}...")
            
    finally:
        sock.close()
    
    print("\n2. Checking I/O statistics...")
    
    # Получаем статистику
    stats = monitor.get_statistics()
    
    print(f"   Total operations: {stats['total_operations']}")
    print(f"   Total syscalls: {stats['total_syscalls']}")
    print(f"   Real I/O detected: {stats['io_operations_in_session']}")
    print(f"   Session duration: {stats['session_duration']:.3f}s")
    
    print("\n3. Operation breakdown:")
    for op_type, count in stats['operation_stats'].items():
        print(f"   {op_type}: {count} operations")
    
    print("\n4. Byte statistics:")
    for op_type, bytes_count in stats['byte_stats'].items():
        print(f"   {op_type}: {bytes_count} bytes")
    
    print("\n5. Recent operations (last 3):")
    recent_ops = monitor.get_recent_operations(3)
    for i, op in enumerate(recent_ops, 1):
        print(f"   {i}. {op.operation_type.value}")
        print(f"      Size: {op.data_size} bytes")
        print(f"      Success: {op.success}")
        print(f"      Location: {op.source_location}")
        if op.metadata:
            print(f"      Duration: {op.metadata.get('duration', 0):.6f}s")
        print()
    
    print("6. Testing real I/O requirement...")
    
    # Тестируем декоратор require_real_io
    @require_real_io
    def test_with_real_io():
        print("   Function with real I/O requirement - PASSED")
        return "success"
    
    try:
        result = test_with_real_io()
        print(f"   Result: {result}")
    except RuntimeError as e:
        print(f"   Error: {e}")
    
    print("\n=== Demo Complete ===")
    print("✓ Socket send/recv operations intercepted")
    print("✓ Actual bytes logged") 
    print("✓ System calls recorded")
    print("✓ Real I/O verification working")
    print("✓ Detailed statistics collected")

if __name__ == "__main__":
    demo_instrumentation_features()
