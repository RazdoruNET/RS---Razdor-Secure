#!/usr/bin/env python3
"""
Интеграция LLM с локальным Ollama
Интеллектуальная оптимизация пайплайнов через ИИ
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .base_pipeline import BasePipeline, BypassTechnique

# Импорт логгера с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class LLMAnalysis:
    """Результат анализа LLM"""
    dpi_type: str
    confidence: float
    recommended_techniques: List[str]
    optimization_suggestions: List[str]
    new_techniques: List[Dict[str, Any]]
    performance_prediction: float

class LLMIntegration:
    """Интеграция с LLM для оптимизации DPI обхода"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama2"):
        self.ollama_url = ollama_url
        self.model = model
        self.session = None
        self.analysis_history: List[Dict[str, Any]] = []
        
        # Промпты для разных задач
        self.prompts = {
            'dpi_analysis': """
Анализируй данные DPI блокировки и определи:
1. Тип DPI (SNI, DPI, Deep Packet Inspection)
2. Методы блокировки (TCP RST, HTTP фильтрация, TLS инспекция)
3. Уровень агрессивности (низкий, средний, высокий)
4. Вероятные векторы обхода

Данные:
{traffic_data}

Ответ в JSON формате:
{{
    "dpi_type": "тип DPI",
    "confidence": 0.9,
    "recommended_techniques": ["spoof_dpi", "domain_fronting"],
    "optimization_suggestions": ["использовать сегментацию TCP", "изменить TLS fingerprint"],
    "new_techniques": [{{"name": "custom_technique", "parameters": {}}}]
}}
""",
            'pipeline_optimization': """
Оптимизируй производительность пайплайнов обхода DPI на основе статистики:

Текущие пайплайны:
{pipeline_stats}

История производительности:
{performance_history}

Проанализируй и предоставь:
1. Рейтинг эффективности каждого пайплайна
2. Причины низкой производительности
3. Рекомендации по оптимизации
4. Предложения по созданию новых пайплайнов

Ответ в JSON формате:
{{
    "pipeline_rankings": [{{"name": "pipeline_name", "score": 0.8, "issues": ["проблема1"]}}],
    "optimization_recommendations": ["рекомендация1"],
    "new_pipeline_templates": [{{"technique": "spoof_dpi", "parameters": {}}}],
    "performance_prediction": 0.85
}}
""",
            'technique_generation': """
Сгенерируй новые техники обхода DPI на основе анализа блокировок:

Анализ блокировок:
{blocking_analysis}

Успешные техники:
{successful_techniques}

Неудачные техники:
{failed_techniques}

Создай инновационные подходы:
1. Комбинации существующих техник
2. Новые методы обфускации
3. Альтернативные протоколы
4. Адаптивные стратегии

Ответ в JSON формате:
{{
    "new_techniques": [
        {{
            "name": "hybrid_technique",
            "description": "описание",
            "technique_type": "spoof_dpi",
            "parameters": {{"param1": "value1"}},
            "expected_success_rate": 0.7,
            "complexity": "medium"
        }}
    ],
    "implementation_priority": ["technique1", "technique2"],
    "estimated_improvement": 0.15
}}
"""
        }
        
        logger.info(f"Инициализация LLM интеграции: {ollama_url}, модель {model}")
    
    async def initialize(self):
        """Инициализация сессии с Ollama"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60.0)
            )
            
            # Проверяем доступность Ollama
            async with self.session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    available_models = [model['name'] for model in models.get('models', [])]
                    
                    if self.model in available_models:
                        logger.info(f"✅ LLM доступен: {self.model}")
                        return True
                    else:
                        logger.warning(f"Модель {self.model} не найдена. Доступные: {available_models}")
                        return False
                else:
                    logger.error(f"Ollama недоступен: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка инициализации LLM: {e}")
            return False
    
    async def analyze_dpi(self, traffic_data: Dict[str, Any]) -> Optional[LLMAnalysis]:
        """
        Анализ DPI блокировок через LLM
        
        Args:
            traffic_data: Данные о трафике и блокировках
            
        Returns:
            LLMAnalysis: Результат анализа
        """
        if not self.session:
            await self.initialize()
        
        try:
            prompt = self.prompts['dpi_analysis'].format(
                traffic_data=json.dumps(traffic_data, indent=2)
            )
            
            response = await self._call_ollama(prompt)
            
            if response:
                return LLMAnalysis(**response)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка анализа DPI: {e}")
            return None
    
    async def optimize_pipelines(self, pipeline_stats: Dict[str, Any], 
                            performance_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Оптимизация пайплайнов через LLM
        
        Args:
            pipeline_stats: Статистика пайплайнов
            performance_history: История производительности
            
        Returns:
            Dict: Рекомендации по оптимизации
        """
        if not self.session:
            await self.initialize()
        
        try:
            prompt = self.prompts['pipeline_optimization'].format(
                pipeline_stats=json.dumps(pipeline_stats, indent=2),
                performance_history=json.dumps(performance_history[-10:], indent=2)
            )
            
            response = await self._call_ollama(prompt)
            
            if response:
                # Сохраняем анализ в историю
                self.analysis_history.append({
                    'timestamp': time.time(),
                    'type': 'pipeline_optimization',
                    'input_stats': pipeline_stats,
                    'result': response
                })
                
                return response
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка оптимизации пайплайнов: {e}")
            return None
    
    async def generate_techniques(self, blocking_analysis: Dict[str, Any],
                              successful_techniques: List[str],
                              failed_techniques: List[str]) -> Optional[Dict[str, Any]]:
        """
        Генерация новых техник обхода через LLM
        
        Args:
            blocking_analysis: Анализ блокировок
            successful_techniques: Список успешных техник
            failed_techniques: Список неудачных техник
            
        Returns:
            Dict: Новые техники
        """
        if not self.session:
            await self.initialize()
        
        try:
            prompt = self.prompts['technique_generation'].format(
                blocking_analysis=json.dumps(blocking_analysis, indent=2),
                successful_techniques=json.dumps(successful_techniques),
                failed_techniques=json.dumps(failed_techniques)
            )
            
            response = await self._call_ollama(prompt)
            
            if response:
                # Сохраняем в историю
                self.analysis_history.append({
                    'timestamp': time.time(),
                    'type': 'technique_generation',
                    'input_blocking': blocking_analysis,
                    'result': response
                })
                
                return response
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка генерации техник: {e}")
            return None
    
    async def _call_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Вызов Ollama API
        
        Args:
            prompt: Промпт для LLM
            
        Returns:
            Dict: Ответ от LLM
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            async with self.session.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            ) as response:
                
                if response.status != 200:
                    logger.error(f"Ollama API ошибка: {response.status}")
                    return None
                
                result = await response.json()
                
                # Парсим JSON из ответа
                response_text = result.get('response', '')
                
                # Ищем JSON в ответе
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    
                    try:
                        parsed_response = json.loads(json_text)
                        logger.info(f"✅ LLM ответ получен ({len(json_text)} символов)")
                        return parsed_response
                    except json.JSONDecodeError as e:
                        logger.warning(f"Ошибка парсинга JSON: {e}")
                        logger.debug(f"JSON текст: {json_text}")
                        return None
                else:
                    logger.warning("JSON не найден в ответе LLM")
                    logger.debug(f"Ответ LLM: {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка вызова Ollama: {e}")
            return None
    
    async def get_pipeline_recommendations(self, current_pipelines: List[BasePipeline], 
                                     target_url: str) -> List[Dict[str, Any]]:
        """
        Получение рекомендаций по пайплайнам для конкретного URL
        
        Args:
            current_pipelines: Текущие пайплайны
            target_url: Целевой URL
            
        Returns:
            List: Рекомендации
        """
        try:
            # Анализируем URL
            url_analysis = {
                'domain': target_url.split('//')[1].split('/')[0] if '//' in target_url else target_url.split('/')[0],
                'protocol': target_url.split(':')[0] if ':' in target_url else 'https',
                'path': '/' + '/'.join(target_url.split('/')[3:]) if len(target_url.split('/')) > 3 else '/',
            }
            
            # Собираем статистику текущих пайплайнов
            pipeline_stats = {}
            for pipeline in current_pipelines:
                pipeline_stats[pipeline.name] = {
                    'technique': pipeline.technique.value,
                    'success_rate': pipeline.metrics.success_rate,
                    'avg_response_time': pipeline.metrics.avg_response_time,
                    'performance_score': pipeline.get_performance_score()
                }
            
            # Запрашиваем рекомендации
            recommendations_prompt = f"""
Проанализируй целевой URL и текущие пайплайны:

Целевой URL: {target_url}
Анализ URL: {json.dumps(url_analysis, indent=2)}

Текущие пайплайны:
{json.dumps(pipeline_stats, indent=2)}

Рекомендуй оптимальные техники обхода для этого URL:
1. Приоритетные техники для данного домена
2. Параметры для каждой техники
3. Ожидаемая успешность
4. Потенциальные проблемы

Ответ в JSON формате:
{{
    "recommendations": [
        {{
            "technique": "spoof_dpi",
            "priority": 1,
            "parameters": {{"tcp_segmentation": 4}},
            "expected_success_rate": 0.7,
            "reasoning": "обоснование"
        }}
    ],
    "domain_specific": true,
    "overall_confidence": 0.85
}}
"""
            
            response = await self._call_ollama(recommendations_prompt)
            
            if response:
                return response.get('recommendations', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return []
    
    async def predict_performance(self, pipeline_config: Dict[str, Any], 
                             context: Dict[str, Any]) -> float:
        """
        Предсказание производительности пайплайна
        
        Args:
            pipeline_config: Конфигурация пайплайна
            context: Контекст использования
            
        Returns:
            float: Предсказанная успешность (0.0 - 1.0)
        """
        try:
            prediction_prompt = f"""
Предскажь производительность пайплайна обхода DPI:

Конфигурация пайплайна:
{json.dumps(pipeline_config, indent=2)}

Контекст использования:
{json.dumps(context, indent=2)}

Исторические данные:
{json.dumps(self.analysis_history[-5:], indent=2)}

Предскажи:
1. Вероятность успешного обхода (0.0 - 1.0)
2. Ожидаемое время отклика в секундах
3. Потенциальные проблемы
4. Рекомендации по улучшению

Ответ в JSON формате:
{{
    "success_probability": 0.75,
    "expected_response_time": 2.5,
    "potential_issues": ["проблема1"],
    "improvements": ["улучшение1"]
}}
"""
            
            response = await self._call_ollama(prediction_prompt)
            
            if response:
                success_prob = response.get('success_probability', 0.5)
                logger.info(f"Предсказанная успешность: {success_prob:.2f}")
                return success_prob
            else:
                return 0.5  # Значение по умолчанию
                
        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            return 0.5
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получение истории анализа
        
        Args:
            limit: Количество записей
            
        Returns:
            List: История анализа
        """
        return self.analysis_history[-limit:]
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("LLM сессия закрыта")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса LLM интеграции
        
        Returns:
            Dict: Статус интеграции
        """
        return {
            'ollama_url': self.ollama_url,
            'model': self.model,
            'connected': self.session is not None,
            'analysis_count': len(self.analysis_history),
            'last_analysis': self.analysis_history[-1] if self.analysis_history else None,
            'available_prompts': list(self.prompts.keys())
        }
