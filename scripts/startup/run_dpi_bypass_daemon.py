#!/usr/bin/env python3
"""
DPI-Bypass Combiner v2.0 - Daemon режим
Запуск в фоновом режиме с автоматическим перезапуском
"""

import sys
import os
import time
import signal
import atexit
from datetime import datetime

# Добавляем путь к модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rsecure/modules/defense'))

try:
    from dpi_bypass_combiner_v2 import dpi_combiner_v2
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

class DPIBypassDaemon:
    """Демон для DPI-Bypass Combiner v2.0"""
    
    def __init__(self):
        self.running = True
        self.log_file = "/Users/razdor/Documents/GitHub/RS---Razdor-Secure/dpi_bypass_daemon.log"
        self.pid_file = "/Users/razdor/Documents/GitHub/RS---Razdor-Secure/dpi_bypass_daemon.pid"
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Регистрируем очистку при выходе
        atexit.register(self.cleanup)
        
        # Создаем PID файл
        self.create_pid_file()
    
    def create_pid_file(self):
        """Создание PID файла"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except:
            pass
    
    def cleanup(self):
        """Очистка при выходе"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.log(f"Получен сигнал {signum}, завершение работы...")
        self.running = False
    
    def log(self, message):
        """Запись в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Вывод в консоль
        print(log_message)
        
        # Запись в файл
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + '\n')
        except:
            pass
    
    def run_daemon(self):
        """Основной цикл демона"""
        self.log("👻 DPI-Bypass Combiner v2.0 Daemon запущен")
        self.log(f"PID: {os.getpid()}")
        
        # Проверяем статус системы
        status = dpi_combiner_v2.get_status()
        self.log(f"Версия: {status['version']}")
        self.log(f"Whitelist доменов: {status['whitelist_domains']} категорий")
        self.log(f"Активных цепочек: {status['active_chains']}")
        
        # Основной цикл
        check_interval = 300  # 5 минут
        last_check = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Проверяем необходимость обхода
                if current_time - last_check >= check_interval:
                    self.log("🔍 Периодическая проверка...")
                    
                    # Здесь можно добавить логику проверки доступности
                    # и автоматического запуска обхода при необходимости
                    
                    last_check = current_time
                
                # Небольшая пауза
                time.sleep(10)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"❌ Ошибка в цикле демона: {e}")
                time.sleep(30)  # Пауза при ошибке
        
        self.log("🏁 DPI-Bypass Daemon завершен")
    
    def run_once(self, target="www.youtube.com"):
        """Запустить обход один раз"""
        self.log(f"🚀 Запуск обхода для {target}")
        
        try:
            result = dpi_combiner_v2.bypass_target(target)
            
            if result.get('direct_access', False):
                self.log(f"✅ {target} доступен напрямую")
            elif result.get('final_success', False):
                self.log(f"🏆 {target} разблокирован через {result.get('successful_chain', 'unknown')}")
            else:
                self.log(f"❌ {target} не разблокирован")
                
        except Exception as e:
            self.log(f"❌ Ошибка обхода: {e}")


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DPI-Bypass Combiner v2.0 Daemon')
    parser.add_argument('--daemon', action='store_true', help='Запустить в режиме демона')
    parser.add_argument('--target', default='www.youtube.com', help='Цель для обхода')
    parser.add_argument('--once', action='store_true', help='Запустить один раз и выйти')
    parser.add_argument('--stop', action='store_true', help='Остановить демона')
    
    args = parser.parse_args()
    
    # Остановка демона
    if args.stop:
        pid_file = "/Users/razdor/Documents/GitHub/RS---Razdor-Secure/dpi_bypass_daemon.pid"
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print("✅ Демон остановлен")
        except:
            print("❌ Не удалось остановить демона")
        return
    
    # Создаем и запускаем демон
    daemon = DPIBypassDaemon()
    
    if args.once:
        # Запуск один раз
        daemon.run_once(args.target)
    elif args.daemon:
        # Запуск в режиме демона
        daemon.run_daemon()
    else:
        # Интерактивный режим
        print("👻 DPI-Bypass Combiner v2.0 Daemon")
        print("Используйте --daemon для фонового режима")
        print("Используйте --once для однократного запуска")
        print("Используйте --stop для остановки демона")
        
        # Запускаем один раз для демонстрации
        daemon.run_once(args.target)


if __name__ == "__main__":
    main()
