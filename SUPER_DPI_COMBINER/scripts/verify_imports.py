#!/usr/bin/env python3
"""
Import Verification Script for Super DPI Combiner
Проверяет, что все модули проекта могут быть импортированы без ошибок
"""

import sys
import os
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ImportVerifier:
    """Верификатор импортов для проекта"""
    
    def __init__(self):
        self.results = {
            'success': [],
            'failure': [],
            'total': 0,
            'success_count': 0,
            'failure_count': 0
        }
        
    def test_import(self, module_name: str) -> Tuple[bool, str]:
        """
        Тестирование импорта модуля
        
        Args:
            module_name: Имя модуля для импорта
            
        Returns:
            Tuple[bool, str]: (успех, сообщение об ошибке)
        """
        try:
            importlib.import_module(module_name)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def verify_core_modules(self):
        """Проверка основных модулей core"""
        core_modules = [
            'super_dpi_combiner.core.types',
            'super_dpi_combiner.core.safe_pipeline',
            'super_dpi_combiner.core.base_pipeline',
            'super_dpi_combiner.core.registry',
            'super_dpi_combiner.core.http_client',
        ]
        
        print("🔍 Проверка core модулей...")
        for module in core_modules:
            self._test_and_log(module)
    
    def verify_utils_modules(self):
        """Проверка модулей utils"""
        utils_modules = [
            'super_dpi_combiner.utils.logger',
        ]
        
        print("🔍 Проверка utils модулей...")
        for module in utils_modules:
            self._test_and_log(module)
    
    def verify_config_modules(self):
        """Проверка модулей config"""
        config_modules = [
            'super_dpi_combiner.config.settings',
        ]
        
        print("🔍 Проверка config модулей...")
        for module in config_modules:
            self._test_and_log(module)
    
    def verify_pipeline_modules(self):
        """Проверка модулей pipelines"""
        pipelines_dir = project_root / "super_dpi_combiner" / "pipelines"
        pipeline_modules = []
        
        if pipelines_dir.exists():
            # Рекурсивный поиск всех .py файлов в pipelines
            for py_file in pipelines_dir.rglob("*.py"):
                if py_file.name != "__init__.py":
                    # Преобразуем путь в имя модуля
                    relative_path = py_file.relative_to(project_root)
                    module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
                    pipeline_modules.append(module_name)
        
        print("🔍 Проверка pipeline модулей...")
        for module in pipeline_modules:
            self._test_and_log(module)
    
    def verify_main_entrypoint(self):
        """Проверка основного entrypoint"""
        main_modules = [
            'super_dpi_combiner.main',
            'super_dpi_combiner.__main__',
        ]
        
        print("🔍 Проверка main entrypoints...")
        for module in main_modules:
            self._test_and_log(module)
    
    def _test_and_log(self, module_name: str):
        """Тестирование и логирование результата"""
        self.results['total'] += 1
        
        success, error = self.test_import(module_name)
        
        if success:
            self.results['success'].append(module_name)
            self.results['success_count'] += 1
            print(f"  ✅ {module_name}")
        else:
            self.results['failure'].append((module_name, error))
            self.results['failure_count'] += 1
            print(f"  ❌ {module_name}: {error}")
    
    def run_full_verification(self):
        """Запуск полной верификации импортов"""
        print("🚀 Начало верификации импортов Super DPI Combiner")
        print("=" * 60)
        
        # Проверяем все категории модулей
        self.verify_core_modules()
        self.verify_utils_modules()
        self.verify_config_modules()
        self.verify_pipeline_modules()
        self.verify_main_entrypoint()
        
        # Выводим итоговый отчет
        self.print_summary()
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 60)
        
        print(f"Всего модулей: {self.results['total']}")
        print(f"Успешно: {self.results['success_count']} ✅")
        print(f"С ошибками: {self.results['failure_count']} ❌")
        print(f"Success rate: {(self.results['success_count'] / self.results['total'] * 100):.1f}%")
        
        if self.results['failure']:
            print("\n❌ МОДУЛИ С ОШИБКАМИ:")
            for module, error in self.results['failure']:
                print(f"  • {module}")
                print(f"    {error}")
        
        if self.results['success_count'] == self.results['total']:
            print("\n🎉 ВСЕ МОДУЛИ УСПЕШНО ИМПОРТИРОВАНЫ!")
            print("✅ Проект готов к запуску")
        else:
            print(f"\n⚠️  {self.results['failure_count']} модулей имеют проблемы с импортом")
            print("🔧 Требуется исправление перед запуском")

def main():
    """Основная функция"""
    verifier = ImportVerifier()
    verifier.run_full_verification()
    
    # Возвращаем код выхода для CI/CD
    if verifier.results['failure_count'] == 0:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
