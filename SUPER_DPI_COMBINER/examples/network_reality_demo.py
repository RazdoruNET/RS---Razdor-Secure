#!/usr/bin/env python3
"""
Network Reality Verifier Demo - TASK 8.3
Демонстрация верификатора реальных сетевых операций
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.network_reality_verifier import (
    NetworkRealityVerifier, 
    NetworkOperation,
    verify_network_reality
)

async def demo_basic_verification():
    """Демонстрация базовой верификации"""
    print("🔍 Network Reality Verifier Demo")
    print("=" * 50)
    
    verifier = NetworkRealityVerifier()
    
    # Тест 1: Верификация подключения к httpbin.org
    print("\n📡 Тест 1: Верификация подключения к httpbin.org:80")
    try:
        operation, fd = await verifier.create_test_operation("httpbin.org", 80, "connect")
        result = await verifier.verify_network_operation(operation)
        
        print(f"  Socket открыт: {'✅' if result.socket_open else '❌'}")
        print(f"  TCP Handshake: {'✅' if result.handshake_verified else '❌'}")
        print(f"  Network Verified: {'✅' if result.network_verified else '❌'}")
        print(f"  Время верификации: {result.verification_time:.3f}s")
        
        if fd:
            os.close(fd)
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Тест 2: Верификация отправки данных
    print("\n📤 Тест 2: Верификация отправки данных на httpbin.org:80")
    try:
        operation, fd = await verifier.create_test_operation("httpbin.org", 80, "send")
        result = await verifier.verify_network_operation(operation)
        
        print(f"  Socket открыт: {'✅' if result.socket_open else '❌'}")
        print(f"  Bytes Sent Verified: {'✅' if result.bytes_sent_verified else '❌'}")
        print(f"  Network Verified: {'✅' if result.network_verified else '❌'}")
        print(f"  Заявлено байт: {operation.claimed_bytes}")
        print(f"  Время верификации: {result.verification_time:.3f}s")
        
        if fd:
            os.close(fd)
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # Тест 3: Верификация получения данных
    print("\n📥 Тест 3: Верификация получения данных с httpbin.org:80")
    try:
        operation, fd = await verifier.create_test_operation("httpbin.org", 80, "recv")
        result = await verifier.verify_network_operation(operation)
        
        print(f"  Socket открыт: {'✅' if result.socket_open else '❌'}")
        print(f"  Bytes Recv Verified: {'✅' if result.bytes_recv_verified else '❌'}")
        print(f"  Network Verified: {'✅' if result.network_verified else '❌'}")
        print(f"  Получено байт: {operation.claimed_bytes}")
        print(f"  Время верификации: {result.verification_time:.3f}s")
        
        if fd:
            os.close(fd)
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

async def demo_convenience_function():
    """Демонстрация удобной функции"""
    print("\n🔧 Удобная функция verify_network_reality")
    print("=" * 50)
    
    # Тест с удобной функцией
    try:
        result = await verify_network_reality(
            "connect",
            "httpbin.org", 
            80,
            claimed_success=True
        )
        
        print(f"  Network Verified: {'✅' if result['network_verified'] else '❌'}")
        print(f"  Verification Time: {result['verification_time']:.3f}s")
        print(f"  Socket Open: {'✅' if result['checks']['socket_open'] else '❌'}")
        print(f"  Handshake Verified: {'✅' if result['checks']['handshake_verified'] else '❌'}")
        
        if result['error_message']:
            print(f"  Error: {result['error_message']}")
            
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

async def demo_statistics():
    """Демонстрация статистики верификации"""
    print("\n📊 Статистика верификации")
    print("=" * 50)
    
    verifier = NetworkRealityVerifier()
    
    # Выполняем несколько верификаций для сбора статистики
    operations = [
        ("connect", "httpbin.org", 80),
        ("send", "httpbin.org", 80),
        ("recv", "httpbin.org", 80)
    ]
    
    for op_type, host, port in operations:
        try:
            operation, fd = await verifier.create_test_operation(host, port, op_type)
            await verifier.verify_network_operation(operation)
            
            if fd:
                os.close(fd)
                
        except Exception as e:
            print(f"  ⚠️ Ошибка в операции {op_type}: {e}")
    
    # Показываем статистику
    stats = verifier.get_verification_statistics()
    
    print(f"  Всего верификаций: {stats['total_verifications']}")
    print(f"  Успешных: {stats['successful_verifications']}")
    print(f"  Неудачных: {stats['failed_verifications']}")
    print(f"  Success Rate: {stats['success_rate']:.2%}")
    print(f"  Среднее время: {stats['avg_verification_time']:.3f}s")
    print(f"  Recent Success Rate: {stats['recent_success_rate']:.2%}")

async def demo_error_handling():
    """Демонстрация обработки ошибок"""
    print("\n⚠️ Обработка ошибок")
    print("=" * 50)
    
    verifier = NetworkRealityVerifier()
    
    # Тест с неверным FD
    print("\nТест с неверным файловым дескриптором:")
    operation = NetworkOperation(
        operation_type="connect",
        socket_fd=99999,  # Неверный FD
        target_host="example.com",
        target_port=443
    )
    
    result = await verifier.verify_network_operation(operation)
    print(f"  Socket открыт: {'✅' if result.socket_open else '❌'}")
    print(f"  Network Verified: {'✅' if result.network_verified else '❌'}")
    print(f"  Error: {result.error_message or 'Нет ошибок'}")
    
    # Тест с недоступным хостом
    print("\nТест с недоступным хостом:")
    try:
        operation, fd = await verifier.create_test_operation("nonexistent.host.example", 80, "connect")
        result = await verifier.verify_network_operation(operation)
        
        print(f"  Network Verified: {'✅' if result.network_verified else '❌'}")
        print(f"  Error: {result.error_message or 'Нет ошибок'}")
        
        if fd:
            os.close(fd)
            
    except Exception as e:
        print(f"  ❌ Ошибка создания операции: {e}")

async def main():
    """Главная функция демо"""
    print("🚀 Запуск Network Reality Verifier Demo")
    print("TASK 8.3 - Отделение 'код сказал отправил' от 'ОС реально отправила'")
    print()
    
    try:
        await demo_basic_verification()
        await demo_convenience_function()
        await demo_statistics()
        await demo_error_handling()
        
        print("\n✅ Демонстрация завершена!")
        print("\nКлючевые возможности:")
        print("- 🔍 Проверка реального состояния сокетов")
        print("- 📤 Верификация отправленных байт")
        print("- 📥 Верификация полученных байт")
        print("- 🤝 Проверка TCP handshake")
        print("- 📊 Сбор статистики верификаций")
        print("- ⚠️ Обработка ошибок и исключений")
        
    except KeyboardInterrupt:
        print("\n🛑 Демонстрация прервана")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
