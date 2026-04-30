"""
Модуль визуальной безопасности RSecure
Защита от атак через зрительный канал: мерцания, яркость, визуальные паттерны
"""

import numpy as np
import cv2
import threading
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import logging

@dataclass
class VisualThreat:
    """Данные о визуальной угрозе"""
    threat_type: str
    severity: float  # 0.0 - 1.0
    confidence: float
    timestamp: float
    description: str
    affected_region: Optional[Tuple[int, int, int, int]] = None

class VisualSecurityMonitor:
    """Монитор визуальной безопасности"""
    
    def __init__(self, sampling_rate: int = 30, history_size: int = 300):
        self.sampling_rate = sampling_rate
        self.history_size = history_size
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Исторические данные для анализа
        self.brightness_history = deque(maxlen=history_size)
        self.flicker_history = deque(maxlen=history_size)
        self.frame_history = deque(maxlen=10)
        
        # Пороги обнаружения
        self.flicker_threshold = 0.15  # Порог мерцания
        self.brightness_change_threshold = 0.3  # Порог изменения яркости
        self.pattern_anomaly_threshold = 0.25  # Порог аномалии паттерна
        
        # Статистика
        self.threats_detected = []
        self.last_analysis_time = time.time()
        
        # Логгер
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self):
        """Запуск мониторинга"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Визуальный мониторинг безопасности запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("Визуальный мониторинг безопасности остановлен")
    
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.is_monitoring:
            try:
                # Получение текущего кадра экрана
                frame = self._capture_screen_frame()
                if frame is not None:
                    self._analyze_frame(frame)
                
                time.sleep(1.0 / self.sampling_rate)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(0.1)
    
    def _capture_screen_frame(self) -> Optional[np.ndarray]:
        """Захват кадра экрана"""
        try:
            # Используем PIL для захвата экрана
            from PIL import ImageGrab
            
            # Захват всего экрана
            screen = ImageGrab.grab()
            frame = np.array(screen)
            
            # Конвертация в BGR для OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
            
        except ImportError:
            self.logger.warning("PIL не доступен, используется тестовый кадр")
            return self._generate_test_frame()
        except Exception as e:
            self.logger.error(f"Ошибка захвата экрана: {e}")
            return None
    
    def _generate_test_frame(self) -> np.ndarray:
        """Генерация тестового кадра для демонстрации"""
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Добавляем тестовые паттерны мерцания
        if np.random.random() > 0.9:
            frame = frame * np.random.uniform(0.5, 1.5)
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def _analyze_frame(self, frame: np.ndarray):
        """Анализ кадра на наличие угроз"""
        current_time = time.time()
        
        # Сохранение кадра в историю
        self.frame_history.append(frame.copy())
        
        # Анализ яркости
        brightness = self._calculate_brightness(frame)
        self.brightness_history.append(brightness)
        
        # Анализ мерцаний
        flicker_level = self._detect_flicker()
        self.flicker_history.append(flicker_level)
        
        # Обнаружение угроз
        threats = []
        
        # Проверка мерцаний
        if flicker_level > self.flicker_threshold:
            threat = VisualThreat(
                threat_type="flicker_attack",
                severity=min(flicker_level, 1.0),
                confidence=0.8,
                timestamp=current_time,
                description=f"Обнаружено аномальное мерцание: {flicker_level:.3f}"
            )
            threats.append(threat)
        
        # Проверка резких изменений яркости
        if len(self.brightness_history) > 10:
            brightness_volatility = self._calculate_brightness_volatility()
            if brightness_volatility > self.brightness_change_threshold:
                threat = VisualThreat(
                    threat_type="brightness_attack",
                    severity=min(brightness_volatility, 1.0),
                    confidence=0.7,
                    timestamp=current_time,
                    description=f"Обнаружена аномалия яркости: {brightness_volatility:.3f}"
                )
                threats.append(threat)
        
        # Проверка визуальных паттернов
        if len(self.frame_history) >= 5:
            pattern_anomaly = self._detect_pattern_anomalies()
            if pattern_anomaly > self.pattern_anomaly_threshold:
                threat = VisualThreat(
                    threat_type="pattern_attack",
                    severity=min(pattern_anomaly, 1.0),
                    confidence=0.6,
                    timestamp=current_time,
                    description=f"Обнаружен аномальный визуальный паттерн: {pattern_anomaly:.3f}"
                )
                threats.append(threat)
        
        # Сохранение обнаруженных угроз
        for threat in threats:
            self.threats_detected.append(threat)
            self.logger.warning(f"Обнаружена визуальная угроза: {threat.description}")
    
    def _calculate_brightness(self, frame: np.ndarray) -> float:
        """Расчет средней яркости кадра"""
        # Конвертация в grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray) / 255.0
    
    def _detect_flicker(self) -> float:
        """Обнаружение мерцаний на основе истории яркости"""
        if len(self.brightness_history) < 10:
            return 0.0
        
        # Анализ частотной составляющей яркости
        brightness_array = np.array(list(self.brightness_history)[-20:])
        
        # Вычисление разностей между соседними кадрами
        diffs = np.diff(brightness_array)
        
        # Расчет уровня мерцания как среднеквадратичного отклонения разностей
        flicker_level = np.std(diffs) * 10  # Масштабирование
        
        return min(flicker_level, 1.0)
    
    def _calculate_brightness_volatility(self) -> float:
        """Расчет волатильности яркости"""
        if len(self.brightness_history) < 10:
            return 0.0
        
        brightness_array = np.array(list(self.brightness_history)[-10:])
        return np.std(brightness_array)
    
    def _detect_pattern_anomalies(self) -> float:
        """Обнаружение аномальных визуальных паттернов"""
        if len(self.frame_history) < 5:
            return 0.0
        
        # Анализ последовательности кадров
        frames = list(self.frame_history)[-5:]
        
        # Расчет оптического потока между кадрами
        anomaly_score = 0.0
        
        for i in range(len(frames) - 1):
            frame1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            frame2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
            
            # Вычисление оптического потока
            flow = cv2.calcOpticalFlowPyrLK(
                frame1, frame2, 
                np.array([[100, 100]], dtype=np.float32).reshape(-1, 1, 2),
                None
            )[0]
            
            if flow is not None and len(flow) > 0:
                # Анализ характеристик потока
                flow_magnitude = np.linalg.norm(flow[0][0])
                anomaly_score += flow_magnitude
        
        return min(anomaly_score / len(frames), 1.0)
    
    def get_current_status(self) -> Dict:
        """Получение текущего статуса мониторинга"""
        return {
            "is_monitoring": self.is_monitoring,
            "current_brightness": list(self.brightness_history)[-1] if self.brightness_history else 0,
            "current_flicker": list(self.flicker_history)[-1] if self.flicker_history else 0,
            "threats_count": len(self.threats_detected),
            "last_threat": self.threats_detected[-1].description if self.threats_detected else None
        }
    
    def get_recent_threats(self, minutes: int = 5) -> List[VisualThreat]:
        """Получение угроз за последние N минут"""
        cutoff_time = time.time() - (minutes * 60)
        return [t for t in self.threats_detected if t.timestamp > cutoff_time]
    
    def clear_threat_history(self):
        """Очистка истории угроз"""
        self.threats_detected.clear()
        self.logger.info("История визуальных угроз очищена")

class VisualProtectionFilter:
    """Фильтр визуальной защиты"""
    
    def __init__(self):
        self.filter_strength = 0.5
        self.is_active = False
    
    def apply_flicker_filter(self, frame: np.ndarray) -> np.ndarray:
        """Применение фильтра мерцаний"""
        if not self.is_active:
            return frame
        
        # Временное сглаживание для уменьшения мерцаний
        filtered = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # Смешивание с оригиналом в зависимости от силы фильтра
        result = cv2.addWeighted(
            frame, 1 - self.filter_strength,
            filtered, self.filter_strength,
            0
        )
        
        return result
    
    def apply_brightness_normalization(self, frame: np.ndarray) -> np.ndarray:
        """Применение нормализации яркости"""
        if not self.is_active:
            return frame
        
        # Выравнивание гистограммы для стабилизации яркости
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return result
    
    def activate_protection(self, strength: float = 0.5):
        """Активация защиты"""
        self.filter_strength = max(0.0, min(1.0, strength))
        self.is_active = True
    
    def deactivate_protection(self):
        """Деактивация защиты"""
        self.is_active = False

# Экспортируемые классы и функции
__all__ = [
    'VisualSecurityMonitor',
    'VisualProtectionFilter',
    'VisualThreat'
]
