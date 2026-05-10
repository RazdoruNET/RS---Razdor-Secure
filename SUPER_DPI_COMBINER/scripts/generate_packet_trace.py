#!/usr/bin/env python3
"""
Generate Runtime Packet Proof - JSONL trace с реальными packet events
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from super_dpi_combiner.core.packet_capture import get_packet_capture_layer, enable_packet_capture, clear_capture_events
from super_dpi_combiner.pipelines.http_fragmentation import HTTPFragmentation
from super_dpi_combiner.core.contracts import Request

def generate_packet_trace():
    """Генерирует packet trace с реальными событиями"""
    print("🔍 Generating Runtime Packet Proof")
    
    # Включаем packet capture
    enable_packet_capture()
    clear_capture_events()
    
    # Создаем JSONL файл
    with open('PACKET_EXECUTION_TRACE.jsonl', 'w') as f:
        # Записываем начало trace
        f.write(json.dumps({
            "ts": time.time(),
            "event": "trace_start"
        }) + '\n')
        
        # Выполняем HTTP fragmentation для packet capture
        pipeline = HTTPFragmentation()
        pipeline.chunk_size = 50  # Маленький размер для множества чанков
        
        request = Request(
            host="httpbin.org",
            port=80,
            method="GET",
            path="/get"
        )
        
        # Записываем начало pipeline
        f.write(json.dumps({
            "ts": time.time(),
            "event": "pipeline_start",
            "pipeline": "HTTPFragmentation"
        }) + '\n')
        
        # Выполняем запрос
        response = pipeline.execute(request)
        
        # Получаем захваченные события
        events = get_packet_capture_layer().get_events()
        
        # Записываем packet события в JSONL
        for event in events:
            packet_event = {
                "ts": event.timestamp,
                "event": event.event,
                "bytes": event.bytes,
                "pipeline": "HTTPFragmentation"
            }
            
            if event.remote_host:
                packet_event["remote_host"] = event.remote_host
                packet_event["remote_port"] = event.remote_port
            
            if event.data_preview:
                packet_event["data_preview"] = event.data_preview
            
            f.write(json.dumps(packet_event) + '\n')
        
        # Записываем завершение pipeline
        f.write(json.dumps({
            "ts": time.time(),
            "event": "pipeline_finish",
            "pipeline": "HTTPFragmentation",
            "success": response.success,
            "status_code": response.status_code
        }) + '\n')
        
        # Записываем конец trace
        f.write(json.dumps({
            "ts": time.time(),
            "event": "trace_end"
        }) + '\n')
    
    # Анализируем trace
    with open('PACKET_EXECUTION_TRACE.jsonl', 'r') as f:
        lines = f.readlines()
    
    events = [json.loads(line) for line in lines]
    
    connect_events = [e for e in events if e["event"] == "socket_connect"]
    send_events = [e for e in events if e["event"] == "socket_send"]
    recv_events = [e for e in events if e["event"] == "socket_recv"]
    close_events = [e for e in events if e["event"] == "socket_close"]
    
    print(f"📊 Packet Trace Analysis:")
    print(f"  Connect events: {len(connect_events)}")
    print(f"  Send events: {len(send_events)}")
    print(f"  Recv events: {len(recv_events)}")
    print(f"  Close events: {len(close_events)}")
    print(f"  Total events: {len(events)}")
    
    # Проверяем минимальные требования
    requirements_met = (
        len(connect_events) >= 1 and
        len(send_events) >= 2 and
        len(recv_events) >= 1
    )
    
    print(f"  Requirements met: {'YES' if requirements_met else 'NO'}")
    print(f"  Trace file: PACKET_EXECUTION_TRACE.jsonl")
    
    return requirements_met

def main():
    """Основная функция"""
    success = generate_packet_trace()
    
    if success:
        print("✅ Runtime Packet Proof generated successfully")
        return 0
    else:
        print("❌ Runtime Packet Proof generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
