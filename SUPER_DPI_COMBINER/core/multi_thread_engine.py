#!/usr/bin/env python3
"""
Многопоточный движок для работы с пайплайнами
Автоматический подбор и переключение между техниками
"""

import asyncio
import threading
import time
import queue
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum

from .base_pipeline import BasePipeline, BypassRequest, BypassResponse, PipelineStatus
from .pipeline_generator import PipelineGenerator

# Импорт логгера с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger(__name__)

class EngineMode(Enum):
    """Режимы работы движка"""
    AUTO_SELECT = "auto_select"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    ADAPTIVE = "adaptive"

@dataclass
class PipelineWorker:
    """Рабочий поток для пайплайна"""
    pipeline: BasePipeline
    thread_id: int
    active: bool = True
    requests_processed: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    last_activity: float = field(default_factory=time.time)

@dataclass
class EngineStats:
    """Статистика движка"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    active_pipelines: int = 0
    best_pipeline: Optional[str] = None
    pipeline_switches: int = 0
    start_time: float = field(default_factory=time.time)

class MultiThreadEngine:
    """Многопоточный движок для управления пайплайнами"""
    
    def __init__(self, max_workers: int = 20, mode: EngineMode = EngineMode.AUTO_SELECT):
        self.max_workers = max_workers
        self.mode = mode
        self.running = False
        
        # Пайплайны и работники
        self.pipelines: Dict[str, BasePipeline] = {}
        self.workers: Dict[str, PipelineWorker] = {}
        self.pipeline_generator = PipelineGenerator(max_workers)
        
        # Очереди
        self.request_queue = asyncio.Queue(maxsize=1000)
        self.response_queue = asyncio.Queue(maxsize=1000)
        self.control_queue = asyncio.Queue()
        
        # Статистика
        self.stats = EngineStats()
        self.performance_history: List[Dict[str, Any]] = []
        
        # Управление
        self.lock = threading.Lock()
        self.active_pipelines: List[str] = []
        self.pipeline_scores: Dict[str, float] = {}
        
        # Потоки
        self.main_thread = None
        self.worker_threads: List[threading.Thread] = []
        self.monitor_thread = None
        
        logger.info(f"Инициализация MultiThreadEngine: {max_workers} потоков, режим {mode.value}")
    
    async def start(self, target_url: str = "https://www.youtube.com"):
        """
        Запуск движка с автоматической оптимизацией
        
        Args:
            target_url: Целевой URL для оптимизации
        """
        if self.running:
            logger.warning("Движок уже запущен")
            return False
        
        logger.info(f"Запуск MultiThreadEngine для {target_url}")
        self.running = True
        self.stats.start_time = time.time()
        
        try:
            # Этап 1: Генерация и тестирование пайплайнов
            await self._initialize_pipelines(target_url)
            
            # Этап 2: Запуск рабочих потоков
            await self._start_worker_threads()
            
            # Этап 3: Запуск монитора
            await self._start_monitor()
            
            # Этап 4: Основной цикл обработки запросов
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Ошибка запуска движка: {e}")
            return False
        
        return True
    
    async def _initialize_pipelines(self, target_url: str):
        """Инициализация пайплайнов через автогенерацию"""
        logger.info("Этап 1: Генерация и оптимизация пайплайнов...")
        
        # Генерируем и тестируем пайплайны
        best_pipelines = await self.pipeline_generator.auto_optimize(
            target_url=target_url,
            generations=3
        )
        
        # Создаем лучшие пайплайны
        for pipeline_data in best_pipelines:
            pipeline_name = pipeline_data['template'].name
            pipeline = self.pipeline_generator.create_pipeline_from_template(
                pipeline_data['template']
            )
            
            if pipeline:
                self.pipelines[pipeline_name] = pipeline
                self.pipeline_scores[pipeline_name] = pipeline_data['performance_score']
                
                logger.info(f"Добавлен пайплайн: {pipeline_name} (score: {pipeline_data['performance_score']:.3f})")
        
        if not self.pipelines:
            raise Exception("Не удалось создать ни одного пайплайна")
        
        logger.info(f"Инициализировано {len(self.pipelines)} пайплайнов")
    
    async def _start_worker_threads(self):
        """Запуск рабочих потоков"""
        logger.info("Этап 2: Запуск рабочих потоков...")
        
        # Создаем работников для каждого пайплайна
        for i, (name, pipeline) in enumerate(self.pipelines.items()):
            if i >= self.max_workers:
                break
            
            worker = PipelineWorker(
                pipeline=pipeline,
                thread_id=i,
                active=True
            )
            
            self.workers[name] = worker
            
            # Запускаем поток
            thread = threading.Thread(
                target=self._worker_loop,
                args=(worker,),
                name=f"PipelineWorker-{name}",
                daemon=True
            )
            
            thread.start()
            self.worker_threads.append(thread)
            
            logger.info(f"Запущен работник: {name} (поток {i})")
        
        self.active_pipelines = list(self.workers.keys())
        logger.info(f"Запущено {len(self.worker_threads)} рабочих потоков")
    
    async def _start_monitor(self):
        """Запуск потока монитора"""
        logger.info("Этап 3: Запуск монитора производительности...")
        
        def monitor_loop():
            while self.running:
                try:
                    # Обновляем статистику
                    self._update_stats()
                    
                    # Адаптивное переключение пайплайнов
                    if self.mode == EngineMode.ADAPTIVE:
                        self._adaptive_pipeline_switching()
                    
                    # Логирование статуса
                    if len(self.performance_history) % 10 == 0:
                        self._log_performance_status()
                    
                    time.sleep(5)  # Мониторинг каждые 5 секунд
                    
                except Exception as e:
                    logger.error(f"Ошибка в мониторе: {e}")
                    time.sleep(5)
        
        self.monitor_thread = threading.Thread(
            target=monitor_loop,
            name="EngineMonitor",
            daemon=True
        )
        
        self.monitor_thread.start()
        logger.info("Монитор производительности запущен")
    
    async def _main_loop(self):
        """Основной цикл обработки запросов"""
        logger.info("Этап 4: Запуск основного цикла...")
        
        while self.running:
            try:
                # Получаем запрос из очереди
                try:
                    request_data = await asyncio.wait_for(
                        self.request_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Выбираем лучший пайплайн для запроса
                pipeline_name = self._select_best_pipeline(request_data)
                
                if pipeline_name and pipeline_name in self.workers:
                    worker = self.workers[pipeline_name]
                    
                    # Отправляем запрос работнику
                    response = await self._execute_request(worker, request_data)
                    
                    # Отправляем ответ
                    await self.response_queue.put(response)
                    
                    # Обновляем статистику
                    self._update_worker_stats(worker, response.success)
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(0.1)
    
    def _worker_loop(self, worker: PipelineWorker):
        """Цикл рабочего потока"""
        logger.info(f"Рабочий поток {worker.pipeline.name} запущен")
        
        while worker.active and self.running:
            try:
                # Здесь работник ждет запросы
                # В реальной реализации здесь будет сетевое взаимодействие
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Ошибка в рабочем потоке {worker.pipeline.name}: {e}")
                time.sleep(1)
        
        logger.info(f"Рабочий поток {worker.pipeline.name} остановлен")
    
    async def _execute_request(self, worker: PipelineWorker, request_data: Dict[str, Any]) -> BypassResponse:
        """Выполнение запроса через работника"""
        start_time = time.time()
        
        try:
            # Создаем запрос
            request = BypassRequest(
                host=request_data.get('host', 'www.youtube.com'),
                port=request_data.get('port', 443),
                method=request_data.get('method', 'GET'),
                headers=request_data.get('headers', {}),
                data=request_data.get('data'),
                timeout=request_data.get('timeout', 30.0)
            )
            
            # Выполняем через пайплайн
            response = await worker.pipeline.execute(request)
            
            # Обновляем время отклика
            response.response_time = time.time() - start_time
            
            return response
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    def _select_best_pipeline(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Выбор лучшего пайплайна для запроса"""
        if not self.active_pipelines:
            return None
        
        with self.lock:
            if self.mode == EngineMode.PERFORMANCE:
                # Выбираем самый быстрый
                best_name = min(
                    self.active_pipelines,
                    key=lambda name: self.workers[name].avg_response_time
                )
                
            elif self.mode == EngineMode.RELIABILITY:
                # Выбираем самый надежный
                best_name = max(
                    self.active_pipelines,
                    key=lambda name: self.workers[name].success_rate
                )
                
            elif self.mode == EngineMode.ADAPTIVE:
                # Адаптивный выбор на основе производительности
                best_name = max(
                    self.active_pipelines,
                    key=lambda name: self.pipeline_scores.get(name, 0.0)
                )
                
            else:  # AUTO_SELECT
                # Сбалансированный выбор
                best_name = max(
                    self.active_pipelines,
                    key=lambda name: (
                        self.workers[name].success_rate * 0.6 +
                        (1.0 - min(self.workers[name].avg_response_time / 30.0, 1.0)) * 0.4
                    )
                )
        
        return best_name
    
    def _adaptive_pipeline_switching(self):
        """Адаптивное переключение между пайплайнами"""
        with self.lock:
            current_time = time.time()
            
            # Проверяем производительность каждого активного пайплайна
            underperforming = []
            
            for name in self.active_pipelines:
                worker = self.workers[name]
                
                # Пайплайн считается неэффективным если:
                # 1. Успешность < 30%
                # 2. Среднее время > 30 секунд
                # 3. Нет активности последние 2 минуты
                
                time_since_activity = current_time - worker.last_activity
                
                if (worker.success_rate < 0.3 or 
                    worker.avg_response_time > 30.0 or
                    time_since_activity > 120):
                    
                    underperforming.append(name)
            
            # Заменяем неэффективные пайплайны
            if underperforming:
                # Находим запасные пайплайны
                backup_pipelines = [
                    name for name in self.pipelines.keys()
                    if name not in self.active_pipelines
                ]
                
                for bad_name in underperforming:
                    if backup_pipelines:
                        # Выбираем лучший из запасных
                        best_backup = max(
                            backup_pipelines,
                            key=lambda name: self.pipeline_scores.get(name, 0.0)
                        )
                        
                        # Переключаем
                        self._switch_pipeline(bad_name, best_backup)
                        backup_pipelines.remove(best_backup)
                        
                        logger.info(f"Переключение: {bad_name} -> {best_backup}")
    
    def _switch_pipeline(self, old_name: str, new_name: str):
        """Переключение между пайплайнами"""
        if old_name in self.active_pipelines:
            self.active_pipelines.remove(old_name)
        
        if new_name not in self.active_pipelines:
            self.active_pipelines.append(new_name)
        
        self.stats.pipeline_switches += 1
        
        # Сбрасываем статистику нового пайплайна
        if new_name in self.workers:
            self.workers[new_name].requests_processed = 0
            self.workers[new_name].success_rate = 0.0
            self.workers[new_name].avg_response_time = 0.0
    
    def _update_worker_stats(self, worker: PipelineWorker, success: bool):
        """Обновление статистики работника"""
        with self.lock:
            worker.requests_processed += 1
            worker.last_activity = time.time()
            
            # Обновляем успешность
            if worker.requests_processed == 1:
                worker.success_rate = 1.0 if success else 0.0
                worker.avg_response_time = 0.0
            else:
                # Экспоненциальное скользящее среднее
                alpha = 0.1
                worker.success_rate = (
                    worker.success_rate * (1 - alpha) + 
                    (1.0 if success else 0.0) * alpha
                )
            
            # Обновляем общую статистику
            self.stats.total_requests += 1
            
            if success:
                self.stats.successful_requests += 1
            else:
                self.stats.failed_requests += 1
            
            self.stats.success_rate = (
                self.stats.successful_requests / self.stats.total_requests
            )
    
    def _update_stats(self):
        """Обновление общей статистики"""
        with self.lock:
            active_count = 0
            total_response_time = 0.0
            
            for worker in self.workers.values():
                if worker.active:
                    active_count += 1
                    total_response_time += worker.avg_response_time
            
            self.stats.active_pipelines = active_count
            
            if active_count > 0:
                self.stats.avg_response_time = total_response_time / active_count
            
            # Находим лучший пайплайн
            if self.active_pipelines:
                best_name = max(
                    self.active_pipelines,
                    key=lambda name: (
                        self.workers[name].success_rate * 0.7 +
                        self.pipeline_scores.get(name, 0.0) * 0.3
                    )
                )
                self.stats.best_pipeline = best_name
            
            # Сохраняем в историю
            self.performance_history.append({
                'timestamp': time.time(),
                'stats': self.stats.__dict__.copy(),
                'active_pipelines': self.active_pipelines.copy()
            })
            
            # Ограничиваем историю
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
    
    def _log_performance_status(self):
        """Логирование статуса производительности"""
        logger.info(f"=== Статус движка (работает {time.time() - self.stats.start_time:.1f}s) ===")
        logger.info(f"Всего запросов: {self.stats.total_requests}")
        logger.info(f"Успешность: {self.stats.success_rate:.2%}")
        logger.info(f"Среднее время: {self.stats.avg_response_time:.3f}s")
        logger.info(f"Активных пайплайнов: {self.stats.active_pipelines}")
        logger.info(f"Лучший пайплайн: {self.stats.best_pipeline}")
        logger.info(f"Переключений: {self.stats.pipeline_switches}")
        
        # Топ-5 пайплайнов
        if self.active_pipelines:
            top_pipelines = sorted(
                self.active_pipelines,
                key=lambda name: self.workers[name].success_rate,
                reverse=True
            )[:5]
            
            logger.info("Топ пайплайнов:")
            for i, name in enumerate(top_pipelines, 1):
                worker = self.workers[name]
                logger.info(f"  {i}. {name}: {worker.success_rate:.2%} ({worker.avg_response_time:.3f}s)")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Optional[BypassResponse]:
        """
        Обработка внешнего запроса
        
        Args:
            request_data: Данные запроса
            
        Returns:
            BypassResponse: Результат обработки
        """
        if not self.running:
            return None
        
        # Добавляем в очередь
        try:
            await self.request_queue.put(request_data, timeout=1.0)
            
            # Ждем ответа
            response = await asyncio.wait_for(
                self.response_queue.get(),
                timeout=60.0
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.error("Таймаут обработки запроса")
            return BypassResponse(
                success=False,
                error="Request timeout"
            )
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Получение статуса движка"""
        with self.lock:
            return {
                'running': self.running,
                'mode': self.mode.value,
                'stats': self.stats.__dict__,
                'active_pipelines': self.active_pipelines.copy(),
                'total_pipelines': len(self.pipelines),
                'worker_count': len(self.worker_threads),
                'uptime': time.time() - self.stats.start_time if self.running else 0
            }
    
    async def stop(self):
        """Остановка движка"""
        logger.info("Остановка MultiThreadEngine...")
        
        self.running = False
        
        # Останавливаем рабочие потоки
        for worker in self.workers.values():
            worker.active = False
        
        # Ждем завершения потоков
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        
        # Очищаем пайплайны
        for pipeline in self.pipelines.values():
            try:
                pipeline.cleanup()
            except Exception as e:
                logger.error(f"Ошибка очистки пайплайна {pipeline.name}: {e}")
        
        logger.info("MultiThreadEngine остановлен")
    
    def set_mode(self, mode: EngineMode):
        """Установка режима работы"""
        with self.lock:
            self.mode = mode
            logger.info(f"Режим изменен на: {mode.value}")
