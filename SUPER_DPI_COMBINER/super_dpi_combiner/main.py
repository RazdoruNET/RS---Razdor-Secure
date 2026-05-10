#!/usr/bin/env python3
"""
Super DPI Combiner - Стабилизированный главный модуль
TRUTH MODE - никаких симуляций
"""

import asyncio
import sys
from .core import Runner, Request, get_logger, get_shutdown_manager
from .pipelines import HTTPFragmentation, Echo

async def main():
    """Основная функция - реальный execution loop"""
    logger = get_logger("Main")
    shutdown_manager = get_shutdown_manager()
    
    logger.info("Super DPI Combiner - Runtime Stabilization v1")
    logger.info("TRUTH MODE активирован - никаких симуляций")
    
    # Создаем runner
    runner = Runner()
    
    # Регистрируем пайплайны
    runner.register_pipeline(HTTPFragmentation())
    runner.register_pipeline(Echo())
    
    # Показываем доступные пайплайны
    runner.list_pipelines()
    
    # Настраиваем graceful shutdown
    shutdown_manager.setup_signal_handlers()
    
    # Интерактивный режим
    while not shutdown_manager.shutdown_requested:
        try:
            print("\n" + "=" * 50)
            print("Доступные команды:")
            print("  test <host> [port]  - тестировать запрос")
            print("  stats               - показать статистику") 
            print("  list                - показать пайплайны")
            print("  quit                - выход")
            print("=" * 50)
            
            command = input("→ ").strip().split()
            if not command:
                continue
                
            cmd = command[0].lower()
            
            if cmd == 'quit' or cmd == 'exit':
                logger.info("Запрошен выход")
                break
                
            elif cmd == 'test':
                if len(command) < 2:
                    logger.error("Укажите host")
                    continue
                    
                host = command[1]
                port = int(command[2]) if len(command) > 2 else 80
                pipeline_name = command[3] if len(command) > 3 else None
                
                request = Request(
                    host=host,
                    port=port,
                    method="GET"
                )
                
                # Выбираем пайплайн
                pipeline = None
                if pipeline_name and pipeline_name in runner.pipelines:
                    pipeline = runner.pipelines[pipeline_name]
                elif runner.pipelines:
                    pipeline = list(runner.pipelines.values())[0]
                else:
                    logger.error("Нет доступных пайплайнов")
                    continue
                
                # Выполняем асинхронно
                response = await runner.run(pipeline, request)
                
            elif cmd == 'stats':
                stats = runner.get_stats()
                logger.info(f"Статистика: {stats['total_requests']} запросов, "
                           f"{stats['successful_requests']} успешных, "
                           f"{stats['failed_requests']} ошибок")
                logger.info(f"Success rate: {stats['success_rate']:.1f}%")
                
            elif cmd == 'list':
                runner.list_pipelines()
                
            else:
                logger.error(f"Неизвестная команда: {cmd}")
                
        except KeyboardInterrupt:
            logger.info("Прерывание пользователем")
            break
        except Exception as e:
            logger.error(f"Ошибка: {e}")
    
    # Graceful shutdown
    await shutdown_manager.shutdown("user_request")
    
    # Финальная статистика
    final_stats = runner.get_stats()
    logger.info(f"Финальная статистика: {final_stats['total_requests']} запросов")
    logger.info(f"Success rate: {final_stats['success_rate']:.1f}%")
    
    if final_stats['total_requests'] > 0:
        if final_stats['success_rate'] == 100.0:
            logger.info("✅ Все запросы выполнены успешно")
        elif final_stats['success_rate'] > 0:
            logger.warning(f"⚠️ Частичный успех: {final_stats['success_rate']:.1f}%")
        else:
            logger.error("❌ Все запросы завершились ошибкой")

if __name__ == "__main__":
    asyncio.run(main())
