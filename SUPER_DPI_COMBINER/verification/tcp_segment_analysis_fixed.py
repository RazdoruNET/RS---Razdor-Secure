#!/usr/bin/env python3
"""
TCP Segment Analysis - Анализ TCP сегментов для доказательства wire fragmentation (исправленная версия)
"""

import sys
import time
import struct
import socket
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TCPSegmentAnalyzer:
    """Анализатор TCP сегментов"""
    
    def __init__(self):
        self.segments = []
        self.analysis_results = {}
        
    def parse_tcp_segment(self, packet_data, timestamp):
        """Парсить TCP сегмент"""
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
            if protocol != 6:  # TCP
                return None
                
            if len(packet_data) < ihl + 20:
                return None
                    
            tcp_header = packet_data[ihl:ihl+20]
            tcph = struct.unpack('!HHLLBBHHH', tcp_header)
            
            src_port = tcph[0]
            dst_port = tcph[1]
            seq_num = tcph[2]
            ack_num = tcph[3]
            
            # Флаги TCP
            flags = tcph[5]
            fin = (flags & 0x01) != 0
            syn = (flags & 0x02) != 0
            rst = (flags & 0x04) != 0
            psh = (flags & 0x08) != 0
            ack = (flags & 0x10) != 0
            urg = (flags & 0x20) != 0
            
            # Вычисляем payload
            tcp_header_len = (tcph[12] >> 4) * 4
            payload_start = ihl + tcp_header_len
            
            if len(packet_data) > payload_start:
                payload = packet_data[payload_start:]
                payload_len = len(payload)
            else:
                payload = b''
                payload_len = 0
            
            segment = {
                'timestamp': timestamp,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'src_port': src_port,
                'dst_port': dst_port,
                'seq': seq_num,
                'ack': ack_num,
                'flags': {
                    'fin': fin,
                    'syn': syn,
                    'rst': rst,
                    'psh': psh,
                    'ack': ack,
                    'urg': urg
                },
                'payload_len': payload_len,
                'payload_preview': payload[:20].hex() if payload else '',
                'total_len': len(packet_data)
            }
            
            return segment
            
        except Exception as e:
            print(f"❌ TCP parsing error: {e}")
            return None
    
    def analyze_wire_fragmentation(self, segments):
        """Анализировать wire фрагментацию"""
        if not segments:
            return None
            
        # Группируем по соединениям
        connections = {}
        for segment in segments:
            conn_key = f"{segment['src_ip']}:{segment['src_port']}-{segment['dst_ip']}:{segment['dst_port']}"
            if conn_key not in connections:
                connections[conn_key] = []
            connections[conn_key].append(segment)
        
        analysis = {}
        
        for conn_key, conn_segments in connections.items():
            # Сортируем по timestamp
            conn_segments.sort(key=lambda x: x['timestamp'])
            
            # Ищем фрагментацию
            payload_segments = [s for s in conn_segments if s['payload_len'] > 0]
            
            if len(payload_segments) > 1:
                # Анализируем последовательность
                seq_numbers = [s['seq'] for s in payload_segments]
                payloads = [s['payload_len'] for s in payload_segments]
                timestamps = [s['timestamp'] for s in payload_segments]
                
                # Проверяем монотонность sequence numbers
                is_monotonic = all(seq_numbers[i] <= seq_numbers[i+1] for i in range(len(seq_numbers)-1))
                
                # Вычисляем gaps
                gaps = []
                for i in range(len(seq_numbers)-1):
                    expected_next = seq_numbers[i] + payloads[i]
                    actual_next = seq_numbers[i+1]
                    if actual_next != expected_next:
                        gaps.append({
                            'expected': expected_next,
                            'actual': actual_next,
                            'gap': actual_next - expected_next
                        })
                
                analysis[conn_key] = {
                    'total_segments': len(conn_segments),
                    'payload_segments': len(payload_segments),
                    'sequence_numbers': seq_numbers,
                    'payload_sizes': payloads,
                    'timestamps': timestamps,
                    'is_monotonic': is_monotonic,
                    'gaps': gaps,
                    'has_fragmentation': len(payload_segments) > 1,
                    'inter_segment_delays': [
                        timestamps[i+1] - timestamps[i] 
                        for i in range(len(timestamps)-1)
                    ]
                }
            else:
                analysis[conn_key] = {
                    'total_segments': len(conn_segments),
                    'payload_segments': len(payload_segments),
                    'has_fragmentation': False
                }
        
        return analysis
    
    async def capture_segments_with_monitoring(self, target_host, target_port, chunk_size):
        """Захватить сегменты с мониторингом"""
        print(f"🔍 Capturing segments: {target_host}:{target_port}")
        print(f"    Chunk size: {chunk_size}")
        
        segments = []
        
        try:
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setblocking(False)
            
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
            
            # Отправляем с фрагментацией
            send_start = time.time()
            fragment_count = 0
            
            for i in range(0, len(request_bytes), chunk_size):
                chunk = request_bytes[i:i + chunk_size]
                
                # Отправляем чанк
                await asyncio.wait_for(
                    asyncio.get_event_loop().sock_sendall(sock, chunk),
                    timeout=5.0
                )
                
                fragment_time = time.time()
                fragment_count += 1
                
                print(f"    Fragment {fragment_count}: {len(chunk)} bytes")
                print(f"    Timestamp: {fragment_time}")
                
                # Небольшая задержка
                await asyncio.sleep(0.01)
            
            send_time = time.time()
            
            print(f"    Send complete: {(send_time - send_start)*1000:.2f}ms")
            print(f"    Fragments: {fragment_count}")
            
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
                    
                    # Парсим каждый полученный сегмент
                    segment = self.parse_tcp_segment(chunk, time.time())
                    if segment:
                        segments.append(segment)
                        
                except asyncio.TimeoutError:
                    break
            
            recv_time = time.time()
            
            print(f"    Response: {len(response_data)} bytes")
            print(f"    Response time: {(recv_time - recv_start)*1000:.2f}ms")
            print(f"    Segments captured: {len(segments)}")
            
            sock.close()
            
            return {
                'success': True,
                'connect_time': connect_time - connect_start,
                'send_time': send_time - send_start,
                'recv_time': recv_time - recv_start,
                'fragment_count': fragment_count,
                'bytes_sent': len(request_bytes),
                'bytes_received': len(response_data),
                'segments': segments
            }
            
        except Exception as e:
            print(f"❌ Segment capture failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'segments': []
            }
    
    async def run_segment_analysis(self):
        """Запустить анализ сегментов"""
        print("🚀 TCP Segment Analysis")
        print("Цель: Доказать wire fragmentation")
        print("=" * 60)
        
        target_host = "httpbin.org"
        target_port = 80
        
        # Тестируем разные размеры чанков
        chunk_sizes = [1000, 100, 50, 30, 10]
        
        for i, chunk_size in enumerate(chunk_sizes):
            print(f"\n🔍 Test {i+1}/{len(chunk_sizes)}: chunk_size={chunk_size}")
            print("-" * 40)
            
            result = await self.capture_segments_with_monitoring(target_host, target_port, chunk_size)
            
            if result['success']:
                # Анализируем сегменты
                analysis = self.analyze_wire_fragmentation(result['segments'])
                
                if analysis:
                    for conn_key, conn_analysis in analysis.items():
                        print(f"  Connection: {conn_key}")
                        print(f"    Total segments: {conn_analysis['total_segments']}")
                        print(f"    Payload segments: {conn_analysis['payload_segments']}")
                        print(f"    Has fragmentation: {conn_analysis['has_fragmentation']}")
                        
                        if conn_analysis['has_fragmentation']:
                            print(f"    Sequence numbers: {conn_analysis['sequence_numbers']}")
                            print(f"    Payload sizes: {conn_analysis['payload_sizes']}")
                            delays = conn_analysis['inter_segment_delays']
                            print(f"    Inter-segment delays: {[d*1000:.2f for d in delays]}ms")
                            
                            # Проверяем границы payload
                            payloads = []
                            for segment in result['segments']:
                                if segment['payload_len'] > 0:
                                    payloads.append(segment['payload_preview'])
                                    
                            print(f"    Payload boundaries:")
                            for j, payload in enumerate(payloads):
                                print(f"      Segment {j+1}: {payload}")
                        else:
                            print(f"    No wire fragmentation")
                
                self.analysis_results[chunk_size] = {
                    'result': result,
                    'analysis': analysis
                }
            
            # Задержка между тестами
            await asyncio.sleep(1)
        
        # Итоговый анализ
        self.generate_final_report()
    
    def generate_final_report(self):
        """Генерировать финальный отчет"""
        print(f"\n📊 Final TCP Segment Analysis")
        print("=" * 60)
        
        fragmentation_detected = False
        
        for chunk_size, data in self.analysis_results.items():
            result = data['result']
            analysis = data['analysis']
            
            print(f"\nChunk Size {chunk_size}:")
            print(f"  Success: {result['success']}")
            print(f"  Fragments: {result['fragment_count']}")
            print(f"  Segments captured: {len(result['segments'])}")
            
            if analysis:
                for conn_key, conn_analysis in analysis.items():
                    if conn_analysis['has_fragmentation']:
                        fragmentation_detected = True
                        print(f"  📦 Wire fragmentation DETECTED")
                        print(f"    Sequence numbers: {conn_analysis['sequence_numbers']}")
                        print(f"    Payload sizes: {conn_analysis['payload_sizes']}")
                    else:
                        print(f"  📦 No wire fragmentation")
        
        print(f"\n🎯 Overall Wire Fragmentation: {'VERIFIED' if fragmentation_detected else 'NOT VERIFIED'}")
        
        # Сохраняем результаты
        import json
        with open("TCP_SEGMENT_ANALYSIS_FIXED.json", "w") as f:
            json.dump(self.analysis_results, f, indent=2)
        
        print(f"📄 Results saved to: TCP_SEGMENT_ANALYSIS_FIXED.json")
        
        return fragmentation_detected

async def main():
    """Основная функция"""
    analyzer = TCPSegmentAnalyzer()
    fragmentation_detected = await analyzer.run_segment_analysis()
    
    return 0 if fragmentation_detected else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
