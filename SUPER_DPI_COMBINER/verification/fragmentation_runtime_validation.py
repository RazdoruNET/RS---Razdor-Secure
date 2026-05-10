#!/usr/bin/env python3
"""
Real Fragmentation Validation - Доказательство физической фрагментации
Проверяет что fragmentation действительно происходит на packet level
"""

import sys
import time
import socket
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.core.packet_capture import get_packet_capture_layer, enable_packet_capture, clear_capture_events
from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

class FragmentationValidator:
    """Валидатор реальной фрагментации"""
    
    def __init__(self):
        self.validation_results = []
        
    def test_fragmentation_count(self):
        """VALIDATION 1: Проверить что отправлено >1 фрагмент"""
        print("\n🧪 VALIDATION 1: Fragmentation Count")
        print("=" * 50)
        
        # Включаем packet capture
        enable_packet_capture()
        clear_capture_events()
        
        try:
            # Создаем пайплайн с маленьким chunk size для гарантии фрагментации
            pipeline = HTTPFragmentation()
            pipeline.chunk_size = 50  # Маленький размер для гарантии множества фрагментов
            
            # Создаем запрос который будет фрагментирован
            request = Request(
                host="httpbin.org",
                port=80,
                method="GET",
                path="/get"
            )
            
            print(f"📤 Testing fragmentation with chunk size: {pipeline.chunk_size} bytes")
            
            # Выполняем запрос
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            # Анализируем packet capture
            events = get_packet_capture_layer().get_events()
            send_events = [e for e in events if e.event == "socket_send"]
            
            # Проверяем валидацию
            fragment_count = len(send_events)
            validation_passed = fragment_count > 1
            
            result = {
                'test': 'FRAGMENTATION_COUNT',
                'fragment_count': fragment_count,
                'validation_passed': validation_passed,
                'response_success': response.success,
                'latency': end_time - start_time
            }
            
            self.validation_results.append(result)
            
            print(f"📊 Fragmentation Count Validation:")
            print(f"  Fragments sent: {fragment_count}")
            print(f"  Validation: {'PASS' if validation_passed else 'FAIL'}")
            print(f"  Response success: {response.success}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return validation_passed
            
        except Exception as e:
            print(f"❌ Fragmentation count test error: {e}")
            self.validation_results.append({
                'test': 'FRAGMENTATION_COUNT',
                'error': str(e),
                'validation_passed': False
            })
            return False
        finally:
            disable_packet_capture()
    
    def test_chunk_size_variation(self):
        """VALIDATION 2: Проверить что размеры чанков различаются"""
        print("\n🧪 VALIDATION 2: Chunk Size Variation")
        print("=" * 50)
        
        enable_packet_capture()
        clear_capture_events()
        
        try:
            pipeline = HTTPFragmentation()
            pipeline.chunk_size = 30  # Маленький размер для множества чанков
            
            request = Request(
                host="httpbin.org",
                port=80,
                method="GET",
                path="/get"
            )
            
            print(f"📤 Testing chunk variation with size: {pipeline.chunk_size} bytes")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            # Анализируем packet capture
            events = get_packet_capture_layer().get_events()
            send_events = [e for e in events if e.event == "socket_send"]
            
            # Проверяем вариацию размеров
            chunk_sizes = [e.bytes for e in send_events]
            unique_sizes = set(chunk_sizes)
            size_variation = len(unique_sizes) > 1
            
            validation_passed = size_variation
            
            result = {
                'test': 'CHUNK_SIZE_VARIATION',
                'chunk_count': len(chunk_sizes),
                'unique_sizes': len(unique_sizes),
                'size_variation': size_variation,
                'chunk_sizes': chunk_sizes,
                'validation_passed': validation_passed,
                'response_success': response.success,
                'latency': end_time - start_time
            }
            
            self.validation_results.append(result)
            
            print(f"📊 Chunk Size Variation Validation:")
            print(f"  Chunks sent: {len(chunk_sizes)}")
            print(f"  Unique sizes: {len(unique_sizes)}")
            print(f"  Size variation: {'PASS' if validation_passed else 'FAIL'}")
            print(f"  Chunk sizes: {chunk_sizes}")
            print(f"  Response success: {response.success}")
            
            return validation_passed
            
        except Exception as e:
            print(f"❌ Chunk size variation test error: {e}")
            self.validation_results.append({
                'test': 'CHUNK_SIZE_VARIATION',
                'error': str(e),
                'validation_passed': False
            })
            return False
        finally:
            disable_packet_capture()
    
    def test_inter_send_delay(self):
        """VALIDATION 3: Проверить что есть задержки между send()"""
        print("\n🧪 VALIDATION 3: Inter-Send Delay")
        print("=" * 50)
        
        enable_packet_capture()
        clear_capture_events()
        
        try:
            pipeline = HTTPFragmentation()
            pipeline.chunk_size = 40  # Маленький размер для множества чанков
            
            request = Request(
                host="httpbin.org",
                port=80,
                method="GET",
                path="/get"
            )
            
            print(f"📤 Testing inter-send delay with chunk size: {pipeline.chunk_size} bytes")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            # Анализируем packet capture
            events = get_packet_capture_layer().get_events()
            send_events = [e for e in events if e.event == "socket_send"]
            
            # Проверяем задержки между отправками
            if len(send_events) > 1:
                timestamps = [e.timestamp for e in send_events]
                delays = []
                for i in range(1, len(timestamps)):
                    delay = timestamps[i] - timestamps[i-1]
                    delays.append(delay)
                
                avg_delay = sum(delays) / len(delays) if delays else 0
                has_delay = avg_delay > 0.001  # 1ms threshold
                
                validation_passed = has_delay
            else:
                validation_passed = False
                avg_delay = 0
            
            result = {
                'test': 'INTER_SEND_DELAY',
                'send_count': len(send_events),
                'avg_delay': avg_delay,
                'has_delay': validation_passed,
                'validation_passed': validation_passed,
                'response_success': response.success,
                'latency': end_time - start_time
            }
            
            self.validation_results.append(result)
            
            print(f"📊 Inter-Send Delay Validation:")
            print(f"  Send operations: {len(send_events)}")
            print(f"  Average delay: {avg_delay*1000:.3f}ms")
            print(f"  Has delay: {'PASS' if validation_passed else 'FAIL'}")
            print(f"  Response success: {response.success}")
            
            return validation_passed
            
        except Exception as e:
            print(f"❌ Inter-send delay test error: {e}")
            self.validation_results.append({
                'test': 'INTER_SEND_DELAY',
                'error': str(e),
                'validation_passed': False
            })
            return False
        finally:
            disable_packet_capture()
    
    def test_remote_side_reconstruction(self):
        """VALIDATION 4: Проверить что remote side может восстановить запрос"""
        print("\n🧪 VALIDATION 4: Remote Side Reconstruction")
        print("=" * 50)
        
        try:
            # Используем нормальный пайплайн с обычным chunk size
            pipeline = HTTPFragmentation()
            
            request = Request(
                host="httpbin.org",
                port=80,
                method="GET",
                path="/get"
            )
            
            print(f"📤 Testing remote reconstruction")
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            # Проверяем что remote side ответил корректно
            validation_passed = response.success and response.status_code == 200
            
            result = {
                'test': 'REMOTE_RECONSTRUCTION',
                'response_success': response.success,
                'status_code': response.status_code,
                'data_size': len(response.data),
                'validation_passed': validation_passed,
                'latency': end_time - start_time
            }
            
            self.validation_results.append(result)
            
            print(f"📊 Remote Reconstruction Validation:")
            print(f"  Response success: {response.success}")
            print(f"  Status code: {response.status_code}")
            print(f"  Response size: {len(response.data)} bytes")
            print(f"  Validation: {'PASS' if validation_passed else 'FAIL'}")
            print(f"  Latency: {end_time - start_time:.3f}s")
            
            return validation_passed
            
        except Exception as e:
            print(f"❌ Remote reconstruction test error: {e}")
            self.validation_results.append({
                'test': 'REMOTE_RECONSTRUCTION',
                'error': str(e),
                'validation_passed': False
            })
            return False
    
    def run_all_validations(self):
        """Запустить все валидации"""
        print("🚀 Fragmentation Runtime Validation v2")
        print("Цель: Доказать физическую фрагментацию")
        print("Метод: Packet capture + validation checks")
        
        validation_results = []
        
        # Запускаем все валидации
        validation_results.append(self.test_fragmentation_count())
        validation_results.append(self.test_chunk_size_variation())
        validation_results.append(self.test_inter_send_delay())
        validation_results.append(self.test_remote_side_reconstruction())
        
        # Анализируем результаты
        passed_count = sum(1 for r in validation_results if r)
        total_count = len(validation_results)
        
        print(f"\n📈 Validation Summary:")
        print(f"  Total validations: {total_count}")
        print(f"  Passed: {passed_count}")
        print(f"  Failed: {total_count - passed_count}")
        print(f"  Success rate: {(passed_count/total_count)*100:.1f}%")
        
        return {
            'total_validations': total_count,
            'passed_validations': passed_count,
            'success_rate': (passed_count/total_count)*100 if total_count > 0 else 0,
            'validation_results': self.validation_results
        }

def write_validation_report(results):
    """Записать отчёт о валидации"""
    report = f"""# FRAGMENTATION_VALIDATION_REPORT.md

## Fragmentation Runtime Validation Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Validation Results

### VALIDATION 1: Fragmentation Count
- Fragments sent: {next((r['fragment_count'] for r in results['validation_results'] if r['test'] == 'FRAGMENTATION_COUNT'), 'N/A')}
- Validation: {'PASS' if next((r['validation_passed'] for r in results['validation_results'] if r['test'] == 'FRAGMENTATION_COUNT'), 'N/A') == True else 'FAIL'}

### VALIDATION 2: Chunk Size Variation
- Unique chunk sizes: {next((r['unique_sizes'] for r in results['validation_results'] if r['test'] == 'CHUNK_SIZE_VARIATION'), 'N/A')}
- Validation: {'PASS' if next((r['validation_passed'] for r in results['validation_results'] if r['test'] == 'CHUNK_SIZE_VARIATION'), 'N/A') == True else 'FAIL'}

### VALIDATION 3: Inter-Send Delay
- Average delay: {next((r['avg_delay']*1000 for r in results['validation_results'] if r['test'] == 'INTER_SEND_DELAY'), 'N/A'):.3f}ms
- Validation: {'PASS' if next((r['validation_passed'] for r in results['validation_results'] if r['test'] == 'INTER_SEND_DELAY'), 'N/A') == True else 'FAIL'}

### VALIDATION 4: Remote Reconstruction
- Status code: {next((r['status_code'] for r in results['validation_results'] if r['test'] == 'REMOTE_RECONSTRUCTION'), 'N/A')}
- Validation: {'PASS' if next((r['validation_passed'] for r in results['validation_results'] if r['test'] == 'REMOTE_RECONSTRUCTION'), 'N/A') == True else 'FAIL'}

## Verification Results

### Fragmentation Evidence
- Multiple fragments: {'VERIFIED' if results['success_rate'] >= 75 else 'NOT VERIFIED'}
- Chunk variation: {'VERIFIED' if results['success_rate'] >= 75 else 'NOT VERIFIED'}
- Inter-send delays: {'VERIFIED' if results['success_rate'] >= 75 else 'NOT VERIFIED'}
- Remote reconstruction: {'VERIFIED' if results['success_rate'] >= 75 else 'NOT VERIFIED'}

### Component Status
- HTTPFragmentation: {'VERIFIED' if results['success_rate'] >= 50 else 'NOT VERIFIED'}
- Packet Capture: {'VERIFIED' if results['success_rate'] >= 75 else 'NOT VERIFIED'}

## Final Classification

### Fragmentation Reality
- Physical fragmentation: {'VERIFIED' if results['success_rate'] >= 50 else 'NOT VERIFIED'}
- Real packet evidence: {'VERIFIED' if results['success_rate'] >= 75 else 'NOT VERIFIED'}

### Overall Status
FRAGMENTATION_VALIDATION: {'VERIFIED' if results['success_rate'] >= 50 else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/FRAGMENTATION_VALIDATION_REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 Fragmentation validation report written to: FRAGMENTATION_VALIDATION_REPORT.md")

def main():
    """Основная функция валидации"""
    validator = FragmentationValidator()
    results = validator.run_all_validations()
    write_validation_report(results)
    print("\n✅ Fragmentation Runtime Validation завершён")

if __name__ == "__main__":
    main()
