#!/usr/bin/env python3
"""
Cross-Platform Original Destination Extractor
Извлечение оригинального IP и порта назначения для Linux/macOS
"""

import sys
import socket
import struct
import platform
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class CrossPlatformDestinationExtractor:
    """Кросс-платформенный извлекатель назначения"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.platform = platform.system()
    
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
            if self.platform == "Linux":
                return self._extract_linux_destination(sock)
            elif self.platform == "Darwin":  # macOS
                return self._extract_macos_destination(sock)
            else:
                self.logger.warning(f"Unsupported platform: {self.platform}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to extract original destination: {e}")
            return None
    
    def _extract_linux_destination(self, sock):
        """Извлечение назначения для Linux"""
        try:
            # Получаем оригинальный адрес назначения
            orig_dst = sock.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
            
            if not orig_dst:
                self.logger.error("No original destination found")
                return None
            
            self.logger.info(f"Linux original destination: {orig_dst.hex()}")
            
            # Парсим IPv4 адрес
            if len(orig_dst) >= 4:
                ip_bytes = orig_dst[:4]
                port_bytes = orig_dst[4:6]
                
                ip = socket.inet_ntoa(ip_bytes)
                port = struct.unpack('!H', port_bytes)[0]
                
                destination = f"{ip}:{port}"
                self.logger.info(f"Extracted Linux destination: {destination}")
                return destination
            
            self.logger.error("Invalid destination format")
            return None
                
        except Exception as e:
            self.logger.error(f"Linux extraction failed: {e}")
            return None
    
    def _extract_macos_destination(self, sock):
        """Извлечение назначения для macOS"""
        try:
            # На macOS используем альтернативный подход
            # так как SO_ORIGINAL_DST может быть недоступен
            
            # Получаем информацию о сокете
            sockname = sock.getsockname()
            peername = sock.getpeername()
            
            self.logger.info(f"macOS socket info:")
            self.logger.info(f"  Local: {sockname}")
            self.logger.info(f"  Remote: {peername}")
            
            # Для macOS используем IP_PKTINFO для получения оригинального назначения
            try:
                # Это требует специальной обработки на macOS
                import fcntl
                import os
                
                # Получаем IP_PKTINFO
                SIOCGIPPKTOPTIONS = 0x40182083
                IP_PKTINFO_DEST = 0x00000008
                
                # Создаем структуру для запроса
                class IP_PKTINFO_DEST_Optional(struct.Struct):
                    _fields_ = [
                        ('name', '16s'),
                        ('value', '16s'),
                    ]
                
                option = IP_PKTINFO_DEST_Optional()
                option.name = b'IP_PKTINFO_DEST'
                
                # Выполняем системный вызов
                result = fcntl.ioctl(sock.fileno(), SIOCGIPPKTOPTIONS, option)
                
                if result == 0:
                    self.logger.warning("IP_PKTINFO not available")
                    return None
                
                # Получаем данные
                pktinfo = IP_PKTINFO_DEST_Optional.from_buffer_copy(result)
                
                if pktinfo.value:
                    # Парсим IP адрес назначения
                    dest_ip = socket.inet_ntoa(pktinfo.value[:4])
                    dest_port = struct.unpack('!H', pktinfo.value[4:6])[0]
                    
                    destination = f"{dest_ip}:{dest_port}"
                    self.logger.info(f"macOS extracted destination: {destination}")
                    return destination
                
            except ImportError:
                self.logger.warning("fcntl module not available")
            except Exception as e:
                self.logger.error(f"macOS IP_PKTINFO extraction failed: {e}")
            
            # Fallback: используем информацию о соединении
            if peername:
                ip, port = peername
                destination = f"{ip}:{port}"
                self.logger.info(f"macOS fallback destination: {destination}")
                return destination
            
            return None
                
        except Exception as e:
            self.logger.error(f"macOS extraction failed: {e}")
            return None
    
    def test_destination_extraction(self):
        """Тестировать извлечение назначения"""
        self.logger.info(f"Testing destination extraction on {self.platform}")
        
        try:
            # Создаем тестовый сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if self.platform == "Linux":
                # Устанавливаем тестовый адрес назначения
                test_dst = socket.inet_aton("93.184.216.34")  # example.com
                sock.setsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, test_dst)
                
            elif self.platform == "Darwin":
                # На macOS просто создаем сокет для теста
                pass  # IP_PKTINFO проверим позже
            
            # Извлекаем оригинальный адрес назначения
            destination = self.extract_original_destination(sock)
            
            if destination:
                self.logger.info("✅ Destination extraction works")
                self.logger.info(f"  Platform: {self.platform}")
                self.logger.info(f"  Destination: {destination}")
                return True
            else:
                self.logger.error("❌ Destination extraction failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Test failed: {e}")
            return False

def main():
    """Основная функция"""
    extractor = CrossPlatformDestinationExtractor()
    
    print("🔍 Cross-Platform Destination Extraction Tests")
    print("=" * 60)
    print(f"Platform: {extractor.platform}")
    
    # Запускаем тест
    success = extractor.test_destination_extraction()
    
    print(f"\n📊 Test Result: {'✅' if success else '❌'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
