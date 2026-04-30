"""
RSecure Tor Integration Module
Comprehensive Tor network integration for anonymous routing
"""

import socket
import struct
import time
import threading
import queue
import hashlib
import hmac
import base64
import json
import subprocess
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import stem
from stem import Circumstance
from stem.control import Controller
from stem.process import launch_tor_with_config


class TorNodeType(Enum):
    """Tor network node types"""
    GUARD = "guard"
    MIDDLE = "middle"
    EXIT = "exit"
    DIRECTORY = "directory"
    BRIDGE = "bridge"


class TorCircuitType(Enum):
    """Tor circuit types"""
    STANDARD = "standard"
    LONG_LIVED = "long_lived"
    HIGH_BANDWIDTH = "high_bandwidth"
    OBFS4 = "obfs4"
    MEEK = "meek"
    SNOWFLAKE = "snowflake"


@dataclass
class TorNode:
    """Tor node information"""
    fingerprint: str
    nickname: str
    ip_address: str
    or_port: int
    dir_port: int
    flags: List[str]
    bandwidth: int
    node_type: TorNodeType


@dataclass
class TorCircuitConfig:
    """Tor circuit configuration"""
    circuit_type: TorCircuitType
    path_length: int = 3
    specific_nodes: List[str] = None
    exit_country: Optional[str] = None
    avoid_countries: List[str] = None
    purpose: str = "general"


class TorController:
    """Tor network controller"""
    
    def __init__(self, control_port: int = 9051, password: Optional[str] = None):
        self.control_port = control_port
        self.password = password
        self.controller = None
        self.connected = False
        self.circuits = {}
        self.nodes = {}
        self.streams = {}
    
    def connect(self) -> bool:
        """Connect to Tor control port"""
        try:
            self.controller = Controller.from_port(port=self.control_port)
            
            if self.password:
                self.controller.authenticate(password=self.password)
            else:
                self.controller.authenticate()
            
            self.connected = True
            self._setup_event_listeners()
            
            print("Connected to Tor control port")
            return True
            
        except Exception as e:
            print(f"Failed to connect to Tor: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Tor control port"""
        if self.controller:
            self.controller.close()
            self.connected = False
    
    def _setup_event_listeners(self):
        """Setup event listeners for Tor events"""
        def circuit_event(event):
            if event.type == "CIRC":
                self.circuits[event.id] = {
                    "status": event.status,
                    "path": event.path,
                    "purpose": event.purpose,
                    "build_flags": event.build_flags
                }
        
        def stream_event(event):
            if event.type == "STREAM":
                self.streams[event.id] = {
                    "status": event.status,
                    "target": event.target_address,
                    "circuit": event.circ_id
                }
        
        # Add event listeners
        self.controller.add_event_listener(circuit_event, "CIRC")
        self.controller.add_event_listener(stream_event, "STREAM")
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get Tor network status"""
        if not self.connected:
            return {}
        
        try:
            status = self.controller.get_info("status/current")
            version = self.controller.get_version()
            bandwidth = self.controller.get_info("status/bandwidth-observed")
            
            return {
                "status": status,
                "version": str(version),
                "bandwidth": bandwidth,
                "circuits": len(self.circuits),
                "streams": len(self.streams)
            }
        except Exception as e:
            print(f"Failed to get network status: {e}")
            return {}
    
    def get_nodes(self) -> List[TorNode]:
        """Get available Tor nodes"""
        if not self.connected:
            return []
        
        try:
            relays = self.controller.get_network_statuses()
            nodes = []
            
            for relay in relays:
                # Determine node type based on flags
                node_type = TorNodeType.MIDDLE
                if "Guard" in relay.flags:
                    node_type = TorNodeType.GUARD
                elif "Exit" in relay.flags:
                    node_type = TorNodeType.EXIT
                elif "Directory" in relay.flags:
                    node_type = TorNodeType.DIRECTORY
                elif "Bridge" in relay.flags:
                    node_type = TorNodeType.BRIDGE
                
                node = TorNode(
                    fingerprint=relay.fingerprint,
                    nickname=relay.nickname,
                    ip_address=relay.address,
                    or_port=relay.or_port,
                    dir_port=relay.dir_port,
                    flags=relay.flags,
                    bandwidth=relay.bandwidth_rate,
                    node_type=node_type
                )
                nodes.append(node)
            
            return nodes
            
        except Exception as e:
            print(f"Failed to get nodes: {e}")
            return []
    
    def create_circuit(self, config: TorCircuitConfig) -> Optional[str]:
        """Create new Tor circuit"""
        if not self.connected:
            return None
        
        try:
            path = self._select_path(config)
            
            # Create circuit with specific path
            circuit_id = self.controller.new_circuit(
                path,
                purpose=config.purpose,
                await_build=True
            )
            
            self.circuits[circuit_id] = {
                "config": config,
                "path": path,
                "status": "BUILT",
                "created": time.time()
            }
            
            print(f"Created circuit {circuit_id} with path {path}")
            return circuit_id
            
        except Exception as e:
            print(f"Failed to create circuit: {e}")
            return None
    
    def _select_path(self, config: TorCircuitConfig) -> List[str]:
        """Select path for circuit based on configuration"""
        nodes = self.get_nodes()
        path = []
        
        # Filter nodes based on requirements
        guard_nodes = [n for n in nodes if TorNodeType.GUARD in n.flags]
        middle_nodes = [n for n in nodes if TorNodeType.MIDDLE in n.flags]
        exit_nodes = [n for n in nodes if TorNodeType.EXIT in n.flags]
        
        # Apply country filters
        if config.avoid_countries:
            guard_nodes = [n for n in guard_nodes if not self._node_in_country(n, config.avoid_countries)]
            middle_nodes = [n for n in middle_nodes if not self._node_in_country(n, config.avoid_countries)]
            exit_nodes = [n for n in exit_nodes if not self._node_in_country(n, config.avoid_countries)]
        
        if config.exit_country:
            exit_nodes = [n for n in exit_nodes if self._node_in_country(n, [config.exit_country])]
        
        # Select nodes
        if config.specific_nodes and len(config.specific_nodes) >= config.path_length:
            # Use specific nodes
            path = config.specific_nodes[:config.path_length]
        else:
            # Select random nodes
            if guard_nodes and config.path_length >= 1:
                path.append(random.choice(guard_nodes).fingerprint)
            
            for i in range(1, config.path_length - 1):
                if middle_nodes:
                    path.append(random.choice(middle_nodes).fingerprint)
            
            if exit_nodes and config.path_length >= 2:
                path.append(random.choice(exit_nodes).fingerprint)
        
        return path
    
    def _node_in_country(self, node: TorNode, countries: List[str]) -> bool:
        """Check if node is in specified countries"""
        # This would require GeoIP database
        # For now, return False (no filtering)
        return False
    
    def close_circuit(self, circuit_id: str) -> bool:
        """Close Tor circuit"""
        if not self.connected:
            return False
        
        try:
            self.controller.close_circuit(circuit_id)
            if circuit_id in self.circuits:
                del self.circuits[circuit_id]
            return True
        except Exception as e:
            print(f"Failed to close circuit: {e}")
            return False
    
    def get_circuit_info(self, circuit_id: str) -> Dict[str, Any]:
        """Get circuit information"""
        return self.circuits.get(circuit_id, {})


class TorBridgeManager:
    """Tor bridge manager for circumvention"""
    
    def __init__(self):
        self.bridges = []
        self.active_bridges = []
        self.bridge_types = ["obfs4", "meek", "snowflake", "vanilla"]
    
    def add_bridge(self, bridge_line: str) -> bool:
        """Add bridge configuration"""
        try:
            # Parse bridge line: "obfs4 <ip>:<port> <fingerprint> <cert> <iat-mode>"
            parts = bridge_line.split()
            if len(parts) >= 5:
                bridge_info = {
                    "type": parts[0],
                    "ip": parts[1].split(":")[0],
                    "port": int(parts[1].split(":")[1]),
                    "fingerprint": parts[2],
                    "cert": parts[3],
                    "iat_mode": parts[4],
                    "line": bridge_line
                }
                self.bridges.append(bridge_info)
                return True
        except:
            pass
        return False
    
    def get_bridges_by_type(self, bridge_type: str) -> List[Dict[str, Any]]:
        """Get bridges by type"""
        return [b for b in self.bridges if b["type"] == bridge_type]
    
    def test_bridge(self, bridge_info: Dict[str, Any]) -> bool:
        """Test bridge connectivity"""
        try:
            # Try to connect to bridge
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((bridge_info["ip"], bridge_info["port"]))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_working_bridges(self) -> List[Dict[str, Any]]:
        """Get list of working bridges"""
        working = []
        for bridge in self.bridges:
            if self.test_bridge(bridge):
                working.append(bridge)
        return working


class TorPluggableTransport:
    """Tor pluggable transport manager"""
    
    def __init__(self):
        self.transports = {}
        self.running_transports = {}
    
    def register_transport(self, transport_type: str, executable: str, 
                         args: List[str] = None) -> bool:
        """Register pluggable transport"""
        try:
            self.transports[transport_type] = {
                "executable": executable,
                "args": args or [],
                "process": None
            }
            return True
        except:
            return False
    
    def start_transport(self, transport_type: str, port: int) -> bool:
        """Start pluggable transport"""
        if transport_type not in self.transports:
            return False
        
        try:
            transport_config = self.transports[transport_type]
            cmd = [transport_config["executable"]] + transport_config["args"]
            
            # Add port to command
            cmd.extend(["--port", str(port)])
            
            process = subprocess.Popen(cmd)
            self.running_transports[transport_type] = {
                "process": process,
                "port": port,
                "pid": process.pid
            }
            
            time.sleep(2)  # Give transport time to start
            return process.poll() is None
            
        except Exception as e:
            print(f"Failed to start transport {transport_type}: {e}")
            return False
    
    def stop_transport(self, transport_type: str) -> bool:
        """Stop pluggable transport"""
        if transport_type not in self.running_transports:
            return False
        
        try:
            transport_info = self.running_transports[transport_type]
            process = transport_info["process"]
            process.terminate()
            process.wait(timeout=5)
            
            del self.running_transports[transport_type]
            return True
        except:
            return False


class TorHiddenService:
    """Tor hidden service manager"""
    
    def __init__(self):
        self.services = {}
        self.service_dirs = {}
    
    def create_hidden_service(self, service_id: str, local_port: int, 
                            virtual_port: int = 80, service_dir: str = None) -> bool:
        """Create hidden service"""
        try:
            if service_dir is None:
                service_dir = f"/tmp/tor_hidden_service_{service_id}"
            
            # Create service directory
            os.makedirs(service_dir, exist_ok=True)
            
            # Store service info
            self.services[service_id] = {
                "local_port": local_port,
                "virtual_port": virtual_port,
                "service_dir": service_dir,
                "onion_address": None
            }
            
            self.service_dirs[service_dir] = service_id
            return True
            
        except Exception as e:
            print(f"Failed to create hidden service: {e}")
            return False
    
    def get_onion_address(self, service_id: str) -> Optional[str]:
        """Get onion address for hidden service"""
        if service_id not in self.services:
            return None
        
        service_dir = self.services[service_id]["service_dir"]
        hostname_file = os.path.join(service_dir, "hostname")
        
        try:
            if os.path.exists(hostname_file):
                with open(hostname_file, 'r') as f:
                    onion_address = f.read().strip()
                    self.services[service_id]["onion_address"] = onion_address
                    return onion_address
        except:
            pass
        
        return None
    
    def remove_hidden_service(self, service_id: str) -> bool:
        """Remove hidden service"""
        if service_id not in self.services:
            return False
        
        try:
            service_dir = self.services[service_id]["service_dir"]
            
            # Remove service directory
            import shutil
            if os.path.exists(service_dir):
                shutil.rmtree(service_dir)
            
            # Remove from registry
            del self.services[service_id]
            if service_dir in self.service_dirs:
                del self.service_dirs[service_dir]
            
            return True
            
        except Exception as e:
            print(f"Failed to remove hidden service: {e}")
            return False


class TorClient:
    """Tor client for making requests through Tor"""
    
    def __init__(self, socks_port: int = 9050):
        self.socks_port = socks_port
        self.circuit_id = None
        self.controller = None
    
    def set_controller(self, controller: TorController):
        """Set Tor controller for circuit management"""
        self.controller = controller
    
    def create_socks_connection(self, host: str, port: int, 
                              circuit_id: str = None) -> Optional[socket.socket]:
        """Create SOCKS connection through Tor"""
        try:
            # Connect to SOCKS port
            socks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socks_socket.connect(("127.0.0.1", self.socks_port))
            
            # SOCKS5 authentication
            socks_socket.send(b"\x05\x01\x00")
            response = socks_socket.recv(2)
            
            if response != b"\x05\x00":
                socks_socket.close()
                return None
            
            # SOCKS5 connect request
            connect_request = b"\x05\x01\x00\x03" + bytes([len(host)]) + host.encode() + struct.pack("!H", port)
            socks_socket.send(connect_request)
            
            response = socks_socket.recv(10)
            if response[0] != 0x05:
                socks_socket.close()
                return None
            
            # Attach to specific circuit if specified
            if circuit_id and self.controller:
                try:
                    self.controller.attach_stream(
                        response[1:].hex(),  # Stream ID
                        circuit_id
                    )
                except:
                    pass
            
            return socks_socket
            
        except Exception as e:
            print(f"Failed to create SOCKS connection: {e}")
            return None
    
    def http_request(self, method: str, url: str, headers: Dict[str, str] = None,
                    data: bytes = None, circuit_id: str = None) -> Tuple[int, bytes]:
        """Make HTTP request through Tor"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            
            # Create SOCKS connection
            sock = self.create_socks_connection(host, port, circuit_id)
            if not sock:
                return 0, b""
            
            # Build HTTP request
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {host}\r\n"
            
            if headers:
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
            
            if data:
                request += f"Content-Length: {len(data)}\r\n"
            
            request += "Connection: close\r\n\r\n"
            
            if data:
                request += data.decode()
            
            # Send request
            sock.send(request.encode())
            
            # Read response
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            sock.close()
            
            # Parse status code
            if response:
                headers_end = response.find(b"\r\n\r\n")
                if headers_end > 0:
                    headers_part = response[:headers_end].decode()
                    first_line = headers_part.split("\r\n")[0]
                    parts = first_line.split(" ")
                    if len(parts) >= 2:
                        status_code = int(parts[1])
                        return status_code, response
            
            return 200, response
            
        except Exception as e:
            print(f"HTTP request failed: {e}")
            return 0, b""


class TorIntegrationManager:
    """Main Tor integration manager"""
    
    def __init__(self):
        self.controller = TorController()
        self.bridge_manager = TorBridgeManager()
        self.transport_manager = TorPluggableTransport()
        self.hidden_service = TorHiddenService()
        self.client = TorClient()
        self.tor_process = None
        
    def start_tor(self, config_file: str = None) -> bool:
        """Start Tor process"""
        try:
            tor_config = {
                'SocksPort': '9050',
                'ControlPort': '9051',
                'CookieAuthentication': '1',
                'ExitNodes': '{us}',
                'NewCircuitPeriod': '30'
            }
            
            self.tor_process = launch_tor_with_config(
                config=tor_config,
                tor_cmd="tor"  # Path to tor executable
            )
            
            # Give Tor time to start
            time.sleep(10)
            
            # Connect controller
            if self.controller.connect():
                self.client.set_controller(self.controller)
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to start Tor: {e}")
            return False
    
    def stop_tor(self):
        """Stop Tor process"""
        if self.tor_process:
            self.tor_process.terminate()
            self.tor_process = None
        
        self.controller.disconnect()
    
    def create_anonymous_connection(self, target_host: str, target_port: int,
                                 circuit_config: TorCircuitConfig = None) -> Optional[str]:
        """Create anonymous connection through Tor"""
        try:
            # Create circuit if configuration provided
            circuit_id = None
            if circuit_config:
                circuit_id = self.controller.create_circuit(circuit_config)
            
            # Create connection
            sock = self.client.create_socks_connection(target_host, target_port, circuit_id)
            if sock:
                sock.close()
                return circuit_id or "default"
            
            return None
            
        except Exception as e:
            print(f"Failed to create anonymous connection: {e}")
            return None
    
    def setup_bridges(self, bridge_lines: List[str]) -> bool:
        """Setup Tor bridges"""
        try:
            for bridge_line in bridge_lines:
                self.bridge_manager.add_bridge(bridge_line)
            
            # Test bridges
            working_bridges = self.bridge_manager.get_working_bridges()
            print(f"Found {len(working_bridges)} working bridges")
            
            return len(working_bridges) > 0
            
        except Exception as e:
            print(f"Failed to setup bridges: {e}")
            return False
    
    def create_hidden_service(self, service_id: str, local_port: int) -> Optional[str]:
        """Create hidden service and return onion address"""
        try:
            if self.hidden_service.create_hidden_service(service_id, local_port):
                # Wait for onion address to be generated
                time.sleep(5)
                return self.hidden_service.get_onion_address(service_id)
            return None
        except Exception as e:
            print(f"Failed to create hidden service: {e}")
            return None
    
    def get_tor_status(self) -> Dict[str, Any]:
        """Get comprehensive Tor status"""
        status = {
            "tor_running": self.tor_process is not None,
            "controller_connected": self.controller.connected,
            "circuits": len(self.controller.circuits),
            "streams": len(self.controller.streams),
            "bridges": len(self.bridge_manager.bridges),
            "hidden_services": len(self.hidden_service.services),
            "network_status": self.controller.get_network_status()
        }
        
        return status


# Example usage
if __name__ == "__main__":
    # Initialize Tor integration manager
    tor_manager = TorIntegrationManager()
    
    # Start Tor
    if tor_manager.start_tor():
        print("Tor started successfully")
        
        # Get status
        status = tor_manager.get_tor_status()
        print(f"Tor status: {status}")
        
        # Create circuit
        circuit_config = TorCircuitConfig(
            circuit_type=TorCircuitType.STANDARD,
            exit_country="us"
        )
        
        circuit_id = tor_manager.controller.create_circuit(circuit_config)
        print(f"Created circuit: {circuit_id}")
        
        # Create anonymous connection
        connection_id = tor_manager.create_anonymous_connection(
            "example.com", 80, circuit_config
        )
        print(f"Created anonymous connection: {connection_id}")
        
        # Make HTTP request
        status_code, response = tor_manager.client.http_request(
            "GET", "http://example.com", circuit_id=circuit_id
        )
        print(f"HTTP status: {status_code}")
        
        # Create hidden service
        onion_address = tor_manager.create_hidden_service("test_service", 8080)
        print(f"Hidden service address: {onion_address}")
        
        # Stop Tor
        tor_manager.stop_tor()
    else:
        print("Failed to start Tor")
