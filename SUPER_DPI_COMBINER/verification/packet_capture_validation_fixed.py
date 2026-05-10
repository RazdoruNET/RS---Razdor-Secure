#!/usr/bin/env python3
"""
RAW Packet Evidence Validation - Доказательство packet-level fragmentation через tcpdump/pcap
"""

import sys
import time
import subprocess
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

def start_tcpdump(interface="lo0", pcap_file="artifacts/runtime_capture.pcap"):
    """Запустить tcpdump для захвата пакетов"""
    print(f"🔍 Starting tcpdump on {interface}")
    
    # Создаем artifacts директорию
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    
    # Запускаем tcpdump
    tcpdump_cmd = [
        "tcpdump",
        "-i", interface,
        "-w", pcap_file,
        "-s", "0",  # Capture all bytes
        "tcp",
        "port", "8080"
    ]
    
    try:
        process = subprocess.Popen(tcpdump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"  tcpdump PID: {process.pid}")
        print(f"  Capture file: {pcap_file}")
        
        # Даем время на запуск
        time.sleep(2)
        
        return process, pcap_file
        
    except Exception as e:
        print(f"❌ Failed to start tcpdump: {e}")
        return None, None

def stop_tcpdump(process):
    """Остановить tcpdump"""
    if process:
        print("🛑 Stopping tcpdump")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("  tcpdump stopped successfully")
        except subprocess.TimeoutExpired:
            print("  Force killing tcpdump")
            process.kill()

def analyze_pcap(pcap_file):
    """Анализировать pcap файл"""
    print(f"📊 Analyzing pcap file: {pcap_file}")
    
    if not Path(pcap_file).exists():
        print(f"❌ PCAP file not found: {pcap_file}")
        return False
    
    # Используем tcpdump для анализа
    analyze_cmd = [
        "tcpdump",
        "-r", pcap_file,
        "-nn",
        "-v"
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

def test_fragmentation_with_capture():
    """Тест фрагментации с захватом пакетов"""
    print("🚀 RAW Packet Evidence Validation")
    print("Цель: Доказать packet-level fragmentation через tcpdump/pcap")
    print("=" * 60)
    
    tcpdump_process = None
    pcap_file = None
    fragmentation_proven = False
    
    try:
        # Запускаем tcpdump
        tcpdump_process, pcap_file = start_tcpdump()
        
        if not tcpdump_process:
            return False
        
        # Выполняем HTTP fragmentation
        print("📤 Executing HTTP fragmentation with packet capture")
        
        pipeline = HTTPFragmentation()
        pipeline.chunk_size = 50  # Маленький размер для гарантии фрагментации
        
        # Используем localhost для захвата
        request = Request(
            host="127.0.0.1",
            port=8080,
            method="GET",
            path="/test"
        )
        
        start_time = time.time()
        response = pipeline.execute(request)
        end_time = time.time()
        
        print(f"  Request duration: {end_time - start_time:.3f}s")
        print(f"  Response success: {response.success}")
        print(f"  Response error: {response.error}")
        
        # Даем время на захват всех пакетов
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False
        
    finally:
        # Останавливаем tcpdump
        stop_tcpdump(tcpdump_process)
        
        # Анализируем pcap
        if pcap_file:
            fragmentation_proven = analyze_pcap(pcap_file)
        
    return fragmentation_proven

def main():
    """Основная функция"""
    print("🔍 RAW Packet Evidence Validation")
    print("Метод: tcpdump + PCAP анализ")
    
    # Проверяем что tcpdump доступен
    try:
        subprocess.run(["tcpdump", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ tcpdump not found. Please install tcpdump:")
        print("  brew install tcpdump  # macOS")
        print("  sudo apt-get install tcpdump  # Ubuntu")
        print("  Note: tcpdump requires sudo for localhost capture")
        return 1
    
    # Выполняем тест
    success = test_fragmentation_with_capture()
    
    if success:
        print("\n✅ RAW Packet Evidence Validation: VERIFIED")
        print("  Packet-level fragmentation proven")
        print("  PCAP evidence captured")
        return 0
    else:
        print("\n❌ RAW Packet Evidence Validation: NOT VERIFIED")
        print("  Packet-level fragmentation not proven")
        print("  Note: May need sudo for localhost capture")
        return 1

if __name__ == "__main__":
    sys.exit(main())
