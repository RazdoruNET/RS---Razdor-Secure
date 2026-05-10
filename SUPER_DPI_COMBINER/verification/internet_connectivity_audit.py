#!/usr/bin/env python3
"""
Real Internet Connectivity Audit - Проверка реальной связности с интернет целями
"""

import sys
import time
import socket
import json
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verification.internet_targets import TARGETS, TEST_PATHS, FRAGMENTATION_SCENARIOS

class InternetConnectivityAuditor:
    """Аудитор реальной интернет связности"""
    
    def __init__(self):
        self.results = []
        
    def measure_dns_resolution(self, host: str) -> dict:
        """Измерить DNS resolution"""
        print(f"🔍 Testing DNS resolution for {host}")
        
        try:
            start_time = time.time()
            
            # Используем getaddrinfo для DNS resolution
            addr_info = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            end_time = time.time()
            
            dns_time = (end_time - start_time) * 1000  # в мс
            
            result = {
                "host": host,
                "dns_success": True,
                "dns_ms": dns_time,
                "resolved_ips": [info[4][0] for info in addr_info],
                "timestamp": time.time()
            }
            
            print(f"  DNS success: {dns_time:.2f}ms")
            print(f"  Resolved IPs: {result['resolved_ips']}")
            
        except Exception as e:
            result = {
                "host": host,
                "dns_success": False,
                "dns_ms": -1,
                "error": str(e),
                "timestamp": time.time()
            }
            
            print(f"  DNS failed: {e}")
        
        return result
    
    def measure_tcp_connect(self, host: str, port: int) -> dict:
        """Измерить TCP connect"""
        print(f"🔗 Testing TCP connect to {host}:{port}")
        
        try:
            start_time = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            sock.connect((host, port))
            end_time = time.time()
            
            connect_time = (end_time - start_time) * 1000  # в мс
            
            sock.close()
            
            result = {
                "host": host,
                "port": port,
                "connect_success": True,
                "connect_ms": connect_time,
                "timestamp": time.time()
            }
            
            print(f"  Connect success: {connect_time:.2f}ms")
            
        except Exception as e:
            result = {
                "host": host,
                "port": port,
                "connect_success": False,
                "connect_ms": -1,
                "error": str(e),
                "timestamp": time.time()
            }
            
            print(f"  Connect failed: {e}")
        
        return result
    
    def measure_http_request(self, host: str, port: int, path: str = "/get", chunk_size: int = 1000) -> dict:
        """Измерить HTTP request"""
        print(f"📤 Testing HTTP request to {host}:{port}{path} (chunk_size: {chunk_size})")
        
        try:
            start_time = time.time()
            
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            # Connect
            connect_start = time.time()
            sock.connect((host, port))
            connect_time = (time.time() - connect_start) * 1000
            
            # Формируем HTTP request
            http_request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            request_bytes = http_request.encode()
            
            # Отправляем с фрагментацией
            send_start = time.time()
            bytes_sent = 0
            for i in range(0, len(request_bytes), chunk_size):
                chunk = request_bytes[i:i + chunk_size]
                sock.send(chunk)
                bytes_sent += len(chunk)
                time.sleep(0.001)  # Небольшая задержка между чанками
            
            send_time = (time.time() - send_start) * 1000
            
            # Получаем ответ
            recv_start = time.time()
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            recv_time = (time.time() - recv_start) * 1000
            end_time = time.time()
            
            sock.close()
            
            # Анализируем ответ
            response_text = response_data.decode('utf-8', errors='ignore')
            first_line = response_text.split('\r\n')[0] if response_text else ""
            
            # Определяем success
            success = "200" in first_line
            status_code = 200
            if "200" in first_line:
                status_code = 200
            elif "404" in first_line:
                status_code = 404
            elif "403" in first_line:
                status_code = 403
            elif "500" in first_line:
                status_code = 500
            
            result = {
                "host": host,
                "port": port,
                "path": path,
                "chunk_size": chunk_size,
                "http_success": success,
                "status_code": status_code,
                "dns_ms": -1,  # Будет заполнено отдельно
                "connect_ms": connect_time,
                "send_ms": send_time,
                "recv_ms": recv_time,
                "response_ms": (end_time - start_time) * 1000,
                "bytes_sent": bytes_sent,
                "bytes_received": len(response_data),
                "fragment_count": (len(request_bytes) + chunk_size - 1) // chunk_size,
                "timestamp": time.time()
            }
            
            print(f"  HTTP success: {success}")
            print(f"  Status code: {status_code}")
            print(f"  Response time: {result['response_ms']:.2f}ms")
            print(f"  Bytes sent: {bytes_sent}")
            print(f"  Bytes received: {len(response_data)}")
            print(f"  Fragment count: {result['fragment_count']}")
            
        except Exception as e:
            result = {
                "host": host,
                "port": port,
                "path": path,
                "chunk_size": chunk_size,
                "http_success": False,
                "status_code": 0,
                "dns_ms": -1,
                "connect_ms": -1,
                "send_ms": -1,
                "recv_ms": -1,
                "response_ms": -1,
                "bytes_sent": 0,
                "bytes_received": 0,
                "fragment_count": 0,
                "error": str(e),
                "timestamp": time.time()
            }
            
            print(f"  HTTP failed: {e}")
        
        return result
    
    def audit_target(self, host: str, port: int):
        """Аудировать одну цель"""
        print(f"\n🎯 Auditing target: {host}:{port}")
        print("=" * 50)
        
        target_results = []
        
        # DNS resolution
        dns_result = self.measure_dns_resolution(host)
        target_results.append(dns_result)
        
        # TCP connect
        connect_result = self.measure_tcp_connect(host, port)
        target_results.append(connect_result)
        
        # HTTP requests с разными сценариями
        for scenario in FRAGMENTATION_SCENARIOS:
            http_result = self.measure_http_request(host, port, "/get", scenario["chunk_size"])
            http_result["scenario"] = scenario["name"]
            http_result["scenario_description"] = scenario["description"]
            target_results.append(http_result)
        
        return {
            "target": f"{host}:{port}",
            "results": target_results
        }
    
    def run_full_audit(self):
        """Полный аудит всех целей"""
        print("🚀 Real Internet Connectivity Audit")
        print("Цель: Проверить реальную связность с интернет целями")
        print("=" * 60)
        
        audit_results = []
        
        for host, port in TARGETS:
            if port in [80, 443]:  # Только HTTP/HTTPS порты
                target_audit = self.audit_target(host, port)
                audit_results.append(target_audit)
        
        # Анализируем результаты
        successful_targets = []
        failed_targets = []
        
        for target_result in audit_results:
            target_name = target_result["target"]
            
            # Проверяем хотя бы один успешный HTTP запрос
            http_results = [r for r in target_result["results"] if r.get("http_success", False)]
            
            if http_results:
                successful_targets.append(target_name)
            else:
                failed_targets.append(target_name)
        
        print(f"\n📊 Audit Summary:")
        print(f"  Total targets: {len(TARGETS)}")
        print(f"  Successful targets: {len(successful_targets)}")
        print(f"  Failed targets: {len(failed_targets)}")
        
        if failed_targets:
            print(f"\n❌ Failed Targets:")
            for target in failed_targets:
                print(f"  {target}")
        
        if successful_targets:
            print(f"\n✅ Successful Targets:")
            for target in successful_targets:
                print(f"  {target}")
        
        final_results = {
            "timestamp": time.time(),
            "total_targets": len(TARGETS),
            "successful_targets": len(successful_targets),
            "failed_targets": len(failed_targets),
            "success_rate": (len(successful_targets) / len(TARGETS)) * 100 if TARGETS else 0,
            "target_audits": audit_results
        }
        
        return final_results

def main():
    """Основная функция"""
    auditor = InternetConnectivityAuditor()
    results = auditor.run_full_audit()
    
    # Сохраняем результаты
    with open("INTERNET_CONNECTIVITY_AUDIT.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: INTERNET_CONNECTIVITY_AUDIT.json")
    
    # Возвращаем exit code
    success = results["success_rate"] > 0  # Хотя бы одна цель работает
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
