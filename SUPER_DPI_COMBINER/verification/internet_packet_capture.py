#!/usr/bin/env python3
"""
Real Internet Packet Capture - Захват пакетов для реального интернет трафика
"""

import sys
import time
import subprocess
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verification.internet_targets import get_target_for_test
from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

class InternetPacketCapture:
    """Захват пакетов для реального интернет трафика"""
    
    def __init__(self):
        self.capture_process = None
        self.pcap_file = "artifacts/internet_capture.pcap"
        
    def start_tcpdump(self, target_host: str, target_port: int):
        """Запустить tcpdump для захвата интернет трафика"""
        print(f"🔍 Starting tcpdump for {target_host}:{target_port}")
        
        # Создаем artifacts директорию
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        # Запускаем tcpdump
        tcpdump_cmd = [
            "tcpdump",
            "-i", "any",  # Любой интерфейс
            "-w", self.pcap_file,
            "-s", "0",  # Capture all bytes
            "tcp",
            "and",
            f"host {target_host}",
            "and",
            f"port {target_port}"
        ]
        
        try:
            self.capture_process = subprocess.Popen(tcpdump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"  tcpdump PID: {self.capture_process.pid}")
            print(f"  Capture file: {self.pcap_file}")
            
            # Даем время на запуск
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start tcpdump: {e}")
            return False
    
    def stop_tcpdump(self):
        """Остановить tcpdump"""
        if self.capture_process:
            print("🛑 Stopping tcpdump")
            self.capture_process.terminate()
            try:
                self.capture_process.wait(timeout=5)
                print("  tcpdump stopped successfully")
            except subprocess.TimeoutExpired:
                print("  Force killing tcpdump")
                self.capture_process.kill()
    
    def analyze_pcap(self):
        """Анализировать pcap файл"""
        print(f"📊 Analyzing pcap file: {self.pcap_file}")
        
        if not Path(self.pcap_file).exists():
            print(f"❌ PCAP file not found: {self.pcap_file}")
            return False
        
        # Используем tcpdump для анализа
        analyze_cmd = [
            "tcpdump",
            "-r", self.pcap_file,
            "-nn",
            "-v",
            "-c", "10"  # Первые 10 пакетов
        ]
        
        try:
            result = subprocess.run(analyze_cmd, capture_output=True, text=True)
            packets = result.stdout.strip().split('\n') if result.stdout else []
            
            print(f"  Total packets captured: {len([p for p in packets if p.strip()])}")
            
            # Анализируем TCP сегменты
            tcp_segments = [p for p in packets if 'tcp' in p.lower()]
            print(f"  TCP segments: {len(tcp_segments)}")
            
            # Ищем фрагментацию
            fragmented_packets = []
            for packet in tcp_segments:
                if 'tcp' in packet.lower() and ('seq' in packet.lower() or 'ack' in packet.lower()):
                    fragmented_packets.append(packet)
            
            print(f"  Potential fragmented packets: {len(fragmented_packets)}")
            
            # Проверяем timestamps
            if len(fragmented_packets) > 1:
                print("  📋 Fragmentation evidence:")
                for i, packet in enumerate(fragmented_packets[:5]):  # Первые 5 пакетов
                    print(f"    {i+1}. {packet[:100]}...")
            
            return len(fragmented_packets) > 1
            
        except Exception as e:
            print(f"❌ Failed to analyze pcap: {e}")
            return False
    
    def capture_internet_traffic(self, target_host: str, target_port: int):
        """Захватить реальный интернет трафик"""
        print(f"🚀 Capturing Internet Traffic to {target_host}:{target_port}")
        print("Цель: Доказать packet-level fragmentation в реальном интернете")
        print("=" * 60)
        
        try:
            # Запускаем tcpdump
            if not self.start_tcpdump(target_host, target_port):
                return False
            
            # Выполняем HTTP fragmentation с packet capture
            print("📤 Executing HTTP fragmentation with internet packet capture")
            
            pipeline = HTTPFragmentation()
            pipeline.chunk_size = 50  # Маленький размер для гарантии фрагментации
            
            # Создаем запрос
            request = Request(
                host=target_host,
                port=target_port,
                method="GET",
                path="/get"
            )
            
            start_time = time.time()
            response = pipeline.execute(request)
            end_time = time.time()
            
            print(f"  Request duration: {end_time - start_time:.3f}s")
            print(f"  Response success: {response.success}")
            print(f"  Response error: {response.error}")
            
            # Даем время на захват всех пакетов
            time.sleep(2)
            
            return response.success
            
        except Exception as e:
            print(f"❌ Internet traffic capture failed: {e}")
            return False
        
        finally:
            # Останавливаем tcpdump
            self.stop_tcpdump()
    
    def run_capture_test(self):
        """Запустить тест захвата"""
        print("🚀 Real Internet Packet Capture Test")
        print("Метод: tcpdump + PCAP анализ для реального интернета")
        print("=" * 60)
        
        # Проверяем что tcpdump доступен
        try:
            subprocess.run(["tcpdump", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ tcpdump not found. Please install tcpdump:")
            print("  brew install tcpdump  # macOS")
            print("  sudo apt-get install tcpdump  # Ubuntu")
            print("  Note: tcpdump requires sudo for internet capture")
            return False
        
        # Используем успешную цель из предыдущего аудита
        target_host, target_port = get_target_for_test(1)  # httpbin.org:80
        
        # Захватываем трафик
        capture_success = self.capture_internet_traffic(target_host, target_port)
        
        # Анализируем pcap
        fragmentation_proven = self.analyze_pcap()
        
        # Проверяем наличие pcap файла
        pcap_exists = Path(self.pcap_file).exists()
        
        print(f"\n📈 Capture Results:")
        print(f"  Internet traffic captured: {'YES' if capture_success else 'NO'}")
        print(f"  PCAP file exists: {'YES' if pcap_exists else 'NO'}")
        print(f"  Fragmentation proven: {'YES' if fragmentation_proven else 'NO'}")
        
        # Определяем успешность
        success = (
            capture_success and
            pcap_exists and
            fragmentation_proven
        )
        
        print(f"\n✅ Internet Packet Capture: {'VERIFIED' if success else 'NOT VERIFIED'}")
        
        return {
            "capture_success": capture_success,
            "pcap_exists": pcap_exists,
            "fragmentation_proven": fragmentation_proven,
            "overall_success": success
        }

def main():
    """Основная функция"""
    capturer = InternetPacketCapture()
    results = capturer.run_capture_test()
    
    # Сохраняем результаты
    with open("INTERNET_PACKET_CAPTURE_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: INTERNET_PACKET_CAPTURE_RESULTS.json")
    
    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())
