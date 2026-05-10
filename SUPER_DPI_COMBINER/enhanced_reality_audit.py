#!/usr/bin/env python3
"""
ENHANCED SYSTEM REALITY AUDIT - Runtime Execution Scanner
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
import asyncio
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
            "has_async_execute": False,
            "inherits_base_pipeline": False,
            "runtime_facts": []
        }
        
        try:
            # Add project root to sys.path for imports
            project_root = str(self.base_path)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                
            # Load module
            spec = importlib.util.spec_from_file_location(pipeline_name, pipeline_file)
            module = importlib.util.module_from_spec(spec)
            
            # Execute module to get classes
            spec.loader.exec_module(module)
            
            # Find pipeline classes
            pipeline_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith('Pipeline') and hasattr(obj, 'initialize') and hasattr(obj, 'execute'):
                    pipeline_classes.append(obj)
                    
            if not pipeline_classes:
                result["errors"].append("No valid pipeline class found")
                self.results.append(result)
                return
                
            # Use first pipeline class found
            pipeline_class = pipeline_classes[0]
            
            # Check inheritance
            base_pipeline_found = False
            try:
                from core.base_pipeline import BasePipeline
                if issubclass(pipeline_class, BasePipeline):
                    result["inherits_base_pipeline"] = True
                    base_pipeline_found = True
            except:
                pass
                
            result["has_initialize"] = True
            result["has_execute"] = True
            result["has_async_execute"] = inspect.iscoroutinefunction(pipeline_class.execute)
            
            # Start network monitoring
            self.network_monitor.start_monitoring()
            
            # Test instantiation and initialization
            start_time = time.time()
            try:
                pipeline_instance = pipeline_class()
                result["runtime_facts"].append("Pipeline instantiated successfully")
                
                # Test initialization
                config = {"test": True}
                if result["has_async_execute"]:
                    # Async pipeline
                    init_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(init_loop)
                    init_result = init_loop.run_until_complete(pipeline_instance.initialize(config))
                    init_loop.close()
                else:
                    # Sync pipeline
                    init_result = pipeline_instance.initialize(config)
                    
                result["initializable"] = True
                result["runtime_facts"].append("initialize() executed successfully")
                
                # Test execution
                try:
                    # Create mock request
                    mock_request = type('MockRequest', (), {
                        'host': 'example.com',
                        'port': 80,
                        'method': 'GET',
                        'headers': {},
                        'data': b''
                    })()
                    
                    if result["has_async_execute"]:
                        # Async execution
                        exec_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(exec_loop)
                        exec_result = exec_loop.run_until_complete(pipeline_instance.execute(mock_request))
                        exec_loop.close()
                    else:
                        # Sync execution
                        exec_result = pipeline_instance.execute(mock_request)
                        
                    result["executable"] = True
                    result["runtime_facts"].append("execute() executed successfully")
                    
                    # Check execution result
                    if hasattr(exec_result, 'success'):
                        if exec_result.success and len(self.network_monitor.socket_calls) == 0:
                            result["runtime_facts"].append("execute() returned success without network activity")
                            result["simulation_detected"] = True
                        elif exec_result.success and len(self.network_monitor.socket_calls) > 0:
                            result["simulation_detected"] = False
                            result["runtime_facts"].append("execute() returned success with real network activity")
                            
                except Exception as e:
                    result["errors"].append(f"execute() failed: {str(e)}")
                    result["runtime_facts"].append(f"execute() failed: {type(e).__name__}")
                    
            except Exception as e:
                result["errors"].append(f"Pipeline instantiation/initialization failed: {str(e)}")
                result["runtime_facts"].append(f"Pipeline instantiation/initialization failed: {type(e).__name__}")
                
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
            # Add project root to sys.path
            project_root = str(self.base_path)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                
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
                        
                        # Check for actual threading components
                        if hasattr(engine, 'executor') or hasattr(engine, 'thread_pool'):
                            result["runtime_facts"].append("Thread pool/executor found")
                            
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
            # Add project root to sys.path
            project_root = str(self.base_path)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                
            llm_path = self.base_path / "core" / "llm_integration.py"
            spec = importlib.util.spec_from_file_location("llm", llm_path)
            llm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(llm_module)
            
            result["loadable"] = True
            result["runtime_facts"].append("LLM module loads successfully")
            
            # Test Ollama connection
            self.network_monitor.start_monitoring()
            
            try:
                if hasattr(llm_module, 'LLMIntegration'):
                    llm_integration = llm_module.LLMIntegration()
                    result["runtime_facts"].append("LLMIntegration instantiated successfully")
                    
                    if hasattr(llm_integration, 'test_ollama_connection'):
                        # Test Ollama connection
                        test_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(test_loop)
                        try:
                            ollama_result = test_loop.run_until_complete(llm_integration.test_ollama_connection())
                            result["runtime_facts"].append(f"Ollama test executed: {ollama_result}")
                        except:
                            result["runtime_facts"].append("Ollama test failed - service likely unavailable")
                        test_loop.close()
                        
                    net_stats = self.network_monitor.get_stats()
                    if net_stats["has_network_activity"]:
                        result["real_http_calls"] = True
                        result["runtime_facts"].append("Real HTTP calls detected during LLM test")
                    else:
                        result["runtime_facts"].append("No network activity during LLM test")
                        
            except Exception as e:
                result["errors"].append(f"LLM instantiation failed: {str(e)}")
                
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
        
        print("🔍 Starting Enhanced System Reality Audit...")
        
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
        async_pipelines = [p for p in pipeline_results if p.get("has_async_execute", False)]
        
        return {
            "total_pipelines": total_pipelines,
            "simulated_pipelines": len(simulated_pipelines),
            "real_io_pipelines": len(real_io_pipelines),
            "async_pipelines": len(async_pipelines),
            "simulation_rate": len(simulated_pipelines) / total_pipelines if total_pipelines > 0 else 0,
            "simulation_details": [
                {
                    "pipeline": p["pipeline"],
                    "reason": "No network activity detected" if not p.get("network_activity_detected", False) else "Fast execution pattern",
                    "evidence": p["runtime_facts"],
                    "execution_time": p.get("execution_time", 0)
                }
                for p in simulated_pipelines
            ]
        }
        
    def _analyze_failures(self, pipeline_results: List[Dict], core_results: List[Dict]) -> Dict[str, Any]:
        """Анализ failures"""
        failing_pipelines = [p for p in pipeline_results if p.get("errors")]
        initialization_failures = [p for p in pipeline_results if not p.get("initializable", False)]
        execution_failures = [p for p in pipeline_results if not p.get("executable", False)]
        loading_failures = [p for p in pipeline_results if "Module loading failed" in str(p.get("errors", []))]
        
        return {
            "total_failures": len(failing_pipelines),
            "initialization_failures": len(initialization_failures),
            "execution_failures": len(execution_failures),
            "loading_failures": len(loading_failures),
            "failing_components": [c for c in core_results if c.get("errors")],
            "failure_details": [
                {
                    "component": p["pipeline"],
                    "errors": p["errors"],
                    "failure_type": "pipeline",
                    "loadable": "Module loading failed" not in str(p.get("errors", []))
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
    
    print("🚀 ENHANCED SYSTEM REALITY AUDIT STARTED")
    print("=" * 50)
    
    # Run audit
    audit_report = auditor.run_full_audit()
    
    # Save results
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / "ENHANCED_SYSTEM_REALITY_AUDIT_RAW.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Enhanced audit data saved to: {report_file}")
    
    # Generate summary
    print("\n📊 ENHANCED AUDIT SUMMARY")
    print("-" * 30)
    print(f"Total pipelines scanned: {audit_report['audit_metadata']['total_pipelines_scanned']}")
    print(f"Pipelines with real I/O: {audit_report['simulation_analysis']['real_io_pipelines']}")
    print(f"Simulated pipelines: {audit_report['simulation_analysis']['simulated_pipelines']}")
    print(f"Async pipelines: {audit_report['simulation_analysis']['async_pipelines']}")
    print(f"Total failures: {audit_report['failure_analysis']['total_failures']}")
    print(f"Loading failures: {audit_report['failure_analysis']['loading_failures']}")
    
    return audit_report

if __name__ == "__main__":
    main()
