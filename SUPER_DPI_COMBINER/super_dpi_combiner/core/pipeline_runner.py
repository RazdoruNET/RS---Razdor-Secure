#!/usr/bin/env python3
"""
Pipeline Runner - Minimal Execution Engine
Реализация минимального движка выполнения пайплайнов
"""

import time
import asyncio
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

from core.base_pipeline import BasePipeline, BypassRequest, BypassResponse
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ExecutionResult:
    """Унифицированный формат результата выполнения"""
    success: bool
    pipeline: str
    error: Optional[str] = None
    duration: float = 0.0
    response: Optional[BypassResponse] = None

class ExecutionGuard:
    """Слой защиты выполнения - валидация пайплайнов"""
    
    @staticmethod
    def validate_pipeline(pipeline: BasePipeline) -> tuple[bool, str]:
        """
        Проверка валидности пайплайна
        
        Args:
            pipeline: Пайплайн для проверки
            
        Returns:
            tuple[bool, str]: (Валиден, Сообщение об ошибке)
        """
        # Проверка 1: pipeline is instantiable
        if not isinstance(pipeline, BasePipeline):
            return False, "Pipeline is not a BasePipeline instance"
        
        # Проверка 2: execute is implemented
        if not hasattr(pipeline, 'execute') or not callable(pipeline.execute):
            return False, "Pipeline missing execute method"
        
        # Проверка 3: execute is async
        if not asyncio.iscoroutinefunction(pipeline.execute):
            return False, "Pipeline execute method must be async"
        
        # Проверка 4: _validate_initialized method exists
        if not hasattr(pipeline, '_validate_initialized') or not callable(pipeline._validate_initialized):
            return False, "Pipeline missing _validate_initialized method"
        
        # Проверка 5: _mark_initialized method exists
        if not hasattr(pipeline, '_mark_initialized') or not callable(pipeline._mark_initialized):
            return False, "Pipeline missing _mark_initialized method"
        
        return True, "Pipeline is valid"
    
    @staticmethod
    def validate_initialization(pipeline: BasePipeline) -> tuple[bool, str]:
        """
        Проверка статуса инициализации пайплайна
        
        Args:
            pipeline: Пайплайн для проверки
            
        Returns:
            tuple[bool, str]: (Инициализирован, Сообщение об ошибке)
        """
        if not pipeline._validate_initialized():
            return False, "Pipeline not initialized"
        
        return True, "Pipeline initialized"

class PipelineRunner:
    """Минимальный движок выполнения пайплайнов"""
    
    def __init__(self):
        self.execution_guard = ExecutionGuard()
        logger.info("PipelineRunner initialized")
    
    async def run(self, pipeline: BasePipeline, request: BypassRequest) -> ExecutionResult:
        """
        Основной метод выполнения пайплайна
        
        Args:
            pipeline: Пайплайн для выполнения
            request: Запрос на обход DPI
            
        Returns:
            ExecutionResult: Результат выполнения
        """
        start_time = time.time()
        pipeline_name = getattr(pipeline, 'name', 'Unknown')
        
        logger.info(f"Starting pipeline execution: {pipeline_name}")
        
        # 1. Initialize pipeline (если еще не инициализирован)
        try:
            if not pipeline._validate_initialized():
                logger.info(f"Initializing pipeline: {pipeline_name}")
                init_success = pipeline.initialize({})
                pipeline._mark_initialized(init_success)
                
                if not init_success:
                    duration = time.time() - start_time
                    error_msg = f"Pipeline {pipeline_name} initialization failed"
                    logger.error(error_msg)
                    return ExecutionResult(
                        success=False,
                        pipeline=pipeline_name,
                        error=error_msg,
                        duration=duration
                    )
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Pipeline {pipeline_name} initialization error: {str(e)}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                pipeline=pipeline_name,
                error=error_msg,
                duration=duration
            )
        
        # 2. Execution guard validation
        is_valid, validation_error = self.execution_guard.validate_pipeline(pipeline)
        if not is_valid:
            duration = time.time() - start_time
            error_msg = f"Pipeline {pipeline_name} validation failed: {validation_error}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                pipeline=pipeline_name,
                error=error_msg,
                duration=duration
            )
        
        is_initialized, init_error = self.execution_guard.validate_initialization(pipeline)
        if not is_initialized:
            duration = time.time() - start_time
            error_msg = f"Pipeline {pipeline_name} initialization validation failed: {init_error}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                pipeline=pipeline_name,
                error=error_msg,
                duration=duration
            )
        
        # 3. Execute pipeline
        try:
            logger.info(f"Executing pipeline: {pipeline_name}")
            response = await pipeline.safe_execute(request)
            
            duration = time.time() - start_time
            
            # 4. Return structured result
            result = ExecutionResult(
                success=response.success,
                pipeline=pipeline_name,
                error=response.error_reason if not response.success else None,
                duration=duration,
                response=response
            )
            
            if result.success:
                logger.info(f"✅ Pipeline {pipeline_name} completed successfully in {duration:.3f}s")
            else:
                logger.warning(f"❌ Pipeline {pipeline_name} failed in {duration:.3f}s: {result.error}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Pipeline {pipeline_name} execution exception: {str(e)}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                pipeline=pipeline_name,
                error=error_msg,
                duration=duration
            )
    
    async def run_with_timeout(self, pipeline: BasePipeline, request: BypassRequest, timeout: float = 30.0) -> ExecutionResult:
        """
        Выполнение пайплайна с таймаутом
        
        Args:
            pipeline: Пайплайн для выполнения
            request: Запрос на обход DPI
            timeout: Максимальное время выполнения
            
        Returns:
            ExecutionResult: Результат выполнения
        """
        try:
            result = await asyncio.wait_for(
                self.run(pipeline, request),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            pipeline_name = getattr(pipeline, 'name', 'Unknown')
            error_msg = f"Pipeline {pipeline_name} execution timeout after {timeout}s"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                pipeline=pipeline_name,
                error=error_msg,
                duration=timeout
            )
        except Exception as e:
            pipeline_name = getattr(pipeline, 'name', 'Unknown')
            error_msg = f"Pipeline {pipeline_name} runner error: {str(e)}"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                pipeline=pipeline_name,
                error=error_msg,
                duration=0.0
            )

# Singleton instance
_pipeline_runner = None

def get_pipeline_runner() -> PipelineRunner:
    """Получение экземпляра PipelineRunner (singleton)"""
    global _pipeline_runner
    if _pipeline_runner is None:
        _pipeline_runner = PipelineRunner()
    return _pipeline_runner
