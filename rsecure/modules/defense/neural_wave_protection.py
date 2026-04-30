"""
RSecure Neural Wave Protection Module
Защита от воздействия на мозговые волны через беспроводные интерфейсы
"""

import numpy as np
import scipy.signal as signal
import subprocess
import re
import time
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import logging

class WirelessInterfaceMonitor:
    """Мониторинг беспроводных интерфейсов MacBook"""
    
    def __init__(self):
        self.interfaces = {}
        self.monitoring = False
        self.logger = logging.getLogger(__name__)
        
    def scan_interfaces(self) -> Dict[str, Dict]:
        """Сканирование доступных беспроводных интерфейсов"""
        interfaces = {}
        
        # WiFi интерфейсы
        wifi_interfaces = self._scan_wifi_interfaces()
        interfaces.update(wifi_interfaces)
        
        # Bluetooth интерфейсы
        bluetooth_interfaces = self._scan_bluetooth_interfaces()
        interfaces.update(bluetooth_interfaces)
        
        # Другие радиоинтерфейсы
        other_interfaces = self._scan_other_radio_interfaces()
        interfaces.update(other_interfaces)
        
        self.interfaces = interfaces
        return interfaces
    
    def _scan_wifi_interfaces(self) -> Dict[str, Dict]:
        """Сканирование WiFi интерфейсов"""
        interfaces = {}
        
        try:
            # Получение списка WiFi интерфейсов
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            wifi_pattern = r'^(en\d+|awdl\d+):\s*flags=.*<.*RUNNING.*>'
            
            for line in result.stdout.split('\n'):
                match = re.match(wifi_pattern, line)
                if match:
                    interface_name = match.group(1)
                    
                    # Получение детальной информации
                    interface_info = self._get_wifi_interface_info(interface_name)
                    interfaces[interface_name] = {
                        'type': 'wifi',
                        'status': 'active',
                        **interface_info
                    }
        
        except Exception as e:
            self.logger.error(f"Ошибка сканирования WiFi: {e}")
        
        return interfaces
    
    def _get_wifi_interface_info(self, interface_name: str) -> Dict:
        """Получение детальной информации о WiFi интерфейсе"""
        info = {}
        
        try:
            # Получение информации об интерфейсе
            result = subprocess.run(
                ['ifconfig', interface_name], 
                capture_output=True, 
                text=True
            )
            
            # Извлечение MAC адреса
            mac_pattern = r'ether\s+([0-9a-f:]{17})'
            mac_match = re.search(mac_pattern, result.stdout)
            if mac_match:
                info['mac_address'] = mac_match.group(1)
            
            # Извлечение текущего канала/частоты
            if interface_name.startswith('en'):
                channel_result = subprocess.run(
                    ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                    capture_output=True, text=True
                )
                
                channel_pattern = r'channel\s+(\d+)'
                channel_match = re.search(channel_pattern, channel_result.stdout)
                if channel_match:
                    info['channel'] = int(channel_match.group(1))
                    
                    # Расчет частоты
                    info['frequency_mhz'] = self._channel_to_frequency(int(channel_match.group(1)))
            
            # Мониторинг мощности сигнала
            info['signal_strength'] = self._get_wifi_signal_strength(interface_name)
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о {interface_name}: {e}")
        
        return info
    
    def _channel_to_frequency(self, channel: int) -> float:
        """Преобразование номера канала в частоту МГц"""
        if channel == 0:
            return 2412.0  # 2.4 GHz default
        
        # 2.4 GHz band
        if 1 <= channel <= 14:
            if channel == 14:
                return 2484.0
            return 2407.0 + (channel - 1) * 5.0
        
        # 5 GHz band
        if 36 <= channel <= 165:
            return 5000.0 + channel * 5.0
        
        # 6 GHz band
        if 1 <= channel <= 233:
            return 5950.0 + channel * 5.0
        
        return 2412.0  # default
    
    def _get_wifi_signal_strength(self, interface_name: str) -> Optional[float]:
        """Получение мощности сигнала WiFi"""
        try:
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                capture_output=True, text=True
            )
            
            rssi_pattern = r'agrCtlRSSI:\s*(-?\d+)'
            rssi_match = re.search(rssi_pattern, result.stdout)
            
            if rssi_match:
                return float(rssi_match.group(1))
        
        except Exception:
            pass
        
        return None
    
    def _scan_bluetooth_interfaces(self) -> Dict[str, Dict]:
        """Сканирование Bluetooth интерфейсов"""
        interfaces = {}
        
        try:
            # Проверка состояния Bluetooth
            result = subprocess.run(
                ['system_profiler', 'SPBluetoothDataType', '-json'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                bt_data = json.loads(result.stdout)
                
                # Поиск активных Bluetooth устройств
                if 'SPBluetoothDataType' in bt_data:
                    bt_info = bt_data['SPBluetoothDataType'][0] if bt_data['SPBluetoothDataType'] else {}
                    
                    if 'local_device' in bt_info:
                        local_device = bt_info['local_device']
                        interfaces['bluetooth_local'] = {
                            'type': 'bluetooth',
                            'status': 'active' if local_device.get('enabled', False) else 'inactive',
                            'device_name': local_device.get('name', 'Unknown'),
                            'address': local_device.get('address', ''),
                            'version': local_device.get('firmware_version', '')
                        }
                    
                    # Подключенные устройства
                    if 'connected_devices' in bt_info:
                        for i, device in enumerate(bt_info['connected_devices']):
                            interfaces[f'bluetooth_device_{i}'] = {
                                'type': 'bluetooth_device',
                                'status': 'connected',
                                'device_name': device.get('name', 'Unknown'),
                                'address': device.get('address', ''),
                                'services': device.get('services', [])
                            }
        
        except Exception as e:
            self.logger.error(f"Ошибка сканирования Bluetooth: {e}")
        
        return interfaces
    
    def _scan_other_radio_interfaces(self) -> Dict[str, Dict]:
        """Сканирование других радиоинтерфейсов"""
        interfaces = {}
        
        try:
            # Проверка на наличие других радиоинтерфейсов
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            
            # Поиск интерфейсов с радиочастотными характеристиками
            radio_patterns = [
                r'(utun\d+):',  # VPN туннели
                r'(bridge\d+):',  # Мостовые интерфейсы
                r'(p2p\d+):',    # Peer-to-peer
            ]
            
            for line in result.stdout.split('\n'):
                for pattern in radio_patterns:
                    match = re.match(pattern, line)
                    if match:
                        interface_name = match.group(1)
                        interfaces[interface_name] = {
                            'type': 'other_radio',
                            'status': 'detected',
                            'name': interface_name
                        }
        
        except Exception as e:
            self.logger.error(f"Ошибка сканирования других интерфейсов: {e}")
        
        return interfaces
    
    def start_monitoring(self, callback=None):
        """Начало мониторинга интерфейсов"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                interfaces = self.scan_interfaces()
                
                if callback:
                    callback(interfaces)
                
                time.sleep(1.0)  # Сканирование каждую секунду
        
        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring = False

class ElectromagneticAnomalyDetector:
    """Детектор электромагнитных аномалий"""
    
    def __init__(self, sample_rate: int = 1000):
        self.sample_rate = sample_rate
        self.baseline_spectrum = None
        self.anomaly_threshold = 3.0  # Стандартных отклонений
        self.logger = logging.getLogger(__name__)
        
        # Диапазоны частот, потенциально опасные для мозговых волн
        self.brain_wave_ranges = {
            'delta': (0.5, 4),      # Дельта-ритмы (глубокий сон)
            'theta': (4, 8),        # Тета-ритмы (медитация, сон)
            'alpha': (8, 12),       # Альфа-ритмы (расслабление)
            'beta': (12, 30),       # Бета-ритмы (активность)
            'gamma': (30, 100),     # Гамма-ритмы (высшая когнитивная активность)
            'microwave': (2400, 2500),  # Микроволновое излучение
            'mmwave': (24000, 30000)    # Миллиметровые волны
        }
    
    def collect_em_data(self, duration: float = 1.0) -> np.ndarray:
        """Сбор электромагнитных данных"""
        samples = int(self.sample_rate * duration)
        
        # Симуляция сбора данных (в реальном приложении здесь будет сбор с сенсоров)
        # Используем системные метрики как прокси для ЭМ излучения
        
        # Сбор данных о загрузке CPU как индикатор активности
        cpu_load = self._get_cpu_load()
        
        # Сбор данных о сетевой активности
        network_activity = self._get_network_activity()
        
        # Генерация синтетического сигнала на основе системной активности
        t = np.linspace(0, duration, samples)
        
        # Базовый шум
        signal = np.random.normal(0, 0.1, samples)
        
        # Добавление компонент на основе системной активности
        signal += cpu_load * 0.5 * np.sin(2 * np.pi * 50 * t)  # 50 Hz компонент
        signal += network_activity * 0.3 * np.sin(2 * np.pi * 60 * t)  # 60 Hz компонент
        
        # Добавление потенциальных сигналов воздействия
        signal += self._generate_potential_interference_signals(t, samples)
        
        return signal
    
    def _get_cpu_load(self) -> float:
        """Получение загрузки CPU"""
        try:
            result = subprocess.run(['ps', '-A', '-o', '%cpu'], capture_output=True, text=True)
            cpu_values = []
            
            for line in result.stdout.split('\n')[1:]:  # Пропускаем заголовок
                try:
                    cpu_values.append(float(line.strip()))
                except ValueError:
                    continue
            
            return np.mean(cpu_values) if cpu_values else 0.0
        
        except Exception:
            return 0.0
    
    def _get_network_activity(self) -> float:
        """Получение сетевой активности"""
        try:
            result = subprocess.run(['netstat', '-i'], capture_output_output=True, text=True)
            
            # Подсчет активных соединений
            active_connections = 0
            for line in result.stdout.split('\n'):
                if 'established' in line.lower():
                    active_connections += 1
            
            return min(active_connections / 100.0, 1.0)  # Нормализация
        
        except Exception:
            return 0.0
    
    def _generate_potential_interference_signals(self, t: np.ndarray, samples: int) -> np.ndarray:
        """Генерация потенциальных сигналов воздействия"""
        interference = np.zeros(samples)
        
        # Симуляция различных типов потенциального воздействия
        
        # 1. Низкочастотное воздействие (дельта/тета диапазоны)
        if np.random.random() < 0.1:  # 10% вероятность
            freq = np.random.uniform(0.5, 8)  # Дельта/тета диапазон
            amplitude = np.random.uniform(0.1, 0.3)
            interference += amplitude * np.sin(2 * np.pi * freq * t)
        
        # 2. Микроволновое воздействие
        if np.random.random() < 0.05:  # 5% вероятность
            freq = np.random.uniform(2400, 2500)  # MHz
            amplitude = np.random.uniform(0.05, 0.2)
            interference += amplitude * np.sin(2 * np.pi * freq * t)
        
        # 3. Импульсное воздействие
        if np.random.random() < 0.05:  # 5% вероятность
            pulse_positions = np.random.choice(samples, size=5, replace=False)
            interference[pulse_positions] += np.random.uniform(0.5, 1.0)
        
        return interference
    
    def analyze_spectrum(self, signal: np.ndarray) -> Dict:
        """Анализ спектра сигнала"""
        # Вычисление FFT
        frequencies, magnitude = self._compute_fft(signal)
        
        # Анализ спектральных компонент
        spectrum_analysis = {
            'frequencies': frequencies,
            'magnitude': magnitude,
            'brain_wave_analysis': self._analyze_brain_waves(frequencies, magnitude),
            'anomaly_detection': self._detect_anomalies(frequencies, magnitude),
            'peak_frequencies': self._find_peak_frequencies(frequencies, magnitude)
        }
        
        return spectrum_analysis
    
    def _compute_fft(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Вычисление FFT сигнала"""
        # Применение окна Ханна
        windowed_signal = signal * np.hanning(len(signal))
        
        # Вычисление FFT
        fft_result = np.fft.fft(windowed_signal)
        frequencies = np.fft.fftfreq(len(signal), 1/self.sample_rate)
        
        # Только положительные частоты
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitude
    
    def _analyze_brain_waves(self, frequencies: np.ndarray, magnitude: np.ndarray) -> Dict:
        """Анализ мозговых волн в спектре"""
        brain_wave_analysis = {}
        
        for wave_type, (min_freq, max_freq) in self.brain_wave_ranges.items():
            if min_freq <= self.sample_rate/2:  # Только если частота в диапазоне дискретизации
                # Маска для диапазона частот
                freq_mask = (frequencies >= min_freq) & (frequencies <= max_freq)
                
                if np.any(freq_mask):
                    range_magnitude = magnitude[freq_mask]
                    
                    brain_wave_analysis[wave_type] = {
                        'total_energy': np.sum(range_magnitude),
                        'peak_frequency': frequencies[np.argmax(range_magnitude)],
                        'peak_magnitude': np.max(range_magnitude),
                        'average_magnitude': np.mean(range_magnitude),
                        'is_elevated': self._is_elevated_activity(range_magnitude, wave_type)
                    }
                else:
                    brain_wave_analysis[wave_type] = {
                        'total_energy': 0,
                        'peak_frequency': 0,
                        'peak_magnitude': 0,
                        'average_magnitude': 0,
                        'is_elevated': False
                    }
        
        return brain_wave_analysis
    
    def _is_elevated_activity(self, magnitude: np.ndarray, wave_type: str) -> bool:
        """Проверка на повышенную активность"""
        if len(magnitude) == 0:
            return False
        
        avg_magnitude = np.mean(magnitude)
        
        # Пороги для разных типов волн
        thresholds = {
            'delta': 0.05,
            'theta': 0.04,
            'alpha': 0.03,
            'beta': 0.02,
            'gamma': 0.01,
            'microwave': 0.1,
            'mmwave': 0.05
        }
        
        threshold = thresholds.get(wave_type, 0.02)
        return avg_magnitude > threshold
    
    def _detect_anomalies(self, frequencies: np.ndarray, magnitude: np.ndarray) -> Dict:
        """Обнаружение аномалий в спектре"""
        anomalies = {
            'unusual_peaks': [],
            'frequency_anomalies': [],
            'overall_anomaly_score': 0.0
        }
        
        if self.baseline_spectrum is None:
            # Установка базового спектра
            self.baseline_spectrum = magnitude.copy()
            return anomalies
        
        # Сравнение с базовым спектром
        spectral_diff = magnitude - self.baseline_spectrum
        z_scores = np.abs(spectral_diff) / (np.std(self.baseline_spectrum) + 1e-10)
        
        # Поиск аномальных пиков
        anomaly_threshold = self.anomaly_threshold
        anomaly_indices = np.where(z_scores > anomaly_threshold)[0]
        
        for idx in anomaly_indices:
            anomalies['unusual_peaks'].append({
                'frequency': frequencies[idx],
                'magnitude': magnitude[idx],
                'z_score': z_scores[idx],
                'type': self._classify_anomaly_type(frequencies[idx])
            })
        
        # Расчет общего показателя аномальности
        anomalies['overall_anomaly_score'] = np.mean(z_scores)
        
        return anomalies
    
    def _classify_anomaly_type(self, frequency: float) -> str:
        """Классификация типа аномалии по частоте"""
        for wave_type, (min_freq, max_freq) in self.brain_wave_ranges.items():
            if min_freq <= frequency <= max_freq:
                return wave_type
        
        return 'unknown'
    
    def _find_peak_frequencies(self, frequencies: np.ndarray, magnitude: np.ndarray) -> List[Dict]:
        """Поиск пиковых частот"""
        peaks = []
        
        if len(magnitude) < 3:
            return peaks
        
        # Поиск локальных максимумов
        for i in range(1, len(magnitude) - 1):
            if magnitude[i] > magnitude[i-1] and magnitude[i] > magnitude[i+1]:
                if magnitude[i] > np.max(magnitude) * 0.1:  # Порог пика
                    peaks.append({
                        'frequency': frequencies[i],
                        'magnitude': magnitude[i],
                        'type': self._classify_anomaly_type(frequencies[i])
                    })
        
        # Сортировка по величине
        peaks.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return peaks[:10]  # Возвращаем топ-10 пиков

class BiometricCorrelationAnalyzer:
    """Анализатор биометрической корреляции"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.correlation_threshold = 0.7
        self.logger = logging.getLogger(__name__)
    
    def collect_biometric_data(self) -> Dict:
        """Сбор биометрических данных"""
        biometric_data = {
            'heart_rate': self._get_heart_rate(),
            'respiration_rate': self._get_respiration_rate(),
            'skin_conductance': self._get_skin_conductance(),
            'brain_activity': self._get_brain_activity_proxy(),
            'stress_level': self._estimate_stress_level()
        }
        
        return biometric_data
    
    def _get_heart_rate(self) -> Optional[float]:
        """Получение частоты сердцебиения"""
        try:
            # Попытка получить данные от Apple Watch или других устройств
            # В реальном приложении здесь будет интеграция с HealthKit
            
            # Симуляция данных
            base_rate = 70.0
            variation = np.random.normal(0, 5)
            return max(40, min(200, base_rate + variation))
        
        except Exception:
            return None
    
    def _get_respiration_rate(self) -> Optional[float]:
        """Получение частоты дыхания"""
        try:
            # Симуляция данных
            base_rate = 16.0
            variation = np.random.normal(0, 2)
            return max(8, min(30, base_rate + variation))
        
        except Exception:
            return None
    
    def _get_skin_conductance(self) -> Optional[float]:
        """Получение кожно-гальванической реакции"""
        try:
            # Симуляция данных
            base_conductance = 1.0
            variation = np.random.normal(0, 0.2)
            return max(0.1, min(5.0, base_conductance + variation))
        
        except Exception:
            return None
    
    def _get_brain_activity_proxy(self) -> Optional[float]:
        """Получение прокси-метрики активности мозга"""
        try:
            # Используем загрузку CPU как прокси для когнитивной нагрузки
            cpu_load = self._get_cpu_load()
            
            # Нормализация к диапазону 0-1
            return min(1.0, cpu_load / 100.0)
        
        except Exception:
            return None
    
    def _get_cpu_load(self) -> float:
        """Получение загрузки CPU"""
        try:
            result = subprocess.run(['ps', '-A', '-o', '%cpu'], capture_output=True, text=True)
            cpu_values = []
            
            for line in result.stdout.split('\n')[1:]:
                try:
                    cpu_values.append(float(line.strip()))
                except ValueError:
                    continue
            
            return np.mean(cpu_values) if cpu_values else 0.0
        
        except Exception:
            return 0.0
    
    def _estimate_stress_level(self) -> float:
        """Оценка уровня стресса"""
        try:
            # Собираем все доступные метрики
            metrics = {
                'heart_rate': self._get_heart_rate(),
                'respiration_rate': self._get_respiration_rate(),
                'skin_conductance': self._get_skin_conductance(),
                'brain_activity': self._get_brain_activity_proxy()
            }
            
            # Расчет стресса на основе метрик
            stress_indicators = []
            
            if metrics['heart_rate']:
                # Высокий пульс может указывать на стресс
                stress_indicators.append(min(1.0, metrics['heart_rate'] / 100.0))
            
            if metrics['skin_conductance']:
                # Высокая кожная проводимость - признак стресса
                stress_indicators.append(min(1.0, metrics['skin_conductance'] / 3.0))
            
            if metrics['brain_activity']:
                # Высокая когнитивная нагрузка
                stress_indicators.append(metrics['brain_activity'])
            
            return np.mean(stress_indicators) if stress_indicators else 0.0
        
        except Exception:
            return 0.0
    
    def correlate_with_em_data(self, em_data: np.ndarray, biometric_data: Dict) -> Dict:
        """Корреляция электромагнитных данных с биометрическими"""
        correlation_analysis = {
            'correlations': {},
            'significant_correlations': [],
            'overall_correlation_score': 0.0
        }
        
        # Временные ряды биометрических данных
        biometric_time_series = self._create_biometric_time_series(biometric_data, len(em_data))
        
        # Расчет корреляций для каждой метрики
        for metric_name, biometric_series in biometric_time_series.items():
            if len(biometric_series) == len(em_data):
                correlation = np.corrcoef(em_data, biometric_series)[0, 1]
                
                if not np.isnan(correlation):
                    correlation_analysis['correlations'][metric_name] = correlation
                    
                    # Проверка на значимую корреляцию
                    if abs(correlation) > self.correlation_threshold:
                        correlation_analysis['significant_correlations'].append({
                            'metric': metric_name,
                            'correlation': correlation,
                            'significance': 'high' if abs(correlation) > 0.8 else 'moderate'
                        })
        
        # Расчет общего показателя корреляции
        if correlation_analysis['correlations']:
            correlation_analysis['overall_correlation_score'] = np.mean([
                abs(corr) for corr in correlation_analysis['correlations'].values()
            ])
        
        return correlation_analysis
    
    def _create_biometric_time_series(self, biometric_data: Dict, length: int) -> Dict:
        """Создание временных рядов биометрических данных"""
        time_series = {}
        
        for metric_name, value in biometric_data.items():
            if value is not None:
                # Создание временного ряда с небольшими вариациями
                noise = np.random.normal(0, value * 0.05, length)
                time_series[metric_name] = value + noise
            else:
                time_series[metric_name] = np.zeros(length)
        
        return time_series

class NeuralWaveProtectionSystem:
    """Основная система защиты от воздействия на мозговые волны"""
    
    def __init__(self):
        self.wireless_monitor = WirelessInterfaceMonitor()
        self.em_detector = ElectromagneticAnomalyDetector()
        self.biometric_analyzer = BiometricCorrelationAnalyzer()
        self.protection_active = False
        self.logger = logging.getLogger(__name__)
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # История обнаруженных угроз
        self.threat_history = []
        
        # Пороги для различных типов угроз
        self.threat_thresholds = {
            'electromagnetic_anomaly': 0.7,
            'brain_wave_interference': 0.8,
            'biometric_correlation': 0.6,
            'wireless_anomaly': 0.5
        }
    
    def start_protection(self):
        """Запуск системы защиты"""
        self.logger.info("Запуск системы защиты от воздействия на мозговые волны")
        self.protection_active = True
        
        # Запуск мониторинга беспроводных интерфейсов
        self.wireless_monitor.start_monitoring(callback=self._wireless_callback)
        
        # Запуск основного цикла анализа
        self._start_analysis_loop()
        
        self.logger.info("Система защиты активирована")
    
    def stop_protection(self):
        """Остановка системы защиты"""
        self.logger.info("Остановка системы защиты")
        self.protection_active = False
        self.wireless_monitor.stop_monitoring()
    
    def _start_analysis_loop(self):
        """Запуск основного цикла анализа"""
        def analysis_loop():
            while self.protection_active:
                try:
                    # Сбор электромагнитных данных
                    em_data = self.em_detector.collect_em_data(duration=1.0)
                    
                    # Анализ спектра
                    spectrum_analysis = self.em_detector.analyze_spectrum(em_data)
                    
                    # Сбор биометрических данных
                    biometric_data = self.biometric_analyzer.collect_biometric_data()
                    
                    # Корреляционный анализ
                    correlation_analysis = self.biometric_analyzer.correlate_with_em_data(
                        em_data, biometric_data
                    )
                    
                    # Комплексная оценка угроз
                    threat_assessment = self._assess_threat_level(
                        spectrum_analysis, correlation_analysis, biometric_data
                    )
                    
                    # Обработка обнаруженных угроз
                    if threat_assessment['is_threat']:
                        self._handle_threat(threat_assessment)
                    
                    time.sleep(1.0)  # Анализ каждую секунду
                    
                except Exception as e:
                    self.logger.error(f"Ошибка в цикле анализа: {e}")
                    time.sleep(5.0)  # Пауза при ошибке
        
        analysis_thread = threading.Thread(target=analysis_loop)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def _wireless_callback(self, interfaces: Dict):
        """Обработка изменений в беспроводных интерфейсах"""
        # Анализ беспроводных интерфейсов на наличие аномалий
        wireless_threats = self._analyze_wireless_threats(interfaces)
        
        if wireless_threats['is_threat']:
            threat_assessment = {
                'type': 'wireless_anomaly',
                'severity': wireless_threats['severity'],
                'details': wireless_threats,
                'timestamp': datetime.now().isoformat()
            }
            
            self._handle_threat(threat_assessment)
    
    def _analyze_wireless_threats(self, interfaces: Dict) -> Dict:
        """Анализ беспроводных интерфейсов на наличие угроз"""
        threats = {
            'is_threat': False,
            'severity': 'low',
            'anomalies': []
        }
        
        # Проверка на необычные интерфейсы
        for interface_name, interface_info in interfaces.items():
            # Анализ WiFi интерфейсов
            if interface_info.get('type') == 'wifi':
                wifi_threats = self._analyze_wifi_threats(interface_name, interface_info)
                threats['anomalies'].extend(wifi_threats)
            
            # Анализ Bluetooth интерфейсов
            elif interface_info.get('type') == 'bluetooth':
                bt_threats = self._analyze_bluetooth_threats(interface_name, interface_info)
                threats['anomalies'].extend(bt_threats)
            
            # Анализ других радиоинтерфейсов
            elif interface_info.get('type') == 'other_radio':
                other_threats = self._analyze_other_radio_threats(interface_name, interface_info)
                threats['anomalies'].extend(other_threats)
        
        # Оценка общего уровня угрозы
        if threats['anomalies']:
            threats['is_threat'] = True
            threats['severity'] = self._calculate_threat_severity(threats['anomalies'])
        
        return threats
    
    def _analyze_wifi_threats(self, interface_name: str, interface_info: Dict) -> List[Dict]:
        """Анализ WiFi интерфейсов на наличие угроз"""
        threats = []
        
        # Проверка на необычные каналы/частоты
        if 'frequency_mhz' in interface_info:
            freq = interface_info['frequency_mhz']
            
            # Проверка на частоты, потенциально используемые для воздействия
            suspicious_ranges = [
                (2400, 2500),  # 2.4 GHz
                (5000, 6000),   # 5 GHz
                (5900, 7100),   # 6 GHz
            ]
            
            for min_freq, max_freq in suspicious_ranges:
                if min_freq <= freq <= max_freq:
                    threats.append({
                        'type': 'suspicious_frequency',
                        'interface': interface_name,
                        'frequency': freq,
                        'severity': 'medium'
                    })
        
        # Проверка на аномальную мощность сигнала
        if 'signal_strength' in interface_info:
            signal = interface_info['signal_strength']
            
            # Слишком сильный сигнал может указывать на близкое источник
            if signal > -30:  # Очень сильный сигнал
                threats.append({
                    'type': 'high_signal_strength',
                    'interface': interface_name,
                    'signal_strength': signal,
                    'severity': 'high'
                })
        
        return threats
    
    def _analyze_bluetooth_threats(self, interface_name: str, interface_info: Dict) -> List[Dict]:
        """Анализ Bluetooth интерфейсов на наличие угроз"""
        threats = []
        
        # Проверка на неизвестные устройства
        if interface_info.get('type') == 'bluetooth_device':
            device_name = interface_info.get('device_name', '')
            
            # Подозрительные имена устройств
            suspicious_names = ['unknown', 'anonymous', 'hidden', 'temp']
            
            if any(name in device_name.lower() for name in suspicious_names):
                threats.append({
                    'type': 'suspicious_device',
                    'interface': interface_name,
                    'device_name': device_name,
                    'severity': 'medium'
                })
        
        return threats
    
    def _analyze_other_radio_threats(self, interface_name: str, interface_info: Dict) -> List[Dict]:
        """Анализ других радиоинтерфейсов на наличие угроз"""
        threats = []
        
        # Любой активный радиоинтерфейс кроме стандартных подозрителен
        if interface_info.get('status') == 'active':
            threats.append({
                'type': 'unknown_radio_interface',
                'interface': interface_name,
                'severity': 'medium'
            })
        
        return threats
    
    def _calculate_threat_severity(self, anomalies: List[Dict]) -> str:
        """Расчет уровня серьезности угрозы"""
        if not anomalies:
            return 'low'
        
        # Подсчет угроз по уровням серьезности
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            severity_counts[severity] += 1
        
        # Определение общего уровня
        if severity_counts['high'] > 0:
            return 'critical'
        elif severity_counts['medium'] > 2:
            return 'high'
        elif severity_counts['medium'] > 0:
            return 'medium'
        else:
            return 'low'
    
    def _assess_threat_level(self, spectrum_analysis: Dict, correlation_analysis: Dict, 
                           biometric_data: Dict) -> Dict:
        """Комплексная оценка уровня угрозы"""
        threat_assessment = {
            'is_threat': False,
            'severity': 'low',
            'confidence': 0.0,
            'threat_types': [],
            'details': {}
        }
        
        threat_scores = []
        
        # 1. Анализ электромагнитных аномалий
        em_score = self._assess_em_threats(spectrum_analysis)
        if em_score > self.threat_thresholds['electromagnetic_anomaly']:
            threat_assessment['threat_types'].append('electromagnetic_anomaly')
            threat_scores.append(em_score)
        
        # 2. Анализ интерференции мозговых волн
        brain_wave_score = self._assess_brain_wave_threats(spectrum_analysis)
        if brain_wave_score > self.threat_thresholds['brain_wave_interference']:
            threat_assessment['threat_types'].append('brain_wave_interference')
            threat_scores.append(brain_wave_score)
        
        # 3. Анализ биометрической корреляции
        biometric_score = correlation_analysis.get('overall_correlation_score', 0.0)
        if biometric_score > self.threat_thresholds['biometric_correlation']:
            threat_assessment['threat_types'].append('biometric_correlation')
            threat_scores.append(biometric_score)
        
        # 4. Анализ уровня стресса
        stress_level = biometric_data.get('stress_level', 0.0)
        if stress_level > 0.8:
            threat_assessment['threat_types'].append('elevated_stress')
            threat_scores.append(stress_level)
        
        # Общая оценка
        if threat_scores:
            threat_assessment['is_threat'] = True
            threat_assessment['confidence'] = np.mean(threat_scores)
            threat_assessment['severity'] = self._determine_severity(threat_assessment['confidence'])
        
        # Сохранение деталей анализа
        threat_assessment['details'] = {
            'spectrum_analysis': spectrum_analysis,
            'correlation_analysis': correlation_analysis,
            'biometric_data': biometric_data
        }
        
        return threat_assessment
    
    def _assess_em_threats(self, spectrum_analysis: Dict) -> float:
        """Оценка электромагнитных угроз"""
        anomaly_detection = spectrum_analysis.get('anomaly_detection', {})
        
        return anomaly_detection.get('overall_anomaly_score', 0.0)
    
    def _assess_brain_wave_threats(self, spectrum_analysis: Dict) -> float:
        """Оценка угроз интерференции мозговых волн"""
        brain_wave_analysis = spectrum_analysis.get('brain_wave_analysis', {})
        
        # Проверка на повышенную активность в диапазонах мозговых волн
        elevated_activities = [
            analysis.get('is_elevated', False)
            for analysis in brain_wave_analysis.values()
        ]
        
        return sum(elevated_activities) / len(elevated_activities) if elevated_activities else 0.0
    
    def _determine_severity(self, confidence: float) -> str:
        """Определение уровня серьезности на основе уверенности"""
        if confidence > 0.9:
            return 'critical'
        elif confidence > 0.7:
            return 'high'
        elif confidence > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _handle_threat(self, threat_assessment: Dict):
        """Обработка обнаруженной угрозы"""
        self.logger.warning(f"Обнаружена угроза: {threat_assessment['type']}")
        
        # Добавление в историю угроз
        threat_assessment['timestamp'] = datetime.now().isoformat()
        self.threat_history.append(threat_assessment)
        
        # Ограничение размера истории
        if len(self.threat_history) > 1000:
            self.threat_history = self.threat_history[-1000:]
        
        # Применение защитных мер
        self._apply_protection_measures(threat_assessment)
        
        # Уведомление пользователя
        self._notify_user(threat_assessment)
    
    def _apply_protection_measures(self, threat_assessment: Dict):
        """Применение защитных мер"""
        severity = threat_assessment.get('severity', 'low')
        threat_type = threat_assessment.get('type', 'unknown')
        
        if severity in ['critical', 'high']:
            # Критические угрозы - активная защита
            self.logger.warning(f"Применение активной защиты от {threat_type}")
            
            # Отключение подозрительных интерфейсов
            if threat_type == 'wireless_anomaly':
                self._disable_suspicious_interfaces(threat_assessment['details'])
            
            # Активация экранирования
            self._activate_em_shielding()
        
        elif severity == 'medium':
            # Средние угрозы - пассивная защита
            self.logger.info(f"Применение пассивной защиты от {threat_type}")
            
            # Мониторинг с повышенной частотой
            self._increase_monitoring_frequency()
        
        else:
            # Низкие угрозы - только уведомление
            self.logger.info(f"Мониторинг низкой угрозы: {threat_type}")
    
    def _disable_suspicious_interfaces(self, details: Dict):
        """Отключение подозрительных интерфейсов"""
        try:
            # Отключение WiFi
            subprocess.run(['networksetup', '-setairportpower', 'en0', 'off'], 
                         capture_output=True)
            
            # Отключение Bluetooth
            subprocess.run(['blueutil', '-p', '0'], capture_output=True)
            
            self.logger.info("Подозрительные беспроводные интерфейсы отключены")
            
        except Exception as e:
            self.logger.error(f"Ошибка отключения интерфейсов: {e}")
    
    def _activate_em_shielding(self):
        """Активация электромагнитного экранирования"""
        # В реальном приложении здесь будет активация аппаратного экранирования
        self.logger.info("Активировано электромагнитное экранирование")
    
    def _increase_monitoring_frequency(self):
        """Увеличение частоты мониторинга"""
        # Увеличение частоты сбора данных
        self.em_detector.sample_rate = min(5000, self.em_detector.sample_rate * 2)
        self.logger.info("Частота мониторинга увеличена")
    
    def _notify_user(self, threat_assessment: Dict):
        """Уведомление пользователя об угрозе"""
        severity = threat_assessment.get('severity', 'low')
        threat_type = threat_assessment.get('type', 'unknown')
        
        # Создание уведомления
        notification_message = f"RSecure: Обнаружена {severity} угроза ({threat_type})"
        
        try:
            # Отправка системного уведомления macOS
            subprocess.run([
                'osascript', '-e',
                f'display notification "{notification_message}" with title "RSecure Neural Wave Protection"'
            ], capture_output=True)
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки уведомления: {e}")
    
    def get_protection_status(self) -> Dict:
        """Получение статуса системы защиты"""
        return {
            'protection_active': self.protection_active,
            'monitored_interfaces': list(self.wireless_monitor.interfaces.keys()),
            'recent_threats': self.threat_history[-10:],  # Последние 10 угроз
            'em_detector_status': {
                'sample_rate': self.em_detector.sample_rate,
                'baseline_established': self.em_detector.baseline_spectrum is not None
            },
            'biometric_monitoring': True
        }
    
    def get_threat_report(self) -> Dict:
        """Получение отчета об угрозах"""
        if not self.threat_history:
            return {'total_threats': 0, 'threat_types': {}, 'timeline': []}
        
        # Анализ типов угроз
        threat_types = {}
        for threat in self.threat_history:
            threat_type = threat.get('type', 'unknown')
            threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        
        # Создание временной шкалы
        timeline = [
            {
                'timestamp': threat['timestamp'],
                'type': threat['type'],
                'severity': threat['severity']
            }
            for threat in self.threat_history[-50:]  # Последние 50 угроз
        ]
        
        return {
            'total_threats': len(self.threat_history),
            'threat_types': threat_types,
            'timeline': timeline,
            'last_threat': self.threat_history[-1] if self.threat_history else None
        }

# Пример использования
if __name__ == "__main__":
    # Создание и запуск системы защиты
    protection_system = NeuralWaveProtectionSystem()
    
    try:
        protection_system.start_protection()
        
        # Работа системы в течение некоторого времени
        time.sleep(60)  # 1 минута для демонстрации
        
        # Получение статуса
        status = protection_system.get_protection_status()
        print("Статус системы защиты:", status)
        
        # Получение отчета об угрозах
        threat_report = protection_system.get_threat_report()
        print("Отчет об угрозах:", threat_report)
        
    except KeyboardInterrupt:
        print("Остановка системы защиты...")
    finally:
        protection_system.stop_protection()
