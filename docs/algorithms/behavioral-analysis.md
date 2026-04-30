# Алгоритмы анализа поведения

## Обзор

Документация описывает алгоритмы анализа поведения пользователя для обнаружения психологических манипуляций и аномалий в когнитивных паттернах.

## 🧠 Типы поведенческого анализа

### 1. Анализ паттернов набора текста

#### Алгоритм временных интервалов
```python
class TypingPatternAnalyzer:
    def __init__(self):
        self.baseline_intervals = []
        self.anomaly_threshold = 2.5  # стандартных отклонений
    
    def analyze_keystroke_timing(self, keystrokes):
        """Анализ времени между нажатиями клавиш"""
        intervals = self._calculate_intervals(keystrokes)
        
        # Статистический анализ
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # Обнаружение аномалий
        anomalies = []
        for i, interval in enumerate(intervals):
            z_score = abs(interval - mean_interval) / std_interval
            if z_score > self.anomaly_threshold:
                anomalies.append({
                    'position': i,
                    'interval': interval,
                    'z_score': z_score,
                    'type': 'timing_anomaly'
                })
        
        return {
            'mean_interval': mean_interval,
            'std_interval': std_interval,
            'anomalies': anomalies,
            'anomaly_rate': len(anomalies) / len(intervals)
        }
    
    def _calculate_intervals(self, keystrokes):
        """Расчет интервалов между нажатиями"""
        intervals = []
        for i in range(1, len(keystrokes)):
            interval = keystrokes[i]['timestamp'] - keystrokes[i-1]['timestamp']
            intervals.append(interval)
        return intervals
```

#### Алгоритм анализа ритма
```python
class RhythmAnalyzer:
    def __init__(self):
        self.window_size = 10  # количество нажатий в окне
        self.rhythm_threshold = 0.3
    
    def analyze_typing_rhythm(self, keystrokes):
        """Анализ ритмичности набора текста"""
        if len(keystrokes) < self.window_size:
            return {'status': 'insufficient_data'}
        
        # Скользящее окно для анализа ритма
        rhythm_scores = []
        for i in range(len(keystrokes) - self.window_size + 1):
            window = keystrokes[i:i + self.window_size]
            rhythm_score = self._calculate_rhythm_score(window)
            rhythm_scores.append(rhythm_score)
        
        # Обнаружение ритмических аномалий
        rhythm_variability = np.std(rhythm_scores)
        is_anomalous = rhythm_variability > self.rhythm_threshold
        
        return {
            'rhythm_scores': rhythm_scores,
            'variability': rhythm_variability,
            'is_anomalous': is_anomalous,
            'average_rhythm': np.mean(rhythm_scores)
        }
    
    def _calculate_rhythm_score(self, window):
        """Расчет ритмической оценки для окна"""
        intervals = []
        for i in range(1, len(window)):
            interval = window[i]['timestamp'] - window[i-1]['timestamp']
            intervals.append(interval)
        
        # Коэффициент вариации как мера ритмичности
        if len(intervals) > 1:
            return np.std(intervals) / np.mean(intervals)
        return 0
```

### 2. Анализ паттернов принятия решений

#### Алгоритм последовательности выбора
```python
class DecisionPatternAnalyzer:
    def __init__(self):
        self.decision_history = []
        self.pattern_window = 20  # последних решений
    
    def analyze_decision_patterns(self, decisions):
        """Анализ паттернов принятия решений"""
        self.decision_history.extend(decisions)
        recent_decisions = self.decision_history[-self.pattern_window:]
        
        # Анализ последовательности
        sequence_analysis = self._analyze_decision_sequence(recent_decisions)
        
        # Обнаружение когнитивного диссонанса
        dissonance_score = self._calculate_cognitive_dissonance(recent_decisions)
        
        # Анализ консистентности
        consistency_score = self._calculate_consistency(recent_decisions)
        
        return {
            'sequence_analysis': sequence_analysis,
            'cognitive_dissonance': dissonance_score,
            'consistency': consistency_score,
            'anomaly_detected': self._detect_anomalies(
                sequence_analysis, dissonance_score, consistency_score
            )
        }
    
    def _analyze_decision_sequence(self, decisions):
        """Анализ последовательности решений"""
        patterns = {
            'repetition_rate': 0,
            'alternation_rate': 0,
            'randomness_score': 0
        }
        
        if len(decisions) < 2:
            return patterns
        
        # Расчет повторений
        repetitions = 0
        alternations = 0
        for i in range(1, len(decisions)):
            if decisions[i] == decisions[i-1]:
                repetitions += 1
            else:
                alternations += 1
        
        patterns['repetition_rate'] = repetitions / (len(decisions) - 1)
        patterns['alternation_rate'] = alternations / (len(decisions) - 1)
        
        # Оценка случайности (энтропия)
        unique_decisions = set(decisions)
        entropy = 0
        for decision in unique_decisions:
            probability = decisions.count(decision) / len(decisions)
            entropy -= probability * np.log2(probability)
        
        patterns['randomness_score'] = entropy / np.log2(len(unique_decisions))
        
        return patterns
    
    def _calculate_cognitive_dissonance(self, decisions):
        """Расчет когнитивного диссонанса"""
        if len(decisions) < 3:
            return 0
        
        # Анализ противоречивых паттернов
        contradictions = 0
        for i in range(2, len(decisions)):
            if decisions[i] == decisions[i-2] and decisions[i] != decisions[i-1]:
                contradictions += 1
        
        return contradictions / (len(decisions) - 2)
```

### 3. Анализ паттернов навигации

#### Алгоритм анализа движения мыши
```python
class MouseMovementAnalyzer:
    def __init__(self):
        self.movement_history = []
        self.velocity_threshold = 0.1
        self.acceleration_threshold = 0.5
    
    def analyze_mouse_movements(self, movements):
        """Анализ паттернов движения мыши"""
        if len(movements) < 2:
            return {'status': 'insufficient_data'}
        
        # Расчет скорости и ускорения
        velocities = self._calculate_velocities(movements)
        accelerations = self._calculate_accelerations(velocities)
        
        # Обнаружение аномалий
        velocity_anomalies = self._detect_velocity_anomalies(velocities)
        acceleration_anomalies = self._detect_acceleration_anomalies(accelerations)
        
        # Анализ паттернов движения
        movement_patterns = self._analyze_movement_patterns(movements)
        
        return {
            'velocities': velocities,
            'accelerations': accelerations,
            'velocity_anomalies': velocity_anomalies,
            'acceleration_anomalies': acceleration_anomalies,
            'movement_patterns': movement_patterns,
            'anomaly_score': self._calculate_anomaly_score(
                velocity_anomalies, acceleration_anomalies
            )
        }
    
    def _calculate_velocities(self, movements):
        """Расчет скоростей движения"""
        velocities = []
        for i in range(1, len(movements)):
            dx = movements[i]['x'] - movements[i-1]['x']
            dy = movements[i]['y'] - movements[i-1]['y']
            dt = movements[i]['timestamp'] - movements[i-1]['timestamp']
            
            if dt > 0:
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(velocity)
        
        return velocities
    
    def _analyze_movement_patterns(self, movements):
        """Анализ паттернов движения"""
        patterns = {
            'straight_line_ratio': 0,
            'curvature_score': 0,
            'pause_frequency': 0
        }
        
        if len(movements) < 3:
            return patterns
        
        # Анализ прямолинейности движения
        straight_movements = 0
        for i in range(2, len(movements)):
            # Проверка коллинеарности трех точек
            p1, p2, p3 = movements[i-2], movements[i-1], movements[i]
            
            # Векторное произведение для проверки коллинеарности
            v1 = (p2['x'] - p1['x'], p2['y'] - p1['y'])
            v2 = (p3['x'] - p2['x'], p3['y'] - p2['y'])
            
            cross_product = abs(v1[0] * v2[1] - v1[1] * v2[0])
            if cross_product < 10:  # порог коллинеарности
                straight_movements += 1
        
        patterns['straight_line_ratio'] = straight_movements / (len(movements) - 2)
        
        return patterns
```

## 🎯 Методы обнаружения аномалий

### 1. Статистические методы

#### Z-score анализ
```python
class ZScoreAnomalyDetector:
    def __init__(self, threshold=2.5):
        self.threshold = threshold
        self.baseline_stats = None
    
    def fit(self, baseline_data):
        """Обучение на базовых данных"""
        self.baseline_stats = {
            'mean': np.mean(baseline_data),
            'std': np.std(baseline_data)
        }
    
    def detect_anomalies(self, data):
        """Обнаружение аномалий с использованием Z-score"""
        if self.baseline_stats is None:
            raise ValueError("Model not fitted")
        
        anomalies = []
        for i, value in enumerate(data):
            z_score = abs(value - self.baseline_stats['mean']) / self.baseline_stats['std']
            if z_score > self.threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'z_score': z_score
                })
        
        return anomalies
```

#### IQR (Interquartile Range) метод
```python
class IQRAnomalyDetector:
    def __init__(self, multiplier=1.5):
        self.multiplier = multiplier
        self.q1 = None
        self.q3 = None
    
    def fit(self, baseline_data):
        """Обучение на базовых данных"""
        self.q1 = np.percentile(baseline_data, 25)
        self.q3 = np.percentile(baseline_data, 75)
    
    def detect_anomalies(self, data):
        """Обнаружение аномалий с использованием IQR"""
        if self.q1 is None or self.q3 is None:
            raise ValueError("Model not fitted")
        
        iqr = self.q3 - self.q1
        lower_bound = self.q1 - self.multiplier * iqr
        upper_bound = self.q3 + self.multiplier * iqr
        
        anomalies = []
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'type': 'iqr_outlier'
                })
        
        return anomalies
```

### 2. Машинное обучение

#### Изолирующий лес (Isolation Forest)
```python
from sklearn.ensemble import IsolationForest

class IsolationForestAnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_fitted = False
    
    def fit(self, baseline_data):
        """Обучение модели"""
        if isinstance(baseline_data[0], (int, float)):
            # Одномерные данные
            X = np.array(baseline_data).reshape(-1, 1)
        else:
            # Многомерные данные
            X = np.array(baseline_data)
        
        self.model.fit(X)
        self.is_fitted = True
    
    def detect_anomalies(self, data):
        """Обнаружение аномалий"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        if isinstance(data[0], (int, float)):
            X = np.array(data).reshape(-1, 1)
        else:
            X = np.array(data)
        
        predictions = self.model.predict(X)
        anomaly_scores = self.model.decision_function(X)
        
        anomalies = []
        for i, (prediction, score) in enumerate(zip(predictions, anomaly_scores)):
            if prediction == -1:  # аномалия
                anomalies.append({
                    'index': i,
                    'score': score,
                    'type': 'isolation_forest'
                })
        
        return anomalies
```

### 3. Временные ряды

#### Экспоненциальное сглаживание
```python
class ExponentialSmoothingAnomalyDetector:
    def __init__(self, alpha=0.3, threshold=2.0):
        self.alpha = alpha
        self.threshold = threshold
        self.smoothed_value = None
    
    def detect_anomalies(self, data):
        """Обнаружение аномалий с экспоненциальным сглаживанием"""
        anomalies = []
        
        for i, value in enumerate(data):
            if self.smoothed_value is None:
                self.smoothed_value = value
                continue
            
            # Экспоненциальное сглаживание
            self.smoothed_value = self.alpha * value + (1 - self.alpha) * self.smoothed_value
            
            # Расчет отклонения
            deviation = abs(value - self.smoothed_value)
            
            # Обнаружение аномалии
            if deviation > self.threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'smoothed': self.smoothed_value,
                    'deviation': deviation
                })
        
        return anomalies
```

## 🔄 Интеграция алгоритмов

### Комплексный анализатор поведения
```python
class ComprehensiveBehaviorAnalyzer:
    def __init__(self):
        self.typing_analyzer = TypingPatternAnalyzer()
        self.rhythm_analyzer = RhythmAnalyzer()
        self.decision_analyzer = DecisionPatternAnalyzer()
        self.mouse_analyzer = MouseMovementAnalyzer()
        
        # Детекторы аномалий
        self.zscore_detector = ZScoreAnomalyDetector()
        self.iqr_detector = IQRAnomalyDetector()
        self.isolation_detector = IsolationForestAnomalyDetector()
    
    def analyze_user_behavior(self, behavior_data):
        """Комплексный анализ поведения пользователя"""
        results = {
            'typing_analysis': None,
            'rhythm_analysis': None,
            'decision_analysis': None,
            'mouse_analysis': None,
            'overall_anomaly_score': 0,
            'threat_level': 'low'
        }
        
        # Анализ набора текста
        if 'keystrokes' in behavior_data:
            results['typing_analysis'] = self.typing_analyzer.analyze_keystroke_timing(
                behavior_data['keystrokes']
            )
            results['rhythm_analysis'] = self.rhythm_analyzer.analyze_typing_rhythm(
                behavior_data['keystrokes']
            )
        
        # Анализ принятия решений
        if 'decisions' in behavior_data:
            results['decision_analysis'] = self.decision_analyzer.analyze_decision_patterns(
                behavior_data['decisions']
            )
        
        # Анализ движения мыши
        if 'mouse_movements' in behavior_data:
            results['mouse_analysis'] = self.mouse_analyzer.analyze_mouse_movements(
                behavior_data['mouse_movements']
            )
        
        # Расчет общей оценки аномалий
        results['overall_anomaly_score'] = self._calculate_overall_anomaly_score(results)
        
        # Определение уровня угрозы
        results['threat_level'] = self._determine_threat_level(results['overall_anomaly_score'])
        
        return results
    
    def _calculate_overall_anomaly_score(self, results):
        """Расчет общей оценки аномалий"""
        scores = []
        
        if results['typing_analysis']:
            scores.append(results['typing_analysis']['anomaly_rate'])
        
        if results['rhythm_analysis'] and results['rhythm_analysis']['is_anomalous']:
            scores.append(0.5)
        
        if results['decision_analysis']:
            scores.append(results['decision_analysis']['cognitive_dissonance'])
        
        if results['mouse_analysis']:
            scores.append(results['mouse_analysis']['anomaly_score'])
        
        return np.mean(scores) if scores else 0
    
    def _determine_threat_level(self, anomaly_score):
        """Определение уровня угрозы"""
        if anomaly_score > 0.7:
            return 'critical'
        elif anomaly_score > 0.5:
            return 'high'
        elif anomaly_score > 0.3:
            return 'medium'
        elif anomaly_score > 0.1:
            return 'low'
        else:
            return 'minimal'
```

## 📊 Метрики оценки

### Точность обнаружения
```python
def calculate_detection_metrics(true_anomalies, detected_anomalies):
    """Расчет метрик обнаружения"""
    true_positives = len(set(true_anomalies) & set(detected_anomalies))
    false_positives = len(set(detected_anomalies) - set(true_anomalies))
    false_negatives = len(set(true_anomalies) - set(detected_anomalies))
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives
    }
```

## 🔧 Оптимизация производительности

### Векторизация операций
```python
def vectorized_typing_analysis(keystrokes):
    """Векторизованный анализ набора текста"""
    timestamps = np.array([k['timestamp'] for k in keystrokes])
    intervals = np.diff(timestamps)
    
    # Векторизованный статистический анализ
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    z_scores = np.abs((intervals - mean_interval) / std_interval)
    
    anomalies = np.where(z_scores > 2.5)[0]
    
    return {
        'mean_interval': mean_interval,
        'std_interval': std_interval,
        'anomaly_indices': anomalies.tolist(),
        'anomaly_rate': len(anomalies) / len(intervals)
    }
```

## 🚀 Практическое применение

### Пример использования
```python
# Инициализация анализатора
analyzer = ComprehensiveBehaviorAnalyzer()

# Обучение на базовых данных пользователя
baseline_keystrokes = load_user_baseline_keystrokes()
analyzer.typing_analyzer.fit(baseline_keystrokes)

# Анализ текущего поведения
current_behavior = {
    'keystrokes': get_current_keystrokes(),
    'decisions': get_recent_decisions(),
    'mouse_movements': get_mouse_movements()
}

results = analyzer.analyze_user_behavior(current_behavior)

# Принятие решений на основе анализа
if results['threat_level'] == 'critical':
    activate_emergency_protection()
elif results['threat_level'] == 'high':
    notify_security_team()
```

---

*Документация актуальна для версии RSecure 1.0+*
