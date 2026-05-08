import asyncio
import logging
from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import cv2
import numpy as np
from PIL import Image
import requests
import re

logger = logging.getLogger(__name__)

class ViolationAnalyzer:
    def __init__(self, api_id: str, api_hash: str):
        self.client = TelegramClient('violation_analyzer', api_id, api_hash)
        self.violation_patterns = {
            'copyright': [
                r'(?:©|copyright|©\s*\d{4})',
                r'(?:official music|official video)',
                r'(?:brand|trademark|™)'
            ],
            'fraud': [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card patterns
                r'(?:bitcoin|btc|ethereum|eth).*\b[a-zA-Z0-9]{26,35}\b',
                r'(?:donate|payment|transfer|send money)',
                r'(?:paypal|stripe|venmo|cashapp)'
            ],
            'spam': [
                r'(?:click here|visit now|check out)',
                r'(?:discount|offer|deal|sale)',
                r'(?:buy now|purchase|order)',
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            ],
            'violence': [
                r'(?:crash|accident|wreck|collision)',
                r'(?:dangerous|racing|drifting|street racing)',
                r'(?:weapon|gun|knife|violence)',
                r'(?:police|chase|pursuit)'
            ]
        }
    
    async def analyze_channel(self, channel_username: str, limit: int = 100) -> Dict[str, Any]:
        """Analyze channel for content violations"""
        results = {
            'channel': channel_username,
            'total_messages': 0,
            'violations': {
                'copyright': [],
                'fraud': [],
                'spam': [],
                'violence': []
            },
            'media_analysis': {
                'video_count': 0,
                'image_count': 0,
                'document_count': 0,
                'suspicious_media': []
            }
        }
        
        try:
            await self.client.connect()
            
            async for message in self.client.iter_messages(channel_username, limit=limit):
                results['total_messages'] += 1
                
                # Analyze text content
                if message.text:
                    text_violations = self._analyze_text(message.text)
                    for category, violations in text_violations.items():
                        results['violations'][category].extend([
                            {
                                'message_id': message.id,
                                'text': message.text[:200],
                                'pattern': violation,
                                'timestamp': message.date.isoformat()
                            }
                            for violation in violations
                        ])
                
                # Analyze media content
                if message.media:
                    media_analysis = await self._analyze_media(message)
                    if media_analysis['is_suspicious']:
                        results['media_analysis']['suspicious_media'].append({
                            'message_id': message.id,
                            'media_type': media_analysis['type'],
                            'reason': media_analysis['reason'],
                            'timestamp': message.date.isoformat()
                        })
                    
                    results['media_analysis'][f"{media_analysis['type']}_count"] += 1
            
            logger.info(f"Analysis complete for {channel_username}: {results['total_messages']} messages analyzed")
            
        except Exception as e:
            logger.error(f"Error analyzing channel {channel_username}: {str(e)}")
            results['error'] = str(e)
        
        finally:
            await self.client.disconnect()
        
        return results
    
    def _analyze_text(self, text: str) -> Dict[str, List[str]]:
        """Analyze text for violation patterns"""
        violations = {}
        text_lower = text.lower()
        
        for category, patterns in self.violation_patterns.items():
            category_violations = []
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    category_violations.extend(matches)
            
            if category_violations:
                violations[category] = list(set(category_violations))  # Remove duplicates
        
        return violations
    
    async def _analyze_media(self, message) -> Dict[str, Any]:
        """Analyze media content for potential violations"""
        analysis = {
            'type': 'unknown',
            'is_suspicious': False,
            'reason': None
        }
        
        try:
            if isinstance(message.media, MessageMediaPhoto):
                analysis['type'] = 'image'
                # Download and analyze image for potential copyright issues
                photo_path = await message.download_media()
                if photo_path:
                    image_analysis = self._analyze_image(photo_path)
                    analysis.update(image_analysis)
                    os.remove(photo_path)  # Clean up
            
            elif isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                if doc.mime_type:
                    if 'video' in doc.mime_type:
                        analysis['type'] = 'video'
                        analysis['is_suspicious'] = True
                        analysis['reason'] = 'Video content requires manual review for copyright'
                    elif 'audio' in doc.mime_type:
                        analysis['type'] = 'audio'
                        analysis['is_suspicious'] = True
                        analysis['reason'] = 'Audio content requires manual review for copyright'
                    else:
                        analysis['type'] = 'document'
        
        except Exception as e:
            logger.error(f"Error analyzing media: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image for potential violations"""
        analysis = {
            'is_suspicious': False,
            'reason': None
        }
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return analysis
            
            # Basic image analysis
            height, width = image.shape[:2]
            
            # Check for potential brand logos (simplified)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection for logo-like shapes
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # If we find many small contours, it might contain logos/text
            small_contours = [c for c in contours if cv2.contourArea(c) > 100 and cv2.contourArea(c) < 1000]
            if len(small_contours) > 5:
                analysis['is_suspicious'] = True
                analysis['reason'] = 'Potential brand logos or text overlays detected'
            
            # Check for watermark-like patterns in corners
            corner_regions = [
                gray[:height//4, :width//4],  # Top-left
                gray[:height//4, 3*width//4:],  # Top-right
                gray[3*height//4:, :width//4],  # Bottom-left
                gray[3*height//4:, 3*width//4:]  # Bottom-right
            ]
            
            for region in corner_regions:
                if np.mean(region) > 200 or np.mean(region) < 50:  # Very bright or very dark
                    analysis['is_suspicious'] = True
                    analysis['reason'] = 'Potential watermark detected'
                    break
        
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
        
        return analysis

import os
