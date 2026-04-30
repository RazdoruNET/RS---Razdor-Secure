"""
Tests for VPN and Proxy Module
"""

import unittest
import socket
import threading
import time
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rsecure.modules.defense.vpn_proxy import (
    ProxyServer, ProxyConfig, ProxyType,
    VPNManager, VPNConfig, VPNType,
    ProxyChain, NetworkBypassManager
)


class TestProxyServer(unittest.TestCase):
    """Test Proxy Server functionality"""
    
    def setUp(self):
        self.config = ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="0.0.0.0",
            port=8080
        )
        self.proxy = ProxyServer(self.config)
    
    def test_start_proxy_server(self):
        """Test starting proxy server"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            
            result = self.proxy.start()
            
            self.assertTrue(result)
            mock_sock.bind.assert_called_with(("0.0.0.0", 8080))
            mock_sock.listen.assert_called_with(5)
    
    def test_stop_proxy_server(self):
        """Test stopping proxy server"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            
            self.proxy.start()
            self.proxy.stop()
            
            self.assertFalse(self.proxy.running)
            mock_sock.close.assert_called()
    
    def test_handle_http_proxy(self):
        """Test HTTP proxy handling"""
        with patch('socket.socket') as mock_socket:
            mock_client = Mock()
            mock_target = Mock()
            mock_socket.return_value = mock_target
            
            # Mock CONNECT request
            mock_client.recv.return_value = b"CONNECT example.com:80 HTTP/1.1\r\n\r\n"
            mock_target.recv.return_value = b"HTTP/1.1 200 OK\r\n\r\n"
            
            self.proxy._handle_http_proxy(mock_client)
            
            mock_target.connect.assert_called_with(("example.com", 80))
            mock_client.send.assert_called_with(b"HTTP/1.1 200 Connection Established\r\n\r\n")
    
    def test_handle_socks5_proxy(self):
        """Test SOCKS5 proxy handling"""
        with patch('socket.socket') as mock_socket:
            mock_client = Mock()
            mock_target = Mock()
            mock_socket.return_value = mock_target
            
            # Mock SOCKS5 handshake
            mock_client.recv.side_effect = [
                b"\x05\x01\x00",  # Auth request
                b"\x05\x01\x00\x03\x0bexample.com\x00\x50"  # Connect request
            ]
            mock_target.recv.return_value = b"HTTP/1.1 200 OK\r\n\r\n"
            
            self.proxy._handle_socks5_proxy(mock_client)
            
            mock_target.connect.assert_called_with(("example.com", 80))
    
    def test_relay_data(self):
        """Test data relay between client and target"""
        with patch('select.select') as mock_select:
            mock_client = Mock()
            mock_target = Mock()
            
            # Mock select returns both sockets ready
            mock_select.return_value = ([mock_client, mock_target], [], [])
            
            mock_client.recv.return_value = b"client data"
            mock_target.recv.return_value = b"target data"
            
            # Run relay for a short time
            import threading
            relay_thread = threading.Thread(
                target=self.proxy._relay_data,
                args=(mock_client, mock_target)
            )
            relay_thread.daemon = True
            relay_thread.start()
            
            time.sleep(0.1)
            
            # Verify data was exchanged
            self.assertTrue(mock_client.send.called or mock_target.send.called)


class TestVPNManager(unittest.TestCase):
    """Test VPN Manager functionality"""
    
    def setUp(self):
        self.vpn_manager = VPNManager()
    
    def test_create_openvpn_config(self):
        """Test OpenVPN configuration creation"""
        config = VPNConfig(
            vpn_type=VPNType.OPENVPN,
            server_host="vpn.example.com",
            server_port=1194,
            protocol="udp",
            cipher="aes-256-cbc",
            auth="sha256"
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.vpn_manager.create_vpn_config(config, "/tmp/openvpn.conf")
            
            self.assertTrue(result)
            mock_open.assert_called_with("/tmp/openvpn.conf", 'w')
            mock_file.write.assert_called()
            
            # Check config content
            written_data = mock_file.write.call_args[0][0]
            self.assertIn("client", written_data)
            self.assertIn("remote vpn.example.com 1194", written_data)
            self.assertIn("cipher aes-256-cbc", written_data)
    
    def test_create_wireguard_config(self):
        """Test WireGuard configuration creation"""
        config = VPNConfig(
            vpn_type=VPNType.WIREGUARD,
            server_host="vpn.example.com",
            server_port=51820
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.vpn_manager.create_vpn_config(config, "/tmp/wg.conf")
            
            self.assertTrue(result)
            written_data = mock_file.write.call_args[0][0]
            self.assertIn("[Interface]", written_data)
            self.assertIn("[Peer]", written_data)
            self.assertIn("Endpoint = vpn.example.com:51820", written_data)
    
    def test_create_ikev2_config(self):
        """Test IKEv2 configuration creation"""
        config = VPNConfig(
            vpn_type=VPNType.IKEV2,
            server_host="vpn.example.com",
            server_port=500
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = self.vpn_manager.create_vpn_config(config, "/tmp/ikev2.conf")
            
            self.assertTrue(result)
            written_data = mock_file.write.call_args[0][0]
            self.assertIn("conn ikev2-vpn", written_data)
            self.assertIn("right=vpn.example.com", written_data)
    
    def test_connect_vpn(self):
        """Test VPN connection"""
        config = VPNConfig(
            vpn_type=VPNType.OPENVPN,
            server_host="vpn.example.com",
            server_port=1194
        )
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            connection_id = self.vpn_manager.connect_vpn(config)
            
            self.assertIsNotNone(connection_id)
            self.assertIn(connection_id, self.vpn_manager.active_connections)
            mock_popen.assert_called()
    
    def test_disconnect_vpn(self):
        """Test VPN disconnection"""
        config = VPNConfig(
            vpn_type=VPNType.OPENVPN,
            server_host="vpn.example.com",
            server_port=1194
        )
        
        # First connect
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            connection_id = self.vpn_manager.connect_vpn(config)
        
        # Then disconnect
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = self.vpn_manager.disconnect_vpn(connection_id)
            
            self.assertTrue(result)
            self.assertNotIn(connection_id, self.vpn_manager.active_connections)
    
    def test_get_connection_status(self):
        """Test getting VPN connection status"""
        config = VPNConfig(
            vpn_type=VPNType.OPENVPN,
            server_host="vpn.example.com",
            server_port=1194
        )
        
        with patch('subprocess.Popen') as mock_popen, \
             patch('subprocess.run') as mock_run:
            
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            mock_run.return_value.returncode = 0
            
            connection_id = self.vpn_manager.connect_vpn(config)
            status = self.vpn_manager.get_connection_status(connection_id)
            
            self.assertIn("config", status)
            self.assertIn("status", status)
            self.assertIn("start_time", status)
            self.assertTrue(status["connected"])


class TestProxyChain(unittest.TestCase):
    """Test Proxy Chain functionality"""
    
    def setUp(self):
        self.proxy_chain = ProxyChain()
        
        # Add test proxies
        self.proxy_chain.add_proxy(ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="127.0.0.1",
            port=8080
        ))
        self.proxy_chain.add_proxy(ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="127.0.0.1",
            port=8081
        ))
    
    def test_add_proxy(self):
        """Test adding proxy to chain"""
        initial_count = len(self.proxy_chain.proxies)
        
        self.proxy_chain.add_proxy(ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="127.0.0.1",
            port=8082
        ))
        
        self.assertEqual(len(self.proxy_chain.proxies), initial_count + 1)
    
    def test_create_chain(self):
        """Test creating proxy chain"""
        result = self.proxy_chain.create_chain([0, 1])
        
        self.assertTrue(result)
        self.assertEqual(len(self.proxy_chain.current_chain), 2)
        self.assertEqual(self.proxy_chain.current_chain[0].port, 8080)
        self.assertEqual(self.proxy_chain.current_chain[1].port, 8081)
    
    def test_create_chain_invalid_index(self):
        """Test creating chain with invalid indices"""
        result = self.proxy_chain.create_chain([0, 5])
        
        self.assertFalse(result)
        self.assertEqual(len(self.proxy_chain.current_chain), 0)
    
    def test_connect_through_chain(self):
        """Test connecting through proxy chain"""
        self.proxy_chain.create_chain([0, 1])
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 Connection Established"
            
            result = self.proxy_chain.connect_through_chain("example.com", 80)
            
            self.assertIsNotNone(result)
            self.assertGreater(mock_sock.connect.call_count, 0)
    
    def test_connect_through_empty_chain(self):
        """Test connecting with empty proxy chain"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            
            result = self.proxy_chain.connect_through_chain("example.com", 80)
            
            self.assertIsNotNone(result)
            mock_sock.connect.assert_called_with(("example.com", 80))


class TestNetworkBypassManager(unittest.TestCase):
    """Test Network Bypass Manager"""
    
    def setUp(self):
        self.manager = NetworkBypassManager()
    
    def test_start_proxy_server(self):
        """Test starting proxy server through manager"""
        config = ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="0.0.0.0",
            port=8080
        )
        
        with patch('rsecure.modules.defense.vpn_proxy.ProxyServer.start') as mock_start:
            mock_start.return_value = True
            
            server_id = self.manager.start_proxy_server(config)
            
            self.assertIsNotNone(server_id)
            self.assertIn(server_id, self.manager.proxy_servers)
    
    def test_stop_proxy_server(self):
        """Test stopping proxy server through manager"""
        config = ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="0.0.0.0",
            port=8080
        )
        
        # First start server
        with patch('rsecure.modules.defense.vpn_proxy.ProxyServer.start') as mock_start, \
             patch('rsecure.modules.defense.vpn_proxy.ProxyServer.stop') as mock_stop:
            
            mock_start.return_value = True
            server_id = self.manager.start_proxy_server(config)
            
            result = self.manager.stop_proxy_server(server_id)
            
            self.assertTrue(result)
            self.assertNotIn(server_id, self.manager.proxy_servers)
            mock_stop.assert_called()
    
    def test_connect_vpn(self):
        """Test VPN connection through manager"""
        config = VPNConfig(
            vpn_type=VPNType.OPENVPN,
            server_host="vpn.example.com",
            server_port=1194
        )
        
        with patch.object(self.manager.vpn_manager, 'connect_vpn') as mock_connect:
            mock_connect.return_value = "vpn_123"
            
            connection_id = self.manager.connect_vpn(config)
            
            self.assertEqual(connection_id, "vpn_123")
            mock_connect.assert_called_with(config)
    
    def test_disconnect_vpn(self):
        """Test VPN disconnection through manager"""
        with patch.object(self.manager.vpn_manager, 'disconnect_vpn') as mock_disconnect:
            mock_disconnect.return_value = True
            
            result = self.manager.disconnect_vpn("vpn_123")
            
            self.assertTrue(result)
            mock_disconnect.assert_called_with("vpn_123")
    
    def test_create_bypass_route(self):
        """Test creating bypass route"""
        with patch.object(self.manager, '_try_bypass_method') as mock_try:
            mock_try.return_value = True
            
            bypass_id = self.manager.create_bypass_route("example.com", 80)
            
            self.assertIsNotNone(bypass_id)
            self.assertIn(bypass_id, self.manager.active_bypasses)
            
            bypass = self.manager.active_bypasses[bypass_id]
            self.assertEqual(bypass["target"], "example.com:80")
            self.assertEqual(bypass["status"], "active")
    
    def test_create_bypass_route_auto(self):
        """Test creating bypass route with auto method"""
        with patch.object(self.manager, '_try_bypass_method') as mock_try:
            mock_try.side_effect = [False, False, True, False]  # Third method succeeds
            
            bypass_id = self.manager.create_bypass_route("example.com", 80, "auto")
            
            self.assertIsNotNone(bypass_id)
            self.assertEqual(mock_try.call_count, 3)
    
    def test_get_bypass_status(self):
        """Test getting bypass status"""
        with patch.object(self.manager, '_try_bypass_method') as mock_try:
            mock_try.return_value = True
            
            bypass_id = self.manager.create_bypass_route("example.com", 80)
            status = self.manager.get_bypass_status(bypass_id)
            
            self.assertIn("method", status)
            self.assertIn("target", status)
            self.assertIn("status", status)
            self.assertIn("start_time", status)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_proxy_server_start_failure(self):
        """Test proxy server start failure"""
        config = ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="0.0.0.0",
            port=8080
        )
        proxy = ProxyServer(config)
        
        with patch('socket.socket') as mock_socket:
            mock_socket.side_effect = Exception("Bind failed")
            
            result = proxy.start()
            
            self.assertFalse(result)
    
    def test_vpn_config_creation_failure(self):
        """Test VPN config creation failure"""
        vpn_manager = VPNManager()
        config = VPNConfig(
            vpn_type=VPNType.OPENVPN,
            server_host="vpn.example.com",
            server_port=1194
        )
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = vpn_manager.create_vpn_config(config, "/root/openvpn.conf")
            
            self.assertFalse(result)
    
    def test_proxy_chain_connection_failure(self):
        """Test proxy chain connection failure"""
        proxy_chain = ProxyChain()
        proxy_chain.add_proxy(ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="127.0.0.1",
            port=8080
        ))
        proxy_chain.create_chain([0])
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect.side_effect = Exception("Connection failed")
            
            result = proxy_chain.connect_through_chain("example.com", 80)
            
            self.assertIsNone(result)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_concurrent_proxy_connections(self):
        """Test concurrent proxy connections"""
        proxy = ProxyServer(ProxyConfig(
            proxy_type=ProxyType.HTTP,
            host="0.0.0.0",
            port=8080
        ))
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            proxy.start()
            
            # Simulate multiple concurrent connections
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=proxy._handle_http_proxy,
                    args=(Mock(),)
                )
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=0.1)
            
            self.assertTrue(proxy.running)


if __name__ == '__main__':
    unittest.main()
