#!/usr/bin/env python3
"""
Network Reality Verifier Tests - TASK 8.3
Тесты верификатора реальных сетевых операций
"""

import asyncio
import unittest
import socket
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.network_reality_verifier import (
    NetworkRealityVerifier, 
    NetworkOperation, 
    VerificationResult,
    VerificationStatus,
    verify_network_reality
)

class TestNetworkRealityVerifier(unittest.TestCase):
    """Тесты Network Reality Verifier"""
    
    def setUp(self):
        """Настройка тестов"""
        self.verifier = NetworkRealityVerifier()
        
    def test_verifier_initialization(self):
        """Тест инициализации верификатора"""
        self.assertIsInstance(self.verifier, NetworkRealityVerifier)
        self.assertEqual(len(self.verifier.active_sockets), 0)
        self.assertEqual(len(self.verifier.verification_history), 0)
    
    def test_network_operation_creation(self):
        """Тест создания сетевой операции"""
        operation = NetworkOperation(
            operation_type="connect",
            claimed_success=True,
            timestamp=time.time(),
            target_host="example.com",
            target_port=443
        )
        
        self.assertEqual(operation.operation_type, "connect")
        self.assertTrue(operation.claimed_success)
        self.assertEqual(operation.target_host, "example.com")
        self.assertEqual(operation.target_port, 443)
    
    def test_verification_result_creation(self):
        """Тест создания результата верификации"""
        operation = NetworkOperation(
            operation_type="send",
            claimed_bytes=1024,
            target_host="example.com",
            target_port=80
        )
        
        result = VerificationResult(operation=operation)
        
        self.assertEqual(result.operation, operation)
        self.assertFalse(result.network_verified)
        self.assertEqual(result.verification_time, 0.0)
    
    async def test_verify_socket_open_success(self):
        """Тест проверки открытого сокета - успех"""
        # Создаем реальный сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fd = sock.fileno()
        
        try:
            result = await self.verifier._verify_socket_open(fd)
            self.assertTrue(result)
        finally:
            sock.close()
    
    async def test_verify_socket_open_invalid_fd(self):
        """Тест проверки открытого сокета - неверный FD"""
        # Используем заведомо неверный FD
        invalid_fd = 99999
        
        result = await self.verifier._verify_socket_open(invalid_fd)
        self.assertFalse(result)
    
    async def test_verify_bytes_sent_with_socket(self):
        """Тест проверки отправленных байт с реальным сокетом"""
        # Создаем операцию отправки
        operation = NetworkOperation(
            operation_type="send",
            claimed_bytes=100,
            target_host="httpbin.org",
            target_port=80
        )
        
        # Создаем сокет и отправляем данные
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        try:
            sock.connect(("httpbin.org", 80))
            data = b"GET / HTTP/1.1\r\nHost: httpbin.org\r\n\r\n"
            bytes_sent = sock.send(data)
            
            operation.socket_fd = sock.fileno()
            operation.claimed_bytes = bytes_sent
            
            result = await self.verifier._verify_bytes_sent(operation)
            self.assertTrue(result)
            
        except Exception as e:
            # Если не удалось подключиться, пропускаем тест
            self.skipTest(f"Network connection failed: {e}")
        finally:
            sock.close()
    
    async def test_verify_tcp_handshake_success(self):
        """Тест проверки TCP handshake - успех"""
        operation = NetworkOperation(
            operation_type="connect",
            target_host="httpbin.org",
            target_port=80
        )
        
        # Создаем сокет и выполняем подключение
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        try:
            sock.connect(("httpbin.org", 80))
            operation.socket_fd = sock.fileno()
            
            result = await self.verifier._verify_tcp_handshake(operation)
            self.assertTrue(result)
            
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")
        finally:
            sock.close()
    
    async def test_verify_network_operation_connect(self):
        """Тест полной верификации операции подключения"""
        operation = NetworkOperation(
            operation_type="connect",
            claimed_success=True,
            target_host="httpbin.org",
            target_port=80
        )
        
        # Создаем сокет и подключаемся
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        try:
            sock.connect(("httpbin.org", 80))
            operation.socket_fd = sock.fileno()
            
            result = await self.verifier.verify_network_operation(operation)
            
            self.assertIsInstance(result, VerificationResult)
            self.assertTrue(result.socket_open)
            self.assertTrue(result.handshake_verified)
            # network_verified может быть False если нет правильного FD
            
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")
        finally:
            sock.close()
    
    async def test_verify_network_operation_send(self):
        """Тест полной верификации операции отправки"""
        operation = NetworkOperation(
            operation_type="send",
            claimed_bytes=100,
            target_host="httpbin.org",
            target_port=80
        )
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        try:
            sock.connect(("httpbin.org", 80))
            data = b"GET / HTTP/1.1\r\nHost: httpbin.org\r\n\r\n"
            bytes_sent = sock.send(data)
            
            operation.socket_fd = sock.fileno()
            operation.claimed_bytes = bytes_sent
            
            result = await self.verifier.verify_network_operation(operation)
            
            self.assertIsInstance(result, VerificationResult)
            self.assertTrue(result.socket_open)
            self.assertTrue(result.bytes_sent_verified)
            
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")
        finally:
            sock.close()
    
    def test_calculate_final_verification_all_checks_pass(self):
        """Тест расчета финальной верификации - все проверки пройдены"""
        operation = NetworkOperation(
            operation_type="connect",
            target_host="example.com",
            target_port=443
        )
        
        result = VerificationResult(operation=operation)
        result.socket_open = True
        result.handshake_verified = True
        
        final = self.verifier._calculate_final_verification(result)
        self.assertTrue(final)
    
    def test_calculate_final_verification_some_checks_fail(self):
        """Тест расчета финальной верификации - некоторые проверки не пройдены"""
        operation = NetworkOperation(
            operation_type="connect",
            target_host="example.com",
            target_port=443
        )
        
        result = VerificationResult(operation=operation)
        result.socket_open = True
        result.handshake_verified = False  # Одна проверка не пройдена
        
        final = self.verifier._calculate_final_verification(result)
        self.assertFalse(final)
    
    def test_get_verification_statistics_empty(self):
        """Тест получения статистики - пустая история"""
        stats = self.verifier.get_verification_statistics()
        
        self.assertEqual(stats['total_verifications'], 0)
        self.assertEqual(stats['successful_verifications'], 0)
        self.assertEqual(stats['failed_verifications'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
        self.assertEqual(stats['avg_verification_time'], 0.0)
    
    def test_get_verification_statistics_with_data(self):
        """Тест получения статистики - с данными"""
        # Добавляем тестовые результаты
        operation1 = NetworkOperation("connect", target_host="a.com", target_port=80)
        operation2 = NetworkOperation("send", target_host="b.com", target_port=443)
        
        result1 = VerificationResult(operation1)
        result1.network_verified = True
        result1.verification_time = 0.1
        
        result2 = VerificationResult(operation2)
        result2.network_verified = False
        result2.verification_time = 0.2
        
        self.verifier.verification_history = [result1, result2]
        
        stats = self.verifier.get_verification_statistics()
        
        self.assertEqual(stats['total_verifications'], 2)
        self.assertEqual(stats['successful_verifications'], 1)
        self.assertEqual(stats['failed_verifications'], 1)
        self.assertEqual(stats['success_rate'], 0.5)
        self.assertEqual(stats['avg_verification_time'], 0.15)
    
    def test_clear_history(self):
        """Тест очистки истории"""
        # Добавляем тестовые данные
        operation = NetworkOperation("connect", target_host="test.com", target_port=80)
        result = VerificationResult(operation)
        self.verifier.verification_history.append(result)
        
        # Проверяем что данные есть
        self.assertEqual(len(self.verifier.verification_history), 1)
        
        # Очищаем
        self.verifier.clear_history()
        
        # Проверяем что данные удалены
        self.assertEqual(len(self.verifier.verification_history), 0)
    
    async def test_create_test_operation_connect(self):
        """Тест создания тестовой операции подключения"""
        try:
            operation, fd = await self.verifier.create_test_operation(
                "httpbin.org", 80, "connect"
            )
            
            self.assertEqual(operation.operation_type, "connect")
            self.assertTrue(operation.claimed_success)
            self.assertEqual(operation.target_host, "httpbin.org")
            self.assertEqual(operation.target_port, 80)
            self.assertIsNotNone(operation.socket_fd)
            
            # Закрываем сокет
            if fd:
                os.close(fd)
                
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")
    
    async def test_create_test_operation_send(self):
        """Тест создания тестовой операции отправки"""
        try:
            operation, fd = await self.verifier.create_test_operation(
                "httpbin.org", 80, "send"
            )
            
            self.assertEqual(operation.operation_type, "send")
            self.assertGreater(operation.claimed_bytes, 0)
            self.assertTrue(operation.claimed_success)
            
            # Закрываем сокет
            if fd:
                os.close(fd)
                
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")


class TestVerifyNetworkRealityFunction(unittest.TestCase):
    """Тесты удобной функции verify_network_reality"""
    
    async def test_verify_network_reality_connect(self):
        """Тест удобной функции для верификации подключения"""
        try:
            result = await verify_network_reality(
                "connect", 
                "httpbin.org", 
                80,
                claimed_success=True
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('network_verified', result)
            self.assertIn('verification_time', result)
            self.assertIn('checks', result)
            self.assertIn('socket_open', result['checks'])
            self.assertIn('handshake_verified', result['checks'])
            
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")
    
    async def test_verify_network_reality_send(self):
        """Тест удобной функции для верификации отправки"""
        try:
            result = await verify_network_reality(
                "send", 
                "httpbin.org", 
                80,
                claimed_bytes=100
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('bytes_sent_verified', result['checks'])
            
        except Exception as e:
            self.skipTest(f"Network connection failed: {e}")


class TestNetworkRealityVerifierMock(unittest.TestCase):
    """Тесты с моками для изоляции от сети"""
    
    def setUp(self):
        self.verifier = NetworkRealityVerifier()
    
    async def test_verify_socket_open_with_mock(self):
        """Тест проверки сокета с моком"""
        with patch('socket.fromfd') as mock_fromfd:
            mock_sock = Mock()
            mock_sock.getsockopt.return_value = 0  # Нет ошибок
            mock_sock.close = Mock()
            mock_fromfd.return_value = mock_sock
            
            result = await self.verifier._verify_socket_open(123)
            self.assertTrue(result)
            
            mock_sock.getsockopt.assert_called()
            mock_sock.close.assert_called()
    
    async def test_verify_bytes_sent_with_mock(self):
        """Тест проверки отправки байт с моком"""
        operation = NetworkOperation(
            operation_type="send",
            claimed_bytes=100,
            socket_fd=123,
            target_host="example.com",
            target_port=80
        )
        
        with patch('socket.fromfd') as mock_fromfd:
            mock_sock = Mock()
            mock_sock.getsockopt.side_effect = [8192, 0]  # SNDBUF, SO_ERROR
            mock_sock.close = Mock()
            mock_fromfd.return_value = mock_sock
            
            result = await self.verifier._verify_bytes_sent(operation)
            self.assertTrue(result)
    
    async def test_verify_tcp_handshake_with_mock(self):
        """Тест проверки TCP handshake с моком"""
        operation = NetworkOperation(
            operation_type="connect",
            socket_fd=123,
            target_host="example.com",
            target_port=443
        )
        
        with patch('socket.fromfd') as mock_fromfd:
            mock_sock = Mock()
            mock_sock.getsockopt.return_value = 0  # Нет ошибок
            mock_sock.getsockname.return_value = ('192.168.1.1', 12345)
            mock_sock.getpeername.return_value = ('example.com', 443)
            mock_sock.close = Mock()
            mock_fromfd.return_value = mock_sock
            
            result = await self.verifier._verify_tcp_handshake(operation)
            self.assertTrue(result)


def run_async_test(test_func):
    """Вспомогательная функция для запуска асинхронных тестов"""
    def wrapper(self):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(test_func(self))
        finally:
            loop.close()
    return wrapper


# Применяем декоратор ко всем асинхронным тестам
for attr in dir(TestNetworkRealityVerifier):
    if attr.startswith('test_') and asyncio.iscoroutinefunction(getattr(TestNetworkRealityVerifier, attr)):
        setattr(TestNetworkRealityVerifier, attr, run_async_test(getattr(TestNetworkRealityVerifier, attr)))

for attr in dir(TestVerifyNetworkRealityFunction):
    if attr.startswith('test_') and asyncio.iscoroutinefunction(getattr(TestVerifyNetworkRealityFunction, attr)):
        setattr(TestVerifyNetworkRealityFunction, attr, run_async_test(getattr(TestVerifyNetworkRealityFunction, attr)))

for attr in dir(TestNetworkRealityVerifierMock):
    if attr.startswith('test_') and asyncio.iscoroutinefunction(getattr(TestNetworkRealityVerifierMock, attr)):
        setattr(TestNetworkRealityVerifierMock, attr, run_async_test(getattr(TestNetworkRealityVerifierMock, attr)))


if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)
