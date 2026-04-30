#!/usr/bin/env python3
"""
Тестовый пример использования нейро-шифратора RSecure
"""

import sys
import os
import time
import json
import numpy as np

# Добавляем путь к модулям RSecure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure'))

from rsecure.modules.defense.neural_encryptor import (
    NeuralEncryptor, 
    NeuralEncryptorManager, 
    NeuralEncryptConfig,
    EncryptionMethod,
    TrafficMimicType
)


def test_basic_encryption():
    """Базовый тест шифрования/дешифрования"""
    print("=== Базовый тест шифрования ===")
    
    # Создание конфигурации
    config = NeuralEncryptConfig(
        method=EncryptionMethod.AUTOENCODER,
        mimic_type=TrafficMimicType.HTTP,
        latent_dim=128,
        sequence_length=64
    )
    
    # Создание шифратора
    encryptor = NeuralEncryptor(config)
    
    # Тестовые данные
    test_data = "Это секретное сообщение для тестирования нейро-шифрования!"
    
    print(f"Оригинал: {test_data}")
    print(f"Длина: {len(test_data)} байт")
    
    # Шифрование
    start_time = time.time()
    encrypted = encryptor.encrypt_data(test_data)
    encrypt_time = time.time() - start_time
    
    print(f"Зашифровано: {len(encrypted)} байт")
    print(f"Время шифрования: {encrypt_time:.4f} сек")
    print(f"Пример зашифрованного: {encrypted[:100].decode('utf-8', errors='ignore')}...")
    
    # Дешифрование
    start_time = time.time()
    decrypted = encryptor.decrypt_data(encrypted)
    decrypt_time = time.time() - start_time
    
    print(f"Расшифровано: {len(decrypted)} байт")
    print(f"Время дешифрования: {decrypt_time:.4f} сек")
    
    # Проверка
    try:
        decrypted_str = decrypted.decode('utf-8')
        success = test_data == decrypted_str
        print(f"Успех: {success}")
        if success:
            print(f"Расшифровано: {decrypted_str}")
        else:
            print(f"Ожидалось: {test_data}")
            print(f"Получено: {decrypted_str}")
    except Exception as e:
        print(f"Ошибка декодирования: {e}")
        success = False
    
    # Статистика
    stats = encryptor.get_stats()
    print(f"Статистика: {json.dumps(stats, indent=2)}")
    
    return success


def test_different_methods():
    """Тест разных методов шифрования"""
    print("\n=== Тест разных методов шифрования ===")
    
    methods = [
        EncryptionMethod.AUTOENCODER,
        EncryptionMethod.VAE,
        EncryptionMethod.TRANSFORMER
    ]
    
    test_data = "Тестовое сообщение для сравнения методов"
    
    results = {}
    
    for method in methods:
        print(f"\nТест метода: {method.value}")
        
        try:
            config = NeuralEncryptConfig(
                method=method,
                mimic_type=TrafficMimicType.HTTP,
                latent_dim=64,
                sequence_length=32
            )
            
            encryptor = NeuralEncryptor(config)
            
            # Тестирование
            test_result = encryptor.test_encryption(test_data)
            results[method.value] = test_result
            
            print(f"  Успех: {test_result.get('success', False)}")
            print(f"  Коэффициент сжатия: {test_result.get('compression_ratio', 0):.2f}")
            
            if test_result.get('error'):
                print(f"  Ошибка: {test_result['error']}")
            
        except Exception as e:
            print(f"  Ошибка метода: {e}")
            results[method.value] = {'success': False, 'error': str(e)}
    
    return results


def test_traffic_mimicry():
    """Тест маскировки под разные типы трафика"""
    print("\n=== Тест маскировки под трафик ===")
    
    mimic_types = [
        TrafficMimicType.HTTP,
        TrafficMimicType.DNS,
        TrafficMimicType.ICMP,
        TrafficMimicType.SSH
    ]
    
    test_data = "Секретные данные для маскировки"
    
    for mimic_type in mimic_types:
        print(f"\nТест маскировки: {mimic_type.value}")
        
        try:
            config = NeuralEncryptConfig(
                method=EncryptionMethod.AUTOENCODER,
                mimic_type=mimic_type,
                latent_dim=64,
                sequence_length=32
            )
            
            encryptor = NeuralEncryptor(config)
            
            # Шифрование
            encrypted = encryptor.encrypt_data(test_data)
            
            print(f"  Оригинал: {test_data}")
            print(f"  Зашифровано: {len(encrypted)} байт")
            print(f"  Пример: {encrypted[:80].decode('utf-8', errors='ignore')}...")
            
            # Дешифрование
            decrypted = encryptor.decrypt_data(encrypted)
            try:
                decrypted_str = decrypted.decode('utf-8')
                success = test_data == decrypted_str
                print(f"  Успех: {success}")
            except Exception as e:
                print(f"  Ошибка декодирования: {e}")
            
        except Exception as e:
            print(f"  Ошибка маскировки: {e}")


def test_manager():
    """Тест менеджера нейро-шифрования"""
    print("\n=== Тест менеджера шифрования ===")
    
    manager = NeuralEncryptorManager()
    
    # Создание нескольких шифраторов
    configs = [
        NeuralEncryptConfig(
            method=EncryptionMethod.AUTOENCODER,
            mimic_type=TrafficMimicType.HTTP,
            latent_dim=64
        ),
        NeuralEncryptConfig(
            method=EncryptionMethod.VAE,
            mimic_type=TrafficMimicType.DNS,
            latent_dim=128
        )
    ]
    
    session_ids = []
    
    for i, config in enumerate(configs):
        session_id = manager.create_encryptor(config, f"test_session_{i}")
        session_ids.append(session_id)
        print(f"Создана сессия: {session_id}")
    
    # Тестирование шифрования
    test_data = "Тест через менеджер"
    
    for session_id in session_ids:
        print(f"\nТест сессии: {session_id}")
        
        # Шифрование
        encrypted = manager.encrypt_data(session_id, test_data)
        if encrypted:
            print(f"  Зашифровано: {len(encrypted)} байт")
            
            # Дешифрование
            decrypted = manager.decrypt_data(session_id, encrypted)
            if decrypted:
                try:
                    decrypted_str = decrypted.decode('utf-8')
                    success = test_data == decrypted_str
                    print(f"  Успех: {success}")
                except Exception as e:
                    print(f"  Ошибка: {e}")
            
            # Статистика
            stats = manager.get_encryptor_stats(session_id)
            if stats:
                print(f"  Статистика: {json.dumps(stats, indent=6)}")


def test_large_data():
    """Тест больших объемов данных"""
    print("\n=== Тест больших данных ===")
    
    config = NeuralEncryptConfig(
        method=EncryptionMethod.AUTOENCODER,
        mimic_type=TrafficMimicType.HTTP,
        latent_dim=256,
        sequence_length=512
    )
    
    encryptor = NeuralEncryptor(config)
    
    # Генерация больших данных
    large_data = "Большой объем данных для тестирования. " * 100
    print(f"Размер данных: {len(large_data)} байт")
    
    # Шифрование
    start_time = time.time()
    encrypted = encryptor.encrypt_data(large_data)
    encrypt_time = time.time() - start_time
    
    print(f"Время шифрования: {encrypt_time:.4f} сек")
    print(f"Размер зашифрованного: {len(encrypted)} байт")
    
    # Дешифрование
    start_time = time.time()
    decrypted = encryptor.decrypt_data(encrypted)
    decrypt_time = time.time() - start_time
    
    print(f"Время дешифрования: {decrypt_time:.4f} сек")
    
    # Проверка
    try:
        decrypted_str = decrypted.decode('utf-8')
        success = large_data == decrypted_str
        print(f"Успех: {success}")
        
        if not success:
            print(f"Оригинал (начало): {large_data[:100]}...")
            print(f"Расшифровано (начало): {decrypted_str[:100]}...")
    except Exception as e:
        print(f"Ошибка: {e}")


def main():
    """Основная функция тестирования"""
    print("RSecure Neural Encryptor - Тестирование")
    print("=" * 50)
    
    # Проверка доступности TensorFlow
    try:
        import tensorflow as tf
        print(f"TensorFlow доступен: {tf.__version__}")
    except ImportError:
        print("TensorFlow недоступен, будут использованы mock модели")
    
    # Запуск тестов
    tests = [
        test_basic_encryption,
        test_different_methods,
        test_traffic_mimicry,
        test_manager,
        test_large_data
    ]
    
    results = {}
    
    for test_func in tests:
        try:
            print(f"\n{'='*20} {test_func.__name__} {'='*20}")
            result = test_func()
            results[test_func.__name__] = result
        except Exception as e:
            print(f"Ошибка в тесте {test_func.__name__}: {e}")
            results[test_func.__name__] = {'error': str(e)}
    
    # Итоги
    print(f"\n{'='*50}")
    print("Итоги тестирования:")
    
    for test_name, result in results.items():
        if isinstance(result, dict) and 'success' in result:
            status = "✓ Успешно" if result['success'] else "✗ Ошибка"
        elif result is True:
            status = "✓ Успешно"
        elif result is False:
            status = "✗ Ошибка"
        else:
            status = "? Неизвестно"
        
        print(f"  {test_name}: {status}")
    
    print("\nТестирование завершено!")


if __name__ == "__main__":
    main()
