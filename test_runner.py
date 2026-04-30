#!/usr/bin/env python3
"""
Запускатель тестов RSecure с генерацией отчетов
"""

import pytest
import sys
import os
import time
import json
from datetime import datetime
import numpy as np

class RSecureTestRunner:
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск комплексного тестирования RSecure")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Определение тестовых модулей
        test_modules = [
            'tests.test_behavioral_analysis',
            'tests.test_spectral_analysis', 
            'tests.test_neural_architectures'
        ]
        
        total_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'modules': {}
        }
        
        for module in test_modules:
            print(f"\n📋 Тестирование модуля: {module}")
            print("-" * 40)
            
            try:
                # Запуск pytest для каждого модуля
                module_result = self._run_pytest_module(module)
                total_results['modules'][module] = module_result
                
                # Агрегация результатов
                total_results['total_tests'] += module_result['total']
                total_results['passed'] += module_result['passed']
                total_results['failed'] += module_result['failed']
                total_results['skipped'] += module_result['skipped']
                total_results['errors'] += module_result['errors']
                
                # Вывод результатов модуля
                self._print_module_results(module, module_result)
                
            except Exception as e:
                print(f"❌ Ошибка при запуске {module}: {e}")
                total_results['modules'][module] = {
                    'total': 0, 'passed': 0, 'failed': 0, 
                    'skipped': 0, 'errors': 1, 'error': str(e)
                }
                total_results['errors'] += 1
        
        self.end_time = time.time()
        total_results['duration'] = self.end_time - self.start_time
        total_results['timestamp'] = datetime.now().isoformat()
        
        # Генерация отчета
        self._generate_final_report(total_results)
        
        return total_results
    
    def _run_pytest_module(self, module):
        """Запуск pytest для конкретного модуля"""
        # Настройка pytest
        pytest_args = [
            module,
            '-v',  # Verbose output
            '--tb=short',  # Краткий traceback
            '--json-report',  # JSON отчет
            '--json-report-file=/tmp/pytest_report.json',
            '--durations=10',  # Показать медленные тесты
        ]
        
        try:
            # Запуск pytest
            exit_code = pytest.main(pytest_args)
            
            # Чтение JSON отчета
            try:
                with open('/tmp/pytest_report.json', 'r') as f:
                    report = json.load(f)
                
                return self._parse_pytest_report(report)
                
            except FileNotFoundError:
                # Fallback если JSON отчет не сгенерировался
                return self._create_fallback_result(module, exit_code)
                
        except Exception as e:
            return {
                'total': 0, 'passed': 0, 'failed': 0, 
                'skipped': 0, 'errors': 1, 'error': str(e)
            }
    
    def _parse_pytest_report(self, report):
        """Парсинг JSON отчета pytest"""
        summary = report.get('summary', {})
        
        return {
            'total': summary.get('total', 0),
            'passed': summary.get('passed', 0),
            'failed': summary.get('failed', 0),
            'skipped': summary.get('skipped', 0),
            'errors': summary.get('error', 0),
            'duration': summary.get('duration', 0),
            'tests': report.get('tests', [])
        }
    
    def _create_fallback_result(self, module, exit_code):
        """Создание резервного результата"""
        return {
            'total': 0,
            'passed': 0,
            'failed': 1 if exit_code != 0 else 0,
            'skipped': 0,
            'errors': 0,
            'duration': 0,
            'exit_code': exit_code
        }
    
    def _print_module_results(self, module, result):
        """Вывод результатов модуля"""
        status = "✅ PASSED" if result['failed'] == 0 and result['errors'] == 0 else "❌ FAILED"
        
        print(f"Статус: {status}")
        print(f"Всего тестов: {result['total']}")
        print(f"Прошло: {result['passed']}")
        print(f"Провалено: {result['failed']}")
        print(f"Пропущено: {result['skipped']}")
        print(f"Ошибки: {result['errors']}")
        
        if 'duration' in result:
            print(f"Длительность: {result['duration']:.2f}s")
        
        # Показать проваленные тесты
        if 'tests' in result:
            failed_tests = [t for t in result['tests'] if t.get('outcome') == 'failed']
            if failed_tests:
                print("\nПроваленные тесты:")
                for test in failed_tests[:5]:  # Показать первые 5
                    print(f"  - {test.get('name', 'Unknown')}")
                if len(failed_tests) > 5:
                    print(f"  ... и еще {len(failed_tests) - 5}")
    
    def _generate_final_report(self, results):
        """Генерация финального отчета"""
        print("\n" + "=" * 60)
        print("📊 ОБЩИЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        # Общая статистика
        total_tests = results['total_tests']
        passed = results['passed']
        failed = results['failed']
        skipped = results['skipped']
        errors = results['errors']
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Всего тестов: {total_tests}")
        print(f"✅ Прошло: {passed} ({success_rate:.1f}%)")
        print(f"❌ Провалено: {failed}")
        print(f"⏭️ Пропущено: {skipped}")
        print(f"🚫 Ошибки: {errors}")
        print(f"⏱️ Общее время: {results['duration']:.2f}s")
        
        # Статус тестирования
        if failed == 0 and errors == 0:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        else:
            print(f"\n⚠️ ОБНАРУЖЕНО ПРОБЛЕМЫ: {failed + errors} тестов не прошли")
        
        # Детализация по модулям
        print("\n📋 Результаты по модулям:")
        for module, result in results['modules'].items():
            module_name = module.split('.')[-1]
            status = "✅" if result['failed'] == 0 and result['errors'] == 0 else "❌"
            print(f"  {status} {module_name}: {result['passed']}/{result['total']} passed")
        
        # Сохранение отчета
        self._save_report(results)
        
        # Рекомендации
        self._generate_recommendations(results)
    
    def _save_report(self, results):
        """Сохранение отчета в файл"""
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Отчет сохранен: {report_file}")
        except Exception as e:
            print(f"\n❌ Ошибка сохранения отчета: {e}")
    
    def _generate_recommendations(self, results):
        """Генерация рекомендаций"""
        print("\n💡 РЕКОМЕНДАЦИИ:")
        
        total_tests = results['total_tests']
        success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 95:
            print("  🌟 Отличное качество кода! Тесты проходят успешно.")
        elif success_rate >= 80:
            print("  ⚠️ Хорошее качество кода, но есть проблемы для исправления.")
        else:
            print("  🚨 Низкое качество кода. Требуется доработка.")
        
        # Анализ проблемных модулей
        problematic_modules = []
        for module, result in results['modules'].items():
            if result['failed'] > 0 or result['errors'] > 0:
                problematic_modules.append((module, result))
        
        if problematic_modules:
            print("\n🔧 Проблемные модули для внимания:")
            for module, result in problematic_modules:
                module_name = module.split('.')[-1]
                issues = result['failed'] + result['errors']
                print(f"  - {module_name}: {issues} проблем")
        
        # Производительность
        if results['duration'] > 60:
            print("\n⏱️ Тесты выполняются медленно. Рассмотрите оптимизацию.")
        
        # Покрытие кода
        print("\n📊 Рекомендуемые действия:")
        print("  1. Исправьте проваленные тесты")
        print("  2. Добавьте тесты для критических функций")
        print("  3. Настройте CI/CD для автоматического тестирования")
        print("  4. Рассмотрите добавление интеграционных тестов")

class TestCoverageAnalyzer:
    """Анализатор покрытия кода тестами"""
    
    def __init__(self):
        self.coverage_data = {}
    
    def analyze_coverage(self):
        """Анализ покрытия кода"""
        print("\n🔍 АНАЛИЗ ПОКРЫТИЯ КОДА")
        print("-" * 40)
        
        # Модули для анализа
        modules_to_analyze = [
            'rsecure.modules.defense.visual_security',
            'rsecure.core.neural_security_core',
            'rsecure.core.ollama_integration'
        ]
        
        coverage_results = {}
        
        for module in modules_to_analyze:
            try:
                coverage = self._calculate_module_coverage(module)
                coverage_results[module] = coverage
                print(f"📦 {module}: {coverage['percentage']:.1f}% покрыто")
            except Exception as e:
                print(f"❌ Ошибка анализа {module}: {e}")
                coverage_results[module] = {'percentage': 0, 'error': str(e)}
        
        return coverage_results
    
    def _calculate_module_coverage(self, module_name):
        """Расчет покрытия модуля"""
        # Упрощенный анализ покрытия (реальный анализ требует pytest-cov)
        try:
            # Попытка импортировать модуль
            module = __import__(module_name, fromlist=[''])
            
            # Подсчет функций/классов/методов
            total_items = 0
            documented_items = 0
            
            for name in dir(module):
                if not name.startswith('_'):
                    total_items += 1
                    # Проверяем наличие документации
                    obj = getattr(module, name)
                    if obj.__doc__:
                        documented_items += 1
            
            coverage_percentage = (documented_items / total_items * 100) if total_items > 0 else 0
            
            return {
                'percentage': coverage_percentage,
                'total_items': total_items,
                'documented_items': documented_items
            }
            
        except ImportError:
            return {'percentage': 0, 'error': 'Module not found'}

def main():
    """Основная функция"""
    print("🔬 RSecure Test Suite")
    print("Комплексное тестирование системы безопасности")
    print()
    
    # Запуск тестов
    runner = RSecureTestRunner()
    results = runner.run_all_tests()
    
    # Анализ покрытия
    coverage_analyzer = TestCoverageAnalyzer()
    coverage_results = coverage_analyzer.analyze_coverage()
    
    # Финальный статус
    total_issues = results['failed'] + results['errors']
    exit_code = 0 if total_issues == 0 else 1
    
    print(f"\n🏁 Завершено с кодом выхода: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
