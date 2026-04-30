"""
Tests for DPI Bypass Module
"""

import unittest
import socket
import threading
import time
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rsecure.modules.defense.dpi_bypass import (
    DPIBypassEngine, BypassConfig, BypassMethod, 
    AdvancedBypassTechniques, BypassManager
)


class TestDPIBypassEngine(unittest.TestCase):
    """Test DPI Bypass Engine functionality"""
    
    def setUp(self):
        self.engine = DPIBypassEngine()
        self.config = BypassConfig(
            method=BypassMethod.FRAGMENTATION,
            target_host="example.com",
            target_port=80,
            fragment_size=256,
            delay_ms=50
        )
    
    def test_fragmentation_bypass(self):
        """Test packet fragmentation bypass"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._fragmentation_bypass(self.config)
            
            self.assertTrue(result)
            mock_socket.assert_called()
            mock_sock.connect.assert_called_with(("example.com", 80))
            mock_sock.send.assert_called()
            mock_sock.close.assert_called()
    
    def test_tls_sni_splitting(self):
        """Test TLS SNI splitting bypass"""
        config = BypassConfig(
            method=BypassMethod.TLS_SNI_SPLITTING,
            target_host="example.com",
            target_port=443
        )
        
        with patch('socket.socket') as mock_socket, \
             patch('ssl.create_default_context') as mock_ssl:
            
            mock_sock = Mock()
            mock_ssl_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_ssl.return_value.wrap_socket.return_value = mock_ssl_sock
            mock_ssl_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._tls_sni_splitting(config)
            
            self.assertTrue(result)
            mock_socket.assert_called()
            mock_sock.connect.assert_called_with(("example.com", 443))
    
    def test_http_header_obfuscation(self):
        """Test HTTP header obfuscation"""
        config = BypassConfig(
            method=BypassMethod.HTTP_HEADER_OBFUSCATION,
            target_host="example.com",
            target_port=80,
            custom_headers={"X-Custom": "value"}
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._http_header_obfuscation(config)
            
            self.assertTrue(result)
            mock_sock.send.assert_called()
            # Check that custom headers are included
            sent_data = mock_sock.send.call_args[0][0]
            self.assertIn(b"X-Custom: value", sent_data)
    
    def test_domain_fronting(self):
        """Test domain fronting bypass"""
        config = BypassConfig(
            method=BypassMethod.DOMAIN_FRONTING,
            target_host="target.example.com",
            target_port=443
        )
        
        with patch('socket.socket') as mock_socket, \
             patch('ssl.create_default_context') as mock_ssl:
            
            mock_sock = Mock()
            mock_ssl_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_ssl.return_value.wrap_socket.return_value = mock_ssl_sock
            mock_ssl_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._domain_fronting(config)
            
            self.assertTrue(result)
            # Check that Host header is different from SNI
            sent_data = mock_ssl_sock.send.call_args[0][0]
            self.assertIn(b"Host: target.example.com", sent_data)
    
    def test_proxy_chaining(self):
        """Test proxy chaining bypass"""
        config = BypassConfig(
            method=BypassMethod.PROXY_CHAINING,
            target_host="example.com",
            target_port=80,
            proxy_chain=["127.0.0.1:8080", "127.0.0.1:8081"]
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 Connection Established"
            
            result = self.engine._proxy_chaining(config)
            
            self.assertTrue(result)
            self.assertEqual(mock_sock.connect.call_count, 2)
    
    def test_tor_routing(self):
        """Test Tor routing bypass"""
        config = BypassConfig(
            method=BypassMethod.TOR_ROUTING,
            target_host="example.com",
            target_port=80
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._tor_routing(config)
            
            self.assertTrue(result)
            # Check SOCKS5 handshake
            calls = mock_sock.send.call_args_list
            self.assertTrue(any(b"\x05\x01\x00" in call[0][0] for call in calls))
    
    def test_encoded_payload(self):
        """Test encoded payload bypass"""
        config = BypassConfig(
            method=BypassMethod.ENCODED_PAYLOAD,
            target_host="example.com",
            target_port=80
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._encoded_payload(config)
            
            self.assertTrue(result)
            # Check that payload is encoded
            sent_data = mock_sock.send.call_args[0][0]
            self.assertIn(b"data=", sent_data)
    
    def test_stealth_ports_bypass(self):
        """Test stealth ports bypass"""
        config = BypassConfig(
            method=BypassMethod.STEALTH_PORTS,
            target_host="example.com",
            target_port=80
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            result = self.engine._stealth_ports_bypass(config)
            
            self.assertTrue(result)
            # Check that stealth ports are tried
            self.assertTrue(any(port in self.engine.stealth_ports for port in [80, 443, 8443]))


class TestAdvancedBypassTechniques(unittest.TestCase):
    """Test Advanced Bypass Techniques"""
    
    def setUp(self):
        self.advanced = AdvancedBypassTechniques()
        self.config = BypassConfig(
            method=BypassMethod.FRAGMENTATION,
            target_host="example.com",
            target_port=80
        )
    
    def test_multi_stage_bypass(self):
        """Test multi-stage bypass"""
        with patch.object(self.advanced.engine, 'bypass_dpi') as mock_bypass:
            mock_bypass.return_value = True
            
            result = self.advanced.multi_stage_bypass(self.config)
            
            self.assertTrue(result)
            # Check that multiple techniques were tried
            self.assertGreater(mock_bypass.call_count, 0)
    
    def test_adaptive_bypass(self):
        """Test adaptive bypass"""
        with patch.object(self.advanced.engine, 'bypass_dpi') as mock_bypass:
            mock_bypass.return_value = True
            
            result = self.advanced.adaptive_bypass(self.config)
            
            self.assertTrue(result)
            # Check that all techniques were evaluated
            self.assertEqual(mock_bypass.call_count, len(BypassMethod))


class TestBypassManager(unittest.TestCase):
    """Test Bypass Manager"""
    
    def setUp(self):
        self.manager = BypassManager()
        self.config = BypassConfig(
            method=BypassMethod.FRAGMENTATION,
            target_host="example.com",
            target_port=80
        )
    
    def test_start_bypass(self):
        """Test starting bypass operation"""
        with patch.object(self.manager.engine, 'bypass_dpi') as mock_bypass:
            mock_bypass.return_value = True
            
            bypass_id = self.manager.start_bypass(self.config)
            
            self.assertIsNotNone(bypass_id)
            self.assertIn(bypass_id, self.manager.active_bypasses)
            
            # Wait for background thread
            time.sleep(0.1)
            
            status = self.manager.get_bypass_status(bypass_id)
            self.assertEqual(status["status"], "completed")
            self.assertTrue(status["success"])
    
    def test_stop_bypass(self):
        """Test stopping bypass operation"""
        bypass_id = self.manager.start_bypass(self.config)
        
        result = self.manager.stop_bypass(bypass_id)
        
        self.assertTrue(result)
        status = self.manager.get_bypass_status(bypass_id)
        self.assertEqual(status["status"], "stopped")
    
    def test_get_bypass_history(self):
        """Test getting bypass history"""
        with patch.object(self.manager.engine, 'bypass_dpi') as mock_bypass:
            mock_bypass.return_value = True
            
            bypass_id = self.manager.start_bypass(self.config)
            
            # Wait for completion
            time.sleep(0.1)
            
            history = self.manager.get_bypass_history()
            
            self.assertGreater(len(history), 0)
            self.assertEqual(history[0]["bypass_id"], bypass_id)


class TestProtocolMimicking(unittest.TestCase):
    """Test protocol mimicking functionality"""
    
    def setUp(self):
        self.engine = DPIBypassEngine()
    
    def test_mimic_ssh(self):
        """Test SSH protocol mimicking"""
        config = BypassConfig(
            method=BypassMethod.PROTOCOL_MIMICKING,
            target_host="example.com",
            target_port=22
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"SSH-2.0-OpenSSH_7.4"
            
            result = self.engine._mimic_ssh(config)
            
            self.assertTrue(result)
            # Check SSH version string
            sent_data = mock_sock.send.call_args[0][0]
            self.assertIn(b"SSH-2.0-OpenSSH_7.4", sent_data)
    
    def test_mimic_ftp(self):
        """Test FTP protocol mimicking"""
        config = BypassConfig(
            method=BypassMethod.PROTOCOL_MIMICKING,
            target_host="example.com",
            target_port=21
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"220 FTP Server Ready"
            
            result = self.engine._mimic_ftp(config)
            
            self.assertTrue(result)
            # Check FTP commands
            sent_data = mock_sock.send.call_args[0][0]
            self.assertIn(b"USER anonymous", sent_data)
    
    def test_mimic_smtp(self):
        """Test SMTP protocol mimicking"""
        config = BypassConfig(
            method=BypassMethod.PROTOCOL_MIMICKING,
            target_host="example.com",
            target_port=25
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"220 SMTP Server Ready"
            
            result = self.engine._mimic_smtp(config)
            
            self.assertTrue(result)
            # Check SMTP commands
            sent_data = mock_sock.send.call_args[0][0]
            self.assertIn(b"EHLO example.com", sent_data)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def setUp(self):
        self.engine = DPIBypassEngine()
        self.config = BypassConfig(
            method=BypassMethod.FRAGMENTATION,
            target_host="invalid.host",
            target_port=80
        )
    
    def test_connection_failure(self):
        """Test handling of connection failures"""
        with patch('socket.socket') as mock_socket:
            mock_socket.side_effect = Exception("Connection failed")
            
            result = self.engine.bypass_dpi(self.config)
            
            self.assertFalse(result)
    
    def test_invalid_method(self):
        """Test handling of invalid bypass method"""
        config = BypassConfig(
            method="invalid_method",
            target_host="example.com",
            target_port=80
        )
        
        result = self.engine.bypass_dpi(config)
        
        self.assertFalse(result)
    
    def test_timeout_handling(self):
        """Test handling of timeouts"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect.side_effect = socket.timeout("Timeout")
            
            result = self.engine._fragmentation_bypass(self.config)
            
            self.assertFalse(result)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        self.engine = DPIBypassEngine()
        self.config = BypassConfig(
            method=BypassMethod.FRAGMENTATION,
            target_host="example.com",
            target_port=80,
            fragment_size=512,
            delay_ms=10
        )
    
    def test_fragmentation_performance(self):
        """Test fragmentation bypass performance"""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.recv.return_value = b"HTTP/1.1 200 OK"
            
            start_time = time.time()
            result = self.engine._fragmentation_bypass(self.config)
            end_time = time.time()
            
            self.assertTrue(result)
            # Check that operation completes in reasonable time
            self.assertLess(end_time - start_time, 1.0)
    
    def test_concurrent_bypass(self):
        """Test concurrent bypass operations"""
        manager = BypassManager()
        
        with patch.object(manager.engine, 'bypass_dpi') as mock_bypass:
            mock_bypass.return_value = True
            
            # Start multiple bypass operations
            bypass_ids = []
            for i in range(5):
                config = BypassConfig(
                    method=BypassMethod.FRAGMENTATION,
                    target_host=f"example{i}.com",
                    target_port=80
                )
                bypass_id = manager.start_bypass(config)
                bypass_ids.append(bypass_id)
            
            # Wait for all to complete
            time.sleep(0.5)
            
            # Check that all completed successfully
            for bypass_id in bypass_ids:
                status = manager.get_bypass_status(bypass_id)
                self.assertEqual(status["status"], "completed")
                self.assertTrue(status["success"])


if __name__ == '__main__':
    unittest.main()
