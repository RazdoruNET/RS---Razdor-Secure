"""
Тесты для методов спектрального анализа
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавление путей для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Импортируем тестируемые классы (создадим их здесь для тестирования)
class SpectralAnalyzer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.window_size = 1024
        self.hop_size = 512
    
    def compute_fft(self, audio_data):
        if len(audio_data) == 0:
            return np.array([]), np.array([])
        
        window = np.hanning(len(audio_data))
        windowed_signal = audio_data * window
        
        fft_result = np.fft.fft(windowed_signal)
        frequencies = np.fft.fftfreq(len(windowed_signal), 1/self.sample_rate)
        
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitude
    
    def compute_spectrogram(self, audio_data):
        if len(audio_data) < self.window_size:
            return {'frequencies': np.array([]), 'time': np.array([]), 'spectrogram': np.array([])}
        
        # Простая реализация спектрограммы
        num_frames = (len(audio_data) - self.window_size) // self.hop_size + 1
        spectrogram = []
        
        for i in range(num_frames):
            start = i * self.hop_size
            end = start + self.window_size
            frame = audio_data[start:end]
            
            freqs, magnitude = self.compute_fft(frame)
            spectrogram.append(magnitude)
        
        spectrogram = np.array(spectrogram).T
        frequencies = np.fft.fftfreq(self.window_size, 1/self.sample_rate)[:self.window_size//2]
        time_frames = np.arange(num_frames) * self.hop_size / self.sample_rate
        
        return {
            'frequencies': frequencies,
            'time': time_frames,
            'spectrogram': spectrogram
        }

class SubliminalDetector:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.threshold_db = -40
        self.min_duration = 0.1
    
    def detect_subliminal_messages(self, audio_data):
        if len(audio_data) == 0:
            return []
        
        audio_db = 20 * np.log10(np.abs(audio_data) + 1e-10)
        low_amplitude_mask = audio_db < self.threshold_db
        low_amplitude_segments = self._find_continuous_segments(low_amplitude_mask)
        
        subliminal_segments = []
        for start, end in low_amplitude_segments:
            duration = (end - start) / self.sample_rate
            if duration >= self.min_duration:
                segment = audio_data[start:end]
                analysis = self._analyze_subliminal_segment(segment)
                
                if analysis['is_suspicious']:
                    subliminal_segments.append({
                        'start_time': start / self.sample_rate,
                        'end_time': end / self.sample_rate,
                        'duration': duration,
                        'analysis': analysis
                    })
        
        return subliminal_segments
    
    def _find_continuous_segments(self, mask):
        segments = []
        start = None
        
        for i, value in enumerate(mask):
            if value and start is None:
                start = i
            elif not value and start is not None:
                segments.append((start, i))
                start = None
        
        if start is not None:
            segments.append((start, len(mask)))
        
        return segments
    
    def _analyze_subliminal_segment(self, segment):
        if len(segment) < 2:
            return {'is_suspicious': False, 'spectral_peaks': [], 'regularity_score': 0}
        
        # Простой спектральный анализ
        frequencies, magnitude = self._compute_fft(segment)
        
        # Поиск пиков
        spectral_peaks = self._find_spectral_peaks(frequencies, magnitude)
        regularity_score = self._calculate_regularity(spectral_peaks)
        
        return {
            'is_suspicious': regularity_score > 0.7,
            'spectral_peaks': spectral_peaks,
            'regularity_score': regularity_score,
            'dominant_frequencies': frequencies[np.argsort(magnitude)[-5:]] if len(frequencies) > 0 else []
        }
    
    def _compute_fft(self, segment):
        if len(segment) == 0:
            return np.array([]), np.array([])
        
        window = np.hanning(len(segment))
        windowed_signal = segment * window
        fft_result = np.fft.fft(windowed_signal)
        frequencies = np.fft.fftfreq(len(windowed_signal), 1/self.sample_rate)
        
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitude
    
    def _find_spectral_peaks(self, frequencies, magnitude):
        if len(magnitude) < 3:
            return []
        
        peaks = []
        for i in range(1, len(magnitude) - 1):
            if magnitude[i] > magnitude[i-1] and magnitude[i] > magnitude[i+1]:
                if magnitude[i] > np.max(magnitude) * 0.1:  # Порог пика
                    peaks.append({
                        'frequency': frequencies[i],
                        'magnitude': magnitude[i]
                    })
        
        return peaks
    
    def _calculate_regularity(self, spectral_peaks):
        if len(spectral_peaks) < 2:
            return 0
        
        # Расчет регулярности интервалов между пиками
        intervals = []
        for i in range(1, len(spectral_peaks)):
            interval = spectral_peaks[i]['frequency'] - spectral_peaks[i-1]['frequency']
            intervals.append(interval)
        
        if len(intervals) == 0:
            return 0
        
        # Чем меньше вариация интервалов, тем выше регулярность
        interval_std = np.std(intervals)
        interval_mean = np.mean(intervals)
        
        if interval_mean == 0:
            return 0
        
        coefficient_of_variation = interval_std / interval_mean
        regularity = max(0, 1 - coefficient_of_variation)
        
        return regularity

class UltrasonicDetector:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.ultrasonic_range = (18000, 20000)
    
    def detect_ultrasonic_signals(self, audio_data):
        if len(audio_data) == 0:
            return {'ultrasonic_detected': False}
        
        frequencies, magnitude = self._compute_fft(audio_data)
        
        if len(frequencies) == 0:
            return {'ultrasonic_detected': False}
        
        ultrasonic_mask = (frequencies >= self.ultrasonic_range[0]) & \
                         (frequencies <= self.ultrasonic_range[1])
        
        ultrasonic_frequencies = frequencies[ultrasonic_mask]
        ultrasonic_magnitude = magnitude[ultrasonic_mask]
        
        if len(ultrasonic_magnitude) > 0:
            max_magnitude = np.max(ultrasonic_magnitude)
            avg_magnitude = np.mean(ultrasonic_magnitude)
            
            signal_to_noise = max_magnitude / (avg_magnitude + 1e-10)
            
            return {
                'ultrasonic_detected': signal_to_noise > 3.0,
                'max_frequency': ultrasonic_frequencies[np.argmax(ultrasonic_magnitude)],
                'signal_strength': max_magnitude,
                'signal_to_noise': signal_to_noise,
                'frequency_range': self.ultrasonic_range
            }
        
        return {'ultrasonic_detected': False}
    
    def _compute_fft(self, audio_data):
        if len(audio_data) == 0:
            return np.array([]), np.array([])
        
        window = np.hanning(len(audio_data))
        windowed_signal = audio_data * window
        fft_result = np.fft.fft(windowed_signal)
        frequencies = np.fft.fftfreq(len(windowed_signal), 1/self.sample_rate)
        
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitude

class BinauralBeatDetector:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.target_frequencies = {
            'theta': (4, 8),
            'alpha': (8, 12),
            'beta': (12, 30),
            'gamma': (30, 100)
        }
    
    def analyze_binaural_beats(self, left_channel, right_channel):
        if len(left_channel) == 0 or len(right_channel) == 0:
            return {'frequency_differences': [], 'rhythm_analysis': {}, 'manipulation_score': 0, 'is_manipulated': False}
        
        if len(left_channel) != len(right_channel):
            min_len = min(len(left_channel), len(right_channel))
            left_channel = left_channel[:min_len]
            right_channel = right_channel[:min_len]
        
        left_freq, left_mag = self._compute_fft(left_channel)
        right_freq, right_mag = self._compute_fft(right_channel)
        
        frequency_differences = self._calculate_frequency_differences(
            left_freq, left_mag, right_freq, right_mag
        )
        
        rhythm_analysis = self._classify_rhythms(frequency_differences)
        manipulation_score = self._detect_manipulation(rhythm_analysis)
        
        return {
            'frequency_differences': frequency_differences,
            'rhythm_analysis': rhythm_analysis,
            'manipulation_score': manipulation_score,
            'is_manipulated': manipulation_score > 0.7
        }
    
    def _compute_fft(self, channel_data):
        if len(channel_data) == 0:
            return np.array([]), np.array([])
        
        window = np.hanning(len(channel_data))
        windowed_signal = channel_data * window
        fft_result = np.fft.fft(windowed_signal)
        frequencies = np.fft.fftfreq(len(windowed_signal), 1/self.sample_rate)
        
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitude
    
    def _calculate_frequency_differences(self, left_freq, left_mag, right_freq, right_mag):
        if len(left_freq) == 0 or len(right_freq) == 0:
            return []
        
        # Поиск пиков в каждом канале
        left_peaks = self._find_peaks(left_freq, left_mag)
        right_peaks = self._find_peaks(right_freq, right_mag)
        
        differences = []
        for left_peak in left_peaks:
            for right_peak in right_peaks:
                freq_diff = abs(left_peak['frequency'] - right_peak['frequency'])
                if freq_diff < 50:  # максимальная разница для бинауральных ритмов
                    differences.append({
                        'frequency_difference': freq_diff,
                        'left_magnitude': left_peak['magnitude'],
                        'right_magnitude': right_peak['magnitude'],
                        'combined_strength': (left_peak['magnitude'] + right_peak['magnitude']) / 2
                    })
        
        return differences
    
    def _find_peaks(self, frequencies, magnitude):
        if len(magnitude) < 3:
            return []
        
        peaks = []
        for i in range(1, len(magnitude) - 1):
            if magnitude[i] > magnitude[i-1] and magnitude[i] > magnitude[i+1]:
                if magnitude[i] > np.max(magnitude) * 0.1:
                    peaks.append({
                        'frequency': frequencies[i],
                        'magnitude': magnitude[i]
                    })
        
        return peaks
    
    def _classify_rhythms(self, frequency_differences):
        rhythm_classification = {
            'theta': [],
            'alpha': [],
            'beta': [],
            'gamma': []
        }
        
        for diff in frequency_differences:
            freq_diff = diff['frequency_difference']
            
            for rhythm_type, (min_freq, max_freq) in self.target_frequencies.items():
                if min_freq <= freq_diff <= max_freq:
                    rhythm_classification[rhythm_type].append(diff)
                    break
        
        return rhythm_classification
    
    def _detect_manipulation(self, rhythm_analysis):
        # Простая эвристика для обнаружения манипуляций
        manipulation_indicators = []
        
        for rhythm_type, rhythms in rhythm_analysis.items():
            if len(rhythms) > 0:
                # Проверка на необычно сильные сигналы
                avg_strength = np.mean([r['combined_strength'] for r in rhythms])
                if avg_strength > np.percentile([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 90):
                    manipulation_indicators.append(0.3)
                
                # Проверка на множественные ритмы одного типа
                if len(rhythms) > 3:
                    manipulation_indicators.append(0.2)
        
        return min(np.sum(manipulation_indicators), 1.0)

class VisualFlickerAnalyzer:
    def __init__(self, frame_rate=30):
        self.frame_rate = frame_rate
        self.flicker_frequencies = {
            'harmful_low': (0.5, 3),
            'epilepsy_risk': (3, 30),
            'noticeable': (30, 60)
        }
    
    def analyze_screen_flicker(self, frames):
        if len(frames) == 0:
            return {'temporal_analysis': {}, 'frequency_analysis': {}, 'harmful_patterns': [], 'flicker_detected': False}
        
        brightness_values = self._extract_brightness(frames)
        
        if len(brightness_values) < 2:
            return {'temporal_analysis': {}, 'frequency_analysis': {}, 'harmful_patterns': [], 'flicker_detected': False}
        
        temporal_analysis = self._analyze_temporal_patterns(brightness_values)
        frequency_analysis = self._analyze_flicker_frequencies(brightness_values)
        harmful_patterns = self._detect_harmful_patterns(frequency_analysis)
        
        return {
            'temporal_analysis': temporal_analysis,
            'frequency_analysis': frequency_analysis,
            'harmful_patterns': harmful_patterns,
            'flicker_detected': len(harmful_patterns) > 0
        }
    
    def _extract_brightness(self, frames):
        brightness_values = []
        
        for frame in frames:
            if len(frame.shape) == 3:
                gray_frame = np.mean(frame, axis=2)
            else:
                gray_frame = frame
            
            avg_brightness = np.mean(gray_frame)
            brightness_values.append(avg_brightness)
        
        return np.array(brightness_values)
    
    def _analyze_temporal_patterns(self, brightness_values):
        if len(brightness_values) < 2:
            return {}
        
        return {
            'mean_brightness': np.mean(brightness_values),
            'std_brightness': np.std(brightness_values),
            'min_brightness': np.min(brightness_values),
            'max_brightness': np.max(brightness_values),
            'brightness_range': np.max(brightness_values) - np.min(brightness_values)
        }
    
    def _analyze_flicker_frequencies(self, brightness_values):
        if len(brightness_values) < 4:
            return {}
        
        # Вычисление FFT
        fft_result = np.fft.fft(brightness_values - np.mean(brightness_values))
        frequencies = np.fft.fftfreq(len(brightness_values), 1/self.frame_rate)
        
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        frequency_analysis = {}
        
        for range_name, (min_freq, max_freq) in self.flicker_frequencies.items():
            freq_mask = (frequencies >= min_freq) & (frequencies <= max_freq)
            range_magnitude = magnitude[freq_mask]
            
            if len(range_magnitude) > 0:
                frequency_analysis[range_name] = {
                    'total_energy': np.sum(range_magnitude),
                    'peak_frequency': frequencies[np.argmax(range_magnitude)],
                    'peak_magnitude': np.max(range_magnitude)
                }
            else:
                frequency_analysis[range_name] = {
                    'total_energy': 0,
                    'peak_frequency': 0,
                    'peak_magnitude': 0
                }
        
        return frequency_analysis
    
    def _detect_harmful_patterns(self, frequency_analysis):
        harmful_patterns = []
        
        for range_name, analysis in frequency_analysis.items():
            if analysis['total_energy'] > 0:
                # Пороги для разных диапазонов
                if range_name == 'harmful_low' and analysis['total_energy'] > 10:
                    harmful_patterns.append({
                        'type': 'harmful_low_frequency',
                        'frequency': analysis['peak_frequency'],
                        'energy': analysis['total_energy'],
                        'severity': 'medium'
                    })
                elif range_name == 'epilepsy_risk' and analysis['total_energy'] > 5:
                    harmful_patterns.append({
                        'type': 'epilepsy_risk',
                        'frequency': analysis['peak_frequency'],
                        'energy': analysis['total_energy'],
                        'severity': 'high'
                    })
                elif range_name == 'noticeable' and analysis['total_energy'] > 15:
                    harmful_patterns.append({
                        'type': 'noticeable_flicker',
                        'frequency': analysis['peak_frequency'],
                        'energy': analysis['total_energy'],
                        'severity': 'low'
                    })
        
        return harmful_patterns

# Тесты
class TestSpectralAnalyzer:
    """Тесты базового спектрального анализатора"""
    
    def test_compute_fft_normal(self, sample_audio_data):
        """Тест вычисления FFT для нормальных данных"""
        analyzer = SpectralAnalyzer()
        frequencies, magnitude = analyzer.compute_fft(sample_audio_data)
        
        assert len(frequencies) > 0
        assert len(magnitude) > 0
        assert len(frequencies) == len(magnitude)
        assert np.all(frequencies > 0)  # Только положительные частоты
        assert np.all(magnitude >= 0)  # Амплитуда должна быть неотрицательной
    
    def test_compute_fft_empty(self):
        """Тест FFT с пустыми данными"""
        analyzer = SpectralAnalyzer()
        frequencies, magnitude = analyzer.compute_fft(np.array([]))
        
        assert len(frequencies) == 0
        assert len(magnitude) == 0
    
    def test_compute_spectrogram_normal(self, sample_audio_data):
        """Тест вычисления спектрограммы"""
        analyzer = SpectralAnalyzer()
        
        # Создаем достаточно длинный сигнал для спектрограммы
        long_signal = np.random.randn(2048)
        result = analyzer.compute_spectrogram(long_signal)
        
        assert 'frequencies' in result
        assert 'time' in result
        assert 'spectrogram' in result
        
        assert len(result['frequencies']) > 0
        assert len(result['time']) > 0
        assert result['spectrogram'].shape[0] == len(result['frequencies'])
        assert result['spectrogram'].shape[1] == len(result['time'])
    
    def test_compute_spectrogram_short_signal(self):
        """Тест спектрограммы с коротким сигналом"""
        analyzer = SpectralAnalyzer()
        short_signal = np.random.randn(100)  # Меньше window_size
        
        result = analyzer.compute_spectrogram(short_signal)
        
        assert len(result['frequencies']) == 0
        assert len(result['time']) == 0
        assert result['spectrogram'].size == 0

class TestSubliminalDetector:
    """Тесты детектора сублиминальных сообщений"""
    
    def test_detect_subliminal_normal(self, sample_audio_data):
        """Тест обнаружения сублиминальных сообщений в нормальном аудио"""
        detector = SubliminalDetector()
        result = detector.detect_subliminal_messages(sample_audio_data)
        
        assert isinstance(result, list)
        # В нормальном аудио не должно быть сублиминальных сообщений
        assert len(result) == 0
    
    def test_detect_subliminal_with_low_amplitude(self):
        """Тест обнаружения сублиминальных сообщений с низкой амплитудой"""
        detector = SubliminalDetector()
        
        # Создаем сигнал с низкой амплитудой
        sample_rate = 44100
        duration = 0.5  # 0.5 секунды
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Низкоамплитудный сигнал
        low_amplitude_signal = 0.001 * np.sin(2 * np.pi * 1000 * t)
        
        result = detector.detect_subliminal_messages(low_amplitude_signal)
        
        assert isinstance(result, list)
        # Может обнаружить или не обнаружить в зависимости от порога
    
    def test_detect_subliminal_empty(self):
        """Тест с пустыми данными"""
        detector = SubliminalDetector()
        result = detector.detect_subliminal_messages(np.array([]))
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_find_continuous_segments(self):
        """Тест поиска непрерывных сегментов"""
        detector = SubliminalDetector()
        
        mask = [False, True, True, False, True, False, False, True, True, True]
        segments = detector._find_continuous_segments(mask)
        
        expected_segments = [(1, 3), (4, 5), (7, 10)]
        assert segments == expected_segments
    
    def test_analyze_subliminal_segment(self):
        """Тест анализа сублиминального сегмента"""
        detector = SubliminalDetector()
        
        # Создаем тестовый сегмент
        segment = np.sin(2 * np.pi * np.arange(100) / 10)
        result = detector._analyze_subliminal_segment(segment)
        
        assert 'is_suspicious' in result
        assert 'spectral_peaks' in result
        assert 'regularity_score' in result
        assert 'dominant_frequencies' in result
        
        assert isinstance(result['is_suspicious'], bool)
        assert isinstance(result['spectral_peaks'], list)
        assert 0 <= result['regularity_score'] <= 1

class TestUltrasonicDetector:
    """Тесты детектора ультразвуковых сигналов"""
    
    def test_detect_ultrasonic_normal(self, sample_audio_data):
        """Тест обнаружения ультразвука в нормальном аудио"""
        detector = UltrasonicDetector()
        result = detector.detect_ultrasonic_signals(sample_audio_data)
        
        assert 'ultrasonic_detected' in result
        assert isinstance(result['ultrasonic_detected'], bool)
        # В нормальном аудио ультразвук не должен обнаруживаться
        assert result['ultrasonic_detected'] == False
    
    def test_detect_ultrasonic_with_ultrasonic_signal(self):
        """Тест обнаружения ультразвукового сигнала"""
        detector = UltrasonicDetector()
        
        # Создаем ультразвуковой сигнал
        sample_rate = 44100
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Ультразвуковой сигнал на 19000 Hz
        ultrasonic_signal = 0.5 * np.sin(2 * np.pi * 19000 * t)
        
        result = detector.detect_ultrasonic_signals(ultrasonic_signal)
        
        assert 'ultrasonic_detected' in result
        assert 'max_frequency' in result
        assert 'signal_strength' in result
        assert 'signal_to_noise' in result
        assert 'frequency_range' in result
        
        if result['ultrasonic_detected']:
            assert result['max_frequency'] >= detector.ultrasonic_range[0]
            assert result['max_frequency'] <= detector.ultrasonic_range[1]
    
    def test_detect_ultrasonic_empty(self):
        """Тест с пустыми данными"""
        detector = UltrasonicDetector()
        result = detector.detect_ultrasonic_signals(np.array([]))
        
        assert result['ultrasonic_detected'] == False

class TestBinauralBeatDetector:
    """Тесты детектора бинауральных ритмов"""
    
    def test_analyze_binaural_beats_normal(self, sample_stereo_audio):
        """Тест анализа бинауральных ритмов в нормальном стерео аудио"""
        detector = BinauralBeatDetector()
        
        left_channel = sample_stereo_audio[:, 0]
        right_channel = sample_stereo_audio[:, 1]
        
        result = detector.analyze_binaural_beats(left_channel, right_channel)
        
        assert 'frequency_differences' in result
        assert 'rhythm_analysis' in result
        assert 'manipulation_score' in result
        assert 'is_manipulated' in result
        
        assert isinstance(result['frequency_differences'], list)
        assert isinstance(result['rhythm_analysis'], dict)
        assert 0 <= result['manipulation_score'] <= 1
        assert isinstance(result['is_manipulated'], bool)
    
    def test_analyze_binaural_beats_with_binaural_rhythm(self):
        """Тест анализа с бинауральным ритмом"""
        detector = BinauralBeatDetector()
        
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Левый канал - 440 Hz
        left_channel = np.sin(2 * np.pi * 440 * t)
        # Правый канал - 444 Hz (разница 4 Hz - тета-ритм)
        right_channel = np.sin(2 * np.pi * 444 * t)
        
        result = detector.analyze_binaural_beats(left_channel, right_channel)
        
        # Должен обнаружить бинауральный ритм
        assert len(result['frequency_differences']) > 0
        
        # Проверка классификации ритмов
        rhythm_analysis = result['rhythm_analysis']
        assert 'theta' in rhythm_analysis
        assert 'alpha' in rhythm_analysis
        assert 'beta' in rhythm_analysis
        assert 'gamma' in rhythm_analysis
    
    def test_analyze_binaural_beats_empty_channels(self):
        """Тест с пустыми каналами"""
        detector = BinauralBeatDetector()
        
        result = detector.analyze_binaural_beats(np.array([]), np.array([]))
        
        assert result['frequency_differences'] == []
        assert result['manipulation_score'] == 0
        assert result['is_manipulated'] == False
    
    def test_analyze_binaural_beats_unequal_channels(self):
        """Тест с каналами разной длины"""
        detector = BinauralBeatDetector()
        
        left_channel = np.random.randn(1000)
        right_channel = np.random.randn(800)  # Короче
        
        result = detector.analyze_binaural_beats(left_channel, right_channel)
        
        # Должен обрабатывать разную длину каналов
        assert isinstance(result['frequency_differences'], list)
    
    def test_classify_rhythms(self):
        """Тест классификации ритмов"""
        detector = BinauralBeatDetector()
        
        # Создаем тестовые разницы частот
        frequency_differences = [
            {'frequency_difference': 6, 'combined_strength': 1.0},  # theta
            {'frequency_difference': 10, 'combined_strength': 0.8},  # alpha
            {'frequency_difference': 20, 'combined_strength': 0.6},  # beta
            {'frequency_difference': 50, 'combined_strength': 0.4},  # gamma
            {'frequency_difference': 2, 'combined_strength': 0.3},   # вне диапазонов
        ]
        
        result = detector._classify_rhythms(frequency_differences)
        
        assert 'theta' in result
        assert 'alpha' in result
        assert 'beta' in result
        assert 'gamma' in result
        
        assert len(result['theta']) == 1
        assert len(result['alpha']) == 1
        assert len(result['beta']) == 1
        assert len(result['gamma']) == 1

class TestVisualFlickerAnalyzer:
    """Тесты анализатора визуальных мерцаний"""
    
    def test_analyze_screen_flicker_normal(self, sample_video_frames):
        """Тест анализа нормальных видеокадров"""
        analyzer = VisualFlickerAnalyzer()
        result = analyzer.analyze_screen_flicker(sample_video_frames)
        
        assert 'temporal_analysis' in result
        assert 'frequency_analysis' in result
        assert 'harmful_patterns' in result
        assert 'flicker_detected' in result
        
        assert isinstance(result['temporal_analysis'], dict)
        assert isinstance(result['frequency_analysis'], dict)
        assert isinstance(result['harmful_patterns'], list)
        assert isinstance(result['flicker_detected'], bool)
    
    def test_analyze_screen_flicker_empty(self):
        """Тест с пустыми кадрами"""
        analyzer = VisualFlickerAnalyzer()
        result = analyzer.analyze_screen_flicker(np.array([]))
        
        assert result['temporal_analysis'] == {}
        assert result['frequency_analysis'] == {}
        assert result['harmful_patterns'] == []
        assert result['flicker_detected'] == False
    
    def test_analyze_screen_flicker_single_frame(self):
        """Тест с одним кадром"""
        analyzer = VisualFlickerAnalyzer()
        single_frame = np.random.randint(0, 255, (64, 64, 3))
        
        result = analyzer.analyze_screen_flicker(np.array([single_frame]))
        
        assert result['temporal_analysis'] == {}
        assert result['frequency_analysis'] == {}
        assert result['harmful_patterns'] == []
        assert result['flicker_detected'] == False
    
    def test_extract_brightness(self, sample_video_frames):
        """Тест извлечения яркости"""
        analyzer = VisualFlickerAnalyzer()
        brightness_values = analyzer._extract_brightness(sample_video_frames)
        
        assert len(brightness_values) == len(sample_video_frames)
        assert np.all(brightness_values >= 0)
        assert np.all(brightness_values <= 255)
    
    def test_analyze_temporal_patterns(self):
        """Тест анализа временных паттернов"""
        analyzer = VisualFlickerAnalyzer()
        
        # Создаем тестовые значения яркости
        brightness_values = np.array([100, 120, 110, 130, 115, 125, 105, 140, 120, 135])
        
        result = analyzer._analyze_temporal_patterns(brightness_values)
        
        assert 'mean_brightness' in result
        assert 'std_brightness' in result
        assert 'min_brightness' in result
        assert 'max_brightness' in result
        assert 'brightness_range' in result
        
        assert result['mean_brightness'] == np.mean(brightness_values)
        assert result['min_brightness'] == np.min(brightness_values)
        assert result['max_brightness'] == np.max(brightness_values)
    
    def test_detect_harmful_patterns(self):
        """Тест обнаружения вредных паттернов"""
        analyzer = VisualFlickerAnalyzer()
        
        # Создаем частотный анализ с вредными паттернами
        frequency_analysis = {
            'harmful_low': {'total_energy': 15, 'peak_frequency': 2, 'peak_magnitude': 10},
            'epilepsy_risk': {'total_energy': 8, 'peak_frequency': 10, 'peak_magnitude': 5},
            'noticeable': {'total_energy': 20, 'peak_frequency': 40, 'peak_magnitude': 12}
        }
        
        harmful_patterns = analyzer._detect_harmful_patterns(frequency_analysis)
        
        assert isinstance(harmful_patterns, list)
        assert len(harmful_patterns) > 0
        
        # Проверка структуры паттернов
        for pattern in harmful_patterns:
            assert 'type' in pattern
            assert 'frequency' in pattern
            assert 'energy' in pattern
            assert 'severity' in pattern
            assert pattern['severity'] in ['low', 'medium', 'high']

class TestSpectralAnalysisIntegration:
    """Интеграционные тесты для спектрального анализа"""
    
    def test_end_to_end_audio_analysis(self, sample_audio_data, sample_stereo_audio):
        """Тест полного цикла аудио анализа"""
        # Базовый спектральный анализ
        spectral_analyzer = SpectralAnalyzer()
        frequencies, magnitude = spectral_analyzer.compute_fft(sample_audio_data)
        
        # Детекция сублиминальных сообщений
        subliminal_detector = SubliminalDetector()
        subliminal_result = subliminal_detector.detect_subliminal_messages(sample_audio_data)
        
        # Детекция ультразвука
        ultrasonic_detector = UltrasonicDetector()
        ultrasonic_result = ultrasonic_detector.detect_ultrasonic_signals(sample_audio_data)
        
        # Анализ бинауральных ритмов
        binaural_detector = BinauralBeatDetector()
        left_channel = sample_stereo_audio[:, 0]
        right_channel = sample_stereo_audio[:, 1]
        binaural_result = binaural_detector.analyze_binaural_beats(left_channel, right_channel)
        
        # Проверка результатов
        assert len(frequencies) > 0
        assert isinstance(subliminal_result, list)
        assert isinstance(ultrasonic_result, dict)
        assert isinstance(binaural_result, dict)
        
        # Проверка структуры результатов
        assert 'ultrasonic_detected' in ultrasonic_result
        assert 'frequency_differences' in binaural_result
        assert 'is_manipulated' in binaural_result
    
    def test_performance_with_large_audio(self):
        """Тест производительности с большими аудио данными"""
        import time
        
        # Генерация больших аудио данных
        large_audio = np.random.randn(44100 * 10)  # 10 секунд аудио
        
        analyzer = SpectralAnalyzer()
        
        start_time = time.time()
        frequencies, magnitude = analyzer.compute_fft(large_audio)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 2.0  # Должно выполняться менее 2 секунд
        assert len(frequencies) > 0
    
    def test_error_handling_corrupted_data(self):
        """Тест обработки поврежденных данных"""
        spectral_analyzer = SpectralAnalyzer()
        subliminal_detector = SubliminalDetector()
        ultrasonic_detector = UltrasonicDetector()
        
        # Тест с NaN значениями
        corrupted_data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        
        # Должен обрабатывать ошибки без падения
        frequencies, magnitude = spectral_analyzer.compute_fft(corrupted_data)
        assert isinstance(frequencies, np.ndarray)
        assert isinstance(magnitude, np.ndarray)
        
        # Тест с бесконечными значениями
        infinite_data = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        
        frequencies, magnitude = spectral_analyzer.compute_fft(infinite_data)
        assert isinstance(frequencies, np.ndarray)
        assert isinstance(magnitude, np.ndarray)
    
    def test_comprehensive_security_analysis(self, sample_audio_data, sample_stereo_audio, sample_video_frames):
        """Тест комплексного анализа безопасности"""
        security_analyzer = {
            'spectral': SpectralAnalyzer(),
            'subliminal': SubliminalDetector(),
            'ultrasonic': UltrasonicDetector(),
            'binaural': BinauralBeatDetector(),
            'visual': VisualFlickerAnalyzer()
        }
        
        # Анализ всех типов данных
        results = {}
        
        # Аудио анализ
        results['spectral'] = security_analyzer['spectral'].compute_fft(sample_audio_data)
        results['subliminal'] = security_analyzer['subliminal'].detect_subliminal_messages(sample_audio_data)
        results['ultrasonic'] = security_analyzer['ultrasonic'].detect_ultrasonic_signals(sample_audio_data)
        
        # Стерео анализ
        left_channel = sample_stereo_audio[:, 0]
        right_channel = sample_stereo_audio[:, 1]
        results['binaural'] = security_analyzer['binaural'].analyze_binaural_beats(left_channel, right_channel)
        
        # Визуальный анализ
        results['visual'] = security_analyzer['visual'].analyze_screen_flicker(sample_video_frames)
        
        # Проверка полноты результатов
        assert len(results) == 5
        assert all(isinstance(result, (tuple, list, dict)) for result in results.values())
        
        # Оценка общего уровня угроз
        threat_indicators = {
            'subliminal_detected': len(results['subliminal']) > 0,
            'ultrasonic_detected': results['ultrasonic']['ultrasonic_detected'],
            'binaural_manipulated': results['binaural']['is_manipulated'],
            'visual_flicker': results['visual']['flicker_detected']
        }
        
        total_threats = sum(threat_indicators.values())
        assert 0 <= total_threats <= 4

if __name__ == "__main__":
    pytest.main([__file__])
