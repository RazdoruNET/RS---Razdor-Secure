#!/usr/bin/env python3
"""
Crawler & Parser Module
Collects all input vectors (URL parameters, GET/POST, headers, cookies)
"""

import requests
import urllib.parse
from bs4 import BeautifulSoup
from typing import Dict, List, Set, Tuple, Optional
import re
from urllib.robotparser import RobotFileParser
import time
import logging

class InputVector:
    """Represents an input vector for testing"""
    def __init__(self, url: str, method: str = 'GET', params: Dict = None, 
                 headers: Dict = None, cookies: Dict = None, data: Dict = None):
        self.url = url
        self.method = method.upper()
        self.params = params or {}
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.data = data or {}
        
    def __str__(self):
        return f"{self.method} {self.url} - Params: {list(self.params.keys())}"

class WebCrawler:
    """Web crawler for discovering input vectors"""
    
    def __init__(self, delay: float = 1.0, user_agent: str = None, 
                 respect_robots: bool = True):
        self.delay = delay
        self.session = requests.Session()
        self.visited_urls: Set[str] = set()
        self.input_vectors: List[InputVector] = []
        self.respect_robots = respect_robots
        self.logger = logging.getLogger(__name__)
        
        # Set default headers
        default_headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (compatible; SQLiAuditor/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(default_headers)
        
    def check_robots_txt(self, base_url: str) -> RobotFileParser:
        """Check robots.txt for crawling restrictions"""
        rp = RobotFileParser()
        robots_url = urllib.parse.urljoin(base_url, '/robots.txt')
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp
        except Exception as e:
            self.logger.warning(f"Could not read robots.txt: {e}")
            return None
    
    def crawl_url(self, url: str, max_depth: int = 3, current_depth: int = 0) -> None:
        """Crawl a URL and discover input vectors"""
        if current_depth >= max_depth or url in self.visited_urls:
            return
            
        self.visited_urls.add(url)
        self.logger.info(f"Crawling (depth {current_depth}): {url}")
        
        try:
            # Check robots.txt if enabled
            if self.respect_robots and current_depth == 0:
                rp = self.check_robots_txt(url)
                if rp and not rp.can_fetch(self.session.headers['User-Agent'], url):
                    self.logger.info(f"Skipping {url} due to robots.txt")
                    return
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract input vectors from current URL
            self._extract_url_vectors(url)
            
            # Parse HTML for forms and links
            soup = BeautifulSoup(response.content, 'html.parser')
            self._extract_forms(url, soup)
            self._extract_links(url, soup, max_depth, current_depth)
            
            # Respect delay
            time.sleep(self.delay)
            
        except requests.RequestException as e:
            self.logger.error(f"Error crawling {url}: {e}")
    
    def _extract_url_vectors(self, url: str) -> None:
        """Extract input vectors from URL parameters"""
        parsed = urllib.parse.urlparse(url)
        if parsed.query:
            params = urllib.parse.parse_qs(parsed.query)
            vector = InputVector(
                url=url,
                method='GET',
                params={k: v[0] for k, v in params.items()}
            )
            self.input_vectors.append(vector)
    
    def _extract_forms(self, base_url: str, soup: BeautifulSoup) -> None:
        """Extract forms and create input vectors"""
        forms = soup.find_all('form')
        
        for form in forms:
            action = form.get('action', '')
            method = form.get('method', 'GET').upper()
            
            # Convert relative URL to absolute
            form_url = urllib.parse.urljoin(base_url, action)
            
            # Extract form fields
            form_data = {}
            inputs = form.find_all(['input', 'textarea', 'select'])
            
            for input_tag in inputs:
                name = input_tag.get('name')
                if name:
                    input_type = input_tag.get('type', 'text')
                    if input_type.lower() in ['text', 'password', 'search', 'email', 
                                             'hidden', 'textarea']:
                        # Use default values if available
                        value = input_tag.get('value', 'test')
                        form_data[name] = value
            
            if form_data:
                vector = InputVector(
                    url=form_url,
                    method=method,
                    data=form_data if method == 'POST' else None,
                    params=form_data if method == 'GET' else None
                )
                self.input_vectors.append(vector)
    
    def _extract_links(self, base_url: str, soup: BeautifulSoup, 
                      max_depth: int, current_depth: int) -> None:
        """Extract links and continue crawling"""
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            absolute_url = urllib.parse.urljoin(base_url, href)
            
            # Only follow same-domain links
            if urllib.parse.urlparse(base_url).netloc == urllib.parse.urlparse(absolute_url).netloc:
                self.crawl_url(absolute_url, max_depth, current_depth + 1)
    
    def crawl_domain(self, start_url: str, max_depth: int = 3) -> List[InputVector]:
        """Crawl entire domain and return all input vectors"""
        self.logger.info(f"Starting crawl of {start_url}")
        self.crawl_url(start_url, max_depth)
        self.logger.info(f"Crawling complete. Found {len(self.input_vectors)} input vectors")
        return self.input_vectors
    
    def get_input_vectors(self) -> List[InputVector]:
        """Return all discovered input vectors"""
        return self.input_vectors
    
    def clear_vectors(self) -> None:
        """Clear all stored vectors"""
        self.input_vectors.clear()
        self.visited_urls.clear()

class VectorAnalyzer:
    """Analyze input vectors for SQL injection potential"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_vectors(self, vectors: List[InputVector]) -> Dict:
        """Analyze vectors and categorize by injection potential"""
        analysis = {
            'total_vectors': len(vectors),
            'get_vectors': [],
            'post_vectors': [],
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }
        
        for vector in vectors:
            # Categorize by method
            if vector.method == 'GET':
                analysis['get_vectors'].append(vector)
            else:
                analysis['post_vectors'].append(vector)
            
            # Assess risk based on parameter names and patterns
            risk_score = self._assess_risk(vector)
            
            if risk_score >= 7:
                analysis['high_risk'].append(vector)
            elif risk_score >= 4:
                analysis['medium_risk'].append(vector)
            else:
                analysis['low_risk'].append(vector)
        
        return analysis
    
    def _assess_risk(self, vector: InputVector) -> int:
        """Assess risk score for an input vector"""
        score = 0
        high_risk_params = ['id', 'user', 'username', 'password', 'email', 
                           'search', 'query', 'filter', 'category', 'product']
        medium_risk_params = ['page', 'sort', 'order', 'limit', 'offset']
        
        # Check parameter names
        all_params = list(vector.params.keys()) + list(vector.data.keys())
        for param in all_params:
            param_lower = param.lower()
            if any(risk in param_lower for risk in high_risk_params):
                score += 3
            elif any(risk in param_lower for risk in medium_risk_params):
                score += 2
            else:
                score += 1
        
        # Bonus for numeric parameters
        for param in all_params:
            values = (vector.params.get(param, []) or vector.data.get(param, []))
            if isinstance(values, list):
                values = values[0] if values else ''
            if str(values).isdigit():
                score += 1
        
        return min(score, 10)
