#!/usr/bin/env python3
"""
Runtime Boundary Enforcement - Запрет forbidden imports
EXIT CODE != 0 при обнаружении forbidden import
"""

import sys
import importlib
from pathlib import Path

# Forbidden import patterns
FORBIDDEN_IMPORTS = [
    'legacy/',
    'adaptive/',
    'darknet/',
    'ai/',
    'generator/',
    'legacy.',
    'adaptive.',
    'darknet.',
    'ai.',
    'generator.'
]

class BoundaryViolationError(Exception):
    """Ошибка нарушения boundary"""
    pass

def check_runtime_boundary():
    """Проверить runtime boundary violations"""
    project_root = Path(__file__).parent.parent
    super_dpi_root = project_root / "super_dpi_combiner"
    
    violations = []
    
    # Проверяем runtime файлы
    runtime_files = [
        "core/__init__.py",
        "core/contracts.py",
        "core/runner.py",
        "core/http_client.py",
        "core/logging.py",
        "core/shutdown.py",
        "core/packet_capture.py",
        "core/runtime_config.py",
        "core/metrics.py",
        "core/runtime_state.py",
        "pipelines/__init__.py",
        "pipelines/http_fragmentation.py",
        "pipelines/echo.py",
        "main.py"
    ]
    
    for file_path in runtime_files:
        full_path = super_dpi_root / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем forbidden imports
                for forbidden in FORBIDDEN_IMPORTS:
                    if forbidden in content:
                        violations.append({
                            'file': str(file_path),
                            'forbidden_import': forbidden,
                            'line_number': _find_line_number(content, forbidden)
                        })
                        
            except Exception as e:
                violations.append({
                    'file': str(file_path),
                    'error': str(e)
                })
    
    return violations

def _find_line_number(content: str, pattern: str) -> int:
    """Найти номер строки для pattern"""
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if pattern in line:
            return i
    return 0

def enforce_runtime_boundary():
    """Принудительно проверить boundary и выйти при violations"""
    violations = check_runtime_boundary()
    
    if violations:
        print("❌ RUNTIME BOUNDARY VIOLATIONS DETECTED")
        print("=" * 60)
        
        for violation in violations:
            if 'forbidden_import' in violation:
                print(f"FILE: {violation['file']}")
                print(f"LINE: {violation['line_number']}")
                print(f"VIOLATION: Forbidden import '{violation['forbidden_import']}'")
                print("-" * 40)
            else:
                print(f"FILE: {violation['file']}")
                print(f"ERROR: {violation['error']}")
                print("-" * 40)
        
        print(f"\nTOTAL VIOLATIONS: {len(violations)}")
        print("RUNTIME BOUNDARY ENFORCEMENT: FAILED")
        sys.exit(1)
    
    print("✅ RUNTIME BOUNDARY ENFORCEMENT: PASSED")
    print("No forbidden imports detected in runtime")
    sys.exit(0)

def main():
    """Основная функция"""
    enforce_runtime_boundary()

if __name__ == "__main__":
    main()
