# 🔓 DPI Обход - Технические Детали

## Обзор

Этот документ предоставляет технические детали реализации DPI обхода в RSecure, включая алгоритмы, протоколы и методы оптимизации.

## 🔬 Технические Алгоритмы

### 1. Фрагментация Пакетов

#### Алгоритм Фрагментации
```python
def fragment_packet(data, fragment_size, delay_ms=0):
    """
    Разделяет данные на фрагменты указанного размера
    
    Args:
        data: Исходные данные для фрагментации
        fragment_size: Размер каждого фрагмента
        delay_ms: Задержка между фрагментами
    
    Returns:
        List[bytes]: Список фрагментированных данных
    """
    fragments = []
    for i in range(0, len(data), fragment_size):
        fragment = data[i:i + fragment_size]
        fragments.append(fragment)
        
        # Добавляем задержку между фрагментами
        if delay_ms > 0 and i + fragment_size < len(data):
            time.sleep(delay_ms / 1000.0)
    
    return fragments
```

#### Оптимизация Фрагментации
- **Адаптивный размер**: Динамическая подстройка размера фрагментов
- **Рандомизация**: Случайная вариация размеров для обхода паттернов
- **Временная рандомизация**: Случайные задержки между фрагментами

### 2. TLS SNI Splitting

#### Реализация SNI Splitting
```python
def split_sni_tls_handshake(target_host, target_port):
    """
    Разделяет TLS handshake для обхода SNI инспекции
    
    Args:
        target_host: Целевой хост
        target_port: Целевой порт
    
    Returns:
        tuple: (client_hello_data, server_hello_data)
    """
    # Создание Client Hello без SNI
    client_hello = create_client_hello_without_sni(target_host, target_port)
    
    # Отдельная отправка SNI
    sni_extension = create_sni_extension(target_host)
    
    return client_hello, sni_extension
```

#### Технические Детали
- **TLS 1.3**: Использование новых возможностей TLS 1.3
- **ESNI**: Encrypted SNI для дополнительной защиты
- **Множественные SNI**: Использование нескольких доменов

### 3. Обфускация HTTP Заголовков

#### Алгоритм Обфускации
```python
def obfuscate_http_headers(headers):
    """
    Обфусцирует HTTP заголовки для обхода DPI
    
    Args:
        headers: Словарь HTTP заголовков
    
    Returns:
        dict: Обфусцированные заголовки
    """
    obfuscated = {}
    
    for key, value in headers.items():
        # Рандомизация порядка заголовков
        obfuscated_key = randomize_case(key)
        
        # Добавление случайных заголовков
        obfuscated_value = add_random_noise(value)
        
        # Кодирование значений
        if random.random() > 0.5:
            obfuscated_value = url_encode_partial(obfuscated_value)
        
        obfuscated[obfuscated_key] = obfuscated_value
    
    return obfuscated
```

#### Методы Обфускации
- **Case Randomization**: Случайная регистрация заголовков
- **Value Obfuscation**: Добавление шума в значения
- **Header Splitting**: Разделение заголовков на части
- **Fake Headers**: Добавление ложных заголовков

### 4. Domain Fronting

#### Реализация Domain Fronting
```python
def create_domain_fronted_request(target_url, cdn_domain):
    """
    Создает запрос с domain fronting
    
    Args:
        target_url: Целевой URL
        cdn_domain: CDN домен для маскировки
    
    Returns:
        tuple: (request_headers, request_data)
    """
    # Host заголовок указывает на CDN
    headers = {
        'Host': cdn_domain,
        'X-Forwarded-Host': extract_host(target_url)
    }
    
    # URL остается оригинальным
    return headers, target_url.encode()
```

#### Поддерживаемые CDN
- **Cloudflare**: Использование Cloudflare Workers
- **AWS CloudFront**: Amazon CDN fronting
- **Google Cloud**: Google CDN integration
- **Azure Edge**: Microsoft Azure CDN

## 🛡️ Продвинутые Техники

### 1. Многостадийный Обход

#### Алгоритм Многостадийности
```python
class MultiStageBypass:
    def __init__(self):
        self.stages = [
            self.fragmentation_stage,
            self.obfuscation_stage,
            self.encryption_stage,
            self.protocol_mimicry_stage
        ]
    
    def bypass(self, data, target):
        """
        Применяет многостадийный обход
        
        Args:
            data: Данные для отправки
            target: Целевой хост:порт
        
        Returns:
            bytes: Обработанные данные
        """
        processed_data = data
        
        for stage in self.stages:
            try:
                processed_data = stage(processed_data, target)
            except Exception as e:
                logger.warning(f"Stage {stage.__name__} failed: {e}")
                continue
        
        return processed_data
```

### 2. Адаптивный Обход

#### Алгоритм Адаптации
```python
class AdaptiveBypass:
    def __init__(self):
        self.methods = {
            'fragmentation': FragmentationBypass(),
            'sni_splitting': SNISplittingBypass(),
            'header_obfuscation': HeaderObfuscationBypass(),
            'domain_fronting': DomainFrontingBypass()
        }
        self.success_rates = {method: 0.0 for method in self.methods}
        self.performance_metrics = {method: {} for method in self.methods}
    
    def select_best_method(self, target, network_conditions):
        """
        Выбирает лучший метод на основе статистики
        
        Args:
            target: Целевой хост:порт
            network_conditions: Сетевые условия
        
        Returns:
            str: Лучший метод обхода
        """
        scores = {}
        
        for method, bypass in self.methods.items():
            # Учет успеха
            success_score = self.success_rates[method]
            
            # Учет производительности
            perf_score = self.calculate_performance_score(method)
            
            # Учет сетевых условий
            network_score = self.calculate_network_score(method, network_conditions)
            
            # Комбинированная оценка
            scores[method] = (success_score * 0.4 + 
                           perf_score * 0.3 + 
                           network_score * 0.3)
        
        return max(scores, key=scores.get)
```

## 🔐 Протоколы и Шифрование

### 1. Протокол Мимикрия

#### HTTP Мимикрия
```python
def create_http_mimicry(data, target_host):
    """
    Создает HTTP мимикрию для данных
    
    Args:
        data: Данные для маскировки
        target_host: Целевой хост
    
    Returns:
        tuple: (http_headers, http_body)
    """
    # Создание HTTP запроса
    headers = {
        'GET': f'/{generate_random_path()} HTTP/1.1',
        'Host': target_host,
        'User-Agent': generate_random_user_agent(),
        'Accept': '*/*',
        'X-Custom-Data': base64.b64encode(data).decode(),
        'Connection': 'keep-alive'
    }
    
    # Формирование HTTP запроса
    http_request = format_http_request(headers)
    
    return http_request.encode()
```

#### SSH Мимикрия
```python
def create_ssh_mimicry(data, target_host):
    """
    Создает SSH мимикрию для данных
    
    Args:
        data: Данные для маскировки
        target_host: Целевой хост
    
    Returns:
        bytes: SSH пакет с данными
    """
    # SSH пакет структура
    packet_length = len(data) + 32  # SSH заголовок
    padding_length = 8 - (packet_length % 8)
    
    # Создание SSH пакета
    ssh_packet = struct.pack('!I', packet_length + padding_length)
    ssh_packet += struct.pack('!B', padding_length)
    ssh_packet += data
    ssh_packet += os.urandom(padding_length)
    
    # MAC (简化版)
    ssh_packet += calculate_ssh_mac(ssh_packet)
    
    return ssh_packet
```

### 2. Шифрование и Обфускация

#### AES Шифрование
```python
class AESEncryption:
    def __init__(self, key):
        self.key = key
        self.cipher = AES.new(key, AES.MODE_CBC)
    
    def encrypt(self, data):
        """
        Шифрует данные с AES
        
        Args:
            data: Данные для шифрования
        
        Returns:
            bytes: Зашифрованные данные
        """
        # Padding для AES
        padded_data = pad_data(data, AES.block_size)
        
        # Шифрование
        iv = os.urandom(16)
        encrypted = self.cipher.encrypt(padded_data)
        
        # Возврат IV + зашифрованные данные
        return iv + encrypted
    
    def decrypt(self, encrypted_data):
        """
        Расшифровывает AES данные
        
        Args:
            encrypted_data: Зашифрованные данные
        
        Returns:
            bytes: Расшифрованные данные
        """
        # Извлечение IV
        iv = encrypted_data[:16]
        encrypted = encrypted_data[16:]
        
        # Расшифрование
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted)
        
        # Удаление padding
        return unpad_data(decrypted, AES.block_size)
```

#### ChaCha20 Шифрование
```python
class ChaCha20Encryption:
    def __init__(self, key):
        self.key = key
    
    def encrypt(self, data, nonce=None):
        """
        Шифрует данные с ChaCha20
        
        Args:
            data: Данные для шифрования
            nonce: Nonce для шифрования
        
        Returns:
            tuple: (encrypted_data, nonce)
        """
        if nonce is None:
            nonce = os.urandom(12)
        
        # ChaCha20 шифрование
        cipher = ChaCha20.new(key=self.key, nonce=nonce)
        encrypted = cipher.encrypt(data)
        
        return encrypted, nonce
```

## 📊 Оптимизация Производительности

### 1. Параллельная Обработка

#### Многопоточный Обход
```python
import threading
import queue

class ParallelBypass:
    def __init__(self, num_threads=4):
        self.num_threads = num_threads
        self.work_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        
        # Создание воркеров
        for i in range(num_threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Воркер для обработки задач"""
        while True:
            try:
                task = self.work_queue.get(timeout=1)
                if task is None:
                    break
                
                data, target, method = task
                result = self.process_bypass(data, target, method)
                self.result_queue.put(result)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def bypass_parallel(self, data_list, targets, methods):
        """
        Параллельный обход
        
        Args:
            data_list: Список данных для обработки
            targets: Список целей
            methods: Список методов
        
        Returns:
            List[dict]: Результаты обработки
        """
        # Добавление задач в очередь
        for data, target in zip(data_list, targets):
            for method in methods:
                self.work_queue.put((data, target, method))
        
        # Сбор результатов
        results = []
        for _ in range(len(data_list) * len(targets) * len(methods)):
            try:
                result = self.result_queue.get(timeout=30)
                results.append(result)
            except queue.Empty:
                break
        
        return results
```

### 2. Кэширование Результатов

#### Система Кэширования
```python
class BypassCache:
    def __init__(self, cache_size=1000):
        self.cache = {}
        self.cache_size = cache_size
        self.access_times = {}
    
    def get(self, key):
        """
        Получает результат из кэша
        
        Args:
            key: Ключ кэша
        
        Returns:
            bytes: Кэшированные данные или None
        """
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def put(self, key, value):
        """
        Сохраняет результат в кэш
        
        Args:
            key: Ключ кэша
            value: Значение для кэширования
        """
        # Проверка размера кэша
        if len(self.cache) >= self.cache_size:
            self._evict_oldest()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """Удаляет самые старые записи из кэша"""
        oldest_key = min(self.access_times, key=self.access_times.get)
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
```

## 🔍 Мониторинг и Аналитика

### 1. Метрики Производительности

#### Сбор Метрик
```python
class BypassMetrics:
    def __init__(self):
        self.metrics = {
            'success_rate': {},
            'latency': {},
            'throughput': {},
            'error_rate': {}
        }
    
    def record_attempt(self, method, success, latency, data_size):
        """
        Записывает метрики попытки обхода
        
        Args:
            method: Метод обхода
            success: Успешность попытки
            latency: Задержка в мс
            data_size: Размер данных в байтах
        """
        if method not in self.metrics['success_rate']:
            self.metrics['success_rate'][method] = []
            self.metrics['latency'][method] = []
            self.metrics['throughput'][method] = []
            self.metrics['error_rate'][method] = []
        
        # Запись метрик
        self.metrics['success_rate'][method].append(success)
        self.metrics['latency'][method].append(latency)
        self.metrics['throughput'][method].append(data_size / latency * 1000)
        self.metrics['error_rate'][method].append(not success)
    
    def get_statistics(self, method):
        """
        Получает статистику для метода
        
        Args:
            method: Метод обхода
        
        Returns:
            dict: Статистика метода
        """
        if method not in self.metrics['success_rate']:
            return {}
        
        return {
            'success_rate': sum(self.metrics['success_rate'][method]) / len(self.metrics['success_rate'][method]),
            'avg_latency': sum(self.metrics['latency'][method]) / len(self.metrics['latency'][method]),
            'avg_throughput': sum(self.metrics['throughput'][method]) / len(self.metrics['throughput'][method]),
            'error_rate': sum(self.metrics['error_rate'][method]) / len(self.metrics['error_rate'][method])
        }
```

### 2. Детекция DPI Систем

#### Анализ DPI Поведения
```python
class DPIAnalyzer:
    def __init__(self):
        self.dpi_signatures = {
            'packet_inspection': self.detect_packet_inspection,
            'sni_filtering': self.detect_sni_filtering,
            'header_analysis': self.detect_header_analysis,
            'traffic_shaping': self.detect_traffic_shaping
        }
    
    def analyze_dpi_behavior(self, target_host, target_port):
        """
        Анализирует поведение DPI системы
        
        Args:
            target_host: Целевой хост
            target_port: Целевой порт
        
        Returns:
            dict: Результаты анализа DPI
        """
        results = {}
        
        for dpi_type, detector in self.dpi_signatures.items():
            try:
                results[dpi_type] = detector(target_host, target_port)
            except Exception as e:
                logger.error(f"DPI analysis {dpi_type} failed: {e}")
                results[dpi_type] = {'detected': False, 'error': str(e)}
        
        return results
    
    def detect_packet_inspection(self, target_host, target_port):
        """Детекция инспекции пакетов"""
        # Отправка тестовых пакетов
        test_packets = [
            self.create_normal_packet(target_host, target_port),
            self.create_fragmented_packet(target_host, target_port),
            self.create_obfuscated_packet(target_host, target_port)
        ]
        
        responses = []
        for packet in test_packets:
            response = self.send_packet(packet, target_host, target_port)
            responses.append(response)
        
        # Анализ ответов
        return self.analyze_responses(responses)
```

## 🛠️ Конфигурация и Настройка

### 1. Конфигурация Методов

#### JSON Конфигурация
```json
{
  "dpi_bypass": {
    "methods": {
      "fragmentation": {
        "enabled": true,
        "fragment_size": 512,
        "delay_ms": 50,
        "randomize_size": true,
        "max_delay_variance": 0.5
      },
      "sni_splitting": {
        "enabled": true,
        "use_esni": true,
        "multiple_sni": false,
        "fallback_method": "fragmentation"
      },
      "header_obfuscation": {
        "enabled": true,
        "randomize_case": true,
        "add_fake_headers": true,
        "split_headers": false,
        "encode_values": true
      },
      "domain_fronting": {
        "enabled": true,
        "cdn_providers": ["cloudflare", "aws", "google"],
        "fallback_domains": ["backup1.com", "backup2.com"]
      }
    },
    "adaptive_selection": {
      "enabled": true,
      "success_threshold": 0.8,
      "performance_weight": 0.6,
      "learning_rate": 0.1
    },
    "performance": {
      "parallel_processing": true,
      "max_threads": 4,
      "cache_enabled": true,
      "cache_size": 1000,
      "metrics_enabled": true
    }
  }
}
```

### 2. Динамическая Конфигурация

#### Runtime Конфигурация
```python
class DynamicBypassConfig:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()
        self.watchers = []
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def update_config(self, updates):
        """
        Обновляет конфигурацию
        
        Args:
            updates: Словарь обновлений
        """
        self.config.update(updates)
        self.save_config()
        self.notify_watchers(updates)
    
    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def watch_config(self, callback):
        """
        Добавляет наблюдателя за конфигурацией
        
        Args:
            callback: Функция обратного вызова
        """
        self.watchers.append(callback)
```

## 🔒 Безопасность и Защита

### 1. Защита от Обнаружения

#### Анти-Детекция Меры
```python
class AntiDetection:
    def __init__(self):
        self.techniques = [
            self.randomize_timing,
            self.mimic_legitimate_traffic,
            self.rotate_user_agents,
            self.vary_packet_sizes
        ]
    
    def apply_anti_detection(self, data, method):
        """
        Применяет анти-детекционные меры
        
        Args:
            data: Данные для обработки
            method: Метод обхода
        
        Returns:
            bytes: Обработанные данные
        """
        processed_data = data
        
        for technique in self.techniques:
            try:
                processed_data = technique(processed_data, method)
            except Exception as e:
                logger.warning(f"Anti-detection technique failed: {e}")
        
        return processed_data
    
    def randomize_timing(self, data, method):
        """Рандомизация таймингов"""
        if method in ['fragmentation', 'sni_splitting']:
            # Случайная задержка между пакетами
            delay = random.uniform(0.01, 0.1)
            time.sleep(delay)
        return data
    
    def mimic_legitimate_traffic(self, data, method):
        """Мимикрия под легитимный трафик"""
        # Добавление заголовков легитимных приложений
        legitimate_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        return data, legitimate_headers
```

### 2. Валидация и Проверки

#### Валидация Конфигурации
```python
class ConfigValidator:
    def __init__(self):
        self.validators = {
            'fragmentation': self.validate_fragmentation_config,
            'sni_splitting': self.validate_sni_splitting_config,
            'header_obfuscation': self.validate_header_obfuscation_config,
            'domain_fronting': self.validate_domain_fronting_config
        }
    
    def validate_config(self, config):
        """
        Валидирует конфигурацию DPI обхода
        
        Args:
            config: Конфигурация для валидации
        
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        if 'dpi_bypass' not in config:
            errors.append("Missing 'dpi_bypass' section")
            return False, errors
        
        dpi_config = config['dpi_bypass']
        
        if 'methods' not in dpi_config:
            errors.append("Missing 'methods' section")
            return False, errors
        
        methods = dpi_config['methods']
        
        for method, method_config in methods.items():
            if method in self.validators:
                method_errors = self.validators[method](method_config)
                errors.extend(method_errors)
        
        return len(errors) == 0, errors
    
    def validate_fragmentation_config(self, config):
        """Валидация конфигурации фрагментации"""
        errors = []
        
        if 'fragment_size' in config:
            if not isinstance(config['fragment_size'], int) or config['fragment_size'] <= 0:
                errors.append("fragment_size must be positive integer")
        
        if 'delay_ms' in config:
            if not isinstance(config['delay_ms'], (int, float)) or config['delay_ms'] < 0:
                errors.append("delay_ms must be non-negative number")
        
        return errors
```

## 📈 Тестирование и Отладка

### 1. Unit Тесты

#### Тестирование Фрагментации
```python
import unittest

class TestFragmentation(unittest.TestCase):
    def setUp(self):
        self.fragmenter = PacketFragmenter()
    
    def test_basic_fragmentation(self):
        """Тест базовой фрагментации"""
        data = b"Hello, World! This is a test message for fragmentation."
        fragments = self.fragmenter.fragment(data, fragment_size=10)
        
        # Проверка количества фрагментов
        expected_fragments = len(data) // 10 + (1 if len(data) % 10 else 0)
        self.assertEqual(len(fragments), expected_fragments)
        
        # Проверка восстановления данных
        reconstructed = b"".join(fragments)
        self.assertEqual(reconstructed, data)
    
    def test_fragmentation_with_delay(self):
        """Тест фрагментации с задержкой"""
        data = b"Test message with delay"
        start_time = time.time()
        fragments = self.fragmenter.fragment(data, fragment_size=5, delay_ms=10)
        end_time = time.time()
        
        # Проверка задержки
        expected_delay = (len(fragments) - 1) * 0.01  # 10ms in seconds
        actual_delay = end_time - start_time
        
        self.assertAlmostEqual(actual_delay, expected_delay, delta=0.1)
```

### 2. Интеграционные Тесты

#### Тестирование Интеграции
```python
class TestBypassIntegration(unittest.TestCase):
    def setUp(self):
        self.bypass_engine = DPIBypassEngine()
        self.test_target = ("example.com", 80)
    
    def test_end_to_end_bypass(self):
        """Тест полного цикла обхода"""
        test_data = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        
        # Тест различных методов
        methods = ['fragmentation', 'sni_splitting', 'header_obfuscation']
        
        for method in methods:
            with self.subTest(method=method):
                config = BypassConfig(method=method, target_host=self.test_target[0])
                
                # Попытка обхода
                result = self.bypass_engine.bypass_dpi(config, test_data)
                
                # Проверка результата
                self.assertIsNotNone(result)
                self.assertTrue(result.get('success', False))
                
                # Проверка целостности данных
                if 'processed_data' in result:
                    self.assertIsInstance(result['processed_data'], bytes)
```

## 📚 Заключение

Этот документ предоставляет технические детали реализации DPI обхода в RSecure. Ключевые аспекты включают:

- **Многослойный подход**: Комбинация различных техник обхода
- **Адаптивность**: Динамическая подстройка под сетевые условия
- **Производительность**: Оптимизация для высокой пропускной способности
- **Безопасность**: Защита от обнаружения и анализа
- **Масштабируемость**: Поддержка параллельной обработки

Для дополнительной информации смотрите:
- [DPI Bypass Guide](dpi-bypass-guide.md) - Пользовательское руководство
- [VPN/Proxy Guide](vpn-proxy-guide.md) - VPN и прокси интеграция
- [Traffic Obfuscation Guide](traffic-obfuscation-guide.md) - Обфускация трафика
