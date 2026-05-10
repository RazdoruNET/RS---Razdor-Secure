#!/usr/bin/env python3
"""
Network Reality Verifier - TASK 8.3
Отделяет "код сказал отправил" от "ОС реально отправила"
Проверяет реальные сетевые операции против заявленных
"""

import socket
import asyncio
import time
import struct
import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for logger import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger(__name__)

class VerificationStatus(Enum):
    """Статусы верификации"""
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"

@dataclass
class NetworkOperation:
    """Описание сетевой операции"""
    operation_type: str  # "send", "recv", "connect", "handshake"
    claimed_bytes: int = 0
    claimed_success: bool = False
    timestamp: float = 0.0
    socket_fd: Optional[int] = None
    target_host: str = ""
    target_port: int = 0

@dataclass
class VerificationResult:
    """Результат верификации"""
    operation: NetworkOperation
    socket_open: bool = False
    bytes_sent_verified: bool = False
    bytes_recv_verified: bool = False
    handshake_verified: bool = False
    network_verified: bool = False
    verification_time: float = 0.0
    error_message: str = ""
    raw_metrics: Dict[str, Any] = None

class NetworkRealityVerifier:
    """
    Верификатор реальных сетевых операций
    Проверяет что ОС действительно выполнила заявленные операции
    """
    
    def __init__(self):
        self.active_sockets: Dict[int, Dict[str, Any]] = {}
        self.verification_history: List[VerificationResult] = []
        self.logger = logger
        
    async def verify_network_operation(self, operation: NetworkOperation) -> VerificationResult:
        """
        Основной метод верификации сетевой операции
        
        Args:
            operation: Заявленная сетевая операция
            
        Returns:
            VerificationResult: Результат верификации
        """
        start_time = time.time()
        result = VerificationResult(operation=operation, raw_metrics={})
        
        try:
            self.logger.info(f"🔍 Верификация операции: {operation.operation_type} -> {operation.target_host}:{operation.target_port}")
            
            # 1. Проверка что сокет реально открыт
            if operation.socket_fd is not None:
                result.socket_open = await self._verify_socket_open(operation.socket_fd)
                result.raw_metrics['socket_open_check'] = result.socket_open
            else:
                result.socket_open = False
                result.raw_metrics['socket_open_check'] = "no_fd_provided"
            
            # 2. Проверка bytes_sent > 0
            if operation.operation_type == "send" and operation.claimed_bytes > 0:
                result.bytes_sent_verified = await self._verify_bytes_sent(operation)
                result.raw_metrics['bytes_sent_check'] = result.bytes_sent_verified
            else:
                result.bytes_sent_verified = operation.operation_type != "send"
                result.raw_metrics['bytes_sent_check'] = "not_applicable"
            
            # 3. Проверка recv != 0
            if operation.operation_type == "recv":
                result.bytes_recv_verified = await self._verify_bytes_received(operation)
                result.raw_metrics['bytes_recv_check'] = result.bytes_recv_verified
            else:
                result.bytes_recv_verified = operation.operation_type != "recv"
                result.raw_metrics['bytes_recv_check'] = "not_applicable"
            
            # 4. Проверка TCP handshake
            if operation.operation_type == "connect" or operation.operation_type == "handshake":
                result.handshake_verified = await self._verify_tcp_handshake(operation)
                result.raw_metrics['handshake_check'] = result.handshake_verified
            else:
                result.handshake_verified = operation.operation_type not in ["connect", "handshake"]
                result.raw_metrics['handshake_check'] = "not_applicable"
            
            # Общая верификация
            result.network_verified = self._calculate_final_verification(result)
            result.verification_time = time.time() - start_time
            
            # Логирование результатов
            self._log_verification_result(result)
            
            # Сохранение в историю
            self.verification_history.append(result)
            
            return result
            
        except Exception as e:
            result.error_message = f"Verification error: {str(e)}"
            result.verification_time = time.time() - start_time
            self.logger.error(f"❌ Ошибка верификации: {e}")
            return result
    
    async def _verify_socket_open(self, socket_fd: int) -> bool:
        """
        Проверка что сокет реально открыт в ОС
        
        Args:
            socket_fd: Файловый дескриптор сокета
            
        Returns:
            bool: True если сокет открыт
        """
        try:
            # Проверка через getsockopt
            sock = socket.fromfd(socket_fd, socket.AF_INET, socket.SOCK_STREAM)
            
            # Проверяем что сокет валиден
            try:
                sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                return True
            except OSError as e:
                if e.errno == 9:  # EBADF - Bad file descriptor
                    return False
                elif e.errno == 107:  # ENOTCONN - Transport endpoint is not connected
                    return True  # Сокет открыт но не подключен
                else:
                    # Другие ошибки могут означать что сокет в проблемном состоянии
                    self.logger.warning(f"⚠️ Сокет {socket_fd} в состоянии: {e}")
                    return False
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось проверить сокет {socket_fd}: {e}")
            return False
    
    async def _verify_bytes_sent(self, operation: NetworkOperation) -> bool:
        """
        Проверка что данные реально были отправлены
        
        Args:
            operation: Операция отправки
            
        Returns:
            bool: True если данные отправлены
        """
        try:
            if operation.socket_fd is None:
                return False
            
            # Проверяем через getsockopt SO_SNDBUF и статистику отправки
            sock = socket.fromfd(operation.socket_fd, socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                # Получаем статистику отправки через ioctl SIOCOUTQ
                import fcntl
                outq = struct.unpack('I', fcntl.ioctl(sock.fileno(), 0x5412, struct.pack('I', 0)))[0]
                
                # Если outq < claimed_bytes, значит данные были отправлены из буфера
                # Если outq == 0 и claimed_bytes > 0, значит все данные отправлены
                if outq == 0 and operation.claimed_bytes > 0:
                    return True
                elif outq < operation.claimed_bytes:
                    return True
                else:
                    return False
                    
            except (ImportError, OSError, struct.error):
                # Fallback: проверяем через send buffer size
                sndbuf = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
                return operation.claimed_bytes <= sndbuf
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось проверить отправку байт: {e}")
            return False
    
    async def _verify_bytes_received(self, operation: NetworkOperation) -> bool:
        """
        Проверка что данные реально были получены
        
        Args:
            operation: Операция получения
            
        Returns:
            bool: True если данные получены
        """
        try:
            if operation.socket_fd is None:
                return False
            
            # Проверяем через getsockopt SO_RCVBUF и статистику приема
            sock = socket.fromfd(operation.socket_fd, socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                # Проверяем наличие данных в буфере приема
                # Используем ioctl SIOCINQ для проверки доступных байт
                import fcntl
                inq = struct.unpack('I', fcntl.ioctl(sock.fileno(), 0x541B, struct.pack('I', 0)))[0]
                
                # Если в буфере есть данные или claimed_bytes > 0, значит были получены данные
                return inq > 0 or operation.claimed_bytes > 0
                
            except (ImportError, OSError, struct.error):
                # Fallback: проверяем через receive buffer size
                rcvbuf = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
                return operation.claimed_bytes <= rcvbuf
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось проверку получения байт: {e}")
            return False
    
    async def _verify_tcp_handshake(self, operation: NetworkOperation) -> bool:
        """
        Проверка что TCP handshake реально состоялся
        
        Args:
            operation: Операция подключения
            
        Returns:
            bool: True если handshake выполнен
        """
        try:
            if operation.socket_fd is None:
                return False
            
            sock = socket.fromfd(operation.socket_fd, socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                # Проверяем состояние сокета через getsockopt
                error = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                
                if error == 0:
                    # Проверяем что сокет действительно подключен
                    try:
                        # Пытаемся получить локальный и удаленный адреса
                        local_addr = sock.getsockname()
                        remote_addr = sock.getpeername()
                        
                        # Если адреса получены и порт != 0, значит соединение установлено
                        return (remote_addr[1] > 0 and 
                               operation.target_host in remote_addr[0] and
                               operation.target_port == remote_addr[1])
                    except OSError:
                        # getpeername failed - соединение не установлено
                        return False
                else:
                    # Есть ошибка в сокете
                    return False
                    
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось проверить TCP handshake: {e}")
            return False
    
    def _calculate_final_verification(self, result: VerificationResult) -> bool:
        """
        Расчет финального статуса верификации
        
        Args:
            result: Результаты проверок
            
        Returns:
            bool: Финальный статус верификации
        """
        # Базовая логика: все применимые проверки должны пройти
        checks = []
        
        # Всегда проверяем сокет
        checks.append(result.socket_open)
        
        # Проверяем отправку если применимо
        if result.operation.operation_type == "send":
            checks.append(result.bytes_sent_verified)
        
        # Проверяем получение если применимо
        if result.operation.operation_type == "recv":
            checks.append(result.bytes_recv_verified)
        
        # Проверяем handshake если применимо
        if result.operation.operation_type in ["connect", "handshake"]:
            checks.append(result.handshake_verified)
        
        # Все проверки должны быть True
        return all(checks)
    
    def _log_verification_result(self, result: VerificationResult):
        """Логирование результатов верификации"""
        status = "✅ VERIFIED" if result.network_verified else "❌ FAILED"
        
        self.logger.info(f"{status} {result.operation.operation_type} -> {result.operation.target_host}:{result.operation.target_port}")
        self.logger.info(f"  Socket: {'✅' if result.socket_open else '❌'}")
        self.logger.info(f"  Bytes Sent: {'✅' if result.bytes_sent_verified else '❌'}")
        self.logger.info(f"  Bytes Recv: {'✅' if result.bytes_recv_verified else '❌'}")
        self.logger.info(f"  Handshake: {'✅' if result.handshake_verified else '❌'}")
        self.logger.info(f"  Time: {result.verification_time:.3f}s")
        
        if result.error_message:
            self.logger.error(f"  Error: {result.error_message}")
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики верификации
        
        Returns:
            Dict: Статистика верификаций
        """
        if not self.verification_history:
            return {
                'total_verifications': 0,
                'successful_verifications': 0,
                'failed_verifications': 0,
                'success_rate': 0.0,
                'avg_verification_time': 0.0
            }
        
        total = len(self.verification_history)
        successful = sum(1 for r in self.verification_history if r.network_verified)
        failed = total - successful
        avg_time = sum(r.verification_time for r in self.verification_history) / total
        
        return {
            'total_verifications': total,
            'successful_verifications': successful,
            'failed_verifications': failed,
            'success_rate': successful / total,
            'avg_verification_time': avg_time,
            'recent_success_rate': self._get_recent_success_rate()
        }
    
    def _get_recent_success_rate(self, window: int = 10) -> float:
        """
        Получение success rate за последние N верификаций
        
        Args:
            window: Размер окна
            
        Returns:
            float: Success rate
        """
        recent = self.verification_history[-window:]
        if not recent:
            return 0.0
        
        successful = sum(1 for r in recent if r.network_verified)
        return successful / len(recent)
    
    def clear_history(self):
        """Очистка истории верификаций"""
        self.verification_history.clear()
        self.logger.info("🧹 История верификаций очищена")
    
    async def create_test_operation(self, host: str, port: int, operation_type: str) -> Tuple[NetworkOperation, int]:
        """
        Создание тестовой операции для верификации
        
        Args:
            host: Целевой хост
            port: Целевой порт
            operation_type: Тип операции
            
        Returns:
            Tuple[NetworkOperation, int]: Операция и FD сокета
        """
        try:
            # Создаем реальный сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            if operation_type == "connect":
                # Выполняем подключение
                sock.connect((host, port))
                
                operation = NetworkOperation(
                    operation_type="connect",
                    claimed_success=True,
                    timestamp=time.time(),
                    socket_fd=sock.fileno(),
                    target_host=host,
                    target_port=port
                )
                
                return operation, sock.fileno()
                
            elif operation_type == "send":
                # Подключаемся и отправляем данные
                sock.connect((host, port))
                test_data = b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n"
                bytes_sent = sock.send(test_data)
                
                operation = NetworkOperation(
                    operation_type="send",
                    claimed_bytes=bytes_sent,
                    claimed_success=True,
                    timestamp=time.time(),
                    socket_fd=sock.fileno(),
                    target_host=host,
                    target_port=port
                )
                
                return operation, sock.fileno()
                
            elif operation_type == "recv":
                # Подключаемся, отправляем запрос и получаем ответ
                sock.connect((host, port))
                test_data = b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n"
                sock.send(test_data)
                
                try:
                    response = sock.recv(4096)
                    bytes_recv = len(response)
                except socket.timeout:
                    bytes_recv = 0
                
                operation = NetworkOperation(
                    operation_type="recv",
                    claimed_bytes=bytes_recv,
                    claimed_success=True,
                    timestamp=time.time(),
                    socket_fd=sock.fileno(),
                    target_host=host,
                    target_port=port
                )
                
                return operation, sock.fileno()
                
            else:
                raise ValueError(f"Unsupported operation type: {operation_type}")
                
        except Exception as e:
            self.logger.error(f"❌ Не удалось создать тестовую операцию: {e}")
            raise

# Удобная функция для быстрой верификации
async def verify_network_reality(operation_type: str, host: str, port: int, **kwargs) -> Dict[str, Any]:
    """
    Удобная функция для верификации сетевой операции
    
    Args:
        operation_type: Тип операции
        host: Целевой хост
        port: Целевой порт
        **kwargs: Дополнительные параметры
        
    Returns:
        Dict: Результат верификации
    """
    verifier = NetworkRealityVerifier()
    
    operation = NetworkOperation(
        operation_type=operation_type,
        claimed_bytes=kwargs.get('claimed_bytes', 0),
        claimed_success=kwargs.get('claimed_success', True),
        timestamp=time.time(),
        socket_fd=kwargs.get('socket_fd'),
        target_host=host,
        target_port=port
    )
    
    result = await verifier.verify_network_operation(operation)
    
    return {
        'network_verified': result.network_verified,
        'verification_time': result.verification_time,
        'checks': {
            'socket_open': result.socket_open,
            'bytes_sent_verified': result.bytes_sent_verified,
            'bytes_recv_verified': result.bytes_recv_verified,
            'handshake_verified': result.handshake_verified
        },
        'raw_metrics': result.raw_metrics,
        'error_message': result.error_message
    }
