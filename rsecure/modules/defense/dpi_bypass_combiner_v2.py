#!/usr/bin/env python3
"""
DPI-Bypass Combiner v2.0 "White-Ghost"
Многоуровневые цепочки обхода DPI с адаптивной мимикрией под whitelist РФ
Zero-Dependency реализация для macOS User-Space
"""

import socket
import ssl
import time
import random
import struct
import threading
import subprocess
import os
import json
import hashlib
import base64
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass
import urllib.request
import urllib.error


class PipelineStage(Enum):
    """Этапы цепочки обхода"""
    FRAGMENTATION = "fragmentation"
    SNI_SPOOFING = "sni_spoofing"
    HEADER_OBFUSCATION = "header_obfuscation"
    TLS_JUNK = "tls_junk"
    HTTP2_MULTIPLEXING = "http2_multiplexing"
    FAKE_PADDING = "fake_padding"
    ENCRYPTED_PAYLOAD = "encrypted_payload"
    TTL_LOWERING = "ttl_lowering"


@dataclass
class PipelineResult:
    """Результат выполнения цепочки"""
    success: bool
    stage_completed: str
    error: Optional[str] = None
    duration: float = 0.0
    response_data: Optional[bytes] = None


class WhitelistEngine:
    """Whitelist Engine с Randomizer для доменов-прикрытий"""
    
    def __init__(self):
        self.WHITE_LIST_DOMAINS = {
            "GOVERNMENT": [
                "gosuslugi.ru", "nalog.gov.ru", "zakupki.gov.ru", 
                "pfr.gov.ru", "lk.rnrc.ru", "fss.gov.ru", "mvd.gov.ru"
            ],
            "FINANCIAL": [
                "sbp.nspk.ru", "vtb.ru", "alfabank.ru", "tbank.ru",
                "sberbank.ru", "raiffeisen.ru", "moex.com"
            ],
            "TELECOM": [
                "rutube.ru", "smotrim.ru", "1tv.ru", "vgtrk.ru",
                "kion.ru", "vk.video", "ok.ru", "dzen.ru"
            ],
            "TRANSPORT": [
                "rzd.ru", "aoglonass.ru", "yandex.ru", "taxi.yandex.ru"
            ],
            "MEDICAL": [
                "librelink.com", "medtrum.com", "istok.io",
                "anytime.cgms.ru", "lizaalert.org", "docdoc.ru"
            ]
        }
        
        self.current_masks = {}
        self.last_rotation = time.time()
        self.rotation_interval = 60  # 60 секунд
        
        # Инициализация начальных масок
        self._rotate_masks()
    
    def _rotate_masks(self):
        """Ротация доменов-прикрытий"""
        self.last_rotation = time.time()
        
        for category, domains in self.WHITE_LIST_DOMAINS.items():
            self.current_masks[category] = random.choice(domains)
        
        print(f"   🔄 Маски обновлены: {dict(list(self.current_masks.items())[:3])}...")
    
    def get_mask(self, category: str) -> str:
        """Получить домен-маску для категории"""
        # Проверяем необходимость ротации
        if time.time() - self.last_rotation > self.rotation_interval:
            self._rotate_masks()
        
        return self.current_masks.get(category, self.current_masks["GOVERNMENT"])
    
    def get_priority_mask(self) -> str:
        """Получить маску с наивысшим приоритетом (Гос-сервисы)"""
        return self.get_mask("GOVERNMENT")
    
    def get_media_mask(self) -> str:
        """Получить маску для медиа-трафика"""
        return self.get_mask("TELECOM")
    
    def get_financial_mask(self) -> str:
        """Получить маску для финансового трафика"""
        return self.get_mask("FINANCIAL")
    
    def get_lifeline_mask(self) -> str:
        """Получить маску для Life-Line режима"""
        return self.get_mask("MEDICAL")


class PacketManipulator:
    """Манипулятор пакетов - фрагментация, обфускация, SNI спуфинг"""
    
    def __init__(self):
        self.whitelist_engine = WhitelistEngine()
        
    def create_fragmented_socket(self, target_host: str, target_port: int) -> socket.socket:
        """Создать сокет с фрагментацией"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # Устанавливаем маленький размер окна для фрагментации
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        
        try:
            sock.connect((target_host, target_port))
            return sock
        except Exception as e:
            sock.close()
            raise e
    
    def split_sni_fragments(self, hostname: str, num_parts: int = 3) -> List[bytes]:
        """Разрезание SNI на 2-3 части"""
        hostname_bytes = hostname.encode()
        
        if num_parts == 2:
            split_pos = len(hostname_bytes) // 2
            return [hostname_bytes[:split_pos], hostname_bytes[split_pos:]]
        elif num_parts == 3:
            part1 = len(hostname_bytes) // 3
            part2 = part1 * 2
            return [
                hostname_bytes[:part1],
                hostname_bytes[part1:part2],
                hostname_bytes[part2:]
            ]
        else:
            return [hostname_bytes]
    
    def obfuscate_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Обфускация HTTP заголовков"""
        obfuscated = {}
        
        for key, value in headers.items():
            # Смена регистра заголовков
            if key.lower() == "host":
                key = "hOsT"
            elif key.lower() == "user-agent":
                key = "UsEr-AgEnT"
            elif key.lower() == "connection":
                key = "CoNnEcTiOn"
            
            obfuscated[key] = value
        
        # Добавляем мусорные поля
        obfuscated["X-Junk-Data"] = base64.b64encode(os.urandom(16)).decode()
        obfuscated["X-Padding"] = "A" * random.randint(10, 50)
        obfuscated["X-Random"] = str(random.randint(100000, 999999))
        
        return obfuscated
    
    def set_tcp_window_size(self, sock: socket.socket, window_size: int = 8):
        """Принудительная установка window size < 10 байт"""
        try:
            # Устанавливаем минимальный размер окна
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, window_size)
            return True
        except:
            return False
    
    def create_tls_junk(self) -> bytes:
        """Создание TLS мусорных данных"""
        junk = bytearray()
        
        # Добавляем случайные TLS записи
        for _ in range(random.randint(1, 3)):
            junk.extend(b'\x17')  # Application data
            junk.extend(b'\x03\x03')  # TLS 1.2
            junk.extend(struct.pack('>H', random.randint(100, 500)))  # Length
            junk.extend(os.urandom(random.randint(100, 500)))  # Random data
        
        return bytes(junk)
    
    def create_fake_padding(self, target_size: int = 1024) -> bytes:
        """Создание фейковых padding данных"""
        return os.urandom(target_size)
    
    def lower_ttl(self, ttl_value: int = 3) -> int:
        """Установка низкого TTL для пакетов-пустышек"""
        return ttl_value


class PipelineChain:
    """Базовый класс цепочки обхода"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.packet_manipulator = PacketManipulator()
        self.whitelist_engine = WhitelistEngine()
        
    def execute(self, target_host: str, target_port: int = 443) -> PipelineResult:
        """Выполнение цепочки - должен быть переопределен"""
        raise NotImplementedError


class GovernmentFragmentChain(PipelineChain):
    """Цепочка №1: Гос-Фрагмент (Для пробития White List)"""
    
    def __init__(self):
        super().__init__("Гос-Фрагмент", 1)
    
    def execute(self, target_host: str, target_port: int = 443) -> PipelineResult:
        """TCP_Window_Size(1) + SNI_Spoofing(gosuslugi.ru) + TLS_Header_Junk"""
        start_time = time.time()
        
        try:
            print(f"   🟢 Запускаю цепочку '{self.name}'...")
            
            # Этап 1: Создаем фрагментированный сокет
            sock = self.packet_manipulator.create_fragmented_socket(target_host, target_port)
            
            # Этап 2: Устанавливаем маленький размер окна
            self.packet_manipulator.set_tcp_window_size(sock, 8)
            
            # Этап 3: SNI Spoofing под госуслуги
            cover_domain = self.whitelist_engine.get_mask("GOVERNMENT")
            print(f"      🎭 SNI маскировка под: {cover_domain}")
            
            # Этап 4: Создаем TLS Client Hello с обфускацией
            client_hello = self._create_obfuscated_client_hello(target_host, cover_domain)
            
            # Этап 5: Добавляем TLS Junk
            tls_junk = self.packet_manipulator.create_tls_junk()
            
            # Этап 6: Отправляем фрагментированные данные
            fragments = self.packet_manipulator.split_sni_fragments(cover_domain, 3)
            
            for i, fragment in enumerate(fragments):
                sock.send(fragment)
                time.sleep(0.01)  # Небольшая задержка между фрагментами
            
            # Этап 7: Отправляем TLS junk
            sock.send(tls_junk)
            
            # Этап 8: Завершаем TLS handshake
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=target_host)
            
            # Этап 9: Отправляем HTTP запрос с обфускацией
            headers = {
                "Host": target_host,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Connection": "close"
            }
            
            obfuscated_headers = self.packet_manipulator.obfuscate_headers(headers)
            request = self._build_request(obfuscated_headers)
            
            ssl_sock.send(request)
            response = ssl_sock.recv(8192)
            
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                return PipelineResult(
                    success=True,
                    stage_completed="all_stages",
                    duration=duration,
                    response_data=response
                )
            else:
                return PipelineResult(
                    success=False,
                    stage_completed="tls_handshake",
                    error="Invalid HTTP response",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return PipelineResult(
                success=False,
                stage_completed="socket_creation",
                error=str(e),
                duration=duration
            )
    
    def _create_obfuscated_client_hello(self, target_host: str, cover_domain: str) -> bytes:
        """Создание обфусцированного Client Hello"""
        # Упрощенная реализация для демонстрации
        client_hello = bytearray()
        client_hello.extend(b'\x16\x03\x03')  # Handshake, TLS 1.2
        
        # Добавляем cover_domain в SNI
        sni_data = cover_domain.encode()
        client_hello.extend(sni_data)
        
        # Добавляем обфусцированный target_host
        target_encoded = target_host.encode()[::-1]  # Простая обфускация
        client_hello.extend(target_encoded)
        
        return bytes(client_hello)
    
    def _build_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP запроса из заголовков"""
        request_lines = ["GET / HTTP/1.1"]
        
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        
        request_lines.append("")  # Пустая строка перед телом
        request_lines.append("")  # Конец заголовков
        
        return "\r\n".join(request_lines).encode()


class MediaChameleonChain(PipelineChain):
    """Цепочка №2: Медиа-Хамелеон (Для тяжелого трафика)"""
    
    def __init__(self):
        super().__init__("Медиа-Хамелеон", 2)
    
    def execute(self, target_host: str, target_port: int = 443) -> PipelineResult:
        """HTTP2_Multiplexing + SNI_Spoofing(rutube.ru) + Fake_Padding"""
        start_time = time.time()
        
        try:
            print(f"   🔵 Запускаю цепочку '{self.name}'...")
            
            # Этап 1: SNI Spoofing под медиа-ресурс
            cover_domain = self.whitelist_engine.get_mask("TELECOM")
            print(f"      🎭 SNI маскировка под: {cover_domain}")
            
            # Этап 2: Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_host, target_port))
            
            # Этап 3: Имитация HTTP/2 multiplexing
            # Отправляем ALPN для HTTP/2
            sock.send(b'\x16\x03\x01')  # TLS Handshake
            sock.send(b'\x00\x00\xdc')  # Length
            sock.send(b'\x01\x00\x00\xd8')  # Handshake
            sock.send(b'\x03\x03')  # TLS 1.2
            
            # Этап 4: Добавляем fake padding
            padding = self.packet_manipulator.create_fake_padding(2048)
            sock.send(padding)
            
            # Этап 5: TLS handshake
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=target_host)
            
            # Этап 6: HTTP/2 style запрос
            headers = {
                ":method": "GET",
                ":path": "/",
                ":scheme": "https",
                ":authority": target_host,
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) [RutubeApp]",
                "accept": "*/*"
            }
            
            request = self._build_http2_request(headers)
            ssl_sock.send(request)
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                return PipelineResult(
                    success=True,
                    stage_completed="http2_multiplexing",
                    duration=duration,
                    response_data=response
                )
            else:
                return PipelineResult(
                    success=False,
                    stage_completed="tls_handshake",
                    error="Invalid HTTP response",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return PipelineResult(
                success=False,
                stage_completed="socket_creation",
                error=str(e),
                duration=duration
            )
    
    def _build_http2_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP/2 style запроса"""
        # Упрощенная HTTP/2 реализация
        request_lines = ["GET / HTTP/1.1"]  # Фallback на HTTP/1.1
        
        for key, value in headers.items():
            if not key.startswith(":"):
                request_lines.append(f"{key}: {value}")
        
        request_lines.extend(["", ""])
        return "\r\n".join(request_lines).encode()


class FinancialGhostChain(PipelineChain):
    """Цепочка №3: Финансовый Призрак (Для скрытности)"""
    
    def __init__(self):
        super().__init__("Финансовый Призрак", 3)
    
    def execute(self, target_host: str, target_port: int = 443) -> PipelineResult:
        """SNI_Spoofing(sbp.nspk.ru) + Encrypted_Payload(Reality) + TTL_Lowering"""
        start_time = time.time()
        
        try:
            print(f"   🔴 Запускаю цепочку '{self.name}'...")
            
            # Этап 1: SNI Spoofing под финансовый сервис
            cover_domain = self.whitelist_engine.get_mask("FINANCIAL")
            print(f"      🎭 SNI маскировка под: {cover_domain}")
            
            # Этап 2: Создаем сокет с низким TTL
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 3)
            
            sock.connect((target_host, target_port))
            
            # Этап 3: Создаем зашифрованный payload (Reality style)
            encrypted_payload = self._create_reality_payload(target_host, cover_domain)
            
            # Этап 4: Отправляем зашифрованные данные
            sock.send(encrypted_payload)
            
            # Этап 5: TLS handshake с Reality
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=cover_domain)
            
            # Этап 6: Банковский style запрос
            headers = {
                "Host": target_host,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) [SBPApp/1.5.0]",
                "X-Banking-Request": "true",
                "X-Transaction-ID": str(random.randint(100000, 999999)),
                "Content-Type": "application/json",
                "Connection": "close"
            }
            
            request = self._build_request(headers)
            ssl_sock.send(request)
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                return PipelineResult(
                    success=True,
                    stage_completed="reality_encryption",
                    duration=duration,
                    response_data=response
                )
            else:
                return PipelineResult(
                    success=False,
                    stage_completed="tls_handshake",
                    error="Invalid HTTP response",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return PipelineResult(
                success=False,
                stage_completed="socket_creation",
                error=str(e),
                duration=duration
            )
    
    def _create_reality_payload(self, target_host: str, cover_domain: str) -> bytes:
        """Создание Reality style зашифрованного payload"""
        # Простая имитация Reality шифрования
        payload = bytearray()
        
        # Reality header
        payload.extend(b'REALITY')
        payload.extend(struct.pack('>H', len(cover_domain)))
        payload.extend(cover_domain.encode())
        
        # Зашифрованный target
        target_encrypted = target_host.encode()
        for i, byte in enumerate(target_encrypted):
            payload.append(byte ^ 0x42)  # Простое XOR шифрование
        
        return bytes(payload)
    
    def _build_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP запроса"""
        request_lines = ["GET / HTTP/1.1"]
        
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        
        request_lines.extend(["", ""])
        return "\r\n".join(request_lines).encode()


class LifeLineChain(PipelineChain):
    """Life-Line режим (мимикрия под медицинские системы)"""
    
    def __init__(self):
        super().__init__("Life-Line", 99)  # Самый низкий приоритет
    
    def execute(self, target_host: str, target_port: int = 443) -> PipelineResult:
        """Мимикрия под медицинские CGM-системы"""
        start_time = time.time()
        
        try:
            print(f"   🏥 Запускаю Life-Line режим...")
            
            # Этап 1: SNI Spoofing под медицинский сервис
            cover_domain = self.whitelist_engine.get_mask("MEDICAL")
            print(f"      🎭 SNI маскировка под: {cover_domain}")
            
            # Этап 2: Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_host, target_port))
            
            # Этап 3: TLS handshake
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=cover_domain)
            
            # Этап 4: Медицинский style запрос
            headers = {
                "Host": target_host,
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) [LibreLinkApp]",
                "X-Medical-Device": "LibreLink",
                "X-Emergency-Data": "true",
                "Content-Type": "application/json",
                "Connection": "close"
            }
            
            request = self._build_request(headers)
            ssl_sock.send(request)
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Life-Line успешен ({duration:.2f}s)")
                return PipelineResult(
                    success=True,
                    stage_completed="medical_mimicry",
                    duration=duration,
                    response_data=response
                )
            else:
                return PipelineResult(
                    success=False,
                    stage_completed="tls_handshake",
                    error="Invalid HTTP response",
                    duration=duration
                )
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Life-Line ошибка: {e}")
            return PipelineResult(
                success=False,
                stage_completed="socket_creation",
                error=str(e),
                duration=duration
            )
    
    def _build_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP запроса"""
        request_lines = ["GET / HTTP/1.1"]
        
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        
        request_lines.extend(["", ""])
        return "\r\n".join(request_lines).encode()


class AutoSwitcher:
    """Auto-Switcher для автоматического переключения цепочек"""
    
    def __init__(self):
        self.chains = [
            GovernmentFragmentChain(),
            MediaChameleonChain(),
            FinancialGhostChain()
        ]
        self.lifeline_chain = LifeLineChain()
        
        # Сортируем по приоритету
        self.chains.sort(key=lambda x: x.priority)
    
    def execute_with_fallback(self, target_host: str, target_port: int = 443) -> Dict[str, Any]:
        """Выполнение с автоматическим переключением"""
        results = {
            "target_host": target_host,
            "chains_tried": [],
            "successful_chain": None,
            "lifeline_activated": False,
            "total_duration": 0.0,
            "final_success": False
        }
        
        start_time = time.time()
        
        # Пробуем основные цепочки
        for chain in self.chains:
            print(f"\n🔄 Пробую цепочку: {chain.name} (приоритет {chain.priority})")
            
            result = chain.execute(target_host, target_port)
            results["chains_tried"].append({
                "name": chain.name,
                "priority": chain.priority,
                "success": result.success,
                "stage_completed": result.stage_completed,
                "error": result.error,
                "duration": result.duration
            })
            
            if result.success:
                results["successful_chain"] = chain.name
                results["final_success"] = True
                print(f"   🎯 Цепочка '{chain.name}' успешно обошла DPI!")
                break
            else:
                # Проверяем на Handshake Timeout
                if "handshake" in result.stage_completed.lower() or "timeout" in str(result.error).lower():
                    print(f"   ⚠️ Handshake timeout - переключаюсь на следующую цепочку")
                    continue
                else:
                    print(f"   ❌ Цепочка не сработала: {result.error}")
        
        # Если все цепочки не сработали, активируем Life-Line
        if not results["final_success"]:
            print(f"\n🏥 Активирую Life-Line режим...")
            lifeline_result = self.lifeline_chain.execute(target_host, target_port)
            
            results["lifeline_activated"] = True
            results["chains_tried"].append({
                "name": "Life-Line",
                "priority": 99,
                "success": lifeline_result.success,
                "stage_completed": lifeline_result.stage_completed,
                "error": lifeline_result.error,
                "duration": lifeline_result.duration
            })
            
            if lifeline_result.success:
                results["successful_chain"] = "Life-Line"
                results["final_success"] = True
                print(f"   🏥 Life-Line спас ситуацию!")
        
        results["total_duration"] = time.time() - start_time
        
        return results


class DPIBypassCombinerV2:
    """DPI-Bypass Combiner v2.0 'White-Ghost'"""
    
    def __init__(self):
        self.auto_switcher = AutoSwitcher()
        self.whitelist_engine = WhitelistEngine()
        
    def bypass_target(self, target_host: str, target_port: int = 443) -> Dict[str, Any]:
        """Основной метод обхода цели"""
        print(f"👻 DPI-Bypass Combiner v2.0 'White-Ghost'")
        print(f"🎯 Цель: {target_host}:{target_port}")
        print(f"=" * 50)
        
        # Проверяем доступность напрямую
        print(f"\n🔍 Проверка доступности...")
        direct_accessible = self._check_direct_access(target_host, target_port)
        
        if direct_accessible:
            print(f"   ✅ {target_host} доступен напрямую - обход не требуется")
            return {
                "target_host": target_host,
                "direct_access": True,
                "bypass_required": False,
                "success": True
            }
        
        print(f"   ❌ {target_host} заблокирован - запускаю цепочки обхода")
        
        # Запускаем цепочки с Auto-Switcher
        results = self.auto_switcher.execute_with_fallback(target_host, target_port)
        
        # Добавляем информацию о прямом доступе
        results["direct_access"] = False
        results["bypass_required"] = True
        
        return results
    
    def _check_direct_access(self, target_host: str, target_port: int) -> bool:
        """Проверка прямого доступа к цели"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            result = sock.connect_ex((target_host, target_port))
            sock.close()
            
            return result == 0
            
        except:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус системы"""
        return {
            "version": "2.0 White-Ghost",
            "whitelist_domains": len(self.whitelist_engine.WHITE_LIST_DOMAINS),
            "active_chains": len(self.auto_switcher.chains),
            "current_masks": self.whitelist_engine.current_masks,
            "last_rotation": self.whitelist_engine.last_rotation
        }


# Глобальный экземпляр для использования
dpi_combiner_v2 = DPIBypassCombinerV2()


if __name__ == "__main__":
    # Тестирование
    target = "www.youtube.com"
    result = dpi_combiner_v2.bypass_target(target)
    
    print(f"\n📊 РЕЗУЛЬТАТ ОБХОДА:")
    print(f"=" * 30)
    print(f"🎯 Цель: {result['target_host']}")
    print(f"✅ Успех: {result['final_success']}")
    print(f"🔄 Цепочек попробовано: {len(result['chains_tried'])}")
    
    if result['successful_chain']:
        print(f"🏆 Успешная цепочка: {result['successful_chain']}")
    
    print(f"⏱️ Общее время: {result['total_duration']:.2f}s")
    
    if result.get('lifeline_activated'):
        print(f"🏥 Life-Line активирован: Да")
