#!/usr/bin/env python3
"""
Super DPI Combiner - Минимальный главный модуль
"""

import sys
from .core import Runner, Request
from .pipelines import HTTPFragmentation, Echo

def main():
    """Основная функция - реальный execution loop"""
    print("🚀 Super DPI Combiner - Minimal Mode")
    print("=" * 50)
    
    # Создаем runner
    runner = Runner()
    
    # Регистрируем пайплайны
    runner.register_pipeline(HTTPFragmentation())
    runner.register_pipeline(Echo())
    
    # Показываем доступные пайплайны
    runner.list_pipelines()
    
    print("\n🎯 Режим реального выполнения (TRUTH MODE)")
    print("❌ Без симуляции, без фейковых успехов")
    print("✅ Только реальное выполнение кода")
    
    # Интерактивный режим
    while True:
        try:
            print("\n" + "=" * 50)
            print("Введите команду:")
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
                print("🛑 Выход...")
                break
                
            elif cmd == 'test':
                if len(command) < 2:
                    print("❌ Укажите host")
                    continue
                    
                host = command[1]
                
                # Ищем опцию -p для пайплайна
                pipeline_name = None
                port = 80
                
                i = 2
                while i < len(command):
                    if command[i] == '-p' and i + 1 < len(command):
                        pipeline_name = command[i + 1]
                    elif command[i] == '--port' and i + 1 < len(command):
                        try:
                            port = int(command[i + 1])
                        except ValueError:
                            print("❌ Неверный порт")
                            continue
                    i += 2
                
                request = Request(
                    host=host,
                    port=port,
                    method="GET"
                )
                
                response = runner.execute_request(request, pipeline_name)
                
            elif cmd == 'stats':
                stats = runner.get_stats()
                print(f"\n📊 Статистика:")
                print(f"  Всего запросов: {stats['total_requests']}")
                print(f"  Успешных: {stats['successful_requests']}")
                print(f"  Ошибок: {stats['failed_requests']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
                
            elif cmd == 'list':
                runner.list_pipelines()
                
            else:
                print(f"❌ Неизвестная команда: {cmd}")
                
        except KeyboardInterrupt:
            print("\n🛑 Прерывание...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Финальная статистика
    final_stats = runner.get_stats()
    print(f"\n📋 Финальная статистика:")
    print(f"  Выполнено запросов: {final_stats['total_requests']}")
    print(f"  Успешных: {final_stats['successful_requests']}")
    print(f"  Ошибок: {final_stats['failed_requests']}")
    print(f"  Итоговый success rate: {final_stats['success_rate']:.1f}%")
    
    if final_stats['total_requests'] > 0:
        if final_stats['success_rate'] == 100.0:
            print("✅ Все запросы выполнены успешно")
        elif final_stats['success_rate'] > 0:
            print(f"⚠️ Частичный успех: {final_stats['success_rate']:.1f}%")
        else:
            print("❌ Все запросы завершились ошибкой")

if __name__ == "__main__":
    main()
