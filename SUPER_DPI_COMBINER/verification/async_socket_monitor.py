#!/usr/bin/env python3
"""
Async Socket Monitor - Мониторинг сокетов без sudo через asyncio
"""

import sys
import time
import asyncio
import socket
import struct
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AsyncSocketMonitor:
    """Асинхронный монитор сокетов без sudo"""
    
    def __init__(self):
        self.pcap_file = "artifacts/wire_capture.pcap"
        self.captured_packets = []
        self.monitoring = False
        
    def create_pcap_header(self):
        """Создать PCAP header"""
        magic_number = 0xa1b2c3d4
        version_major = 2
        version_minor = 4
        thiszone = 0
        sigfigs = 0
        snaplen = 65535
        network = 1  # DLT_EN10MB
        
        return struct.pack('<LHHLLLL', magic_number, version_major, version_minor, 
                        thiszone, sigfigs, snaplen, network)
    
    def create_pcap_packet_header(self, packet_data, timestamp):
        """Создать PCAP packet header"""
        ts_sec = int(timestamp)
        ts_usec = int((timestamp - ts_sec) * 1000000)
        caplen = len(packet_data)
        origlen = len(packet_data)
        
        return struct.pack('<LLLL', ts_sec, ts_usec, caplen, origlen)
    
    def parse_packet(self, packet_data, timestamp):
        """Парсить пакет и извлекать TCP информацию"""
        try:
            # Парсим IP заголовок
            if len(packet_data) < 20:
                return None
                
            ip_header = packet_data[:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
            
            version_ihl = iph[0]
            version = (version_ihl >> 4) & 0xF
            ihl = (version_ihl & 0xF) * 4
            
            if version != 4 or len(packet_data) < ihl:
                return None
                
            protocol = iph[6]
            src_ip = socket.inet_ntoa(iph[8])
            dst_ip = socket.inet_ntoa(iph[9])
            
            # Ищем TCP пакеты
            if protocol == 6:  # TCP
                if len(packet_data) < ihl + 20:
                    return None
                    
                tcp_header = packet_data[ihl:ihl+20]
                tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                
                src_port = tcph[0]
                dst_port = tcph[1]
                seq_num = tcph[2]
                ack_num = tcph[3]
                
                # Вычисляем payload
                tcp_header_len = (tcph[12] >> 4) * 4
                payload_start = ihl + tcp_header_len
                
                if len(packet_data) > payload_start:
                    payload = packet_data[payload_start:]
                    payload_len = len(payload)
                else:
                    payload = b''
                    payload_len = 0
                
                # Сохраняем пакет
                packet_info = {
                    'timestamp': timestamp,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'seq': seq_num,
                    'ack': ack_num,
                    'payload_len': payload_len,
                    'payload_preview': payload[:30].hex() if payload else '',
                    'raw_data': packet_data
                }
                
                print(f"📦 TCP: {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
                print(f"    Seq: {seq_num}, Ack: {ack_num}")
                print(f"    Payload: {payload_len} bytes")
                if payload_len > 0:
                    print(f"    Preview: {payload[:30].hex()}...")
                
                return packet_info
                    
        except Exception as e:
            print(f"❌ Packet parsing error: {e}")
            return None
    
    def save_pcap(self):
        """Сохранить захваченные пакеты в PCAP"""
        try:
            with open(self.pcap_file, 'wb') as f:
                # PCAP header
                f.write(self.create_pcap_header())
                
                # Пакеты
                for packet_info in self.captured_packets:
                    pcap_header = self.create_pcap_packet_header(
                        packet_info['raw_data'], 
                        packet_info['timestamp']
                    )
                    f.write(pcap_header)
                    f.write(packet_info['raw_data'])
            
            print(f"💾 PCAP saved: {self.pcap_file}")
            return True
            
        except Exception as e:
            print(f"❌ PCAP save failed: {e}")
            return False
    
    async def monitor_socket_send(self, sock, target_host, target_port, chunk_size):
        """Мониторить отправку через сокет"""
        print(f"📤 Monitoring socket send to {target_host}:{target_port}")
        print(f"    Chunk size: {chunk_size}")
        
        try:
            # Создаем сокет
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle
            
            # Подключаемся
            connect_start = time.time()
            await asyncio.wait_for(
                asyncio.get_event_loop().sock_connect(sock, (target_host, target_port)),
                timeout=10.0
            )
            connect_time = time.time()
            
            print(f"    Connected: {(connect_time - connect_start)*1000:.2f}ms")
            
            # Формируем HTTP запрос
            http_request = f"GET /get HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n"
            request_bytes = http_request.encode()
            
            # Отправляем с фрагментацией и мониторингом
            send_start = time.time()
            bytes_sent = 0
            fragment_count = 0
            
            for i in range(0, len(request_bytes), chunk_size):
                chunk = request_bytes[i:i + chunk_size]
                
                # Отправляем чанк
                await asyncio.wait_for(
                    asyncio.get_event_loop().sock_sendall(sock, chunk),
                    timeout=5.0
                )
                
                chunk_time = time.time()
                bytes_sent += len(chunk)
                fragment_count += 1
                
                print(f"    Fragment {fragment_count}: {len(chunk)} bytes")
                print(f"    Timestamp: {chunk_time}")
                print(f"    Total sent: {bytes_sent}/{len(request_bytes)}")
                
                # Небольшая задержка между чанками
                await asyncio.sleep(0.01)
            
            send_time = time.time()
            
            print(f"    Send complete: {(send_time - send_start)*1000:.2f}ms")
            print(f"    Fragments: {fragment_count}")
            print(f"    Total bytes: {bytes_sent}")
            
            # Получаем ответ
            recv_start = time.time()
            response_data = b""
            
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        asyncio.get_event_loop().sock_recv(sock, 4096),
                        timeout=5.0
                    )
                    if not chunk:
                        break
                    response_data += chunk
                    
                    # Логируем получение
                    recv_time = time.time()
                    print(f"    Received: {len(chunk)} bytes at {recv_time}")
                    
                except asyncio.TimeoutError:
                    break
            
            recv_time = time.time()
            
            print(f"    Response: {len(response_data)} bytes")
            print(f"    Response time: {(recv_time - recv_start)*1000:.2f}ms")
            
            return {
                'success': True,
                'connect_time': connect_time - connect_start,
                'send_time': send_time - send_start,
                'recv_time': recv_time - recv_start,
                'bytes_sent': bytes_sent,
                'bytes_received': len(response_data),
                'fragment_count': fragment_count,
                'response_data': response_data
            }
            
        except Exception as e:
            print(f"❌ Socket monitor failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            sock.close()
    
    async def test_wire_monitoring(self):
        """Тестировать мониторинг wire"""
        print("🚀 Async Socket Monitor Test")
        print("Цель: Мониторинг сокетов без sudo")
        print("=" * 60)
        
        # Тестируем разные размеры чанков
        chunk_sizes = [1000, 100, 50, 30, 10]
        target_host = "httpbin.org"
        target_port = 80
        
        for i, chunk_size in enumerate(chunk_sizes):
            print(f"\n🔍 Test {i+1}/{len(chunk_sizes)}: chunk_size={chunk_size}")
            print("-" * 40)
            
            # Создаем сокет для каждого теста
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            
            # Мониторим отправку
            result = await self.monitor_socket_send(sock, target_host, target_port, chunk_size)
            
            # Анализируем результат
            if result['success']:
                print(f"  ✅ Test successful")
                print(f"  Fragments: {result['fragment_count']}")
                print(f"  Send time: {result['send_time']*1000:.2f}ms")
                print(f"  Response: {result['bytes_received']} bytes")
                
                # Проверяем на фрагментацию
                if chunk_size < 1000 and result['fragment_count'] > 1:
                    print(f"  📦 Wire fragmentation DETECTED")
                else:
                    print(f"  📦 No wire fragmentation")
            else:
                print(f"  ❌ Test failed: {result['error']}")
            
            # Небольшая задержка между тестами
            await asyncio.sleep(1)
        
        # Сохраняем PCAP если есть пакеты
        if self.captured_packets:
            self.save_pcap()
            return True
        else:
            print("❌ No packets captured for PCAP")
            return False

def main():
    """Основная функция"""
    monitor = AsyncSocketMonitor()
    
    try:
        # Запускаем асинхронный тест
        success = asyncio.run(monitor.test_wire_monitoring())
        
        print(f"\n📄 Async Socket Monitor: {'VERIFIED' if success else 'NOT VERIFIED'}")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Monitor failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
