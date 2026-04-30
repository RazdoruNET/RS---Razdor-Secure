#!/usr/bin/env python3
"""
RSecure Integrated Launcher
Запускает основную систему RSecure с веб-дашбордом
"""

import sys
import os
import threading
import time
import signal
from pathlib import Path

# Добавляем rsecure и mock библиотеки в путь
sys.path.insert(0, str(Path(__file__).parent / 'rsecure'))
sys.path.insert(0, str(Path(__file__).parent / 'mock_libs'))

# Попытка импорта с обработкой ошибок зависимостей
try:
    from rsecure.rsecure_main import RSecureMain
    RSECURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  RSecure модули недоступны: {e}")
    print("📊 Запуск дашборда в автономном режиме (без модулей безопасности)")
    RSECURE_AVAILABLE = False

from rsecure.utils.dashboard import RSecureDashboard

class RSecureIntegrated:
    """Интегрированная система RSecure с дашбордом"""
    
    def __init__(self):
        self.rsecure = None
        self.dashboard = None
        self.running = False
        self.shutdown_event = threading.Event()
        
    def start(self):
        """Запуск интегрированной системы"""
        print("🛡️ RSecure Integrated System Starting...")
        print("=" * 60)
        
        try:
            # 1. Запуск основной системы RSecure (если доступна)
            if RSECURE_AVAILABLE:
                print("\n📡 Запуск RSecure модулей безопасности...")
                self.rsecure = RSecureMain()
                self.rsecure.start()
                
                # Ждем инициализации компонентов
                time.sleep(3)
            else:
                print("\n⚠️  RSecure модули не загружены (отсутствуют зависимости)")
                print("💡 Для полной функциональности установите зависимости:")
                print("   pip install -r requirements.txt")
            
            # 2. Запуск веб-дашборда с подключением к RSecure
            print("\n🌐 Запуск веб-дашборда...")
            self.dashboard = RSecureDashboard(rsecure_instance=self.rsecure)
            
            # Запускаем дашборд в отдельном потоке
            dashboard_thread = threading.Thread(
                target=self._run_dashboard,
                daemon=True
            )
            dashboard_thread.start()
            
            self.running = True
            
            # 3. Настройка обработчиков сигналов
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            print("\n✅ RSecure Integrated System запущена успешно!")
            print("=" * 60)
            print("📊 Веб-дашборд: http://127.0.0.1:5002")
            print("📋 Логи: ./logs/")
            print("⚠️  Нажмите Ctrl+C для остановки")
            print("=" * 60)
            
            # Основной цикл
            while self.running and not self.shutdown_event.is_set():
                time.sleep(10)
                
                # Периодический вывод статуса
                if self.rsecure and RSECURE_AVAILABLE:
                    status = self.rsecure.get_status()
                    metrics = status.get('metrics', {})
                    print(f"📈 Событий: {metrics.get('events_processed', 0)}, "
                          f"Угроз: {metrics.get('threats_detected', 0)}, "
                          f"Прогнозов: {metrics.get('neural_predictions', 0)}")
                else:
                    print("📊 Дашборд работает в автономном режиме")
        
        except Exception as e:
            print(f"\n❌ Ошибка запуска: {e}")
            import traceback
            traceback.print_exc()
            self.stop()
            sys.exit(1)
    
    def _run_dashboard(self):
        """Запуск дашборда в отдельном потоке"""
        try:
            self.dashboard.run(host='127.0.0.1', port=5002, debug=False)
        except Exception as e:
            print(f"❌ Ошибка дашборда: {e}")
    
    def stop(self):
        """Остановка системы"""
        print("\n🛑 Остановка RSecure Integrated System...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Остановка RSecure
        if self.rsecure:
            self.rsecure.stop()
        
        # Остановка дашборда
        if self.dashboard:
            self.dashboard.stop_data_collection()
        
        print("✅ Система остановлена")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        print(f"\n📨 Получен сигнал {signum}")
        self.stop()

def main():
    """Точка входа"""
    integrated = RSecureIntegrated()
    
    try:
        integrated.start()
    except KeyboardInterrupt:
        integrated.stop()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        integrated.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
