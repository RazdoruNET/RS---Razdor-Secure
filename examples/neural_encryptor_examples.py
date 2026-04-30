#!/usr/bin/env python3
"""
Примеры использования RSecure Neural Encryptor
Различные сценарии применения нейро-шифрования
"""

import sys
import os
import time
import json
import numpy as np

# Добавляем путь к модулям RSecure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rsecure.modules.defense.neural_encryptor import (
    NeuralEncryptor, 
    NeuralEncryptorManager, 
    NeuralEncryptConfig,
    EncryptionMethod,
    TrafficMimicType
)


def example_basic_usage():
    """Пример 1: Базовое использование нейро-шифратора"""
    print("=" * 60)
    print("ПРИМЕР 1: Базовое использование нейро-шифратора")
    print("=" * 60)
    
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
    secret_message = "Это секретное сообщение для демонстрации нейро-шифрования"
    
    print(f"📝 Оригинальное сообщение: {secret_message}")
    print(f"📏 Длина: {len(secret_message)} байт")
    
    # Шифрование
    print("\n🔐 Шифрование...")
    start_time = time.time()
    encrypted = encryptor.encrypt_data(secret_message)
    encrypt_time = time.time() - start_time
    
    print(f"⏱️ Время шифрования: {encrypt_time:.4f} сек")
    print(f"📦 Размер зашифрованного: {len(encrypted)} байт")
    print(f"📊 Коэффициент сжатия: {len(encrypted)/len(secret_message):.2f}")
    
    # Дешифрование
    print("\n🔓 Дешифрование...")
    start_time = time.time()
    decrypted = encryptor.decrypt_data(encrypted)
    decrypt_time = time.time() - start_time
    
    print(f"⏱️ Время дешифрования: {decrypt_time:.4f} сек")
    
    # Проверка
    try:
        decrypted_str = decrypted.decode('utf-8')
        success = secret_message == decrypted_str
        print(f"✅ Успешное восстановление: {success}")
        if success:
            print(f"📝 Расшифрованное: {decrypted_str}")
        else:
            print(f"❌ Ожидалось: {secret_message}")
            print(f"❌ Получено: {decrypted_str}")
    except Exception as e:
        print(f"❌ Ошибка декодирования: {e}")
    
    # Статистика
    stats = encryptor.get_stats()
    print(f"\n📈 Статистика: {json.dumps(stats, indent=2)}")


def example_different_methods():
    """Пример 2: Сравнение различных методов шифрования"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 2: Сравнение различных методов шифрования")
    print("=" * 60)
    
    test_data = "Тестовое сообщение для сравнения методов нейро-шифрования"
    methods = [
        (EncryptionMethod.AUTOENCODER, "Autoencoder"),
        (EncryptionMethod.VAE, "Variational Autoencoder"),
        (EncryptionMethod.TRANSFORMER, "Transformer"),
        (EncryptionMethod.HYBRID, "Hybrid")
    ]
    
    results = []
    
    for method, name in methods:
        print(f"\n🧠 Тест метода: {name}")
        
        try:
            config = NeuralEncryptConfig(
                method=method,
                mimic_type=TrafficMimicType.HTTP,
                latent_dim=64,
                sequence_length=32
            )
            
            encryptor = NeuralEncryptor(config)
            
            # Тестирование
            start_time = time.time()
            encrypted = encryptor.encrypt_data(test_data)
            encrypt_time = time.time() - start_time
            
            start_time = time.time()
            decrypted = encryptor.decrypt_data(encrypted)
            decrypt_time = time.time() - start_time
            
            try:
                decrypted_str = decrypted.decode('utf-8')
                success = test_data == decrypted_str
                compression_ratio = len(encrypted) / len(test_data)
                
                result = {
                    'method': name,
                    'success': success,
                    'encrypt_time': encrypt_time,
                    'decrypt_time': decrypt_time,
                    'compression_ratio': compression_ratio,
                    'encrypted_size': len(encrypted)
                }
                
                results.append(result)
                
                print(f"  ✅ Успех: {success}")
                print(f"  ⏱️ Шифрование: {encrypt_time:.4f} сек")
                print(f"  ⏱️ Дешифрование: {decrypt_time:.4f} сек")
                print(f"  📊 Сжатие: {compression_ratio:.2f}")
                
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
                results.append({'method': name, 'success': False, 'error': str(e)})
            
        except Exception as e:
            print(f"  ❌ Ошибка метода: {e}")
            results.append({'method': name, 'success': False, 'error': str(e)})
    
    # Сводная таблица
    print(f"\n📊 Сводная таблица результатов:")
    print("-" * 80)
    print(f"{'Метод':<25} {'Успех':<8} {'Шифрование':<12} {'Дешифрование':<12} {'Сжатие':<8}")
    print("-" * 80)
    
    for result in results:
        if result.get('success'):
            print(f"{result['method']:<25} {'✅':<8} {result['encrypt_time']:<12.4f} {result['decrypt_time']:<12.4f} {result['compression_ratio']:<8.2f}")
        else:
            print(f"{result['method']:<25} {'❌':<8} {'-':<12} {'-':<12} {'-':<8}")


def example_traffic_mimicry():
    """Пример 3: Маскировка под разные типы трафика"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 3: Маскировка под разные типы трафика")
    print("=" * 60)
    
    secret_data = "Конфиденциальные данные для маскировки в сетевом трафике"
    mimic_types = [
        (TrafficMimicType.HTTP, "HTTP"),
        (TrafficMimicType.DNS, "DNS"),
        (TrafficMimicType.ICMP, "ICMP"),
        (TrafficMimicType.SSH, "SSH")
    ]
    
    for mimic_type, name in mimic_types:
        print(f"\n📡 Маскировка под: {name}")
        
        try:
            config = NeuralEncryptConfig(
                method=EncryptionMethod.AUTOENCODER,
                mimic_type=mimic_type,
                latent_dim=64,
                sequence_length=32
            )
            
            encryptor = NeuralEncryptor(config)
            
            # Шифрование
            encrypted = encryptor.encrypt_data(secret_data)
            
            print(f"  📝 Оригинал: {secret_data[:30]}...")
            print(f"  📦 Размер: {len(encrypted)} байт")
            
            # Показываем начало зашифрованного трафика
            encrypted_preview = encrypted[:100].decode('utf-8', errors='ignore')
            print(f"  🔐 Пример трафика: {encrypted_preview}...")
            
            # Дешифрование
            decrypted = encryptor.decrypt_data(encrypted)
            try:
                decrypted_str = decrypted.decode('utf-8')
                success = secret_data == decrypted_str
                print(f"  ✅ Восстановление: {success}")
            except Exception as e:
                print(f"  ❌ Ошибка восстановления: {e}")
            
        except Exception as e:
            print(f"  ❌ Ошибка маскировки: {e}")


def example_manager_usage():
    """Пример 4: Использование менеджера нейро-шифрования"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 4: Использование менеджера нейро-шифрования")
    print("=" * 60)
    
    manager = NeuralEncryptorManager()
    
    # Создание нескольких сессий с разными конфигурациями
    configs = [
        (NeuralEncryptConfig(
            method=EncryptionMethod.AUTOENCODER,
            mimic_type=TrafficMimicType.HTTP,
            latent_dim=64
        ), "HTTP_Autoencoder"),
        (NeuralEncryptConfig(
            method=EncryptionMethod.VAE,
            mimic_type=TrafficMimicType.DNS,
            latent_dim=128
        ), "DNS_VAE"),
        (NeuralEncryptConfig(
            method=EncryptionMethod.TRANSFORMER,
            mimic_type=TrafficMimicType.ICMP,
            latent_dim=96
        ), "ICMP_Transformer")
    ]
    
    session_ids = []
    
    print("🔧 Создание сессий шифрования:")
    for config, name in configs:
        session_id = manager.create_encryptor(config, f"session_{name.lower()}")
        session_ids.append((session_id, name))
        print(f"  ✅ Создана сессия: {session_id} ({name})")
    
    # Тестирование всех сессий
    test_data = "Тестовое сообщение для менеджера нейро-шифрования"
    
    print(f"\n📝 Тестовые данные: {test_data}")
    
    for session_id, name in session_ids:
        print(f"\n🧪 Тест сессии: {name}")
        
        try:
            # Шифрование
            encrypted = manager.encrypt_data(session_id, test_data)
            if encrypted:
                print(f"  🔐 Зашифровано: {len(encrypted)} байт")
                
                # Дешифрование
                decrypted = manager.decrypt_data(session_id, encrypted)
                if decrypted:
                    try:
                        decrypted_str = decrypted.decode('utf-8')
                        success = test_data == decrypted_str
                        print(f"  ✅ Успех: {success}")
                    except Exception as e:
                        print(f"  ❌ Ошибка декодирования: {e}")
                
                # Статистика
                stats = manager.get_encryptor_stats(session_id)
                if stats:
                    print(f"  📊 Статистика: {stats}")
            else:
                print(f"  ❌ Ошибка шифрования")
                
        except Exception as e:
            print(f"  ❌ Ошибка сессии: {e}")


def example_large_data():
    """Пример 5: Работа с большими объемами данных"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 5: Работа с большими объемами данных")
    print("=" * 60)
    
    config = NeuralEncryptConfig(
        method=EncryptionMethod.AUTOENCODER,
        mimic_type=TrafficMimicType.HTTP,
        latent_dim=256,
        sequence_length=512
    )
    
    encryptor = NeuralEncryptor(config)
    
    # Генерация больших данных
    sizes = [100, 1000, 5000, 10000]  # байты
    
    for size in sizes:
        print(f"\n📊 Тест размера: {size} байт")
        
        # Создание тестовых данных
        large_data = "A" * size
        print(f"  📝 Размер данных: {len(large_data)} байт")
        
        try:
            # Шифрование
            start_time = time.time()
            encrypted = encryptor.encrypt_data(large_data)
            encrypt_time = time.time() - start_time
            
            print(f"  ⏱️ Время шифрования: {encrypt_time:.4f} сек")
            print(f"  📦 Размер зашифрованного: {len(encrypted)} байт")
            print(f"  📊 Коэффициент: {len(encrypted)/len(large_data):.2f}")
            
            # Дешифрование
            start_time = time.time()
            decrypted = encryptor.decrypt_data(encrypted)
            decrypt_time = time.time() - start_time
            
            print(f"  ⏱️ Время дешифрования: {decrypt_time:.4f} сек")
            
            # Проверка
            try:
                decrypted_str = decrypted.decode('utf-8')
                success = large_data == decrypted_str
                print(f"  ✅ Успех: {success}")
                
                if not success:
                    print(f"    Оригинал (начало): {large_data[:50]}...")
                    print(f"    Расшифровано (начало): {decrypted_str[:50]}...")
                    
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
                
        except Exception as e:
            print(f"  ❌ Ошибка обработки: {e}")


def example_integration_with_other_modules():
    """Пример 6: Интеграция с другими модулями RSecure"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 6: Интеграция с другими модулями RSecure")
    print("=" * 60)
    
    # Интеграция с Traffic Obfuscation
    try:
        from rsecure.modules.defense.traffic_obfuscation import TrafficObfuscator, ObfuscationConfig, ObfuscationMethod
        
        print("🔗 Интеграция с Traffic Obfuscation:")
        
        # Создание нейро-шифратора
        neural_config = NeuralEncryptConfig(
            method=EncryptionMethod.AUTOENCODER,
            mimic_type=TrafficMimicType.HTTP,
            latent_dim=128
        )
        neural_encryptor = NeuralEncryptor(neural_config)
        
        # Создание обфускатора
        obfusc_config = ObfuscationConfig(method=ObfuscationMethod.AES)
        obfuscator = TrafficObfuscator()
        
        # Тестовые данные
        secret_data = "Секретные данные для комплексной защиты"
        
        print(f"  📝 Оригинал: {secret_data}")
        
        # Многослойная защита
        print("  🔄 Применение многослойной защиты:")
        
        # 1. Нейро-шифрование
        step1 = neural_encryptor.encrypt_data(secret_data)
        print(f"    1️⃣ Нейро-шифрование: {len(secret_data)} → {len(step1)} байт")
        
        # 2. Дополнительная обфускация
        step2 = obfuscator.obfuscate_data(step1, obfusc_config)
        print(f"    2️⃣ Обфускация: {len(step1)} → {len(step2)} байт")
        
        # Обратный процесс
        print("  🔓 Обратный процесс:")
        
        # 1. Удаление обфускации
        step3 = obfuscator.deobfuscate_data(step2, obfusc_config)
        print(f"    1️⃣ Деобфускация: {len(step2)} → {len(step3)} байт")
        
        # 2. Нейро-дешифрование
        step4 = neural_encryptor.decrypt_data(step3)
        print(f"    2️⃣ Нейро-дешифрование: {len(step3)} → {len(step4)} байт")
        
        # Проверка
        try:
            result_str = step4.decode('utf-8')
            success = secret_data == result_str
            print(f"  ✅ Итоговый успех: {success}")
            if success:
                print(f"  📝 Результат: {result_str}")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            
    except ImportError:
        print("  ⚠️ Модуль Traffic Obfuscation недоступен")
    
    # Интеграция с Ollama (если доступен)
    try:
        from rsecure.core.ollama_integration import OllamaSecurityAnalyzer
        
        print("\n🤖 Интеграция с Ollama:")
        
        # Создание анализатора
        ollama_analyzer = OllamaSecurityAnalyzer()
        
        # Анализ зашифрованных данных
        neural_config = NeuralEncryptConfig(
            method=EncryptionMethod.AUTOENCODER,
            mimic_type=TrafficMimicType.HTTP
        )
        encryptor = NeuralEncryptor(neural_config)
        
        # Шифрование данных
        test_event = {
            "timestamp": "2024-01-01T12:00:00Z",
            "event_type": "neural_encrypted_data",
            "source": "neural_encryptor",
            "data": "Секретные данные для анализа"
        }
        
        encrypted_data = encryptor.encrypt_data(test_event["data"])
        
        # Анализ события (симуляция)
        print(f"  📊 Анализ зашифрованного события:")
        print(f"    Тип: {test_event['event_type']}")
        print(f"    Размер: {len(encrypted_data)} байт")
        print(f"    Источник: {test_event['source']}")
        print(f"    ✅ Анализ завершен")
        
    except ImportError:
        print("\n⚠️ Модуль Ollama недоступен")


def example_custom_configuration():
    """Пример 7: Кастомная конфигурация и параметры"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 7: Кастомная конфигурация и параметры")
    print("=" * 60)
    
    # Создание кастомной конфигурации
    custom_config = NeuralEncryptConfig(
        method=EncryptionMethod.HYBRID,
        mimic_type=TrafficMimicType.HTTPS,
        latent_dim=512,
        sequence_length=256,
        compression_ratio=0.2,
        adversarial_strength=0.15,
        model_path="./models/custom_neural_encryptor"
    )
    
    print("⚙️ Кастомная конфигурация:")
    print(f"  🧠 Метод: {custom_config.method.value}")
    print(f"  📡 Маскировка: {custom_config.mimic_type.value}")
    print(f"  📏 Латентное пространство: {custom_config.latent_dim}")
    print(f"  📊 Длина последовательности: {custom_config.sequence_length}")
    print(f"  🗜️ Целевое сжатие: {custom_config.compression_ratio}")
    print(f"  🛡️ Adversarial сила: {custom_config.adversarial_strength}")
    print(f"  💾 Путь к моделям: {custom_config.model_path}")
    
    try:
        # Создание шифратора с кастомной конфигурацией
        encryptor = NeuralEncryptor(custom_config)
        
        # Тестирование
        test_data = "Тест данных для кастомной конфигурации нейро-шифратора"
        
        print(f"\n🧪 Тестирование кастомной конфигурации:")
        print(f"  📝 Данные: {test_data}")
        
        # Шифрование
        start_time = time.time()
        encrypted = encryptor.encrypt_data(test_data)
        encrypt_time = time.time() - start_time
        
        print(f"  🔐 Шифрование: {encrypt_time:.4f} сек, {len(encrypted)} байт")
        
        # Дешифрование
        start_time = time.time()
        decrypted = encryptor.decrypt_data(encrypted)
        decrypt_time = time.time() - start_time
        
        print(f"  🔓 Дешифрование: {decrypt_time:.4f} сек")
        
        # Проверка
        try:
            result_str = decrypted.decode('utf-8')
            success = test_data == result_str
            print(f"  ✅ Успех: {success}")
            
            # Статистика
            stats = encryptor.get_stats()
            print(f"  📈 Статистика: {json.dumps(stats, indent=6)}")
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка кастомной конфигурации: {e}")


def main():
    """Основная функция - запуск всех примеров"""
    print("🚀 RSecure Neural Encryptor - Примеры использования")
    print("=" * 80)
    
    # Проверка доступности зависимостей
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow доступен: {tf.__version__}")
    except ImportError:
        print("⚠️ TensorFlow недоступен, будет использован mock режим")
    
    try:
        from cryptography.fernet import Fernet
        print("✅ Cryptography доступен")
    except ImportError:
        print("⚠️ Cryptography недоступен, будет использован XOR")
    
    # Запуск примеров
    examples = [
        example_basic_usage,
        example_different_methods,
        example_traffic_mimicry,
        example_manager_usage,
        example_large_data,
        example_integration_with_other_modules,
        example_custom_configuration
    ]
    
    results = {}
    
    for i, example_func in enumerate(examples, 1):
        try:
            print(f"\n🔄 Запуск примера {i}...")
            result = example_func()
            results[f"example_{i}"] = "success"
            print(f"✅ Пример {i} завершен успешно")
        except Exception as e:
            print(f"❌ Ошибка в примере {i}: {e}")
            results[f"example_{i}"] = f"error: {str(e)}"
    
    # Итоги
    print(f"\n" + "=" * 80)
    print("📊 ИТОГИ ПРИМЕРОВ:")
    print("-" * 80)
    
    for example_name, result in results.items():
        status = "✅ Успешно" if result == "success" else "❌ Ошибка"
        print(f"  {example_name}: {status}")
    
    print(f"\n🎉 Все примеры завершены!")
    print("💡 Используйте эти примеры как основу для ваших приложений")


if __name__ == "__main__":
    main()
