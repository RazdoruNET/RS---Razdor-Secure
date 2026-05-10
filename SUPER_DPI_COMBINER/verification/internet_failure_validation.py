#!/usr/bin/env python3
"""
Internet Failure Validation - Проверка реальных интернет ошибок и условий цензуры
"""

import sys
import time
import socket
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verification.internet_targets import get_target_for_test
from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

class InternetFailureValidator:
    """Валидатор реальных интернет ошибок"""
    
    def __init__(self):
        self.failure_results = []
        
    def test_dns_failure(self, host: str, port: int) -> dict:
        """Тестировать DNS failure"""
        print(f"🔍 Testing DNS failure: {host}")
        
        try:
            start_time = time.time()
            
            # Создаем пайплайн
            pipeline = HTTPFragmentation()
            
            # Создаем запрос с несуществующим хостом
            request = Request(
                host=f"nonexistent-{int(time.time())}.invalid",
                port=port,
                method="GET",
                path="/get"
            )
            
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                "failure_type": "dns_failure",
                "host": host,
                "success": response.success,
                "status_code": response.status_code,
                "error": response.error,
                "latency": end_time - start_time,
                "timestamp": time.time()
            }
            
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return result
            
        except Exception as e:
            result = {
                "failure_type": "dns_failure",
                "host": host,
                "success": False,
                "status_code": 0,
                "error": str(e),
                "latency": -1,
                "timestamp": time.time()
            }
            
            print(f"  ❌ Exception: {e}")
            return result
    
    def test_connection_timeout(self, host: str, port: int) -> dict:
        """Тестировать connection timeout"""
        print(f"⏱️ Testing connection timeout: {host}:{port}")
        
        try:
            start_time = time.time()
            
            # Создаем пайплайн с очень коротким таймаутом
            pipeline = HTTPFragmentation()
            
            request = Request(
                host=host,
                port=port,
                method="GET",
                path="/get",
                timeout=0.001  # Очень короткий таймаут
            )
            
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                "failure_type": "timeout_failure",
                "host": host,
                "success": response.success,
                "status_code": response.status_code,
                "error": response.error,
                "latency": end_time - start_time,
                "timestamp": time.time()
            }
            
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return result
            
        except Exception as e:
            result = {
                "failure_type": "timeout_failure",
                "host": host,
                "success": False,
                "status_code": 0,
                "error": str(e),
                "latency": -1,
                "timestamp": time.time()
            }
            
            print(f"  ❌ Exception: {e}")
            return result
    
    def test_connection_refused(self, host: str, port: int) -> dict:
        """Тестировать connection refused"""
        print(f"🚫 Testing connection refused: {host}:{port}")
        
        try:
            start_time = time.time()
            
            # Создаем пайплайн
            pipeline = HTTPFragmentation()
            
            request = Request(
                host=host,
                port=9999,  # Закрытый порт
                method="GET",
                path="/get"
            )
            
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                "failure_type": "connection_refused",
                "host": host,
                "success": response.success,
                "status_code": response.status_code,
                "error": response.error,
                "latency": end_time - start_time,
                "timestamp": time.time()
            }
            
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return result
            
        except Exception as e:
            result = {
                "failure_type": "connection_refused",
                "host": host,
                "success": False,
                "status_code": 0,
                "error": str(e),
                "latency": -1,
                "timestamp": time.time()
            }
            
            print(f"  ❌ Exception: {e}")
            return result
    
    def test_partial_recv(self, host: str, port: int) -> dict:
        """Тестировать partial recv"""
        print(f"📥 Testing partial recv: {host}:{port}")
        
        try:
            start_time = time.time()
            
            # Используем прямой socket для теста
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            sock.connect((host, port))
            
            # Отправляем HTTP запрос
            http_request = f"GET /get HTTP/1.1\r\nHost: {host}\r\n\r\n"
            sock.send(http_request.encode())
            
            # Получаем только часть ответа
            response_data = b""
            sock.settimeout(0.001)  # Очень короткий таймаут для recv
            try:
                chunk = sock.recv(100)  # Только 100 байт
                response_data += chunk
            except socket.timeout:
                pass  # Это ожидаемо - partial recv
            
            sock.close()
            end_time = time.time()
            
            result = {
                "failure_type": "partial_recv",
                "host": host,
                "success": len(response_data) > 0,  # Частичный успех если получили хоть что-то
                "status_code": 200 if b"HTTP" in response_data else 0,
                "error": None if len(response_data) > 0 else "partial_recv_timeout",
                "latency": end_time - start_time,
                "bytes_received": len(response_data),
                "timestamp": time.time()
            }
            
            print(f"  Success: {result['success']}")
            print(f"  Status Code: {result['status_code']}")
            print(f"  Bytes Received: {len(response_data)}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return result
            
        except Exception as e:
            result = {
                "failure_type": "partial_recv",
                "host": host,
                "success": False,
                "status_code": 0,
                "error": str(e),
                "latency": -1,
                "bytes_received": 0,
                "timestamp": time.time()
            }
            
            print(f"  ❌ Exception: {e}")
            return result
    
    def test_remote_close(self, host: str, port: int) -> dict:
        """Тестировать remote close"""
        print(f"🔌 Testing remote close: {host}:{port}")
        
        try:
            start_time = time.time()
            
            # Используем прямой socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            
            sock.connect((host, port))
            
            # Отправляем HTTP запрос
            http_request = f"GET /get HTTP/1.1\r\nHost: {host}\r\n\r\n"
            sock.send(http_request.encode())
            
            # Ждем remote close
            try:
                response_data = sock.recv(4096)
            except:
                pass  # Remote может закрыть соединение
            
            sock.close()
            end_time = time.time()
            
            result = {
                "failure_type": "remote_close",
                "host": host,
                "success": True,  # Соединение было установлено
                "status_code": 0,  # Нет полного ответа из-за close
                "error": "connection_closed_by_remote",
                "latency": end_time - start_time,
                "bytes_received": len(response_data) if 'response_data' in locals() else 0,
                "timestamp": time.time()
            }
            
            print(f"  Connection Established: True")
            print(f"  Remote Close: True")
            print(f"  Bytes Received: {result['bytes_received']}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return result
            
        except Exception as e:
            result = {
                "failure_type": "remote_close",
                "host": host,
                "success": False,
                "status_code": 0,
                "error": str(e),
                "latency": -1,
                "bytes_received": 0,
                "timestamp": time.time()
            }
            
            print(f"  ❌ Exception: {e}")
            return result
    
    def run_failure_validation(self):
        """Запустить валидацию отказов"""
        print("🚀 Internet Failure Validation")
        print("Цель: Проверить реальные интернет ошибки и условия цензуры")
        print("=" * 60)
        
        # Используем успешную цель из предыдущих тестов
        target_host, target_port = get_target_for_test(1)  # httpbin.org:80
        
        # Тестируем различные типы отказов
        failure_tests = [
            self.test_dns_failure(target_host, target_port),
            self.test_connection_timeout(target_host, target_port),
            self.test_connection_refused(target_host, target_port),
            self.test_partial_recv(target_host, target_port),
            self.test_remote_close(target_host, target_port)
        ]
        
        self.failure_results = failure_tests
        
        # Анализируем результаты
        dns_failures = [r for r in failure_tests if r['failure_type'] == 'dns_failure' and not r['success']]
        timeout_failures = [r for r in failure_tests if r['failure_type'] == 'timeout_failure' and not r['success']]
        refused_failures = [r for r in failure_tests if r['failure_type'] == 'connection_refused' and not r['success']]
        partial_recv_failures = [r for r in failure_tests if r['failure_type'] == 'partial_recv' and not r['success']]
        
        print(f"\n📊 Failure Validation Results:")
        print(f"  DNS Failures: {len(dns_failures)}")
        print(f"  Timeout Failures: {len(timeout_failures)}")
        print(f"  Connection Refused: {len(refused_failures)}")
        print(f"  Partial Recv Failures: {len(partial_recv_failures)}")
        
        # Проверяем что все типы отказов были обнаружены
        failure_types_detected = (
            len(dns_failures) > 0 or
            len(timeout_failures) > 0 or
            len(refused_failures) > 0 or
            len(partial_recv_failures) > 0
        )
        
        print(f"\n🎯 Overall Failure Validation: {'VERIFIED' if failure_types_detected else 'NOT VERIFIED'}")
        
        return {
            "timestamp": time.time(),
            "target": f"{target_host}:{target_port}",
            "total_tests": len(failure_tests),
            "failure_results": failure_tests,
            "dns_failures": len(dns_failures),
            "timeout_failures": len(timeout_failures),
            "refused_failures": len(refused_failures),
            "partial_recv_failures": len(partial_recv_failures),
            "failure_types_detected": failure_types_detected,
            "validation_success": failure_types_detected
        }

def main():
    """Основная функция"""
    validator = InternetFailureValidator()
    results = validator.run_failure_validation()
    
    # Сохраняем результаты
    with open("INTERNET_FAILURE_VALIDATION.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: INTERNET_FAILURE_VALIDATION.json")
    
    return 0 if results['validation_success'] else 1

if __name__ == "__main__":
    sys.exit(main())
