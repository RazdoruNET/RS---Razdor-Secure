#!/usr/bin/env python3
"""
Тестирование исправленного HTTP Fragmentation Pipeline
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipelines.spoof_dpi.http_fragmentation import HTTPFragmentationPipeline
from core.base_pipeline import BypassRequest

async def test_fixed_pipeline():
    print('🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО HTTP FRAGMENTATION')
    print('=' * 60)
    
    pipeline = HTTPFragmentationPipeline()
    
    # Тестовые запросы
    test_requests = [
        BypassRequest(host='httpbin.org', port=80, method='GET', timeout=10.0),
        BypassRequest(host='httpbin.org', port=443, method='GET', timeout=10.0),
        BypassRequest(host='google.com', port=443, method='GET', timeout=10.0)
    ]
    
    # Тест конфигураций
    test_configs = [
        {'fragment_size': 128, 'fragment_delay': 0.001, 'random_padding': False},
        {'fragment_size': 256, 'fragment_delay': 0.002, 'random_padding': False},
        {'fragment_size': 512, 'fragment_delay': 0.005, 'random_padding': False}
    ]
    
    print(f'\n🔧 Тестирую {len(test_configs)} конфигураций с {len(test_requests)} запросами...')
    
    for i, config in enumerate(test_configs):
        print(f'\n📋 Конфигурация {i+1}: fragment_size={config["fragment_size"]}, delay={config["fragment_delay"]}')
        
        # Инициализация
        init_success = pipeline.initialize(config)
        print(f'   Инициализация: {"✅" if init_success else "❌"}')
        
        if init_success:
            for j, request in enumerate(test_requests):
                try:
                    print(f'   🔄 Запрос {j+1}: {request.host}:{request.port}')
                    response = await pipeline.execute(request)
                    
                    success = response.success and response.status_code in [200, 201, 202, 301, 302]
                    print(f'      Результат: {"✅" if success else "❌"} ({response.status_code}, {response.response_time:.3f}s)')
                    
                    if response.data and len(response.data) > 0:
                        # Проверяем HTTP status в ответе
                        status_line = response.data.split(b'\r\n', 1)[0]
                        print(f'      Status line: {status_line.decode("utf-8", errors="ignore")}')
                    
                except Exception as e:
                    print(f'      ❌ Ошибка: {str(e)}')
            
            # Очистка
            cleanup_success = await pipeline.cleanup()
            print(f'   Очистка: {"✅" if cleanup_success else "❌"}')
    
    print('\n' + '=' * 60)
    print('🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!')
    print('\n📊 Ключевые улучшения:')
    print('  ✅ Удален padding ломающий HTTP')
    print('  ✅ Добавлено полноценное чтение response')
    print('  ✅ Добавлены timeout wrappers')
    print('  ✅ Переведено на dataclass конфигурация')
    print('  ✅ Использован logger вместо print')
    print('  ✅ Добавлена поддержка TLS для HTTPS')

if __name__ == '__main__':
    asyncio.run(test_fixed_pipeline())
