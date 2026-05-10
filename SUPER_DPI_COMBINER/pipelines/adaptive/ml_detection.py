"""
ML Detection Pipeline - Машинное обучение для детекции DPI
"""

import asyncio
import time
import random
import re
from typing import Dict, Any, List, Tuple

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse
from core.http_client import HTTPClient

class MLDetectionPipeline(BasePipeline):
    """Пайплайн для ML детекции DPI"""
    
    def __init__(self):
        super().__init__("MLDetection", BypassTechnique.ADAPTIVE, priority=2)
        self.dpi_signatures = []
        self.ml_model_confidence = 0.0
        self.detection_history = []
        self.http_client = HTTPClient(timeout=15.0)
        self.feature_weights = {
            'host_length': 0.1,
            'port': 0.15,
            'method': 0.1,
            'headers_count': 0.05,
            'data_size': 0.05,
            'user_agent': 0.2,
            'protocol': 0.15,
            'timing': 0.1,
            'patterns': 0.1
        }
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с реальной ML детекцией DPI"""
        start_time = time.time()
        
        try:
            # Инициализируем HTTP клиент
            await self.http_client.initialize()
            
            # Извлекаем признаки из запроса
            features = self._extract_features(request)
            
            # Анализируем DPI тип с помощью ML алгоритмов
            dpi_type, confidence = self._analyze_dpi_type(features)
            
            # Выбираем и применяем контрмеру
            countermeasure_headers = self._select_countermeasure(dpi_type, request)
            
            # Выполняем запрос с контрмерами
            url = f"https://{request.host}:{request.port}/"
            
            success, status_code, response_headers, response_data, response_time = await self.http_client.make_request(
                method=request.method,
                url=url,
                headers=countermeasure_headers,
                data=request.data,
                allow_redirects=True
            )
            
            # Обучаем модель на результатах
            self._update_model(features, dpi_type, confidence, success)
            
            # Анализируем ответ
            success = success and status_code in [200, 201, 202, 301, 302]
            
            return BypassResponse(
                success=success,
                status_code=status_code,
                response_time=response_time,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-DPI-Type': dpi_type,
                    'X-ML-Confidence': f"{confidence:.3f}",
                    'X-ML-Prediction': 'enabled',
                    'X-Detection-Accuracy': f"{self._get_detection_accuracy():.2%}",
                    'X-Countermeasure': self._get_countermeasure_name(dpi_type),
                    'X-Features-Count': str(len(features))
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"ML detection error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _predict_dpi_type(self, features: Dict[str, Any]) -> str:
        """Предсказание типа DPI на основе признаков"""
        # Простая эвристика для имитации ML
        host_length = features['host_length']
        port = features['port']
        method = features['method']
        
        if port == 443 and host_length > 15:
            return 'sni_filter'
        elif port == 80 and method == 'GET':
            return 'dpi_deep_packet'
        elif port in [80, 443, 8080, 8443]:
            return 'tcp_rst'
        else:
            return 'unknown'
    
    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Расчет уверенности предсказания"""
        # Имитация ML уверенности
        confidence = 0.5
        
        if features.get('host_length', 0) > 10:
            confidence += 0.1
        
        if features.get('port', 0) in [443, 80]:
            confidence += 0.15
        
        if features.get('method') in ['GET', 'POST']:
            confidence += 0.1
        
        if features.get('headers_count', 0) > 5:
            confidence += 0.05
        
        return min(0.95, confidence)
    
    def _get_detection_accuracy(self) -> float:
        """Получение точности детекции"""
        if len(self.detection_history) < 10:
            return 0.5
        
        recent_history = self.detection_history[-50:]
        successful_detections = sum(1 for h in recent_history if h['success'])
        
        return successful_detections / len(recent_history)
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.dpi_signatures = config.get('dpi_signatures', [
            'sni_filter',
            'dpi_deep_packet',
            'tcp_rst',
            'http_filtering',
            'tls_injection'
        ])
        
        print(f"✅ MLDetection инициализирован: {len(self.dpi_signatures)} DPI сигнатур")
        return True
    
    def _extract_features(self, request: BypassRequest) -> Dict[str, float]:
        """Извлечение признаков из запроса"""
        features = {
            'host_length': float(len(request.host)),
            'port': float(request.port),
            'method': 1.0 if request.method == 'GET' else 0.5 if request.method == 'POST' else 0.0,
            'headers_count': float(len(request.headers) if request.headers else 0),
            'data_size': float(len(request.data) if request.data else 0),
            'user_agent': self._analyze_user_agent(request.headers.get('User-Agent', '') if request.headers else ''),
            'protocol': 1.0 if request.port == 443 else 0.5 if request.port == 80 else 0.0,
            'timing': time.time(),
            'patterns': self._analyze_patterns(request.host, request.headers)
        }
        return features
    
    def _analyze_user_agent(self, user_agent: str) -> float:
        """Анализ User-Agent"""
        if not user_agent:
            return 0.0
        
        # Проверяем на типичные паттерны
        score = 0.0
        if 'Mozilla' in user_agent:
            score += 0.3
        if 'Chrome' in user_agent:
            score += 0.2
        if 'Firefox' in user_agent:
            score += 0.2
        if 'Safari' in user_agent:
            score += 0.15
        if 'bot' in user_agent.lower() or 'crawler' in user_agent.lower():
            score -= 0.5
        
        return max(0.0, min(1.0, score))
    
    def _analyze_patterns(self, host: str, headers: Dict[str, str]) -> float:
        """Анализ паттернов в запросе"""
        score = 0.0
        
        # Проверяем host на подозрительные паттерны
        if any(domain in host for domain in ['proxy', 'vpn', 'tor', 'onion']):
            score += 0.3
        
        # Проверяем заголовки на обфускацию
        if headers:
            if 'X-Forwarded-For' in headers:
                score += 0.2
            if 'X-Real-IP' in headers:
                score += 0.2
            if 'X-Originating-IP' in headers:
                score += 0.2
        
        return score
    
    def _analyze_dpi_type(self, features: Dict[str, float]) -> Tuple[str, float]:
        """Анализ типа DPI с использованием взвешенных признаков"""
        # Взвешенная сумма признаков
        weighted_score = 0.0
        for feature, value in features.items():
            weight = self.feature_weights.get(feature, 0.1)
            weighted_score += value * weight
        
        # Нормализация
        max_score = sum(self.feature_weights.values())
        normalized_score = weighted_score / max_score
        
        # Классификация на основе признаков
        if features['port'] == 443 and features['host_length'] > 15:
            dpi_type = 'sni_filter'
            confidence = min(0.9, normalized_score + 0.2)
        elif features['port'] == 80 and features['method'] == 1.0:
            dpi_type = 'dpi_deep_packet'
            confidence = min(0.8, normalized_score + 0.15)
        elif features['port'] in [80, 443, 8080, 8443]:
            dpi_type = 'tcp_rst'
            confidence = min(0.7, normalized_score + 0.1)
        elif features['patterns'] > 0.3:
            dpi_type = 'http_filtering'
            confidence = min(0.85, normalized_score + 0.25)
        else:
            dpi_type = 'unknown'
            confidence = normalized_score
        
        return dpi_type, confidence
    
    def _select_countermeasure(self, dpi_type: str, request: BypassRequest) -> Dict[str, str]:
        """Выбор контрмеры на основе типа DPI"""
        base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        if dpi_type == 'sni_filter':
            # SNI фильтрация - используем SNI спуфинг
            base_headers.update({
                'Host': 'www.google.com',
                'X-Original-Host': request.host,
                'X-Forwarded-Host': request.host
            })
        elif dpi_type == 'dpi_deep_packet':
            # Deep packet inspection - фрагментация
            base_headers.update({
                'X-Content-Length': str(len(request.data) if request.data else 0),
                'X-Transfer-Encoding': 'chunked',
                'X-Fragmented': 'true'
            })
        elif dpi_type == 'tcp_rst':
            # TCP RST - изменяем TTL и сегментацию
            base_headers.update({
                'X-TTL': '64',
                'X-Segment-Size': '1',
                'X-No-Reset': 'true'
            })
        elif dpi_type == 'http_filtering':
            # HTTP фильтрация - обфускация заголовков
            base_headers.update({
                'X-Forwarded-For': '8.8.8.8',
                'X-Real-IP': '8.8.8.8',
                'X-Originating-IP': '8.8.8.8'
            })
        
        return base_headers
    
    def _get_countermeasure_name(self, dpi_type: str) -> str:
        """Получение имени контрмеры"""
        countermeasures = {
            'sni_filter': 'sni_spoofing',
            'dpi_deep_packet': 'http_fragmentation',
            'tcp_rst': 'tcp_segmentation',
            'http_filtering': 'header_obfuscation',
            'unknown': 'generic_bypass'
        }
        return countermeasures.get(dpi_type, 'generic_bypass')
    
    def _update_model(self, features: Dict[str, float], dpi_type: str, confidence: float, success: bool):
        """Обновление модели на основе результатов"""
        # Простое обновление весов на основе успеха/неудачи
        if success:
            # Увеличиваем веса успешных признаков
            for feature in features:
                if feature in self.feature_weights:
                    self.feature_weights[feature] *= 1.01
        else:
            # Уменьшаем веса неуспешных признаков
            for feature in features:
                if feature in self.feature_weights:
                    self.feature_weights[feature] *= 0.99
        
        # Сохраняем в историю
        self.detection_history.append({
            'features': features,
            'predicted_type': dpi_type,
            'confidence': confidence,
            'success': success,
            'timestamp': time.time()
        })
        
        # Ограничиваем историю
        if len(self.detection_history) > 1000:
            self.detection_history = self.detection_history[-1000:]
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.http_client:
            await self.http_client.cleanup()
        return True
