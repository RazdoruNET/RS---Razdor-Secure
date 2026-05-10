#!/usr/bin/env python3
"""
Truth Mode Audit - Доказательство реальных сценариев ошибок
Проверяем что failure scenarios действительно возвращают success=False
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TruthModeAuditor:
    """Auditor для Truth Mode проверки"""
    
    def __init__(self):
        self.test_results = []
        
    def test_dns_failure(self):
        """Тест DNS failure"""
        print("\n🌐 Testing DNS Failure Scenario")
        print("=" * 50)
        
        try:
            from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
            from super_dpi_combiner.core.contracts import Request
            
            pipeline = HTTPFragmentation()
            
            # Запрос к несуществующему домену
            request = Request(
                host="nonexistent-domain-12345.invalid",
                port=80,
                method="GET"
            )
            
            print(f"📤 Testing DNS failure with: {request.host}")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                'test': 'DNS_FAILURE',
                'success': response.success,
                'error': response.error,
                'status_code': response.status_code,
                'latency': end_time - start_time
            }
            
            self.test_results.append(result)
            
            print(f"📊 DNS Failure Result:")
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            # Проверяем Truth Mode
            if not response.success and response.error:
                print("  ✅ Truth Mode VERIFIED - DNS failure returns success=False")
                result['truth_mode'] = 'VERIFIED'
            else:
                print("  ❌ Truth Mode FAILED - DNS failure should return success=False")
                result['truth_mode'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.test_results.append({
                'test': 'DNS_FAILURE',
                'success': None,
                'error': str(e),
                'truth_mode': 'ERROR'
            })
    
    def test_connection_refused(self):
        """Тест connection refused"""
        print("\n🚫 Testing Connection Refused Scenario")
        print("=" * 50)
        
        try:
            from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
            from super_dpi_combiner.core.contracts import Request
            
            pipeline = HTTPFragmentation()
            
            # Запрос к localhost на закрытом порту
            request = Request(
                host="127.0.0.1",
                port=9999,  # Закрытый порт
                method="GET"
            )
            
            print(f"📤 Testing connection refused with: {request.host}:{request.port}")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                'test': 'CONNECTION_REFUSED',
                'success': response.success,
                'error': response.error,
                'status_code': response.status_code,
                'latency': end_time - start_time
            }
            
            self.test_results.append(result)
            
            print(f"📊 Connection Refused Result:")
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            # Проверяем Truth Mode
            if not response.success and response.error:
                print("  ✅ Truth Mode VERIFIED - Connection refused returns success=False")
                result['truth_mode'] = 'VERIFIED'
            else:
                print("  ❌ Truth Mode FAILED - Connection refused should return success=False")
                result['truth_mode'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.test_results.append({
                'test': 'CONNECTION_REFUSED',
                'success': None,
                'error': str(e),
                'truth_mode': 'ERROR'
            })
    
    def test_timeout_scenario(self):
        """Тест timeout scenario"""
        print("\n⏱️ Testing Timeout Scenario")
        print("=" * 50)
        
        try:
            from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
            from super_dpi_combiner.core.contracts import Request
            
            pipeline = HTTPFragmentation()
            
            # Запрос с очень коротким таймаутом к медленному серверу
            request = Request(
                host="httpbin.org",
                port=80,
                method="GET",
                timeout=0.001  # Очень короткий таймаут
            )
            
            print(f"📤 Testing timeout with: {request.host}:{request.port} (timeout: {request.timeout}s)")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                'test': 'TIMEOUT',
                'success': response.success,
                'error': response.error,
                'status_code': response.status_code,
                'latency': end_time - start_time
            }
            
            self.test_results.append(result)
            
            print(f"📊 Timeout Result:")
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            # Проверяем Truth Mode
            if not response.success and response.error:
                print("  ✅ Truth Mode VERIFIED - Timeout returns success=False")
                result['truth_mode'] = 'VERIFIED'
            else:
                print("  ❌ Truth Mode FAILED - Timeout should return success=False")
                result['truth_mode'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.test_results.append({
                'test': 'TIMEOUT',
                'success': None,
                'error': str(e),
                'truth_mode': 'ERROR'
            })
    
    def test_echo_pipeline_success(self):
        """Тест Echo pipeline для проверки что success не подделывается"""
        print("\n🔊 Testing Echo Pipeline Success Scenario")
        print("=" * 50)
        
        try:
            from super_dpi_combiner.pipelines.echo import Echo
            from super_dpi_combiner.core.contracts import Request
            
            pipeline = Echo()
            
            # Запрос к Echo
            request = Request(
                host="test.example.com",
                port=80,
                method="GET"
            )
            
            print(f"📤 Testing Echo pipeline with: {request.host}:{request.port}")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            result = {
                'test': 'ECHO_SUCCESS',
                'success': response.success,
                'error': response.error,
                'status_code': response.status_code,
                'latency': end_time - start_time
            }
            
            self.test_results.append(result)
            
            print(f"📊 Echo Result:")
            print(f"  Success: {response.success}")
            print(f"  Error: {response.error}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Data: {response.data}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            # Echo всегда должен возвращать success=True
            if response.success and response.status_code == 200:
                print("  ✅ Echo pipeline works correctly - returns success=True")
                result['truth_mode'] = 'VERIFIED'
            else:
                print("  ❌ Echo pipeline failed - should return success=True")
                result['truth_mode'] = 'FAILED'
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            self.test_results.append({
                'test': 'ECHO_SUCCESS',
                'success': None,
                'error': str(e),
                'truth_mode': 'ERROR'
            })
    
    def run_all_tests(self):
        """Запустить все тесты Truth Mode"""
        print("🚀 Truth Mode Audit v2")
        print("Цель: Доказать что failure scenarios возвращают success=False")
        print("Метод: Real failure scenarios testing")
        
        # Запускаем все тесты
        self.test_dns_failure()
        self.test_connection_refused()
        self.test_timeout_scenario()
        self.test_echo_pipeline_success()
    
    def analyze_results(self):
        """Анализировать результаты тестов"""
        print("\n📈 Truth Mode Analysis")
        print("=" * 50)
        
        verified_count = 0
        failed_count = 0
        error_count = 0
        
        for result in self.test_results:
            if result.get('truth_mode') == 'VERIFIED':
                verified_count += 1
                print(f"✅ {result['test']}: VERIFIED")
            elif result.get('truth_mode') == 'FAILED':
                failed_count += 1
                print(f"❌ {result['test']}: FAILED")
            else:
                error_count += 1
                print(f"⚠️ {result['test']}: ERROR")
        
        print(f"\n📊 Truth Mode Summary:")
        print(f"  VERIFIED: {verified_count}")
        print(f"  FAILED: {failed_count}")
        print(f"  ERROR: {error_count}")
        print(f"  Total: {len(self.test_results)}")
        
        return {
            'verified': verified_count,
            'failed': failed_count,
            'error': error_count,
            'total': len(self.test_results)
        }

def write_truth_mode_report(auditor):
    """Записать отчёт о Truth Mode"""
    analysis = auditor.analyze_results()
    
    report = f"""# TRUTH_MODE_AUDIT.md

## Truth Mode Audit Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Failure Scenario Tests

### DNS Failure Test
- Success: {next((r['success'] for r in auditor.test_results if r['test'] == 'DNS_FAILURE'), 'N/A')}
- Error: {next((r['error'] for r in auditor.test_results if r['test'] == 'DNS_FAILURE'), 'N/A')}
- Truth Mode: {next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'DNS_FAILURE'), 'N/A')}

### Connection Refused Test
- Success: {next((r['success'] for r in auditor.test_results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}
- Error: {next((r['error'] for r in auditor.test_results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}
- Truth Mode: {next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'CONNECTION_REFUSED'), 'N/A')}

### Timeout Test
- Success: {next((r['success'] for r in auditor.test_results if r['test'] == 'TIMEOUT'), 'N/A')}
- Error: {next((r['error'] for r in auditor.test_results if r['test'] == 'TIMEOUT'), 'N/A')}
- Truth Mode: {next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'TIMEOUT'), 'N/A')}

### Echo Success Test
- Success: {next((r['success'] for r in auditor.test_results if r['test'] == 'ECHO_SUCCESS'), 'N/A')}
- Error: {next((r['error'] for r in auditor.test_results if r['test'] == 'ECHO_SUCCESS'), 'N/A')}
- Truth Mode: {next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'ECHO_SUCCESS'), 'N/A')}

## Verification Results

### Truth Mode Status
- DNS Failure: {'VERIFIED' if next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'DNS_FAILURE'), 'N/A') == 'VERIFIED' else 'NOT VERIFIED'}
- Connection Refused: {'VERIFIED' if next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'CONNECTION_REFUSED'), 'N/A') == 'VERIFIED' else 'NOT VERIFIED'}
- Timeout: {'VERIFIED' if next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'TIMEOUT'), 'N/A') == 'VERIFIED' else 'NOT VERIFIED'}
- Echo Success: {'VERIFIED' if next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'ECHO_SUCCESS'), 'N/A') == 'VERIFIED' else 'NOT VERIFIED'}

### Summary
- Tests Verified: {analysis['verified']}
- Tests Failed: {analysis['failed']}
- Tests Error: {analysis['error']}
- Total Tests: {analysis['total']}

## Final Classification

### Truth Mode Integrity
- Failure scenarios return success=False: {'VERIFIED' if analysis['verified'] >= 3 else 'NOT VERIFIED'}
- No fake success responses: {'VERIFIED' if analysis['failed'] == 0 else 'NOT VERIFIED'}
- Exceptions not swallowed: {'VERIFIED' if analysis['error'] == 0 else 'NOT VERIFIED'}

### Component Status
- HTTPFragmentation: {'VERIFIED' if next((r['truth_mode'] for r in auditor.test_results if r['test'] and 'FRAG' in r['test']), 'N/A') == 'VERIFIED' else 'NOT VERIFIED'}
- Echo: {'VERIFIED' if next((r['truth_mode'] for r in auditor.test_results if r['test'] == 'ECHO_SUCCESS'), 'N/A') == 'VERIFIED' else 'NOT VERIFIED'}

## Final Classification
TRUTH_MODE: {'VERIFIED' if analysis['verified'] >= 3 and analysis['failed'] == 0 else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/TRUTH_MODE_AUDIT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 Truth Mode audit report written to: TRUTH_MODE_AUDIT.md")

def main():
    """Основная функция аудита"""
    auditor = TruthModeAuditor()
    auditor.run_all_tests()
    write_truth_mode_report(auditor)
    print("\n✅ Truth Mode Audit завершён")

if __name__ == "__main__":
    main()
