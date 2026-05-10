#!/usr/bin/env python3
"""
Instrumentation Layer - перехват реальных I/O операций
Мониторинг и логирование фактических сетевых операций
"""

import socket
import asyncio
import time
import sys
import os
import logging
import functools
import inspect
from typing import Dict, Any, Optional, Tuple, Callable, Union, List
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque

# Add parent directory to path for logger import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import get_tracer

class IOOperationType(Enum):
    """Типы I/O операций"""
    SOCKET_SEND = "socket_send"
    SOCKET_RECV = "socket_recv"
    ASYNCIO_WRITE = "asyncio_write"
    ASYNCIO_READ = "asyncio_read"
    HTTP_REQUEST = "http_request"
    HTTP_RESPONSE = "http_response"
    SYSTEM_CALL = "system_call"

@dataclass
class IOOperationRecord:
    """Запись I/O операции"""
    operation_type: IOOperationType
    timestamp: float
    thread_id: int
    data_size: int
    data_bytes: bytes
    source_location: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemCallRecord:
    """Запись системного вызова"""
    syscall_name: str
    timestamp: float
    thread_id: int
    args: tuple
    kwargs: dict
    return_value: Any
    success: bool
    error: Optional[str] = None

class IOMonitor:
    """Монитор I/O операций"""
    
    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self.records: deque = deque(maxlen=max_records)
        self.syscall_records: deque = deque(maxlen=max_records)
        self.lock = threading.Lock()
        self.logger = logging.getLogger("instrumentation")
        self.tracer = get_tracer("instrumentation")
        
        # Статистика по операциям
        self.operation_stats = defaultdict(int)
        self.byte_stats = defaultdict(int)
        self.error_stats = defaultdict(int)
        
        # Флаг для предотвращения логических успехов без I/O
        self.io_operations_in_session = False
        self.session_start_time = time.time()
        
    def record_operation(self, 
                        operation_type: IOOperationType,
                        data: bytes,
                        success: bool = True,
                        error: Optional[str] = None,
                        metadata: Dict[str, Any] = None) -> str:
        """Записать I/O операцию"""
        
        # Получаем информацию о вызове
        frame = inspect.currentframe().f_back
        source_location = f"{frame.f_code.co_filename}:{frame.f_lineno}" if frame else "unknown"
        
        record = IOOperationRecord(
            operation_type=operation_type,
            timestamp=time.time(),
            thread_id=threading.get_ident(),
            data_size=len(data),
            data_bytes=data,
            source_location=source_location,
            success=success,
            error=error,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.records.append(record)
            self.operation_stats[operation_type.value] += 1
            self.byte_stats[operation_type.value] += len(data)
            
            if not success:
                self.error_stats[operation_type.value] += 1
            
            # Отмечаем что были реальные I/O операции
            self.io_operations_in_session = True
        
        # Логирование
        self._log_operation(record)
        
        return f"op_{int(record.timestamp * 1000000)}"
    
    def record_syscall(self,
                      syscall_name: str,
                      args: tuple,
                      kwargs: dict,
                      return_value: Any,
                      success: bool = True,
                      error: Optional[str] = None) -> str:
        """Записать системный вызов"""
        
        frame = inspect.currentframe().f_back
        source_location = f"{frame.f_code.co_filename}:{frame.f_lineno}" if frame else "unknown"
        
        record = SystemCallRecord(
            syscall_name=syscall_name,
            timestamp=time.time(),
            thread_id=threading.get_ident(),
            args=args,
            kwargs=kwargs,
            return_value=return_value,
            success=success,
            error=error
        )
        
        with self.lock:
            self.syscall_records.append(record)
        
        # Логирование системного вызова
        self._log_syscall(record)
        
        return f"sys_{int(record.timestamp * 1000000)}"
    
    def _log_operation(self, record: IOOperationRecord):
        """Логирование I/O операции"""
        log_data = {
            'type': record.operation_type.value,
            'timestamp': record.timestamp,
            'thread': record.thread_id,
            'size': record.data_size,
            'success': record.success,
            'location': record.source_location
        }
        
        if record.error:
            log_data['error'] = record.error
        
        if record.metadata:
            log_data['metadata'] = record.metadata
        
        # Логируем первые 64 байт данных для анализа
        if record.data_bytes:
            sample_size = min(64, len(record.data_bytes))
            log_data['data_sample'] = record.data_bytes[:sample_size].hex()
        
        self.logger.info(f"IO_OPERATION: {log_data}")
        
        # Отправляем в трейсер через существующий интерфейс
        try:
            # Используем существующий метод логирования трейсера
            if hasattr(self.tracer, 'logger'):
                if record.success:
                    self.tracer.logger.info("io_operation", **log_data)
                else:
                    self.tracer.logger.error("io_operation", **log_data)
        except Exception:
            # Если трейсер недоступен, просто логируем через обычный логгер
            pass
    
    def _log_syscall(self, record: SystemCallRecord):
        """Логирование системного вызова"""
        log_data = {
            'syscall': record.syscall_name,
            'timestamp': record.timestamp,
            'thread': record.thread_id,
            'args': str(record.args)[:100],  # Ограничиваем длину
            'success': record.success,
            'return': str(record.return_value)[:50]
        }
        
        if record.error:
            log_data['error'] = record.error
        
        self.logger.info(f"SYSCALL: {log_data}")
    
    def verify_real_io(self) -> bool:
        """Проверить что были реальные I/O операции"""
        with self.lock:
            return self.io_operations_in_session
    
    def reset_session(self):
        """Сброс сессии - для предотвращения логических успехов без I/O"""
        with self.lock:
            self.io_operations_in_session = False
            self.session_start_time = time.time()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику операций"""
        with self.lock:
            return {
                'total_operations': len(self.records),
                'total_syscalls': len(self.syscall_records),
                'operation_stats': dict(self.operation_stats),
                'byte_stats': dict(self.byte_stats),
                'error_stats': dict(self.error_stats),
                'io_operations_in_session': self.io_operations_in_session,
                'session_duration': time.time() - self.session_start_time
            }
    
    def get_recent_operations(self, count: int = 100) -> List[IOOperationRecord]:
        """Получить последние операции"""
        with self.lock:
            return list(self.records)[-count:]

# Глобальный монитор
_io_monitor = IOMonitor()

def get_io_monitor() -> IOMonitor:
    """Получить экземпляр монитора I/O"""
    return _io_monitor

def instrument_socket_send(original_send: Callable) -> Callable:
    """Обертка для socket.send"""
    @functools.wraps(original_send)
    def wrapped_send(self, data: bytes, *args, **kwargs) -> int:
        start_time = time.time()
        
        try:
            result = original_send(self, data, *args, **kwargs)
            
            # Записываем операцию
            _io_monitor.record_operation(
                operation_type=IOOperationType.SOCKET_SEND,
                data=data[:result] if result > 0 else data,
                success=True,
                metadata={
                    'sent_bytes': result,
                    'total_bytes': len(data),
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                    'duration': time.time() - start_time
                }
            )
            
            # Записываем системный вызов
            _io_monitor.record_syscall(
                syscall_name='socket.send',
                args=(self, data[:result] if result > 0 else data) + args,
                kwargs=kwargs,
                return_value=result,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Записываем ошибку
            _io_monitor.record_operation(
                operation_type=IOOperationType.SOCKET_SEND,
                data=data,
                success=False,
                error=str(e),
                metadata={'duration': time.time() - start_time}
            )
            
            _io_monitor.record_syscall(
                syscall_name='socket.send',
                args=(self, data) + args,
                kwargs=kwargs,
                return_value=None,
                success=False,
                error=str(e)
            )
            
            raise
    
    return wrapped_send

def instrument_socket_recv(original_recv: Callable) -> Callable:
    """Обертка для socket.recv"""
    @functools.wraps(original_recv)
    def wrapped_recv(self, bufsize: int, *args, **kwargs) -> bytes:
        start_time = time.time()
        
        try:
            result = original_recv(self, bufsize, *args, **kwargs)
            
            # Записываем операцию
            _io_monitor.record_operation(
                operation_type=IOOperationType.SOCKET_RECV,
                data=result,
                success=True,
                metadata={
                    'requested_bytes': bufsize,
                    'received_bytes': len(result),
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                    'duration': time.time() - start_time
                }
            )
            
            # Записываем системный вызов
            _io_monitor.record_syscall(
                syscall_name='socket.recv',
                args=(self, bufsize) + args,
                kwargs=kwargs,
                return_value=result,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Записываем ошибку
            _io_monitor.record_operation(
                operation_type=IOOperationType.SOCKET_RECV,
                data=b"",
                success=False,
                error=str(e),
                metadata={
                    'requested_bytes': bufsize,
                    'duration': time.time() - start_time
                }
            )
            
            _io_monitor.record_syscall(
                syscall_name='socket.recv',
                args=(self, bufsize) + args,
                kwargs=kwargs,
                return_value=None,
                success=False,
                error=str(e)
            )
            
            raise
    
    return wrapped_recv

def instrument_asyncio_write(original_write: Callable) -> Callable:
    """Обертка для asyncio.StreamWriter.write"""
    @functools.wraps(original_write)
    async def wrapped_write(self, data: bytes) -> None:
        start_time = time.time()
        
        try:
            await original_write(self, data)
            
            # Записываем операцию
            _io_monitor.record_operation(
                operation_type=IOOperationType.ASYNCIO_WRITE,
                data=data,
                success=True,
                metadata={
                    'bytes_written': len(data),
                    'duration': time.time() - start_time
                }
            )
            
            # Записываем системный вызов
            _io_monitor.record_syscall(
                syscall_name='asyncio.StreamWriter.write',
                args=(self, data),
                kwargs={},
                return_value=None,
                success=True
            )
            
        except Exception as e:
            # Записываем ошибку
            _io_monitor.record_operation(
                operation_type=IOOperationType.ASYNCIO_WRITE,
                data=data,
                success=False,
                error=str(e),
                metadata={'duration': time.time() - start_time}
            )
            
            _io_monitor.record_syscall(
                syscall_name='asyncio.StreamWriter.write',
                args=(self, data),
                kwargs={},
                return_value=None,
                success=False,
                error=str(e)
            )
            
            raise
    
    return wrapped_write

def instrument_asyncio_read(original_read: Callable) -> Callable:
    """Обертка для asyncio.StreamReader.read"""
    @functools.wraps(original_read)
    async def wrapped_read(self, n: int = -1) -> bytes:
        start_time = time.time()
        
        try:
            result = await original_read(self, n)
            
            # Записываем операцию
            _io_monitor.record_operation(
                operation_type=IOOperationType.ASYNCIO_READ,
                data=result,
                success=True,
                metadata={
                    'requested_bytes': n,
                    'received_bytes': len(result),
                    'duration': time.time() - start_time
                }
            )
            
            # Записываем системный вызов
            _io_monitor.record_syscall(
                syscall_name='asyncio.StreamReader.read',
                args=(self, n),
                kwargs={},
                return_value=result,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Записываем ошибку
            _io_monitor.record_operation(
                operation_type=IOOperationType.ASYNCIO_READ,
                data=b"",
                success=False,
                error=str(e),
                metadata={
                    'requested_bytes': n,
                    'duration': time.time() - start_time
                }
            )
            
            _io_monitor.record_syscall(
                syscall_name='asyncio.StreamReader.read',
                args=(self, n),
                kwargs={},
                return_value=None,
                success=False,
                error=str(e)
            )
            
            raise
    
    return wrapped_read

def instrument_http_request(original_request: Callable) -> Callable:
    """Обертка для HTTP запросов"""
    @functools.wraps(original_request)
    async def wrapped_request(self, *args, **kwargs):
        start_time = time.time()
        
        # Извлекаем данные запроса
        method = args[0] if args else kwargs.get('method', 'GET')
        url = args[1] if len(args) > 1 else kwargs.get('url', '')
        data = kwargs.get('data', b'')
        headers = kwargs.get('headers', {})
        
        try:
            response = await original_request(self, *args, **kwargs)
            
            # Извлекаем данные ответа
            if hasattr(response, 'read'):
                response_data = await response.read()
                response_status = response.status
                response_headers = dict(response.headers)
            else:
                response_data = response.get('data', b'')
                response_status = response.get('status_code', 0)
                response_headers = response.get('headers', {})
            
            # Записываем операцию запроса
            _io_monitor.record_operation(
                operation_type=IOOperationType.HTTP_REQUEST,
                data=data,
                success=True,
                metadata={
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'duration': time.time() - start_time
                }
            )
            
            # Записываем операцию ответа
            _io_monitor.record_operation(
                operation_type=IOOperationType.HTTP_RESPONSE,
                data=response_data,
                success=True,
                metadata={
                    'status_code': response_status,
                    'headers': response_headers,
                    'response_size': len(response_data)
                }
            )
            
            # Записываем системный вызов
            _io_monitor.record_syscall(
                syscall_name='http.request',
                args=args,
                kwargs=kwargs,
                return_value=response_status,
                success=True
            )
            
            return response
            
        except Exception as e:
            # Записываем ошибку
            _io_monitor.record_operation(
                operation_type=IOOperationType.HTTP_REQUEST,
                data=data,
                success=False,
                error=str(e),
                metadata={
                    'method': method,
                    'url': url,
                    'duration': time.time() - start_time
                }
            )
            
            _io_monitor.record_syscall(
                syscall_name='http.request',
                args=args,
                kwargs=kwargs,
                return_value=None,
                success=False,
                error=str(e)
            )
            
            raise
    
    return wrapped_request

def require_real_io(func: Callable) -> Callable:
    """Декоратор для требования реальных I/O операций"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Сбрасываем сессию перед выполнением
        _io_monitor.reset_session()
        
        try:
            result = func(*args, **kwargs)
            
            # Проверяем что были реальные I/O операции
            if not _io_monitor.verify_real_io():
                raise RuntimeError(f"Function {func.__name__} completed without real I/O operations")
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            _io_monitor.logger.error(f"Real IO requirement failed for {func.__name__}: {str(e)}")
            raise
    
    return wrapper

def async_require_real_io(func: Callable) -> Callable:
    """Асинхронный декоратор для требования реальных I/O операций"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Сбрасываем сессию перед выполнением
        _io_monitor.reset_session()
        
        try:
            result = await func(*args, **kwargs)
            
            # Проверяем что были реальные I/O операции
            if not _io_monitor.verify_real_io():
                raise RuntimeError(f"Function {func.__name__} completed without real I/O operations")
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            _io_monitor.logger.error(f"Real IO requirement failed for {func.__name__}: {str(e)}")
            raise
    
    return wrapper

def patch_socket_operations():
    """Наложить патчи на socket операции"""
    socket.socket.send = instrument_socket_send(socket.socket.send)
    socket.socket.recv = instrument_socket_recv(socket.socket.recv)
    socket.socket.sendall = instrument_socket_send(socket.socket.sendall)
    socket.socket.recv_into = instrument_socket_recv(socket.socket.recv_into)

def patch_asyncio_operations():
    """Наложить патчи на asyncio операции"""
    asyncio.StreamWriter.write = instrument_asyncio_write(asyncio.StreamWriter.write)
    asyncio.StreamReader.read = instrument_asyncio_read(asyncio.StreamReader.read)

def patch_http_operations():
    """Наложить патчи на HTTP операции (для aiohttp)"""
    try:
        import aiohttp
        aiohttp.ClientSession.request = instrument_http_request(aiohttp.ClientSession.request)
    except ImportError:
        pass

def enable_instrumentation():
    """Включить всю инструментацию"""
    patch_socket_operations()
    patch_asyncio_operations()
    patch_http_operations()
    
    _io_monitor.logger.info("Instrumentation enabled for all I/O operations")

def disable_instrumentation():
    """Отключить инструментацию (восстановить оригинальные функции)"""
    # TODO: Implement restoration of original functions
    _io_monitor.logger.info("Instrumentation disabled")
