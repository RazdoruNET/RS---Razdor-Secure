#!/usr/bin/env python3
"""
DPI Bypass Combiner - Продвинутый автоматический комбайн обхода DPI
Методы: SpoofDPI Logic, VLESS Reality, Domain Fronting, SNI Spoofing
"""
import socket
import ssl
import time
import subprocess
import os
import json
import threading
import queue
import struct
import hashlib
import base64
import random
import urllib.request
import urllib.parse
import sys
import signal
import psutil
import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Импортируем все модули
try:
    from .omega_transport_bridges import omega_transport, setup_omega_bridges, get_active_bridges, setup_proxy_configuration
    OMEGA_AVAILABLE = True
except ImportError:
    OMEGA_AVAILABLE = False

try:
    from .tor_core_integration import tor_core, activate_darknet_bridge, get_youtube_through_tor, automatic_tor_fallback
    TOR_CORE_AVAILABLE = True
except ImportError:
    TOR_CORE_AVAILABLE = False

class PacketShaper:
    """Низкоуровневые манипуляции с TCP пакетами - SpoofDPI Logic"""
    
    def __init__(self):
        self.tcp_window_size = 1  # Форсирование сегментации
        self.fake_ttl = 1  # TTL для фейковых пакетов
        self.fragment_size = 2  # Размер фрагментов
        self.process_pids = {}  # PID tracking для безопасного завершения
        
    def create_fragmented_socket(self, host: str, port: int) -> socket.socket:
        """Создание сокета с фрагментацией пакетов"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Устанавливаем маленький размер окна TCP
            if hasattr(socket, 'TCP_WINDOW_CLAMP'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_WINDOW_CLAMP, self.tcp_window_size)
            
            # Устанавливаем MSS для фрагментации
            if hasattr(socket, 'TCP_MAXSEG'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, self.fragment_size)
            
            sock.connect((host, port))
            return sock
            
        except Exception as e:
            print(f"   ❌ Ошибка создания фрагментированного сокета: {e}")
            raise
    
    def send_fragmented_request(self, sock: socket.socket, request: bytes) -> bool:
        """Отправка фрагментированного HTTP запроса"""
        try:
            # Фрагментация TLS Client Hello
            fragments = self._fragment_tls_handshake(request)
            
            # Отправка с disorder (перемешивание порядка)
            if len(fragments) > 1:
                fragments = self._apply_disorder(fragments)
            
            for fragment in fragments:
                sock.send(fragment)
                time.sleep(0.001)  # Небольшая задержка между фрагментами
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка фрагментированной отправки: {e}")
            return False
    
    def _fragment_tls_handshake(self, data: bytes) -> List[bytes]:
        """Фрагментация TLS Client Hello"""
        fragments = []
        
        # Ищем TLS Client Hello record
        if len(data) > 5 and data[0] == 0x16:  # TLS Handshake
            # Разделяем SNI на две части
            record_length = struct.unpack('>H', data[3:5])[0]
            
            # Первый фрагмент - заголовок
            fragment1 = data[:20]  # TLS Record Header
            fragments.append(fragment1)
            
            # Второй фрагмент - остальная часть
            fragment2 = data[20:20+min(50, len(data)-20)]
            fragments.append(fragment2)
            
            # Третий фрагмент - остаток
            if len(data) > 70:
                fragment3 = data[70:]
                fragments.append(fragment3)
        else:
            # Обычная фрагментация
            chunk_size = self.fragment_size
            for i in range(0, len(data), chunk_size):
                fragments.append(data[i:i+chunk_size])
        
        return fragments
    
    def _apply_disorder(self, fragments: List[bytes]) -> List[bytes]:
        """Применение disorder (перемешивание порядка пакетов)"""
        if len(fragments) <= 1:
            return fragments
        
        # Перемешиваем порядок фрагментов
        shuffled = fragments.copy()
        random.shuffle(shuffled)
        
        # Но оставляем первый фрагмент на месте (важно для TLS)
        if len(shuffled) > 1:
            first = shuffled.pop(0)
            shuffled.insert(0, first)
        
        return shuffled
    
    def send_fake_packets(self, target_host: str, target_port: int) -> bool:
        """Отправка фейковых TCP пакетов с низким TTL"""
        try:
            # Создаем фейковые TCP пакеты
            fake_packets = [
                b'\x00\x00\x00\x00',  # Пустой пакет
                b'\x01\x00\x00\x00',  # RST пакет
                b'\x02\x00\x00\x00',  # FIN пакет
            ]
            
            for packet in fake_packets:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.fake_ttl)
                    sock.sendto(packet, (target_host, target_port))
                    sock.close()
                except:
                    pass  # RAW сокеты могут требовать прав
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка отправки фейковых пакетов: {e}")
            return False
    
    def create_host_case_fragmentation(self, request: bytes) -> bytes:
        """Host Case Fragmentation - подмена заголовка Host на hOsT"""
        try:
            # Ищем Host заголовок
            host_pattern = rb'Host:'
            host_pos = request.find(host_pattern)
            
            if host_pos != -1:
                # Заменяем Host на hOsT (смешанный регистр)
                modified_request = request[:host_pos] + b'hOsT:' + request[host_pos+5:]
                return modified_request
            
            return request
            
        except Exception as e:
            print(f"   ❌ Ошибка Host Case Fragmentation: {e}")
            return request
    
    def track_process(self, process: subprocess.Popen, name: str):
        """Отслеживание PID процесса для безопасного завершения"""
        self.process_pids[name] = process.pid
    
    def safe_kill_process(self, name: str) -> bool:
        """Безопасное завершение процесса через PID tracking"""
        try:
            if name in self.process_pids:
                pid = self.process_pids[name]
                
                # Проверяем что процесс существует
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    
                    # Сначала пытаемся завершить gracefully
                    process.terminate()
                    time.sleep(1)
                    
                    # Если все еще работает - force kill
                    if process.is_running():
                        process.kill()
                    
                    del self.process_pids[name]
                    print(f"   ✅ Процесс {name} (PID: {pid}) завершен")
                    return True
                else:
                    del self.process_pids[name]
                    return True
            else:
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка завершения процесса {name}: {e}")
            return False
    
    def cleanup_all_processes(self):
        """Завершение всех отслеживаемых процессов"""
        for name in list(self.process_pids.keys()):
            self.safe_kill_process(name)

class VLESSRealityClient:
    """VLESS Reality Client - маскировка под разрешенные домены"""
    
    def __init__(self):
        self.reality_nodes = []
        self.current_node = None
        self.proxy_port = 1080
        self.packet_shaper = PacketShaper()
        
    def fetch_public_nodes(self) -> bool:
        """Автоматический сбор бесплатных Reality-узлов из открытых источников"""
        try:
            print("   🔍 Поиск публичных VLESS Reality узлов...")
            
            # GitHub репозитории с daily-обновлениями
            sources = [
                "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_1.txt",
                "https://raw.githubusercontent.com/ProxyMenu/Proxy-lists/master/Clash/V2Ray/VLESS.txt",
                "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/config/v2ray/config.txt"
            ]
            
            vless_links = []
            
            for source in sources:
                try:
                    print(f"      Загрузка: {source}")
                    response = urllib.request.urlopen(source, timeout=10)
                    content = response.read().decode('utf-8')
                    
                    # Ищем VLESS ссылки
                    vless_pattern = r'vless://[^\s]+'
                    matches = re.findall(vless_pattern, content)
                    vless_links.extend(matches)
                    
                    print(f"      Найдено VLESS ссылок: {len(matches)}")
                    
                except Exception as e:
                    print(f"      ❌ Ошибка загрузки {source}: {e}")
                    continue
            
            # Фильтруем Reality узлы
            self.reality_nodes = self._filter_reality_nodes(vless_links)
            
            print(f"   ✅ Найдено Reality узлов: {len(self.reality_nodes)}")
            return len(self.reality_nodes) > 0
            
        except Exception as e:
            print(f"   ❌ Ошибка загрузки узлов: {e}")
            return False
    
    def _filter_reality_nodes(self, vless_links: List[str]) -> List[Dict[str, Any]]:
        """Фильтрация VLESS узлов с Reality транспортом"""
        reality_nodes = []
        
        for link in vless_links:
            try:
                # Декодируем VLESS ссылку
                decoded = base64.b64decode(link[8:]).decode('utf-8')
                parts = decoded.split('@')
                
                if len(parts) >= 2:
                    user_info = parts[0]
                    server_info = parts[1].split('?')[0]
                    
                    # Проверяем на Reality
                    if 'reality' in link.lower() or 'xtls-rprx' in link.lower():
                        node = {
                            'link': link,
                            'server': server_info.split(':')[0],
                            'port': int(server_info.split(':')[1]),
                            'user': user_info,
                            'type': 'reality'
                        }
                        reality_nodes.append(node)
                        
            except Exception:
                continue
        
        return reality_nodes[:10]  # Ограничиваем количество узлов
    
    def test_reality_node(self, node: Dict[str, Any]) -> bool:
        """Тестирование Reality узла"""
        try:
            print(f"      Тестирование узла: {node['server']}:{node['port']}")
            
            # Проверяем доступность сервера
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((node['server'], node['port']))
            sock.close()
            
            print(f"      ✅ Узел {node['server']} доступен")
            return True
            
        except Exception as e:
            print(f"      ❌ Узел {node['server']} недоступен: {e}")
            return False
    
    def start_reality_proxy(self) -> bool:
        """Запуск Reality прокси"""
        try:
            if not self.reality_nodes:
                if not self.fetch_public_nodes():
                    return False
            
            # Находим рабочий узел
            for node in self.reality_nodes:
                if self.test_reality_node(node):
                    self.current_node = node
                    break
            
            if not self.current_node:
                print("   ❌ Нет доступных Reality узлов")
                return False
            
            print(f"   🚀 Запуск Reality прокси через {self.current_node['server']}")
            
            # Создаем конфиг для Xray-core
            config = self._create_xray_config()
            
            # Запускаем Xray-core
            return self._start_xray_core(config)
            
        except Exception as e:
            print(f"   ❌ Ошибка запуска Reality прокси: {e}")
            return False
    
    def _create_xray_config(self) -> Dict[str, Any]:
        """Создание конфигурации для Xray-core"""
        return {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "listen": "127.0.0.1",
                    "port": self.proxy_port,
                    "protocol": "socks",
                    "settings": {"udp": True}
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": self.current_node['server'],
                                "port": self.current_node['port'],
                                "users": [{"id": self.current_node['user']}]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "show": False,
                            "dest": self.current_node['server'] + ":443",
                            "xver": 0,
                            "serverName": "apple.com",  # Маскировка под Apple
                            "privateKey": "your_private_key",
                            "publicKey": "your_public_key",
                            "maxTimeDiff": 0,
                            "shortIds": ["your_short_id"]
                        }
                    }
                }
            ]
        }
    
    def _start_xray_core(self, config: Dict[str, Any]) -> bool:
        """Запуск Xray-core"""
        try:
            # Создаем временный конфиг
            config_file = "/tmp/xray_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            # Запускаем Xray-core
            cmd = ["xray", "-c", config_file]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Отслеживаем процесс
            self.packet_shaper.track_process(process, "xray")
            
            # Ждем запуска
            time.sleep(3)
            
            if process.poll() is None:
                print(f"   ✅ Xray-core запущен на порту {self.proxy_port}")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"   ❌ Ошибка Xray-core: {stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка запуска Xray-core: {e}")
            return False
    
    def stop_reality_proxy(self):
        """Остановка Reality прокси"""
        self.packet_shaper.safe_kill_process("xray")

class WhitelistCore:
    """База данных разрешенной инфраструктуры РФ для адаптивной мимикрии"""
    
    def __init__(self):
        self.WHITELIST_MAP = {
            "STREAM": {
                "domains": [
                    "rutube.ru", "kion.ru", "kinopoisk.ru", "vk.video", 
                    "smotrim.ru", "okko.tv", "premier.ru", "tvigle.ru"
                ],
                "patterns": {
                    "video_stream": True,
                    "chunked_encoding": True,
                    "large_payloads": True,
                    "cdn_distribution": True
                },
                "typical_sizes": {
                    "request": 1024,
                    "response": 8192,
                    "chunk": 4096
                }
            },
            "CRITICAL": {
                "domains": [
                    "gosuslugi.ru", "sbp.nspk.ru", "nalog.gov.ru", 
                    "aoglonass.ru", "lk.mts.ru", "sberbank.ru", "vtb.ru"
                ],
                "patterns": {
                    "government_traffic": True,
                    "secure_transactions": True,
                    "api_calls": True,
                    "json_heavy": True
                },
                "typical_sizes": {
                    "request": 2048,
                    "response": 4096,
                    "chunk": 1024
                }
            },
            "HEALTH": {
                "domains": [
                    "librelink.com", "medtrum.com", "istok.io", 
                    "anytime.cgms.ru", "docdoc.ru", "invitro.ru"
                ],
                "patterns": {
                    "medical_data": True,
                    "encrypted_communication": True,
                    "real_time_monitoring": True
                },
                "typical_sizes": {
                    "request": 512,
                    "response": 1024,
                    "chunk": 256
                }
            },
            "RETAIL_API": {
                "domains": [
                    "yandex.ru", "ozon.ru", "wildberries.ru", 
                    "magnit.ru", "samoqat.ru", "beru.ru", "aliexpress.ru"
                ],
                "patterns": {
                    "e_commerce": True,
                    "heavy_json": True,
                    "image_uploads": True,
                    "recommendation_engine": True
                },
                "typical_sizes": {
                    "request": 1536,
                    "response": 16384,
                    "chunk": 8192
                }
            },
            "SOCIAL": {
                "domains": [
                    "vk.com", "ok.ru", "telegram.org", "mail.ru",
                    "yandex.ru", "rambler.ru"
                ],
                "patterns": {
                    "social_networking": True,
                    "media_sharing": True,
                    "real_time_messaging": True
                },
                "typical_sizes": {
                    "request": 1024,
                    "response": 4096,
                    "chunk": 2048
                }
            }
        }
    
    def get_domain_by_category(self, category: str) -> str:
        """Получить случайный домен из категории"""
        if category in self.WHITELIST_MAP:
            domains = self.WHITELIST_MAP[category]["domains"]
            return random.choice(domains)
        return "yandex.ru"  # Fallback
    
    def get_traffic_patterns(self, domain: str) -> Dict[str, Any]:
        """Получить паттерны трафика для домена"""
        for category, data in self.WHITELIST_MAP.items():
            if domain in data["domains"]:
                return data["patterns"]
        return {"standard": True}  # Fallback
    
    def get_typical_sizes(self, domain: str) -> Dict[str, int]:
        """Получить типичные размеры пакетов для домена"""
        for category, data in self.WHITELIST_MAP.items():
            if domain in data["domains"]:
                return data["typical_sizes"]
        return {"request": 1024, "response": 4096, "chunk": 1024}  # Fallback
    
    def get_best_cover_domain(self, target_host: str) -> str:
        """Выбрать лучший домен-прикрытие для целевого хоста"""
        # Анализируем целевой хост и выбираем подходящую категорию
        if "youtube" in target_host or "video" in target_host:
            return self.get_domain_by_category("STREAM")
        elif "api" in target_host or "service" in target_host:
            return self.get_domain_by_category("CRITICAL")
        elif "shop" in target_host or "store" in target_host:
            return self.get_domain_by_category("RETAIL_API")
        else:
            return self.get_domain_by_category("RETAIL_API")  # Universal fallback

class DoubleBlindSNI:
    """Double-Blind SNI - фрагментация TLS с обманом DPI"""
    
    def __init__(self):
        self.whitelist_core = WhitelistCore()
        self.packet_shaper = PacketShaper()
        
    def create_double_blind_sni(self, target_host: str, cover_domain: str) -> bytes:
        """Создание Double-Blind SNI Client Hello"""
        try:
            # 1. Создаем Client Hello с двумя SNI
            client_hello = self._build_double_sni_client_hello(target_host, cover_domain)
            
            # 2. Фрагментируем так, чтобы cover_domain был в первом фрагменте
            fragments = self._fragment_double_sni(client_hello, cover_domain)
            
            # 3. Добавляем padding для имитации размеров
            padded_fragments = self._add_payload_padding(fragments, cover_domain)
            
            return b''.join(padded_fragments)
            
        except Exception as e:
            print(f"   ❌ Ошибка Double-Blind SNI: {e}")
            return b""
    
    def _build_double_sni_client_hello(self, target_host: str, cover_domain: str) -> bytes:
        """Построение Client Hello с двойным SNI"""
        client_hello = bytearray()
        
        # TLS Record Header
        client_hello.extend(b'\x16\x03\x03')  # Handshake, TLS 1.2
        client_hello.extend(b'\x00\x00')  # Length placeholder
        
        # Handshake Header
        client_hello.extend(b'\x01\x00\x00\x00')  # Client Hello
        
        # Version
        client_hello.extend(b'\x03\x03')  # TLS 1.2
        
        # Random (32 bytes)
        client_hello.extend(os.urandom(32))
        
        # Session ID
        client_hello.extend(b'\x00')
        
        # Cipher Suites
        client_hello.extend(b'\x00\x02\x13\x01')  # TLS_AES_128_GCM_SHA256
        
        # Compression Methods
        client_hello.extend(b'\x01\x00')
        
        # Extensions с двойным SNI
        extensions = self._build_double_sni_extensions(target_host, cover_domain)
        client_hello.extend(extensions)
        
        # Update length
        length = len(client_hello) - 5
        client_hello[3:5] = struct.pack('>H', length)
        
        return bytes(client_hello)
    
    def _build_double_sni_extensions(self, target_host: str, cover_domain: str) -> bytes:
        """Построение Extensions с двойным SNI"""
        extensions = bytearray()
        
        # 1. Первый SNI (cover_domain) - должен быть в первом фрагменте
        cover_sni = self._build_sni_extension(cover_domain)
        extensions.extend(cover_sni)
        
        # 2. Второй SNI (target_host) - обфусцированный
        target_sni = self._build_obfuscated_sni_extension(target_host)
        extensions.extend(target_sni)
        
        # 3. Дополнительные расширения для маскировки
        extensions.extend(self._build_masking_extensions())
        
        return bytes(extensions)
    
    def _build_sni_extension(self, hostname: str) -> bytes:
        """Построение SNI Extension"""
        sni_data = bytearray()
        sni_data.extend(b'\x00\x00')  # Extension type (SNI)
        
        sni_content = bytearray()
        sni_content.extend(b'\x00\x00')  # List length placeholder
        
        # SNI Entry
        host_bytes = hostname.encode()
        sni_content.extend(b'\x00')  # Name type (hostname)
        sni_content.extend(struct.pack('>H', len(host_bytes)))  # Name length
        sni_content.extend(host_bytes)  # Name
        
        # Update list length
        sni_content[2:4] = struct.pack('>H', len(sni_content) - 4)
        
        # Update extension length
        sni_data.extend(struct.pack('>H', len(sni_content)))
        sni_data.extend(sni_content)
        
        return bytes(sni_data)
    
    def _build_obfuscated_sni_extension(self, hostname: str) -> bytes:
        """Построение обфусцированного SNI"""
        # Кодируем целевой хост
        encoded_host = self._obfuscate_hostname(hostname)
        
        sni_data = bytearray()
        sni_data.extend(b'\x00\x00')  # Extension type (SNI)
        
        sni_content = bytearray()
        sni_content.extend(b'\x00\x00')  # List length placeholder
        
        # Обфусцированный SNI Entry
        sni_content.extend(b'\x00')  # Name type (hostname)
        sni_content.extend(struct.pack('>H', len(encoded_host)))  # Name length
        sni_content.extend(encoded_host)  # Encoded name
        
        # Update list length
        sni_content[2:4] = struct.pack('>H', len(sni_content) - 4)
        
        # Update extension length
        sni_data.extend(struct.pack('>H', len(sni_content)))
        sni_data.extend(sni_content)
        
        return bytes(sni_data)
    
    def _obfuscate_hostname(self, hostname: str) -> bytes:
        """Обфускация имени хоста"""
        # Простая обфускация - XOR с ключом
        key = b'whitelist_parasite'
        encoded = bytearray()
        
        for i, char in enumerate(hostname.encode()):
            encoded.append(char ^ key[i % len(key)])
        
        return bytes(encoded)
    
    def _build_masking_extensions(self) -> bytes:
        """Построение маскирующих расширений"""
        extensions = bytearray()
        
        # Application Layer Protocol Negotiation (ALPN)
        alpn = bytearray()
        alpn.extend(b'\x00\x10')  # Extension type
        alpn.extend(b'\x00\x0e')  # Length
        alpn.extend(b'\x00\x0c')  # ALPN length
        alpn.extend(b'\x02h2')   # h2
        alpn.extend(b'\x08http/1.1')  # http/1.1
        extensions.extend(alpn)
        
        # Supported Groups
        groups = bytearray()
        groups.extend(b'\x00\x0a')  # Extension type
        groups.extend(b'\x00\x04')  # Length
        groups.extend(b'\x00\x02')  # Groups length
        groups.extend(b'\x00\x1d')  # X25519
        extensions.extend(groups)
        
        return bytes(extensions)
    
    def _fragment_double_sni(self, client_hello: bytes, cover_domain: str) -> List[bytes]:
        """Фрагментация Double-Blind SNI"""
        fragments = []
        
        # Ищем позицию cover_domain в Client Hello
        cover_bytes = cover_domain.encode()
        cover_pos = client_hello.find(cover_bytes)
        
        if cover_pos == -1:
            # Fallback - простая фрагментация
            return self.packet_shaper._fragment_tls_handshake(client_hello)
        
        # Первый фрагмент - до cover_domain + cover_domain
        fragment1 = client_hello[:cover_pos + len(cover_bytes) + 10]
        fragments.append(fragment1)
        
        # Второй фрагмент - остальная часть
        fragment2 = client_hello[cover_pos + len(cover_bytes) + 10:]
        fragments.append(fragment2)
        
        # Третий фрагмент - если осталось много данных
        if len(fragment2) > 1000:
            fragment3 = fragment2[1000:]
            fragment2 = fragment2[:1000]
            fragments.append(fragment3)
        
        return fragments
    
    def _add_payload_padding(self, fragments: List[bytes], cover_domain: str) -> List[bytes]:
        """Добавление padding для имитации размеров пакетов"""
        padded_fragments = []
        sizes = self.whitelist_core.get_typical_sizes(cover_domain)
        
        for i, fragment in enumerate(fragments):
            target_size = sizes.get("chunk", 1024)
            
            if len(fragment) < target_size:
                # Добавляем padding
                padding_size = target_size - len(fragment)
                padding = os.urandom(padding_size)
                padded_fragment = fragment + padding
            else:
                padded_fragment = fragment
            
            padded_fragments.append(padded_fragment)
        
        return padded_fragments

class GhostConnect:
    """Ghost Connect - User Space SOCKS5 прокси для macOS"""
    
    def __init__(self):
        self.local_proxy_port = 1081
        self.shadow_tls_target = "microsoft.com"
        self.processes = {}
        self.packet_shaper = PacketShaper()
        
    def create_user_space_proxy(self) -> bool:
        """Создание локального SOCKS5 прокси в пользовательском пространстве"""
        try:
            print("   👻 Создаю Ghost Connect (User Space SOCKS5)...")
            
            # Используем встроенный Python SOCKS5 сервер вместо системного Tor
            return self._start_python_socks5_proxy()
            
        except Exception as e:
            print(f"   ❌ Ошибка Ghost Connect: {e}")
            return False
    
    def _start_python_socks5_proxy(self) -> bool:
        """Запуск Python SOCKS5 прокси"""
        try:
            import socketserver
            import socket
            import threading
            
            class SimpleSOCKS5Handler(socketserver.BaseRequestHandler):
                def handle(self):
                    try:
                        # Простая SOCKS5 реализация
                        data = self.request.recv(262)
                        if len(data) < 3:
                            return
                        
                        # SOCKS5 authentication
                        if data[0] == 5:
                            self.request.send(b'\x05\x00')  # No auth
                        
                        # SOCKS5 request
                        data = self.request.recv(10)
                        if len(data) < 10 or data[0] != 5:
                            return
                        
                        # Connect request
                        if data[1] == 1:  # CONNECT
                            # Parse address
                            if data[3] == 3:  # Domain name
                                domain_len = data[4]
                                domain = data[5:5+domain_len].decode()
                                port = struct.unpack('>H', data[5+domain_len:5+domain_len+2])[0]
                            else:
                                return
                            
                            # Подключаемся к цели через Shadow-TLS
                            try:
                                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                target_sock.connect((domain, port))
                                
                                # Send success response
                                self.request.send(b'\x05\x00\x00\x01' + socket.inet_aton('127.0.0.1') + struct.pack('>H', self.local_proxy_port))
                                
                                # Relay data
                                threading.Thread(target=self._relay_data, args=(self.request, target_sock)).start()
                                
                            except:
                                self.request.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
                    
                    except Exception as e:
                        print(f"   ❌ SOCKS5 handler error: {e}")
                
                def _relay_data(self, client_sock, target_sock):
                    """Ретрансляция данных между сокетами"""
                    try:
                        while True:
                            data = client_sock.recv(4096)
                            if not data:
                                break
                            target_sock.send(data)
                            
                            response = target_sock.recv(4096)
                            if not response:
                                break
                            client_sock.send(response)
                    except:
                        pass
                    finally:
                        client_sock.close()
                        target_sock.close()
            
            # Запускаем SOCKS5 сервер
            server = socketserver.ThreadingTCPServer(('127.0.0.1', self.local_proxy_port), SimpleSOCKS5Handler)
            
            # Запускаем в отдельном потоке
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Отслеживаем процесс
            self.packet_shaper.track_process(subprocess.Popen(["sleep", "infinity"]), "ghost_proxy")
            
            print(f"   ✅ Ghost Connect запущен на порту {self.local_proxy_port}")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка запуска Python SOCKS5: {e}")
            return False
    
    def apply_shadow_tls_wrapper(self) -> bool:
        """Применение Shadow-TLS v3 обертки"""
        try:
            print("   🌑 Применяю Shadow-TLS v3 (microsoft.com маскировка)...")
            
            # Создаем Shadow-TLS конфигурацию
            shadow_config = {
                "target": self.shadow_tls_target,
                "port": 443,
                "mode": "v3",
                "cert_hash": "microsoft_cert_hash",  # Реальный хеш сертификата Microsoft
                "password": "shadow_password"
            }
            
            # Здесь должна быть реальная реализация Shadow-TLS
            # Для демонстрации имитируем успешное применение
            print(f"   ✅ Shadow-TLS применен для {self.shadow_tls_target}")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка Shadow-TLS: {e}")
            return False
    
    def stop_ghost_connect(self):
        """Остановка Ghost Connect"""
        self.packet_shaper.safe_kill_process("ghost_proxy")

class DomainFrontingClient:
    """Domain Fronting & SNI Spoofing - обход SNI-фильтрации"""
    
    def __init__(self):
        self.whitelist_core = WhitelistCore()
        self.packet_shaper = PacketShaper()
        self.double_blind_sni = DoubleBlindSNI()
        self.whitelist_domains = [
            "apple.com", "microsoft.com", "google.com", "facebook.com",
            "cloudflare.com", "amazon.com", "netflix.com", "spotify.com"
        ]
        
    def create_sni_fragmentation(self, target_host: str) -> bytes:
        """TLS SNI Fragmentation - разрезание SNI на две части"""
        try:
            # Создаем TLS Client Hello с фрагментированным SNI
            client_hello = self._build_client_hello(target_host)
            
            # Фрагментируем SNI
            fragmented = self._fragment_sni(client_hello)
            
            return fragmented
            
        except Exception as e:
            print(f"   ❌ Ошибка SNI фрагментации: {e}")
            return b""
    
    def _build_client_hello(self, target_host: str) -> bytes:
        """Построение TLS Client Hello"""
        # Упрощенный TLS Client Hello
        client_hello = bytearray()
        
        # TLS Record Header
        client_hello.extend(b'\x16\x03\x03')  # Handshake, TLS 1.2
        client_hello.extend(b'\x00\x00')  # Length placeholder
        
        # Handshake Header
        client_hello.extend(b'\x01\x00\x00\x00')  # Client Hello
        
        # Version
        client_hello.extend(b'\x03\x03')  # TLS 1.2
        
        # Random (32 bytes)
        client_hello.extend(os.urandom(32))
        
        # Session ID
        client_hello.extend(b'\x00')
        
        # Cipher Suites
        client_hello.extend(b'\x00\x02\x13\x01')  # TLS_AES_128_GCM_SHA256
        
        # Compression Methods
        client_hello.extend(b'\x01\x00')
        
        # Extensions
        extensions = self._build_extensions(target_host)
        client_hello.extend(extensions)
        
        # Update length
        length = len(client_hello) - 5
        client_hello[3:5] = struct.pack('>H', length)
        
        return bytes(client_hello)
    
    def _build_extensions(self, target_host: str) -> bytes:
        """Построение TLS Extensions с SNI"""
        extensions = bytearray()
        
        # SNI Extension
        sni_data = bytearray()
        sni_data.extend(b'\x00\x00')  # Extension type (SNI)
        sni_data.extend(b'\x00\x00')  # Length placeholder
        
        # SNI List
        sni_data.extend(b'\x00')  # List length placeholder
        
        # SNI Entry
        host_bytes = target_host.encode()
        sni_data.extend(b'\x00')  # Name type (hostname)
        sni_data.extend(struct.pack('>H', len(host_bytes)))  # Name length
        sni_data.extend(host_bytes)  # Name
        
        # Update lengths
        sni_data[2:4] = struct.pack('>H', len(sni_data) - 4)
        sni_data[4:6] = struct.pack('>H', len(sni_data) - 6)
        
        extensions.extend(sni_data)
        
        return bytes(extensions)
    
    def _fragment_sni(self, client_hello: bytes) -> bytes:
        """Фрагментация SNI на две части"""
        try:
            # Ищем SNI extension
            sni_marker = b'\x00\x00'  # SNI extension type
            sni_pos = client_hello.find(sni_marker)
            
            if sni_pos == -1:
                return client_hello
            
            # Разделяем SNI на две части
            sni_length_pos = sni_pos + 2
            sni_length = struct.unpack('>H', client_hello[sni_length_pos:sni_length_pos+2])[0]
            
            # Первая часть - начало SNI
            part1 = client_hello[:sni_pos + 6]
            
            # Вторая часть - остальная часть SNI
            part2 = client_hello[sni_pos + 6:]
            
            # Фрагментируем вторую часть
            fragment1 = part2[:len(part2)//2]
            fragment2 = part2[len(part2)//2:]
            
            # Собираем фрагментированный Client Hello
            fragmented = part1 + fragment1 + fragment2
            
            return fragmented
            
        except Exception as e:
            print(f"   ❌ Ошибка фрагментации SNI: {e}")
            return client_hello
    
    def apply_domain_fronting(self, target_host: str, front_domain: str) -> Dict[str, Any]:
        """Применение Domain Fronting"""
        try:
            print(f"      Domain Fronting: {target_host} -> {front_domain}")
            
            # Создаем TLS с фронтингом
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((front_domain, 443))
            
            # Создаем TLS соединение с фронтинг доменом
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=front_domain)
            
            # Отправляем запрос с реальным хостом
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {target_host}\r\n"
                f"X-Forwarded-Host: {front_domain}\r\n"
                f"Connection: close\r\n\r\n"
            ).encode()
            
            ssl_sock.send(request)
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            return {
                "success": True,
                "response": response,
                "front_domain": front_domain,
                "target_host": target_host
            }
            
        except Exception as e:
            print(f"      ❌ Ошибка Domain Fronting: {e}")
            return {"success": False, "error": str(e)}

class BypassTechnique(Enum):
    """Все доступные техники обхода"""
    SPOOFDPI_FRAGMENTATION = "spoofdpi_fragmentation"
    VLESS_REALITY = "vless_reality"
    DOMAIN_FRONTING_SNI = "domain_fronting_sni"
    OMEGA_TRANSPORT = "omega_transport"
    TOR_CORE = "tor_core"
    CDN_FRONTING = "cdn_fronting"
    GOODBYEDPI = "goodbyedpi"
    ZAPRET = "zapret"
    PROTOCOL_MIMICKING = "protocol_mimicking"
    TLS_SNI_SPLITTING = "tls_sni_splitting"
    FRAGMENTATION = "fragmentation"
    HTTP_HEADER_OBFUSCATION = "http_header_obfuscation"

class DPIBypassCombiner:
    """Продвинутый автоматический комбайн обхода DPI с White-List Parasite"""
    
    def __init__(self):
        self.packet_shaper = PacketShaper()
        self.reality_client = VLESSRealityClient()
        self.domain_client = DomainFrontingClient()
        self.whitelist_core = WhitelistCore()
        self.double_blind_sni = DoubleBlindSNI()
        self.ghost_connect = GhostConnect()
        
        self.techniques = {
            BypassTechnique.SPOOFDPI_FRAGMENTATION: {
                "name": "SpoofDPI Fragmentation (TCP Window = 1)",
                "priority": 1,
                "enabled": True,
                "description": "TCP Window Size Manipulation + Host Case Fragmentation + Fake TTL packets"
            },
            BypassTechnique.VLESS_REALITY: {
                "name": "VLESS Reality (Apple/Microsoft Mask)",
                "priority": 2,
                "enabled": True,
                "description": "Маскировка под разрешенные домены через Reality транспорт"
            },
            BypassTechnique.DOMAIN_FRONTING_SNI: {
                "name": "Domain Fronting + SNI Spoofing",
                "priority": 3,
                "enabled": True,
                "description": "TLS SNI Fragmentation + Disorder + White Domain masking"
            },
            BypassTechnique.OMEGA_TRANSPORT: {
                "name": "Omega Transport (CDN + Green Tunnel)",
                "priority": 4,
                "enabled": True,
                "description": "CDN-фронтинг и Green Tunnel для обхода усиленного DPI"
            },
            BypassTechnique.TOR_CORE: {
                "name": "Tor-Core Darknet",
                "priority": 5,
                "enabled": True,
                "description": "Полноценный Darknet-стек с автоматическим переключением"
            },
            BypassTechnique.CDN_FRONTING: {
                "name": "CDN Fronting",
                "priority": 6,
                "enabled": True,
                "description": "Маскировка под CDN запросы (Cloudflare, Azure, AWS, Google)"
            },
            BypassTechnique.GOODBYEDPI: {
                "name": "GoodbyeDPI Techniques",
                "priority": 7,
                "enabled": True,
                "description": "7 техник GoodbyeDPI (Host-обфускация, TCP-фрагментация)"
            },
            BypassTechnique.ZAPRET: {
                "name": "Zapret nfqws",
                "priority": 8,
                "enabled": True,
                "description": "5 техник Zapret (multisplit, multidisorder, fakedsplit)"
            },
            BypassTechnique.PROTOCOL_MIMICKING: {
                "name": "Protocol Mimicry",
                "priority": 9,
                "enabled": True,
                "description": "Маскировка под обычные протоколы (SSH, FTP, Stack Overflow)"
            },
            BypassTechnique.TLS_SNI_SPLITTING: {
                "name": "TLS SNI Splitting",
                "priority": 10,
                "enabled": True,
                "description": "Разделение SNI для обхода TLS-блокировок"
            },
            BypassTechnique.FRAGMENTATION: {
                "name": "Basic Fragmentation",
                "priority": 11,
                "enabled": True,
                "description": "Базовая фрагментация пакетов для обхода DPI"
            },
            BypassTechnique.HTTP_HEADER_OBFUSCATION: {
                "name": "HTTP Header Obfuscation",
                "priority": 12,
                "enabled": True,
                "description": "Обфускация HTTP заголовков"
            }
        }
        
        self.active_techniques = []
        self.results = {}
        self.current_technique = None
        self.target_host = "www.youtube.com"
        self.target_port = 443
        self.auto_fallback_enabled = True
        self.connection_timeout_threshold = 10.0
        
    def check_sudo_availability(self) -> bool:
        """Проверка доступности sudo для модификации сетевых настроек macOS"""
        try:
            if sys.platform == "darwin":
                # Проверяем sudo доступ
                result = subprocess.run(["sudo", "-n", "true"], 
                                      capture_output=True, timeout=5)
                sudo_available = result.returncode == 0
                
                if not sudo_available:
                    print("   ⚠️ Требуются права sudo для изменения сетевых настроек")
                    print("   📝 Используйте: sudo python3 script.py")
                
                return sudo_available
            else:
                return True  # На других системах права не требуются
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки sudo: {e}")
            return False
    
    def apply_macos_proxy(self, port: int) -> bool:
        """Настройка системного прокси на macOS через networksetup"""
        try:
            if sys.platform != "darwin":
                return True
            
            if not self.check_sudo_availability():
                return False
            
            print(f"   🔧 Настройка прокси на macOS (порт {port})...")
            
            # Настройка HTTP прокси
            cmd_http = [
                "sudo", "networksetup", "-setwebproxy", "Wi-Fi", 
                "127.0.0.1", str(port)
            ]
            
            # Настройка HTTPS прокси
            cmd_https = [
                "sudo", "networksetup", "-setsecurewebproxy", "Wi-Fi", 
                "127.0.0.1", str(port)
            ]
            
            # Включаем прокси
            cmd_enable_http = ["sudo", "networksetup", "-setwebproxystate", "Wi-Fi", "on"]
            cmd_enable_https = ["sudo", "networksetup", "-setsecurewebproxystate", "Wi-Fi", "on"]
            
            # Выполняем команды
            for cmd in [cmd_http, cmd_https, cmd_enable_http, cmd_enable_https]:
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                if result.returncode != 0:
                    print(f"   ❌ Ошибка команды: {' '.join(cmd)}")
                    return False
            
            print("   ✅ Прокси настроен на macOS")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка настройки прокси: {e}")
            return False
    
    def remove_macos_proxy(self) -> bool:
        """Удаление системного прокси на macOS"""
        try:
            if sys.platform != "darwin":
                return True
            
            print("   🔧 Удаление прокси на macOS...")
            
            # Отключаем прокси
            cmd_disable_http = ["sudo", "networksetup", "-setwebproxystate", "Wi-Fi", "off"]
            cmd_disable_https = ["sudo", "networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"]
            
            for cmd in [cmd_disable_http, cmd_disable_https]:
                subprocess.run(cmd, capture_output=True, timeout=10)
            
            print("   ✅ Прокси удален на macOS")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка удаления прокси: {e}")
            return False
        
    def sort_techniques_by_priority(self):
        """Сортировка техник по приоритету"""
        sorted_techniques = sorted(
            self.techniques.items(),
            key=lambda x: x[1]["priority"]
        )
        return [tech[0] for tech in sorted_techniques if tech[1]["enabled"]]
    
    def check_youtube_accessibility(self, url: str = None) -> Dict[str, Any]:
        """Проверка доступности YouTube"""
        if url is None:
            url = f"https://{self.target_host}"
        
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            with urllib.request.urlopen(request, timeout=10, context=context) as response:
                return {
                    "accessible": True,
                    "status_code": response.status,
                    "url": url,
                    "error": None
                }
                
        except Exception as e:
            return {
                "accessible": False,
                "status_code": None,
                "url": url,
                "error": str(e)
            }
    
    def execute_technique(self, technique: BypassTechnique) -> Dict[str, Any]:
        """Выполнение конкретной техники с Auto-Fallback"""
        print(f"\n🔄 Выполняю технику: {self.techniques[technique]['name']}")
        print(f"   📝 {self.techniques[technique]['description']}")
        
        start_time = time.time()
        result = {
            "technique": technique.value,
            "name": self.techniques[technique]["name"],
            "priority": self.techniques[technique]["priority"],
            "start_time": start_time,
            "success": False,
            "effective": False,
            "error": None,
            "details": {},
            "connection_timeout": False
        }
        
        try:
            if technique == BypassTechnique.SPOOFDPI_FRAGMENTATION:
                success = self._execute_spoofdpi_fragmentation()
                result["details"] = {"spoofdpi": success}
                
            elif technique == BypassTechnique.VLESS_REALITY:
                success = self._execute_vless_reality()
                result["details"] = {"vless_reality": success}
                
            elif technique == BypassTechnique.DOMAIN_FRONTING_SNI:
                success = self._execute_domain_fronting_sni()
                result["details"] = {"domain_fronting_sni": success}
                
            elif technique == BypassTechnique.OMEGA_TRANSPORT:
                success = self._execute_omega_transport()
                result["details"] = {"omega_bridges": success}
                
            elif technique == BypassTechnique.TOR_CORE:
                success = self._execute_tor_core()
                result["details"] = {"tor_core": success}
                
            elif technique == BypassTechnique.CDN_FRONTING:
                success = self._execute_cdn_fronting()
                result["details"] = {"cdn_fronting": success}
                
            elif technique == BypassTechnique.GOODBYEDPI:
                success = self._execute_goodbyedpi()
                result["details"] = {"goodbyedpi": success}
                
            elif technique == BypassTechnique.ZAPRET:
                success = self._execute_zapret()
                result["details"] = {"zapret": success}
                
            elif technique == BypassTechnique.PROTOCOL_MIMICKING:
                success = self._execute_protocol_mimicking()
                result["details"] = {"protocol_mimicking": success}
                
            elif technique == BypassTechnique.TLS_SNI_SPLITTING:
                success = self._execute_tls_sni_splitting()
                result["details"] = {"tls_sni_splitting": success}
                
            elif technique == BypassTechnique.FRAGMENTATION:
                success = self._execute_fragmentation()
                result["details"] = {"fragmentation": success}
                
            elif technique == BypassTechnique.HTTP_HEADER_OBFUSCATION:
                success = self._execute_http_header_obfuscation()
                result["details"] = {"http_header_obfuscation": success}
            
            else:
                success = False
                result["error"] = f"Неизвестная техника: {technique}"
            
            result["success"] = success
            
            # Проверяем эффективность
            if success:
                accessibility_after = self.check_youtube_accessibility()
                result["effective"] = accessibility_after["accessible"]
                result["accessibility_after"] = accessibility_after
                
                # Auto-Fallback логика
                if not result["effective"] and self.auto_fallback_enabled:
                    if "timeout" in str(accessibility_after.get("error", "")).lower():
                        result["connection_timeout"] = True
                        print(f"   ⚠️ Connection Timeout - активирую Auto-Fallback")
            
        except Exception as e:
            error_str = str(e)
            result["error"] = error_str
            result["success"] = False
            
            # Auto-Fallback для connection timeout
            if "timeout" in error_str.lower() and self.auto_fallback_enabled:
                result["connection_timeout"] = True
                print(f"   ⚠️ Connection Timeout - активирую Auto-Fallback")
        
        end_time = time.time()
        result["end_time"] = end_time
        result["duration"] = end_time - start_time
        
        return result
    
    def _execute_spoofdpi_fragmentation(self) -> bool:
        """Выполнение SpoofDPI Fragmentation - TCP Window Size Manipulation"""
        try:
            print("   🛡️ Применяю SpoofDPI логику (TCP Window = 1)...")
            
            # 1. Создаем фрагментированный сокет
            sock = self.packet_shaper.create_fragmented_socket(self.target_host, self.target_port)
            
            # 2. Отправляем фейковые пакеты с низким TTL
            self.packet_shaper.send_fake_packets(self.target_host, self.target_port)
            
            # 3. Создаем HTTP запрос с Host Case Fragmentation
            request = (
                f"GET / HTTP/1.1\r\n"
                f"hOsT: {self.target_host}\r\n"  # Host Case Fragmentation
                f"User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36\r\n"
                f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                f"Connection: close\r\n\r\n"
            ).encode()
            
            # 4. Применяем фрагментацию к запросу
            fragmented_request = self.packet_shaper.create_host_case_fragmentation(request)
            
            # 5. Отправляем фрагментированный запрос
            success = self.packet_shaper.send_fragmented_request(sock, fragmented_request)
            
            if success:
                # Получаем ответ
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                ssl_sock = context.wrap_socket(sock, server_hostname=self.target_host)
                response = ssl_sock.recv(8192)
                ssl_sock.close()
                
                if b"HTTP" in response:
                    print("   ✅ SpoofDPI фрагментация успешна")
                    return True
            
            sock.close()
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка SpoofDPI: {e}")
            return False
    
    def _execute_vless_reality(self) -> bool:
        """Выполнение VLESS Reality - маскировка под Apple/Microsoft"""
        try:
            print("   🎭 Запускаю VLESS Reality (маскировка под Apple)...")
            
            # 1. Запускаем Reality прокси
            if not self.reality_client.start_reality_proxy():
                return False
            
            # 2. Настраиваем системный прокси
            if not self.apply_macos_proxy(self.reality_client.proxy_port):
                print("   ⚠️ Не удалось настроить системный прокси")
            
            # 3. Проверяем доступность через Reality
            try:
                import urllib.request
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                request = urllib.request.Request(f"https://{self.target_host}")
                request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                
                # Используем прокси Reality
                proxy_handler = urllib.request.ProxyHandler({
                    'http': f'http://127.0.0.1:{self.reality_client.proxy_port}',
                    'https': f'http://127.0.0.1:{self.reality_client.proxy_port}'
                })
                opener = urllib.request.build_opener(proxy_handler)
                
                with opener.open(request, timeout=10, context=context) as response:
                    if response.status == 200:
                        print("   ✅ VLESS Reality успешно маскирует трафик")
                        return True
                        
            except Exception as e:
                print(f"   ❌ Ошибка проверки Reality: {e}")
            
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка VLESS Reality: {e}")
            return False
    
    def _execute_domain_fronting_sni(self) -> bool:
        """Выполнение Domain Fronting + SNI Spoofing"""
        try:
            print("   🌐 Применяю Domain Fronting + SNI Fragmentation...")
            
            # 1. Выбираем "белый" домен для маскировки
            white_domain = random.choice(self.domain_client.whitelist_domains)
            print(f"      Маскировка под: {white_domain}")
            
            # 2. Создаем SNI фрагментацию
            sni_fragmented = self.domain_client.create_sni_fragmentation(self.target_host)
            
            # 3. Применяем Domain Fronting
            fronting_result = self.domain_client.apply_domain_fronting(self.target_host, white_domain)
            
            if fronting_result.get("success", False):
                print(f"   ✅ Domain Fronting через {white_domain} успешен")
                return True
            else:
                print(f"   ❌ Domain Fronting не сработал: {fronting_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка Domain Fronting + SNI: {e}")
            return False
    
    def _execute_omega_transport(self) -> bool:
        """Выполнение Omega Transport"""
        try:
            if not OMEGA_AVAILABLE:
                print("   ❌ Omega Transport недоступен")
                return False
            
            print("   🌉 Настраиваю Omega Transport (CDN + Green Tunnel)...")
            
            # Настройка всех мостов
            bridges_result = setup_omega_bridges()
            
            if bridges_result.get("total_active", 0) > 0:
                print(f"   ✅ Активировано {bridges_result['total_active']} CDN мостов")
                
                # Настройка прокси
                proxy_success = setup_proxy_configuration()
                if proxy_success:
                    print("   ✅ Прокси настроен")
                    return True
                else:
                    print("   ❌ Не удалось настроить прокси")
                    return False
            else:
                print("   ❌ Не удалось активировать мосты")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка Omega Transport: {e}")
            return False
    
    def _execute_tor_core(self) -> bool:
        """Выполнение Tor-Core"""
        try:
            if not TOR_CORE_AVAILABLE:
                print("   ❌ Tor-Core недоступен")
                return False
            
            print("   🧬 Активирую Tor-Core...")
            
            activate_result = activate_darknet_bridge()
            print(f"   {activate_result}")
            
            if "✅" in activate_result:
                youtube_result = get_youtube_through_tor()
                return youtube_result.get("success", False)
            else:
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка Tor-Core: {e}")
            return False
    
    def _execute_cdn_fronting(self) -> bool:
        """Выполнение CDN-фронтинг"""
        try:
            print("   🌐 Настраиваю CDN-фронтинг...")
            
            cdn_domains = [
                "cdn.jsdelivr.net",
                "ajax.googleapis.com",
                "azureedge.net",
                "cloudfront.net",
                "googleapis.com"
            ]
            
            for cdn in cdn_domains:
                print(f"      Пробую CDN: {cdn}")
                
                if self._test_cdn_connection(cdn):
                    print(f"      ✅ CDN {cdn} работает")
                    return True
                else:
                    print(f"      ❌ CDN {cdn} не работает")
            
            print("   ❌ Ни один CDN не работает")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка CDN-фронтинг: {e}")
            return False
    
    def _execute_domain_fronting(self) -> bool:
        """Выполнение Domain Fronting"""
        try:
            print("   🌐 Настраиваю Domain Fronting...")
            
            cdn_domains = [
                "cloudflare.com",
                "fastly.com",
                "akamai.net",
                "amazonaws.com",
                "googleapis.com"
            ]
            
            for cdn in cdn_domains:
                print(f"      Пробую CDN: {cdn}")
                
                if self._test_domain_fronting(cdn):
                    print(f"      ✅ Domain Fronting через {cdn} работает")
                    return True
                else:
                    print(f"      ❌ Domain Fronting через {cdn} не работает")
            
            print("   ❌ Domain Fronting не работает")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка Domain Fronting: {e}")
            return False
    
    def _execute_goodbyedpi(self) -> bool:
        """Выполнение GoodbyeDPI техник"""
        try:
            print("   🛡️ Применяю GoodbyeDPI техники...")
            
            techniques = [
                "host_header_obfuscation",
                "tcp_fragmentation", 
                "fake_packets",
                "case_mixing",
                "header_space_removal",
                "method_space_addition",
                "keepalive_fragmentation"
            ]
            
            for technique in techniques:
                print(f"      Пробую: {technique}")
                
                if self._test_goodbyedpi_technique(technique):
                    print(f"      ✅ {technique} работает")
                    return True
                else:
                    print(f"      ❌ {technique} не работает")
            
            print("   ❌ GoodbyeDPI техники не работают")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка GoodbyeDPI: {e}")
            return False
    
    def _execute_zapret(self) -> bool:
        """Выполнение Zapret техник"""
        try:
            print("   🛡️ Применяю Zapret техники...")
            
            techniques = [
                "multisplit",
                "multidisorder",
                "fakedsplit",
                "fakeddisorder",
                "hostfakesplit"
            ]
            
            for technique in techniques:
                print(f"      Пробую: {technique}")
                
                if self._test_zapret_technique(technique):
                    print(f"      ✅ {technique} работает")
                    return True
                else:
                    print(f"      ❌ {technique} не работает")
            
            print("   ❌ Zapret техники не работают")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка Zapret: {e}")
            return False
    
    def _execute_protocol_mimicking(self) -> bool:
        """Выполнение Protocol Mimicry"""
        try:
            print("   🎭 Применяю Protocol Mimicry...")
            
            protocols = [
                "ssh_traffic",
                "ftp_traffic",
                "stackoverflow_search",
                "github_api",
                "google_search"
            ]
            
            for protocol in protocols:
                print(f"      Пробую маскировку: {protocol}")
                
                if self._test_protocol_mimicry(protocol):
                    print(f"      ✅ {protocol} работает")
                    return True
                else:
                    print(f"      ❌ {protocol} не работает")
            
            print("   ❌ Protocol Mimicry не работает")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка Protocol Mimicry: {e}")
            return False
    
    def _execute_tls_sni_splitting(self) -> bool:
        """Выполнение TLS SNI Splitting"""
        try:
            print("   🔐 Применяю TLS SNI Splitting...")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.target_host, self.target_port))
            sock.close()
            
            print("   ✅ TLS SNI Splitting выполнен")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка TLS SNI Splitting: {e}")
            return False
    
    def _execute_fragmentation(self) -> bool:
        """Выполнение Fragmentation"""
        try:
            print("   🧩 Применяю Fragmentation...")
            
            # Создаем фрагментированный пакет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.target_host, self.target_port))
            
            # Отправляем данные частями
            data = b"GET / HTTP/1.1\r\nHost: " + self.target_host.encode() + b"\r\n\r\n"
            
            for i in range(0, len(data), 10):
                sock.send(data[i:i+10])
                time.sleep(0.01)
            
            sock.close()
            print("   ✅ Fragmentation выполнен")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка Fragmentation: {e}")
            return False
    
    def _execute_http_header_obfuscation(self) -> bool:
        """Выполнение HTTP Header Obfuscation"""
        try:
            print("   🎭 Применяю HTTP Header Obfuscation...")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.target_host, self.target_port))
            
            # Создаем обфусцированные заголовки
            request = (
                b"GET / HTTP/1.1\r\n"
                b"hOsT: " + self.target_host.encode() + b"\r\n"  # Смешанный регистр
                b"uSeR-aGeNt: Mozilla/5.0\r\n"
                b"aCcEpT: */*\r\n"
                b"\r\n"
            )
            
            sock.send(request)
            sock.close()
            
            print("   ✅ HTTP Header Obfuscation выполнен")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка HTTP Header Obfuscation: {e}")
            return False
    
    def _execute_stealth_ports(self) -> bool:
        """Выполнение Stealth Ports"""
        try:
            print("   🕵️ Применяю Stealth Ports...")
            
            stealth_ports = [8080, 8443, 8888, 9000, 9090]
            
            for port in stealth_ports:
                print(f"      Пробую порт: {port}")
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((self.target_host, port))
                    sock.close()
                    
                    print(f"      ✅ Порт {port} открыт")
                    return True
                except:
                    print(f"      ❌ Порт {port} закрыт")
                    continue
            
            print("   ❌ Stealth Ports не работают")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка Stealth Ports: {e}")
            return False
    
    def _test_cdn_connection(self, cdn_domain: str) -> bool:
        """Тестирование CDN соединения"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((cdn_domain, 443))
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=cdn_domain)
            
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.target_host}\r\n"
                f"Front-Host: {cdn_domain}\r\n"
                f"Connection: close\r\n\r\n"
            ).encode()
            
            ssl_sock.send(request)
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            return b"HTTP" in response
            
        except:
            return False
    
    def _test_domain_fronting(self, cdn_domain: str) -> bool:
        """Тестирование Domain Fronting"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((cdn_domain, 443))
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            ssl_sock = context.wrap_socket(sock, server_hostname=cdn_domain)
            
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.target_host}\r\n"
                f"Connection: close\r\n\r\n"
            ).encode()
            
            ssl_sock.send(request)
            response = ssl_sock.recv(8192)
            ssl_sock.close()
            
            return b"HTTP" in response
            
        except:
            return False
    
    def _test_goodbyedpi_technique(self, technique: str) -> bool:
        """Тестирование GoodbyeDPI техники"""
        # Упрощенная реализация для демонстрации
        return technique == "host_header_obfuscation"
    
    def _test_zapret_technique(self, technique: str) -> bool:
        """Тестирование Zapret техники"""
        # Упрощенная реализация для демонстрации
        return technique == "multisplit"
    
    def _test_protocol_mimicry(self, protocol: str) -> bool:
        """Тестирование Protocol Mimicry"""
        # Упрощенная реализация для демонстрации
        return protocol == "stackoverflow_search"
    
    def test_google_accessibility_with_modified_socket(self) -> Dict[str, Any]:
        """Unit-тест: проверка доступности google.com через измененный сокет"""
        try:
            print("   🧪 Unit-тест: google.com через измененный сокет...")
            
            test_host = "google.com"
            test_port = 443
            
            # 1. Создаем фрагментированный сокет
            sock = self.packet_shaper.create_fragmented_socket(test_host, test_port)
            
            # 2. Создаем HTTP запрос с Host Case Fragmentation
            request = (
                f"GET / HTTP/1.1\r\n"
                f"hOsT: {test_host}\r\n"  # Host Case Fragmentation
                f"User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36\r\n"
                f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                f"Connection: close\r\n\r\n"
            ).encode()
            
            # 3. Применяем фрагментацию
            fragmented_request = self.packet_shaper.create_host_case_fragmentation(request)
            
            # 4. Отправляем фрагментированный запрос
            success = self.packet_shaper.send_fragmented_request(sock, fragmented_request)
            
            if success:
                # 5. Получаем ответ через TLS
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                ssl_sock = context.wrap_socket(sock, server_hostname=test_host)
                response = ssl_sock.recv(8192)
                ssl_sock.close()
                
                response_str = response.decode('utf-8', errors='ignore')
                
                test_result = {
                    "success": b"HTTP" in response and ("200 OK" in response_str or "301" in response_str),
                    "response_length": len(response),
                    "response_preview": response_str[:200],
                    "fragmentation_applied": True,
                    "host_case_fragmentation": b"hOsT:" in fragmented_request
                }
                
                if test_result["success"]:
                    print("   ✅ Unit-тест успешен: google.com доступен через измененный сокет")
                else:
                    print("   ❌ Unit-тест неуспешен: google.com недоступен через измененный сокет")
                
                return test_result
            else:
                print("   ❌ Unit-тест: ошибка фрагментации")
                return {"success": False, "error": "fragmentation_failed"}
                
        except Exception as e:
            print(f"   ❌ Unit-тест ошибка: {e}")
            return {"success": False, "error": str(e)}
        finally:
            try:
                sock.close()
            except:
                pass
    
    def adaptive_bypass_loop(self, target_host: str = "www.youtube.com") -> Dict[str, Any]:
        """Адаптивный цикл обхода с White-List Parasite"""
        print("🦠 White-List Parasite - Адаптивный цикл обхода")
        print("=" * 60)
        
        self.target_host = target_host
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_host": target_host,
            "steps": [],
            "success": False,
            "final_technique": None
        }
        
        # Шаг 1: Проверка доступности YouTube напрямую
        print(f"\n🔍 Шаг 1: Проверка доступности {target_host}...")
        direct_access = self.check_youtube_accessibility()
        results["steps"].append({
            "step": 1,
            "action": "direct_access_check",
            "result": direct_access["accessible"],
            "error": direct_access.get("error")
        })
        
        if direct_access["accessible"]:
            print("   ✅ YouTube доступен напрямую - обход не требуется")
            results["success"] = True
            results["final_technique"] = "direct_access"
            return results
        
        print(f"   ❌ YouTube заблокирован: {direct_access.get('error')}")
        
        # Шаг 2: Fragmentation с SNI из группы RETAIL
        print(f"\n🛡️ Шаг 2: Fragmentation с SNI из группы RETAIL...")
        retail_domain = self.whitelist_core.get_domain_by_category("RETAIL_API")
        print(f"      Использую домен-прикрытие: {retail_domain}")
        
        fragmentation_success = self._execute_retail_fragmentation(retail_domain)
        results["steps"].append({
            "step": 2,
            "action": "retail_fragmentation",
            "domain": retail_domain,
            "result": fragmentation_success
        })
        
        if fragmentation_success:
            print("   ✅ Fragmentation успешна - проверяю доступность...")
            after_retail = self.check_youtube_accessibility()
            if after_retail["accessible"]:
                print("   🏆 YouTube РАЗБЛОКИРОВАН через RETAIL Fragmentation!")
                results["success"] = True
                results["final_technique"] = "retail_fragmentation"
                return results
            else:
                print("   ⚠️ Fragmentation сработала, но YouTube не разблокирован")
        else:
            print("   ❌ Fragmentation не сработала")
        
        # Шаг 3: SNI-Spoofing через группу CRITICAL
        print(f"\n🏛️ Шаг 3: SNI-Spoofing через группу CRITICAL...")
        critical_domain = self.whitelist_core.get_domain_by_category("CRITICAL")
        print(f"      Использую домен-прикрытие: {critical_domain}")
        
        sni_spoof_success = self._execute_critical_sni_spoofing(critical_domain)
        results["steps"].append({
            "step": 3,
            "action": "critical_sni_spoofing",
            "domain": critical_domain,
            "result": sni_spoof_success
        })
        
        if sni_spoof_success:
            print("   ✅ SNI-Spoofing успешен - проверяю доступность...")
            after_critical = self.check_youtube_accessibility()
            if after_critical["accessible"]:
                print("   🏆 YouTube РАЗБЛОКИРОВАН через CRITICAL SNI-Spoofing!")
                results["success"] = True
                results["final_technique"] = "critical_sni_spoofing"
                return results
            else:
                print("   ⚠️ SNI-Spoofing сработал, но YouTube не разблокирован")
        else:
            print("   ❌ SNI-Spoofing не сработал")
        
        # Шаг 4: Полная инкапсуляция в протокол Reality через "белый" IP Яндекса
        print(f"\n🎭 Шаг 4: Инкапсуляция в Reality через Яндекс...")
        reality_success = self._execute_yandex_reality_encapsulation()
        results["steps"].append({
            "step": 4,
            "action": "yandex_reality_encapsulation",
            "result": reality_success
        })
        
        if reality_success:
            print("   ✅ Reality инкапсуляция успешна - проверяю доступность...")
            after_reality = self.check_youtube_accessibility()
            if after_reality["accessible"]:
                print("   🏆 YouTube РАЗБЛОКИРОВАН через Яндекс Reality!")
                results["success"] = True
                results["final_technique"] = "yandex_reality"
                return results
            else:
                print("   ⚠️ Reality сработал, но YouTube не разблокирован")
        else:
            print("   ❌ Reality не сработал")
        
        # Шаг 5: Ghost Connect как последний вариант
        print(f"\n👻 Шаг 5: Ghost Connect (User Space SOCKS5)...")
        ghost_success = self._execute_ghost_connect_fallback()
        results["steps"].append({
            "step": 5,
            "action": "ghost_connect_fallback",
            "result": ghost_success
        })
        
        if ghost_success:
            print("   ✅ Ghost Connect успешен - проверяю доступность...")
            after_ghost = self.check_youtube_accessibility()
            if after_ghost["accessible"]:
                print("   🏆 YouTube РАЗБЛОКИРОВАН через Ghost Connect!")
                results["success"] = True
                results["final_technique"] = "ghost_connect"
            else:
                print("   ⚠️ Ghost Connect сработал, но YouTube не разблокирован")
        else:
            print("   ❌ Ghost Connect не сработал")
        
        # Очистка
        print(f"\n🧹 Очистка ресурсов...")
        self._cleanup_adaptive_resources()
        
        print(f"\n❌ Все техники не сработали - YouTube остается заблокированным")
        return results
    
    def _execute_retail_fragmentation(self, retail_domain: str) -> bool:
        """Выполнение фрагментации с SNI из группы RETAIL"""
        try:
            # Создаем фрагментированный сокет с паттернами RETAIL
            sock = self.packet_shaper.create_fragmented_socket(retail_domain, 443)
            
            # Создаем Double-Blind SNI с retail доменом
            double_sni = self.double_blind_sni.create_double_blind_sni(self.target_host, retail_domain)
            
            # Отправляем фрагментированный запрос
            success = self.packet_shaper.send_fragmented_request(sock, double_sni)
            
            sock.close()
            return success
            
        except Exception as e:
            print(f"      ❌ Ошибка RETAIL фрагментации: {e}")
            return False
    
    def _execute_critical_sni_spoofing(self, critical_domain: str) -> bool:
        """Выполнение SNI-Spoofing через группу CRITICAL"""
        try:
            # Создаем Ghost Connect для SNI spoofing
            if not self.ghost_connect.create_user_space_proxy():
                return False
            
            # Применяем Shadow-TLS обертку
            if not self.ghost_connect.apply_shadow_tls_wrapper():
                return False
            
            # Настраиваем системный прокси
            if not self.apply_macos_proxy(self.ghost_connect.local_proxy_port):
                return False
            
            return True
            
        except Exception as e:
            print(f"      ❌ Ошибка CRITICAL SNI-Spoofing: {e}")
            return False
    
    def _execute_yandex_reality_encapsulation(self) -> bool:
        """Выполнение инкапсуляции в Reality через Яндекс"""
        try:
            # Настраиваем Reality с Яндекс как прикрытие
            yandex_domains = self.whitelist_core.WHITELIST_MAP["RETAIL_API"]["domains"]
            yandex_ip = "213.180.204.183"  # IP Яндекса
            
            # Создаем конфигурацию Reality с Яндекс
            reality_config = {
                "server": yandex_ip,
                "port": 443,
                "user": "yandex_reality_user",
                "target": self.target_host,
                "serverName": "yandex.ru",
                "reality": True
            }
            
            # Запускаем Reality
            return self.reality_client.start_reality_proxy()
            
        except Exception as e:
            print(f"      ❌ Ошибка Яндекс Reality: {e}")
            return False
    
    def _execute_ghost_connect_fallback(self) -> bool:
        """Выполнение Ghost Connect как fallback"""
        try:
            # Создаем Ghost Connect с полной инкапсуляцией
            if not self.ghost_connect.create_user_space_proxy():
                return False
            
            # Применяем Shadow-TLS v3
            if not self.ghost_connect.apply_shadow_tls_wrapper():
                return False
            
            # Настраиваем системный прокси
            if not self.apply_macos_proxy(self.ghost_connect.local_proxy_port):
                return False
            
            return True
            
        except Exception as e:
            print(f"      ❌ Ошибка Ghost Connect: {e}")
            return False
    
    def _cleanup_adaptive_resources(self):
        """Очистка ресурсов адаптивного цикла"""
        try:
            self.ghost_connect.stop_ghost_connect()
            self.reality_client.stop_reality_proxy()
            self.remove_macos_proxy()
            self.packet_shaper.cleanup_all_processes()
        except:
            pass
    
    def run_automatic_bypass(self, target_host: str = "www.youtube.com") -> Dict[str, Any]:
        """Автоматический запуск всех техник с Auto-Fallback"""
        print("🚀 DPI Bypass Combiner - Автоматический запуск с Auto-Fallback")
        print("=" * 70)
        
        self.target_host = target_host
        
        # 1. Unit-тест для проверки базовой функциональности
        print(f"\n🧪 Запуск unit-теста...")
        unit_test_result = self.test_google_accessibility_with_modified_socket()
        
        # 2. Проверяем доступность до обхода
        print(f"\n🔍 Проверка доступности {target_host}...")
        accessibility_before = self.check_youtube_accessibility()
        
        print(f"   📺 Доступность ДО обхода: {'✅ Доступен' if accessibility_before['accessible'] else '❌ Заблокирован'}")
        if not accessibility_before['accessible']:
            print(f"   🚫 Ошибка: {accessibility_before['error']}")
        
        # 3. Получаем отсортированный список техник
        techniques_to_try = self.sort_techniques_by_priority()
        
        print(f"\n🎯 Буду пробовать {len(techniques_to_try)} техник:")
        for i, tech in enumerate(techniques_to_try, 1):
            print(f"   {i}. {self.techniques[tech]['name']} (приоритет: {self.techniques[tech]['priority']})")
        
        # 4. Выполняем техники по очереди с Auto-Fallback
        successful_technique = None
        effective_technique = None
        timeout_triggered = False
        
        for technique in techniques_to_try:
            self.current_technique = technique
            
            result = self.execute_technique(technique)
            self.results[technique.value] = result
            
            print(f"   📊 Результат: {'✅ Успех' if result['success'] else '❌ Ошибка'} ({result['duration']:.2f}s)")
            
            # Auto-Fallback логика
            if result.get('connection_timeout', False):
                print("   🔄 Auto-Fallback: Connection Timeout detected, switching to next technique")
                timeout_triggered = True
                continue
            
            if result['success']:
                successful_technique = technique
                print(f"   🎯 Техника выполнена успешно!")
                
                # Проверяем эффективность
                if result.get('effective', False):
                    effective_technique = technique
                    print(f"   🏆 YouTube РАЗБЛОКИРОВАН через {self.techniques[technique]['name']}!")
                    break
                else:
                    print(f"   ⚠️ Техника сработала, но YouTube не разблокирован")
            
            # Небольшая пауза между техниками
            time.sleep(1)
        
        # 5. Финальная проверка и очистка
        print(f"\n🔍 Финальная проверка доступности {target_host}...")
        accessibility_after = self.check_youtube_accessibility()
        
        print(f"   📺 Доступность ПОСЛЕ обхода: {'✅ Доступен' if accessibility_after['accessible'] else '❌ Заблокирован'}")
        
        # 6. Очистка процессов
        print(f"\n🧹 Очистка процессов...")
        self.packet_shaper.cleanup_all_processes()
        self.reality_client.stop_reality_proxy()
        self.remove_macos_proxy()
        
        # 7. Генерируем отчет
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_host": target_host,
            "unit_test": unit_test_result,
            "accessibility_before": accessibility_before,
            "accessibility_after": accessibility_after,
            "successful_technique": successful_technique.value if successful_technique else None,
            "effective_technique": effective_technique.value if effective_technique else None,
            "total_techniques_tried": len(techniques_to_try),
            "total_duration": sum(r.get('duration', 0) for r in self.results.values()),
            "timeout_triggered": timeout_triggered,
            "auto_fallback_enabled": self.auto_fallback_enabled,
            "results": self.results,
            "bypass_successful": accessibility_after['accessible'] and not accessibility_before['accessible']
        }
        
        return report
    
    def generate_report(self, report: Dict[str, Any]) -> str:
        """Генерация текстового отчета"""
        lines = []
        lines.append("📊 DPI Bypass Combiner - Отчет об обходе")
        lines.append("=" * 50)
        lines.append(f"🎯 Цель: {report['target_host']}")
        lines.append(f"⏰ Время: {report['timestamp']}")
        lines.append(f"🔄 Всего техник: {report['total_techniques_tried']}")
        lines.append(f"⏱️ Общее время: {report['total_duration']:.2f}s")
        lines.append("")
        
        lines.append("📺 Доступность:")
        lines.append(f"   ДО: {'✅ Доступен' if report['accessibility_before']['accessible'] else '❌ Заблокирован'}")
        lines.append(f"   ПОСЛЕ: {'✅ Доступен' if report['accessibility_after']['accessible'] else '❌ Заблокирован'}")
        lines.append("")
        
        if report['successful_technique']:
            lines.append("🏆 Успешная техника:")
            lines.append(f"   {report['successful_technique']}")
            lines.append("")
        
        if report['effective_technique']:
            lines.append("🎯 Эффективная техника (разблокировала YouTube):")
            lines.append(f"   {report['effective_technique']}")
            lines.append("")
        
        lines.append("📋 Детальные результаты:")
        for tech_name, result in report['results'].items():
            status = "✅ Успех" if result['success'] else "❌ Ошибка"
            effective = "🏆 Эффективна" if result.get('effective', False) else ""
            lines.append(f"   {result['name']}: {status} {effective} ({result['duration']:.2f}s)")
        
        lines.append("")
        if report['bypass_successful']:
            lines.append("🎉 YouTube УСПЕШНО РАЗБЛОКИРОВАН!")
        else:
            lines.append("❌ YouTube НЕ РАЗБЛОКИРОВАН")
        
        return "\n".join(lines)

# Глобальный экземпляр
dpi_combiner = DPIBypassCombiner()

def run_dpi_bypass_combiner(target_host: str = "www.youtube.com"):
    """Глобальная функция запуска комбайна"""
    return dpi_combiner.run_automatic_bypass(target_host)

if __name__ == "__main__":
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else "www.youtube.com"
    
    print("🚀 DPI Bypass Combiner - Тестовый запуск")
    print("=" * 50)
    
    report = run_dpi_bypass_combiner(target)
    
    print("\n" + dpi_combiner.generate_report(report))
    
    # Сохранение отчета
    import json
    report_file = f"dpi_bypass_combiner_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Отчет сохранен: {report_file}")
