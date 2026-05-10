#!/usr/bin/env python3
"""
Raw Socket Capture - Захват пакетов через raw sockets без sudo
"""

import sys
import time
import socket
import struct
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class RawSocketCapture:
    """Захват пакетов через raw sockets"""
    
    def __init__(self):
        self.pcap_file = "artifacts/wire_capture.pcap"
        self.captured_packets = []
        self.capture_running = False
        
    def create_pcap_header(self):
        """Создать PCAP header"""
        # PCAP global header
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
    
    def packet_callback(self, packet_data, timestamp):
        """Callback для захвата пакетов"""
        try:
            # Парсим IP заголовок (первые 20 байт)
            if len(packet_data) < 20:
                return
                
            ip_header = packet_data[:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
            
            version_ihl = iph[0]
            version = (version_ihl >> 4) & 0xF
            ihl = (version_ihl & 0xF) * 4
            
            if version != 4 or len(packet_data) < ihl:
                return
                
            protocol = iph[6]
            src_ip = socket.inet_ntoa(iph[8])
            dst_ip = socket.inet_ntoa(iph[9])
            
            # Ищем TCP пакеты
            if protocol == 6:  # TCP
                if len(packet_data) < ihl + 20:
                    return
                    
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
                    'payload_preview': payload[:20].hex() if payload else '',
                    'raw_data': packet_data
                }
                
                self.captured_packets.append(packet_info)
                
                print(f"📦 TCP Packet: {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
                print(f"    Seq: {seq_num}, Ack: {ack_num}")
                print(f"    Payload: {payload_len} bytes")
                if payload_len > 0:
                    print(f"    Preview: {payload[:20].hex()}...")
                    
        except Exception as e:
            print(f"❌ Packet parsing error: {e}")
    
    def start_raw_capture(self, target_host: str, target_port: int, duration: int = 10):
        """Запустить захват через raw socket"""
        print(f"🔍 Starting raw socket capture")
        print(f"  Target: {target_host}:{target_port}")
        print(f"  Duration: {duration} seconds")
        print(f"  PCAP file: {self.pcap_file}")
        
        # Создаем artifacts директорию
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        try:
            # Создаем raw socket
            # На macOS может потребоваться IPPROTO_IP
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            
            print(f"  Raw socket created")
            
            self.capture_running = True
            self.captured_packets = []
            
            start_time = time.time()
            
            while time.time() - start_time < duration and self.capture_running:
                try:
                    # Получаем пакет
                    packet_data, addr = raw_socket.recvfrom(65535)
                    timestamp = time.time()
                    
                    # Фильтруем только нужный трафик
                    if len(packet_data) >= 20:  # Минимум IP заголовок
                        ip_header = packet_data[:20]
                        iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                        dst_ip = socket.inet_ntoa(iph[9])
                        
                        # Проверяем что пакет к нашей цели
                        if dst_ip == target_host:
                            self.packet_callback(packet_data, timestamp)
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Capture error: {e}")
                    break
            
            self.capture_running = False
            raw_socket.close()
            
            print(f"🛑 Capture stopped")
            print(f"  Packets captured: {len(self.captured_packets)}")
            
            # Сохраняем в PCAP
            if self.captured_packets:
                self.save_pcap()
                return True
            else:
                print(f"  No packets captured")
                return False
                
        except Exception as e:
            print(f"❌ Raw socket capture failed: {e}")
            return False
    
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
            
            print(f"  PCAP saved: {self.pcap_file}")
            return True
            
        except Exception as e:
            print(f"❌ PCAP save failed: {e}")
            return False
    
    def test_capture_with_real_traffic(self):
        """Тестировать захват с реальным трафиком"""
        print("🚀 Raw Socket Capture Test")
        print("Цель: Захватить реальные TCP сегменты без sudo")
        print("=" * 60)
        
        # Генерируем тестовый трафик
        print("📤 Generating test traffic...")
        
        # Запускаем захват в фоне
        import threading
        
        def capture_worker():
            # Используем httpbin.org как цель
            return self.start_raw_capture("httpbin.org", 80, duration=15)
        
        capture_thread = threading.Thread(target=capture_worker)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Даем время на запуск захвата
        time.sleep(2)
        
        # Генерируем трафик
        try:
            from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
            from super_dpi_combiner.core.contracts import Request
            
            pipeline = HTTPFragmentation()
            pipeline.chunk_size = 30  # Маленький размер для гарантии фрагментации
            
            request = Request(
                host="httpbin.org",
                port=80,
                method="GET",
                path="/get"
            )
            
            print("📤 Sending fragmented HTTP request...")
            response = pipeline.execute(request)
            
            print(f"  Response: {response.success}")
            print(f"  Status: {response.status_code}")
            print(f"  Data size: {len(response.data)} bytes")
            
        except Exception as e:
            print(f"❌ Traffic generation failed: {e}")
        
        # Ждем завершения захвата
        capture_thread.join(timeout=20)
        
        # Анализируем результаты
        return len(self.captured_packets) > 0

def main():
    """Основная функция"""
    capturer = RawSocketCapture()
    success = capturer.test_capture_with_real_traffic()
    
    print(f"\n📄 Raw Socket Capture: {'VERIFIED' if success else 'NOT VERIFIED'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
