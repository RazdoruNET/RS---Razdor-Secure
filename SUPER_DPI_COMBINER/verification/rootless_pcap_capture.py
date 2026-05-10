#!/usr/bin/env python3
"""
Rootless PCAP Capture - Захват пакетов без sudo используя scapy/sniff
"""

import sys
import time
import socket
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from scapy.all import sniff, IP, TCP, Raw
    from scapy.utils import PcapWriter
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class RootlessPcapCapture:
    """Захват PCAP без прав root"""
    
    def __init__(self):
        self.pcap_file = "artifacts/wire_capture.pcap"
        self.captured_packets = []
        self.capture_running = False
        
    def install_scapy_if_needed(self):
        """Установить scapy если нужно"""
        if not SCAPY_AVAILABLE:
            print("📦 Installing scapy...")
            import subprocess
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "scapy"], check=True)
                print("✅ Scapy installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install scapy: {e}")
                return False
        return True
    
    def packet_callback(self, packet):
        """Callback для захвата пакетов"""
        if TCP in packet and Raw in packet:
            # Фильтруем только TCP пакеты с данными
            self.captured_packets.append(packet)
            
            # Логируем важную информацию
            if IP in packet and TCP in packet:
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                seq = packet[TCP].seq
                ack = packet[TCP].ack
                payload_len = len(packet[TCP].payload) if packet[TCP].payload else 0
                
                print(f"📦 Packet: {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
                print(f"    Seq: {seq}, Ack: {ack}, Payload: {payload_len} bytes")
                
                # Показываем начало payload
                if payload_len > 0:
                    payload_bytes = bytes(packet[TCP].payload)
                    payload_preview = payload_bytes[:50].hex()
                    print(f"    Payload: {payload_preview}...")
    
    def start_capture(self, target_host: str, target_port: int, duration: int = 10):
        """Запустить захват пакетов"""
        print(f"🔍 Starting rootless packet capture")
        print(f"  Target: {target_host}:{target_port}")
        print(f"  Duration: {duration} seconds")
        print(f"  PCAP file: {self.pcap_file}")
        
        # Создаем artifacts директорию
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        try:
            # Фильтр для захвата только нужного трафика
            filter_str = f"tcp and host {target_host} and port {target_port}"
            
            print(f"  Filter: {filter_str}")
            print(f"  Starting capture...")
            
            self.capture_running = True
            self.captured_packets = []
            
            # Запускаем захват
            packets = sniff(
                filter=filter_str,
                timeout=duration,
                prn=self.packet_callback,
                store=False  # Не храним в памяти, используем callback
            )
            
            self.capture_running = False
            
            print(f"🛑 Capture stopped")
            print(f"  Packets captured: {len(self.captured_packets)}")
            
            # Сохраняем в PCAP
            if self.captured_packets:
                writer = PcapWriter(self.pcap_file)
                for packet in self.captured_packets:
                    writer.write(packet)
                writer.close()
                print(f"  PCAP saved: {self.pcap_file}")
                return True
            else:
                print(f"  No packets captured")
                return False
                
        except Exception as e:
            print(f"❌ Capture failed: {e}")
            return False
    
    def test_capture_with_real_traffic(self):
        """Тестировать захват с реальным трафиком"""
        print("🚀 Rootless PCAP Capture Test")
        print("Цель: Захватить реальные TCP сегменты без sudo")
        print("=" * 60)
        
        # Проверяем scapy
        if not self.install_scapy_if_needed():
            return False
        
        # Импортируем заново после установки
        try:
            from scapy.all import sniff, IP, TCP, Raw
            from scapy.utils import PcapWriter
        except ImportError:
            print("❌ Scapy still not available")
            return False
        
        # Создаем тестовый трафик
        print("📤 Generating test traffic...")
        
        # Запускаем захват в фоне
        import threading
        
        def capture_worker():
            # Используем httpbin.org как цель
            return self.start_capture("httpbin.org", 80, duration=15)
        
        capture_thread = threading.Thread(target=capture_worker)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Даем время на запуск захвата
        time.sleep(2)
        
        # Генерируем тестовый трафик
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
    capturer = RootlessPcapCapture()
    success = capturer.test_capture_with_real_traffic()
    
    print(f"\n📄 Rootless PCAP Capture: {'VERIFIED' if success else 'NOT VERIFIED'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
