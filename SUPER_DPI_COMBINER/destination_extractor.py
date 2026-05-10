#!/usr/bin/env python3
"""
Original Destination Extractor - Извлечение оригинального IP и порта назначения
"""

import sys
import socket
import struct
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class DestinationExtractor:
    """Извлекатель оригинального назначения через socket.getsockopt"""
    
    def __init__(self):
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Настройка логгирования"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def extract_original_destination(self, sock):
        """Извлечь оригинальный IP и порт назначения"""
        try:
            # Получаем оригинальный адрес назначения
            orig_dst = sock.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
            
            if not orig_dst:
                self.logger.error("No original destination found")
                return None
            
            self.logger.info(f"Raw original destination: {orig_dst.hex()}")
            
            # Парсим в зависимости от длины
            if len(orig_dst) == 4:
                # IPv4 адрес
                ip_bytes = orig_dst[:4]
                port_bytes = orig_dst[4:6]
                
                ip = socket.inet_ntoa(ip_bytes)
                port = struct.unpack('!H', port_bytes)[0]
                
                destination = f"{ip}:{port}"
                
                self.logger.info(f"Extracted IPv4 destination: {destination}")
                return destination
                
            elif len(orig_dst) == 16:
                # IPv6 адрес
                ip_bytes = orig_dst[:16]
                port_bytes = orig_dst[16:18]
                
                # Для IPv6 нужна специальная обработка
                import ipaddress
                try:
                    ip = ipaddress.IPv6Address(ip_bytes.tobytes())
                    port = struct.unpack('!H', port_bytes)[0]
                    destination = f"[{ip}]:{port}"
                    
                    self.logger.info(f"Extracted IPv6 destination: {destination}")
                    return destination
                except:
                    self.logger.error("Failed to parse IPv6 address")
                    return None
            else:
                self.logger.error(f"Unsupported destination length: {len(orig_dst)} bytes")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to extract original destination: {e}")
            return None
    
    def test_destination_extraction(self):
        """Тестировать извлечение назначения"""
        self.logger.info("Testing destination extraction...")
        
        try:
            # Создаем тестовый сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Устанавливаем тестовый адрес назначения
            test_dst = socket.inet_aton("93.184.216.34")  # example.com
            test_port = 80
            
            # Устанавливаем оригинальный адрес назначения
            sock.setsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, test_dst)
            
            # Проверяем что адрес установлен
            extracted = sock.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
            
            if extracted == test_dst:
                self.logger.info("✅ Destination extraction works correctly")
                
                # Выводим детальную информацию
                ip_bytes = extracted[:4]
                port_bytes = extracted[4:6]
                ip = socket.inet_ntoa(ip_bytes)
                port = struct.unpack('!H', port_bytes)[0]
                
                self.logger.info(f"  Extracted IP: {ip}")
                self.logger.info(f"  Extracted Port: {port}")
                self.logger.info(f"  Full Destination: {ip}:{port}")
                
                return True
            else:
                self.logger.error(f"❌ Destination extraction failed")
                self.logger.error(f"  Expected: {test_dst.hex()}")
                self.logger.error(f"  Got: {extracted.hex()}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Test failed: {e}")
            return False
    
    def test_real_connection(self):
        """Тестировать с реальным соединением"""
        self.logger.info("Testing with real connection...")
        
        try:
            # Создаем сокет и подключаемся к реальному серверу
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("93.184.216.34", 80))  # example.com
            
            # Извлекаем оригинальный адрес назначения
            destination = self.extract_original_destination(sock)
            
            if destination:
                self.logger.info(f"✅ Real connection test successful")
                self.logger.info(f"  Original destination: {destination}")
                return True
            else:
                self.logger.error("❌ Real connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Real connection failed: {e}")
            return False

def main():
    """Основная функция"""
    extractor = DestinationExtractor()
    
    # Запускаем тесты
    print("🔍 Original Destination Extraction Tests")
    print("=" * 50)
    
    # Тест 1: Базовое извлечение
    test1_success = extractor.test_destination_extraction()
    
    # Тест 2: Извлечение с реальным соединением
    test2_success = extractor.test_real_connection()
    
    # Итоги
    print(f"\n📊 Test Results:")
    print(f"  Basic extraction: {'✅' if test1_success else '❌'}")
    print(f"  Real connection: {'✅' if test2_success else '❌'}")
    
    overall_success = test1_success and test2_success
    print(f"\n🎯 Overall: {'VERIFIED' if overall_success else 'NOT VERIFIED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
