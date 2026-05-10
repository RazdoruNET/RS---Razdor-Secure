#!/usr/bin/env python3
"""
Runtime Isolation Audit - Доказательство изоляции runtime от legacy кода
Проверяем что runtime НЕ импортирует legacy, darknet, AI, adaptive
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RuntimeIsolationAuditor:
    """Auditor для проверки изоляции runtime"""
    
    def __init__(self):
        self.forbidden_imports = [
            'legacy',
            'darknet', 
            'tor',
            'dns',
            'adaptive',
            'ai',
            'llm',
            'generators',
            'old_registry'
        ]
        self.runtime_modules = []
        self.import_violations = []
        
    def scan_runtime_imports(self):
        """Сканировать импорты runtime модулей"""
        print("\n🔍 Scanning Runtime Imports")
        print("=" * 50)
        
        # Список runtime модулей для проверки
        runtime_files = [
            'super_dpi_combiner/core/__init__.py',
            'super_dpi_combiner/core/contracts.py',
            'super_dpi_combiner/core/runner.py',
            'super_dpi_combiner/core/http_client.py',
            'super_dpi_combiner/core/logging.py',
            'super_dpi_combiner/core/shutdown.py',
            'super_dpi_combiner/pipelines/__init__.py',
            'super_dpi_combiner/pipelines/http_fragmentation.py',
            'super_dpi_combiner/pipelines/echo.py',
            'super_dpi_combiner/main.py'
        ]
        
        for file_path in runtime_files:
            try:
                full_path = project_root / file_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Проверяем запрещённые импорты
                    found_violations = []
                    for forbidden in self.forbidden_imports:
                        if forbidden in content.lower():
                            # Проверяем что это действительно import
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if forbidden in line.lower() and ('import' in line or 'from' in line):
                                    found_violations.append(f"Line {i}: {line.strip()}")
                    
                    if found_violations:
                        print(f"❌ {file_path}: Forbidden imports found")
                        for violation in found_violations:
                            print(f"  {violation}")
                        self.import_violations.append({
                            'file': file_path,
                            'violations': found_violations
                        })
                    else:
                        print(f"✅ {file_path}: No forbidden imports")
                        
                    self.runtime_modules.append(file_path)
                        
            except Exception as e:
                print(f"⚠️ Error scanning {file_path}: {e}")
    
    def check_sys_modules(self):
        """Проверить sys.modules на наличие legacy"""
        print("\n🖥️ Checking sys.modules")
        print("=" * 50)
        
        legacy_modules = []
        for module_name in sys.modules:
            if any(forbidden in module_name.lower() for forbidden in self.forbidden_imports):
                legacy_modules.append(module_name)
                print(f"❌ Legacy module in sys.modules: {module_name}")
        
        if not legacy_modules:
            print("✅ No legacy modules found in sys.modules")
            
        return legacy_modules
    
    def test_runtime_imports(self):
        """Тестировать импорты runtime"""
        print("\n🧪 Testing Runtime Import Behavior")
        print("=" * 50)
        
        try:
            # Пробуем импортировать все runtime компоненты
            print("📤 Importing core components...")
            from super_dpi_combiner.core import contracts, runner, http_client, logging, shutdown
            print("✅ Core components imported successfully")
            
            print("📤 Importing pipelines...")
            from super_dpi_combiner.pipelines import HTTPFragmentation, Echo
            print("✅ Pipelines imported successfully")
            
            print("📤 Importing main...")
            from super_dpi_combiner import main
            print("✅ Main imported successfully")
            
            # Проверяем что legacy модули не импортируются автоматически
            print("📤 Testing legacy import attempts...")
            
            try:
                from super_dpi_combiner.legacy import darknet
                print("❌ Legacy darknet module imported - VIOLATION")
                self.import_violations.append({
                    'test': 'LEGACY_AUTO_IMPORT',
                    'module': 'darknet',
                    'status': 'VIOLATION'
                })
            except ImportError:
                print("✅ Legacy darknet module not importable - GOOD")
            except Exception as e:
                print(f"⚠️ Unexpected error importing legacy: {e}")
            
            try:
                from super_dpi_combiner.legacy import ai
                print("❌ Legacy AI module imported - VIOLATION")
                self.import_violations.append({
                    'test': 'LEGACY_AUTO_IMPORT',
                    'module': 'ai',
                    'status': 'VIOLATION'
                })
            except ImportError:
                print("✅ Legacy AI module not importable - GOOD")
            except Exception as e:
                print(f"⚠️ Unexpected error importing legacy AI: {e}")
                
        except Exception as e:
            print(f"❌ Runtime import test failed: {e}")
            self.import_violations.append({
                'test': 'RUNTIME_IMPORT_TEST',
                'error': str(e),
                'status': 'ERROR'
            })
    
    def analyze_isolation(self):
        """Анализировать изоляцию"""
        print("\n📈 Runtime Isolation Analysis")
        print("=" * 50)
        
        total_files = len(self.runtime_modules)
        violation_files = len(self.import_violations)
        clean_files = total_files - violation_files
        
        print(f"📊 Isolation Statistics:")
        print(f"  Total runtime files: {total_files}")
        print(f"  Files with violations: {violation_files}")
        print(f"  Clean files: {clean_files}")
        print(f"  Isolation rate: {(clean_files/total_files)*100:.1f}%" if total_files > 0 else "N/A")
        
        if self.import_violations:
            print(f"\n❌ Import Violations Found:")
            for violation in self.import_violations:
                if 'file' in violation:
                    print(f"  File: {violation['file']}")
                    for v in violation['violations']:
                        print(f"    {v}")
                else:
                    print(f"  Test: {violation['test']} - {violation.get('module', '')} - {violation['status']}")
        else:
            print("\n✅ No import violations found - Runtime is isolated")
        
        return {
            'total_files': total_files,
            'violation_files': violation_files,
            'clean_files': clean_files,
            'isolation_rate': (clean_files/total_files)*100 if total_files > 0 else 0,
            'violations': self.import_violations
        }
    
    def run_full_audit(self):
        """Полный аудит изоляции"""
        print("🚀 Runtime Isolation Audit v2")
        print("Цель: Доказать изоляцию runtime от legacy кода")
        print("Метод: Static import analysis + runtime testing")
        
        # Сканируем импорты
        self.scan_runtime_imports()
        
        # Проверяем sys.modules
        self.check_sys_modules()
        
        # Тестируем поведение импортов
        self.test_runtime_imports()
        
        # Анализируем изоляцию
        analysis = self.analyze_isolation()
        
        return analysis

def write_isolation_report(auditor):
    """Записать отчёт об изоляции"""
    analysis = auditor.analyze_isolation()
    
    report = f"""# RUNTIME_ISOLATION_AUDIT.md

## Runtime Isolation Audit Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Forbidden Imports Check

### Runtime Files Scanned
- Total files: {analysis['total_files']}
- Files with violations: {analysis['violation_files']}
- Clean files: {analysis['clean_files']}
- Isolation rate: {analysis['isolation_rate']:.1f}%

### Import Violations
{chr(10).join(f"- {v['file']}: {len(v.get('violations', []))} violations" for v in analysis['violations'] if 'file' in v)}

## Verification Results

### Runtime Isolation Status
- Legacy imports in runtime: {'VERIFIED' if analysis['violation_files'] == 0 else 'NOT VERIFIED'}
- Darknet modules isolated: {'VERIFIED' if not any('darknet' in str(v) for v in analysis['violations']) else 'NOT VERIFIED'}
- AI modules isolated: {'VERIFIED' if not any('ai' in str(v) for v in analysis['violations']) else 'NOT VERIFIED'}

### Forbidden Modules Status
- legacy: {'ISOLATED' if not any('legacy' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}
- darknet: {'ISOLATED' if not any('darknet' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}
- tor: {'ISOLATED' if not any('tor' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}
- dns: {'ISOLATED' if not any('dns' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}
- adaptive: {'ISOLATED' if not any('adaptive' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}
- ai: {'ISOLATED' if not any('ai' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}
- llm: {'ISOLATED' if not any('llm' in str(v) for v in analysis['violations']) else 'NOT ISOLATED'}

## Component Status
- Core: {'ISOLATED' if analysis['isolation_rate'] == 100 else 'NOT ISOLATED'}
- Pipelines: {'ISOLATED' if analysis['isolation_rate'] == 100 else 'NOT ISOLATED'}
- Main: {'ISOLATED' if analysis['isolation_rate'] == 100 else 'NOT ISOLATED'}

## Final Classification

### Runtime Isolation Integrity
- Complete isolation: {'VERIFIED' if analysis['isolation_rate'] == 100 else 'NOT VERIFIED'}
- No legacy dependencies: {'VERIFIED' if analysis['violation_files'] == 0 else 'NOT VERIFIED'}
- Clean import graph: {'VERIFIED' if analysis['isolation_rate'] == 100 else 'NOT VERIFIED'}

### Runtime Status
RUNTIME_ISOLATION: {'VERIFIED' if analysis['isolation_rate'] == 100 else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/RUNTIME_ISOLATION_AUDIT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 Runtime isolation audit report written to: RUNTIME_ISOLATION_AUDIT.md")

def main():
    """Основная функция аудита"""
    auditor = RuntimeIsolationAuditor()
    analysis = auditor.run_full_audit()
    write_isolation_report(auditor)
    print("\n✅ Runtime Isolation Audit завершён")

if __name__ == "__main__":
    main()
