"""
ML Detection Pipeline - Машинное обучение для детекции DPI
"""

import asyncio
import time
import random
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class MLDetectionPipeline(BasePipeline):
    """Пайплайн для ML детекции DPI"""
    
    def __init__(self):
        super().__init__("MLDetection", BypassTechnique.ADAPTIVE, priority=2)
        self.dpi_signatures = []
        self.ml_model_confidence = 0.0
        self.detection_history = []
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение с ML детекцией DPI"""
        start_time = time.time()
        
        try:
            # Имитация анализа DPI через ML
            await asyncio.sleep(0.008)  # ML инференс
            
            # Анализируем признаки DPI
            dpi_features = {
                'host_length': len(request.host),
                'port': request.port,
                'method': request.method,
                'headers_count': len(request.headers) if request.headers else 0,
                'data_size': len(request.data) if request.data else 0
            }
            
            # Имитация ML предсказания
            dpi_type = self._predict_dpi_type(dpi_features)
            confidence = self._calculate_confidence(dpi_features)
            
            # Выбираем контрмеру на основе предсказания
            if dpi_type == 'sni_filter':
                await asyncio.sleep(0.01)  # SNI обход
                success_prob = 0.5
            elif dpi_type == 'dpi_deep_packet':
                await asyncio.sleep(0.02)  # Deep packet обход
                success_prob = 0.4
            elif dpi_type == 'tcp_rst':
                await asyncio.sleep(0.015)  # TCP RST обход
                success_prob = 0.45
            else:
                await asyncio.sleep(0.012)  # Общий обход
                success_prob = 0.35
            
            # Корректировка на основе уверенности модели
            success_prob += confidence * 0.1
            
            success = random.random() < success_prob
            
            # Сохраняем в историю для обучения
            self.detection_history.append({
                'features': dpi_features,
                'predicted_type': dpi_type,
                'confidence': confidence,
                'success': success,
                'timestamp': time.time()
            })
            
            # Ограничиваем историю
            if len(self.detection_history) > 1000:
                self.detection_history = self.detection_history[-1000:]
            
            response_time = time.time() - start_time
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-DPI-Type': dpi_type,
                    'X-ML-Confidence': f"{confidence:.3f}",
                    'X-ML-Prediction': 'enabled',
                    'X-Detection-Accuracy': f"{self._get_detection_accuracy():.2%}"
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
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
