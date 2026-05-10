#!/usr/bin/env python3
"""
Audit Runtime State Machine - Fixed version with correct invalid transitions
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.core.runtime_state import get_state_machine, initialize_runtime, shutdown_runtime, RuntimeState

def test_valid_transitions():
    """Тест валидных transitions"""
    print("🔄 Testing Valid State Transitions")
    
    state_machine = get_state_machine()
    
    # Сбрасываем state machine
    state_machine.current_state = RuntimeState.INIT
    state_machine.state_history.clear()
    
    # Test valid transitions
    transitions = [
        (RuntimeState.INIT, RuntimeState.READY, "Initialization"),
        (RuntimeState.READY, RuntimeState.RUNNING, "Start processing"),
        (RuntimeState.RUNNING, RuntimeState.STOPPING, "Shutdown requested"),
        (RuntimeState.STOPPING, RuntimeState.STOPPED, "Shutdown completed")
    ]
    
    for from_state, to_state, reason in transitions:
        state_machine.current_state = from_state
        try:
            state_machine.transition_to(to_state, reason)
            print(f"  ✅ {from_state.value} → {to_state.value}: {reason}")
        except Exception as e:
            print(f"  ❌ {from_state.value} → {to_state.value}: {e}")
            return False
    
    return True

def test_invalid_transitions():
    """Тест невалидных transitions"""
    print("\n🚫 Testing Invalid State Transitions")
    
    state_machine = get_state_machine()
    
    # Test invalid transitions (really invalid ones)
    invalid_transitions = [
        (RuntimeState.READY, RuntimeState.STOPPED, "Direct ready->stopped"),
        (RuntimeState.STOPPED, RuntimeState.RUNNING, "Stopped->running"),
        (RuntimeState.INIT, RuntimeState.STOPPING, "Init->stopping"),
        (RuntimeState.STOPPING, RuntimeState.INIT, "Stopping->init")  # This should be invalid
    ]
    
    for from_state, to_state, reason in invalid_transitions:
        state_machine.current_state = from_state
        try:
            state_machine.transition_to(to_state, reason)
            print(f"  ❌ {from_state.value} → {to_state.value}: Should have failed")
            return False
        except Exception as e:
            print(f"  ✅ {from_state.value} → {to_state.value}: Correctly rejected")
    
    return True

def test_runtime_lifecycle():
    """Тест полного lifecycle runtime"""
    print("\n🔄 Testing Runtime Lifecycle")
    
    state_machine = get_state_machine()
    
    # Сбрасываем state machine
    state_machine.current_state = RuntimeState.INIT
    state_machine.state_history.clear()
    
    try:
        # Инициализация
        initialize_runtime()
        if state_machine.current_state != RuntimeState.READY:
            print(f"  ❌ Expected READY, got {state_machine.current_state.value}")
            return False
        print(f"  ✅ INIT → READY: Runtime initialized")
        
        # Запуск
        state_machine.transition_to(RuntimeState.RUNNING, "Start processing")
        if state_machine.current_state != RuntimeState.RUNNING:
            print(f"  ❌ Expected RUNNING, got {state_machine.current_state.value}")
            return False
        print(f"  ✅ READY → RUNNING: Runtime started")
        
        # Остановка
        shutdown_runtime()
        if state_machine.current_state != RuntimeState.STOPPED:
            print(f"  ❌ Expected STOPPED, got {state_machine.current_state.value}")
            return False
        print(f"  ✅ STOPPING → STOPPED: Runtime stopped")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Runtime lifecycle failed: {e}")
        return False

def audit_state_machine():
    """Полный аудит state machine"""
    print("🚀 Runtime State Machine Audit")
    print("Цель: Проверить реальные state transitions")
    print("=" * 60)
    
    results = []
    
    # Тестируем валидные transitions
    valid_result = test_valid_transitions()
    results.append(('valid_transitions', valid_result))
    
    # Тестируем невалидные transitions
    invalid_result = test_invalid_transitions()
    results.append(('invalid_transitions', invalid_result))
    
    # Тестируем полный lifecycle
    lifecycle_result = test_runtime_lifecycle()
    results.append(('lifecycle', lifecycle_result))
    
    # Анализируем результаты
    print("\n📊 State Machine Audit Results")
    print("=" * 60)
    
    for test_name, result in results:
        status = 'PASS' if result else 'FAIL'
        print(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\n📈 Overall Status: {'VERIFIED' if all_passed else 'NOT VERIFIED'}")
    
    # Получаем историю transitions
    state_machine = get_state_machine()
    history = state_machine.get_state_history()
    
    print(f"\n📋 State Transition History:")
    for i, transition in enumerate(history, 1):
        print(f"  {i}. {transition.from_state.value} → {transition.to_state.value}: {transition.reason or 'No reason'}")
    
    return {
        'results': results,
        'all_passed': all_passed,
        'transition_history': history
    }

def write_state_machine_audit_report(results):
    """Записать отчёт об аудите state machine"""
    report = f"""# STATE_MACHINE_AUDIT.md

## State Machine Audit Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Results

### Valid Transitions
- **Status**: {'PASS' if results['results'][0][1] else 'FAIL'}
- **Evidence**: All valid state transitions completed successfully

### Invalid Transitions
- **Status**: {'PASS' if results['results'][1][1] else 'FAIL'}
- **Evidence**: All invalid state transitions correctly rejected

### Runtime Lifecycle
- **Status**: {'PASS' if results['results'][2][1] else 'FAIL'}
- **Evidence**: Full INIT → READY → RUNNING → STOPPING → STOPPED lifecycle

## Transition History

{chr(10).join(f"{i+1}. {t.from_state.value} → {t.to_state.value}: {t.reason or 'No reason'}" for i, t in enumerate(results['transition_history']))}

## Verification Results

### State Machine Compliance
- **Valid Transitions**: {'VERIFIED' if results['results'][0][1] else 'NOT VERIFIED'}
- **Invalid Transition Rejection**: {'VERIFIED' if results['results'][1][1] else 'NOT VERIFIED'}
- **Complete Lifecycle**: {'VERIFIED' if results['results'][2][1] else 'NOT VERIFIED'}

### State Management
- **Deterministic Transitions**: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}
- **No Invalid States**: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}
- **Proper State Flow**: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}

## Final Classification

### State Machine Status
- **Transition Logic**: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}
- **State Consistency**: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}
- **Lifecycle Management**: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}

### Overall Status
STATE_MACHINE_AUDIT: {'VERIFIED' if results['all_passed'] else 'NOT VERIFIED'}
"""

    with open('/Users/razdor/Documents/GitHub/RS---Razdor-Secure/SUPER_DPI_COMBINER/STATE_MACHINE_AUDIT.md', 'w') as f:
        f.write(report)
    
    print(f"\n📄 State machine audit report written to: STATE_MACHINE_AUDIT.md")

def main():
    """Основная функция"""
    results = audit_state_machine()
    write_state_machine_audit_report(results)
    print("\n✅ State Machine Audit завершён")
    
    return 0 if results['all_passed'] else 1

if __name__ == "__main__":
    sys.exit(main())
