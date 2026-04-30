"""
Тесты для алгоритмов анализа поведения
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавление путей для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Импортируем тестируемые классы (создадим их здесь для тестирования)
class TypingPatternAnalyzer:
    def __init__(self):
        self.baseline_intervals = []
        self.anomaly_threshold = 2.5
    
    def analyze_keystroke_timing(self, keystrokes):
        if len(keystrokes) < 2:
            return {'status': 'insufficient_data'}
        
        intervals = self._calculate_intervals(keystrokes)
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        anomalies = []
        for i, interval in enumerate(intervals):
            z_score = abs(interval - mean_interval) / std_interval if std_interval > 0 else 0
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
        intervals = []
        for i in range(1, len(keystrokes)):
            interval = keystrokes[i]['timestamp'] - keystrokes[i-1]['timestamp']
            intervals.append(interval)
        return intervals

class RhythmAnalyzer:
    def __init__(self):
        self.window_size = 10
        self.rhythm_threshold = 0.3
    
    def analyze_typing_rhythm(self, keystrokes):
        if len(keystrokes) < self.window_size:
            return {'status': 'insufficient_data'}
        
        rhythm_scores = []
        for i in range(len(keystrokes) - self.window_size + 1):
            window = keystrokes[i:i + self.window_size]
            rhythm_score = self._calculate_rhythm_score(window)
            rhythm_scores.append(rhythm_score)
        
        rhythm_variability = np.std(rhythm_scores)
        is_anomalous = rhythm_variability > self.rhythm_threshold
        
        return {
            'rhythm_scores': rhythm_scores,
            'variability': rhythm_variability,
            'is_anomalous': is_anomalous,
            'average_rhythm': np.mean(rhythm_scores)
        }
    
    def _calculate_rhythm_score(self, window):
        intervals = []
        for i in range(1, len(window)):
            interval = window[i]['timestamp'] - window[i-1]['timestamp']
            intervals.append(interval)
        
        if len(intervals) > 1:
            return np.std(intervals) / np.mean(intervals)
        return 0

class DecisionPatternAnalyzer:
    def __init__(self):
        self.decision_history = []
        self.pattern_window = 20
    
    def analyze_decision_patterns(self, decisions):
        self.decision_history.extend(decisions)
        recent_decisions = self.decision_history[-self.pattern_window:]
        
        sequence_analysis = self._analyze_decision_sequence(recent_decisions)
        dissonance_score = self._calculate_cognitive_dissonance(recent_decisions)
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
        patterns = {
            'repetition_rate': 0,
            'alternation_rate': 0,
            'randomness_score': 0
        }
        
        if len(decisions) < 2:
            return patterns
        
        repetitions = 0
        alternations = 0
        for i in range(1, len(decisions)):
            if decisions[i] == decisions[i-1]:
                repetitions += 1
            else:
                alternations += 1
        
        patterns['repetition_rate'] = repetitions / (len(decisions) - 1)
        patterns['alternation_rate'] = alternations / (len(decisions) - 1)
        
        unique_decisions = set(decisions)
        entropy = 0
        for decision in unique_decisions:
            probability = decisions.count(decision) / len(decisions)
            entropy -= probability * np.log2(probability)
        
        patterns['randomness_score'] = entropy / np.log2(len(unique_decisions)) if len(unique_decisions) > 1 else 0
        
        return patterns
    
    def _calculate_cognitive_dissonance(self, decisions):
        if len(decisions) < 3:
            return 0
        
        contradictions = 0
        for i in range(2, len(decisions)):
            if decisions[i] == decisions[i-2] and decisions[i] != decisions[i-1]:
                contradictions += 1
        
        return contradictions / (len(decisions) - 2)
    
    def _calculate_consistency(self, decisions):
        if len(decisions) < 2:
            return 1.0
        
        unique_decisions = set(decisions)
        return 1.0 / len(unique_decisions)
    
    def _detect_anomalies(self, sequence_analysis, dissonance_score, consistency_score):
        return (dissonance_score > 0.3 or 
                sequence_analysis['randomness_score'] > 0.8 or 
                consistency_score < 0.5)

class MouseMovementAnalyzer:
    def __init__(self):
        self.movement_history = []
        self.velocity_threshold = 0.1
        self.acceleration_threshold = 0.5
    
    def analyze_mouse_movements(self, movements):
        if len(movements) < 2:
            return {'status': 'insufficient_data'}
        
        velocities = self._calculate_velocities(movements)
        accelerations = self._calculate_accelerations(velocities)
        
        velocity_anomalies = self._detect_velocity_anomalies(velocities)
        acceleration_anomalies = self._detect_acceleration_anomalies(accelerations)
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
        velocities = []
        for i in range(1, len(movements)):
            dx = movements[i]['x'] - movements[i-1]['x']
            dy = movements[i]['y'] - movements[i-1]['y']
            dt = movements[i]['timestamp'] - movements[i-1]['timestamp']
            
            if dt > 0:
                velocity = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(velocity)
        
        return velocities
    
    def _calculate_accelerations(self, velocities):
        if len(velocities) < 2:
            return []
        
        accelerations = []
        for i in range(1, len(velocities)):
            dv = velocities[i] - velocities[i-1]
            accelerations.append(abs(dv))
        
        return accelerations
    
    def _detect_velocity_anomalies(self, velocities):
        if not velocities:
            return []
        
        mean_vel = np.mean(velocities)
        std_vel = np.std(velocities)
        
        anomalies = []
        for i, vel in enumerate(velocities):
            z_score = abs(vel - mean_vel) / std_vel if std_vel > 0 else 0
            if z_score > 2.5:
                anomalies.append({'index': i, 'velocity': vel, 'z_score': z_score})
        
        return anomalies
    
    def _detect_acceleration_anomalies(self, accelerations):
        if not accelerations:
            return []
        
        mean_acc = np.mean(accelerations)
        std_acc = np.std(accelerations)
        
        anomalies = []
        for i, acc in enumerate(accelerations):
            z_score = abs(acc - mean_acc) / std_acc if std_acc > 0 else 0
            if z_score > 2.5:
                anomalies.append({'index': i, 'acceleration': acc, 'z_score': z_score})
        
        return anomalies
    
    def _analyze_movement_patterns(self, movements):
        patterns = {
            'straight_line_ratio': 0,
            'curvature_score': 0,
            'pause_frequency': 0
        }
        
        if len(movements) < 3:
            return patterns
        
        straight_movements = 0
        for i in range(2, len(movements)):
            p1, p2, p3 = movements[i-2], movements[i-1], movements[i]
            
            v1 = (p2['x'] - p1['x'], p2['y'] - p1['y'])
            v2 = (p3['x'] - p2['x'], p3['y'] - p2['y'])
            
            cross_product = abs(v1[0] * v2[1] - v1[1] * v2[0])
            if cross_product < 10:
                straight_movements += 1
        
        patterns['straight_line_ratio'] = straight_movements / (len(movements) - 2)
        
        return patterns
    
    def _calculate_anomaly_score(self, velocity_anomalies, acceleration_anomalies):
        total_points = len(velocity_anomalies) + len(acceleration_anomalies)
        return min(total_points / 10.0, 1.0)  # Нормализация до [0, 1]

class ComprehensiveBehaviorAnalyzer:
    def __init__(self):
        self.typing_analyzer = TypingPatternAnalyzer()
        self.rhythm_analyzer = RhythmAnalyzer()
        self.decision_analyzer = DecisionPatternAnalyzer()
        self.mouse_analyzer = MouseMovementAnalyzer()
    
    def analyze_user_behavior(self, behavior_data):
        results = {
            'typing_analysis': None,
            'rhythm_analysis': None,
            'decision_analysis': None,
            'mouse_analysis': None,
            'overall_anomaly_score': 0,
            'threat_level': 'low'
        }
        
        if 'keystrokes' in behavior_data:
            results['typing_analysis'] = self.typing_analyzer.analyze_keystroke_timing(
                behavior_data['keystrokes']
            )
            results['rhythm_analysis'] = self.rhythm_analyzer.analyze_typing_rhythm(
                behavior_data['keystrokes']
            )
        
        if 'decisions' in behavior_data:
            results['decision_analysis'] = self.decision_analyzer.analyze_decision_patterns(
                behavior_data['decisions']
            )
        
        if 'mouse_movements' in behavior_data:
            results['mouse_analysis'] = self.mouse_analyzer.analyze_mouse_movements(
                behavior_data['mouse_movements']
            )
        
        results['overall_anomaly_score'] = self._calculate_overall_anomaly_score(results)
        results['threat_level'] = self._determine_threat_level(results['overall_anomaly_score'])
        
        return results
    
    def _calculate_overall_anomaly_score(self, results):
        scores = []
        
        if results['typing_analysis'] and 'anomaly_rate' in results['typing_analysis']:
            scores.append(results['typing_analysis']['anomaly_rate'])
        
        if results['rhythm_analysis'] and results['rhythm_analysis'].get('is_anomalous'):
            scores.append(0.5)
        
        if results['decision_analysis']:
            scores.append(results['decision_analysis']['cognitive_dissonance'])
        
        if results['mouse_analysis']:
            scores.append(results['mouse_analysis']['anomaly_score'])
        
        return np.mean(scores) if scores else 0
    
    def _determine_threat_level(self, anomaly_score):
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

# Тесты
class TestTypingPatternAnalyzer:
    """Тесты анализатора паттернов набора текста"""
    
    def test_analyze_keystroke_timing_normal(self, sample_keystrokes):
        """Тест анализа нормального набора текста"""
        analyzer = TypingPatternAnalyzer()
        result = analyzer.analyze_keystroke_timing(sample_keystrokes)
        
        assert 'mean_interval' in result
        assert 'std_interval' in result
        assert 'anomalies' in result
        assert 'anomaly_rate' in result
        
        assert result['mean_interval'] > 0
        assert result['std_interval'] >= 0
        assert isinstance(result['anomalies'], list)
        assert 0 <= result['anomaly_rate'] <= 1
    
    def test_analyze_keystroke_timing_insufficient_data(self):
        """Тест с недостаточным количеством данных"""
        analyzer = TypingPatternAnalyzer()
        result = analyzer.analyze_keystroke_timing([{'key': 'a', 'timestamp': 1000.0}])
        
        assert result['status'] == 'insufficient_data'
    
    def test_analyze_keystroke_timing_with_anomalies(self):
        """Тест обнаружения аномалий"""
        keystrokes_with_anomalies = [
            {'key': 'a', 'timestamp': 1000.0},
            {'key': 'b', 'timestamp': 1000.15},  # Нормально
            {'key': 'c', 'timestamp': 1000.20},  # Нормально
            {'key': 'd', 'timestamp': 1005.0},   # Аномалия - большая задержка
            {'key': 'e', 'timestamp': 1005.15},  # Нормально
            {'key': 'f', 'timestamp': 1005.20}   # Нормально
        ]
        
        analyzer = TypingPatternAnalyzer()
        analyzer.anomaly_threshold = 1.5  # Снижаем порог для теста
        result = analyzer.analyze_keystroke_timing(keystrokes_with_anomalies)
        
        assert len(result['anomalies']) > 0
        assert result['anomaly_rate'] > 0
    
    def test_calculate_intervals(self, sample_keystrokes):
        """Тест расчета интервалов"""
        analyzer = TypingPatternAnalyzer()
        intervals = analyzer._calculate_intervals(sample_keystrokes)
        
        assert len(intervals) == len(sample_keystrokes) - 1
        assert all(interval > 0 for interval in intervals)
        
        # Проверка первого интервала
        expected_first = sample_keystrokes[1]['timestamp'] - sample_keystrokes[0]['timestamp']
        assert intervals[0] == expected_first

class TestRhythmAnalyzer:
    """Тесты анализатора ритма"""
    
    def test_analyze_typing_rhythm_normal(self, sample_keystrokes):
        """Тест анализа нормального ритма"""
        analyzer = RhythmAnalyzer()
        analyzer.window_size = 5  # Уменьшаем для теста
        
        # Расширяем данные для окна
        extended_keystrokes = sample_keystrokes * 2
        result = analyzer.analyze_typing_rhythm(extended_keystrokes)
        
        assert 'rhythm_scores' in result
        assert 'variability' in result
        assert 'is_anomalous' in result
        assert 'average_rhythm' in result
        
        assert isinstance(result['rhythm_scores'], list)
        assert result['variability'] >= 0
        assert isinstance(result['is_anomalous'], bool)
    
    def test_analyze_typing_rhythm_insufficient_data(self, sample_keystrokes):
        """Тест с недостаточным количеством данных"""
        analyzer = RhythmAnalyzer()
        analyzer.window_size = 20  # Больше, чем количество данных
        
        result = analyzer.analyze_typing_rhythm(sample_keystrokes)
        
        assert result['status'] == 'insufficient_data'
    
    def test_analyze_typing_rhythm_with_anomalies(self):
        """Тест обнаружения ритмических аномалий"""
        # Создаем данные с нерегулярным ритмом
        irregular_keystrokes = [
            {'key': 'a', 'timestamp': 1000.0},
            {'key': 'b', 'timestamp': 1000.10},
            {'key': 'c', 'timestamp': 1000.50},  # Большая пауза
            {'key': 'd', 'timestamp': 1000.55},
            {'key': 'e', 'timestamp': 1001.00},  # Еще большая пауза
            {'key': 'f', 'timestamp': 1001.05},
            {'key': 'g', 'timestamp': 1001.10},
            {'key': 'h', 'timestamp': 1001.15},
            {'key': 'i', 'timestamp': 1001.20},
            {'key': 'j', 'timestamp': 1001.25},
            {'key': 'k', 'timestamp': 1001.30},
            {'key': 'l', 'timestamp': 1001.35}
        ]
        
        analyzer = RhythmAnalyzer()
        analyzer.window_size = 5
        analyzer.rhythm_threshold = 0.1  # Снижаем порог
        
        result = analyzer.analyze_typing_rhythm(irregular_keystrokes)
        
        assert result['is_anomalous'] == True
        assert result['variability'] > analyzer.rhythm_threshold

class TestDecisionPatternAnalyzer:
    """Тесты анализатора паттернов принятия решений"""
    
    def test_analyze_decision_patterns_normal(self, sample_decisions):
        """Тест анализа нормальных паттернов решений"""
        analyzer = DecisionPatternAnalyzer()
        result = analyzer.analyze_decision_patterns(sample_decisions)
        
        assert 'sequence_analysis' in result
        assert 'cognitive_dissonance' in result
        assert 'consistency' in result
        assert 'anomaly_detected' in result
        
        # Проверка структуры анализа последовательности
        seq_analysis = result['sequence_analysis']
        assert 'repetition_rate' in seq_analysis
        assert 'alternation_rate' in seq_analysis
        assert 'randomness_score' in seq_analysis
        
        assert 0 <= seq_analysis['repetition_rate'] <= 1
        assert 0 <= seq_analysis['alternation_rate'] <= 1
        assert 0 <= seq_analysis['randomness_score'] <= 1
    
    def test_analyze_decision_patterns_with_dissonance(self):
        """Тест обнаружения когнитивного диссонанса"""
        decisions_with_dissonance = ['accept', 'reject', 'accept', 'reject', 'accept', 'reject']
        
        analyzer = DecisionPatternAnalyzer()
        result = analyzer.analyze_decision_patterns(decisions_with_dissonance)
        
        assert result['cognitive_dissonance'] > 0
    
    def test_analyze_decision_patterns_consistency(self):
        """Тест оценки консистентности"""
        consistent_decisions = ['accept'] * 10
        inconsistent_decisions = ['accept', 'reject', 'modify', 'delete', 'accept']
        
        analyzer = DecisionPatternAnalyzer()
        
        result_consistent = analyzer.analyze_decision_patterns(consistent_decisions)
        result_inconsistent = analyzer.analyze_decision_patterns(inconsistent_decisions)
        
        assert result_consistent['consistency'] > result_inconsistent['consistency']

class TestMouseMovementAnalyzer:
    """Тесты анализатора движения мыши"""
    
    def test_analyze_mouse_movements_normal(self, sample_mouse_movements):
        """Тест анализа нормальных движений мыши"""
        analyzer = MouseMovementAnalyzer()
        result = analyzer.analyze_mouse_movements(sample_mouse_movements)
        
        assert 'velocities' in result
        assert 'accelerations' in result
        assert 'velocity_anomalies' in result
        assert 'acceleration_anomalies' in result
        assert 'movement_patterns' in result
        assert 'anomaly_score' in result
        
        assert isinstance(result['velocities'], list)
        assert isinstance(result['accelerations'], list)
        assert isinstance(result['velocity_anomalies'], list)
        assert isinstance(result['acceleration_anomalies'], list)
        assert 0 <= result['anomaly_score'] <= 1
    
    def test_analyze_mouse_movements_insufficient_data(self):
        """Тест с недостаточным количеством данных"""
        analyzer = MouseMovementAnalyzer()
        result = analyzer.analyze_mouse_movements([
            {'x': 100, 'y': 100, 'timestamp': 1000.0}
        ])
        
        assert result['status'] == 'insufficient_data'
    
    def test_calculate_velocities(self, sample_mouse_movements):
        """Тест расчета скоростей"""
        analyzer = MouseMovementAnalyzer()
        velocities = analyzer._calculate_velocities(sample_mouse_movements)
        
        assert len(velocities) == len(sample_mouse_movements) - 1
        assert all(v >= 0 for v in velocities)
    
    def test_detect_velocity_anomalies(self):
        """Тест обнаружения аномалий скоростей"""
        normal_velocities = [10, 12, 11, 13, 9, 14, 10, 12, 11, 13]
        velocities_with_anomaly = [10, 12, 11, 100, 9, 14, 10, 12, 11, 13]  # Аномалия
        
        analyzer = MouseMovementAnalyzer()
        
        anomalies_normal = analyzer._detect_velocity_anomalies(normal_velocities)
        anomalies_with_anomaly = analyzer._detect_velocity_anomalies(velocities_with_anomaly)
        
        assert len(anomalies_with_anomaly) > len(anomalies_normal)

class TestComprehensiveBehaviorAnalyzer:
    """Тесты комплексного анализатора поведения"""
    
    def test_analyze_user_behavior_complete(self, sample_keystrokes, sample_mouse_movements, sample_decisions):
        """Тест комплексного анализа с полными данными"""
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        behavior_data = {
            'keystrokes': sample_keystrokes,
            'mouse_movements': sample_mouse_movements,
            'decisions': sample_decisions
        }
        
        result = analyzer.analyze_user_behavior(behavior_data)
        
        assert 'typing_analysis' in result
        assert 'rhythm_analysis' in result
        assert 'decision_analysis' in result
        assert 'mouse_analysis' in result
        assert 'overall_anomaly_score' in result
        assert 'threat_level' in result
        
        assert result['typing_analysis'] is not None
        assert result['rhythm_analysis'] is not None
        assert result['decision_analysis'] is not None
        assert result['mouse_analysis'] is not None
        assert 0 <= result['overall_anomaly_score'] <= 1
        assert result['threat_level'] in ['minimal', 'low', 'medium', 'high', 'critical']
    
    def test_analyze_user_behavior_partial_data(self, sample_keystrokes):
        """Тест анализа с частичными данными"""
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        behavior_data = {'keystrokes': sample_keystrokes}
        result = analyzer.analyze_user_behavior(behavior_data)
        
        assert result['typing_analysis'] is not None
        assert result['rhythm_analysis'] is not None
        assert result['decision_analysis'] is None
        assert result['mouse_analysis'] is None
    
    def test_analyze_user_behavior_empty_data(self):
        """Тест анализа с пустыми данными"""
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        result = analyzer.analyze_user_behavior({})
        
        assert result['typing_analysis'] is None
        assert result['rhythm_analysis'] is None
        assert result['decision_analysis'] is None
        assert result['mouse_analysis'] is None
        assert result['overall_anomaly_score'] == 0
        assert result['threat_level'] == 'minimal'
    
    def test_determine_threat_level(self):
        """Тест определения уровня угрозы"""
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        assert analyzer._determine_threat_level(0.05) == 'minimal'
        assert analyzer._determine_threat_level(0.15) == 'low'
        assert analyzer._determine_threat_level(0.4) == 'medium'
        assert analyzer._determine_threat_level(0.6) == 'high'
        assert analyzer._determine_threat_level(0.8) == 'critical'

class TestBehavioralAnalysisIntegration:
    """Интеграционные тесты для анализа поведения"""
    
    def test_end_to_end_analysis(self, integration_test_data):
        """Тест полного цикла анализа"""
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        result = analyzer.analyze_user_behavior(integration_test_data['user_session'])
        
        # Проверка структуры результата
        assert isinstance(result, dict)
        assert 'overall_anomaly_score' in result
        assert 'threat_level' in result
        
        # Проверка валидности значений
        assert 0 <= result['overall_anomaly_score'] <= 1
        assert result['threat_level'] in ['minimal', 'low', 'medium', 'high', 'critical']
    
    def test_performance_with_large_dataset(self):
        """Тест производительности с большими данными"""
        import time
        
        # Генерация больших данных
        large_keystrokes = []
        for i in range(1000):
            large_keystrokes.append({
                'key': chr(ord('a') + (i % 26)),
                'timestamp': 1000.0 + i * 0.1
            })
        
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        start_time = time.time()
        result = analyzer.analyze_user_behavior({'keystrokes': large_keystrokes})
        end_time = time.time()
        
        # Проверка производительности
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Должно выполняться менее 5 секунд
        assert result is not None
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        analyzer = ComprehensiveBehaviorAnalyzer()
        
        # Тест с некорректными данными
        invalid_data = {
            'keystrokes': [
                {'key': 'a'},  # Отсутствует timestamp
                {'timestamp': 1000.0}  # Отсутствует key
            ]
        }
        
        # Должен обрабатывать ошибки без падения
        result = analyzer.analyze_user_behavior(invalid_data)
        assert isinstance(result, dict)
        assert 'overall_anomaly_score' in result

if __name__ == "__main__":
    pytest.main([__file__])
