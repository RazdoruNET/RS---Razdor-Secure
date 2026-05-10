#!/usr/bin/env python3
"""
Graceful Shutdown - Корректное завершение работы
Без hanging tasks и orphan sockets
"""

import asyncio
import signal
from typing import Set
from .logging import get_logger

class ShutdownManager:
    """Менеджер корректного завершения"""
    
    def __init__(self):
        self.logger = get_logger("Shutdown")
        self.running_tasks: Set[asyncio.Task] = set()
        self.shutdown_requested = False
        
    def register_task(self, task: asyncio.Task):
        """Зарегистрировать задачу для отслеживания"""
        self.running_tasks.add(task)
        
    def unregister_task(self, task: asyncio.Task):
        """Убрать задачу из отслеживания"""
        self.running_tasks.discard(task)
        
    async def shutdown(self, signal_name: str = "unknown"):
        """Корректно завершить все задачи"""
        if self.shutdown_requested:
            return
            
        self.shutdown_requested = True
        self.logger.info(f"Начало graceful shutdown (signal: {signal_name})")
        
        # Отменяем все активные задачи
        for task in list(self.running_tasks):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.error(f"Ошибка при отмене задачи: {e}")
        
        # Ждём завершения всех задач
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
            
        self.logger.info("Graceful shutdown завершён")
        
    def setup_signal_handlers(self):
        """Настроить обработчики сигналов"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            asyncio.create_task(self.shutdown(signal_name))
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

# Global shutdown manager
_shutdown_manager = None

def get_shutdown_manager() -> ShutdownManager:
    """Получить глобальный менеджер завершения"""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = ShutdownManager()
    return _shutdown_manager
