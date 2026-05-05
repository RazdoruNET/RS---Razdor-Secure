#!/usr/bin/env python3
"""
RSecure CVU (Cyber Vulnerability Updates) Intelligence Module
Integrates vulnerability intelligence from NVD, GHSA, and CISA KEV
"""

import os
import json
import requests
import time
import threading
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set, Optional, Any
from pathlib import Path

class RSecureCVU:
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Directories and files
        self.save_dir = Path(self.config.get('save_dir', './data'))
        self.save_dir.mkdir(exist_ok=True)
        self.output_file = self.save_dir / 'active_threats.json'
        
        # API endpoints
        self.nvd_api = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.ghsa_api = "https://api.github.com/advisories"
        self.cisa_kev_api = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        
        # Target categories for classification
        self.target = {
            "linux": ["linux", "kernel", "ubuntu", "debian"],
            "cloud": ["aws", "azure", "gcp", "kubernetes"],
            "llm": ["llm", "ai", "model"],
            "macos": ["macos", "apple"],
            "docker": ["docker", "container"],
            "web": ["http", "nginx", "apache", "xss", "sql", "auth"],
            "network": ["tcp", "udp", "arp", "lan"],
            "iot": ["camera", "ipcam", "router"]
        }
        
        # Data storage
        self.kev_cache = set()
        self.active_threats = []
        self.processed_vulnerabilities = set()
        
        # Offline knowledge base
        self.offline_threats = []
        self.offline_file = Path('./rsecure/config/offline_threats.json')
        
        # Threading
        self.running = False
        self.update_thread = None
        
        # Setup logging
        log_dir = Path('./logs/security')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('rsecure_cvu')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_dir / 'cvu_intelligence.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # Initialize components
        self._initialize_data_storage()
        self._load_existing_data()
        self._load_offline_knowledge_base()
        
    def _initialize_data_storage(self):
        """Initialize data storage directories and files"""
        try:
            # Create data directory
            self.save_dir.mkdir(exist_ok=True)
            
            # Initialize data structures
            self.active_threats = []
            self.processed_vulnerabilities = set()
            self.kev_cache = set()
            
            self.logger.info("CVU data storage initialized")
        except Exception as e:
            self.logger.error(f"Error initializing data storage: {e}")
    
    def _get_default_config(self) -> Dict:
        return {
            'save_dir': os.environ.get("CVU_DIR", "./data"),
            'interval_min': 7,
            'max_results': 100,
            'days_back': 7,
            'request_timeout': 20,
            'auto_classify': True,
            'enable_kev': True,
            'enable_nvd': True,
            'enable_ghsa': True
        }
    
    def _load_existing_data(self):
        """Load existing threat data from file"""
        try:
            if self.output_file.exists():
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
                    self.active_threats = data.get('active_threats', [])
                    self.processed_vulnerabilities = set(data.get('processed_vulnerabilities', []))
                self.logger.info(f"Loaded {len(self.active_threats)} existing threats")
        except Exception as e:
            self.logger.error(f"Error loading existing data: {e}")
    
    def _load_offline_knowledge_base(self):
        """Load offline threat knowledge base"""
        try:
            if self.offline_file.exists():
                with open(self.offline_file, 'r') as f:
                    self.offline_threats = json.load(f)
                self.logger.info(f"Loaded {len(self.offline_threats)} offline threats")
        except Exception as e:
            self.logger.error(f"Error loading offline knowledge base: {e}")
    
    def start_intelligence(self):
        """Start CVU intelligence gathering"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._intelligence_loop, daemon=True)
        self.update_thread.start()
        
        self.logger.info("RSecure CVU intelligence started")
    
    def stop_intelligence(self):
        """Stop CVU intelligence gathering"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=30)
        self.logger.info("RSecure CVU intelligence stopped")
    
    def _intelligence_loop(self):
        """Main intelligence gathering loop"""
        self.logger.info("CVU STABLE ENGINE STARTED")
        
        while self.running:
            try:
                self._update_cycle()
            except Exception as e:
                self.logger.error(f"Error in CVU cycle: {e}")
            
            time.sleep(self.config['interval_min'] * 60)
    
    def _update_cycle(self):
        """Single update cycle"""
        self.logger.info("Starting CVU update cycle")
        
        # Update KEV cache
        if self.config['enable_kev']:
            self.kev_cache = self._fetch_kev()
            self.logger.info(f"KEV cache updated: {len(self.kev_cache)} vulnerabilities")
        
        # Fetch vulnerability data
        nvd_data = []
        ghsa_data = []
        
        if self.config['enable_nvd']:
            nvd_data = self._fetch_nvd()
            self.logger.info(f"NVD items fetched: {len(nvd_data)}")
        
        if self.config['enable_ghsa']:
            ghsa_data = self._fetch_ghsa()
            self.logger.info(f"GHSA items fetched: {len(ghsa_data)}")
        
        # Normalize and merge data
        nvd_normalized = [self._normalize_nvd(x) for x in nvd_data]
        nvd_normalized = [x for x in nvd_normalized if x]
        
        ghsa_normalized = [self._normalize_ghsa(x) for x in ghsa_data]
        ghsa_normalized = [x for x in ghsa_normalized if x]
        
        merged_data = self._merge_data(nvd_normalized, ghsa_normalized)
        
        # Process and score threats
        processed_threats = []
        for item in merged_data:
            processed_item = self._process_threat(item)
            if processed_item:
                processed_threats.append(processed_item)
        
        # Sort by risk
        processed_threats.sort(key=lambda x: x.get('final_risk', 0), reverse=True)
        
        # Save results
        self.active_threats = processed_threats[:self.config['max_results']]
        self._save_threats()
        
        self.logger.info(f"CVU cycle completed: {len(self.active_threats)} active threats")
    
    def _fetch_kev(self) -> Set[str]:
        """Fetch CISA Known Exploited Vulnerabilities"""
        try:
            response = requests.get(self.cisa_kev_api, timeout=self.config['request_timeout'])
            data = response.json()
            return {x["cveID"] for x in data.get("vulnerabilities", [])}
        except Exception as e:
            self.logger.error(f"Error fetching KEV data: {e}")
            return set()
    
    def _fetch_nvd(self) -> List[Dict]:
        """Fetch NVD vulnerability data"""
        try:
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=self.config['days_back'])
            
            params = {
                "resultsPerPage": self.config['max_results'],
                "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "pubEndDate": now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            }
            
            response = requests.get(self.nvd_api, params=params, timeout=self.config['request_timeout'])
            data = response.json()
            return data.get("vulnerabilities", [])
        except Exception as e:
            self.logger.error(f"Error fetching NVD data: {e}")
            return []
    
    def _fetch_ghsa(self) -> List[Dict]:
        """Fetch GitHub Security Advisory data"""
        try:
            headers = {"Accept": "application/vnd.github+json"}
            response = requests.get(self.ghsa_api, headers=headers, timeout=self.config['request_timeout'])
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching GHSA data: {e}")
            return []
    
    def _normalize_nvd(self, item: Dict) -> Optional[Dict]:
        """Normalize NVD vulnerability data"""
        try:
            cve = item.get("cve", {})
            cve_id = cve.get("id")
            
            descriptions = cve.get("descriptions", [])
            description = descriptions[0]["value"] if descriptions else ""
            
            metrics = cve.get("metrics", {})
            cvss_score = 0.0
            
            if "cvssMetricV31" in metrics:
                cvss_score = self._safe_float(metrics["cvssMetricV31"][0]["cvssData"]["baseScore"])
            elif "cvssMetricV30" in metrics:
                cvss_score = self._safe_float(metrics["cvssMetricV30"][0]["cvssData"]["baseScore"])
            elif "cvssMetricV2" in metrics:
                cvss_score = self._safe_float(metrics["cvssMetricV2"][0]["cvssData"]["baseScore"])
            
            if cvss_score == 0:
                return None
            
            return {
                "id": cve_id,
                "source": "NVD",
                "summary": description[:300],
                "cvss_score": cvss_score,
                "published_date": cve.get("published", ""),
                "modified_date": cve.get("lastModified", ""),
                "merged": False
            }
        except Exception as e:
            self.logger.error(f"Error normalizing NVD item: {e}")
            return None
    
    def _normalize_ghsa(self, item: Dict) -> Optional[Dict]:
        """Normalize GHSA vulnerability data"""
        try:
            cvss = item.get("cvss") or {}
            if not isinstance(cvss, dict):
                cvss = {}
            
            cvss_score = self._safe_float(cvss.get("score"))
            
            return {
                "id": item.get("ghsa_id"),
                "cve": item.get("cve_id"),
                "source": "GHSA",
                "summary": (item.get("summary") or "")[:300],
                "cvss_score": cvss_score,
                "published_date": item.get("published_at", ""),
                "modified_date": item.get("updated_at", ""),
                "severity": item.get("severity", ""),
                "merged": False
            }
        except Exception as e:
            self.logger.error(f"Error normalizing GHSA item: {e}")
            return None
    
    def _merge_data(self, nvd_data: List[Dict], ghsa_data: List[Dict]) -> List[Dict]:
        """Merge NVD and GHSA data"""
        merged_db = {}
        
        # Add NVD data
        for item in nvd_data:
            merged_db[item["id"]] = item
        
        # Merge GHSA data
        for item in ghsa_data:
            key = item.get("cve") or item["id"]
            
            if key in merged_db:
                # Merge with existing NVD entry
                existing = merged_db[key]
                existing["source"] = "NVD+GHSA"
                existing["merged"] = True
                existing["cvss_score"] = max(existing["cvss_score"], item["cvss_score"])
                existing["ghsa_id"] = item["id"]
            else:
                merged_db[key] = item
        
        return list(merged_db.values())
    
    def _process_threat(self, item: Dict) -> Optional[Dict]:
        """Process and score individual threat"""
        try:
            # Generate tags
            tags = self._generate_tags(item.get("summary", ""))
            if not tags:
                return None
            
            # Calculate scores
            trust_score = self._calculate_trust(item)
            ai_risk_score = self._calculate_ai_risk(item)
            final_risk_score = self._calculate_final_risk(item, trust_score, ai_risk_score)
            
            # Add processed data
            item.update({
                "tags": tags,
                "trust": trust_score,
                "ai_risk": ai_risk_score,
                "final_risk": final_risk_score,
                "processed_at": datetime.now().isoformat(),
                "in_kev": item.get("id") in self.kev_cache
            })
            
            return item
        except Exception as e:
            self.logger.error(f"Error processing threat: {e}")
            return None
    
    def _generate_tags(self, text: str) -> List[str]:
        """Generate classification tags from text"""
        text = text.lower()
        tags = []
        
        for category, keywords in self.target.items():
            if any(keyword in text for keyword in keywords):
                tags.append(category)
        
        # Fallback tags for general security terms
        if not tags:
            security_keywords = [
                "vulnerability", "exploit", "unauthenticated",
                "remote", "access", "injection", "bypass"
            ]
            if any(keyword in text for keyword in security_keywords):
                tags.append("web")
        
        return tags
    
    def _safe_float(self, value) -> float:
        """Safely convert to float"""
        try:
            return float(value)
        except:
            return 0.0
    
    def _calculate_trust(self, item: Dict) -> float:
        """Calculate trust score based on source and metrics"""
        # KEV vulnerabilities get maximum trust
        if item.get("id") in self.kev_cache:
            return 10.0
        
        score = 0.0
        
        # Source-based scoring
        source = item.get("source", "")
        if source == "NVD":
            score += 4.0
        elif source == "NVD+GHSA":
            score += 6.0
        elif source == "GHSA":
            score += 3.0
        
        # CVSS score bonus
        cvss_score = item.get("cvss_score", 0)
        if cvss_score >= 9.0:
            score += 1.0
        elif cvss_score >= 7.0:
            score += 0.5
        
        return min(score, 10.0)
    
    def _calculate_ai_risk(self, item: Dict) -> float:
        """Calculate AI-based risk score"""
        # KEV vulnerabilities get maximum risk
        if item.get("id") in self.kev_cache:
            return 10.0
        
        score = self._safe_float(item.get("cvss_score", 0))
        summary = (item.get("summary") or "").lower()
        
        # Risk factors
        if "rce" in summary:
            score += 2.0
        if "jwt" in summary:
            score += 1.5
        if "bypass" in summary:
            score += 1.0
        if "privilege escalation" in summary:
            score += 1.5
        if "remote code execution" in summary:
            score += 2.5
        
        # Category-based risk adjustment
        tags = self._generate_tags(summary)
        for tag in tags:
            if tag == "cloud":
                score += 1.0
            elif tag == "docker":
                score += 1.0
            elif tag == "llm":
                score += 1.2
            elif tag == "network":
                score += 0.8
            elif tag == "linux":
                score += 0.5
        
        return min(score, 10.0)
    
    def _calculate_final_risk(self, item: Dict, trust_score: float, ai_risk_score: float) -> float:
        """Calculate final risk score"""
        # KEV vulnerabilities get maximum final risk
        if item.get("id") in self.kev_cache:
            return 10.0
        
        # Apply trust penalty
        penalty = (10.0 - trust_score) * 0.6
        
        final_score = ai_risk_score - penalty
        return max(0.0, min(10.0, final_score))
    
    def _save_threats(self):
        """Save active threats to file"""
        try:
            with open(self.output_file, "w") as f:
                for threat in self.active_threats:
                    f.write(json.dumps(threat) + "\n")
            
            self.logger.info(f"Saved {len(self.active_threats)} threats to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving threats: {e}")
    
    def get_active_threats(self, limit: int = None, min_risk: float = 0.0) -> List[Dict]:
        """Get active threats with optional filtering"""
        threats = self.active_threats.copy()
        
        # Filter by minimum risk
        if min_risk > 0:
            threats = [t for t in threats if t.get('final_risk', 0) >= min_risk]
        
        # Apply limit
        if limit:
            threats = threats[:limit]
        
        return threats
    
    def get_threats_by_tag(self, tag: str, limit: int = 10) -> List[Dict]:
        """Get threats filtered by specific tag"""
        filtered = [t for t in self.active_threats if tag in t.get('tags', [])]
        filtered.sort(key=lambda x: x.get('final_risk', 0), reverse=True)
        return filtered[:limit]
    
    def get_kev_threats(self) -> List[Dict]:
        """Get all KEV (Known Exploited Vulnerabilities)"""
        return [t for t in self.active_threats if t.get('in_kev', False)]
    
    def get_high_risk_threats(self, threshold: float = 7.0) -> List[Dict]:
        """Get high risk threats above threshold"""
        # Try online threats first
        online_threats = [t for t in self.active_threats if t.get('final_risk', 0) >= threshold]
        
        # If no online threats available, use offline knowledge base
        if not online_threats and self.is_offline_available():
            offline_threats = self.get_offline_threats(min_score=threshold)
            self.logger.info(f"Using offline knowledge base: {len(offline_threats)} threats found")
            return offline_threats
        
        return online_threats
    
    def search_threats(self, query: str) -> List[Dict]:
        """Search threats by text query"""
        query = query.lower()
        results = []
        
        # Search online threats first
        for threat in self.active_threats:
            text = f"{threat.get('id', '')} {threat.get('summary', '')} {threat.get('cve', '')}".lower()
            if query in text:
                results.append(threat)
        
        # If no online results, search offline knowledge base
        if not results and self.is_offline_available():
            offline_results = self.search_offline_threats(query)
            self.logger.info(f"Using offline search: {len(offline_results)} results found")
            results.extend(offline_results)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get CVU statistics"""
        total_threats = len(self.active_threats)
        kev_count = len(self.get_kev_threats())
        high_risk_count = len(self.get_high_risk_threats())
        
        # Tag distribution
        tag_counts = {}
        for threat in self.active_threats:
            for tag in threat.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Source distribution
        source_counts = {}
        for threat in self.active_threats:
            source = threat.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'total_threats': total_threats,
            'source_distribution': source_counts,
            'tag_distribution': tag_counts,
            'average_score': avg_score
        }
    
    def is_offline_available(self) -> bool:
        """Check if offline knowledge base is available"""
        return len(self.offline_threats) > 0
    
    def get_fallback_threats(self, limit: int = 50) -> List[Dict]:
        """Get fallback threats from offline knowledge base when internet is unavailable"""
        if self.is_offline_available():
            return self.offline_threats[:limit]
        return []

if __name__ == "__main__":
    # Example usage
    cvu = RSecureCVU()
    cvu.start_intelligence()
    
    try:
        while True:
            # Get high risk threats
            high_risk = cvu.get_high_risk_threats(7.0)
            print(f"High risk threats: {len(high_risk)}")
            
            # Get KEV threats
            kev_threats = cvu.get_kev_threats()
            print(f"KEV threats: {len(kev_threats)}")
            
            # Get statistics
            stats = cvu.get_statistics()
            print(f"Statistics: {stats}")
            
            time.sleep(60)
    except KeyboardInterrupt:
        cvu.stop_intelligence()
