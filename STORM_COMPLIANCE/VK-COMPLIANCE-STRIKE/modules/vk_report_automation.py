#!/usr/bin/env python3
"""
VK-REPORT-AUTOMATION Module
Automated VK Complaint Filing System

This module handles automated submission of complaints to VK through:
- API methods (reports.report)
- Browser automation (Selenium/Playwright) for bypassing filters
- Multi-account rotation system
- Activity simulation before reporting
"""

import vk_api
import time
import random
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from playwright.async_api import async_playwright
import asyncio

@dataclass
class VKAccount:
    """Data class for VK account credentials"""
    login: str
    password: str
    user_id: str
    cookies: Optional[Dict] = None
    last_used: Optional[datetime] = None
    is_active: bool = True

@dataclass
class ReportRequest:
    """Data class for report request"""
    post_url: str
    owner_id: int
    post_id: int
    report_type: str
    reason: str
    evidence: Dict
    priority: int = 1

class VKReportAutomation:
    """Main class for VK automated reporting system"""
    
    # VK report types
    REPORT_TYPES = {
        "spam": 0,
        "child_pornography": 1,
        "extremism": 2,
        "violence": 3,
        "drug_propaganda": 4,
        "adult_material": 5,
        "abuse": 6,
        "suicide": 7,
        "copyright": 8,
        "duplicate_content": 9,
        "fake_news": 10
    }
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.accounts = self._load_accounts()
        self.current_account_index = 0
        self.logger = self._setup_logging()
        self.driver = None
        self.playwright = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file"""
        default_config = {
            "vk": {
                "api_version": "5.199",
                "report_cooldown": 300,  # 5 minutes between reports
                "account_rotation": True,
                "max_reports_per_account": 50
            },
            "automation": {
                "use_selenium": True,
                "use_playwright": True,
                "headless": True,
                "activity_simulation": True,
                "min_view_time": 5,
                "max_view_time": 15
            },
            "proxy": {
                "enabled": False,
                "rotation": True,
                "proxy_list": []
            },
            "storage": {
                "accounts_file": "./config/vk_accounts.json",
                "reports_log": "./data/reports_log.json",
                "cookies_dir": "./data/cookies"
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_accounts(self) -> List[VKAccount]:
        """Load VK accounts from file"""
        accounts_file = Path(self.config["storage"]["accounts_file"])
        accounts = []
        
        if accounts_file.exists():
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts_data = json.load(f)
                for acc_data in accounts_data:
                    account = VKAccount(**acc_data)
                    accounts.append(account)
        
        return accounts
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("VKReportAutomation")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(
                Path("./data/logs") / "vk_reports.log",
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_next_account(self) -> Optional[VKAccount]:
        """Get next available account for rotation"""
        if not self.accounts:
            return None
        
        # Find active account that hasn't been used recently
        for _ in range(len(self.accounts)):
            account = self.accounts[self.current_account_index]
            self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
            
            if account.is_active:
                # Check cooldown
                if (account.last_used is None or 
                    datetime.now() - account.last_used > timedelta(seconds=self.config["vk"]["report_cooldown"])):
                    return account
        
        return None
    
    def _simulate_activity(self, driver, post_url: str):
        """Simulate human-like activity before reporting"""
        if not self.config["automation"]["activity_simulation"]:
            return
        
        try:
            # Navigate to the post
            driver.get(post_url)
            time.sleep(random.uniform(2, 4))
            
            # Scroll around
            for _ in range(random.randint(1, 3)):
                driver.execute_script("window.scrollBy(0, random.randint(100, 500))")
                time.sleep(random.uniform(0.5, 1.5))
            
            # View time
            view_time = random.uniform(
                self.config["automation"]["min_view_time"],
                self.config["automation"]["max_view_time"]
            )
            time.sleep(view_time)
            
            self.logger.info(f"Activity simulation completed for {post_url}")
            
        except Exception as e:
            self.logger.error(f"Activity simulation failed: {e}")
    
    def _setup_selenium_driver(self) -> webdriver.Chrome:
        """Setup Selenium WebDriver"""
        options = Options()
        
        if self.config["automation"]["headless"]:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _login_via_selenium(self, account: VKAccount) -> bool:
        """Login to VK using Selenium"""
        try:
            if not self.driver:
                self.driver = self._setup_selenium_driver()
            
            # Navigate to VK login
            self.driver.get("https://vk.com/login")
            time.sleep(2)
            
            # Enter credentials
            email_field = self.driver.find_element(By.NAME, "email")
            email_field.send_keys(account.login)
            
            password_field = self.driver.find_element(By.NAME, "pass")
            password_field.send_keys(account.password)
            
            # Submit login
            password_field.submit()
            time.sleep(3)
            
            # Check if login successful
            if "vk.com/feed" in self.driver.current_url or "vk.com/id" in self.driver.current_url:
                # Save cookies
                account.cookies = self.driver.get_cookies()
                account.last_used = datetime.now()
                self.logger.info(f"Successfully logged in as {account.login}")
                return True
            else:
                self.logger.error(f"Login failed for {account.login}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error for {account.login}: {e}")
            return False
    
    def _submit_report_via_selenium(self, report: ReportRequest, account: VKAccount) -> bool:
        """Submit report using Selenium automation"""
        try:
            # Simulate activity first
            self._simulate_activity(self.driver, report.post_url)
            
            # Find and click report button
            report_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-report-type]"))
            )
            report_button.click()
            time.sleep(1)
            
            # Select report type
            report_type_element = self.driver.find_element(
                By.CSS_SELECTOR, 
                f"[data-report-type='{self.REPORT_TYPES.get(report.report_type, 0)}']"
            )
            report_type_element.click()
            time.sleep(1)
            
            # Submit report
            submit_button = self.driver.find_element(By.CSS_SELECTOR, ".box_submit")
            submit_button.click()
            time.sleep(2)
            
            self.logger.info(f"Report submitted via Selenium for {report.post_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Selenium report submission failed: {e}")
            return False
    
    def _submit_report_via_api(self, report: ReportRequest, account: VKAccount) -> bool:
        """Submit report using VK API"""
        try:
            vk_session = vk_api.VkApi(token=account.cookies.get('access_token'))
            vk = vk_session.get_api()
            
            # Submit report
            result = vk.reports.report(
                owner_id=report.owner_id,
                post_id=report.post_id,
                type=self.REPORT_TYPES.get(report.report_type, 0),
                reason=report.reason
            )
            
            if result == 1:  # Success
                self.logger.info(f"API report submitted for {report.post_url}")
                return True
            else:
                self.logger.error(f"API report failed for {report.post_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"API report submission error: {e}")
            return False
    
    def submit_report(self, report: ReportRequest) -> bool:
        """Submit a single report using available methods"""
        account = self._get_next_account()
        if not account:
            self.logger.error("No available accounts for reporting")
            return False
        
        self.logger.info(f"Submitting report for {report.post_url} using account {account.login}")
        
        # Try API first
        if hasattr(account, 'access_token') and account.access_token:
            if self._submit_report_via_api(report, account):
                self._log_report(report, account, "api")
                return True
        
        # Fallback to Selenium
        if self.config["automation"]["use_selenium"]:
            if self._login_via_selenium(account):
                if self._submit_report_via_selenium(report, account):
                    self._log_report(report, account, "selenium")
                    return True
        
        self.logger.error(f"Failed to submit report for {report.post_url}")
        return False
    
    def submit_bulk_reports(self, reports: List[ReportRequest]) -> Dict:
        """Submit multiple reports with account rotation"""
        results = {
            "total": len(reports),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for i, report in enumerate(reports):
            try:
                success = self.submit_report(report)
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                # Rate limiting between reports
                time.sleep(random.uniform(2, 5))
                
                # Account rotation
                if i % 10 == 0:  # Rotate every 10 reports
                    time.sleep(random.uniform(10, 30))
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(str(e))
                self.logger.error(f"Bulk report error: {e}")
        
        self.logger.info(f"Bulk reporting completed: {results['successful']}/{results['total']} successful")
        return results
    
    def _log_report(self, report: ReportRequest, account: VKAccount, method: str):
        """Log report submission"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "post_url": report.post_url,
            "report_type": report.report_type,
            "account": account.login,
            "method": method,
            "evidence": report.evidence
        }
        
        log_file = Path(self.config["storage"]["reports_log"])
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def generate_report_requests(self, violations: List[Dict]) -> List[ReportRequest]:
        """Convert violations to report requests"""
        requests = []
        
        for violation in violations:
            # Extract owner_id and post_id from post_url
            post_url = violation.get("post_url", "")
            if "wall" in post_url:
                parts = post_url.split("wall")[1].split("_")
                if len(parts) == 2:
                    owner_id = int(parts[0])
                    post_id = int(parts[1])
                    
                    # Map violation types to report types
                    report_type_map = {
                        "duplicate_content": "duplicate_content",
                        "fraud_scam": "spam",
                        "traffic_violence": "violence"
                    }
                    
                    report_type = report_type_map.get(
                        violation.get("violation_type", ""), 
                        "spam"
                    )
                    
                    request = ReportRequest(
                        post_url=post_url,
                        owner_id=owner_id,
                        post_id=post_id,
                        report_type=report_type,
                        reason=violation.get("evidence", {}).get("text_snippet", ""),
                        evidence=violation.get("evidence", {}),
                        priority=1 if violation.get("confidence", 0) >= 0.8 else 2
                    )
                    
                    requests.append(request)
        
        return requests
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()
        
        if self.playwright:
            asyncio.create_task(self.playwright.stop())

if __name__ == "__main__":
    # Example usage
    automation = VKReportAutomation()
    
    # Example report request
    sample_report = ReportRequest(
        post_url="https://vk.com/wall-123456789_123456789",
        owner_id=-123456789,
        post_id=123456789,
        report_type="duplicate_content",
        reason="Duplicate content detected",
        evidence={"hash": "abc123", "confidence": 0.95}
    )
    
    success = automation.submit_report(sample_report)
    print(f"Report submission: {'Success' if success else 'Failed'}")
