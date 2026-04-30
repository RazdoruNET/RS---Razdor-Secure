"""
Конфигурация pytest и общие фикстуры для тестов RSecure
"""

import pytest
import numpy as np
import sys
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any

# Добавление путей к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rsecure'))

@pytest.fixture
def sample_keystrokes():
    """Фикстура с образцами данных нажатий клавиш"""
    return [
        {'key': 'a', 'timestamp': 1000.0},
        {'key': 'b', 'timestamp': 1000.15},
        {'key': 'c', 'timestamp': 1000.25},
        {'key': 'd', 'timestamp': 1000.40},
        {'key': 'e', 'timestamp': 1000.55},
        {'key': 'f', 'timestamp': 1000.70},
        {'key': 'g', 'timestamp': 1000.85},
        {'key': 'h', 'timestamp': 1001.00},
        {'key': 'i', 'timestamp': 1001.20},
        {'key': 'j', 'timestamp': 1001.35}
    ]

@pytest.fixture
def sample_mouse_movements():
    """Фикстура с образцами данных движения мыши"""
    return [
        {'x': 100, 'y': 100, 'timestamp': 1000.0},
        {'x': 110, 'y': 105, 'timestamp': 1000.05},
        {'x': 125, 'y': 115, 'timestamp': 1000.10},
        {'x': 145, 'y': 130, 'timestamp': 1000.15},
        {'x': 170, 'y': 150, 'timestamp': 1000.20},
        {'x': 200, 'y': 175, 'timestamp': 1000.25},
        {'x': 235, 'y': 205, 'timestamp': 1000.30},
        {'x': 275, 'y': 240, 'timestamp': 1000.35},
        {'x': 320, 'y': 280, 'timestamp': 1000.40},
        {'x': 370, 'y': 325, 'timestamp': 1000.45}
    ]

@pytest.fixture
def sample_decisions():
    """Фикстура с образцами данных принятия решений"""
    return ['accept', 'reject', 'accept', 'accept', 'reject', 
            'accept', 'reject', 'accept', 'accept', 'reject']

@pytest.fixture
def sample_audio_data():
    """Фикстура с образцами аудио данных"""
    # Генерация тестового аудио сигнала
    sample_rate = 44100
    duration = 1.0  # 1 секунда
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Смешивание нескольких частот
    signal = (np.sin(2 * np.pi * 440 * t) +  # 440 Hz
              0.5 * np.sin(2 * np.pi * 880 * t) +  # 880 Hz
              0.3 * np.sin(2 * np.pi * 1760 * t))  # 1760 Hz
    
    # Добавление шума
    noise = np.random.normal(0, 0.1, len(t))
    signal += noise
    
    return signal.astype(np.float32)

@pytest.fixture
def sample_stereo_audio():
    """Фикстура со стерео аудио данными"""
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Левый канал - 440 Hz
    left_channel = np.sin(2 * np.pi * 440 * t)
    
    # Правый канал - 444 Hz (разница 4 Hz для бинауральных ритмов)
    right_channel = np.sin(2 * np.pi * 444 * t)
    
    # Добавление шума
    noise = np.random.normal(0, 0.05, len(t))
    left_channel += noise
    right_channel += noise
    
    return np.column_stack([left_channel, right_channel]).astype(np.float32)

@pytest.fixture
def sample_video_frames():
    """Фикстура с образцами видеокадров"""
    frames = []
    for i in range(10):
        # Генерация кадра с varying яркостью
        frame = np.random.randint(100 + i*10, 150 + i*10, (64, 64, 3), dtype=np.uint8)
        frames.append(frame)
    
    return np.array(frames)

@pytest.fixture
def mock_tensorflow():
    """Мок для TensorFlow"""
    mock_tf = MagicMock()
    
    # Мок для keras
    mock_keras = MagicMock()
    mock_tf.keras = mock_keras
    
    # Мок для слоев
    mock_layers = MagicMock()
    mock_keras.layers = mock_layers
    
    # Мок для моделей
    mock_models = MagicMock()
    mock_keras.models = mock_models
    
    # Мок для оптимизаторов
    mock_optimizers = MagicMock()
    mock_keras.optimizers = mock_optimizers
    
    # Мок для callbacks
    mock_callbacks = MagicMock()
    mock_keras.callbacks = mock_callbacks
    
    return mock_tf

@pytest.fixture
def mock_scipy():
    """Мок для scipy"""
    mock_scipy = MagicMock()
    
    # Мок для signal
    mock_signal = MagicMock()
    mock_scipy.signal = mock_signal
    
    # Мок для fft
    mock_fft = MagicMock()
    mock_scipy.fft = mock_fft
    
    return mock_scipy

@pytest.fixture
def mock_pywt():
    """Мок для PyWavelets"""
    mock_pywt = MagicMock()
    
    # Мок для cwt
    mock_pywt.cwt = MagicMock(return_value=(np.array([[1, 2, 3]]), np.array([4, 8, 12])))
    
    return mock_pywt

@pytest.fixture
def sample_network_data():
    """Фикстура с образцами сетевых данных"""
    return {
        'connections': [
            {'local_port': 80, 'remote_port': 8080, 'protocol': 'tcp', 'status': 'ESTABLISHED'},
            {'local_port': 443, 'remote_port': 3000, 'protocol': 'tcp', 'status': 'TIME_WAIT'},
            {'local_port': 22, 'remote_port': 54321, 'protocol': 'tcp', 'status': 'ESTABLISHED'}
        ],
        'packets': np.random.randint(100, 1000, 100),
        'bytes_transferred': np.random.randint(1000, 10000, 100)
    }

@pytest.fixture
def sample_system_metrics():
    """Фикстура с образцами системных метрик"""
    return {
        'cpu_percent': np.random.uniform(10, 80, 50),
        'memory_percent': np.random.uniform(20, 70, 50),
        'disk_usage': np.random.uniform(30, 60, 50),
        'network_io': np.random.uniform(100, 1000, 50),
        'process_count': np.random.randint(50, 200, 50)
    }

@pytest.fixture
def anomaly_data():
    """Фикстура с данными, содержащими аномалии"""
    # Нормальные данные
    normal_data = np.random.normal(0, 1, 100)
    
    # Вставка аномалий
    normal_data[20:25] = 5.0  # Выбросы
    normal_data[60:65] = -4.0  # Выбросы
    
    return normal_data

@pytest.fixture
def temporal_sequence_data():
    """Фикстура с временными последовательностями"""
    sequence_length = 50
    feature_dim = 10
    num_samples = 100
    
    return np.random.randn(num_samples, sequence_length, feature_dim)

@pytest.fixture
def classification_data():
    """Фикстура с данными для классификации"""
    num_samples = 200
    feature_dim = 20
    num_classes = 3
    
    X = np.random.randn(num_samples, feature_dim)
    y = np.random.randint(0, num_classes, num_samples)
    
    # One-hot кодирование для y
    y_one_hot = np.zeros((num_samples, num_classes))
    y_one_hot[np.arange(num_samples), y] = 1
    
    return X, y_one_hot

@pytest.fixture
def graph_data():
    """Фикстура с графовыми данными"""
    num_nodes = 10
    node_features = 8
    edge_features = 4
    
    # Матрица смежности
    adjacency = np.random.randint(0, 2, (num_nodes, num_nodes))
    adjacency = adjacency * (adjacency.T == adjacency)  # Симметричная матрица
    
    # Признаки узлов
    node_features_matrix = np.random.randn(num_nodes, node_features)
    
    # Признаки ребер
    edge_features_matrix = np.random.randn(num_nodes, num_nodes, edge_features)
    
    return {
        'nodes': node_features_matrix,
        'edges': edge_features_matrix,
        'adjacency': adjacency
    }

@pytest.fixture(scope="session")
def test_config():
    """Глобальная конфигурация тестов"""
    return {
        'random_seed': 42,
        'tolerance': 1e-6,
        'max_iterations': 1000,
        'sample_rate': 44100,
        'test_data_size': 100
    }

@pytest.fixture(autouse=True)
def set_random_seed(test_config):
    """Установка случайного seed для воспроизводимости"""
    np.random.seed(test_config['random_seed'])

@pytest.fixture
def mock_logger():
    """Мок для логгера"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    return logger

@pytest.fixture
def performance_metrics():
    """Фикстура для сбора метрик производительности"""
    return {
        'execution_time': [],
        'memory_usage': [],
        'accuracy': [],
        'precision': [],
        'recall': []
    }

@pytest.fixture
def integration_test_data():
    """Фикстура с данными для интеграционных тестов"""
    return {
        'user_session': {
            'keystrokes': [
                {'key': 'a', 'timestamp': 1000.0},
                {'key': 'b', 'timestamp': 1000.15},
                {'key': 'c', 'timestamp': 1000.25}
            ],
            'mouse_movements': [
                {'x': 100, 'y': 100, 'timestamp': 1000.0},
                {'x': 110, 'y': 105, 'timestamp': 1000.05}
            ],
            'decisions': ['accept', 'reject', 'accept']
        },
        'system_state': {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'network_activity': 1024,
            'active_processes': 156
        },
        'security_events': [
            {'type': 'suspicious_login', 'timestamp': 1000.0, 'severity': 'medium'},
            {'type': 'port_scan', 'timestamp': 1005.0, 'severity': 'high'},
            {'type': 'file_access', 'timestamp': 1010.0, 'severity': 'low'}
        ]
    }
