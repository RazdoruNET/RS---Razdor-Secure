#!/usr/bin/env python3
"""
Remote Response Validation - Проверка ответов от реальных хостов
"""

import sys
import time
import json
import socket
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verification.internet_targets import get_target_for_test, get_scenario_for_test
from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

class RemoteResponseValidator:
    """Валидатор ответов от реальных хостов"""
    
    def __init__(self):
        self.validation_results = []
        
    def validate_response_structure(self, host: str, response_data: bytes) -> dict:
        """Валидировать структуру HTTP ответа"""
        try:
            response_text = response_data.decode('utf-8', errors='ignore')
            
            # Проверяем базовую HTTP структуру
            if not response_text:
                return {
                    "valid_http": False,
                    "reason": "empty_response"
                }
            
            # Ищем HTTP status line
            lines = response_text.split('\r\n')
            if not lines:
                return {
                    "valid_http": False,
                    "reason": "no_lines"
                }
            
            status_line = lines[0]
            if not status_line.startswith('HTTP/'):
                return {
                    "valid_http": False,
                    "reason": "no_http_status"
                }
            
            # Парсим status line
            parts = status_line.split(' ')
            if len(parts) < 2:
                return {
                    "valid_http": False,
                    "reason": "invalid_status_line"
                }
            
            try:
                status_code = int(parts[1])
            except ValueError:
                return {
                    "valid_http": False,
                    "reason": "invalid_status_code"
                }
            
            # Проверяем что remote host реально отвечает
            validation = {
                "valid_http": True,
                "status_code": status_code,
                "response_size": len(response_data),
                "has_headers": len(lines) > 1,
                "has_body": '\r\n\r\n' in response_text or '\r\n\r\n' in response_text,
                "host_responsive": True
            }
            
            print(f"  HTTP Status: {status_code}")
            print(f"  Response Size: {len(response_data)} bytes")
            print(f"  Has Headers: {validation['has_headers']}")
            print(f"  Has Body: {validation['has_body']}")
            
            return validation
            
        except Exception as e:
            return {
                "valid_http": False,
                "reason": f"parse_error: {e}"
            }
    
    def test_remote_responses(self):
        """Тестировать ответы от реальных хостов"""
        print("🚀 Remote Response Validation")
        print("Цель: Проверить что remote host реально отвечает")
        print("Недостаточно: TCP ACK. Нужно: HTTP/1.1 200 OK")
        print("=" * 60)
        
        # Тестируем несколько целей
        test_targets = [
            get_target_for_test(1),  # httpbin.org:80
            get_target_for_test(2),  # neverssl.com:80
            get_target_for_test(0),  # example.com:80
        ]
        
        for i, (host, port) in enumerate(test_targets):
            print(f"\n🎯 Testing Target {i+1}/3: {host}:{port}")
            print("-" * 40)
            
            # Тестируем разные сценарии
            for j, scenario in enumerate([get_scenario_for_test(k) for k in range(3)]):
                print(f"\n📤 Scenario {j+1}: {scenario['name']}")
                print(f"  Description: {scenario['description']}")
                print(f"  Chunk size: {scenario['chunk_size']}")
                
                try:
                    # Создаем пайплайн
                    pipeline = HTTPFragmentation()
                    pipeline.chunk_size = scenario['chunk_size']
                    
                    # Создаем запрос
                    request = Request(
                        host=host,
                        port=port,
                        method="GET",
                        path="/get"
                    )
                    
                    # Выполняем запрос
                    start_time = time.time()
                    response = pipeline.execute(request)
                    end_time = time.time()
                    
                    # Валидируем ответ
                    response_validation = self.validate_response_structure(host, response.data)
                    
                    result = {
                        "target": f"{host}:{port}",
                        "scenario": scenario['name'],
                        "chunk_size": scenario['chunk_size'],
                        "success": response.success,
                        "status_code": response.status_code,
                        "latency": end_time - start_time,
                        "response_validation": response_validation,
                        "timestamp": time.time()
                    }
                    
                    self.validation_results.append(result)
                    
                    print(f"  Success: {response.success}")
                    print(f"  Status Code: {response.status_code}")
                    print(f"  Latency: {end_time - start_time:.3f}s")
                    print(f"  HTTP Valid: {response_validation['valid_http']}")
                    
                    if not response_validation['valid_http']:
                        print(f"  Validation Error: {response_validation['reason']}")
                    
                except Exception as e:
                    error_result = {
                        "target": f"{host}:{port}",
                        "scenario": scenario['name'],
                        "chunk_size": scenario['chunk_size'],
                        "success": False,
                        "status_code": 0,
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    
                    self.validation_results.append(error_result)
                    print(f"  ❌ Error: {e}")
        
        # Анализируем результаты
        self.analyze_results()
    
    def analyze_results(self):
        """Анализировать результаты валидации"""
        print(f"\n📊 Remote Response Validation Analysis")
        print("=" * 60)
        
        # Считаем статистику
        total_tests = len(self.validation_results)
        successful_tests = len([r for r in self.validation_results if r['success']])
        http_valid_tests = len([r for r in self.validation_results if r.get('response_validation', {}).get('valid_http', False)])
        
        print(f"Total tests: {total_tests}")
        print(f"Successful tests: {successful_tests}")
        print(f"HTTP valid responses: {http_valid_tests}")
        
        # Анализируем по целям
        targets = {}
        for result in self.validation_results:
            target = result['target']
            if target not in targets:
                targets[target] = {
                    'total': 0,
                    'successful': 0,
                    'http_valid': 0
                }
            
            targets[target]['total'] += 1
            if result['success']:
                targets[target]['successful'] += 1
            if result.get('response_validation', {}).get('valid_http', False):
                targets[target]['http_valid'] += 1
        
        print(f"\n📈 Results by Target:")
        for target, stats in targets.items():
            success_rate = (stats['successful'] / stats['total']) * 100 if stats['total'] > 0 else 0
            http_valid_rate = (stats['http_valid'] / stats['total']) * 100 if stats['total'] > 0 else 0
            
            print(f"  {target}:")
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    HTTP Valid Rate: {http_valid_rate:.1f}%")
            print(f"    Total Tests: {stats['total']}")
        
        # Определяем успешность
        overall_success = (
            successful_tests > 0 and  # Хотя бы один успешный тест
            http_valid_tests > 0 and  # Хотя бы один валидный HTTP ответ
            total_tests >= 3  # Минимум 3 теста
        )
        
        print(f"\n🎯 Overall Validation: {'VERIFIED' if overall_success else 'NOT VERIFIED'}")
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'http_valid_tests': http_valid_tests,
            'targets': targets,
            'overall_success': overall_success
        }

def main():
    """Основная функция"""
    validator = RemoteResponseValidator()
    results = validator.test_remote_responses()
    
    # Сохраняем результаты
    with open("REMOTE_RESPONSE_VALIDATION.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: REMOTE_RESPONSE_VALIDATION.json")
    
    return 0 if results and results.get('overall_success', False) else 1

if __name__ == "__main__":
    sys.exit(main())
