#!/usr/bin/env python3
"""
SYSTEM REALITY AUDIT - Runtime Execution Scanner
Только факты выполнения, без интерпретаций
"""

import os
import sys
import json
import time
import socket
import threading
import traceback
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util
import inspect

class NetworkMonitor:
    """Монитор сетевой активности в реальном времени"""
    
    def __init__(self):
        self.socket_calls = []
        self.dns_calls = []
        self.http_calls = []
        self.bytes_sent = 0
        self.bytes_received = 0
        self.original_socket = None
        self.original_getaddrinfo = None
        
    def start_monitoring(self):
        """Начать мониторинг сетевых вызовов"""
        self._patch_socket()
        self._patch_dns()
        
    def stop_monitoring(self):
        """Остановить мониторинг и восстановить оригинальные функции"""
        self._restore_socket()
        self._restore_dns()
        
    def _patch_socket(self):
        """Патчинг socket calls"""
        self.original_socket = socket.socket
        
        def monitored_socket(*args, **kwargs):
            sock = self.original_socket(*args, **kwargs)
            
            original_send = sock.send
            original_recv = sock.recv
            original_connect = sock.connect
            
            def monitored_send(data):
                self.bytes_sent += len(data)
                self.socket_calls.append({
                    'type': 'send',
                    'size': len(data),
                    'timestamp': time.time()
                })
                return original_send(data)
                
            def monitored_recv(bufsize):
                data = original_recv(bufsize)
                self.bytes_received += len(data)
                self.socket_calls.append({
                    'type': 'recv', 
                    'size': len(data),
                    'timestamp': time.time()
                })
                return data
                
            def monitored_connect(address):
                self.socket_calls.append({
                    'type': 'connect',
                    'address': address,
                    'timestamp': time.time()
                })
                return original_connect(address)
            
            sock.send = monitored_send
            sock.recv = monitored_recv
            sock.connect = monitored_connect
            
            return sock
            
        socket.socket = monitored_socket
        
    def _patch_dns(self):
        """Патчинг DNS calls"""
        self.original_getaddrinfo = socket.getaddrinfo
        
        def monitored_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            self.dns_calls.append({
                'host': host,
                'port': port,
                'timestamp': time.time()
            })
            return self.original_getaddrinfo(host, port, family, type, proto, flags)
            
        socket.getaddrinfo = monitored_getaddrinfo
        
    def _restore_socket(self):
        """Восстановление оригинального socket"""
        if self.original_socket:
            socket.socket = self.original_socket
            
    def _restore_dns(self):
        """Восстановление оригинального DNS"""
        if self.original_getaddrinfo:
            socket.getaddrinfo = self.original_getaddrinfo
            
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику сетевой активности"""
        return {
            'socket_calls': len(self.socket_calls),
            'dns_calls': len(self.dns_calls),
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'has_network_activity': len(self.socket_calls) > 0 or len(self.dns_calls) > 0
        }

class PipelineRealityScanner:
    """Сканер реального исполнения pipeline"""
    
    def __init__(self):
        self.results = []
        self.network_monitor = NetworkMonitor()
        self.base_path = Path(__file__).parent
        
    def scan_all_pipelines(self) -> List[Dict[str, Any]]:
        """Сканировать все pipeline модули"""
        pipelines_dir = self.base_path / "pipelines"
        
        for pipeline_category in pipelines_dir.iterdir():
            if pipeline_category.is_dir() and pipeline_category.name != "__pycache__":
                for pipeline_file in pipeline_category.glob("*.py"):
                    if pipeline_file.name != "__init__.py":
                        self._test_pipeline(pipeline_file, pipeline_category.name)
                        
        return self.results
        
    def _test_pipeline(self, pipeline_file: Path, category: str):
        """Тестировать конкретный pipeline"""
        pipeline_name = pipeline_file.stem
        result = {
            "pipeline": f"{category}/{pipeline_name}",
            "category": category,
            "file_path": str(pipeline_file),
            "initializable": False,
            "executable": False,
            "network_activity_detected": False,
            "bytes_sent": 0,
            "bytes_received": 0,
            "errors": [],
            "simulation_detected": True,  # Default to simulation until proven otherwise
            "execution_time": 0,
            "has_initialize": False,
            "has_execute": False,
            "runtime_facts": []
        }
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(pipeline_name, pipeline_file)
            module = importlib.util.module_from_spec(spec)
            
            # Check for required methods
            has_initialize = hasattr(module, 'initialize')
            has_execute = hasattr(module, 'execute')
            
            result["has_initialize"] = has_initialize
            result["has_execute"] = has_execute
            
            if not has_initialize or not has_execute:
                result["errors"].append("Missing required methods (initialize/execute)")
                self.results.append(result)
                return
                
            # Start network monitoring
            self.network_monitor.start_monitoring()
            
            # Test initialization
            start_time = time.time()
            try:
                init_result = module.initialize()
                result["initializable"] = True
                result["runtime_facts"].append("initialize() executed successfully")
            except Exception as e:
                result["errors"].append(f"initialize() failed: {str(e)}")
                result["runtime_facts"].append(f"initialize() failed: {type(e).__name__}")
                
            # Test execution
            try:
                exec_result = module.execute()
                result["executable"] = True
                result["runtime_facts"].append("execute() executed successfully")
                
                # Check if execution returns fake success
                if exec_result is True and len(self.network_monitor.socket_calls) == 0:
                    result["runtime_facts"].append("execute() returned True without network activity")
                    result["simulation_detected"] = True
                    
            except Exception as e:
                result["errors"].append(f"execute() failed: {str(e)}")
                result["runtime_facts"].append(f"execute() failed: {type(e).__name__}")
                
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            # Get network stats
            net_stats = self.network_monitor.get_stats()
            result.update(net_stats)
            
            # Detect simulation patterns
            if execution_time < 0.1 and not net_stats["has_network_activity"]:
                result["simulation_detected"] = True
                result["runtime_facts"].append("Fast execution with no network activity - likely simulation")
                
            if len(self.network_monitor.socket_calls) > 0:
                result["simulation_detected"] = False
                result["runtime_facts"].append(f"Real network activity: {len(self.network_monitor.socket_calls)} socket calls")
                
            self.network_monitor.stop_monitoring()
            
        except Exception as e:
            result["errors"].append(f"Module loading failed: {str(e)}")
            result["runtime_facts"].append(f"Module loading failed: {type(e).__name__}")
            
        self.results.append(result)

class CoreSystemRealityChecker:
    """Проверка реальности core системы"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.network_monitor = NetworkMonitor()
        
    def check_engine_reality(self) -> Dict[str, Any]:
        """Проверить реальность engine"""
        result = {
            "component": "multi_thread_engine",
            "loadable": False,
            "instantiable": False,
            "real_threading": False,
            "pipeline_execution": False,
            "network_activity": False,
            "errors": [],
            "runtime_facts": []
        }
        
        try:
            # Test engine loading
            engine_path = self.base_path / "core" / "multi_thread_engine.py"
            spec = importlib.util.spec_from_file_location("engine", engine_path)
            engine_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(engine_module)
            
            result["loadable"] = True
            result["runtime_facts"].append("Engine module loads successfully")
            
            # Check for threading classes
            if hasattr(engine_module, 'MultiThreadEngine'):
                result["instantiable"] = True
                result["runtime_facts"].append("MultiThreadEngine class found")
                
                # Test instantiation
                try:
                    engine = engine_module.MultiThreadEngine()
                    result["runtime_facts"].append("MultiThreadEngine instantiated successfully")
                    
                    # Check for threading methods
                    if hasattr(engine, 'start') and hasattr(engine, 'execute_pipeline'):
                        result["real_threading"] = True
                        result["runtime_facts"].append("Threading methods present")
                        
                except Exception as e:
                    result["errors"].append(f"Engine instantiation failed: {str(e)}")
                    
        except Exception as e:
            result["errors"].append(f"Engine loading failed: {str(e)}")
            
        return result
        
    def check_llm_integration(self) -> Dict[str, Any]:
        """Проверить LLM интеграцию"""
        result = {
            "component": "llm_integration",
            "loadable": False,
            "ollama_available": False,
            "fallback_behavior": False,
            "real_http_calls": False,
            "errors": [],
            "runtime_facts": []
        }
        
        try:
            llm_path = self.base_path / "core" / "llm_integration.py"
            spec = importlib.util.spec_from_file_location("llm", llm_path)
            llm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(llm_module)
            
            result["loadable"] = True
            result["runtime_facts"].append("LLM module loads successfully")
            
            # Test Ollama connection
            self.network_monitor.start_monitoring()
            
            try:
                if hasattr(llm_module, 'test_ollama_connection'):
                    ollama_result = llm_module.test_ollama_connection()
                    result["runtime_facts"].append(f"Ollama test executed: {ollama_result}")
                    
                    net_stats = self.network_monitor.get_stats()
                    if net_stats["has_network_activity"]:
                        result["real_http_calls"] = True
                        result["runtime_facts"].append("Real HTTP calls detected during Ollama test")
                    else:
                        result["runtime_facts"].append("No network activity during Ollama test")
                        
            except Exception as e:
                result["errors"].append(f"Ollama test failed: {str(e)}")
                
            self.network_monitor.stop_monitoring()
            
        except Exception as e:
            result["errors"].append(f"LLM module loading failed: {str(e)}")
            
        return result

class SystemRealityAuditor:
    """Основной аудитор системы"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.pipeline_scanner = PipelineRealityScanner()
        self.core_checker = CoreSystemRealityChecker()
        
    def run_full_audit(self) -> Dict[str, Any]:
        """Запустить полный аудит системы"""
        audit_start = time.time()
        
        print("🔍 Starting System Reality Audit...")
        
        # Scan pipelines
        print("📦 Scanning pipelines...")
        pipeline_results = self.pipeline_scanner.scan_all_pipelines()
        
        # Check core systems
        print("⚙️ Checking core systems...")
        engine_result = self.core_checker.check_engine_reality()
        llm_result = self.core_checker.check_llm_integration()
        
        # Analyze simulation patterns
        print("🎭 Detecting simulation patterns...")
        simulation_analysis = self._analyze_simulation_patterns(pipeline_results)
        
        # Document failures
        print("💥 Documenting failures...")
        failure_analysis = self._analyze_failures(pipeline_results, [engine_result, llm_result])
        
        audit_duration = time.time() - audit_start
        
        audit_report = {
            "audit_metadata": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": audit_duration,
                "total_pipelines_scanned": len(pipeline_results),
                "total_components_checked": len([engine_result, llm_result])
            },
            "pipeline_reality": pipeline_results,
            "core_system_reality": {
                "engine": engine_result,
                "llm_integration": llm_result
            },
            "simulation_analysis": simulation_analysis,
            "failure_analysis": failure_analysis
        }
        
        return audit_report
        
    def _analyze_simulation_patterns(self, pipeline_results: List[Dict]) -> Dict[str, Any]:
        """Анализ паттернов симуляции"""
        total_pipelines = len(pipeline_results)
        simulated_pipelines = [p for p in pipeline_results if p.get("simulation_detected", True)]
        real_io_pipelines = [p for p in pipeline_results if p.get("network_activity_detected", False)]
        
        return {
            "total_pipelines": total_pipelines,
            "simulated_pipelines": len(simulated_pipelines),
            "real_io_pipelines": len(real_io_pipelines),
            "simulation_rate": len(simulated_pipelines) / total_pipelines if total_pipelines > 0 else 0,
            "simulation_details": [
                {
                    "pipeline": p["pipeline"],
                    "reason": "No network activity detected",
                    "evidence": p["runtime_facts"]
                }
                for p in simulated_pipelines
            ]
        }
        
    def _analyze_failures(self, pipeline_results: List[Dict], core_results: List[Dict]) -> Dict[str, Any]:
        """Анализ failures"""
        failing_pipelines = [p for p in pipeline_results if p.get("errors")]
        initialization_failures = [p for p in pipeline_results if not p.get("initializable", False)]
        execution_failures = [p for p in pipeline_results if not p.get("executable", False)]
        
        return {
            "total_failures": len(failing_pipelines),
            "initialization_failures": len(initialization_failures),
            "execution_failures": len(execution_failures),
            "failing_components": [c for c in core_results if c.get("errors")],
            "failure_details": [
                {
                    "component": p["pipeline"],
                    "errors": p["errors"],
                    "failure_type": "pipeline"
                }
                for p in failing_pipelines
            ] + [
                {
                    "component": c["component"],
                    "errors": c["errors"],
                    "failure_type": "core"
                }
                for c in core_results if c.get("errors")
            ]
        }

def main():
    """Main execution"""
    auditor = SystemRealityAuditor()
    
    print("🚀 SYSTEM REALITY AUDIT STARTED")
    print("=" * 50)
    
    # Run audit
    audit_report = auditor.run_full_audit()
    
    # Save results
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "SYSTEM_REALITY_AUDIT_RAW.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Raw audit data saved to: {report_file}")
    
    # Generate summary
    print("\n📊 AUDIT SUMMARY")
    print("-" * 30)
    print(f"Total pipelines scanned: {audit_report['audit_metadata']['total_pipelines_scanned']}")
    print(f"Pipelines with real I/O: {audit_report['simulation_analysis']['real_io_pipelines']}")
    print(f"Simulated pipelines: {audit_report['simulation_analysis']['simulated_pipelines']}")
    print(f"Total failures: {audit_report['failure_analysis']['total_failures']}")
    
    return audit_report

if __name__ == "__main__":
    main()
