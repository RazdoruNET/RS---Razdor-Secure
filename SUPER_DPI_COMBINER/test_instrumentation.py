#!/usr/bin/env python3
"""
Тестирование слоя инструментирования I/O операций
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.truth import enable_instrumentation, get_io_monitor, require_real_io, async_require_real_io
import socket
import aiohttp

@require_real_io
def test_socket_operations():
    """Тест socket операций"""
    print("Testing socket operations...")
    
    # Создаем сокет и делаем реальный запрос
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("www.google.com", 80))
        request = b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n"
        sock.send(request)
        response = sock.recv(1024)
        print(f"Received {len(response)} bytes")
    finally:
        sock.close()

@async_require_real_io
async def test_asyncio_operations():
    """Тест asyncio операций"""
    print("Testing asyncio operations...")
    
    # Создаем соединение через asyncio
    reader, writer = await asyncio.open_connection("www.google.com", 80)
    try:
        request = b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n"
        writer.write(request)
        await writer.drain()
        
        response = await reader.read(1024)
        print(f"Received {len(response)} bytes")
    finally:
        writer.close()
        await writer.wait_closed()

@async_require_real_io
async def test_http_operations():
    """Тест HTTP операций"""
    print("Testing HTTP operations...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.google.com") as response:
            data = await response.read()
            print(f"HTTP GET received {len(data)} bytes, status: {response.status}")

def main():
    """Основная функция тестирования"""
    print("=== Instrumentation Layer Test ===")
    
    # Включаем инструментирование
    enable_instrumentation()
    
    # Получаем монитор
    monitor = get_io_monitor()
    
    print("\n1. Testing socket operations...")
    try:
        test_socket_operations()
        print("✓ Socket operations completed successfully")
    except Exception as e:
        print(f"✗ Socket operations failed: {e}")
    
    print("\n2. Testing asyncio operations...")
    try:
        asyncio.run(test_asyncio_operations())
        print("✓ Asyncio operations completed successfully")
    except Exception as e:
        print(f"✗ Asyncio operations failed: {e}")
    
    print("\n3. Testing HTTP operations...")
    try:
        asyncio.run(test_http_operations())
        print("✓ HTTP operations completed successfully")
    except Exception as e:
        print(f"✗ HTTP operations failed: {e}")
    
    # Показываем статистику
    print("\n=== Instrumentation Statistics ===")
    stats = monitor.get_statistics()
    
    print(f"Total operations: {stats['total_operations']}")
    print(f"Total syscalls: {stats['total_syscalls']}")
    print(f"IO operations in session: {stats['io_operations_in_session']}")
    print(f"Session duration: {stats['session_duration']:.2f}s")
    
    print("\nOperation breakdown:")
    for op_type, count in stats['operation_stats'].items():
        print(f"  {op_type}: {count} operations")
    
    print("\nByte statistics:")
    for op_type, bytes_count in stats['byte_stats'].items():
        print(f"  {op_type}: {bytes_count} bytes")
    
    if stats['error_stats']:
        print("\nError statistics:")
        for op_type, error_count in stats['error_stats'].items():
            print(f"  {op_type}: {error_count} errors")
    
    print("\nRecent operations (last 5):")
    recent_ops = monitor.get_recent_operations(5)
    for i, op in enumerate(recent_ops, 1):
        print(f"  {i}. {op.operation_type.value} - {op.data_size} bytes - {op.source_location}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
