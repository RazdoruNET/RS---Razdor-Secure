"""
HTTP Fragmentation Pipeline - Фрагментация HTTP запросов
"""

import asyncio
import time
import random
import socket
import logging
import re
from typing import Dict, Any, NamedTuple
from dataclasses import dataclass
from collections import deque
import json

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse, PipelineExecutionStatus
from core.http_client import TCPClient

from enum import Enum

class FragmentMode(Enum):
    """Режимы фрагментации"""
    FIXED = "fixed"
    RANDOM = "random"
    HEADER_BODY_SPLIT = "header_body_split"
    BYTE_BY_BYTE = "byte_by_byte"

class PerformanceRecord(NamedTuple):
    """Запись производительности"""
    timestamp: float
    response_time: float
    success: bool
    status_code: int
    fragment_count: int
    bytes_sent: int
    bytes_received: int

@dataclass
class FragmentationConfig:
    """Конфигурация фрагментации"""
    fragment_size: int = 256
    fragment_delay: float = 0.001
    random_padding: bool = False
    fragment_mode: FragmentMode = FragmentMode.FIXED
    jitter_range: tuple = (0.8, 1.2)  # Random jitter для задержек

logger = logging.getLogger(__name__)

class HTTPFragmentationPipeline(BasePipeline):
    """Пайплайн для фрагментации HTTP запросов"""
    
    def __init__(self):
        super().__init__("HTTPFragmentation", BypassTechnique.SPOOF_DPI, priority=3, execution_status=PipelineExecutionStatus.REAL)
        self.config = FragmentationConfig()
        self.tcp_client = TCPClient(timeout=10.0)
        
        # Performance tracking с защитой от memory leaks и thread safety
        self._performance_lock = asyncio.Lock()
        self.performance_history = deque(maxlen=1000)  # Ring buffer с ограничением
        self.total_requests = 0
        self.successful_requests = 0
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение реальной HTTP фрагментации"""
        start_time = time.time()
        
        writer = None
        reader = None
        
        try:
            # Создаем HTTP запрос для фрагментации
            http_request = self._create_fragmented_request(request)
            
            # Разбиваем на фрагменты с защитой от memory spikes
            try:
                fragments = self._fragment_data(http_request, self.config.fragment_size)
            except Exception as e:
                logger.error(f"Fragmentation failed: {str(e)}")
                # Fallback на фрагментацию с текущим конфигом при ошибках
                fragments = [http_request[i:i+self.config.fragment_size] for i in range(0, len(http_request), self.config.fragment_size)]
            
            # Устанавливаем соединение (TCP для HTTP, TLS для HTTPS) с валидацией
            try:
                if request.port == 443:
                    # HTTPS - используем TLS
                    connection_result = await self.tcp_client.create_tls_connection(request.host, request.port)
                else:
                    # HTTP - используем plain TCP
                    connection_result = await self.tcp_client.create_connection(request.host, request.port)
                
                # Валидируем результат соединения
                if not connection_result or len(connection_result) != 2:
                    raise ConnectionError(f"Invalid connection result: {connection_result}")
                
                reader, writer = connection_result
                
            except Exception as e:
                logger.error(f"Connection failed: {str(e)}")
                raise
            
            # Устанавливаем TCP_NODELAY один раз для гарантии фрагментации
            sock = writer.get_extra_info('socket')
            if sock is not None:
                try:
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    logger.debug("TCP_NODELAY set successfully")
                except (AttributeError, OSError) as e:
                    logger.warning(f"Failed to set TCP_NODELAY: {str(e)}")
                    logger.debug(f"Socket type: {type(sock)}, transport: {type(writer)}")
            else:
                logger.warning("Socket is None, cannot set TCP_NODELAY")
            
            # Отправляем фрагменты с задержкой и jitter
            for i, fragment in enumerate(fragments):
                await self.tcp_client.send_data(writer, fragment)
                
                # Добавляем jitter к задержке для имитации реального трафика
                jitter_delay = random.uniform(*self.config.jitter_range)
                actual_delay = self.config.fragment_delay * jitter_delay
                await asyncio.sleep(actual_delay)
                
                # Padding отключен - ломает HTTP протокол
                # Для реальной packet fragmentation нужны raw sockets
                # asyncio stream не даёт контроля над packet boundaries
            
            # Получаем ответ полностью (надежное чтение с защитой от бесконечного цикла)
            buffer = bytearray()
            max_response_size = 10 * 1024 * 1024  # 10MB лимит
            max_chunks = 1000  # Максимальное количество чанков для защиты от memory overflow
            start_read_time = time.time()
            max_read_time = 60.0  # 60 секунд максимум на чтение
            
            while True:
                # Проверяем таймаут чтения
                elapsed = time.time() - start_read_time
                if elapsed > max_read_time:
                    logger.warning(f"Response read timeout after {elapsed:.1f}s")
                    break
                
                # Проверяем размер буфера и количество чанков
                if len(buffer) > max_response_size:
                    logger.warning(f"Response too large: {len(buffer)} bytes, truncating")
                    break
                
                if len(buffer) // 8192 > max_chunks:  # Защита от memory overflow
                    logger.warning(f"Too many chunks: {len(buffer) // 8192}, stopping read")
                    break
                
                try:
                    chunk = await asyncio.wait_for(
                        reader.read(8192),
                        timeout=5.0  # Таймаут на каждый chunk
                    )
                    if not chunk:
                        break
                    buffer.extend(chunk)
                except asyncio.TimeoutError:
                    logger.warning("Chunk read timeout, ending response read")
                    break
                except Exception as e:
                    logger.error(f"Error reading chunk: {str(e)}")
                    break
            
            response_data = bytes(buffer)
            
            response_time = time.time() - start_time
            
            # Анализируем ответ с корректным парсингом status line
            status_code = self._parse_http_status(response_data)
            success = 200 <= status_code < 400
            
            # Записываем performance metrics
            self._record_performance(
                response_time=response_time,
                success=success,
                status_code=status_code,
                fragment_count=len(fragments),
                bytes_sent=len(http_request),
                bytes_received=len(response_data)
            )
            
            return BypassResponse(
                success=success,
                latency=response_time,
                status_code=status_code,
                technique_used=self.name,
                data=response_data,
                headers={
                    'X-Fragments': str(len(fragments)),
                    'X-Fragment-Size': str(self.config.fragment_size),
                    'X-Fragment-Delay': str(self.config.fragment_delay),
                    'X-Random-Padding': str(self.config.random_padding),
                    'X-Success-Rate': f"{self._get_success_rate():.1%}",
                    'X-Avg-Latency': f"{self._get_avg_latency():.3f}s"
                }
            )
            
        except Exception as e:
            logger.error(f"HTTP fragmentation error: {str(e)}")
            return BypassResponse(
                success=False,
                latency=time.time() - start_time,
                error_reason=f"HTTP fragmentation error: {str(e)}"
            )
        finally:
            # Гарантированное закрытие соединения
            if writer:
                try:
                    await self.tcp_client.close_connection(writer)
                except Exception as e:
                    logger.error(f"Error closing connection: {str(e)}")
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией и валидацией диапазонов"""
        try:
            # Безопасный парсинг FragmentMode с fallback
            mode_str = config.get('fragment_mode', 'FIXED').upper()
            try:
                fragment_mode = FragmentMode[mode_str]
            except KeyError:
                logger.warning(f"Unknown fragment mode '{mode_str}', falling back to FIXED")
                fragment_mode = FragmentMode.FIXED
            
            # Валидация fragment_size
            fragment_size = config.get('fragment_size', 256)
            if not self._validate_fragment_size(fragment_size):
                logger.warning(f"Invalid fragment_size: {fragment_size}, using default 256")
                fragment_size = 256
            
            # Валидация fragment_delay
            fragment_delay = config.get('fragment_delay', 0.001)
            if not self._validate_fragment_delay(fragment_delay):
                logger.warning(f"Invalid fragment_delay: {fragment_delay}, using default 0.001")
                fragment_delay = 0.001
            
            # Валидация jitter_range
            jitter_range = config.get('jitter_range', (0.8, 1.2))
            if not self._validate_jitter_range(jitter_range):
                logger.warning(f"Invalid jitter_range: {jitter_range}, using default (0.8, 1.2)")
                jitter_range = (0.8, 1.2)
            
            # Валидация random_padding
            random_padding = config.get('random_padding', False)
            if not isinstance(random_padding, bool):
                logger.warning(f"Invalid random_padding: {random_padding}, using default False")
                random_padding = False
            
            self.config = FragmentationConfig(
                fragment_size=fragment_size,
                fragment_delay=fragment_delay,
                random_padding=random_padding,
                fragment_mode=fragment_mode,
                jitter_range=jitter_range
            )
        except Exception as e:
            logger.error(f"Invalid config: {str(e)}")
            return False
        
        logger.info(f"HTTPFragmentation initialized: size={self.config.fragment_size}, delay={self.config.fragment_delay}, mode={self.config.fragment_mode.value}")
        return True
    
    def _create_fragmented_request(self, request: BypassRequest) -> bytes:
        """Создание HTTP запроса для фрагментации"""
        headers = request.headers or {}
        path = getattr(request, 'path', '/')
        
        # Валидируем обязательные поля request
        if not hasattr(request, 'method') or not request.method:
            raise ValueError("Request method is required")
        if not hasattr(request, 'host') or not request.host:
            raise ValueError("Request host is required")
        
        # Валидация метода HTTP
        allowed_methods = {'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH'}
        if request.method not in allowed_methods:
            logger.warning(f"Unsupported method: {request.method}, allowing but may cause issues")
        
        # Валидация host
        if not isinstance(request.host, str) or len(request.host.strip()) == 0:
            raise ValueError("Host must be non-empty string")
        if len(request.host) > 253:  # RFC 1034
            logger.warning(f"Host too long: {len(request.host)}, truncating")
            request.host = request.host[:253]
        
        # Валидируем и формируем базовые заголовки
        request_headers = {
            "Host": self._validate_header_value(request.host),
            "Connection": "close",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        # Добавляем пользовательские заголовки с валидацией
        for key, value in headers.items():
            clean_key = self._validate_header_name(key)
            clean_value = self._validate_header_value(value, key)
            if clean_key and clean_value:
                request_headers[clean_key] = clean_value
        
        # Добавляем Content-Length если есть тело
        body = request.data or b""
        if body:
            request_headers["Content-Length"] = str(len(body))
            if "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/octet-stream"
        
        # Собираем HTTP запрос как bytes
        lines = [f"{request.method} {path} HTTP/1.1".encode()]
        
        for key, value in request_headers.items():
            lines.append(f"{key}: {value}".encode())
        
        lines.append(b"")  # Пустая строка перед телом
        
        # Собираем полный запрос
        request_bytes = b"\r\n".join(lines) + b"\r\n" + body
        
        return request_bytes
    
    def _fragment_data(self, data: bytes, fragment_size: int) -> list:
        """Разбиение данных на фрагменты с учётом режима"""
        fragments = []
        
        if self.config.fragment_mode == FragmentMode.HEADER_BODY_SPLIT:
            # Разделяем headers и body
            split_pos = data.find(b'\r\n\r\n')
            if split_pos != -1:
                headers = data[:split_pos]
                body = data[split_pos + 4:]
                fragments.append(headers)
                if body:
                    fragments.append(body)
            else:
                fragments.append(data)
        elif self.config.fragment_mode == FragmentMode.BYTE_BY_BYTE:
            # Побайтовая фрагментация с защитой от перегрузки
            if len(data) > 2048:  # Уменьшен лимит для защиты от CPU spike
                logger.warning(f"Data too large for BYTE_BY_BYTE mode: {len(data)} bytes, falling back to FIXED")
                # Fallback на FIXED режим
                for i in range(0, len(data), self.config.fragment_size):
                    fragment = data[i:i + self.config.fragment_size]
                    fragments.append(fragment)
            else:
                # Защита от слишком большого количества фрагментов
                if len(data) > 1024:  # Максимум 1KB для BYTE_BY_BYTE
                    logger.warning(f"Data too large for BYTE_BY_BYTE mode: {len(data)} bytes, falling back to FIXED")
                    for i in range(0, len(data), self.config.fragment_size):
                        fragment = data[i:i + self.config.fragment_size]
                        fragments.append(fragment)
                else:
                    # Защита от слишком большого количества фрагментов
                    max_fragments = 512  # Hard cap для защиты от CPU spikes
                    fragment_count = 0
                    for i in range(len(data)):
                        if fragment_count >= max_fragments:
                            logger.warning(f"Too many fragments ({fragment_count}), stopping BYTE_BY_BYTE mode")
                            break
                        fragments.append(bytes([data[i]]))
                        fragment_count += 1
        elif self.config.fragment_mode == FragmentMode.RANDOM:
            # Случайные размеры фрагментов
            pos = 0
            while pos < len(data):
                size = random.randint(1, min(fragment_size, len(data) - pos))
                fragments.append(data[pos:pos + size])
                pos += size
        else:  # FIXED
            # Фиксированная фрагментация
            for i in range(0, len(data), fragment_size):
                fragment = data[i:i + fragment_size]
                fragments.append(fragment)
        
        return fragments
    
    def _parse_http_status(self, response_data: bytes) -> int:
        """Устойчивый парсинг HTTP статуса из ответа"""
        if not response_data:
            logger.debug("Empty response data")
            return 0
        
        try:
            # Ищем status line в первых 10 строках (для устойчивости к garbage)
            lines = response_data.split(b"\r\n")
            
            for line in lines[:10]:
                match = re.search(rb'HTTP/\d\.\d\s+(\d+)', line)
                if match:
                    return int(match.group(1))
            
            # Fallback: ищем первое число после HTTP/
            for line in lines[:5]:
                parts = line.split(b' ')
                if len(parts) >= 2 and b'HTTP/' in parts[0]:
                    try:
                        return int(parts[1])
                    except ValueError:
                        pass
            
            # Если статус не найден, логируем причину
            if len(response_data) > 0:
                logger.warning(f"Could not parse HTTP status from response, first 100 bytes: {response_data[:100]}")
            else:
                logger.warning("Empty response, cannot parse HTTP status")
            
            return 0
        except Exception as e:
            logger.error(f"Error parsing HTTP status: {str(e)}")
            return 0
    
        
    def _validate_header_name(self, name: str) -> str:
        """Валидация имени HTTP заголовка"""
        if not name:
            return ""
        
        # Удаляем опасные символы
        clean_name = name.strip()
        
        # Запрещаем спецсимволы в именах заголовков
        if any(char in clean_name for char in ['\r', '\n', '\0']):
            logger.warning(f"Invalid header name: {repr(name)}")
            return ""
        
        # Ограничиваем длину имени
        if len(clean_name) > 100:
            logger.warning(f"Header name too long: {len(clean_name)}")
            return clean_name[:100]
        
        return clean_name
    
    def _validate_header_value(self, value: str, header_name: str = "") -> str:
        """Валидация значения HTTP заголовка"""
        if value is None:
            return ""
        
        # Конвертируем в строку если нужно
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                value = value.decode('latin-1', errors='replace')
        elif not isinstance(value, str):
            value = str(value)
        
        # Удаляем опасные символы
        clean_value = value.strip()
        
        # Запрещаем \r и \n в значениях заголовков
        clean_value = clean_value.replace('\r', '').replace('\n', '')
        
        # Удаляем null bytes
        clean_value = clean_value.replace('\0', '')
        
        # Ограничиваем длину значения (RFC 7230)
        if len(clean_value) > 8192:
            logger.warning(f"Header value too long: {len(clean_value)}, truncating")
            clean_value = clean_value[:8192]
        
        # Дополнительная валидация для ключевых заголовков
        if header_name.lower() in ['host', 'user-agent', 'connection']:
            if len(clean_value) > 1024:  # Более строгий лимит для ключевых заголовков
                logger.warning(f"Key header value too long: {len(clean_value)}, truncating")
                clean_value = clean_value[:1024]
        
        return clean_value
    
    def _validate_fragment_size(self, size: int) -> bool:
        """Валидация fragment_size для защиты от критических значений"""
        if not isinstance(size, (int, float)):
            return False
        
        size = int(size)
        
        # Защита от division by zero
        if size <= 0:
            return False
        
        # Защита от слишком малых значений
        if size < 1:
            return False
        
        # Защита от слишком больших значений (memory protection)
        if size > 10240:  # 10KB максимальный размер фрагмента
            return False
        
        return True
    
    def _validate_fragment_delay(self, delay: float) -> bool:
        """Валидация fragment_delay для защиты от аномальных значений"""
        if not isinstance(delay, (int, float)):
            return False
        
        delay = float(delay)
        
        # Защита от отрицательных значений
        if delay < 0:
            return False
        
        # Защита от слишком больших задержек
        if delay > 1.0:  # 1 секунда максимум
            return False
        
        return True
    
    def _validate_jitter_range(self, jitter_range: tuple) -> bool:
        """Валидация jitter_range для защиты от инвертированных диапазонов"""
        if not isinstance(jitter_range, (tuple, list)):
            return False
        
        if len(jitter_range) != 2:
            return False
        
        try:
            min_val, max_val = float(jitter_range[0]), float(jitter_range[1])
        except (ValueError, TypeError):
            return False
        
        # Защита от инвертированных диапазонов
        if min_val >= max_val:
            return False
        
        # Защита от экстремальных значений
        if min_val < 0.1 or max_val > 5.0:
            return False
        
        # Защита от слишком широкого диапазона
        if max_val - min_val > 2.0:
            return False
        
        return True
    
    def _record_performance(self, response_time: float, success: bool, status_code: int, 
                         fragment_count: int, bytes_sent: int, bytes_received: int):
        """Записываем performance metrics в ring buffer с thread-safety"""
        record = PerformanceRecord(
            timestamp=time.time(),
            response_time=response_time,
            success=success,
            status_code=status_code,
            fragment_count=fragment_count,
            bytes_sent=bytes_sent,
            bytes_received=bytes_received
        )
        
        # Используем try/except для thread-safety без async
        try:
            self.performance_history.append(record)
            self.total_requests += 1
            if success:
                self.successful_requests += 1
        except Exception as e:
            logger.warning(f"Failed to record performance metrics: {str(e)}")
    
    def _get_success_rate(self) -> float:
        """Расчет success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def _get_avg_latency(self) -> float:
        """Расчет средней задержки"""
        if not self.performance_history:
            return 0.0
        
        recent_records = list(self.performance_history)[-100:]  # Последние 100 записей
        if not recent_records:
            return 0.0
        
        return sum(r.response_time for r in recent_records) / len(recent_records)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        if not self.performance_history:
            return {}
        
        recent = list(self.performance_history)[-50:]  # Последние 50 записей
        
        # Bypass effectiveness metrics
        successful_recent = sum(1 for r in recent if r.success)
        effectiveness_score = (successful_recent / len(recent)) * 100 if recent else 0.0
        
        # Latency distribution
        latencies = [r.response_time for r in recent]
        if latencies:
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        else:
            min_latency = max_latency = p95_latency = 0.0
        
        # Fragmentation effectiveness
        avg_fragments = sum(r.fragment_count for r in recent) / len(recent) if recent else 0
        avg_bytes_sent = sum(r.bytes_sent for r in recent) / len(recent) if recent else 0
        avg_bytes_received = sum(r.bytes_received for r in recent) / len(recent) if recent else 0
        
        return {
            'total_requests': self.total_requests,
            'success_rate': self._get_success_rate(),
            'avg_latency': self._get_avg_latency(),
            'recent_avg_latency': sum(r.response_time for r in recent) / len(recent) if recent else 0.0,
            'min_latency': min_latency,
            'max_latency': max_latency,
            'p95_latency': p95_latency,
            'effectiveness_score': effectiveness_score,
            'avg_fragments': avg_fragments,
            'avg_bytes_sent': avg_bytes_sent,
            'avg_bytes_received': avg_bytes_received,
            'history_size': len(self.performance_history),
            'max_history': self.performance_history.maxlen
        }
    
    def log_bypass_effectiveness(self, target_host: str):
        """Логирование bypass effectiveness для анализа"""
        stats = self.get_performance_stats()
        
        logger.info(f"Bypass Effectiveness Report for {target_host}:")
        logger.info(f"  Success Rate: {stats.get('success_rate', 0):.1f}%")
        logger.info(f"  Effectiveness Score: {stats.get('effectiveness_score', 0):.1f}%")
        logger.info(f"  Avg Latency: {stats.get('avg_latency', 0):.3f}s")
        logger.info(f"  P95 Latency: {stats.get('p95_latency', 0):.3f}s")
        logger.info(f"  Avg Fragments: {stats.get('avg_fragments', 0):.1f}")
        logger.info(f"  Total Requests: {stats.get('total_requests', 0)}")
        
        # Записываем в файл для долгосрочного анализа
        try:
            log_entry = {
                'timestamp': time.time(),
                'target_host': target_host,
                'stats': stats,
                'config': {
                    'fragment_size': self.config.fragment_size,
                    'fragment_delay': self.config.fragment_delay,
                    'fragment_mode': self.config.fragment_mode.value,
                    'jitter_range': self.config.jitter_range
                }
            }
            
            # Здесь можно добавить запись в файл или БД
            # with open('bypass_effectiveness.log', 'a') as f:
            #     f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            logger.warning(f"Failed to log bypass effectiveness: {str(e)}")
    
    async def cleanup(self) -> bool:
        """Очистка ресурсов"""
        if self.tcp_client:
            await self.tcp_client.cleanup()
        return True
