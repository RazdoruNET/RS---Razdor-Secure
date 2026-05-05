#!/usr/bin/env python3
"""
Расширенные пайплайны для обхода DPI
Продвинутые техники для сложных случаев блокировки
"""

import socket
import ssl
import time
import random
import struct
import hashlib
from typing import Dict, Any

class TLSFragmentationPipeline:
    """Пайплайн с фрагментацией TLS handshake"""
    
    def __init__(self):
        self.name = "TLS-Фрагментация"
        self.priority = 4
    
    def execute(self, target_host: str) -> Dict[str, Any]:
        """Фрагментация TLS Client Hello для обхода DPI"""
        start_time = time.time()
        
        try:
            print(f"   ⛓️ Запускаю цепочку '{self.name}'...")
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            sock.connect((target_host, 443))
            
            # Этап 1: Отправляем фрагментированный Client Hello
            client_hello = self._build_fragmented_client_hello(target_host)
            
            # Разбиваем на мелкие фрагменты
            fragment_size = 100  # Очень маленькие фрагменты
            for i in range(0, len(client_hello), fragment_size):
                fragment = client_hello[i:i + fragment_size]
                sock.send(fragment)
                time.sleep(0.001)  # Небольшая задержка между фрагментами
            
            # Получаем Server Hello
            response = sock.recv(4096)
            
            # Завершаем handshake
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=target_host)
            
            # Тестовый запрос
            request = f"GET / HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n"
            ssl_sock.send(request.encode())
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                return {
                    "success": True,
                    "pipeline": self.name,
                    "duration": duration,
                    "response": response.decode('utf-8', errors='ignore')[:200]
                }
            else:
                return {
                    "success": False,
                    "pipeline": self.name,
                    "error": "Invalid HTTP response",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return {
                "success": False,
                "pipeline": self.name,
                "error": str(e),
                "duration": duration
            }
    
    def _build_fragmented_client_hello(self, hostname: str) -> bytes:
        """Создание фрагментированного TLS Client Hello"""
        # Упрощенный Client Hello с фрагментацией
        record_header = b"\x16\x03\x01"  # Handshake, TLS 1.0
        handshake_header = b"\x01\x00\x00\x00"  # Client Hello
        
        # Сессия ID
        session_id = b"\x00"
        
        # Cipher suites
        cipher_suites = b"\x00\x02\x00\x2f"  # TLS_RSA_WITH_AES_128_CBC_SHA
        
        # Compression methods
        compression = b"\x01\x00"
        
        # Extensions
        extensions = self._build_extensions(hostname)
        
        # Собираем Client Hello
        client_hello = (
            handshake_header +
            b"\x03\x03" +  # TLS 1.2
            struct.pack(">I", int(time.time()))[1:] +  # Random (4 байта)
            b"\x00" * 28 +  # Random (28 байт)
            session_id +
            cipher_suites +
            compression +
            extensions
        )
        
        # Обновляем длину handshake
        client_hello = b"\x01" + struct.pack(">I", len(client_hello))[1:] + client_hello[5:]
        
        # Обновляем длину record
        record = record_header + struct.pack(">H", len(client_hello)) + client_hello
        
        return record
    
    def _build_extensions(self, hostname: str) -> bytes:
        """Построение расширений TLS"""
        extensions = []
        
        # SNI extension
        sni = b"\x00\x00"  # SNI type
        sni += struct.pack(">H", len(hostname) + 5)  # Length
        sni += struct.pack(">H", len(hostname) + 3)  # Server name list length
        sni += b"\x00"  # Name type: hostname
        sni += struct.pack(">H", len(hostname))  # Hostname length
        sni += hostname.encode()
        
        extensions.append(sni)
        
        # Supported groups
        groups = b"\x00\x0a"  # Supported groups
        groups += struct.pack(">H", 4)  # Length
        groups += struct.pack(">H", 2)  # Groups length
        groups += b"\x00\x1d"  # X25519
        
        extensions.append(groups)
        
        # EC point formats
        ec_formats = b"\x00\x0b"  # EC point formats
        ec_formats += struct.pack(">H", 2)  # Length
        ec_formats += b"\x01\x00"  # Uncompressed
        
        extensions.append(ec_formats)
        
        # Собираем все расширения
        all_extensions = b"".join(extensions)
        return struct.pack(">H", len(all_extensions)) + all_extensions

class MobileUserAgentPipeline:
    """Пайплайн с мобильными User-Agent и заголовками"""
    
    def __init__(self):
        self.name = "Мобильный-Маскарад"
        self.priority = 5
    
    def execute(self, target_host: str) -> Dict[str, Any]:
        """Имитация мобильного устройства"""
        start_time = time.time()
        
        try:
            print(f"   ⛓️ Запускаю цепочку '{self.name}'...")
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Мобильные настройки
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 512)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512)
            
            sock.connect((target_host, 443))
            
            # TLS с мобильным SNI
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            mobile_sni = f"m.{target_host}"
            ssl_sock = context.wrap_socket(sock, server_hostname=mobile_sni)
            
            # Мобильные заголовки
            mobile_user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Instagram 250.1.0.23.113 Mobile/15E148",
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36"
            ]
            
            headers = {
                "Host": target_host,
                "User-Agent": random.choice(mobile_user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "Connection": "close",
                "X-Mobile-Request": "true",
                "X-App-Version": "16.6.0",
                "X-Device-Platform": "iOS" if "iPhone" in mobile_user_agents[0] else "Android"
            }
            
            request = self._build_request(headers)
            ssl_sock.send(request)
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                return {
                    "success": True,
                    "pipeline": self.name,
                    "duration": duration,
                    "response": response.decode('utf-8', errors='ignore')[:200]
                }
            else:
                return {
                    "success": False,
                    "pipeline": self.name,
                    "error": "Invalid HTTP response",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return {
                "success": False,
                "pipeline": self.name,
                "error": str(e),
                "duration": duration
            }
    
    def _build_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP запроса"""
        request_lines = ["GET / HTTP/1.1"]
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        request_lines.extend(["", ""])
        return "\r\n".join(request_lines).encode()

class DomainFrontingPipeline:
    """Пайплайн с Domain Fronting техникой"""
    
    def __init__(self):
        self.name = "Domain-Fronting"
        self.priority = 6
    
    def execute(self, target_host: str) -> Dict[str, Any]:
        """Domain Fronting через CDN"""
        start_time = time.time()
        
        try:
            print(f"   ⛓️ Запускаю цепочку '{self.name}'...")
            
            # CDN домены для fronting
            cdn_domains = [
                "cloudflare.com",
                "googleusercontent.com", 
                "amazonaws.com",
                "azureedge.net",
                "fastly.net"
            ]
            
            # Пробуем разные CDN
            for cdn_domain in cdn_domains:
                try:
                    # Создаем сокет
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    
                    # Подключаемся к CDN
                    sock.connect((cdn_domain, 443))
                    
                    # TLS с CDN доменом
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    ssl_sock = context.wrap_socket(sock, server_hostname=cdn_domain)
                    
                    # HTTP заголовки с domain fronting
                    headers = {
                        "Host": target_host,  # Реальный хост в заголовке
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "*/*",
                        "X-Forwarded-Host": target_host,
                        "X-Original-Host": target_host,
                        "X-CDN-Forwarding": "true",
                        "Connection": "close"
                    }
                    
                    request = self._build_request(headers)
                    ssl_sock.send(request)
                    
                    response = ssl_sock.recv(8192)
                    ssl_sock.close()
                    
                    if b"HTTP" in response:
                        duration = time.time() - start_time
                        print(f"   ✅ Цепочка '{self.name}' успешна через {cdn_domain} ({duration:.2f}s)")
                        return {
                            "success": True,
                            "pipeline": self.name,
                            "cdn_domain": cdn_domain,
                            "duration": duration,
                            "response": response.decode('utf-8', errors='ignore')[:200]
                        }
                        
                except Exception as e:
                    print(f"      ❌ CDN {cdn_domain} не сработал: {e}")
                    continue
            
            # Если ни один CDN не сработал
            duration = time.time() - start_time
            return {
                "success": False,
                "pipeline": self.name,
                "error": "All CDN domains failed",
                "duration": duration
            }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return {
                "success": False,
                "pipeline": self.name,
                "error": str(e),
                "duration": duration
            }
    
    def _build_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP запроса"""
        request_lines = ["GET / HTTP/1.1"]
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        request_lines.extend(["", ""])
        return "\r\n".join(request_lines).encode()

class RandomPaddingPipeline:
    """Пайплайн со случайным паддингом"""
    
    def __init__(self):
        self.name = "Random-Padding"
        self.priority = 7
    
    def execute(self, target_host: str) -> Dict[str, Any]:
        """Добавление случайного паддинга к запросам"""
        start_time = time.time()
        
        try:
            print(f"   ⛓️ Запускаю цепочку '{self.name}'...")
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Случайные размеры буферов
            recv_buf = random.randint(256, 2048)
            send_buf = random.randint(256, 2048)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, recv_buf)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_buf)
            
            sock.connect((target_host, 443))
            
            # TLS
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=target_host)
            
            # HTTP запрос с паддингом
            headers = {
                "Host": target_host,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Connection": "close"
            }
            
            request = self._build_padded_request(headers)
            ssl_sock.send(request)
            
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            duration = time.time() - start_time
            
            if b"HTTP" in response:
                print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                return {
                    "success": True,
                    "pipeline": self.name,
                    "duration": duration,
                    "response": response.decode('utf-8', errors='ignore')[:200]
                }
            else:
                return {
                    "success": False,
                    "pipeline": self.name,
                    "error": "Invalid HTTP response",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return {
                "success": False,
                "pipeline": self.name,
                "error": str(e),
                "duration": duration
            }
    
    def _build_padded_request(self, headers: Dict[str, str]) -> bytes:
        """Построение HTTP запроса с паддингом"""
        request_lines = ["GET / HTTP/1.1"]
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        
        # Добавляем случайные заголовки для паддинга
        padding_headers = [
            f"X-Padding-{random.randint(1000, 9999)}: {'A' * random.randint(10, 50)}",
            f"X-Random-{random.randint(1000, 9999)}: {'B' * random.randint(5, 30)}",
            f"X-Noise-{random.randint(1000, 9999)}: {'C' * random.randint(15, 40)}"
        ]
        
        # Добавляем 1-3 случайных заголовка
        for header in random.sample(padding_headers, random.randint(1, 3)):
            request_lines.append(header)
        
        request_lines.extend(["", ""])
        return "\r\n".join(request_lines).encode()

class QUICFallbackPipeline:
    """Пайплайн с QUIC fallback"""
    
    def __init__(self):
        self.name = "QUIC-Fallback"
        self.priority = 8
    
    def execute(self, target_host: str) -> Dict[str, Any]:
        """Попытка подключения через QUIC/UDP"""
        start_time = time.time()
        
        try:
            print(f"   ⛓️ Запускаю цепочку '{self.name}'...")
            
            # Создаем UDP сокет для QUIC
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10)
            
            # Отправляем QUIC Initial packet
            quic_packet = self._build_quic_initial(target_host)
            sock.sendto(quic_packet, (target_host, 443))
            
            # Получаем ответ
            try:
                response, addr = sock.recvfrom(8192)
                sock.close()
                
                duration = time.time() - start_time
                
                # Проверяем QUIC response
                if len(response) > 0:
                    print(f"   ✅ Цепочка '{self.name}' успешна ({duration:.2f}s)")
                    return {
                        "success": True,
                        "pipeline": self.name,
                        "duration": duration,
                        "response": f"QUIC Response: {len(response)} bytes"
                    }
                else:
                    return {
                        "success": False,
                        "pipeline": self.name,
                        "error": "Empty QUIC response",
                        "duration": duration
                    }
                    
            except socket.timeout:
                sock.close()
                duration = time.time() - start_time
                return {
                    "success": False,
                    "pipeline": self.name,
                    "error": "QUIC timeout",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Цепочка '{self.name}' ошибка: {e}")
            return {
                "success": False,
                "pipeline": self.name,
                "error": str(e),
                "duration": duration
            }
    
    def _build_quic_initial(self, hostname: str) -> bytes:
        """Построение QUIC Initial packet"""
        # Упрощенный QUIC Initial packet
        header = b"\x80"  # Long header
        header += b"\x00"  # Fixed bit
        header += b"\x00\x00\x00\x01"  # Version
        header += b"\x00\x00\x00\x00\x00\x00\x00\x01"  # Destination CID
        header += b"\x00\x00\x00\x00\x00\x00\x00\x02"  # Source CID
        
        # Token length
        header += b"\x00"
        
        # Length (упрощено)
        header += b"\x00\x40"
        
        # Crypto frame (упрощено)
        crypto_frame = b"\x06\x00\x00\x00\x00"
        crypto_frame += b"\x00\x00\x00\x00\x00\x00\x00\x00"
        crypto_frame += b"\x00\x00\x00\x00\x00\x00\x00\x00"
        
        return header + crypto_frame
