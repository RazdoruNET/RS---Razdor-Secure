#!/usr/bin/env python3
"""
Pipeline Runner - Стабилизированный исполнитель
Только contracts, никаких magic
"""

import asyncio
import time
from typing import Dict, Optional
from .contracts import BasePipeline, Request, Response
from .logging import get_logger

class Runner:
    """Минимальный runner для выполнения пайплайнов"""
    
    def __init__(self):
        self.pipelines: Dict[str, BasePipeline] = {}
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        self.logger = get_logger("Runner")
        
    def register_pipeline(self, pipeline: BasePipeline):
        """Зарегистрировать пайплайн"""
        self.pipelines[pipeline.name] = pipeline
        self.logger.info(f"Зарегистрирован пайплайн: {pipeline.name}")
        
    async def run(
        self,
        pipeline: BasePipeline,
        request: Request
    ) -> Response:
        """Запустить пайплайн с таймаутом"""
        self.stats['total_requests'] += 1
        pipeline.set_status(pipeline.status.RUNNING)
        
        start_time = time.time()
        
        try:
            # Выполняем с таймаутом
            response = await asyncio.wait_for(
                pipeline.execute(request),
                timeout=request.timeout
            )
            
            latency = time.time() - start_time
            response.latency = latency
            response.pipeline = pipeline.name
            
            # Обновляем статистику
            if response.success:
                self.stats['successful_requests'] += 1
                pipeline.set_status(pipeline.status.COMPLETED)
                self.logger.success(
                    f"Успешное выполнение: {response.status_code}",
                    pipeline=pipeline.name,
                    latency=latency
                )
            else:
                self.stats['failed_requests'] += 1
                pipeline.set_status(pipeline.status.FAILED)
                self.logger.error(
                    f"Ошибка выполнения: {response.error}",
                    pipeline=pipeline.name
                )
                
            return response
            
        except asyncio.TimeoutError:
            self.stats['failed_requests'] += 1
            pipeline.set_status(pipeline.status.FAILED)
            self.logger.error(
                f"Таймаут выполнения ({request.timeout}s)",
                pipeline=pipeline.name
            )
            return Response(
                success=False,
                error=f"Timeout after {request.timeout}s",
                pipeline=pipeline.name
            )
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            pipeline.set_status(pipeline.status.FAILED)
            self.logger.error(
                f"Исключение при выполнении: {e}",
                pipeline=pipeline.name
            )
            return Response(
                success=False,
                error=f"Runner exception: {e}",
                pipeline=pipeline.name
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
        self.logger.info("Доступные пайплайны:")
        for name, pipeline in self.pipelines.items():
            status = pipeline.get_status().value
            self.logger.info(f"  • {name} (status: {status})")
