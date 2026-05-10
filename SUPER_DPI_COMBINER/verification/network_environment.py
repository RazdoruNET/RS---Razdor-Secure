#!/usr/bin/env python3
"""
Network Environment Detection - Определение характеристик сети и ISP
"""

import sys
import socket
import subprocess
import json
import platform
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class NetworkEnvironmentDetector:
    """Детектор сетевого окружения"""
    
    def __init__(self):
        self.environment_info = {}
        
    def get_public_ip(self) -> str:
        """Получить публичный IP"""
        try:
            # Используем несколько сервисов для определения публичного IP
            services = [
                "https://api.ipify.org",
                "https://ipinfo.io/ip",
                "https://icanhazip.com"
            ]
            
            for service in services:
                try:
                    result = subprocess.run(
                        ["curl", "-s", service],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        ip = result.stdout.strip()
                        if ip and self._is_valid_ip(ip):
                            return ip
                except:
                    continue
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Проверить валидность IP"""
        try:
            socket.inet_aton(ip)
            return True
        except:
            return False
    
    def get_dns_servers(self) -> list:
        """Получить DNS серверы"""
        try:
            # На macOS используем scutil
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["scutil", "--dns"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    dns_servers = []
                    for line in lines:
                        if line.strip() and 'nameserver' in line:
                            ip = line.split()[-1]
                            if self._is_valid_ip(ip):
                                dns_servers.append(ip)
                    return dns_servers
            
            # Fallback на /etc/resolv.conf
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    content = f.read()
                    dns_servers = []
                    for line in content.split('\n'):
                        if line.strip().startswith('nameserver'):
                            ip = line.split()[-1]
                            if self._is_valid_ip(ip):
                                dns_servers.append(ip)
                    return list(set(dns_servers))
            except:
                pass
                
        except Exception:
            pass
        
        return []
    
    def get_network_interfaces(self) -> dict:
        """Получить сетевые интерфейсы"""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["ifconfig"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    interfaces = {}
                    current_interface = None
                    current_lines = []
                    
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line.startswith('en') or line.startswith('eth') or line.startswith('lo'):
                            if ':' in line:
                                interface_name = line.split(':')[0].strip()
                                if not current_interface:
                                    current_interface = interface_name
                                current_lines.append(line)
                            elif interface_name == current_interface:
                                current_lines.append(line)
                    
                    # Парсим информацию о текущем интерфейсе
                    if current_interface and current_lines:
                        interfaces[current_interface] = {
                            'name': current_interface,
                            'config': '\n'.join(current_lines)
                        }
                    
                    return interfaces
                    
        except Exception:
            pass
        
        return {}
    
    def get_system_info(self) -> dict:
        """Получить системную информацию"""
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname()
        }
    
    def detect_isp(self, public_ip: str) -> str:
        """Определить ISP по IP"""
        try:
            # Используем whois для информации об IP
            result = subprocess.run(
                ["whois", public_ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # Ищем признаки ISP
                isp_keywords = ['provider', 'isp', 'organization', 'org-name', 'netname']
                for line in output.split('\n'):
                    for keyword in isp_keywords:
                        if keyword in line and ':' in line:
                            org_info = line.split(':', 1)[1].strip()
                            if org_info and len(org_info) > 3:
                                return org_info
                
                # Ищем признаки крупных провайдеров
                major_isps = {
                    'comcast': ['comcast', 'xfinity'],
                    'verizon': ['verizon', 'fios'],
                    'at&t': ['at&t', 'att', 'bell'],
                    'charter': ['charter', 'spectrum'],
                    'cox': ['cox'],
                    'time warner': ['warner', 'spectrum'],
                    'centurylink': ['centurylink', 'ctl'],
                    'vodafone': ['vodafone'],
                    'orange': ['orange'],
                    'telefonica': ['telefonica', 'o2', 'e-plus'],
                    'deutsche telekom': ['deutsche telekom', 'dt'],
                    'bt': ['bt', 'british telecom'],
                    'sky': ['sky'],
                    'talktalk': ['talktalk'],
                    'virgin media': ['virgin', 'media'],
                    'tele2': ['tele2']
                }
                
                for isp, keywords in major_isps.items():
                    for keyword in keywords:
                        if keyword in output:
                            return isp
                
                return "unknown"
                
        except Exception:
            return "unknown"
    
    def run_detection(self):
        """Запустить детекцию сетевого окружения"""
        print("🌐 Network Environment Detection")
        print("Цель: Определить характеристики сети и ISP")
        print("=" * 60)
        
        # Получаем информацию
        public_ip = self.get_public_ip()
        dns_servers = self.get_dns_servers()
        network_interfaces = self.get_network_interfaces()
        system_info = self.get_system_info()
        isp_info = self.detect_isp(public_ip)
        
        # Собираем результаты
        self.environment_info = {
            'timestamp': sys.modules.get('time', {}).time(),
            'public_ip': public_ip,
            'dns_servers': dns_servers,
            'network_interfaces': network_interfaces,
            'system_info': system_info,
            'isp_info': isp_info,
            'detection_methods': {
                'public_ip': 'ipify.org, ipinfo.io, icanhazip.com',
                'dns_servers': 'scutil, /etc/resolv.conf',
                'network_interfaces': 'ifconfig (macOS)',
                'isp': 'whois database'
            }
        }
        
        # Выводим результаты
        print(f"📊 Public IP: {public_ip}")
        print(f"📊 DNS Servers: {dns_servers}")
        print(f"📊 Network Interfaces: {list(network_interfaces.keys())}")
        print(f"📊 System: {system_info['platform']} {system_info['platform_release']}")
        print(f"📊 ISP: {isp_info}")
        
        return self.environment_info
    
    def generate_report(self) -> str:
        """Генерировать отчет"""
        info = self.environment_info
        
        report = f"""# NETWORK_ENVIRONMENT_REPORT.md

## Network Environment Report

Generated: {info['timestamp']}

## Network Information
- **Public IP**: {info['public_ip']}
- **DNS Servers**: {info['dns_servers']}
- **Network Interfaces**: {list(info['network_interfaces'].keys())}
- **ISP**: {info['isp_info']}

## System Information
- **Platform**: {info['system_info']['platform']}
- **Release**: {info['system_info']['platform_release']}
- **Version**: {info['system_info']['platform_version']}
- **Machine**: {info['system_info']['machine']}
- **Processor**: {info['system_info']['processor']}
- **Hostname**: {info['system_info']['hostname']}

## Detection Methods
- **Public IP Detection**: {info['detection_methods']['public_ip']}
- **DNS Detection**: {info['detection_methods']['dns_servers']}
- **Network Interface Detection**: {info['detection_methods']['network_interfaces']}
- **ISP Detection**: {info['detection_methods']['isp']}

## Environment Classification
- **Network Type**: {'Internet' if info['public_ip'] != 'unknown' else 'Local/Unknown'}
- **ISP Identified**: {'YES' if info['isp_info'] != 'unknown' else 'NO'}
- **DNS Available**: {'YES' if info['dns_servers'] else 'NO'}
- **Interfaces Detected**: {'YES' if info['network_interfaces'] else 'NO'}

## Network Characteristics
- **Public Connectivity**: {'VERIFIED' if info['public_ip'] != 'unknown' else 'NOT VERIFIED'}
- **ISP Information**: {'VERIFIED' if info['isp_info'] != 'unknown' else 'NOT VERIFIED'}
- **Network Stack**: {'VERIFIED' if info['dns_servers'] or info['network_interfaces'] else 'NOT VERIFIED'}

## Final Classification
**NETWORK_ENVIRONMENT**: {'VERIFIED' if info['public_ip'] != 'unknown' else 'NOT VERIFIED'}
"""
        
        return report

def main():
    """Основная функция"""
    detector = NetworkEnvironmentDetector()
    environment_info = detector.run_detection()
    
    # Сохраняем результаты
    with open("NETWORK_ENVIRONMENT.json", "w") as f:
        json.dump(environment_info, f, indent=2)
    
    # Генерируем отчет
    report = detector.generate_report()
    with open("NETWORK_ENVIRONMENT_REPORT.md", "w") as f:
        f.write(report)
    
    print(f"\n📄 Results saved to: NETWORK_ENVIRONMENT.json")
    print(f"📄 Report saved to: NETWORK_ENVIRONMENT_REPORT.md")
    
    return environment_info

if __name__ == "__main__":
    main()
