#!/usr/bin/env python3
"""
Pipeline Runner - Минимальный исполнитель
"""

import time
from typing import Dict, List, Optional
from .base import BasePipeline, Request, Response

class Runner:
    """Минимальный runner для выполнения пайплайнов"""
    
    def __init__(self):
        self.pipelines: Dict[str, BasePipeline] = {}
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
    
    def register_pipeline(self, pipeline: BasePipeline):
        """Зарегистрировать пайплайн"""
        self.pipelines[pipeline.name] = pipeline
        print(f"✓ Зарегистрирован пайплайн: {pipeline.name}")
    
    def execute_request(self, request: Request, pipeline_name: Optional[str] = None) -> Response:
        """Выполнить запрос"""
        self.stats['total_requests'] += 1
        
        # Выбираем пайплайн
        if pipeline_name and pipeline_name in self.pipelines:
            pipeline = self.pipelines[pipeline_name]
        elif self.pipelines:
            pipeline = list(self.pipelines.values())[0]  # Первый доступный
        else:
            return Response(
                success=False,
                error="Нет доступных пайплайнов"
            )
        
        print(f"→ Выполнение запроса через {pipeline.name}")
        print(f"  Host: {request.host}:{request.port}")
        
        try:
            start_time = time.time()
            response = pipeline.execute(request)
            latency = time.time() - start_time
            
            # Обновляем статистику пайплайна
            pipeline.last_latency = latency
            
            # Обновляем общую статистику
            if response.success:
                self.stats['successful_requests'] += 1
                print(f"✅ Успех: {response.status_code} ({latency:.3f}s)")
            else:
                self.stats['failed_requests'] += 1
                print(f"❌ Ошибка: {response.error}")
                
            response.latency = latency
            return response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            print(f"❌ Исключение: {e}")
            return Response(
                success=False,
                error=str(e)
            )
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        success_rate = 0.0
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            
        return {
            **self.stats,
            'success_rate': success_rate,
            'available_pipelines': list(self.pipelines.keys())
        }
    
    def list_pipelines(self):
        """Показать доступные пайплайны"""
        print("\n📋 Доступные пайплайны:")
        for name, pipeline in self.pipelines.items():
            stats = pipeline.get_stats()
            print(f"  • {name} (latency: {stats.get('last_latency', 0):.3f}s)")
