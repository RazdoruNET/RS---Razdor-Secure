#!/usr/bin/env python3
"""
Verify Failure Reality - Проверка реальных failure scenarios с исключениями
"""

import sys
import time
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

def test_dns_failure():
    """Тест DNS failure с реальным исключением"""
    print("🌐 Testing DNS Failure Reality")
    
    pipeline = HTTPFragmentation()
    request = Request(
        host="nonexistent-domain-12345.invalid",
        port=80,
        method="GET"
    )
    
    start_time = time.time()
    response = pipeline.execute(request)
    end_time = time.time()
    
    result = {
        'test': 'DNS_FAILURE',
        'success': response.success,
        'error': response.error,
        'status_code': response.status_code,
        'execution_duration': end_time - start_time,
        'exception_type': None,
        'response_data_size': len(response.data)
    }
    
    # Анализируем ошибку
    if response.error and 'nodename' in response.error:
        result['exception_type'] = 'socket.gaierror'
    elif response.error and 'Name or service not known' in response.error:
        result['exception_type'] = 'socket.gaierror'
    
    print(f"  Success: {response.success}")
    print(f"  Error: {response.error}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Duration: {end_time - start_time:.3f}s")
    print(f"  Exception Type: {result['exception_type']}")
    
    return result

def test_connection_refused():
    """Тест connection refused с реальным исключением"""
    print("\n🚫 Testing Connection Refused Reality")
    
    pipeline = HTTPFragmentation()
    request = Request(
        host="127.0.0.1",
        port=9999,  # Закрытый порт
        method="GET"
    )
    
    start_time = time.time()
    response = pipeline.execute(request)
    end_time = time.time()
    
    result = {
        'test': 'CONNECTION_REFUSED',
        'success': response.success,
        'error': response.error,
        'status_code': response.status_code,
        'execution_duration': end_time - start_time,
        'exception_type': None,
        'response_data_size': len(response.data)
    }
    
    # Анализируем ошибку
    if response.error and 'Connection refused' in response.error:
        result['exception_type'] = 'ConnectionRefusedError'
    elif response.error and '61' in response.error:  # macOS connection refused
        result['exception_type'] = 'ConnectionRefusedError'
    
    print(f"  Success: {response.success}")
    print(f"  Error: {response.error}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Duration: {end_time - start_time:.3f}s")
    print(f"  Exception Type: {result['exception_type']}")
    
    return result

def test_timeout():
    """Тест timeout с реальным исключением"""
    print("\n⏱️ Testing Timeout Reality")
    
    pipeline = HTTPFragmentation()
    request = Request(
        host="httpbin.org",
        port=80,
        method="GET",
        timeout=0.001  # Очень короткий таймаут
    )
    
    start_time = time.time()
    response = pipeline.execute(request)
    end_time = time.time()
    
    result = {
        'test': 'TIMEOUT',
        'success': response.success,
        'error': response.error,
        'status_code': response.status_code,
        'execution_duration': end_time - start_time,
        'exception_type': None,
        'response_data_size': len(response.data)
    }
    
    # Анализируем ошибку
    if response.error and 'timed out' in response.error.lower():
        result['exception_type'] = 'socket.timeout'
    elif response.error and 'timeout' in response.error.lower():
        result['exception_type'] = 'socket.timeout'
    
    print(f"  Success: {response.success}")
    print(f"  Error: {response.error}")
    print(f"  Status Code: {response.status_code}")
    print(f"  Duration: {end_time - start_time:.3f}s")
    print(f"  Exception Type: {result['exception_type']}")
    
    return result

def verify_failure_reality():
    """Проверить реальность failure scenarios"""
    print("🚀 Failure Reality Verification")
    print("Цель: Доказать реальные failure scenarios с исключениями")
    
    results = []
    
    # Выполняем все тесты
    results.append(test_dns_failure())
    results.append(test_connection_refused())
    results.append(test_timeout())
    
    # Анализируем результаты
    print("\n📊 Failure Reality Analysis")
    print("=" * 50)
    
    for result in results:
        test_name = result['test']
        success = result['success']
        has_error = result['error'] is not None
        has_exception_type = result['exception_type'] is not None
        correct_status_code = result['status_code'] == 0
        
        # Проверяем что failure реально обработан
        failure_handled = not success and has_error and correct_status_code
        
        print(f"\n{test_name}:")
        print(f"  Failure Handled: {'YES' if failure_handled else 'NO'}")
        print(f"  Success=False: {'YES' if not success else 'NO'}")
        print(f"  Error Present: {'YES' if has_error else 'NO'}")
        print(f"  Exception Type: {result['exception_type']}")
        print(f"  Status Code=0: {'YES' if correct_status_code else 'NO'}")
        
        result['failure_handled'] = failure_handled
    
    # Считаем статистику
    handled_failures = sum(1 for r in results if r['failure_handled'])
    total_failures = len(results)
    
    print(f"\n📈 Summary:")
    print(f"  Total Failure Tests: {total_failures}")
    print(f"  Handled Failures: {handled_failures}")
    print(f"  Failure Handling Rate: {(handled_failures/total_failures)*100:.1f}%")
    
    return results

def write_failure_reality_report(results):
    """Записать отчёт о failure reality"""
    report = f"""# FAILURE_REALITY_REPORT.md

## Failure Reality Verification Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Failure Scenarios Tested

### DNS Failure
- **Success**: {next((r['success'] for r in results if r['test'] == 'DNS_FAILURE'), 'N/A')}
- **Error**: {next((r['error'] for r in results if r['test'] == 'DNS_FAILURE'), 'N/A')}
- **Exception Type**: {next((r['exception_type'] for r in results if r['test'] == 'DNS_FAILURE'), 'N/A')}
- **Execution Duration**: {next((r['execution_duration'] for r in results if r['test'] == 'DNS_FAILURE'), 'N/A'):.3f}s
- **Failure Handled**: {next((r['failure_handled'] for r in results if r['test'] == 'DNS_FAILURE'), 'N/A')}

### Connection Refused
- **Success**: {next((r['success'] for r in results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}
- **Error**: {next((r['error'] for r in results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}
- **Exception Type**: {next((r['exception_type'] for r in results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}
- **Execution Duration**: {next((r['execution_duration'] for r in results if r['test'] == 'CONNECTION_REFUSED'), 'N/A'):.3f}s
- **Failure Handled**: {next((r['failure_handled'] for r in results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}

### Timeout
- **Success**: {next((r['success'] for r in results if r['test'] == 'TIMEOUT'), 'N/A')}
- **Error**: {next((r['error'] for r in results if r['test'] == 'TIMEOUT'), 'N/A')}
- **Exception Type**: {next((r['exception_type'] for r in results if r['test'] == 'TIMEOUT'), 'N/A')}
- **Execution Duration**: {next((r['execution_duration'] for r in results if r['test'] == 'TIMEOUT'), 'N/A'):.3f}s
- **Failure Handled**: {next((r['failure_handled'] for r in results if r['test'] == 'TIMEOUT'), 'N/A')}

## Verification Results

### Failure Handling Reality
- **DNS Failure**: {'VERIFIED' if next((r['failure_handled'] for r in results if r['test'] == 'DNS_FAILURE'), 'N/A') else 'NOT VERIFIED'}
- **Connection Refused**: {'VERIFIED' if next((r['failure_handled'] for r in results if r['test'] == 'CONNECTION_REFUSED'), 'N/A') else 'NOT VERIFIED'}
- **Timeout**: {'VERIFIED' if next((r['failure_handled'] for r in results if r['test'] == 'TIMEOUT'), 'N/A') else 'NOT VERIFIED'}

### Exception Evidence
- **Real Exceptions**: {'VERIFIED' if all(r['exception_type'] for r in results) else 'NOT VERIFIED'}
- **No Hidden Failures**: {'VERIFIED' if all(not r['success'] for r in results) else 'NOT VERIFIED'}
- **Proper Error Messages**: {'VERIFIED' if all(r['error'] for r in results) else 'NOT VERIFIED'}

## Final Classification

### Failure Reality
- **Truth Mode Compliance**: {'VERIFIED' if sum(1 for r in results if r['failure_handled']) == 3 else 'NOT VERIFIED'}
- **Real Exception Handling**: {'VERIFIED' if all(r['exception_type'] for r in results) else 'NOT VERIFIED'}
- **No Fake Success**: {'VERIFIED' if all(not r['success'] for r in results) else 'NOT VERIFIED'}

### Overall Status
FAILURE_REALITY: {'VERIFIED' if sum(1 for r in results if r['failure_handled']) == 3 else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/FAILURE_REALITY_REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 Failure reality report written to: FAILURE_REALITY_REPORT.md")

def main():
    """Основная функция"""
    results = verify_failure_reality()
    write_failure_reality_report(results)
    print("\n✅ Failure Reality Verification завершён")
    
    # Return exit code based on results
    handled_failures = sum(1 for r in results if r['failure_handled'])
    return 0 if handled_failures == 3 else 1

if __name__ == "__main__":
    sys.exit(main())
