#!/usr/bin/env python3
"""
Runtime State Machine - Убрать implicit state
Детерминированные переходы, fail-fast при inconsistent state
"""

import time
import threading
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable

class RuntimeState(Enum):
    """Состояния runtime"""
    INIT = "init"
    READY = "ready"
    RUNNING = "ready"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"

class StateTransitionError(Exception):
    """Ошибка недопустимого перехода состояния"""
    pass

@dataclass
class StateTransition:
    """Переход состояния"""
    from_state: RuntimeState
    to_state: RuntimeState
    timestamp: float
    reason: Optional[str] = None

class RuntimeStateMachine:
    """State Machine для runtime"""
    
    def __init__(self):
        self.current_state = RuntimeState.INIT
        self.state_history: list[StateTransition] = []
        self.lock = threading.Lock()
        self.state_handlers: Dict[RuntimeState, Callable] = {
            RuntimeState.INIT: self._handle_init,
            RuntimeState.READY: self._handle_ready,
            RuntimeState.RUNNING: self._handle_running,
            RuntimeState.STOPPING: self._handle_stopping,
            RuntimeState.STOPPED: self._handle_stopped,
            RuntimeState.FAILED: self._handle_failed
        }
        
    def transition_to(self, new_state: RuntimeState, reason: Optional[str] = None):
        """Выполнить переход состояния"""
        with self.lock:
            if not self._is_valid_transition(self.current_state, new_state):
                raise StateTransitionError(
                    f"Invalid state transition: {self.current_state.value} -> {new_state.value}"
                )
            
            old_state = self.current_state
            self.current_state = new_state
            
            transition = StateTransition(
                from_state=old_state,
                to_state=new_state,
                timestamp=time.time(),
                reason=reason
            )
            
            self.state_history.append(transition)
            
            # Вызываем handler для нового состояния
            handler = self.state_handlers.get(new_state)
            if handler:
                handler(old_state, new_state, reason)
    
    def _is_valid_transition(self, from_state: RuntimeState, to_state: RuntimeState) -> bool:
        """Проверить валидность перехода"""
        # Определяем допустимые переходы
        valid_transitions = {
            RuntimeState.INIT: [RuntimeState.READY, RuntimeState.FAILED],
            RuntimeState.READY: [RuntimeState.RUNNING, RuntimeState.FAILED],
            RuntimeState.RUNNING: [RuntimeState.READY, RuntimeState.STOPPING, RuntimeState.FAILED],
            RuntimeState.STOPPING: [RuntimeState.STOPPED, RuntimeState.FAILED],
            RuntimeState.STOPPED: [RuntimeState.READY, RuntimeState.FAILED],
            RuntimeState.FAILED: [RuntimeState.INIT, RuntimeState.READY]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def _handle_init(self, old_state: RuntimeState, new_state: RuntimeState, reason: Optional[str]):
        """Обработчик состояния INIT"""
        print(f"[STATE] INIT -> {new_state.value}: {reason or 'No reason'}")
        
        if new_state == RuntimeState.READY:
            print("[STATE] Runtime initialized and ready")
        elif new_state == RuntimeState.FAILED:
            print(f"[STATE] Runtime initialization failed: {reason}")
    
    def _handle_ready(self, old_state: RuntimeState, new_state: RuntimeState, reason: Optional[str]):
        """Обработчик состояния READY"""
        print(f"[STATE] READY -> {new_state.value}: {reason or 'No reason'}")
        
        if new_state == RuntimeState.RUNNING:
            print("[STATE] Runtime started processing")
        elif new_state == RuntimeState.FAILED:
            print(f"[STATE] Runtime failed in ready state: {reason}")
    
    def _handle_running(self, old_state: RuntimeState, new_state: RuntimeState, reason: Optional[str]):
        """Обработчик состояния RUNNING"""
        print(f"[STATE] RUNNING -> {new_state.value}: {reason or 'No reason'}")
        
        if new_state == RuntimeState.READY:
            print("[STATE] Runtime finished processing and ready again")
        elif new_state == RuntimeState.STOPPING:
            print("[STATE] Runtime stopping...")
        elif new_state == RuntimeState.FAILED:
            print(f"[STATE] Runtime failed while running: {reason}")
    
    def _handle_stopping(self, old_state: RuntimeState, new_state: RuntimeState, reason: Optional[str]):
        """Обработчик состояния STOPPING"""
        print(f"[STATE] STOPPING -> {new_state.value}: {reason or 'No reason'}")
        
        if new_state == RuntimeState.STOPPED:
            print("[STATE] Runtime stopped successfully")
        elif new_state == RuntimeState.FAILED:
            print(f"[STATE] Runtime failed during shutdown: {reason}")
    
    def _handle_stopped(self, old_state: RuntimeState, new_state: RuntimeState, reason: Optional[str]):
        """Обработчик состояния STOPPED"""
        print(f"[STATE] STOPPED -> {new_state.value}: {reason or 'No reason'}")
        
        if new_state == RuntimeState.READY:
            print("[STATE] Runtime ready to start again")
        elif new_state == RuntimeState.FAILED:
            print(f"[STATE] Runtime failed in stopped state: {reason}")
    
    def _handle_failed(self, old_state: RuntimeState, new_state: RuntimeState, reason: Optional[str]):
        """Обработчик состояния FAILED"""
        print(f"[STATE] FAILED -> {new_state.value}: {reason or 'No reason'}")
        
        if new_state == RuntimeState.INIT:
            print("[STATE] Runtime reinitializing after failure")
        elif new_state == RuntimeState.READY:
            print("[STATE] Runtime recovered and ready")
    
    def get_current_state(self) -> RuntimeState:
        """Получить текущее состояние"""
        with self.lock:
            return self.current_state
    
    def get_state_history(self) -> list[StateTransition]:
        """Получить историю переходов"""
        with self.lock:
            return self.state_history.copy()
    
    def is_ready_for_operation(self) -> bool:
        """Проверить готовность для операций"""
        return self.current_state in [RuntimeState.READY, RuntimeState.RUNNING]
    
    def is_failed(self) -> bool:
        """Проверить что runtime в состоянии ошибки"""
        return self.current_state == RuntimeState.FAILED
    
    def force_fail(self, reason: str):
        """Принудительно перевести в состояние ошибки"""
        print(f"[STATE] Force failing runtime: {reason}")
        self.transition_to(RuntimeState.FAILED, reason)

# Global state machine instance
_global_state_machine: Optional[RuntimeStateMachine] = None

def get_state_machine() -> RuntimeStateMachine:
    """Получить глобальный state machine"""
    global _global_state_machine
    if _global_state_machine is None:
        _global_state_machine = RuntimeStateMachine()
    return _global_state_machine

def initialize_runtime():
    """Инициализировать runtime"""
    state_machine = get_state_machine()
    state_machine.transition_to(RuntimeState.READY, "Runtime initialized")

def shutdown_runtime():
    """Корректно завершить runtime"""
    state_machine = get_state_machine()
    if state_machine.is_ready_for_operation():
        state_machine.transition_to(RuntimeState.STOPPING, "Shutdown requested")
        state_machine.transition_to(RuntimeState.STOPPED, "Shutdown completed")
    else:
        state_machine.force_fail("Cannot shutdown from failed state")
