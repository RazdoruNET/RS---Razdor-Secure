#!/usr/bin/env python3
"""
PCAP Parser - Упрощенный парсер PCAP для анализа packet boundaries и TCP seq
"""

import sys
import struct
import json
from pathlib import Path

class PCAPParser:
    """Упрощенный PCAP парсер"""
    
    def __init__(self):
        self.packets = []
        
    def parse_pcap_file(self, pcap_file_path):
        """Парсить PCAP файл"""
        print(f"🔍 Parsing PCAP: {pcap_file_path}")
        
        try:
            with open(pcap_file_path, 'rb') as f:
                pcap_data = f.read()
            
            if not pcap_data:
                print("  Empty PCAP file")
                return False
            
            # Парсим PCAP header
            if len(pcap_data) < 24:
                print("  Invalid PCAP header")
                return False
            
            magic_number, version_major, version_minor, thiszone, sigfigs, snaplen, network = struct.unpack('<LHHLLLL', pcap_data[:24])
            
            if magic_number != 0xa1b2c3d4:
                print("  Invalid PCAP magic number")
                return False
            
            print(f"  PCAP version: {version_major}.{version_minor}")
            print(f"  Snaplen: {snaplen}")
            print(f"  Network: {network}")
            
            # Парсим пакеты
            offset = 24
            packet_count = 0
            
            while offset < len(pcap_data):
                # Парсим packet header
                if offset + 16 > len(pcap_data):
                    break
                
                ts_sec, ts_usec, caplen, origlen = struct.unpack('<LLLL', pcap_data[offset:offset+16])
                
                packet_start = offset + 16
                packet_end = packet_start + caplen
                
                if packet_end > len(pcap_data):
                    break
                
                packet_data = pcap_data[packet_start:packet_end]
                
                # Парсим IP и TCP headers
                packet_info = self.parse_packet(packet_data, ts_sec + ts_usec / 1000000)
                
                if packet_info:
                    self.packets.append(packet_info)
                    packet_count += 1
                    
                    # Показываем прогресс
                    if packet_count % 10 == 0:
                        print(f"  Parsed {packet_count} packets...")
                
                offset = packet_start + caplen
            
            print(f"  Total packets parsed: {len(self.packets)}")
            return True
            
        except Exception as e:
            print(f"  ❌ PCAP parsing failed: {e}")
            return False
    
    def parse_packet(self, packet_data, timestamp):
        """Парсить отдельный пакет"""
        try:
            # Парсим IP header
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
            
            return {
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
            
        except Exception as e:
            print(f"  ❌ Packet parsing error: {e}")
            return None
    
    def analyze_packet_boundaries(self):
        """Анализировать границы пакетов"""
        if not self.packets:
            print("  No packets to analyze")
            return None
        
        # Фильтруем TCP пакеты с payload
        tcp_packets = [p for p in self.packets if p and p['payload_len'] > 0]
        
        if not tcp_packets:
            print("  No TCP packets with payload")
            return None
        
        # Группируем по соединениям
        connections = {}
        for packet in tcp_packets:
            conn_key = f"{packet['src_ip']}:{packet['src_port']}-{packet['dst_ip']}:{packet['dst_port']}"
            
            if conn_key not in connections:
                connections[conn_key] = []
            
            connections[conn_key].append(packet)
        
        analysis = {}
        
        for conn_key, conn_packets in connections.items():
            # Сортируем по timestamp
            conn_packets.sort(key=lambda x: x['timestamp'])
            
            if len(conn_packets) > 1:
                # Анализируем фрагментацию
                seq_numbers = [p['seq'] for p in conn_packets]
                payload_sizes = [p['payload_len'] for p in conn_packets]
                timestamps = [p['timestamp'] for p in conn_packets]
                
                # Проверяем монотонность sequence numbers
                is_monotonic = all(seq_numbers[i] <= seq_numbers[i+1] for i in range(len(seq_numbers)-1))
                
                # Вычисляем gaps
                gaps = []
                for i in range(len(seq_numbers)-1):
                    expected_next = seq_numbers[i] + payload_sizes[i]
                    actual_next = seq_numbers[i+1]
                    if actual_next != expected_next:
                        gaps.append({
                            'expected': expected_next,
                            'actual': actual_next,
                            'gap': actual_next - expected_next
                        })
                
                # Вычисляем inter-packet delays
                inter_packet_delays = []
                for i in range(len(timestamps)-1):
                    delay = timestamps[i+1] - timestamps[i]
                    inter_packet_delays.append(delay)
                
                analysis[conn_key] = {
                    'packet_count': len(conn_packets),
                    'sequence_numbers': seq_numbers,
                    'payload_sizes': payload_sizes,
                    'timestamps': timestamps,
                    'is_monotonic': is_monotonic,
                    'gaps': gaps,
                    'has_fragmentation': len(conn_packets) > 1,
                    'inter_packet_delays': inter_packet_delays,
                    'total_payload_size': sum(payload_sizes),
                    'avg_payload_size': sum(payload_sizes) / len(payload_sizes) if payload_sizes else 0,
                    'first_packet_time': timestamps[0],
                    'last_packet_time': timestamps[-1],
                    'duration': timestamps[-1] - timestamps[0]
                }
            else:
                analysis[conn_key] = {
                    'packet_count': 1,
                    'has_fragmentation': False
                }
        
        return analysis
    
    def generate_report(self, analysis):
        """Генерировать отчет"""
        if not analysis:
            print("  No analysis data")
            return False
        
        print(f"\n📊 PCAP Analysis Report")
        print("=" * 60)
        
        fragmentation_detected = False
        
        for conn_key, conn_analysis in analysis.items():
            print(f"\n🔗 Connection: {conn_key}")
            print(f"  Packets: {conn_analysis['packet_count']}")
            print(f"  Has fragmentation: {conn_analysis['has_fragmentation']}")
            
            if conn_analysis['has_fragmentation']:
                fragmentation_detected = True
                
                print(f"  Sequence numbers: {conn_analysis['sequence_numbers']}")
                print(f"  Payload sizes: {conn_analysis['payload_sizes']}")
                print(f"  Total payload: {conn_analysis['total_payload_size']} bytes")
                print(f"  Avg payload: {conn_analysis['avg_payload_size']:.1f} bytes")
                print(f"  Duration: {conn_analysis['duration']:.3f}s")
                
                # Показываем payload boundaries
                print(f"  Payload boundaries:")
                for i, seq in enumerate(conn_analysis['sequence_numbers']):
                    payload = conn_analysis['payload_sizes'][i]
                    timestamp = conn_analysis['timestamps'][i]
                    print(f"    Packet {i+1}: seq={seq}, payload={payload} bytes, time={timestamp}")
                
                # Показываем inter-packet delays
                if conn_analysis['inter_packet_delays']:
                    delays_ms = [d*1000 for d in conn_analysis['inter_packet_delays']]
                    delays_formatted = [f"{d:.2f}" for d in delays_ms]
                    print(f"  Inter-packet delays: {delays_formatted}ms")
                
                # Показываем gaps
                if conn_analysis['gaps']:
                    print(f"  Sequence gaps: {conn_analysis['gaps']}")
            else:
                print(f"  No fragmentation")
        
        print(f"\n🎯 Overall Fragmentation: {'VERIFIED' if fragmentation_detected else 'NOT VERIFIED'}")
        
        return fragmentation_detected

def main():
    """Основная функция"""
    parser = PCAPParser()
    
    # Ищем PCAP файлы
    pcap_files = [
        "artifacts/wire_capture.pcap",
        "artifacts/internet_capture.pcap",
        "wire_capture.pcap",
        "internet_capture.pcap"
    ]
    
    found_pcap = None
    for pcap_file in pcap_files:
        if Path(pcap_file).exists():
            found_pcap = pcap_file
            break
    
    if not found_pcap:
        print("❌ No PCAP files found")
        print("  Expected files:")
        for pcap_file in pcap_files:
            print(f"    {pcap_file}")
        return 1
    
    # Парсим PCAP
    if parser.parse_pcap_file(found_pcap):
        # Анализируем
        analysis = parser.analyze_packet_boundaries()
        
        if analysis:
            fragmentation_detected = parser.generate_report(analysis)
            
            # Сохраняем результаты
            with open("PCAP_PARSER_RESULTS.json", "w") as f:
                json.dump(analysis, f, indent=2)
            
            print(f"\n📄 Results saved to: PCAP_PARSER_RESULTS.json")
            
            return 0 if fragmentation_detected else 1
    
    return 1

if __name__ == "__main__":
    import socket
    sys.exit(main())
