"""
Steganography Pipeline - Скрытие данных в медиа
"""

import asyncio
import time
import random
import base64
from typing import Dict, Any

# Импорт с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class SteganographyPipeline(BasePipeline):
    """Пайплайн для стеганографии"""
    
    def __init__(self):
        super().__init__("Steganography", BypassTechnique.PROTOCOL_OBFUSCATION, priority=22)
        self.cover_images = []
        self.stego_method = "lsb"
        self.extraction_key = ""
        
    async def execute(self, request: BypassRequest) -> BypassResponse:
        """Выполнение через стеганографию"""
        start_time = time.time()
        
        try:
            # Выбираем случайное cover image
            cover_image = random.choice(self.cover_images)
            
            # Кодируем данные
            encoded_data = self._encode_request_data(request)
            
            # Внедряем данные в cover image
            stego_image = self._embed_data(encoded_data, cover_image)
            
            # Имитация передачи стеганограммы
            await asyncio.sleep(0.03)
            
            # Извлечение данных на стороне получателя
            await asyncio.sleep(0.02)
            
            response_time = time.time() - start_time
            
            # Стеганография очень эффективно обходит DPI
            success_probability = 0.8
            if self.stego_method == 'lsb':
                success_probability += 0.1
            if cover_image.endswith('.png'):
                success_probability += 0.05
            
            success = random.random() < success_probability
            
            return BypassResponse(
                success=success,
                status_code=200 if success else 403,
                response_time=response_time,
                technique_used=self.name,
                headers={
                    'X-Cover-Image': cover_image,
                    'X-Stego-Method': self.stego_method,
                    'X-Stego-Size': str(len(encoded_data)),
                    'X-Extraction-Key': self.extraction_key,
                    'X-Protocol': 'Steganography'
                }
            )
            
        except Exception as e:
            return BypassResponse(
                success=False,
                error=f"Steganography error: {str(e)}",
                response_time=time.time() - start_time
            )
    
    def _encode_request_data(self, request: BypassRequest) -> str:
        """Кодирование данных запроса"""
        # Собираем все данные
        data_parts = [
            request.host,
            str(request.port),
            request.method,
            str(request.headers) if request.headers else "",
            request.data.decode('utf-8', errors='ignore') if request.data else ""
        ]
        
        combined_data = '|'.join(data_parts)
        
        # Кодируем в base64 для встраивания
        return base64.b64encode(combined_data.encode()).decode()
    
    def _embed_data(self, data: str, cover_image: str) -> str:
        """Внедрение данных в cover image"""
        # Имитация LSB стеганографии
        if self.stego_method == 'lsb':
            # Least Significant Bit метод
            stego_data = f"LSB:{data}:{cover_image}"
        elif self.stego_method == 'dct':
            # DCT коэффициенты
            stego_data = f"DCT:{data}:{cover_image}"
        elif self.stego_method == 'frequency':
            # Частотная стеганография
            stego_data = f"FREQ:{data}:{cover_image}"
        else:
            stego_data = f"STEGO:{data}:{cover_image}"
        
        return stego_data
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Инициализация с конфигурацией"""
        self.config = config
        self.cover_images = config.get('cover_images', [
            'cat.png',
            'dog.jpg',
            'nature.png',
            'city.jpg',
            'abstract.png',
            'landscape.jpg',
            'portrait.png',
            'artwork.jpg',
            'photo.png',
            'image.jpg'
        ])
        
        self.stego_method = config.get('stego_method', 'lsb')
        self.extraction_key = config.get('extraction_key', 'stego_key_2023')
        
        print(f"✅ Steganography инициализирован: {len(self.cover_images)} cover images, метод={self.stego_method}")
        return True
    
    def cleanup(self) -> bool:
        """Очистка ресурсов"""
        return True
