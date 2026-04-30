"""
Tests for Tor Integration Module
"""

import unittest
import socket
import threading
import time
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rsecure.modules.defense.tor_integration import (
    TorController, TorNode, TorCircuitConfig, TorCircuitType,
    TorBridgeManager, TorPluggableTransport, TorHiddenService,
    TorClient, TorIntegrationManager
)


class TestTorController(unittest.TestCase):
    """Test Tor Controller functionality"""
    
    def setUp(self):
        self.controller = TorController()
    
    def test_connect_success(self):
        """Test successful connection to Tor control port"""
        with patch('stem.control.Controller.from_port') as mock_from_port, \
             patch('stem.process.launch_tor_with_config') as mock_launch:
            
            mock_ctrl = Mock()
            mock_from_port.return_value = mock_ctrl
            
            result = self.controller.connect()
            
            self.assertTrue(result)
            self.assertTrue(self.controller.connected)
            mock_from_port.assert_called_with(port=9051)
            mock_ctrl.authenticate.assert_called()
    
    def test_connect_failure(self):
        """Test connection failure to Tor control port"""
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_from_port.side_effect = Exception("Connection failed")
            
            result = self.controller.connect()
            
            self.assertFalse(result)
            self.assertFalse(self.controller.connected)
    
    def test_disconnect(self):
        """Test disconnecting from Tor control port"""
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_ctrl = Mock()
            mock_from_port.return_value = mock_ctrl
            
            self.controller.connect()
            self.controller.disconnect()
            
            self.assertFalse(self.controller.connected)
            mock_ctrl.close.assert_called()
    
    def test_get_network_status(self):
        """Test getting Tor network status"""
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_ctrl = Mock()
            mock_from_port.return_value = mock_ctrl
            mock_ctrl.get_info.side_effect = [
                "Ready",
                "0.4.6.10",
                "1048576"
            ]
            mock_ctrl.get_version.return_value = "0.4.6.10"
            
            self.controller.connect()
            status = self.controller.get_network_status()
            
            self.assertIn("status", status)
            self.assertIn("version", status)
            self.assertIn("bandwidth", status)
            self.assertEqual(status["circuits"], 0)
            self.assertEqual(status["streams"], 0)
    
    def test_get_nodes(self):
        """Test getting available Tor nodes"""
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_ctrl = Mock()
            mock_from_port.return_value = mock_ctrl
            
            # Mock relay data
            mock_relay = Mock()
            mock_relay.fingerprint = "1234567890ABCDEF"
            mock_relay.nickname = "testrelay"
            mock_relay.address = "192.168.1.1"
            mock_relay.or_port = 9001
            mock_relay.dir_port = 9030
            mock_relay.flags = ["Guard", "Exit", "Fast", "Running"]
            mock_relay.bandwidth_rate = 1048576
            
            mock_ctrl.get_network_statuses.return_value = [mock_relay]
            
            self.controller.connect()
            nodes = self.controller.get_nodes()
            
            self.assertEqual(len(nodes), 1)
            node = nodes[0]
            self.assertEqual(node.fingerprint, "1234567890ABCDEF")
            self.assertEqual(node.nickname, "testrelay")
            self.assertEqual(node.ip_address, "192.168.1.1")
            self.assertEqual(node.or_port, 9001)
            self.assertEqual(node.dir_port, 9030)
    
    def test_create_circuit(self):
        """Test creating Tor circuit"""
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_ctrl = Mock()
            mock_from_port.return_value = mock_ctrl
            mock_ctrl.new_circuit.return_value = "1234567890"
            
            config = TorCircuitConfig(
                circuit_type=TorCircuitType.STANDARD,
                path_length=3
            )
            
            self.controller.connect()
            circuit_id = self.controller.create_circuit(config)
            
            self.assertEqual(circuit_id, "1234567890")
            self.assertIn("1234567890", self.controller.circuits)
            mock_ctrl.new_circuit.assert_called()
    
    def test_close_circuit(self):
        """Test closing Tor circuit"""
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_ctrl = Mock()
            mock_from_port.return_value = mock_ctrl
            
            self.controller.connect()
            self.controller.circuits["1234567890"] = {"status": "BUILT"}
            
            result = self.controller.close_circuit("1234567890")
            
            self.assertTrue(result)
            self.assertNotIn("1234567890", self.controller.circuits)
            mock_ctrl.close_circuit.assert_called_with("1234567890")


class TestTorBridgeManager(unittest.TestCase):
    """Test Tor Bridge Manager functionality"""
    
    def setUp(self):
        self.bridge_manager = TorBridgeManager()
    
    def test_add_bridge(self):
        """Test adding bridge configuration"""
        bridge_line = "obfs4 192.168.1.1:80 1234567890ABCDEF cert=abc123 iat-mode=0"
        
        result = self.bridge_manager.add_bridge(bridge_line)
        
        self.assertTrue(result)
        self.assertEqual(len(self.bridge_manager.bridges), 1)
        bridge = self.bridge_manager.bridges[0]
        self.assertEqual(bridge["type"], "obfs4")
        self.assertEqual(bridge["ip"], "192.168.1.1")
        self.assertEqual(bridge["port"], 80)
    
    def test_add_invalid_bridge(self):
        """Test adding invalid bridge configuration"""
        bridge_line = "invalid_bridge_line"
        
        result = self.bridge_manager.add_bridge(bridge_line)
        
        self.assertFalse(result)
        self.assertEqual(len(self.bridge_manager.bridges), 0)
    
    def test_get_bridges_by_type(self):
        """Test getting bridges by type"""
        # Add different types of bridges
        self.bridge_manager.add_bridge("obfs4 192.168.1.1:80 cert=123")
        self.bridge_manager.add_bridge("meek 192.168.1.2:80 cert=456")
        self.bridge_manager.add_bridge("obfs4 192.168.1.3:80 cert=789")
        
        obfs4_bridges = self.bridge_manager.get_bridges_by_type("obfs4")
        meek_bridges = self.bridge_manager.get_bridges_by_type("meek")
        
        self.assertEqual(len(obfs4_bridges), 2)
        self.assertEqual(len(meek_bridges), 1)
    
    def test_bridge_connectivity(self):
        """Test bridge connectivity testing"""
        bridge_info = {
            "ip": "192.168.1.1",
            "port": 80,
            "type": "obfs4"
        }
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 0  # Success
            
            result = self.bridge_manager.test_bridge(bridge_info)
            
            self.assertTrue(result)
            mock_socket.assert_called()
            mock_sock.connect_ex.assert_called_with(("192.168.1.1", 80))
    
    def test_get_working_bridges(self):
        """Test getting working bridges"""
        # Add bridges
        self.bridge_manager.add_bridge("obfs4 192.168.1.1:80 cert=123")
        self.bridge_manager.add_bridge("obfs4 192.168.1.2:80 cert=456")
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            # First bridge works, second fails
            mock_sock.connect_ex.side_effect = [0, 1]
            
            working_bridges = self.bridge_manager.get_working_bridges()
            
            self.assertEqual(len(working_bridges), 1)
            self.assertEqual(working_bridges[0]["ip"], "192.168.1.1")


class TestTorPluggableTransport(unittest.TestCase):
    """Test Tor Pluggable Transport functionality"""
    
    def setUp(self):
        self.transport_manager = TorPluggableTransport()
    
    def test_register_transport(self):
        """Test registering pluggable transport"""
        result = self.transport_manager.register_transport(
            "obfs4",
            "/usr/bin/obfs4proxy",
            ["--logLevel", "INFO"]
        )
        
        self.assertTrue(result)
        self.assertIn("obfs4", self.transport_manager.transports)
        transport = self.transport_manager.transports["obfs4"]
        self.assertEqual(transport["executable"], "/usr/bin/obfs4proxy")
        self.assertEqual(transport["args"], ["--logLevel", "INFO"])
    
    def test_start_transport(self):
        """Test starting pluggable transport"""
        self.transport_manager.register_transport("obfs4", "/usr/bin/obfs4proxy")
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process is running
            mock_popen.return_value = mock_process
            
            result = self.transport_manager.start_transport("obfs4", 12345)
            
            self.assertTrue(result)
            self.assertIn("obfs4", self.transport_manager.running_transports)
            transport_info = self.transport_manager.running_transports["obfs4"]
            self.assertEqual(transport_info["port"], 12345)
            mock_popen.assert_called()
    
    def test_start_transport_failure(self):
        """Test transport start failure"""
        self.transport_manager.register_transport("obfs4", "/usr/bin/obfs4proxy")
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = 1  # Process exited
            mock_popen.return_value = mock_process
            
            result = self.transport_manager.start_transport("obfs4", 12345)
            
            self.assertFalse(result)
            self.assertNotIn("obfs4", self.transport_manager.running_transports)
    
    def test_stop_transport(self):
        """Test stopping pluggable transport"""
        self.transport_manager.register_transport("obfs4", "/usr/bin/obfs4proxy")
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # Start transport
            self.transport_manager.start_transport("obfs4", 12345)
            
            # Stop transport
            result = self.transport_manager.stop_transport("obfs4")
            
            self.assertTrue(result)
            self.assertNotIn("obfs4", self.transport_manager.running_transports)
            mock_process.terminate.assert_called()


class TestTorHiddenService(unittest.TestCase):
    """Test Tor Hidden Service functionality"""
    
    def setUp(self):
        self.hidden_service = TorHiddenService()
    
    def test_create_hidden_service(self):
        """Test creating hidden service"""
        with patch('os.makedirs') as mock_makedirs:
            result = self.hidden_service.create_hidden_service(
                "test_service",
                8080,
                80,
                "/tmp/tor_hidden_service_test"
            )
            
            self.assertTrue(result)
            self.assertIn("test_service", self.hidden_service.services)
            service = self.hidden_service.services["test_service"]
            self.assertEqual(service["local_port"], 8080)
            self.assertEqual(service["virtual_port"], 80)
            self.assertEqual(service["service_dir"], "/tmp/tor_hidden_service_test")
            mock_makedirs.assert_called_with("/tmp/tor_hidden_service_test", exist_ok=True)
    
    def test_get_onion_address(self):
        """Test getting onion address"""
        # Create service
        self.hidden_service.create_hidden_service("test_service", 8080)
        service_dir = self.hidden_service.services["test_service"]["service_dir"]
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.return_value = "test1234567890.onion\n"
            
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                
                address = self.hidden_service.get_onion_address("test_service")
                
                self.assertEqual(address, "test1234567890.onion")
                service = self.hidden_service.services["test_service"]
                self.assertEqual(service["onion_address"], "test1234567890.onion")
    
    def test_remove_hidden_service(self):
        """Test removing hidden service"""
        with patch('os.makedirs') as mock_makedirs, \
             patch('shutil.rmtree') as mock_rmtree, \
             patch('os.path.exists') as mock_exists:
            
            mock_exists.return_value = True
            
            # Create service
            self.hidden_service.create_hidden_service("test_service", 8080)
            service_dir = self.hidden_service.services["test_service"]["service_dir"]
            
            # Remove service
            result = self.hidden_service.remove_hidden_service("test_service")
            
            self.assertTrue(result)
            self.assertNotIn("test_service", self.hidden_service.services)
            self.assertNotIn(service_dir, self.hidden_service.service_dirs)
            mock_rmtree.assert_called_with(service_dir)


class TestTorClient(unittest.TestCase):
    """Test Tor Client functionality"""
    
    def setUp(self):
        self.client = TorClient()
    
    def test_create_socks_connection(self):
        """Test creating SOCKS connection through Tor"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.side_effect = [
                b"\x05\x00",  # Auth response
                b"\x05\x00\x00\x01\x7f\x00\x00\x01\x50"  # Connect response
            ]
            
            result = self.client.create_socks_connection("example.com", 80)
            
            self.assertIsNotNone(result)
            mock_socket.assert_called()
            mock_sock.connect.assert_called_with(("127.0.0.1", 9050))
    
    def test_create_socks_connection_with_circuit(self):
        """Test creating SOCKS connection with specific circuit"""
        mock_controller = Mock()
        self.client.set_controller(mock_controller)
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.side_effect = [
                b"\x05\x00",  # Auth response
                b"\x05\x00\x00\x01\x7f\x00\x00\x01\x50"  # Connect response
            ]
            
            result = self.client.create_socks_connection("example.com", 80, "1234567890")
            
            self.assertIsNotNone(result)
            mock_controller.attach_stream.assert_called()
    
    def test_http_request(self):
        """Test making HTTP request through Tor"""
        with patch.object(self.client, 'create_socks_connection') as mock_connect:
            mock_sock = Mock()
            mock_connect.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK\r\n\r\nHello, World!"
            
            status_code, response = self.client.http_request(
                "GET",
                "http://example.com/",
                {"User-Agent": "Test"},
                None,
                "1234567890"
            )
            
            self.assertEqual(status_code, 200)
            self.assertIn(b"HTTP/1.1 200 OK", response)
            mock_connect.assert_called_with("example.com", 80, "1234567890")
    
    def test_https_request(self):
        """Test making HTTPS request through Tor"""
        with patch.object(self.client, 'create_socks_connection') as mock_connect:
            mock_sock = Mock()
            mock_connect.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK\r\n\r\nHello, World!"
            
            status_code, response = self.client.http_request(
                "GET",
                "https://example.com/",
                {"User-Agent": "Test"},
                None,
                "1234567890"
            )
            
            self.assertEqual(status_code, 200)
            mock_connect.assert_called_with("example.com", 443, "1234567890")


class TestTorIntegrationManager(unittest.TestCase):
    """Test Tor Integration Manager functionality"""
    
    def setUp(self):
        self.tor_manager = TorIntegrationManager()
    
    def test_start_tor(self):
        """Test starting Tor process"""
        with patch('stem.process.launch_tor_with_config') as mock_launch, \
             patch.object(self.tor_manager.controller, 'connect') as mock_connect:
            
            mock_process = Mock()
            mock_launch.return_value = mock_process
            mock_connect.return_value = True
            
            result = self.tor_manager.start_tor()
            
            self.assertTrue(result)
            self.assertIsNotNone(self.tor_manager.tor_process)
            mock_launch.assert_called()
            mock_connect.assert_called()
    
    def test_stop_tor(self):
        """Test stopping Tor process"""
        mock_process = Mock()
        self.tor_manager.tor_process = mock_process
        
        with patch.object(self.tor_manager.controller, 'disconnect') as mock_disconnect:
            self.tor_manager.stop_tor()
            
            self.assertIsNone(self.tor_manager.tor_process)
            mock_process.terminate.assert_called()
            mock_disconnect.assert_called()
    
    def test_create_anonymous_connection(self):
        """Test creating anonymous connection"""
        with patch.object(self.tor_manager.client, 'create_socks_connection') as mock_connect:
            mock_sock = Mock()
            mock_connect.return_value = mock_sock
            
            result = self.tor_manager.create_anonymous_connection("example.com", 80)
            
            self.assertIsNotNone(result)
            mock_connect.assert_called_with("example.com", 80, None)
    
    def test_create_anonymous_connection_with_circuit(self):
        """Test creating anonymous connection with circuit"""
        config = TorCircuitConfig(
            circuit_type=TorCircuitType.STANDARD,
            path_length=3
        )
        
        with patch.object(self.tor_manager.controller, 'create_circuit') as mock_circuit, \
             patch.object(self.tor_manager.client, 'create_socks_connection') as mock_connect:
            
            mock_circuit.return_value = "1234567890"
            mock_sock = Mock()
            mock_connect.return_value = mock_sock
            
            result = self.tor_manager.create_anonymous_connection("example.com", 80, config)
            
            self.assertEqual(result, "1234567890")
            mock_circuit.assert_called_with(config)
            mock_connect.assert_called_with("example.com", 80, "1234567890")
    
    def test_setup_bridges(self):
        """Test setting up Tor bridges"""
        bridge_lines = [
            "obfs4 192.168.1.1:80 cert=123 iat-mode=0",
            "meek 192.168.1.2:80 cert=456 iat-mode=0"
        ]
        
        with patch.object(self.tor_manager.bridge_manager, 'test_bridge') as mock_test:
            mock_test.return_value = True  # All bridges work
            
            result = self.tor_manager.setup_bridges(bridge_lines)
            
            self.assertTrue(result)
            self.assertEqual(len(self.tor_manager.bridge_manager.bridges), 2)
    
    def test_create_hidden_service(self):
        """Test creating hidden service"""
        with patch.object(self.tor_manager.hidden_service, 'create_hidden_service') as mock_create, \
             patch.object(self.tor_manager.hidden_service, 'get_onion_address') as mock_address:
            
            mock_create.return_value = True
            mock_address.return_value = "test1234567890.onion"
            
            result = self.tor_manager.create_hidden_service("test_service", 8080)
            
            self.assertEqual(result, "test1234567890.onion")
            mock_create.assert_called_with("test_service", 8080)
            mock_address.assert_called_with("test_service")
    
    def test_get_tor_status(self):
        """Test getting comprehensive Tor status"""
        mock_process = Mock()
        self.tor_manager.tor_process = mock_process
        self.tor_manager.controller.connected = True
        self.tor_manager.controller.circuits = {"123": "test"}
        self.tor_manager.controller.streams = {"456": "test"}
        
        with patch.object(self.tor_manager.controller, 'get_network_status') as mock_status:
            mock_status.return_value = {"status": "Ready"}
            
            status = self.tor_manager.get_tor_status()
            
            self.assertTrue(status["tor_running"])
            self.assertTrue(status["controller_connected"])
            self.assertEqual(status["circuits"], 1)
            self.assertEqual(status["streams"], 1)
            self.assertIn("network_status", status)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_tor_connection_failure(self):
        """Test Tor connection failure"""
        controller = TorController()
        
        with patch('stem.control.Controller.from_port') as mock_from_port:
            mock_from_port.side_effect = Exception("Connection refused")
            
            result = controller.connect()
            
            self.assertFalse(result)
            self.assertFalse(controller.connected)
    
    def test_bridge_connection_failure(self):
        """Test bridge connection failure"""
        bridge_manager = TorBridgeManager()
        bridge_info = {"ip": "192.168.1.1", "port": 80}
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 1  # Connection failed
            
            result = bridge_manager.test_bridge(bridge_info)
            
            self.assertFalse(result)
    
    def test_hidden_service_creation_failure(self):
        """Test hidden service creation failure"""
        hidden_service = TorHiddenService()
        
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = OSError("Permission denied")
            
            result = hidden_service.create_hidden_service("test", 8080)
            
            self.assertFalse(result)
    
    def test_socks_connection_failure(self):
        """Test SOCKS connection failure"""
        client = TorClient()
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect.side_effect = Exception("Connection failed")
            
            result = client.create_socks_connection("example.com", 80)
            
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
