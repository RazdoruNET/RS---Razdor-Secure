#!/usr/bin/env python3
"""
LEGAL-MINING-VK Module
VK Content Analysis and Violation Detection System

This module scans VK group walls for:
- Non-original content (duplicate videos/photos via hash analysis)
- Traffic violations/Violence (dangerous maneuvers without censorship)
- Fraud/scam (sales without official documentation)
"""

import vk_api
import hashlib
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import io
import base64

@dataclass
class Violation:
    """Data class for storing violation information"""
    post_id: int
    post_url: str
    violation_type: str
    content_type: str
    confidence: float
    evidence: Dict
    timestamp: datetime
    content_hash: Optional[str] = None

class LegalMiningVK:
    """Main class for VK content analysis and violation detection"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.session = self._initialize_vk_session()
        self.violations = []
        self.content_hashes = {}  # Store seen content hashes
        self.logger = self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        default_config = {
            "vk": {
                "access_token": "",
                "group_id": "dsmotopro",
                "api_version": "5.199"
            },
            "analysis": {
                "max_posts_per_scan": 100,
                "hash_threshold": 0.95,
                "violence_threshold": 0.8,
                "fraud_keywords": ["продам", "куплю", "цена", "договор", "официально"]
            },
            "storage": {
                "cache_dir": "./data/cache",
                "results_dir": "./data/results"
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _initialize_vk_session(self) -> vk_api.VkApi:
        """Initialize VK API session"""
        try:
            vk_session = vk_api.VkApi(token=self.config["vk"]["access_token"])
            return vk_session
        except Exception as e:
            raise Exception(f"Failed to initialize VK session: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("LegalMiningVK")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(
                Path(self.config["storage"]["results_dir"]) / "legal_mining.log",
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _calculate_content_hash(self, content_url: str, content_type: str) -> str:
        """Calculate hash for content (image or video)"""
        try:
            response = requests.get(content_url, timeout=10)
            response.raise_for_status()
            
            if content_type == "photo":
                # Calculate perceptual hash for images
                image = Image.open(io.BytesIO(response.content))
                image = image.resize((8, 8), Image.LANCZOS)
                image = image.convert('L')
                pixels = list(image.getdata())
                avg = sum(pixels) / len(pixels)
                bits = ''.join(['1' if pixel > avg else '0' for pixel in pixels])
                return hashlib.md5(bits.encode()).hexdigest()
            
            elif content_type == "video":
                # For videos, use file hash (simplified approach)
                return hashlib.md5(response.content).hexdigest()
                
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {content_url}: {e}")
            return ""
    
    def _detect_duplicate_content(self, post: Dict) -> List[Violation]:
        """Detect non-original content by comparing hashes"""
        violations = []
        
        # Check photos
        if 'attachments' in post:
            for attachment in post['attachments']:
                if attachment['type'] == 'photo':
                    photo_url = max(attachment['photo']['sizes'], 
                                  key=lambda x: x.get('width', 0))['url']
                    content_hash = self._calculate_content_hash(photo_url, "photo")
                    
                    if content_hash and content_hash in self.content_hashes:
                        violations.append(Violation(
                            post_id=post['id'],
                            post_url=f"https://vk.com/wall{post['owner_id']}_{post['id']}",
                            violation_type="duplicate_content",
                            content_type="photo",
                            confidence=0.95,
                            evidence={
                                "original_post": self.content_hashes[content_hash],
                                "duplicate_url": photo_url,
                                "content_hash": content_hash
                            },
                            timestamp=datetime.now(),
                            content_hash=content_hash
                        ))
                    elif content_hash:
                        self.content_hashes[content_hash] = f"https://vk.com/wall{post['owner_id']}_{post['id']}"
        
        return violations
    
    def _analyze_content_for_violations(self, post: Dict) -> List[Violation]:
        """Analyze post content for various violations"""
        violations = []
        text = post.get('text', '').lower()
        
        # Check for fraud/scam indicators
        fraud_keywords = self.config["analysis"]["fraud_keywords"]
        fraud_score = sum(1 for keyword in fraud_keywords if keyword in text)
        
        if fraud_score >= 2:  # Multiple fraud indicators
            violations.append(Violation(
                post_id=post['id'],
                post_url=f"https://vk.com/wall{post['owner_id']}_{post['id']}",
                violation_type="fraud_scam",
                content_type="text",
                confidence=min(fraud_score * 0.3, 1.0),
                evidence={
                    "fraud_keywords_found": [kw for kw in fraud_keywords if kw in text],
                    "text_snippet": text[:200]
                },
                timestamp=datetime.now()
            ))
        
        # Check for traffic violence indicators
        violence_keywords = ["дтп", "авария", "наезд", "столкновение", "опасный", "нарушение"]
        violence_score = sum(1 for keyword in violence_keywords if keyword in text)
        
        if violence_score >= 1:
            violations.append(Violation(
                post_id=post['id'],
                post_url=f"https://vk.com/wall{post['owner_id']}_{post['id']}",
                violation_type="traffic_violence",
                content_type="text",
                confidence=min(violence_score * 0.4, 1.0),
                evidence={
                    "violence_keywords_found": [kw for kw in violence_keywords if kw in text],
                    "text_snippet": text[:200]
                },
                timestamp=datetime.now()
            ))
        
        return violations
    
    def scan_group_wall(self, count: int = None) -> List[Violation]:
        """Main method to scan VK group wall for violations"""
        if count is None:
            count = self.config["analysis"]["max_posts_per_scan"]
        
        self.logger.info(f"Starting scan of group {self.config['vk']['group_id']}")
        
        try:
            vk = self.session.get_api()
            posts = vk.wall.get(
                owner_id=f"-{self.config['vk']['group_id']}",
                count=count,
                extended=1
            )
            
            all_violations = []
            
            for post in posts['items']:
                if post.get('marked_as_ads', 0):
                    continue  # Skip ads
                
                # Check for duplicate content
                duplicate_violations = self._detect_duplicate_content(post)
                all_violations.extend(duplicate_violations)
                
                # Analyze content for other violations
                content_violations = self._analyze_content_for_violations(post)
                all_violations.extend(content_violations)
                
                # Rate limiting
                time.sleep(0.3)
            
            self.violations.extend(all_violations)
            self.logger.info(f"Scan completed. Found {len(all_violations)} violations")
            
            return all_violations
            
        except Exception as e:
            self.logger.error(f"Error during group scan: {e}")
            return []
    
    def save_results(self, filename: str = None) -> str:
        """Save scan results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"violations_{timestamp}.json"
        
        results_path = Path(self.config["storage"]["results_dir"]) / filename
        
        # Convert violations to serializable format
        results_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_violations": len(self.violations),
            "violations": [
                {
                    "post_id": v.post_id,
                    "post_url": v.post_url,
                    "violation_type": v.violation_type,
                    "content_type": v.content_type,
                    "confidence": v.confidence,
                    "evidence": v.evidence,
                    "timestamp": v.timestamp.isoformat(),
                    "content_hash": v.content_hash
                }
                for v in self.violations
            ]
        }
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Results saved to {results_path}")
        return str(results_path)
    
    def get_violation_summary(self) -> Dict:
        """Get summary of found violations"""
        summary = {
            "total_violations": len(self.violations),
            "by_type": {},
            "by_content_type": {},
            "high_confidence": len([v for v in self.violations if v.confidence >= 0.8])
        }
        
        for violation in self.violations:
            # Count by violation type
            vtype = violation.violation_type
            summary["by_type"][vtype] = summary["by_type"].get(vtype, 0) + 1
            
            # Count by content type
            ctype = violation.content_type
            summary["by_content_type"][ctype] = summary["by_content_type"].get(ctype, 0) + 1
        
        return summary

if __name__ == "__main__":
    # Example usage
    analyzer = LegalMiningVK()
    violations = analyzer.scan_group_wall()
    
    if violations:
        print(f"Found {len(violations)} violations:")
        for violation in violations[:5]:  # Show first 5
            print(f"- {violation.violation_type}: {violation.post_url} (confidence: {violation.confidence:.2f})")
        
        # Save results
        results_file = analyzer.save_results()
        print(f"Results saved to: {results_file}")
    else:
        print("No violations found.")
