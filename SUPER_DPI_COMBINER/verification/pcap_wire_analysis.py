#!/usr/bin/env python3
"""
PCAP Wire Analysis - Парсер PCAP для анализа packet boundaries и TCP seq
"""

import sys
import struct
import socket
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class PCAPWireAnalyzer:
    """Анализатор PCAP для wire-level доказательств"""
    
    def __init__(self):
        self.packets = []
        self.analysis_results = {}
        
    def parse_pcap_header(self, pcap_data):
        """Парсить PCAP header"""
        if len(pcap_data) < 24:
            return None
            
        magic_number, version_major, version_minor, thiszone, sigfigs, snaplen, network = struct.unpack('<LHHLLLL', pcap_data[:24])
        
        if magic_number != 0xa1b2c3d4:
            return None
            
        return {
            'magic_number': magic_number,
            'version_major': version_major,
            'version_minor': version_minor,
            'snaplen': snaplen,
            'network': network,
            'header_size': 24
        }
    
    def parse_pcap_packet_header(self, pcap_data, offset):
        """Парсить PCAP packet header"""
        if len(pcap_data) < offset + 16:
            return None
            
        ts_sec, ts_usec, caplen, origlen = struct.unpack('<LLLL', pcap_data[offset:offset+16])
        
        return {
            'timestamp': ts_sec + ts_usec / 1000000,
            'caplen': caplen,
            'origlen': origlen,
            'header_size': 16
        }
    
    def parse_ip_header(self, packet_data):
        """Парсить IP header"""
        if len(packet_data) < 20:
            return None
            
        iph = struct.unpack('!BBHHHBBH4s4s', packet_data[:20])
        
        version_ihl = iph[0]
        version = (version_ihl >> 4) & 0xF
        ihl = (version_ihl & 0xF) * 4
        
        if version != 4:
            return None
            
        return {
            'version': version,
            'ihl': ihl,
            'tos': iph[1],
            'total_len': iph[2],
            'id': iph[3],
            'flags': iph[4],
            'frag_offset': iph[5],
            'ttl': iph[6],
            'protocol': iph[7],
            'checksum': iph[8],
            'src_ip': socket.inet_ntoa(iph[9]),
            'dst_ip': socket.inet_ntoa(iph[10]),
            'header_size': ihl
        }
    
    def parse_tcp_header(self, packet_data, ip_header):
        """Парсить TCP header"""
        tcp_offset = ip_header['header_size']
        
        if len(packet_data) < tcp_offset + 20:
            return None
            
        tcph = struct.unpack('!HHLLBBHHH', packet_data[tcp_offset:tcp_offset+20])
        
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
        
        # Размер TCP header
        tcp_header_len = (tcph[12] >> 4) * 4
        
        return {
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
            'window': tcph[6],
            'checksum': tcph[7],
            'urgent_ptr': tcph[8],
            'header_size': tcp_header_len
        }
    
    def parse_packet(self, pcap_data, offset):
        """Парсить полный пакет"""
        # Парсим PCAP packet header
        packet_header = self.parse_pcap_packet_header(pcap_data, offset)
        if not packet_header:
            return None
            
        # Получаем packet data
        packet_start = offset + packet_header['header_size']
        packet_end = packet_start + packet_header['caplen']
        packet_data = pcap_data[packet_start:packet_end]
        
        # Парсим IP header
        ip_header = self.parse_ip_header(packet_data)
        if not ip_header:
            return None
            
        # Парсим TCP header
        tcp_header = self.parse_tcp_header(packet_data, ip_header)
        if not tcp_header:
            return None
            
        # Вычисляем payload
        payload_start = ip_header['header_size'] + tcp_header['header_size']
        payload_size = len(packet_data) - payload_start
        
        if payload_size > 0:
            payload = packet_data[payload_start:]
        else:
            payload = b''
        
        packet = {
            'timestamp': packet_header['timestamp'],
            'ip_header': ip_header,
            'tcp_header': tcp_header,
            'payload_size': payload_size,
            'payload_preview': payload[:20].hex() if payload_size > 0 else '',
            'total_size': len(packet_data)
        }
        
        return packet
    
    def analyze_pcap_file(self, pcap_file_path):
        """Анализировать PCAP файл"""
        print(f"🔍 Analyzing PCAP file: {pcap_file_path}")
        
        try:
            with open(pcap_file_path, 'rb') as f:
                pcap_data = f.read()
            
            if not pcap_data:
                print("  Empty PCAP file")
                return None
            
            # Парсим PCAP header
            pcap_header = self.parse_pcap_header(pcap_data)
            if not pcap_header:
                print("  Invalid PCAP header")
                return None
            
            print(f"  PCAP version: {pcap_header['version_major']}.{pcap_header['version_minor']}")
            print(f"  Network type: {pcap_header['network']}")
            print(f"  Snaplen: {pcap_header['snaplen']}")
            
            # Парсим пакеты
            offset = pcap_header['header_size']
            packet_count = 0
            
            while offset < len(pcap_data):
                packet = self.parse_packet(pcap_data, offset)
                if not packet:
                    break
                
                self.packets.append(packet)
                packet_count += 1
                
                # Переходим к следующему пакету
                packet_header_size = 16
                packet_size = packet['total_size']
                offset += packet_header_size + packet_size
            
            print(f"  Total packets: {packet_count}")
            print(f"  TCP packets: {len([p for p in self.packets if p['tcp_header']])}")
            
            return self.analyze_packets()
            
        except Exception as e:
            print(f"  ❌ PCAP analysis failed: {e}")
            return None
    
    def analyze_packets(self):
        """Анализировать захваченные пакеты"""
        if not self.packets:
            return None
            
        # Фильтруем TCP пакеты
        tcp_packets = [p for p in self.packets if p['tcp_header']]
        
        if not tcp_packets:
            print("  No TCP packets found")
            return None
            
        # Группируем по соединениям
        connections = {}
        for packet in tcp_packets:
            if packet['payload_size'] > 0:  # Только пакеты с данными
                conn_key = f"{packet['ip_header']['src_ip']}:{packet['tcp_header']['src_port']}-{packet['ip_header']['dst_ip']}:{packet['tcp_header']['dst_port']}"
                
                if conn_key not in connections:
                    connections[conn_key] = []
                
                connections[conn_key].append(packet)
        
        analysis = {}
        
        for conn_key, conn_packets in connections.items():
            # Сортируем по timestamp
            conn_packets.sort(key=lambda x: x['timestamp'])
            
            if len(conn_packets) > 1:
                # Анализируем фрагментацию
                seq_numbers = [p['tcp_header']['seq'] for p in conn_packets]
                payload_sizes = [p['payload_size'] for p in conn_packets]
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
                    'inter_packet_delays': inter_packet_delays,
                    'has_fragmentation': len(conn_packets) > 1,
                    'total_payload_size': sum(payload_sizes),
                    'avg_payload_size': sum(payload_sizes) / len(payload_sizes) if payload_sizes else 0
                }
        
        return analysis
    
    def generate_wire_report(self, analysis):
        """Генерировать wire report"""
        if not analysis:
            print("  No analysis data available")
            return
        
        print(f"\n📊 Wire Fragmentation Analysis")
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
                
                # Показываем payload boundaries
                print(f"  Payload boundaries:")
                for i, packet in enumerate(self.packets):
                    if (packet['ip_header']['src_ip'] in conn_key and 
                        packet['tcp_header']['src_port'] in conn_key and
                        packet['payload_size'] > 0):
                        
                        print(f"    Packet {i+1}:")
                        print(f"      Timestamp: {packet['timestamp']}")
                        print(f"      Seq: {packet['tcp_header']['seq']}")
                        print(f"      Payload: {packet['payload_size']} bytes")
                        print(f"      Preview: {packet['payload_preview']}")
                
                # Показываем inter-packet delays
                if conn_analysis['inter_packet_delays']:
                    delays_ms = [d*1000 for d in conn_analysis['inter_packet_delays']]
                    delays_formatted = [f"{d:.2f}" for d in delays_ms]
                            print(f"  Inter-packet delays: {delays_formatted}ms")
                
                # Показываем gaps
                if conn_analysis['gaps']:
                    print(f"  Sequence gaps: {conn_analysis['gaps']}")
            else:
                print(f"  No fragmentation detected")
        
        print(f"\n🎯 Overall Wire Fragmentation: {'VERIFIED' if fragmentation_detected else 'NOT VERIFIED'}")
        
        return fragmentation_detected

def main():
    """Основная функция"""
    analyzer = PCAPWireAnalyzer()
    
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
    
    analysis = analyzer.analyze_pcap_file(found_pcap)
    
    if analysis:
        fragmentation_detected = analyzer.generate_wire_report(analysis)
        
        # Сохраняем результаты
        import json
        with open("PCAP_WIRE_ANALYSIS.json", "w") as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n📄 Results saved to: PCAP_WIRE_ANALYSIS.json")
        
        return 0 if fragmentation_detected else 1
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
