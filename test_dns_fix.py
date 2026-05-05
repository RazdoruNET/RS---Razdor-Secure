#!/usr/bin/env python3
"""
Тест DNS резолвинга для DPI-Bypass (без внешних зависимостей)
"""

import socket

def test_dns_resolution():
    """Тест DNS резолвинга через системный DNS"""
    test_hosts = ['www.youtube.com', 'google.com', 'telegram.org']
    
    print("🔍 Тест DNS резолвинга...")
    print("=" * 40)
    
    for host in test_hosts:
        print(f"\n📡 Тестирую {host}:")
        
        # Тест системного DNS
        try:
            ip = socket.gethostbyname(host)
            print(f"   ✅ Системный DNS: {host} → {ip}")
        except Exception as e:
            print(f"   ❌ Системный DNS: {host} → {e}")
            
            # Тест прямого DNS запроса
            try:
                ip = direct_dns_query(host, '8.8.8.8')
                if ip:
                    print(f"   ✅ Прямой DNS (8.8.8.8): {host} → {ip}")
                else:
                    print(f"   ❌ Прямой DNS (8.8.8.8): {host} → ошибка")
            except Exception as e:
                print(f"   ❌ Прямой DNS (8.8.8.8): {host} → {e}")

def direct_dns_query(hostname: str, dns_server: str) -> str:
    """Прямой DNS запрос к серверу"""
    try:
        # Создаем UDP сокет для DNS запроса
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        # Простая DNS query для A записи
        query = build_dns_query(hostname)
        sock.sendto(query, (dns_server, 53))
        
        response, _ = sock.recvfrom(512)
        sock.close()
        
        # Парсим ответ и извлекаем IP
        return parse_dns_response(response, hostname)
        
    except:
        return None

def build_dns_query(hostname: str) -> bytes:
    """Создание DNS запроса"""
    query = bytearray()
    
    # Header
    query.extend(b'\x00\x01')  # ID
    query.extend(b'\x01\x00')  # Flags
    query.extend(b'\x00\x01')  # Questions
    query.extend(b'\x00\x00')  # Answer RRs
    query.extend(b'\x00\x00')  # Authority RRs
    query.extend(b'\x00\x00')  # Additional RRs
    
    # Question
    query.extend(b'\x00\x01')  # QTYPE: A, QCLASS: IN
    
    # Hostname
    for part in hostname.split('.'):
        if part:
            query.append(len(part))
            query.extend(part.encode())
    query.extend(b'\x00')  # End of hostname
    
    return bytes(query)

def parse_dns_response(response: bytes, hostname: str) -> str:
    """Парсинг DNS ответа"""
    try:
        if len(response) < 16:
            return None
            
        # Ищем IP адрес в ответе
        for i in range(12, len(response) - 4):
            if all(0 <= b <= 255 for b in response[i:i+4]):
                ip = '.'.join(str(b) for b in response[i:i+4])
                if not ip.startswith('127.') and not ip.startswith('0.'):
                    return ip
        return None
    except:
        return None

if __name__ == "__main__":
    test_dns_resolution()
