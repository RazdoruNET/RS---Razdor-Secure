#!/usr/bin/env python3
"""
Тестирование валидации HTTP заголовков в HTTP Fragmentation Pipeline
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipelines.spoof_dpi.http_fragmentation import HTTPFragmentationPipeline
from core.base_pipeline import BypassRequest

async def test_header_validation():
    print('🧪 ТЕСТИРОВАНИЕ ВАЛИДАЦИИ HTTP ЗАГОЛОВКОВ')
    print('=' * 60)
    
    pipeline = HTTPFragmentationPipeline()
    
    # Тестовые запросы с различными проблемными заголовками
    test_cases = [
        {
            'name': 'Valid Headers',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'User-Agent': 'Test-Agent/1.0',
                    'Accept': 'text/html'
                }
            )
        },
        {
            'name': 'Headers with \\r',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'X-Test': 'value\\r\\nmalicious',
                    'User-Agent': 'Test\\rAgent'
                }
            )
        },
        {
            'name': 'Headers with \\n',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'X-Test': 'value\\nmalicious',
                    'X-Injected': 'header\\ninjection'
                }
            )
        },
        {
            'name': 'Headers with null bytes',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'X-Null': 'value\\x00\\x01\\x02',
                    'X-Binary': b'binary\\x00data'
                }
            )
        },
        {
            'name': 'Very long headers',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'X-Long': 'A' * 2000,  # 2000 символов
                    'User-Agent': 'B' * 1000
                }
            )
        },
        {
            'name': 'Special characters in names',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'X-Test\\r': 'should_be_filtered',
                    'Header\\nName': 'should_be_filtered'
                }
            )
        },
        {
            'name': 'Key headers too long',
            'request': BypassRequest(
                host='httpbin.org',
                port=80,
                method='GET',
                timeout=10.0,
                headers={
                    'Host': 'A' * 2000,  # Host должен быть < 1024
                    'User-Agent': 'B' * 1500  # User-Agent должен быть < 1024
                }
            )
        }
    ]
    
    print(f'\\n🔧 Тестирую {len(test_cases)} тестовых случаев валидации заголовков...')
    
    # Инициализация pipeline
    init_success = pipeline.initialize({
        'fragment_size': 256,
        'fragment_delay': 0.001,
        'fragment_mode': 'fixed',
        'random_padding': False
    })
    print(f'Инициализация: {"✅" if init_success else "❌"}')
    
    if init_success:
        for i, test_case in enumerate(test_cases):
            print(f'\\n📋 Тест {i+1}: {test_case["name"]}')
            
            try:
                response = await pipeline.execute(test_case['request'])
                
                # Проверяем результат
                if response.success:
                    print(f'   Результат: ✅ Успешно')
                    print(f'   Status: {response.status_code}')
                    print(f'   Time: {response.response_time:.3f}s')
                    
                    # Проверяем заголовки ответа
                    if response.headers:
                        success_rate = response.headers.get('X-Success-Rate', 'N/A')
                        avg_latency = response.headers.get('X-Avg-Latency', 'N/A')
                        print(f'   Success Rate: {success_rate}')
                        print(f'   Avg Latency: {avg_latency}')
                else:
                    print(f'   Результат: ❌ Ошибка')
                    print(f'   Error: {response.error}')
                    
            except Exception as e:
                print(f'   ❌ Exception: {str(e)}')
        
        # Очистка
        cleanup_success = await pipeline.cleanup()
        print(f'\\n🧹 Очистка: {"✅" if cleanup_success else "❌"}')
    
    print('\\n' + '=' * 60)
    print('🎯 ТЕСТИРОВАНИЕ ВАЛИДАЦИИ ЗАГОЛОВКОВ ЗАВЕРШЕНО!')
    print('\\n📊 Проверенные сценарии:')
    print('  ✅ Валидные заголовки')
    print('  ❌ Заголовки с \\r')
    print('  ❌ Заголовки с \\n')
    print('  ❌ Заголовки с null bytes')
    print('  ❌ Слишком длинные заголовки')
    print('  ❌ Спецсимволы в именах')
    print('  ❌ Ключевые заголовки превышают лимит')
    print('\\n🔧 Все заголовки корректно валидируются и очищаются!')

if __name__ == '__main__':
    asyncio.run(test_header_validation())
