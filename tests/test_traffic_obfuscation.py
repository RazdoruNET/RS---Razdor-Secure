"""
Tests for Traffic Obfuscation Module
"""

import unittest
import socket
import threading
import time
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rsecure.modules.defense.traffic_obfuscation import (
    TrafficObfuscator, ObfuscationConfig, ObfuscationMethod,
    ProtocolType, ObfuscatedSocket, AdvancedObfuscation,
    ObfuscationManager
)


class TestTrafficObfuscator(unittest.TestCase):
    """Test Traffic Obfuscator functionality"""
    
    def setUp(self):
        self.obfuscator = TrafficObfuscator()
        self.config = ObfuscationConfig(
            method=ObfuscationMethod.XOR,
            encryption_key=b"test_key_123456789012345678901234"
        )
    
    def test_xor_obfuscation(self):
        """Test XOR obfuscation"""
        data = b"Hello, World!"
        
        obfuscated = self.obfuscator._xor_obfuscate(data, self.config)
        deobfuscated = self.obfuscator._xor_obfuscate(obfuscated, self.config)
        
        self.assertEqual(deobfuscated, data)
        self.assertNotEqual(obfuscated, data)
    
    def test_aes_encryption(self):
        """Test AES encryption"""
        data = b"Hello, World! This is a test message."
        
        encrypted = self.obfuscator._aes_encrypt(data, self.config)
        decrypted = self.obfuscator._aes_decrypt(encrypted, self.config)
        
        self.assertEqual(decrypted, data)
        self.assertNotEqual(encrypted, data)
        # Check IV is prepended
        self.assertEqual(len(encrypted), len(data) + 16 + 16)  # IV + padding
    
    def test_chacha20_encryption(self):
        """Test ChaCha20 encryption"""
        data = b"Hello, World! This is a test message."
        
        encrypted = self.obfuscator._chacha20_encrypt(data, self.config)
        decrypted = self.obfuscator._chacha20_decrypt(encrypted, self.config)
        
        self.assertEqual(decrypted, data)
        self.assertNotEqual(encrypted, data)
        # Check nonce is prepended
        self.assertEqual(len(encrypted), len(data) + 12)  # nonce
    
    def test_base64_encoding(self):
        """Test Base64 encoding"""
        data = b"Hello, World!"
        
        encoded = self.obfuscator._base64_encode(data)
        decoded = self.obfuscator._base64_decode(encoded)
        
        self.assertEqual(decoded, data)
        self.assertNotEqual(encoded, data)
    
    def test_zlib_compression(self):
        """Test ZLIB compression"""
        data = b"Hello, World! " * 100  # Larger data for compression
        
        compressed = self.obfuscator._zlib_compress(data)
        decompressed = self.obfuscator._zlib_decompress(compressed)
        
        self.assertEqual(decompressed, data)
        self.assertLess(len(compressed), len(data))
    
    def test_custom_transform(self):
        """Test custom transformation"""
        data = b"Hello"
        
        transformed = self.obfuscator._custom_transform(data, self.config)
        reversed_transformed = self.obfuscator._custom_reverse(transformed, self.config)
        
        self.assertEqual(reversed_transformed, data)
    
    def test_steganography_hide_extract(self):
        """Test steganography hide and extract"""
        data = b"Secret message"
        config = ObfuscationConfig(
            method=ObfuscationMethod.STEGANOGRAPHY,
            steganography_medium="image"
        )
        
        hidden = self.obfuscator._steganography_hide(data, config)
        extracted = self.obfuscator._steganography_extract(hidden, config)
        
        self.assertEqual(extracted, data)
        self.assertTrue(hidden.startswith(b"IMG_STEG:"))
    
    def test_packet_padding(self):
        """Test packet padding"""
        data = b"Hello"
        config = ObfuscationConfig(
            method=ObfuscationMethod.PACKET_PADDING,
            padding_size=100
        )
        
        padded = self.obfuscator._packet_padding(data, config)
        unpadded = self.obfuscator._packet_unpad(padded, config)
        
        self.assertEqual(unpadded, data)
        self.assertGreater(len(padded), len(data))
    
    def test_timing_obfuscation(self):
        """Test timing obfuscation"""
        data = b"Hello"
        config = ObfuscationConfig(
            method=ObfuscationMethod.TIMING_OBFUSCATION,
            timing_variance=0.5
        )
        
        obfuscated = self.obfuscator._timing_obfuscate(data, config)
        deobfuscated = self.obfuscator._timing_deobfuscate(obfuscated, config)
        
        self.assertEqual(deobfuscated, data)
        self.assertEqual(len(obfuscated), len(data) + 8)  # timestamp + delay


class TestProtocolMimicking(unittest.TestCase):
    """Test protocol mimicking functionality"""
    
    def setUp(self):
        self.obfuscator = TrafficObfuscator()
        self.data = b"Secret data to hide"
    
    def test_mimic_http(self):
        """Test HTTP protocol mimicking"""
        mimicked = self.obfuscator._mimic_http(self.data)
        
        self.assertIn(b"GET /path HTTP/1.1", mimicked)
        self.assertIn(b"Host: example.com", mimicked)
        self.assertIn(b"X-Custom-Data:", mimicked)
    
    def test_mimic_https(self):
        """Test HTTPS protocol mimicking"""
        mimicked = self.obfuscator._mimic_https(self.data)
        
        # Check TLS record structure
        self.assertEqual(mimicked[0], 0x17)  # Application data
        self.assertEqual(mimicked[1:3], b"\x03\x03")  # TLS 1.2
    
    def test_mimic_ssh(self):
        """Test SSH protocol mimicking"""
        mimicked = self.obfuscator._mimic_ssh(self.data)
        
        # Check SSH packet structure
        packet_length = struct.unpack("!I", mimicked[:4])[0]
        self.assertEqual(packet_length, len(self.data) + 4)
    
    def test_mimic_ftp(self):
        """Test FTP protocol mimicking"""
        mimicked = self.obfuscator._mimic_ftp(self.data)
        
        self.assertIn(b"STOR", mimicked)
        self.assertIn(b"\r\n", mimicked)
    
    def test_mimic_smtp(self):
        """Test SMTP protocol mimicking"""
        mimicked = self.obfuscator._mimic_smtp(self.data)
        
        self.assertIn(b"DATA", mimicked)
        self.assertIn(b"Subject:", mimicked)
    
    def test_mimic_dns(self):
        """Test DNS protocol mimicking"""
        mimicked = self.obfuscator._mimic_dns(self.data)
        
        # Check DNS structure
        self.assertEqual(len(mimicked), 12 + 1 + len(base64.b64encode(self.data)[:63]) + 4)
    
    def test_mimic_icmp(self):
        """Test ICMP protocol mimicking"""
        mimicked = self.obfuscator._mimic_icmp(self.data)
        
        # Check ICMP structure
        self.assertEqual(mimicked[0], 8)  # Echo Request
        self.assertEqual(mimicked[1], 0)  # Code
    
    def test_mimic_tor(self):
        """Test Tor protocol mimicking"""
        mimicked = self.obfuscator._mimic_tor(self.data)
        
        # Check Tor cell structure
        self.assertEqual(len(mimicked), 512)  # Fixed cell size
        self.assertEqual(mimicked[2], 2)  # Relay cell


class TestObfuscatedSocket(unittest.TestCase):
    """Test Obfuscated Socket functionality"""
    
    def setUp(self):
        self.mock_socket = Mock()
        self.obfuscator = TrafficObfuscator()
        self.config = ObfuscationConfig(
            method=ObfuscationMethod.XOR,
            encryption_key=b"test_key_123456789012345678901234"
        )
        self.obs_socket = ObfuscatedSocket(self.mock_socket, self.obfuscator, self.config)
    
    def test_send_data(self):
        """Test sending data through obfuscated socket"""
        data = b"Hello, World!"
        
        result = self.obs_socket.send(data)
        
        self.assertTrue(result)
        # Check that data was put in send buffer
        self.assertFalse(self.obs_socket.send_buffer.empty())
    
    def test_receive_data(self):
        """Test receiving data through obfuscated socket"""
        # Put data in receive buffer
        original_data = b"Hello, World!"
        obfuscated_data = self.obfuscator.obfuscate_data(original_data, self.config)
        self.obs_socket.receive_buffer.put(obfuscated_data)
        
        received_data = self.obs_socket.receive(timeout=0.1)
        
        self.assertEqual(received_data, original_data)
    
    def test_start_obfuscation(self):
        """Test starting obfuscation threads"""
        self.obs_socket.start_obfuscation()
        
        self.assertTrue(self.obs_socket.running)
    
    def test_close_socket(self):
        """Test closing obfuscated socket"""
        self.obs_socket.close()
        
        self.assertFalse(self.obs_socket.running)
        self.mock_socket.close.assert_called()


class TestAdvancedObfuscation(unittest.TestCase):
    """Test Advanced Obfuscation functionality"""
    
    def setUp(self):
        self.advanced = AdvancedObfuscation()
        self.data = b"Test data for advanced obfuscation"
    
    def test_layered_obfuscation(self):
        """Test layered obfuscation"""
        methods = [
            ObfuscationMethod.ZLIB,
            ObfuscationMethod.BASE64,
            ObfuscationMethod.XOR
        ]
        
        layered = self.advanced.create_layered_obfuscation(self.data, methods)
        restored = self.advanced.remove_layered_obfuscation(layered)
        
        self.assertEqual(restored, self.data)
        self.assertNotEqual(layered, self.data)
    
    def test_adaptive_obfuscation(self):
        """Test adaptive obfuscation"""
        # Test with high inspection
        network_conditions = {"high_inspection": True}
        result = self.advanced.adaptive_obfuscation(self.data, network_conditions)
        
        # Should use protocol mimicking
        self.assertIn(b"GET", result) or self.assertIn(b"SSH", result)
        
        # Test with bandwidth limited
        network_conditions = {"bandwidth_limited": True}
        result = self.advanced.adaptive_obfuscation(self.data, network_conditions)
        
        # Should use compression
        self.assertLess(len(result), len(self.data))
        
        # Test with high latency
        network_conditions = {"high_latency": True}
        result = self.advanced.adaptive_obfuscation(self.data, network_conditions)
        
        # Should use encoding
        self.assertNotEqual(result, self.data)


class TestObfuscationManager(unittest.TestCase):
    """Test Obfuscation Manager functionality"""
    
    def setUp(self):
        self.manager = ObfuscationManager()
    
    def test_create_obfuscated_connection(self):
        """Test creating obfuscated connection"""
        config = ObfuscationConfig(
            method=ObfuscationMethod.XOR,
            encryption_key=b"test_key_123456789012345678901234"
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect.return_value = None
            
            obs_socket = self.manager.create_obfuscated_connection("example.com", 80, config)
            
            self.assertIsNotNone(obs_socket)
            self.assertIsInstance(obs_socket, ObfuscatedSocket)
            self.assertGreater(len(self.manager.active_sessions), 0)
    
    def test_close_session(self):
        """Test closing obfuscated session"""
        config = ObfuscationConfig(
            method=ObfuscationMethod.XOR,
            encryption_key=b"test_key_123456789012345678901234"
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect.return_value = None
            
            obs_socket = self.manager.create_obfuscated_connection("example.com", 80, config)
            
            # Get session ID
            session_id = list(self.manager.active_sessions.keys())[0]
            
            result = self.manager.close_session(session_id)
            
            self.assertTrue(result)
            self.assertNotIn(session_id, self.manager.active_sessions)
    
    def test_get_session_stats(self):
        """Test getting session statistics"""
        config = ObfuscationConfig(
            method=ObfuscationMethod.XOR,
            encryption_key=b"test_key_123456789012345678901234"
        )
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_socket.return_value = mock_sock
            mock_sock.connect.return_value = None
            
            obs_socket = self.manager.create_obfuscated_connection("example.com", 80, config)
            
            # Get session ID
            session_id = list(self.manager.active_sessions.keys())[0]
            
            stats = self.manager.get_session_stats(session_id)
            
            self.assertIn("start_time", stats)
            self.assertIn("bytes_sent", stats)
            self.assertIn("bytes_received", stats)
            self.assertIn("method", stats)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def setUp(self):
        self.obfuscator = TrafficObfuscator()
    
    def test_aes_decryption_without_key(self):
        """Test AES decryption without key"""
        data = b"Hello"
        config = ObfuscationConfig(method=ObfuscationMethod.AES)
        
        result = self.obfuscator._aes_decrypt(data, config)
        
        # Should return original data if no key
        self.assertEqual(result, data)
    
    def test_chacha20_decryption_without_key(self):
        """Test ChaCha20 decryption without key"""
        data = b"Hello"
        config = ObfuscationConfig(method=ObfuscationMethod.CHACHA20)
        
        result = self.obfuscator._chacha20_decrypt(data, config)
        
        # Should return original data if no key
        self.assertEqual(result, data)
    
    def test_invalid_base64_decode(self):
        """Test invalid Base64 decode"""
        data = b"invalid_base64!"
        
        with self.assertRaises(Exception):
            self.obfuscator._base64_decode(data)
    
    def test_zlib_decompress_invalid_data(self):
        """Test ZLIB decompress invalid data"""
        data = b"not_compressed_data"
        
        with self.assertRaises(Exception):
            self.obfuscator._zlib_decompress(data)
    
    def test_steganography_extract_invalid_format(self):
        """Test steganography extract invalid format"""
        data = b"invalid_steganography_format"
        config = ObfuscationConfig(
            method=ObfuscationMethod.STEGANOGRAPHY,
            steganography_medium="image"
        )
        
        result = self.obfuscator._steganography_extract(data, config)
        
        # Should return original data for invalid format
        self.assertEqual(result, data)
    
    def test_packet_unpad_invalid_data(self):
        """Test packet unpad invalid data"""
        data = b"short"
        config = ObfuscationConfig(method=ObfuscationMethod.PACKET_PADDING)
        
        result = self.obfuscator._packet_unpad(data, config)
        
        # Should return original data for invalid format
        self.assertEqual(result, data)
    
    def test_timing_deobfuscate_invalid_data(self):
        """Test timing deobfuscate invalid data"""
        data = b"short"
        config = ObfuscationConfig(method=ObfuscationMethod.TIMING_OBFUSCATION)
        
        result = self.obfuscator._timing_deobfuscate(data, config)
        
        # Should return original data for invalid format
        self.assertEqual(result, data)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        self.obfuscator = TrafficObfuscator()
        self.config = ObfuscationConfig(
            method=ObfuscationMethod.AES,
            encryption_key=b"test_key_123456789012345678901234"
        )
    
    def test_obfuscation_performance(self):
        """Test obfuscation performance"""
        data = b"Hello, World! " * 1000  # Large data
        
        start_time = time.time()
        obfuscated = self.obfuscator.obfuscate_data(data, self.config)
        end_time = time.time()
        
        self.assertNotEqual(obfuscated, data)
        self.assertLess(end_time - start_time, 1.0)  # Should complete within 1 second
    
    def test_deobfuscation_performance(self):
        """Test deobfuscation performance"""
        data = b"Hello, World! " * 1000  # Large data
        obfuscated = self.obfuscator.obfuscate_data(data, self.config)
        
        start_time = time.time()
        deobfuscated = self.obfuscator.deobfuscate_data(obfuscated, self.config)
        end_time = time.time()
        
        self.assertEqual(deobfuscated, data)
        self.assertLess(end_time - start_time, 1.0)  # Should complete within 1 second
    
    def test_concurrent_obfuscation(self):
        """Test concurrent obfuscation operations"""
        data = b"Hello, World!"
        
        def obfuscate_thread():
            return self.obfuscator.obfuscate_data(data, self.config)
        
        threads = []
        results = []
        
        # Start multiple threads
        for i in range(10):
            thread = threading.Thread(target=lambda: results.append(obfuscate_thread()))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=1.0)
        
        # Check all operations completed
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertNotEqual(result, data)


if __name__ == '__main__':
    unittest.main()
