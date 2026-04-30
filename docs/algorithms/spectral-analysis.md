# Методы спектрального анализа

## Обзор

Документация описывает методы спектрального анализа аудио и видеосигналов для обнаружения психологических манипуляций и вредоносных воздействий через сенсорные каналы.

## 🎵 Основы спектрального анализа

### 1. Преобразование Фурье

#### Быстрое преобразование Фурье (FFT)
```python
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq

class SpectralAnalyzer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.window_size = 1024
        self.hop_size = 512
    
    def compute_fft(self, audio_data):
        """Вычисление FFT для аудио сигнала"""
        # Применение окна Ханна для уменьшения спектральной утечки
        window = np.hanning(len(audio_data))
        windowed_signal = audio_data * window
        
        # Вычисление FFT
        fft_result = fft(windowed_signal)
        frequencies = fftfreq(len(windowed_signal), 1/self.sample_rate)
        
        # Только положительные частоты
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        return frequencies, magnitude
    
    def compute_spectrogram(self, audio_data):
        """Вычисление спектрограммы"""
        f, t, Sxx = signal.spectrogram(
            audio_data, 
            fs=self.sample_rate,
            window='hann',
            nperseg=self.window_size,
            noverlap=self.window_size - self.hop_size
        )
        
        return {
            'frequencies': f,
            'time': t,
            'spectrogram': Sxx
        }
```

#### Кратковременное преобразование Фурье (STFT)
```python
class STFTAnalyzer:
    def __init__(self, sample_rate=44100, frame_length=1024, hop_length=512):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length
    
    def analyze_stft(self, audio_data):
        """Анализ с использованием STFT"""
        # Разбиение на фреймы
        frames = self._frame_signal(audio_data)
        
        # Применение окна и FFT для каждого фрейма
        spectrogram = []
        for frame in frames:
            windowed = frame * np.hanning(len(frame))
            fft_result = fft(windowed)
            spectrogram.append(np.abs(fft_result[:len(fft_result)//2]))
        
        spectrogram = np.array(spectrogram).T
        
        return {
            'spectrogram': spectrogram,
            'frequencies': np.fft.fftfreq(self.frame_length, 1/self.sample_rate)[:self.frame_length//2],
            'time_frames': np.arange(spectrogram.shape[1]) * self.hop_length / self.sample_rate
        }
    
    def _frame_signal(self, signal):
        """Разбиение сигнала на фреймы"""
        frames = []
        for i in range(0, len(signal) - self.frame_length + 1, self.hop_length):
            frames.append(signal[i:i + self.frame_length])
        return frames
```

### 2. Вейвлет-анализ

#### Непрерывное вейвлет-преобразование
```python
import pywt

class WaveletAnalyzer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.scales = np.arange(1, 128)
    
    def analyze_cwt(self, audio_data):
        """Непрерывное вейвлет-преобразование"""
        # Использование вейвлета Морле
        coeffs, freqs = pywt.cwt(audio_data, self.scales, 'cmor', 1.0/self.sample_rate)
        
        return {
            'coefficients': coeffs,
            'frequencies': freqs,
            'scales': self.scales
        }
    
    def detect_frequency_patterns(self, audio_data):
        """Обнаружение частотных паттернов"""
        cwt_result = self.analyze_cwt(audio_data)
        coeffs = cwt_result['coefficients']
        freqs = cwt_result['frequencies']
        
        # Анализ энергии в разных частотных диапазонах
        patterns = {}
        
        # Тета-ритмы (4-8 Гц)
        theta_mask = (freqs >= 4) & (freqs <= 8)
        patterns['theta_energy'] = np.sum(np.abs(coeffs[theta_mask, :])**2)
        
        # Альфа-ритмы (8-12 Гц)
        alpha_mask = (freqs >= 8) & (freqs <= 12)
        patterns['alpha_energy'] = np.sum(np.abs(coeffs[alpha_mask, :])**2)
        
        # Бета-ритмы (12-30 Гц)
        beta_mask = (freqs >= 12) & (freqs <= 30)
        patterns['beta_energy'] = np.sum(np.abs(coeffs[beta_mask, :])**2)
        
        # Гамма-ритмы (30-100 Гц)
        gamma_mask = (freqs >= 30) & (freqs <= 100)
        patterns['gamma_energy'] = np.sum(np.abs(coeffs[gamma_mask, :])**2)
        
        return patterns
```

## 🔍 Детекция вредоносных сигналов

### 1. Обнаружение сублиминальных сообщений

#### Анализ амплитудных маскировок
```python
class SubliminalDetector:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.threshold_db = -40  # порог слышимости
        self.min_duration = 0.1  # минимальная длительность в секундах
    
    def detect_subliminal_messages(self, audio_data):
        """Обнаружение сублиминальных сообщений"""
        # Преобразование в дБ
        audio_db = 20 * np.log10(np.abs(audio_data) + 1e-10)
        
        # Обнаружение низкоамплитудных сигналов
        low_amplitude_mask = audio_db < self.threshold_db
        low_amplitude_segments = self._find_continuous_segments(low_amplitude_mask)
        
        # Анализ сегментов
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
        """Поиск непрерывных сегментов"""
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
        """Анализ сублиминального сегмента"""
        # Спектральный анализ
        frequencies, magnitude = self._compute_fft(segment)
        
        # Обнаружение структурированных паттернов
        spectral_peaks = self._find_spectral_peaks(frequencies, magnitude)
        
        # Анализ регулярности
        regularity_score = self._calculate_regularity(spectral_peaks)
        
        return {
            'is_suspicious': regularity_score > 0.7,
            'spectral_peaks': spectral_peaks,
            'regularity_score': regularity_score,
            'dominant_frequencies': frequencies[np.argsort(magnitude)[-5:]]
        }
```

#### Детекция ультразвуковых сигналов
```python
class UltrasonicDetector:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.ultrasonic_range = (18000, 20000)  # Гц
    
    def detect_ultrasonic_signals(self, audio_data):
        """Обнаружение ультразвуковых сигналов"""
        # Вычисление спектра
        frequencies, magnitude = self._compute_fft(audio_data)
        
        # Фильтрация ультразвукового диапазона
        ultrasonic_mask = (frequencies >= self.ultrasonic_range[0]) & \
                         (frequencies <= self.ultrasonic_range[1])
        
        ultrasonic_frequencies = frequencies[ultrasonic_mask]
        ultrasonic_magnitude = magnitude[ultrasonic_mask]
        
        # Обнаружение сигналов
        if len(ultrasonic_magnitude) > 0:
            max_magnitude = np.max(ultrasonic_magnitude)
            avg_magnitude = np.mean(ultrasonic_magnitude)
            
            # Проверка на наличие структурированного сигнала
            signal_to_noise = max_magnitude / (avg_magnitude + 1e-10)
            
            return {
                'ultrasonic_detected': signal_to_noise > 3.0,
                'max_frequency': ultrasonic_frequencies[np.argmax(ultrasonic_magnitude)],
                'signal_strength': max_magnitude,
                'signal_to_noise': signal_to_noise,
                'frequency_range': self.ultrasonic_range
            }
        
        return {'ultrasonic_detected': False}
```

### 2. Анализ бинауральных ритмов

#### Детекция бинауральных паттернов
```python
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
        """Анализ бинауральных ритмов"""
        # Вычисление спектра для каждого канала
        left_freq, left_mag = self._compute_fft(left_channel)
        right_freq, right_mag = self._compute_fft(right_channel)
        
        # Обнаружение разницы частот
        frequency_differences = self._calculate_frequency_differences(
            left_freq, left_mag, right_freq, right_mag
        )
        
        # Классификация ритмов
        rhythm_analysis = self._classify_rhythms(frequency_differences)
        
        # Обнаружение манипуляций
        manipulation_score = self._detect_manipulation(rhythm_analysis)
        
        return {
            'frequency_differences': frequency_differences,
            'rhythm_analysis': rhythm_analysis,
            'manipulation_score': manipulation_score,
            'is_manipulated': manipulation_score > 0.7
        }
    
    def _calculate_frequency_differences(self, left_freq, left_mag, right_freq, right_mag):
        """Расчет разниц частот между каналами"""
        # Поиск пиков в каждом канале
        left_peaks = self._find_peaks(left_freq, left_mag)
        right_peaks = self._find_peaks(right_freq, right_mag)
        
        # Вычисление разниц
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
    
    def _classify_rhythms(self, frequency_differences):
        """Классификация ритмов по частотным диапазонам"""
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
```

### 3. Визуальный спектральный анализ

#### Анализ мерцаний экрана
```python
class VisualFlickerAnalyzer:
    def __init__(self, frame_rate=30):
        self.frame_rate = frame_rate
        self.flicker_frequencies = {
            'harmful_low': (0.5, 3),    # потенциально вредные низкие частоты
            'epilepsy_risk': (3, 30),   # риск эпилепсии
            'noticeable': (30, 60)      заметные мерцания
        }
    
    def analyze_screen_flicker(self, frames):
        """Анализ мерцаний экрана"""
        # Извлечение яркости для каждого кадра
        brightness_values = self._extract_brightness(frames)
        
        # Временной анализ
        temporal_analysis = self._analyze_temporal_patterns(brightness_values)
        
        # Частотный анализ
        frequency_analysis = self._analyze_flicker_frequencies(brightness_values)
        
        # Обнаружение вредоносных паттернов
        harmful_patterns = self._detect_harmful_patterns(frequency_analysis)
        
        return {
            'temporal_analysis': temporal_analysis,
            'frequency_analysis': frequency_analysis,
            'harmful_patterns': harmful_patterns,
            'flicker_detected': len(harmful_patterns) > 0
        }
    
    def _extract_brightness(self, frames):
        """Извлечение значений яркости из кадров"""
        brightness_values = []
        
        for frame in frames:
            # Конвертация в grayscale
            if len(frame.shape) == 3:
                gray_frame = np.mean(frame, axis=2)
            else:
                gray_frame = frame
            
            # Средняя яркость кадра
            avg_brightness = np.mean(gray_frame)
            brightness_values.append(avg_brightness)
        
        return np.array(brightness_values)
    
    def _analyze_flicker_frequencies(self, brightness_values):
        """Анализ частот мерцаний"""
        # Вычисление FFT
        fft_result = fft(brightness_values - np.mean(brightness_values))
        frequencies = fftfreq(len(brightness_values), 1/self.frame_rate)
        
        # Только положительные частоты
        positive_freq_idx = frequencies > 0
        frequencies = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        # Анализ частотных диапазонов
        frequency_analysis = {}
        
        for range_name, (min_freq, max_freq) in self.flicker_frequencies.items():
            freq_mask = (frequencies >= min_freq) & (frequencies <= max_freq)
            range_magnitude = magnitude[freq_mask]
            
            frequency_analysis[range_name] = {
                'total_energy': np.sum(range_magnitude),
                'peak_frequency': frequencies[np.argmax(range_magnitude)] if len(range_magnitude) > 0 else 0,
                'peak_magnitude': np.max(range_magnitude) if len(range_magnitude) > 0 else 0
            }
        
        return frequency_analysis
```

## 🎯 Алгоритмы обработки сигналов

### 1. Фильтрация

#### Цифровые фильтры
```python
from scipy.signal import butter, filtfilt

class DigitalFilters:
    @staticmethod
    def butter_bandpass(lowcut, highcut, fs, order=5):
        """Полосовой фильтр Баттерворта"""
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a
    
    @staticmethod
    def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
        """Применение полосового фильтра"""
        b, a = DigitalFilters.butter_bandpass(lowcut, highcut, fs, order)
        y = filtfilt(b, a, data)
        return y
    
    @staticmethod
    def notch_filter(data, freq, fs, quality=30):
        """Режекторный фильтр для удаления конкретной частоты"""
        b, a = signal.iirnotch(freq, quality, fs)
        return filtfilt(b, a, data)
```

### 2. Адаптивная фильтрация

#### LMS (Least Mean Squares) фильтр
```python
class AdaptiveFilter:
    def __init__(self, filter_length=32, mu=0.01):
        self.filter_length = filter_length
        self.mu = mu  # шаг адаптации
        self.weights = np.zeros(filter_length)
    
    def lms_filter(self, input_signal, desired_signal):
        """LMS адаптивная фильтрация"""
        filtered_signal = np.zeros(len(input_signal))
        
        for i in range(self.filter_length, len(input_signal)):
            # Входной вектор
            x = input_signal[i-self.filter_length:i][::-1]
            
            # Выход фильтра
            y = np.dot(self.weights, x)
            filtered_signal[i] = y
            
            # Ошибка
            error = desired_signal[i] - y
            
            # Обновление весов
            self.weights += self.mu * error * x
        
        return filtered_signal
```

## 📊 Метрики и оценка

### 1. Спектральные метрики

#### Спектральная плотность мощности
```python
def compute_power_spectral_density(audio_data, sample_rate):
    """Вычисление спектральной плотности мощности"""
    frequencies, psd = signal.periodogram(audio_data, sample_rate)
    
    return {
        'frequencies': frequencies,
        'psd': psd,
        'total_power': np.sum(psd),
        'spectral_centroid': np.sum(frequencies * psd) / np.sum(psd)
    }
```

#### Спектральный центроид
```python
def compute_spectral_centroid(frequencies, magnitude):
    """Вычисление спектрального центроида"""
    if np.sum(magnitude) == 0:
        return 0
    
    return np.sum(frequencies * magnitude) / np.sum(magnitude)
```

#### Спектральная ширина
```python
def compute_spectral_bandwidth(frequencies, magnitude, centroid):
    """Вычисление спектральной ширины"""
    if np.sum(magnitude) == 0:
        return 0
    
    return np.sqrt(np.sum(((frequencies - centroid) ** 2) * magnitude) / np.sum(magnitude))
```

### 2. Временные метрики

#### RMS (Root Mean Square)
```python
def compute_rms(signal):
    """Вычисление RMS уровня сигнала"""
    return np.sqrt(np.mean(signal ** 2))
```

#### Пиковый фактор
```python
def compute_crest_factor(signal):
    """Вычисление пикового фактора"""
    rms = compute_rms(signal)
    peak = np.max(np.abs(signal))
    
    return 20 * np.log10(peak / rms) if rms > 0 else 0
```

## 🔧 Оптимизация производительности

### 1. Векторизация

#### Оптимизированный FFT анализ
```python
class OptimizedSpectralAnalyzer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.fft_window_size = 1024
        self.hop_size = 512
        
        # Предвычисленные окна
        self.window = np.hanning(self.fft_window_size)
        self.frequencies = np.fft.fftfreq(self.fft_window_size, 1/sample_rate)
    
    def analyze_streaming(self, audio_stream):
        """Потоковый анализ аудио"""
        results = []
        
        for chunk in self._chunk_generator(audio_stream):
            # Векторизованная обработка
            windowed = chunk * self.window
            fft_result = np.fft.fft(windowed)
            
            # Векторизованный анализ
            magnitude = np.abs(fft_result[:self.fft_window_size//2])
            frequencies = self.frequencies[:self.fft_window_size//2]
            
            results.append({
                'frequencies': frequencies,
                'magnitude': magnitude,
                'spectral_centroid': self._compute_centroid_vectorized(frequencies, magnitude)
            })
        
        return results
    
    def _compute_centroid_vectorized(self, frequencies, magnitude):
        """Векторизованное вычисление центроида"""
        if np.sum(magnitude) == 0:
            return 0
        
        return np.sum(frequencies * magnitude) / np.sum(magnitude)
```

### 2. Параллельная обработка

#### Многопоточный анализ
```python
import concurrent.futures
from multiprocessing import Pool

class ParallelSpectralAnalyzer:
    def __init__(self, sample_rate=44100, num_workers=4):
        self.sample_rate = sample_rate
        self.num_workers = num_workers
    
    def analyze_multiple_channels(self, audio_channels):
        """Параллельный анализ нескольких каналов"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            
            for channel_name, channel_data in audio_channels.items():
                future = executor.submit(self._analyze_single_channel, channel_data)
                futures.append((channel_name, future))
            
            results = {}
            for channel_name, future in futures:
                results[channel_name] = future.result()
        
        return results
    
    def _analyze_single_channel(self, channel_data):
        """Анализ одного канала"""
        # Базовый спектральный анализ
        frequencies, magnitude = self._compute_fft(channel_data)
        
        # Дополнительный анализ
        spectral_features = {
            'centroid': self._compute_spectral_centroid(frequencies, magnitude),
            'bandwidth': self._compute_spectral_bandwidth(frequencies, magnitude),
            'rolloff': self._compute_spectral_rolloff(frequencies, magnitude)
        }
        
        return {
            'frequencies': frequencies,
            'magnitude': magnitude,
            'features': spectral_features
        }
```

## 🚀 Практическое применение

### Интеграция с системой безопасности
```python
class SecuritySpectralAnalyzer:
    def __init__(self):
        self.subliminal_detector = SubliminalDetector()
        self.ultrasonic_detector = UltrasonicDetector()
        self.binaural_detector = BinauralBeatDetector()
        self.visual_analyzer = VisualFlickerAnalyzer()
    
    def analyze_security_threats(self, audio_data, video_data=None):
        """Комплексный анализ угроз безопасности"""
        threats = {
            'subliminal': [],
            'ultrasonic': None,
            'binaural': None,
            'visual_flicker': None,
            'overall_threat_level': 'low'
        }
        
        # Анализ сублиминальных сообщений
        if audio_data is not None:
            threats['subliminal'] = self.subliminal_detector.detect_subliminal_messages(audio_data)
            threats['ultrasonic'] = self.ultrasonic_detector.detect_ultrasonic_signals(audio_data)
            
            # Анализ бинауральных ритмов (если стерео)
            if len(audio_data.shape) > 1 and audio_data.shape[1] >= 2:
                threats['binaural'] = self.binaural_detector.analyze_binaural_beats(
                    audio_data[:, 0], audio_data[:, 1]
                )
        
        # Анализ видео
        if video_data is not None:
            threats['visual_flicker'] = self.visual_analyzer.analyze_screen_flicker(video_data)
        
        # Оценка общего уровня угрозы
        threats['overall_threat_level'] = self._assess_overall_threat(threats)
        
        return threats
    
    def _assess_overall_threat(self, threats):
        """Оценка общего уровня угрозы"""
        threat_score = 0
        
        # Взвешенная оценка различных угроз
        if len(threats['subliminal']) > 0:
            threat_score += 0.3
        
        if threats['ultrasonic'] and threats['ultrasonic']['ultrasonic_detected']:
            threat_score += 0.2
        
        if threats['binaural'] and threats['binaural']['is_manipulated']:
            threat_score += 0.3
        
        if threats['visual_flicker'] and threats['visual_flicker']['flicker_detected']:
            threat_score += 0.2
        
        # Классификация уровня угрозы
        if threat_score >= 0.7:
            return 'critical'
        elif threat_score >= 0.5:
            return 'high'
        elif threat_score >= 0.3:
            return 'medium'
        else:
            return 'low'
```

---

*Документация актуальна для версии RSecure 1.0+*
